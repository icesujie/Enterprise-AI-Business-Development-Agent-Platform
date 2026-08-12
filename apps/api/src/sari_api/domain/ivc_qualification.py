from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sari_api.domain.packages.models import SupportedLocale

IvcProjectType = Literal["new_facility", "expansion", "retrofit", "replacement", "feasibility"]
ReadinessStatus = Literal["confirmed", "partial", "unknown", "risk"]
QualificationLevel = Literal["A", "B", "C"]
IvcQualificationFactorCategory = Literal[
    "customer", "project", "technical", "budget", "timeline", "stakeholders"
]


def level_for_score(score: float) -> QualificationLevel:
    return "A" if score >= 75 else "B" if score >= 45 else "C"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class IvcCustomerProfile(StrictModel):
    organization_name: str = Field(min_length=1, max_length=250)
    organization_type: str = Field(min_length=1, max_length=120)
    country: str = Field(min_length=2, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    contact_role: str | None = Field(default=None, max_length=160)
    decision_stakeholders: list[str] = Field(default_factory=list, max_length=12)


class IvcProjectProfile(StrictModel):
    project_type: IvcProjectType
    facility_location: str = Field(min_length=1, max_length=300)
    project_summary: str = Field(min_length=1, max_length=3000)


class IvcTechnicalRequirements(StrictModel):
    research_program_and_species: str = Field(min_length=1, max_length=1000)
    planned_capacity: str = Field(min_length=1, max_length=500)
    room_and_workflow_scope: list[
        Literal[
            "housing",
            "procedure",
            "quarantine",
            "washing",
            "sterilization",
            "storage",
            "support",
        ]
    ] = Field(min_length=1, max_length=7)
    containment_and_biosafety_context: str | None = Field(default=None, max_length=2000)
    environmental_and_hvac_requirements: str | None = Field(default=None, max_length=2000)
    existing_design_information: str | None = Field(default=None, max_length=2000)
    validation_and_compliance_expectations: str | None = Field(default=None, max_length=2000)
    service_and_lifecycle_scope: list[str] = Field(default_factory=list, max_length=12)


class IvcBudgetIndicators(StrictModel):
    indicative_budget: str | None = Field(default=None, max_length=500)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    funding_status: Literal["approved", "allocated", "under_review", "unknown"] = "unknown"
    procurement_context: str | None = Field(default=None, max_length=1000)


class IvcTimeline(StrictModel):
    target_timeline: str = Field(min_length=1, max_length=1000)
    current_stage: Literal[
        "early_discovery",
        "feasibility",
        "design",
        "tender",
        "procurement",
        "implementation",
    ]


class IvcQualificationInput(StrictModel):
    schema_version: Literal["ivc_qualification_input_v1"] = "ivc_qualification_input_v1"
    customer_profile: IvcCustomerProfile
    project: IvcProjectProfile
    technical_requirements: IvcTechnicalRequirements
    budget_indicators: IvcBudgetIndicators
    timeline: IvcTimeline


class IvcQualificationFactor(StrictModel):
    category: IvcQualificationFactorCategory
    status: ReadinessStatus
    summary: str = Field(min_length=1, max_length=1000)


class IvcQualificationOutput(StrictModel):
    schema_version: Literal["ivc_qualification_output_v1"] = "ivc_qualification_output_v1"
    response_locale: SupportedLocale
    score: float = Field(ge=0, le=100)
    qualification_level: QualificationLevel
    business_summary: str = Field(min_length=1, max_length=3000)
    key_qualification_factors: list[IvcQualificationFactor] = Field(min_length=6, max_length=6)
    missing_information: list[str] = Field(max_length=20)
    risk_flags: list[str] = Field(max_length=20)
    recommended_next_actions: list[str] = Field(min_length=1, max_length=8)
    confidence: float = Field(ge=0, le=1)
    expert_review_required: Literal[True] = True

    @model_validator(mode="after")
    def level_matches_score(self) -> Self:
        if self.qualification_level != level_for_score(self.score):
            raise ValueError("qualification_level does not match score")
        categories = [factor.category for factor in self.key_qualification_factors]
        expected = {"customer", "project", "technical", "budget", "timeline", "stakeholders"}
        if set(categories) != expected or len(categories) != len(expected):
            raise ValueError("one qualification factor is required for every rubric category")
        return self
