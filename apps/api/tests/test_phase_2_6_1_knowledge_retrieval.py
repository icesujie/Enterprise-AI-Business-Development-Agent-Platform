from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import select, text

from sari_api.adapters.database import session_factory
from sari_api.adapters.knowledge_embedding import DeterministicKnowledgeEmbeddingProvider
from sari_api.adapters.models import (
    Agent,
    KnowledgeCollection,
    KnowledgeDocumentAgentBinding,
    KnowledgeDocumentVersion,
    KnowledgeProcessingRun,
    ManagedKnowledgeChunk,
    ManagedKnowledgeDocument,
)
from sari_api.api.dependencies import get_token_identity
from sari_api.domain.identity import TokenIdentity
from sari_api.main import app

TENANT_ID = UUID("10000000-0000-4000-8000-000000000001")
ADMIN_USER_ID = UUID("20000000-0000-4000-8000-000000000001")
SARI_AGENT_ID = UUID("61000000-0000-4000-8000-000000000001")
IVC_AGENT_ID = UUID("61000000-0000-4000-8000-000000000002")
ADMIN_SUBJECT = "30000000-0000-4000-8000-000000000001"


async def admin_identity() -> TokenIdentity:
    return TokenIdentity(subject=ADMIN_SUBJECT, email="admin@sari-arta.example")


@pytest.mark.asyncio
async def test_retrieval_returns_only_governed_agent_bound_citable_knowledge() -> None:
    collection_id = await seed_retrieval_fixture()
    app.dependency_overrides[get_token_identity] = admin_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/knowledge/search",
                json={
                    "tenant_id": str(TENANT_ID),
                    "agent_id": str(SARI_AGENT_ID),
                    "query": "ventilation exhaust airflow",
                    "language": "en",
                    "top_k": 10,
                },
            )
            assert response.status_code == 200, response.text
            payload = response.json()
            assert payload["evidence_status"] == "sufficient_candidates"
            assert payload["decision_reason"] == "meets_minimum_evidence"
            assert payload["similarity_threshold"] == 0.15
            assert payload["minimum_evidence_count"] == 1
            assert payload["correlation_id"]
            assert payload["duration_ms"] >= 0
            assert len(payload["results"]) == 1
            result = payload["results"][0]
            assert result["document_name"].startswith("Eligible Ventilation Guide")
            assert result["document_version"] == 1
            assert "exhaust airflow" in result["chunk_content"]
            assert result["page_number"] == 7
            assert result["section"] == "Ventilation design"
            assert result["metadata"]["synthetic"] is True
            assert result["similarity_score"] > 0.15
            assert result["citation"]["chunk_id"]
            assert result["citation"]["document_version_id"]
            assert result["citation"]["document_version"] == 1
            assert result["citation"]["page_number"] == 7

            wrong_language = await client.post(
                "/api/v1/knowledge/search",
                json={
                    "tenant_id": str(TENANT_ID),
                    "agent_id": str(SARI_AGENT_ID),
                    "query": "ventilation exhaust airflow",
                    "language": "zh-CN",
                    "top_k": 10,
                },
            )
            assert wrong_language.status_code == 200
            assert wrong_language.json()["evidence_status"] == "insufficient_evidence"
            assert wrong_language.json()["results"] == []

            irrelevant = await client.post(
                "/api/v1/knowledge/search",
                json={
                    "tenant_id": str(TENANT_ID),
                    "agent_id": str(SARI_AGENT_ID),
                    "query": "zebrafish astronomy cryogenics",
                    "language": "en",
                    "top_k": 10,
                },
            )
            assert irrelevant.status_code == 200
            assert irrelevant.json()["results"] == []
            assert irrelevant.json()["evidence_status"] == "insufficient_evidence"
            assert irrelevant.json()["decision_reason"] == "below_similarity_threshold"
    finally:
        app.dependency_overrides.clear()
        await cleanup_collection(collection_id)


@pytest.mark.asyncio
async def test_retrieval_rejects_cross_tenant_and_unenabled_agent() -> None:
    app.dependency_overrides[get_token_identity] = admin_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            cross_tenant = await client.post(
                "/api/v1/knowledge/search",
                json={
                    "tenant_id": str(uuid4()),
                    "agent_id": str(SARI_AGENT_ID),
                    "query": "ventilation exhaust airflow",
                    "language": "en",
                    "top_k": 5,
                },
            )
            assert cross_tenant.status_code == 403

            ivc_disabled = await client.post(
                "/api/v1/knowledge/search",
                json={
                    "tenant_id": str(TENANT_ID),
                    "agent_id": str(IVC_AGENT_ID),
                    "query": "cage capacity airflow",
                    "language": "en",
                    "top_k": 5,
                },
            )
            assert ivc_disabled.status_code == 403
            assert ivc_disabled.json()["detail"] == (
                "Knowledge retrieval is not enabled for this tenant agent."
            )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_authorization_happens_before_embedding_provider_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider_called = False

    def forbidden_provider(_: object) -> object:
        nonlocal provider_called
        provider_called = True
        raise AssertionError("embedding provider must not be called")

    monkeypatch.setattr(
        "sari_api.api.routes.knowledge_retrieval.build_knowledge_embedding_provider",
        forbidden_provider,
    )
    app.dependency_overrides[get_token_identity] = admin_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/knowledge/search",
                json={
                    "tenant_id": str(TENANT_ID),
                    "agent_id": str(IVC_AGENT_ID),
                    "query": "cage capacity airflow",
                    "language": "en",
                    "top_k": 5,
                },
            )
        assert response.status_code == 403
        assert provider_called is False
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_disabling_document_agent_binding_immediately_revokes_retrieval() -> None:
    collection_id = await seed_retrieval_fixture()
    app.dependency_overrides[get_token_identity] = admin_identity
    try:
        async with session_factory() as session:
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(TENANT_ID)},
            )
            binding = await session.scalar(
                select(KnowledgeDocumentAgentBinding)
                .join(
                    ManagedKnowledgeDocument,
                    ManagedKnowledgeDocument.id == KnowledgeDocumentAgentBinding.document_id,
                )
                .where(
                    KnowledgeDocumentAgentBinding.tenant_id == TENANT_ID,
                    ManagedKnowledgeDocument.collection_id == collection_id,
                    ManagedKnowledgeDocument.title.like("Eligible Ventilation Guide%"),
                )
            )
            assert binding is not None
            binding.status = "disabled"
            await session.commit()

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/knowledge/search",
                json={
                    "tenant_id": str(TENANT_ID),
                    "agent_id": str(SARI_AGENT_ID),
                    "query": "ventilation exhaust airflow",
                    "language": "en",
                    "top_k": 5,
                },
            )
            assert response.status_code == 200
            assert response.json()["results"] == []
    finally:
        app.dependency_overrides.clear()
        await cleanup_collection(collection_id)


@pytest.mark.asyncio
async def test_managed_chunks_force_rls_and_other_tenant_scope_is_empty() -> None:
    other_tenant_id = uuid4()
    async with session_factory() as session:
        row = (
            await session.execute(
                text(
                    "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
                    "WHERE relname = 'managed_knowledge_chunks'"
                )
            )
        ).one()
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(other_tenant_id)},
        )
        visible = list(
            (
                await session.scalars(
                    select(ManagedKnowledgeChunk.id).where(
                        ManagedKnowledgeChunk.tenant_id == other_tenant_id
                    )
                )
            ).all()
        )
    assert row == (True, True)
    assert visible == []


async def seed_retrieval_fixture() -> UUID:
    suffix = uuid4().hex[:10]
    provider = DeterministicKnowledgeEmbeddingProvider(1536)
    async with session_factory() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(TENANT_ID)},
        )
        agent = await session.get(Agent, SARI_AGENT_ID)
        assert agent is not None
        collection = KnowledgeCollection(
            tenant_id=TENANT_ID,
            domain_package_id=agent.domain_package_id,
            collection_key=f"retrieval-{suffix}",
            name=f"Synthetic Retrieval {suffix}",
            description="Synthetic Phase 2.6.1 retrieval validation.",
            collection_metadata={"synthetic": True},
            created_by=ADMIN_USER_ID,
        )
        session.add(collection)
        await session.flush()

        await add_document_chunk(
            session,
            collection,
            agent,
            title=f"Eligible Ventilation Guide {suffix}",
            content=(
                "Commercial kitchen ventilation exhaust airflow must follow the engineered design."
            ),
            lifecycle="active",
            bound=True,
            page_number=7,
            section="Ventilation design",
            provider=provider,
        )
        await add_document_chunk(
            session,
            collection,
            agent,
            title=f"Inactive Ventilation Draft {suffix}",
            content="Commercial kitchen ventilation exhaust airflow draft reference.",
            lifecycle="approved",
            bound=True,
            page_number=2,
            section="Draft",
            provider=provider,
        )
        await add_document_chunk(
            session,
            collection,
            agent,
            title=f"Unbound Ventilation Guide {suffix}",
            content="Commercial kitchen ventilation exhaust airflow unbound reference.",
            lifecycle="active",
            bound=False,
            page_number=3,
            section="Unbound",
            provider=provider,
        )
        await add_document_chunk(
            session,
            collection,
            agent,
            title=f"Irrelevant Contract Note {suffix}",
            content="Corporate contract warranty legal renewal terms.",
            lifecycle="active",
            bound=True,
            page_number=4,
            section="Contracts",
            provider=provider,
        )
        await session.commit()
        return collection.id


async def add_document_chunk(
    session: object,
    collection: KnowledgeCollection,
    agent: Agent,
    *,
    title: str,
    content: str,
    lifecycle: str,
    bound: bool,
    page_number: int,
    section: str,
    provider: DeterministicKnowledgeEmbeddingProvider,
) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession

    assert isinstance(session, AsyncSession)
    now = datetime.now(UTC)
    active = lifecycle == "active"
    document = ManagedKnowledgeDocument(
        tenant_id=TENANT_ID,
        domain_package_id=agent.domain_package_id,
        agent_id=agent.id,
        collection_id=collection.id,
        title=title,
        document_type="technical_reference",
        language="en",
        lifecycle_status=lifecycle,
        approval_status="approved",
        processing_status="completed",
        current_version_number=1,
        document_metadata={"synthetic": True},
        approved_by=ADMIN_USER_ID,
        approved_at=now,
        created_by=ADMIN_USER_ID,
    )
    session.add(document)
    await session.flush()
    digest = hashlib.sha256(content.encode()).hexdigest()
    version = KnowledgeDocumentVersion(
        tenant_id=TENANT_ID,
        document_id=document.id,
        version_number=1,
        original_filename=f"{document.id}.md",
        media_type="text/markdown",
        object_key=f"synthetic/retrieval/{document.id}.md",
        content_sha256=digest,
        byte_size=len(content.encode()),
        version_metadata={"synthetic": True},
        status="active" if active else "approved",
        review_status="approved",
        reviewed_by=ADMIN_USER_ID,
        reviewed_at=now,
        created_by=ADMIN_USER_ID,
    )
    session.add(version)
    await session.flush()
    document.current_version_id = version.id
    if active:
        document.published_version_id = version.id
        document.active_version_id = version.id
        document.published_by = ADMIN_USER_ID
        document.published_at = now
    run = KnowledgeProcessingRun(
        tenant_id=TENANT_ID,
        document_id=document.id,
        document_version_id=version.id,
        status="completed",
        chunk_size=1200,
        chunk_overlap=200,
        embedding_provider=provider.provider_type,
        embedding_model=provider.model_id,
        embedding_dimensions=1536,
        chunk_count=1,
        source_metadata_snapshot={"synthetic": True},
        completed_at=now,
        created_by=ADMIN_USER_ID,
    )
    session.add(run)
    if bound:
        session.add(
            KnowledgeDocumentAgentBinding(
                tenant_id=TENANT_ID,
                document_id=document.id,
                agent_id=agent.id,
                status="enabled",
                created_by=ADMIN_USER_ID,
            )
        )
    await session.flush()
    embedding = (await provider.embed([content]))[0]
    session.add(
        ManagedKnowledgeChunk(
            tenant_id=TENANT_ID,
            domain_package_id=agent.domain_package_id,
            agent_id=agent.id,
            collection_id=collection.id,
            document_id=document.id,
            document_version_id=version.id,
            processing_run_id=run.id,
            chunk_index=0,
            content=content,
            content_sha256=digest,
            character_count=len(content),
            page_number=page_number,
            section_title=section,
            language="en",
            document_type="technical_reference",
            source_metadata={"synthetic": True, "document_metadata": document.document_metadata},
            citation_metadata={
                "document_id": str(document.id),
                "document_version_id": str(version.id),
                "version_number": 1,
                "page_number": page_number,
                "section_title": section,
            },
            embedding=embedding,
            embedding_provider=provider.provider_type,
            embedding_model=provider.model_id,
        )
    )


async def cleanup_collection(collection_id: UUID) -> None:
    async with session_factory() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(TENANT_ID)},
        )
        for statement in (
            "DELETE FROM managed_knowledge_chunks WHERE collection_id = :id",
            "DELETE FROM knowledge_processing_runs WHERE document_id IN "
            "(SELECT id FROM managed_knowledge_documents WHERE collection_id = :id)",
            "DELETE FROM knowledge_audit_logs WHERE document_id IN "
            "(SELECT id FROM managed_knowledge_documents WHERE collection_id = :id)",
            "DELETE FROM knowledge_document_agent_bindings WHERE document_id IN "
            "(SELECT id FROM managed_knowledge_documents WHERE collection_id = :id)",
            "UPDATE managed_knowledge_documents SET current_version_id = NULL, "
            "published_version_id = NULL, active_version_id = NULL WHERE collection_id = :id",
            "DELETE FROM knowledge_document_versions WHERE document_id IN "
            "(SELECT id FROM managed_knowledge_documents WHERE collection_id = :id)",
            "DELETE FROM managed_knowledge_documents WHERE collection_id = :id",
            "DELETE FROM knowledge_collections WHERE id = :id",
        ):
            await session.execute(text(statement), {"id": collection_id})
        await session.commit()
