from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from sari_api.adapters.database import session_factory
from sari_api.adapters.models import ContentAuditLog, ContentVersion
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


def asset_payload(suffix: str) -> dict[str, object]:
    return {
        "domain_key": "commercial_kitchen",
        "title": f"Synthetic School Kitchen Article {suffix}",
        "content_type": "website_article",
        "audience": "schools",
        "language": "en",
        "channel": "website",
        "content_body": {"headline": "A synthetic school kitchen"},
        "plain_text": "A synthetic school kitchen reference for governance testing.",
        "claims": [],
        "citations": [],
    }


def mutation_headers(key: str, version: int | None = None) -> dict[str, str]:
    headers = {"Idempotency-Key": key}
    if version is not None:
        headers["If-Match"] = f'"{version}"'
    return headers


@pytest.mark.asyncio
async def test_content_version_governance_concurrency_approval_rollback_and_audit() -> None:
    suffix = uuid4().hex[:10]
    app.dependency_overrides[get_token_identity] = sales_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            request_payload = {
                "domain_key": "commercial_kitchen",
                "content_type": "website_article",
                "audience": "schools",
                "language": "en",
                "channel": "website",
                "business_objective": "Explain a synthetic school kitchen capability.",
                "topic": f"Synthetic governance case {suffix}",
                "call_to_action": "Request a consultation",
            }
            request_key = f"request-{suffix}"
            created_request = await client.post(
                "/api/v1/content/requests",
                headers=mutation_headers(request_key),
                json=request_payload,
            )
            assert created_request.status_code == 201, created_request.text
            repeated_request = await client.post(
                "/api/v1/content/requests",
                headers=mutation_headers(request_key),
                json=request_payload,
            )
            assert repeated_request.status_code == 201
            assert repeated_request.json()["id"] == created_request.json()["id"]

            payload = asset_payload(suffix)
            payload["request_id"] = created_request.json()["id"]
            created = await client.post(
                "/api/v1/content/assets",
                headers=mutation_headers(f"asset-{suffix}"),
                json=payload,
            )
            assert created.status_code == 201, created.text
            asset = created.json()
            asset_id = asset["id"]
            version_one = asset["current_version"]
            assert asset["status"] == "draft"
            assert version_one["version_number"] == 1

            async def create_candidate(label: str) -> httpx.Response:
                return await client.post(
                    f"/api/v1/content/assets/{asset_id}/versions",
                    headers=mutation_headers(f"version-{suffix}-{label}", 1),
                    json={
                        "content_body": {"headline": f"Synthetic candidate {label}"},
                        "plain_text": f"Synthetic candidate {label}.",
                        "claims": [],
                        "citations": [],
                    },
                )

            candidates = await asyncio.gather(create_candidate("a"), create_candidate("b"))
            assert sorted(item.status_code for item in candidates) == [201, 412]
            versioned = next(item for item in candidates if item.status_code == 201).json()
            version_two = versioned["current_version"]
            assert version_two["version_number"] == 2
            assert versioned["record_version"] == 2

            submitted = await client.post(
                f"/api/v1/content/assets/{asset_id}/submit-review",
                headers=mutation_headers(f"submit-{suffix}", 2),
                json={
                    "content_version_id": version_two["id"],
                    "content_sha256": version_two["content_sha256"],
                    "comment": "Synthetic review submission.",
                },
            )
            assert submitted.status_code == 200, submitted.text
            assert submitted.json()["asset"]["status"] == "review"

            forbidden_approval = await client.post(
                f"/api/v1/content/assets/{asset_id}/decisions",
                headers=mutation_headers(f"sales-approve-{suffix}", 3),
                json={
                    "content_version_id": version_two["id"],
                    "content_sha256": version_two["content_sha256"],
                    "decision": "approved",
                    "comment": "Sales must not approve.",
                },
            )
            assert forbidden_approval.status_code == 403

            app.dependency_overrides[get_token_identity] = admin_identity
            approved = await client.post(
                f"/api/v1/content/assets/{asset_id}/decisions",
                headers=mutation_headers(f"admin-approve-{suffix}", 3),
                json={
                    "content_version_id": version_two["id"],
                    "content_sha256": version_two["content_sha256"],
                    "decision": "approved",
                    "comment": "Synthetic independent approval.",
                },
            )
            assert approved.status_code == 200, approved.text
            approved_asset = approved.json()["asset"]
            assert approved_asset["status"] == "approved"
            assert approved_asset["approved_version_id"] == version_two["id"]

            app.dependency_overrides[get_token_identity] = sales_identity
            edited = await client.post(
                f"/api/v1/content/assets/{asset_id}/versions",
                headers=mutation_headers(f"edit-after-approval-{suffix}", 4),
                json={
                    "content_body": {"headline": "Edited after approval"},
                    "plain_text": "Synthetic material edit after approval.",
                    "claims": [],
                    "citations": [],
                },
            )
            assert edited.status_code == 201, edited.text
            assert edited.json()["status"] == "draft"
            assert edited.json()["approved_version_id"] == version_two["id"]
            assert edited.json()["current_version"]["version_number"] == 3

            rolled_back = await client.post(
                f"/api/v1/content/assets/{asset_id}/rollback",
                headers=mutation_headers(f"rollback-{suffix}", 5),
                json={"source_version_id": version_one["id"]},
            )
            assert rolled_back.status_code == 201, rolled_back.text
            rollback = rolled_back.json()["current_version"]
            assert rollback["version_number"] == 4
            assert rollback["origin"] == "rollback"
            assert rollback["based_on_version_id"] == version_one["id"]
            assert rolled_back.json()["approved_version_id"] == version_two["id"]

            archive_denied = await client.post(
                f"/api/v1/content/assets/{asset_id}/archive",
                headers=mutation_headers(f"sales-archive-{suffix}", 6),
                json={"reason": "Sales cannot archive governed content."},
            )
            assert archive_denied.status_code == 403

            app.dependency_overrides[get_token_identity] = admin_identity
            archived = await client.post(
                f"/api/v1/content/assets/{asset_id}/archive",
                headers=mutation_headers(f"admin-archive-{suffix}", 6),
                json={"reason": "Synthetic lifecycle archive."},
            )
            assert archived.status_code == 200, archived.text
            assert archived.json()["status"] == "archived"
            restored = await client.post(
                f"/api/v1/content/assets/{asset_id}/restore",
                headers=mutation_headers(f"admin-restore-{suffix}", 7),
                json={"reason": "Synthetic lifecycle restore."},
            )
            assert restored.status_code == 200, restored.text
            assert restored.json()["status"] == "draft"
            assert restored.json()["approved_version_id"] == version_two["id"]

            audit = await client.get(f"/api/v1/content/assets/{asset_id}/audit")
            assert audit.status_code == 200, audit.text
            actions = {entry["action"] for entry in audit.json()}
            assert {
                "content.asset_created",
                "content.version_created",
                "content.edited",
                "content.review_submitted",
                "content.approved",
                "content.rollback",
                "content.archived",
                "content.restored",
            }.issubset(actions)

            app.dependency_overrides[get_token_identity] = sales_identity
            audit_denied = await client.get(f"/api/v1/content/assets/{asset_id}/audit")
            assert audit_denied.status_code == 403

        async with session_factory() as session:
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(TENANT_ID)},
            )
            with pytest.raises(DBAPIError, match="governed content history is immutable"):
                await session.execute(
                    text("UPDATE content_versions SET plain_text = 'mutated' WHERE id = :id"),
                    {"id": rollback["id"]},
                )
                await session.flush()
            await session.rollback()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_creator_cannot_approve_own_content_and_checksum_is_exact() -> None:
    suffix = uuid4().hex[:10]
    app.dependency_overrides[get_token_identity] = admin_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/api/v1/content/assets",
                headers=mutation_headers(f"admin-asset-{suffix}"),
                json=asset_payload(suffix),
            )
            assert created.status_code == 201, created.text
            asset = created.json()
            version = asset["current_version"]

            wrong_checksum = await client.post(
                f"/api/v1/content/assets/{asset['id']}/submit-review",
                headers=mutation_headers(f"wrong-checksum-{suffix}", 1),
                json={
                    "content_version_id": version["id"],
                    "content_sha256": "0" * 64,
                },
            )
            assert wrong_checksum.status_code == 409

            submitted = await client.post(
                f"/api/v1/content/assets/{asset['id']}/submit-review",
                headers=mutation_headers(f"admin-submit-{suffix}", 1),
                json={
                    "content_version_id": version["id"],
                    "content_sha256": version["content_sha256"],
                },
            )
            assert submitted.status_code == 200, submitted.text

            self_approval = await client.post(
                f"/api/v1/content/assets/{asset['id']}/decisions",
                headers=mutation_headers(f"self-approve-{suffix}", 2),
                json={
                    "content_version_id": version["id"],
                    "content_sha256": version["content_sha256"],
                    "decision": "approved",
                },
            )
            assert self_approval.status_code == 409
            assert "cannot approve" in self_approval.text

            rejected = await client.post(
                f"/api/v1/content/assets/{asset['id']}/decisions",
                headers=mutation_headers(f"admin-reject-{suffix}", 2),
                json={
                    "content_version_id": version["id"],
                    "content_sha256": version["content_sha256"],
                    "decision": "rejected",
                    "comment": "Synthetic rejection requires revision.",
                },
            )
            assert rejected.status_code == 200, rejected.text
            assert rejected.json()["asset"]["status"] == "draft"
            audit = await client.get(f"/api/v1/content/assets/{asset['id']}/audit")
            assert "content.rejected" in {entry["action"] for entry in audit.json()}
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_content_rls_is_forced_and_cross_tenant_access_is_denied() -> None:
    suffix = uuid4().hex[:10]
    app.dependency_overrides[get_token_identity] = sales_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/api/v1/content/assets",
                headers=mutation_headers(f"rls-asset-{suffix}"),
                json=asset_payload(suffix),
            )
            assert created.status_code == 201, created.text
            asset_id = created.json()["id"]
            denied = await client.get(
                f"/api/v1/content/assets/{asset_id}",
                headers={"X-Tenant-Id": str(uuid4())},
            )
            assert denied.status_code == 403

        async with session_factory() as session:
            policies = (
                await session.execute(
                    text(
                        "SELECT relname, relrowsecurity, relforcerowsecurity "
                        "FROM pg_class WHERE relname = ANY(:tables)"
                    ),
                    {
                        "tables": [
                            "content_requests",
                            "content_assets",
                            "content_generation_runs",
                            "content_versions",
                            "content_approval_decisions",
                            "content_audit_logs",
                        ]
                    },
                )
            ).all()
            assert len(policies) == 6
            assert all(row.relrowsecurity and row.relforcerowsecurity for row in policies)
            policy_expressions = (
                await session.execute(
                    text(
                        "SELECT tablename, qual, with_check FROM pg_policies "
                        "WHERE tablename = ANY(:tables)"
                    ),
                    {"tables": [row.relname for row in policies]},
                )
            ).all()
            assert len(policy_expressions) == 6
            assert all("app.tenant_id" in row.qual for row in policy_expressions)
            assert all("app.tenant_id" in row.with_check for row in policy_expressions)
            immutable_triggers = await session.scalar(
                text(
                    "SELECT count(*) FROM pg_trigger WHERE tgname IN "
                    "('content_versions_immutable','content_approval_decisions_immutable',"
                    "'content_audit_logs_immutable') AND NOT tgisinternal"
                )
            )
            assert immutable_triggers == 3
            other_tenant = uuid4()
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(other_tenant)},
            )
            assert (
                await session.scalar(
                    select(ContentVersion).where(ContentVersion.tenant_id == other_tenant).limit(1)
                )
                is None
            )
            assert (
                await session.scalar(
                    select(ContentAuditLog)
                    .where(ContentAuditLog.tenant_id == other_tenant)
                    .limit(1)
                )
                is None
            )
    finally:
        app.dependency_overrides.clear()
