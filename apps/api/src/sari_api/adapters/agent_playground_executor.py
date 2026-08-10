from __future__ import annotations

import logging
import math
from datetime import UTC, datetime
from uuid import UUID

from sari_api.adapters.agent_playground_provider import AgentPlaygroundProvider
from sari_api.adapters.agent_playground_repository import SqlAlchemyAgentPlaygroundRepository
from sari_api.adapters.database import session_factory
from sari_api.adapters.qualification_executor import RetrySchedule
from sari_api.core.observability import reset_correlation_id, set_correlation_id
from sari_api.domain.agent_playground import PlaygroundQualificationRequest

logger = logging.getLogger(__name__)


class AgentPlaygroundRunExecutor:
    def __init__(self, provider: AgentPlaygroundProvider, retry_base_seconds: int = 2) -> None:
        self._provider = provider
        self._retry_base_seconds = retry_base_seconds

    async def execute(self, run_id: UUID, tenant_id: UUID) -> RetrySchedule | None:
        async with session_factory() as session:
            repo = SqlAlchemyAgentPlaygroundRepository(session, tenant_id)
            await repo.set_tenant_context()
            run = await repo.get_run(run_id, for_update=True)
            token = set_correlation_id(run.correlation_id or str(run.id))
            try:
                if run.status != "queued":
                    return None
                if run.next_retry_at and run.next_retry_at > datetime.now(UTC):
                    remaining = math.ceil((run.next_retry_at - datetime.now(UTC)).total_seconds())
                    return RetrySchedule(max(remaining, 1), run.correlation_id)
                await repo.start_run(run, self._provider.provider_type, self._provider.model_id)
                request = PlaygroundQualificationRequest.model_validate(run.input_snapshot)
                attempt_count = run.attempt_count
                max_attempts = run.max_attempts
                await session.commit()
            finally:
                reset_correlation_id(token)

        token = set_correlation_id(run.correlation_id or str(run.id))
        try:
            logger.info(
                "Agent Playground attempt started",
                extra={
                    "event": "agent_playground.run.attempt_started",
                    "agent_run_id": str(run_id),
                    "tenant_id": str(tenant_id),
                    "domain": request.domain,
                    "response_locale": request.response_locale,
                },
            )
            try:
                output = await self._provider.qualify(request)
            except Exception:
                logger.exception(
                    "Agent Playground provider call failed",
                    extra={
                        "event": "agent_playground.provider.failed",
                        "agent_run_id": str(run_id),
                        "tenant_id": str(tenant_id),
                        "domain": request.domain,
                    },
                )
                return await self._handle_failure(
                    run_id,
                    tenant_id,
                    attempt_count,
                    max_attempts,
                    run.correlation_id,
                )

            async with session_factory() as session:
                repo = SqlAlchemyAgentPlaygroundRepository(session, tenant_id)
                await repo.set_tenant_context()
                current = await repo.get_run(run_id, for_update=True)
                if current.status != "running":
                    return None
                await repo.complete_run(current, output)
                await session.commit()
            return None
        finally:
            reset_correlation_id(token)

    async def _handle_failure(
        self,
        run_id: UUID,
        tenant_id: UUID,
        attempt_count: int,
        max_attempts: int,
        correlation_id: str | None,
    ) -> RetrySchedule | None:
        async with session_factory() as session:
            repo = SqlAlchemyAgentPlaygroundRepository(session, tenant_id)
            await repo.set_tenant_context()
            run = await repo.get_run(run_id, for_update=True)
            if run.status != "running":
                return None
            if attempt_count < max_attempts:
                delay = self._retry_base_seconds * (2 ** (attempt_count - 1))
                await repo.schedule_retry(
                    run,
                    "provider_unavailable",
                    "Agent Playground is temporarily unavailable. Automatic retry scheduled.",
                    delay,
                )
                await session.commit()
                return RetrySchedule(delay, correlation_id)
            await repo.fail_run(
                run,
                "provider_unavailable",
                "Agent Playground is unavailable after bounded retries. Try again later.",
            )
            await session.commit()
        return None

    async def fail_scheduled_retry(self, run_id: UUID, tenant_id: UUID) -> None:
        async with session_factory() as session:
            repo = SqlAlchemyAgentPlaygroundRepository(session, tenant_id)
            await repo.set_tenant_context()
            run = await repo.get_run(run_id, for_update=True)
            if run.status == "queued":
                await repo.fail_run(
                    run,
                    "queue_unavailable",
                    "Automatic retry could not be queued. Retry manually later.",
                )
                await session.commit()
