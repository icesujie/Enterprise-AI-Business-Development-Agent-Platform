from __future__ import annotations

from sari_api.domain.health import Readiness, evaluate_readiness


def build_readiness(*, database_ready: bool) -> Readiness:
    return evaluate_readiness(database_ready=database_ready)

