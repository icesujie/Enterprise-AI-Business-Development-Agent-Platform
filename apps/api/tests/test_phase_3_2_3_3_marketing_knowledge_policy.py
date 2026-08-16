from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.database import session_factory
from sari_api.adapters.knowledge_embedding import DeterministicKnowledgeEmbeddingProvider
from sari_api.adapters.managed_knowledge_retrieval import (
    ManagedKnowledgeRetrievalDeniedError,
    ManagedKnowledgeRetrievalRepository,
)
from sari_api.adapters.models import (
    Agent,
    KnowledgeCollection,
    KnowledgeDocumentAgentBinding,
    KnowledgeDocumentVersion,
    KnowledgeProcessingRun,
    ManagedKnowledgeChunk,
    ManagedKnowledgeDocument,
    TenantAgentActivation,
)
from sari_api.api.dependencies import get_token_identity
from sari_api.domain.identity import TokenIdentity
from sari_api.domain.marketing_knowledge_policy import MARKETING_CONTENT_AGENT_ID
from sari_api.main import app

TENANT_ID = UUID("10000000-0000-4000-8000-000000000001")
ADMIN_USER_ID = UUID("20000000-0000-4000-8000-000000000001")
ADMIN_SUBJECT = "30000000-0000-4000-8000-000000000001"
SARI_AGENT_ID = UUID("61000000-0000-4000-8000-000000000001")
COMMERCIAL_DOMAIN_ID = UUID("60000000-0000-4000-8000-000000000001")
IVC_DOMAIN_ID = UUID("60000000-0000-4000-8000-000000000002")


async def admin_identity() -> TokenIdentity:
    return TokenIdentity(subject=ADMIN_SUBJECT, email="admin@sari-arta.example")


@pytest.mark.asyncio
async def test_marketing_registry_identity_capability_and_activation_boundary() -> None:
    app.dependency_overrides[get_token_identity] = admin_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/agent-registry/agents/commercial_kitchen.marketing_content",
                params={"locale": "zh-CN"},
            )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["id"] == str(MARKETING_CONTENT_AGENT_ID)
        assert payload["name"] == "Sari Arta 营销内容智能体"
        assert payload["domain_key"] == "commercial_kitchen"
        assert payload["supported_locales"] == ["en", "zh-CN"]
        assert payload["activation_status"] == "active"
        capabilities = {item["key"]: item for item in payload["versions"][0]["capabilities"]}
        marketing = capabilities["public_marketing_content_generation"]
        assert marketing["required"] is True
        assert marketing["status"] == "available"

        async with session_factory() as session:
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(TENANT_ID)},
            )
            rows = (
                await session.execute(
                    select(
                        TenantAgentActivation.environment,
                        TenantAgentActivation.status,
                        TenantAgentActivation.rollout_percentage,
                    )
                    .where(
                        TenantAgentActivation.tenant_id == TENANT_ID,
                        TenantAgentActivation.agent_id == MARKETING_CONTENT_AGENT_ID,
                    )
                    .order_by(TenantAgentActivation.environment)
                )
            ).all()
        assert rows == [("development", "active", 100), ("production", "pending", 0)]

        async with session_factory() as session:
            repository = ManagedKnowledgeRetrievalRepository(
                session, TENANT_ID, environment="production"
            )
            await repository.set_tenant_context()
            with pytest.raises(ManagedKnowledgeRetrievalDeniedError):
                await repository.ensure_agent_retrieval_enabled(MARKETING_CONTENT_AGENT_ID)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_marketing_retrieval_allows_only_explicit_public_marketing_knowledge(
    caplog: pytest.LogCaptureFixture,
) -> None:
    collection_ids = await seed_policy_fixture()
    app.dependency_overrides[get_token_identity] = admin_identity
    caplog.set_level(logging.INFO, logger="sari_api.marketing_knowledge_policy")
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/knowledge/search",
                json={
                    "tenant_id": str(TENANT_ID),
                    "agent_id": str(MARKETING_CONTENT_AGENT_ID),
                    "query": "synthetic public marketing boundary consultation",
                    "language": "en",
                    "top_k": 20,
                },
            )
        assert response.status_code == 200, response.text
        results = response.json()["results"]
        assert [item["document_name"] for item in results] == ["Allowed Public Company Profile"]
        assert results[0]["metadata"]["document_metadata"]["knowledge_class"] == (
            "public_company_profile"
        )
        decisions = [
            record
            for record in caplog.records
            if getattr(record, "event", None) == "marketing.knowledge_policy.decision"
        ]
        assert any(
            getattr(record, "outcome", None) == "allow"
            and getattr(record, "policy_reason", None)
            == "public_marketing_policy_authorized"
            for record in decisions
        )
        assert all(not hasattr(record, "knowledge_content") for record in decisions)
    finally:
        app.dependency_overrides.clear()
        await cleanup_collections(collection_ids)


@pytest.mark.asyncio
async def test_marketing_policy_rejects_cross_tenant_before_embedding_or_retrieval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider_called = False
    search_called = False

    def forbidden_provider(_: object) -> object:
        nonlocal provider_called
        provider_called = True
        raise AssertionError("embedding provider must not be called")

    async def forbidden_search(*_: object, **__: object) -> object:
        nonlocal search_called
        search_called = True
        raise AssertionError("retrieval must not be called")

    monkeypatch.setattr(
        "sari_api.api.routes.knowledge_retrieval.build_knowledge_embedding_provider",
        forbidden_provider,
    )
    monkeypatch.setattr(
        "sari_api.adapters.managed_knowledge_retrieval."
        "ManagedKnowledgeRetrievalRepository.search",
        forbidden_search,
    )
    app.dependency_overrides[get_token_identity] = admin_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/knowledge/search",
                json={
                    "tenant_id": str(uuid4()),
                    "agent_id": str(MARKETING_CONTENT_AGENT_ID),
                    "query": "public marketing boundary",
                    "language": "en",
                    "top_k": 5,
                },
            )
        assert response.status_code == 403
        assert provider_called is False
        assert search_called is False
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_inactive_marketing_agent_is_denied_before_embedding_or_retrieval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider_called = False
    search_called = False

    def forbidden_provider(_: object) -> object:
        nonlocal provider_called
        provider_called = True
        raise AssertionError("embedding provider must not be called")

    async def forbidden_search(*_: object, **__: object) -> object:
        nonlocal search_called
        search_called = True
        raise AssertionError("retrieval must not be called")

    monkeypatch.setattr(
        "sari_api.api.routes.knowledge_retrieval.build_knowledge_embedding_provider",
        forbidden_provider,
    )
    monkeypatch.setattr(
        "sari_api.adapters.managed_knowledge_retrieval."
        "ManagedKnowledgeRetrievalRepository.search",
        forbidden_search,
    )
    await set_development_activation("suspended")
    app.dependency_overrides[get_token_identity] = admin_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/knowledge/search",
                json={
                    "tenant_id": str(TENANT_ID),
                    "agent_id": str(MARKETING_CONTENT_AGENT_ID),
                    "query": "public marketing boundary",
                    "language": "en",
                    "top_k": 5,
                },
            )
        assert response.status_code == 403
        assert provider_called is False
        assert search_called is False
    finally:
        app.dependency_overrides.clear()
        await set_development_activation("active")


async def seed_policy_fixture() -> list[UUID]:
    suffix = uuid4().hex[:10]
    provider = DeterministicKnowledgeEmbeddingProvider(1536)
    collection_ids: list[UUID] = []
    async with session_factory() as session:
        await set_context(session)
        marketing_agent = await session.get(Agent, MARKETING_CONTENT_AGENT_ID)
        sari_agent = await session.get(Agent, SARI_AGENT_ID)
        assert marketing_agent is not None and sari_agent is not None

        public_collection = await add_collection(
            session,
            suffix=f"public-{suffix}",
            domain_id=COMMERCIAL_DOMAIN_ID,
            visibility="public_marketing",
        )
        internal_collection = await add_collection(
            session,
            suffix=f"internal-{suffix}",
            domain_id=COMMERCIAL_DOMAIN_ID,
            visibility="internal",
        )
        cross_domain_collection = await add_collection(
            session,
            suffix=f"cross-domain-{suffix}",
            domain_id=IVC_DOMAIN_ID,
            visibility="public_marketing",
        )
        collection_ids.extend(
            [public_collection.id, internal_collection.id, cross_domain_collection.id]
        )

        common = "Synthetic public marketing boundary consultation engineering capability."
        await add_policy_document(
            session,
            collection=public_collection,
            agent=marketing_agent,
            title="Allowed Public Company Profile",
            knowledge_class="public_company_profile",
            content=common,
            provider=provider,
        )
        for title, knowledge_class in (
            ("Forbidden Internal Pricing", "internal_pricing"),
            ("Forbidden Private Customer", "private_customer_information"),
            ("Forbidden Internal SOP", "internal_sop"),
        ):
            await add_policy_document(
                session,
                collection=public_collection,
                agent=marketing_agent,
                title=title,
                knowledge_class=knowledge_class,
                content=common,
                provider=provider,
            )
        await add_policy_document(
            session,
            collection=internal_collection,
            agent=marketing_agent,
            title="Internal Collection Company Profile",
            knowledge_class="public_company_profile",
            content=common,
            provider=provider,
        )
        await add_policy_document(
            session,
            collection=public_collection,
            agent=marketing_agent,
            title="Unpublished Public Draft",
            knowledge_class="public_marketing_reference",
            content=common,
            provider=provider,
            active=False,
        )
        await add_policy_document(
            session,
            collection=public_collection,
            agent=marketing_agent,
            title="Unapproved Public Reference",
            knowledge_class="public_marketing_reference",
            content=common,
            provider=provider,
            approved=False,
        )
        await add_policy_document(
            session,
            collection=public_collection,
            agent=sari_agent,
            title="Other Agent Public Reference",
            knowledge_class="public_marketing_reference",
            content=common,
            provider=provider,
        )
        await add_policy_document(
            session,
            collection=cross_domain_collection,
            agent=marketing_agent,
            title="Cross Domain Public Reference",
            knowledge_class="public_marketing_reference",
            content=common,
            provider=provider,
        )
        await session.commit()
    return collection_ids


async def add_collection(
    session: AsyncSession,
    *,
    suffix: str,
    domain_id: UUID,
    visibility: str,
) -> KnowledgeCollection:
    collection = KnowledgeCollection(
        tenant_id=TENANT_ID,
        domain_package_id=domain_id,
        collection_key=f"marketing-policy-{suffix}",
        name=f"Synthetic Marketing Policy {suffix}",
        description="Synthetic Phase 3.2.3.3 policy validation.",
        collection_metadata={"synthetic": True, "visibility": visibility},
        created_by=ADMIN_USER_ID,
    )
    session.add(collection)
    await session.flush()
    return collection


async def add_policy_document(
    session: AsyncSession,
    *,
    collection: KnowledgeCollection,
    agent: Agent,
    title: str,
    knowledge_class: str,
    content: str,
    provider: DeterministicKnowledgeEmbeddingProvider,
    active: bool = True,
    approved: bool = True,
) -> None:
    now = datetime.now(UTC)
    metadata = {"synthetic": True, "knowledge_class": knowledge_class}
    document = ManagedKnowledgeDocument(
        tenant_id=TENANT_ID,
        domain_package_id=collection.domain_package_id,
        agent_id=agent.id,
        collection_id=collection.id,
        title=title,
        document_type="marketing_reference",
        language="en",
        lifecycle_status="active" if active else "approved",
        approval_status="approved" if approved else "pending",
        processing_status="completed",
        current_version_number=1,
        document_metadata=metadata,
        approved_by=ADMIN_USER_ID if approved else None,
        approved_at=now if approved else None,
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
        object_key=f"synthetic/marketing-policy/{document.id}.md",
        content_sha256=digest,
        byte_size=len(content.encode()),
        version_metadata=metadata,
        status="active" if active else "approved",
        review_status="approved" if approved else "pending",
        reviewed_by=ADMIN_USER_ID if approved else None,
        reviewed_at=now if approved else None,
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
        source_metadata_snapshot=metadata,
        completed_at=now,
        created_by=ADMIN_USER_ID,
    )
    session.add(run)
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
            domain_package_id=collection.domain_package_id,
            agent_id=agent.id,
            collection_id=collection.id,
            document_id=document.id,
            document_version_id=version.id,
            processing_run_id=run.id,
            chunk_index=0,
            content=content,
            content_sha256=digest,
            character_count=len(content),
            page_number=1,
            section_title="Synthetic policy section",
            language="en",
            document_type="marketing_reference",
            source_metadata={"synthetic": True, "document_metadata": metadata},
            citation_metadata={
                "document_id": str(document.id),
                "document_version_id": str(version.id),
                "version_number": 1,
                "page_number": 1,
                "section_title": "Synthetic policy section",
            },
            embedding=embedding,
            embedding_provider=provider.provider_type,
            embedding_model=provider.model_id,
        )
    )


async def set_development_activation(status: str) -> None:
    async with session_factory() as session:
        await set_context(session)
        activation = await session.scalar(
            select(TenantAgentActivation).where(
                TenantAgentActivation.tenant_id == TENANT_ID,
                TenantAgentActivation.agent_id == MARKETING_CONTENT_AGENT_ID,
                TenantAgentActivation.environment == "development",
            )
        )
        assert activation is not None
        activation.status = status
        await session.commit()


async def set_context(session: AsyncSession) -> None:
    await session.execute(
        text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
        {"tenant_id": str(TENANT_ID)},
    )


async def cleanup_collections(collection_ids: list[UUID]) -> None:
    async with session_factory() as session:
        await set_context(session)
        for collection_id in collection_ids:
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
