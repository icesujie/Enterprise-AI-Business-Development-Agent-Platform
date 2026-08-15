from __future__ import annotations

import logging
import time
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.database import get_session
from sari_api.adapters.knowledge_embedding import build_knowledge_embedding_provider
from sari_api.adapters.managed_knowledge_retrieval import (
    ManagedKnowledgeRetrievalDeniedError,
    ManagedKnowledgeRetrievalRepository,
)
from sari_api.api.dependencies import require_permission
from sari_api.core.config import get_settings
from sari_api.core.observability import get_correlation_id
from sari_api.domain.identity import Principal

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge-retrieval"])

EvidenceStatus = Literal["sufficient_candidates", "insufficient_evidence"]
DecisionReason = Literal[
    "meets_minimum_evidence",
    "below_similarity_threshold",
    "insufficient_result_count",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ManagedKnowledgeSearchInput(StrictModel):
    tenant_id: UUID
    agent_id: UUID
    query: str = Field(min_length=3, max_length=2000)
    language: Literal["en", "zh-CN", "id"] = "en"
    top_k: int = Field(default=5, ge=1, le=20)
    include_diagnostics: bool = False


class ManagedKnowledgeCitation(StrictModel):
    document_id: UUID
    document_name: str
    document_version_id: UUID
    document_version: int
    chunk_id: UUID
    page_number: int | None
    section: str | None
    content_sha256: str


class ManagedKnowledgeSearchResult(StrictModel):
    document_name: str
    document_version: int
    chunk_content: str
    page_number: int | None
    section: str | None
    metadata: dict[str, Any]
    similarity_score: float
    citation: ManagedKnowledgeCitation


class ManagedKnowledgeSearchResponse(StrictModel):
    evidence_status: EvidenceStatus
    tenant_id: UUID
    agent_id: UUID
    language: str
    correlation_id: str
    duration_ms: float
    similarity_threshold: float
    minimum_evidence_count: int
    decision_reason: DecisionReason
    results: list[ManagedKnowledgeSearchResult]
    below_threshold_results: list[ManagedKnowledgeSearchResult]


@router.post("/search", response_model=ManagedKnowledgeSearchResponse)
async def search_managed_knowledge(
    payload: ManagedKnowledgeSearchInput,
    principal: Annotated[Principal, Depends(require_permission("knowledge:retrieve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ManagedKnowledgeSearchResponse:
    started_at = time.perf_counter()
    if payload.tenant_id != principal.tenant_id:
        raise HTTPException(status_code=403, detail="Workspace access denied.")

    repository = ManagedKnowledgeRetrievalRepository(session, principal.tenant_id)
    await repository.set_tenant_context()
    try:
        await repository.ensure_agent_retrieval_enabled(payload.agent_id)
    except ManagedKnowledgeRetrievalDeniedError as exc:
        raise HTTPException(
            status_code=403,
            detail="Knowledge retrieval is not enabled for this tenant agent.",
        ) from exc

    settings = get_settings()
    provider = build_knowledge_embedding_provider(settings)
    query_embedding = (await provider.embed([payload.query]))[0]
    try:
        diagnostic_count = (
            settings.knowledge_retrieval_diagnostic_candidates if payload.include_diagnostics else 0
        )
        candidate_limit = min(20, max(payload.top_k, diagnostic_count))
        hits = await repository.search(
            agent_id=payload.agent_id,
            query_embedding=query_embedding,
            embedding_provider=provider.provider_type,
            embedding_model=provider.model_id,
            language=payload.language,
            top_k=candidate_limit,
        )
    except ManagedKnowledgeRetrievalDeniedError as exc:
        raise HTTPException(
            status_code=403,
            detail="Knowledge retrieval is not enabled for this tenant agent.",
        ) from exc

    candidates = []
    for hit in hits:
        similarity = round(max(-1.0, min(1.0, 1.0 - hit.distance)), 6)
        chunk = hit.chunk
        document = hit.document
        version = hit.version
        metadata = {
            **chunk.source_metadata,
            "document_type": chunk.document_type,
            "language": chunk.language,
            "chunk_index": chunk.chunk_index,
        }
        candidates.append(
            ManagedKnowledgeSearchResult(
                document_name=document.title,
                document_version=version.version_number,
                chunk_content=chunk.content,
                page_number=chunk.page_number,
                section=chunk.section_title,
                metadata=metadata,
                similarity_score=similarity,
                citation=ManagedKnowledgeCitation(
                    document_id=document.id,
                    document_name=document.title,
                    document_version_id=version.id,
                    document_version=version.version_number,
                    chunk_id=chunk.id,
                    page_number=chunk.page_number,
                    section=chunk.section_title,
                    content_sha256=chunk.content_sha256,
                ),
            )
        )
    qualified = [
        result
        for result in candidates
        if result.similarity_score >= settings.knowledge_retrieval_min_similarity
    ][: payload.top_k]
    below_threshold = (
        [
            result
            for result in candidates
            if result.similarity_score < settings.knowledge_retrieval_min_similarity
        ][: settings.knowledge_retrieval_diagnostic_candidates]
        if payload.include_diagnostics
        else []
    )
    sufficient = len(qualified) >= settings.knowledge_retrieval_min_evidence_count
    results = qualified if sufficient else []
    reason: DecisionReason
    if sufficient:
        reason = "meets_minimum_evidence"
    elif qualified:
        reason = "insufficient_result_count"
    else:
        reason = "below_similarity_threshold"
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    outcome: EvidenceStatus = "sufficient_candidates" if sufficient else "insufficient_evidence"
    logging.getLogger("sari_api.knowledge_retrieval").info(
        "Knowledge retrieval completed",
        extra={
            "event": "knowledge.retrieval.completed",
            "tenant_id": str(principal.tenant_id),
            "agent_id": str(payload.agent_id),
            "language": payload.language,
            "result_count": len(results),
            "duration_ms": duration_ms,
            "outcome": outcome,
        },
    )
    return ManagedKnowledgeSearchResponse(
        evidence_status=outcome,
        tenant_id=principal.tenant_id,
        agent_id=payload.agent_id,
        language=payload.language,
        correlation_id=get_correlation_id(),
        duration_ms=duration_ms,
        similarity_threshold=settings.knowledge_retrieval_min_similarity,
        minimum_evidence_count=settings.knowledge_retrieval_min_evidence_count,
        decision_reason=reason,
        results=results,
        below_threshold_results=below_threshold,
    )
