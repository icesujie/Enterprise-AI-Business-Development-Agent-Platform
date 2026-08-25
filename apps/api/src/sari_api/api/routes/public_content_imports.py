from __future__ import annotations

import hashlib
import re
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.database import get_session
from sari_api.adapters.document_import_extractor import (
    DefaultDocumentImportExtractor,
    DocumentImportResult,
    InsufficientImportExtractionError,
    UnsupportedImportDocumentError,
)
from sari_api.adapters.media_repository import MediaRepository
from sari_api.adapters.media_storage import MediaStorage, get_media_storage
from sari_api.adapters.public_content_import_repository import (
    PublicContentImportNotFoundError,
    PublicContentImportRepository,
)
from sari_api.api.dependencies import require_permission
from sari_api.core.config import get_settings
from sari_api.domain.identity import Principal
from sari_api.domain.media_validation import InvalidMediaError, validate_image

router = APIRouter(prefix="/api/v1/public-content/imports", tags=["public-content-imports"])

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
IMPORT_TYPES = {
    ".docx": ("docx", DOCX_MIME),
    ".pdf": ("pdf", "application/pdf"),
    ".html": ("html", "text/html"),
    ".htm": ("html", "text/html"),
    ".txt": ("txt", "text/plain"),
    ".md": ("markdown", "text/markdown"),
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class PublicContentImportResponse(StrictModel):
    id: UUID
    tenant_id: UUID
    source_type: str
    original_filename: str
    mime_type: str
    checksum: str
    file_size: int
    requested_by: UUID
    storage_provider: str
    processing_status: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    failure_reason: str | None
    extraction_metadata: dict[str, object]
    extraction_result: dict[str, object]
    extracted_media_ids: list[str]


async def repository(
    session: AsyncSession, principal: Principal
) -> PublicContentImportRepository:
    repo = PublicContentImportRepository(session, principal.tenant_id)
    await repo.set_tenant_context()
    return repo


@router.post("", response_model=PublicContentImportResponse, status_code=201)
async def import_document(
    principal: Annotated[Principal, Depends(require_permission("public_content:import"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[MediaStorage, Depends(get_media_storage)],
    file: Annotated[UploadFile, File()],
) -> PublicContentImportResponse:
    settings = get_settings()
    filename = _display_filename(file.filename)
    source_type, media_type = _validate_declaration(filename, file.content_type or "")
    content = await file.read(settings.public_content_import_max_upload_bytes + 1)
    if not content:
        raise HTTPException(status_code=422, detail="Imported document is empty.")
    if len(content) > settings.public_content_import_max_upload_bytes:
        raise HTTPException(status_code=413, detail="Imported document exceeds the size limit.")
    _validate_content(content, source_type)

    import_id = uuid4()
    suffix = Path(filename).suffix.casefold()
    object_key = f"{principal.tenant_id}/imports/{import_id}/source{suffix}"
    repo = await repository(session, principal)
    await storage.put(object_key, content)
    try:
        record = await repo.create(
            id=import_id,
            source_type=source_type,
            original_filename=filename,
            mime_type=media_type,
            checksum=hashlib.sha256(content).hexdigest(),
            file_size=len(content),
            storage_provider=storage.provider,
            storage_key=object_key,
            actor_id=principal.membership_id,
        )
        await session.commit()
        await repo.set_tenant_context()
        await repo.mark_processing(import_id, actor_id=principal.membership_id)
        await session.commit()
    except Exception:
        await session.rollback()
        await storage.delete(object_key)
        raise

    written_media_keys: list[str] = []
    try:
        result = await DefaultDocumentImportExtractor().extract(content, media_type)
        await repo.set_tenant_context()
        media_ids, media_keys, media_summary = await _create_imported_media(
            result=result,
            import_id=import_id,
            filename=filename,
            source_type=source_type,
            principal=principal,
            session=session,
            storage=storage,
        )
        written_media_keys.extend(media_keys)
        metadata = dict(result.metadata)
        metadata.update(
            {
                "source_checksum": record.checksum,
                "block_count": len(result.blocks),
                "character_count": sum(len(block.text) for block in result.blocks),
                "extracted_media_count": len(media_ids),
            }
        )
        extraction_result: dict[str, object] = {
            "title": result.title,
            "blocks": [
                {
                    "kind": block.kind,
                    "text": block.text,
                    "order": block.order,
                    "level": block.level,
                    "page_number": block.page_number,
                    "section_title": block.section_title,
                }
                for block in result.blocks
            ],
            "media": media_summary,
        }
        record = await repo.mark_completed(
            import_id,
            actor_id=principal.membership_id,
            extraction_metadata=metadata,
            extraction_result=extraction_result,
            extracted_media_ids=[str(media_id) for media_id in media_ids],
        )
        await session.commit()
        return PublicContentImportResponse.model_validate(record)
    except (UnsupportedImportDocumentError, InsufficientImportExtractionError) as exc:
        await session.rollback()
        for key in written_media_keys:
            await storage.delete(key)
        await repo.set_tenant_context()
        failure_code = (
            "insufficient_extraction"
            if isinstance(exc, InsufficientImportExtractionError)
            else "unsupported_document"
        )
        record = await repo.mark_failed(
            import_id,
            actor_id=principal.membership_id,
            reason=str(exc),
            metadata={"failure_code": failure_code, "ocr_supported": False},
        )
        await session.commit()
        return PublicContentImportResponse.model_validate(record)
    except Exception:
        await session.rollback()
        for key in written_media_keys:
            await storage.delete(key)
        await repo.set_tenant_context()
        record = await repo.mark_failed(
            import_id,
            actor_id=principal.membership_id,
            reason="Document processing failed safely.",
            metadata={"failure_code": "processing_failed"},
        )
        await session.commit()
        return PublicContentImportResponse.model_validate(record)


@router.get("", response_model=list[PublicContentImportResponse])
async def list_imports(
    principal: Annotated[Principal, Depends(require_permission("public_content:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[PublicContentImportResponse]:
    repo = await repository(session, principal)
    return [
        PublicContentImportResponse.model_validate(record)
        for record in await repo.list_imports()
    ]


@router.get("/{import_id}", response_model=PublicContentImportResponse)
async def get_import(
    import_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("public_content:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PublicContentImportResponse:
    repo = await repository(session, principal)
    try:
        return PublicContentImportResponse.model_validate(await repo.get(import_id))
    except PublicContentImportNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


async def _create_imported_media(
    *,
    result: DocumentImportResult,
    import_id: UUID,
    filename: str,
    source_type: str,
    principal: Principal,
    session: AsyncSession,
    storage: MediaStorage,
) -> tuple[list[UUID], list[str], list[dict[str, object]]]:
    media_repo = MediaRepository(session, principal.tenant_id)
    media_ids: list[UUID] = []
    storage_keys: list[str] = []
    summary: list[dict[str, object]] = []
    try:
        for image in result.images:
            try:
                validated = validate_image(image.content, image.filename, image.mime_type)
            except InvalidMediaError:
                continue
            asset_id = uuid4()
            key = f"{principal.tenant_id}/media/{asset_id}{validated.extension}"
            await storage.put(key, image.content)
            storage_keys.append(key)
            asset = await media_repo.create(
                id=asset_id,
                media_type="image",
                original_filename=_clean_filename(image.filename),
                mime_type=validated.mime_type,
                file_size=len(image.content),
                checksum=hashlib.sha256(image.content).hexdigest(),
                storage_provider=storage.provider,
                storage_key=key,
                width=validated.width,
                height=validated.height,
                title=f"Imported image {image.order + 1} from {filename}"[:250],
                alt_text="Review required before this imported image may be used publicly.",
                caption=None,
                visibility="private",
                public_use_status="uploaded",
                source_type=f"{source_type}_import",
                source_reference_id=import_id,
                actor_id=principal.membership_id,
            )
            media_ids.append(asset.id)
            summary.append(
                {
                    "media_asset_id": str(asset.id),
                    "order": image.order,
                    "page_number": image.page_number,
                    "section_title": image.section_title,
                }
            )
    except Exception:
        for key in storage_keys:
            await storage.delete(key)
        raise
    return media_ids, storage_keys, summary


def _clean_filename(filename: str | None) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", filename or "document")[:255]
    return cleaned or "document"


def _display_filename(filename: str | None) -> str:
    basename = (filename or "document").replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    cleaned = "".join(character for character in basename if character.isprintable()).strip()
    return (cleaned or "document")[:255]


def _validate_declaration(filename: str, declared_mime: str) -> tuple[str, str]:
    definition = IMPORT_TYPES.get(Path(filename).suffix.casefold())
    if definition is None:
        raise HTTPException(status_code=415, detail="Unsupported document extension.")
    source_type, expected_mime = definition
    normalized = declared_mime.split(";", maxsplit=1)[0].strip().lower()
    compatible = {
        expected_mime,
        "application/octet-stream",
        "text/plain" if source_type == "markdown" else expected_mime,
    }
    if normalized not in compatible:
        raise HTTPException(status_code=415, detail="File extension and MIME type do not match.")
    return source_type, expected_mime


def _validate_content(content: bytes, source_type: str) -> None:
    if source_type == "pdf" and not content.lstrip().startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="The uploaded file is not a valid PDF.")
    if source_type == "docx":
        try:
            with zipfile.ZipFile(BytesIO(content)) as archive:
                if "word/document.xml" not in archive.namelist():
                    raise HTTPException(status_code=415, detail="The uploaded file is not a DOCX.")
        except zipfile.BadZipFile as exc:
            raise HTTPException(status_code=415, detail="The uploaded file is not a DOCX.") from exc
    if source_type in {"html", "txt", "markdown"}:
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=415, detail="Text imports must use UTF-8.") from exc
