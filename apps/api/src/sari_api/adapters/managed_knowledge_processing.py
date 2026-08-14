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
from sari_api.adapters.knowledge_storage import KnowledgeObjectNotFoundError, KnowledgeStorage
from sari_api.adapters.models import (
    KnowledgeCollection,
    KnowledgeDocumentAgentBinding,
    KnowledgeDocumentVersion,
    KnowledgeProcessingRun,
    ManagedKnowledgeChunk,
    ManagedKnowledgeDocument,
)
from sari_api.domain.knowledge import TextChunk, chunk_sections


class ManagedKnowledgeProcessingExecutor:
    def __init__(
        self,
        storage: KnowledgeStorage,
        embedding_provider: KnowledgeEmbeddingProvider,
    ) -> None:
        self._storage = storage
        self._embedding_provider = embedding_provider
        self._extractor = DefaultKnowledgeTextExtractor()

    async def execute(self, processing_run_id: UUID, tenant_id: UUID) -> None:
        try:
            state = await self._start(processing_run_id, tenant_id)
            if state is None:
                return
            run, document, version = state
            if (
                self._embedding_provider.provider_type != run.embedding_provider
                or self._embedding_provider.model_id != run.embedding_model
                or self._embedding_provider.dimensions != run.embedding_dimensions
            ):
                raise ValueError("embedding_configuration_mismatch")
            content = await self._storage.get(version.object_key)
            if hashlib.sha256(content).hexdigest() != version.content_sha256:
                raise ValueError("stored_content_digest_mismatch")
            sections = await self._extractor.extract(content, version.media_type)
            chunks = chunk_sections(
                sections,
                chunk_size=run.chunk_size,
                overlap=run.chunk_overlap,
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
            if len(embeddings) != len(chunks) or any(
                len(item) != run.embedding_dimensions for item in embeddings
            ):
                raise ValueError("embedding_dimension_mismatch")
            await self._complete(run, document, version, chunks, embeddings, tenant_id)
        except UnsupportedKnowledgeDocumentError:
            await self._fail(
                processing_run_id,
                tenant_id,
                "unsupported_document",
                "Document extraction failed.",
            )
        except EmptyKnowledgeDocumentError:
            await self._fail(
                processing_run_id,
                tenant_id,
                "empty_document",
                "No usable text was extracted.",
            )
        except KnowledgeObjectNotFoundError:
            await self._fail(
                processing_run_id,
                tenant_id,
                "object_missing",
                "Uploaded object is unavailable.",
            )
        except Exception:
            await self._fail(
                processing_run_id,
                tenant_id,
                "processing_failed",
                "Knowledge processing failed safely.",
            )

    async def _start(
        self, processing_run_id: UUID, tenant_id: UUID
    ) -> (
        tuple[
            KnowledgeProcessingRun,
            ManagedKnowledgeDocument,
            KnowledgeDocumentVersion,
        ]
        | None
    ):
        async with session_factory() as session:
            await self._set_tenant(session, tenant_id)
            run = await session.scalar(
                select(KnowledgeProcessingRun)
                .where(
                    KnowledgeProcessingRun.id == processing_run_id,
                    KnowledgeProcessingRun.tenant_id == tenant_id,
                )
                .with_for_update()
            )
            if run is None:
                raise ValueError("processing_run_not_found")
            if run.status != "uploaded":
                return None
            document = await session.scalar(
                select(ManagedKnowledgeDocument).where(
                    ManagedKnowledgeDocument.id == run.document_id,
                    ManagedKnowledgeDocument.tenant_id == tenant_id,
                )
            )
            version = await session.scalar(
                select(KnowledgeDocumentVersion).where(
                    KnowledgeDocumentVersion.id == run.document_version_id,
                    KnowledgeDocumentVersion.tenant_id == tenant_id,
                )
            )
            collection_status = (
                await session.scalar(
                    select(KnowledgeCollection.status).where(
                        KnowledgeCollection.id == document.collection_id
                    )
                )
                if document is not None
                else None
            )
            agent_ids = list(
                (
                    await session.scalars(
                        select(KnowledgeDocumentAgentBinding.agent_id).where(
                            KnowledgeDocumentAgentBinding.tenant_id == tenant_id,
                            KnowledgeDocumentAgentBinding.document_id == run.document_id,
                            KnowledgeDocumentAgentBinding.status == "enabled",
                        )
                    )
                ).all()
            )
            if (
                document is None
                or version is None
                or document.approval_status != "approved"
                or document.lifecycle_status not in {"approved", "published", "active"}
                or document.current_version_number != version.version_number
                or collection_status != "active"
                or not agent_ids
            ):
                raise ValueError("document_not_eligible")
            run.status = "processing"
            run.started_at = datetime.now(UTC)
            document.processing_status = "processing"
            await session.commit()
            return run, document, version

    async def _complete(
        self,
        run: KnowledgeProcessingRun,
        document: ManagedKnowledgeDocument,
        version: KnowledgeDocumentVersion,
        chunks: list[TextChunk],
        embeddings: list[list[float]],
        tenant_id: UUID,
    ) -> None:
        async with session_factory() as session:
            await self._set_tenant(session, tenant_id)
            persistent_run = await session.scalar(
                select(KnowledgeProcessingRun)
                .where(KnowledgeProcessingRun.id == run.id)
                .with_for_update()
            )
            persistent_document = await session.scalar(
                select(ManagedKnowledgeDocument)
                .where(ManagedKnowledgeDocument.id == document.id)
                .with_for_update()
            )
            if persistent_run is None or persistent_document is None:
                raise ValueError("processing_state_missing")
            current_collection_status = await session.scalar(
                select(KnowledgeCollection.status).where(
                    KnowledgeCollection.id == persistent_document.collection_id,
                    KnowledgeCollection.tenant_id == tenant_id,
                )
            )
            current_agent_ids = list(
                (
                    await session.scalars(
                        select(KnowledgeDocumentAgentBinding.agent_id).where(
                            KnowledgeDocumentAgentBinding.tenant_id == tenant_id,
                            KnowledgeDocumentAgentBinding.document_id == persistent_document.id,
                            KnowledgeDocumentAgentBinding.status == "enabled",
                        )
                    )
                ).all()
            )
            if (
                persistent_run.status != "processing"
                or persistent_document.approval_status != "approved"
                or persistent_document.lifecycle_status not in {"approved", "published", "active"}
                or persistent_document.current_version_number != version.version_number
                or current_collection_status != "active"
                or not current_agent_ids
            ):
                raise ValueError("document_eligibility_changed")
            await session.execute(
                delete(ManagedKnowledgeChunk).where(
                    ManagedKnowledgeChunk.tenant_id == tenant_id,
                    ManagedKnowledgeChunk.document_id == document.id,
                )
            )
            for agent_id in current_agent_ids:
                for item, embedding in zip(chunks, embeddings, strict=True):
                    content_digest = hashlib.sha256(item.text.encode()).hexdigest()
                    citation = {
                        "tenant_id": str(tenant_id),
                        "domain_package_id": str(document.domain_package_id),
                        "agent_id": str(agent_id),
                        "collection_id": str(document.collection_id),
                        "document_id": str(document.id),
                        "document_version_id": str(version.id),
                        "version_number": version.version_number,
                        "title": document.title,
                        "filename": version.original_filename,
                        "page_number": item.page_number,
                        "section_title": item.section_title,
                        "chunk_index": item.index,
                        "content_sha256": content_digest,
                    }
                    session.add(
                        ManagedKnowledgeChunk(
                            tenant_id=tenant_id,
                            domain_package_id=document.domain_package_id,
                            agent_id=agent_id,
                            collection_id=document.collection_id,
                            document_id=document.id,
                            document_version_id=version.id,
                            processing_run_id=run.id,
                            chunk_index=item.index,
                            content=item.text,
                            content_sha256=content_digest,
                            character_count=len(item.text),
                            page_number=item.page_number,
                            section_title=item.section_title,
                            language=document.language,
                            document_type=document.document_type,
                            source_metadata=run.source_metadata_snapshot,
                            citation_metadata=citation,
                            embedding=embedding,
                            embedding_provider=run.embedding_provider,
                            embedding_model=run.embedding_model,
                        )
                    )
            persistent_run.status = "completed"
            persistent_run.chunk_count = len(chunks)
            persistent_run.completed_at = datetime.now(UTC)
            persistent_document.processing_status = "completed"
            await session.commit()

    async def _fail(
        self,
        processing_run_id: UUID,
        tenant_id: UUID,
        code: str,
        safe_message: str,
    ) -> None:
        async with session_factory() as session:
            await self._set_tenant(session, tenant_id)
            run = await session.scalar(
                select(KnowledgeProcessingRun).where(
                    KnowledgeProcessingRun.id == processing_run_id,
                    KnowledgeProcessingRun.tenant_id == tenant_id,
                )
            )
            if run is None or run.status == "completed":
                return
            document = await session.scalar(
                select(ManagedKnowledgeDocument).where(
                    ManagedKnowledgeDocument.id == run.document_id,
                    ManagedKnowledgeDocument.tenant_id == tenant_id,
                )
            )
            run.status = "failed"
            run.error_code = code
            run.error_message_safe = safe_message
            run.completed_at = datetime.now(UTC)
            if document is not None:
                document.processing_status = "failed"
            await session.commit()

    @staticmethod
    async def _set_tenant(session: AsyncSession, tenant_id: UUID) -> None:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_id)},
        )
