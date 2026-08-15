from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import (
    Agent,
    AgentCapability,
    AgentCapabilityBinding,
    AgentConfiguration,
    DomainPackage,
    KnowledgeCollection,
    KnowledgeDocumentAgentBinding,
    KnowledgeDocumentVersion,
    KnowledgeProcessingRun,
    ManagedKnowledgeChunk,
    ManagedKnowledgeDocument,
    TenantAgentActivation,
)


class ManagedKnowledgeRetrievalDeniedError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ManagedKnowledgeSearchHit:
    chunk: ManagedKnowledgeChunk
    document: ManagedKnowledgeDocument
    version: KnowledgeDocumentVersion
    distance: float


@dataclass(frozen=True, slots=True)
class ManagedKnowledgeAgentContext:
    agent_id: UUID
    agent_key: str
    domain_key: str
    configuration: AgentConfiguration


class ManagedKnowledgeRetrievalRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def search(
        self,
        *,
        agent_id: UUID,
        query_embedding: list[float],
        embedding_provider: str,
        embedding_model: str,
        language: str,
        top_k: int,
        minimum_similarity: float | None = None,
    ) -> list[ManagedKnowledgeSearchHit]:
        await self.ensure_agent_retrieval_enabled(agent_id)

        distance = ManagedKnowledgeChunk.embedding.cosine_distance(query_embedding).label(
            "distance"
        )
        conditions = [
            ManagedKnowledgeChunk.tenant_id == self._tenant_id,
            ManagedKnowledgeChunk.agent_id == agent_id,
            ManagedKnowledgeChunk.language == language,
            ManagedKnowledgeChunk.embedding_provider == embedding_provider,
            ManagedKnowledgeChunk.embedding_model == embedding_model,
            ManagedKnowledgeDocument.lifecycle_status == "active",
            ManagedKnowledgeDocument.approval_status == "approved",
            ManagedKnowledgeDocument.published_version_id
            == ManagedKnowledgeChunk.document_version_id,
            ManagedKnowledgeDocument.active_version_id == ManagedKnowledgeChunk.document_version_id,
            KnowledgeDocumentVersion.review_status == "approved",
            KnowledgeDocumentVersion.status == "active",
            KnowledgeCollection.status == "active",
            KnowledgeDocumentAgentBinding.status == "enabled",
            KnowledgeProcessingRun.status == "completed",
        ]
        if minimum_similarity is not None:
            conditions.append(distance <= 1.0 - minimum_similarity)

        statement = (
            select(
                ManagedKnowledgeChunk,
                ManagedKnowledgeDocument,
                KnowledgeDocumentVersion,
                distance,
            )
            .join(
                ManagedKnowledgeDocument,
                (ManagedKnowledgeDocument.id == ManagedKnowledgeChunk.document_id)
                & (ManagedKnowledgeDocument.tenant_id == self._tenant_id),
            )
            .join(
                KnowledgeDocumentVersion,
                (KnowledgeDocumentVersion.id == ManagedKnowledgeChunk.document_version_id)
                & (KnowledgeDocumentVersion.tenant_id == self._tenant_id),
            )
            .join(
                KnowledgeCollection,
                (KnowledgeCollection.id == ManagedKnowledgeChunk.collection_id)
                & (KnowledgeCollection.tenant_id == self._tenant_id),
            )
            .join(
                KnowledgeDocumentAgentBinding,
                (KnowledgeDocumentAgentBinding.document_id == ManagedKnowledgeDocument.id)
                & (KnowledgeDocumentAgentBinding.agent_id == agent_id)
                & (KnowledgeDocumentAgentBinding.tenant_id == self._tenant_id),
            )
            .join(
                KnowledgeProcessingRun,
                (KnowledgeProcessingRun.id == ManagedKnowledgeChunk.processing_run_id)
                & (KnowledgeProcessingRun.tenant_id == self._tenant_id),
            )
            .where(*conditions)
            .order_by(distance, ManagedKnowledgeChunk.id)
            .limit(top_k)
        )
        rows = (await self._session.execute(statement)).tuples().all()
        return [
            ManagedKnowledgeSearchHit(
                chunk=chunk,
                document=document,
                version=version,
                distance=float(raw_distance),
            )
            for chunk, document, version, raw_distance in rows
        ]

    async def ensure_agent_retrieval_enabled(self, agent_id: UUID) -> None:
        await self.get_agent_retrieval_context(agent_id)

    async def get_agent_retrieval_context(self, agent_id: UUID) -> ManagedKnowledgeAgentContext:
        row = (
            await self._session.execute(
                select(Agent, DomainPackage, AgentConfiguration)
                .select_from(TenantAgentActivation)
                .join(Agent, Agent.id == TenantAgentActivation.agent_id)
                .join(DomainPackage, DomainPackage.id == Agent.domain_package_id)
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
                    Agent.status == "available",
                    DomainPackage.status == "available",
                    AgentConfiguration.tenant_id == self._tenant_id,
                    AgentConfiguration.status == "active",
                    AgentConfiguration.runtime_config.contains({"knowledge_enabled": True}),
                    AgentCapabilityBinding.tenant_id == self._tenant_id,
                    AgentCapabilityBinding.status == "available",
                    AgentCapability.capability_key == "approved_knowledge_retrieval",
                    AgentCapability.status == "available",
                )
            )
        ).one_or_none()
        if row is None:
            raise ManagedKnowledgeRetrievalDeniedError
        agent, domain, configuration = row
        return ManagedKnowledgeAgentContext(
            agent_id=agent.id,
            agent_key=agent.agent_key,
            domain_key=domain.domain_key,
            configuration=configuration,
        )
