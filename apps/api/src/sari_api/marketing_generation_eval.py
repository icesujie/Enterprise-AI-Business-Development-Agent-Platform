from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from sari_api.adapters.marketing_content_provider import build_marketing_content_provider
from sari_api.core.config import get_settings
from sari_api.domain.marketing_content_evaluation import (
    BusinessEvaluationOutcome,
    evaluate_business_quality,
    summarize_business,
)
from sari_api.domain.marketing_content_generation import (
    MarketingEvidence,
    validate_draft,
)

DATASET = Path(__file__).with_name("evaluation_data") / "marketing_generation_cases.v1.json"


async def evaluate(*, allow_paid_provider: bool, max_cases: int | None) -> dict[str, Any]:
    settings = get_settings()
    provider = build_marketing_content_provider(settings)
    if provider.provider_type != "mock" and not allow_paid_provider:
        raise RuntimeError("Real-provider evaluation requires --allow-paid-provider.")
    dataset = json.loads(DATASET.read_text())
    cases = dataset["cases"][:max_cases] if max_cases else dataset["cases"]
    if provider.provider_type != "mock" and len(cases) > 2:
        raise RuntimeError("Real-provider evaluation is limited to two cases per manual run.")
    outcomes: list[BusinessEvaluationOutcome] = []
    latencies: list[int] = []
    for case in cases:
        evidence = _evidence(case)
        request = _request(case)
        started = time.perf_counter()
        draft = await provider.generate(request, [evidence])
        latency = round((time.perf_counter() - started) * 1000)
        latencies.append(latency)
        validated = validate_draft(draft, str(case["content_type"]), [evidence])
        citation = {"chunk_id": str(evidence.chunk_id)}
        quality = evaluate_business_quality(validated, request, [citation])
        outcomes.append(
            BusinessEvaluationOutcome(
                case_id=case["case_id"],
                scenario=case["scenario"],
                content_type=case["content_type"],
                language=case["language"],
                quality=quality,
                structure_valid=True,
                citation_complete=True,
                bilingual_pair_id=case["pair_id"],
            )
        )
    return {
        "schema_version": "marketing_generation_baseline_v1",
        "dataset_version": dataset["schema_version"],
        "provider": provider.provider_type,
        "model": provider.model_id,
        "case_count": len(outcomes),
        "metrics": summarize_business(outcomes),
        "latency_ms": {
            "average": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "maximum": max(latencies, default=0),
        },
        "usage": "not_available_from_current_provider_contract",
        "cases": [item.model_dump(mode="json") for item in outcomes],
    }


def _request(case: dict[str, Any]) -> dict[str, object]:
    return {
        "content_type": case["content_type"],
        "audience": case["audience"],
        "channel": case["channel"],
        "language": case["language"],
        "topic": case["topic"],
        "business_objective": case["business_objective"],
        "call_to_action": case["call_to_action"],
    }


def _evidence(case: dict[str, Any]) -> MarketingEvidence:
    case_id = case["case_id"]
    return MarketingEvidence(
        document_id=uuid5(NAMESPACE_URL, f"marketing-eval-document:{case_id}"),
        document_name=f"Synthetic public marketing evidence — {case['scenario']}",
        document_version_id=uuid5(NAMESPACE_URL, f"marketing-eval-version:{case_id}"),
        document_version=1,
        chunk_id=uuid5(NAMESPACE_URL, f"marketing-eval-chunk:{case_id}"),
        page_number=1,
        section="Public capability evidence",
        similarity_score=0.92,
        content=case["evidence"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run governed marketing generation evaluation.")
    parser.add_argument("--allow-paid-provider", action="store_true")
    parser.add_argument("--max-cases", type=int, default=None)
    args = parser.parse_args()
    print(
        json.dumps(
            asyncio.run(
                evaluate(
                    allow_paid_provider=args.allow_paid_provider,
                    max_cases=args.max_cases,
                )
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
