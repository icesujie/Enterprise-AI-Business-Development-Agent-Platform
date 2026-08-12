from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import text

from sari_api.adapters.database import session_factory
from sari_api.adapters.knowledge_embedding import DeterministicKnowledgeEmbeddingProvider
from sari_api.adapters.knowledge_ingestion import KnowledgeIngestionExecutor
from sari_api.adapters.knowledge_queue import get_knowledge_queue
from sari_api.adapters.knowledge_repository import SqlAlchemyKnowledgeRepository
from sari_api.adapters.knowledge_storage import LocalKnowledgeStorage, get_knowledge_storage
from sari_api.api.dependencies import get_token_identity
from sari_api.core.config import get_settings
from sari_api.domain.identity import TokenIdentity
from sari_api.domain.knowledge import ExtractedSection, chunk_sections
from sari_api.main import app

ADMIN_SUBJECT = "30000000-0000-4000-8000-000000000001"
SALES_SUBJECT = "30000000-0000-4000-8000-000000000002"
TENANT_ID = UUID("10000000-0000-4000-8000-000000000001")


async def admin_identity() -> TokenIdentity:
    return TokenIdentity(subject=ADMIN_SUBJECT, email="admin@sari-arta.example")


async def sales_identity() -> TokenIdentity:
    return TokenIdentity(subject=SALES_SUBJECT, email="sales@sari-arta.example")


class RecordingKnowledgeQueue:
    def __init__(self) -> None:
        self.messages: list[tuple[UUID, UUID, str | None]] = []

    async def enqueue(
        self,
        ingestion_run_id: UUID,
        tenant_id: UUID,
        *,
        correlation_id: str | None = None,
    ) -> None:
        self.messages.append((ingestion_run_id, tenant_id, correlation_id))


def test_chunking_preserves_page_and_overlap_boundaries() -> None:
    chunks = chunk_sections(
        [
            ExtractedSection(
                text="School kitchen ventilation and food safety. " * 20,
                page_number=3,
                section_title="Engineering scope",
            )
        ],
        chunk_size=180,
        overlap=30,
    )
    assert len(chunks) > 1
    assert [item.index for item in chunks] == list(range(len(chunks)))
    assert all(item.page_number == 3 for item in chunks)
    assert all(item.section_title == "Engineering scope" for item in chunks)


@pytest.mark.asyncio
async def test_knowledge_upload_approval_ingestion_retrieval_and_citations(
    tmp_path: Path,
) -> None:
    storage = LocalKnowledgeStorage(tmp_path / "knowledge")
    queue = RecordingKnowledgeQueue()
    app.dependency_overrides[get_token_identity] = admin_identity
    app.dependency_overrides[get_knowledge_storage] = lambda: storage
    app.dependency_overrides[get_knowledge_queue] = lambda: queue
    unique_term = f"syntheticmarker{uuid4().hex[:12]}"
    source_key = f"synthetic-sari-{uuid4().hex[:10]}"
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            source = await client.post(
                "/api/v1/knowledge/sources",
                json={
                    "source_key": source_key,
                    "name": "Synthetic Sari Arta Engineering Notes",
                    "description": "Approved synthetic validation material.",
                    "source_metadata": {"synthetic": True, "owner": "test"},
                },
            )
            assert source.status_code == 201, source.text
            source_id = source.json()["id"]

            binding = await client.post(
                f"/api/v1/knowledge/sources/{source_id}/bindings",
                json={
                    "domain_key": "commercial_kitchen",
                    "agent_key": "commercial_kitchen.lead_qualification",
                    "knowledge_category": "engineering_capabilities",
                },
            )
            assert binding.status_code == 201, binding.text

            synthetic_document = (
                "# Synthetic school kitchen design note\n\n"
                "A school central kitchen serving 3,000 meals per day requires separated raw "
                "and cooked food flows. The synthetic design includes receiving, dry storage, "
                "cold storage, preparation, cooking, plating and wash areas. Exhaust ventilation "
                "and fire safety remain subject to project-specific engineering review. "
                f"Validation marker: {unique_term}."
            )
            uploaded = await client.post(
                f"/api/v1/knowledge/sources/{source_id}/documents",
                data={
                    "title": "Synthetic School Central Kitchen Design Note",
                    "language": "en",
                    "source_metadata_json": '{"synthetic":true,"revision":"demo-v1"}',
                },
                files={
                    "file": (
                        "synthetic-school-kitchen.md",
                        synthetic_document.encode(),
                        "text/markdown",
                    )
                },
            )
            assert uploaded.status_code == 201, uploaded.text
            document_id = uploaded.json()["id"]
            assert uploaded.json()["approval_status"] == "pending"
            assert uploaded.json()["ingestion_status"] == "not_started"

            before_approval = await client.post(
                "/api/v1/knowledge/retrieval/search",
                json={
                    "domain_key": "commercial_kitchen",
                    "agent_key": "commercial_kitchen.lead_qualification",
                    "query": unique_term,
                    "minimum_similarity": 0,
                },
            )
            assert before_approval.status_code == 200, before_approval.text
            assert all(
                item["citation"]["document_id"] != document_id
                for item in before_approval.json()["results"]
            )

            review = await client.post(
                f"/api/v1/knowledge/documents/{document_id}/reviews",
                headers={"X-Correlation-ID": "knowledge-test-001"},
                json={"decision": "approved", "note": "Synthetic document approved for test."},
            )
            assert review.status_code == 200, review.text
            assert review.json()["document"]["approval_status"] == "approved"
            run_id = UUID(review.json()["ingestion_run"]["id"])
            assert queue.messages == [(run_id, TENANT_ID, "knowledge-test-001")]

            await KnowledgeIngestionExecutor(
                storage,
                DeterministicKnowledgeEmbeddingProvider(1536),
                get_settings(),
            ).execute(run_id, TENANT_ID)

            run = await client.get(f"/api/v1/knowledge/ingestion-runs/{run_id}")
            assert run.status_code == 200, run.text
            assert run.json()["status"] == "succeeded"
            assert run.json()["chunk_count"] >= 1

            search = await client.post(
                "/api/v1/knowledge/retrieval/search",
                json={
                    "domain_key": "commercial_kitchen",
                    "agent_key": "commercial_kitchen.lead_qualification",
                    "query": unique_term,
                    "minimum_similarity": 0,
                },
            )
            assert search.status_code == 200, search.text
            payload = search.json()
            assert payload["evidence_status"] == "sufficient_candidates"
            assert payload["results"]
            result = next(
                item
                for item in payload["results"]
                if item["citation"]["document_id"] == document_id
            )
            citation = result["citation"]
            assert citation["source_name"] == "Synthetic Sari Arta Engineering Notes"
            assert citation["document_id"] == document_id
            assert citation["document_title"] == "Synthetic School Central Kitchen Design Note"
            assert citation["filename"] == "synthetic-school-kitchen.md"
            assert citation["chunk_index"] == 0
            assert len(citation["content_sha256"]) == 64

            ivc_denied = await client.post(
                "/api/v1/knowledge/retrieval/search",
                json={
                    "domain_key": "laboratory_animal_facility",
                    "agent_key": "laboratory_animal_facility.ivc_business_development",
                    "query": "school kitchen ventilation",
                },
            )
            assert ivc_denied.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_sales_cannot_manage_knowledge() -> None:
    app.dependency_overrides[get_token_identity] = sales_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/knowledge/sources",
                json={"source_key": "sales-must-not-create", "name": "Forbidden source"},
            )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_document_approval_requires_an_explicit_agent_binding(tmp_path: Path) -> None:
    storage = LocalKnowledgeStorage(tmp_path / "knowledge")
    queue = RecordingKnowledgeQueue()
    app.dependency_overrides[get_token_identity] = admin_identity
    app.dependency_overrides[get_knowledge_storage] = lambda: storage
    app.dependency_overrides[get_knowledge_queue] = lambda: queue
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            source = await client.post(
                "/api/v1/knowledge/sources",
                json={
                    "source_key": f"unbound-source-{uuid4().hex[:10]}",
                    "name": "Synthetic unbound source",
                },
            )
            assert source.status_code == 201, source.text
            uploaded = await client.post(
                f"/api/v1/knowledge/sources/{source.json()['id']}/documents",
                data={"title": "Unbound synthetic note", "language": "en"},
                files={"file": ("unbound.txt", b"Synthetic unbound knowledge.", "text/plain")},
            )
            assert uploaded.status_code == 201, uploaded.text
            review = await client.post(
                f"/api/v1/knowledge/documents/{uploaded.json()['id']}/reviews",
                json={"decision": "approved"},
            )
    finally:
        app.dependency_overrides.clear()

    assert review.status_code == 409
    assert queue.messages == []


@pytest.mark.asyncio
async def test_knowledge_tables_force_rls_and_ivc_capability_remains_disabled() -> None:
    async with session_factory() as session:
        rls_rows = (
            await session.execute(
                text(
                    "SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity, p.policyname "
                    "FROM pg_class c JOIN pg_policies p ON p.tablename = c.relname "
                    "WHERE c.relname IN ('knowledge_sources','knowledge_bindings',"
                    "'knowledge_documents','knowledge_ingestion_runs','knowledge_chunks') "
                    "ORDER BY c.relname"
                )
            )
        ).all()
        bindings = (
            await session.execute(
                text(
                    "SELECT a.agent_key, b.status, "
                    "c.runtime_config->>'knowledge_enabled' AS enabled "
                    "FROM agent_capability_bindings b "
                    "JOIN agent_configurations c ON c.id = b.agent_configuration_id "
                    "JOIN agents a ON a.id = c.agent_id "
                    "JOIN agent_capabilities cap ON cap.id = b.capability_id "
                    "WHERE cap.capability_key = 'approved_knowledge_retrieval' "
                    "ORDER BY a.agent_key"
                )
            )
        ).all()
        other_tenant_repository = SqlAlchemyKnowledgeRepository(session, uuid4())
        await other_tenant_repository.set_tenant_context()
        cross_tenant_visible = await other_tenant_repository.list_sources()

    assert [row.relname for row in rls_rows] == [
        "knowledge_bindings",
        "knowledge_chunks",
        "knowledge_documents",
        "knowledge_ingestion_runs",
        "knowledge_sources",
    ]
    assert all(row.relrowsecurity and row.relforcerowsecurity for row in rls_rows)
    assert all(row.policyname == "tenant_isolation" for row in rls_rows)
    assert cross_tenant_visible == []
    by_agent = {row.agent_key: (row.status, row.enabled) for row in bindings}
    assert by_agent["commercial_kitchen.lead_qualification"] == ("available", "true")
    assert by_agent["laboratory_animal_facility.ivc_business_development"] == (
        "planned",
        "false",
    )
