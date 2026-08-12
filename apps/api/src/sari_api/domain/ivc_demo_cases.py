# ruff: noqa: E501 -- synthetic multilingual demo content is intentionally explicit.

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sari_api.domain.ivc_qualification import IvcQualificationInput
from sari_api.domain.packages.models import LocalizedText, SupportedLocale

IvcDemoCaseKey = Literal[
    "university_animal_facility",
    "pharmaceutical_research_facility",
    "laboratory_upgrade",
]


@dataclass(frozen=True, slots=True)
class IvcDemoCase:
    key: IvcDemoCaseKey
    name: LocalizedText
    description: LocalizedText
    input: IvcQualificationInput

    def summary(self, locale: SupportedLocale) -> dict[str, str]:
        return {
            "key": self.key,
            "name": self.name.for_locale(locale),
            "description": self.description.for_locale(locale),
        }


def _input(**payload: object) -> IvcQualificationInput:
    return IvcQualificationInput.model_validate(payload)


UNIVERSITY_CASE = IvcDemoCase(
    key="university_animal_facility",
    name=LocalizedText(
        en="University animal facility",
        zh_cn="大学实验动物设施",
        id="Fasilitas hewan universitas",
    ),
    description=LocalizedText(
        en="A funded new-build mouse and rat research facility with defined stakeholders.",
        zh_cn="一个资金已落实、决策人明确的小鼠和大鼠新建设施项目。",
        id="Fasilitas riset tikus baru dengan dana dan pemangku kepentingan yang jelas.",
    ),
    input=_input(
        customer_profile={
            "organization_name": "Synthetic Nusantara University",
            "organization_type": "university",
            "country": "Indonesia",
            "city": "Bandung",
            "contact_role": "Director of Research Infrastructure",
            "decision_stakeholders": [
                "Research vice rector",
                "Attending veterinarian",
                "Facility manager",
                "Procurement committee",
            ],
        },
        project={
            "project_type": "new_facility",
            "facility_location": "Synthetic biomedical campus, Bandung",
            "project_summary": "New rodent facility supporting biomedical teaching and research.",
        },
        technical_requirements={
            "research_program_and_species": "Mouse and rat biomedical research programs",
            "planned_capacity": "2,400 mouse cages and 240 rat cages in two phases",
            "room_and_workflow_scope": [
                "housing",
                "procedure",
                "quarantine",
                "washing",
                "sterilization",
                "storage",
                "support",
            ],
            "containment_and_biosafety_context": "Institutional biosafety review is planned; final containment requirements await specialist confirmation.",
            "environmental_and_hvac_requirements": "Room pressure strategy, temperature, humidity, exhaust, redundancy, and monitoring are included in the user requirement draft.",
            "existing_design_information": "Concept layout and utility schedules are available.",
            "validation_and_compliance_expectations": "Commissioning records and institutional acceptance documentation are expected.",
            "service_and_lifecycle_scope": [
                "installation",
                "commissioning_support",
                "training",
                "preventive_service",
                "spare_parts",
            ],
        },
        budget_indicators={
            "indicative_budget": "2.1-2.5 million",
            "currency": "USD",
            "funding_status": "approved",
            "procurement_context": "Competitive university procurement after technical specification approval.",
        },
        timeline={
            "target_timeline": "Design freeze Q1 2027; installation Q4 2027; operation Q1 2028",
            "current_stage": "design",
        },
    ),
)

PHARMA_CASE = IvcDemoCase(
    key="pharmaceutical_research_facility",
    name=LocalizedText(
        en="Pharmaceutical research facility",
        zh_cn="制药研发动物设施",
        id="Fasilitas riset farmasi",
    ),
    description=LocalizedText(
        en="An expansion with mature requirements and funding still under review.",
        zh_cn="一个技术需求较成熟、资金仍在审批中的扩建项目。",
        id="Proyek perluasan dengan kebutuhan matang dan dana yang masih ditinjau.",
    ),
    input=_input(
        customer_profile={
            "organization_name": "Synthetic Meridian Pharma Research",
            "organization_type": "pharmaceutical_research",
            "country": "Singapore",
            "city": "Singapore",
            "contact_role": "Capital Projects Manager",
            "decision_stakeholders": [
                "Research operations",
                "Attending veterinarian",
                "EHS",
                "Engineering",
                "Procurement",
            ],
        },
        project={
            "project_type": "expansion",
            "facility_location": "Synthetic preclinical research campus",
            "project_summary": "Expansion of an operating rodent facility with additional IVC capacity and wash support.",
        },
        technical_requirements={
            "research_program_and_species": "Mouse and rat preclinical research",
            "planned_capacity": "1,200 additional mouse cages and 120 rat cages",
            "room_and_workflow_scope": [
                "housing",
                "procedure",
                "washing",
                "sterilization",
                "storage",
                "support",
            ],
            "containment_and_biosafety_context": "Existing institutional controls apply; specialist gap review requested.",
            "environmental_and_hvac_requirements": "Existing air-handling capacity study and room pressure schedule are available.",
            "existing_design_information": "User requirement specification, room data sheets, and 60 percent design package are available.",
            "validation_and_compliance_expectations": "Documented commissioning and owner acceptance testing are required.",
            "service_and_lifecycle_scope": [
                "installation",
                "commissioning_support",
                "training",
                "preventive_service",
                "spare_parts",
                "consumables",
            ],
        },
        budget_indicators={
            "indicative_budget": "1.4-1.8 million",
            "currency": "USD",
            "funding_status": "under_review",
            "procurement_context": "Capital request pending final scope validation.",
        },
        timeline={
            "target_timeline": "Procurement decision Q2 2027; phased installation from Q4 2027",
            "current_stage": "design",
        },
    ),
)

UPGRADE_CASE = IvcDemoCase(
    key="laboratory_upgrade",
    name=LocalizedText(
        en="Laboratory upgrade project",
        zh_cn="实验室升级项目",
        id="Proyek peningkatan laboratorium",
    ),
    description=LocalizedText(
        en="An early replacement inquiry with major budget, stakeholder, and technical gaps.",
        zh_cn="一个仍缺少预算、决策人和关键技术资料的早期设备替换询盘。",
        id="Permintaan awal penggantian dengan kekurangan data anggaran, pemangku kepentingan, dan teknis.",
    ),
    input=_input(
        customer_profile={
            "organization_name": "Synthetic Regional Research Laboratory",
            "organization_type": "public_research_laboratory",
            "country": "Indonesia",
            "city": "Surabaya",
            "contact_role": "Laboratory administrator",
            "decision_stakeholders": [],
        },
        project={
            "project_type": "replacement",
            "facility_location": "Existing synthetic research building, Surabaya",
            "project_summary": "Replace aging ventilated racks while keeping the facility operational.",
        },
        technical_requirements={
            "research_program_and_species": "Rodent research; exact species mix not confirmed",
            "planned_capacity": "Approximately 300 cages; current inventory not verified",
            "room_and_workflow_scope": ["housing"],
            "containment_and_biosafety_context": None,
            "environmental_and_hvac_requirements": None,
            "existing_design_information": None,
            "validation_and_compliance_expectations": None,
            "service_and_lifecycle_scope": ["installation"],
        },
        budget_indicators={
            "indicative_budget": None,
            "currency": None,
            "funding_status": "unknown",
            "procurement_context": None,
        },
        timeline={
            "target_timeline": "Preferred during the next academic break; dates not confirmed",
            "current_stage": "early_discovery",
        },
    ),
)

IVC_DEMO_CASES: tuple[IvcDemoCase, ...] = (UNIVERSITY_CASE, PHARMA_CASE, UPGRADE_CASE)
IVC_DEMO_CASES_BY_KEY = {case.key: case for case in IVC_DEMO_CASES}
