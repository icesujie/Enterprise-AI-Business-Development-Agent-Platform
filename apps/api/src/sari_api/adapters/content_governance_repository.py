from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import (
    Agent,
    ContentApprovalDecision,
    ContentAsset,
    ContentAuditLog,
    ContentRequest,
    ContentVersion,
    DomainPackage,
    TenantAgentActivation,
    TenantMembership,
)
from sari_api.core.observability import get_correlation_id


class ContentNotFoundError(Exception):
    pass


class ContentStateError(Exception):
    pass


class ContentConcurrencyError(Exception):
    pass


class ContentSeparationOfDutiesError(Exception):
    pass


def content_checksum(
    *,
    content_body: dict[str, Any],
    plain_text: str,
    claims: list[dict[str, Any]],
    citations: list[dict[str, Any]],
) -> str:
    canonical = json.dumps(
        {
            "citations": citations,
            "claims": claims,
            "content_body": content_body,
            "plain_text": plain_text,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


class ContentGovernanceRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def get_domain(self, domain_key: str) -> DomainPackage:
        domain = await self._session.scalar(
            select(DomainPackage).where(DomainPackage.domain_key == domain_key)
        )
        if domain is None:
            raise ContentNotFoundError("Domain not found.")
        return domain

    async def create_request(
        self,
        *,
        domain_key: str,
        requested_by: UUID,
        values: dict[str, Any],
    ) -> ContentRequest:
        domain = await self.get_domain(domain_key)
        await self._validate_agent(values.get("agent_id"), domain.id)
        request = ContentRequest(
            tenant_id=self._tenant_id,
            domain_id=domain.id,
            requested_by=requested_by,
            **values,
        )
        self._session.add(request)
        await self._session.flush()
        self._audit(
            actor_id=requested_by,
            action="content.request_created",
            target_type="content_request",
            target_id=request.id,
            request_id=request.id,
            after={"status": request.status, "content_type": request.content_type},
        )
        return request

    async def create_asset(
        self,
        *,
        domain_key: str,
        actor_id: UUID,
        asset_values: dict[str, Any],
        version_values: dict[str, Any],
    ) -> tuple[ContentAsset, ContentVersion]:
        domain = await self.get_domain(domain_key)
        await self._validate_agent(asset_values.get("agent_id"), domain.id)
        owner_id = asset_values.pop("owner_membership_id", actor_id)
        await self._validate_membership(owner_id)
        request_id = asset_values.get("request_id")
        request: ContentRequest | None = None
        if request_id is not None:
            request = await self._session.scalar(
                select(ContentRequest).where(
                    ContentRequest.id == request_id,
                    ContentRequest.tenant_id == self._tenant_id,
                )
            )
            if request is None:
                raise ContentNotFoundError("Content request not found.")
            if request.domain_id != domain.id:
                raise ContentStateError("Content request belongs to another domain.")

        asset = ContentAsset(
            tenant_id=self._tenant_id,
            domain_id=domain.id,
            creator_membership_id=actor_id,
            owner_membership_id=owner_id,
            **asset_values,
        )
        self._session.add(asset)
        await self._session.flush()
        version = self._new_version(
            asset=asset,
            actor_id=actor_id,
            version_number=1,
            origin="human",
            based_on_version_id=None,
            values=version_values,
        )
        self._session.add(version)
        await self._session.flush()
        asset.current_version_id = version.id
        if request is not None:
            request.result_asset_id = asset.id
            request.status = "completed"
        self._audit(
            actor_id=actor_id,
            action="content.asset_created",
            target_type="content_asset",
            target_id=asset.id,
            asset_id=asset.id,
            version_id=version.id,
            request_id=request_id,
            after={"status": asset.status, "record_version": asset.record_version},
        )
        self._audit_version(actor_id=actor_id, asset=asset, version=version, action="created")
        await self._session.flush()
        return asset, version

    async def list_assets(self) -> list[ContentAsset]:
        return list(
            (
                await self._session.scalars(
                    select(ContentAsset)
                    .where(ContentAsset.tenant_id == self._tenant_id)
                    .order_by(ContentAsset.updated_at.desc(), ContentAsset.id)
                )
            ).all()
        )

    async def get_request(self, request_id: UUID) -> ContentRequest:
        request = await self._session.scalar(
            select(ContentRequest).where(
                ContentRequest.id == request_id,
                ContentRequest.tenant_id == self._tenant_id,
            )
        )
        if request is None:
            raise ContentNotFoundError("Content request not found.")
        return request

    async def get_asset(self, asset_id: UUID, *, lock: bool = False) -> ContentAsset:
        statement = select(ContentAsset).where(
            ContentAsset.id == asset_id,
            ContentAsset.tenant_id == self._tenant_id,
        )
        if lock:
            statement = statement.with_for_update()
        asset = await self._session.scalar(statement)
        if asset is None:
            raise ContentNotFoundError("Content asset not found.")
        return asset

    async def refresh_asset(self, asset: ContentAsset) -> None:
        await self._session.refresh(asset)

    async def get_version(self, asset_id: UUID, version_id: UUID) -> ContentVersion:
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

    async def list_versions(self, asset_id: UUID) -> list[ContentVersion]:
        await self.get_asset(asset_id)
        return list(
            (
                await self._session.scalars(
                    select(ContentVersion)
                    .where(
                        ContentVersion.content_asset_id == asset_id,
                        ContentVersion.tenant_id == self._tenant_id,
                    )
                    .order_by(ContentVersion.version_number.desc())
                )
            ).all()
        )

    async def create_successor(
        self,
        *,
        asset_id: UUID,
        expected_record_version: int,
        actor_id: UUID,
        values: dict[str, Any],
    ) -> tuple[ContentAsset, ContentVersion]:
        asset = await self.get_asset(asset_id, lock=True)
        self._check_record_version(asset, expected_record_version)
        if asset.status == "archived":
            raise ContentStateError("Archived content must be restored before editing.")
        predecessor_id = asset.current_version_id
        next_number = await self._next_version_number(asset.id)
        version = self._new_version(
            asset=asset,
            actor_id=actor_id,
            version_number=next_number,
            origin="human",
            based_on_version_id=predecessor_id,
            values=values,
        )
        self._session.add(version)
        await self._session.flush()
        before = self._asset_state(asset)
        asset.current_version_id = version.id
        asset.approved_version_id = None
        asset.status = "draft"
        asset.record_version += 1
        self._audit_version(actor_id=actor_id, asset=asset, version=version, action="edited")
        self._audit(
            actor_id=actor_id,
            action="content.edited",
            target_type="content_asset",
            target_id=asset.id,
            asset_id=asset.id,
            version_id=version.id,
            before=before,
            after=self._asset_state(asset),
        )
        await self._session.flush()
        return asset, version

    async def rollback(
        self,
        *,
        asset_id: UUID,
        source_version_id: UUID,
        expected_record_version: int,
        actor_id: UUID,
    ) -> tuple[ContentAsset, ContentVersion]:
        asset = await self.get_asset(asset_id, lock=True)
        self._check_record_version(asset, expected_record_version)
        if asset.status == "archived":
            raise ContentStateError("Archived content must be restored before rollback.")
        source = await self.get_version(asset.id, source_version_id)
        next_number = await self._next_version_number(asset.id)
        version = self._new_version(
            asset=asset,
            actor_id=actor_id,
            version_number=next_number,
            origin="rollback",
            based_on_version_id=source.id,
            values={
                "content_body": source.content_body,
                "plain_text": source.plain_text,
                "claims": source.claims,
                "citations": source.citations,
            },
        )
        self._session.add(version)
        await self._session.flush()
        before = self._asset_state(asset)
        asset.current_version_id = version.id
        asset.approved_version_id = None
        asset.status = "draft"
        asset.record_version += 1
        self._audit_version(actor_id=actor_id, asset=asset, version=version, action="rollback")
        self._audit(
            actor_id=actor_id,
            action="content.rollback",
            target_type="content_asset",
            target_id=asset.id,
            asset_id=asset.id,
            version_id=version.id,
            before=before,
            after=self._asset_state(asset),
            details={"source_version_id": str(source.id)},
        )
        await self._session.flush()
        return asset, version

    async def submit_review(
        self,
        *,
        asset_id: UUID,
        version_id: UUID,
        checksum: str,
        expected_record_version: int,
        actor_id: UUID,
        comment: str | None,
    ) -> tuple[ContentAsset, ContentApprovalDecision]:
        asset = await self.get_asset(asset_id, lock=True)
        self._check_record_version(asset, expected_record_version)
        if asset.status not in {"draft", "generated"}:
            raise ContentStateError("Only draft or generated content can enter review.")
        version = await self._validate_exact_current_version(asset, version_id, checksum)
        before = self._asset_state(asset)
        decision = self._decision(
            asset=asset,
            version=version,
            actor_id=actor_id,
            decision_type="submitted",
            comment=comment,
        )
        asset.status = "review"
        asset.approved_version_id = None
        asset.record_version += 1
        self._session.add(decision)
        self._audit(
            actor_id=actor_id,
            action="content.review_submitted",
            target_type="content_version",
            target_id=version.id,
            asset_id=asset.id,
            version_id=version.id,
            before=before,
            after=self._asset_state(asset),
        )
        await self._session.flush()
        return asset, decision

    async def decide(
        self,
        *,
        asset_id: UUID,
        version_id: UUID,
        checksum: str,
        decision_type: str,
        expected_record_version: int,
        actor_id: UUID,
        comment: str | None,
    ) -> tuple[ContentAsset, ContentApprovalDecision]:
        asset = await self.get_asset(asset_id, lock=True)
        self._check_record_version(asset, expected_record_version)
        if asset.status != "review":
            raise ContentStateError("Only content in review can receive a decision.")
        version = await self._validate_exact_current_version(asset, version_id, checksum)
        if decision_type == "approved" and asset.creator_membership_id == actor_id:
            raise ContentSeparationOfDutiesError(
                "A content creator cannot approve their own content."
            )
        before = self._asset_state(asset)
        decision = self._decision(
            asset=asset,
            version=version,
            actor_id=actor_id,
            decision_type=decision_type,
            comment=comment,
        )
        if decision_type == "approved":
            asset.status = "approved"
            asset.approved_version_id = version.id
            action = "content.approved"
        elif decision_type == "rejected":
            asset.status = "draft"
            asset.approved_version_id = None
            action = "content.rejected"
        else:
            asset.status = "draft"
            asset.approved_version_id = None
            action = "content.changes_requested"
        asset.record_version += 1
        self._session.add(decision)
        self._audit(
            actor_id=actor_id,
            action=action,
            target_type="content_version",
            target_id=version.id,
            asset_id=asset.id,
            version_id=version.id,
            before=before,
            after=self._asset_state(asset),
        )
        await self._session.flush()
        return asset, decision

    async def archive(
        self,
        *,
        asset_id: UUID,
        expected_record_version: int,
        actor_id: UUID,
        reason: str,
    ) -> ContentAsset:
        asset = await self.get_asset(asset_id, lock=True)
        self._check_record_version(asset, expected_record_version)
        if asset.status == "archived":
            raise ContentStateError("Content is already archived.")
        before = self._asset_state(asset)
        asset.status = "archived"
        asset.approved_version_id = None
        asset.archived_at = datetime.now(UTC)
        asset.archived_by = actor_id
        asset.archive_reason = reason
        asset.record_version += 1
        self._audit(
            actor_id=actor_id,
            action="content.archived",
            target_type="content_asset",
            target_id=asset.id,
            asset_id=asset.id,
            version_id=asset.current_version_id,
            before=before,
            after=self._asset_state(asset),
            details={"reason": reason},
        )
        await self._session.flush()
        return asset

    async def restore(
        self,
        *,
        asset_id: UUID,
        expected_record_version: int,
        actor_id: UUID,
        reason: str,
    ) -> ContentAsset:
        asset = await self.get_asset(asset_id, lock=True)
        self._check_record_version(asset, expected_record_version)
        if asset.status != "archived":
            raise ContentStateError("Only archived content can be restored.")
        before = self._asset_state(asset)
        asset.status = "draft"
        asset.approved_version_id = None
        asset.archived_at = None
        asset.archived_by = None
        asset.archive_reason = None
        asset.record_version += 1
        self._audit(
            actor_id=actor_id,
            action="content.restored",
            target_type="content_asset",
            target_id=asset.id,
            asset_id=asset.id,
            version_id=asset.current_version_id,
            before=before,
            after=self._asset_state(asset),
            details={"reason": reason},
        )
        await self._session.flush()
        return asset

    async def list_decisions(self, asset_id: UUID) -> list[ContentApprovalDecision]:
        await self.get_asset(asset_id)
        return list(
            (
                await self._session.scalars(
                    select(ContentApprovalDecision)
                    .where(
                        ContentApprovalDecision.content_asset_id == asset_id,
                        ContentApprovalDecision.tenant_id == self._tenant_id,
                    )
                    .order_by(ContentApprovalDecision.created_at.desc())
                )
            ).all()
        )

    async def list_audit(self, asset_id: UUID) -> list[ContentAuditLog]:
        await self.get_asset(asset_id)
        return list(
            (
                await self._session.scalars(
                    select(ContentAuditLog)
                    .where(
                        ContentAuditLog.content_asset_id == asset_id,
                        ContentAuditLog.tenant_id == self._tenant_id,
                    )
                    .order_by(ContentAuditLog.created_at.desc())
                )
            ).all()
        )

    async def _next_version_number(self, asset_id: UUID) -> int:
        current = await self._session.scalar(
            select(func.max(ContentVersion.version_number)).where(
                ContentVersion.tenant_id == self._tenant_id,
                ContentVersion.content_asset_id == asset_id,
            )
        )
        return int(current or 0) + 1

    async def _validate_membership(self, membership_id: UUID) -> None:
        exists = await self._session.scalar(
            select(TenantMembership.id).where(
                TenantMembership.id == membership_id,
                TenantMembership.tenant_id == self._tenant_id,
                TenantMembership.status == "active",
            )
        )
        if exists is None:
            raise ContentNotFoundError("Content owner is not an active tenant member.")

    async def _validate_agent(self, agent_id: UUID | None, domain_id: UUID) -> None:
        if agent_id is None:
            return
        agent = await self._session.scalar(
            select(Agent).where(
                Agent.id == agent_id,
                Agent.domain_package_id == domain_id,
                Agent.status == "available",
            )
        )
        activation = await self._session.scalar(
            select(TenantAgentActivation.id).where(
                TenantAgentActivation.tenant_id == self._tenant_id,
                TenantAgentActivation.agent_id == agent_id,
                TenantAgentActivation.status == "active",
            )
        )
        if agent is None or activation is None:
            raise ContentNotFoundError("Agent is not active for this tenant and domain.")

    @staticmethod
    def _check_record_version(asset: ContentAsset, expected: int) -> None:
        if asset.record_version != expected:
            raise ContentConcurrencyError("Content changed; reload and retry.")

    async def _validate_exact_current_version(
        self, asset: ContentAsset, version_id: UUID, checksum: str
    ) -> ContentVersion:
        if asset.current_version_id != version_id:
            raise ContentStateError("The reviewed version is not the current version.")
        version = await self.get_version(asset.id, version_id)
        if version.content_sha256 != checksum:
            raise ContentStateError("The content checksum does not match the reviewed version.")
        return version

    @staticmethod
    def _new_version(
        *,
        asset: ContentAsset,
        actor_id: UUID,
        version_number: int,
        origin: str,
        based_on_version_id: UUID | None,
        values: dict[str, Any],
    ) -> ContentVersion:
        claims = values.get("claims", [])
        citations = values.get("citations", [])
        checksum = content_checksum(
            content_body=values["content_body"],
            plain_text=values["plain_text"],
            claims=claims,
            citations=citations,
        )
        return ContentVersion(
            tenant_id=asset.tenant_id,
            content_asset_id=asset.id,
            version_number=version_number,
            origin=origin,
            content_body=values["content_body"],
            plain_text=values["plain_text"],
            claims=claims,
            citations=citations,
            based_on_version_id=based_on_version_id,
            content_sha256=checksum,
            created_by=actor_id,
        )

    @staticmethod
    def _decision(
        *,
        asset: ContentAsset,
        version: ContentVersion,
        actor_id: UUID,
        decision_type: str,
        comment: str | None,
    ) -> ContentApprovalDecision:
        return ContentApprovalDecision(
            tenant_id=asset.tenant_id,
            content_asset_id=asset.id,
            content_version_id=version.id,
            decision_type=decision_type,
            decided_by=actor_id,
            content_sha256=version.content_sha256,
            comment=comment,
        )

    def _audit_version(
        self,
        *,
        actor_id: UUID,
        asset: ContentAsset,
        version: ContentVersion,
        action: str,
    ) -> None:
        self._audit(
            actor_id=actor_id,
            action="content.version_created",
            target_type="content_version",
            target_id=version.id,
            asset_id=asset.id,
            version_id=version.id,
            after={
                "version_number": version.version_number,
                "origin": version.origin,
                "content_sha256": version.content_sha256,
            },
            details={"reason": action},
        )

    def _audit(
        self,
        *,
        actor_id: UUID,
        action: str,
        target_type: str,
        target_id: UUID,
        asset_id: UUID | None = None,
        version_id: UUID | None = None,
        request_id: UUID | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
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
                outcome="success",
                before_metadata=before or {},
                after_metadata=after or {},
                details=details or {},
                correlation_id=get_correlation_id(),
            )
        )

    @staticmethod
    def _asset_state(asset: ContentAsset) -> dict[str, Any]:
        return {
            "approved_version_id": (
                str(asset.approved_version_id) if asset.approved_version_id else None
            ),
            "current_version_id": (
                str(asset.current_version_id) if asset.current_version_id else None
            ),
            "record_version": asset.record_version,
            "status": asset.status,
        }
