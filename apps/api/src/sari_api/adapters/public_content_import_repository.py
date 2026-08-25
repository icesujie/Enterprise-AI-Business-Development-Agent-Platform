from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import PublicContentImport, PublicContentImportAuditLog
from sari_api.core.observability import get_correlation_id


class PublicContentImportNotFoundError(Exception):
    pass


class PublicContentImportRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def create(self, *, actor_id: UUID, **values: Any) -> PublicContentImport:
        record = PublicContentImport(
            tenant_id=self._tenant_id,
            requested_by=actor_id,
            processing_status="uploaded",
            **values,
        )
        self._session.add(record)
        await self._session.flush()
        self._audit(record, actor_id, "public_content_import.uploaded")
        return record

    async def mark_processing(
        self, import_id: UUID, *, actor_id: UUID
    ) -> PublicContentImport:
        record = await self.get(import_id, lock=True)
        record.processing_status = "processing"
        record.started_at = datetime.now(UTC)
        record.failure_reason = None
        self._audit(record, actor_id, "public_content_import.processing")
        return record

    async def mark_completed(
        self,
        import_id: UUID,
        *,
        actor_id: UUID,
        extraction_metadata: dict[str, object],
        extraction_result: dict[str, object],
        extracted_media_ids: list[str],
    ) -> PublicContentImport:
        record = await self.get(import_id, lock=True)
        record.processing_status = "completed"
        record.extraction_metadata = extraction_metadata
        record.extraction_result = extraction_result
        record.extracted_media_ids = extracted_media_ids
        record.completed_at = datetime.now(UTC)
        blocks = extraction_result.get("blocks")
        self._audit(
            record,
            actor_id,
            "public_content_import.completed",
            {
                "block_count": len(blocks) if isinstance(blocks, list) else 0,
                "media_count": len(extracted_media_ids),
            },
        )
        return record

    async def mark_failed(
        self,
        import_id: UUID,
        *,
        actor_id: UUID,
        reason: str,
        metadata: dict[str, object] | None = None,
    ) -> PublicContentImport:
        record = await self.get(import_id, lock=True)
        record.processing_status = "failed"
        record.failure_reason = reason[:500]
        record.extraction_metadata = metadata or {}
        record.extraction_result = {}
        record.extracted_media_ids = []
        record.completed_at = datetime.now(UTC)
        self._audit(
            record,
            actor_id,
            "public_content_import.failed",
            {"failure_code": (metadata or {}).get("failure_code", "extraction_failed")},
        )
        return record

    async def list_imports(self) -> list[PublicContentImport]:
        result = await self._session.scalars(
            select(PublicContentImport)
            .where(PublicContentImport.tenant_id == self._tenant_id)
            .order_by(PublicContentImport.created_at.desc(), PublicContentImport.id)
        )
        return list(result.all())

    async def get(self, import_id: UUID, *, lock: bool = False) -> PublicContentImport:
        statement = select(PublicContentImport).where(
            PublicContentImport.id == import_id,
            PublicContentImport.tenant_id == self._tenant_id,
        )
        if lock:
            statement = statement.with_for_update()
        record = await self._session.scalar(statement)
        if record is None:
            raise PublicContentImportNotFoundError("Document import not found.")
        return record

    def _audit(
        self,
        record: PublicContentImport,
        actor_id: UUID,
        action: str,
        details: dict[str, object] | None = None,
    ) -> None:
        self._session.add(
            PublicContentImportAuditLog(
                tenant_id=self._tenant_id,
                public_content_import_id=record.id,
                actor_membership_id=actor_id,
                action=action,
                details=details or {},
                correlation_id=get_correlation_id(),
            )
        )
