from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import select, text

from sari_api.adapters.database import session_factory
from sari_api.adapters.knowledge_storage import LocalKnowledgeStorage, get_knowledge_storage
from sari_api.adapters.models import KnowledgeAuditLog
from sari_api.api.dependencies import get_token_identity
from sari_api.domain.identity import TokenIdentity
from sari_api.main import app

TENANT_ID = UUID("10000000-0000-4000-8000-000000000001")
ADMIN_SUBJECT = "30000000-0000-4000-8000-000000000001"
SALES_SUBJECT = "30000000-0000-4000-8000-000000000002"


async def admin_identity() -> TokenIdentity:
    return TokenIdentity(subject=ADMIN_SUBJECT, email="admin@sari-arta.example")


async def sales_identity() -> TokenIdentity:
    return TokenIdentity(subject=SALES_SUBJECT, email="sales@sari-arta.example")


@pytest.mark.asyncio
async def test_version_governance_concurrency_rollback_and_audit(tmp_path: Path) -> None:
    storage = LocalKnowledgeStorage(tmp_path / "governed")
    app.dependency_overrides[get_token_identity] = admin_identity
    app.dependency_overrides[get_knowledge_storage] = lambda: storage
    suffix = uuid4().hex[:10]
    collection_id: str | None = None
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            collection = await client.post(
                "/api/v1/knowledge-management/collections",
                json={
                    "domain_key": "commercial_kitchen",
                    "collection_key": f"governance-{suffix}",
                    "name": f"Synthetic Governance {suffix}",
                },
            )
            assert collection.status_code == 201, collection.text
            collection_id = collection.json()["id"]
            upload = await client.post(
                f"/api/v1/knowledge-management/collections/{collection_id}/documents",
                data={
                    "title": f"Synthetic Governed Document {suffix}",
                    "document_type": "technical_reference",
                    "language": "en",
                    "document_metadata_json": '{"synthetic":true,"classification":"internal"}',
                },
                files={"file": ("v1.md", b"Synthetic governed version one.", "text/markdown")},
            )
            assert upload.status_code == 201, upload.text
            document = upload.json()
            document_id = document["id"]
            version_one_id = document["current_version_id"]
            assert document["record_version"] == 1
            assert document["published_version_id"] is None
            assert document["active_version_id"] is None

            metadata = await client.patch(
                f"/api/v1/knowledge-management/documents/{document_id}",
                headers={"If-Match": '"1"'},
                json={"title": f"Governed Kitchen Standard {suffix}"},
            )
            assert metadata.status_code == 200, metadata.text
            assert metadata.json()["record_version"] == 2

            awaiting_review = await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/submit-review"
            )
            assert awaiting_review.status_code == 200, awaiting_review.text
            invalidated = await client.patch(
                f"/api/v1/knowledge-management/documents/{document_id}",
                headers={"If-Match": '"3"'},
                json={"document_metadata": {"synthetic": True, "classification": "internal-v2"}},
            )
            assert invalidated.status_code == 200, invalidated.text
            assert invalidated.json()["lifecycle_status"] == "uploaded"
            assert invalidated.json()["approval_status"] == "pending"
            assert invalidated.json()["record_version"] == 4

            async def create_candidate(filename: str, body: bytes) -> httpx.Response:
                return await client.post(
                    f"/api/v1/knowledge-management/documents/{document_id}/versions",
                    headers={"If-Match": '"4"'},
                    data={"version_metadata_json": '{"synthetic":true}'},
                    files={"file": (filename, body, "text/markdown")},
                )

            candidates = await asyncio.gather(
                create_candidate("v2-a.md", b"Synthetic governed version two candidate A."),
                create_candidate("v2-b.md", b"Synthetic governed version two candidate B."),
            )
            assert sorted(item.status_code for item in candidates) == [201, 412]
            created = next(item for item in candidates if item.status_code == 201).json()
            version_two_id = created["current_version_id"]
            assert created["current_version_number"] == 2
            assert created["record_version"] == 5

            versions = await client.get(
                f"/api/v1/knowledge-management/documents/{document_id}/versions"
            )
            assert versions.status_code == 200
            assert [item["version_number"] for item in versions.json()] == [2, 1]

            submitted = await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/submit-review"
            )
            assert submitted.status_code == 200, submitted.text
            approved = await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/approval",
                json={"decision": "approved", "note": "Synthetic governance approval."},
            )
            assert approved.status_code == 200, approved.text

            binding = await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/bindings",
                json={"agent_key": "commercial_kitchen.lead_qualification"},
            )
            assert binding.status_code == 201, binding.text
            binding_id = binding.json()["id"]

            published = await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/publish"
            )
            assert published.status_code == 200, published.text
            assert published.json()["published_version_id"] == version_two_id
            activated = await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/activate"
            )
            assert activated.status_code == 200, activated.text
            assert activated.json()["active_version_id"] == version_two_id

            rollback = await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/versions/"
                f"{version_one_id}/rollback",
                headers={"If-Match": f'"{activated.json()["record_version"]}"'},
                json={"reason": "Synthetic rollback safety validation."},
            )
            assert rollback.status_code == 201, rollback.text
            rolled_back = rollback.json()
            assert rolled_back["current_version_number"] == 3
            assert rolled_back["active_version_id"] == version_two_id
            version_three_id = rolled_back["current_version_id"]
            assert version_three_id not in {version_one_id, version_two_id}

            rollback_version = await client.get(
                f"/api/v1/knowledge-management/documents/{document_id}/versions/{version_three_id}"
            )
            assert rollback_version.json()["restored_from_version_id"] == version_one_id
            assert rollback_version.json()["created_from_action"] == "rollback"

            await client.post(f"/api/v1/knowledge-management/documents/{document_id}/submit-review")
            await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/approval",
                json={"decision": "approved", "note": "Approved restored content."},
            )
            await client.post(f"/api/v1/knowledge-management/documents/{document_id}/publish")
            reactivated = await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/activate"
            )
            assert reactivated.status_code == 200, reactivated.text
            assert reactivated.json()["active_version_id"] == version_three_id

            archived = await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/archive",
                json={"reason": "Synthetic scheduled archive."},
            )
            assert archived.status_code == 200, archived.text
            assert archived.json()["active_version_id"] is None
            restored = await client.post(
                f"/api/v1/knowledge-management/documents/{document_id}/restore",
                json={"reason": "Synthetic restore for review."},
            )
            assert restored.status_code == 200, restored.text
            assert restored.json()["lifecycle_status"] == "approved"
            assert restored.json()["active_version_id"] is None

            disabled = await client.patch(
                f"/api/v1/knowledge-management/documents/{document_id}/bindings/{binding_id}",
                json={"status": "disabled", "reason": "Synthetic access revocation."},
            )
            assert disabled.status_code == 200, disabled.text
            assert disabled.json()["status"] == "disabled"
            enabled = await client.patch(
                f"/api/v1/knowledge-management/documents/{document_id}/bindings/{binding_id}",
                json={"status": "enabled", "reason": "Synthetic access restoration."},
            )
            assert enabled.status_code == 200, enabled.text

            audit = await client.get(
                f"/api/v1/knowledge-management/documents/{document_id}/audit-events"
            )
            assert audit.status_code == 200, audit.text
            actions = {item["action"] for item in audit.json()}
            assert {
                "upload",
                "metadata_update",
                "version_creation",
                "approval",
                "publish",
                "activate",
                "rollback",
                "archive",
                "restore",
                "agent_binding_disabled",
                "agent_binding_enabled",
            }.issubset(actions)
            assert all(item["actor_display_name"] for item in audit.json())
    finally:
        app.dependency_overrides.clear()
        if collection_id:
            await cleanup_collection(UUID(collection_id))


@pytest.mark.asyncio
async def test_sales_role_cannot_cross_governance_permission_boundaries() -> None:
    app.dependency_overrides[get_token_identity] = sales_identity
    document_id = uuid4()
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            checks = [
                await client.post(
                    "/api/v1/knowledge-management/collections",
                    json={
                        "domain_key": "commercial_kitchen",
                        "collection_key": f"forbidden-{uuid4().hex[:10]}",
                        "name": "Forbidden governance collection",
                    },
                ),
                await client.patch(
                    f"/api/v1/knowledge-management/documents/{document_id}",
                    headers={"If-Match": '"1"'},
                    json={"title": "Forbidden edit"},
                ),
                await client.post(
                    f"/api/v1/knowledge-management/documents/{document_id}/submit-review"
                ),
                await client.post(
                    f"/api/v1/knowledge-management/documents/{document_id}/approval",
                    json={"decision": "approved"},
                ),
                await client.post(f"/api/v1/knowledge-management/documents/{document_id}/publish"),
                await client.post(
                    f"/api/v1/knowledge-management/documents/{document_id}/archive",
                    json={"reason": "Forbidden archive"},
                ),
                await client.post(
                    f"/api/v1/knowledge-management/documents/{document_id}/restore",
                    json={"reason": "Forbidden restore"},
                ),
                await client.get(
                    f"/api/v1/knowledge-management/documents/{document_id}/audit-events"
                ),
            ]
    finally:
        app.dependency_overrides.clear()
    assert {item.status_code for item in checks} == {403}


@pytest.mark.asyncio
async def test_knowledge_audit_log_forces_tenant_rls() -> None:
    other_tenant_id = uuid4()
    async with session_factory() as session:
        row = (
            await session.execute(
                text(
                    "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
                    "WHERE relname = 'knowledge_audit_logs'"
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
                    select(KnowledgeAuditLog).where(KnowledgeAuditLog.tenant_id == other_tenant_id)
                )
            ).all()
        )
    assert row == (True, True)
    assert visible == []


async def cleanup_collection(collection_id: UUID) -> None:
    async with session_factory() as cleanup:
        await cleanup.execute(
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
            await cleanup.execute(text(statement), {"id": collection_id})
        await cleanup.commit()
