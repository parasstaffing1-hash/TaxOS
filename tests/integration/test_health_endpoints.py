"""Integration tests for health endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestHealthEndpoints:
    """Integration tests for /api/v1/health endpoints."""

    async def test_liveness_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health", follow_redirects=True)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    async def test_liveness_includes_app_name(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health", follow_redirects=True)
        data = response.json()
        assert "app_name" in data
        assert "environment" in data
        assert "timestamp" in data

    async def test_readiness_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health/ready", follow_redirects=True)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in {"ready", "degraded"}
        assert "checks" in data
