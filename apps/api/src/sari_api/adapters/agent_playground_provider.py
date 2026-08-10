# ruff: noqa: E501, RUF001 -- prompt and multilingual demo copy are intentionally explicit.

from __future__ import annotations

import asyncio
import json
from typing import Protocol

from agents import Agent, ModelSettings, RunConfig, Runner, set_default_openai_key

from sari_api.adapters.qualification_provider import AiProviderUnavailableError
from sari_api.core.config import Settings
from sari_api.domain.agent_playground import (
    PlaygroundQualificationOutput,
    PlaygroundQualificationRequest,
    playground_level,
)
from sari_api.domain.packages.models import SupportedLocale

AGENT_PLAYGROUND_INSTRUCTIONS = """
You are running one selected business-development qualification agent in a demonstration playground.
Use only the supplied structured fields. Never invent customer facts, budgets, technical evidence,
prices, delivery commitments, standards compliance, scientific suitability, or regulatory approval.

For commercial_kitchen score five categories at 20 points each: project type, location, capacity,
budget evidence, and timeline evidence.

For laboratory_animal_facility score: organization 10, facility type 15, species/research 15,
capacity 15, technical requirements 30, and timeline 15. Scientific, veterinary, biosafety,
animal-welfare, regulatory, and engineering suitability always requires qualified expert review.

Use A for 75-100, B for 45-74.99, and C for 0-44.99. Return visible business explanations only.
All human-facing text must use response_locale: en for English, zh-CN for Simplified Chinese, or id
for Bahasa Indonesia. Do not expose chain-of-thought or internal deliberation. Set demo_only and
human_review_required to true. Recommend internal discovery or specialist review only. Use no tools.
""".strip()


class AgentPlaygroundProvider(Protocol):
    provider_type: str
    model_id: str

    async def qualify(
        self,
        request: PlaygroundQualificationRequest,
    ) -> PlaygroundQualificationOutput: ...


class MockAgentPlaygroundProvider:
    provider_type = "mock"
    model_id = "agent-playground-deterministic-v1"

    async def qualify(
        self,
        request: PlaygroundQualificationRequest,
    ) -> PlaygroundQualificationOutput:
        if request.domain == "commercial_kitchen":
            return _commercial_output(request)
        return _ivc_output(request)


class AgentsSdkPlaygroundProvider:
    provider_type = "openai"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.model_id = settings.openai_model

    async def qualify(
        self,
        request: PlaygroundQualificationRequest,
    ) -> PlaygroundQualificationOutput:
        if not self._settings.ai_enabled or self._settings.openai_api_key is None:
            raise AiProviderUnavailableError("AI playground is not configured.")
        set_default_openai_key(self._settings.openai_api_key.get_secret_value())
        name = (
            "Sari Arta Commercial Kitchen Agent"
            if request.domain == "commercial_kitchen"
            else "IVC Facility Business Development Agent"
        )
        agent = Agent(
            name=f"{name} Playground",
            instructions=AGENT_PLAYGROUND_INSTRUCTIONS,
            model=self.model_id,
            output_type=PlaygroundQualificationOutput,
            tools=[],
            model_settings=ModelSettings(max_tokens=self._settings.agent_max_output_tokens),
        )
        run = Runner.run(
            agent,
            json.dumps(request.model_dump(mode="json"), ensure_ascii=False),
            max_turns=self._settings.agent_max_turns,
            run_config=RunConfig(
                workflow_name="Multi-domain agent playground",
                tracing_disabled=True,
                trace_include_sensitive_data=False,
            ),
        )
        result = await asyncio.wait_for(run, timeout=self._settings.agent_timeout_seconds)
        if not isinstance(result.final_output, PlaygroundQualificationOutput):
            raise TypeError("Agent returned an unexpected playground output type.")
        if result.final_output.domain != request.domain:
            raise ValueError("Agent output domain does not match the selected agent.")
        if result.final_output.response_locale != request.response_locale:
            raise ValueError("Agent output locale does not match the requested locale.")
        return result.final_output


def build_agent_playground_provider(settings: Settings) -> AgentPlaygroundProvider:
    if settings.ai_enabled:
        return AgentsSdkPlaygroundProvider(settings)
    return MockAgentPlaygroundProvider()


def _commercial_output(
    request: PlaygroundQualificationRequest,
) -> PlaygroundQualificationOutput:
    data = request.commercial_kitchen
    if data is None:
        raise ValueError("Commercial-kitchen input is missing")
    fields = {
        "project_type": data.project_type,
        "location": data.location,
        "capacity": data.capacity,
        "budget": data.budget,
        "timeline": data.timeline,
    }
    score = float(sum(20 for value in fields.values() if value))
    missing = [
        _copy("commercial_missing", key, request.response_locale)
        for key, value in fields.items()
        if not value
    ]
    risks = [_copy("risk", "commercial_validation", request.response_locale)]
    if not data.capacity:
        risks.append(_copy("risk", "capacity_unknown", request.response_locale))
    actions = [_copy("action", "commercial_discovery", request.response_locale)]
    if data.project_type and data.location and data.capacity:
        actions.append(_copy("action", "kitchen_specialist", request.response_locale))
    return PlaygroundQualificationOutput(
        domain=request.domain,
        response_locale=request.response_locale,
        qualification_score=score,
        qualification_level=playground_level(score),
        business_summary=_commercial_summary(request),
        missing_information=missing,
        risks=risks,
        recommended_next_actions=actions,
        demo_only=True,
        human_review_required=True,
    )


def _ivc_output(request: PlaygroundQualificationRequest) -> PlaygroundQualificationOutput:
    data = request.laboratory_animal_facility
    if data is None:
        raise ValueError("IVC input is missing")
    weights = {
        "organization": 10,
        "facility_type": 15,
        "species_research": 15,
        "capacity": 15,
        "technical_requirements": 30,
        "timeline": 15,
    }
    values = data.model_dump()
    score = float(sum(weight for key, weight in weights.items() if values[key]))
    missing = [
        _copy("ivc_missing", key, request.response_locale) for key in weights if not values[key]
    ]
    risks = [_copy("risk", "ivc_expert_review", request.response_locale)]
    if not data.technical_requirements:
        risks.append(_copy("risk", "ivc_technical_unknown", request.response_locale))
    actions = [_copy("action", "ivc_specialist", request.response_locale)]
    if missing:
        actions.append(_copy("action", "ivc_discovery", request.response_locale))
    return PlaygroundQualificationOutput(
        domain=request.domain,
        response_locale=request.response_locale,
        qualification_score=score,
        qualification_level=playground_level(score),
        business_summary=_ivc_summary(request),
        missing_information=missing,
        risks=risks,
        recommended_next_actions=actions,
        demo_only=True,
        human_review_required=True,
    )


def _commercial_summary(request: PlaygroundQualificationRequest) -> str:
    data = request.commercial_kitchen
    if data is None:
        raise ValueError("Commercial-kitchen input is missing")
    project = data.project_type or _copy("fallback", "project", request.response_locale)
    location = data.location or _copy("fallback", "location", request.response_locale)
    capacity = data.capacity or _copy("fallback", "capacity", request.response_locale)
    if request.response_locale == "zh-CN":
        return f"该机会涉及位于{location}的{project}，当前计划产能为{capacity}。"
    if request.response_locale == "id":
        return f"Peluang ini mencakup {project} di {location} dengan kapasitas {capacity}."
    return f"This opportunity covers a {project} in {location} with planned capacity of {capacity}."


def _ivc_summary(request: PlaygroundQualificationRequest) -> str:
    data = request.laboratory_animal_facility
    if data is None:
        raise ValueError("IVC input is missing")
    organization = data.organization or _copy("fallback", "organization", request.response_locale)
    facility = data.facility_type or _copy("fallback", "facility", request.response_locale)
    research = data.species_research or _copy("fallback", "research", request.response_locale)
    if request.response_locale == "zh-CN":
        return f"{organization}正在评估{facility}项目，研究与动物范围为{research}。"
    if request.response_locale == "id":
        return f"{organization} sedang mengevaluasi proyek {facility} untuk {research}."
    return f"{organization} is evaluating a {facility} project for {research}."


_COPY: dict[str, dict[str, tuple[str, str, str]]] = {
    "commercial_missing": {
        "project_type": ("Project type", "项目类型", "Jenis proyek"),
        "location": ("Project location", "项目地点", "Lokasi proyek"),
        "capacity": (
            "Kitchen size or meal capacity",
            "厨房面积或供餐量",
            "Ukuran dapur atau kapasitas makanan",
        ),
        "budget": ("Indicative budget", "预估预算", "Anggaran indikatif"),
        "timeline": ("Target timeline", "目标时间", "Target jadwal"),
    },
    "ivc_missing": {
        "organization": ("Customer organization", "客户机构", "Organisasi pelanggan"),
        "facility_type": ("Facility project type", "设施项目类型", "Jenis proyek fasilitas"),
        "species_research": (
            "Species and research program",
            "动物种类和研究方向",
            "Spesies dan program riset",
        ),
        "capacity": (
            "Planned cage, rack, or room capacity",
            "计划笼位、笼架或房间容量",
            "Kapasitas kandang, rak, atau ruangan",
        ),
        "technical_requirements": (
            "Technical, workflow, HVAC, and biosafety requirements",
            "技术、流程、HVAC 和生物安全要求",
            "Kebutuhan teknis, alur kerja, HVAC, dan biosafety",
        ),
        "timeline": ("Target timeline", "目标时间", "Target jadwal"),
    },
    "risk": {
        "commercial_validation": (
            "Budget, scope, pricing, and delivery assumptions require sales and engineering validation.",
            "预算、范围、价格和交期假设需要销售与工程人员确认。",
            "Asumsi anggaran, ruang lingkup, harga, dan pengiriman memerlukan validasi penjualan dan teknik.",
        ),
        "capacity_unknown": (
            "Equipment scope cannot be estimated reliably without operating capacity.",
            "缺少运营产能时无法可靠估算设备范围。",
            "Ruang lingkup peralatan tidak dapat diperkirakan tanpa kapasitas operasi.",
        ),
        "ivc_expert_review": (
            "Scientific, veterinary, biosafety, regulatory, and engineering suitability requires qualified expert review.",
            "科研、兽医、生物安全、法规和工程适用性必须由合格专家审核。",
            "Kesesuaian ilmiah, veteriner, biosafety, regulasi, dan teknik memerlukan tinjauan ahli.",
        ),
        "ivc_technical_unknown": (
            "Facility utilities, HVAC, workflow, and containment requirements are not yet evidenced.",
            "设施机电、HVAC、流程和隔离要求尚无充分依据。",
            "Kebutuhan utilitas, HVAC, alur kerja, dan containment belum memiliki bukti.",
        ),
    },
    "action": {
        "commercial_discovery": (
            "Confirm missing project facts, budget context, decision stakeholders, and target opening date.",
            "确认缺失的项目资料、预算背景、决策人和目标开业时间。",
            "Konfirmasi fakta proyek, konteks anggaran, pemangku keputusan, dan target pembukaan.",
        ),
        "kitchen_specialist": (
            "Arrange a commercial-kitchen discovery session and request the available floor plan.",
            "安排商用厨房需求访谈并索取现有平面图。",
            "Atur sesi penemuan dapur komersial dan minta denah yang tersedia.",
        ),
        "ivc_specialist": (
            "Assign the opportunity to an IVC facility specialist for human review.",
            "将该机会交由 IVC 设施专家人工审核。",
            "Tugaskan peluang kepada spesialis fasilitas IVC untuk tinjauan manusia.",
        ),
        "ivc_discovery": (
            "Request the missing user requirements, facility information, stakeholder map, and project milestones.",
            "索取缺失的用户需求、设施资料、决策人信息和项目节点。",
            "Minta kebutuhan pengguna, informasi fasilitas, peta pemangku kepentingan, dan tahapan proyek yang belum tersedia.",
        ),
    },
    "fallback": {
        "project": ("commercial-kitchen project", "商用厨房项目", "proyek dapur komersial"),
        "location": ("an unconfirmed location", "待确认地点", "lokasi yang belum dikonfirmasi"),
        "capacity": (
            "an unconfirmed operating capacity",
            "待确认运营产能",
            "kapasitas operasi yang belum dikonfirmasi",
        ),
        "organization": (
            "An unconfirmed organization",
            "待确认机构",
            "Organisasi yang belum dikonfirmasi",
        ),
        "facility": ("laboratory animal facility", "实验动物设施", "fasilitas hewan laboratorium"),
        "research": (
            "an unconfirmed research program",
            "待确认研究方向",
            "program riset yang belum dikonfirmasi",
        ),
    },
}


def _copy(group: str, key: str, locale: SupportedLocale) -> str:
    value = _COPY[group][key]
    return value[0 if locale == "en" else 1 if locale == "zh-CN" else 2]
