"""Integration tests for the Calculator API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from taxos.main import app
from taxos.domain.rules import FilingStatus
from taxos.domain.financial.currency import Currency
from taxos.infrastructure.rules.file_repository import FileBasedRuleRepository


@pytest.fixture
def mock_rule_dir(tmp_path):
    """Setup a simple rule for testing."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir(exist_ok=True)
    
    us_dir = rules_dir / "US" / "2024"
    us_dir.mkdir(parents=True)
    us_rule = us_dir / "federal.yaml"
    us_rule.write_text(
        """
        jurisdiction: "US"
        level: "country"
        tax_year: 2024
        rules:
          all:
            - type: "flat"
              name: "Flat Federal Tax"
              rate: 0.15
        """
    )
    return rules_dir


@pytest.mark.asyncio
class TestCalculatorAPI:
    """Test the full HTTP REST API."""

    @pytest.fixture(autouse=True)
    def override_dependencies(self, mock_rule_dir, monkeypatch):
        # We need the real endpoints to load from our tmp rules dir.
        # This is a bit hacky without a real DI container, but works for the test.
        from taxos.api.v1 import deps
        
        def mock_get_calculator_service():
            from taxos.application.services.salary_calculator import SalaryCalculatorService
            from taxos.application.services.rule_engine import RuleEngineService
            from taxos.application.services.currency import CurrencyEngine
            from taxos.application.calculations.engine import TaxCalculator
            from taxos.infrastructure.currency.mock_provider import MockExchangeRateProvider
            from taxos.infrastructure.rules.file_repository import FileBasedRuleRepository
            
            repo = FileBasedRuleRepository(base_dir=str(mock_rule_dir))
            rule_service = RuleEngineService(repo)
            currency_engine = CurrencyEngine(provider=MockExchangeRateProvider())
            tax_calculator = TaxCalculator()
            return SalaryCalculatorService(rule_service, currency_engine, tax_calculator)
            
        app.dependency_overrides[deps.get_salary_calculator_service] = mock_get_calculator_service

    async def test_calculate_salary_json(self) -> None:
        """Test the standard JSON endpoint."""
        payload = {
            "income": {
                "gross_income": "100000",
                "currency": "USD"
            },
            "location": {
                "country": "US"
            },
            "demographics": {
                "filing_status": FilingStatus.SINGLE.value,
                "tax_year": 2024
            }
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/after-tax-salary-calculator/US", json=payload)
            
        assert response.status_code == 200
        data = response.json()
        assert data["total_tax"] == "15000.00"
        assert data["net_income"]["annual"] == "85000.00"
        assert len(data["breakdown"]) == 1
        assert data["breakdown"][0]["name"] == "Flat Federal Tax"

    async def test_calculate_salary_pdf(self) -> None:
        """Test the PDF export endpoint."""
        payload = {
            "income": {
                "gross_income": "50000",
                "currency": "USD"
            },
            "location": {
                "country": "US"
            },
            "demographics": {
                "filing_status": FilingStatus.SINGLE.value,
                "tax_year": 2024
            }
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/after-tax-salary-calculator/US/pdf", json=payload)
            
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert b"%PDF" in response.content

    async def test_calculate_salary_excel(self) -> None:
        """Test the Excel export endpoint."""
        payload = {
            "income": {
                "gross_income": "75000",
                "currency": "USD"
            },
            "location": {
                "country": "US"
            },
            "demographics": {
                "filing_status": FilingStatus.SINGLE.value,
                "tax_year": 2024
            }
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/after-tax-salary-calculator/US/excel", json=payload)
            
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert b"PK" in response.content  # Excel is a zipped XML format
