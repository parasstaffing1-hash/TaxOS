"""Unit tests for the Tax Analytics Platform."""

from decimal import Decimal

import pytest

from taxos.api.schemas.analytics import IncomeDistributionRequest, LocationComparisonRequest
from taxos.api.schemas.calculator import CalculatorRequest
from taxos.application.services.analytics import TaxAnalyticsService
from taxos.domain.financial.validation import DemographicProfile, IncomeProfile, LocationProfile


# Mock Salary Service
class MockSalaryService:
    async def calculate(self, request: CalculatorRequest):
        from taxos.api.schemas.calculator import CalculationResponse, PeriodAmounts

        # Just return a dummy response
        val = request.income.gross_income or Decimal("0")
        tax = val * Decimal("0.2")
        net = val - tax

        return CalculationResponse(
            gross_income=PeriodAmounts(
                annual=val,
                monthly=val / 12,
                biweekly=val / 26,
                weekly=val / 52,
                daily=val / 365,
                hourly=val / 2080,
            ),
            net_income=PeriodAmounts(
                annual=net,
                monthly=net / 12,
                biweekly=net / 26,
                weekly=net / 52,
                daily=net / 365,
                hourly=net / 2080,
            ),
            total_tax=tax,
            total_deductions=Decimal("0"),
            federal_tax=tax,
            state_tax=Decimal("0"),
            local_tax=Decimal("0"),
            payroll_tax=Decimal("0"),
            social_security=Decimal("0"),
            medicare=Decimal("0"),
            pension_deductions=Decimal("0"),
            effective_tax_rate=Decimal("20.0"),
            marginal_tax_rate=Decimal("20.0"),
            employer_cost=Decimal("0"),
            employee_deductions=tax,
            breakdown=[],
            currency="USD",
        )


@pytest.mark.asyncio
async def test_compare_locations() -> None:
    service = TaxAnalyticsService(MockSalaryService())  # type: ignore

    req = LocationComparisonRequest(
        base_request=CalculatorRequest(
            location=LocationProfile(country="US"),
            demographics=DemographicProfile(tax_year=2026, filing_status="single"),
            income=IncomeProfile(gross_income=Decimal("100000")),
            currency="USD",
        ),
        locations=[
            LocationProfile(country="US", state="CA"),
            LocationProfile(country="US", state="TX"),
        ],
    )

    res = await service.compare_locations(req)
    assert len(res.results) == 2
    assert "CA_US" in res.results
    assert "TX_US" in res.results

    # Assert cache works
    assert len(service._cache._cache) == 1


@pytest.mark.asyncio
async def test_income_distribution() -> None:
    service = TaxAnalyticsService(MockSalaryService())  # type: ignore

    req = IncomeDistributionRequest(
        base_request=CalculatorRequest(
            location=LocationProfile(country="US"),
            demographics=DemographicProfile(tax_year=2026, filing_status="single"),
            income=IncomeProfile(gross_income=Decimal("0")),
            currency="USD",
        ),
        start_income=50000,
        end_income=150000,
        step=50000,
    )

    res = await service.analyze_income_distribution(req)
    assert len(res.results) == 3  # 50k, 100k, 150k

    assert 50000.0 in res.results
    assert res.results[50000.0].total_tax == Decimal("10000.0")
