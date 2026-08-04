from decimal import Decimal

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_calculate_all_taxes(client: AsyncClient, setup_database):
    payload = {
        "income": {"annual_salary": "100000.00"},
        "location": {"country": "US", "state": "CA"},
        "demographics": {"tax_year": 2024, "filing_status": "single"},
    }

    response = await client.post("/api/v1/calculate/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "gross_income" in data
    assert data["gross_income"]["annual"] == "100000.00"
    assert data["total_tax"] == "27918.14"
    assert Decimal(data["taxable_income_by_jurisdiction"]["country:US"]["annual"]) == Decimal(
        "85400"
    )
    assert Decimal(data["taxable_income_by_jurisdiction"]["state:CA"]["annual"]) == Decimal(
        "94460"
    )
    assert "breakdown" in data


@pytest.mark.asyncio
async def test_calculate_payroll_tax_only(client: AsyncClient, setup_database):
    payload = {
        "income": {"annual_salary": "100000.00"},
        "location": {"country": "US", "state": "CA"},
        "demographics": {"tax_year": 2024, "filing_status": "single"},
    }

    response = await client.post("/api/v1/calculate/payroll-tax", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Assert no progressive income tax was applied, only payroll rules.
    for item in data["breakdown"]:
        assert (
            "payroll" in item["rule"].lower()
            or "medicare" in item["rule"].lower()
            or "social security" in item["rule"].lower()
        )


@pytest.mark.asyncio
async def test_calculate_all_taxes_applies_declared_pre_tax_deduction(
    client: AsyncClient, setup_database
):
    payload = {
        "income": {"annual_salary": "100000.00"},
        "location": {"country": "US", "state": "CA"},
        "demographics": {"tax_year": 2024, "filing_status": "single"},
        "deductions": {"pre_tax_401k": "10000.00"},
    }

    response = await client.post("/api/v1/calculate/", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Federal and California tax bases both receive the contribution, while
    # take-home pay is reduced by the contribution only once.
    assert Decimal(data["taxable_income_by_jurisdiction"]["country:US"]["annual"]) == Decimal(
        "75400"
    )
    assert Decimal(data["taxable_income_by_jurisdiction"]["state:CA"]["annual"]) == Decimal(
        "84460"
    )
    assert Decimal(data["employee_deductions"]["annual"]) == (
        Decimal(data["final_tax"]["annual"]) + Decimal("10000")
    )
    assert Decimal(data["net_income"]["annual"]) == (
        Decimal("100000") - Decimal(data["final_tax"]["annual"]) - Decimal("10000")
    )
