from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sari_api.domain.packages.models import SupportedLocale

PlaygroundDomain = Literal["commercial_kitchen", "laboratory_animal_facility"]
QualificationLevel = Literal["A", "B", "C"]


def playground_level(score: float) -> QualificationLevel:
    return "A" if score >= 75 else "B" if score >= 45 else "C"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CommercialKitchenPlaygroundInput(StrictModel):
    project_type: str | None = Field(default=None, max_length=250)
    location: str | None = Field(default=None, max_length=300)
    capacity: str | None = Field(default=None, max_length=500)
    budget: str | None = Field(default=None, max_length=500)
    timeline: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def has_some_project_evidence(self) -> Self:
        if not any((self.project_type, self.location, self.capacity, self.budget, self.timeline)):
            raise ValueError("Provide at least one commercial-kitchen project field")
        return self


class IvcPlaygroundInput(StrictModel):
    organization: str | None = Field(default=None, max_length=250)
    facility_type: str | None = Field(default=None, max_length=250)
    species_research: str | None = Field(default=None, max_length=1000)
    capacity: str | None = Field(default=None, max_length=500)
    technical_requirements: str | None = Field(default=None, max_length=3000)
    timeline: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def has_some_project_evidence(self) -> Self:
        if not any(
            (
                self.organization,
                self.facility_type,
                self.species_research,
                self.capacity,
                self.technical_requirements,
                self.timeline,
            )
        ):
            raise ValueError("Provide at least one IVC project field")
        return self


class PlaygroundQualificationRequest(StrictModel):
    schema_version: Literal["agent_playground_input_v1"] = "agent_playground_input_v1"
    domain: PlaygroundDomain
    response_locale: SupportedLocale = "en"
    commercial_kitchen: CommercialKitchenPlaygroundInput | None = None
    laboratory_animal_facility: IvcPlaygroundInput | None = None

    @model_validator(mode="after")
    def input_matches_domain(self) -> Self:
        if self.domain == "commercial_kitchen":
            if self.commercial_kitchen is None or self.laboratory_animal_facility is not None:
                raise ValueError("commercial_kitchen input must match the selected domain")
        elif self.laboratory_animal_facility is None or self.commercial_kitchen is not None:
            raise ValueError("laboratory_animal_facility input must match the selected domain")
        return self


class PlaygroundQualificationOutput(StrictModel):
    schema_version: Literal["agent_playground_output_v1"] = "agent_playground_output_v1"
    domain: PlaygroundDomain
    response_locale: SupportedLocale
    qualification_score: float = Field(ge=0, le=100)
    qualification_level: QualificationLevel
    business_summary: str = Field(min_length=1, max_length=3000)
    missing_information: list[str] = Field(max_length=20)
    risks: list[str] = Field(max_length=20)
    recommended_next_actions: list[str] = Field(min_length=1, max_length=8)
    demo_only: Literal[True] = True
    human_review_required: Literal[True] = True

    @model_validator(mode="after")
    def level_matches_score(self) -> Self:
        if self.qualification_level != playground_level(self.qualification_score):
            raise ValueError("qualification_level does not match qualification_score")
        return self
