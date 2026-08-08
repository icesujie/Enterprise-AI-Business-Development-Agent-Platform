from __future__ import annotations

from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import text

from sari_api.adapters.database import session_factory
from sari_api.api.dependencies import get_token_identity
from sari_api.domain.identity import TokenIdentity
from sari_api.main import app

ADMIN_SUBJECT = "30000000-0000-4000-8000-000000000001"
SALES_SUBJECT = "30000000-0000-4000-8000-000000000002"
SARI_ARTA_ID = UUID("10000000-0000-4000-8000-000000000001")


def override_identity(subject: str) -> None:
    async def identity() -> TokenIdentity:
        return TokenIdentity(subject=subject, email=None)

    app.dependency_overrides[get_token_identity] = identity


@pytest.mark.asyncio
async def test_protected_endpoint_rejects_unauthenticated_request() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_seeded_admin_resolves_current_workspace() -> None:
    override_identity(ADMIN_SUBJECT)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["workspace"]["id"] == str(SARI_ARTA_ID)
    assert body["role"] == "admin"
    assert "memberships:manage" in body["permissions"]


@pytest.mark.asyncio
async def test_sales_role_cannot_list_memberships() -> None:
    override_identity(SALES_SUBJECT)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/memberships")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_client_selected_workspace_does_not_grant_access() -> None:
    override_identity(ADMIN_SUBJECT)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/me",
                headers={"X-Tenant-Id": str(uuid4())},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Workspace access denied."


@pytest.mark.asyncio
async def test_database_enforces_row_security_on_tenant_tables() -> None:
    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT c.relrowsecurity, c.relforcerowsecurity, p.policyname "
                "FROM pg_class c "
                "JOIN pg_policies p ON p.tablename = c.relname "
                "WHERE c.relname = 'organizations'"
            )
        )

    row = result.one()
    assert row.relrowsecurity is True
    assert row.relforcerowsecurity is True
    assert row.policyname == "tenant_isolation"


@pytest.mark.asyncio
async def test_m2_core_schema_is_present() -> None:
    expected = {
        "activities",
        "agent_configurations",
        "agent_runs",
        "audit_events",
        "contacts",
        "lead_assessments",
        "leads",
        "opportunities",
        "organizations",
        "tasks",
        "tenant_memberships",
        "tenants",
        "users",
    }
    async with session_factory() as session:
        names = set(
            (
                await session.scalars(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public'"
                    )
                )
            ).all()
        )

    assert expected <= names
