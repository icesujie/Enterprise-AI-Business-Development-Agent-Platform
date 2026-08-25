from __future__ import annotations

import base64
import struct
import zlib
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from pypdf import PdfWriter

from sari_api.adapters.media_storage import LocalMediaStorage, get_media_storage
from sari_api.adapters.public_content_structuring_provider import (
    MockPublicContentStructuringProvider,
)
from sari_api.api.dependencies import get_token_identity
from sari_api.api.routes.public_content_structuring import (
    get_public_content_structuring_provider,
)
from sari_api.domain.identity import TokenIdentity
from sari_api.domain.public_content_structuring import PublicContentStructuringResult
from sari_api.main import app

ADMIN_SUBJECT = "30000000-0000-4000-8000-000000000001"
SALES_SUBJECT = "30000000-0000-4000-8000-000000000002"


async def admin_identity() -> TokenIdentity:
    return TokenIdentity(subject=ADMIN_SUBJECT, email="admin@sari-arta.example")


async def sales_identity() -> TokenIdentity:
    return TokenIdentity(subject=SALES_SUBJECT, email="sales@sari-arta.example")


async def unknown_identity() -> TokenIdentity:
    return TokenIdentity(subject=str(uuid4()), email="unknown@example.invalid")


class CountingProvider:
    provider_type = "mock"
    model_id = "counting-source-structuring-v1"

    def __init__(self) -> None:
        self.calls = 0
        self._delegate = MockPublicContentStructuringProvider()

    async def structure(
        self,
        *,
        import_id: UUID,
        import_result: dict[str, object],
        selected_page_type: str,
        locale: str,
    ) -> PublicContentStructuringResult:
        self.calls += 1
        return await self._delegate.structure(
            import_id=import_id,
            import_result=import_result,
            selected_page_type=selected_page_type,
            locale=locale,
        )


def png() -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data))
        )

    header = struct.pack(">IIBBBBB", 2, 3, 8, 2, 0, 0, 0)
    pixels = b"".join(b"\x00" + b"\x80\x80\x80" * 2 for _ in range(3))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(
        b"IDAT", zlib.compress(pixels)
    ) + chunk(b"IEND", b"")


def blank_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


async def import_html(client: httpx.AsyncClient) -> dict[str, Any]:
    image = base64.b64encode(png()).decode()
    html = f"""
      <html><head><title>Synthetic School Kitchen Solution</title></head><body>
      <h1>School kitchen planning</h1>
      <p>Plan preparation, cooking, washing and storage areas for the school canteen.</p>
      <h2>Project requirements</h2>
      <p>Review the site, workflow and known operating requirements with the engineering team.</p>
      <img alt="synthetic plan" src="data:image/png;base64,{image}">
      </body></html>
    """.encode()
    response = await client.post(
        "/api/v1/public-content/imports",
        files={"file": ("synthetic-school.html", html, "text/html")},
    )
    assert response.status_code == 201, response.text
    assert response.json()["processing_status"] == "completed"
    return response.json()


async def structure(
    client: httpx.AsyncClient, import_id: str, page_type: str = "solution"
) -> httpx.Response:
    return await client.post(
        f"/api/v1/public-content/imports/{import_id}/structure",
        json={"page_type": page_type, "locale": "en"},
    )


@pytest.mark.asyncio
async def test_completed_import_structures_solution_and_creates_governed_draft_only(
    tmp_path: Path,
) -> None:
    provider = CountingProvider()
    app.dependency_overrides[get_token_identity] = sales_identity
    app.dependency_overrides[get_media_storage] = lambda: LocalMediaStorage(tmp_path / "media")
    app.dependency_overrides[get_public_content_structuring_provider] = lambda: provider
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            imported = await import_html(client)
            response = await structure(client, str(imported["id"]))
            assert response.status_code == 201, response.text
            run = response.json()
            assert run["status"] == "completed"
            assert run["selected_page_type"] == "solution"
            assert run["provider"] == "mock"
            assert provider.calls == 1
            result = run["result"]
            assert "School Kitchen" in result["title"]
            serialized = str(result)
            for unsupported in ("price", "certification", "delivery guarantee", "customer name"):
                assert unsupported not in serialized.casefold()
            assert result["evidence"]
            assert result["evidence"][0]["import_id"] == imported["id"]
            assert result["media_suggestions"][0]["media_asset_id"] in imported[
                "extracted_media_ids"
            ]

            media_id = imported["extracted_media_ids"][0]
            media = await client.get(f"/api/v1/media/assets/{media_id}")
            assert media.json()["visibility"] == "private"
            assert media.json()["public_use_status"] == "uploaded"

            slug = f"structured-school-{uuid4().hex[:8]}"
            draft = await client.post(
                f"/api/v1/public-content/imports/{imported['id']}/drafts",
                headers={"Idempotency-Key": f"draft-{uuid4()}"},
                json={
                    "structuring_run_id": run["id"],
                    "slug": slug,
                    "title": result["title"],
                    "summary": result["summary"],
                    "seo_title": result["seo_title"],
                    "seo_description": result["seo_description"],
                    "structured_content": result["cms_structured_content"],
                    "media_references": [
                        {
                            "media_asset_id": media_id,
                            "role": "hero",
                            "alt_text": "Synthetic imported media pending human review.",
                        }
                    ],
                    "is_synthetic": True,
                },
            )
            assert draft.status_code == 201, draft.text
            item = draft.json()
            assert item["status"] == "draft"
            assert item["approved_version_id"] is None
            assert item["published_version_id"] is None
            assert item["current_version"]["origin"] == "ai_draft"
            assert item["current_version"]["source_type"] == "html_import"
            assert item["current_version"]["source_reference_id"] == imported["id"]
            assert item["current_version"]["source_checksum"] == imported["checksum"]
            assert (await client.get(f"/api/v1/media/public/{media_id}")).status_code == 404

            app.dependency_overrides[get_token_identity] = admin_identity
            publish = await client.post(
                f"/api/v1/public-content/items/{item['id']}/publish",
                headers={"If-Match": '"1"', "Idempotency-Key": f"publish-{uuid4()}"},
                json={
                    "public_content_version_id": item["current_version"]["id"],
                    "content_sha256": item["current_version"]["content_sha256"],
                    "comment": "Publishing must remain blocked for an unapproved Draft.",
                },
            )
            assert publish.status_code == 409
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_case_study_keeps_missing_facts_explicit_and_mock_is_deterministic(
    tmp_path: Path,
) -> None:
    app.dependency_overrides[get_token_identity] = sales_identity
    app.dependency_overrides[get_media_storage] = lambda: LocalMediaStorage(tmp_path / "media")
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            imported = await import_html(client)
            first = await structure(client, str(imported["id"]), "case_study")
            second = await structure(client, str(imported["id"]), "case_study")
            assert first.status_code == second.status_code == 201
            left = first.json()["result"]
            right = second.json()["result"]
            assert left == right
            assert first.json()["outcome"] == "requires_human_input"
            assert {"location", "industry", "project_type"}.issubset(
                set(first.json()["missing_fields"])
            )
            assert left["content"]["location"] is None
            assert left["content"]["industry"] is None
            assert left["content"]["project_type"] is None
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_failed_import_and_denied_tenant_do_not_call_provider(tmp_path: Path) -> None:
    provider = CountingProvider()
    app.dependency_overrides[get_token_identity] = sales_identity
    app.dependency_overrides[get_media_storage] = lambda: LocalMediaStorage(tmp_path / "media")
    app.dependency_overrides[get_public_content_structuring_provider] = lambda: provider
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            failed = await client.post(
                "/api/v1/public-content/imports",
                files={"file": ("scanned.pdf", blank_pdf(), "application/pdf")},
            )
            assert failed.status_code == 201
            assert failed.json()["processing_status"] == "failed"
            blocked = await structure(client, failed.json()["id"])
            assert blocked.status_code == 409
            assert provider.calls == 0

            completed = await import_html(client)
            denied_tenant = await client.post(
                f"/api/v1/public-content/imports/{completed['id']}/structure",
                headers={"X-Tenant-Id": str(uuid4())},
                json={"page_type": "solution", "locale": "en"},
            )
            assert denied_tenant.status_code == 403
            assert provider.calls == 0

            app.dependency_overrides[get_token_identity] = unknown_identity
            denied_identity = await structure(client, str(completed["id"]))
            assert denied_identity.status_code == 403
            assert provider.calls == 0
    finally:
        app.dependency_overrides.clear()
