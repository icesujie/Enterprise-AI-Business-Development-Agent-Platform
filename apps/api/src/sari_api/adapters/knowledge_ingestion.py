from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.database import session_factory
from sari_api.adapters.knowledge_embedding import KnowledgeEmbeddingProvider
from sari_api.adapters.knowledge_extractor import (
    DefaultKnowledgeTextExtractor,
    EmptyKnowledgeDocumentError,
    UnsupportedKnowledgeDocumentError,
)
from sari_api.adapters.knowledge_storage import (
    KnowledgeObjectNotFoundError,
    KnowledgeStorage,
)
from sari_api.adapters.models import (
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeIngestionRun,
)
from sari_api.core.config import Settings
from sari_api.domain.knowledge import TextChunk, chunk_sections


class KnowledgeIngestionExecutor:
    def __init__(
        self,
        storage: KnowledgeStorage,
        embedding_provider: KnowledgeEmbeddingProvider,
        settings: Settings,
    ) -> None:
        self._storage = storage
        self._embedding_provider = embedding_provider
        self._settings = settings
        self._extractor = DefaultKnowledgeTextExtractor()

    async def execute(self, ingestion_run_id: UUID, tenant_id: UUID) -> None:
        try:
            state = await self._start(ingestion_run_id, tenant_id)
            if state is None:
                return
            run, document = state
            content = await self._storage.get(document.object_key)
            if hashlib.sha256(content).hexdigest() != document.content_sha256:
                raise ValueError("stored_content_digest_mismatch")
            sections = await self._extractor.extract(content, document.media_type)
            chunks = chunk_sections(
                sections,
                chunk_size=self._settings.knowledge_chunk_size,
                overlap=self._settings.knowledge_chunk_overlap,
            )
            if not chunks:
                raise EmptyKnowledgeDocumentError
            embeddings: list[list[float]] = []
            for start in range(0, len(chunks), 64):
                embeddings.extend(
                    await self._embedding_provider.embed(
                        [item.text for item in chunks[start : start + 64]]
                    )
                )
            if len(embeddings) != len(chunks) or any(len(item) != 1536 for item in embeddings):
                raise ValueError("embedding_dimension_mismatch")
            await self._complete(run, document, chunks, embeddings, tenant_id)
        except UnsupportedKnowledgeDocumentError:
            await self._fail(
                ingestion_run_id, tenant_id, "unsupported_document", "Document extraction failed."
            )
        except EmptyKnowledgeDocumentError:
            await self._fail(
                ingestion_run_id, tenant_id, "empty_document", "No usable text was extracted."
            )
        except KnowledgeObjectNotFoundError:
            await self._fail(
                ingestion_run_id, tenant_id, "object_missing", "Uploaded object is unavailable."
            )
        except Exception:
            await self._fail(
                ingestion_run_id,
                tenant_id,
                "ingestion_failed",
                "Knowledge ingestion failed safely.",
            )

    async def _start(
        self, ingestion_run_id: UUID, tenant_id: UUID
    ) -> tuple[KnowledgeIngestionRun, KnowledgeDocument] | None:
        async with session_factory() as session:
            await self._set_tenant(session, tenant_id)
            run = await session.scalar(
                select(KnowledgeIngestionRun)
                .where(
                    KnowledgeIngestionRun.id == ingestion_run_id,
                    KnowledgeIngestionRun.tenant_id == tenant_id,
                )
                .with_for_update()
            )
            if run is None:
                raise ValueError("ingestion_run_not_found")
            document = await session.scalar(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.id == run.document_id,
                    KnowledgeDocument.tenant_id == tenant_id,
                )
            )
            if document is None or document.approval_status != "approved":
                raise ValueError("document_not_approved")
            if run.status == "succeeded":
                return None
            run.status = "processing"
            run.started_at = datetime.now(UTC)
            document.ingestion_status = "processing"
            await session.commit()
            return run, document

    async def _complete(
        self,
        run: KnowledgeIngestionRun,
        document: KnowledgeDocument,
        chunks: list[TextChunk],
        embeddings: list[list[float]],
        tenant_id: UUID,
    ) -> None:
        async with session_factory() as session:
            await self._set_tenant(session, tenant_id)
            persistent_run = await session.scalar(
                select(KnowledgeIngestionRun)
                .where(KnowledgeIngestionRun.id == run.id)
                .with_for_update()
            )
            persistent_document = await session.scalar(
                select(KnowledgeDocument)
                .where(KnowledgeDocument.id == document.id)
                .with_for_update()
            )
            if persistent_run is None or persistent_document is None:
                raise ValueError("ingestion_state_missing")
            if persistent_document.approval_status != "approved":
                raise ValueError("document_approval_changed")
            await session.execute(
                delete(KnowledgeChunk).where(
                    KnowledgeChunk.tenant_id == tenant_id,
                    KnowledgeChunk.document_id == document.id,
                )
            )
            for item, embedding in zip(chunks, embeddings, strict=True):
                session.add(
                    KnowledgeChunk(
                        tenant_id=tenant_id,
                        source_id=document.source_id,
                        document_id=document.id,
                        ingestion_run_id=run.id,
                        chunk_index=item.index,
                        content=item.text,
                        content_sha256=hashlib.sha256(item.text.encode("utf-8")).hexdigest(),
                        character_count=len(item.text),
                        page_number=item.page_number,
                        section_title=item.section_title,
                        citation_metadata={
                            "document_id": str(document.id),
                            "source_id": str(document.source_id),
                            "title": document.title,
                            "filename": document.original_filename,
                            "page_number": item.page_number,
                            "section_title": item.section_title,
                            "chunk_index": item.index,
                            "content_sha256": hashlib.sha256(item.text.encode("utf-8")).hexdigest(),
                        },
                        embedding=embedding,
                        embedding_provider=self._embedding_provider.provider_type,
                        embedding_model=self._embedding_provider.model_id,
                    )
                )
            persistent_run.status = "succeeded"
            persistent_run.chunk_count = len(chunks)
            persistent_run.completed_at = datetime.now(UTC)
            persistent_document.ingestion_status = "ready"
            await session.commit()

    async def _fail(
        self,
        ingestion_run_id: UUID,
        tenant_id: UUID,
        code: str,
        safe_message: str,
    ) -> None:
        async with session_factory() as session:
            await self._set_tenant(session, tenant_id)
            run = await session.scalar(
                select(KnowledgeIngestionRun).where(
                    KnowledgeIngestionRun.id == ingestion_run_id,
                    KnowledgeIngestionRun.tenant_id == tenant_id,
                )
            )
            if run is None or run.status == "succeeded":
                return
            document = await session.scalar(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.id == run.document_id,
                    KnowledgeDocument.tenant_id == tenant_id,
                )
            )
            run.status = "failed"
            run.error_code = code
            run.error_message_safe = safe_message
            run.completed_at = datetime.now(UTC)
            if document is not None:
                document.ingestion_status = "failed"
            await session.commit()

    @staticmethod
    async def _set_tenant(session: AsyncSession, tenant_id: UUID) -> None:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_id)},
        )
