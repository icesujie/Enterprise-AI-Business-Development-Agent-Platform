from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict


class AcceptanceCase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str
    scenario: str
    content_type: str
    audience: str
    language: str
    channel: str
    business_objective: str
    topic: str
    call_to_action: str


class AcceptanceDataset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset_version: str
    cases: tuple[AcceptanceCase, ...]


@lru_cache(maxsize=1)
def load_acceptance_dataset() -> AcceptanceDataset:
    path = (
        Path(__file__).parents[1]
        / "evaluation_data"
        / "marketing_business_acceptance_cases.v1.json"
    )
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    dataset = AcceptanceDataset.model_validate(payload)
    if len(dataset.cases) != 10:
        raise ValueError("The Phase 3.2 acceptance dataset must contain exactly ten cases.")
    return dataset
