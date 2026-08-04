"""Public dynamic-calculator regression coverage."""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_every_shipped_dynamic_calculator_executes_with_its_defaults(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/dynamic-calculators/")
    assert response.status_code == 200
    calculators: list[dict[str, Any]] = response.json()

    expected_slugs = {
        "bonus-tax-calculator",
        "ctc-calculator",
        "employer-cost-calculator",
        "income-tax-calculator",
        "net-to-gross-calculator",
        "paycheck-calculator",
    }
    assert {calculator["slug"] for calculator in calculators} == expected_slugs

    for calculator in calculators:
        payload = {
            field["id"]: field["default"] for field in calculator["inputs"] if "default" in field
        }
        calculation = await client.post(
            f"/api/v1/dynamic-calculators/{calculator['slug']}/calculate",
            json=payload,
        )
        assert calculation.status_code == 200, calculation.text
        result = calculation.json()["results"]
        assert result


@pytest.mark.asyncio
async def test_public_seo_routes_only_advertise_verified_calculators(client: AsyncClient) -> None:
    public_route = await client.get(
        "/api/v1/seo/page-data",
        params={
            "calculator_type": "after-tax-salary-calculator",
            "country": "US",
            "state": "CA",
            "year": 2024,
        },
    )
    assert public_route.status_code == 200

    unsupported_route = await client.get(
        "/api/v1/seo/page-data",
        params={
            "calculator_type": "after-tax-salary-calculator",
            "country": "US",
            "state": "NY",
            "year": 2024,
        },
    )
    assert unsupported_route.status_code == 404
