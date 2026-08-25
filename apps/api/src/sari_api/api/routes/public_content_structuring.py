from __future__ import annotations

import time
from functools import lru_cache
from typing import Annotated, Any, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.database import get_session
from sari_api.adapters.public_content_import_repository import (
    PublicContentImportNotFoundError,
    PublicContentImportRepository,
)
from sari_api.adapters.public_content_repository import (
    PublicContentRepository,
    PublicContentStateError,
)
from sari_api.adapters.public_content_structuring_provider import (
    PublicContentStructuringProvider,
    build_public_content_structuring_provider,
)
from sari_api.adapters.public_content_structuring_repository import (
    PublicContentStructuringRepository,
    PublicContentStructuringRunNotFoundError,
)
from sari_api.api.dependencies import require_permission
from sari_api.api.routes.content_governance import (
    existing_idempotent_response,
    request_hash,
    save_idempotency,
)
from sari_api.api.routes.public_content import (
    CreatePublicContentInput,
    MediaReferenceInput,
    PublicContentItemResponse,
    SourceType,
    canonical_path,
    item_response,
    validated_version_values,
)
from sari_api.api.routes.public_content import (
    Locale as PublicContentLocale,
)
from sari_api.core.config import get_settings
from sari_api.core.observability import get_correlation_id
from sari_api.domain.identity import Principal
from sari_api.domain.public_content_structuring import (
    PageType,
    PublicContentStructuringResult,
    cms_structured_content,
    product_cms_structured_content,
)

router = APIRouter(prefix="/api/v1/public-content/imports", tags=["public-content-structuring"])
Locale = Literal["en", "zh-CN"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, from_attributes=True)


class StructuringRequest(StrictModel):
    page_type: PageType
    locale: Locale


class StructuringRunResponse(StrictModel):
    id: UUID
    tenant_id: UUID
    public_content_import_id: UUID
    requested_by: UUID
    selected_page_type: str
    recommended_page_type: str | None
    provider: str
    model: str
    locale: str
    status: str
    outcome: str | None
    result: dict[str, Any]
    missing_fields: list[str]
    failure_reason: str | None
    duration_ms: int | None
    correlation_id: str | None


class CreateImportedDraftRequest(StrictModel):
    structuring_run_id: UUID
    product_candidate_key: str | None = Field(
        default=None, pattern=r"^product-[1-9][0-9]*$", max_length=40
    )
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=160)
    title: str = Field(min_length=2, max_length=250)
    summary: str = Field(min_length=3, max_length=5000)
    seo_title: str = Field(min_length=2, max_length=250)
    seo_description: str = Field(min_length=3, max_length=500)
    structured_content: dict[str, Any]
    media_references: list[MediaReferenceInput] = Field(default_factory=list, max_length=100)
    is_synthetic: bool = False


@lru_cache
def get_public_content_structuring_provider() -> PublicContentStructuringProvider:
    return build_public_content_structuring_provider(get_settings())


async def _repositories(
    session: AsyncSession, principal: Principal
) -> tuple[PublicContentImportRepository, PublicContentStructuringRepository]:
    imports = PublicContentImportRepository(session, principal.tenant_id)
    runs = PublicContentStructuringRepository(session, principal.tenant_id)
    await imports.set_tenant_context()
    return imports, runs


@router.post("/{import_id}/structure", response_model=StructuringRunResponse, status_code=201)
async def structure_import(
    import_id: UUID,
    payload: StructuringRequest,
    principal: Annotated[Principal, Depends(require_permission("public_content:structure"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    provider: Annotated[
        PublicContentStructuringProvider,
        Depends(get_public_content_structuring_provider),
    ],
) -> StructuringRunResponse:
    imports, runs = await _repositories(session, principal)
    try:
        imported = await imports.get(import_id)
    except PublicContentImportNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if imported.processing_status != "completed":
        raise HTTPException(status_code=409, detail="Only completed imports can be structured.")
    run = await runs.create_run(
        import_id=import_id,
        requested_by=principal.membership_id,
        selected_page_type=payload.page_type,
        provider=provider.provider_type,
        model=provider.model_id,
        locale=payload.locale,
        correlation_id=get_correlation_id(),
    )
    await session.commit()
    started = time.perf_counter()
    try:
        result = await provider.structure(
            import_id=import_id,
            import_result=imported.extraction_result,
            selected_page_type=payload.page_type,
            locale=payload.locale,
        )
        _validate_grounding(
            result,
            imported.extraction_result,
            imported.extracted_media_ids,
            payload.page_type,
        )
        duration = round((time.perf_counter() - started) * 1000)
        await runs.set_tenant_context()
        serialized_result = result.model_dump(mode="json")
        serialized_result["cms_structured_content"] = cms_structured_content(result)
        if result.selected_page_type == "product":
            serialized_result["product_candidates"] = [
                {
                    **candidate.model_dump(mode="json"),
                    "cms_structured_content": product_cms_structured_content(candidate.content),
                }
                for candidate in result.product_candidates
            ]
        run = await runs.complete(
            run.id,
            recommended_page_type=result.recommended_page_type,
            outcome=result.outcome,
            result=serialized_result,
            missing_fields=result.missing_fields,
            duration_ms=duration,
        )
        await session.commit()
        return StructuringRunResponse.model_validate(run)
    except Exception as exc:
        await session.rollback()
        duration = round((time.perf_counter() - started) * 1000)
        await runs.set_tenant_context()
        await runs.fail(run.id, reason="Content structuring failed safely.", duration_ms=duration)
        await session.commit()
        raise HTTPException(status_code=502, detail="Content structuring failed safely.") from exc


@router.get("/{import_id}/structuring-runs", response_model=list[StructuringRunResponse])
async def list_structuring_runs(
    import_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("public_content:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[StructuringRunResponse]:
    imports, runs = await _repositories(session, principal)
    try:
        await imports.get(import_id)
    except PublicContentImportNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        StructuringRunResponse.model_validate(run) for run in await runs.list_for_import(import_id)
    ]


@router.post("/{import_id}/drafts", response_model=PublicContentItemResponse, status_code=201)
async def create_imported_draft(
    import_id: UUID,
    payload: CreateImportedDraftRequest,
    response: Response,
    principal: Annotated[Principal, Depends(require_permission("public_content:create"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)],
) -> PublicContentItemResponse:
    imports, runs = await _repositories(session, principal)
    try:
        imported = await imports.get(import_id)
        run = await runs.get(payload.structuring_run_id)
    except (PublicContentImportNotFoundError, PublicContentStructuringRunNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if imported.processing_status != "completed" or run.status != "completed":
        raise HTTPException(status_code=409, detail="A completed structuring run is required.")
    if run.outcome == "insufficient_source":
        raise HTTPException(
            status_code=409,
            detail="Insufficient source evidence cannot create a Public Content Draft.",
        )
    if run.public_content_import_id != import_id:
        raise HTTPException(
            status_code=409, detail="Structuring run does not belong to this import."
        )
    _validate_product_candidate_selection(run.result, payload)
    _validate_media_ids(payload, imported.extracted_media_ids)
    source_type = {
        "docx": "docx_import",
        "pdf": "pdf_import",
        "html": "html_import",
        "txt": "text_import",
        "markdown": "text_import",
    }[imported.source_type]
    create_payload = CreatePublicContentInput(
        page_type=cast(PageType, run.selected_page_type),
        slug=payload.slug,
        locale=cast(PublicContentLocale, run.locale),
        title=payload.title,
        summary=payload.summary,
        seo_title=payload.seo_title,
        seo_description=payload.seo_description,
        structured_content=payload.structured_content,
        media_references=payload.media_references,
        source_type=cast(SourceType, source_type),
        source_reference_id=imported.id,
        source_filename=imported.original_filename,
        source_checksum=imported.checksum,
        is_synthetic=payload.is_synthetic,
    )
    payload_hash = request_hash(payload.model_dump(mode="json"))
    scope = f"public-content-import-draft-{import_id}"
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
    public_repo = PublicContentRepository(session, principal.tenant_id)
    page_type = cast(PageType, run.selected_page_type)
    try:
        version_values = validated_version_values(page_type, create_payload)
        for field in ("page_type", "slug", "locale", "is_synthetic"):
            version_values.pop(field, None)
        version_values["source_structuring_run_id"] = run.id
        version_values["source_candidate_key"] = payload.product_candidate_key
        item, _ = await public_repo.create_item(
            actor_id=principal.membership_id,
            item_values={
                "page_type": run.selected_page_type,
                "slug": payload.slug,
                "locale": run.locale,
                "title": payload.title,
                "summary": payload.summary,
                "seo_title": payload.seo_title,
                "seo_description": payload.seo_description,
                "canonical_path": canonical_path(page_type, payload.slug),
                "is_synthetic": payload.is_synthetic,
            },
            version_values=version_values,
            version_origin="ai_draft",
        )
        result = await item_response(public_repo, item)
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
    except (IntegrityError, PublicContentStateError) as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Public content route already exists.") from exc


def _validate_grounding(
    result: PublicContentStructuringResult,
    import_result: dict[str, object],
    extracted_media_ids: list[str],
    requested_page_type: PageType,
) -> None:
    raw_blocks = import_result.get("blocks")
    blocks = raw_blocks if isinstance(raw_blocks, list) else []
    valid_orders = {
        int(block["order"])
        for block in blocks
        if isinstance(block, dict) and isinstance(block.get("order"), int)
    }
    if result.selected_page_type != requested_page_type:
        raise ValueError("Provider changed the human-selected page type.")
    if result.selected_page_type != result.content.page_type:
        raise ValueError("Structured content type does not match the selected page type.")
    for evidence in result.evidence:
        if evidence.block_order is not None and evidence.block_order not in valid_orders:
            raise ValueError("Structuring result contains invalid source evidence.")
    allowed_media = set(extracted_media_ids)
    if any(str(value.media_asset_id) not in allowed_media for value in result.media_suggestions):
        raise ValueError("Structuring result contains media outside the source import.")
    if result.outcome != "insufficient_source" and not result.evidence:
        raise ValueError("A structured result requires source evidence.")
    if result.selected_page_type == "product":
        _validate_product_grounding(result, blocks)


def _validate_media_ids(
    payload: CreateImportedDraftRequest, extracted_media_ids: list[str]
) -> None:
    allowed = set(extracted_media_ids)
    references = [str(reference.media_asset_id) for reference in payload.media_references]
    gallery = payload.structured_content.get("gallery_references")
    if isinstance(gallery, list):
        references.extend(
            str(value.get("media_asset_id")) for value in gallery if isinstance(value, dict)
        )
    for field in (
        "hero_media_asset_id",
        "gallery_media_asset_ids",
        "drawing_media_asset_ids",
    ):
        value = payload.structured_content.get(field)
        if isinstance(value, list):
            references.extend(str(item) for item in value)
        elif value:
            references.append(str(value))
    if any(reference not in allowed for reference in references):
        raise HTTPException(
            status_code=422,
            detail="Draft media must come from the exact source import.",
        )


def _validate_product_candidate_selection(
    result: dict[str, Any], payload: CreateImportedDraftRequest
) -> None:
    if result.get("selected_page_type") != "product":
        if payload.product_candidate_key is not None:
            raise HTTPException(
                status_code=422,
                detail="Product candidate selection is only valid for Product structuring.",
            )
        return
    candidates = result.get("product_candidates")
    candidate_keys = (
        {
            str(candidate.get("candidate_key"))
            for candidate in candidates
            if isinstance(candidate, dict) and candidate.get("candidate_key")
        }
        if isinstance(candidates, list)
        else set()
    )
    if result.get("multiple_products_detected") and payload.product_candidate_key is None:
        raise HTTPException(
            status_code=409,
            detail="Select one Product candidate before creating a Draft.",
        )
    if payload.product_candidate_key and payload.product_candidate_key not in candidate_keys:
        raise HTTPException(status_code=422, detail="Selected Product candidate is invalid.")


def _validate_product_grounding(
    result: PublicContentStructuringResult, blocks: list[object]
) -> None:
    candidates = result.product_candidates
    if not candidates:
        raise ValueError("Product structuring requires at least one candidate.")
    if result.multiple_products_detected != (len(candidates) > 1):
        raise ValueError("Multiple-product detection does not match the candidate set.")
    source_by_order = {
        int(block["order"]): str(block.get("text", "")).casefold()
        for block in blocks
        if isinstance(block, dict) and isinstance(block.get("order"), int)
    }
    evidence = {item.field_path: item for item in result.evidence}
    sensitive = (
        "sku_model",
        "brand",
        "material",
        "dimensions",
        "configuration",
        "currency",
        "price_min",
        "price_max",
        "moq",
        "availability_note",
    )
    for candidate in candidates:
        prefix = f"product_candidates.{candidate.candidate_key}.content"
        for field in sensitive:
            value = getattr(candidate.content, field)
            if value is None or value == "":
                continue
            proof = evidence.get(f"{prefix}.{field}")
            if proof is None or proof.block_order is None:
                raise ValueError(f"Product field {field} lacks exact source evidence.")
            source = source_by_order.get(proof.block_order, "")
            normalized = str(value).replace(",", "").casefold()
            normalized_source = source.replace(",", "")
            if normalized not in normalized_source:
                raise ValueError(f"Product field {field} is not present in its source evidence.")
        for index, specification in enumerate(candidate.content.specifications):
            proof = evidence.get(f"{prefix}.specifications[{index}]")
            if proof is None or proof.block_order is None:
                raise ValueError("Product specification lacks exact source evidence.")
            source = source_by_order.get(proof.block_order, "").casefold()
            if specification.value.casefold() not in source:
                raise ValueError("Product specification is not present in its source evidence.")
