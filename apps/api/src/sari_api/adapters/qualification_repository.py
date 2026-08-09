from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import (
    Activity,
    AgentConfiguration,
    AgentRun,
    Contact,
    Lead,
    LeadAssessment,
    Organization,
    Task,
)
from sari_api.domain.qualification import QualificationOutput


class QualificationNotFoundError(Exception):
    pass


class AssessmentAlreadyReviewedError(Exception):
    pass


class SqlAlchemyQualificationRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def get_lead(self, lead_id: UUID, *, for_update: bool = False) -> Lead:
        statement = select(Lead).where(
            Lead.id == lead_id,
            Lead.tenant_id == self._tenant_id,
            Lead.deleted_at.is_(None),
        )
        if for_update:
            statement = statement.with_for_update()
        lead = await self._session.scalar(statement)
        if lead is None:
            raise QualificationNotFoundError
        return lead

    async def get_active_configuration(self) -> AgentConfiguration:
        config = await self._session.scalar(
            select(AgentConfiguration).where(
                AgentConfiguration.tenant_id == self._tenant_id,
                AgentConfiguration.agent_key == "lead_qualification",
                AgentConfiguration.status == "active",
            )
        )
        if config is None:
            raise QualificationNotFoundError
        return config

    async def build_snapshot(self, lead: Lead, actor_membership_id: UUID) -> dict[str, Any]:
        organization = None
        if lead.organization_id:
            organization = await self._session.scalar(
                select(Organization).where(
                    Organization.id == lead.organization_id,
                    Organization.tenant_id == self._tenant_id,
                    Organization.deleted_at.is_(None),
                )
            )
        contact = None
        if lead.contact_id:
            contact = await self._session.scalar(
                select(Contact).where(
                    Contact.id == lead.contact_id,
                    Contact.tenant_id == self._tenant_id,
                    Contact.deleted_at.is_(None),
                )
            )
        tasks = list(
            (
                await self._session.scalars(
                    select(Task)
                    .where(
                        Task.tenant_id == self._tenant_id,
                        Task.lead_id == lead.id,
                        Task.deleted_at.is_(None),
                    )
                    .order_by(Task.created_at.desc())
                    .limit(20)
                )
            ).all()
        )
        activities = list(
            (
                await self._session.scalars(
                    select(Activity)
                    .where(Activity.tenant_id == self._tenant_id, Activity.lead_id == lead.id)
                    .order_by(Activity.occurred_at.desc())
                    .limit(20)
                )
            ).all()
        )
        return {
            "schema_version": "lead_qualification_input_v1",
            "actor_membership_id": str(actor_membership_id),
            "lead": {
                "id": str(lead.id),
                "source_channel": lead.source_channel,
                "inquiry_summary": lead.inquiry_summary,
                "priority": lead.priority,
                "estimated_value": str(lead.estimated_value) if lead.estimated_value else None,
                "currency": lead.currency,
                "target_timeline": lead.target_timeline,
                "project_country_code": lead.project_country_code,
                "project_city": lead.project_city,
                "project_type": lead.project_type,
                "expected_capacity": lead.expected_capacity,
                "requirements": lead.requirements,
                "version": lead.version,
            },
            "organization": (
                {
                    "name": organization.display_name,
                    "industry": organization.industry,
                    "country_code": organization.country_code,
                    "city": organization.city,
                }
                if organization
                else None
            ),
            "contact": (
                {
                    "name": " ".join(
                        part for part in (contact.first_name, contact.last_name) if part
                    ),
                    "job_title": contact.job_title,
                    "preferred_language": contact.preferred_language,
                }
                if contact
                else None
            ),
            "tasks": [
                {
                    "title": task.title,
                    "status": task.status,
                    "due_at": task.due_at.isoformat() if task.due_at else None,
                }
                for task in tasks
            ],
            "recent_activities": [
                {
                    "type": activity.activity_type,
                    "subject": activity.subject,
                    "description": activity.description,
                    "occurred_at": activity.occurred_at.isoformat(),
                }
                for activity in activities
                if activity.activity_type == "manual_note"
            ],
        }

    async def create_run(
        self,
        *,
        configuration: AgentConfiguration,
        lead_id: UUID,
        user_id: UUID,
        input_snapshot: dict[str, Any],
    ) -> AgentRun:
        run = AgentRun(
            tenant_id=self._tenant_id,
            agent_configuration_id=configuration.id,
            workflow_type="lead_qualification",
            initiated_by_user_id=user_id,
            lead_id=lead_id,
            input_snapshot=input_snapshot,
            status="queued",
        )
        self._session.add(run)
        await self._session.flush()
        await self._session.refresh(run)
        return run

    async def get_run(self, run_id: UUID, *, for_update: bool = False) -> AgentRun:
        statement = select(AgentRun).where(
            AgentRun.id == run_id,
            AgentRun.tenant_id == self._tenant_id,
        )
        if for_update:
            statement = statement.with_for_update()
        run = await self._session.scalar(statement)
        if run is None:
            raise QualificationNotFoundError
        return run

    async def list_runs(self, lead_id: UUID, limit: int = 20) -> list[AgentRun]:
        await self.get_lead(lead_id)
        result = await self._session.scalars(
            select(AgentRun)
            .where(
                AgentRun.tenant_id == self._tenant_id,
                AgentRun.lead_id == lead_id,
                AgentRun.workflow_type == "lead_qualification",
            )
            .order_by(AgentRun.created_at.desc())
            .limit(limit)
        )
        return list(result.all())

    async def start_run(self, run: AgentRun, provider_type: str, model_id: str) -> None:
        if run.status != "queued":
            return
        run.status = "running"
        run.provider_type = provider_type
        run.model_id = model_id
        run.started_at = datetime.now(UTC)
        run.version += 1
        await self._session.flush()

    async def complete_run(
        self,
        run: AgentRun,
        output: QualificationOutput,
    ) -> LeadAssessment:
        if run.lead_id is None:
            raise QualificationNotFoundError
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": f"lead-assessment:{run.lead_id}"},
        )
        latest_version = await self._session.scalar(
            select(func.max(LeadAssessment.assessment_version)).where(
                LeadAssessment.tenant_id == self._tenant_id,
                LeadAssessment.lead_id == run.lead_id,
            )
        )
        assessment = LeadAssessment(
            tenant_id=self._tenant_id,
            lead_id=run.lead_id,
            assessment_version=(latest_version or 0) + 1,
            agent_run_id=run.id,
            score=Decimal(str(output.score)),
            tier=output.tier,
            need_summary=output.need_summary,
            qualification=output.qualification_dimensions(),
            recommended_action=output.recommended_action,
            missing_information=output.missing_information,
            confidence=Decimal(str(output.confidence)),
            review_status="pending",
        )
        self._session.add(assessment)
        await self._session.flush()
        result = {
            "assessment_id": str(assessment.id),
            **output.model_dump(mode="json"),
            "review_status": "pending",
        }
        run.output_result = result
        run.status = "succeeded"
        run.completed_at = datetime.now(UTC)
        run.version += 1
        await self._session.flush()
        return assessment

    async def fail_run(self, run: AgentRun, code: str, message: str) -> None:
        run.status = "failed"
        run.completed_at = datetime.now(UTC)
        run.error_code = code
        run.error_message_safe = message[:1000]
        run.version += 1
        await self._session.flush()

    async def list_assessments(self, lead_id: UUID) -> list[LeadAssessment]:
        await self.get_lead(lead_id)
        result = await self._session.scalars(
            select(LeadAssessment)
            .where(
                LeadAssessment.tenant_id == self._tenant_id,
                LeadAssessment.lead_id == lead_id,
            )
            .order_by(LeadAssessment.assessment_version.desc())
        )
        return list(result.all())

    async def get_assessment(
        self, assessment_id: UUID, *, for_update: bool = False
    ) -> LeadAssessment:
        statement = select(LeadAssessment).where(
            LeadAssessment.id == assessment_id,
            LeadAssessment.tenant_id == self._tenant_id,
        )
        if for_update:
            statement = statement.with_for_update()
        assessment = await self._session.scalar(statement)
        if assessment is None:
            raise QualificationNotFoundError
        return assessment

    async def review_assessment(
        self,
        assessment: LeadAssessment,
        *,
        decision: str,
        user_id: UUID,
    ) -> Lead:
        if assessment.review_status != "pending":
            raise AssessmentAlreadyReviewedError
        assessment.review_status = decision
        assessment.reviewed_by = user_id
        assessment.reviewed_at = datetime.now(UTC)
        lead = await self.get_lead(assessment.lead_id, for_update=True)
        if decision == "approved":
            lead.qualification_score = assessment.score
            lead.version += 1
        return lead
