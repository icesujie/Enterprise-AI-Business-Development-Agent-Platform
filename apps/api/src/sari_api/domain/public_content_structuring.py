from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

PageType = Literal["solution", "industry", "case_study", "guide", "product"]
Outcome = Literal["ready", "requires_human_input", "insufficient_source"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class StructuredSection(StrictModel):
    title: str
    description: str


class CtaSuggestion(StrictModel):
    label: str
    description: str
    destination: Literal["public_consultation_agent", "contact_form"]


class RelatedPageSuggestion(StrictModel):
    page_type: PageType
    label: str
    source_reason: str
    suggested_path: str | None = None


class ApprovedFact(StrictModel):
    label: str
    value: str
    source_note: str | None = None


class FaqItem(StrictModel):
    question: str
    answer: str


class SolutionDraftContent(StrictModel):
    page_type: Literal["solution"] = "solution"
    overview: list[str] = Field(default_factory=list)
    customer_needs: list[str] = Field(default_factory=list)
    service_scope: list[StructuredSection] = Field(default_factory=list)
    workflow_areas: list[StructuredSection] = Field(default_factory=list)
    related_page_suggestions: list[RelatedPageSuggestion] = Field(default_factory=list)
    cta: CtaSuggestion


class IndustryDraftContent(StrictModel):
    page_type: Literal["industry"] = "industry"
    overview: list[str] = Field(default_factory=list)
    business_needs: list[str] = Field(default_factory=list)
    project_considerations: list[StructuredSection] = Field(default_factory=list)
    related_page_suggestions: list[RelatedPageSuggestion] = Field(default_factory=list)
    cta: CtaSuggestion


class CaseStudyDraftContent(StrictModel):
    page_type: Literal["case_study"] = "case_study"
    project_overview: list[str] = Field(default_factory=list)
    location: str | None = None
    industry: str | None = None
    project_type: str | None = None
    project_requirements: list[str] = Field(default_factory=list)
    scope_of_work: list[StructuredSection] = Field(default_factory=list)
    functional_areas: list[StructuredSection] = Field(default_factory=list)
    delivery_approach: list[StructuredSection] = Field(default_factory=list)
    approved_project_facts: list[ApprovedFact] = Field(default_factory=list)
    related_page_suggestions: list[RelatedPageSuggestion] = Field(default_factory=list)
    cta: CtaSuggestion


class GuideDraftContent(StrictModel):
    page_type: Literal["guide"] = "guide"
    introduction: list[str] = Field(default_factory=list)
    sections: list[StructuredSection] = Field(default_factory=list)
    faq_items: list[FaqItem] = Field(default_factory=list)
    related_page_suggestions: list[RelatedPageSuggestion] = Field(default_factory=list)
    cta: CtaSuggestion


class ProductSpecification(StrictModel):
    label: str
    value: str


class ProductDraftContent(StrictModel):
    page_type: Literal["product"] = "product"
    product_name: str | None = None
    sku_model: str | None = None
    category: str | None = None
    brand: str | None = None
    short_description: str | None = None
    detailed_description: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    applications: list[str] = Field(default_factory=list)
    material: str | None = None
    dimensions: str | None = None
    configuration: str | None = None
    specifications: list[ProductSpecification] = Field(default_factory=list)
    price_mode: Literal["fixed", "starting_from", "range", "request_quote"] = "request_quote"
    currency: str | None = None
    price_min: Decimal | None = None
    price_max: Decimal | None = None
    price_note: str | None = None
    moq: str | None = None
    availability_note: str | None = None
    hero_media_asset_id: UUID | None = None
    gallery_media_asset_ids: list[UUID] = Field(default_factory=list)
    drawing_media_asset_ids: list[UUID] = Field(default_factory=list)
    related_page_suggestions: list[RelatedPageSuggestion] = Field(default_factory=list)
    inquiry_cta: CtaSuggestion
    quote_cta: CtaSuggestion


DraftContent = Annotated[
    SolutionDraftContent
    | IndustryDraftContent
    | CaseStudyDraftContent
    | GuideDraftContent
    | ProductDraftContent,
    Field(discriminator="page_type"),
]


class FieldEvidence(StrictModel):
    field_path: str
    import_id: UUID
    block_order: int | None = None
    source_section: str | None = None
    source_page: int | None = None
    media_asset_id: UUID | None = None


class MediaSuggestion(StrictModel):
    media_asset_id: UUID
    role: Literal["hero", "gallery"]
    order: int
    source_page: int | None = None
    source_section: str | None = None


class ProductCandidate(StrictModel):
    candidate_key: str
    slug_suggestion: str
    title: str | None = None
    summary: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    content: ProductDraftContent
    missing_fields: list[str] = Field(default_factory=list)
    media_suggestions: list[MediaSuggestion] = Field(default_factory=list)
    evidence: list[FieldEvidence] = Field(default_factory=list)


class PublicContentStructuringResult(StrictModel):
    recommended_page_type: PageType
    selected_page_type: PageType
    outcome: Outcome
    title: str | None = None
    summary: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    content: DraftContent
    missing_fields: list[str] = Field(default_factory=list)
    media_suggestions: list[MediaSuggestion] = Field(default_factory=list)
    evidence: list[FieldEvidence] = Field(default_factory=list)
    multiple_products_detected: bool = False
    product_candidates: list[ProductCandidate] = Field(default_factory=list)


def cms_structured_content(result: PublicContentStructuringResult) -> dict[str, object]:
    if result.selected_page_type == "product":
        return product_cms_structured_content(result.content)
    content = result.content.model_dump(mode="json")
    content.pop("page_type", None)
    content.pop("related_page_suggestions", None)
    if result.selected_page_type == "solution":
        content["related_industries"] = []
        content["related_projects"] = []
    elif result.selected_page_type == "industry":
        content["relevant_solutions"] = []
        content["related_projects"] = []
    elif result.selected_page_type == "case_study":
        content["location"] = content.get("location") or ""
        content["industry"] = content.get("industry") or ""
        content["project_type"] = content.get("project_type") or ""
        content["gallery_references"] = []
        content["related_solution"] = None
        content["related_industry"] = None
    else:
        content["related_solutions"] = []
        content["related_industries"] = []
        content["related_projects"] = []
    return content


def product_cms_structured_content(content: DraftContent) -> dict[str, object]:
    if not isinstance(content, ProductDraftContent):
        raise ValueError("Product CMS content requires a Product draft candidate.")
    values = content.model_dump(mode="json")
    values.pop("page_type", None)
    values.pop("related_page_suggestions", None)
    values["product_name"] = values.get("product_name") or ""
    values["sku_model"] = values.get("sku_model") or ""
    values["category"] = values.get("category") or ""
    values["short_description"] = values.get("short_description") or ""
    values["related_products"] = []
    values["related_solution"] = None
    values["related_industry"] = None
    values["related_guide"] = None
    values["related_project"] = None
    return values
