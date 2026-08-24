"""Integration tests for universal catalog tool schema retrieval and calculation API."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

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
        assert len(data["input_fields"]) >= 1
        assert len(data["official_sources"]) >= 1


@pytest.mark.asyncio
async def test_calculate_catalog_tool_deductions():
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
        assert res.status_code == 200
        data = res.json()
        assert data["jurisdiction"] == "IN"
        assert data["tax_type"] == "income_tax_deductions"
        assert "calculation_id" in data
        assert "calculation" in data
        assert data["calculation"]["total_deductions_allowed"] == "225000.00"
        assert len(data["steps"]) >= 3


@pytest.mark.asyncio
async def test_calculate_catalog_tool_house_property():
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
        assert res.status_code == 200
        data = res.json()
        assert data["jurisdiction"] == "IN"
        assert data["calculation"]["interest_deduction_24b"] == "200000.00"
        assert data["calculation"]["net_income_or_loss"] == "-200000.00"


@pytest.mark.asyncio
async def test_calculate_catalog_tool_business_44ad():
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
        assert res.status_code == 200
        data = res.json()
        assert data["calculation"]["presumptive_profit"] == "600000.00"  # 6% of 1 Cr


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
