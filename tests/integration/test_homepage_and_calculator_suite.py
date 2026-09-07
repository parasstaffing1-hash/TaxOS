"""Comprehensive integration test suite for TaxOS Homepage, Catalog, and India Calculators."""

from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from taxos.main import app


@pytest.mark.asyncio
async def test_homepage_catalog_loading():
    """Verify GET /api/v1/catalog returns valid structured catalog tools."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/catalog?limit=50")
        assert res.status_code == 200
        tools = res.json()
        assert isinstance(tools, list)
        assert len(tools) > 0
        first_tool = tools[0]
        assert "id" in first_tool
        assert "title" in first_tool
        assert "jurisdiction" in first_tool
        assert "route" in first_tool


@pytest.mark.asyncio
async def test_catalog_jurisdiction_filter():
    """Verify GET /api/v1/catalog with jurisdiction filtering."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/catalog?jurisdiction=IN&limit=20")
        assert res.status_code == 200
        tools = res.json()
        assert all(t["jurisdiction"] == "IN" for t in tools)


@pytest.mark.asyncio
async def test_catalog_tool_not_found():
    """Verify GET /api/v1/catalog/{tool_id}/schema returns 404 for non-existent tool."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/catalog/non-existent-tool-xyz-9999/schema")
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_income_tax_regime_comparison_ay2025_26():
    """Verify Old vs New Regime calculation for AY 2025-26."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "financial_year": "2024-25",
            "assessment_year": "2025-26",
            "salary_income": 1500000,
            "house_property_income": -150000,
            "other_sources_income": 50000,
            "section_80c": 150000,
            "section_80d_self": 25000,
            "section_80ccd_1b": 50000,
            "section_80ccd_2": 0,
        }
        res = await client.post("/api/v1/india/income-tax/compare-regimes", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["financial_year"] == "2024-25"
        assert data["assessment_year"] == "2025-26"
        assert data["recommended_regime"] in ("new", "old")
        assert Decimal(str(data["new_regime_deductions"])) == Decimal("75000.0")
        assert Decimal(str(data["old_regime_deductions"])) == Decimal("275000.0")
        assert "summary_explanation" in data


@pytest.mark.asyncio
async def test_income_tax_rebate_87a_under_7lakhs():
    """Verify full Section 87A rebate for income <= 7 Lakhs under New Regime."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "financial_year": "2024-25",
            "assessment_year": "2025-26",
            "salary_income": 775000,  # 7.75L - 75k std deduction = 7.0L taxable
            "house_property_income": 0,
            "other_sources_income": 0,
            "section_80c": 0,
            "section_80d_self": 0,
            "section_80ccd_1b": 0,
            "section_80ccd_2": 0,
        }
        res = await client.post("/api/v1/india/income-tax/compare-regimes", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert Decimal(str(data["new_regime_taxable_income"])) == Decimal("700000.0")
        assert Decimal(str(data["new_regime_total_tax"])) == Decimal("0.0")
        assert Decimal(str(data["new_regime_rebate_87a"])) > Decimal("0.0")


@pytest.mark.asyncio
async def test_income_tax_invalid_input_validation():
    """Verify 422 Unprocessable Entity on negative income or invalid types."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "financial_year": "2024-25",
            "assessment_year": "2025-26",
            "salary_income": -50000,  # Invalid negative salary
        }
        res = await client.post("/api/v1/india/income-tax/compare-regimes", json=payload)
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_salary_ctc_take_home_calculation():
    """Verify POST /api/v1/india/salary/take-home converts CTC to take-home breakdown."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "annual_ctc": 1200000,
            "basic_percentage": 0.40,
            "hra_percentage": 0.20,
            "is_metro_city": True,
            "actual_rent_paid_annually": 0,
            "lta_claimed": 0,
            "employer_nps_percentage": 0,
            "professional_tax_annual": 2400,
            "bonus_annual": 0,
            "food_other_allowances": 0,
        }
        res = await client.post("/api/v1/india/salary/take-home?regime=new", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert Decimal(str(data["annual_ctc"])) == Decimal("1200000.0")
        assert Decimal(str(data["monthly_take_home"])) > Decimal("0.0")
        assert Decimal(str(data["annual_take_home"])) > Decimal("0.0")
        assert Decimal(str(data["employee_epf"])) > Decimal("0.0")
        assert Decimal(str(data["professional_tax"])) == Decimal("2400.0")


@pytest.mark.asyncio
async def test_all_main_calculator_endpoints_healthy():
    """Verify all primary calculator API endpoints respond successfully."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. TDS Sections
        res_tds = await client.get("/api/v1/india/tds/sections")
        assert res_tds.status_code == 200
        assert len(res_tds.json()) > 0

        # 2. HRA Exemption
        res_hra = await client.post(
            "/api/v1/india/salary/hra-exemption",
            json={
                "basic_salary": 600000,
                "hra_received": 240000,
                "annual_rent_paid": 300000,
                "is_metro": True,
            },
        )
        assert res_hra.status_code == 200
        assert "exempt_hra_amount" in res_hra.json()

        # 3. Capital Gains
        res_cg = await client.post(
            "/api/v1/india/capital-gains/calculate",
            json={
                "assessment_year": "2025-26",
                "transactions": [
                    {
                        "asset_name": "TCS Listed Equity",
                        "asset_type": "listed_equity_stocks",
                        "sale_date": "2024-11-15",
                        "purchase_date": "2022-10-10",
                        "holding_period_months": 25,
                        "sale_consideration": 500000,
                        "cost_of_acquisition": 300000,
                    }
                ],
            },
        )
        assert res_cg.status_code == 200
        assert "ltcg_112a_equity_gross" in res_cg.json()

        # 4. Advance Tax
        res_at = await client.post(
            "/api/v1/india/advance-tax/calculate",
            json={
                "total_tax_assessed": 150000,
                "tds_tcs_credits": 30000,
            },
        )
        assert res_at.status_code == 200
