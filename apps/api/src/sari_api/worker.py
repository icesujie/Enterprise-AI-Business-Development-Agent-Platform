from __future__ import annotations

import asyncio
import logging

from sari_api.adapters.agent_queue import (
    InvalidAgentQueueMessageError,
    RedisAgentQueue,
)
from sari_api.adapters.database import dispose_database
from sari_api.adapters.qualification_executor import QualificationRunExecutor
from sari_api.adapters.qualification_provider import build_qualification_provider
from sari_api.core.config import get_settings
from sari_api.core.observability import (
    configure_logging,
    reset_correlation_id,
    set_correlation_id,
)

logger = logging.getLogger(__name__)


async def run_worker() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    queue = RedisAgentQueue(settings.redis_url, settings.agent_queue_name)
    provider = build_qualification_provider(settings)
    executor = QualificationRunExecutor(provider, settings.agent_retry_base_seconds)
    logger.info(
        "Qualification provider selected",
        extra={
            "event": "agent.worker.provider_selected",
            "provider_type": provider.provider_type,
            "model_id": provider.model_id,
        },
    )
    logger.info("Qualification worker started", extra={"event": "agent.worker.started"})
    try:
        while True:
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
                retry = await executor.execute(message.run_id, message.tenant_id)
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
                        await executor.fail_scheduled_retry(
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
