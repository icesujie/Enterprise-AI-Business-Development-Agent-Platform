from __future__ import annotations

import asyncio
import json
from typing import Any, Literal, Protocol

from agents import Agent, ModelSettings, RunConfig, Runner, set_default_openai_key

from sari_api.core.config import Settings
from sari_api.domain.qualification import QualificationOutput, QualificationStatus

QUALIFICATION_INSTRUCTIONS = """
You are Sari Arta's lead qualification assistant for commercial-kitchen engineering projects.
Evaluate only the supplied saved CRM snapshot. Never invent facts.

Score using this fixed rubric:
- Need and project fit: 35 points.
- Timeline clarity and urgency: 25 points.
- Budget evidence: 20 points.
- Decision authority evidence: 20 points.

Use hot for 75-100, warm for 45-74.99, and cold for 0-44.99.
Unknown budget or authority must lower confidence but does not automatically disqualify a
valuable project. State missing evidence explicitly. Recommend a safe internal next step only;
do not promise pricing, delivery dates, technical guarantees, or external communication.
Return concise, business-friendly explanations. Do not include hidden reasoning, chain-of-thought,
or internal deliberation.
""".strip()


class QualificationProvider(Protocol):
    provider_type: str
    model_id: str

    async def qualify(self, snapshot: dict[str, Any]) -> QualificationOutput: ...


class AiProviderUnavailableError(Exception):
    pass


class MockQualificationProvider:
    """Deterministic qualification for local demos and API-key-free development."""

    provider_type = "mock"
    model_id = "deterministic-rubric-v1"

    async def qualify(self, snapshot: dict[str, Any]) -> QualificationOutput:
        lead = _mapping(snapshot.get("lead"))
        organization = _mapping(snapshot.get("organization"))
        contact = _mapping(snapshot.get("contact"))
        requirements = _mapping(lead.get("requirements"))

        project_type = _text(lead.get("project_type"))
        capacity = _text(lead.get("expected_capacity"))
        inquiry = _text(lead.get("inquiry_summary"))
        timeline = _text(lead.get("target_timeline"))
        currency = _text(lead.get("currency"))
        estimated_value = _text(lead.get("estimated_value"))
        job_title = _text(contact.get("job_title"))
        contact_name = _text(contact.get("name"))
        authority_evidence = next(
            (
                _text(requirements.get(key))
                for key in ("decision_authority", "decision_maker", "authority")
                if _text(requirements.get(key))
            ),
            None,
        )

        need_points = (15 if project_type else 0) + (10 if capacity else 0)
        need_points += 10 if inquiry and len(inquiry) >= 20 else 5 if inquiry else 0
        need_status: QualificationStatus = (
            "confirmed"
            if project_type and capacity and inquiry and len(inquiry) >= 20
            else "partial"
            if project_type or capacity or inquiry
            else "unknown"
        )

        timeline_points = 25 if timeline else 0
        timeline_status: QualificationStatus = "confirmed" if timeline else "unknown"
        budget_points = 20 if estimated_value and currency else 0
        budget_status: QualificationStatus = (
            "confirmed" if estimated_value and currency else "unknown"
        )
        if authority_evidence:
            authority_points = 20
            authority_status: QualificationStatus = "confirmed"
        elif job_title:
            authority_points, authority_status = 10, "partial"
        elif contact_name:
            authority_points, authority_status = 5, "partial"
        else:
            authority_points, authority_status = 0, "unknown"

        score = need_points + timeline_points + budget_points + authority_points
        tier: Literal["hot", "warm", "cold"] = (
            "hot" if score >= 75 else "warm" if score >= 45 else "cold"
        )
        missing_information: list[str] = []
        if not project_type:
            missing_information.append("Project type")
        if not capacity:
            missing_information.append("Kitchen size or expected meal capacity")
        if not timeline:
            missing_information.append("Expected project timeline")
        if not estimated_value or not currency:
            missing_information.append("Indicative budget and currency")
        if not authority_evidence:
            missing_information.append("Decision maker and approval role")

        evidenced_dimensions = sum(
            status != "unknown"
            for status in (
                need_status,
                timeline_status,
                budget_status,
                authority_status,
            )
        )
        confidence = min(0.95, 0.35 + evidenced_dimensions * 0.15)

        return QualificationOutput(
            score=score,
            tier=tier,
            need_summary=_business_summary(lead, organization),
            budget_status=budget_status,
            authority_status=authority_status,
            need_status=need_status,
            timeline_status=timeline_status,
            missing_information=missing_information,
            recommended_action=_recommended_action(
                project_type=project_type,
                capacity=capacity,
                timeline=timeline,
                estimated_value=estimated_value,
                currency=currency,
                authority_evidence=authority_evidence,
            ),
            confidence=confidence,
        )


class AgentsSdkQualificationProvider:
    provider_type = "openai"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.model_id = settings.openai_model

    async def qualify(self, snapshot: dict[str, Any]) -> QualificationOutput:
        if not self._settings.ai_enabled or self._settings.openai_api_key is None:
            raise AiProviderUnavailableError("AI qualification is not configured.")
        set_default_openai_key(self._settings.openai_api_key.get_secret_value())
        agent = Agent(
            name="Sari Arta Lead Qualification Agent",
            instructions=QUALIFICATION_INSTRUCTIONS,
            model=self.model_id,
            output_type=QualificationOutput,
            tools=[],
            model_settings=ModelSettings(max_tokens=self._settings.agent_max_output_tokens),
        )
        run = Runner.run(
            agent,
            json.dumps(snapshot, ensure_ascii=False, default=str),
            max_turns=self._settings.agent_max_turns,
            run_config=RunConfig(
                workflow_name="Sari Arta lead qualification",
                tracing_disabled=True,
                trace_include_sensitive_data=False,
            ),
        )
        result = await asyncio.wait_for(run, timeout=self._settings.agent_timeout_seconds)
        if not isinstance(result.final_output, QualificationOutput):
            raise TypeError("Agent returned an unexpected output type.")
        return result.final_output


def build_qualification_provider(settings: Settings) -> QualificationProvider:
    if settings.ai_enabled:
        return AgentsSdkQualificationProvider(settings)
    return MockQualificationProvider()


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _business_summary(lead: dict[str, Any], organization: dict[str, Any]) -> str:
    company = _text(organization.get("name")) or "An unassigned company"
    industry = _text(organization.get("industry"))
    project_type = _text(lead.get("project_type")) or "commercial-kitchen project"
    capacity = _text(lead.get("expected_capacity"))
    location = _text(lead.get("project_city")) or _text(lead.get("project_country_code"))

    details = [f"a {project_type}"]
    if capacity:
        details.append(f"with a stated size or capacity of {capacity}")
    if location:
        details.append(f"in {location}")
    industry_context = f" in the {industry} sector" if industry else ""
    return f"{company}{industry_context} submitted an inquiry for {' '.join(details)}."


def _recommended_action(
    *,
    project_type: str | None,
    capacity: str | None,
    timeline: str | None,
    estimated_value: str | None,
    currency: str | None,
    authority_evidence: str | None,
) -> str:
    if not project_type or not capacity:
        return "Confirm the kitchen use case, operating volume, and required equipment scope."
    if not timeline:
        return "Confirm the target opening date and procurement milestones."
    if not estimated_value or not currency:
        return "Request an indicative budget range before solution development."
    if not authority_evidence:
        return "Identify the decision stakeholders, then schedule a technical discovery call."
    return "Schedule a technical discovery call and request the available floor plan."
