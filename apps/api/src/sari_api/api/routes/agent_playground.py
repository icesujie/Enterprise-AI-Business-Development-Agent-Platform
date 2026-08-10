from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.agent_playground_repository import (
    AgentPlaygroundNotFoundError,
    SqlAlchemyAgentPlaygroundRepository,
)
from sari_api.adapters.agent_queue import AgentQueue, get_agent_queue
from sari_api.adapters.database import get_session
from sari_api.adapters.models import AuditEvent, IdempotencyKey
from sari_api.api.dependencies import require_permission
from sari_api.core.config import get_settings
from sari_api.core.observability import get_correlation_id
from sari_api.domain.agent_playground import PlaygroundQualificationRequest
from sari_api.domain.identity import Principal

router = APIRouter(prefix="/api/v1/agent-playground", tags=["agent-playground"])


class PlaygroundRunStartResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: UUID
    workflow_type: str
    status: str
    status_url: str
    created_at: datetime


async def _repository(
    session: AsyncSession,
    principal: Principal,
) -> SqlAlchemyAgentPlaygroundRepository:
    repo = SqlAlchemyAgentPlaygroundRepository(session, principal.tenant_id)
    await repo.set_tenant_context()
    return repo


def _audit(
    session: AsyncSession,
    principal: Principal,
    *,
    action: str,
    target_id: UUID,
    details: dict[str, Any],
) -> None:
    session.add(
        AuditEvent(
            tenant_id=principal.tenant_id,
            actor_user_id=principal.user_id,
            action=action,
            target_type="agent_run",
            target_id=target_id,
            result="success",
            request_id=get_correlation_id(),
            details=details,
        )
    )


@router.post("/runs", response_model=PlaygroundRunStartResponse, status_code=202)
async def start_playground_run(
    payload: PlaygroundQualificationRequest,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("leads:qualify"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    queue: Annotated[AgentQueue, Depends(get_agent_queue)],
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=8, max_length=200),
    ],
) -> PlaygroundRunStartResponse:
    scope = f"agent-playground:{principal.tenant_id}"
    request_body = payload.model_dump(mode="json")
    request_hash = hashlib.sha256(json.dumps(request_body, sort_keys=True).encode()).hexdigest()
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
        replay = PlaygroundRunStartResponse.model_validate(existing.response_body)
        response.headers["Location"] = replay.status_url
        return replay

    repo = await _repository(session, principal)
    try:
        configuration = await repo.get_active_configuration(payload.domain)
    except AgentPlaygroundNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Selected demo agent is not active.") from exc
    run = await repo.create_run(
        configuration=configuration,
        user_id=principal.user_id,
        request=payload,
        correlation_id=get_correlation_id(),
        max_attempts=get_settings().agent_max_attempts,
    )
    result = PlaygroundRunStartResponse(
        run_id=run.id,
        workflow_type=run.workflow_type,
        status=run.status,
        status_url=f"/api/v1/agent-runs/{run.id}",
        created_at=run.created_at,
    )
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
    _audit(
        session,
        principal,
        action="agent_playground.run_requested",
        target_id=run.id,
        details={
            "domain": payload.domain,
            "response_locale": payload.response_locale,
            "workflow_type": run.workflow_type,
        },
    )
    await session.commit()

    try:
        await queue.enqueue(run.id, principal.tenant_id)
    except Exception as exc:
        repo = await _repository(session, principal)
        failed = await repo.get_run(run.id, for_update=True)
        await repo.fail_run(failed, "queue_unavailable", "AI queue is unavailable. Retry later.")
        await session.commit()
        raise HTTPException(
            status_code=503, detail="AI queue is unavailable. Retry later."
        ) from exc

    response.headers["Location"] = result.status_url
    return result
