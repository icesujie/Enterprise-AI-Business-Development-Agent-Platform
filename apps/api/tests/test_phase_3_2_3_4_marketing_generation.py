from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import text

from sari_api.adapters.agent_queue import get_agent_queue
from sari_api.adapters.database import session_factory
from sari_api.adapters.knowledge_embedding import DeterministicKnowledgeEmbeddingProvider
from sari_api.adapters.marketing_content_generation_executor import (
    MarketingContentGenerationExecutor,
)
from sari_api.adapters.marketing_content_provider import MockMarketingContentProvider
from sari_api.adapters.models import ContentAsset, ContentVersion
from sari_api.api.dependencies import get_token_identity
from sari_api.core.config import get_settings
from sari_api.domain.identity import TokenIdentity
from sari_api.domain.marketing_content_evaluation import EvaluationOutcome, summarize
from sari_api.domain.marketing_content_generation import (
    MarketingEvidence,
    contains_forbidden_request,
    plain_text,
    validate_draft,
)
from sari_api.main import app
from test_phase_3_2_3_3_marketing_knowledge_policy import (
    ADMIN_SUBJECT,
    TENANT_ID,
    cleanup_collections,
    seed_policy_fixture,
)


async def admin_identity() -> TokenIdentity:
    return TokenIdentity(subject=ADMIN_SUBJECT, email="admin@sari-arta.example")


async def sales_identity() -> TokenIdentity:
    return TokenIdentity(
        subject="30000000-0000-4000-8000-000000000002",
        email="sales@sari-arta.example",
    )


class CapturingQueue:
    def __init__(self) -> None:
        self.messages: list[tuple[UUID, UUID, str | None]] = []

    async def enqueue(
        self,
        run_id: UUID,
        tenant_id: UUID,
        *,
        correlation_id: str | None = None,
        delay_seconds: int = 0,
    ) -> None:
        assert delay_seconds == 0
        self.messages.append((run_id, tenant_id, correlation_id))


@pytest.mark.asyncio
async def test_mock_provider_returns_all_five_valid_grounded_structures() -> None:
    provider = MockMarketingContentProvider()
    evidence = [_evidence()]
    content_types = (
        "website_article",
        "tiktok_script",
        "instagram_reel_script",
        "facebook_post",
        "email_draft",
    )
    for content_type in content_types:
        draft = await provider.generate(_request(content_type), evidence)
        validated = validate_draft(draft, content_type, evidence)
        assert validated.references[0].chunk_id == evidence[0].chunk_id
        assert "Synthetic approved public engineering capability" in plain_text(validated)


@pytest.mark.asyncio
async def test_mock_generation_is_bilingual_and_uses_same_core_evidence() -> None:
    provider = MockMarketingContentProvider()
    evidence = [_evidence()]
    english = await provider.generate(_request("website_article", "en"), evidence)
    chinese = await provider.generate(_request("website_article", "zh-CN"), evidence)
    assert english.references == chinese.references
    assert "Approved evidence" in plain_text(english)
    assert "经批准的依据" in plain_text(chinese)


def test_forbidden_requests_are_detected_before_generation() -> None:
    assert contains_forbidden_request("Provide private pricing and discount")
    assert contains_forbidden_request("请提供供应商价格")
    assert not contains_forbidden_request("Explain commercial kitchen design services")


def test_invalid_or_invented_references_are_rejected() -> None:
    raw = {
        "content_type": "facebook_post",
        "headline": "Synthetic",
        "body": "Unsupported named customer claim",
        "call_to_action": "Consult",
        "hashtags": [],
        "references": [{"chunk_id": str(uuid4())}],
    }
    with pytest.raises(ValueError, match="retrieved evidence"):
        validate_draft(raw, "facebook_post", [_evidence()])


def test_unsupported_price_specification_and_certification_claims_are_rejected() -> None:
    for body in ("Only USD 5000.", "Capacity is 200 units.", "ISO 9001 certified."):
        raw = {
            "content_type": "facebook_post",
            "headline": "Synthetic",
            "body": body,
            "call_to_action": "Consult",
            "hashtags": [],
            "references": [{"chunk_id": str(_evidence().chunk_id)}],
        }
        item = _evidence()
        raw["references"] = [{"chunk_id": str(item.chunk_id)}]
        with pytest.raises(ValueError, match="protected claim"):
            validate_draft(raw, "facebook_post", [item])


def test_repeatable_evaluation_fixture_and_metrics() -> None:
    path = Path(__file__).parent / "fixtures" / "marketing_content_evaluation.v1.json"
    fixture = json.loads(path.read_text())
    assert len(fixture["cases"]) == 8
    metrics = summarize(
        [
            EvaluationOutcome(
                grounding_correct=True,
                citations_complete=True,
                unsupported_claim=False,
                insufficient_handled=True,
                structure_valid=True,
                bilingual_consistent=True,
            )
            for _ in fixture["cases"]
        ]
    )
    assert metrics == {
        "grounding_accuracy": 1.0,
        "citation_completeness": 1.0,
        "unsupported_claim_rate": 0.0,
        "insufficient_evidence_accuracy": 1.0,
        "structural_validity": 1.0,
        "bilingual_consistency": 1.0,
    }


@pytest.mark.asyncio
async def test_end_to_end_mock_generation_persists_exact_governed_version() -> None:
    collections = await seed_policy_fixture()
    queue = CapturingQueue()
    request_id: UUID | None = None
    run_id: UUID | None = None
    app.dependency_overrides[get_token_identity] = sales_identity
    app.dependency_overrides[get_agent_queue] = lambda: queue
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/api/v1/content/requests",
                headers={"Idempotency-Key": f"marketing-request-{uuid4()}"},
                json={
                    "domain_key": "commercial_kitchen",
                    "content_type": "website_article",
                    "audience": "schools",
                    "language": "en",
                    "channel": "website",
                    "business_objective": "Explain synthetic public engineering capability",
                    "topic": "Synthetic public marketing boundary consultation",
                    "call_to_action": "Request a consultation",
                },
            )
            assert created.status_code == 201, created.text
            request_id = UUID(created.json()["id"])
            started = await client.post(
                f"/api/v1/content/requests/{request_id}/generate",
                headers={"Idempotency-Key": f"marketing-generate-{uuid4()}"},
            )
            assert started.status_code == 202, started.text
            run_id = UUID(started.json()["run_id"])
            assert queue.messages[0][0] == run_id

            executor = MarketingContentGenerationExecutor(
                DeterministicKnowledgeEmbeddingProvider(1536),
                MockMarketingContentProvider(),
                get_settings(),
            )
            assert await executor.execute(run_id, TENANT_ID) is None
            completed = await client.get(f"/api/v1/content/generation-runs/{run_id}")
            assert completed.status_code == 200, completed.text
            payload = completed.json()
            assert payload["status"] == "succeeded"
            assert payload["result"]["outcome"] == "generated"
            assert payload["result"]["citations"][0]["document_name"] == (
                "Allowed Public Company Profile"
            )
            assert payload["result"]["asset_id"]
            evaluation = await client.get(
                f"/api/v1/content/assets/{payload['result']['asset_id']}/evaluation"
            )
            assert evaluation.status_code == 200, evaluation.text
            assert evaluation.json()["quality_evaluation"]["factual_grounding"] == 100
            assert evaluation.json()["quality_evaluation"]["overall_score"] > 80
            assert evaluation.json()["generated_version_number"] == 1
            assert evaluation.json()["approved_human_version_number"] is None
            assert evaluation.json()["human_edit_distance"] is None

            successor = await client.post(
                f"/api/v1/content/assets/{payload['result']['asset_id']}/versions",
                headers={
                    "If-Match": '"1"',
                    "Idempotency-Key": f"marketing-human-edit-{uuid4()}",
                },
                json={
                    "content_body": {"body": "Human-approved synthetic revision."},
                    "plain_text": "Human-approved synthetic revision.",
                    "claims": [],
                    "citations": payload["result"]["citations"],
                },
            )
            assert successor.status_code == 201, successor.text
            human_version = successor.json()["current_version"]
            submitted = await client.post(
                f"/api/v1/content/assets/{payload['result']['asset_id']}/submit-review",
                headers={
                    "If-Match": '"2"',
                    "Idempotency-Key": f"marketing-human-submit-{uuid4()}",
                },
                json={
                    "content_version_id": human_version["id"],
                    "content_sha256": human_version["content_sha256"],
                },
            )
            assert submitted.status_code == 200, submitted.text
            app.dependency_overrides[get_token_identity] = admin_identity
            approved = await client.post(
                f"/api/v1/content/assets/{payload['result']['asset_id']}/decisions",
                headers={
                    "If-Match": '"3"',
                    "Idempotency-Key": f"marketing-human-approve-{uuid4()}",
                },
                json={
                    "content_version_id": human_version["id"],
                    "content_sha256": human_version["content_sha256"],
                    "decision": "approved",
                },
            )
            assert approved.status_code == 200, approved.text
            final_evaluation = await client.get(
                f"/api/v1/content/assets/{payload['result']['asset_id']}/evaluation"
            )
            assert final_evaluation.status_code == 200, final_evaluation.text
            assert final_evaluation.json()["generated_version_number"] == 1
            assert final_evaluation.json()["approved_human_version_number"] == 2
            assert final_evaluation.json()["human_edit_distance"] > 0

            async with session_factory() as session:
                await session.execute(
                    text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                    {"tenant_id": str(TENANT_ID)},
                )
                asset = await session.get(ContentAsset, UUID(payload["result"]["asset_id"]))
                version = await session.get(ContentVersion, UUID(payload["result"]["version_id"]))
                assert asset is not None and asset.status == "approved"
                assert version is not None and version.origin == "ai_generated"
                assert asset.current_version_id == UUID(human_version["id"])
                assert asset.approved_version_id == UUID(human_version["id"])
            assert version.citations[0]["chunk_id"]
            assert (
                payload["result"]["content"]["content_type"]
                == "website_article"
            )
    finally:
        app.dependency_overrides.clear()
        await cleanup_collections(collections)


def _request(content_type: str, language: str = "en") -> dict[str, object]:
    return {
        "content_type": content_type,
        "language": language,
        "topic": "Synthetic kitchen engineering",
        "call_to_action": "Request a consultation",
    }


def _evidence() -> MarketingEvidence:
    return MarketingEvidence(
        document_id=uuid4(),
        document_name="Synthetic Public Company Profile",
        document_version_id=uuid4(),
        document_version=1,
        chunk_id=uuid4(),
        page_number=1,
        section="Capabilities",
        similarity_score=0.91,
        content="Synthetic approved public engineering capability.",
    )
