from __future__ import annotations

import re
from difflib import SequenceMatcher
from statistics import mean
from typing import Any

from pydantic import BaseModel, ConfigDict

from sari_api.domain.marketing_content_generation import MarketingDraft, plain_text


class EvaluationOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grounding_correct: bool
    citations_complete: bool
    unsupported_claim: bool
    insufficient_handled: bool
    structure_valid: bool
    bilingual_consistent: bool


def summarize(outcomes: list[EvaluationOutcome]) -> dict[str, float]:
    total = len(outcomes)
    if total == 0:
        return {}
    return {
        "grounding_accuracy": sum(item.grounding_correct for item in outcomes) / total,
        "citation_completeness": sum(item.citations_complete for item in outcomes) / total,
        "unsupported_claim_rate": sum(item.unsupported_claim for item in outcomes) / total,
        "insufficient_evidence_accuracy": sum(item.insufficient_handled for item in outcomes)
        / total,
        "structural_validity": sum(item.structure_valid for item in outcomes) / total,
        "bilingual_consistency": sum(item.bilingual_consistent for item in outcomes) / total,
    }


class MarketingQualityEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand_fit: int
    audience_fit: int
    channel_fit: int
    clarity: int
    cta_quality: int
    factual_grounding: int
    unsupported_claims: int
    repetition: int
    content_usefulness: int
    overall_score: float
    issues: list[str]


class BusinessEvaluationOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    scenario: str
    content_type: str
    language: str
    quality: MarketingQualityEvaluation
    structure_valid: bool
    citation_complete: bool
    bilingual_pair_id: str


AUDIENCE_TERMS: dict[str, tuple[str, ...]] = {
    "schools": ("school", "canteen", "学校", "食堂"),
    "hospitals": ("hospital", "institutional", "医院", "机构"),
    "factories": ("factory", "workforce", "工厂", "员工"),
    "central_kitchens": ("central kitchen", "capacity planning", "中央厨房", "产能规划"),
    "project_owners": ("project owner", "业主"),
    "facility_managers": ("facility", "设施"),
}


def evaluate_business_quality(
    draft: MarketingDraft,
    request: dict[str, object],
    citations: list[dict[str, Any]],
) -> MarketingQualityEvaluation:
    text = plain_text(draft)
    normalized = text.casefold()
    topic = str(request.get("topic", "")).casefold()
    audience = str(request.get("audience", ""))
    cta = str(request.get("call_to_action", "")).strip()
    issues: list[str] = []

    brand_fit = 90 if "sari arta" in normalized else 65
    if brand_fit < 80:
        issues.append("brand_identity_not_explicit")

    audience_terms = AUDIENCE_TERMS.get(audience, ())
    audience_fit = 90 if any(term in f"{normalized} {topic}" for term in audience_terms) else 60
    if audience_fit < 80:
        issues.append("audience_context_too_generic")

    channel_fit = 95
    word_count = len(re.findall(r"[\w\u3400-\u9fff]+", text))
    clarity = 90 if 20 <= word_count <= 700 else 70
    if clarity < 80:
        issues.append("content_length_needs_review")

    cta_quality = 95 if len(cta) >= 8 and cta.casefold() in normalized else 65
    if cta_quality < 80:
        issues.append("weak_or_missing_cta")

    reference_ids = {str(item.chunk_id) for item in draft.references}
    citation_ids = {str(item.get("chunk_id")) for item in citations}
    factual_grounding = 100 if reference_ids and reference_ids.issubset(citation_ids) else 40
    unsupported_claims = 0 if factual_grounding == 100 else 100
    if factual_grounding < 80:
        issues.append("citation_mapping_incomplete")

    repetition = _repetition_score(text)
    if repetition < 75:
        issues.append("repetitive_content")

    usefulness = round(
        mean([brand_fit, audience_fit, channel_fit, clarity, cta_quality, factual_grounding])
    )
    if usefulness < 75:
        issues.append("limited_business_usefulness")
    overall = round(
        mean(
            [
                brand_fit,
                audience_fit,
                channel_fit,
                clarity,
                cta_quality,
                factual_grounding,
                100 - unsupported_claims,
                repetition,
                usefulness,
            ]
        ),
        2,
    )
    return MarketingQualityEvaluation(
        brand_fit=brand_fit,
        audience_fit=audience_fit,
        channel_fit=channel_fit,
        clarity=clarity,
        cta_quality=cta_quality,
        factual_grounding=factual_grounding,
        unsupported_claims=unsupported_claims,
        repetition=repetition,
        content_usefulness=usefulness,
        overall_score=overall,
        issues=issues,
    )


def summarize_business(outcomes: list[BusinessEvaluationOutcome]) -> dict[str, float]:
    if not outcomes:
        return {}
    score_fields = (
        "brand_fit",
        "audience_fit",
        "channel_fit",
        "clarity",
        "cta_quality",
        "factual_grounding",
        "unsupported_claims",
        "repetition",
        "content_usefulness",
        "overall_score",
    )
    summary = {
        field: round(mean(float(getattr(item.quality, field)) for item in outcomes), 2)
        for field in score_fields
    }
    summary["structure_validity"] = round(
        mean(float(item.structure_valid) for item in outcomes), 4
    )
    summary["citation_completeness"] = round(
        mean(float(item.citation_complete) for item in outcomes), 4
    )
    return summary


def human_edit_distance(generated: str, human_approved: str) -> float:
    """Normalized 0..1 distance; 0 means unchanged and 1 means fully different."""
    if not generated and not human_approved:
        return 0.0
    return round(1.0 - SequenceMatcher(None, generated, human_approved).ratio(), 4)


def _repetition_score(text: str) -> int:
    segments = [
        item.strip().casefold()
        for item in re.split(r"[\n.!?。！？]+", text)  # noqa: RUF001
        if len(item.strip()) >= 8
    ]
    if len(segments) < 2:
        return 90
    unique_ratio = len(set(segments)) / len(segments)
    return max(0, min(100, round(unique_ratio * 100)))
