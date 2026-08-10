from __future__ import annotations

from uuid import UUID, uuid4

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy import text

from sari_api.adapters.agent_queue import get_agent_queue
from sari_api.adapters.database import session_factory
from sari_api.adapters.ivc_qualification_executor import IvcQualificationRunExecutor
from sari_api.adapters.ivc_qualification_provider import (
    IVC_QUALIFICATION_INSTRUCTIONS,
    MockIvcQualificationProvider,
)
from sari_api.api.dependencies import get_token_identity
from sari_api.domain.identity import TokenIdentity
from sari_api.domain.ivc_demo_cases import IVC_DEMO_CASES_BY_KEY
from sari_api.domain.ivc_qualification import IvcQualificationOutput
from sari_api.main import app
from sari_api.worker import resolve_workflow_type

ADMIN_SUBJECT = "30000000-0000-4000-8000-000000000001"
SARI_ARTA_ID = UUID("10000000-0000-4000-8000-000000000001")


async def admin_identity() -> TokenIdentity:
    return TokenIdentity(subject=ADMIN_SUBJECT, email="admin@sari-arta.example")


class RecordingQueue:
    def __init__(self) -> None:
        self.messages: list[tuple[UUID, UUID]] = []

    async def enqueue(self, run_id: UUID, tenant_id: UUID) -> None:
        self.messages.append((run_id, tenant_id))


def test_ivc_output_schema_rejects_mismatched_level() -> None:
    with pytest.raises(ValidationError):
        IvcQualificationOutput(
            response_locale="en",
            score=90,
            qualification_level="C",
            business_summary="Synthetic IVC project.",
            key_qualification_factors=[
                {"category": category, "status": "partial", "summary": "Review evidence."}
                for category in (
                    "customer",
                    "project",
                    "technical",
                    "budget",
                    "timeline",
                    "stakeholders",
                )
            ],
            missing_information=[],
            risk_flags=[],
            recommended_next_actions=["Review manually."],
            confidence=0.5,
            expert_review_required=True,
        )


@pytest.mark.asyncio
async def test_three_synthetic_cases_and_locales_are_deterministic() -> None:
    provider = MockIvcQualificationProvider()
    expected = {
        "university_animal_facility": (100, "A"),
        "pharmaceutical_research_facility": (97, "A"),
        "laboratory_upgrade": (44, "C"),
    }

    for case_key, (score, level) in expected.items():
        case = IVC_DEMO_CASES_BY_KEY[case_key]
        outputs = [await provider.qualify(case.input, locale) for locale in ("en", "zh-CN", "id")]
        assert [item.response_locale for item in outputs] == ["en", "zh-CN", "id"]
        assert all(item.score == score for item in outputs)
        assert all(item.qualification_level == level for item in outputs)
        assert all(item.expert_review_required for item in outputs)
        assert len({item.business_summary for item in outputs}) == 3
        assert all(len(item.key_qualification_factors) == 6 for item in outputs)

    upgrade = await provider.qualify(IVC_DEMO_CASES_BY_KEY["laboratory_upgrade"].input, "zh-CN")
    assert any("预算" in item for item in upgrade.missing_information)
    assert any("专家" in item for item in upgrade.risk_flags)


def test_ivc_prompt_has_safety_and_localization_contract() -> None:
    assert "Never invent" in IVC_QUALIFICATION_INSTRUCTIONS
    assert "expert_review_required to true" in IVC_QUALIFICATION_INSTRUCTIONS
    assert "en, zh-CN, or id" in IVC_QUALIFICATION_INSTRUCTIONS
    assert "Never reveal chain-of-thought" in IVC_QUALIFICATION_INSTRUCTIONS
    assert "price, or delivery commitment" in IVC_QUALIFICATION_INSTRUCTIONS


@pytest.mark.asyncio
async def test_ivc_demo_run_is_idempotent_localized_and_reviewable() -> None:
    queue = RecordingQueue()
    app.dependency_overrides[get_token_identity] = admin_identity
    app.dependency_overrides[get_agent_queue] = lambda: queue
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            cases = await client.get("/api/v1/ivc/demo-cases", params={"locale": "zh-CN"})
            assert cases.status_code == 200, cases.text
            assert cases.json()[0]["name"] == "大学实验动物设施"
            assert len(cases.json()) == 3

            key = f"ivc-demo-{uuid4()}"
            headers = {"Idempotency-Key": key, "X-Correlation-ID": "ivc-demo-0001"}
            payload = {
                "demo_case_key": "pharmaceutical_research_facility",
                "response_locale": "id",
            }
            first = await client.post(
                "/api/v1/ivc/qualification-runs",
                headers=headers,
                json=payload,
            )
            second = await client.post(
                "/api/v1/ivc/qualification-runs",
                headers=headers,
                json=payload,
            )
            assert first.status_code == 202, first.text
            assert second.json() == first.json()
            assert len(queue.messages) == 1

            run_id, tenant_id = queue.messages[0]
            assert tenant_id == SARI_ARTA_ID
            assert await resolve_workflow_type(run_id, tenant_id) == "ivc_facility_qualification"
            await IvcQualificationRunExecutor(MockIvcQualificationProvider()).execute(
                run_id,
                tenant_id,
            )

            run = await client.get(f"/api/v1/agent-runs/{run_id}")
            assert run.status_code == 200, run.text
            result = run.json()["result"]
            assert run.json()["workflow_type"] == "ivc_facility_qualification"
            assert run.json()["provider_type"] == "mock"
            assert run.json()["correlation_id"] == "ivc-demo-0001"
            assert result["response_locale"] == "id"
            assert result["score"] == 97
            assert result["qualification_level"] == "A"
            assert result["expert_review_required"] is True
            assert "sedang mengevaluasi" in result["business_summary"]
            assert "chain_of_thought" not in result

            assessment_id = result["assessment_id"]
            assessment = await client.get(f"/api/v1/ivc/qualification-assessments/{assessment_id}")
            assert assessment.status_code == 200, assessment.text
            assert assessment.json()["review_status"] == "pending"

            review = await client.post(
                f"/api/v1/ivc/qualification-assessments/{assessment_id}/reviews",
                json={"decision": "approved"},
            )
            assert review.status_code == 200, review.text
            assert review.json()["review_status"] == "approved"

            duplicate_review = await client.post(
                f"/api/v1/ivc/qualification-assessments/{assessment_id}/reviews",
                json={"decision": "rejected"},
            )
            assert duplicate_review.status_code == 409
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ivc_registry_activation_and_assessment_rls() -> None:
    async with session_factory() as session:
        registry = (
            await session.execute(
                text(
                    "SELECT d.status AS domain_status, a.status AS agent_status, "
                    "c.status AS config_status, c.runtime_config, t.status AS activation_status "
                    "FROM domain_packages d JOIN agents a ON a.domain_package_id = d.id "
                    "JOIN agent_configurations c ON c.agent_id = a.id "
                    "JOIN tenant_agent_activations t ON t.agent_configuration_id = c.id "
                    "WHERE d.domain_key = 'laboratory_animal_facility'"
                )
            )
        ).one()
        rls = (
            await session.execute(
                text(
                    "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
                    "WHERE relname = 'ivc_qualification_assessments'"
                )
            )
        ).one()

    assert registry.domain_status == "available"
    assert registry.agent_status == "available"
    assert registry.config_status == "active"
    assert registry.activation_status == "active"
    assert registry.runtime_config == {
        "execution_enabled": True,
        "human_review_required": True,
        "knowledge_enabled": False,
    }
    assert rls.relrowsecurity and rls.relforcerowsecurity
