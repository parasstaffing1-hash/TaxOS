"""Integration tests linking Validation, Currency, and Calculation engines."""

from __future__ import annotations

from decimal import Decimal

import pytest

from taxos.application.calculations.engine import TaxCalculator
from taxos.application.services.currency import CurrencyEngine
from taxos.domain.financial.currency import Currency
from taxos.domain.financial.validation import IncomeProfile
from taxos.domain.rules import FlatTaxRule
from taxos.infrastructure.currency.mock_provider import MockExchangeRateProvider


@pytest.mark.asyncio
class TestFullValidationFlow:
    """Test standard data flows through the systems."""

    async def test_foreign_income_to_tax_calculation(self) -> None:
        """Test parsing dirty foreign income, converting it to USD, and taxing it."""

        # 1. User inputs a messy string for EUR salary
        profile = IncomeProfile(currency=Currency.EUR, salary="€ 50,000.00", bonus="€ 5,000.50")

        # 2. Validate Profile correctly computed gross income in EUR
        assert profile.gross_income == Decimal("55000.50")

        # 3. Convert to local jurisdiction currency (USD)
        currency_engine = CurrencyEngine(provider=MockExchangeRateProvider())
        usd_gross = await currency_engine.convert(
            amount=profile.gross_income, from_currency=profile.currency, to_currency=Currency.USD
        )
        # EUR to USD via mock is (1 / 0.92) * 1.0 = 1.086956...
        # 55000.50 * 1.086956... = 59783.15 (rounded to 2 places)
        assert usd_gross == Decimal("59783.15")

        # 4. Run tax calculations in USD
        calc = TaxCalculator()
        rule = FlatTaxRule(name="Test Tax", rate=Decimal("0.10"))

        results = calc.calculate(usd_gross, [rule])

        # 59783.15 * 10% = 5978.32 (rounded)
        assert Decimal(results["final_tax"]) == Decimal("5978.32")
        assert Decimal(results["net_income"]) == Decimal("53804.83")
