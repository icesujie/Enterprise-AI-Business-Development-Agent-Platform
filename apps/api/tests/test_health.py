from __future__ import annotations

import httpx
import pytest

from sari_api.adapters.database import database_is_ready
from sari_api.main import app


@pytest.mark.asyncio
async def test_liveness_reports_service_version() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "api",
        "version": "0.1.0",
    }
    assert response.headers["X-Correlation-ID"]


@pytest.mark.asyncio
async def test_correlation_id_is_preserved_when_valid() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/health/live",
            headers={"X-Correlation-ID": "demo-request-0001"},
        )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "demo-request-0001"


@pytest.mark.asyncio
async def test_readiness_reports_healthy_database() -> None:
    async def database_ready() -> bool:
        return True

    app.dependency_overrides[database_is_ready] = database_ready
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "checks": {"database": "healthy"},
    }


@pytest.mark.asyncio
async def test_readiness_fails_when_database_is_unavailable() -> None:
    async def database_unavailable() -> bool:
        return False

    app.dependency_overrides[database_is_ready] = database_unavailable
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "status": "unhealthy",
        "checks": {"database": "unhealthy"},
    }
