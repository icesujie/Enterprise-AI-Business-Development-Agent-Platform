from __future__ import annotations

from functools import lru_cache
from pathlib import Path
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
    agent_stale_after_seconds: int = Field(default=120, ge=30, le=3600)
    agent_recovery_interval_seconds: int = Field(default=30, ge=10, le=300)
    knowledge_storage_path: Path = Path(".local/knowledge")
    knowledge_max_upload_bytes: int = Field(default=10 * 1024 * 1024, ge=1024, le=50 * 1024 * 1024)
    knowledge_chunk_size: int = Field(default=1200, ge=200, le=4000)
    knowledge_chunk_overlap: int = Field(default=200, ge=0, le=1000)
    knowledge_embedding_provider: Literal["mock", "openai"] = "mock"
    knowledge_embedding_model: str = "text-embedding-3-small"
    knowledge_embedding_dimensions: int = Field(default=1536, ge=128, le=3072)
    knowledge_queue_name: str = "sari-arta:knowledge-ingestion"
    knowledge_processing_queue_name: str = "sari-arta:knowledge-processing"
    knowledge_retrieval_min_similarity: float = Field(default=0.15, ge=0, le=1)
    knowledge_retrieval_min_evidence_count: int = Field(default=1, ge=1, le=5)
    knowledge_retrieval_diagnostic_candidates: int = Field(default=5, ge=0, le=20)
    knowledge_assistant_top_k: int = Field(default=5, ge=1, le=10)

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
        if self.knowledge_embedding_provider == "openai" and self.openai_api_key is None:
            raise ValueError("OpenAI knowledge embeddings require OPENAI_API_KEY")
        if self.knowledge_chunk_overlap >= self.knowledge_chunk_size:
            raise ValueError("KNOWLEDGE_CHUNK_OVERLAP must be smaller than KNOWLEDGE_CHUNK_SIZE")
        if self.knowledge_embedding_dimensions != 1536:
            raise ValueError("Phase 2.5 knowledge embeddings require 1536 dimensions")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
