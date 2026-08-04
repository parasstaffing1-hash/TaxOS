"""Unit tests for the Currency Engine."""

from __future__ import annotations

from decimal import Decimal

import pytest

from taxos.application.services.currency import CurrencyEngine
from taxos.core.exceptions import NotFoundError
from taxos.domain.financial.currency import Currency
from taxos.infrastructure.currency.mock_provider import MockExchangeRateProvider


@pytest.fixture
def currency_engine() -> CurrencyEngine:
    return CurrencyEngine(provider=MockExchangeRateProvider())


@pytest.mark.asyncio
class TestCurrencyEngine:
    """Tests for multi-currency conversion."""

    async def test_same_currency(self, currency_engine: CurrencyEngine) -> None:
        """Testing converting USD to USD returns same amount."""
        res = await currency_engine.convert(Decimal("100"), Currency.USD, Currency.USD)
        assert res == Decimal("100.00")

    async def test_usd_to_eur(self, currency_engine: CurrencyEngine) -> None:
        """Test converting USD to EUR."""
        # Rate is 0.92
        res = await currency_engine.convert(Decimal("100"), Currency.USD, Currency.EUR)
        assert res == Decimal("92.00")

    async def test_cross_rate_gbp_to_cad(self, currency_engine: CurrencyEngine) -> None:
        """Test a cross conversion that routes through USD."""
        # GBP to USD = 1 / 0.79 = 1.2658
        # USD to CAD = 1.35
        # Cross rate = 1.2658 * 1.35 = 1.7088
        # 100 GBP = 170.89 CAD
        res = await currency_engine.convert(Decimal("100"), Currency.GBP, Currency.CAD)
        assert res == Decimal("170.89")

    async def test_unsupported_currency(self, currency_engine: CurrencyEngine) -> None:
        """Test that unknown currencies raise an error."""
        # Force an unsupported string that bypassing typing
        with pytest.raises(NotFoundError):
            await currency_engine.convert(Decimal("100"), Currency.USD, "XYZ")  # type: ignore
