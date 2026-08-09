from __future__ import annotations

from uuid import UUID, uuid4

import httpx
import pytest
from pydantic import ValidationError

from sari_api.adapters.agent_queue import get_agent_queue
from sari_api.adapters.qualification_executor import QualificationRunExecutor
from sari_api.adapters.qualification_provider import (
    AgentsSdkQualificationProvider,
    MockQualificationProvider,
    build_qualification_provider,
)
from sari_api.api.dependencies import get_token_identity
from sari_api.core.config import Settings
from sari_api.domain.identity import TokenIdentity
from sari_api.domain.qualification import QualificationOutput
from sari_api.main import app

ADMIN_SUBJECT = "30000000-0000-4000-8000-000000000001"
SARI_ARTA_ID = UUID("10000000-0000-4000-8000-000000000001")


async def admin_identity() -> TokenIdentity:
    return TokenIdentity(subject=ADMIN_SUBJECT, email="admin@sari-arta.example")


class RecordingQueue:
    def __init__(self) -> None:
        self.messages: list[tuple[UUID, UUID]] = []

    async def enqueue(self, run_id: UUID, tenant_id: UUID) -> None:
        self.messages.append((run_id, tenant_id))


@pytest.mark.parametrize(
    ("score", "tier"),
    [(90, "hot"), (60, "warm"), (20, "cold")],
)
def test_qualification_schema_accepts_representative_tiers(
    score: float,
    tier: str,
) -> None:
    output = QualificationOutput(
        score=score,
        tier=tier,  # type: ignore[arg-type]
        need_summary="Synthetic commercial-kitchen project.",
        budget_status="unknown",
        authority_status="unknown",
        need_status="confirmed",
        timeline_status="partial",
        missing_information=["Budget", "Decision maker"],
        recommended_action="Complete a discovery call.",
        confidence=0.6,
    )
    assert output.tier == tier


def test_qualification_schema_rejects_inconsistent_tier() -> None:
    with pytest.raises(ValidationError):
        QualificationOutput(
            score=90,
            tier="cold",
            need_summary="Synthetic project.",
            budget_status="unknown",
            authority_status="unknown",
            need_status="confirmed",
            timeline_status="partial",
            missing_information=[],
            recommended_action="Review manually.",
            confidence=0.5,
        )


@pytest.mark.asyncio
async def test_mock_provider_returns_repeatable_business_output() -> None:
    snapshot = {
        "lead": {
            "project_type": "School central kitchen",
            "expected_capacity": "2,000 meals/day",
            "inquiry_summary": "A new school campus requires a production kitchen.",
            "target_timeline": "Opening in Q3 2027",
            "estimated_value": "250000",
            "currency": "USD",
            "project_country_code": "ID",
            "project_city": "Surabaya",
            "requirements": {"decision_maker": "School board"},
        },
        "organization": {"name": "Synthetic Education Group", "industry": "Education"},
        "contact": {"name": "Demo Contact", "job_title": "Project Director"},
    }
    provider = MockQualificationProvider()

    first = await provider.qualify(snapshot)
    second = await provider.qualify(snapshot)

    assert first == second
    assert first.score == 100
    assert first.qualification_level() == "A"
    assert first.need_summary == (
        "Synthetic Education Group in the Education sector submitted an inquiry for a School "
        "central kitchen with a stated size or capacity of 2,000 meals/day in Surabaya."
    )
    assert first.key_qualification_factors()[0] == {
        "key": "budget",
        "label": "Budget",
        "status": "confirmed",
    }


def test_provider_factory_uses_mock_unless_real_ai_is_enabled() -> None:
    mock_provider = build_qualification_provider(Settings(ai_enabled=False))
    real_provider = build_qualification_provider(
        Settings(ai_enabled=True, openai_api_key="test-key")
    )

    assert isinstance(mock_provider, MockQualificationProvider)
    assert isinstance(real_provider, AgentsSdkQualificationProvider)


@pytest.mark.asyncio
async def test_tasks_notes_and_automatic_activity_history() -> None:
    app.dependency_overrides[get_token_identity] = admin_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            lead = await client.post(
                "/api/v1/leads",
                json={
                    "source_channel": "manual",
                    "inquiry_summary": "Synthetic resort kitchen project in Bali.",
                    "project_type": "Resort kitchen",
                    "priority": "high",
                },
            )
            assert lead.status_code == 201, lead.text
            lead_id = lead.json()["id"]

            note = await client.post(
                f"/api/v1/leads/{lead_id}/activities",
                json={
                    "subject": "Discovery call",
                    "description": "Customer confirmed a target opening quarter.",
                },
            )
            assert note.status_code == 201, note.text
            assert note.json()["activity_type"] == "manual_note"

            task = await client.post(
                f"/api/v1/leads/{lead_id}/tasks",
                json={
                    "title": "Request floor plan",
                    "description": "Ask for a synthetic project floor plan.",
                    "priority": "urgent",
                    "due_at": "2026-08-20T09:00:00Z",
                },
            )
            assert task.status_code == 201, task.text
            task_body = task.json()

            completed = await client.patch(
                f"/api/v1/tasks/{task_body['id']}",
                headers={"If-Match": '"1"'},
                json={"status": "completed"},
            )
            assert completed.status_code == 200, completed.text
            assert completed.json()["completed_at"] is not None
            assert completed.json()["version"] == 2

            stale = await client.patch(
                f"/api/v1/tasks/{task_body['id']}",
                headers={"If-Match": '"1"'},
                json={"status": "open"},
            )
            assert stale.status_code == 409

            updated_lead = await client.patch(
                f"/api/v1/leads/{lead_id}",
                headers={"If-Match": '"1"'},
                json={"status": "qualifying", "priority": "urgent"},
            )
            assert updated_lead.status_code == 200, updated_lead.text

            activities = await client.get(f"/api/v1/leads/{lead_id}/activities")
            assert activities.status_code == 200
            activity_types = {item["activity_type"] for item in activities.json()}
            assert {
                "lead_created",
                "manual_note",
                "task_created",
                "task_updated",
                "lead_updated",
            } <= activity_types
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_qualification_run_is_idempotent_and_requires_human_review() -> None:
    queue = RecordingQueue()
    app.dependency_overrides[get_token_identity] = admin_identity
    app.dependency_overrides[get_agent_queue] = lambda: queue
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            lead = await client.post(
                "/api/v1/leads",
                json={
                    "source_channel": "manual",
                    "inquiry_summary": "Hotel kitchen for 1,500 meals per day in Jakarta.",
                    "project_type": "Hotel central kitchen",
                    "expected_capacity": "1,500 meals/day",
                    "target_timeline": "Opening in Q1 2027",
                    "priority": "high",
                },
            )
            assert lead.status_code == 201, lead.text
            lead_body = lead.json()
            key = f"qualification-{uuid4()}"
            headers = {"Idempotency-Key": key}
            payload = {
                "rubric_key": "commercial_kitchen_project_v1",
                "language": "en",
            }
            first = await client.post(
                f"/api/v1/leads/{lead_body['id']}/qualification-runs",
                headers=headers,
                json=payload,
            )
            second = await client.post(
                f"/api/v1/leads/{lead_body['id']}/qualification-runs",
                headers=headers,
                json=payload,
            )
            assert first.status_code == 202, first.text
            assert second.status_code == 202
            assert second.json() == first.json()
            assert len(queue.messages) == 1

            run_id, tenant_id = queue.messages[0]
            assert tenant_id == SARI_ARTA_ID
            await QualificationRunExecutor(MockQualificationProvider()).execute(
                run_id,
                tenant_id,
            )

            run = await client.get(f"/api/v1/agent-runs/{run_id}")
            assert run.status_code == 200, run.text
            assert run.json()["status"] == "succeeded"
            assert run.json()["provider_type"] == "mock"
            assert run.json()["result"]["tier"] == "warm"
            assert run.json()["result"]["qualification_level"] == "B"
            assert run.json()["result"]["business_summary"] == (
                "An unassigned company submitted an inquiry for a Hotel central kitchen with "
                "a stated size or capacity of 1,500 meals/day."
            )
            assert len(run.json()["result"]["key_qualification_factors"]) == 4

            assessments = await client.get(
                f"/api/v1/leads/{lead_body['id']}/qualification-assessments"
            )
            assert assessments.status_code == 200, assessments.text
            assessment = assessments.json()[0]
            assert assessment["review_status"] == "pending"
            assert assessment["qualification_level"] == "B"
            assert assessment["business_summary"] == assessment["need_summary"]
            assert len(assessment["key_qualification_factors"]) == 4

            unchanged_lead = await client.get(f"/api/v1/leads/{lead_body['id']}")
            assert unchanged_lead.json()["qualification_score"] is None
            assert unchanged_lead.json()["status"] == "new"

            approved = await client.post(
                f"/api/v1/lead-assessments/{assessment['id']}/reviews",
                json={"decision": "approved"},
            )
            assert approved.status_code == 200, approved.text
            assert approved.json()["review_status"] == "approved"

            reviewed_lead = await client.get(f"/api/v1/leads/{lead_body['id']}")
            assert reviewed_lead.json()["qualification_score"] == "60.00"
            assert reviewed_lead.json()["status"] == "new"

            repeated_review = await client.post(
                f"/api/v1/lead-assessments/{assessment['id']}/reviews",
                json={"decision": "rejected"},
            )
            assert repeated_review.status_code == 409
    finally:
        app.dependency_overrides.clear()
