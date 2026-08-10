from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import AgentConfiguration, AgentRun
from sari_api.domain.agent_playground import (
    PlaygroundQualificationOutput,
    PlaygroundQualificationRequest,
)


class AgentPlaygroundNotFoundError(Exception):
    pass


class SqlAlchemyAgentPlaygroundRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def get_active_configuration(self, domain: str) -> AgentConfiguration:
        agent_key = (
            "lead_qualification" if domain == "commercial_kitchen" else "ivc_business_development"
        )
        config = await self._session.scalar(
            select(AgentConfiguration).where(
                AgentConfiguration.tenant_id == self._tenant_id,
                AgentConfiguration.agent_key == agent_key,
                AgentConfiguration.status == "active",
            )
        )
        if config is None:
            raise AgentPlaygroundNotFoundError
        return config

    async def create_run(
        self,
        *,
        configuration: AgentConfiguration,
        user_id: UUID,
        request: PlaygroundQualificationRequest,
        correlation_id: str,
        max_attempts: int,
    ) -> AgentRun:
        run = AgentRun(
            tenant_id=self._tenant_id,
            agent_configuration_id=configuration.id,
            workflow_type="agent_playground_qualification",
            initiated_by_user_id=user_id,
            lead_id=None,
            input_snapshot=request.model_dump(mode="json"),
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
            AgentRun.workflow_type == "agent_playground_qualification",
        )
        if for_update:
            statement = statement.with_for_update()
        run = await self._session.scalar(statement)
        if run is None:
            raise AgentPlaygroundNotFoundError
        return run

    async def start_run(self, run: AgentRun, provider_type: str, model_id: str) -> None:
        if run.status != "queued":
            return
        now = datetime.now(UTC)
        run.status = "running"
        run.provider_type = provider_type
        run.model_id = model_id
        run.started_at = run.started_at or now
        run.last_heartbeat_at = now
        run.next_retry_at = None
        run.completed_at = None
        run.attempt_count += 1
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

    async def complete_run(
        self,
        run: AgentRun,
        output: PlaygroundQualificationOutput,
    ) -> None:
        run.output_result = output.model_dump(mode="json")
        run.status = "succeeded"
        run.completed_at = datetime.now(UTC)
        run.last_heartbeat_at = run.completed_at
        run.next_retry_at = None
        run.error_code = None
        run.error_message_safe = None
        run.version += 1
        await self._session.flush()

    async def fail_run(self, run: AgentRun, code: str, message: str) -> None:
        run.status = "failed"
        run.completed_at = datetime.now(UTC)
        run.last_heartbeat_at = run.completed_at
        run.next_retry_at = None
        run.error_code = code
        run.error_message_safe = message[:1000]
        run.version += 1
        await self._session.flush()
