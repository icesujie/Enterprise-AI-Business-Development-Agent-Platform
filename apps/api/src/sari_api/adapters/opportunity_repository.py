from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import (
    Activity,
    Lead,
    Opportunity,
    Tenant,
    TenantMembership,
)


class OpportunityNotFoundError(Exception):
    pass


class OpportunityConflictError(Exception):
    pass


class OpportunityVersionConflictError(Exception):
    pass


class InvalidOpportunityTransitionError(Exception):
    pass


STAGE_TRANSITIONS: dict[str, frozenset[str]] = {
    "discovery": frozenset({"requirements_confirmed", "lost"}),
    "requirements_confirmed": frozenset({"discovery", "proposal", "lost"}),
    "proposal": frozenset({"requirements_confirmed", "negotiation", "lost"}),
    "negotiation": frozenset({"proposal", "won", "lost"}),
    "won": frozenset(),
    "lost": frozenset(),
}

STAGE_PROBABILITY: dict[str, Decimal] = {
    "discovery": Decimal("10"),
    "requirements_confirmed": Decimal("35"),
    "proposal": Decimal("60"),
    "negotiation": Decimal("80"),
    "won": Decimal("100"),
    "lost": Decimal("0"),
}


class SqlAlchemyOpportunityRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def lock_lead_conversion(self, lead_id: UUID) -> None:
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": f"lead-conversion:{self._tenant_id}:{lead_id}"},
        )

    async def get_lead_for_conversion(self, lead_id: UUID) -> Lead:
        lead = await self._session.scalar(
            select(Lead)
            .where(
                Lead.id == lead_id,
                Lead.tenant_id == self._tenant_id,
                Lead.deleted_at.is_(None),
            )
            .with_for_update()
        )
        if lead is None:
            raise OpportunityNotFoundError
        return lead

    async def get_by_source_lead(self, lead_id: UUID) -> Opportunity | None:
        return await self._session.scalar(
            select(Opportunity).where(
                Opportunity.tenant_id == self._tenant_id,
                Opportunity.source_lead_id == lead_id,
                Opportunity.deleted_at.is_(None),
            )
        )

    async def require_membership(self, membership_id: UUID) -> None:
        exists = await self._session.scalar(
            select(TenantMembership.id).where(
                TenantMembership.id == membership_id,
                TenantMembership.tenant_id == self._tenant_id,
                TenantMembership.status == "active",
            )
        )
        if exists is None:
            raise OpportunityNotFoundError

    async def default_currency(self) -> str:
        currency = await self._session.scalar(
            select(Tenant.default_currency).where(Tenant.id == self._tenant_id)
        )
        if currency is None:
            raise OpportunityNotFoundError
        return currency

    async def convert(
        self,
        lead: Lead,
        *,
        name: str,
        owner_membership_id: UUID,
        expected_close_date: date | None,
        estimated_value: Decimal | None,
        currency: str | None,
        actor_membership_id: UUID,
    ) -> Opportunity:
        if lead.status != "qualified":
            raise OpportunityConflictError("Only qualified leads can be converted.")
        if lead.organization_id is None:
            raise OpportunityConflictError("Select a customer company before conversion.")
        await self.require_membership(owner_membership_id)
        opportunity = Opportunity(
            tenant_id=self._tenant_id,
            organization_id=lead.organization_id,
            primary_contact_id=lead.contact_id,
            source_lead_id=lead.id,
            name=name,
            stage="discovery",
            status="open",
            probability=STAGE_PROBABILITY["discovery"],
            estimated_value=(
                estimated_value
                if estimated_value is not None
                else lead.estimated_value or Decimal("0")
            ),
            currency=currency or lead.currency or await self.default_currency(),
            expected_close_date=expected_close_date,
            requirements={
                **lead.requirements,
                "project_country_code": lead.project_country_code,
                "project_city": lead.project_city,
                "project_type": lead.project_type,
                "expected_capacity": lead.expected_capacity,
                "target_timeline": lead.target_timeline,
            },
            owner_membership_id=owner_membership_id,
        )
        self._session.add(opportunity)
        await self._session.flush()
        lead.status = "converted"
        lead.version += 1
        self._session.add(
            Activity(
                tenant_id=self._tenant_id,
                lead_id=lead.id,
                opportunity_id=opportunity.id,
                organization_id=lead.organization_id,
                contact_id=lead.contact_id,
                activity_type="lead_converted",
                occurred_at=datetime.now(UTC),
                subject="Lead converted to opportunity",
                actor_membership_id=actor_membership_id,
                metadata_json={"opportunity_id": str(opportunity.id)},
            )
        )
        await self._session.flush()
        await self._session.refresh(opportunity)
        return opportunity

    async def list_opportunities(
        self,
        *,
        search: str | None,
        stage: str | None,
        status: str | None,
        created_before: datetime | None,
        limit: int,
    ) -> list[Opportunity]:
        statement = select(Opportunity).where(
            Opportunity.tenant_id == self._tenant_id,
            Opportunity.deleted_at.is_(None),
        )
        if search:
            statement = statement.where(Opportunity.name.ilike(f"%{search.strip()}%"))
        if stage:
            statement = statement.where(Opportunity.stage == stage)
        if status:
            statement = statement.where(Opportunity.status == status)
        if created_before:
            statement = statement.where(Opportunity.created_at < created_before)
        result = await self._session.scalars(
            statement.order_by(Opportunity.created_at.desc(), Opportunity.id.desc()).limit(limit)
        )
        return list(result.all())

    async def get(self, opportunity_id: UUID, *, for_update: bool = False) -> Opportunity:
        statement = select(Opportunity).where(
            Opportunity.id == opportunity_id,
            Opportunity.tenant_id == self._tenant_id,
            Opportunity.deleted_at.is_(None),
        )
        if for_update:
            statement = statement.with_for_update()
        opportunity = await self._session.scalar(statement)
        if opportunity is None:
            raise OpportunityNotFoundError
        return opportunity

    async def transition(
        self,
        opportunity: Opportunity,
        *,
        target_stage: str,
        reason: str | None,
        expected_version: int,
        actor_membership_id: UUID,
    ) -> None:
        if opportunity.version != expected_version:
            raise OpportunityVersionConflictError
        if target_stage not in STAGE_TRANSITIONS[opportunity.stage]:
            raise InvalidOpportunityTransitionError
        if target_stage == "lost" and not reason:
            raise OpportunityConflictError("A loss reason is required.")
        previous_stage = opportunity.stage
        opportunity.stage = target_stage
        opportunity.status = target_stage if target_stage in {"won", "lost"} else "open"
        opportunity.probability = STAGE_PROBABILITY[target_stage]
        opportunity.version += 1
        self._session.add(
            Activity(
                tenant_id=self._tenant_id,
                opportunity_id=opportunity.id,
                organization_id=opportunity.organization_id,
                activity_type="opportunity_stage_changed",
                occurred_at=datetime.now(UTC),
                subject=f"Opportunity moved to {target_stage.replace('_', ' ')}",
                description=reason,
                actor_membership_id=actor_membership_id,
                metadata_json={"from": previous_stage, "to": target_stage},
            )
        )

    async def activities(self, opportunity_id: UUID, limit: int = 100) -> list[Activity]:
        await self.get(opportunity_id)
        result = await self._session.scalars(
            select(Activity)
            .where(
                Activity.tenant_id == self._tenant_id,
                Activity.opportunity_id == opportunity_id,
            )
            .order_by(Activity.occurred_at.desc(), Activity.created_at.desc())
            .limit(limit)
        )
        return list(result.all())
