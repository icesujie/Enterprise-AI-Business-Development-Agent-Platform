from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.database import get_session
from sari_api.adapters.models import Activity, IdempotencyKey, Opportunity
from sari_api.adapters.opportunity_repository import (
    InvalidOpportunityTransitionError,
    OpportunityConflictError,
    OpportunityNotFoundError,
    OpportunityVersionConflictError,
    SqlAlchemyOpportunityRepository,
)
from sari_api.api.dependencies import require_permission
from sari_api.domain.identity import Principal

router = APIRouter(prefix="/api/v1", tags=["opportunities"])

OpportunityStage = Literal[
    "discovery", "requirements_confirmed", "proposal", "negotiation", "won", "lost"
]
OpportunityStatus = Literal["open", "won", "lost", "cancelled"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LeadConversionInput(StrictModel):
    name: str = Field(min_length=3, max_length=250)
    owner_membership_id: UUID | None = None
    expected_close_date: date | None = None
    estimated_value: Decimal | None = Field(default=None, ge=0, max_digits=19, decimal_places=4)
    currency: str | None = Field(default=None, min_length=3, max_length=3)

    @model_validator(mode="after")
    def money_is_paired(self) -> LeadConversionInput:
        if (self.estimated_value is None) != (self.currency is None):
            raise ValueError("estimated_value and currency must be provided together")
        if self.currency:
            self.currency = self.currency.upper()
        return self


class StageTransitionInput(StrictModel):
    stage: OpportunityStage
    reason: str | None = Field(default=None, max_length=1000)


class OpportunityResponse(StrictModel):
    id: UUID
    organization_id: UUID
    primary_contact_id: UUID | None
    source_lead_id: UUID | None
    name: str
    stage: str
    status: str
    probability: Decimal
    estimated_value: Decimal
    currency: str
    expected_close_date: date | None
    requirements: dict[str, Any]
    owner_membership_id: UUID
    created_at: datetime
    updated_at: datetime
    version: int


class OpportunityListResponse(StrictModel):
    items: list[OpportunityResponse]
    next_cursor: datetime | None


class ActivityResponse(StrictModel):
    id: UUID
    opportunity_id: UUID | None
    activity_type: str
    occurred_at: datetime
    subject: str
    description: str | None
    actor_membership_id: UUID
    metadata: dict[str, Any]
    created_at: datetime


def opportunity_response(entity: Opportunity) -> OpportunityResponse:
    return OpportunityResponse(
        **{field: getattr(entity, field) for field in OpportunityResponse.model_fields}
    )


def activity_response(entity: Activity) -> ActivityResponse:
    return ActivityResponse(
        id=entity.id,
        opportunity_id=entity.opportunity_id,
        activity_type=entity.activity_type,
        occurred_at=entity.occurred_at,
        subject=entity.subject,
        description=entity.description,
        actor_membership_id=entity.actor_membership_id,
        metadata=entity.metadata_json,
        created_at=entity.created_at,
    )


def parse_if_match(value: str) -> int:
    try:
        return int(value.strip().strip("W/").strip('"'))
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="If-Match must contain a record version."
        ) from exc


async def repository(
    session: AsyncSession, principal: Principal
) -> SqlAlchemyOpportunityRepository:
    repo = SqlAlchemyOpportunityRepository(session, principal.tenant_id)
    await repo.set_tenant_context()
    return repo


@router.post("/leads/{lead_id}/conversions", response_model=OpportunityResponse, status_code=201)
async def convert_lead(
    lead_id: UUID,
    payload: LeadConversionInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("leads:convert"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    if_match: Annotated[str, Header(alias="If-Match")],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)],
) -> OpportunityResponse:
    repo = await repository(session, principal)
    request_hash = hashlib.sha256(
        json.dumps(
            {"lead_id": str(lead_id), **payload.model_dump(mode="json")}, sort_keys=True
        ).encode()
    ).hexdigest()
    scope = f"lead-conversion:{principal.tenant_id}"
    await repo.lock_lead_conversion(lead_id)
    existing_key = await session.scalar(
        select(IdempotencyKey).where(
            IdempotencyKey.tenant_id == principal.tenant_id,
            IdempotencyKey.scope == scope,
            IdempotencyKey.idempotency_key == idempotency_key,
        )
    )
    if existing_key:
        if existing_key.request_hash != request_hash:
            raise HTTPException(status_code=409, detail="Idempotency key was reused.")
        response.status_code = existing_key.response_status
        return OpportunityResponse.model_validate(existing_key.response_body)

    try:
        lead = await repo.get_lead_for_conversion(lead_id)
        existing_opportunity = await repo.get_by_source_lead(lead_id)
        if existing_opportunity is not None:
            result = opportunity_response(existing_opportunity)
            result_status = 200
        else:
            expected_version = parse_if_match(if_match)
            if lead.version != expected_version:
                raise OpportunityVersionConflictError
            opportunity = await repo.convert(
                lead,
                name=payload.name,
                owner_membership_id=payload.owner_membership_id or principal.membership_id,
                expected_close_date=payload.expected_close_date,
                estimated_value=payload.estimated_value,
                currency=payload.currency,
                actor_membership_id=principal.membership_id,
            )
            result = opportunity_response(opportunity)
            result_status = 201
        response.status_code = result_status
        session.add(
            IdempotencyKey(
                tenant_id=principal.tenant_id,
                scope=scope,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_status=result_status,
                response_body=result.model_dump(mode="json"),
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )
        await session.commit()
        return result
    except OpportunityNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=404, detail="Lead or assignee not found.") from exc
    except OpportunityConflictError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except OpportunityVersionConflictError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="The lead changed; reload and retry.") from exc


@router.get("/opportunities", response_model=OpportunityListResponse)
async def list_opportunities(
    principal: Annotated[Principal, Depends(require_permission("crm:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    search: str | None = Query(default=None, max_length=200),
    stage: OpportunityStage | None = None,
    opportunity_status: Annotated[OpportunityStatus | None, Query(alias="status")] = None,
    cursor: datetime | None = None,
    limit: int = Query(default=25, ge=1, le=100),
) -> OpportunityListResponse:
    repo = await repository(session, principal)
    items = await repo.list_opportunities(
        search=search,
        stage=stage,
        status=opportunity_status,
        created_before=cursor,
        limit=limit + 1,
    )
    has_more = len(items) > limit
    items = items[:limit]
    return OpportunityListResponse(
        items=[opportunity_response(item) for item in items],
        next_cursor=items[-1].created_at if has_more and items else None,
    )


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: UUID,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("crm:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OpportunityResponse:
    repo = await repository(session, principal)
    try:
        opportunity = await repo.get(opportunity_id)
        response.headers["ETag"] = f'"{opportunity.version}"'
        return opportunity_response(opportunity)
    except OpportunityNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Opportunity not found.") from exc


@router.post(
    "/opportunities/{opportunity_id}/stage-transitions",
    response_model=OpportunityResponse,
)
async def transition_stage(
    opportunity_id: UUID,
    payload: StageTransitionInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("opportunities:manage"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    if_match: Annotated[str, Header(alias="If-Match")],
) -> OpportunityResponse:
    repo = await repository(session, principal)
    try:
        opportunity = await repo.get(opportunity_id, for_update=True)
        await repo.transition(
            opportunity,
            target_stage=payload.stage,
            reason=payload.reason,
            expected_version=parse_if_match(if_match),
            actor_membership_id=principal.membership_id,
        )
        await session.commit()
        await session.refresh(opportunity)
        response.headers["ETag"] = f'"{opportunity.version}"'
        return opportunity_response(opportunity)
    except OpportunityNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Opportunity not found.") from exc
    except OpportunityVersionConflictError as exc:
        raise HTTPException(
            status_code=409, detail="The record changed; reload and retry."
        ) from exc
    except InvalidOpportunityTransitionError as exc:
        raise HTTPException(
            status_code=409, detail="This stage transition is not allowed."
        ) from exc
    except OpportunityConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/opportunities/{opportunity_id}/activities", response_model=list[ActivityResponse])
async def list_opportunity_activities(
    opportunity_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("crm:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ActivityResponse]:
    repo = await repository(session, principal)
    try:
        return [activity_response(item) for item in await repo.activities(opportunity_id)]
    except OpportunityNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Opportunity not found.") from exc
