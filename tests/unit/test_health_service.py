"""Unit tests for the health service."""

from __future__ import annotations

import pytest

from taxos.application.services.health import HealthService
from taxos.core.config import Settings


@pytest.fixture
def health_service() -> HealthService:
    """Provide a health service with test settings."""
    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///",
        ENVIRONMENT="testing",
    )
    return HealthService(settings=settings)


class TestHealthService:
    """Tests for HealthService."""

    async def test_check_health_returns_healthy(self, health_service: HealthService) -> None:
        result = await health_service.check_health()
        assert result["status"] == "healthy"
        assert result["app_name"] == "TaxOS"
        assert "timestamp" in result

    async def test_check_health_includes_version(self, health_service: HealthService) -> None:
        result = await health_service.check_health()
        assert result["version"] == "0.1.0"
        assert result["environment"] == "testing"
