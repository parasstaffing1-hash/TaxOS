"""Calculator API schemas."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, model_validator

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
    currency: Currency | None = Field(default=None)


class TaxBreakdownItem(BaseModel):
    """Single item in the tax breakdown."""

    rule: str
    name: str | None = None
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
    taxable_income_by_jurisdiction: dict[str, PeriodAmounts] = Field(default_factory=dict)
    total_tax_before_credits: PeriodAmounts
    total_credits: PeriodAmounts
    final_tax: PeriodAmounts
    net_income: PeriodAmounts
    employer_cost: PeriodAmounts
    employee_deductions: PeriodAmounts
    total_deductions: PeriodAmounts | None = None
    total_tax: Decimal | None = None

    # Rates
    effective_tax_rate: Decimal
    marginal_tax_rate: Decimal | None = None

    # Granular details
    breakdown: list[TaxBreakdownItem]

    currency: Currency = Field(default=Currency.USD)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_payload(cls, value: object) -> object:
        """Accept the original scalar response shape during migration."""
        if not isinstance(value, dict):
            return value

        payload = dict(value)
        gross = payload.get("gross_income")
        if isinstance(gross, PeriodAmounts):
            gross_periods = gross
        elif isinstance(gross, dict) and "annual" in gross:
            gross_periods = PeriodAmounts.model_validate(gross)
            payload["gross_income"] = gross_periods
        elif gross is not None:
            amount = Decimal(str(gross))
            gross_periods = cls._periods(amount)
            payload["gross_income"] = gross_periods
        else:
            gross_periods = None

        def as_period(key: str, fallback: PeriodAmounts | None = None) -> None:
            current = payload.get(key)
            if isinstance(current, PeriodAmounts):
                return
            if isinstance(current, dict) and "annual" in current:
                payload[key] = PeriodAmounts.model_validate(current)
                return
            if current is not None:
                payload[key] = cls._periods(Decimal(str(current)))
            elif fallback is not None:
                payload[key] = fallback

        total_tax = payload.get("total_tax")
        total_tax_periods = (
            cls._periods(Decimal(str(total_tax))) if total_tax is not None else None
        )
        as_period("taxable_income", gross_periods)
        as_period("total_tax_before_credits", total_tax_periods or gross_periods)
        as_period("total_credits", cls._periods(Decimal("0")))
        as_period("final_tax", total_tax_periods or cls._periods(Decimal("0")))
        as_period("employer_cost", cls._periods(Decimal("0")))
        as_period("employee_deductions", total_tax_periods or cls._periods(Decimal("0")))
        as_period("total_deductions", cls._periods(Decimal("0")))
        return payload

    @staticmethod
    def _periods(amount: Decimal) -> PeriodAmounts:
        """Build a period breakdown for a legacy annual scalar."""
        return PeriodAmounts(
            annual=amount,
            monthly=(amount / 12).quantize(Decimal("0.01")),
            biweekly=(amount / 26).quantize(Decimal("0.01")),
            weekly=(amount / 52).quantize(Decimal("0.01")),
            daily=(amount / 365).quantize(Decimal("0.01")),
            hourly=(amount / 2080).quantize(Decimal("0.01")),
        )

    @model_validator(mode="after")
    def populate_compatibility_fields(self) -> CalculationResponse:
        """Expose stable aliases while retaining the structured response."""
        if self.total_tax is None:
            self.total_tax = self.final_tax.annual
        if self.total_deductions is None:
            self.total_deductions = self.employee_deductions
        for item in self.breakdown:
            if item.name is None:
                item.name = item.rule
        return self

    @property
    def federal_tax(self) -> Decimal:
        """Return the tax total for federal/national rules."""
        return sum(
            (item.tax for item in self.breakdown if "federal" in item.rule.lower()),
            Decimal("0"),
        )

    @property
    def state_tax(self) -> Decimal:
        """Return the tax total for state/provincial rules."""
        return sum(
            (
                item.tax
                for item in self.breakdown
                if any(token in item.rule.lower() for token in ("state", "provincial"))
            ),
            Decimal("0"),
        )
