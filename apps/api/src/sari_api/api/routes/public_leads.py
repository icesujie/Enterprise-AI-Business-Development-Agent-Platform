from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from hmac import compare_digest
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from redis.exceptions import RedisError
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.crm_repository import SqlAlchemyCrmRepository
from sari_api.adapters.database import get_session
from sari_api.adapters.models import AuditEvent, Contact, IdempotencyKey, Lead, Organization
from sari_api.adapters.rate_limit import consume_fixed_window
from sari_api.core.config import get_settings

router = APIRouter(prefix="/api/v1/public", tags=["public lead capture"])


class PublicModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PublicContact(PublicModel):
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    email: str = Field(max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone_e164: str | None = Field(default=None, max_length=20, pattern=r"^\+[1-9]\d{6,14}$")
    preferred_language: str | None = Field(default=None, max_length=20)


class PublicOrganization(PublicModel):
    name: str = Field(min_length=1, max_length=250)
    website_url: str | None = Field(default=None, max_length=2048)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)


class PublicInquiry(PublicModel):
    message: str = Field(min_length=10, max_length=10000)
    project_country_code: str | None = Field(default=None, min_length=2, max_length=2)
    project_city: str | None = Field(default=None, max_length=120)
    project_type: str | None = Field(default=None, max_length=120)
    facility_type: str | None = Field(default=None, max_length=120)
    expected_capacity: str | None = Field(default=None, max_length=120)
    target_timeline: str | None = Field(default=None, max_length=100)
    budget_range: str | None = Field(default=None, max_length=120)


class PublicAttribution(PublicModel):
    source: Literal["website", "website_ai_assistant"] = "website"
    campaign: str | None = Field(default=None, max_length=200)


class PublicConsent(PublicModel):
    privacy_policy_version: str = Field(min_length=1, max_length=50)
    contact_consent: Literal[True]
    marketing_consent: bool = False


class PublicLeadSubmission(PublicModel):
    contact: PublicContact
    organization: PublicOrganization
    inquiry: PublicInquiry
    attribution: PublicAttribution = Field(default_factory=PublicAttribution)
    consent: PublicConsent


class PublicLeadAccepted(PublicModel):
    submission_id: UUID
    status: Literal["accepted"] = "accepted"
    message: str = "Your inquiry has been received."
    duplicate: bool = False


async def enforce_public_rate_limit(request: Request) -> None:
    settings = get_settings()
    client_host = request.client.host if request.client else "unknown"
    digest = hashlib.sha256(client_host.encode()).hexdigest()[:24]
    try:
        allowed, retry_after = await consume_fixed_window(
            redis_url=settings.redis_url,
            key=f"rate:public-leads:{digest}",
            limit=settings.public_rate_limit,
            window_seconds=settings.public_rate_window_seconds,
        )
    except RedisError as exc:
        raise HTTPException(
            status_code=503, detail="Inquiry service is temporarily unavailable."
        ) from exc
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many inquiry submissions.",
            headers={"Retry-After": str(max(retry_after, 1))},
        )


@router.post(
    "/lead-submissions",
    response_model=PublicLeadAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(enforce_public_rate_limit)],
)
async def submit_public_lead(
    payload: PublicLeadSubmission,
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)],
    site_token: Annotated[str, Header(alias="X-Site-Token")],
) -> PublicLeadAccepted:
    settings = get_settings()
    if not compare_digest(site_token, settings.public_site_token):
        raise HTTPException(status_code=401, detail="Invalid site token.")

    tenant_id = UUID(settings.public_tenant_id)
    repo = SqlAlchemyCrmRepository(session, tenant_id)
    await repo.set_tenant_context()
    request_hash = hashlib.sha256(
        json.dumps(payload.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
        {"lock_key": f"public-lead:{idempotency_key}"},
    )
    existing = await session.scalar(
        select(IdempotencyKey).where(
            IdempotencyKey.scope == "public-lead",
            IdempotencyKey.idempotency_key == idempotency_key,
        )
    )
    if existing:
        if existing.request_hash != request_hash:
            raise HTTPException(
                status_code=409, detail="Idempotency key was used for another request."
            )
        return PublicLeadAccepted.model_validate(existing.response_body)

    duplicate_conditions = [
        Contact.tenant_id == tenant_id,
        func.lower(Contact.email) == payload.contact.email.lower(),
        Lead.tenant_id == tenant_id,
        Lead.source_channel == payload.attribution.source,
        Lead.created_at >= datetime.now(UTC) - timedelta(days=1),
    ]
    if payload.inquiry.project_type:
        duplicate_conditions.append(
            func.lower(Lead.project_type) == payload.inquiry.project_type.lower()
        )
    if payload.inquiry.project_city:
        duplicate_conditions.append(
            func.lower(Lead.project_city) == payload.inquiry.project_city.lower()
        )
    duplicate_lead = await session.scalar(
        select(Lead)
        .join(Contact, Contact.id == Lead.contact_id)
        .where(*duplicate_conditions)
        .order_by(Lead.created_at.desc())
        .limit(1)
    )
    if duplicate_lead is not None:
        duplicate_result = PublicLeadAccepted(
            submission_id=duplicate_lead.id,
            message="Your existing inquiry has already been received.",
            duplicate=True,
        )
        session.add(
            IdempotencyKey(
                tenant_id=tenant_id,
                scope="public-lead",
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_status=202,
                response_body=duplicate_result.model_dump(mode="json"),
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
        )
        session.add(
            AuditEvent(
                tenant_id=tenant_id,
                actor_user_id=None,
                action="public_lead.duplicate_detected",
                target_type="lead",
                target_id=duplicate_lead.id,
                result="success",
                details={"source": payload.attribution.source},
            )
        )
        await session.commit()
        return duplicate_result

    organization = await repo.add(
        Organization(
            tenant_id=tenant_id,
            legal_name=payload.organization.name,
            display_name=payload.organization.name,
            website_url=payload.organization.website_url,
            domain=hostname(payload.organization.website_url),
            country_code=uppercase(payload.organization.country_code),
        )
    )
    contact = await repo.add(
        Contact(
            tenant_id=tenant_id,
            organization_id=organization.id,
            first_name=payload.contact.first_name,
            last_name=payload.contact.last_name,
            email=payload.contact.email.lower(),
            phone_e164=payload.contact.phone_e164,
            preferred_language=payload.contact.preferred_language,
            marketing_consent_status=("granted" if payload.consent.marketing_consent else "denied"),
        )
    )
    lead = await repo.add(
        Lead(
            tenant_id=tenant_id,
            organization_id=organization.id,
            contact_id=contact.id,
            source_channel=payload.attribution.source,
            source_detail=payload.attribution.campaign,
            inquiry_summary=payload.inquiry.message,
            project_country_code=uppercase(payload.inquiry.project_country_code),
            project_city=payload.inquiry.project_city,
            project_type=payload.inquiry.project_type,
            expected_capacity=payload.inquiry.expected_capacity,
            target_timeline=payload.inquiry.target_timeline,
            requirements={
                "privacy_policy_version": payload.consent.privacy_policy_version,
                "contact_consent": True,
                "facility_type": payload.inquiry.facility_type,
                "budget_range": payload.inquiry.budget_range,
            },
        )
    )
    result = PublicLeadAccepted(submission_id=lead.id)
    session.add(
        IdempotencyKey(
            tenant_id=tenant_id,
            scope="public-lead",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response_status=202,
            response_body=result.model_dump(mode="json"),
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
    )
    session.add(
        AuditEvent(
            tenant_id=tenant_id,
            actor_user_id=None,
            action="public_lead.created",
            target_type="lead",
            target_id=lead.id,
            result="success",
            details={"source": payload.attribution.source},
        )
    )
    await session.commit()
    return result


def uppercase(value: str | None) -> str | None:
    return value.upper() if value else None


def hostname(value: str | None) -> str | None:
    if not value:
        return None
    from urllib.parse import urlparse

    parsed = urlparse(value if "://" in value else f"https://{value}")
    return parsed.hostname.lower() if parsed.hostname else None
