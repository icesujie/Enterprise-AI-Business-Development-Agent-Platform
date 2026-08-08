from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from sari_api import __version__
from sari_api.adapters.database import database_is_ready
from sari_api.application.health import build_readiness
from sari_api.domain.health import HealthStatus

router = APIRouter(prefix="/health", tags=["health"])


class LivenessResponse(BaseModel):
    status: HealthStatus
    service: str
    version: str


class ReadinessChecks(BaseModel):
    database: HealthStatus


class ReadinessResponse(BaseModel):
    status: HealthStatus
    checks: ReadinessChecks


@router.get("/live", response_model=LivenessResponse)
async def live() -> LivenessResponse:
    return LivenessResponse(
        status=HealthStatus.HEALTHY,
        service="api",
        version=__version__,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def ready(
    response: Response,
    database_ready: Annotated[bool, Depends(database_is_ready)],
) -> ReadinessResponse:
    readiness = build_readiness(database_ready=database_ready)
    if readiness.status is HealthStatus.UNHEALTHY:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status=readiness.status,
        checks=ReadinessChecks(database=readiness.database),
    )

