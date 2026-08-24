"""Application configuration management.

Uses pydantic-settings to load configuration from environment variables
and .env files with full validation and type safety.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_SECRET_KEY_LENGTH = 32
DEFAULT_DEVELOPMENT_SECRET = "development-only-taxos-secret-32"  # noqa: S105


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "TaxOS"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production", "testing"] = "development"

    # ── API ──────────────────────────────────────────────────────
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///taxos.db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── Security ─────────────────────────────────────────────────
    # Local-only fallback. Production validation below requires a provisioned key.
    SECRET_KEY: str = DEFAULT_DEVELOPMENT_SECRET
    FIELD_ENCRYPTION_KEY: str | None = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    AUTH_COOKIE_NAME: str = "taxos_access_token"
    AUTH_COOKIE_DOMAIN: str | None = None
    ADMIN_EMAILS: str = ""
    ENABLE_INTERNAL_TOOLS: bool = False
    MAGIC_LINK_EXPIRE_MINUTES: int = 15
    TRUSTED_PROXIES: list[str] = Field(default_factory=list)
    RATE_LIMIT_MAX_REQUESTS: int = Field(default=100, ge=1)
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, ge=1)
    AUTH_RATE_LIMIT_MAX_REQUESTS: int = Field(default=10, ge=1)
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, ge=1)

    # ── Logging ──────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "json"

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            msg = f"LOG_LEVEL must be one of {allowed}"
            raise ValueError(msg)
        return upper

    @model_validator(mode="after")
    def validate_production_settings(self) -> Settings:
        """Fail closed for settings that would make production unsafe."""
        if self.is_production:
            if (
                len(self.SECRET_KEY) < MIN_SECRET_KEY_LENGTH
                or self.SECRET_KEY == DEFAULT_DEVELOPMENT_SECRET
            ):
                raise ValueError("SECRET_KEY must be a random value of at least 32 characters")
            if (
                not self.FIELD_ENCRYPTION_KEY
                or len(self.FIELD_ENCRYPTION_KEY) < MIN_SECRET_KEY_LENGTH
                or self.FIELD_ENCRYPTION_KEY == DEFAULT_DEVELOPMENT_SECRET
            ):
                raise ValueError(
                    "FIELD_ENCRYPTION_KEY must be configured with a random value of at least 32 characters in production"
                )
            if self.DEBUG:
                raise ValueError("DEBUG must be false in production")
            if not self.ALLOWED_ORIGINS:
                raise ValueError("ALLOWED_ORIGINS must contain an explicit origin in production")
            if self.ENABLE_INTERNAL_TOOLS and not self.admin_emails:
                raise ValueError(
                    "ADMIN_EMAILS must contain at least one address when internal tools are enabled"
                )
        return self

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.ENVIRONMENT == "testing"

    @property
    def admin_emails(self) -> frozenset[str]:
        """Return normalized administrator addresses configured for this deployment."""
        return frozenset(
            address.strip().lower() for address in self.ADMIN_EMAILS.split(",") if address.strip()
        )

    @property
    def internal_tools_enabled(self) -> bool:
        """Keep unfinished operational tooling out of the production public surface."""
        return not self.is_production or self.ENABLE_INTERNAL_TOOLS


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
