from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from sari_api.adapters.database import session_factory
from sari_api.adapters.models import ContentReviewFeedback
from sari_api.api.dependencies import get_token_identity
from sari_api.domain.identity import TokenIdentity
from sari_api.domain.marketing_content_acceptance import load_acceptance_dataset
from sari_api.domain.marketing_content_evaluation import human_edit_distance
from sari_api.main import app
from sari_api.marketing_generation_eval import evaluate

ADMIN_SUBJECT = "30000000-0000-4000-8000-000000000001"
SALES_SUBJECT = "30000000-0000-4000-8000-000000000002"
TENANT_ID = UUID("10000000-0000-4000-8000-000000000001")


async def admin_identity() -> TokenIdentity:
    return TokenIdentity(subject=ADMIN_SUBJECT, email="admin@sari-arta.example")


async def sales_identity() -> TokenIdentity:
    return TokenIdentity(subject=SALES_SUBJECT, email="sales@sari-arta.example")


@pytest.mark.asyncio
async def test_business_dataset_executes_bilingually_against_versioned_mock_baseline() -> None:
    result = await evaluate(allow_paid_provider=False, max_cases=None)
    baseline_path = (
        Path(__file__).parents[1]
        / "src/sari_api/evaluation_data/marketing_generation_baseline.mock.v1.json"
    )
    baseline = json.loads(baseline_path.read_text())
    assert result["provider"] == "mock"
    assert result["case_count"] == 10
    assert result["metrics"] == baseline["metrics"]
    assert {item["content_type"] for item in result["cases"]} == {
        "website_article",
        "tiktok_script",
        "instagram_reel_script",
        "facebook_post",
        "email_draft",
    }
    pairs: dict[str, list[dict[str, object]]] = {}
    for item in result["cases"]:
        pairs.setdefault(str(item["bilingual_pair_id"]), []).append(item)
    assert len(pairs) == 5
    for pair in pairs.values():
        assert {item["language"] for item in pair} == {"en", "zh-CN"}
        scores = [float(item["quality"]["overall_score"]) for item in pair]  # type: ignore[index]
        assert max(scores) - min(scores) <= 10


def test_human_edit_distance_is_normalized_and_review_oriented() -> None:
    assert human_edit_distance("same", "same") == 0.0
    assert human_edit_distance("generated draft", "human approved revision") > 0.5
    assert human_edit_distance("", "") == 0.0


@pytest.mark.asyncio
async def test_fixed_business_acceptance_dataset_and_dashboard_are_bilingual() -> None:
    dataset = load_acceptance_dataset()
    assert dataset.dataset_version == "phase_3_2_business_acceptance_v1"
    assert len(dataset.cases) == 10
    assert {case.content_type for case in dataset.cases} == {
        "website_article",
        "tiktok_script",
        "instagram_reel_script",
        "facebook_post",
        "email_draft",
    }
    for content_type in {case.content_type for case in dataset.cases}:
        assert {case.language for case in dataset.cases if case.content_type == content_type} == {
            "en",
            "zh-CN",
        }

    app.dependency_overrides[get_token_identity] = admin_identity
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/content/acceptance")
            assert response.status_code == 200, response.text
            payload = response.json()
            assert payload["summary"]["total"] == 10
            assert payload["summary"]["brand_guideline_validation"] == "pending"
            assert payload["summary"]["openai_comparison_state"] == "not_run"
            assert payload["mock_preparation_allowed"] is True
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_structured_feedback_is_authorized_immutable_and_tenant_isolated() -> None:
    suffix = uuid4().hex[:10]
    app.dependency_overrides[get_token_identity] = sales_identity
    feedback_id: UUID | None = None
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            asset_response = await client.post(
                "/api/v1/content/assets",
                headers={"Idempotency-Key": f"eval-asset-{suffix}"},
                json={
                    "domain_key": "commercial_kitchen",
                    "title": f"Synthetic evaluation article {suffix}",
                    "content_type": "website_article",
                    "audience": "schools",
                    "language": "en",
                    "channel": "website",
                    "content_body": {
                        "content_type": "website_article",
                        "title": "Synthetic school kitchen planning",
                        "summary": "Synthetic public summary.",
                        "sections": [{"heading": "Planning", "body": "Synthetic body."}],
                        "call_to_action": "Request a consultation",
                        "references": [],
                    },
                    "plain_text": "Synthetic school kitchen planning and consultation.",
                    "claims": [],
                    "citations": [],
                },
            )
            assert asset_response.status_code == 201, asset_response.text
            asset = asset_response.json()
            version = asset["current_version"]
            payload = {
                "content_version_id": version["id"],
                "content_sha256": version["content_sha256"],
                "categories": ["useful", "weak_cta"],
                "note": "Synthetic human reviewer feedback.",
            }
            denied = await client.post(
                f"/api/v1/content/assets/{asset['id']}/feedback",
                headers={"Idempotency-Key": f"sales-feedback-{suffix}"},
                json=payload,
            )
            assert denied.status_code == 403

            app.dependency_overrides[get_token_identity] = admin_identity
            created = await client.post(
                f"/api/v1/content/assets/{asset['id']}/feedback",
                headers={"Idempotency-Key": f"admin-feedback-{suffix}"},
                json=payload,
            )
            assert created.status_code == 201, created.text
            feedback_id = UUID(created.json()["id"])
            assert created.json()["categories"] == ["useful", "weak_cta"]
            repeated = await client.post(
                f"/api/v1/content/assets/{asset['id']}/feedback",
                headers={"Idempotency-Key": f"admin-feedback-{suffix}"},
                json=payload,
            )
            assert repeated.status_code == 201
            assert repeated.json()["id"] == str(feedback_id)

            evaluation = await client.get(
                f"/api/v1/content/assets/{asset['id']}/evaluation"
            )
            assert evaluation.status_code == 200, evaluation.text
            assert evaluation.json()["feedback"][0]["id"] == str(feedback_id)
            assert evaluation.json()["quality_evaluation"] is None
            assert evaluation.json()["generated_version_number"] is None
            assert evaluation.json()["approved_human_version_number"] is None
            assert evaluation.json()["human_edit_distance"] is None

            cross_tenant = await client.get(
                f"/api/v1/content/assets/{asset['id']}/evaluation",
                headers={"X-Tenant-Id": str(uuid4())},
            )
            assert cross_tenant.status_code == 403

        async with session_factory() as session:
            policy = (
                await session.execute(
                    text(
                        "SELECT c.relrowsecurity, c.relforcerowsecurity, p.qual, p.with_check "
                        "FROM pg_class c JOIN pg_policies p ON p.tablename = c.relname "
                        "WHERE c.relname = 'content_review_feedback'"
                    )
                )
            ).one()
            assert policy.relrowsecurity and policy.relforcerowsecurity
            assert "app.tenant_id" in policy.qual
            assert "app.tenant_id" in policy.with_check
            other_tenant = uuid4()
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(other_tenant)},
            )
            assert await session.scalar(
                select(ContentReviewFeedback.id).where(
                    ContentReviewFeedback.id == feedback_id,
                    ContentReviewFeedback.tenant_id == other_tenant,
                )
            ) is None
        async with session_factory() as session:
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(TENANT_ID)},
            )
            with pytest.raises(DBAPIError, match="governed content history is immutable"):
                await session.execute(
                    text(
                        "UPDATE content_review_feedback SET note = 'forbidden mutation' "
                        "WHERE id = :feedback_id"
                    ),
                    {"feedback_id": str(feedback_id)},
                )
    finally:
        app.dependency_overrides.clear()
