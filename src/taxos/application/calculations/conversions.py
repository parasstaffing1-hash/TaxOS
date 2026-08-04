"""Income frequency conversions."""

from __future__ import annotations

from decimal import Decimal

from taxos.application.calculations.utils import round_currency

# Standard financial constants
WEEKS_PER_YEAR = Decimal("52")
MONTHS_PER_YEAR = Decimal("12")
WORKING_HOURS_PER_YEAR = Decimal("2080")  # standard 40 hrs * 52 weeks
DAYS_PER_YEAR = Decimal("365")


def annual_to_monthly(annual_amount: Decimal) -> Decimal:
    """Convert annual income to monthly."""
    return round_currency(annual_amount / MONTHS_PER_YEAR)


def annual_to_weekly(annual_amount: Decimal) -> Decimal:
    """Convert annual income to weekly."""
    return round_currency(annual_amount / WEEKS_PER_YEAR)


def annual_to_daily(annual_amount: Decimal) -> Decimal:
    """Convert annual income to daily (assuming 365 days)."""
    return round_currency(annual_amount / DAYS_PER_YEAR)


def annual_to_hourly(
    annual_amount: Decimal, hours_per_year: Decimal = WORKING_HOURS_PER_YEAR
) -> Decimal:
    """Convert annual income to hourly."""
    return round_currency(annual_amount / hours_per_year)


def monthly_to_annual(monthly_amount: Decimal) -> Decimal:
    """Convert monthly income to annual."""
    return round_currency(monthly_amount * MONTHS_PER_YEAR)


def hourly_to_annual(
    hourly_amount: Decimal, hours_per_year: Decimal = WORKING_HOURS_PER_YEAR
) -> Decimal:
    """Convert hourly income to annual."""
    return round_currency(hourly_amount * hours_per_year)
