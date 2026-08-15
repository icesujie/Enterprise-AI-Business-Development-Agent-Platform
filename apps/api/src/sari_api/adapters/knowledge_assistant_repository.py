from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import AgentConfiguration, AgentRun
from sari_api.domain.knowledge_assistant import KnowledgeAssistantResult


class KnowledgeAssistantRunNotFoundError(Exception):
    pass


class KnowledgeAssistantRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def create_run(
        self,
        *,
        configuration: AgentConfiguration,
        user_id: UUID,
        agent_id: UUID,
        language: str,
        question: str,
        correlation_id: str,
        max_attempts: int,
    ) -> AgentRun:
        run = AgentRun(
            tenant_id=self._tenant_id,
            agent_configuration_id=configuration.id,
            workflow_type="knowledge_assistant",
            initiated_by_user_id=user_id,
            input_snapshot={
                "schema_version": "knowledge_assistant_input_v1",
                "agent_id": str(agent_id),
                "language": language,
                "question": question,
            },
            status="queued",
            correlation_id=correlation_id,
            max_attempts=max_attempts,
        )
        self._session.add(run)
        await self._session.flush()
        await self._session.refresh(run)
        return run

    async def get_run(self, run_id: UUID, *, for_update: bool = False) -> AgentRun:
        statement = select(AgentRun).where(
            AgentRun.id == run_id,
            AgentRun.tenant_id == self._tenant_id,
            AgentRun.workflow_type == "knowledge_assistant",
        )
        if for_update:
            statement = statement.with_for_update()
        run = await self._session.scalar(statement)
        if run is None:
            raise KnowledgeAssistantRunNotFoundError
        return run

    async def start_run(self, run: AgentRun) -> None:
        if run.status != "queued":
            return
        now = datetime.now(UTC)
        run.status = "running"
        run.started_at = run.started_at or now
        run.last_heartbeat_at = now
        run.next_retry_at = None
        run.completed_at = None
        run.attempt_count += 1
        run.version += 1
        await self._session.flush()

    async def complete_run(
        self,
        run: AgentRun,
        result: KnowledgeAssistantResult,
    ) -> None:
        question = str(run.input_snapshot.get("question", ""))
        run.input_snapshot = {
            "schema_version": "knowledge_assistant_input_v1",
            "agent_id": run.input_snapshot.get("agent_id"),
            "language": run.input_snapshot.get("language"),
            "question_sha256": hashlib.sha256(question.encode()).hexdigest(),
        }
        run.output_result = result.model_dump(mode="json")
        run.provider_type = result.model_provider
        run.model_id = result.model_id
        run.status = "succeeded"
        run.completed_at = datetime.now(UTC)
        run.last_heartbeat_at = run.completed_at
        run.next_retry_at = None
        run.error_code = None
        run.error_message_safe = None
        run.version += 1
        await self._session.flush()

    async def schedule_retry(
        self,
        run: AgentRun,
        code: str,
        message: str,
        delay_seconds: int,
    ) -> None:
        now = datetime.now(UTC)
        run.status = "queued"
        run.error_code = code
        run.error_message_safe = message[:1000]
        run.next_retry_at = now + timedelta(seconds=delay_seconds)
        run.last_heartbeat_at = now
        run.completed_at = None
        run.version += 1
        await self._session.flush()

    async def fail_run(self, run: AgentRun, code: str, message: str) -> None:
        self._redact_question(run)
        run.status = "failed"
        run.completed_at = datetime.now(UTC)
        run.last_heartbeat_at = run.completed_at
        run.next_retry_at = None
        run.error_code = code
        run.error_message_safe = message[:1000]
        run.version += 1
        await self._session.flush()

    def _redact_question(self, run: AgentRun) -> None:
        snapshot: dict[str, Any] = run.input_snapshot
        question = str(snapshot.get("question", ""))
        if not question:
            return
        run.input_snapshot = {
            "schema_version": snapshot.get("schema_version"),
            "agent_id": snapshot.get("agent_id"),
            "language": snapshot.get("language"),
            "question_sha256": hashlib.sha256(question.encode()).hexdigest(),
        }
