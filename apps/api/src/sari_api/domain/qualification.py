from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

QualificationStatus = Literal["confirmed", "partial", "unknown", "not_fit"]


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
