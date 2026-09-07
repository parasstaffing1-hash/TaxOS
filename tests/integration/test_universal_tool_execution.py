"""Integration tests for universal catalog tool schema retrieval and calculation API."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from taxos.application.tools.executor import get_universal_tool_executor
from taxos.main import app


@pytest.mark.asyncio
async def test_get_tool_schema_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Deductions tool (#51)
        res = await client.get("/api/v1/catalog/section-80c-calculator/schema")
        assert res.status_code == 200
        data = res.json()
        assert data["tool_id"] == "section-80c-calculator"
        assert data["family"] == "india_deductions"
        assert data["status"] == "not_started"
        assert len(data["input_fields"]) >= 1
        assert len(data["official_sources"]) >= 1


@pytest.mark.asyncio
async def test_unreleased_catalog_tool_is_not_executable():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "sec_80c_epf_ppf_elss_lic_tuition": 150000,
            "sec_80ccd1b_nps_additional": 50000,
            "sec_80d_self_family_premium": 25000,
        }
        res = await client.post(
            "/api/v1/catalog/section-80c-calculator/calculate",
            json=payload,
        )
        assert res.status_code == 409
        assert "not released yet" in res.json()["detail"]


@pytest.mark.asyncio
async def test_unreleased_house_property_tool_is_not_executable():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "occupancy_type": "self_occupied",
            "home_loan_interest_annual": 200000,
        }
        res = await client.post(
            "/api/v1/catalog/house-property-income-calculator/calculate",
            json=payload,
        )
        assert res.status_code == 409
        assert "not released yet" in res.json()["detail"]


@pytest.mark.asyncio
async def test_unreleased_business_tool_is_not_executable():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "scheme_type": "44AD",
            "gross_turnover_digital": 10000000,  # 1 Cr
            "gross_turnover_cash": 0,
        }
        res = await client.post(
            "/api/v1/catalog/section-44ad-calculator/calculate",
            json=payload,
        )
        assert res.status_code == 409
        assert "not released yet" in res.json()["detail"]


def test_universal_executor_keeps_domain_engines_available_for_release_work():
    executor = get_universal_tool_executor()
    result = executor.execute_tool(
        tool_id="section-80c-calculator",
        payload={
            "sec_80c_epf_ppf_elss_lic_tuition": 150000,
            "sec_80ccd1b_nps_additional": 50000,
            "sec_80d_self_family_premium": 25000,
        },
    )

    assert result.calculation["total_deductions_allowed"] == "225000.00"


@pytest.mark.asyncio
async def test_calculate_catalog_tool_global_tax():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "country_code": "US",
            "tax_type": "income_tax",
            "gross_income_or_revenue": 100000,
        }
        res = await client.post(
            "/api/v1/catalog/global-income-tax-calculator/calculate",
            json=payload,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["jurisdiction"] == "US"
        assert "net_tax_payable" in data["calculation"]
