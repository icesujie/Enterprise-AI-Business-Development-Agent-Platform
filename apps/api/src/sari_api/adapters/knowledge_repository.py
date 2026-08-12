from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import (
    Agent,
    AgentCapability,
    AgentCapabilityBinding,
    AgentConfiguration,
    DomainPackage,
    KnowledgeBinding,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeIngestionRun,
    KnowledgeSource,
    TenantAgentActivation,
)


class KnowledgeNotFoundError(Exception):
    pass


class KnowledgeAccessDeniedError(Exception):
    pass


class KnowledgeStateConflictError(Exception):
    pass


class SqlAlchemyKnowledgeRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def create_source(
        self,
        *,
        source_key: str,
        name: str,
        description: str | None,
        source_type: str,
        source_metadata: dict[str, Any],
        created_by: UUID,
    ) -> KnowledgeSource:
        source = KnowledgeSource(
            tenant_id=self._tenant_id,
            source_key=source_key,
            name=name,
            description=description,
            source_type=source_type,
            source_metadata=source_metadata,
            created_by=created_by,
        )
        self._session.add(source)
        await self._session.flush()
        return source

    async def list_sources(self) -> list[KnowledgeSource]:
        return list(
            (
                await self._session.scalars(
                    select(KnowledgeSource)
                    .where(KnowledgeSource.tenant_id == self._tenant_id)
                    .order_by(KnowledgeSource.created_at.desc())
                )
            ).all()
        )

    async def get_source(self, source_id: UUID) -> KnowledgeSource:
        source = await self._session.scalar(
            select(KnowledgeSource).where(
                KnowledgeSource.id == source_id,
                KnowledgeSource.tenant_id == self._tenant_id,
            )
        )
        if source is None:
            raise KnowledgeNotFoundError
        return source

    async def create_binding(
        self,
        *,
        source_id: UUID,
        domain_key: str,
        agent_key: str,
        knowledge_category: str,
        created_by: UUID,
    ) -> KnowledgeBinding:
        source = await self.get_source(source_id)
        if source.status != "active":
            raise KnowledgeStateConflictError
        row = (
            await self._session.execute(
                select(DomainPackage, Agent)
                .join(Agent, Agent.domain_package_id == DomainPackage.id)
                .where(
                    DomainPackage.domain_key == domain_key,
                    Agent.agent_key == agent_key,
                )
            )
        ).one_or_none()
        if row is None:
            raise KnowledgeNotFoundError
        domain, agent = row
        if not await self._retrieval_capability_enabled(agent.id):
            raise KnowledgeAccessDeniedError
        binding = KnowledgeBinding(
            tenant_id=self._tenant_id,
            source_id=source_id,
            domain_package_id=domain.id,
            agent_id=agent.id,
            knowledge_category=knowledge_category,
            status="enabled",
            created_by=created_by,
        )
        self._session.add(binding)
        await self._session.flush()
        return binding

    async def list_bindings(
        self, source_id: UUID
    ) -> list[tuple[KnowledgeBinding, DomainPackage, Agent]]:
        await self.get_source(source_id)
        return list(
            (
                await self._session.execute(
                    select(KnowledgeBinding, DomainPackage, Agent)
                    .join(
                        DomainPackage,
                        DomainPackage.id == KnowledgeBinding.domain_package_id,
                    )
                    .join(Agent, Agent.id == KnowledgeBinding.agent_id)
                    .where(
                        KnowledgeBinding.tenant_id == self._tenant_id,
                        KnowledgeBinding.source_id == source_id,
                    )
                    .order_by(DomainPackage.domain_key, Agent.agent_key)
                )
            )
            .tuples()
            .all()
        )

    async def find_document_by_digest(
        self, source_id: UUID, content_sha256: str
    ) -> KnowledgeDocument | None:
        return await self._session.scalar(
            select(KnowledgeDocument).where(
                KnowledgeDocument.tenant_id == self._tenant_id,
                KnowledgeDocument.source_id == source_id,
                KnowledgeDocument.content_sha256 == content_sha256,
            )
        )

    async def create_document(
        self,
        *,
        source_id: UUID,
        title: str,
        original_filename: str,
        media_type: str,
        language: str,
        object_key: str,
        content_sha256: str,
        byte_size: int,
        source_metadata: dict[str, Any],
        created_by: UUID,
    ) -> KnowledgeDocument:
        source = await self.get_source(source_id)
        if source.status != "active":
            raise KnowledgeStateConflictError
        document = KnowledgeDocument(
            tenant_id=self._tenant_id,
            source_id=source_id,
            title=title,
            original_filename=original_filename,
            media_type=media_type,
            language=language,
            object_key=object_key,
            content_sha256=content_sha256,
            byte_size=byte_size,
            source_metadata=source_metadata,
            created_by=created_by,
        )
        self._session.add(document)
        await self._session.flush()
        return document

    async def list_documents(self, source_id: UUID | None = None) -> list[KnowledgeDocument]:
        statement = select(KnowledgeDocument).where(KnowledgeDocument.tenant_id == self._tenant_id)
        if source_id is not None:
            statement = statement.where(KnowledgeDocument.source_id == source_id)
        return list(
            (
                await self._session.scalars(statement.order_by(KnowledgeDocument.created_at.desc()))
            ).all()
        )

    async def get_document(self, document_id: UUID, *, lock: bool = False) -> KnowledgeDocument:
        statement = select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.tenant_id == self._tenant_id,
        )
        if lock:
            statement = statement.with_for_update()
        document = await self._session.scalar(statement)
        if document is None:
            raise KnowledgeNotFoundError
        return document

    async def approve_document(
        self,
        document_id: UUID,
        *,
        reviewer_id: UUID,
        review_note: str | None,
        embedding_provider: str,
        embedding_model: str,
        correlation_id: str | None,
    ) -> tuple[KnowledgeDocument, KnowledgeIngestionRun]:
        document = await self.get_document(document_id, lock=True)
        if document.approval_status != "pending":
            raise KnowledgeStateConflictError
        enabled_binding = await self._session.scalar(
            select(KnowledgeBinding.id).where(
                KnowledgeBinding.tenant_id == self._tenant_id,
                KnowledgeBinding.source_id == document.source_id,
                KnowledgeBinding.status == "enabled",
            )
        )
        if enabled_binding is None:
            raise KnowledgeAccessDeniedError
        now = datetime.now(UTC)
        document.approval_status = "approved"
        document.ingestion_status = "queued"
        document.approved_by = reviewer_id
        document.approved_at = now
        document.review_note = review_note
        run = KnowledgeIngestionRun(
            tenant_id=self._tenant_id,
            document_id=document.id,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            correlation_id=correlation_id,
            created_by=reviewer_id,
        )
        self._session.add(run)
        await self._session.flush()
        return document, run

    async def reject_document(
        self, document_id: UUID, *, reviewer_id: UUID, review_note: str | None
    ) -> KnowledgeDocument:
        document = await self.get_document(document_id, lock=True)
        if document.approval_status != "pending":
            raise KnowledgeStateConflictError
        document.approval_status = "rejected"
        document.rejected_by = reviewer_id
        document.rejected_at = datetime.now(UTC)
        document.review_note = review_note
        return document

    async def create_ingestion_run(
        self,
        document_id: UUID,
        *,
        created_by: UUID,
        embedding_provider: str,
        embedding_model: str,
        correlation_id: str | None,
    ) -> tuple[KnowledgeDocument, KnowledgeIngestionRun]:
        document = await self.get_document(document_id, lock=True)
        if document.approval_status != "approved" or document.ingestion_status in {
            "queued",
            "processing",
        }:
            raise KnowledgeStateConflictError
        document.ingestion_status = "queued"
        run = KnowledgeIngestionRun(
            tenant_id=self._tenant_id,
            document_id=document.id,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            correlation_id=correlation_id,
            created_by=created_by,
        )
        self._session.add(run)
        await self._session.flush()
        return document, run

    async def get_ingestion_run(self, run_id: UUID) -> KnowledgeIngestionRun:
        run = await self._session.scalar(
            select(KnowledgeIngestionRun).where(
                KnowledgeIngestionRun.id == run_id,
                KnowledgeIngestionRun.tenant_id == self._tenant_id,
            )
        )
        if run is None:
            raise KnowledgeNotFoundError
        return run

    async def search(
        self,
        *,
        domain_key: str,
        agent_key: str,
        query_embedding: list[float],
        embedding_provider: str,
        embedding_model: str,
        limit: int,
    ) -> list[tuple[KnowledgeChunk, KnowledgeDocument, KnowledgeSource, float]]:
        row = (
            await self._session.execute(
                select(DomainPackage, Agent)
                .join(Agent, Agent.domain_package_id == DomainPackage.id)
                .where(
                    DomainPackage.domain_key == domain_key,
                    Agent.agent_key == agent_key,
                )
            )
        ).one_or_none()
        if row is None:
            raise KnowledgeNotFoundError
        domain, agent = row
        if not await self._retrieval_capability_enabled(agent.id):
            raise KnowledgeAccessDeniedError
        distance = KnowledgeChunk.embedding.cosine_distance(query_embedding).label("distance")
        statement = (
            select(KnowledgeChunk, KnowledgeDocument, KnowledgeSource, distance)
            .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
            .join(KnowledgeSource, KnowledgeSource.id == KnowledgeChunk.source_id)
            .join(
                KnowledgeBinding,
                (KnowledgeBinding.source_id == KnowledgeSource.id)
                & (KnowledgeBinding.tenant_id == self._tenant_id),
            )
            .where(
                KnowledgeChunk.tenant_id == self._tenant_id,
                KnowledgeDocument.tenant_id == self._tenant_id,
                KnowledgeSource.tenant_id == self._tenant_id,
                KnowledgeDocument.approval_status == "approved",
                KnowledgeDocument.ingestion_status == "ready",
                KnowledgeSource.status == "active",
                KnowledgeBinding.status == "enabled",
                KnowledgeBinding.domain_package_id == domain.id,
                KnowledgeBinding.agent_id == agent.id,
                KnowledgeChunk.embedding_provider == embedding_provider,
                KnowledgeChunk.embedding_model == embedding_model,
            )
            .order_by(distance)
            .limit(limit)
        )
        return [
            (chunk, document, source, float(raw_distance))
            for chunk, document, source, raw_distance in (
                await self._session.execute(statement)
            ).tuples()
        ]

    async def _retrieval_capability_enabled(self, agent_id: UUID) -> bool:
        enabled = await self._session.scalar(
            select(TenantAgentActivation.id)
            .join(
                AgentConfiguration,
                AgentConfiguration.id == TenantAgentActivation.agent_configuration_id,
            )
            .join(
                AgentCapabilityBinding,
                AgentCapabilityBinding.agent_configuration_id == AgentConfiguration.id,
            )
            .join(
                AgentCapability,
                AgentCapability.id == AgentCapabilityBinding.capability_id,
            )
            .where(
                TenantAgentActivation.tenant_id == self._tenant_id,
                TenantAgentActivation.agent_id == agent_id,
                TenantAgentActivation.status == "active",
                AgentConfiguration.tenant_id == self._tenant_id,
                AgentConfiguration.status == "active",
                AgentConfiguration.runtime_config.contains({"knowledge_enabled": True}),
                AgentCapabilityBinding.tenant_id == self._tenant_id,
                AgentCapabilityBinding.status == "available",
                AgentCapability.capability_key == "approved_knowledge_retrieval",
                AgentCapability.status == "available",
            )
        )
        return enabled is not None
