from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.agent_queue import AgentQueue, get_agent_queue
from sari_api.adapters.database import get_session
from sari_api.adapters.models import AgentRun, IdempotencyKey, LeadAssessment
from sari_api.adapters.qualification_repository import (
    AssessmentAlreadyReviewedError,
    QualificationNotFoundError,
    SqlAlchemyQualificationRepository,
)
from sari_api.adapters.work_repository import SqlAlchemyWorkRepository
from sari_api.api.dependencies import require_permission
from sari_api.domain.identity import Principal
from sari_api.domain.qualification import (
    QUALIFICATION_FACTOR_LABELS,
    QualificationLevel,
    qualification_level_for_score,
)

router = APIRouter(prefix="/api/v1", tags=["qualification"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class QualificationRunInput(StrictModel):
    rubric_key: Literal["commercial_kitchen_project_v1"] = "commercial_kitchen_project_v1"
    language: Literal["en", "id"] = "en"


class QualificationRunStartResponse(StrictModel):
    run_id: UUID
    workflow_type: str
    status: str
    status_url: str
    created_at: datetime


class QualificationRunResponse(StrictModel):
    id: UUID
    workflow_type: str
    status: str
    lead_id: UUID | None
    result: dict[str, Any] | None
    provider_type: str | None
    model_id: str | None
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    error_message: str | None
    created_at: datetime


class QualificationFactorResponse(StrictModel):
    key: str
    label: str
    status: str


class AssessmentResponse(StrictModel):
    id: UUID
    lead_id: UUID
    assessment_version: int
    agent_run_id: UUID | None
    score: Decimal
    qualification_level: QualificationLevel
    tier: str
    need_summary: str | None
    business_summary: str | None
    qualification: dict[str, Any]
    key_qualification_factors: list[QualificationFactorResponse]
    recommended_action: str
    missing_information: list[str]
    confidence: Decimal
    review_status: str
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    created_at: datetime


class ReviewInput(StrictModel):
    decision: Literal["approved", "rejected"]


def run_start_response(run: AgentRun) -> QualificationRunStartResponse:
    return QualificationRunStartResponse(
        run_id=run.id,
        workflow_type=run.workflow_type,
        status=run.status,
        status_url=f"/api/v1/agent-runs/{run.id}",
        created_at=run.created_at,
    )


def run_response(run: AgentRun) -> QualificationRunResponse:
    return QualificationRunResponse(
        id=run.id,
        workflow_type=run.workflow_type,
        status=run.status,
        lead_id=run.lead_id,
        result=run.output_result,
        provider_type=run.provider_type,
        model_id=run.model_id,
        started_at=run.started_at,
        completed_at=run.completed_at,
        error_code=run.error_code,
        error_message=run.error_message_safe,
        created_at=run.created_at,
    )


def assessment_response(assessment: LeadAssessment) -> AssessmentResponse:
    return AssessmentResponse(
        id=assessment.id,
        lead_id=assessment.lead_id,
        assessment_version=assessment.assessment_version,
        agent_run_id=assessment.agent_run_id,
        score=assessment.score,
        qualification_level=qualification_level_for_score(assessment.score),
        tier=assessment.tier,
        need_summary=assessment.need_summary,
        business_summary=assessment.need_summary,
        qualification=assessment.qualification,
        key_qualification_factors=[
            QualificationFactorResponse(
                key=key.removesuffix("_status"),
                label=QUALIFICATION_FACTOR_LABELS.get(key, key.replace("_", " ").title()),
                status=str(status),
            )
            for key, status in assessment.qualification.items()
        ],
        recommended_action=assessment.recommended_action,
        missing_information=assessment.missing_information,
        confidence=assessment.confidence,
        review_status=assessment.review_status,
        reviewed_by=assessment.reviewed_by,
        reviewed_at=assessment.reviewed_at,
        created_at=assessment.created_at,
    )


async def repository(
    session: AsyncSession, principal: Principal
) -> SqlAlchemyQualificationRepository:
    repo = SqlAlchemyQualificationRepository(session, principal.tenant_id)
    await repo.set_tenant_context()
    return repo


def not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="Qualification record not found.")


@router.post(
    "/leads/{lead_id}/qualification-runs",
    response_model=QualificationRunStartResponse,
    status_code=202,
)
async def start_qualification(
    lead_id: UUID,
    payload: QualificationRunInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("leads:qualify"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    queue: Annotated[AgentQueue, Depends(get_agent_queue)],
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=8, max_length=200),
    ],
) -> QualificationRunStartResponse:
    repo = await repository(session, principal)
    scope = f"lead-qualification:{principal.tenant_id}"
    request_hash = hashlib.sha256(
        json.dumps(
            {"lead_id": str(lead_id), **payload.model_dump()},
            sort_keys=True,
        ).encode()
    ).hexdigest()
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"{scope}:{idempotency_key}"},
    )
    existing = await session.scalar(
        select(IdempotencyKey).where(
            IdempotencyKey.tenant_id == principal.tenant_id,
            IdempotencyKey.scope == scope,
            IdempotencyKey.idempotency_key == idempotency_key,
        )
    )
    if existing:
        if existing.request_hash != request_hash:
            raise HTTPException(status_code=409, detail="Idempotency key was reused.")
        replay = QualificationRunStartResponse.model_validate(existing.response_body)
        response.headers["Location"] = replay.status_url
        return replay

    try:
        lead = await repo.get_lead(lead_id)
        configuration = await repo.get_active_configuration()
        snapshot = await repo.build_snapshot(lead, principal.membership_id)
        snapshot["requested_language"] = payload.language
        run = await repo.create_run(
            configuration=configuration,
            lead_id=lead_id,
            user_id=principal.user_id,
            input_snapshot=snapshot,
        )
        result = run_start_response(run)
        session.add(
            IdempotencyKey(
                tenant_id=principal.tenant_id,
                scope=scope,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_status=202,
                response_body=result.model_dump(mode="json"),
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )
        work_repo = SqlAlchemyWorkRepository(session, principal.tenant_id)
        await work_repo.add_activity(
            lead_id=lead_id,
            activity_type="qualification_requested",
            subject="AI qualification requested",
            actor_membership_id=principal.membership_id,
            metadata={"agent_run_id": str(run.id)},
        )
        await session.commit()
    except QualificationNotFoundError as exc:
        raise not_found() from exc

    try:
        await queue.enqueue(run.id, principal.tenant_id)
    except Exception as exc:
        repo = await repository(session, principal)
        failed_run = await repo.get_run(run.id, for_update=True)
        await repo.fail_run(
            failed_run,
            "queue_unavailable",
            "AI queue is unavailable. Retry later.",
        )
        await session.commit()
        raise HTTPException(
            status_code=503,
            detail="AI queue is unavailable. Retry later.",
        ) from exc

    response.headers["Location"] = result.status_url
    return result


@router.get("/agent-runs/{run_id}", response_model=QualificationRunResponse)
async def get_agent_run(
    run_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("leads:qualify"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QualificationRunResponse:
    repo = await repository(session, principal)
    try:
        return run_response(await repo.get_run(run_id))
    except QualificationNotFoundError as exc:
        raise not_found() from exc


@router.get(
    "/leads/{lead_id}/qualification-runs",
    response_model=list[QualificationRunResponse],
)
async def list_agent_runs(
    lead_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("leads:qualify"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[QualificationRunResponse]:
    repo = await repository(session, principal)
    try:
        return [run_response(item) for item in await repo.list_runs(lead_id)]
    except QualificationNotFoundError as exc:
        raise not_found() from exc


@router.get(
    "/leads/{lead_id}/qualification-assessments",
    response_model=list[AssessmentResponse],
)
async def list_assessments(
    lead_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("leads:qualify"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[AssessmentResponse]:
    repo = await repository(session, principal)
    try:
        return [assessment_response(item) for item in await repo.list_assessments(lead_id)]
    except QualificationNotFoundError as exc:
        raise not_found() from exc


@router.post(
    "/lead-assessments/{assessment_id}/reviews",
    response_model=AssessmentResponse,
)
async def review_assessment(
    assessment_id: UUID,
    payload: ReviewInput,
    principal: Annotated[Principal, Depends(require_permission("leads:qualify"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AssessmentResponse:
    repo = await repository(session, principal)
    try:
        assessment = await repo.get_assessment(assessment_id, for_update=True)
        await repo.review_assessment(
            assessment,
            decision=payload.decision,
            user_id=principal.user_id,
        )
        work_repo = SqlAlchemyWorkRepository(session, principal.tenant_id)
        await work_repo.add_activity(
            lead_id=assessment.lead_id,
            activity_type="qualification_reviewed",
            subject=f"AI qualification {payload.decision}",
            actor_membership_id=principal.membership_id,
            metadata={"assessment_id": str(assessment.id), "decision": payload.decision},
        )
        await session.commit()
        await session.refresh(assessment)
        return assessment_response(assessment)
    except QualificationNotFoundError as exc:
        raise not_found() from exc
    except AssessmentAlreadyReviewedError as exc:
        raise HTTPException(
            status_code=409,
            detail="This assessment was already reviewed.",
        ) from exc
