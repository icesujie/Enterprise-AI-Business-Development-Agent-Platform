from __future__ import annotations

import asyncio
import logging
import time
from typing import Protocol
from uuid import UUID

from sqlalchemy import select, text

from sari_api.adapters.agent_playground_executor import AgentPlaygroundRunExecutor
from sari_api.adapters.agent_playground_provider import build_agent_playground_provider
from sari_api.adapters.agent_queue import (
    InvalidAgentQueueMessageError,
    RedisAgentQueue,
)
from sari_api.adapters.agent_recovery import AgentRunRecoveryService
from sari_api.adapters.database import dispose_database, session_factory
from sari_api.adapters.ivc_qualification_executor import IvcQualificationRunExecutor
from sari_api.adapters.ivc_qualification_provider import build_ivc_qualification_provider
from sari_api.adapters.models import AgentRun
from sari_api.adapters.qualification_executor import QualificationRunExecutor, RetrySchedule
from sari_api.adapters.qualification_provider import build_qualification_provider
from sari_api.core.config import get_settings
from sari_api.core.observability import (
    configure_logging,
    reset_correlation_id,
    set_correlation_id,
)

logger = logging.getLogger(__name__)


class RunnableAgentExecutor(Protocol):
    async def execute(self, run_id: UUID, tenant_id: UUID) -> RetrySchedule | None: ...

    async def fail_scheduled_retry(self, run_id: UUID, tenant_id: UUID) -> None: ...


async def resolve_workflow_type(run_id: UUID, tenant_id: UUID) -> str | None:
    async with session_factory() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_id)},
        )
        workflow_type = await session.scalar(
            select(AgentRun.workflow_type).where(
                AgentRun.id == run_id,
                AgentRun.tenant_id == tenant_id,
            )
        )
        return workflow_type if isinstance(workflow_type, str) else None


async def run_worker() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    queue = RedisAgentQueue(settings.redis_url, settings.agent_queue_name)
    provider = build_qualification_provider(settings)
    executor = QualificationRunExecutor(provider, settings.agent_retry_base_seconds)
    ivc_provider = build_ivc_qualification_provider(settings)
    ivc_executor = IvcQualificationRunExecutor(
        ivc_provider,
        settings.agent_retry_base_seconds,
    )
    playground_provider = build_agent_playground_provider(settings)
    playground_executor = AgentPlaygroundRunExecutor(
        playground_provider,
        settings.agent_retry_base_seconds,
    )
    recovery = AgentRunRecoveryService(settings.agent_stale_after_seconds)
    next_recovery_at = 0.0
    logger.info(
        "Qualification provider selected",
        extra={
            "event": "agent.worker.provider_selected",
            "provider_type": provider.provider_type,
            "model_id": provider.model_id,
        },
    )
    logger.info(
        "IVC qualification provider selected",
        extra={
            "event": "ivc_agent.worker.provider_selected",
            "provider_type": ivc_provider.provider_type,
            "model_id": ivc_provider.model_id,
        },
    )
    logger.info(
        "Agent Playground provider selected",
        extra={
            "event": "agent_playground.worker.provider_selected",
            "provider_type": playground_provider.provider_type,
            "model_id": playground_provider.model_id,
        },
    )
    logger.info("Qualification worker started", extra={"event": "agent.worker.started"})
    try:
        while True:
            if time.monotonic() >= next_recovery_at:
                try:
                    recovered = await recovery.recover()
                    for item in recovered:
                        await queue.enqueue(
                            item.run_id,
                            item.tenant_id,
                            correlation_id=item.correlation_id,
                        )
                    if recovered:
                        logger.warning(
                            "Recovered durable Agent Runs",
                            extra={
                                "event": "agent.run.recovered",
                                "recovered_count": len(recovered),
                            },
                        )
                except Exception:
                    logger.exception(
                        "Agent Run recovery scan failed",
                        extra={"event": "agent.run.recovery_scan_failed"},
                    )
                next_recovery_at = time.monotonic() + settings.agent_recovery_interval_seconds
            try:
                message = await queue.dequeue(block_seconds=5)
            except InvalidAgentQueueMessageError:
                logger.warning(
                    "Discarded an invalid agent queue message",
                    extra={"event": "agent.queue.invalid_message"},
                )
                continue
            if message is None:
                continue
            token = set_correlation_id(message.correlation_id or str(message.run_id))
            try:
                workflow_type = await resolve_workflow_type(
                    message.run_id,
                    message.tenant_id,
                )
                executors: dict[str, RunnableAgentExecutor] = {
                    "lead_qualification": executor,
                    "ivc_facility_qualification": ivc_executor,
                    "agent_playground_qualification": playground_executor,
                }
                selected_executor = executors.get(workflow_type) if workflow_type else None
                if selected_executor is None:
                    logger.error(
                        "Unsupported Agent Run workflow",
                        extra={
                            "event": "agent.worker.unsupported_workflow",
                            "agent_run_id": str(message.run_id),
                            "tenant_id": str(message.tenant_id),
                            "workflow_type": workflow_type,
                        },
                    )
                    continue
                retry = await selected_executor.execute(message.run_id, message.tenant_id)
                if retry:
                    try:
                        await queue.enqueue(
                            message.run_id,
                            message.tenant_id,
                            correlation_id=retry.correlation_id,
                            delay_seconds=retry.delay_seconds,
                        )
                    except Exception:
                        logger.exception(
                            "Failed to schedule an Agent Run retry",
                            extra={
                                "event": "agent.queue.retry_enqueue_failed",
                                "agent_run_id": str(message.run_id),
                                "tenant_id": str(message.tenant_id),
                            },
                        )
                        await selected_executor.fail_scheduled_retry(
                            message.run_id,
                            message.tenant_id,
                        )
            except Exception:
                logger.exception(
                    "Agent queue message failed unexpectedly",
                    extra={
                        "event": "agent.queue.unexpected_failure",
                        "agent_run_id": str(message.run_id),
                        "tenant_id": str(message.tenant_id),
                    },
                )
            finally:
                reset_correlation_id(token)
    finally:
        await queue.close()
        await dispose_database()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
