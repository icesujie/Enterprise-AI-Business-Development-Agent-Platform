from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import (
    PublicContentAuditLog,
    PublicContentDecision,
    PublicContentItem,
    PublicContentVersion,
)
from sari_api.core.observability import get_correlation_id


class PublicContentNotFoundError(Exception):
    pass


class PublicContentStateError(Exception):
    pass


class PublicContentConcurrencyError(Exception):
    pass


class PublicContentSeparationOfDutiesError(Exception):
    pass


def public_content_checksum(
    *,
    title: str,
    summary: str,
    seo_title: str,
    seo_description: str,
    structured_content: dict[str, Any],
    media_references: list[dict[str, Any]],
    source_type: str,
    source_reference_id: UUID | None,
    source_filename: str | None,
    source_checksum: str | None,
) -> str:
    canonical = json.dumps(
        {
            "media_references": media_references,
            "seo_description": seo_description,
            "seo_title": seo_title,
            "source_checksum": source_checksum,
            "source_filename": source_filename,
            "source_reference_id": str(source_reference_id) if source_reference_id else None,
            "source_type": source_type,
            "structured_content": structured_content,
            "summary": summary,
            "title": title,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


class PublicContentRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def create_item(
        self,
        *,
        actor_id: UUID,
        item_values: dict[str, Any],
        version_values: dict[str, Any],
    ) -> tuple[PublicContentItem, PublicContentVersion]:
        item = PublicContentItem(
            tenant_id=self._tenant_id,
            created_by=actor_id,
            **item_values,
        )
        self._session.add(item)
        await self._session.flush()
        version = self._new_version(
            item=item,
            actor_id=actor_id,
            version_number=1,
            origin="human",
            based_on_version_id=None,
            values=version_values,
        )
        self._session.add(version)
        await self._session.flush()
        item.current_version_id = version.id
        self._audit(
            actor_id=actor_id,
            action="public_content.created",
            item=item,
            version=version,
            after=self._item_state(item),
        )
        await self._session.flush()
        await self._session.refresh(item)
        return item, version

    async def list_items(
        self,
        *,
        status: str | None = None,
        page_type: str | None = None,
        locale: str | None = None,
        search: str | None = None,
    ) -> list[PublicContentItem]:
        statement = select(PublicContentItem).where(PublicContentItem.tenant_id == self._tenant_id)
        if status:
            statement = statement.where(PublicContentItem.status == status)
        if page_type:
            statement = statement.where(PublicContentItem.page_type == page_type)
        if locale:
            statement = statement.where(PublicContentItem.locale == locale)
        if search:
            pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    PublicContentItem.title.ilike(pattern),
                    PublicContentItem.slug.ilike(pattern),
                    PublicContentItem.summary.ilike(pattern),
                )
            )
        result = await self._session.scalars(
            statement.order_by(PublicContentItem.updated_at.desc(), PublicContentItem.id)
        )
        return list(result.all())

    async def get_item(self, item_id: UUID, *, lock: bool = False) -> PublicContentItem:
        statement = select(PublicContentItem).where(
            PublicContentItem.id == item_id,
            PublicContentItem.tenant_id == self._tenant_id,
        )
        if lock:
            statement = statement.with_for_update()
        item = await self._session.scalar(statement)
        if item is None:
            raise PublicContentNotFoundError("Public content item not found.")
        return item

    async def get_version(
        self, item_id: UUID, version_id: UUID | None
    ) -> PublicContentVersion | None:
        if version_id is None:
            return None
        return cast(
            PublicContentVersion | None,
            await self._session.scalar(
                select(PublicContentVersion).where(
                    PublicContentVersion.id == version_id,
                    PublicContentVersion.public_content_item_id == item_id,
                    PublicContentVersion.tenant_id == self._tenant_id,
                )
            ),
        )

    async def get_published_page(
        self,
        *,
        page_type: str,
        slug: str,
        locale: str,
    ) -> tuple[PublicContentItem, PublicContentVersion] | None:
        row = (
            await self._session.execute(
                select(PublicContentItem, PublicContentVersion)
                .join(
                    PublicContentVersion,
                    PublicContentVersion.id == PublicContentItem.published_version_id,
                )
                .where(
                    PublicContentItem.tenant_id == self._tenant_id,
                    PublicContentItem.page_type == page_type,
                    PublicContentItem.slug == slug,
                    PublicContentItem.locale == locale,
                    PublicContentItem.status != "archived",
                    PublicContentItem.published_at.is_not(None),
                    PublicContentVersion.tenant_id == self._tenant_id,
                    PublicContentVersion.public_content_item_id == PublicContentItem.id,
                )
            )
        ).one_or_none()
        return (row[0], row[1]) if row else None

    async def get_published_relation(
        self,
        *,
        locale: str,
        item_id: UUID | None = None,
        canonical_path: str | None = None,
    ) -> PublicContentItem | None:
        if item_id is None and canonical_path is None:
            return None
        statement = (
            select(PublicContentItem)
            .join(
                PublicContentVersion,
                PublicContentVersion.id == PublicContentItem.published_version_id,
            )
            .where(
                PublicContentItem.tenant_id == self._tenant_id,
                PublicContentItem.locale == locale,
                PublicContentItem.status != "archived",
                PublicContentItem.published_at.is_not(None),
                PublicContentVersion.tenant_id == self._tenant_id,
                PublicContentVersion.public_content_item_id == PublicContentItem.id,
            )
        )
        if item_id is not None:
            statement = statement.where(PublicContentItem.id == item_id)
        if canonical_path is not None:
            statement = statement.where(PublicContentItem.canonical_path == canonical_path)
        return cast(PublicContentItem | None, await self._session.scalar(statement))

    async def has_governed_path(self, *, locale: str, canonical_path: str) -> bool:
        return bool(
            await self._session.scalar(
                select(PublicContentItem.id).where(
                    PublicContentItem.tenant_id == self._tenant_id,
                    PublicContentItem.locale == locale,
                    PublicContentItem.canonical_path == canonical_path,
                )
            )
        )

    async def list_versions(self, item_id: UUID) -> list[PublicContentVersion]:
        await self.get_item(item_id)
        versions = await self._session.scalars(
            select(PublicContentVersion)
            .where(
                PublicContentVersion.public_content_item_id == item_id,
                PublicContentVersion.tenant_id == self._tenant_id,
            )
            .order_by(PublicContentVersion.version_number.desc())
        )
        return list(versions.all())

    async def list_decisions(self, item_id: UUID) -> list[PublicContentDecision]:
        await self.get_item(item_id)
        decisions = await self._session.scalars(
            select(PublicContentDecision)
            .where(
                PublicContentDecision.public_content_item_id == item_id,
                PublicContentDecision.tenant_id == self._tenant_id,
            )
            .order_by(PublicContentDecision.created_at.desc(), PublicContentDecision.id.desc())
        )
        return list(decisions.all())

    async def list_audit(self, item_id: UUID) -> list[PublicContentAuditLog]:
        await self.get_item(item_id)
        entries = await self._session.scalars(
            select(PublicContentAuditLog)
            .where(
                PublicContentAuditLog.public_content_item_id == item_id,
                PublicContentAuditLog.tenant_id == self._tenant_id,
            )
            .order_by(PublicContentAuditLog.created_at.desc(), PublicContentAuditLog.id.desc())
        )
        return list(entries.all())

    async def create_successor(
        self,
        *,
        item_id: UUID,
        expected_record_version: int,
        actor_id: UUID,
        values: dict[str, Any],
    ) -> tuple[PublicContentItem, PublicContentVersion]:
        item = await self.get_item(item_id, lock=True)
        self._check_record_version(item, expected_record_version)
        if item.status == "archived":
            raise PublicContentStateError("Archived public content cannot be edited.")
        current = await self._required_version(item, item.current_version_id)
        before = self._item_state(item)
        version = self._new_version(
            item=item,
            actor_id=actor_id,
            version_number=current.version_number + 1,
            origin="human",
            based_on_version_id=current.id,
            values=values,
        )
        self._session.add(version)
        await self._session.flush()
        item.current_version_id = version.id
        item.approved_version_id = None
        item.approved_by = None
        item.title = version.title
        item.summary = version.summary
        item.seo_title = version.seo_title
        item.seo_description = version.seo_description
        item.status = "draft"
        self._advance(item)
        self._audit(
            actor_id=actor_id,
            action="public_content.version_created",
            item=item,
            version=version,
            before=before,
            after=self._item_state(item),
            details={"based_on_version_id": str(current.id)},
        )
        await self._session.flush()
        return item, version

    async def submit_review(
        self,
        *,
        item_id: UUID,
        version_id: UUID,
        checksum: str,
        expected_record_version: int,
        actor_id: UUID,
        comment: str | None,
    ) -> tuple[PublicContentItem, PublicContentDecision]:
        item = await self.get_item(item_id, lock=True)
        self._check_record_version(item, expected_record_version)
        if item.status != "draft":
            raise PublicContentStateError("Only draft public content can enter review.")
        version = await self._exact_current_version(item, version_id, checksum)
        decision = self._decision(item, version, "submitted", actor_id, comment)
        self._session.add(decision)
        before = self._item_state(item)
        item.status = "review"
        self._advance(item)
        self._audit(
            actor_id=actor_id,
            action="public_content.review_submitted",
            item=item,
            version=version,
            before=before,
            after=self._item_state(item),
        )
        await self._session.flush()
        return item, decision

    async def decide(
        self,
        *,
        item_id: UUID,
        version_id: UUID,
        checksum: str,
        decision_type: str,
        expected_record_version: int,
        actor_id: UUID,
        comment: str | None,
    ) -> tuple[PublicContentItem, PublicContentDecision]:
        item = await self.get_item(item_id, lock=True)
        self._check_record_version(item, expected_record_version)
        if item.status != "review":
            raise PublicContentStateError("Public content is not in review.")
        version = await self._exact_current_version(item, version_id, checksum)
        if decision_type == "approved" and version.created_by == actor_id:
            raise PublicContentSeparationOfDutiesError(
                "The version creator cannot approve their own public content."
            )
        if decision_type not in {"changes_requested", "approved", "rejected"}:
            raise PublicContentStateError("Unsupported public content decision.")
        before = self._item_state(item)
        decision = self._decision(item, version, decision_type, actor_id, comment)
        self._session.add(decision)
        if decision_type == "approved":
            item.status = "approved"
            item.approved_version_id = version.id
            item.approved_by = actor_id
        else:
            item.status = "draft"
            item.approved_version_id = None
            item.approved_by = None
        self._advance(item)
        self._audit(
            actor_id=actor_id,
            action=f"public_content.{decision_type}",
            item=item,
            version=version,
            before=before,
            after=self._item_state(item),
        )
        await self._session.flush()
        return item, decision

    async def publish(
        self,
        *,
        item_id: UUID,
        version_id: UUID,
        checksum: str,
        expected_record_version: int,
        actor_id: UUID,
        comment: str | None,
    ) -> tuple[PublicContentItem, PublicContentDecision]:
        item = await self.get_item(item_id, lock=True)
        self._check_record_version(item, expected_record_version)
        if item.is_synthetic:
            raise PublicContentStateError("Synthetic public content cannot be published.")
        if item.status != "approved" or item.approved_version_id != version_id:
            raise PublicContentStateError("Only the exact approved version can be published.")
        version = await self._exact_current_version(item, version_id, checksum)
        before = self._item_state(item)
        decision = self._decision(item, version, "published", actor_id, comment)
        self._session.add(decision)
        item.status = "published"
        item.published_version_id = version.id
        item.published_by = actor_id
        item.published_at = datetime.now(UTC)
        self._advance(item)
        self._audit(
            actor_id=actor_id,
            action="public_content.published",
            item=item,
            version=version,
            before=before,
            after=self._item_state(item),
        )
        await self._session.flush()
        return item, decision

    async def archive(
        self,
        *,
        item_id: UUID,
        expected_record_version: int,
        actor_id: UUID,
        reason: str,
    ) -> PublicContentItem:
        item = await self.get_item(item_id, lock=True)
        self._check_record_version(item, expected_record_version)
        if item.status == "archived":
            raise PublicContentStateError("Public content is already archived.")
        before = self._item_state(item)
        item.status = "archived"
        item.archived_at = datetime.now(UTC)
        item.archived_by = actor_id
        item.archive_reason = reason
        self._advance(item)
        self._audit(
            actor_id=actor_id,
            action="public_content.archived",
            item=item,
            version=await self.get_version(item.id, item.current_version_id),
            before=before,
            after=self._item_state(item),
            details={"reason": reason},
        )
        await self._session.flush()
        return item

    async def restore(
        self,
        *,
        item_id: UUID,
        expected_record_version: int,
        actor_id: UUID,
        reason: str,
    ) -> PublicContentItem:
        item = await self.get_item(item_id, lock=True)
        self._check_record_version(item, expected_record_version)
        if item.status != "archived":
            raise PublicContentStateError("Only archived public content can be restored.")
        before = self._item_state(item)
        item.status = "published" if item.published_version_id else "draft"
        item.archived_at = None
        item.archived_by = None
        item.archive_reason = None
        self._advance(item)
        self._audit(
            actor_id=actor_id,
            action="public_content.restored",
            item=item,
            version=await self.get_version(item.id, item.current_version_id),
            before=before,
            after=self._item_state(item),
            details={"reason": reason},
        )
        await self._session.flush()
        return item

    def _new_version(
        self,
        *,
        item: PublicContentItem,
        actor_id: UUID,
        version_number: int,
        origin: str,
        based_on_version_id: UUID | None,
        values: dict[str, Any],
    ) -> PublicContentVersion:
        checksum = public_content_checksum(**values)
        return PublicContentVersion(
            tenant_id=self._tenant_id,
            public_content_item_id=item.id,
            version_number=version_number,
            origin=origin,
            based_on_version_id=based_on_version_id,
            created_by=actor_id,
            content_sha256=checksum,
            **values,
        )

    async def _required_version(
        self, item: PublicContentItem, version_id: UUID | None
    ) -> PublicContentVersion:
        version = await self.get_version(item.id, version_id)
        if version is None:
            raise PublicContentStateError("Public content version is missing.")
        return version

    async def _exact_current_version(
        self, item: PublicContentItem, version_id: UUID, checksum: str
    ) -> PublicContentVersion:
        if item.current_version_id != version_id:
            raise PublicContentStateError("The command must reference the exact current version.")
        version = await self._required_version(item, version_id)
        if version.content_sha256 != checksum:
            raise PublicContentStateError("Public content checksum does not match.")
        return version

    @staticmethod
    def _check_record_version(item: PublicContentItem, expected: int) -> None:
        if item.record_version != expected:
            raise PublicContentConcurrencyError("Public content changed; reload and retry.")

    @staticmethod
    def _advance(item: PublicContentItem) -> None:
        item.record_version += 1
        item.updated_at = datetime.now(UTC)

    def _decision(
        self,
        item: PublicContentItem,
        version: PublicContentVersion,
        decision_type: str,
        actor_id: UUID,
        comment: str | None,
    ) -> PublicContentDecision:
        return PublicContentDecision(
            tenant_id=self._tenant_id,
            public_content_item_id=item.id,
            public_content_version_id=version.id,
            decision_type=decision_type,
            decided_by=actor_id,
            content_sha256=version.content_sha256,
            comment=comment,
        )

    def _audit(
        self,
        *,
        actor_id: UUID,
        action: str,
        item: PublicContentItem,
        version: PublicContentVersion | None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self._session.add(
            PublicContentAuditLog(
                tenant_id=self._tenant_id,
                actor_membership_id=actor_id,
                action=action,
                public_content_item_id=item.id,
                public_content_version_id=version.id if version else None,
                before_metadata=before or {},
                after_metadata=after or {},
                details=details or {},
                correlation_id=get_correlation_id(),
            )
        )

    @staticmethod
    def _item_state(item: PublicContentItem) -> dict[str, Any]:
        return {
            "approved_version_id": str(item.approved_version_id)
            if item.approved_version_id
            else None,
            "current_version_id": str(item.current_version_id) if item.current_version_id else None,
            "published_version_id": str(item.published_version_id)
            if item.published_version_id
            else None,
            "record_version": item.record_version,
            "status": item.status,
        }
