"""Health check response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Liveness check response."""

    model_config = ConfigDict(frozen=True)

    status: str
    app_name: str
    version: str
    environment: str
    timestamp: str


class ReadinessResponse(BaseModel):
    """Readiness check response including dependency statuses."""

    model_config = ConfigDict(frozen=True)

    status: str
    app_name: str
    version: str
    timestamp: str
    checks: dict[str, Any]
