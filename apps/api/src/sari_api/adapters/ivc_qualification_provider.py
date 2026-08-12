# ruff: noqa: E501, RUF001 -- prompt and multilingual demo copy are intentionally explicit.

from __future__ import annotations

import asyncio
import json
from typing import Any, Protocol

from agents import Agent, ModelSettings, RunConfig, Runner, set_default_openai_key

from sari_api.adapters.qualification_provider import AiProviderUnavailableError
from sari_api.core.config import Settings
from sari_api.domain.ivc_qualification import (
    IvcQualificationFactor,
    IvcQualificationFactorCategory,
    IvcQualificationInput,
    IvcQualificationOutput,
    ReadinessStatus,
    level_for_score,
)
from sari_api.domain.packages.models import SupportedLocale

IVC_QUALIFICATION_INSTRUCTIONS = """
You are the IVC Facility Business Development Agent for laboratory-animal-facility opportunities.
Evaluate only the supplied structured project snapshot. Never invent a customer fact, scientific
requirement, regulation, standard, product performance, price, or delivery commitment.

Use this fixed 100-point commercial-discovery rubric:
- Customer profile: 10 points.
- Project definition and fit: 15 points.
- Technical requirement completeness: 35 points.
- Budget and procurement evidence: 20 points.
- Timeline readiness: 15 points.
- Decision-stakeholder evidence: 5 points.

Assign level A for 75-100, B for 45-74.99, and C for 0-44.99. Missing evidence must reduce the
score and appear in missing_information. Always set expert_review_required to true. Scientific,
veterinary, biosafety, animal-welfare, regulatory, facility-engineering, and commercial conclusions
must be identified for qualified human review. Recommend internal discovery or specialist-review
actions only. Do not claim that a design is compliant or suitable.

Write all human-facing summaries, factors, missing-information items, risk flags, and next actions
in the requested response_locale (en, zh-CN, or id). Keep stable schema keys and enum values in
English. Return concise business explanations only. Never reveal chain-of-thought, hidden reasoning,
or internal deliberation.
""".strip()


class IvcQualificationProvider(Protocol):
    provider_type: str
    model_id: str

    async def qualify(
        self,
        input_data: IvcQualificationInput,
        response_locale: SupportedLocale,
    ) -> IvcQualificationOutput: ...


class MockIvcQualificationProvider:
    """Deterministic, localized IVC qualification for safe demonstrations."""

    provider_type = "mock"
    model_id = "ivc-deterministic-rubric-v1"

    async def qualify(
        self,
        input_data: IvcQualificationInput,
        response_locale: SupportedLocale,
    ) -> IvcQualificationOutput:
        customer = input_data.customer_profile
        project = input_data.project
        technical = input_data.technical_requirements
        budget = input_data.budget_indicators
        timeline = input_data.timeline

        customer_score = 5
        customer_score += 3 if customer.organization_type else 0
        customer_score += 2 if customer.contact_role else 0

        project_score = 8
        project_score += 4 if len(project.project_summary) >= 40 else 2
        project_score += 3 if project.facility_location else 0

        technical_score = 12
        technical_score += min(len(technical.room_and_workflow_scope), 4) * 2
        technical_score += sum(
            3
            for value in (
                technical.containment_and_biosafety_context,
                technical.environmental_and_hvac_requirements,
                technical.existing_design_information,
                technical.validation_and_compliance_expectations,
            )
            if value
        )
        technical_score += 3 if len(technical.service_and_lifecycle_scope) >= 3 else 0
        technical_score = min(technical_score, 35)

        budget_score = 0
        if budget.indicative_budget and budget.currency:
            budget_score += 10
        if budget.funding_status in {"approved", "allocated"}:
            budget_score += 7
        elif budget.funding_status == "under_review":
            budget_score += 4
        if budget.procurement_context:
            budget_score += 3

        timeline_score = 5
        timeline_score += {
            "early_discovery": 0,
            "feasibility": 4,
            "design": 10,
            "tender": 10,
            "procurement": 10,
            "implementation": 7,
        }[timeline.current_stage]

        stakeholder_count = len(customer.decision_stakeholders)
        stakeholder_score = 5 if stakeholder_count >= 3 else 3 if stakeholder_count else 0
        score = float(
            customer_score
            + project_score
            + technical_score
            + budget_score
            + timeline_score
            + stakeholder_score
        )

        missing_keys: list[str] = []
        if stakeholder_count == 0:
            missing_keys.append("stakeholders")
        if not technical.containment_and_biosafety_context:
            missing_keys.append("biosafety")
        if not technical.environmental_and_hvac_requirements:
            missing_keys.append("hvac")
        if not technical.existing_design_information:
            missing_keys.append("design_information")
        if not technical.validation_and_compliance_expectations:
            missing_keys.append("validation")
        if not budget.indicative_budget or not budget.currency:
            missing_keys.append("budget")
        if budget.funding_status == "unknown":
            missing_keys.append("funding")
        if not budget.procurement_context:
            missing_keys.append("procurement")

        risk_keys = ["expert_validation"]
        if project.project_type in {"retrofit", "replacement"}:
            risk_keys.append("operational_continuity")
        if not technical.environmental_and_hvac_requirements:
            risk_keys.append("utilities_unknown")

        factors = [
            self._factor(
                "customer",
                "confirmed" if customer_score == 10 else "partial",
                response_locale,
            ),
            self._factor("project", "confirmed", response_locale),
            self._factor(
                "technical",
                "confirmed"
                if technical_score >= 30
                else "partial"
                if technical_score >= 18
                else "unknown",
                response_locale,
            ),
            self._factor(
                "budget",
                "confirmed" if budget_score >= 17 else "partial" if budget_score else "unknown",
                response_locale,
            ),
            self._factor(
                "timeline",
                "confirmed" if timeline_score >= 13 else "partial",
                response_locale,
            ),
            self._factor(
                "stakeholders",
                "confirmed"
                if stakeholder_score == 5
                else "partial"
                if stakeholder_score
                else "unknown",
                response_locale,
            ),
        ]

        evidenced = sum(factor.status not in {"unknown", "risk"} for factor in factors)
        confidence = min(0.95, 0.35 + evidenced * 0.09)
        return IvcQualificationOutput(
            response_locale=response_locale,
            score=score,
            qualification_level=level_for_score(score),
            business_summary=self._summary(input_data, response_locale),
            key_qualification_factors=factors,
            missing_information=[
                _localized("missing", key, response_locale) for key in missing_keys
            ],
            risk_flags=[_localized("risk", key, response_locale) for key in risk_keys],
            recommended_next_actions=self._next_actions(input_data, missing_keys, response_locale),
            confidence=confidence,
            expert_review_required=True,
        )

    @staticmethod
    def _factor(
        category: IvcQualificationFactorCategory,
        status: ReadinessStatus,
        locale: SupportedLocale,
    ) -> IvcQualificationFactor:
        return IvcQualificationFactor(
            category=category,
            status=status,
            summary=_localized("factor", f"{category}_{status}", locale),
        )

    @staticmethod
    def _summary(
        input_data: IvcQualificationInput,
        locale: SupportedLocale,
    ) -> str:
        customer = input_data.customer_profile
        project = input_data.project
        technical = input_data.technical_requirements
        if locale == "zh-CN":
            return (
                f"{customer.organization_name} 正在评估位于 {project.facility_location} 的"
                f"{_project_type(project.project_type, locale)}，计划容量为 {technical.planned_capacity}。"
            )
        if locale == "id":
            return (
                f"{customer.organization_name} sedang mengevaluasi {_project_type(project.project_type, locale)} "
                f"di {project.facility_location} dengan kapasitas {technical.planned_capacity}."
            )
        return (
            f"{customer.organization_name} is evaluating a {_project_type(project.project_type, locale)} "
            f"at {project.facility_location} with planned capacity of {technical.planned_capacity}."
        )

    @staticmethod
    def _next_actions(
        input_data: IvcQualificationInput,
        missing_keys: list[str],
        locale: SupportedLocale,
    ) -> list[str]:
        actions = [_localized("action", "specialist_review", locale)]
        if any(key in missing_keys for key in ("biosafety", "hvac", "design_information")):
            actions.append(_localized("action", "technical_discovery", locale))
        if any(key in missing_keys for key in ("budget", "funding", "procurement")):
            actions.append(_localized("action", "commercial_discovery", locale))
        if "stakeholders" in missing_keys:
            actions.append(_localized("action", "stakeholder_map", locale))
        if len(actions) == 1 and input_data.timeline.current_stage in {"design", "tender"}:
            actions.append(_localized("action", "review_documents", locale))
        return actions


class AgentsSdkIvcQualificationProvider:
    provider_type = "openai"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.model_id = settings.openai_model

    async def qualify(
        self,
        input_data: IvcQualificationInput,
        response_locale: SupportedLocale,
    ) -> IvcQualificationOutput:
        if not self._settings.ai_enabled or self._settings.openai_api_key is None:
            raise AiProviderUnavailableError("AI qualification is not configured.")
        set_default_openai_key(self._settings.openai_api_key.get_secret_value())
        agent = Agent(
            name="IVC Facility Business Development Agent",
            instructions=IVC_QUALIFICATION_INSTRUCTIONS,
            model=self.model_id,
            output_type=IvcQualificationOutput,
            tools=[],
            model_settings=ModelSettings(max_tokens=self._settings.agent_max_output_tokens),
        )
        payload: dict[str, Any] = {
            "response_locale": response_locale,
            "project_snapshot": input_data.model_dump(mode="json"),
        }
        run = Runner.run(
            agent,
            json.dumps(payload, ensure_ascii=False),
            max_turns=self._settings.agent_max_turns,
            run_config=RunConfig(
                workflow_name="IVC facility qualification",
                tracing_disabled=True,
                trace_include_sensitive_data=False,
            ),
        )
        result = await asyncio.wait_for(run, timeout=self._settings.agent_timeout_seconds)
        if not isinstance(result.final_output, IvcQualificationOutput):
            raise TypeError("Agent returned an unexpected output type.")
        return result.final_output


def build_ivc_qualification_provider(settings: Settings) -> IvcQualificationProvider:
    if settings.ai_enabled:
        return AgentsSdkIvcQualificationProvider(settings)
    return MockIvcQualificationProvider()


def _project_type(project_type: str, locale: SupportedLocale) -> str:
    labels = {
        "new_facility": ("new animal facility", "新建实验动物设施", "fasilitas hewan baru"),
        "expansion": ("facility expansion", "设施扩建项目", "perluasan fasilitas"),
        "retrofit": ("facility retrofit", "设施改造项目", "renovasi fasilitas"),
        "replacement": ("equipment replacement", "设备替换项目", "penggantian peralatan"),
        "feasibility": ("feasibility study", "可行性研究", "studi kelayakan"),
    }
    return labels[project_type][0 if locale == "en" else 1 if locale == "zh-CN" else 2]


_COPY: dict[str, dict[str, tuple[str, str, str]]] = {
    "missing": {
        "stakeholders": (
            "Decision stakeholders and approval path",
            "决策人和审批路径",
            "Pemangku kepentingan dan jalur persetujuan",
        ),
        "biosafety": (
            "Containment and institutional biosafety context",
            "隔离和机构生物安全背景",
            "Konteks containment dan biosafety institusi",
        ),
        "hvac": (
            "Environmental, HVAC, pressure, exhaust, and monitoring requirements",
            "环境、HVAC、压差、排风和监控要求",
            "Kebutuhan lingkungan, HVAC, tekanan, exhaust, dan pemantauan",
        ),
        "design_information": (
            "Existing layouts, room data, utilities, and design information",
            "现有布局、房间数据、机电条件和设计资料",
            "Layout, data ruang, utilitas, dan informasi desain",
        ),
        "validation": (
            "Validation, commissioning, and acceptance expectations",
            "验证、调试和验收预期",
            "Harapan validasi, commissioning, dan penerimaan",
        ),
        "budget": (
            "Indicative budget and currency",
            "预估预算和币种",
            "Anggaran indikatif dan mata uang",
        ),
        "funding": ("Funding approval status", "资金审批状态", "Status persetujuan dana"),
        "procurement": (
            "Procurement method and decision process",
            "采购方式和决策流程",
            "Metode pengadaan dan proses keputusan",
        ),
    },
    "risk": {
        "expert_validation": (
            "Scientific, veterinary, biosafety, regulatory, and engineering suitability requires qualified expert review.",
            "科研、兽医、生物安全、法规和工程适用性必须由合格专家审核。",
            "Kesesuaian ilmiah, veteriner, biosafety, regulasi, dan teknik memerlukan tinjauan ahli.",
        ),
        "operational_continuity": (
            "Work in an operating facility requires a validated transition and continuity plan.",
            "在运设施施工需要经过验证的切换和连续运行方案。",
            "Pekerjaan di fasilitas aktif memerlukan rencana transisi dan kontinuitas yang tervalidasi.",
        ),
        "utilities_unknown": (
            "Utility and HVAC suitability is not yet evidenced.",
            "机电和 HVAC 适用性尚无充分依据。",
            "Kesesuaian utilitas dan HVAC belum memiliki bukti.",
        ),
    },
    "action": {
        "specialist_review": (
            "Assign the opportunity to an IVC facility specialist for human review.",
            "将该机会交由 IVC 设施专家人工审核。",
            "Tugaskan peluang kepada spesialis fasilitas IVC untuk tinjauan manusia.",
        ),
        "technical_discovery": (
            "Run a technical discovery session and request available layouts, room data, utility information, and user requirements.",
            "安排技术需求访谈，并索取现有布局、房间数据、机电资料和用户需求文件。",
            "Lakukan sesi penemuan teknis dan minta layout, data ruang, informasi utilitas, dan kebutuhan pengguna.",
        ),
        "commercial_discovery": (
            "Confirm the budget range, funding status, procurement route, and approval milestones.",
            "确认预算范围、资金状态、采购路径和审批节点。",
            "Konfirmasi rentang anggaran, status dana, jalur pengadaan, dan tahapan persetujuan.",
        ),
        "stakeholder_map": (
            "Identify the project owner, principal investigator, veterinarian, facility manager, engineering, and procurement roles.",
            "识别项目业主、PI、兽医、设施经理、工程和采购角色。",
            "Identifikasi pemilik proyek, peneliti utama, dokter hewan, manajer fasilitas, teknik, dan pengadaan.",
        ),
        "review_documents": (
            "Review the current design package and record all assumptions requiring customer or specialist confirmation.",
            "审核现有设计资料，并记录所有需要客户或专家确认的假设。",
            "Tinjau paket desain dan catat semua asumsi yang memerlukan konfirmasi pelanggan atau ahli.",
        ),
    },
    "factor": {},
}

for _category, _labels in {
    "customer": ("Customer profile", "客户资料", "Profil pelanggan"),
    "project": ("Project definition", "项目定义", "Definisi proyek"),
    "technical": ("Technical requirements", "技术需求", "Kebutuhan teknis"),
    "budget": ("Budget and procurement", "预算与采购", "Anggaran dan pengadaan"),
    "timeline": ("Timeline", "时间计划", "Jadwal"),
    "stakeholders": ("Decision stakeholders", "决策人", "Pemangku kepentingan"),
}.items():
    for _status, _status_labels in {
        "confirmed": ("has strong evidence", "信息较完整", "memiliki bukti kuat"),
        "partial": ("is partially evidenced", "信息不完整", "memiliki bukti sebagian"),
        "unknown": ("requires discovery", "需要进一步确认", "memerlukan penemuan lebih lanjut"),
        "risk": ("requires specialist review", "需要专家审核", "memerlukan tinjauan ahli"),
    }.items():
        _COPY["factor"][f"{_category}_{_status}"] = (
            f"{_labels[0]} {_status_labels[0]}.",
            f"{_labels[1]} {_status_labels[1]}.",
            f"{_labels[2]} {_status_labels[2]}.",
        )


def _localized(group: str, key: str, locale: SupportedLocale) -> str:
    value = _COPY[group][key]
    return value[0 if locale == "en" else 1 if locale == "zh-CN" else 2]
