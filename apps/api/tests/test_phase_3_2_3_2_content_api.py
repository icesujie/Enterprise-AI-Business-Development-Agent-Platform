from __future__ import annotations

from uuid import uuid4

import httpx
import pytest

from sari_api.api.dependencies import get_token_identity
from sari_api.domain.identity import TokenIdentity
from sari_api.main import app

SALES_SUBJECT = "30000000-0000-4000-8000-000000000002"


async def sales_identity() -> TokenIdentity:
    return TokenIdentity(subject=SALES_SUBJECT, email="sales@sari-arta.example")


async def unknown_agent_identity() -> TokenIdentity:
    return TokenIdentity(subject="synthetic-marketing-agent", email=None)


def key(value: str) -> dict[str, str]:
    return {"Idempotency-Key": value}


@pytest.mark.asyncio
async def test_request_crud_filters_etag_and_manual_asset_association() -> None:
    suffix = uuid4().hex[:10]
    app.dependency_overrides[get_token_identity] = sales_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            request_payload = {
                "domain_key": "commercial_kitchen",
                "content_type": "facebook_post",
                "audience": "factories",
                "language": "en",
                "channel": "facebook",
                "business_objective": "Explain a synthetic factory cafeteria solution.",
                "topic": f"Synthetic factory content {suffix}",
                "call_to_action": "Request a project consultation",
            }
            created = await client.post(
                "/api/v1/content/requests",
                headers=key(f"request-api-{suffix}"),
                json=request_payload,
            )
            assert created.status_code == 201, created.text
            request_id = created.json()["id"]

            detail = await client.get(f"/api/v1/content/requests/{request_id}")
            assert detail.status_code == 200
            etag = detail.headers["etag"]
            updated = await client.patch(
                f"/api/v1/content/requests/{request_id}",
                headers={**key(f"request-update-{suffix}"), "If-Match": etag},
                json={"topic": f"Updated synthetic factory content {suffix}"},
            )
            assert updated.status_code == 200, updated.text
            assert updated.json()["topic"].startswith("Updated")
            assert updated.headers["etag"] != etag

            stale = await client.patch(
                f"/api/v1/content/requests/{request_id}",
                headers={**key(f"request-stale-{suffix}"), "If-Match": etag},
                json={"topic": "Stale overwrite must fail"},
            )
            assert stale.status_code == 412

            listed = await client.get(
                "/api/v1/content/requests",
                params={
                    "status": "draft",
                    "content_type": "facebook_post",
                    "language": "en",
                    "search": suffix,
                },
            )
            assert listed.status_code == 200
            assert [item["id"] for item in listed.json()] == [request_id]

            asset = await client.post(
                "/api/v1/content/assets",
                headers=key(f"manual-asset-{suffix}"),
                json={
                    "domain_key": "commercial_kitchen",
                    "request_id": request_id,
                    "title": f"Synthetic Factory Post {suffix}",
                    "content_type": "facebook_post",
                    "audience": "factories",
                    "language": "en",
                    "channel": "facebook",
                    "content_body": {"body": "Synthetic governed manual content."},
                    "plain_text": "Synthetic governed manual content.",
                    "claims": [],
                    "citations": [],
                },
            )
            assert asset.status_code == 201, asset.text
            assert asset.json()["request_id"] == request_id

            associated_request = await client.get(
                f"/api/v1/content/requests/{request_id}"
            )
            assert associated_request.json()["status"] == "completed"
            assert associated_request.json()["result_asset_id"] == asset.json()["id"]

            update_associated = await client.patch(
                f"/api/v1/content/requests/{request_id}",
                headers={
                    **key(f"request-associated-{suffix}"),
                    "If-Match": associated_request.headers["etag"],
                },
                json={"topic": "Forbidden after association"},
            )
            assert update_associated.status_code == 409

            assets = await client.get(
                "/api/v1/content/assets",
                params={
                    "status": "draft",
                    "content_type": "facebook_post",
                    "language": "en",
                    "search": suffix,
                },
            )
            assert assets.status_code == 200
            assert [item["id"] for item in assets.json()] == [asset.json()["id"]]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_non_human_agent_identity_cannot_use_content_approval_api() -> None:
    app.dependency_overrides[get_token_identity] = unknown_agent_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/content/assets/{uuid4()}/decisions",
                headers={**key(f"agent-denied-{uuid4().hex}"), "If-Match": '"1"'},
                json={
                    "content_version_id": str(uuid4()),
                    "content_sha256": "0" * 64,
                    "decision": "approved",
                },
            )
            assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()
