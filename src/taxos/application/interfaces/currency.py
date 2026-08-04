"""Currency and Exchange Rate interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from taxos.domain.financial.currency import Currency


class AbstractExchangeRateProvider(ABC):
    """Interface for providing currency exchange rates."""

    @abstractmethod
    async def get_exchange_rate(
        self, from_currency: Currency, to_currency: Currency, for_date: date | None = None
    ) -> Decimal:
        """
        Fetch the exchange rate multiplier to convert from one currency to another.

        Args:
            from_currency: The base currency.
            to_currency: The target currency.
            for_date: The historical date for the rate. If None, uses the latest rate.

        Returns:
            The exchange rate multiplier as a high-precision Decimal.

        Raises:
            NotFoundError: If the exchange rate or currency pair is not available.
            InfrastructureError: If the provider fails to fetch the rate.
        """
        ...
