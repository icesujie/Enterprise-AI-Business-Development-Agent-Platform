from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol
from uuid import UUID

from redis.asyncio import Redis

from sari_api.core.config import get_settings


class InvalidKnowledgeProcessingMessageError(Exception):
    pass


@dataclass(frozen=True)
class KnowledgeProcessingMessage:
    processing_run_id: UUID
    tenant_id: UUID
    correlation_id: str | None = None

    def serialize(self) -> str:
        return json.dumps(
            {
                "processing_run_id": str(self.processing_run_id),
                "tenant_id": str(self.tenant_id),
                "correlation_id": self.correlation_id,
            }
        )

    @classmethod
    def parse(cls, raw_payload: str) -> KnowledgeProcessingMessage:
        try:
            payload: Any = json.loads(raw_payload)
            if not isinstance(payload, dict):
                raise TypeError
            correlation_id = payload.get("correlation_id")
            if correlation_id is not None and not isinstance(correlation_id, str):
                raise TypeError
            return cls(
                processing_run_id=UUID(payload["processing_run_id"]),
                tenant_id=UUID(payload["tenant_id"]),
                correlation_id=correlation_id,
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise InvalidKnowledgeProcessingMessageError from exc


class KnowledgeProcessingQueue(Protocol):
    async def enqueue(
        self,
        processing_run_id: UUID,
        tenant_id: UUID,
        *,
        correlation_id: str | None = None,
    ) -> None: ...


class RedisKnowledgeProcessingQueue:
    def __init__(self, redis_url: str, queue_name: str) -> None:
        self._redis = Redis.from_url(redis_url, decode_responses=True)
        self._queue_name = queue_name

    async def enqueue(
        self,
        processing_run_id: UUID,
        tenant_id: UUID,
        *,
        correlation_id: str | None = None,
    ) -> None:
        message = KnowledgeProcessingMessage(processing_run_id, tenant_id, correlation_id)
        await self._redis.rpush(self._queue_name, message.serialize())

    async def dequeue(self, block_seconds: int = 1) -> KnowledgeProcessingMessage | None:
        item = await self._redis.blpop(self._queue_name, timeout=block_seconds)
        return None if item is None else KnowledgeProcessingMessage.parse(item[1])

    async def close(self) -> None:
        await self._redis.aclose()


@lru_cache
def get_knowledge_processing_queue() -> RedisKnowledgeProcessingQueue:
    settings = get_settings()
    return RedisKnowledgeProcessingQueue(
        settings.redis_url, settings.knowledge_processing_queue_name
    )
