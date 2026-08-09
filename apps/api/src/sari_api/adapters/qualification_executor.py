from __future__ import annotations

from uuid import UUID

from sari_api.adapters.database import session_factory
from sari_api.adapters.qualification_provider import QualificationProvider
from sari_api.adapters.qualification_repository import SqlAlchemyQualificationRepository


class QualificationRunExecutor:
    def __init__(self, provider: QualificationProvider) -> None:
        self._provider = provider

    async def execute(self, run_id: UUID, tenant_id: UUID) -> None:
        async with session_factory() as session:
            repo = SqlAlchemyQualificationRepository(session, tenant_id)
            await repo.set_tenant_context()
            run = await repo.get_run(run_id, for_update=True)
            if run.status != "queued":
                return
            await repo.start_run(run, self._provider.provider_type, self._provider.model_id)
            snapshot = run.input_snapshot
            await session.commit()

        try:
            output = await self._provider.qualify(snapshot)
        except Exception as exc:
            async with session_factory() as session:
                repo = SqlAlchemyQualificationRepository(session, tenant_id)
                await repo.set_tenant_context()
                run = await repo.get_run(run_id, for_update=True)
                await repo.fail_run(
                    run,
                    type(exc).__name__,
                    "AI qualification is unavailable. Retry later.",
                )
                await session.commit()
            return

        async with session_factory() as session:
            repo = SqlAlchemyQualificationRepository(session, tenant_id)
            await repo.set_tenant_context()
            run = await repo.get_run(run_id, for_update=True)
            await repo.complete_run(run, output)
            await session.commit()
