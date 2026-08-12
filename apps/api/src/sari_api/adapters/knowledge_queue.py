from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol
from uuid import UUID

from redis.asyncio import Redis

from sari_api.core.config import get_settings


class InvalidKnowledgeQueueMessageError(Exception):
    pass


@dataclass(frozen=True)
class KnowledgeQueueMessage:
    ingestion_run_id: UUID
    tenant_id: UUID
    correlation_id: str | None = None

    def serialize(self) -> str:
        return json.dumps(
            {
                "ingestion_run_id": str(self.ingestion_run_id),
                "tenant_id": str(self.tenant_id),
                "correlation_id": self.correlation_id,
            }
        )

    @classmethod
    def parse(cls, raw_payload: str) -> KnowledgeQueueMessage:
        try:
            payload: Any = json.loads(raw_payload)
            if not isinstance(payload, dict):
                raise TypeError
            correlation_id = payload.get("correlation_id")
            if correlation_id is not None and not isinstance(correlation_id, str):
                raise TypeError
            return cls(
                ingestion_run_id=UUID(payload["ingestion_run_id"]),
                tenant_id=UUID(payload["tenant_id"]),
                correlation_id=correlation_id,
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise InvalidKnowledgeQueueMessageError from exc


class KnowledgeQueue(Protocol):
    async def enqueue(
        self,
        ingestion_run_id: UUID,
        tenant_id: UUID,
        *,
        correlation_id: str | None = None,
    ) -> None: ...


class RedisKnowledgeQueue:
    def __init__(self, redis_url: str, queue_name: str) -> None:
        self._redis = Redis.from_url(redis_url, decode_responses=True)
        self._queue_name = queue_name

    async def enqueue(
        self,
        ingestion_run_id: UUID,
        tenant_id: UUID,
        *,
        correlation_id: str | None = None,
    ) -> None:
        await self._redis.rpush(
            self._queue_name,
            KnowledgeQueueMessage(ingestion_run_id, tenant_id, correlation_id).serialize(),
        )

    async def dequeue(self, block_seconds: int = 1) -> KnowledgeQueueMessage | None:
        item = await self._redis.blpop(self._queue_name, timeout=block_seconds)
        return None if item is None else KnowledgeQueueMessage.parse(item[1])

    async def close(self) -> None:
        await self._redis.aclose()


@lru_cache
def get_knowledge_queue() -> RedisKnowledgeQueue:
    settings = get_settings()
    return RedisKnowledgeQueue(settings.redis_url, settings.knowledge_queue_name)
