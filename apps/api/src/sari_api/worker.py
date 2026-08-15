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
from sari_api.adapters.knowledge_assistant_executor import KnowledgeAssistantRunExecutor
from sari_api.adapters.knowledge_assistant_provider import build_knowledge_assistant_provider
from sari_api.adapters.knowledge_embedding import build_knowledge_embedding_provider
from sari_api.adapters.knowledge_ingestion import KnowledgeIngestionExecutor
from sari_api.adapters.knowledge_processing_queue import (
    InvalidKnowledgeProcessingMessageError,
    RedisKnowledgeProcessingQueue,
)
from sari_api.adapters.knowledge_queue import (
    InvalidKnowledgeQueueMessageError,
    RedisKnowledgeQueue,
)
from sari_api.adapters.knowledge_storage import LocalKnowledgeStorage
from sari_api.adapters.managed_knowledge_processing import ManagedKnowledgeProcessingExecutor
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
    knowledge_queue = RedisKnowledgeQueue(settings.redis_url, settings.knowledge_queue_name)
    processing_queue = RedisKnowledgeProcessingQueue(
        settings.redis_url, settings.knowledge_processing_queue_name
    )
    knowledge_executor = KnowledgeIngestionExecutor(
        LocalKnowledgeStorage(settings.knowledge_storage_path),
        build_knowledge_embedding_provider(settings),
        settings,
    )
    processing_executor = ManagedKnowledgeProcessingExecutor(
        LocalKnowledgeStorage(settings.knowledge_storage_path),
        build_knowledge_embedding_provider(settings),
    )
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
    knowledge_assistant_provider = build_knowledge_assistant_provider(settings)
    knowledge_assistant_executor = KnowledgeAssistantRunExecutor(
        build_knowledge_embedding_provider(settings),
        knowledge_assistant_provider,
        settings,
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
    logger.info(
        "Knowledge Assistant provider selected",
        extra={
            "event": "knowledge_assistant.worker.provider_selected",
            "provider_type": knowledge_assistant_provider.provider_type,
            "model_id": knowledge_assistant_provider.model_id,
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
                knowledge_message = await knowledge_queue.dequeue(block_seconds=1)
            except InvalidKnowledgeQueueMessageError:
                logger.warning(
                    "Discarded an invalid knowledge queue message",
                    extra={"event": "knowledge.queue.invalid_message"},
                )
                knowledge_message = None
            if knowledge_message is not None:
                knowledge_token = set_correlation_id(
                    knowledge_message.correlation_id or str(knowledge_message.ingestion_run_id)
                )
                try:
                    await knowledge_executor.execute(
                        knowledge_message.ingestion_run_id,
                        knowledge_message.tenant_id,
                    )
                except Exception:
                    logger.exception(
                        "Knowledge ingestion message failed unexpectedly",
                        extra={
                            "event": "knowledge.ingestion.unexpected_failure",
                            "knowledge_ingestion_run_id": str(knowledge_message.ingestion_run_id),
                            "tenant_id": str(knowledge_message.tenant_id),
                        },
                    )
                finally:
                    reset_correlation_id(knowledge_token)
            try:
                processing_message = await processing_queue.dequeue(block_seconds=1)
            except InvalidKnowledgeProcessingMessageError:
                logger.warning(
                    "Discarded an invalid managed knowledge processing message",
                    extra={"event": "knowledge.processing_queue.invalid_message"},
                )
                processing_message = None
            if processing_message is not None:
                processing_token = set_correlation_id(
                    processing_message.correlation_id or str(processing_message.processing_run_id)
                )
                try:
                    await processing_executor.execute(
                        processing_message.processing_run_id,
                        processing_message.tenant_id,
                    )
                except Exception:
                    logger.exception(
                        "Managed knowledge processing failed unexpectedly",
                        extra={
                            "event": "knowledge.processing.unexpected_failure",
                            "knowledge_processing_run_id": str(
                                processing_message.processing_run_id
                            ),
                            "tenant_id": str(processing_message.tenant_id),
                        },
                    )
                finally:
                    reset_correlation_id(processing_token)
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
                    "knowledge_assistant": knowledge_assistant_executor,
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
        await knowledge_queue.close()
        await processing_queue.close()
        await dispose_database()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
