from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

from openai import AsyncOpenAI

from sari_api.core.config import Settings


class KnowledgeEmbeddingProvider(Protocol):
    provider_type: str
    model_id: str
    dimensions: int

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class DeterministicKnowledgeEmbeddingProvider:
    provider_type = "mock"
    model_id = "deterministic-token-hash-v1"

    def __init__(self, dimensions: int = 1536) -> None:
        self.dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[\w]+|[\u3400-\u9fff]", text.casefold())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            return [value / norm for value in vector]
        return vector


class OpenAIKnowledgeEmbeddingProvider:
    provider_type = "openai"

    def __init__(self, api_key: str, model: str, dimensions: int) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self.model_id = model
        self.dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self._client.embeddings.create(
            model=self.model_id,
            input=texts,
            dimensions=self.dimensions,
            encoding_format="float",
        )
        ordered = sorted(response.data, key=lambda item: item.index)
        return [list(item.embedding) for item in ordered]


def build_knowledge_embedding_provider(settings: Settings) -> KnowledgeEmbeddingProvider:
    if settings.knowledge_embedding_provider == "openai":
        if settings.openai_api_key is None:
            raise RuntimeError("OpenAI knowledge embeddings require OPENAI_API_KEY.")
        return OpenAIKnowledgeEmbeddingProvider(
            settings.openai_api_key.get_secret_value(),
            settings.knowledge_embedding_model,
            settings.knowledge_embedding_dimensions,
        )
    return DeterministicKnowledgeEmbeddingProvider(settings.knowledge_embedding_dimensions)
