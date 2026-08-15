from __future__ import annotations

import json
from pathlib import Path

from sari_api.domain.knowledge_retrieval_evaluation import (
    RetrievalEvaluationCase,
    RetrievalEvaluationObservation,
    evaluate_bilingual_consistency,
    evaluate_retrieval,
)

FIXTURE = Path(__file__).parent / "fixtures" / "knowledge_retrieval_evaluation.v1.json"


def test_retrieval_regression_baseline_meets_acceptance_thresholds() -> None:
    baseline = json.loads(FIXTURE.read_text())
    cases = [
        RetrievalEvaluationCase(
            case_id=item["case_id"],
            language=item["language"],
            expected_chunk_ids=frozenset(item["expected_chunk_ids"]),
            expected_document_ids=frozenset(item["expected_document_ids"]),
            expect_insufficient_evidence=item.get("expect_insufficient_evidence", False),
            bilingual_pair_id=item.get("bilingual_pair_id"),
        )
        for item in baseline["cases"]
    ]
    observations = [
        RetrievalEvaluationObservation(
            case_id=item["case_id"],
            ranked_chunk_ids=tuple(item["ranked_chunk_ids"]),
            ranked_document_ids=tuple(item["ranked_document_ids"]),
            citation_complete=tuple(item["citation_complete"]),
            evidence_status=item["evidence_status"],
            latency_ms=item["latency_ms"],
        )
        for item in baseline["observations"]
    ]
    measured = {
        **evaluate_retrieval(cases, observations),
        **evaluate_bilingual_consistency(cases, observations),
    }
    assert measured == baseline["baseline_results"]
    thresholds = baseline["acceptance_thresholds"]
    results = measured
    for metric, threshold in thresholds.items():
        if metric == "max_latency_ms":
            assert results[metric] <= threshold
        else:
            assert results[metric] >= threshold


def test_metrics_include_hit_at_one_mrr_and_bilingual_consistency() -> None:
    cases = [
        RetrievalEvaluationCase(
            "ventilation-en", "en", frozenset({"core"}), frozenset({"guide"}), False, "v"
        ),
        RetrievalEvaluationCase(
            "ventilation-zh", "zh-CN", frozenset({"core"}), frozenset({"guide"}), False, "v"
        ),
        RetrievalEvaluationCase("unsupported", "en", frozenset(), frozenset(), True),
    ]
    observations = [
        RetrievalEvaluationObservation(
            "ventilation-en", ("core",), ("guide",), (True,), "sufficient_candidates", 12
        ),
        RetrievalEvaluationObservation(
            "ventilation-zh", ("core",), ("guide",), (True,), "sufficient_candidates", 14
        ),
        RetrievalEvaluationObservation("unsupported", (), (), (), "insufficient_evidence", 9),
    ]
    metrics = evaluate_retrieval(cases, observations)
    bilingual = evaluate_bilingual_consistency(cases, observations)
    assert metrics["hit_at_1"] == 1
    assert metrics["mrr"] == 1
    assert metrics["insufficient_evidence_accuracy"] == 1
    assert bilingual == {
        "same_source_document_rate": 1,
        "relevant_chunk_set_jaccard": 1,
        "ranking_consistency": 1,
    }
