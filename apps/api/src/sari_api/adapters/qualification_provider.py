from __future__ import annotations

import asyncio
import json
from typing import Any, Protocol

from agents import Agent, ModelSettings, RunConfig, Runner, set_default_openai_key

from sari_api.core.config import Settings
from sari_api.domain.qualification import QualificationOutput

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
""".strip()


class QualificationProvider(Protocol):
    provider_type: str
    model_id: str

    async def qualify(self, snapshot: dict[str, Any]) -> QualificationOutput: ...


class AiProviderUnavailableError(Exception):
    pass


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
