from __future__ import annotations

from typing import cast
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from sari_api.adapters.database import session_factory
from sari_api.adapters.models import PublicContentAuditLog, PublicContentVersion
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


def headers(key: str, version: int | None = None) -> dict[str, str]:
    result = {"Idempotency-Key": key}
    if version is not None:
        result["If-Match"] = f'"{version}"'
    return result


def solution_payload(slug: str) -> dict[str, object]:
    return {
        "page_type": "solution",
        "slug": slug,
        "locale": "en",
        "title": "Commercial kitchen project coordination",
        "summary": "Approved public capability fixture for governed CMS testing.",
        "seo_title": "Commercial Kitchen Project Coordination Indonesia",
        "seo_description": (
            "Sari Arta coordinates commercial kitchen planning, manufacturing information, "
            "logistics, local installation, and project handover in Indonesia."
        ),
        "structured_content": {
            "overview": [
                "Sari Arta coordinates commercial kitchen project requirements in Indonesia."
            ],
            "customer_needs": ["Project requirements and site coordination"],
            "service_scope": [
                {
                    "title": "Project coordination",
                    "description": "Coordinate approved scope information across the project team.",
                }
            ],
            "workflow_areas": [
                {
                    "title": "Planning to handover",
                    "description": (
                        "Connect planning, manufacturing information, installation, and handover."
                    ),
                }
            ],
            "related_industries": [],
            "related_projects": [],
            "cta": {
                "label": "Start project consultation",
                "description": "Share project requirements for human review.",
                "destination": "public_consultation_agent",
            },
        },
        "media_references": [],
        "source_type": "manual",
    }


def exact(version: dict[str, object], comment: str) -> dict[str, object]:
    return {
        "public_content_version_id": version["id"],
        "content_sha256": version["content_sha256"],
        "comment": comment,
    }


@pytest.mark.asyncio
async def test_public_content_governed_lifecycle_and_published_pointer() -> None:
    suffix = uuid4().hex[:10]
    app.dependency_overrides[get_token_identity] = sales_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            payload = solution_payload(f"cms-foundation-{suffix}")
            created = await client.post(
                "/api/v1/public-content/items",
                headers=headers(f"create-{suffix}"),
                json=payload,
            )
            assert created.status_code == 201, created.text
            repeated = await client.post(
                "/api/v1/public-content/items",
                headers=headers(f"create-{suffix}"),
                json=payload,
            )
            assert repeated.status_code == 201
            assert repeated.json()["id"] == created.json()["id"]
            item = created.json()
            item_id = item["id"]
            version = item["current_version"]
            assert item["canonical_path"] == f"/solutions/cms-foundation-{suffix}"
            assert version["version_number"] == 1
            assert item["status"] == "draft"

            filtered = await client.get(
                "/api/v1/public-content/items",
                params={
                    "status": "draft",
                    "page_type": "solution",
                    "locale": "en",
                    "search": suffix,
                },
            )
            assert filtered.status_code == 200
            assert [entry["id"] for entry in filtered.json()] == [item_id]
            wrong_locale = await client.get(
                "/api/v1/public-content/items",
                params={"locale": "zh-CN", "search": suffix},
            )
            assert wrong_locale.status_code == 200
            assert wrong_locale.json() == []

            submitted = await client.post(
                f"/api/v1/public-content/items/{item_id}/submit-review",
                headers=headers(f"submit-{suffix}", 1),
                json=exact(version, "Ready for independent review."),
            )
            assert submitted.status_code == 200, submitted.text
            assert submitted.json()["item"]["status"] == "review"

            sales_approval = await client.post(
                f"/api/v1/public-content/items/{item_id}/decisions",
                headers=headers(f"sales-approval-{suffix}", 2),
                json={**exact(version, "Sales cannot approve."), "decision": "approved"},
            )
            assert sales_approval.status_code == 403

            app.dependency_overrides[get_token_identity] = admin_identity
            approved = await client.post(
                f"/api/v1/public-content/items/{item_id}/decisions",
                headers=headers(f"approve-{suffix}", 2),
                json={**exact(version, "Independent human approval."), "decision": "approved"},
            )
            assert approved.status_code == 200, approved.text
            approved_item = approved.json()["item"]
            assert approved_item["approved_version_id"] == version["id"]
            assert approved_item["status"] == "approved"

            published = await client.post(
                f"/api/v1/public-content/items/{item_id}/publish",
                headers=headers(f"publish-{suffix}", 3),
                json=exact(version, "Explicit human publication."),
            )
            assert published.status_code == 200, published.text
            published_item = published.json()["item"]
            assert published_item["status"] == "published"
            assert published_item["published_version_id"] == version["id"]

            app.dependency_overrides[get_token_identity] = sales_identity
            successor_payload = solution_payload(f"cms-foundation-{suffix}")
            successor_payload.pop("page_type")
            successor_payload.pop("slug")
            successor_payload.pop("locale")
            successor_payload["title"] = "Updated commercial kitchen project coordination"
            successor = await client.post(
                f"/api/v1/public-content/items/{item_id}/versions",
                headers=headers(f"successor-{suffix}", 4),
                json=successor_payload,
            )
            assert successor.status_code == 201, successor.text
            successor_item = successor.json()
            assert successor_item["status"] == "draft"
            assert successor_item["approved_version_id"] is None
            assert successor_item["published_version_id"] == version["id"]
            assert successor_item["current_version"]["version_number"] == 2

            stale_successor = await client.post(
                f"/api/v1/public-content/items/{item_id}/versions",
                headers=headers(f"stale-successor-{suffix}", 4),
                json=successor_payload,
            )
            assert stale_successor.status_code == 412

            app.dependency_overrides[get_token_identity] = admin_identity
            archived = await client.post(
                f"/api/v1/public-content/items/{item_id}/archive",
                headers=headers(f"archive-{suffix}", 5),
                json={"reason": "End of governed CMS lifecycle test."},
            )
            assert archived.status_code == 200, archived.text
            assert archived.json()["status"] == "archived"
            restored = await client.post(
                f"/api/v1/public-content/items/{item_id}/restore",
                headers=headers(f"restore-{suffix}", 6),
                json={"reason": "Verify governed restore behavior."},
            )
            assert restored.status_code == 200, restored.text
            assert restored.json()["status"] == "published"
            rearchived = await client.post(
                f"/api/v1/public-content/items/{item_id}/archive",
                headers=headers(f"rearchive-{suffix}", 7),
                json={"reason": "Keep test content publicly ineligible."},
            )
            assert rearchived.status_code == 200

            audit = await client.get(f"/api/v1/public-content/items/{item_id}/audit")
            assert audit.status_code == 200, audit.text
            actions = {entry["action"] for entry in audit.json()}
            assert {
                "public_content.created",
                "public_content.review_submitted",
                "public_content.approved",
                "public_content.published",
                "public_content.version_created",
                "public_content.archived",
                "public_content.restored",
            }.issubset(actions)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_synthetic_content_cannot_publish_and_structured_body_is_strict() -> None:
    suffix = uuid4().hex[:10]
    app.dependency_overrides[get_token_identity] = sales_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            invalid = solution_payload(f"invalid-{suffix}")
            structured = dict(cast(dict[str, object], invalid["structured_content"]))
            structured["uncontrolled_html"] = "<script>not allowed</script>"
            invalid["structured_content"] = structured
            rejected = await client.post(
                "/api/v1/public-content/items",
                headers=headers(f"invalid-{suffix}"),
                json=invalid,
            )
            assert rejected.status_code == 422

            missing_source_reference = solution_payload(f"source-{suffix}")
            missing_source_reference["source_type"] = "knowledge_version"
            source_rejected = await client.post(
                "/api/v1/public-content/items",
                headers=headers(f"source-{suffix}"),
                json=missing_source_reference,
            )
            assert source_rejected.status_code == 422

            payload = solution_payload(f"synthetic-{suffix}")
            payload["is_synthetic"] = True
            created = await client.post(
                "/api/v1/public-content/items",
                headers=headers(f"synthetic-create-{suffix}"),
                json=payload,
            )
            assert created.status_code == 201, created.text
            item = created.json()
            version = item["current_version"]
            submitted = await client.post(
                f"/api/v1/public-content/items/{item['id']}/submit-review",
                headers=headers(f"synthetic-submit-{suffix}", 1),
                json=exact(version, "Synthetic review test."),
            )
            assert submitted.status_code == 200
            app.dependency_overrides[get_token_identity] = admin_identity
            approved = await client.post(
                f"/api/v1/public-content/items/{item['id']}/decisions",
                headers=headers(f"synthetic-approve-{suffix}", 2),
                json={**exact(version, "Synthetic approval test."), "decision": "approved"},
            )
            assert approved.status_code == 200
            denied = await client.post(
                f"/api/v1/public-content/items/{item['id']}/publish",
                headers=headers(f"synthetic-publish-{suffix}", 3),
                json=exact(version, "Must be denied."),
            )
            assert denied.status_code == 409
            assert "Synthetic" in denied.text

            self_owned = solution_payload(f"self-owned-{suffix}")
            self_owned["is_synthetic"] = True
            self_created = await client.post(
                "/api/v1/public-content/items",
                headers=headers(f"self-create-{suffix}"),
                json=self_owned,
            )
            assert self_created.status_code == 201
            self_item = self_created.json()
            self_version = self_item["current_version"]
            self_submitted = await client.post(
                f"/api/v1/public-content/items/{self_item['id']}/submit-review",
                headers=headers(f"self-submit-{suffix}", 1),
                json=exact(self_version, "Submit an administrator-created version."),
            )
            assert self_submitted.status_code == 200
            self_approval = await client.post(
                f"/api/v1/public-content/items/{self_item['id']}/decisions",
                headers=headers(f"self-approve-{suffix}", 2),
                json={
                    **exact(self_version, "Creator must not self-approve."),
                    "decision": "approved",
                },
            )
            assert self_approval.status_code == 409
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_public_content_rls_and_immutable_history() -> None:
    suffix = uuid4().hex[:10]
    app.dependency_overrides[get_token_identity] = sales_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/api/v1/public-content/items",
                headers=headers(f"rls-{suffix}"),
                json={**solution_payload(f"rls-{suffix}"), "is_synthetic": True},
            )
            assert created.status_code == 201, created.text
            item_id = created.json()["id"]
            version_id = created.json()["current_version_id"]
            denied = await client.get(
                f"/api/v1/public-content/items/{item_id}",
                headers={"X-Tenant-Id": str(uuid4())},
            )
            assert denied.status_code == 403

        async with session_factory() as session:
            tables = [
                "public_content_items",
                "public_content_versions",
                "public_content_decisions",
                "public_content_audit_logs",
            ]
            rows = (
                await session.execute(
                    text(
                        "SELECT relname, relrowsecurity, relforcerowsecurity "
                        "FROM pg_class WHERE relname = ANY(:tables)"
                    ),
                    {"tables": tables},
                )
            ).all()
            assert len(rows) == 4
            assert all(row.relrowsecurity and row.relforcerowsecurity for row in rows)
            policies = (
                await session.execute(
                    text(
                        "SELECT tablename, qual, with_check FROM pg_policies "
                        "WHERE tablename = ANY(:tables)"
                    ),
                    {"tables": tables},
                )
            ).all()
            assert len(policies) == 4
            assert all("app.tenant_id" in row.qual for row in policies)
            assert all("app.tenant_id" in row.with_check for row in policies)

            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(TENANT_ID)},
            )
            with pytest.raises(DBAPIError, match="public content history is immutable"):
                await session.execute(
                    text("UPDATE public_content_versions SET title = 'mutated' WHERE id = :id"),
                    {"id": version_id},
                )
                await session.flush()
            await session.rollback()
            other_tenant = uuid4()
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(other_tenant)},
            )
            assert (
                await session.scalar(
                    select(PublicContentVersion)
                    .where(PublicContentVersion.tenant_id == other_tenant)
                    .limit(1)
                )
                is None
            )
            assert (
                await session.scalar(
                    select(PublicContentAuditLog)
                    .where(PublicContentAuditLog.tenant_id == other_tenant)
                    .limit(1)
                )
                is None
            )
    finally:
        app.dependency_overrides.clear()
