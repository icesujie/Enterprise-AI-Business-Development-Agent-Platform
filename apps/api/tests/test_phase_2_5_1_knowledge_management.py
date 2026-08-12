from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import text

from sari_api.adapters.database import session_factory
from sari_api.adapters.enterprise_knowledge_repository import EnterpriseKnowledgeRepository
from sari_api.adapters.knowledge_storage import LocalKnowledgeStorage, get_knowledge_storage
from sari_api.api.dependencies import get_token_identity
from sari_api.domain.identity import TokenIdentity
from sari_api.main import app

ADMIN_SUBJECT = "30000000-0000-4000-8000-000000000001"
SALES_SUBJECT = "30000000-0000-4000-8000-000000000002"


async def admin_identity() -> TokenIdentity:
    return TokenIdentity(subject=ADMIN_SUBJECT, email="admin@sari-arta.example")


async def sales_identity() -> TokenIdentity:
    return TokenIdentity(subject=SALES_SUBJECT, email="sales@sari-arta.example")


@pytest.mark.asyncio
async def test_collection_document_lifecycle_binding_and_search(tmp_path: Path) -> None:
    app.dependency_overrides[get_token_identity] = admin_identity
    app.dependency_overrides[get_knowledge_storage] = lambda: LocalKnowledgeStorage(tmp_path)
    suffix = uuid4().hex[:10]
    collection_id: str | None = None
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            collection = await client.post(
                "/api/v1/knowledge-management/collections",
                json={
                    "domain_key": "commercial_kitchen",
                    "collection_key": f"school-cases-{suffix}",
                    "name": f"Synthetic School Cases {suffix}",
                    "description": "Synthetic test collection.",
                },
            )
            assert collection.status_code == 201, collection.text
            collection_id = collection.json()["id"]

            upload = await client.post(
                f"/api/v1/knowledge-management/collections/{collection_id}/documents",
                data={
                    "title": f"Synthetic School Kitchen Case {suffix}",
                    "document_type": "case_study",
                    "language": "en",
                    "document_metadata_json": '{"synthetic":true}',
                },
                files={"file": ("case.md", b"Synthetic case content.", "text/markdown")},
            )
            assert upload.status_code == 201, upload.text
            document_id = upload.json()["id"]
            assert upload.json()["lifecycle_status"] == "uploaded"
            assert upload.json()["current_version"]["version_number"] == 1

            listed = await client.get(
                "/api/v1/knowledge-management/documents", params={"search": suffix}
            )
            assert listed.status_code == 200
            assert [item["id"] for item in listed.json()] == [document_id]

            submitted = await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/submit-review"
            )
            assert submitted.status_code == 200, submitted.text
            assert submitted.json()["lifecycle_status"] == "review"

            approved = await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/approval",
                json={"decision": "approved", "note": "Synthetic test approval."},
            )
            assert approved.status_code == 200, approved.text
            assert approved.json()["lifecycle_status"] == "approved"

            unbound_activation = await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/activate"
            )
            assert unbound_activation.status_code == 409

            wrong_domain = await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/bindings",
                json={"agent_key": "laboratory_animal_facility.ivc_business_development"},
            )
            assert wrong_domain.status_code == 403

            binding = await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/bindings",
                json={"agent_key": "commercial_kitchen.lead_qualification"},
            )
            assert binding.status_code == 201, binding.text

            activated = await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/activate"
            )
            assert activated.status_code == 200, activated.text
            assert activated.json()["lifecycle_status"] == "active"

            detail = await client.get(f"/api/v1/knowledge-management/documents/{document_id}")
            assert detail.status_code == 200
            assert detail.json()["bindings"][0]["agent_key"] == (
                "commercial_kitchen.lead_qualification"
            )
    finally:
        app.dependency_overrides.clear()
        if collection_id:
            async with session_factory() as cleanup:
                await cleanup.execute(
                    text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                    {"tenant_id": "10000000-0000-4000-8000-000000000001"},
                )
                for statement in (
                    "DELETE FROM knowledge_document_agent_bindings WHERE document_id IN "
                    "(SELECT id FROM managed_knowledge_documents WHERE collection_id = :id)",
                    "DELETE FROM knowledge_document_versions WHERE document_id IN "
                    "(SELECT id FROM managed_knowledge_documents WHERE collection_id = :id)",
                    "DELETE FROM managed_knowledge_documents WHERE collection_id = :id",
                    "DELETE FROM knowledge_collections WHERE id = :id",
                ):
                    await cleanup.execute(text(statement), {"id": collection_id})
                await cleanup.commit()


@pytest.mark.asyncio
async def test_sales_user_cannot_manage_enterprise_knowledge() -> None:
    app.dependency_overrides[get_token_identity] = sales_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/knowledge-management/collections",
                json={
                    "domain_key": "commercial_kitchen",
                    "collection_key": f"forbidden-{uuid4().hex[:10]}",
                    "name": "Forbidden collection",
                },
            )
            readable = await client.get("/api/v1/knowledge-management/collections")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 403
    assert readable.status_code == 200


@pytest.mark.asyncio
async def test_management_tables_force_tenant_rls() -> None:
    async with session_factory() as session:
        rows = (
            await session.execute(
                text(
                    "SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity "
                    "FROM pg_class c WHERE c.relname IN "
                    "('knowledge_collections','managed_knowledge_documents',"
                    "'knowledge_document_versions','knowledge_document_agent_bindings') "
                    "ORDER BY c.relname"
                )
            )
        ).all()
        other_tenant = EnterpriseKnowledgeRepository(session, uuid4())
        await other_tenant.set_tenant_context()
        cross_tenant_visible = await other_tenant.list_collections()
    assert len(rows) == 4
    assert all(row[1] and row[2] for row in rows)
    assert cross_tenant_visible == []
