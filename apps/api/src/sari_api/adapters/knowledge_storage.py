from __future__ import annotations

import asyncio
import os
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from sari_api.core.config import get_settings


class KnowledgeObjectNotFoundError(Exception):
    pass


class KnowledgeStorage(Protocol):
    async def put(self, object_key: str, content: bytes) -> None: ...

    async def get(self, object_key: str) -> bytes: ...

    async def delete(self, object_key: str) -> None: ...


class LocalKnowledgeStorage:
    """Private local storage adapter for development and test environments."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def _path(self, object_key: str) -> Path:
        candidate = (self._root / object_key).resolve()
        if self._root not in candidate.parents:
            raise ValueError("Invalid knowledge object key.")
        return candidate

    async def put(self, object_key: str, content: bytes) -> None:
        path = self._path(object_key)

        def write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_bytes(content)
            os.replace(temporary, path)

        await asyncio.to_thread(write)

    async def get(self, object_key: str) -> bytes:
        path = self._path(object_key)
        try:
            return await asyncio.to_thread(path.read_bytes)
        except FileNotFoundError as exc:
            raise KnowledgeObjectNotFoundError from exc

    async def delete(self, object_key: str) -> None:
        path = self._path(object_key)
        try:
            await asyncio.to_thread(path.unlink)
        except FileNotFoundError:
            return


@lru_cache
def get_knowledge_storage() -> LocalKnowledgeStorage:
    return LocalKnowledgeStorage(get_settings().knowledge_storage_path)
