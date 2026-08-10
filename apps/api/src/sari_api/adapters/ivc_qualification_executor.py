from __future__ import annotations

import logging
import math
from datetime import UTC, datetime
from uuid import UUID

from sari_api.adapters.database import session_factory
from sari_api.adapters.ivc_qualification_provider import IvcQualificationProvider
from sari_api.adapters.ivc_qualification_repository import (
    SqlAlchemyIvcQualificationRepository,
)
from sari_api.adapters.qualification_executor import RetrySchedule
from sari_api.core.observability import reset_correlation_id, set_correlation_id
from sari_api.domain.ivc_qualification import IvcQualificationInput
from sari_api.domain.packages.models import SupportedLocale

logger = logging.getLogger(__name__)


class IvcQualificationRunExecutor:
    def __init__(self, provider: IvcQualificationProvider, retry_base_seconds: int = 2) -> None:
        self._provider = provider
        self._retry_base_seconds = retry_base_seconds

    async def execute(self, run_id: UUID, tenant_id: UUID) -> RetrySchedule | None:
        async with session_factory() as session:
            repo = SqlAlchemyIvcQualificationRepository(session, tenant_id)
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
                input_data = IvcQualificationInput.model_validate(
                    run.input_snapshot["project_snapshot"]
                )
                response_locale: SupportedLocale = run.input_snapshot["response_locale"]
                attempt_count = run.attempt_count
                max_attempts = run.max_attempts
                await session.commit()
            finally:
                reset_correlation_id(token)

        token = set_correlation_id(run.correlation_id or str(run.id))
        try:
            logger.info(
                "IVC Agent Run attempt started",
                extra={
                    "event": "ivc_agent.run.attempt_started",
                    "agent_run_id": str(run_id),
                    "tenant_id": str(tenant_id),
                    "attempt_count": attempt_count,
                    "max_attempts": max_attempts,
                    "response_locale": response_locale,
                },
            )
            try:
                output = await self._provider.qualify(input_data, response_locale)
            except Exception:
                logger.exception(
                    "IVC Agent provider call failed",
                    extra={
                        "event": "ivc_agent.provider.failed",
                        "agent_run_id": str(run_id),
                        "tenant_id": str(tenant_id),
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
                repo = SqlAlchemyIvcQualificationRepository(session, tenant_id)
                await repo.set_tenant_context()
                current = await repo.get_run(run_id, for_update=True)
                if current.status != "running":
                    return None
                await repo.complete_run(current, output)
                await session.commit()
            logger.info(
                "IVC Agent Run succeeded",
                extra={
                    "event": "ivc_agent.run.succeeded",
                    "agent_run_id": str(run_id),
                    "tenant_id": str(tenant_id),
                },
            )
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
            repo = SqlAlchemyIvcQualificationRepository(session, tenant_id)
            await repo.set_tenant_context()
            run = await repo.get_run(run_id, for_update=True)
            if run.status != "running":
                return None
            if attempt_count < max_attempts:
                delay = self._retry_base_seconds * (2 ** (attempt_count - 1))
                await repo.schedule_retry(
                    run,
                    "provider_unavailable",
                    "IVC qualification is temporarily unavailable. Automatic retry scheduled.",
                    delay,
                )
                await session.commit()
                return RetrySchedule(delay, correlation_id)
            await repo.fail_run(
                run,
                "provider_unavailable",
                "IVC qualification is unavailable after bounded retries. Try again later.",
            )
            await session.commit()
        return None

    async def fail_scheduled_retry(self, run_id: UUID, tenant_id: UUID) -> None:
        async with session_factory() as session:
            repo = SqlAlchemyIvcQualificationRepository(session, tenant_id)
            await repo.set_tenant_context()
            run = await repo.get_run(run_id, for_update=True)
            if run.status == "queued":
                await repo.fail_run(
                    run,
                    "queue_unavailable",
                    "Automatic retry could not be queued. Retry manually later.",
                )
                await session.commit()
