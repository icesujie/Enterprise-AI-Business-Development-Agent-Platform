from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal
from urllib.parse import urlparse
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.crm_repository import (
    CrmNotFoundError,
    SqlAlchemyCrmRepository,
    VersionConflictError,
)
from sari_api.adapters.database import get_session
from sari_api.adapters.models import Contact, Lead, Organization
from sari_api.adapters.work_repository import SqlAlchemyWorkRepository
from sari_api.api.dependencies import require_permission
from sari_api.domain.identity import Principal

router = APIRouter(prefix="/api/v1", tags=["crm"])

Priority = Literal["low", "normal", "high", "urgent"]
LeadStatus = Literal[
    "new", "qualifying", "qualified", "nurture", "disqualified", "converted", "archived"
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class OrganizationInput(StrictModel):
    legal_name: str = Field(min_length=1, max_length=250)
    display_name: str | None = Field(default=None, max_length=250)
    website_url: str | None = Field(default=None, max_length=2048)
    domain: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=120)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    city: str | None = Field(default=None, max_length=120)
    preferred_language: str | None = Field(default=None, max_length=20)

    @field_validator("country_code")
    @classmethod
    def uppercase_country(cls, value: str | None) -> str | None:
        return value.upper() if value else None


class OrganizationPatch(StrictModel):
    legal_name: str | None = Field(default=None, min_length=1, max_length=250)
    display_name: str | None = Field(default=None, min_length=1, max_length=250)
    website_url: str | None = Field(default=None, max_length=2048)
    domain: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=120)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    city: str | None = Field(default=None, max_length=120)
    preferred_language: str | None = Field(default=None, max_length=20)
    lifecycle_stage: Literal["prospect", "qualified", "customer", "inactive"] | None = None


class OrganizationResponse(StrictModel):
    id: UUID
    legal_name: str
    display_name: str
    website_url: str | None
    domain: str | None
    industry: str | None
    country_code: str | None
    city: str | None
    preferred_language: str | None
    lifecycle_stage: str
    owner_membership_id: UUID | None
    created_at: datetime
    updated_at: datetime
    version: int
    duplicate_warnings: list[str] = Field(default_factory=list)


class ContactInput(StrictModel):
    organization_id: UUID | None = None
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    job_title: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone_e164: str | None = Field(default=None, max_length=20, pattern=r"^\+[1-9]\d{6,14}$")
    whatsapp_e164: str | None = Field(default=None, max_length=20, pattern=r"^\+[1-9]\d{6,14}$")
    preferred_language: str | None = Field(default=None, max_length=20)
    marketing_consent_status: Literal["unknown", "granted", "denied", "withdrawn"] = "unknown"
    do_not_contact: bool = False

    @model_validator(mode="after")
    def require_identity(self) -> ContactInput:
        if not any((self.first_name, self.last_name, self.email, self.phone_e164)):
            raise ValueError("provide a name, email, or phone number")
        return self


class ContactPatch(StrictModel):
    organization_id: UUID | None = None
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    job_title: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=320)
    phone_e164: str | None = Field(default=None, max_length=20)
    whatsapp_e164: str | None = Field(default=None, max_length=20)
    preferred_language: str | None = Field(default=None, max_length=20)
    marketing_consent_status: Literal["unknown", "granted", "denied", "withdrawn"] | None = None
    do_not_contact: bool | None = None


class ContactResponse(StrictModel):
    id: UUID
    organization_id: UUID | None
    first_name: str | None
    last_name: str | None
    job_title: str | None
    email: str | None
    phone_e164: str | None
    whatsapp_e164: str | None
    preferred_language: str | None
    marketing_consent_status: str
    do_not_contact: bool
    owner_membership_id: UUID | None
    created_at: datetime
    updated_at: datetime
    version: int
    duplicate_warnings: list[str] = Field(default_factory=list)


class LeadInput(StrictModel):
    contact_id: UUID | None = None
    organization_id: UUID | None = None
    source_channel: Literal["website", "manual", "email", "partner", "import"] = "manual"
    source_detail: str | None = Field(default=None, max_length=200)
    inquiry_summary: str = Field(min_length=10, max_length=10000)
    priority: Priority = "normal"
    owner_membership_id: UUID | None = None
    estimated_value: Decimal | None = Field(default=None, ge=0, max_digits=19, decimal_places=4)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    target_timeline: str | None = Field(default=None, max_length=100)
    project_country_code: str | None = Field(default=None, min_length=2, max_length=2)
    project_city: str | None = Field(default=None, max_length=120)
    project_type: str | None = Field(default=None, max_length=120)
    expected_capacity: str | None = Field(default=None, max_length=120)
    requirements: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_money(self) -> LeadInput:
        if (self.estimated_value is None) != (self.currency is None):
            raise ValueError("estimated_value and currency must be provided together")
        if self.currency:
            self.currency = self.currency.upper()
        if self.project_country_code:
            self.project_country_code = self.project_country_code.upper()
        return self


class LeadPatch(StrictModel):
    contact_id: UUID | None = None
    organization_id: UUID | None = None
    inquiry_summary: str | None = Field(default=None, min_length=10, max_length=10000)
    status: LeadStatus | None = None
    priority: Priority | None = None
    owner_membership_id: UUID | None = None
    estimated_value: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    target_timeline: str | None = Field(default=None, max_length=100)
    project_country_code: str | None = Field(default=None, min_length=2, max_length=2)
    project_city: str | None = Field(default=None, max_length=120)
    project_type: str | None = Field(default=None, max_length=120)
    expected_capacity: str | None = Field(default=None, max_length=120)
    requirements: dict[str, Any] | None = None

    @model_validator(mode="after")
    def normalize_codes(self) -> LeadPatch:
        if self.currency:
            self.currency = self.currency.upper()
        if self.project_country_code:
            self.project_country_code = self.project_country_code.upper()
        return self


class LeadResponse(StrictModel):
    id: UUID
    contact_id: UUID | None
    organization_id: UUID | None
    source_channel: str
    source_detail: str | None
    inquiry_summary: str
    status: str
    priority: str
    owner_membership_id: UUID | None
    estimated_value: Decimal | None
    currency: str | None
    target_timeline: str | None
    project_country_code: str | None
    project_city: str | None
    project_type: str | None
    expected_capacity: str | None
    requirements: dict[str, Any]
    qualification_score: Decimal | None
    created_at: datetime
    updated_at: datetime
    version: int


class LeadListResponse(StrictModel):
    items: list[LeadResponse]
    next_cursor: datetime | None


def organization_response(
    entity: Organization, warnings: list[str] | None = None
) -> OrganizationResponse:
    return OrganizationResponse(
        **{
            field: getattr(entity, field)
            for field in OrganizationResponse.model_fields
            if field != "duplicate_warnings"
        },
        duplicate_warnings=warnings or [],
    )


def contact_response(entity: Contact, warnings: list[str] | None = None) -> ContactResponse:
    return ContactResponse(
        **{
            field: getattr(entity, field)
            for field in ContactResponse.model_fields
            if field != "duplicate_warnings"
        },
        duplicate_warnings=warnings or [],
    )


def lead_response(entity: Lead) -> LeadResponse:
    return LeadResponse(**{field: getattr(entity, field) for field in LeadResponse.model_fields})


def parse_if_match(value: str) -> int:
    try:
        return int(value.strip().strip('"'))
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="If-Match must contain a record version."
        ) from exc


async def repository(session: AsyncSession, principal: Principal) -> SqlAlchemyCrmRepository:
    result = SqlAlchemyCrmRepository(session, principal.tenant_id)
    await result.set_tenant_context()
    return result


def not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="CRM record not found.")


@router.get("/organizations", response_model=list[OrganizationResponse])
async def list_organizations(
    principal: Annotated[Principal, Depends(require_permission("crm:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[OrganizationResponse]:
    repo = await repository(session, principal)
    return [organization_response(item) for item in await repo.list_organizations(search, limit)]


@router.post("/organizations", response_model=OrganizationResponse, status_code=201)
async def create_organization(
    payload: OrganizationInput,
    principal: Annotated[Principal, Depends(require_permission("crm:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrganizationResponse:
    repo = await repository(session, principal)
    domain = payload.domain or domain_from_url(payload.website_url)
    warnings = await repo.duplicate_warnings(domain=domain)
    entity = Organization(
        tenant_id=principal.tenant_id,
        legal_name=payload.legal_name,
        display_name=payload.display_name or payload.legal_name,
        website_url=payload.website_url,
        domain=domain,
        industry=payload.industry,
        country_code=payload.country_code,
        city=payload.city,
        preferred_language=payload.preferred_language,
        owner_membership_id=principal.membership_id,
    )
    await repo.add(entity)
    await session.commit()
    return organization_response(entity, warnings)


@router.get("/organizations/{entity_id}", response_model=OrganizationResponse)
async def get_organization(
    entity_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("crm:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrganizationResponse:
    repo = await repository(session, principal)
    try:
        return organization_response(await repo.get_organization(entity_id))
    except CrmNotFoundError as exc:
        raise not_found() from exc


@router.patch("/organizations/{entity_id}", response_model=OrganizationResponse)
async def update_organization(
    entity_id: UUID,
    payload: OrganizationPatch,
    principal: Annotated[Principal, Depends(require_permission("crm:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    if_match: Annotated[str, Header(alias="If-Match")],
) -> OrganizationResponse:
    repo = await repository(session, principal)
    try:
        entity = await repo.get_organization(entity_id, for_update=True)
        repo.apply_versioned_update(
            entity, parse_if_match(if_match), payload.model_dump(exclude_unset=True)
        )
        await session.commit()
        await session.refresh(entity)
        return organization_response(entity)
    except CrmNotFoundError as exc:
        raise not_found() from exc
    except VersionConflictError as exc:
        raise HTTPException(
            status_code=409, detail="The record changed; reload and retry."
        ) from exc


@router.delete("/organizations/{entity_id}", status_code=204)
async def delete_organization(
    entity_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("crm:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    if_match: Annotated[str, Header(alias="If-Match")],
) -> Response:
    repo = await repository(session, principal)
    try:
        entity = await repo.get_organization(entity_id, for_update=True)
        repo.soft_delete(entity, parse_if_match(if_match), datetime.now(UTC))
        await session.commit()
        return Response(status_code=204)
    except CrmNotFoundError as exc:
        raise not_found() from exc
    except VersionConflictError as exc:
        raise HTTPException(
            status_code=409, detail="The record changed; reload and retry."
        ) from exc


@router.get("/contacts", response_model=list[ContactResponse])
async def list_contacts(
    principal: Annotated[Principal, Depends(require_permission("crm:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[ContactResponse]:
    repo = await repository(session, principal)
    return [contact_response(item) for item in await repo.list_contacts(search, limit)]


@router.post("/contacts", response_model=ContactResponse, status_code=201)
async def create_contact(
    payload: ContactInput,
    principal: Annotated[Principal, Depends(require_permission("crm:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ContactResponse:
    repo = await repository(session, principal)
    await repo.validate_links(payload.organization_id, None)
    warnings = await repo.duplicate_warnings(email=payload.email, phone=payload.phone_e164)
    entity = Contact(
        tenant_id=principal.tenant_id,
        owner_membership_id=principal.membership_id,
        **payload.model_dump(),
    )
    await repo.add(entity)
    await session.commit()
    return contact_response(entity, warnings)


@router.get("/contacts/{entity_id}", response_model=ContactResponse)
async def get_contact(
    entity_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("crm:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ContactResponse:
    repo = await repository(session, principal)
    try:
        return contact_response(await repo.get_contact(entity_id))
    except CrmNotFoundError as exc:
        raise not_found() from exc


@router.patch("/contacts/{entity_id}", response_model=ContactResponse)
async def update_contact(
    entity_id: UUID,
    payload: ContactPatch,
    principal: Annotated[Principal, Depends(require_permission("crm:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    if_match: Annotated[str, Header(alias="If-Match")],
) -> ContactResponse:
    repo = await repository(session, principal)
    try:
        entity = await repo.get_contact(entity_id, for_update=True)
        changes = payload.model_dump(exclude_unset=True)
        if changes.get("organization_id"):
            await repo.get_organization(changes["organization_id"])
        repo.apply_versioned_update(entity, parse_if_match(if_match), changes)
        await session.commit()
        await session.refresh(entity)
        return contact_response(entity)
    except CrmNotFoundError as exc:
        raise not_found() from exc
    except VersionConflictError as exc:
        raise HTTPException(
            status_code=409, detail="The record changed; reload and retry."
        ) from exc


@router.delete("/contacts/{entity_id}", status_code=204)
async def delete_contact(
    entity_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("crm:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    if_match: Annotated[str, Header(alias="If-Match")],
) -> Response:
    repo = await repository(session, principal)
    try:
        entity = await repo.get_contact(entity_id, for_update=True)
        repo.soft_delete(entity, parse_if_match(if_match), datetime.now(UTC))
        await session.commit()
        return Response(status_code=204)
    except CrmNotFoundError as exc:
        raise not_found() from exc
    except VersionConflictError as exc:
        raise HTTPException(
            status_code=409, detail="The record changed; reload and retry."
        ) from exc


@router.get("/leads", response_model=LeadListResponse)
async def list_leads(
    principal: Annotated[Principal, Depends(require_permission("crm:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    search: str | None = Query(default=None, max_length=200),
    lead_status: Annotated[LeadStatus | None, Query(alias="status")] = None,
    priority: Priority | None = None,
    owner_id: UUID | None = None,
    cursor: datetime | None = None,
    limit: int = Query(default=25, ge=1, le=100),
) -> LeadListResponse:
    repo = await repository(session, principal)
    items = await repo.list_leads(
        search=search,
        status=lead_status,
        priority=priority,
        owner_id=owner_id,
        created_before=cursor,
        limit=limit + 1,
    )
    has_more = len(items) > limit
    items = items[:limit]
    return LeadListResponse(
        items=[lead_response(item) for item in items],
        next_cursor=items[-1].created_at if has_more and items else None,
    )


@router.post("/leads", response_model=LeadResponse, status_code=201)
async def create_lead(
    payload: LeadInput,
    principal: Annotated[Principal, Depends(require_permission("crm:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LeadResponse:
    repo = await repository(session, principal)
    await repo.validate_links(payload.organization_id, payload.contact_id)
    entity = Lead(tenant_id=principal.tenant_id, **payload.model_dump())
    await repo.add(entity)
    work_repo = SqlAlchemyWorkRepository(session, principal.tenant_id)
    await work_repo.add_activity(
        lead_id=entity.id,
        activity_type="lead_created",
        subject="Lead created",
        description=f"Captured from {entity.source_channel}.",
        actor_membership_id=principal.membership_id,
    )
    await session.commit()
    return lead_response(entity)


@router.get("/leads/{entity_id}", response_model=LeadResponse)
async def get_lead(
    entity_id: UUID,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("crm:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LeadResponse:
    repo = await repository(session, principal)
    try:
        entity = await repo.get_lead(entity_id)
        response.headers["ETag"] = f'"{entity.version}"'
        return lead_response(entity)
    except CrmNotFoundError as exc:
        raise not_found() from exc


@router.patch("/leads/{entity_id}", response_model=LeadResponse)
async def update_lead(
    entity_id: UUID,
    payload: LeadPatch,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("crm:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    if_match: Annotated[str, Header(alias="If-Match")],
) -> LeadResponse:
    repo = await repository(session, principal)
    try:
        entity = await repo.get_lead(entity_id, for_update=True)
        changes = payload.model_dump(exclude_unset=True)
        await repo.validate_links(changes.get("organization_id"), changes.get("contact_id"))
        tracked_fields = {"status", "priority", "owner_membership_id"}
        before = {field: getattr(entity, field) for field in tracked_fields if field in changes}
        repo.apply_versioned_update(entity, parse_if_match(if_match), changes)
        changed = {
            field: {
                "from": str(before[field]) if before[field] is not None else None,
                "to": str(changes[field]) if changes[field] is not None else None,
            }
            for field in before
            if before[field] != changes[field]
        }
        if changed:
            work_repo = SqlAlchemyWorkRepository(session, principal.tenant_id)
            await work_repo.add_activity(
                lead_id=entity.id,
                activity_type="lead_updated",
                subject="Lead workflow updated",
                actor_membership_id=principal.membership_id,
                metadata={"changes": changed},
            )
        await session.commit()
        await session.refresh(entity)
        response.headers["ETag"] = f'"{entity.version}"'
        return lead_response(entity)
    except CrmNotFoundError as exc:
        raise not_found() from exc
    except VersionConflictError as exc:
        raise HTTPException(
            status_code=409, detail="The record changed; reload and retry."
        ) from exc


@router.delete("/leads/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_lead(
    entity_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("crm:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    if_match: Annotated[str, Header(alias="If-Match")],
) -> Response:
    repo = await repository(session, principal)
    try:
        entity = await repo.get_lead(entity_id, for_update=True)
        repo.apply_versioned_update(entity, parse_if_match(if_match), {"status": "archived"})
        await session.commit()
        return Response(status_code=204)
    except CrmNotFoundError as exc:
        raise not_found() from exc
    except VersionConflictError as exc:
        raise HTTPException(
            status_code=409, detail="The record changed; reload and retry."
        ) from exc


def domain_from_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value if "://" in value else f"https://{value}")
    return parsed.hostname.lower() if parsed.hostname else None
