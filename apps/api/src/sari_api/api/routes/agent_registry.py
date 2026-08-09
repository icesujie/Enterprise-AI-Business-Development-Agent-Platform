from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.agent_registry_repository import (
    AgentRegistryNotFoundError,
    SqlAlchemyAgentRegistryRepository,
)
from sari_api.adapters.database import get_session
from sari_api.adapters.models import Agent, DomainPackage
from sari_api.api.dependencies import require_role
from sari_api.domain.identity import Principal, Role
from sari_api.domain.packages.models import DomainAgentManifest, SupportedLocale
from sari_api.domain.packages.registry import PACKAGES_BY_AGENT

router = APIRouter(prefix="/api/v1/agent-registry", tags=["agent-registry"])
LocaleQuery = Literal["en", "zh-CN", "id"]


class DomainPackageResponse(BaseModel):
    id: UUID
    domain_key: str
    name: str
    description: str
    package_version: str
    supported_locales: list[str]
    default_locale: str
    status: str


class CapabilityResponse(BaseModel):
    key: str
    name: str
    required: bool
    status: str


class AgentVersionResponse(BaseModel):
    id: UUID
    version_number: int
    status: str
    input_schema_version: str | None
    output_schema_version: str
    supported_locales: list[str]
    capabilities: list[CapabilityResponse]


class AgentSummaryResponse(BaseModel):
    id: UUID
    agent_key: str
    domain_key: str
    name: str
    agent_type: str
    status: str
    supported_locales: list[str]
    activation_status: str | None


class QualificationFieldResponse(BaseModel):
    key: str
    label: str
    description: str
    field_type: str
    required: bool
    choices: list[str]


class KnowledgeCategoryResponse(BaseModel):
    key: str
    label: str
    description: str
    expert_review_required: bool


class AgentDetailResponse(AgentSummaryResponse):
    default_locale: str
    response_locale_policy: str
    business_objectives: list[str]
    qualification_fields: list[QualificationFieldResponse]
    knowledge_categories: list[KnowledgeCategoryResponse]
    versions: list[AgentVersionResponse]


def _localized(values: dict[str, str], locale: LocaleQuery) -> str:
    return values.get(locale) or values.get("en") or next(iter(values.values()), "")


def _domain_response(row: DomainPackage, locale: LocaleQuery) -> DomainPackageResponse:
    return DomainPackageResponse(
        id=row.id,
        domain_key=row.domain_key,
        name=_localized(row.display_name, locale),
        description=_localized(row.description, locale),
        package_version=row.package_version,
        supported_locales=row.supported_locales,
        default_locale=row.default_locale,
        status=row.status,
    )


async def _summary(
    repository: SqlAlchemyAgentRegistryRepository,
    agent: Agent,
    domain: DomainPackage,
    locale: LocaleQuery,
) -> AgentSummaryResponse:
    activation = await repository.get_activation(agent.id)
    return AgentSummaryResponse(
        id=agent.id,
        agent_key=agent.agent_key,
        domain_key=domain.domain_key,
        name=_localized(agent.display_name, locale),
        agent_type=agent.agent_type,
        status=agent.status,
        supported_locales=agent.supported_locales,
        activation_status=activation.status if activation else None,
    )


async def _versions(
    repository: SqlAlchemyAgentRegistryRepository,
    agent: Agent,
    locale: LocaleQuery,
) -> list[AgentVersionResponse]:
    responses: list[AgentVersionResponse] = []
    for version in await repository.list_versions(agent.id):
        bindings = await repository.list_capabilities(version.id)
        responses.append(
            AgentVersionResponse(
                id=version.id,
                version_number=version.version_number,
                status=version.status,
                input_schema_version=version.input_schema_version,
                output_schema_version=version.output_schema_version,
                supported_locales=version.supported_locales,
                capabilities=[
                    CapabilityResponse(
                        key=capability.capability_key,
                        name=_localized(capability.display_name, locale),
                        required=binding.requirement_level == "required",
                        status=binding.status,
                    )
                    for binding, capability in bindings
                ],
            )
        )
    return responses


def _manifest_fields(
    manifest: DomainAgentManifest, locale: SupportedLocale
) -> list[QualificationFieldResponse]:
    return [
        QualificationFieldResponse(
            key=field.key,
            label=field.label.for_locale(locale),
            description=field.description.for_locale(locale),
            field_type=field.field_type,
            required=field.required,
            choices=list(field.choices),
        )
        for field in manifest.qualification_fields
    ]


@router.get("/domains", response_model=list[DomainPackageResponse])
async def list_domains(
    principal: Annotated[Principal, Depends(require_role(Role.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_session)],
    locale: Annotated[LocaleQuery, Query()] = "en",
) -> list[DomainPackageResponse]:
    repository = SqlAlchemyAgentRegistryRepository(session, principal.tenant_id)
    await repository.set_tenant_context()
    return [_domain_response(row, locale) for row in await repository.list_domains()]


@router.get("/agents", response_model=list[AgentSummaryResponse])
async def list_agents(
    principal: Annotated[Principal, Depends(require_role(Role.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_session)],
    locale: Annotated[LocaleQuery, Query()] = "en",
    domain_key: Annotated[str | None, Query(max_length=100)] = None,
) -> list[AgentSummaryResponse]:
    repository = SqlAlchemyAgentRegistryRepository(session, principal.tenant_id)
    await repository.set_tenant_context()
    return [
        await _summary(repository, agent, domain, locale)
        for agent, domain in await repository.list_agents(domain_key)
    ]


@router.get("/agents/{agent_key}", response_model=AgentDetailResponse)
async def get_agent(
    agent_key: str,
    principal: Annotated[Principal, Depends(require_role(Role.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_session)],
    locale: Annotated[LocaleQuery, Query()] = "en",
) -> AgentDetailResponse:
    repository = SqlAlchemyAgentRegistryRepository(session, principal.tenant_id)
    await repository.set_tenant_context()
    try:
        agent, domain = await repository.get_agent(agent_key)
        manifest = PACKAGES_BY_AGENT[agent.agent_key]
    except (AgentRegistryNotFoundError, KeyError) as exc:
        raise HTTPException(status_code=404, detail="Agent is not registered.") from exc
    summary = await _summary(repository, agent, domain, locale)
    return AgentDetailResponse(
        **summary.model_dump(),
        default_locale=manifest.default_locale,
        response_locale_policy=manifest.response_locale_policy,
        business_objectives=[item.for_locale(locale) for item in manifest.business_objectives],
        qualification_fields=_manifest_fields(manifest, locale),
        knowledge_categories=[
            KnowledgeCategoryResponse(
                key=item.key,
                label=item.label.for_locale(locale),
                description=item.description.for_locale(locale),
                expert_review_required=item.expert_review_required,
            )
            for item in manifest.knowledge_categories
        ],
        versions=await _versions(repository, agent, locale),
    )
