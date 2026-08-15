from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import select, text

from sari_api.adapters.agent_queue import get_agent_queue
from sari_api.adapters.database import session_factory
from sari_api.adapters.knowledge_assistant_executor import KnowledgeAssistantRunExecutor
from sari_api.adapters.knowledge_assistant_provider import MockKnowledgeAssistantProvider
from sari_api.adapters.knowledge_embedding import DeterministicKnowledgeEmbeddingProvider
from sari_api.adapters.models import AgentRun
from sari_api.api.dependencies import get_token_identity
from sari_api.core.config import get_settings
from sari_api.domain.identity import TokenIdentity
from sari_api.domain.knowledge_assistant import (
    InvalidKnowledgeAssistantOutputError,
    KnowledgeAssistantDraft,
    KnowledgeAssistantEvidence,
    detect_evidence_conflicts,
    validate_knowledge_assistant_draft,
)
from sari_api.domain.knowledge_assistant_evaluation import (
    KnowledgeAssistantEvaluationCase,
    KnowledgeAssistantEvaluationObservation,
    evaluate_knowledge_assistant,
)
from sari_api.main import app
from test_phase_2_6_1_knowledge_retrieval import (
    ADMIN_SUBJECT,
    IVC_AGENT_ID,
    SARI_AGENT_ID,
    TENANT_ID,
    cleanup_collection,
    seed_retrieval_fixture,
)

FIXTURE = Path(__file__).parent / "fixtures" / "knowledge_assistant_evaluation.v1.json"


async def admin_identity() -> TokenIdentity:
    return TokenIdentity(subject=ADMIN_SUBJECT, email="admin@sari-arta.example")


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


def evidence(*, claims: dict[str, object] | None = None) -> KnowledgeAssistantEvidence:
    return KnowledgeAssistantEvidence(
        document_id=uuid4(),
        document_name="Synthetic approved guide",
        document_version_id=uuid4(),
        document_version=1,
        page_number=2,
        section="Design",
        chunk_id=uuid4(),
        source_metadata={"document_metadata": {"claims": claims or {}}},
        similarity_score=0.82,
        content="Synthetic evidence content.",
        content_sha256="a" * 64,
    )


def test_citation_validation_rejects_unretrieved_and_incomplete_citations() -> None:
    item = evidence()
    with pytest.raises(InvalidKnowledgeAssistantOutputError):
        validate_knowledge_assistant_draft(
            KnowledgeAssistantDraft(
                language="en",
                answer="Unsupported citation [1]",
                cited_chunk_ids=[uuid4()],
            ),
            "en",
            [item],
        )
    with pytest.raises(InvalidKnowledgeAssistantOutputError):
        second = evidence()
        validate_knowledge_assistant_draft(
            KnowledgeAssistantDraft(
                language="en",
                answer="Only the first citation appears [1]",
                cited_chunk_ids=[item.chunk_id, second.chunk_id],
            ),
            "en",
            [item, second],
        )


def test_conflicting_enterprise_claims_require_human_review() -> None:
    first = evidence(claims={"warranty_months": 12})
    second = evidence(claims={"warranty_months": 24})
    assert detect_evidence_conflicts([first, second]) == ["warranty_months"]


def test_assistant_regression_baseline_covers_required_metrics() -> None:
    baseline = json.loads(FIXTURE.read_text())
    cases = [KnowledgeAssistantEvaluationCase.model_validate(item) for item in baseline["cases"]]
    observations = [
        KnowledgeAssistantEvaluationObservation.model_validate(item)
        for item in baseline["observations"]
    ]
    assert evaluate_knowledge_assistant(cases, observations) == baseline["baseline_results"]


@pytest.mark.asyncio
async def test_read_only_assistant_runs_with_governed_citations_and_redacts_question() -> None:
    collection_id = await seed_retrieval_fixture()
    queue = CapturingQueue()
    app.dependency_overrides[get_token_identity] = admin_identity
    app.dependency_overrides[get_agent_queue] = lambda: queue
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            started = await client.post(
                "/api/v1/knowledge/assistant/runs",
                headers={"Idempotency-Key": f"assistant-{uuid4()}"},
                json={
                    "agent_id": str(SARI_AGENT_ID),
                    "language": "en",
                    "question": "What does the approved guide say about ventilation airflow?",
                },
            )
            assert started.status_code == 202, started.text
            run_id = UUID(started.json()["run_id"])
            assert queue.messages[0][0] == run_id

            executor = KnowledgeAssistantRunExecutor(
                DeterministicKnowledgeEmbeddingProvider(1536),
                MockKnowledgeAssistantProvider(),
                get_settings(),
            )
            assert await executor.execute(run_id, TENANT_ID) is None

            completed = await client.get(f"/api/v1/knowledge/assistant/runs/{run_id}")
            assert completed.status_code == 200
            payload = completed.json()
            assert payload["status"] == "succeeded"
            assert payload["result"]["evidence_status"] == "sufficient"
            assert payload["result"]["citations"][0]["chunk_id"]
            assert payload["result"]["citations"][0]["document_name"].startswith(
                "Eligible Ventilation Guide"
            )
            assert payload["correlation_id"]
            assert payload["duration_ms"] >= 0

            async with session_factory() as session:
                await session.execute(
                    text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                    {"tenant_id": str(TENANT_ID)},
                )
                stored = await session.scalar(select(AgentRun).where(AgentRun.id == run_id))
                assert stored is not None
                assert "question" not in stored.input_snapshot
                assert len(str(stored.input_snapshot["question_sha256"])) == 64
    finally:
        app.dependency_overrides.clear()
        await cleanup_collection(collection_id)


@pytest.mark.asyncio
async def test_assistant_rejects_ivc_and_cross_tenant_before_queueing() -> None:
    queue = CapturingQueue()
    app.dependency_overrides[get_token_identity] = admin_identity
    app.dependency_overrides[get_agent_queue] = lambda: queue
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            ivc = await client.post(
                "/api/v1/knowledge/assistant/runs",
                headers={"Idempotency-Key": f"assistant-{uuid4()}"},
                json={
                    "agent_id": str(IVC_AGENT_ID),
                    "language": "en",
                    "question": "What is the approved IVC cage capacity?",
                },
            )
            assert ivc.status_code == 403

            cross_tenant = await client.post(
                "/api/v1/knowledge/assistant/runs",
                headers={
                    "Idempotency-Key": f"assistant-{uuid4()}",
                    "X-Tenant-Id": str(uuid4()),
                },
                json={
                    "agent_id": str(SARI_AGENT_ID),
                    "language": "en",
                    "question": "What does the guide say?",
                },
            )
            assert cross_tenant.status_code == 403
            assert queue.messages == []
    finally:
        app.dependency_overrides.clear()
