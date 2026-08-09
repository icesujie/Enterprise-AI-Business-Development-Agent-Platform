from __future__ import annotations

import json
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol
from uuid import UUID

from redis.asyncio import Redis

from sari_api.core.config import get_settings


class InvalidAgentQueueMessageError(Exception):
    pass


@dataclass(frozen=True)
class AgentQueueMessage:
    run_id: UUID
    tenant_id: UUID
    correlation_id: str | None = None

    def serialize(self) -> str:
        return json.dumps(
            {
                "run_id": str(self.run_id),
                "tenant_id": str(self.tenant_id),
                "correlation_id": self.correlation_id,
            }
        )

    @classmethod
    def parse(cls, raw_payload: str) -> AgentQueueMessage:
        try:
            payload: Any = json.loads(raw_payload)
            if not isinstance(payload, dict):
                raise TypeError
            correlation_id = payload.get("correlation_id")
            if correlation_id is not None and not isinstance(correlation_id, str):
                raise TypeError
            return cls(
                run_id=UUID(payload["run_id"]),
                tenant_id=UUID(payload["tenant_id"]),
                correlation_id=correlation_id,
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise InvalidAgentQueueMessageError from exc


class AgentQueue(Protocol):
    async def enqueue(self, run_id: UUID, tenant_id: UUID) -> None: ...


class RedisAgentQueue:
    def __init__(self, redis_url: str, queue_name: str) -> None:
        self._redis = Redis.from_url(redis_url, decode_responses=True)
        self._queue_name = queue_name
        self._scheduled_queue_name = f"{queue_name}:scheduled"

    async def enqueue(
        self,
        run_id: UUID,
        tenant_id: UUID,
        *,
        correlation_id: str | None = None,
        delay_seconds: int = 0,
    ) -> None:
        payload = AgentQueueMessage(run_id, tenant_id, correlation_id).serialize()
        if delay_seconds > 0:
            await self._redis.zadd(
                self._scheduled_queue_name,
                {payload: time.time() + delay_seconds},
            )
            return
        await self._redis.rpush(self._queue_name, payload)

    async def dequeue(self, block_seconds: int = 5) -> AgentQueueMessage | None:
        await self._promote_due_messages()
        item = await self._redis.blpop(self._queue_name, timeout=block_seconds)
        if item is None:
            return None
        return AgentQueueMessage.parse(item[1])

    async def _promote_due_messages(self) -> None:
        messages = await self._redis.zrangebyscore(
            self._scheduled_queue_name,
            min="-inf",
            max=time.time(),
            start=0,
            num=100,
        )
        if not messages:
            return
        async with self._redis.pipeline(transaction=True) as pipeline:
            for message in messages:
                pipeline.zrem(self._scheduled_queue_name, message)
                pipeline.rpush(self._queue_name, message)
            await pipeline.execute()

    async def close(self) -> None:
        await self._redis.aclose()


@lru_cache
def get_agent_queue() -> RedisAgentQueue:
    settings = get_settings()
    return RedisAgentQueue(settings.redis_url, settings.agent_queue_name)
