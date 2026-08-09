from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sari_api.adapters.database import session_factory
from sari_api.adapters.qualification_provider import QualificationProvider
from sari_api.adapters.qualification_repository import SqlAlchemyQualificationRepository
from sari_api.core.observability import reset_correlation_id, set_correlation_id

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetrySchedule:
    delay_seconds: int
    correlation_id: str | None


class QualificationRunExecutor:
    def __init__(self, provider: QualificationProvider, retry_base_seconds: int = 2) -> None:
        self._provider = provider
        self._retry_base_seconds = retry_base_seconds

    async def execute(self, run_id: UUID, tenant_id: UUID) -> RetrySchedule | None:
        async with session_factory() as session:
            repo = SqlAlchemyQualificationRepository(session, tenant_id)
            await repo.set_tenant_context()
            run = await repo.get_run(run_id, for_update=True)
            correlation_token = set_correlation_id(run.correlation_id or str(run.id))
            try:
                if run.status != "queued":
                    return None
                if run.next_retry_at and run.next_retry_at > datetime.now(UTC):
                    remaining = math.ceil((run.next_retry_at - datetime.now(UTC)).total_seconds())
                    return RetrySchedule(max(remaining, 1), run.correlation_id)
                await repo.start_run(run, self._provider.provider_type, self._provider.model_id)
                snapshot = run.input_snapshot
                attempt_count = run.attempt_count
                max_attempts = run.max_attempts
                await session.commit()
            finally:
                reset_correlation_id(correlation_token)

        correlation_token = set_correlation_id(run.correlation_id or str(run.id))
        try:
            logger.info(
                "Agent run attempt started",
                extra={
                    "event": "agent.run.attempt_started",
                    "agent_run_id": str(run_id),
                    "tenant_id": str(tenant_id),
                    "attempt_count": attempt_count,
                    "max_attempts": max_attempts,
                },
            )
            try:
                output = await self._provider.qualify(snapshot)
            except Exception:
                logger.exception(
                    "Agent provider call failed",
                    extra={
                        "event": "agent.provider.failed",
                        "agent_run_id": str(run_id),
                        "tenant_id": str(tenant_id),
                        "attempt_count": attempt_count,
                        "max_attempts": max_attempts,
                    },
                )
                return await self._handle_provider_failure(
                    run_id,
                    tenant_id,
                    attempt_count,
                    max_attempts,
                    run.correlation_id,
                )

            async with session_factory() as session:
                repo = SqlAlchemyQualificationRepository(session, tenant_id)
                await repo.set_tenant_context()
                current_run = await repo.get_run(run_id, for_update=True)
                if current_run.status != "running":
                    return None
                await repo.complete_run(current_run, output)
                await session.commit()
            logger.info(
                "Agent run succeeded",
                extra={
                    "event": "agent.run.succeeded",
                    "agent_run_id": str(run_id),
                    "tenant_id": str(tenant_id),
                    "attempt_count": attempt_count,
                    "max_attempts": max_attempts,
                },
            )
            return None
        finally:
            reset_correlation_id(correlation_token)

    async def _handle_provider_failure(
        self,
        run_id: UUID,
        tenant_id: UUID,
        attempt_count: int,
        max_attempts: int,
        correlation_id: str | None,
    ) -> RetrySchedule | None:
        async with session_factory() as session:
            repo = SqlAlchemyQualificationRepository(session, tenant_id)
            await repo.set_tenant_context()
            run = await repo.get_run(run_id, for_update=True)
            if run.status != "running":
                return None
            if attempt_count < max_attempts:
                delay_seconds = self._retry_base_seconds * (2 ** (attempt_count - 1))
                await repo.schedule_retry(
                    run,
                    "provider_unavailable",
                    "AI qualification is temporarily unavailable. Automatic retry scheduled.",
                    delay_seconds,
                )
                await session.commit()
                logger.warning(
                    "Agent run retry scheduled",
                    extra={
                        "event": "agent.run.retry_scheduled",
                        "agent_run_id": str(run_id),
                        "tenant_id": str(tenant_id),
                        "attempt_count": attempt_count,
                        "max_attempts": max_attempts,
                        "retry_delay_seconds": delay_seconds,
                    },
                )
                return RetrySchedule(delay_seconds, correlation_id)

            await repo.fail_run(
                run,
                "provider_unavailable",
                "AI qualification is unavailable after bounded retries. Try again later.",
            )
            await session.commit()
        logger.error(
            "Agent run failed after bounded retries",
            extra={
                "event": "agent.run.failed",
                "agent_run_id": str(run_id),
                "tenant_id": str(tenant_id),
                "attempt_count": attempt_count,
                "max_attempts": max_attempts,
            },
        )
        return None

    async def fail_scheduled_retry(self, run_id: UUID, tenant_id: UUID) -> None:
        async with session_factory() as session:
            repo = SqlAlchemyQualificationRepository(session, tenant_id)
            await repo.set_tenant_context()
            run = await repo.get_run(run_id, for_update=True)
            if run.status == "queued":
                await repo.fail_run(
                    run,
                    "queue_unavailable",
                    "Automatic retry could not be queued. Retry manually later.",
                )
                await session.commit()
