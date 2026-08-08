from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True, slots=True)
class Readiness:
    status: HealthStatus
    database: HealthStatus


def evaluate_readiness(*, database_ready: bool) -> Readiness:
    database = HealthStatus.HEALTHY if database_ready else HealthStatus.UNHEALTHY
    return Readiness(status=database, database=database)
