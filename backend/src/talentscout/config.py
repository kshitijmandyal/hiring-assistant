"""Typed application settings, read once from the environment."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from talentscout.constants import CLAUDE_MAX_TOKENS, CLAUDE_MODEL
from talentscout.constants.auth import JWT_SECRET_MIN_BYTES


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["local", "test", "production"] = "local"
    debug: bool = False

    anthropic_api_key: SecretStr

    # Signs every JWT. Rotating it invalidates all sessions and invite links.
    jwt_secret: SecretStr
    claude_model: str = CLAUDE_MODEL
    claude_max_tokens: int = CLAUDE_MAX_TOKENS

    database_url: PostgresDsn

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    # Human-readable logs locally, JSON everywhere a log aggregator is reading.
    log_json: bool = False

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    api_prefix: str = "/api/v1"

    @field_validator("jwt_secret")
    @classmethod
    def _reject_weak_jwt_secret(cls, value: SecretStr) -> SecretStr:
        """Fail at startup rather than sign tokens with a guessable key.

        RFC 7518 sets 32 bytes as the floor for HMAC-SHA256; a short secret is
        brute-forceable, and anyone who recovers it can mint interviewer tokens.
        """
        secret = value.get_secret_value()
        if len(secret.encode()) < JWT_SECRET_MIN_BYTES:
            raise ValueError(
                f"JWT_SECRET must be at least {JWT_SECRET_MIN_BYTES} bytes. "
                'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )
        if secret.startswith("change-me"):
            raise ValueError("JWT_SECRET is still the placeholder from .env.example")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
