from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.content_governance_repository import (
    ContentConcurrencyError,
    ContentGovernanceRepository,
    ContentNotFoundError,
    ContentSeparationOfDutiesError,
    ContentStateError,
)
from sari_api.adapters.database import get_session
from sari_api.adapters.models import (
    ContentAsset,
    ContentVersion,
    IdempotencyKey,
)
from sari_api.api.dependencies import get_current_principal, require_permission
from sari_api.domain.identity import Principal

router = APIRouter(prefix="/api/v1/content", tags=["content-governance"])

ContentType = Literal[
    "website_article",
    "case_study",
    "tiktok_script",
    "instagram_reel_script",
    "facebook_post",
    "email_draft",
]
Audience = Literal[
    "schools",
    "hospitals",
    "factories",
    "central_kitchens",
    "project_owners",
    "facility_managers",
]
Channel = Literal["website", "tiktok", "instagram", "facebook", "email"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, from_attributes=True)


class ContentRequestInput(StrictModel):
    domain_key: str = Field(default="commercial_kitchen", min_length=2, max_length=100)
    agent_id: UUID | None = None
    content_type: ContentType
    audience: Audience
    language: Literal["en", "zh-CN"]
    channel: Channel
    business_objective: str = Field(min_length=3, max_length=2000)
    topic: str = Field(min_length=3, max_length=2000)
    call_to_action: str = Field(min_length=2, max_length=1000)
    campaign_name: str | None = Field(default=None, max_length=200)
    constraints: dict[str, Any] = Field(default_factory=dict)
    knowledge_collection_ids: list[UUID] = Field(default_factory=list, max_length=50)


class ContentRequestResponse(StrictModel):
    id: UUID
    tenant_id: UUID
    domain_id: UUID
    agent_id: UUID | None
    requested_by: UUID
    content_type: str
    audience: str
    language: str
    channel: str
    business_objective: str
    topic: str
    call_to_action: str
    campaign_name: str | None
    constraints: dict[str, Any]
    knowledge_collection_ids: list[str]
    status: str
    result_asset_id: UUID | None
    created_at: datetime
    updated_at: datetime


class VersionBodyInput(StrictModel):
    content_body: dict[str, Any]
    plain_text: str = Field(min_length=1, max_length=100_000)
    claims: list[dict[str, Any]] = Field(default_factory=list, max_length=500)
    citations: list[dict[str, Any]] = Field(default_factory=list, max_length=500)


class ContentAssetInput(VersionBodyInput):
    domain_key: str = Field(default="commercial_kitchen", min_length=2, max_length=100)
    request_id: UUID | None = None
    agent_id: UUID | None = None
    title: str = Field(min_length=2, max_length=250)
    content_type: ContentType
    audience: Audience
    language: Literal["en", "zh-CN"]
    channel: Channel
    owner_membership_id: UUID | None = None


class ContentVersionResponse(StrictModel):
    id: UUID
    tenant_id: UUID
    content_asset_id: UUID
    version_number: int
    origin: str
    content_body: dict[str, Any]
    plain_text: str
    claims: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    generation_run_id: UUID | None
    based_on_version_id: UUID | None
    content_sha256: str
    created_by: UUID
    created_at: datetime


class ContentAssetResponse(StrictModel):
    id: UUID
    tenant_id: UUID
    domain_id: UUID
    agent_id: UUID | None
    request_id: UUID | None
    title: str
    content_type: str
    audience: str
    language: str
    channel: str
    status: str
    owner_membership_id: UUID
    creator_membership_id: UUID
    current_version_id: UUID | None
    approved_version_id: UUID | None
    record_version: int
    archived_at: datetime | None
    archived_by: UUID | None
    archive_reason: str | None
    created_at: datetime
    updated_at: datetime
    current_version: ContentVersionResponse | None = None


class ExactVersionInput(StrictModel):
    content_version_id: UUID
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    comment: str | None = Field(default=None, max_length=2000)


class DecisionInput(ExactVersionInput):
    decision: Literal["changes_requested", "approved", "rejected"]


class ApprovalDecisionResponse(StrictModel):
    id: UUID
    content_asset_id: UUID
    content_version_id: UUID
    decision_type: str
    decided_by: UUID
    content_sha256: str
    comment: str | None
    created_at: datetime


class GovernanceCommandResponse(StrictModel):
    asset: ContentAssetResponse
    decision: ApprovalDecisionResponse | None = None


class RollbackInput(StrictModel):
    source_version_id: UUID


class ReasonInput(StrictModel):
    reason: str = Field(min_length=3, max_length=2000)


class AuditResponse(StrictModel):
    id: UUID
    actor_membership_id: UUID
    action: str
    target_type: str
    target_id: UUID
    content_asset_id: UUID | None
    content_version_id: UUID | None
    content_request_id: UUID | None
    outcome: str
    before_metadata: dict[str, Any]
    after_metadata: dict[str, Any]
    details: dict[str, Any]
    correlation_id: str | None
    created_at: datetime


def parse_if_match(value: str | None) -> int:
    if value is None:
        raise HTTPException(status_code=428, detail="If-Match is required.")
    try:
        return int(value.strip().removeprefix("W/").strip('"'))
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="If-Match must contain a record version."
        ) from exc


async def repository(
    session: AsyncSession, principal: Principal
) -> ContentGovernanceRepository:
    repo = ContentGovernanceRepository(session, principal.tenant_id)
    await repo.set_tenant_context()
    return repo


def request_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def idempotency_scope(principal: Principal, scope: str) -> str:
    digest = hashlib.sha256(f"{principal.tenant_id}:{scope}".encode()).hexdigest()[:32]
    return f"content:{digest}"


async def existing_idempotent_response(
    session: AsyncSession,
    *,
    principal: Principal,
    scope: str,
    key: str,
    payload_hash: str,
) -> IdempotencyKey | None:
    full_scope = idempotency_scope(principal, scope)
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
        {"key": f"{full_scope}:{key}"},
    )
    existing = await session.scalar(
        select(IdempotencyKey).where(
            IdempotencyKey.tenant_id == principal.tenant_id,
            IdempotencyKey.scope == full_scope,
            IdempotencyKey.idempotency_key == key,
        )
    )
    if existing is not None and existing.request_hash != payload_hash:
        raise HTTPException(status_code=409, detail="Idempotency key was reused.")
    return existing


def save_idempotency(
    session: AsyncSession,
    *,
    principal: Principal,
    scope: str,
    key: str,
    payload_hash: str,
    status_code: int,
    body: BaseModel,
) -> None:
    session.add(
        IdempotencyKey(
            tenant_id=principal.tenant_id,
            scope=idempotency_scope(principal, scope),
            idempotency_key=key,
            request_hash=payload_hash,
            response_status=status_code,
            response_body=body.model_dump(mode="json"),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
    )


def version_response(version: ContentVersion) -> ContentVersionResponse:
    return ContentVersionResponse.model_validate(version)


async def asset_response(
    repo: ContentGovernanceRepository, asset: ContentAsset
) -> ContentAssetResponse:
    await repo.refresh_asset(asset)
    version = (
        await repo.get_version(asset.id, asset.current_version_id)
        if asset.current_version_id is not None
        else None
    )
    data = ContentAssetResponse.model_validate(asset).model_dump()
    data["current_version"] = version_response(version) if version else None
    return ContentAssetResponse.model_validate(data)


def handle_content_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ContentNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ContentConcurrencyError):
        return HTTPException(status_code=412, detail=str(exc))
    if isinstance(exc, ContentSeparationOfDutiesError):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=409, detail=str(exc))


@router.post("/requests", response_model=ContentRequestResponse, status_code=201)
async def create_content_request(
    payload: ContentRequestInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("content:create"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)],
) -> ContentRequestResponse:
    repo = await repository(session, principal)
    payload_hash = request_hash(payload.model_dump(mode="json"))
    existing = await existing_idempotent_response(
        session,
        principal=principal,
        scope="request-create",
        key=idempotency_key,
        payload_hash=payload_hash,
    )
    if existing:
        response.status_code = existing.response_status
        return ContentRequestResponse.model_validate(existing.response_body)
    try:
        values = payload.model_dump(exclude={"domain_key"}, mode="python")
        values["knowledge_collection_ids"] = [
            str(item) for item in payload.knowledge_collection_ids
        ]
        entity = await repo.create_request(
            domain_key=payload.domain_key,
            requested_by=principal.membership_id,
            values=values,
        )
        result = ContentRequestResponse.model_validate(entity)
        save_idempotency(
            session,
            principal=principal,
            scope="request-create",
            key=idempotency_key,
            payload_hash=payload_hash,
            status_code=201,
            body=result,
        )
        await session.commit()
        return result
    except (ContentNotFoundError, ContentStateError) as exc:
        await session.rollback()
        raise handle_content_error(exc) from exc


@router.post("/assets", response_model=ContentAssetResponse, status_code=201)
async def create_content_asset(
    payload: ContentAssetInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("content:create"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)],
) -> ContentAssetResponse:
    repo = await repository(session, principal)
    payload_hash = request_hash(payload.model_dump(mode="json"))
    existing = await existing_idempotent_response(
        session,
        principal=principal,
        scope="asset-create",
        key=idempotency_key,
        payload_hash=payload_hash,
    )
    if existing:
        response.status_code = existing.response_status
        return ContentAssetResponse.model_validate(existing.response_body)
    try:
        version_values = payload.model_dump(
            include={"content_body", "plain_text", "claims", "citations"}, mode="json"
        )
        asset_values = payload.model_dump(
            exclude={
                "domain_key",
                "content_body",
                "plain_text",
                "claims",
                "citations",
            },
            exclude_none=True,
            mode="python",
        )
        _, version = await repo.create_asset(
            domain_key=payload.domain_key,
            actor_id=principal.membership_id,
            asset_values=asset_values,
            version_values=version_values,
        )
        asset = await repo.get_asset(version.content_asset_id)
        result = await asset_response(repo, asset)
        save_idempotency(
            session,
            principal=principal,
            scope="asset-create",
            key=idempotency_key,
            payload_hash=payload_hash,
            status_code=201,
            body=result,
        )
        await session.commit()
        return result
    except (ContentNotFoundError, ContentStateError) as exc:
        await session.rollback()
        raise handle_content_error(exc) from exc


@router.get("/assets", response_model=list[ContentAssetResponse])
async def list_content_assets(
    principal: Annotated[Principal, Depends(require_permission("content:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ContentAssetResponse]:
    repo = await repository(session, principal)
    return [await asset_response(repo, asset) for asset in await repo.list_assets()]


@router.get("/requests/{request_id}", response_model=ContentRequestResponse)
async def get_content_request(
    request_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("content:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ContentRequestResponse:
    repo = await repository(session, principal)
    try:
        return ContentRequestResponse.model_validate(await repo.get_request(request_id))
    except ContentNotFoundError as exc:
        raise handle_content_error(exc) from exc


@router.get("/assets/{asset_id}", response_model=ContentAssetResponse)
async def get_content_asset(
    asset_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("content:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ContentAssetResponse:
    repo = await repository(session, principal)
    try:
        return await asset_response(repo, await repo.get_asset(asset_id))
    except ContentNotFoundError as exc:
        raise handle_content_error(exc) from exc


@router.get("/assets/{asset_id}/versions", response_model=list[ContentVersionResponse])
async def list_content_versions(
    asset_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("content:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ContentVersionResponse]:
    repo = await repository(session, principal)
    try:
        return [version_response(item) for item in await repo.list_versions(asset_id)]
    except ContentNotFoundError as exc:
        raise handle_content_error(exc) from exc


@router.post("/assets/{asset_id}/versions", response_model=ContentAssetResponse, status_code=201)
async def create_content_version(
    asset_id: UUID,
    payload: VersionBodyInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("content:edit"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=8, max_length=200)
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> ContentAssetResponse:
    expected = parse_if_match(if_match)
    repo = await repository(session, principal)
    payload_hash = request_hash({"asset_id": asset_id, **payload.model_dump(mode="json")})
    existing = await existing_idempotent_response(
        session,
        principal=principal,
        scope=f"asset-{asset_id}-version",
        key=idempotency_key,
        payload_hash=payload_hash,
    )
    if existing:
        response.status_code = existing.response_status
        return ContentAssetResponse.model_validate(existing.response_body)
    try:
        asset, _ = await repo.create_successor(
            asset_id=asset_id,
            expected_record_version=expected,
            actor_id=principal.membership_id,
            values=payload.model_dump(mode="python"),
        )
        result = await asset_response(repo, asset)
        save_idempotency(
            session,
            principal=principal,
            scope=f"asset-{asset_id}-version",
            key=idempotency_key,
            payload_hash=payload_hash,
            status_code=201,
            body=result,
        )
        await session.commit()
        return result
    except (
        ContentNotFoundError,
        ContentStateError,
        ContentConcurrencyError,
        IntegrityError,
    ) as exc:
        await session.rollback()
        mapped = (
            ContentConcurrencyError("Content changed; reload and retry.")
            if isinstance(exc, IntegrityError)
            else exc
        )
        raise handle_content_error(mapped) from exc


@router.post("/assets/{asset_id}/rollback", response_model=ContentAssetResponse, status_code=201)
async def rollback_content_version(
    asset_id: UUID,
    payload: RollbackInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("content:edit"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=8, max_length=200)
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> ContentAssetResponse:
    expected = parse_if_match(if_match)
    repo = await repository(session, principal)
    payload_hash = request_hash({"asset_id": asset_id, **payload.model_dump(mode="json")})
    existing = await existing_idempotent_response(
        session,
        principal=principal,
        scope=f"asset-{asset_id}-rollback",
        key=idempotency_key,
        payload_hash=payload_hash,
    )
    if existing:
        response.status_code = existing.response_status
        return ContentAssetResponse.model_validate(existing.response_body)
    try:
        asset, _ = await repo.rollback(
            asset_id=asset_id,
            source_version_id=payload.source_version_id,
            expected_record_version=expected,
            actor_id=principal.membership_id,
        )
        result = await asset_response(repo, asset)
        save_idempotency(
            session,
            principal=principal,
            scope=f"asset-{asset_id}-rollback",
            key=idempotency_key,
            payload_hash=payload_hash,
            status_code=201,
            body=result,
        )
        await session.commit()
        return result
    except (ContentNotFoundError, ContentStateError, ContentConcurrencyError) as exc:
        await session.rollback()
        raise handle_content_error(exc) from exc


@router.post("/assets/{asset_id}/submit-review", response_model=GovernanceCommandResponse)
async def submit_content_review(
    asset_id: UUID,
    payload: ExactVersionInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("content:submit_review"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=8, max_length=200)
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> GovernanceCommandResponse:
    return await apply_review_command(
        asset_id=asset_id,
        payload=payload,
        response=response,
        principal=principal,
        session=session,
        expected=parse_if_match(if_match),
        idempotency_key=idempotency_key,
    )


async def apply_review_command(
    *,
    asset_id: UUID,
    payload: ExactVersionInput,
    response: Response,
    principal: Principal,
    session: AsyncSession,
    expected: int,
    idempotency_key: str,
) -> GovernanceCommandResponse:
    repo = await repository(session, principal)
    payload_hash = request_hash({"asset_id": asset_id, **payload.model_dump(mode="json")})
    scope = f"asset-{asset_id}-submit-review"
    existing = await existing_idempotent_response(
        session,
        principal=principal,
        scope=scope,
        key=idempotency_key,
        payload_hash=payload_hash,
    )
    if existing:
        response.status_code = existing.response_status
        return GovernanceCommandResponse.model_validate(existing.response_body)
    try:
        asset, decision = await repo.submit_review(
            asset_id=asset_id,
            version_id=payload.content_version_id,
            checksum=payload.content_sha256,
            expected_record_version=expected,
            actor_id=principal.membership_id,
            comment=payload.comment,
        )
        result = GovernanceCommandResponse(
            asset=await asset_response(repo, asset),
            decision=ApprovalDecisionResponse.model_validate(decision),
        )
        save_idempotency(
            session,
            principal=principal,
            scope=scope,
            key=idempotency_key,
            payload_hash=payload_hash,
            status_code=200,
            body=result,
        )
        await session.commit()
        return result
    except (ContentNotFoundError, ContentStateError, ContentConcurrencyError) as exc:
        await session.rollback()
        raise handle_content_error(exc) from exc


@router.post("/assets/{asset_id}/decisions", response_model=GovernanceCommandResponse)
async def decide_content_review(
    asset_id: UUID,
    payload: DecisionInput,
    response: Response,
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=8, max_length=200)
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> GovernanceCommandResponse:
    required = (
        "content:approve"
        if payload.decision in {"approved", "rejected"}
        else "content:review"
    )
    if required not in principal.permissions:
        raise HTTPException(status_code=403, detail="This action is not permitted.")
    expected = parse_if_match(if_match)
    repo = await repository(session, principal)
    payload_hash = request_hash({"asset_id": asset_id, **payload.model_dump(mode="json")})
    scope = f"asset-{asset_id}-decision"
    existing = await existing_idempotent_response(
        session,
        principal=principal,
        scope=scope,
        key=idempotency_key,
        payload_hash=payload_hash,
    )
    if existing:
        response.status_code = existing.response_status
        return GovernanceCommandResponse.model_validate(existing.response_body)
    try:
        asset, decision = await repo.decide(
            asset_id=asset_id,
            version_id=payload.content_version_id,
            checksum=payload.content_sha256,
            decision_type=payload.decision,
            expected_record_version=expected,
            actor_id=principal.membership_id,
            comment=payload.comment,
        )
        result = GovernanceCommandResponse(
            asset=await asset_response(repo, asset),
            decision=ApprovalDecisionResponse.model_validate(decision),
        )
        save_idempotency(
            session,
            principal=principal,
            scope=scope,
            key=idempotency_key,
            payload_hash=payload_hash,
            status_code=200,
            body=result,
        )
        await session.commit()
        return result
    except (
        ContentNotFoundError,
        ContentStateError,
        ContentConcurrencyError,
        ContentSeparationOfDutiesError,
    ) as exc:
        await session.rollback()
        raise handle_content_error(exc) from exc


async def apply_archive_command(
    *,
    asset_id: UUID,
    payload: ReasonInput,
    response: Response,
    principal: Principal,
    session: AsyncSession,
    expected: int,
    idempotency_key: str,
    restore: bool,
) -> ContentAssetResponse:
    repo = await repository(session, principal)
    action = "restore" if restore else "archive"
    payload_hash = request_hash({"asset_id": asset_id, "action": action, "reason": payload.reason})
    scope = f"asset-{asset_id}-{action}"
    existing = await existing_idempotent_response(
        session,
        principal=principal,
        scope=scope,
        key=idempotency_key,
        payload_hash=payload_hash,
    )
    if existing:
        response.status_code = existing.response_status
        return ContentAssetResponse.model_validate(existing.response_body)
    try:
        command = repo.restore if restore else repo.archive
        asset = await command(
            asset_id=asset_id,
            expected_record_version=expected,
            actor_id=principal.membership_id,
            reason=payload.reason,
        )
        result = await asset_response(repo, asset)
        save_idempotency(
            session,
            principal=principal,
            scope=scope,
            key=idempotency_key,
            payload_hash=payload_hash,
            status_code=200,
            body=result,
        )
        await session.commit()
        return result
    except (ContentNotFoundError, ContentStateError, ContentConcurrencyError) as exc:
        await session.rollback()
        raise handle_content_error(exc) from exc


@router.post("/assets/{asset_id}/archive", response_model=ContentAssetResponse)
async def archive_content_asset(
    asset_id: UUID,
    payload: ReasonInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("content:archive"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=8, max_length=200)
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> ContentAssetResponse:
    return await apply_archive_command(
        asset_id=asset_id,
        payload=payload,
        response=response,
        principal=principal,
        session=session,
        expected=parse_if_match(if_match),
        idempotency_key=idempotency_key,
        restore=False,
    )


@router.post("/assets/{asset_id}/restore", response_model=ContentAssetResponse)
async def restore_content_asset(
    asset_id: UUID,
    payload: ReasonInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("content:archive"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=8, max_length=200)
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> ContentAssetResponse:
    return await apply_archive_command(
        asset_id=asset_id,
        payload=payload,
        response=response,
        principal=principal,
        session=session,
        expected=parse_if_match(if_match),
        idempotency_key=idempotency_key,
        restore=True,
    )


@router.get("/assets/{asset_id}/audit", response_model=list[AuditResponse])
async def list_content_audit(
    asset_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("content:audit_read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[AuditResponse]:
    repo = await repository(session, principal)
    try:
        return [AuditResponse.model_validate(item) for item in await repo.list_audit(asset_id)]
    except ContentNotFoundError as exc:
        raise handle_content_error(exc) from exc


@router.get(
    "/assets/{asset_id}/decisions",
    response_model=list[ApprovalDecisionResponse],
)
async def list_content_decisions(
    asset_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("content:audit_read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ApprovalDecisionResponse]:
    repo = await repository(session, principal)
    try:
        return [
            ApprovalDecisionResponse.model_validate(item)
            for item in await repo.list_decisions(asset_id)
        ]
    except ContentNotFoundError as exc:
        raise handle_content_error(exc) from exc
