from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from uuid import UUID

from redis.asyncio import Redis

from sari_api.adapters.database import dispose_database
from sari_api.adapters.qualification_executor import QualificationRunExecutor
from sari_api.adapters.qualification_provider import AgentsSdkQualificationProvider
from sari_api.core.config import get_settings

logger = logging.getLogger(__name__)


async def run_worker() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    executor = QualificationRunExecutor(AgentsSdkQualificationProvider(settings))
    logger.info("Qualification worker started")
    try:
        while True:
            item = await redis.blpop(settings.agent_queue_name, timeout=5)
            if item is None:
                continue
            _, raw_payload = item
            try:
                payload: dict[str, Any] = json.loads(raw_payload)
                await executor.execute(UUID(payload["run_id"]), UUID(payload["tenant_id"]))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                logger.warning("Discarded an invalid agent queue message")
            except Exception:
                logger.exception("Agent queue message failed unexpectedly")
    finally:
        await redis.aclose()
        await dispose_database()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
