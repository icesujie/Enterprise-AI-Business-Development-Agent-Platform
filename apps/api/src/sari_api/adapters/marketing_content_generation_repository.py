from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.content_governance_repository import content_checksum
from sari_api.adapters.models import (
    AgentConfiguration,
    AgentRun,
    ContentAsset,
    ContentAuditLog,
    ContentGenerationRun,
    ContentRequest,
    ContentVersion,
)
from sari_api.core.observability import get_correlation_id
from sari_api.domain.marketing_content_evaluation import evaluate_business_quality
from sari_api.domain.marketing_content_generation import MarketingDraft, plain_text


class MarketingGenerationNotFoundError(Exception):
    pass


class MarketingGenerationStateError(Exception):
    pass


class MarketingContentGenerationRepository:
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
        request: ContentRequest,
        configuration: AgentConfiguration,
        agent_id: UUID,
        user_id: UUID,
        membership_id: UUID,
        correlation_id: str,
        max_attempts: int,
    ) -> tuple[AgentRun, ContentGenerationRun]:
        if request.status != "draft" or request.result_asset_id is not None:
            raise MarketingGenerationStateError("Only an unused draft request can be generated.")
        run = AgentRun(
            tenant_id=self._tenant_id,
            agent_configuration_id=configuration.id,
            workflow_type="marketing_content_generation",
            initiated_by_user_id=user_id,
            input_snapshot={
                "schema_version": "marketing_content_request_v1",
                "request_id": str(request.id),
                "agent_id": str(agent_id),
                "membership_id": str(membership_id),
            },
            status="queued",
            correlation_id=correlation_id,
            max_attempts=max_attempts,
        )
        self._session.add(run)
        await self._session.flush()
        generation = ContentGenerationRun(
            tenant_id=self._tenant_id,
            content_request_id=request.id,
            agent_run_id=run.id,
            agent_id=agent_id,
            agent_version_id=configuration.id,
            validation_summary={"outcome": "queued"},
        )
        self._session.add(generation)
        await self._session.flush()
        request.agent_id = agent_id
        request.status = "queued"
        self._audit(
            membership_id,
            "content.generation_requested",
            "content_generation_run",
            generation.id,
            request_id=request.id,
            generation_id=generation.id,
            details={"agent_id": str(agent_id), "content_type": request.content_type},
        )
        await self._session.flush()
        await self._session.refresh(run)
        return run, generation

    async def get_run(
        self, run_id: UUID, *, lock: bool = False
    ) -> tuple[AgentRun, ContentGenerationRun, ContentRequest]:
        statement = (
            select(AgentRun, ContentGenerationRun, ContentRequest)
            .join(ContentGenerationRun, ContentGenerationRun.agent_run_id == AgentRun.id)
            .join(ContentRequest, ContentRequest.id == ContentGenerationRun.content_request_id)
            .where(
                AgentRun.id == run_id,
                AgentRun.tenant_id == self._tenant_id,
                AgentRun.workflow_type == "marketing_content_generation",
                ContentGenerationRun.tenant_id == self._tenant_id,
                ContentRequest.tenant_id == self._tenant_id,
            )
        )
        if lock:
            statement = statement.with_for_update()
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            raise MarketingGenerationNotFoundError
        return row[0], row[1], row[2]

    async def start(self, run: AgentRun, request: ContentRequest) -> None:
        if run.status != "queued":
            return
        now = datetime.now(UTC)
        run.status = "running"
        run.started_at = run.started_at or now
        run.last_heartbeat_at = now
        run.next_retry_at = None
        run.attempt_count += 1
        run.version += 1
        request.status = "running"
        await self._session.flush()

    async def complete_insufficient(
        self,
        run: AgentRun,
        generation: ContentGenerationRun,
        request: ContentRequest,
        *,
        evidence_status: str,
        citations: list[dict[str, Any]],
        provider: str,
        model: str,
        duration_ms: int,
    ) -> None:
        now = datetime.now(UTC)
        result = {
            "outcome": "insufficient_evidence",
            "evidence_status": evidence_status,
            "message": "Approved public marketing evidence is insufficient for a grounded draft.",
            "asset_id": None,
            "version_id": None,
            "content": None,
            "citations": citations,
        }
        run.status = "succeeded"
        run.output_result = result
        run.provider_type = provider
        run.model_id = model
        run.completed_at = now
        run.last_heartbeat_at = now
        run.version += 1
        request.status = "insufficient_evidence"
        generation.provider = provider
        generation.model = model
        generation.evidence_status = evidence_status
        generation.retrieved_chunk_ids = [item["chunk_id"] for item in citations]
        generation.validation_summary = {"outcome": "insufficient_evidence", "citations": citations}
        generation.duration_ms = duration_ms
        generation.completed_at = now
        await self._session.flush()

    async def complete_generated(
        self,
        run: AgentRun,
        generation: ContentGenerationRun,
        request: ContentRequest,
        *,
        draft: MarketingDraft,
        citations: list[dict[str, Any]],
        provider: str,
        model: str,
        duration_ms: int,
    ) -> tuple[ContentAsset, ContentVersion]:
        actor_id = UUID(str(run.input_snapshot["membership_id"]))
        body = draft.model_dump(mode="json")
        rendered = plain_text(draft)
        asset = ContentAsset(
            tenant_id=self._tenant_id,
            domain_id=request.domain_id,
            agent_id=generation.agent_id,
            request_id=request.id,
            title=_draft_title(draft),
            content_type=request.content_type,
            audience=request.audience,
            language=request.language,
            channel=request.channel,
            status="generated",
            owner_membership_id=actor_id,
            creator_membership_id=actor_id,
        )
        self._session.add(asset)
        await self._session.flush()
        checksum = content_checksum(
            content_body=body, plain_text=rendered, claims=[], citations=citations
        )
        version = ContentVersion(
            tenant_id=self._tenant_id,
            content_asset_id=asset.id,
            version_number=1,
            origin="ai_generated",
            content_body=body,
            plain_text=rendered,
            claims=[],
            citations=citations,
            generation_run_id=generation.id,
            content_sha256=checksum,
            created_by=actor_id,
        )
        self._session.add(version)
        await self._session.flush()
        now = datetime.now(UTC)
        asset.current_version_id = version.id
        request.result_asset_id = asset.id
        request.status = "completed"
        generation.provider = provider
        generation.model = model
        generation.evidence_status = "sufficient"
        generation.retrieved_chunk_ids = [item["chunk_id"] for item in citations]
        generation.output_version_id = version.id
        quality = evaluate_business_quality(
            draft,
            {
                "audience": request.audience,
                "channel": request.channel,
                "topic": request.topic,
                "call_to_action": request.call_to_action,
            },
            citations,
        )
        generation.validation_summary = {
            "outcome": "generated",
            "schema": draft.content_type,
            "citations": citations,
            "quality_evaluation": quality.model_dump(mode="json"),
        }
        generation.duration_ms = duration_ms
        generation.completed_at = now
        run.status = "succeeded"
        run.output_result = {
            "outcome": "generated",
            "evidence_status": "sufficient",
            "message": "A governed draft was generated and requires human review.",
            "asset_id": str(asset.id),
            "version_id": str(version.id),
            "content": body,
            "citations": citations,
        }
        run.provider_type = provider
        run.model_id = model
        run.completed_at = now
        run.last_heartbeat_at = now
        run.version += 1
        self._audit(
            actor_id,
            "content.ai_version_generated",
            "content_version",
            version.id,
            asset_id=asset.id,
            version_id=version.id,
            request_id=request.id,
            generation_id=generation.id,
            details={
                "content_sha256": checksum,
                "provider": provider,
                "model": model,
                "quality_overall_score": quality.overall_score,
            },
        )
        await self._session.flush()
        return asset, version

    async def schedule_retry(
        self, run: AgentRun, request: ContentRequest, delay_seconds: int
    ) -> None:
        now = datetime.now(UTC)
        run.status = "queued"
        run.error_code = "generation_temporarily_unavailable"
        run.error_message_safe = "Marketing draft generation is temporarily unavailable."
        run.next_retry_at = now + timedelta(seconds=delay_seconds)
        run.last_heartbeat_at = now
        run.version += 1
        request.status = "queued"
        await self._session.flush()

    async def fail(
        self,
        run: AgentRun,
        generation: ContentGenerationRun,
        request: ContentRequest,
        code: str,
        message: str,
    ) -> None:
        now = datetime.now(UTC)
        run.status = "failed"
        run.error_code = code
        run.error_message_safe = message[:1000]
        run.completed_at = now
        run.last_heartbeat_at = now
        run.version += 1
        request.status = "failed"
        generation.validation_summary = {"outcome": "failed", "error_code": code}
        generation.completed_at = now
        await self._session.flush()

    def _audit(
        self,
        actor_id: UUID,
        action: str,
        target_type: str,
        target_id: UUID,
        *,
        asset_id: UUID | None = None,
        version_id: UUID | None = None,
        request_id: UUID | None = None,
        generation_id: UUID | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self._session.add(
            ContentAuditLog(
                tenant_id=self._tenant_id,
                actor_membership_id=actor_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                content_asset_id=asset_id,
                content_version_id=version_id,
                content_request_id=request_id,
                content_generation_run_id=generation_id,
                outcome="success",
                details=details or {},
                correlation_id=get_correlation_id(),
            )
        )


def _draft_title(draft: MarketingDraft) -> str:
    return str(
        getattr(
            draft, "title", getattr(draft, "headline", getattr(draft, "subject", "Marketing draft"))
        )
    )[:250]
