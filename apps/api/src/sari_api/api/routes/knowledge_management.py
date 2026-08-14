from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.database import get_session
from sari_api.adapters.enterprise_knowledge_repository import (
    EnterpriseKnowledgeAccessError,
    EnterpriseKnowledgeConcurrencyError,
    EnterpriseKnowledgeNotFoundError,
    EnterpriseKnowledgeRepository,
    EnterpriseKnowledgeStateError,
)
from sari_api.adapters.knowledge_embedding import build_knowledge_embedding_provider
from sari_api.adapters.knowledge_processing_queue import (
    KnowledgeProcessingQueue,
    get_knowledge_processing_queue,
)
from sari_api.adapters.knowledge_storage import KnowledgeStorage, get_knowledge_storage
from sari_api.adapters.models import (
    AuditEvent,
    DomainPackage,
    KnowledgeAuditLog,
    KnowledgeCollection,
    KnowledgeDocumentVersion,
    KnowledgeProcessingRun,
    ManagedKnowledgeDocument,
)
from sari_api.api.dependencies import require_permission
from sari_api.core.config import get_settings
from sari_api.core.observability import get_correlation_id
from sari_api.domain.identity import Principal

router = APIRouter(prefix="/api/v1/knowledge-management", tags=["knowledge-management"])
SUPPORTED_MEDIA_TYPES = {"application/pdf", "text/plain", "text/markdown", "text/x-markdown"}
SUPPORTED_MEDIA_TYPES.add("application/vnd.openxmlformats-officedocument.wordprocessingml.document")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CollectionInput(StrictModel):
    domain_key: str = Field(min_length=2, max_length=100)
    collection_key: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{2,119}$")
    name: str = Field(min_length=2, max_length=250)
    description: str | None = Field(default=None, max_length=2000)
    collection_metadata: dict[str, Any] = Field(default_factory=dict)


class CollectionResponse(StrictModel):
    id: UUID
    domain_key: str
    collection_key: str
    name: str
    description: str | None
    status: str
    collection_metadata: dict[str, Any]
    document_count: int
    created_at: datetime
    updated_at: datetime


class VersionResponse(StrictModel):
    id: UUID
    version_number: int
    original_filename: str
    media_type: str
    content_sha256: str
    byte_size: int
    version_metadata: dict[str, Any]
    status: str
    review_status: str
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    review_note: str | None
    restored_from_version_id: UUID | None
    created_from_action: str
    created_by: UUID
    created_at: datetime


class BindingResponse(StrictModel):
    id: UUID
    agent_key: str
    status: str
    created_by: UUID
    created_at: datetime
    updated_by: UUID | None
    updated_at: datetime


class DocumentResponse(StrictModel):
    id: UUID
    tenant_id: UUID
    domain_key: str
    agent_id: UUID | None
    collection_id: UUID
    collection_name: str
    title: str
    document_type: str
    language: str
    lifecycle_status: str
    approval_status: str
    processing_status: str
    record_version: int
    current_version_number: int
    current_version_id: UUID | None
    published_version_id: UUID | None
    active_version_id: UUID | None
    document_metadata: dict[str, Any]
    approved_by: UUID | None
    approved_at: datetime | None
    review_note: str | None
    created_by: UUID
    updated_by: UUID | None
    published_by: UUID | None
    published_at: datetime | None
    archived_by: UUID | None
    archived_at: datetime | None
    archive_reason: str | None
    restore_reason: str | None
    created_at: datetime
    updated_at: datetime
    current_version: VersionResponse | None = None
    bindings: list[BindingResponse] = Field(default_factory=list)


class ReviewInput(StrictModel):
    decision: Literal["approved", "rejected"]
    note: str | None = Field(default=None, max_length=2000)


class BindInput(StrictModel):
    agent_key: str = Field(min_length=2, max_length=120)


class MetadataUpdateInput(StrictModel):
    title: str | None = Field(default=None, min_length=2, max_length=300)
    document_type: str | None = Field(default=None, min_length=2, max_length=80)
    language: Literal["en", "zh-CN", "id"] | None = None
    document_metadata: dict[str, Any] | None = None


class ReasonInput(StrictModel):
    reason: str = Field(min_length=3, max_length=2000)


class BindingUpdateInput(StrictModel):
    status: Literal["enabled", "disabled"]
    reason: str = Field(min_length=3, max_length=1000)


class AuditLogResponse(StrictModel):
    id: UUID
    document_id: UUID
    document_version_id: UUID | None
    actor_user_id: UUID
    actor_display_name: str
    action: str
    before_metadata: dict[str, Any]
    after_metadata: dict[str, Any]
    details: dict[str, Any]
    correlation_id: str | None
    created_at: datetime


class ProcessingRunResponse(StrictModel):
    id: UUID
    document_id: UUID
    document_version_id: UUID
    status: str
    extractor_version: str
    chunking_version: str
    chunk_size: int
    chunk_overlap: int
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    chunk_count: int
    correlation_id: str | None
    error_code: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


def add_audit(
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


def governance_snapshot(
    document: ManagedKnowledgeDocument,
    version: KnowledgeDocumentVersion | None,
) -> dict[str, Any]:
    return {
        "title": document.title,
        "document_type": document.document_type,
        "language": document.language,
        "lifecycle_status": document.lifecycle_status,
        "approval_status": document.approval_status,
        "processing_status": document.processing_status,
        "record_version": document.version,
        "current_version_number": document.current_version_number,
        "current_version_id": str(document.current_version_id)
        if document.current_version_id
        else None,
        "published_version_id": str(document.published_version_id)
        if document.published_version_id
        else None,
        "active_version_id": str(document.active_version_id)
        if document.active_version_id
        else None,
        "document_metadata": document.document_metadata,
        "version_id": str(version.id) if version else None,
        "version_number": version.version_number if version else None,
        "version_status": version.status if version else None,
        "version_review_status": version.review_status if version else None,
        "content_sha256": version.content_sha256 if version else None,
    }


def add_knowledge_audit(
    session: AsyncSession,
    principal: Principal,
    *,
    document_id: UUID,
    document_version_id: UUID | None,
    action: str,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    session.add(
        KnowledgeAuditLog(
            tenant_id=principal.tenant_id,
            document_id=document_id,
            document_version_id=document_version_id,
            actor_user_id=principal.user_id,
            action=action,
            before_metadata=before or {},
            after_metadata=after or {},
            details=details or {},
            correlation_id=get_correlation_id(),
        )
    )


def parse_if_match(value: str | None) -> int:
    if value is None:
        raise HTTPException(status_code=428, detail="If-Match is required.")
    normalized = value.strip().removeprefix("W/").strip('"')
    try:
        result = int(normalized)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="If-Match must contain a record version."
        ) from exc
    if result < 1:
        raise HTTPException(status_code=400, detail="If-Match must contain a record version.")
    return result


async def repository(session: AsyncSession, principal: Principal) -> EnterpriseKnowledgeRepository:
    result = EnterpriseKnowledgeRepository(session, principal.tenant_id)
    await result.set_tenant_context()
    return result


def collection_response(
    collection: KnowledgeCollection, domain: DomainPackage, document_count: int = 0
) -> CollectionResponse:
    return CollectionResponse(
        id=collection.id,
        domain_key=domain.domain_key,
        collection_key=collection.collection_key,
        name=collection.name,
        description=collection.description,
        status=collection.status,
        collection_metadata=collection.collection_metadata,
        document_count=document_count,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


def version_response(version: KnowledgeDocumentVersion) -> VersionResponse:
    return VersionResponse(
        id=version.id,
        version_number=version.version_number,
        original_filename=version.original_filename,
        media_type=version.media_type,
        content_sha256=version.content_sha256,
        byte_size=version.byte_size,
        version_metadata=version.version_metadata,
        status=version.status,
        review_status=version.review_status,
        reviewed_by=version.reviewed_by,
        reviewed_at=version.reviewed_at,
        review_note=version.review_note,
        restored_from_version_id=version.restored_from_version_id,
        created_from_action=version.created_from_action,
        created_by=version.created_by,
        created_at=version.created_at,
    )


def document_response(
    document: ManagedKnowledgeDocument,
    collection: KnowledgeCollection,
    domain: DomainPackage,
    *,
    version: KnowledgeDocumentVersion | None = None,
    bindings: list[BindingResponse] | None = None,
) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        tenant_id=document.tenant_id,
        domain_key=domain.domain_key,
        agent_id=document.agent_id,
        collection_id=document.collection_id,
        collection_name=collection.name,
        title=document.title,
        document_type=document.document_type,
        language=document.language,
        lifecycle_status=document.lifecycle_status,
        approval_status=document.approval_status,
        processing_status=document.processing_status,
        record_version=document.version,
        current_version_number=document.current_version_number,
        current_version_id=document.current_version_id,
        published_version_id=document.published_version_id,
        active_version_id=document.active_version_id,
        document_metadata=document.document_metadata,
        approved_by=document.approved_by,
        approved_at=document.approved_at,
        review_note=document.review_note,
        created_by=document.created_by,
        updated_by=document.updated_by,
        published_by=document.published_by,
        published_at=document.published_at,
        archived_by=document.archived_by,
        archived_at=document.archived_at,
        archive_reason=document.archive_reason,
        restore_reason=document.restore_reason,
        created_at=document.created_at,
        updated_at=document.updated_at,
        current_version=version_response(version) if version else None,
        bindings=bindings or [],
    )


def processing_response(run: KnowledgeProcessingRun) -> ProcessingRunResponse:
    return ProcessingRunResponse(
        id=run.id,
        document_id=run.document_id,
        document_version_id=run.document_version_id,
        status=run.status,
        extractor_version=run.extractor_version,
        chunking_version=run.chunking_version,
        chunk_size=run.chunk_size,
        chunk_overlap=run.chunk_overlap,
        embedding_provider=run.embedding_provider,
        embedding_model=run.embedding_model,
        embedding_dimensions=run.embedding_dimensions,
        chunk_count=run.chunk_count,
        correlation_id=run.correlation_id,
        error_code=run.error_code,
        error_message=run.error_message_safe,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
    )


def binding_response(binding: Any, agent_key: str) -> BindingResponse:
    return BindingResponse(
        id=binding.id,
        agent_key=agent_key,
        status=binding.status,
        created_by=binding.created_by,
        created_at=binding.created_at,
        updated_by=binding.updated_by,
        updated_at=binding.updated_at,
    )


@router.post("/collections", response_model=CollectionResponse, status_code=201)
async def create_collection(
    payload: CollectionInput,
    principal: Annotated[Principal, Depends(require_permission("knowledge:upload"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CollectionResponse:
    repo = await repository(session, principal)
    try:
        collection, domain = await repo.create_collection(
            **payload.model_dump(), created_by=principal.user_id
        )
        add_audit(
            session,
            principal,
            action="knowledge.collection.created",
            target_type="knowledge_collection",
            target_id=collection.id,
            details={"domain_key": domain.domain_key},
        )
        await session.commit()
    except EnterpriseKnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Domain is not registered.") from exc
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Collection key already exists.") from exc
    return collection_response(collection, domain)


@router.get("/collections", response_model=list[CollectionResponse])
async def list_collections(
    principal: Annotated[Principal, Depends(require_permission("knowledge:retrieve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    domain_key: Annotated[str | None, Query(max_length=100)] = None,
    search: Annotated[str | None, Query(max_length=200)] = None,
) -> list[CollectionResponse]:
    repo = await repository(session, principal)
    return [
        collection_response(collection, domain, count)
        for collection, domain, count in await repo.list_collections(
            domain_key=domain_key, search=search
        )
    ]


@router.post(
    "/collections/{collection_id}/documents", response_model=DocumentResponse, status_code=201
)
async def upload_document(
    collection_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:upload"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[KnowledgeStorage, Depends(get_knowledge_storage)],
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form(min_length=2, max_length=300)],
    document_type: Annotated[str, Form(min_length=2, max_length=80)],
    language: Annotated[str, Form(pattern=r"^(en|zh-CN|id)$")] = "en",
    document_metadata_json: Annotated[str, Form(max_length=10000)] = "{}",
) -> DocumentResponse:
    settings = get_settings()
    media_type = (file.content_type or "").split(";", maxsplit=1)[0].lower()
    if media_type not in SUPPORTED_MEDIA_TYPES:
        raise HTTPException(
            status_code=415, detail="Supported types are PDF, DOCX, text, and Markdown."
        )
    content = await file.read(settings.knowledge_max_upload_bytes + 1)
    if not content:
        raise HTTPException(status_code=422, detail="Uploaded document is empty.")
    if len(content) > settings.knowledge_max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded document exceeds the size limit.")
    try:
        metadata = json.loads(document_metadata_json)
        if not isinstance(metadata, dict):
            raise TypeError
    except (json.JSONDecodeError, TypeError) as exc:
        raise HTTPException(
            status_code=422, detail="Document metadata must be a JSON object."
        ) from exc
    filename = re.sub(r"[^A-Za-z0-9._-]", "_", file.filename or "document")[:255]
    digest = hashlib.sha256(content).hexdigest()
    object_key = f"{principal.tenant_id}/managed/{collection_id}/{uuid4()}-{filename}"
    repo = await repository(session, principal)
    try:
        await storage.put(object_key, content)
        try:
            document, version = await repo.create_document(
                collection_id=collection_id,
                title=title,
                document_type=document_type,
                language=language,
                original_filename=filename,
                media_type=media_type,
                object_key=object_key,
                content_sha256=digest,
                byte_size=len(content),
                document_metadata=metadata,
                created_by=principal.user_id,
            )
            collection, domain = await repo.get_collection(collection_id)
            add_audit(
                session,
                principal,
                action="knowledge.document.uploaded",
                target_type="managed_knowledge_document",
                target_id=document.id,
                details={"version": 1, "content_sha256": digest},
            )
            add_knowledge_audit(
                session,
                principal,
                document_id=document.id,
                document_version_id=version.id,
                action="upload",
                after=governance_snapshot(document, version),
                details={"filename": filename, "byte_size": len(content)},
            )
            await session.flush()
            await session.refresh(document)
            await session.commit()
        except Exception:
            await storage.delete(object_key)
            raise
    except EnterpriseKnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge collection not found.") from exc
    except EnterpriseKnowledgeStateError as exc:
        raise HTTPException(status_code=409, detail="Knowledge collection is archived.") from exc
    return document_response(document, collection, domain, version=version)


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(
    principal: Annotated[Principal, Depends(require_permission("knowledge:retrieve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    collection_id: Annotated[UUID | None, Query()] = None,
    domain_key: Annotated[str | None, Query(max_length=100)] = None,
    agent_key: Annotated[str | None, Query(max_length=120)] = None,
    lifecycle_status: Annotated[str | None, Query(max_length=20)] = None,
    search: Annotated[str | None, Query(max_length=200)] = None,
) -> list[DocumentResponse]:
    repo = await repository(session, principal)
    rows = await repo.list_documents(
        collection_id=collection_id,
        domain_key=domain_key,
        agent_key=agent_key,
        lifecycle_status=lifecycle_status,
        search=search,
    )
    return [
        document_response(document, collection, domain) for document, collection, domain in rows
    ]


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:retrieve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DocumentResponse:
    repo = await repository(session, principal)
    try:
        document, collection, domain = await repo.get_document(document_id)
        version = await repo.current_version(document)
        bindings = [
            binding_response(binding, agent.agent_key)
            for binding, agent in await repo.list_bindings(document_id)
        ]
    except EnterpriseKnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge document not found.") from exc
    return document_response(document, collection, domain, version=version, bindings=bindings)


@router.patch("/documents/{document_id}", response_model=DocumentResponse)
async def update_document_metadata(
    document_id: UUID,
    payload: MetadataUpdateInput,
    principal: Annotated[Principal, Depends(require_permission("knowledge:edit"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> DocumentResponse:
    if not payload.model_fields_set:
        raise HTTPException(status_code=422, detail="Provide at least one metadata field.")
    repo = await repository(session, principal)
    try:
        existing, _, _ = await repo.get_document(document_id)
        existing_version = await repo.current_version(existing)
        before = governance_snapshot(existing, existing_version)
        document, version = await repo.update_document_metadata(
            document_id,
            expected_version=parse_if_match(if_match),
            actor_id=principal.user_id,
            **payload.model_dump(),
        )
        _, collection, domain = await repo.get_document(document_id)
        add_knowledge_audit(
            session,
            principal,
            document_id=document.id,
            document_version_id=version.id,
            action="metadata_update",
            before=before,
            after=governance_snapshot(document, version),
            details={"changed_fields": sorted(payload.model_fields_set)},
        )
        await session.flush()
        await session.refresh(document)
        await session.commit()
    except EnterpriseKnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge document not found.") from exc
    except EnterpriseKnowledgeConcurrencyError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=412, detail="Document was changed by another user."
        ) from exc
    except EnterpriseKnowledgeStateError as exc:
        raise HTTPException(
            status_code=409, detail="Archive an active document before editing its metadata."
        ) from exc
    return document_response(document, collection, domain, version=version)


@router.get("/documents/{document_id}/versions", response_model=list[VersionResponse])
async def list_document_versions(
    document_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:retrieve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[VersionResponse]:
    repo = await repository(session, principal)
    try:
        return [version_response(item) for item in await repo.list_versions(document_id)]
    except EnterpriseKnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge document not found.") from exc


@router.get("/documents/{document_id}/versions/{version_id}", response_model=VersionResponse)
async def get_document_version(
    document_id: UUID,
    version_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:retrieve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> VersionResponse:
    repo = await repository(session, principal)
    try:
        return version_response(await repo.get_version(document_id, version_id))
    except EnterpriseKnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge version not found.") from exc


@router.post("/documents/{document_id}/versions", response_model=DocumentResponse, status_code=201)
async def upload_document_version(
    document_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:upload"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[KnowledgeStorage, Depends(get_knowledge_storage)],
    file: Annotated[UploadFile, File()],
    version_metadata_json: Annotated[str, Form(max_length=10000)] = "{}",
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> DocumentResponse:
    settings = get_settings()
    media_type = (file.content_type or "").split(";", maxsplit=1)[0].lower()
    if media_type not in SUPPORTED_MEDIA_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported knowledge document type.")
    content = await file.read(settings.knowledge_max_upload_bytes + 1)
    if not content:
        raise HTTPException(status_code=422, detail="Uploaded document is empty.")
    if len(content) > settings.knowledge_max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded document exceeds the size limit.")
    try:
        metadata = json.loads(version_metadata_json)
        if not isinstance(metadata, dict):
            raise TypeError
    except (json.JSONDecodeError, TypeError) as exc:
        raise HTTPException(
            status_code=422, detail="Version metadata must be a JSON object."
        ) from exc
    filename = re.sub(r"[^A-Za-z0-9._-]", "_", file.filename or "document")[:255]
    digest = hashlib.sha256(content).hexdigest()
    object_key = f"{principal.tenant_id}/managed/{document_id}/{uuid4()}-{filename}"
    repo = await repository(session, principal)
    try:
        before_document, _, _ = await repo.get_document(document_id)
        before_version = await repo.current_version(before_document)
        before = governance_snapshot(before_document, before_version)
        await storage.put(object_key, content)
        try:
            document, version = await repo.create_new_version(
                document_id,
                expected_version=parse_if_match(if_match),
                actor_id=principal.user_id,
                original_filename=filename,
                media_type=media_type,
                object_key=object_key,
                content_sha256=digest,
                byte_size=len(content),
                version_metadata=metadata,
            )
            _, collection, domain = await repo.get_document(document_id)
            add_knowledge_audit(
                session,
                principal,
                document_id=document.id,
                document_version_id=version.id,
                action="version_creation",
                before=before,
                after=governance_snapshot(document, version),
                details={"filename": filename, "created_from_action": "upload"},
            )
            await session.flush()
            await session.refresh(document)
            await session.commit()
        except Exception:
            await storage.delete(object_key)
            raise
    except EnterpriseKnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge document not found.") from exc
    except EnterpriseKnowledgeConcurrencyError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=412, detail="Document was changed by another user."
        ) from exc
    except EnterpriseKnowledgeStateError as exc:
        raise HTTPException(
            status_code=409, detail="Document cannot accept a new version."
        ) from exc
    return document_response(document, collection, domain, version=version)


@router.post(
    "/documents/{document_id}/versions/{version_id}/rollback",
    response_model=DocumentResponse,
    status_code=201,
)
async def rollback_document_version(
    document_id: UUID,
    version_id: UUID,
    payload: ReasonInput,
    principal: Annotated[Principal, Depends(require_permission("knowledge:restore"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[KnowledgeStorage, Depends(get_knowledge_storage)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> DocumentResponse:
    repo = await repository(session, principal)
    object_key: str | None = None
    try:
        document_before, _, _ = await repo.get_document(document_id)
        current_before = await repo.current_version(document_before)
        source = await repo.get_version(document_id, version_id)
        before = governance_snapshot(document_before, current_before)
        content = await storage.get(source.object_key)
        if hashlib.sha256(content).hexdigest() != source.content_sha256:
            raise HTTPException(status_code=409, detail="Historical object integrity check failed.")
        object_key = (
            f"{principal.tenant_id}/managed/{document_id}/{uuid4()}-rollback-"
            f"{source.original_filename}"
        )
        await storage.put(object_key, content)
        try:
            document, version = await repo.create_new_version(
                document_id,
                expected_version=parse_if_match(if_match),
                actor_id=principal.user_id,
                original_filename=source.original_filename,
                media_type=source.media_type,
                object_key=object_key,
                content_sha256=source.content_sha256,
                byte_size=source.byte_size,
                version_metadata={**source.version_metadata, "rollback_reason": payload.reason},
                restored_from_version_id=source.id,
            )
            _, collection, domain = await repo.get_document(document_id)
            add_knowledge_audit(
                session,
                principal,
                document_id=document.id,
                document_version_id=version.id,
                action="rollback",
                before=before,
                after=governance_snapshot(document, version),
                details={"source_version_id": str(source.id), "reason": payload.reason},
            )
            await session.flush()
            await session.refresh(document)
            await session.commit()
        except Exception:
            await storage.delete(object_key)
            raise
    except EnterpriseKnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge version not found.") from exc
    except EnterpriseKnowledgeConcurrencyError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=412, detail="Document was changed by another user."
        ) from exc
    return document_response(document, collection, domain, version=version)


async def apply_transition(
    document_id: UUID,
    principal: Principal,
    session: AsyncSession,
    *,
    transition: Literal["submit_review", "publish", "activate", "archive", "restore"],
    reason: str | None = None,
) -> DocumentResponse:
    repo = await repository(session, principal)
    try:
        before_document, _, _ = await repo.get_document(document_id)
        before_version = await repo.current_version(before_document)
        before = governance_snapshot(before_document, before_version)
        if transition == "submit_review":
            document, version = await repo.submit_for_review(
                document_id, actor_id=principal.user_id
            )
        elif transition == "publish":
            document, version = await repo.publish_document(
                document_id, publisher_id=principal.user_id
            )
        elif transition == "activate":
            document, version = await repo.activate_document(
                document_id, publisher_id=principal.user_id
            )
        elif transition == "restore":
            if reason is None:
                raise EnterpriseKnowledgeStateError
            document, version = await repo.restore_document(
                document_id, actor_id=principal.user_id, reason=reason
            )
        else:
            document, version = await repo.archive_document(
                document_id, actor_id=principal.user_id, reason=reason
            )
        _, collection, domain = await repo.get_document(document_id)
        add_audit(
            session,
            principal,
            action=f"knowledge.document.{transition}",
            target_type="managed_knowledge_document",
            target_id=document.id,
        )
        add_knowledge_audit(
            session,
            principal,
            document_id=document.id,
            document_version_id=version.id,
            action=transition,
            before=before,
            after=governance_snapshot(document, version),
            details={"reason": reason} if reason else {},
        )
        await session.flush()
        await session.refresh(document)
        await session.commit()
    except EnterpriseKnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge document not found.") from exc
    except EnterpriseKnowledgeAccessError as exc:
        raise HTTPException(
            status_code=409, detail="Bind the document to an agent before activation."
        ) from exc
    except EnterpriseKnowledgeStateError as exc:
        raise HTTPException(
            status_code=409, detail="Invalid document lifecycle transition."
        ) from exc
    return document_response(document, collection, domain)


@router.post("/documents/{document_id}/submit-review", response_model=DocumentResponse)
async def submit_for_review(
    document_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:submit_review"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DocumentResponse:
    return await apply_transition(document_id, principal, session, transition="submit_review")


@router.post("/documents/{document_id}/approval", response_model=DocumentResponse)
async def approve_or_reject(
    document_id: UUID,
    payload: ReviewInput,
    principal: Annotated[Principal, Depends(require_permission("knowledge:approve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DocumentResponse:
    repo = await repository(session, principal)
    try:
        before_document, _, _ = await repo.get_document(document_id)
        before_version = await repo.current_version(before_document)
        before = governance_snapshot(before_document, before_version)
        document, _ = await repo.review_document(
            document_id,
            reviewer_id=principal.user_id,
            decision=payload.decision,
            note=payload.note,
        )
        _, collection, domain = await repo.get_document(document_id)
        version = await repo.current_version(document)
        add_audit(
            session,
            principal,
            action=f"knowledge.document.{payload.decision}",
            target_type="managed_knowledge_document",
            target_id=document.id,
            details={"note": payload.note},
        )
        add_knowledge_audit(
            session,
            principal,
            document_id=document.id,
            document_version_id=version.id,
            action="approval" if payload.decision == "approved" else "rejection",
            before=before,
            after=governance_snapshot(document, version),
            details={"note": payload.note},
        )
        await session.flush()
        await session.refresh(document)
        await session.commit()
    except EnterpriseKnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge document not found.") from exc
    except EnterpriseKnowledgeStateError as exc:
        raise HTTPException(status_code=409, detail="Document is not awaiting review.") from exc
    return document_response(document, collection, domain)


@router.post("/documents/{document_id}/publish", response_model=DocumentResponse)
async def publish_document(
    document_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:publish"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DocumentResponse:
    return await apply_transition(document_id, principal, session, transition="publish")


@router.post("/documents/{document_id}/activate", response_model=DocumentResponse)
async def activate_document(
    document_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:publish"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DocumentResponse:
    return await apply_transition(document_id, principal, session, transition="activate")


@router.post("/documents/{document_id}/archive", response_model=DocumentResponse)
async def archive_document(
    document_id: UUID,
    payload: ReasonInput,
    principal: Annotated[Principal, Depends(require_permission("knowledge:archive"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DocumentResponse:
    return await apply_transition(
        document_id, principal, session, transition="archive", reason=payload.reason
    )


@router.post("/documents/{document_id}/restore", response_model=DocumentResponse)
async def restore_document(
    document_id: UUID,
    payload: ReasonInput,
    principal: Annotated[Principal, Depends(require_permission("knowledge:restore"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DocumentResponse:
    return await apply_transition(
        document_id, principal, session, transition="restore", reason=payload.reason
    )


@router.post("/documents/{document_id}/bindings", response_model=BindingResponse, status_code=201)
async def bind_document(
    document_id: UUID,
    payload: BindInput,
    principal: Annotated[Principal, Depends(require_permission("knowledge:edit"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BindingResponse:
    repo = await repository(session, principal)
    try:
        binding, agent = await repo.bind_document(
            document_id, agent_key=payload.agent_key, created_by=principal.user_id
        )
        add_audit(
            session,
            principal,
            action="knowledge.document.agent_bound",
            target_type="managed_knowledge_document",
            target_id=document_id,
            details={"agent_key": agent.agent_key},
        )
        add_knowledge_audit(
            session,
            principal,
            document_id=document_id,
            document_version_id=None,
            action="agent_binding_enabled",
            after={"binding_id": str(binding.id), "status": binding.status},
            details={"agent_key": agent.agent_key},
        )
        await session.commit()
    except EnterpriseKnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document or agent not found.") from exc
    except EnterpriseKnowledgeAccessError as exc:
        raise HTTPException(status_code=403, detail="Agent belongs to another domain.") from exc
    except EnterpriseKnowledgeStateError as exc:
        raise HTTPException(status_code=409, detail="Agent binding is already enabled.") from exc
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="Document is already bound to this agent."
        ) from exc
    return binding_response(binding, agent.agent_key)


@router.patch("/documents/{document_id}/bindings/{binding_id}", response_model=BindingResponse)
async def update_document_binding(
    document_id: UUID,
    binding_id: UUID,
    payload: BindingUpdateInput,
    principal: Annotated[Principal, Depends(require_permission("knowledge:edit"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BindingResponse:
    repo = await repository(session, principal)
    try:
        existing = [
            (binding, agent)
            for binding, agent in await repo.list_bindings(document_id)
            if binding.id == binding_id
        ]
        if not existing:
            raise EnterpriseKnowledgeNotFoundError
        before_binding, _ = existing[0]
        before = {"binding_id": str(before_binding.id), "status": before_binding.status}
        binding, agent, _ = await repo.update_binding(
            document_id,
            binding_id,
            status=payload.status,
            actor_id=principal.user_id,
        )
        add_knowledge_audit(
            session,
            principal,
            document_id=document_id,
            document_version_id=None,
            action=f"agent_binding_{payload.status}",
            before=before,
            after={"binding_id": str(binding.id), "status": binding.status},
            details={"agent_key": agent.agent_key, "reason": payload.reason},
        )
        await session.commit()
    except EnterpriseKnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge binding not found.") from exc
    return binding_response(binding, agent.agent_key)


@router.post(
    "/documents/{document_id}/processing-runs",
    response_model=ProcessingRunResponse,
    status_code=202,
)
async def create_processing_run(
    document_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:process"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    queue: Annotated[KnowledgeProcessingQueue, Depends(get_knowledge_processing_queue)],
) -> ProcessingRunResponse:
    settings = get_settings()
    embedding_provider = build_knowledge_embedding_provider(settings)
    repo = await repository(session, principal)
    try:
        document, run = await repo.create_processing_run(
            document_id,
            created_by=principal.user_id,
            chunk_size=settings.knowledge_chunk_size,
            chunk_overlap=settings.knowledge_chunk_overlap,
            embedding_provider=embedding_provider.provider_type,
            embedding_model=embedding_provider.model_id,
            embedding_dimensions=embedding_provider.dimensions,
            correlation_id=get_correlation_id(),
        )
        add_audit(
            session,
            principal,
            action="knowledge.document.processing_requested",
            target_type="managed_knowledge_document",
            target_id=document.id,
            details={"processing_run_id": str(run.id)},
        )
        version = await repo.current_version(document)
        add_knowledge_audit(
            session,
            principal,
            document_id=document.id,
            document_version_id=version.id,
            action="processing_requested",
            after=governance_snapshot(document, version),
            details={"processing_run_id": str(run.id)},
        )
        await session.commit()
        try:
            await queue.enqueue(
                run.id,
                principal.tenant_id,
                correlation_id=run.correlation_id,
            )
        except Exception as exc:
            await repo.set_tenant_context()
            persistent_run = await repo.get_processing_run(run.id)
            persistent_document, _, _ = await repo.get_document(document.id)
            persistent_run.status = "failed"
            persistent_run.error_code = "queue_unavailable"
            persistent_run.error_message_safe = "Knowledge processing could not be queued."
            persistent_run.completed_at = datetime.now(UTC)
            persistent_document.processing_status = "failed"
            await session.commit()
            raise HTTPException(
                status_code=503, detail="Knowledge processing queue is unavailable."
            ) from exc
    except EnterpriseKnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge document not found.") from exc
    except EnterpriseKnowledgeAccessError as exc:
        raise HTTPException(
            status_code=409, detail="Bind the document to an agent before processing."
        ) from exc
    except EnterpriseKnowledgeStateError as exc:
        raise HTTPException(
            status_code=409,
            detail="Only approved or active documents without a running job can be processed.",
        ) from exc
    return processing_response(run)


@router.get("/processing-runs/{run_id}", response_model=ProcessingRunResponse)
async def get_processing_run(
    run_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:retrieve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProcessingRunResponse:
    repo = await repository(session, principal)
    try:
        return processing_response(await repo.get_processing_run(run_id))
    except EnterpriseKnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge processing run not found.") from exc


@router.get("/documents/{document_id}/audit-events", response_model=list[AuditLogResponse])
async def list_document_audit_events(
    document_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:audit_read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[AuditLogResponse]:
    repo = await repository(session, principal)
    try:
        rows = await repo.list_audit_logs(document_id)
    except EnterpriseKnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge document not found.") from exc
    return [
        AuditLogResponse(
            id=log.id,
            document_id=log.document_id,
            document_version_id=log.document_version_id,
            actor_user_id=log.actor_user_id,
            actor_display_name=user.display_name,
            action=log.action,
            before_metadata=log.before_metadata,
            after_metadata=log.after_metadata,
            details=log.details,
            correlation_id=log.correlation_id,
            created_at=log.created_at,
        )
        for log, user in rows
    ]
