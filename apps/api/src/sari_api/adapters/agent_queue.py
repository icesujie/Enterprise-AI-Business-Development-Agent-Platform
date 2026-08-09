from __future__ import annotations

import json
from functools import lru_cache
from typing import Protocol
from uuid import UUID

from redis.asyncio import Redis

from sari_api.core.config import get_settings


class AgentQueue(Protocol):
    async def enqueue(self, run_id: UUID, tenant_id: UUID) -> None: ...


class RedisAgentQueue:
    def __init__(self, redis_url: str, queue_name: str) -> None:
        self._redis = Redis.from_url(redis_url, decode_responses=True)
        self._queue_name = queue_name

    async def enqueue(self, run_id: UUID, tenant_id: UUID) -> None:
        payload = json.dumps({"run_id": str(run_id), "tenant_id": str(tenant_id)})
        await self._redis.rpush(self._queue_name, payload)


@lru_cache
def get_agent_queue() -> RedisAgentQueue:
    settings = get_settings()
    return RedisAgentQueue(settings.redis_url, settings.agent_queue_name)
