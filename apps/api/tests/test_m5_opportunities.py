from __future__ import annotations

import asyncio
from uuid import uuid4

import httpx
import pytest

from sari_api.api.dependencies import get_token_identity
from sari_api.domain.identity import TokenIdentity
from sari_api.main import app

ADMIN_SUBJECT = "30000000-0000-4000-8000-000000000001"


async def admin_identity() -> TokenIdentity:
    return TokenIdentity(subject=ADMIN_SUBJECT, email="admin@sari-arta.example")


async def create_qualified_lead(client: httpx.AsyncClient) -> dict[str, object]:
    suffix = uuid4().hex[:10]
    organization = await client.post(
        "/api/v1/organizations",
        json={"legal_name": f"M5 Synthetic Kitchens {suffix}", "country_code": "ID"},
    )
    assert organization.status_code == 201, organization.text
    contact = await client.post(
        "/api/v1/contacts",
        json={
            "organization_id": organization.json()["id"],
            "first_name": "Ayu",
            "email": f"ayu-{suffix}@example.co.id",
        },
    )
    assert contact.status_code == 201, contact.text
    lead = await client.post(
        "/api/v1/leads",
        json={
            "organization_id": organization.json()["id"],
            "contact_id": contact.json()["id"],
            "source_channel": "manual",
            "inquiry_summary": "Synthetic hotel kitchen project for M5 tests.",
            "project_type": "Hotel kitchen",
            "project_city": "Jakarta",
            "expected_capacity": "1,200 meals/day",
            "estimated_value": "850000000",
            "currency": "IDR",
        },
    )
    assert lead.status_code == 201, lead.text
    qualified = await client.patch(
        f"/api/v1/leads/{lead.json()['id']}",
        headers={"If-Match": '"1"'},
        json={"status": "qualified"},
    )
    assert qualified.status_code == 200, qualified.text
    return {
        "lead": qualified.json(),
        "organization": organization.json(),
        "contact": contact.json(),
    }


@pytest.mark.asyncio
async def test_conversion_is_transactional_idempotent_and_reuses_customer_records() -> None:
    app.dependency_overrides[get_token_identity] = admin_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            records = await create_qualified_lead(client)
            lead = records["lead"]
            assert isinstance(lead, dict)
            payload = {
                "name": "Jakarta hotel kitchen",
                "expected_close_date": "2026-12-15",
            }
            key = f"conversion-{uuid4()}"
            headers = {"If-Match": '"2"', "Idempotency-Key": key}
            first = await client.post(
                f"/api/v1/leads/{lead['id']}/conversions", headers=headers, json=payload
            )
            replay = await client.post(
                f"/api/v1/leads/{lead['id']}/conversions", headers=headers, json=payload
            )
            assert first.status_code == 201, first.text
            assert replay.status_code == 201
            assert replay.json() == first.json()
            opportunity = first.json()
            assert opportunity["organization_id"] == records["organization"]["id"]
            assert opportunity["primary_contact_id"] == records["contact"]["id"]
            assert opportunity["source_lead_id"] == lead["id"]
            assert opportunity["stage"] == "discovery"
            assert opportunity["estimated_value"] == "850000000.0000"

            duplicate = await client.post(
                f"/api/v1/leads/{lead['id']}/conversions",
                headers={"If-Match": '"2"', "Idempotency-Key": f"conversion-{uuid4()}"},
                json=payload,
            )
            assert duplicate.status_code == 200, duplicate.text
            assert duplicate.json()["id"] == opportunity["id"]

            changed_replay = await client.post(
                f"/api/v1/leads/{lead['id']}/conversions",
                headers=headers,
                json={**payload, "name": "Changed request"},
            )
            assert changed_replay.status_code == 409

            converted_lead = await client.get(f"/api/v1/leads/{lead['id']}")
            assert converted_lead.json()["status"] == "converted"
            assert converted_lead.json()["version"] == 3

            listed = await client.get("/api/v1/opportunities", params={"stage": "discovery"})
            assert listed.status_code == 200
            assert opportunity["id"] in {item["id"] for item in listed.json()["items"]}
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_conversion_failure_rolls_back_lead_and_opportunity() -> None:
    app.dependency_overrides[get_token_identity] = admin_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            records = await create_qualified_lead(client)
            lead = records["lead"]
            assert isinstance(lead, dict)
            failed = await client.post(
                f"/api/v1/leads/{lead['id']}/conversions",
                headers={
                    "If-Match": '"2"',
                    "Idempotency-Key": f"conversion-{uuid4()}",
                },
                json={
                    "name": "Must roll back",
                    "owner_membership_id": str(uuid4()),
                },
            )
            assert failed.status_code == 404, failed.text

            unchanged = await client.get(f"/api/v1/leads/{lead['id']}")
            assert unchanged.json()["status"] == "qualified"
            assert unchanged.json()["version"] == 2
            listed = await client.get("/api/v1/opportunities", params={"search": "Must roll back"})
            assert listed.json()["items"] == []
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_concurrent_conversion_requests_resolve_to_one_opportunity() -> None:
    app.dependency_overrides[get_token_identity] = admin_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            records = await create_qualified_lead(client)
            lead = records["lead"]
            assert isinstance(lead, dict)

            async def convert(key: str) -> httpx.Response:
                return await client.post(
                    f"/api/v1/leads/{lead['id']}/conversions",
                    headers={"If-Match": '"2"', "Idempotency-Key": key},
                    json={"name": "Concurrent conversion test"},
                )

            first, second = await asyncio.gather(
                convert(f"conversion-{uuid4()}"),
                convert(f"conversion-{uuid4()}"),
            )
            assert {first.status_code, second.status_code} == {200, 201}
            assert first.json()["id"] == second.json()["id"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_opportunity_stage_transitions_are_guarded_and_audited() -> None:
    app.dependency_overrides[get_token_identity] = admin_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            records = await create_qualified_lead(client)
            lead = records["lead"]
            assert isinstance(lead, dict)
            converted = await client.post(
                f"/api/v1/leads/{lead['id']}/conversions",
                headers={
                    "If-Match": '"2"',
                    "Idempotency-Key": f"conversion-{uuid4()}",
                },
                json={"name": "Stage transition test"},
            )
            opportunity = converted.json()

            invalid = await client.post(
                f"/api/v1/opportunities/{opportunity['id']}/stage-transitions",
                headers={"If-Match": '"1"'},
                json={"stage": "won"},
            )
            assert invalid.status_code == 409

            moved = await client.post(
                f"/api/v1/opportunities/{opportunity['id']}/stage-transitions",
                headers={"If-Match": '"1"'},
                json={"stage": "requirements_confirmed"},
            )
            assert moved.status_code == 200, moved.text
            assert moved.json()["stage"] == "requirements_confirmed"
            assert moved.json()["probability"] == "35.00"
            assert moved.json()["version"] == 2

            stale = await client.post(
                f"/api/v1/opportunities/{opportunity['id']}/stage-transitions",
                headers={"If-Match": '"1"'},
                json={"stage": "proposal"},
            )
            assert stale.status_code == 409

            lost_without_reason = await client.post(
                f"/api/v1/opportunities/{opportunity['id']}/stage-transitions",
                headers={"If-Match": '"2"'},
                json={"stage": "lost"},
            )
            assert lost_without_reason.status_code == 409

            activities = await client.get(
                f"/api/v1/opportunities/{opportunity['id']}/activities"
            )
            assert activities.status_code == 200
            assert {item["activity_type"] for item in activities.json()} >= {
                "lead_converted",
                "opportunity_stage_changed",
            }
    finally:
        app.dependency_overrides.clear()
