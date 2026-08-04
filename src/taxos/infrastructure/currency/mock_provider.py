"""Mock exchange rate provider for testing and development."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import ClassVar

from taxos.application.interfaces.currency import AbstractExchangeRateProvider
from taxos.core.exceptions import NotFoundError
from taxos.domain.financial.currency import Currency


class MockExchangeRateProvider(AbstractExchangeRateProvider):
    """Static mock provider returning hardcoded exchange rates based against USD."""

    # Base rates relative to 1 USD
    _USD_RATES: ClassVar[dict[Currency, Decimal]] = {
        Currency.USD: Decimal("1.0"),
        Currency.EUR: Decimal("0.92"),
        Currency.GBP: Decimal("0.79"),
        Currency.CAD: Decimal("1.35"),
        Currency.AUD: Decimal("1.52"),
        Currency.JPY: Decimal("150.20"),
        Currency.CHF: Decimal("0.88"),
        Currency.INR: Decimal("83.10"),
    }

    async def get_exchange_rate(
        self, from_currency: Currency, to_currency: Currency, for_date: date | None = None
    ) -> Decimal:
        """Calculate cross-rate using USD as the base."""
        del for_date  # Static development rates intentionally have no historical dimension.
        if from_currency not in self._USD_RATES:
            val = getattr(from_currency, "value", str(from_currency))
            raise NotFoundError(f"No exchange rate found for {val}")
        if to_currency not in self._USD_RATES:
            val = getattr(to_currency, "value", str(to_currency))
            raise NotFoundError(f"No exchange rate found for {val}")

        from_usd = self._USD_RATES[from_currency]
        to_usd = self._USD_RATES[to_currency]
        return to_usd / from_usd
