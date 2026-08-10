from __future__ import annotations

from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import func, select, text

from sari_api.adapters.agent_playground_executor import AgentPlaygroundRunExecutor
from sari_api.adapters.agent_playground_provider import MockAgentPlaygroundProvider
from sari_api.adapters.agent_queue import get_agent_queue
from sari_api.adapters.database import session_factory
from sari_api.adapters.models import Lead
from sari_api.api.dependencies import get_token_identity
from sari_api.domain.agent_playground import PlaygroundQualificationRequest
from sari_api.domain.identity import TokenIdentity
from sari_api.main import app
from sari_api.worker import resolve_workflow_type

ADMIN_SUBJECT = "30000000-0000-4000-8000-000000000001"
TENANT_ID = UUID("10000000-0000-4000-8000-000000000001")


async def admin_identity() -> TokenIdentity:
    return TokenIdentity(subject=ADMIN_SUBJECT, email="admin@sari-arta.example")


class RecordingQueue:
    def __init__(self) -> None:
        self.messages: list[tuple[UUID, UUID]] = []

    async def enqueue(self, run_id: UUID, tenant_id: UUID) -> None:
        self.messages.append((run_id, tenant_id))


@pytest.mark.asyncio
async def test_playground_mock_outputs_are_localized_and_structured() -> None:
    provider = MockAgentPlaygroundProvider()
    commercial = {
        "project_type": "School central kitchen",
        "location": "Jakarta, Indonesia",
        "capacity": "2,000 meals/day",
        "budget": "USD 500,000 indicative",
        "timeline": "Target opening Q3 2027",
    }
    ivc = {
        "organization": "Synthetic Nusantara University",
        "facility_type": "New animal facility",
        "species_research": "Mouse and rat biomedical research",
        "capacity": "2,400 mouse cages and 240 rat cages",
        "technical_requirements": (
            "Housing, procedure, quarantine, wash, sterilization, HVAC and monitoring scope"
        ),
        "timeline": "Design freeze Q1 2027 and operation Q1 2028",
    }

    outputs = []
    for locale in ("en", "zh-CN", "id"):
        outputs.append(
            await provider.qualify(
                PlaygroundQualificationRequest(
                    domain="commercial_kitchen",
                    response_locale=locale,
                    commercial_kitchen=commercial,
                )
            )
        )
        outputs.append(
            await provider.qualify(
                PlaygroundQualificationRequest(
                    domain="laboratory_animal_facility",
                    response_locale=locale,
                    laboratory_animal_facility=ivc,
                )
            )
        )

    assert all(item.qualification_score == 100 for item in outputs)
    assert all(item.qualification_level == "A" for item in outputs)
    assert all(item.demo_only and item.human_review_required for item in outputs)
    assert len({item.business_summary for item in outputs}) == 6
    assert all(item.risks for item in outputs)
    assert all(item.recommended_next_actions for item in outputs)


@pytest.mark.asyncio
async def test_playground_runs_both_agents_without_creating_crm_leads() -> None:
    queue = RecordingQueue()
    app.dependency_overrides[get_token_identity] = admin_identity
    app.dependency_overrides[get_agent_queue] = lambda: queue
    try:
        async with session_factory() as session:
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(TENANT_ID)},
            )
            leads_before = await session.scalar(
                select(func.count()).select_from(Lead).where(Lead.tenant_id == TENANT_ID)
            )

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            requests = [
                {
                    "domain": "commercial_kitchen",
                    "response_locale": "zh-CN",
                    "commercial_kitchen": {
                        "project_type": "学校中央厨房",
                        "location": "印度尼西亚雅加达",
                        "capacity": "每日 2,000 份餐",
                        "budget": None,
                        "timeline": "2027 年第三季度",
                    },
                },
                {
                    "domain": "laboratory_animal_facility",
                    "response_locale": "id",
                    "laboratory_animal_facility": {
                        "organization": "Synthetic University",
                        "facility_type": "Fasilitas hewan baru",
                        "species_research": "Riset tikus",
                        "capacity": "1.000 kandang",
                        "technical_requirements": None,
                        "timeline": "Operasional Q1 2028",
                    },
                },
            ]
            run_ids: list[UUID] = []
            for payload in requests:
                response = await client.post(
                    "/api/v1/agent-playground/runs",
                    headers={"Idempotency-Key": f"playground-{uuid4()}"},
                    json=payload,
                )
                assert response.status_code == 202, response.text
                run_ids.append(UUID(response.json()["run_id"]))

            assert len(queue.messages) == 2
            executor = AgentPlaygroundRunExecutor(MockAgentPlaygroundProvider())
            for run_id in run_ids:
                assert (
                    await resolve_workflow_type(run_id, TENANT_ID)
                    == "agent_playground_qualification"
                )
                await executor.execute(run_id, TENANT_ID)
                result = await client.get(f"/api/v1/agent-runs/{run_id}")
                assert result.status_code == 200, result.text
                assert result.json()["status"] == "succeeded"
                assert result.json()["result"]["demo_only"] is True
                assert "chain_of_thought" not in result.json()["result"]

        async with session_factory() as session:
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(TENANT_ID)},
            )
            leads_after = await session.scalar(
                select(func.count()).select_from(Lead).where(Lead.tenant_id == TENANT_ID)
            )
        assert leads_after == leads_before
    finally:
        app.dependency_overrides.clear()
