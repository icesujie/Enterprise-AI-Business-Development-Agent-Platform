from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.agent_queue import AgentQueue, get_agent_queue
from sari_api.adapters.database import get_session
from sari_api.adapters.knowledge_assistant_repository import (
    KnowledgeAssistantRepository,
    KnowledgeAssistantRunNotFoundError,
)
from sari_api.adapters.managed_knowledge_retrieval import (
    ManagedKnowledgeAgentContext,
    ManagedKnowledgeRetrievalDeniedError,
    ManagedKnowledgeRetrievalRepository,
)
from sari_api.adapters.models import AgentRun, AuditEvent, IdempotencyKey
from sari_api.api.dependencies import require_permission
from sari_api.core.config import get_settings
from sari_api.core.observability import get_correlation_id
from sari_api.domain.identity import Principal
from sari_api.domain.knowledge_assistant import KnowledgeAssistantResult

router = APIRouter(prefix="/api/v1/knowledge/assistant", tags=["knowledge-assistant"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class KnowledgeAssistantRunInput(StrictModel):
    agent_id: UUID
    language: Literal["en", "zh-CN"] = "en"
    question: str = Field(min_length=3, max_length=2000)


class KnowledgeAssistantRunStartResponse(StrictModel):
    run_id: UUID
    workflow_type: Literal["knowledge_assistant"]
    status: str
    status_url: str
    correlation_id: str | None
    created_at: datetime


class KnowledgeAssistantRunResponse(StrictModel):
    run_id: UUID
    workflow_type: Literal["knowledge_assistant"]
    status: str
    correlation_id: str | None
    provider_type: str | None
    model_id: str | None
    duration_ms: float | None
    result: KnowledgeAssistantResult | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


async def _repositories(
    session: AsyncSession,
    principal: Principal,
) -> tuple[KnowledgeAssistantRepository, ManagedKnowledgeRetrievalRepository]:
    runs = KnowledgeAssistantRepository(session, principal.tenant_id)
    retrieval = ManagedKnowledgeRetrievalRepository(session, principal.tenant_id)
    await runs.set_tenant_context()
    return runs, retrieval


async def _authorize_commercial_assistant(
    retrieval: ManagedKnowledgeRetrievalRepository,
    agent_id: UUID,
) -> ManagedKnowledgeAgentContext:
    try:
        context = await retrieval.get_agent_retrieval_context(agent_id)
    except ManagedKnowledgeRetrievalDeniedError as exc:
        raise HTTPException(
            status_code=403,
            detail="Knowledge Assistant is not enabled for this tenant agent.",
        ) from exc
    if (
        context.domain_key != "commercial_kitchen"
        or context.agent_key != "commercial_kitchen.lead_qualification"
    ):
        raise HTTPException(
            status_code=403,
            detail="Knowledge Assistant is enabled only for the Commercial Kitchen Agent.",
        )
    return context


@router.post("/runs", response_model=KnowledgeAssistantRunStartResponse, status_code=202)
async def start_knowledge_assistant_run(
    payload: KnowledgeAssistantRunInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("knowledge:retrieve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    queue: Annotated[AgentQueue, Depends(get_agent_queue)],
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=8, max_length=200),
    ],
) -> KnowledgeAssistantRunStartResponse:
    runs, retrieval = await _repositories(session, principal)
    context = await _authorize_commercial_assistant(retrieval, payload.agent_id)
    configuration = context.configuration

    scope = f"knowledge-assistant:{principal.tenant_id}"
    request_body = payload.model_dump(mode="json")
    request_hash = hashlib.sha256(
        json.dumps(request_body, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
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
        if existing.request_hash != request_hash:
            raise HTTPException(status_code=409, detail="Idempotency key was reused.")
        replay = KnowledgeAssistantRunStartResponse.model_validate(existing.response_body)
        response.headers["Location"] = replay.status_url
        return replay

    run = await runs.create_run(
        configuration=configuration,
        user_id=principal.user_id,
        agent_id=payload.agent_id,
        language=payload.language,
        question=payload.question,
        correlation_id=get_correlation_id(),
        max_attempts=get_settings().agent_max_attempts,
    )
    result = _start_response(run)
    session.add(
        IdempotencyKey(
            tenant_id=principal.tenant_id,
            scope=scope,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response_status=202,
            response_body=result.model_dump(mode="json"),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
    )
    session.add(
        AuditEvent(
            tenant_id=principal.tenant_id,
            actor_user_id=principal.user_id,
            action="knowledge_assistant.run_requested",
            target_type="agent_run",
            target_id=run.id,
            result="success",
            request_id=get_correlation_id(),
            details={
                "agent_id": str(payload.agent_id),
                "language": payload.language,
                "question_sha256": hashlib.sha256(payload.question.encode()).hexdigest(),
            },
        )
    )
    await session.commit()
    try:
        await queue.enqueue(run.id, principal.tenant_id, correlation_id=run.correlation_id)
    except Exception as exc:
        runs, _ = await _repositories(session, principal)
        failed = await runs.get_run(run.id, for_update=True)
        await runs.fail_run(failed, "queue_unavailable", "Knowledge Assistant queue unavailable.")
        await session.commit()
        raise HTTPException(status_code=503, detail="Knowledge Assistant is unavailable.") from exc
    response.headers["Location"] = result.status_url
    return result


@router.get("/runs/{run_id}", response_model=KnowledgeAssistantRunResponse)
async def get_knowledge_assistant_run(
    run_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("knowledge:retrieve"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> KnowledgeAssistantRunResponse:
    runs, _ = await _repositories(session, principal)
    try:
        return _run_response(await runs.get_run(run_id))
    except KnowledgeAssistantRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge Assistant run not found.") from exc


def _start_response(run: AgentRun) -> KnowledgeAssistantRunStartResponse:
    return KnowledgeAssistantRunStartResponse(
        run_id=run.id,
        workflow_type="knowledge_assistant",
        status=run.status,
        status_url=f"/api/v1/knowledge/assistant/runs/{run.id}",
        correlation_id=run.correlation_id,
        created_at=run.created_at,
    )


def _run_response(run: AgentRun) -> KnowledgeAssistantRunResponse:
    duration_ms = None
    if run.started_at and run.completed_at:
        duration_ms = round((run.completed_at - run.started_at).total_seconds() * 1000, 2)
    result = (
        KnowledgeAssistantResult.model_validate(run.output_result)
        if run.output_result is not None
        else None
    )
    return KnowledgeAssistantRunResponse(
        run_id=run.id,
        workflow_type="knowledge_assistant",
        status=run.status,
        correlation_id=run.correlation_id,
        provider_type=run.provider_type,
        model_id=run.model_id,
        duration_ms=duration_ms,
        result=result,
        error_code=run.error_code,
        error_message=run.error_message_safe,
        created_at=run.created_at,
        completed_at=run.completed_at,
    )
