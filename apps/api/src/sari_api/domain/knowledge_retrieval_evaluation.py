from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetrievalEvaluationCase:
    case_id: str
    language: str
    expected_chunk_ids: frozenset[str]
    expected_document_ids: frozenset[str]
    expect_insufficient_evidence: bool = False
    bilingual_pair_id: str | None = None


@dataclass(frozen=True, slots=True)
class RetrievalEvaluationObservation:
    case_id: str
    ranked_chunk_ids: tuple[str, ...]
    ranked_document_ids: tuple[str, ...]
    citation_complete: tuple[bool, ...]
    evidence_status: str
    latency_ms: float


def evaluate_retrieval(
    cases: list[RetrievalEvaluationCase],
    observations: list[RetrievalEvaluationObservation],
) -> dict[str, float]:
    by_id = {observation.case_id: observation for observation in observations}
    retrieval_cases = [case for case in cases if not case.expect_insufficient_evidence]
    no_evidence_cases = [case for case in cases if case.expect_insufficient_evidence]
    recalls: list[float] = []
    precisions: list[float] = []
    hit_at_one: list[float] = []
    reciprocal_ranks: list[float] = []
    citation_values: list[float] = []

    for case in retrieval_cases:
        observation = by_id[case.case_id]
        returned = observation.ranked_chunk_ids
        relevant_returned = [
            chunk_id for chunk_id in returned if chunk_id in case.expected_chunk_ids
        ]
        recalls.append(len(set(relevant_returned)) / len(case.expected_chunk_ids))
        precisions.append(len(relevant_returned) / len(returned) if returned else 0.0)
        hit_at_one.append(float(bool(returned and returned[0] in case.expected_chunk_ids)))
        first_relevant_rank = next(
            (
                rank
                for rank, chunk_id in enumerate(returned, 1)
                if chunk_id in case.expected_chunk_ids
            ),
            None,
        )
        reciprocal_ranks.append(1.0 / first_relevant_rank if first_relevant_rank else 0.0)
        citation_values.extend(float(value) for value in observation.citation_complete)

    insufficient_correct = [
        by_id[case.case_id].evidence_status == "insufficient_evidence" for case in no_evidence_cases
    ]
    latencies = [observation.latency_ms for observation in observations]
    return {
        "recall_at_k": _mean(recalls),
        "precision_at_k": _mean(precisions),
        "hit_at_1": _mean(hit_at_one),
        "mrr": _mean(reciprocal_ranks),
        "citation_completeness": _mean(citation_values),
        "insufficient_evidence_accuracy": _mean([float(value) for value in insufficient_correct]),
        "mean_latency_ms": _mean(latencies),
        "max_latency_ms": max(latencies, default=0.0),
    }


def evaluate_bilingual_consistency(
    cases: list[RetrievalEvaluationCase],
    observations: list[RetrievalEvaluationObservation],
) -> dict[str, float]:
    by_id = {observation.case_id: observation for observation in observations}
    pairs: dict[str, list[RetrievalEvaluationCase]] = {}
    for case in cases:
        if case.bilingual_pair_id:
            pairs.setdefault(case.bilingual_pair_id, []).append(case)

    same_source: list[float] = []
    chunk_jaccard: list[float] = []
    rank_consistency: list[float] = []
    for pair in pairs.values():
        if len(pair) != 2:
            continue
        first, second = (by_id[pair[0].case_id], by_id[pair[1].case_id])
        first_docs = set(first.ranked_document_ids)
        second_docs = set(second.ranked_document_ids)
        same_source.append(float(bool(first_docs & second_docs)))
        first_chunks = set(first.ranked_chunk_ids)
        second_chunks = set(second.ranked_chunk_ids)
        union = first_chunks | second_chunks
        chunk_jaccard.append(len(first_chunks & second_chunks) / len(union) if union else 1.0)
        first_shared_rank = _first_shared_document_rank(first, second_docs)
        second_shared_rank = _first_shared_document_rank(second, first_docs)
        if first_shared_rank is None or second_shared_rank is None:
            rank_consistency.append(0.0)
        else:
            rank_consistency.append(1.0 / (1.0 + abs(first_shared_rank - second_shared_rank)))

    return {
        "same_source_document_rate": _mean(same_source),
        "relevant_chunk_set_jaccard": _mean(chunk_jaccard),
        "ranking_consistency": _mean(rank_consistency),
    }


def _first_shared_document_rank(
    observation: RetrievalEvaluationObservation, other_documents: set[str]
) -> int | None:
    return next(
        (
            rank
            for rank, document_id in enumerate(observation.ranked_document_ids, 1)
            if document_id in other_documents
        ),
        None,
    )


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
