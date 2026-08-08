from __future__ import annotations

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Sari Arta AI Business Development API"
    app_environment: Literal["development", "test", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    database_url: str = Field(
        default="postgresql+asyncpg://sariarta:sariarta_dev@localhost:5432/sariarta",
        min_length=1,
    )
    redis_url: str = Field(default="redis://localhost:6379/0", min_length=1)

    @model_validator(mode="after")
    def reject_local_production_services(self) -> Self:
        if self.app_environment == "production":
            local_markers = ("localhost", "127.0.0.1", "sariarta_dev")
            if any(marker in self.database_url for marker in local_markers):
                raise ValueError("production DATABASE_URL must not use local development values")
            if any(marker in self.redis_url for marker in local_markers):
                raise ValueError("production REDIS_URL must not use local development values")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
