"""Calculator API schemas."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from taxos.domain.financial.currency import Currency
from taxos.domain.financial.validation import (
    DeductionsProfile,
    DemographicProfile,
    IncomeProfile,
    LocationProfile,
)


class CalculatorRequest(BaseModel):
    """Complete payload for the after-tax calculator."""

    income: IncomeProfile
    location: LocationProfile
    demographics: DemographicProfile
    deductions: DeductionsProfile = Field(default_factory=DeductionsProfile)
    currency: Currency = Field(default=Currency.USD)


class TaxBreakdownItem(BaseModel):
    """Single item in the tax breakdown."""

    rule: str
    tax: Decimal
    deduction: Decimal
    credit: Decimal
    employer_cost: Decimal
    details: dict[str, Any] = Field(default_factory=dict)


class PeriodAmounts(BaseModel):
    """Amounts broken down by time period."""

    annual: Decimal
    monthly: Decimal
    biweekly: Decimal
    weekly: Decimal
    daily: Decimal
    hourly: Decimal


class CalculationResponse(BaseModel):
    """Complete tax calculation response."""

    gross_income: PeriodAmounts
    taxable_income: PeriodAmounts
    total_tax_before_credits: PeriodAmounts
    total_credits: PeriodAmounts
    final_tax: PeriodAmounts
    net_income: PeriodAmounts
    employer_cost: PeriodAmounts
    employee_deductions: PeriodAmounts

    # Rates
    effective_tax_rate: Decimal
    marginal_tax_rate: Decimal | None = None

    # Granular details
    breakdown: list[TaxBreakdownItem]

    currency: Currency = Field(default=Currency.USD)
