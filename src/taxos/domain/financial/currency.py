"""Currency definitions."""

from __future__ import annotations

from enum import StrEnum


class Currency(StrEnum):
    """Standard ISO 4217 currency codes supported by the system."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    JPY = "JPY"
    CHF = "CHF"
    INR = "INR"
    # Extensible list
