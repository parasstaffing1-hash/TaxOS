"""Utility functions and rounding rules for tax calculations."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def round_currency(value: Decimal, places: int = 2, rounding: str = ROUND_HALF_UP) -> Decimal:
    """
    Round a decimal value to a specific number of places using standard financial rules.

    Args:
        value: The decimal value to round.
        places: Number of decimal places (default 2 for currency).
        rounding: The rounding mode (default ROUND_HALF_UP).

    Returns:
        The rounded Decimal.
    """
    exp = Decimal("10") ** -places
    return value.quantize(exp, rounding=rounding)
