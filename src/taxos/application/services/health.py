"""Health check service.

Provides application health and readiness checks including
database connectivity verification.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from taxos.core.config import Settings

logger = structlog.get_logger(__name__)


class HealthService:
    """Service for application health and readiness checks."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def check_health(self) -> dict[str, Any]:
        """Return basic liveness information."""
        return {
            "status": "healthy",
            "app_name": self._settings.APP_NAME,
            "version": self._settings.APP_VERSION,
            "environment": self._settings.ENVIRONMENT,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def check_readiness(self, session: AsyncSession) -> dict[str, Any]:
        """Check readiness including database connectivity."""
        checks: dict[str, Any] = {}

        # Database check
        try:
            await session.execute(text("SELECT 1"))
            checks["database"] = {"status": "connected"}
        except Exception as exc:
            logger.exception("database_health_check_failed", error=str(exc))
            checks["database"] = {"status": "disconnected", "error": str(exc)}

        all_healthy = all(
            check.get("status") in {"connected", "healthy"} for check in checks.values()
        )

        return {
            "status": "ready" if all_healthy else "degraded",
            "app_name": self._settings.APP_NAME,
            "version": self._settings.APP_VERSION,
            "timestamp": datetime.now(UTC).isoformat(),
            "checks": checks,
        }
