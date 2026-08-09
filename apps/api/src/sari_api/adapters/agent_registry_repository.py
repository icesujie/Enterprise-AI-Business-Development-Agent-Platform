from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import (
    Agent,
    AgentCapability,
    AgentCapabilityBinding,
    AgentConfiguration,
    DomainPackage,
    TenantAgentActivation,
)


class AgentRegistryNotFoundError(Exception):
    pass


class SqlAlchemyAgentRegistryRepository:
    """Read model for the registry; execution remains in the existing Phase 1 services."""

    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def list_domains(self) -> list[DomainPackage]:
        return list(
            (
                await self._session.scalars(
                    select(DomainPackage).order_by(DomainPackage.domain_key)
                )
            ).all()
        )

    async def list_agents(self, domain_key: str | None = None) -> list[tuple[Agent, DomainPackage]]:
        statement = (
            select(Agent, DomainPackage)
            .join(DomainPackage, DomainPackage.id == Agent.domain_package_id)
            .order_by(DomainPackage.domain_key, Agent.agent_key)
        )
        if domain_key:
            statement = statement.where(DomainPackage.domain_key == domain_key)
        return list((await self._session.execute(statement)).tuples().all())

    async def get_agent(self, agent_key: str) -> tuple[Agent, DomainPackage]:
        row = (
            await self._session.execute(
                select(Agent, DomainPackage)
                .join(DomainPackage, DomainPackage.id == Agent.domain_package_id)
                .where(Agent.agent_key == agent_key)
            )
        ).one_or_none()
        if row is None:
            raise AgentRegistryNotFoundError
        return row[0], row[1]

    async def list_versions(self, agent_id: UUID) -> list[AgentConfiguration]:
        return list(
            (
                await self._session.scalars(
                    select(AgentConfiguration)
                    .where(
                        AgentConfiguration.tenant_id == self._tenant_id,
                        AgentConfiguration.agent_id == agent_id,
                    )
                    .order_by(AgentConfiguration.version_number.desc())
                )
            ).all()
        )

    async def get_activation(self, agent_id: UUID) -> TenantAgentActivation | None:
        return await self._session.scalar(
            select(TenantAgentActivation)
            .where(
                TenantAgentActivation.tenant_id == self._tenant_id,
                TenantAgentActivation.agent_id == agent_id,
            )
            .order_by(TenantAgentActivation.created_at.desc())
            .limit(1)
        )

    async def list_capabilities(
        self, configuration_id: UUID
    ) -> list[tuple[AgentCapabilityBinding, AgentCapability]]:
        return list(
            (
                await self._session.execute(
                    select(AgentCapabilityBinding, AgentCapability)
                    .join(
                        AgentCapability,
                        AgentCapability.id == AgentCapabilityBinding.capability_id,
                    )
                    .where(
                        AgentCapabilityBinding.tenant_id == self._tenant_id,
                        AgentCapabilityBinding.agent_configuration_id == configuration_id,
                    )
                    .order_by(AgentCapability.capability_key)
                )
            )
            .tuples()
            .all()
        )
