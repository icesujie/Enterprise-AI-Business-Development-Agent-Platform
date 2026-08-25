from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    Response,
    UploadFile,
)
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.database import get_session
from sari_api.adapters.knowledge_storage import KnowledgeObjectNotFoundError
from sari_api.adapters.media_repository import (
    MediaConcurrencyError,
    MediaNotFoundError,
    MediaRepository,
    MediaStateError,
)
from sari_api.adapters.media_storage import MediaStorage, get_media_storage
from sari_api.api.dependencies import require_permission
from sari_api.api.routes.content_governance import parse_if_match
from sari_api.core.config import get_settings
from sari_api.domain.identity import Principal
from sari_api.domain.media_validation import InvalidMediaError, validate_image

router = APIRouter(prefix="/api/v1/media", tags=["media"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, from_attributes=True)


class MediaAssetResponse(StrictModel):
    id: UUID
    tenant_id: UUID
    media_type: str
    original_filename: str
    mime_type: str
    file_size: int
    checksum: str
    storage_provider: str
    width: int
    height: int
    title: str
    alt_text: str
    caption: str | None
    visibility: str
    public_use_status: str
    source_type: str
    source_reference_id: UUID | None
    uploaded_by: UUID
    approved_by: UUID | None
    record_version: int
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None
    revoked_at: datetime | None
    archived_at: datetime | None


class MediaMetadataInput(StrictModel):
    title: str = Field(min_length=2, max_length=250)
    alt_text: str = Field(min_length=3, max_length=500)
    caption: str | None = Field(default=None, max_length=2000)


class MediaAuditResponse(StrictModel):
    id: UUID
    media_asset_id: UUID
    actor_membership_id: UUID
    action: str
    before_metadata: dict[str, object]
    after_metadata: dict[str, object]
    details: dict[str, object]
    correlation_id: str | None
    created_at: datetime


async def repository(session: AsyncSession, principal: Principal) -> MediaRepository:
    repo = MediaRepository(session, principal.tenant_id)
    await repo.set_tenant_context()
    return repo


def clean_filename(filename: str | None) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", filename or "image")[:255]


def media_error(exc: Exception) -> HTTPException:
    if isinstance(exc, MediaNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, MediaConcurrencyError):
        return HTTPException(status_code=412, detail=str(exc))
    return HTTPException(status_code=409, detail=str(exc))


@router.get("/public/{asset_id}")
async def public_media(
    asset_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[MediaStorage, Depends(get_media_storage)],
) -> Response:
    tenant_id = UUID(get_settings().public_tenant_id)
    repo = MediaRepository(session, tenant_id)
    await repo.set_tenant_context()
    asset = await repo.get_public(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Public media not found.")
    try:
        content = await storage.get(asset.storage_key)
    except KnowledgeObjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Public media not found.") from exc
    return Response(
        content=content,
        media_type=asset.mime_type,
        headers={
            "Cache-Control": "public, max-age=30, must-revalidate",
            "ETag": f'"{asset.checksum}"',
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/assets", response_model=MediaAssetResponse, status_code=201)
async def upload_media(
    principal: Annotated[Principal, Depends(require_permission("media:upload"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[MediaStorage, Depends(get_media_storage)],
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form(min_length=2, max_length=250)],
    alt_text: Annotated[str, Form(min_length=3, max_length=500)],
    caption: Annotated[str | None, Form(max_length=2000)] = None,
    source_type: Annotated[
        Literal["manual_upload", "docx_import", "pdf_import", "html_import"], Form()
    ] = "manual_upload",
    source_reference_id: Annotated[UUID | None, Form()] = None,
) -> MediaAssetResponse:
    settings = get_settings()
    if source_type != "manual_upload" and source_reference_id is None:
        raise HTTPException(status_code=422, detail="Imported media requires a source reference.")
    filename = clean_filename(file.filename)
    mime_type = (file.content_type or "").split(";", maxsplit=1)[0].lower()
    content = await file.read(settings.media_max_upload_bytes + 1)
    if not content:
        raise HTTPException(status_code=422, detail="Uploaded image is empty.")
    if len(content) > settings.media_max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded image exceeds the size limit.")
    try:
        image = validate_image(content, filename, mime_type)
    except InvalidMediaError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    digest = hashlib.sha256(content).hexdigest()
    asset_id = uuid4()
    object_key = f"{principal.tenant_id}/media/{asset_id}{image.extension}"
    repo = await repository(session, principal)
    await storage.put(object_key, content)
    try:
        asset = await repo.create(
            id=asset_id,
            media_type="image",
            original_filename=filename,
            mime_type=image.mime_type,
            file_size=len(content),
            checksum=digest,
            storage_provider=storage.provider,
            storage_key=object_key,
            width=image.width,
            height=image.height,
            title=title,
            alt_text=alt_text,
            caption=caption,
            visibility="private",
            public_use_status="uploaded",
            source_type=source_type,
            source_reference_id=source_reference_id,
            actor_id=principal.membership_id,
        )
        await session.commit()
    except Exception:
        await session.rollback()
        await storage.delete(object_key)
        raise
    return MediaAssetResponse.model_validate(asset)


@router.get("/assets", response_model=list[MediaAssetResponse])
async def list_media(
    principal: Annotated[Principal, Depends(require_permission("media:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    status: Annotated[str | None, Query(max_length=20)] = None,
    search: Annotated[str | None, Query(max_length=200)] = None,
) -> list[MediaAssetResponse]:
    repo = await repository(session, principal)
    return [
        MediaAssetResponse.model_validate(asset)
        for asset in await repo.list_assets(status=status, search=search)
    ]


@router.get("/assets/{asset_id}", response_model=MediaAssetResponse)
async def get_media(
    asset_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("media:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MediaAssetResponse:
    repo = await repository(session, principal)
    try:
        return MediaAssetResponse.model_validate(await repo.get(asset_id))
    except MediaNotFoundError as exc:
        raise media_error(exc) from exc


@router.patch("/assets/{asset_id}", response_model=MediaAssetResponse)
async def update_media(
    asset_id: UUID,
    payload: MediaMetadataInput,
    principal: Annotated[Principal, Depends(require_permission("media:edit"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    if_match: Annotated[str, Header(alias="If-Match")],
) -> MediaAssetResponse:
    repo = await repository(session, principal)
    try:
        asset = await repo.update_metadata(
            asset_id=asset_id,
            actor_id=principal.membership_id,
            expected_version=parse_if_match(if_match),
            **payload.model_dump(),
        )
        await session.commit()
        return MediaAssetResponse.model_validate(asset)
    except (MediaNotFoundError, MediaStateError, MediaConcurrencyError) as exc:
        await session.rollback()
        raise media_error(exc) from exc


async def transition_media(
    asset_id: UUID,
    action: str,
    principal: Principal,
    session: AsyncSession,
    if_match: str,
) -> MediaAssetResponse:
    repo = await repository(session, principal)
    try:
        asset = await repo.transition(
            asset_id=asset_id,
            actor_id=principal.membership_id,
            expected_version=parse_if_match(if_match),
            action=action,
        )
        await session.commit()
        return MediaAssetResponse.model_validate(asset)
    except (
        MediaNotFoundError,
        MediaStateError,
        MediaConcurrencyError,
    ) as exc:
        await session.rollback()
        raise media_error(exc) from exc


@router.post("/assets/{asset_id}/submit-review", response_model=MediaAssetResponse)
async def submit_media_review(
    asset_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("media:submit_review"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    if_match: Annotated[str, Header(alias="If-Match")],
) -> MediaAssetResponse:
    return await transition_media(asset_id, "submit_review", principal, session, if_match)


@router.post("/assets/{asset_id}/approve", response_model=MediaAssetResponse)
async def approve_media(
    asset_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("media:approve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    if_match: Annotated[str, Header(alias="If-Match")],
) -> MediaAssetResponse:
    return await transition_media(asset_id, "approve", principal, session, if_match)


@router.post("/assets/{asset_id}/revoke", response_model=MediaAssetResponse)
async def revoke_media(
    asset_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("media:revoke"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    if_match: Annotated[str, Header(alias="If-Match")],
) -> MediaAssetResponse:
    return await transition_media(asset_id, "revoke", principal, session, if_match)


@router.post("/assets/{asset_id}/archive", response_model=MediaAssetResponse)
async def archive_media(
    asset_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("media:archive"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    if_match: Annotated[str, Header(alias="If-Match")],
) -> MediaAssetResponse:
    return await transition_media(asset_id, "archive", principal, session, if_match)


@router.get("/assets/{asset_id}/audit", response_model=list[MediaAuditResponse])
async def media_audit(
    asset_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("media:audit_read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[MediaAuditResponse]:
    repo = await repository(session, principal)
    try:
        return [MediaAuditResponse.model_validate(entry) for entry in await repo.audit(asset_id)]
    except MediaNotFoundError as exc:
        raise media_error(exc) from exc
