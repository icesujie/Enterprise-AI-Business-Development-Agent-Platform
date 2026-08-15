from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class KnowledgeAssistantEvaluationCase(StrictModel):
    case_id: str
    category: str
    expected_evidence_status: str
    expected_grounded: bool
    expected_citation_count: int
    expected_access_outcome: str = "allowed"


class KnowledgeAssistantEvaluationObservation(StrictModel):
    case_id: str
    evidence_status: str
    grounded: bool
    citation_correct: bool
    citation_complete: bool
    citation_count: int = 0
    access_outcome: str = "allowed"


def evaluate_knowledge_assistant(
    cases: list[KnowledgeAssistantEvaluationCase],
    observations: list[KnowledgeAssistantEvaluationObservation],
) -> dict[str, float]:
    by_case = {item.case_id: item for item in observations}
    if set(by_case) != {item.case_id for item in cases}:
        raise ValueError("Evaluation observations must match the configured cases.")

    allowed = [item for item in cases if item.expected_access_outcome == "allowed"]
    answerable = [item for item in allowed if item.expected_grounded]
    insufficient = [item for item in allowed if item.expected_evidence_status == "insufficient"]
    conflicting = [item for item in allowed if item.expected_evidence_status == "conflicting"]
    cross_tenant = [item for item in cases if item.category == "cross_tenant"]
    cross_agent = [item for item in cases if item.category == "cross_agent"]

    return {
        "grounded_answer_accuracy": _rate([by_case[item.case_id].grounded for item in answerable]),
        "citation_correctness": _rate(
            [by_case[item.case_id].citation_correct for item in answerable]
        ),
        "citation_completeness": _rate(
            [
                by_case[item.case_id].citation_complete
                and by_case[item.case_id].citation_count >= item.expected_citation_count
                for item in answerable
            ]
        ),
        "insufficient_evidence_accuracy": _rate(
            [by_case[item.case_id].evidence_status == "insufficient" for item in insufficient]
        ),
        "conflict_detection_accuracy": _rate(
            [by_case[item.case_id].evidence_status == "conflicting" for item in conflicting]
        ),
        "cross_tenant_rejection": _rate(
            [by_case[item.case_id].access_outcome == "denied" for item in cross_tenant]
        ),
        "cross_agent_rejection": _rate(
            [by_case[item.case_id].access_outcome == "denied" for item in cross_agent]
        ),
    }


def _rate(values: list[bool]) -> float:
    return round(sum(values) / len(values), 4) if values else 1.0
