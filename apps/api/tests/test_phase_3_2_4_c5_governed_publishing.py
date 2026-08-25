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


def exact(version: dict[str, object]) -> dict[str, object]:
    return {
        "public_content_version_id": version["id"],
        "content_sha256": version["content_sha256"],
        "comment": "Exact human-governed version.",
    }


def solution_payload(slug: str) -> dict[str, object]:
    return {
        "page_type": "solution",
        "slug": slug,
        "locale": "en",
        "title": "Governed commercial kitchen solution",
        "summary": "Approved public solution used for publishing automation validation.",
        "seo_title": "Governed Commercial Kitchen Solution",
        "seo_description": "Approved public solution metadata from the exact version.",
        "structured_content": {
            "overview": ["Approved public solution overview."],
            "customer_needs": ["Project requirements"],
            "service_scope": [
                {"title": "Planning", "description": "Coordinate approved project inputs."}
            ],
            "workflow_areas": [
                {"title": "Workflow", "description": "Review functional kitchen areas."}
            ],
            "related_industries": [],
            "related_projects": [],
            "cta": {
                "label": "Start project consultation",
                "description": "Share requirements for human follow-up.",
                "destination": "public_consultation_agent",
            },
        },
        "media_references": [],
        "source_type": "manual",
    }


def product_payload(slug: str) -> dict[str, object]:
    return {
        "page_type": "product",
        "slug": slug,
        "locale": "en",
        "title": "Governed Preparation Table",
        "summary": "Approved public product summary.",
        "seo_title": "Governed Preparation Table",
        "seo_description": "Approved public product metadata from the exact version.",
        "structured_content": {
            "product_name": "Governed Preparation Table",
            "sku_model": "PT-GOV-01",
            "category": "Preparation Equipment",
            "brand": None,
            "short_description": "Approved public product description.",
            "detailed_description": ["Approved public product details."],
            "features": ["Approved product feature"],
            "applications": ["Commercial kitchen preparation areas"],
            "material": "Stainless steel",
            "dimensions": None,
            "configuration": None,
            "specifications": [{"label": "Material", "value": "Stainless steel"}],
            "price_mode": "request_quote",
            "currency": None,
            "price_min": None,
            "price_max": None,
            "price_note": "Request a human-confirmed quotation.",
            "moq": None,
            "availability_note": None,
            "hero_media_asset_id": None,
            "gallery_media_asset_ids": [],
            "drawing_media_asset_ids": [],
            "related_products": [],
            "related_solution": None,
            "related_industry": None,
            "related_guide": None,
            "related_project": None,
            "inquiry_cta": {
                "label": "Ask about this product",
                "description": "Discuss requirements with the Sari Arta team.",
                "destination": "public_consultation_agent",
            },
            "quote_cta": {
                "label": "Request a quote",
                "description": "Share quantity and configuration for human follow-up.",
                "destination": "public_consultation_agent",
            },
        },
        "media_references": [],
        "source_type": "manual",
    }


async def publish(
    client: httpx.AsyncClient, payload: dict[str, object], suffix: str
) -> dict[str, object]:
    app.dependency_overrides[get_token_identity] = sales_identity
    created = await client.post(
        "/api/v1/public-content/items",
        headers=headers(f"create-{suffix}"),
        json=payload,
    )
    assert created.status_code == 201, created.text
    item = created.json()
    version = item["current_version"]
    submitted = await client.post(
        f"/api/v1/public-content/items/{item['id']}/submit-review",
        headers=headers(f"submit-{suffix}", 1),
        json=exact(version),
    )
    assert submitted.status_code == 200, submitted.text
    app.dependency_overrides[get_token_identity] = admin_identity
    approved = await client.post(
        f"/api/v1/public-content/items/{item['id']}/decisions",
        headers=headers(f"approve-{suffix}", 2),
        json={**exact(version), "decision": "approved"},
    )
    assert approved.status_code == 200, approved.text
    published = await client.post(
        f"/api/v1/public-content/items/{item['id']}/publish",
        headers=headers(f"publish-{suffix}", 3),
        json=exact(version),
    )
    assert published.status_code == 200, published.text
    return published.json()


@pytest.mark.asyncio
async def test_publish_event_catalog_archive_and_automation_audit_are_safe() -> None:
    suffix = uuid4().hex[:10]
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            solution = await publish(
                client, solution_payload(f"c5-solution-{suffix}"), f"solution-{suffix}"
            )
            product = await publish(
                client, product_payload(f"c5-product-{suffix}"), f"product-{suffix}"
            )
            event = solution["publication"]
            item = solution["item"]
            assert event["published_version_id"] == item["published_version_id"]
            assert event["canonical_path"] == item["canonical_path"]
            assert event["canonical_url"].endswith(item["canonical_path"])
            assert set(event) == {
                "event_id",
                "tenant_id",
                "page_type",
                "slug",
                "locale",
                "published_version_id",
                "canonical_path",
                "canonical_url",
                "published_at",
            }

            routes = await client.get(
                "/api/v1/public-content/catalog/routes", params={"locale": "en"}
            )
            assert routes.status_code == 200, routes.text
            paths = {entry["canonical_path"] for entry in routes.json()}
            assert item["canonical_path"] in paths
            assert product["item"]["canonical_path"] in paths

            rendered_product = await client.get(
                f"/api/v1/public-content/render/product/{product['item']['slug']}",
                params={"locale": "en"},
            )
            assert rendered_product.status_code == 200
            assert rendered_product.json()["structured_content"]["price_mode"] == "request_quote"

            automation_payload = {
                "event_type": "publish",
                "public_content_version_id": item["published_version_id"],
                "revalidation_outcome": "succeeded",
                "indexnow_outcome": "disabled",
                "duration_ms": 12,
                "retry_state": "complete",
                "failure_code": None,
            }
            automation_headers = {
                "Idempotency-Key": f"automation-{suffix}",
                "X-Correlation-ID": f"correlation-{suffix}",
            }
            recorded = await client.post(
                f"/api/v1/public-content/items/{item['id']}/publication-automation",
                headers=automation_headers,
                json=automation_payload,
            )
            repeated = await client.post(
                f"/api/v1/public-content/items/{item['id']}/publication-automation",
                headers=automation_headers,
                json=automation_payload,
            )
            assert recorded.status_code == repeated.status_code == 200

            archived = await client.post(
                f"/api/v1/public-content/items/{item['id']}/archive",
                headers=headers(f"archive-{suffix}", 4),
                json={"reason": "Validate governed removal."},
            )
            assert archived.status_code == 200, archived.text
            removed = await client.get(
                f"/api/v1/public-content/render/solution/{item['slug']}",
                params={"locale": "en"},
            )
            assert removed.status_code == 404
            governed_removed = await client.get(
                f"/api/v1/public-content/render/solution/{item['slug']}",
                params={"locale": "en"},
                headers={"X-Site-Token": "local-public-site-token"},
            )
            assert governed_removed.status_code == 404
            assert (
                governed_removed.headers["X-Public-Content-State"]
                == "governed-unavailable"
            )
            routes_after_archive = await client.get(
                "/api/v1/public-content/catalog/routes", params={"locale": "en"}
            )
            assert item["canonical_path"] not in {
                entry["canonical_path"] for entry in routes_after_archive.json()
            }

            audit = await client.get(
                f"/api/v1/public-content/items/{item['id']}/audit"
            )
            automation_events = [
                entry
                for entry in audit.json()
                if entry["action"] == "public_content.publish_automation"
            ]
            assert len(automation_events) == 1
            details = automation_events[0]["details"]
            assert details["published_version_id"] == item["published_version_id"]
            assert details["revalidation_outcome"] == "succeeded"
            assert "content" not in details

            cross_tenant = await client.post(
                f"/api/v1/public-content/items/{item['id']}/publication-automation",
                headers={
                    **headers(f"cross-tenant-{suffix}"),
                    "X-Tenant-Id": str(uuid4()),
                },
                json={**automation_payload, "event_type": "remove"},
            )
            assert cross_tenant.status_code == 403
    finally:
        app.dependency_overrides.clear()
