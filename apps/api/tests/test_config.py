from __future__ import annotations

import pytest
from pydantic import ValidationError

from sari_api.core.config import Settings


def test_development_defaults_are_safe_for_local_use() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_environment == "development"
    assert "sariarta_dev" in settings.database_url


@pytest.mark.parametrize(
    ("database_url", "redis_url"),
    [
        (
            "postgresql+asyncpg://sariarta:sariarta_dev@localhost:5432/sariarta",
            "redis://cache.internal:6379/0",
        ),
        (
            "postgresql+asyncpg://app:secret@database.internal:5432/sariarta",
            "redis://localhost:6379/0",
        ),
    ],
)
def test_production_rejects_local_service_configuration(
    database_url: str,
    redis_url: str,
) -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_environment="production",
            database_url=database_url,
            redis_url=redis_url,
        )

