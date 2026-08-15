from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

KnowledgeAssistantLanguage = Literal["en", "zh-CN"]
KnowledgeEvidenceStatus = Literal["sufficient", "insufficient", "conflicting"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class KnowledgeAssistantCitation(StrictModel):
    document_id: UUID
    document_name: str
    document_version_id: UUID
    document_version: int
    page_number: int | None
    section: str | None
    chunk_id: UUID
    source_metadata: dict[str, Any]
    similarity_score: float


class KnowledgeAssistantEvidence(KnowledgeAssistantCitation):
    content: str
    content_sha256: str


class KnowledgeAssistantDraft(StrictModel):
    language: KnowledgeAssistantLanguage
    answer: str = Field(min_length=1, max_length=6000)
    cited_chunk_ids: list[UUID] = Field(min_length=1, max_length=10)


class KnowledgeAssistantResult(StrictModel):
    evidence_status: KnowledgeEvidenceStatus
    answer: str
    citations: list[KnowledgeAssistantCitation]
    evidence: list[KnowledgeAssistantEvidence]
    conflict_keys: list[str] = Field(default_factory=list)
    retrieved_result_count: int
    model_provider: str
    model_id: str


class InvalidKnowledgeAssistantOutputError(Exception):
    pass


def detect_evidence_conflicts(evidence: list[KnowledgeAssistantEvidence]) -> list[str]:
    claims: dict[str, dict[str, set[UUID]]] = defaultdict(lambda: defaultdict(set))
    for item in evidence:
        document_metadata = item.source_metadata.get("document_metadata")
        if not isinstance(document_metadata, dict):
            continue
        raw_claims = document_metadata.get("claims")
        if isinstance(raw_claims, dict):
            for key, value in raw_claims.items():
                claims[str(key)][_stable_value(value)].add(item.document_id)
        group = document_metadata.get("conflict_group")
        if group is not None and "conflict_value" in document_metadata:
            claims[str(group)][_stable_value(document_metadata["conflict_value"])].add(
                item.document_id
            )
    return sorted(
        key
        for key, values in claims.items()
        if len(values) > 1 and len({doc for docs in values.values() for doc in docs}) > 1
    )


def validate_knowledge_assistant_draft(
    draft: KnowledgeAssistantDraft,
    language: KnowledgeAssistantLanguage,
    evidence: list[KnowledgeAssistantEvidence],
) -> list[KnowledgeAssistantCitation]:
    if draft.language != language:
        raise InvalidKnowledgeAssistantOutputError("Answer language does not match the request.")
    available = {item.chunk_id: item for item in evidence}
    unique_ids = list(dict.fromkeys(draft.cited_chunk_ids))
    if any(chunk_id not in available for chunk_id in unique_ids):
        raise InvalidKnowledgeAssistantOutputError("Answer cited evidence that was not retrieved.")
    markers = {int(value) for value in re.findall(r"\[(\d+)]", draft.answer)}
    expected_markers = set(range(1, len(unique_ids) + 1))
    if markers != expected_markers:
        raise InvalidKnowledgeAssistantOutputError("Answer is missing valid inline citations.")
    return [
        KnowledgeAssistantCitation.model_validate(
            available[chunk_id].model_dump(exclude={"content", "content_sha256"})
        )
        for chunk_id in unique_ids
    ]


def insufficient_result(
    language: KnowledgeAssistantLanguage,
    evidence: list[KnowledgeAssistantEvidence],
) -> KnowledgeAssistantResult:
    answer = (
        "现有已批准知识不足以可靠回答该问题。请补充或审核相关资料后再试。"
        if language == "zh-CN"
        else (
            "The approved knowledge does not provide enough evidence to answer reliably. "
            "Please add or review the relevant source material."
        )
    )
    return KnowledgeAssistantResult(
        evidence_status="insufficient",
        answer=answer,
        citations=[],
        evidence=evidence,
        retrieved_result_count=len(evidence),
        model_provider="not_called",
        model_id="not_called",
    )


def conflicting_result(
    language: KnowledgeAssistantLanguage,
    evidence: list[KnowledgeAssistantEvidence],
    conflict_keys: list[str],
) -> KnowledgeAssistantResult:
    answer = (
        "已批准来源之间存在冲突。系统不会自行合并这些说法。请由负责人审核来源版本后再回答。"
        if language == "zh-CN"
        else (
            "Approved sources conflict, so the assistant will not reconcile them "
            "automatically. A responsible reviewer must resolve the source versions "
            "before an answer is used."
        )
    )
    citations = [
        KnowledgeAssistantCitation.model_validate(
            item.model_dump(exclude={"content", "content_sha256"})
        )
        for item in evidence
    ]
    return KnowledgeAssistantResult(
        evidence_status="conflicting",
        answer=answer,
        citations=citations,
        evidence=evidence,
        conflict_keys=conflict_keys,
        retrieved_result_count=len(evidence),
        model_provider="not_called",
        model_id="not_called",
    )


def _stable_value(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
