from __future__ import annotations

from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

QualificationStatus = Literal["confirmed", "partial", "unknown", "not_fit"]
QualificationLevel = Literal["A", "B", "C"]

QUALIFICATION_FACTOR_LABELS = {
    "need_status": "Need and project fit",
    "timeline_status": "Timeline",
    "budget_status": "Budget",
    "authority_status": "Decision authority",
}


def qualification_level_for_score(score: float | Decimal) -> QualificationLevel:
    numeric_score = float(score)
    return "A" if numeric_score >= 75 else "B" if numeric_score >= 45 else "C"


class QualificationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    score: float = Field(ge=0, le=100)
    tier: Literal["hot", "warm", "cold"]
    need_summary: str = Field(min_length=1, max_length=2000)
    budget_status: QualificationStatus
    authority_status: QualificationStatus
    need_status: QualificationStatus
    timeline_status: QualificationStatus
    missing_information: list[str] = Field(max_length=12)
    recommended_action: str = Field(min_length=1, max_length=2000)
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def tier_matches_score(self) -> Self:
        expected = "hot" if self.score >= 75 else "warm" if self.score >= 45 else "cold"
        if self.tier != expected:
            raise ValueError("tier does not match score")
        return self

    def qualification_dimensions(self) -> dict[str, str]:
        return {
            "budget_status": self.budget_status,
            "authority_status": self.authority_status,
            "need_status": self.need_status,
            "timeline_status": self.timeline_status,
        }

    def qualification_level(self) -> QualificationLevel:
        return qualification_level_for_score(self.score)

    def key_qualification_factors(self) -> list[dict[str, str]]:
        return [
            {
                "key": key.removesuffix("_status"),
                "label": QUALIFICATION_FACTOR_LABELS[key],
                "status": status,
            }
            for key, status in self.qualification_dimensions().items()
        ]
