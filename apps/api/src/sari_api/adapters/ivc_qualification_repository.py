from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import (
    AgentConfiguration,
    AgentRun,
    IvcQualificationAssessment,
)
from sari_api.domain.ivc_qualification import IvcQualificationInput, IvcQualificationOutput
from sari_api.domain.packages.models import SupportedLocale


class IvcQualificationNotFoundError(Exception):
    pass


class IvcAssessmentAlreadyReviewedError(Exception):
    pass


class SqlAlchemyIvcQualificationRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def get_active_configuration(self) -> AgentConfiguration:
        config = await self._session.scalar(
            select(AgentConfiguration).where(
                AgentConfiguration.tenant_id == self._tenant_id,
                AgentConfiguration.agent_key == "ivc_business_development",
                AgentConfiguration.status == "active",
            )
        )
        if config is None or not config.runtime_config.get("execution_enabled", False):
            raise IvcQualificationNotFoundError
        return config

    async def create_run(
        self,
        *,
        configuration: AgentConfiguration,
        user_id: UUID,
        input_data: IvcQualificationInput,
        response_locale: SupportedLocale,
        correlation_id: str,
        max_attempts: int,
    ) -> AgentRun:
        run = AgentRun(
            tenant_id=self._tenant_id,
            agent_configuration_id=configuration.id,
            workflow_type="ivc_facility_qualification",
            initiated_by_user_id=user_id,
            lead_id=None,
            input_snapshot={
                "schema_version": "ivc_agent_run_input_v1",
                "response_locale": response_locale,
                "project_snapshot": input_data.model_dump(mode="json"),
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
            AgentRun.workflow_type == "ivc_facility_qualification",
        )
        if for_update:
            statement = statement.with_for_update()
        run = await self._session.scalar(statement)
        if run is None:
            raise IvcQualificationNotFoundError
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
        output: IvcQualificationOutput,
    ) -> IvcQualificationAssessment:
        assessment = IvcQualificationAssessment(
            tenant_id=self._tenant_id,
            agent_run_id=run.id,
            response_locale=output.response_locale,
            score=Decimal(str(output.score)),
            qualification_level=output.qualification_level,
            business_summary=output.business_summary,
            key_qualification_factors=[
                item.model_dump(mode="json") for item in output.key_qualification_factors
            ],
            recommended_next_actions=output.recommended_next_actions,
            missing_information=output.missing_information,
            risk_flags=output.risk_flags,
            confidence=Decimal(str(output.confidence)),
            expert_review_required=output.expert_review_required,
            review_status="pending",
        )
        self._session.add(assessment)
        await self._session.flush()
        run.output_result = {
            "assessment_id": str(assessment.id),
            **output.model_dump(mode="json"),
            "review_status": "pending",
        }
        run.status = "succeeded"
        run.completed_at = datetime.now(UTC)
        run.last_heartbeat_at = run.completed_at
        run.next_retry_at = None
        run.error_code = None
        run.error_message_safe = None
        run.version += 1
        await self._session.flush()
        return assessment

    async def fail_run(self, run: AgentRun, code: str, message: str) -> None:
        run.status = "failed"
        run.completed_at = datetime.now(UTC)
        run.last_heartbeat_at = run.completed_at
        run.next_retry_at = None
        run.error_code = code
        run.error_message_safe = message[:1000]
        run.version += 1
        await self._session.flush()

    async def list_assessments(self, limit: int = 50) -> list[IvcQualificationAssessment]:
        result = await self._session.scalars(
            select(IvcQualificationAssessment)
            .where(IvcQualificationAssessment.tenant_id == self._tenant_id)
            .order_by(IvcQualificationAssessment.created_at.desc())
            .limit(limit)
        )
        return list(result.all())

    async def get_assessment(
        self,
        assessment_id: UUID,
        *,
        for_update: bool = False,
    ) -> IvcQualificationAssessment:
        statement = select(IvcQualificationAssessment).where(
            IvcQualificationAssessment.id == assessment_id,
            IvcQualificationAssessment.tenant_id == self._tenant_id,
        )
        if for_update:
            statement = statement.with_for_update()
        assessment = await self._session.scalar(statement)
        if assessment is None:
            raise IvcQualificationNotFoundError
        return assessment

    async def review_assessment(
        self,
        assessment: IvcQualificationAssessment,
        *,
        decision: str,
        user_id: UUID,
    ) -> None:
        if assessment.review_status != "pending":
            raise IvcAssessmentAlreadyReviewedError
        assessment.review_status = decision
        assessment.reviewed_by = user_id
        assessment.reviewed_at = datetime.now(UTC)
        await self._session.flush()
