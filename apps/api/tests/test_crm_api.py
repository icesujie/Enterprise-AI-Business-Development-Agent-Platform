from __future__ import annotations

from uuid import uuid4

import httpx
import pytest

from sari_api.api.dependencies import get_token_identity
from sari_api.api.routes.public_leads import enforce_public_rate_limit
from sari_api.domain.identity import TokenIdentity
from sari_api.main import app

ADMIN_SUBJECT = "30000000-0000-4000-8000-000000000001"


async def admin_identity() -> TokenIdentity:
    return TokenIdentity(subject=ADMIN_SUBJECT, email="admin@sari-arta.example")


async def allow_public_request() -> None:
    return None


@pytest.mark.asyncio
async def test_company_contact_and_lead_vertical_slice() -> None:
    suffix = uuid4().hex[:10]
    app.dependency_overrides[get_token_identity] = admin_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            organization = await client.post(
                "/api/v1/organizations",
                json={
                    "legal_name": f"Nusantara Kitchens {suffix}",
                    "website_url": f"https://{suffix}.example.com",
                    "country_code": "id",
                    "city": "Surabaya",
                },
            )
            assert organization.status_code == 201, organization.text
            organization_body = organization.json()
            assert organization_body["domain"] == f"{suffix}.example.com"

            duplicate = await client.post(
                "/api/v1/organizations",
                json={
                    "legal_name": f"Duplicate {suffix}",
                    "domain": f"{suffix}.example.com",
                },
            )
            assert duplicate.status_code == 201
            assert duplicate.json()["duplicate_warnings"]

            contact = await client.post(
                "/api/v1/contacts",
                json={
                    "organization_id": organization_body["id"],
                    "first_name": "Andi",
                    "last_name": "Pratama",
                    "email": f"andi-{suffix}@example.co.id",
                    "phone_e164": "+6281234567890",
                    "preferred_language": "id",
                },
            )
            assert contact.status_code == 201, contact.text

            lead = await client.post(
                "/api/v1/leads",
                json={
                    "organization_id": organization_body["id"],
                    "contact_id": contact.json()["id"],
                    "source_channel": "manual",
                    "inquiry_summary": "Hotel central kitchen for 2,000 meals per day.",
                    "priority": "high",
                    "project_country_code": "ID",
                    "project_city": "Surabaya",
                    "project_type": "Hotel central kitchen",
                    "expected_capacity": "2,000 meals/day",
                },
            )
            assert lead.status_code == 201, lead.text
            lead_body = lead.json()

            updated = await client.patch(
                f"/api/v1/leads/{lead_body['id']}",
                headers={"If-Match": '"1"'},
                json={"priority": "urgent", "status": "qualifying"},
            )
            assert updated.status_code == 200, updated.text
            assert updated.json()["version"] == 2
            assert updated.headers["etag"] == '"2"'

            stale = await client.patch(
                f"/api/v1/leads/{lead_body['id']}",
                headers={"If-Match": '"1"'},
                json={"priority": "low"},
            )
            assert stale.status_code == 409

            lead_list = await client.get("/api/v1/leads", params={"status": "qualifying"})
            assert lead_list.status_code == 200
            assert lead_body["id"] in {item["id"] for item in lead_list.json()["items"]}
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_public_submission_is_idempotent_and_private() -> None:
    key = f"website-{uuid4()}"
    payload = {
        "contact": {
            "first_name": "Dewi",
            "email": f"dewi-{uuid4().hex[:8]}@example.co.id",
            "phone_e164": "+6281234567891",
            "preferred_language": "id",
        },
        "organization": {
            "name": "Synthetic Hospitality Group",
            "website_url": "https://synthetic-hospitality.example",
            "country_code": "ID",
        },
        "inquiry": {
            "message": "We need a commercial kitchen for a new hotel in Bali.",
            "project_country_code": "ID",
            "project_city": "Bali",
            "target_timeline": "Q1 2027",
        },
        "attribution": {"source": "website", "campaign": "m3-test"},
        "consent": {
            "privacy_policy_version": "test-v1",
            "contact_consent": True,
            "marketing_consent": False,
        },
    }
    app.dependency_overrides[enforce_public_rate_limit] = allow_public_request
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            headers = {
                "Idempotency-Key": key,
                "X-Site-Token": "local-public-site-token",
            }
            first = await client.post(
                "/api/v1/public/lead-submissions", headers=headers, json=payload
            )
            second = await client.post(
                "/api/v1/public/lead-submissions", headers=headers, json=payload
            )
            assert first.status_code == 202, first.text
            assert second.status_code == 202
            assert second.json() == first.json()
            assert set(first.json()) == {"submission_id", "status", "message"}

            changed_payload = {
                **payload,
                "inquiry": {**payload["inquiry"], "project_city": "Jakarta"},
            }
            conflict = await client.post(
                "/api/v1/public/lead-submissions",
                headers=headers,
                json=changed_payload,
            )
            assert conflict.status_code == 409
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_crm_endpoints_require_authentication() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/leads")

    assert response.status_code == 401
