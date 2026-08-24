from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Annotated, Any, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.database import get_session
from sari_api.adapters.models import PublicContentItem, PublicContentVersion
from sari_api.adapters.public_content_repository import (
    PublicContentConcurrencyError,
    PublicContentNotFoundError,
    PublicContentRepository,
    PublicContentSeparationOfDutiesError,
    PublicContentStateError,
)
from sari_api.api.dependencies import get_current_principal, require_permission
from sari_api.api.routes.content_governance import (
    existing_idempotent_response,
    parse_if_match,
    request_hash,
    save_idempotency,
)
from sari_api.core.config import get_settings
from sari_api.domain.identity import Principal

router = APIRouter(prefix="/api/v1/public-content", tags=["public-content"])

PageType = Literal["solution", "industry", "case_study", "guide"]
Locale = Literal["en", "zh-CN"]
SourceType = Literal["manual", "knowledge_version", "marketing_content_version"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, from_attributes=True)


class RelatedContentInput(StrictModel):
    label: str = Field(min_length=1, max_length=200)
    public_content_item_id: UUID | None = None
    path: str | None = Field(default=None, pattern=r"^/(solutions|industries|projects|guides)/")

    @model_validator(mode="after")
    def require_reference(self) -> RelatedContentInput:
        if self.public_content_item_id is None and self.path is None:
            raise ValueError("A related content item ID or public path is required.")
        return self


class MediaReferenceInput(StrictModel):
    media_asset_id: UUID
    role: str = Field(min_length=1, max_length=80)
    alt_text: str = Field(min_length=1, max_length=500)
    caption: str | None = Field(default=None, max_length=1000)


class CtaInput(StrictModel):
    label: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=1000)
    destination: Literal["public_consultation_agent", "contact_form"]


class StructuredSectionInput(StrictModel):
    title: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1, max_length=4000)


class ApprovedFactInput(StrictModel):
    label: str = Field(min_length=1, max_length=160)
    value: str = Field(min_length=1, max_length=2000)
    source_note: str | None = Field(default=None, max_length=1000)


class FaqItemInput(StrictModel):
    question: str = Field(min_length=3, max_length=500)
    answer: str = Field(min_length=3, max_length=4000)


class SolutionContentInput(StrictModel):
    overview: list[str] = Field(min_length=1, max_length=20)
    customer_needs: list[str] = Field(min_length=1, max_length=50)
    service_scope: list[StructuredSectionInput] = Field(min_length=1, max_length=30)
    workflow_areas: list[StructuredSectionInput] = Field(min_length=1, max_length=30)
    related_industries: list[RelatedContentInput] = Field(default_factory=list, max_length=30)
    related_projects: list[RelatedContentInput] = Field(default_factory=list, max_length=30)
    cta: CtaInput


class IndustryContentInput(StrictModel):
    overview: list[str] = Field(min_length=1, max_length=20)
    business_needs: list[str] = Field(min_length=1, max_length=50)
    relevant_solutions: list[RelatedContentInput] = Field(default_factory=list, max_length=30)
    project_considerations: list[StructuredSectionInput] = Field(min_length=1, max_length=30)
    related_projects: list[RelatedContentInput] = Field(default_factory=list, max_length=30)
    cta: CtaInput


class CaseStudyContentInput(StrictModel):
    project_overview: list[str] = Field(min_length=1, max_length=20)
    location: str = Field(min_length=1, max_length=250)
    industry: str = Field(min_length=1, max_length=160)
    project_type: str = Field(min_length=1, max_length=160)
    project_requirements: list[str] = Field(min_length=1, max_length=60)
    scope_of_work: list[StructuredSectionInput] = Field(min_length=1, max_length=40)
    functional_areas: list[StructuredSectionInput] = Field(min_length=1, max_length=40)
    delivery_approach: list[StructuredSectionInput] = Field(min_length=1, max_length=40)
    approved_project_facts: list[ApprovedFactInput] = Field(min_length=1, max_length=60)
    gallery_references: list[MediaReferenceInput] = Field(default_factory=list, max_length=80)
    related_solution: RelatedContentInput
    related_industry: RelatedContentInput
    cta: CtaInput


class GuideContentInput(StrictModel):
    introduction: list[str] = Field(min_length=1, max_length=20)
    sections: list[StructuredSectionInput] = Field(min_length=1, max_length=60)
    faq_items: list[FaqItemInput] = Field(default_factory=list, max_length=60)
    related_solutions: list[RelatedContentInput] = Field(default_factory=list, max_length=30)
    related_industries: list[RelatedContentInput] = Field(default_factory=list, max_length=30)
    related_projects: list[RelatedContentInput] = Field(default_factory=list, max_length=30)
    cta: CtaInput


PAGE_SCHEMAS: dict[PageType, type[StrictModel]] = {
    "solution": SolutionContentInput,
    "industry": IndustryContentInput,
    "case_study": CaseStudyContentInput,
    "guide": GuideContentInput,
}


class VersionInput(StrictModel):
    title: str = Field(min_length=2, max_length=250)
    summary: str = Field(min_length=3, max_length=5000)
    seo_title: str = Field(min_length=2, max_length=250)
    seo_description: str = Field(min_length=3, max_length=500)
    structured_content: dict[str, Any]
    media_references: list[MediaReferenceInput] = Field(default_factory=list, max_length=100)
    source_type: SourceType = "manual"
    source_reference_id: UUID | None = None
    source_filename: str | None = Field(default=None, max_length=500)
    source_checksum: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_source(self) -> VersionInput:
        if self.source_type != "manual" and self.source_reference_id is None:
            raise ValueError("A governed source reference is required for this source type.")
        return self


class CreatePublicContentInput(VersionInput):
    page_type: PageType
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=160)
    locale: Locale
    is_synthetic: bool = False


class PublicContentVersionResponse(StrictModel):
    id: UUID
    tenant_id: UUID
    public_content_item_id: UUID
    version_number: int
    origin: str
    title: str
    summary: str
    seo_title: str
    seo_description: str
    structured_content: dict[str, Any]
    media_references: list[dict[str, Any]]
    source_type: str
    source_reference_id: UUID | None
    source_filename: str | None
    source_checksum: str | None
    content_sha256: str
    based_on_version_id: UUID | None
    created_by: UUID
    created_at: datetime


class PublicContentItemResponse(StrictModel):
    id: UUID
    tenant_id: UUID
    page_type: str
    slug: str
    locale: str
    title: str
    summary: str
    seo_title: str
    seo_description: str
    canonical_path: str
    status: str
    is_synthetic: bool
    current_version_id: UUID | None
    approved_version_id: UUID | None
    published_version_id: UUID | None
    created_by: UUID
    approved_by: UUID | None
    published_by: UUID | None
    record_version: int
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    archived_at: datetime | None
    archived_by: UUID | None
    archive_reason: str | None
    current_version: PublicContentVersionResponse | None = None
    approved_version: PublicContentVersionResponse | None = None
    published_version: PublicContentVersionResponse | None = None


class ExactVersionInput(StrictModel):
    public_content_version_id: UUID
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    comment: str | None = Field(default=None, max_length=2000)


class ReviewDecisionInput(ExactVersionInput):
    decision: Literal["changes_requested", "approved", "rejected"]


class ReasonInput(StrictModel):
    reason: str = Field(min_length=3, max_length=2000)


class PublicContentDecisionResponse(StrictModel):
    id: UUID
    public_content_item_id: UUID
    public_content_version_id: UUID
    decision_type: str
    decided_by: UUID
    content_sha256: str
    comment: str | None
    created_at: datetime


class GovernanceCommandResponse(StrictModel):
    item: PublicContentItemResponse
    decision: PublicContentDecisionResponse | None = None


class PublicContentAuditResponse(StrictModel):
    id: UUID
    actor_membership_id: UUID
    action: str
    public_content_item_id: UUID
    public_content_version_id: UUID | None
    before_metadata: dict[str, Any]
    after_metadata: dict[str, Any]
    details: dict[str, Any]
    correlation_id: str | None
    created_at: datetime


class PublishedPublicContentResponse(StrictModel):
    page_type: PageType
    slug: str
    locale: Locale
    title: str
    summary: str
    seo_title: str
    seo_description: str
    canonical_path: str
    structured_content: dict[str, Any]


LEGACY_PUBLIC_PATHS = frozenset(
    {
        "/solutions/school-canteen-kitchen",
        "/industries/schools",
    }
)

RELATED_FIELDS: dict[PageType, tuple[str, ...]] = {
    "solution": ("related_industries", "related_projects"),
    "industry": ("relevant_solutions", "related_projects"),
    "case_study": ("related_solution", "related_industry"),
    "guide": ("related_solutions", "related_industries", "related_projects"),
}


def canonical_path(page_type: PageType, slug: str) -> str:
    prefix = {
        "solution": "solutions",
        "industry": "industries",
        "case_study": "projects",
        "guide": "guides",
    }[page_type]
    return f"/{prefix}/{slug}"


def validated_version_values(page_type: PageType, payload: VersionInput) -> dict[str, Any]:
    try:
        structured = PAGE_SCHEMAS[page_type].model_validate(payload.structured_content)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": error["loc"],
                    "msg": error["msg"],
                    "type": error["type"],
                }
                for error in exc.errors(include_context=False)
            ],
        ) from exc
    values = payload.model_dump(mode="python")
    values["structured_content"] = structured.model_dump(mode="json")
    values["media_references"] = [
        reference.model_dump(mode="json") for reference in payload.media_references
    ]
    return values


async def repository(session: AsyncSession, principal: Principal) -> PublicContentRepository:
    repo = PublicContentRepository(session, principal.tenant_id)
    await repo.set_tenant_context()
    return repo


def version_response(version: PublicContentVersion | None) -> PublicContentVersionResponse | None:
    return PublicContentVersionResponse.model_validate(version) if version else None


async def item_response(
    repo: PublicContentRepository, item: PublicContentItem
) -> PublicContentItemResponse:
    current = await repo.get_version(item.id, item.current_version_id)
    approved = await repo.get_version(item.id, item.approved_version_id)
    published = await repo.get_version(item.id, item.published_version_id)
    data = PublicContentItemResponse.model_validate(item).model_dump()
    data.update(
        current_version=version_response(current),
        approved_version=version_response(approved),
        published_version=version_response(published),
    )
    return PublicContentItemResponse.model_validate(data)


async def sanitize_related_content(
    repo: PublicContentRepository,
    *,
    locale: Locale,
    value: object,
) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    label = value.get("label")
    if not isinstance(label, str) or not label.strip():
        return None
    item_id: UUID | None = None
    raw_id = value.get("public_content_item_id")
    if isinstance(raw_id, str):
        try:
            item_id = UUID(raw_id)
        except ValueError:
            return None
    path = value.get("path") if isinstance(value.get("path"), str) else None
    if item_id is not None:
        target = await repo.get_published_relation(locale=locale, item_id=item_id)
        return {"label": label, "path": target.canonical_path} if target else None
    if path is None:
        return None
    target = await repo.get_published_relation(locale=locale, canonical_path=path)
    if target:
        return {"label": label, "path": target.canonical_path}
    if await repo.has_governed_path(locale=locale, canonical_path=path):
        return None
    if path in LEGACY_PUBLIC_PATHS:
        return {"label": label, "path": path}
    return None


async def sanitize_public_structure(
    repo: PublicContentRepository,
    *,
    page_type: PageType,
    locale: Locale,
    structured_content: dict[str, Any],
) -> dict[str, Any]:
    content = deepcopy(structured_content)
    for field in RELATED_FIELDS[page_type]:
        raw = content.get(field)
        if isinstance(raw, list):
            sanitized = [
                relation
                for value in raw
                if (relation := await sanitize_related_content(repo, locale=locale, value=value))
                is not None
            ]
            content[field] = sanitized
        else:
            content[field] = await sanitize_related_content(repo, locale=locale, value=raw)
    if page_type == "case_study":
        content["gallery_references"] = []
        facts = content.get("approved_project_facts")
        if isinstance(facts, list):
            content["approved_project_facts"] = [
                {"label": fact.get("label"), "value": fact.get("value")}
                for fact in facts
                if isinstance(fact, dict)
                and isinstance(fact.get("label"), str)
                and isinstance(fact.get("value"), str)
            ]
    return content


def handle_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PublicContentNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, PublicContentConcurrencyError):
        return HTTPException(status_code=412, detail=str(exc))
    return HTTPException(status_code=409, detail=str(exc))


@router.get(
    "/render/{page_type}/{slug}",
    response_model=PublishedPublicContentResponse,
    response_model_exclude_none=True,
)
async def render_published_public_content(
    page_type: PageType,
    slug: Annotated[
        str,
        Path(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=160),
    ],
    locale: Locale,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PublishedPublicContentResponse:
    tenant_id = UUID(get_settings().public_tenant_id)
    repo = PublicContentRepository(session, tenant_id)
    await repo.set_tenant_context()
    published = await repo.get_published_page(
        page_type=page_type,
        slug=slug,
        locale=locale,
    )
    if published is None:
        raise HTTPException(status_code=404, detail="Published public content not found.")
    item, version = published
    response.headers["Cache-Control"] = "public, max-age=30, stale-while-revalidate=60"
    return PublishedPublicContentResponse(
        page_type=cast(PageType, item.page_type),
        slug=item.slug,
        locale=cast(Locale, item.locale),
        title=version.title,
        summary=version.summary,
        seo_title=version.seo_title,
        seo_description=version.seo_description,
        canonical_path=item.canonical_path,
        structured_content=await sanitize_public_structure(
            repo,
            page_type=page_type,
            locale=locale,
            structured_content=version.structured_content,
        ),
    )


@router.post("/items", response_model=PublicContentItemResponse, status_code=201)
async def create_public_content(
    payload: CreatePublicContentInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("public_content:create"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)],
) -> PublicContentItemResponse:
    repo = await repository(session, principal)
    payload_hash = request_hash(payload.model_dump(mode="json"))
    scope = "public-content-create"
    existing = await existing_idempotent_response(
        session,
        principal=principal,
        scope=scope,
        key=idempotency_key,
        payload_hash=payload_hash,
    )
    if existing:
        response.status_code = existing.response_status
        return PublicContentItemResponse.model_validate(existing.response_body)
    try:
        version_values = validated_version_values(payload.page_type, payload)
        for field in ("page_type", "slug", "locale", "is_synthetic"):
            version_values.pop(field, None)
        item, _ = await repo.create_item(
            actor_id=principal.membership_id,
            item_values={
                "page_type": payload.page_type,
                "slug": payload.slug,
                "locale": payload.locale,
                "title": payload.title,
                "summary": payload.summary,
                "seo_title": payload.seo_title,
                "seo_description": payload.seo_description,
                "canonical_path": canonical_path(payload.page_type, payload.slug),
                "is_synthetic": payload.is_synthetic,
            },
            version_values=version_values,
        )
        result = await item_response(repo, item)
        save_idempotency(
            session,
            principal=principal,
            scope=scope,
            key=idempotency_key,
            payload_hash=payload_hash,
            status_code=201,
            body=result,
        )
        await session.commit()
        response.headers["ETag"] = f'"{result.record_version}"'
        return result
    except (IntegrityError, PublicContentStateError) as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Public content route already exists.") from exc


@router.get("/items", response_model=list[PublicContentItemResponse])
async def list_public_content(
    principal: Annotated[Principal, Depends(require_permission("public_content:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    status: str | None = None,
    page_type: PageType | None = None,
    locale: Locale | None = None,
    search: str | None = Query(default=None, max_length=200),
) -> list[PublicContentItemResponse]:
    repo = await repository(session, principal)
    return [
        await item_response(repo, item)
        for item in await repo.list_items(
            status=status, page_type=page_type, locale=locale, search=search
        )
    ]


@router.get("/items/{item_id}", response_model=PublicContentItemResponse)
async def get_public_content(
    item_id: UUID,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("public_content:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PublicContentItemResponse:
    repo = await repository(session, principal)
    try:
        result = await item_response(repo, await repo.get_item(item_id))
        response.headers["ETag"] = f'"{result.record_version}"'
        return result
    except PublicContentNotFoundError as exc:
        raise handle_error(exc) from exc


@router.get("/items/{item_id}/versions", response_model=list[PublicContentVersionResponse])
async def list_public_content_versions(
    item_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("public_content:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[PublicContentVersionResponse]:
    repo = await repository(session, principal)
    try:
        return [
            PublicContentVersionResponse.model_validate(version)
            for version in await repo.list_versions(item_id)
        ]
    except PublicContentNotFoundError as exc:
        raise handle_error(exc) from exc


@router.post("/items/{item_id}/versions", response_model=PublicContentItemResponse, status_code=201)
async def create_public_content_successor(
    item_id: UUID,
    payload: VersionInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("public_content:edit"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> PublicContentItemResponse:
    expected = parse_if_match(if_match)
    repo = await repository(session, principal)
    try:
        item = await repo.get_item(item_id)
        version_values = validated_version_values(cast(PageType, item.page_type), payload)
        payload_hash = request_hash({"item_id": item_id, **payload.model_dump(mode="json")})
        scope = f"public-content-{item_id}-version"
        existing = await existing_idempotent_response(
            session,
            principal=principal,
            scope=scope,
            key=idempotency_key,
            payload_hash=payload_hash,
        )
        if existing:
            response.status_code = existing.response_status
            return PublicContentItemResponse.model_validate(existing.response_body)
        item, _ = await repo.create_successor(
            item_id=item_id,
            expected_record_version=expected,
            actor_id=principal.membership_id,
            values=version_values,
        )
        result = await item_response(repo, item)
        save_idempotency(
            session,
            principal=principal,
            scope=scope,
            key=idempotency_key,
            payload_hash=payload_hash,
            status_code=201,
            body=result,
        )
        await session.commit()
        return result
    except (
        IntegrityError,
        PublicContentNotFoundError,
        PublicContentStateError,
        PublicContentConcurrencyError,
    ) as exc:
        await session.rollback()
        mapped = (
            PublicContentConcurrencyError("Public content changed; reload and retry.")
            if isinstance(exc, IntegrityError)
            else exc
        )
        raise handle_error(mapped) from exc


async def governed_command(
    *,
    command: Literal["submit", "decide", "publish"],
    item_id: UUID,
    payload: ExactVersionInput,
    response: Response,
    principal: Principal,
    session: AsyncSession,
    idempotency_key: str,
    expected: int,
    decision: str | None = None,
) -> GovernanceCommandResponse:
    repo = await repository(session, principal)
    payload_hash = request_hash(
        {
            "item_id": item_id,
            "command": command,
            "decision": decision,
            **payload.model_dump(mode="json"),
        }
    )
    scope = f"public-content-{item_id}-{command}-{decision or 'exact'}"
    existing = await existing_idempotent_response(
        session,
        principal=principal,
        scope=scope,
        key=idempotency_key,
        payload_hash=payload_hash,
    )
    if existing:
        response.status_code = existing.response_status
        return GovernanceCommandResponse.model_validate(existing.response_body)
    try:
        if command == "submit":
            item, recorded = await repo.submit_review(
                item_id=item_id,
                version_id=payload.public_content_version_id,
                checksum=payload.content_sha256,
                expected_record_version=expected,
                actor_id=principal.membership_id,
                comment=payload.comment,
            )
        elif command == "publish":
            item, recorded = await repo.publish(
                item_id=item_id,
                version_id=payload.public_content_version_id,
                checksum=payload.content_sha256,
                expected_record_version=expected,
                actor_id=principal.membership_id,
                comment=payload.comment,
            )
        else:
            if decision is None:
                raise PublicContentStateError("A review decision is required.")
            item, recorded = await repo.decide(
                item_id=item_id,
                version_id=payload.public_content_version_id,
                checksum=payload.content_sha256,
                decision_type=decision,
                expected_record_version=expected,
                actor_id=principal.membership_id,
                comment=payload.comment,
            )
        result = GovernanceCommandResponse(
            item=await item_response(repo, item),
            decision=PublicContentDecisionResponse.model_validate(recorded),
        )
        save_idempotency(
            session,
            principal=principal,
            scope=scope,
            key=idempotency_key,
            payload_hash=payload_hash,
            status_code=200,
            body=result,
        )
        await session.commit()
        return result
    except (
        PublicContentNotFoundError,
        PublicContentStateError,
        PublicContentConcurrencyError,
        PublicContentSeparationOfDutiesError,
    ) as exc:
        await session.rollback()
        raise handle_error(exc) from exc


@router.post("/items/{item_id}/submit-review", response_model=GovernanceCommandResponse)
async def submit_public_content_review(
    item_id: UUID,
    payload: ExactVersionInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("public_content:submit_review"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> GovernanceCommandResponse:
    return await governed_command(
        command="submit",
        item_id=item_id,
        payload=payload,
        response=response,
        principal=principal,
        session=session,
        idempotency_key=idempotency_key,
        expected=parse_if_match(if_match),
    )


@router.post("/items/{item_id}/decisions", response_model=GovernanceCommandResponse)
async def decide_public_content_review(
    item_id: UUID,
    payload: ReviewDecisionInput,
    response: Response,
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> GovernanceCommandResponse:
    required = (
        "public_content:approve"
        if payload.decision in {"approved", "rejected"}
        else "public_content:review"
    )
    if required not in principal.permissions:
        raise HTTPException(status_code=403, detail="This action is not permitted.")
    return await governed_command(
        command="decide",
        item_id=item_id,
        payload=payload,
        response=response,
        principal=principal,
        session=session,
        idempotency_key=idempotency_key,
        expected=parse_if_match(if_match),
        decision=payload.decision,
    )


@router.post("/items/{item_id}/publish", response_model=GovernanceCommandResponse)
async def publish_public_content(
    item_id: UUID,
    payload: ExactVersionInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("public_content:publish"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> GovernanceCommandResponse:
    return await governed_command(
        command="publish",
        item_id=item_id,
        payload=payload,
        response=response,
        principal=principal,
        session=session,
        idempotency_key=idempotency_key,
        expected=parse_if_match(if_match),
    )


async def lifecycle_command(
    *,
    item_id: UUID,
    payload: ReasonInput,
    response: Response,
    principal: Principal,
    session: AsyncSession,
    idempotency_key: str,
    expected: int,
    restore: bool,
) -> PublicContentItemResponse:
    repo = await repository(session, principal)
    action = "restore" if restore else "archive"
    payload_hash = request_hash({"item_id": item_id, "action": action, "reason": payload.reason})
    scope = f"public-content-{item_id}-{action}"
    existing = await existing_idempotent_response(
        session,
        principal=principal,
        scope=scope,
        key=idempotency_key,
        payload_hash=payload_hash,
    )
    if existing:
        response.status_code = existing.response_status
        return PublicContentItemResponse.model_validate(existing.response_body)
    try:
        operation = repo.restore if restore else repo.archive
        item = await operation(
            item_id=item_id,
            expected_record_version=expected,
            actor_id=principal.membership_id,
            reason=payload.reason,
        )
        result = await item_response(repo, item)
        save_idempotency(
            session,
            principal=principal,
            scope=scope,
            key=idempotency_key,
            payload_hash=payload_hash,
            status_code=200,
            body=result,
        )
        await session.commit()
        return result
    except (
        PublicContentNotFoundError,
        PublicContentStateError,
        PublicContentConcurrencyError,
    ) as exc:
        await session.rollback()
        raise handle_error(exc) from exc


@router.post("/items/{item_id}/archive", response_model=PublicContentItemResponse)
async def archive_public_content(
    item_id: UUID,
    payload: ReasonInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("public_content:archive"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> PublicContentItemResponse:
    return await lifecycle_command(
        item_id=item_id,
        payload=payload,
        response=response,
        principal=principal,
        session=session,
        idempotency_key=idempotency_key,
        expected=parse_if_match(if_match),
        restore=False,
    )


@router.post("/items/{item_id}/restore", response_model=PublicContentItemResponse)
async def restore_public_content(
    item_id: UUID,
    payload: ReasonInput,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("public_content:publish"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> PublicContentItemResponse:
    return await lifecycle_command(
        item_id=item_id,
        payload=payload,
        response=response,
        principal=principal,
        session=session,
        idempotency_key=idempotency_key,
        expected=parse_if_match(if_match),
        restore=True,
    )


@router.get("/items/{item_id}/decisions", response_model=list[PublicContentDecisionResponse])
async def list_public_content_decisions(
    item_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("public_content:audit_read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[PublicContentDecisionResponse]:
    repo = await repository(session, principal)
    try:
        return [
            PublicContentDecisionResponse.model_validate(decision)
            for decision in await repo.list_decisions(item_id)
        ]
    except PublicContentNotFoundError as exc:
        raise handle_error(exc) from exc


@router.get("/items/{item_id}/audit", response_model=list[PublicContentAuditResponse])
async def list_public_content_audit(
    item_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("public_content:audit_read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[PublicContentAuditResponse]:
    repo = await repository(session, principal)
    try:
        return [
            PublicContentAuditResponse.model_validate(entry)
            for entry in await repo.list_audit(item_id)
        ]
    except PublicContentNotFoundError as exc:
        raise handle_error(exc) from exc
