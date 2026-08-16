from __future__ import annotations

import re
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Reference(StrictModel):
    chunk_id: UUID


class ArticleSection(StrictModel):
    heading: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=5000)


class WebsiteArticle(StrictModel):
    content_type: Literal["website_article"]
    title: str
    summary: str
    sections: list[ArticleSection] = Field(min_length=1, max_length=12)
    call_to_action: str
    references: list[Reference] = Field(min_length=1, max_length=20)


class VideoScene(StrictModel):
    visual: str
    voiceover: str
    on_screen_text: str


class TikTokScript(StrictModel):
    content_type: Literal["tiktok_script"]
    title: str
    hook: str
    scenes: list[VideoScene] = Field(min_length=1, max_length=12)
    call_to_action: str
    references: list[Reference] = Field(min_length=1, max_length=20)


class InstagramReelScript(StrictModel):
    content_type: Literal["instagram_reel_script"]
    title: str
    hook: str
    scenes: list[VideoScene] = Field(min_length=1, max_length=12)
    caption: str
    call_to_action: str
    references: list[Reference] = Field(min_length=1, max_length=20)


class FacebookPost(StrictModel):
    content_type: Literal["facebook_post"]
    headline: str
    body: str
    call_to_action: str
    hashtags: list[str] = Field(default_factory=list, max_length=10)
    references: list[Reference] = Field(min_length=1, max_length=20)


class EmailDraft(StrictModel):
    content_type: Literal["email_draft"]
    subject: str
    preview_text: str
    greeting: str
    body_sections: list[str] = Field(min_length=1, max_length=8)
    call_to_action: str
    closing: str
    references: list[Reference] = Field(min_length=1, max_length=20)


MarketingDraft = Annotated[
    WebsiteArticle | TikTokScript | InstagramReelScript | FacebookPost | EmailDraft,
    Field(discriminator="content_type"),
]
MARKETING_DRAFT_ADAPTER: TypeAdapter[MarketingDraft] = TypeAdapter(MarketingDraft)


class MarketingDraftEnvelope(StrictModel):
    draft: MarketingDraft


class MarketingEvidence(StrictModel):
    document_id: UUID
    document_name: str
    document_version_id: UUID
    document_version: int
    chunk_id: UUID
    page_number: int | None
    section: str | None
    similarity_score: float
    content: str


class MarketingGenerationResult(StrictModel):
    outcome: Literal["generated", "insufficient_evidence"]
    evidence_status: Literal["sufficient", "insufficient", "conflicting"]
    message: str
    asset_id: UUID | None = None
    version_id: UUID | None = None
    content: dict[str, object] | None = None
    citations: list[dict[str, object]] = Field(default_factory=list)


def validate_draft(
    raw: object, expected_type: str, evidence: list[MarketingEvidence]
) -> MarketingDraft:
    draft = MARKETING_DRAFT_ADAPTER.validate_python(raw)
    if draft.content_type != expected_type:
        raise ValueError("Generated content type does not match the request.")
    allowed = {item.chunk_id for item in evidence}
    cited = {item.chunk_id for item in draft.references}
    if not cited or not cited.issubset(allowed):
        raise ValueError("Generated references must identify retrieved evidence only.")
    _validate_protected_claims(plain_text(draft), evidence)
    return draft


def plain_text(draft: MarketingDraft) -> str:
    if isinstance(draft, WebsiteArticle):
        return "\n\n".join(
            [
                draft.title,
                draft.summary,
                *[f"{s.heading}\n{s.body}" for s in draft.sections],
                draft.call_to_action,
            ]
        )
    if isinstance(draft, (TikTokScript, InstagramReelScript)):
        parts = [draft.title, draft.hook]
        parts.extend(f"{s.visual}\n{s.voiceover}\n{s.on_screen_text}" for s in draft.scenes)
        if isinstance(draft, InstagramReelScript):
            parts.append(draft.caption)
        parts.append(draft.call_to_action)
        return "\n\n".join(parts)
    if isinstance(draft, FacebookPost):
        return "\n\n".join(
            [draft.headline, draft.body, draft.call_to_action, " ".join(draft.hashtags)]
        )
    return "\n\n".join(
        [
            draft.subject,
            draft.preview_text,
            draft.greeting,
            *draft.body_sections,
            draft.call_to_action,
            draft.closing,
        ]
    )


FORBIDDEN_REQUEST_TERMS = {
    "price",
    "pricing",
    "discount",
    "margin",
    "supplier",
    "warranty",
    "guarantee",
    "报价",
    "价格",
    "折扣",
    "利润",
    "供应商",
    "质保",
    "保证",
}


def contains_forbidden_request(*values: str) -> bool:
    combined = " ".join(values).casefold()
    return any(term in combined for term in FORBIDDEN_REQUEST_TERMS)


_PROTECTED_PATTERNS = (
    re.compile(r"(?:[$€£¥]|\b(?:usd|idr|rmb|cny)\b)\s*\d", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?\s*(?:sqm|m2|m²|kg|units?|days?|weeks?|months?)\b", re.IGNORECASE),
    re.compile(r"\b(?:iso\s*\d+|certified|certification|warranty|guarantee)\b", re.IGNORECASE),
    re.compile(r"(?:认证|质保|保证|交付)"),
)


def _validate_protected_claims(text: str, evidence: list[MarketingEvidence]) -> None:
    source = "\n".join(item.content for item in evidence).casefold()
    for pattern in _PROTECTED_PATTERNS:
        for match in pattern.finditer(text):
            if match.group(0).casefold() not in source:
                raise ValueError("Generated draft contains an unsupported protected claim.")
