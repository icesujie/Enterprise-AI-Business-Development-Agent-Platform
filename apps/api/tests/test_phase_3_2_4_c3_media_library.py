from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from sari_api.adapters.media_storage import LocalMediaStorage, get_media_storage
from sari_api.api.dependencies import get_token_identity
from sari_api.core.config import get_settings
from sari_api.domain.identity import TokenIdentity
from sari_api.main import app

ADMIN_SUBJECT = "30000000-0000-4000-8000-000000000001"
SALES_SUBJECT = "30000000-0000-4000-8000-000000000002"
ADMIN_MEMBERSHIP_ID = "40000000-0000-4000-8000-000000000001"


async def admin_identity() -> TokenIdentity:
    return TokenIdentity(subject=ADMIN_SUBJECT, email="admin@sari-arta.example")


async def sales_identity() -> TokenIdentity:
    return TokenIdentity(subject=SALES_SUBJECT, email="sales@sari-arta.example")


def png() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\x0dIHDR"
        + (2).to_bytes(4, "big")
        + (3).to_bytes(4, "big")
        + b"\x08\x02\x00\x00\x00"
        + b"\x00\x00\x00\x00"
    )


def jpeg() -> bytes:
    return bytes.fromhex("ffd8ffc00011080003000203011100021100031100ffd9")


def webp() -> bytes:
    return (
        b"RIFF"
        + (22).to_bytes(4, "little")
        + b"WEBPVP8X"
        + (10).to_bytes(4, "little")
        + b"\x00\x00\x00\x00"
        + (1).to_bytes(3, "little")
        + (2).to_bytes(3, "little")
    )


def version_header(version: int) -> dict[str, str]:
    return {"If-Match": f'"{version}"'}


async def upload(
    client: httpx.AsyncClient,
    *,
    name: str = "fixture.png",
    mime: str = "image/png",
    content: bytes | None = None,
) -> dict[str, object]:
    app.dependency_overrides[get_token_identity] = sales_identity
    response = await client.post(
        "/api/v1/media/assets",
        files={"file": (name, content if content is not None else png(), mime)},
        data={
            "title": f"Synthetic {name}",
            "alt_text": "Synthetic image used only for media governance testing.",
            "caption": "Synthetic test fixture.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_supported_images_upload_as_private_and_invalid_files_are_rejected(
    tmp_path: Path,
) -> None:
    storage = LocalMediaStorage(tmp_path / "media")
    app.dependency_overrides[get_media_storage] = lambda: storage
    transport = httpx.ASGITransport(app=app)
    assets: list[dict[str, object]] = []
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            for name, mime, content in (
                ("fixture.jpg", "image/jpeg", jpeg()),
                ("fixture.png", "image/png", png()),
                ("fixture.webp", "image/webp", webp()),
            ):
                asset = await upload(client, name=name, mime=mime, content=content)
                assets.append(asset)
                assert asset["visibility"] == "private"
                assert asset["public_use_status"] == "uploaded"
                assert asset["storage_provider"] == "local"
                assert "storage_key" not in asset

            disguised = await client.post(
                "/api/v1/media/assets",
                files={"file": ("unsafe.png", b"<script>alert(1)</script>", "image/png")},
                data={"title": "Unsafe", "alt_text": "Unsafe executable content"},
            )
            assert disguised.status_code == 415
            svg = await client.post(
                "/api/v1/media/assets",
                files={"file": ("unsafe.svg", b"<svg></svg>", "image/svg+xml")},
                data={"title": "SVG", "alt_text": "Unsupported SVG fixture"},
            )
            assert svg.status_code == 415

            settings = get_settings()
            original_limit = settings.media_max_upload_bytes
            settings.media_max_upload_bytes = 1024
            try:
                oversized = await client.post(
                    "/api/v1/media/assets",
                    files={"file": ("large.png", b"x" * 1025, "image/png")},
                    data={"title": "Large", "alt_text": "Oversized image fixture"},
                )
                assert oversized.status_code == 413
            finally:
                settings.media_max_upload_bytes = original_limit

            app.dependency_overrides[get_token_identity] = admin_identity
            for asset in assets:
                archived = await client.post(
                    f"/api/v1/media/assets/{asset['id']}/archive", headers=version_header(1)
                )
                assert archived.status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_media_governance_tenant_isolation_public_resolution_and_revocation(
    tmp_path: Path,
) -> None:
    storage = LocalMediaStorage(tmp_path / "media")
    app.dependency_overrides[get_media_storage] = lambda: storage
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            asset = await upload(client)
            asset_id = asset["id"]
            private = await client.get(f"/api/v1/media/public/{asset_id}")
            assert private.status_code == 404

            isolated = await client.get(
                f"/api/v1/media/assets/{asset_id}",
                headers={"X-Tenant-Id": str(uuid4())},
            )
            assert isolated.status_code == 403

            edited = await client.patch(
                f"/api/v1/media/assets/{asset_id}",
                headers=version_header(1),
                json={
                    "title": "Updated synthetic media",
                    "alt_text": "Updated factual alt text for a synthetic fixture.",
                    "caption": "Updated synthetic caption.",
                },
            )
            assert edited.status_code == 200, edited.text
            assert edited.json()["title"] == "Updated synthetic media"

            submitted = await client.post(
                f"/api/v1/media/assets/{asset_id}/submit-review", headers=version_header(2)
            )
            assert submitted.status_code == 200
            denied_self_approval = await client.post(
                f"/api/v1/media/assets/{asset_id}/approve", headers=version_header(3)
            )
            assert denied_self_approval.status_code == 403
            app.dependency_overrides[get_token_identity] = admin_identity
            approved = await client.post(
                f"/api/v1/media/assets/{asset_id}/approve", headers=version_header(3)
            )
            assert approved.status_code == 200, approved.text
            assert approved.json()["visibility"] == "public"

            public = await client.get(f"/api/v1/media/public/{asset_id}")
            assert public.status_code == 200
            assert public.content == png()
            assert public.headers["content-type"] == "image/png"

            revoked = await client.post(
                f"/api/v1/media/assets/{asset_id}/revoke", headers=version_header(4)
            )
            assert revoked.status_code == 200
            assert (await client.get(f"/api/v1/media/public/{asset_id}")).status_code == 404
            audit = await client.get(f"/api/v1/media/assets/{asset_id}/audit")
            assert audit.status_code == 200
            assert {
                "media.uploaded",
                "media.metadata_updated",
                "media.submit_review",
                "media.approve",
                "media.revoke",
            }.issubset({entry["action"] for entry in audit.json()})
            archived = await client.post(
                f"/api/v1/media/assets/{asset_id}/archive", headers=version_header(5)
            )
            assert archived.status_code == 200

            admin_upload = await client.post(
                "/api/v1/media/assets",
                files={"file": ("admin.png", png(), "image/png")},
                data={
                    "title": "Administrator fixture",
                    "alt_text": "Synthetic administrator upload fixture.",
                },
            )
            assert admin_upload.status_code == 201
            admin_id = admin_upload.json()["id"]
            assert (
                await client.post(
                    f"/api/v1/media/assets/{admin_id}/submit-review",
                    headers=version_header(1),
                )
            ).status_code == 200
            self_approval = await client.post(
                f"/api/v1/media/assets/{admin_id}/approve", headers=version_header(2)
            )
            assert self_approval.status_code == 200
            assert self_approval.json()["uploaded_by"] == ADMIN_MEMBERSHIP_ID
            assert self_approval.json()["approved_by"] == ADMIN_MEMBERSHIP_ID
            assert self_approval.json()["approved_at"] is not None
            audit = await client.get(f"/api/v1/media/assets/{admin_id}/audit")
            approval_event = next(
                event for event in audit.json() if event["action"] == "media.approve"
            )
            assert approval_event["actor_membership_id"] == ADMIN_MEMBERSHIP_ID
            assert approval_event["details"] == {
                "self_approval": True,
                "uploaded_by": ADMIN_MEMBERSHIP_ID,
                "approved_by": ADMIN_MEMBERSHIP_ID,
            }
            assert (
                await client.get(f"/api/v1/media/public/{admin_id}")
            ).status_code == 200
            revoked_self_approved = await client.post(
                f"/api/v1/media/assets/{admin_id}/revoke", headers=version_header(3)
            )
            assert revoked_self_approved.status_code == 200
            assert (
                await client.get(f"/api/v1/media/public/{admin_id}")
            ).status_code == 404
            assert (
                await client.post(
                    f"/api/v1/media/assets/{admin_id}/archive", headers=version_header(4)
                )
            ).status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_published_public_content_resolves_only_approved_stable_media_id(
    tmp_path: Path,
) -> None:
    storage = LocalMediaStorage(tmp_path / "media")
    app.dependency_overrides[get_media_storage] = lambda: storage
    transport = httpx.ASGITransport(app=app)
    slug = f"media-content-{uuid4().hex[:10]}"
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            asset = await upload(client)
            asset_id = asset["id"]
            submitted_media = await client.post(
                f"/api/v1/media/assets/{asset_id}/submit-review", headers=version_header(1)
            )
            assert submitted_media.status_code == 200
            app.dependency_overrides[get_token_identity] = admin_identity
            assert (
                await client.post(
                    f"/api/v1/media/assets/{asset_id}/approve", headers=version_header(2)
                )
            ).status_code == 200

            app.dependency_overrides[get_token_identity] = sales_identity
            content = await client.post(
                "/api/v1/public-content/items",
                headers={"Idempotency-Key": f"create-{slug}"},
                json=public_content_payload(slug, str(asset_id)),
            )
            assert content.status_code == 201, content.text
            item = content.json()
            version = item["current_version"]
            exact = {
                "public_content_version_id": version["id"],
                "content_sha256": version["content_sha256"],
                "comment": "Synthetic governed media reference test.",
            }
            assert (
                await client.post(
                    f"/api/v1/public-content/items/{item['id']}/submit-review",
                    headers={"If-Match": '"1"', "Idempotency-Key": f"submit-{slug}"},
                    json=exact,
                )
            ).status_code == 200
            app.dependency_overrides[get_token_identity] = admin_identity
            assert (
                await client.post(
                    f"/api/v1/public-content/items/{item['id']}/decisions",
                    headers={"If-Match": '"2"', "Idempotency-Key": f"approve-{slug}"},
                    json={**exact, "decision": "approved"},
                )
            ).status_code == 200
            published = await client.post(
                f"/api/v1/public-content/items/{item['id']}/publish",
                headers={"If-Match": '"3"', "Idempotency-Key": f"publish-{slug}"},
                json=exact,
            )
            assert published.status_code == 200, published.text
            rendered = await client.get(
                f"/api/v1/public-content/render/solution/{slug}", params={"locale": "en"}
            )
            assert rendered.status_code == 200
            reference = rendered.json()["media_references"][0]
            assert reference["media_asset_id"] == str(asset_id)
            assert reference["url"] == f"/api/v1/media/public/{asset_id}"

            revoked = await client.post(
                f"/api/v1/media/assets/{asset_id}/revoke", headers=version_header(3)
            )
            assert revoked.status_code == 200
            assert (await client.get(f"/api/v1/media/public/{asset_id}")).status_code == 404
            rendered_after_revoke = await client.get(
                f"/api/v1/public-content/render/solution/{slug}", params={"locale": "en"}
            )
            assert rendered_after_revoke.status_code == 200
            assert rendered_after_revoke.json()["media_references"] == []
            archived_content = await client.post(
                f"/api/v1/public-content/items/{item['id']}/archive",
                headers={"If-Match": '"4"', "Idempotency-Key": f"archive-{slug}"},
                json={"reason": "Remove public media reference fixture."},
            )
            assert archived_content.status_code == 200
            assert (
                await client.post(
                    f"/api/v1/media/assets/{asset_id}/archive", headers=version_header(4)
                )
            ).status_code == 200
    finally:
        app.dependency_overrides.clear()


def public_content_payload(slug: str, asset_id: str) -> dict[str, object]:
    return {
        "page_type": "solution",
        "slug": slug,
        "locale": "en",
        "title": "Synthetic media reference page",
        "summary": "Synthetic page used only to validate stable media references.",
        "seo_title": "Synthetic media reference page",
        "seo_description": "Synthetic public content media reference validation fixture.",
        "structured_content": {
            "overview": ["Synthetic public content fixture."],
            "customer_needs": ["Stable media references"],
            "service_scope": [{"title": "Media", "description": "Governed image reference."}],
            "workflow_areas": [{"title": "Review", "description": "Human media approval."}],
            "related_industries": [],
            "related_projects": [],
            "cta": {
                "label": "Start project consultation",
                "description": "Share requirements for human review.",
                "destination": "public_consultation_agent",
            },
        },
        "media_references": [
            {
                "media_asset_id": asset_id,
                "role": "hero",
                "alt_text": "Synthetic governed public content image.",
                "caption": "Synthetic fixture.",
            }
        ],
        "source_type": "manual",
        "is_synthetic": False,
    }
