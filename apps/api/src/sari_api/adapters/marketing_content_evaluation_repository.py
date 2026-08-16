from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.content_governance_repository import (
    ContentNotFoundError,
    ContentStateError,
)
from sari_api.adapters.models import (
    AgentRun,
    ContentApprovalDecision,
    ContentAsset,
    ContentAuditLog,
    ContentGenerationRun,
    ContentRequest,
    ContentReviewFeedback,
    ContentVersion,
)
from sari_api.core.observability import get_correlation_id
from sari_api.domain.marketing_content_evaluation import human_edit_distance


@dataclass(frozen=True, slots=True)
class MarketingEvaluationSnapshot:
    asset: ContentAsset
    evaluated_version: ContentVersion
    generation: ContentGenerationRun | None
    agent_run: AgentRun | None
    generated_version: ContentVersion | None
    approved_human_version: ContentVersion | None
    human_edit_distance: float | None
    feedback: list[ContentReviewFeedback]


@dataclass(frozen=True, slots=True)
class AcceptanceRecordSnapshot:
    request: ContentRequest
    attempt_count: int
    asset: ContentAsset | None
    evaluation: MarketingEvaluationSnapshot | None
    latest_decision: ContentApprovalDecision | None


class MarketingContentEvaluationRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def add_feedback(
        self,
        *,
        asset_id: UUID,
        version_id: UUID,
        checksum: str,
        reviewer_membership_id: UUID,
        categories: list[str],
        note: str | None,
    ) -> ContentReviewFeedback:
        asset = await self._asset(asset_id)
        version = await self._version(asset.id, version_id)
        if asset.status == "archived":
            raise ContentStateError("Archived content cannot receive review feedback.")
        if version.content_sha256 != checksum:
            raise ContentStateError("Feedback checksum does not match the selected version.")
        feedback = ContentReviewFeedback(
            tenant_id=self._tenant_id,
            content_asset_id=asset.id,
            content_version_id=version.id,
            reviewer_membership_id=reviewer_membership_id,
            content_sha256=version.content_sha256,
            categories=categories,
            note=note,
        )
        self._session.add(feedback)
        await self._session.flush()
        self._session.add(
            ContentAuditLog(
                tenant_id=self._tenant_id,
                actor_membership_id=reviewer_membership_id,
                action="content.review_feedback_added",
                target_type="content_review_feedback",
                target_id=feedback.id,
                content_asset_id=asset.id,
                content_version_id=version.id,
                outcome="success",
                details={"categories": categories},
                correlation_id=get_correlation_id(),
            )
        )
        await self._session.flush()
        return feedback

    async def snapshot(self, asset_id: UUID) -> MarketingEvaluationSnapshot:
        asset = await self._asset(asset_id)
        if asset.current_version_id is None:
            raise ContentNotFoundError("Current content version not found.")
        evaluated_version = await self._version(asset.id, asset.current_version_id)
        row = (
            await self._session.execute(
                select(ContentGenerationRun, AgentRun, ContentVersion)
                .join(AgentRun, AgentRun.id == ContentGenerationRun.agent_run_id)
                .join(
                    ContentVersion,
                    ContentVersion.id == ContentGenerationRun.output_version_id,
                )
                .where(
                    ContentGenerationRun.tenant_id == self._tenant_id,
                    ContentGenerationRun.output_version_id.is_not(None),
                    ContentVersion.content_asset_id == asset.id,
                )
                .order_by(ContentGenerationRun.created_at.desc())
                .limit(1)
            )
        ).one_or_none()
        generation = row[0] if row else None
        agent_run = row[1] if row else None
        generated_version = row[2] if row else None
        approved_human_version: ContentVersion | None = None
        edit_distance: float | None = None
        if generated_version is not None and asset.approved_version_id is not None:
            approved = await self._version(asset.id, asset.approved_version_id)
            if (
                approved.origin == "human"
                and approved.version_number > generated_version.version_number
                and await self._descends_from(approved, generated_version.id)
            ):
                approved_human_version = approved
                edit_distance = human_edit_distance(
                    generated_version.plain_text, approved.plain_text
                )
        feedback = list(
            (
                await self._session.scalars(
                    select(ContentReviewFeedback)
                    .where(
                        ContentReviewFeedback.tenant_id == self._tenant_id,
                        ContentReviewFeedback.content_asset_id == asset.id,
                    )
                    .order_by(ContentReviewFeedback.created_at.desc())
                )
            ).all()
        )
        return MarketingEvaluationSnapshot(
            asset=asset,
            evaluated_version=evaluated_version,
            generation=generation,
            agent_run=agent_run,
            generated_version=generated_version,
            approved_human_version=approved_human_version,
            human_edit_distance=edit_distance,
            feedback=feedback,
        )

    async def acceptance_records(
        self, dataset_version: str
    ) -> dict[str, AcceptanceRecordSnapshot]:
        requests = list(
            (
                await self._session.scalars(
                    select(ContentRequest)
                    .where(
                        ContentRequest.tenant_id == self._tenant_id,
                        ContentRequest.constraints["acceptance_dataset"].astext
                        == dataset_version,
                    )
                    .order_by(ContentRequest.created_at.desc())
                )
            ).all()
        )
        result: dict[str, AcceptanceRecordSnapshot] = {}
        attempt_counts: dict[str, int] = {}
        for request in requests:
            case_id = request.constraints.get("acceptance_case_id")
            if isinstance(case_id, str):
                attempt_counts[case_id] = attempt_counts.get(case_id, 0) + 1
        for request in requests:
            case_id = request.constraints.get("acceptance_case_id")
            if not isinstance(case_id, str) or case_id in result:
                continue
            asset = (
                await self._asset(request.result_asset_id)
                if request.result_asset_id is not None
                else None
            )
            evaluation = await self.snapshot(asset.id) if asset is not None else None
            latest_decision = None
            if asset is not None:
                latest_decision = await self._session.scalar(
                    select(ContentApprovalDecision)
                    .where(
                        ContentApprovalDecision.tenant_id == self._tenant_id,
                        ContentApprovalDecision.content_asset_id == asset.id,
                    )
                    .order_by(ContentApprovalDecision.created_at.desc())
                    .limit(1)
                )
            result[case_id] = AcceptanceRecordSnapshot(
                request=request,
                attempt_count=attempt_counts[case_id],
                asset=asset,
                evaluation=evaluation,
                latest_decision=latest_decision,
            )
        return result

    async def _descends_from(self, version: ContentVersion, ancestor_id: UUID) -> bool:
        parent_id = version.based_on_version_id
        seen: set[UUID] = set()
        while parent_id is not None and parent_id not in seen:
            if parent_id == ancestor_id:
                return True
            seen.add(parent_id)
            parent = await self._version(version.content_asset_id, parent_id)
            parent_id = parent.based_on_version_id
        return False

    async def _asset(self, asset_id: UUID) -> ContentAsset:
        asset = await self._session.scalar(
            select(ContentAsset).where(
                ContentAsset.id == asset_id,
                ContentAsset.tenant_id == self._tenant_id,
            )
        )
        if asset is None:
            raise ContentNotFoundError("Content asset not found.")
        return asset

    async def _version(self, asset_id: UUID, version_id: UUID) -> ContentVersion:
        version = await self._session.scalar(
            select(ContentVersion).where(
                ContentVersion.id == version_id,
                ContentVersion.content_asset_id == asset_id,
                ContentVersion.tenant_id == self._tenant_id,
            )
        )
        if version is None:
            raise ContentNotFoundError("Content version not found.")
        return version


def quality_from_generation(generation: ContentGenerationRun | None) -> dict[str, Any] | None:
    if generation is None:
        return None
    value = generation.validation_summary.get("quality_evaluation")
    return value if isinstance(value, dict) else None
