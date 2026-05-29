"""Application settings loaded from environment (see `.env.example`)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str | None = None
    groq_model: str = "qwen/qwen3-32b"
    log_level: str = "INFO"
    require_approval: bool = False
    extraction_confidence_threshold: float = 0.5
    transcript_max_chars: int = 120_000


@lru_cache
def get_settings() -> Settings:
    return Settings()
