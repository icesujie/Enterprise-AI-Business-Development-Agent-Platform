from __future__ import annotations

from uuid import uuid4

import httpx
import pytest

from sari_api.api.dependencies import get_token_identity
from sari_api.domain.identity import TokenIdentity
from sari_api.main import app

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


def payload(slug: str, *, title: str = "Published kitchen planning") -> dict[str, object]:
    return {
        "page_type": "solution",
        "slug": slug,
        "locale": "en",
        "title": title,
        "summary": "Public project planning information for dynamic rendering tests.",
        "seo_title": f"{title} SEO",
        "seo_description": "Published SEO description from the exact governed version.",
        "structured_content": {
            "overview": ["Public commercial kitchen project planning information."],
            "customer_needs": ["Project requirements"],
            "service_scope": [
                {"title": "Planning", "description": "Coordinate project requirements."}
            ],
            "workflow_areas": [
                {"title": "Workflow", "description": "Review functional kitchen areas."}
            ],
            "related_industries": [],
            "related_projects": [],
            "cta": {
                "label": "Start project consultation",
                "description": "Share requirements for human review.",
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


async def create_item(client: httpx.AsyncClient, slug: str) -> dict[str, object]:
    app.dependency_overrides[get_token_identity] = sales_identity
    response = await client.post(
        "/api/v1/public-content/items",
        headers=headers(f"create-{slug}"),
        json=payload(slug),
    )
    assert response.status_code == 201, response.text
    return response.json()


async def approve_item(client: httpx.AsyncClient, item: dict[str, object]) -> dict[str, object]:
    version = item["current_version"]
    assert isinstance(version, dict)
    submitted = await client.post(
        f"/api/v1/public-content/items/{item['id']}/submit-review",
        headers=headers(f"submit-{item['id']}", 1),
        json=exact(version, "Submit for review."),
    )
    assert submitted.status_code == 200, submitted.text
    app.dependency_overrides[get_token_identity] = admin_identity
    approved = await client.post(
        f"/api/v1/public-content/items/{item['id']}/decisions",
        headers=headers(f"approve-{item['id']}", 2),
        json={**exact(version, "Independent approval."), "decision": "approved"},
    )
    assert approved.status_code == 200, approved.text
    return approved.json()["item"]


async def publish_item(client: httpx.AsyncClient, item: dict[str, object]) -> dict[str, object]:
    version = item["current_version"]
    assert isinstance(version, dict)
    response = await client.post(
        f"/api/v1/public-content/items/{item['id']}/publish",
        headers=headers(f"publish-{item['id']}", 3),
        json=exact(version, "Publish exact approved version."),
    )
    assert response.status_code == 200, response.text
    return response.json()["item"]


@pytest.mark.asyncio
async def test_public_render_returns_exact_published_version_and_isolates_locale() -> None:
    slug = f"dynamic-render-{uuid4().hex[:10]}"
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            published = await publish_item(
                client, await approve_item(client, await create_item(client, slug))
            )
            published_version = published["published_version"]
            assert isinstance(published_version, dict)

            app.dependency_overrides[get_token_identity] = sales_identity
            successor_payload = payload(slug, title="Unpublished successor title")
            for field in ("page_type", "slug", "locale"):
                successor_payload.pop(field)
            successor = await client.post(
                f"/api/v1/public-content/items/{published['id']}/versions",
                headers=headers(f"successor-{slug}", 4),
                json=successor_payload,
            )
            assert successor.status_code == 201, successor.text

            rendered = await client.get(
                f"/api/v1/public-content/render/solution/{slug}",
                params={"locale": "en"},
            )
            assert rendered.status_code == 200, rendered.text
            body = rendered.json()
            assert body["title"] == published_version["title"]
            assert body["seo_title"] == published_version["seo_title"]
            assert body["structured_content"] == published_version["structured_content"]
            assert "Unpublished successor" not in rendered.text
            assert set(body) == {
                "page_type",
                "slug",
                "locale",
                "title",
                "summary",
                "seo_title",
                "seo_description",
                "canonical_path",
                "structured_content",
                "media_references",
                "published_at",
                "version_created_at",
            }
            assert rendered.headers["cache-control"].startswith("public, max-age=30")

            wrong_locale = await client.get(
                f"/api/v1/public-content/render/solution/{slug}",
                params={"locale": "zh-CN"},
            )
            assert wrong_locale.status_code == 404

            app.dependency_overrides[get_token_identity] = admin_identity
            archived = await client.post(
                f"/api/v1/public-content/items/{published['id']}/archive",
                headers=headers(f"archive-{slug}", 5),
                json={"reason": "Remove dynamic rendering fixture."},
            )
            assert archived.status_code == 200, archived.text
            after_archive = await client.get(
                f"/api/v1/public-content/render/solution/{slug}",
                params={"locale": "en"},
            )
            assert after_archive.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_draft_and_approved_without_published_pointer_return_404() -> None:
    suffix = uuid4().hex[:10]
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            draft = await create_item(client, f"draft-render-{suffix}")
            approved = await approve_item(
                client, await create_item(client, f"approved-render-{suffix}")
            )

            for item in (draft, approved):
                response = await client.get(
                    f"/api/v1/public-content/render/solution/{item['slug']}",
                    params={"locale": "en"},
                )
                assert response.status_code == 404

            app.dependency_overrides[get_token_identity] = admin_identity
            for item, version in ((draft, 1), (approved, 3)):
                archived = await client.post(
                    f"/api/v1/public-content/items/{item['id']}/archive",
                    headers=headers(f"archive-{item['id']}", version),
                    json={"reason": "Remove non-public rendering fixture."},
                )
                assert archived.status_code == 200, archived.text
    finally:
        app.dependency_overrides.clear()
