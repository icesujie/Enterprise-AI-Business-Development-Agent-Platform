from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import select, text

from sari_api.adapters.database import session_factory
from sari_api.adapters.media_storage import LocalMediaStorage, get_media_storage
from sari_api.adapters.models import Lead
from sari_api.api.dependencies import get_token_identity
from sari_api.api.routes.public_leads import enforce_public_rate_limit
from sari_api.domain.identity import TokenIdentity
from sari_api.main import app

ADMIN_SUBJECT = "30000000-0000-4000-8000-000000000001"
SALES_SUBJECT = "30000000-0000-4000-8000-000000000002"
TENANT_ID = UUID("10000000-0000-4000-8000-000000000001")


async def admin_identity() -> TokenIdentity:
    return TokenIdentity(subject=ADMIN_SUBJECT, email="admin@sari-arta.example")


async def sales_identity() -> TokenIdentity:
    return TokenIdentity(subject=SALES_SUBJECT, email="sales@sari-arta.example")


async def allow_request() -> None:
    return None


def headers(key: str, version: int | None = None) -> dict[str, str]:
    result = {"Idempotency-Key": key}
    if version is not None:
        result["If-Match"] = f'"{version}"'
    return result


def png() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\x0dIHDR"
        + (2).to_bytes(4, "big")
        + (3).to_bytes(4, "big")
        + b"\x08\x02\x00\x00\x00"
        + b"\x00\x00\x00\x00"
    )


def product_payload(
    slug: str,
    *,
    mode: str = "fixed",
    media_id: str | None = None,
) -> dict[str, object]:
    price = {
        "fixed": ("USD", "180.00", None),
        "starting_from": ("USD", "280.00", None),
        "range": ("USD", "280.00", "350.00"),
        "request_quote": (None, None, None),
    }[mode]
    media = (
        [
            {
                "media_asset_id": media_id,
                "role": "product_hero",
                "alt_text": "Synthetic product image for governed catalog testing.",
            }
        ]
        if media_id
        else []
    )
    return {
        "page_type": "product",
        "slug": slug,
        "locale": "en",
        "title": "Synthetic Stainless Preparation Table",
        "summary": "Synthetic product information used only for catalog governance testing.",
        "seo_title": "Stainless Preparation Table",
        "seo_description": "Governed public product fixture for commercial kitchen planning.",
        "structured_content": {
            "product_name": "Synthetic Stainless Preparation Table",
            "sku_model": "TEST-PT-01",
            "category": "Preparation Equipment",
            "brand": "Synthetic Test Brand",
            "short_description": "A synthetic preparation-equipment fixture.",
            "detailed_description": ["This content exists only inside automated tests."],
            "features": ["Synthetic governed feature"],
            "applications": ["Commercial kitchen preparation areas"],
            "material": "Stainless steel",
            "dimensions": "Test fixture dimensions",
            "configuration": "Test fixture configuration",
            "specifications": [{"label": "Fixture", "value": "Synthetic"}],
            "price_mode": mode,
            "currency": price[0],
            "price_min": price[1],
            "price_max": price[2],
            "price_note": (
                "Final quotation depends on quantity, configuration, "
                "customization and delivery location."
            ),
            "moq": None,
            "availability_note": None,
            "hero_media_asset_id": media_id,
            "gallery_media_asset_ids": [],
            "drawing_media_asset_ids": [],
            "related_products": [],
            "related_solution": None,
            "related_industry": None,
            "related_guide": None,
            "related_project": None,
            "inquiry_cta": {
                "label": "Ask About This Product",
                "description": "Discuss this product with the Sari Arta team.",
                "destination": "public_consultation_agent",
            },
            "quote_cta": {
                "label": "Request a Quote",
                "description": "Share quantity and configuration for human follow-up.",
                "destination": "public_consultation_agent",
            },
        },
        "media_references": media,
        "source_type": "manual",
    }


def exact(item: dict[str, object], comment: str) -> dict[str, object]:
    version = item["current_version"]
    assert isinstance(version, dict)
    return {
        "public_content_version_id": version["id"],
        "content_sha256": version["content_sha256"],
        "comment": comment,
    }


async def create_product(
    client: httpx.AsyncClient,
    slug: str,
    *,
    mode: str = "fixed",
    media_id: str | None = None,
) -> dict[str, object]:
    app.dependency_overrides[get_token_identity] = sales_identity
    response = await client.post(
        "/api/v1/public-content/items",
        headers=headers(f"create-{slug}"),
        json=product_payload(slug, mode=mode, media_id=media_id),
    )
    assert response.status_code == 201, response.text
    return response.json()


async def approve_product(client: httpx.AsyncClient, item: dict[str, object]) -> dict[str, object]:
    submitted = await client.post(
        f"/api/v1/public-content/items/{item['id']}/submit-review",
        headers=headers(f"submit-{item['id']}", 1),
        json=exact(item, "Submit synthetic catalog fixture for governance testing."),
    )
    assert submitted.status_code == 200, submitted.text
    app.dependency_overrides[get_token_identity] = admin_identity
    approved = await client.post(
        f"/api/v1/public-content/items/{item['id']}/decisions",
        headers=headers(f"approve-{item['id']}", 2),
        json={**exact(item, "Independent test approval."), "decision": "approved"},
    )
    assert approved.status_code == 200, approved.text
    return approved.json()["item"]


@pytest.mark.asyncio
async def test_product_pricing_modes_are_strict_and_unpublished_products_stay_private() -> None:
    transport = httpx.ASGITransport(app=app)
    items: list[dict[str, object]] = []
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            for mode in ("fixed", "starting_from", "range", "request_quote"):
                slug_mode = mode.replace("_", "-")
                item = await create_product(
                    client, f"product-{slug_mode}-{uuid4().hex[:8]}", mode=mode
                )
                items.append(item)
                assert item["canonical_path"].startswith("/products/")
                content = cast(dict[str, Any], item["current_version"])["structured_content"]
                assert content["price_mode"] == mode

                rendered = await client.get(
                    f"/api/v1/public-content/render/product/{item['slug']}",
                    params={"locale": "en"},
                )
                assert rendered.status_code == 404

            catalog = await client.get(
                "/api/v1/public-content/catalog/products", params={"locale": "en"}
            )
            assert catalog.status_code == 200
            slugs = {entry["slug"] for entry in catalog.json()}
            assert not slugs.intersection({str(item["slug"]) for item in items})

            invalid = product_payload(f"invalid-price-{uuid4().hex[:8]}", mode="range")
            cast(dict[str, Any], invalid["structured_content"])["price_max"] = "100.00"
            rejected = await client.post(
                "/api/v1/public-content/items",
                headers=headers(f"invalid-{uuid4()}"),
                json=invalid,
            )
            assert rejected.status_code == 422

            isolated = await client.get(
                f"/api/v1/public-content/items/{items[0]['id']}",
                headers={"X-Tenant-Id": str(uuid4())},
            )
            assert isolated.status_code == 403

            app.dependency_overrides[get_token_identity] = admin_identity
            for item in items:
                archived = await client.post(
                    f"/api/v1/public-content/items/{item['id']}/archive",
                    headers=headers(f"archive-{item['id']}", 1),
                    json={"reason": "Remove product pricing test fixture."},
                )
                assert archived.status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_product_publication_requires_public_media_and_catalog_returns_exact_version(
    tmp_path: Path,
) -> None:
    app.dependency_overrides[get_media_storage] = lambda: LocalMediaStorage(tmp_path / "media")
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            app.dependency_overrides[get_token_identity] = sales_identity
            upload = await client.post(
                "/api/v1/media/assets",
                files={"file": ("product.png", png(), "image/png")},
                data={
                    "title": "Synthetic product media",
                    "alt_text": "Synthetic product image for governed catalog testing.",
                },
            )
            assert upload.status_code == 201, upload.text
            media_id = upload.json()["id"]
            slug = f"published-product-{uuid4().hex[:8]}"
            item = await create_product(client, slug, media_id=media_id)
            approved = await approve_product(client, item)

            blocked = await client.post(
                f"/api/v1/public-content/items/{item['id']}/publish",
                headers=headers(f"blocked-publish-{slug}", 3),
                json=exact(approved, "Private media must block publication."),
            )
            assert blocked.status_code == 409

            app.dependency_overrides[get_token_identity] = sales_identity
            assert (
                await client.post(
                    f"/api/v1/media/assets/{media_id}/submit-review",
                    headers={"If-Match": '"1"'},
                )
            ).status_code == 200
            app.dependency_overrides[get_token_identity] = admin_identity
            assert (
                await client.post(
                    f"/api/v1/media/assets/{media_id}/approve",
                    headers={"If-Match": '"2"'},
                )
            ).status_code == 200
            published = await client.post(
                f"/api/v1/public-content/items/{item['id']}/publish",
                headers=headers(f"publish-{slug}", 3),
                json=exact(approved, "Publish exact approved Product version."),
            )
            assert published.status_code == 200, published.text

            rendered = await client.get(
                f"/api/v1/public-content/render/product/{slug}", params={"locale": "en"}
            )
            assert rendered.status_code == 200
            body = rendered.json()
            assert body["structured_content"]["hero_media_asset_id"] == media_id
            assert body["media_references"][0]["media_asset_id"] == media_id
            assert body["media_references"][0]["url"].endswith(media_id)

            catalog = await client.get(
                "/api/v1/public-content/catalog/products", params={"locale": "en"}
            )
            assert catalog.status_code == 200
            listed = next(entry for entry in catalog.json() if entry["slug"] == slug)
            assert listed["title"] == body["title"]
            assert listed["structured_content"] == body["structured_content"]

            app.dependency_overrides[enforce_public_rate_limit] = allow_request
            email = f"product-inquiry-{uuid4().hex[:10]}@example.invalid"
            inquiry_payload: dict[str, Any] = {
                "contact": {
                    "first_name": "Synthetic",
                    "email": email,
                    "preferred_language": "en",
                },
                "organization": {"name": "Synthetic Product Buyer"},
                "inquiry": {
                    "message": "Synthetic product inquiry for governance testing only.",
                    "project_type": "Product inquiry",
                    "product_context": {
                        "source": "product_page",
                        "product_locale": "en",
                        "product_name": body["title"],
                        "product_slug": slug,
                        "sku_model": "TEST-PT-01",
                        "price_mode": "fixed",
                        "displayed_price": "USD 180.00",
                    },
                },
                "attribution": {"source": "website_ai_assistant"},
                "consent": {
                    "privacy_policy_version": "test-v1",
                    "contact_consent": True,
                },
            }
            inquiry = await client.post(
                "/api/v1/public/lead-submissions",
                headers={
                    "Idempotency-Key": f"product-inquiry-{uuid4()}",
                    "X-Site-Token": "local-public-site-token",
                },
                json=inquiry_payload,
            )
            assert inquiry.status_code == 202, inquiry.text
            tampered_payload = deepcopy(inquiry_payload)
            tampered_payload["inquiry"]["product_context"]["displayed_price"] = "USD 1.00"
            tampered = await client.post(
                "/api/v1/public/lead-submissions",
                headers={
                    "Idempotency-Key": f"tampered-product-inquiry-{uuid4()}",
                    "X-Site-Token": "local-public-site-token",
                },
                json=tampered_payload,
            )
            assert tampered.status_code == 422
            lead_id = UUID(inquiry.json()["submission_id"])
            async with session_factory() as session:
                await session.execute(
                    text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                    {"tenant_id": str(TENANT_ID)},
                )
                lead = await session.scalar(select(Lead).where(Lead.id == lead_id))
                assert lead is not None
                assert lead.requirements["product_context"] == {
                    "source": "product_page",
                    "product_locale": "en",
                    "product_name": body["title"],
                    "product_slug": slug,
                    "sku_model": "TEST-PT-01",
                    "price_mode": "fixed",
                    "displayed_price": "USD 180.00",
                }

            archived = await client.post(
                f"/api/v1/public-content/items/{item['id']}/archive",
                headers=headers(f"archive-{slug}", 4),
                json={"reason": "Remove published product test fixture."},
            )
            assert archived.status_code == 200
            assert (
                await client.get(
                    f"/api/v1/public-content/render/product/{slug}",
                    params={"locale": "en"},
                )
            ).status_code == 404
            assert not any(
                entry["slug"] == slug
                for entry in (
                    await client.get(
                        "/api/v1/public-content/catalog/products",
                        params={"locale": "en"},
                    )
                ).json()
            )
    finally:
        app.dependency_overrides.clear()
