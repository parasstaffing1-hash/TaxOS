"""Unit tests for the Salary Calculator Service."""

from __future__ import annotations

from decimal import Decimal

import pytest

from taxos.api.schemas.calculator import CalculatorRequest
from taxos.application.calculations.engine import TaxCalculator
from taxos.application.services.currency import CurrencyEngine
from taxos.application.services.rule_engine import RuleEngineService
from taxos.application.services.salary_calculator import SalaryCalculatorService
from taxos.domain.financial.currency import Currency
from taxos.domain.financial.validation import (
    DeductionsProfile,
    DemographicProfile,
    IncomeProfile,
    LocationProfile,
)
from taxos.domain.rules import FilingStatus
from taxos.infrastructure.currency.mock_provider import MockExchangeRateProvider
from taxos.infrastructure.rules.file_repository import FileBasedRuleRepository


@pytest.fixture
def calc_service(tmp_path) -> SalaryCalculatorService:
    # Setup mock rules directory
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    # Write a simple rule
    us_dir = rules_dir / "US" / "2024"
    us_dir.mkdir(parents=True)
    us_rule = us_dir / "federal.yaml"
    us_rule.write_text("""
        jurisdiction: "US"
        level: "country"
        tax_year: 2024
        rules:
          all:
            - type: "progressive"
              name: "Federal Income Tax"
              brackets:
                - min_amount: 0
                  max_amount: 50000
                  rate: 0.10
                - min_amount: 50000
                  rate: 0.20
        """)

    repo = FileBasedRuleRepository(base_dir=str(rules_dir))
    rule_service = RuleEngineService(repo)
    currency_engine = CurrencyEngine(provider=MockExchangeRateProvider())
    tax_calculator = TaxCalculator()

    return SalaryCalculatorService(rule_service, currency_engine, tax_calculator)


@pytest.mark.asyncio
class TestSalaryCalculatorService:
    """Test orchestration of engines for full salary calculation."""

    async def test_full_calculation_flow(self, calc_service: SalaryCalculatorService) -> None:
        request = CalculatorRequest(
            income=IncomeProfile(gross_income="100,000", currency=Currency.USD),
            location=LocationProfile(country="US"),
            demographics=DemographicProfile(filing_status=FilingStatus.SINGLE, tax_year=2024),
            deductions=DeductionsProfile(retirement_contribution="0"),
        )

        response = await calc_service.calculate(request)

        # 10% on first 50k = 5,000
        # 20% on next 50k = 10,000
        # Total = 15,000
        assert response.total_tax == Decimal("15000.00")
        assert response.gross_income.annual == Decimal("100000.00")
        assert response.net_income.annual == Decimal("85000.00")
        assert response.effective_tax_rate == Decimal("15.00")
        assert response.marginal_tax_rate == Decimal("20.00")

        # Ensure it maps properly
        assert response.federal_tax == Decimal("15000.00")
        assert response.state_tax == Decimal("0.00")

        # Period conversions check
        # Monthly = 100000 / 12 = 8333.33
        assert response.gross_income.monthly == Decimal("8333.33")

    async def test_declared_pre_tax_deduction_reduces_taxable_and_take_home(
        self, calc_service: SalaryCalculatorService
    ) -> None:
        request = CalculatorRequest(
            income=IncomeProfile(gross_income="100000", currency=Currency.USD),
            location=LocationProfile(country="US"),
            demographics=DemographicProfile(filing_status=FilingStatus.SINGLE, tax_year=2024),
            deductions=DeductionsProfile(pre_tax_401k="10000"),
        )

        response = await calc_service.calculate(request)

        # The contribution lowers the federal tax basis from 100k to 90k,
        # then is withheld exactly once from take-home pay.
        assert response.taxable_income.annual == Decimal("90000.00")
        assert response.total_tax == Decimal("13000.00")
        assert response.employee_deductions.annual == Decimal("23000.00")
        assert response.net_income.annual == Decimal("77000.00")
