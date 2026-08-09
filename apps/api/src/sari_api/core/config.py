from __future__ import annotations

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
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
    auth_issuer: str = "https://local.supabase.example/auth/v1"
    auth_audience: str = "authenticated"
    auth_jwks_url: str = "https://local.supabase.example/auth/v1/.well-known/jwks.json"
    auth_jwks_cache_seconds: int = Field(default=600, ge=60, le=1200)
    development_auth_subject: str | None = None
    public_site_token: str = "local-public-site-token"
    public_tenant_id: str = "10000000-0000-4000-8000-000000000001"
    public_rate_limit: int = Field(default=10, ge=1, le=1000)
    public_rate_window_seconds: int = Field(default=60, ge=10, le=3600)
    ai_enabled: bool = False
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5-mini"
    agent_queue_name: str = "sari-arta:agent-runs"
    agent_timeout_seconds: int = Field(default=45, ge=5, le=180)
    agent_max_turns: int = Field(default=3, ge=1, le=8)
    agent_max_output_tokens: int = Field(default=1200, ge=200, le=4000)
    agent_max_attempts: int = Field(default=3, ge=1, le=5)
    agent_retry_base_seconds: int = Field(default=2, ge=1, le=60)

    @model_validator(mode="after")
    def reject_local_production_services(self) -> Self:
        if self.app_environment == "production":
            local_markers = ("localhost", "127.0.0.1", "sariarta_dev")
            if any(marker in self.database_url for marker in local_markers):
                raise ValueError("production DATABASE_URL must not use local development values")
            if any(marker in self.redis_url for marker in local_markers):
                raise ValueError("production REDIS_URL must not use local development values")
            if ".example" in self.auth_issuer or ".example" in self.auth_jwks_url:
                raise ValueError("production Supabase Auth endpoints must be configured")
            if self.development_auth_subject is not None:
                raise ValueError("production must disable development authentication")
            if self.public_site_token == "local-public-site-token":
                raise ValueError("production PUBLIC_SITE_TOKEN must be configured")
        if self.ai_enabled and self.openai_api_key is None:
            raise ValueError("AI_ENABLED requires OPENAI_API_KEY")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
