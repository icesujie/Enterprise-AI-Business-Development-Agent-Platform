from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.content_governance_repository import (
    ContentNotFoundError,
    ContentStateError,
)
from sari_api.adapters.database import get_session
from sari_api.adapters.marketing_content_evaluation_repository import (
    MarketingContentEvaluationRepository,
    quality_from_generation,
)
from sari_api.api.dependencies import require_permission
from sari_api.api.routes.content_governance import (
    existing_idempotent_response,
    request_hash,
    save_idempotency,
)
from sari_api.core.config import get_settings
from sari_api.domain.identity import Principal
from sari_api.domain.marketing_content_acceptance import load_acceptance_dataset

router = APIRouter(prefix="/api/v1/content", tags=["marketing-content-evaluation"])

FeedbackCategory = Literal[
    "useful",
    "too_generic",
    "brand_tone_issue",
    "weak_cta",
    "insufficient_evidence",
    "too_long",
    "channel_mismatch",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, from_attributes=True)


class FeedbackInput(StrictModel):
    content_version_id: UUID
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    categories: list[FeedbackCategory] = Field(min_length=1, max_length=7)
    note: str | None = Field(default=None, max_length=2000)


class FeedbackResponse(StrictModel):
    id: UUID
    content_asset_id: UUID
    content_version_id: UUID
    reviewer_membership_id: UUID
    content_sha256: str
    categories: list[str]
    note: str | None
    created_at: datetime


class EvaluationResponse(StrictModel):
    asset_id: UUID
    evaluated_version_id: UUID
    generation_run_id: UUID | None
    generation_outcome: str | None
    evidence_status: str | None
    provider: str | None
    model: str | None
    quality_evaluation: dict[str, Any] | None
    human_edit_distance: float | None
    generated_version_id: UUID | None
    generated_version_number: int | None
    approved_human_version_id: UUID | None
    approved_human_version_number: int | None
    citations: list[dict[str, Any]]
    latency_ms: int | None
    token_usage: dict[str, Any]
    estimated_cost: str | None
    correlation_id: str | None
    feedback: list[FeedbackResponse]


class AcceptanceCaseResponse(StrictModel):
    case_id: str
    scenario: str
    content_type: str
    audience: str
    language: str
    channel: str
    business_objective: str
    topic: str
    call_to_action: str
    request_id: UUID | None
    request_status: str | None
    attempt_count: int
    asset_id: UUID | None
    asset_status: str | None
    reviewed: bool
    approved: bool
    rejected: bool
    human_edit_distance: float | None
    generated_version_number: int | None
    approved_human_version_number: int | None
    feedback_categories: list[str]
    quality_evaluation: dict[str, Any] | None


class AcceptanceSummaryResponse(StrictModel):
    total: int
    prepared: int
    reviewed: int
    approved: int
    rejected: int
    average_human_edit_distance: float | None
    common_feedback_categories: dict[str, int]
    quality_metric_summary: dict[str, float]
    brand_guideline_validation: Literal["pending", "completed"]
    brand_guideline_note: str
    openai_comparison_state: Literal["not_run", "completed", "deferred"]
    openai_comparison_note: str


class AcceptanceDashboardResponse(StrictModel):
    dataset_version: str
    configured_provider: str
    mock_preparation_allowed: bool
    cases: list[AcceptanceCaseResponse]
    summary: AcceptanceSummaryResponse


@router.post(
    "/assets/{asset_id}/feedback",
    response_model=FeedbackResponse,
    status_code=201,
)
async def add_marketing_feedback(
    asset_id: UUID,
    payload: FeedbackInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("content:review"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=8, max_length=200)
    ],
) -> FeedbackResponse:
    repo = MarketingContentEvaluationRepository(session, principal.tenant_id)
    await repo.set_tenant_context()
    payload_hash = request_hash({"asset_id": asset_id, **payload.model_dump(mode="json")})
    scope = f"asset-{asset_id}-review-feedback"
    existing = await existing_idempotent_response(
        session,
        principal=principal,
        scope=scope,
        key=idempotency_key,
        payload_hash=payload_hash,
    )
    if existing:
        response.status_code = existing.response_status
        return FeedbackResponse.model_validate(existing.response_body)
    try:
        feedback = await repo.add_feedback(
            asset_id=asset_id,
            version_id=payload.content_version_id,
            checksum=payload.content_sha256,
            reviewer_membership_id=principal.membership_id,
            categories=list(dict.fromkeys(payload.categories)),
            note=payload.note,
        )
        result = FeedbackResponse.model_validate(feedback)
        save_idempotency(
            session,
            principal=principal,
            scope=scope,
            key=idempotency_key,
            payload_hash=payload_hash,
            status_code=201,
            body=result,
        )
        await session.commit()
        return result
    except (ContentNotFoundError, ContentStateError) as exc:
        await session.rollback()
        status = 404 if isinstance(exc, ContentNotFoundError) else 409
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.get("/assets/{asset_id}/evaluation", response_model=EvaluationResponse)
async def get_marketing_evaluation(
    asset_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("content:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EvaluationResponse:
    repo = MarketingContentEvaluationRepository(session, principal.tenant_id)
    await repo.set_tenant_context()
    try:
        snapshot = await repo.snapshot(asset_id)
    except ContentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    generation = snapshot.generation
    agent_run = snapshot.agent_run
    generated = snapshot.generated_version
    return EvaluationResponse(
        asset_id=snapshot.asset.id,
        evaluated_version_id=snapshot.evaluated_version.id,
        generation_run_id=generation.id if generation else None,
        generation_outcome=(
            str(generation.validation_summary.get("outcome")) if generation else None
        ),
        evidence_status=generation.evidence_status if generation else None,
        provider=generation.provider if generation else None,
        model=generation.model if generation else None,
        quality_evaluation=quality_from_generation(generation),
        human_edit_distance=snapshot.human_edit_distance,
        generated_version_id=generated.id if generated else None,
        generated_version_number=generated.version_number if generated else None,
        approved_human_version_id=(
            snapshot.approved_human_version.id
            if snapshot.approved_human_version is not None
            else None
        ),
        approved_human_version_number=(
            snapshot.approved_human_version.version_number
            if snapshot.approved_human_version is not None
            else None
        ),
        citations=generated.citations if generated else [],
        latency_ms=generation.duration_ms if generation else None,
        token_usage=generation.token_usage if generation else {},
        estimated_cost=(
            str(generation.estimated_cost)
            if generation is not None and generation.estimated_cost is not None
            else None
        ),
        correlation_id=agent_run.correlation_id if agent_run else None,
        feedback=[FeedbackResponse.model_validate(item) for item in snapshot.feedback],
    )


@router.get("/acceptance", response_model=AcceptanceDashboardResponse)
async def get_marketing_acceptance_dashboard(
    principal: Annotated[Principal, Depends(require_permission("content:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AcceptanceDashboardResponse:
    dataset = load_acceptance_dataset()
    repo = MarketingContentEvaluationRepository(session, principal.tenant_id)
    await repo.set_tenant_context()
    records = await repo.acceptance_records(dataset.dataset_version)
    cases: list[AcceptanceCaseResponse] = []
    feedback_counts: Counter[str] = Counter()
    edit_distances: list[float] = []
    quality_values: dict[str, list[float]] = defaultdict(list)
    for case in dataset.cases:
        record = records.get(case.case_id)
        evaluation = record.evaluation if record else None
        feedback = evaluation.feedback if evaluation else []
        for item in feedback:
            feedback_counts.update(item.categories)
        if evaluation and evaluation.human_edit_distance is not None:
            edit_distances.append(evaluation.human_edit_distance)
        quality = quality_from_generation(evaluation.generation) if evaluation else None
        if quality:
            for key, value in quality.items():
                if key != "issues" and isinstance(value, int | float):
                    quality_values[key].append(float(value))
        latest_decision = (
            record.latest_decision.decision_type
            if record and record.latest_decision
            else None
        )
        reviewed = bool(feedback) or latest_decision is not None
        cases.append(
            AcceptanceCaseResponse(
                **case.model_dump(),
                request_id=record.request.id if record else None,
                request_status=record.request.status if record else None,
                attempt_count=record.attempt_count if record else 0,
                asset_id=record.asset.id if record and record.asset else None,
                asset_status=record.asset.status if record and record.asset else None,
                reviewed=reviewed,
                approved=bool(record and record.asset and record.asset.status == "approved"),
                rejected=latest_decision == "rejected",
                human_edit_distance=(evaluation.human_edit_distance if evaluation else None),
                generated_version_number=(
                    evaluation.generated_version.version_number
                    if evaluation and evaluation.generated_version
                    else None
                ),
                approved_human_version_number=(
                    evaluation.approved_human_version.version_number
                    if evaluation and evaluation.approved_human_version
                    else None
                ),
                feedback_categories=[category for item in feedback for category in item.categories],
                quality_evaluation=quality,
            )
        )
    summary = AcceptanceSummaryResponse(
        total=len(cases),
        prepared=sum(item.asset_id is not None for item in cases),
        reviewed=sum(item.reviewed for item in cases),
        approved=sum(item.approved for item in cases),
        rejected=sum(item.rejected for item in cases),
        average_human_edit_distance=(
            round(sum(edit_distances) / len(edit_distances), 4) if edit_distances else None
        ),
        common_feedback_categories=dict(feedback_counts.most_common()),
        quality_metric_summary={
            key: round(sum(values) / len(values), 2)
            for key, values in quality_values.items()
            if values
        },
        brand_guideline_validation="pending",
        brand_guideline_note=(
            "No approved real Sari Arta Brand Guideline has been accepted for this milestone."
        ),
        openai_comparison_state="not_run",
        openai_comparison_note=(
            "The controlled one-English/one-Chinese OpenAI comparison has not been run."
        ),
    )
    provider = get_settings().marketing_content_provider
    return AcceptanceDashboardResponse(
        dataset_version=dataset.dataset_version,
        configured_provider=provider,
        mock_preparation_allowed=provider == "mock",
        cases=cases,
        summary=summary,
    )
