from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.database import get_session
from sari_api.adapters.knowledge_embedding import build_knowledge_embedding_provider
from sari_api.adapters.knowledge_queue import KnowledgeQueue, get_knowledge_queue
from sari_api.adapters.knowledge_repository import (
    KnowledgeAccessDeniedError,
    KnowledgeNotFoundError,
    KnowledgeStateConflictError,
    SqlAlchemyKnowledgeRepository,
)
from sari_api.adapters.knowledge_storage import KnowledgeStorage, get_knowledge_storage
from sari_api.adapters.models import (
    AuditEvent,
    KnowledgeDocument,
    KnowledgeIngestionRun,
    KnowledgeSource,
)
from sari_api.api.dependencies import require_permission
from sari_api.core.config import get_settings
from sari_api.core.observability import get_correlation_id
from sari_api.domain.identity import Principal

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])
SUPPORTED_MEDIA_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/x-markdown",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class KnowledgeSourceInput(StrictModel):
    source_key: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{2,119}$")
    name: str = Field(min_length=2, max_length=250)
    description: str | None = Field(default=None, max_length=2000)
    source_type: Literal["manual_upload", "approved_import"] = "manual_upload"
    source_metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeSourceResponse(StrictModel):
    id: UUID
    source_key: str
    name: str
    description: str | None
    source_type: str
    status: str
    source_metadata: dict[str, Any]
    created_at: datetime


class KnowledgeBindingInput(StrictModel):
    domain_key: str = Field(min_length=2, max_length=100)
    agent_key: str = Field(min_length=2, max_length=120)
    knowledge_category: str = Field(min_length=2, max_length=120)


class KnowledgeBindingResponse(StrictModel):
    id: UUID
    source_id: UUID
    domain_key: str
    agent_key: str
    knowledge_category: str
    status: str
    created_at: datetime


class KnowledgeDocumentResponse(StrictModel):
    id: UUID
    source_id: UUID
    title: str
    original_filename: str
    media_type: str
    language: str
    content_sha256: str
    byte_size: int
    source_metadata: dict[str, Any]
    approval_status: str
    ingestion_status: str
    approved_at: datetime | None
    rejected_at: datetime | None
    review_note: str | None
    created_at: datetime


class DocumentReviewInput(StrictModel):
    decision: Literal["approved", "rejected"]
    note: str | None = Field(default=None, max_length=2000)


class KnowledgeIngestionRunResponse(StrictModel):
    id: UUID
    document_id: UUID
    status: str
    extraction_version: str
    chunking_version: str
    embedding_provider: str
    embedding_model: str
    chunk_count: int
    correlation_id: str | None
    error_code: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class DocumentReviewResponse(StrictModel):
    document: KnowledgeDocumentResponse
    ingestion_run: KnowledgeIngestionRunResponse | None


class KnowledgeSearchInput(StrictModel):
    domain_key: str = Field(min_length=2, max_length=100)
    agent_key: str = Field(min_length=2, max_length=120)
    query: str = Field(min_length=3, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)
    minimum_similarity: float = Field(default=0.15, ge=0, le=1)


class CitationResponse(StrictModel):
    source_id: UUID
    source_name: str
    document_id: UUID
    document_title: str
    filename: str
    page_number: int | None
    section_title: str | None
    chunk_index: int
    content_sha256: str


class KnowledgeSearchResult(StrictModel):
    chunk_id: UUID
    content: str
    similarity: float
    citation: CitationResponse


class KnowledgeSearchResponse(StrictModel):
    evidence_status: Literal["sufficient_candidates", "insufficient_evidence"]
    domain_key: str
    agent_key: str
    results: list[KnowledgeSearchResult]


async def repository(session: AsyncSession, principal: Principal) -> SqlAlchemyKnowledgeRepository:
    result = SqlAlchemyKnowledgeRepository(session, principal.tenant_id)
    await result.set_tenant_context()
    return result


def source_response(source: KnowledgeSource) -> KnowledgeSourceResponse:
    return KnowledgeSourceResponse(
        id=source.id,
        source_key=source.source_key,
        name=source.name,
        description=source.description,
        source_type=source.source_type,
        status=source.status,
        source_metadata=source.source_metadata,
        created_at=source.created_at,
    )


def document_response(document: KnowledgeDocument) -> KnowledgeDocumentResponse:
    return KnowledgeDocumentResponse(
        id=document.id,
        source_id=document.source_id,
        title=document.title,
        original_filename=document.original_filename,
        media_type=document.media_type,
        language=document.language,
        content_sha256=document.content_sha256,
        byte_size=document.byte_size,
        source_metadata=document.source_metadata,
        approval_status=document.approval_status,
        ingestion_status=document.ingestion_status,
        approved_at=document.approved_at,
        rejected_at=document.rejected_at,
        review_note=document.review_note,
        created_at=document.created_at,
    )


def ingestion_response(run: KnowledgeIngestionRun) -> KnowledgeIngestionRunResponse:
    return KnowledgeIngestionRunResponse(
        id=run.id,
        document_id=run.document_id,
        status=run.status,
        extraction_version=run.extraction_version,
        chunking_version=run.chunking_version,
        embedding_provider=run.embedding_provider,
        embedding_model=run.embedding_model,
        chunk_count=run.chunk_count,
        correlation_id=run.correlation_id,
        error_code=run.error_code,
        error_message=run.error_message_safe,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
    )


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


@router.post("/sources", response_model=KnowledgeSourceResponse, status_code=201)
async def create_source(
    payload: KnowledgeSourceInput,
    principal: Annotated[Principal, Depends(require_permission("knowledge:manage"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> KnowledgeSourceResponse:
    repo = await repository(session, principal)
    try:
        source = await repo.create_source(**payload.model_dump(), created_by=principal.user_id)
        add_audit(
            session,
            principal,
            action="knowledge.source.created",
            target_type="knowledge_source",
            target_id=source.id,
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Knowledge source key already exists.") from exc
    return source_response(source)


@router.get("/sources", response_model=list[KnowledgeSourceResponse])
async def list_sources(
    principal: Annotated[Principal, Depends(require_permission("knowledge:retrieve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[KnowledgeSourceResponse]:
    repo = await repository(session, principal)
    return [source_response(item) for item in await repo.list_sources()]


@router.post(
    "/sources/{source_id}/bindings",
    response_model=KnowledgeBindingResponse,
    status_code=201,
)
async def create_binding(
    source_id: UUID,
    payload: KnowledgeBindingInput,
    principal: Annotated[Principal, Depends(require_permission("knowledge:manage"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> KnowledgeBindingResponse:
    repo = await repository(session, principal)
    try:
        binding = await repo.create_binding(
            source_id=source_id,
            **payload.model_dump(),
            created_by=principal.user_id,
        )
        add_audit(
            session,
            principal,
            action="knowledge.binding.enabled",
            target_type="knowledge_binding",
            target_id=binding.id,
            details={"agent_key": payload.agent_key, "domain_key": payload.domain_key},
        )
        await session.commit()
    except KnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge source or agent not found.") from exc
    except KnowledgeAccessDeniedError as exc:
        raise HTTPException(
            status_code=403,
            detail="Knowledge retrieval is not enabled for this tenant agent.",
        ) from exc
    except KnowledgeStateConflictError as exc:
        raise HTTPException(status_code=409, detail="Knowledge source is not active.") from exc
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Knowledge binding already exists.") from exc
    return KnowledgeBindingResponse(
        id=binding.id,
        source_id=binding.source_id,
        domain_key=payload.domain_key,
        agent_key=payload.agent_key,
        knowledge_category=binding.knowledge_category,
        status=binding.status,
        created_at=binding.created_at,
    )


@router.get("/sources/{source_id}/bindings", response_model=list[KnowledgeBindingResponse])
async def list_bindings(
    source_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:retrieve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[KnowledgeBindingResponse]:
    repo = await repository(session, principal)
    try:
        rows = await repo.list_bindings(source_id)
    except KnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge source not found.") from exc
    return [
        KnowledgeBindingResponse(
            id=binding.id,
            source_id=binding.source_id,
            domain_key=domain.domain_key,
            agent_key=agent.agent_key,
            knowledge_category=binding.knowledge_category,
            status=binding.status,
            created_at=binding.created_at,
        )
        for binding, domain, agent in rows
    ]


@router.post(
    "/sources/{source_id}/documents",
    response_model=KnowledgeDocumentResponse,
    status_code=201,
)
async def upload_document(
    source_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:manage"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[KnowledgeStorage, Depends(get_knowledge_storage)],
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form(min_length=2, max_length=300)],
    language: Annotated[str, Form(pattern=r"^(en|zh-CN|id)$")] = "en",
    source_metadata_json: Annotated[str, Form(max_length=10000)] = "{}",
) -> KnowledgeDocumentResponse:
    settings = get_settings()
    media_type = (file.content_type or "").split(";", maxsplit=1)[0].lower()
    if media_type not in SUPPORTED_MEDIA_TYPES:
        raise HTTPException(
            status_code=415, detail="Supported document types are PDF, text, and Markdown."
        )
    content = await file.read(settings.knowledge_max_upload_bytes + 1)
    if not content:
        raise HTTPException(status_code=422, detail="Uploaded document is empty.")
    if len(content) > settings.knowledge_max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded document exceeds the size limit.")
    try:
        metadata = json.loads(source_metadata_json)
        if not isinstance(metadata, dict):
            raise TypeError
    except (json.JSONDecodeError, TypeError) as exc:
        raise HTTPException(
            status_code=422, detail="source_metadata_json must be a JSON object."
        ) from exc
    filename = re.sub(r"[^A-Za-z0-9._-]", "_", file.filename or "document")[:255]
    digest = hashlib.sha256(content).hexdigest()
    repo = await repository(session, principal)
    try:
        if await repo.find_document_by_digest(source_id, digest):
            raise HTTPException(
                status_code=409, detail="This document is already uploaded to the source."
            )
        object_key = f"{principal.tenant_id}/{source_id}/{uuid4()}-{filename}"
        await storage.put(object_key, content)
        try:
            document = await repo.create_document(
                source_id=source_id,
                title=title,
                original_filename=filename,
                media_type=media_type,
                language=language,
                object_key=object_key,
                content_sha256=digest,
                byte_size=len(content),
                source_metadata=metadata,
                created_by=principal.user_id,
            )
            add_audit(
                session,
                principal,
                action="knowledge.document.uploaded",
                target_type="knowledge_document",
                target_id=document.id,
                details={"source_id": str(source_id), "content_sha256": digest},
            )
            await session.commit()
        except Exception:
            await storage.delete(object_key)
            raise
    except KnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge source not found.") from exc
    except KnowledgeStateConflictError as exc:
        raise HTTPException(status_code=409, detail="Knowledge source is not active.") from exc
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="This document is already uploaded.") from exc
    return document_response(document)


@router.get("/documents", response_model=list[KnowledgeDocumentResponse])
async def list_documents(
    principal: Annotated[Principal, Depends(require_permission("knowledge:retrieve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    source_id: Annotated[UUID | None, Query()] = None,
) -> list[KnowledgeDocumentResponse]:
    repo = await repository(session, principal)
    return [document_response(item) for item in await repo.list_documents(source_id)]


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentResponse)
async def get_document(
    document_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:retrieve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> KnowledgeDocumentResponse:
    repo = await repository(session, principal)
    try:
        return document_response(await repo.get_document(document_id))
    except KnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge document not found.") from exc


async def enqueue_ingestion(
    session: AsyncSession,
    queue: KnowledgeQueue,
    document: KnowledgeDocument,
    run: KnowledgeIngestionRun,
    principal: Principal,
) -> None:
    await session.commit()
    try:
        await queue.enqueue(
            run.id,
            principal.tenant_id,
            correlation_id=run.correlation_id,
        )
    except Exception as exc:
        repo = await repository(session, principal)
        persistent_run = await repo.get_ingestion_run(run.id)
        persistent_document = await repo.get_document(document.id)
        persistent_run.status = "failed"
        persistent_run.error_code = "queue_unavailable"
        persistent_run.error_message_safe = "Knowledge ingestion could not be queued."
        persistent_document.ingestion_status = "failed"
        await session.commit()
        raise HTTPException(
            status_code=503, detail="Knowledge ingestion queue is unavailable."
        ) from exc


@router.post(
    "/documents/{document_id}/reviews",
    response_model=DocumentReviewResponse,
)
async def review_document(
    document_id: UUID,
    payload: DocumentReviewInput,
    principal: Annotated[Principal, Depends(require_permission("knowledge:manage"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    queue: Annotated[KnowledgeQueue, Depends(get_knowledge_queue)],
) -> DocumentReviewResponse:
    repo = await repository(session, principal)
    settings = get_settings()
    try:
        if payload.decision == "rejected":
            document = await repo.reject_document(
                document_id,
                reviewer_id=principal.user_id,
                review_note=payload.note,
            )
            add_audit(
                session,
                principal,
                action="knowledge.document.rejected",
                target_type="knowledge_document",
                target_id=document.id,
            )
            await session.commit()
            return DocumentReviewResponse(document=document_response(document), ingestion_run=None)
        provider = build_knowledge_embedding_provider(settings)
        document, run = await repo.approve_document(
            document_id,
            reviewer_id=principal.user_id,
            review_note=payload.note,
            embedding_provider=provider.provider_type,
            embedding_model=provider.model_id,
            correlation_id=get_correlation_id(),
        )
        add_audit(
            session,
            principal,
            action="knowledge.document.approved",
            target_type="knowledge_document",
            target_id=document.id,
            details={"ingestion_run_id": str(run.id)},
        )
        await enqueue_ingestion(session, queue, document, run, principal)
        return DocumentReviewResponse(
            document=document_response(document), ingestion_run=ingestion_response(run)
        )
    except KnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge document not found.") from exc
    except KnowledgeAccessDeniedError as exc:
        raise HTTPException(
            status_code=409,
            detail="Document cannot be approved until its source has an enabled agent binding.",
        ) from exc
    except KnowledgeStateConflictError as exc:
        raise HTTPException(status_code=409, detail="Document has already been reviewed.") from exc


@router.post(
    "/documents/{document_id}/ingestion-runs",
    response_model=KnowledgeIngestionRunResponse,
    status_code=202,
)
async def restart_ingestion(
    document_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:manage"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    queue: Annotated[KnowledgeQueue, Depends(get_knowledge_queue)],
) -> KnowledgeIngestionRunResponse:
    repo = await repository(session, principal)
    provider = build_knowledge_embedding_provider(get_settings())
    try:
        document, run = await repo.create_ingestion_run(
            document_id,
            created_by=principal.user_id,
            embedding_provider=provider.provider_type,
            embedding_model=provider.model_id,
            correlation_id=get_correlation_id(),
        )
        add_audit(
            session,
            principal,
            action="knowledge.ingestion.retried",
            target_type="knowledge_ingestion_run",
            target_id=run.id,
            details={"document_id": str(document.id)},
        )
        await enqueue_ingestion(session, queue, document, run, principal)
        return ingestion_response(run)
    except KnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge document not found.") from exc
    except KnowledgeStateConflictError as exc:
        raise HTTPException(
            status_code=409, detail="Document is not eligible for ingestion."
        ) from exc


@router.get("/ingestion-runs/{run_id}", response_model=KnowledgeIngestionRunResponse)
async def get_ingestion_run(
    run_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:retrieve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> KnowledgeIngestionRunResponse:
    repo = await repository(session, principal)
    try:
        return ingestion_response(await repo.get_ingestion_run(run_id))
    except KnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge ingestion run not found.") from exc


@router.post("/retrieval/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    payload: KnowledgeSearchInput,
    principal: Annotated[Principal, Depends(require_permission("knowledge:retrieve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> KnowledgeSearchResponse:
    provider = build_knowledge_embedding_provider(get_settings())
    query_embedding = (await provider.embed([payload.query]))[0]
    repo = await repository(session, principal)
    try:
        rows = await repo.search(
            domain_key=payload.domain_key,
            agent_key=payload.agent_key,
            query_embedding=query_embedding,
            embedding_provider=provider.provider_type,
            embedding_model=provider.model_id,
            limit=payload.limit,
        )
    except KnowledgeNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge domain or agent not found.") from exc
    except KnowledgeAccessDeniedError as exc:
        raise HTTPException(
            status_code=403,
            detail="Knowledge retrieval is not enabled for this tenant agent.",
        ) from exc
    results = []
    for chunk, document, source, distance in rows:
        similarity = max(-1.0, min(1.0, 1.0 - distance))
        if similarity < payload.minimum_similarity:
            continue
        citation = chunk.citation_metadata
        results.append(
            KnowledgeSearchResult(
                chunk_id=chunk.id,
                content=chunk.content,
                similarity=round(similarity, 6),
                citation=CitationResponse(
                    source_id=source.id,
                    source_name=source.name,
                    document_id=document.id,
                    document_title=document.title,
                    filename=document.original_filename,
                    page_number=chunk.page_number,
                    section_title=chunk.section_title,
                    chunk_index=chunk.chunk_index,
                    content_sha256=str(citation.get("content_sha256", chunk.content_sha256)),
                ),
            )
        )
    return KnowledgeSearchResponse(
        evidence_status="sufficient_candidates" if results else "insufficient_evidence",
        domain_key=payload.domain_key,
        agent_key=payload.agent_key,
        results=results,
    )
