from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Protocol

from sari_api.adapters.knowledge_storage import LocalKnowledgeStorage
from sari_api.core.config import get_settings


class MediaStorage(Protocol):
    provider: str

    async def put(self, object_key: str, content: bytes) -> None: ...

    async def get(self, object_key: str) -> bytes: ...

    async def delete(self, object_key: str) -> None: ...


class LocalMediaStorage(LocalKnowledgeStorage):
    """Private development adapter with an object-storage-compatible boundary."""

    provider = "local"

    def __init__(self, root: Path) -> None:
        super().__init__(root)


@lru_cache
def get_media_storage() -> LocalMediaStorage:
    return LocalMediaStorage(get_settings().media_storage_path)
