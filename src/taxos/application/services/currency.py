"""Currency Engine Service."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from taxos.application.calculations.utils import round_currency
from taxos.application.interfaces.currency import AbstractExchangeRateProvider
from taxos.domain.financial.currency import Currency


class CurrencyEngine:
    """Service to handle monetary conversions between currencies."""

    def __init__(self, provider: AbstractExchangeRateProvider) -> None:
        self.provider = provider

    async def convert(
        self,
        amount: Decimal,
        from_currency: Currency,
        to_currency: Currency,
        for_date: date | None = None,
    ) -> Decimal:
        """
        Convert an amount from one currency to another using high-precision math.

        Args:
            amount: The monetary amount.
            from_currency: Base currency.
            to_currency: Target currency.
            for_date: Historical date for the exchange rate.

        Returns:
            The converted amount, rounded to standard 2 decimal places.
        """
        if from_currency == to_currency:
            return round_currency(amount)

        rate = await self.provider.get_exchange_rate(from_currency, to_currency, for_date)
        converted_amount = amount * rate

        return round_currency(converted_amount)
