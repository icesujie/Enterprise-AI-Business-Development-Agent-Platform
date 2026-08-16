from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.agent_queue import AgentQueue, get_agent_queue
from sari_api.adapters.content_governance_repository import (
    ContentGovernanceRepository,
    ContentNotFoundError,
)
from sari_api.adapters.database import get_session
from sari_api.adapters.managed_knowledge_retrieval import (
    ManagedKnowledgeRetrievalDeniedError,
    ManagedKnowledgeRetrievalRepository,
)
from sari_api.adapters.marketing_content_generation_repository import (
    MarketingContentGenerationRepository,
    MarketingGenerationNotFoundError,
    MarketingGenerationStateError,
)
from sari_api.adapters.models import AgentRun, IdempotencyKey
from sari_api.api.dependencies import require_permission
from sari_api.core.config import get_settings
from sari_api.core.observability import get_correlation_id
from sari_api.domain.identity import Principal
from sari_api.domain.marketing_content_generation import MarketingGenerationResult
from sari_api.domain.marketing_knowledge_policy import MARKETING_CONTENT_AGENT_ID

router = APIRouter(prefix="/api/v1/content", tags=["marketing-content-generation"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class GenerationStartResponse(StrictModel):
    run_id: UUID
    request_id: UUID
    workflow_type: Literal["marketing_content_generation"]
    status: str
    status_url: str
    correlation_id: str | None
    created_at: datetime


class GenerationRunResponse(StrictModel):
    run_id: UUID
    request_id: UUID
    workflow_type: Literal["marketing_content_generation"]
    status: str
    correlation_id: str | None
    provider: str | None
    model: str | None
    evidence_status: str | None
    duration_ms: int | None
    result: MarketingGenerationResult | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


@router.post(
    "/requests/{request_id}/generate", response_model=GenerationStartResponse, status_code=202
)
async def start_generation(
    request_id: UUID,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("content:generate"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    queue: Annotated[AgentQueue, Depends(get_agent_queue)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)],
) -> GenerationStartResponse:
    governance = ContentGovernanceRepository(session, principal.tenant_id)
    await governance.set_tenant_context()
    try:
        request = await governance.get_request(request_id, lock=True)
    except ContentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Content request not found.") from exc
    retrieval = ManagedKnowledgeRetrievalRepository(session, principal.tenant_id)
    await retrieval.set_tenant_context()
    try:
        context = await retrieval.get_marketing_generation_context(MARKETING_CONTENT_AGENT_ID)
    except ManagedKnowledgeRetrievalDeniedError as exc:
        raise HTTPException(
            status_code=403, detail="Marketing Content Agent generation is not enabled."
        ) from exc
    if request.domain_id != context.domain_id:
        raise HTTPException(
            status_code=403, detail="Content request is outside the Marketing Agent domain."
        )

    scope = f"content-generation:{principal.tenant_id}:{request_id}"
    payload_hash = hashlib.sha256(str(request_id).encode()).hexdigest()
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
        if existing.request_hash != payload_hash:
            raise HTTPException(status_code=409, detail="Idempotency key was reused.")
        replay = GenerationStartResponse.model_validate(existing.response_body)
        response.headers["Location"] = replay.status_url
        return replay
    repo = MarketingContentGenerationRepository(session, principal.tenant_id)
    try:
        run, _ = await repo.create_run(
            request=request,
            configuration=context.configuration,
            agent_id=context.agent_id,
            user_id=principal.user_id,
            membership_id=principal.membership_id,
            correlation_id=get_correlation_id(),
            max_attempts=get_settings().agent_max_attempts,
        )
    except MarketingGenerationStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    result = _start_response(run, request_id)
    session.add(
        IdempotencyKey(
            tenant_id=principal.tenant_id,
            scope=scope,
            idempotency_key=idempotency_key,
            request_hash=payload_hash,
            response_status=202,
            response_body=result.model_dump(mode="json"),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
    )
    await session.commit()
    try:
        await queue.enqueue(run.id, principal.tenant_id, correlation_id=run.correlation_id)
    except Exception as exc:
        await repo.set_tenant_context()
        queued, generation, current_request = await repo.get_run(run.id, lock=True)
        await repo.fail(
            queued,
            generation,
            current_request,
            "queue_unavailable",
            "Marketing generation queue is unavailable.",
        )
        await session.commit()
        raise HTTPException(status_code=503, detail="Marketing generation is unavailable.") from exc
    response.headers["Location"] = result.status_url
    return result


@router.get("/generation-runs/{run_id}", response_model=GenerationRunResponse)
async def get_generation_run(
    run_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("content:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GenerationRunResponse:
    repo = MarketingContentGenerationRepository(session, principal.tenant_id)
    await repo.set_tenant_context()
    try:
        run, generation, request = await repo.get_run(run_id)
    except MarketingGenerationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Marketing generation run not found.") from exc
    parsed = (
        MarketingGenerationResult.model_validate(run.output_result) if run.output_result else None
    )
    return GenerationRunResponse(
        run_id=run.id,
        request_id=request.id,
        workflow_type="marketing_content_generation",
        status=run.status,
        correlation_id=run.correlation_id,
        provider=generation.provider or run.provider_type,
        model=generation.model or run.model_id,
        evidence_status=generation.evidence_status,
        duration_ms=generation.duration_ms,
        result=parsed,
        error_code=run.error_code,
        error_message=run.error_message_safe,
        created_at=run.created_at,
        completed_at=run.completed_at,
    )


def _start_response(run: AgentRun, request_id: UUID) -> GenerationStartResponse:
    return GenerationStartResponse(
        run_id=run.id,
        request_id=request_id,
        workflow_type="marketing_content_generation",
        status=run.status,
        status_url=f"/api/v1/content/generation-runs/{run.id}",
        correlation_id=run.correlation_id,
        created_at=run.created_at,
    )
