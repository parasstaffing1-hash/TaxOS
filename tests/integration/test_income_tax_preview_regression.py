"""Regression test for India Income Tax Calculator preview endpoint and payload."""

from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from taxos.main import app


@pytest.mark.asyncio
async def test_compare_regimes_preview_payload_ay2025_26():
    """Verify POST /api/v1/india/income-tax/compare-regimes with exact frontend payload."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "financial_year": "2024-25",
            "assessment_year": "2025-26",
            "salary_income": 1200000,
            "house_property_income": -200000,
            "other_sources_income": 0,
            "section_80c": 150000,
            "section_80d_self": 25000,
            "section_80ccd_1b": 50000,
            "section_80ccd_2": 0,
        }
        res = await client.post(
            "/api/v1/india/income-tax/compare-regimes",
            json=payload,
        )
        assert res.status_code == 200
        data = res.json()

        assert data["financial_year"] == "2024-25"
        assert data["assessment_year"] == "2025-26"
        assert Decimal(str(data["gross_total_income"])) > Decimal("0")
        assert "old_regime_total_tax" in data
        assert "new_regime_total_tax" in data
        assert data["recommended_regime"] in ("new", "old")
        assert "tax_savings" in data
        assert "summary_explanation" in data
        assert Decimal(str(data["new_regime_deductions"])) == Decimal(
            "75000.0"
        )  # ₹75k S/D in AY 2025-26
        # Old regime deductions = ₹50k S/D + ₹1.5L (80C) + ₹25k (80D) + ₹50k (80CCD1B) = ₹2.75L
        assert Decimal(str(data["old_regime_deductions"])) == Decimal("275000.0")


@pytest.mark.asyncio
async def test_compare_regimes_preview_payload_ay2024_25():
    """Verify POST /api/v1/india/income-tax/compare-regimes for AY 2024-25."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "financial_year": "2023-24",
            "assessment_year": "2024-25",
            "salary_income": 1200000,
            "house_property_income": 0,
            "other_sources_income": 50000,
            "section_80c": 150000,
            "section_80d_self": 25000,
            "section_80ccd_1b": 50000,
            "section_80ccd_2": 0,
        }
        res = await client.post(
            "/api/v1/india/income-tax/compare-regimes",
            json=payload,
        )
        assert res.status_code == 200
        data = res.json()

        assert data["financial_year"] == "2023-24"
        assert data["assessment_year"] == "2024-25"
        assert Decimal(str(data["new_regime_deductions"])) == Decimal(
            "50000.0"
        )  # ₹50k S/D in AY 2024-25
