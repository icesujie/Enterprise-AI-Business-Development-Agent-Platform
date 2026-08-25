from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import PublicContentStructuringRun


class PublicContentStructuringRunNotFoundError(Exception):
    pass


class PublicContentStructuringRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def create_run(
        self,
        *,
        import_id: UUID,
        requested_by: UUID,
        selected_page_type: str,
        provider: str,
        model: str,
        locale: str,
        correlation_id: str | None,
    ) -> PublicContentStructuringRun:
        run = PublicContentStructuringRun(
            tenant_id=self._tenant_id,
            public_content_import_id=import_id,
            requested_by=requested_by,
            selected_page_type=selected_page_type,
            provider=provider,
            model=model,
            locale=locale,
            status="running",
            correlation_id=correlation_id,
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def complete(
        self,
        run_id: UUID,
        *,
        recommended_page_type: str,
        outcome: str,
        result: dict[str, object],
        missing_fields: list[str],
        duration_ms: int,
    ) -> PublicContentStructuringRun:
        run = await self.get(run_id, lock=True)
        run.recommended_page_type = recommended_page_type
        run.outcome = outcome
        run.result = result
        run.missing_fields = missing_fields
        run.duration_ms = duration_ms
        run.status = "completed"
        run.completed_at = datetime.now(UTC)
        return run

    async def fail(
        self, run_id: UUID, *, reason: str, duration_ms: int
    ) -> PublicContentStructuringRun:
        run = await self.get(run_id, lock=True)
        run.status = "failed"
        run.failure_reason = reason[:500]
        run.duration_ms = duration_ms
        run.completed_at = datetime.now(UTC)
        return run

    async def list_for_import(self, import_id: UUID) -> list[PublicContentStructuringRun]:
        result = await self._session.scalars(
            select(PublicContentStructuringRun)
            .where(
                PublicContentStructuringRun.tenant_id == self._tenant_id,
                PublicContentStructuringRun.public_content_import_id == import_id,
            )
            .order_by(
                PublicContentStructuringRun.created_at.desc(),
                PublicContentStructuringRun.id.desc(),
            )
        )
        return list(result.all())

    async def get(self, run_id: UUID, *, lock: bool = False) -> PublicContentStructuringRun:
        statement = select(PublicContentStructuringRun).where(
            PublicContentStructuringRun.id == run_id,
            PublicContentStructuringRun.tenant_id == self._tenant_id,
        )
        if lock:
            statement = statement.with_for_update()
        run = await self._session.scalar(statement)
        if run is None:
            raise PublicContentStructuringRunNotFoundError("Structuring run not found.")
        return run
