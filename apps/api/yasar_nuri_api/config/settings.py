from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_env: Literal["development", "staging", "production"] = Field(default="development", alias="API_ENV")

    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")
    api_key: str | None = Field(default=None, alias="API_KEY")
    admin_reindex_enabled: bool = Field(default=False, alias="ADMIN_REINDEX_ENABLED")
    admin_key: str | None = Field(default=None, alias="ADMIN_KEY")

    database_url: str = Field(
        default="postgresql+asyncpg://yasar:yasar@localhost:5432/yasar_nuri",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    index_version: int = Field(default=1, alias="INDEX_VERSION")
    cache_ttl_rewrite_seconds: int = Field(default=86400, alias="CACHE_TTL_REWRITE_SECONDS")
    cache_ttl_retrieval_seconds: int = Field(default=3600, alias="CACHE_TTL_RETRIEVAL_SECONDS")
    cache_ttl_answer_seconds: int = Field(default=1800, alias="CACHE_TTL_ANSWER_SECONDS")

    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_llm_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_LLM_MODEL")
    gemini_embedding_model: str = Field(default="models/text-embedding-004", alias="GEMINI_EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=768, alias="EMBEDDING_DIMENSION")

    retrieval_vector_top_k: int = Field(default=30, alias="RETRIEVAL_VECTOR_TOP_K")
    retrieval_fts_top_k: int = Field(default=30, alias="RETRIEVAL_FTS_TOP_K")
    retrieval_merged_top_n: int = Field(default=20, alias="RETRIEVAL_MERGED_TOP_N")
    retrieval_rerank_top_k: int = Field(default=8, alias="RETRIEVAL_RERANK_TOP_K")
    retrieval_min_confidence: float = Field(default=0.35, alias="RETRIEVAL_MIN_CONFIDENCE")
    rerank_enabled: bool = Field(default=True, alias="RERANK_ENABLED")

    max_question_length: int = Field(default=2000, alias="MAX_QUESTION_LENGTH")
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")

    feature_local_tts_default: bool = Field(default=True, alias="FEATURE_LOCAL_TTS_DEFAULT")
    feature_speech_input_default: bool = Field(default=True, alias="FEATURE_SPEECH_INPUT_DEFAULT")
    feature_debug_evidence: bool = Field(default=False, alias="FEATURE_DEBUG_EVIDENCE")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    prompt_assets_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[4] / "packages" / "prompt_assets",
        alias="PROMPT_ASSETS_DIR",
    )

    @field_validator("prompt_assets_dir", mode="before")
    @classmethod
    def coerce_path(cls, v: object) -> Path:
        if v is None or v == "":
            return Path(__file__).resolve().parents[4] / "packages" / "prompt_assets"
        if isinstance(v, Path):
            return v
        return Path(str(v))

    def cors_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
