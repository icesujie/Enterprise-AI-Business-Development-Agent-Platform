from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Any, Literal, Self
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.agent_queue import AgentQueue, get_agent_queue
from sari_api.adapters.database import get_session
from sari_api.adapters.ivc_qualification_repository import (
    IvcAssessmentAlreadyReviewedError,
    IvcQualificationNotFoundError,
    SqlAlchemyIvcQualificationRepository,
)
from sari_api.adapters.models import AuditEvent, IdempotencyKey, IvcQualificationAssessment
from sari_api.api.dependencies import require_permission
from sari_api.core.config import get_settings
from sari_api.core.observability import get_correlation_id
from sari_api.domain.identity import Principal
from sari_api.domain.ivc_demo_cases import (
    IVC_DEMO_CASES,
    IVC_DEMO_CASES_BY_KEY,
    IvcDemoCaseKey,
)
from sari_api.domain.ivc_qualification import IvcQualificationInput
from sari_api.domain.packages.models import SupportedLocale

router = APIRouter(prefix="/api/v1/ivc", tags=["ivc-qualification"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class IvcDemoCaseSummary(StrictModel):
    key: str
    name: str
    description: str


class IvcDemoCaseDetail(IvcDemoCaseSummary):
    project: IvcQualificationInput


class IvcQualificationRunInput(StrictModel):
    response_locale: SupportedLocale = "en"
    demo_case_key: IvcDemoCaseKey | None = None
    project: IvcQualificationInput | None = None

    @model_validator(mode="after")
    def exactly_one_input_source(self) -> Self:
        if (self.demo_case_key is None) == (self.project is None):
            raise ValueError("Provide exactly one of demo_case_key or project")
        return self


class IvcQualificationRunStartResponse(StrictModel):
    run_id: UUID
    workflow_type: str
    status: str
    status_url: str
    created_at: datetime


class IvcAssessmentResponse(StrictModel):
    id: UUID
    agent_run_id: UUID
    response_locale: str
    score: Decimal
    qualification_level: str
    business_summary: str
    key_qualification_factors: list[dict[str, Any]]
    recommended_next_actions: list[str]
    missing_information: list[str]
    risk_flags: list[str]
    confidence: Decimal
    expert_review_required: bool
    review_status: str
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    created_at: datetime


class IvcReviewInput(StrictModel):
    decision: Literal["approved", "rejected"]


def _assessment_response(item: IvcQualificationAssessment) -> IvcAssessmentResponse:
    return IvcAssessmentResponse(
        id=item.id,
        agent_run_id=item.agent_run_id,
        response_locale=item.response_locale,
        score=item.score,
        qualification_level=item.qualification_level,
        business_summary=item.business_summary,
        key_qualification_factors=item.key_qualification_factors,
        recommended_next_actions=item.recommended_next_actions,
        missing_information=item.missing_information,
        risk_flags=item.risk_flags,
        confidence=item.confidence,
        expert_review_required=item.expert_review_required,
        review_status=item.review_status,
        reviewed_by=item.reviewed_by,
        reviewed_at=item.reviewed_at,
        created_at=item.created_at,
    )


async def _repository(
    session: AsyncSession,
    principal: Principal,
) -> SqlAlchemyIvcQualificationRepository:
    repo = SqlAlchemyIvcQualificationRepository(session, principal.tenant_id)
    await repo.set_tenant_context()
    return repo


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="IVC qualification record not found.")


def _audit(
    session: AsyncSession,
    principal: Principal,
    *,
    action: str,
    target_type: str,
    target_id: UUID,
    details: dict[str, Any] | None = None,
) -> None:
    session.add(
        AuditEvent(
            tenant_id=principal.tenant_id,
            actor_user_id=principal.user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            result="success",
            request_id=get_correlation_id(),
            details=details or {},
        )
    )


@router.get("/demo-cases", response_model=list[IvcDemoCaseSummary])
async def list_demo_cases(
    principal: Annotated[Principal, Depends(require_permission("leads:qualify"))],
    locale: Annotated[SupportedLocale, Query()] = "en",
) -> list[IvcDemoCaseSummary]:
    del principal
    return [IvcDemoCaseSummary(**case.summary(locale)) for case in IVC_DEMO_CASES]


@router.get("/demo-cases/{case_key}", response_model=IvcDemoCaseDetail)
async def get_demo_case(
    case_key: IvcDemoCaseKey,
    principal: Annotated[Principal, Depends(require_permission("leads:qualify"))],
    locale: Annotated[SupportedLocale, Query()] = "en",
) -> IvcDemoCaseDetail:
    del principal
    case = IVC_DEMO_CASES_BY_KEY[case_key]
    return IvcDemoCaseDetail(**case.summary(locale), project=case.input)


@router.post(
    "/qualification-runs",
    response_model=IvcQualificationRunStartResponse,
    status_code=202,
)
async def start_ivc_qualification(
    payload: IvcQualificationRunInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("leads:qualify"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    queue: Annotated[AgentQueue, Depends(get_agent_queue)],
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=8, max_length=200),
    ],
) -> IvcQualificationRunStartResponse:
    project = (
        IVC_DEMO_CASES_BY_KEY[payload.demo_case_key].input
        if payload.demo_case_key is not None
        else payload.project
    )
    if project is None:  # Protected by request validation; keeps the service boundary explicit.
        raise HTTPException(status_code=422, detail="IVC project input is required.")

    scope = f"ivc-qualification:{principal.tenant_id}"
    request_body = payload.model_dump(mode="json")
    request_hash = hashlib.sha256(json.dumps(request_body, sort_keys=True).encode()).hexdigest()
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
        replay = IvcQualificationRunStartResponse.model_validate(existing.response_body)
        response.headers["Location"] = replay.status_url
        return replay

    repo = await _repository(session, principal)
    try:
        configuration = await repo.get_active_configuration()
        run = await repo.create_run(
            configuration=configuration,
            user_id=principal.user_id,
            input_data=project,
            response_locale=payload.response_locale,
            correlation_id=get_correlation_id(),
            max_attempts=get_settings().agent_max_attempts,
        )
    except IvcQualificationNotFoundError as exc:
        raise HTTPException(status_code=503, detail="IVC demo agent is not active.") from exc

    result = IvcQualificationRunStartResponse(
        run_id=run.id,
        workflow_type=run.workflow_type,
        status=run.status,
        status_url=f"/api/v1/agent-runs/{run.id}",
        created_at=run.created_at,
    )
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
    _audit(
        session,
        principal,
        action="ivc_agent_run.requested",
        target_type="agent_run",
        target_id=run.id,
        details={
            "workflow_type": run.workflow_type,
            "response_locale": payload.response_locale,
            "demo_case_key": payload.demo_case_key,
        },
    )
    await session.commit()

    try:
        await queue.enqueue(run.id, principal.tenant_id)
    except Exception as exc:
        repo = await _repository(session, principal)
        failed = await repo.get_run(run.id, for_update=True)
        await repo.fail_run(failed, "queue_unavailable", "AI queue is unavailable. Retry later.")
        await session.commit()
        raise HTTPException(
            status_code=503, detail="AI queue is unavailable. Retry later."
        ) from exc

    response.headers["Location"] = result.status_url
    return result


@router.get(
    "/qualification-assessments",
    response_model=list[IvcAssessmentResponse],
)
async def list_ivc_assessments(
    principal: Annotated[Principal, Depends(require_permission("leads:qualify"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(default=50, ge=1, le=100),
) -> list[IvcAssessmentResponse]:
    repo = await _repository(session, principal)
    return [_assessment_response(item) for item in await repo.list_assessments(limit)]


@router.get(
    "/qualification-assessments/{assessment_id}",
    response_model=IvcAssessmentResponse,
)
async def get_ivc_assessment(
    assessment_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("leads:qualify"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> IvcAssessmentResponse:
    repo = await _repository(session, principal)
    try:
        return _assessment_response(await repo.get_assessment(assessment_id))
    except IvcQualificationNotFoundError as exc:
        raise _not_found() from exc


@router.post(
    "/qualification-assessments/{assessment_id}/reviews",
    response_model=IvcAssessmentResponse,
)
async def review_ivc_assessment(
    assessment_id: UUID,
    payload: IvcReviewInput,
    principal: Annotated[Principal, Depends(require_permission("leads:qualify"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> IvcAssessmentResponse:
    repo = await _repository(session, principal)
    try:
        assessment = await repo.get_assessment(assessment_id, for_update=True)
        await repo.review_assessment(
            assessment,
            decision=payload.decision,
            user_id=principal.user_id,
        )
        _audit(
            session,
            principal,
            action="ivc_qualification_assessment.reviewed",
            target_type="ivc_qualification_assessment",
            target_id=assessment.id,
            details={"decision": payload.decision, "agent_run_id": str(assessment.agent_run_id)},
        )
        await session.commit()
        await session.refresh(assessment)
        return _assessment_response(assessment)
    except IvcQualificationNotFoundError as exc:
        raise _not_found() from exc
    except IvcAssessmentAlreadyReviewedError as exc:
        raise HTTPException(
            status_code=409, detail="This assessment was already reviewed."
        ) from exc
