"""Unit tests for configuration management."""

from __future__ import annotations

import pytest

from taxos.core.config import Settings


class TestSettings:
    """Tests for the Settings class."""

    def test_default_values(self) -> None:
        settings = Settings(
            DATABASE_URL="sqlite+aiosqlite:///",
            ENVIRONMENT="testing",
        )
        assert settings.APP_NAME == "TaxOS"
        assert settings.DEBUG is False
        assert settings.LOG_LEVEL == "INFO"

    def test_is_production(self) -> None:
        settings = Settings(
            ENVIRONMENT="production",
            DATABASE_URL="sqlite+aiosqlite:///",
            SECRET_KEY="test-production-secret-key-32-characters",
            ALLOWED_ORIGINS=["https://tax.example.com"],
        )
        assert settings.is_production is True

    def test_is_testing(self) -> None:
        settings = Settings(
            ENVIRONMENT="testing",
            DATABASE_URL="sqlite+aiosqlite:///",
        )
        assert settings.is_testing is True

    def test_invalid_log_level_raises(self) -> None:
        with pytest.raises(ValueError, match="LOG_LEVEL must be one of"):
            Settings(
                DATABASE_URL="sqlite+aiosqlite:///",
                ENVIRONMENT="testing",
                LOG_LEVEL="TRACE",
            )

    def test_log_level_normalised_to_upper(self) -> None:
        settings = Settings(
            DATABASE_URL="sqlite+aiosqlite:///",
            ENVIRONMENT="testing",
            LOG_LEVEL="debug",
        )
        assert settings.LOG_LEVEL == "DEBUG"
