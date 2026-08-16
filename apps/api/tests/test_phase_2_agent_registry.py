from __future__ import annotations

import httpx
import pytest
from sqlalchemy import text

from sari_api.adapters.database import session_factory
from sari_api.api.dependencies import get_token_identity
from sari_api.domain.identity import TokenIdentity
from sari_api.domain.packages.models import SUPPORTED_LOCALES
from sari_api.domain.packages.registry import DOMAIN_PACKAGES, PACKAGES_BY_DOMAIN
from sari_api.main import app

ADMIN_SUBJECT = "30000000-0000-4000-8000-000000000001"
SALES_SUBJECT = "30000000-0000-4000-8000-000000000002"


def override_identity(subject: str) -> None:
    async def identity() -> TokenIdentity:
        return TokenIdentity(subject=subject, email=None)

    app.dependency_overrides[get_token_identity] = identity


def test_domain_manifests_are_valid_and_multilingual() -> None:
    assert set(PACKAGES_BY_DOMAIN) == {
        "commercial_kitchen",
        "laboratory_animal_facility",
    }
    for manifest in DOMAIN_PACKAGES:
        manifest.validate()
        assert manifest.supported_locales == SUPPORTED_LOCALES

    ivc = PACKAGES_BY_DOMAIN["laboratory_animal_facility"]
    assert ivc.agent_name.en == "IVC Facility Business Development Agent"
    assert len(ivc.business_objectives) >= 3
    assert len(ivc.qualification_fields) >= 10
    assert len(ivc.knowledge_categories) >= 5
    knowledge = next(
        item for item in ivc.required_capabilities if item.key == "approved_knowledge_retrieval"
    )
    assert knowledge.required is False
    assert knowledge.status == "planned"


@pytest.mark.asyncio
async def test_admin_can_browse_localized_registry() -> None:
    override_identity(ADMIN_SUBJECT)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            domains = await client.get("/api/v1/agent-registry/domains", params={"locale": "zh-CN"})
            agents = await client.get("/api/v1/agent-registry/agents", params={"locale": "id"})
            sari = await client.get(
                "/api/v1/agent-registry/agents/commercial_kitchen.lead_qualification"
            )
            ivc = await client.get(
                "/api/v1/agent-registry/agents/laboratory_animal_facility.ivc_business_development",
                params={"locale": "zh-CN"},
            )
    finally:
        app.dependency_overrides.clear()

    assert domains.status_code == 200, domains.text
    assert [row["domain_key"] for row in domains.json()] == [
        "commercial_kitchen",
        "laboratory_animal_facility",
    ]
    assert domains.json()[1]["name"] == "实验动物设施"

    assert agents.status_code == 200, agents.text
    assert len(agents.json()) == 3
    sari_summary = next(row for row in agents.json() if row["domain_key"] == "commercial_kitchen")
    ivc_summary = next(
        row for row in agents.json() if row["domain_key"] == "laboratory_animal_facility"
    )
    marketing_summary = next(
        row
        for row in agents.json()
        if row["agent_key"] == "commercial_kitchen.marketing_content"
    )
    assert sari_summary["activation_status"] == "active"
    assert ivc_summary["activation_status"] == "active"
    assert marketing_summary["activation_status"] == "active"

    assert sari.status_code == 200, sari.text
    assert sari.json()["versions"][0]["status"] == "active"
    assert sari.json()["versions"][0]["supported_locales"] == ["en", "zh-CN", "id"]

    assert ivc.status_code == 200, ivc.text
    assert ivc.json()["name"] == "IVC 设施商务拓展智能体"
    assert ivc.json()["versions"][0]["status"] == "active"
    capabilities = {row["key"]: row for row in ivc.json()["versions"][0]["capabilities"]}
    assert capabilities["approved_knowledge_retrieval"] == {
        "key": "approved_knowledge_retrieval",
        "name": "批准知识检索",
        "required": False,
        "status": "planned",
    }


@pytest.mark.asyncio
async def test_sales_role_cannot_access_agent_registry() -> None:
    override_identity(SALES_SUBJECT)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/agent-registry/agents")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_registry_tenant_tables_force_row_level_security() -> None:
    async with session_factory() as session:
        rows = (
            await session.execute(
                text(
                    "SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity, p.policyname "
                    "FROM pg_class c JOIN pg_policies p ON p.tablename = c.relname "
                    "WHERE c.relname IN "
                    "('agent_capability_bindings', 'tenant_agent_activations') "
                    "ORDER BY c.relname"
                )
            )
        ).all()

    assert [row.relname for row in rows] == [
        "agent_capability_bindings",
        "tenant_agent_activations",
    ]
    assert all(row.relrowsecurity and row.relforcerowsecurity for row in rows)
    assert all(row.policyname == "tenant_isolation" for row in rows)


@pytest.mark.asyncio
async def test_phase_1_qualification_runtime_key_is_unchanged() -> None:
    async with session_factory() as session:
        row = (
            await session.execute(
                text(
                    "SELECT agent_key, status, agent_id FROM agent_configurations "
                    "WHERE id = '50000000-0000-4000-8000-000000000001'"
                )
            )
        ).one()

    assert row.agent_key == "lead_qualification"
    assert row.status == "active"
    assert str(row.agent_id) == "61000000-0000-4000-8000-000000000001"
