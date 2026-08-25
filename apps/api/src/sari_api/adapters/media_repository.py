from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import MediaAsset, MediaAuditLog
from sari_api.core.observability import get_correlation_id


class MediaNotFoundError(Exception):
    pass


class MediaStateError(Exception):
    pass


class MediaConcurrencyError(Exception):
    pass


class MediaRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def create(self, *, actor_id: UUID, **values: Any) -> MediaAsset:
        asset = MediaAsset(tenant_id=self._tenant_id, uploaded_by=actor_id, **values)
        self._session.add(asset)
        await self._session.flush()
        self._audit(asset, actor_id, "media.uploaded", after=self.snapshot(asset))
        return asset

    async def list_assets(
        self, *, status: str | None = None, search: str | None = None
    ) -> list[MediaAsset]:
        statement = select(MediaAsset).where(MediaAsset.tenant_id == self._tenant_id)
        if status:
            statement = statement.where(MediaAsset.public_use_status == status)
        if search:
            term = f"%{search.strip()}%"
            statement = statement.where(
                or_(MediaAsset.title.ilike(term), MediaAsset.original_filename.ilike(term))
            )
        result = await self._session.scalars(
            statement.order_by(MediaAsset.updated_at.desc(), MediaAsset.id)
        )
        return list(result.all())

    async def get(self, asset_id: UUID, *, lock: bool = False) -> MediaAsset:
        statement = select(MediaAsset).where(
            MediaAsset.id == asset_id, MediaAsset.tenant_id == self._tenant_id
        )
        if lock:
            statement = statement.with_for_update()
        asset = await self._session.scalar(statement)
        if asset is None:
            raise MediaNotFoundError("Media asset not found.")
        return asset

    async def get_public(self, asset_id: UUID) -> MediaAsset | None:
        return cast(
            MediaAsset | None,
            await self._session.scalar(
                select(MediaAsset).where(
                    MediaAsset.id == asset_id,
                    MediaAsset.tenant_id == self._tenant_id,
                    MediaAsset.public_use_status == "approved",
                    MediaAsset.visibility == "public",
                    MediaAsset.approved_at.is_not(None),
                )
            ),
        )

    async def update_metadata(
        self,
        *,
        asset_id: UUID,
        actor_id: UUID,
        expected_version: int,
        title: str,
        alt_text: str,
        caption: str | None,
    ) -> MediaAsset:
        asset = await self.get(asset_id, lock=True)
        self._check(asset, expected_version)
        if asset.public_use_status == "archived":
            raise MediaStateError("Archived media cannot be edited.")
        before = self.snapshot(asset)
        asset.title = title
        asset.alt_text = alt_text
        asset.caption = caption
        if asset.public_use_status in {"review", "approved", "revoked"}:
            asset.public_use_status = "uploaded"
            asset.visibility = "private"
            asset.approved_by = None
            asset.approved_at = None
            asset.revoked_by = None
            asset.revoked_at = None
        self._advance(asset)
        self._audit(asset, actor_id, "media.metadata_updated", before, self.snapshot(asset))
        return asset

    async def transition(
        self,
        *,
        asset_id: UUID,
        actor_id: UUID,
        expected_version: int,
        action: str,
    ) -> MediaAsset:
        asset = await self.get(asset_id, lock=True)
        self._check(asset, expected_version)
        before = self.snapshot(asset)
        now = datetime.now(UTC)
        if action == "submit_review":
            if asset.public_use_status not in {"uploaded", "revoked"}:
                raise MediaStateError("Only uploaded or revoked media can enter review.")
            asset.public_use_status = "review"
        elif action == "approve":
            if asset.public_use_status != "review":
                raise MediaStateError("Media must be in review before public approval.")
            if not asset.alt_text.strip() or not asset.title.strip():
                raise MediaStateError("Title and alt text are required for public approval.")
            asset.public_use_status = "approved"
            asset.visibility = "public"
            asset.approved_by = actor_id
            asset.approved_at = now
            asset.revoked_by = None
            asset.revoked_at = None
        elif action == "revoke":
            if asset.public_use_status != "approved":
                raise MediaStateError("Only approved public media can be revoked.")
            asset.public_use_status = "revoked"
            asset.visibility = "private"
            asset.revoked_by = actor_id
            asset.revoked_at = now
        elif action == "archive":
            if asset.public_use_status == "archived":
                raise MediaStateError("Media is already archived.")
            asset.public_use_status = "archived"
            asset.visibility = "private"
            asset.archived_by = actor_id
            asset.archived_at = now
        else:
            raise MediaStateError("Unsupported media governance action.")
        self._advance(asset)
        details = (
            {
                "self_approval": asset.uploaded_by == actor_id,
                "uploaded_by": str(asset.uploaded_by),
                "approved_by": str(actor_id),
            }
            if action == "approve"
            else None
        )
        self._audit(
            asset,
            actor_id,
            f"media.{action}",
            before,
            self.snapshot(asset),
            details,
        )
        return asset

    async def audit(self, asset_id: UUID) -> list[MediaAuditLog]:
        await self.get(asset_id)
        result = await self._session.scalars(
            select(MediaAuditLog)
            .where(
                MediaAuditLog.tenant_id == self._tenant_id,
                MediaAuditLog.media_asset_id == asset_id,
            )
            .order_by(MediaAuditLog.created_at.desc(), MediaAuditLog.id)
        )
        return list(result.all())

    @staticmethod
    def snapshot(asset: MediaAsset) -> dict[str, Any]:
        return {
            "title": asset.title,
            "alt_text": asset.alt_text,
            "caption": asset.caption,
            "visibility": asset.visibility,
            "public_use_status": asset.public_use_status,
            "record_version": asset.record_version,
        }

    def _audit(
        self,
        asset: MediaAsset,
        actor_id: UUID,
        action: str,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self._session.add(
            MediaAuditLog(
                tenant_id=self._tenant_id,
                media_asset_id=asset.id,
                actor_membership_id=actor_id,
                action=action,
                before_metadata=before or {},
                after_metadata=after or {},
                details=details or {},
                correlation_id=get_correlation_id(),
            )
        )

    @staticmethod
    def _advance(asset: MediaAsset) -> None:
        asset.record_version += 1
        asset.updated_at = datetime.now(UTC)

    @staticmethod
    def _check(asset: MediaAsset, expected: int) -> None:
        if asset.record_version != expected:
            raise MediaConcurrencyError("Media asset changed; refresh and retry.")
