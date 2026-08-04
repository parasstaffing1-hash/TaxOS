"""Universal Tax Rule Engine domain models."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class JurisdictionLevel(StrEnum):
    """Level of the tax jurisdiction."""

    COUNTRY = "country"
    STATE = "state"
    CITY = "city"
    COUNTY = "county"


class FilingStatus(StrEnum):
    """Standard filing statuses."""

    SINGLE = "single"
    MARRIED_JOINTLY = "married_jointly"
    MARRIED_SEPARATELY = "married_separately"
    HEAD_OF_HOUSEHOLD = "head_of_household"
    WIDOW = "widow"


class TaxBracket(BaseModel):
    """A progressive tax bracket."""

    model_config = ConfigDict(frozen=True)

    min_amount: Decimal = Field(ge=0)
    max_amount: Decimal | None = Field(default=None)
    rate: Decimal = Field(ge=0, le=1)
    fixed_amount: Decimal = Field(default=Decimal("0.0"))


class ProgressiveTaxRule(BaseModel):
    """Progressive tax rule with multiple brackets."""

    model_config = ConfigDict(frozen=True)

    type: Literal["progressive"] = "progressive"
    name: str
    brackets: list[TaxBracket]


class FlatTaxRule(BaseModel):
    """A flat tax rule."""

    model_config = ConfigDict(frozen=True)

    type: Literal["flat"] = "flat"
    name: str
    rate: Decimal = Field(ge=0, le=1)


class DeductionRule(BaseModel):
    """Standard deduction or exemption."""

    model_config = ConfigDict(frozen=True)

    type: Literal["deduction"] = "deduction"
    name: str
    amount: Decimal = Field(ge=0)
    is_percentage: bool = False
    max_limit: Decimal | None = None


class TaxCreditRule(BaseModel):
    """Tax credit (refundable or non-refundable)."""

    model_config = ConfigDict(frozen=True)

    type: Literal["credit"] = "credit"
    name: str
    amount: Decimal = Field(ge=0)
    is_refundable: bool = False
    max_limit: Decimal | None = None


class PayrollTaxRule(BaseModel):
    """Payroll tax rule (e.g., Social Security, Medicare)."""

    model_config = ConfigDict(frozen=True)

    type: Literal["payroll"] = "payroll"
    name: str
    employee_rate: Decimal = Field(ge=0, le=1)
    employer_rate: Decimal = Field(ge=0, le=1)
    wage_base_limit: Decimal | None = None


class VATRule(BaseModel):
    """Value-added tax or sales tax."""

    model_config = ConfigDict(frozen=True)

    type: Literal["vat"] = "vat"
    name: str
    standard_rate: Decimal = Field(ge=0, le=1)
    reduced_rates: dict[str, Decimal] = Field(default_factory=dict)
    exempt_categories: list[str] = Field(default_factory=list)


TaxRule = (
    ProgressiveTaxRule | FlatTaxRule | DeductionRule | TaxCreditRule | PayrollTaxRule | VATRule
)


class TaxRuleSet(BaseModel):
    """A complete set of rules for a specific jurisdiction and year."""

    model_config = ConfigDict(frozen=True)

    jurisdiction: str  # e.g., "US", "CA", "London"
    level: JurisdictionLevel
    tax_year: int
    currency: str = "USD"
    valid_from: date | None = None
    valid_to: date | None = None

    # Specific rules organized by filing status
    # If filing status doesn't matter (e.g., VAT, Payroll), use "all" or specific ones
    rules: dict[FilingStatus | Literal["all"], list[TaxRule]] = Field(default_factory=dict)

    def get_rules_for_status(self, status: FilingStatus) -> list[TaxRule]:
        """Get all rules applicable to a specific filing status."""
        applicable_rules: list[TaxRule] = []
        if "all" in self.rules:
            applicable_rules.extend(self.rules["all"])
        if status in self.rules:
            applicable_rules.extend(self.rules[status])
        return applicable_rules
