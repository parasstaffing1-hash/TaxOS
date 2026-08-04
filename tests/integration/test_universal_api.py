import pytest
from httpx import AsyncClient
from taxos.domain.rules import JurisdictionLevel, FilingStatus

@pytest.mark.asyncio
async def test_calculate_all_taxes(client: AsyncClient, setup_database):
    payload = {
        "income": {"annual_salary": "100000.00"},
        "location": {"country": "US", "state": "CA"},
        "demographics": {"tax_year": 2024, "filing_status": "single"}
    }
    
    response = await client.post("/api/v1/calculate/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "gross_income" in data
    assert data["gross_income"]["annual"] == "100000.00"
    assert "breakdown" in data

@pytest.mark.asyncio
async def test_calculate_payroll_tax_only(client: AsyncClient, setup_database):
    payload = {
        "income": {"annual_salary": "100000.00"},
        "location": {"country": "US", "state": "CA"},
        "demographics": {"tax_year": 2024, "filing_status": "single"}
    }
    
    response = await client.post("/api/v1/calculate/payroll-tax", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Assert no progressive income tax was applied, only payroll rules.
    for item in data["breakdown"]:
        assert "payroll" in item["rule"].lower() or "medicare" in item["rule"].lower() or "social security" in item["rule"].lower()
