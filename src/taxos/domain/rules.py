"""Universal Tax Rule Engine domain models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JurisdictionLevel(StrEnum):
    """Level of the tax jurisdiction."""

    COUNTRY = "country"
    STATE = "state"
    CITY = "city"
    COUNTY = "county"


class RuleReleaseStatus(StrEnum):
    """Readiness of a rule set for public calculations."""

    VERIFIED = "verified"
    EXPERIMENTAL = "experimental"


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
    max_amount: Decimal | None = Field(default=None, gt=0)
    rate: Decimal = Field(ge=0, le=1)
    fixed_amount: Decimal = Field(default=Decimal("0.0"), ge=0)

    @model_validator(mode="after")
    def validate_range(self) -> TaxBracket:
        """Ensure a bracket has a valid, non-empty interval."""
        if self.max_amount is not None and self.max_amount <= self.min_amount:
            raise ValueError("max_amount must be greater than min_amount")
        return self


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
    """A deduction from taxable income, optionally withheld from take-home pay."""

    model_config = ConfigDict(frozen=True)

    type: Literal["deduction"] = "deduction"
    name: str
    amount: Decimal = Field(ge=0)
    is_percentage: bool = False
    max_limit: Decimal | None = Field(default=None, ge=0)
    reduces_take_home: bool = False

    @model_validator(mode="after")
    def validate_percentage_limit(self) -> DeductionRule:
        """Prevent percentage deductions from carrying an invalid cap."""
        if self.is_percentage and self.amount > 1:
            raise ValueError("percentage deduction amount must be between 0 and 1")
        return self


class TaxCreditRule(BaseModel):
    """Tax credit (refundable or non-refundable)."""

    model_config = ConfigDict(frozen=True)

    type: Literal["credit"] = "credit"
    name: str
    amount: Decimal = Field(ge=0)
    is_refundable: bool = False
    max_limit: Decimal | None = Field(default=None, ge=0)


class PayrollTaxRule(BaseModel):
    """Payroll tax rule (e.g., Social Security, Medicare)."""

    model_config = ConfigDict(frozen=True)

    type: Literal["payroll"] = "payroll"
    name: str
    employee_rate: Decimal = Field(ge=0, le=1)
    employer_rate: Decimal = Field(ge=0, le=1)
    wage_base_limit: Decimal | None = Field(default=None, ge=0)


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


@dataclass(frozen=True)
class ScopedTaxRule:
    """A tax rule together with the jurisdiction that supplied it.

    Rule files deliberately describe only tax behaviour.  The application layer
    adds this wrapper when it merges country, state, and city rule sets so the
    calculation engine can keep each jurisdiction's taxable-income basis
    independent.
    """

    rule: TaxRule
    jurisdiction: str
    level: JurisdictionLevel

    @property
    def name(self) -> str:
        """Expose the underlying rule name for read-only callers."""
        return self.rule.name


ApplicableTaxRule = TaxRule | ScopedTaxRule


def unwrap_tax_rule(rule: ApplicableTaxRule) -> TaxRule:
    """Return the underlying rule from a potentially scoped rule."""
    if isinstance(rule, ScopedTaxRule):
        return rule.rule
    return rule


class TaxRuleSet(BaseModel):
    """A complete set of rules for a specific jurisdiction and year."""

    model_config = ConfigDict(frozen=True)

    jurisdiction: str  # e.g., "US", "CA", "London"
    level: JurisdictionLevel
    tax_year: int = Field(ge=1900, le=2100)
    currency: str = "USD"
    release_status: RuleReleaseStatus = RuleReleaseStatus.VERIFIED
    valid_from: date | None = None
    valid_to: date | None = None

    # Specific rules organized by filing status
    # If filing status doesn't matter (e.g., VAT, Payroll), use "all" or specific ones
    rules: dict[FilingStatus | Literal["all"], list[TaxRule]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_effective_dates(self) -> TaxRuleSet:
        """Reject an impossible effective-date window."""
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValueError("valid_from must not be after valid_to")
        return self

    def get_rules_for_status(self, status: FilingStatus) -> list[TaxRule]:
        """Get all rules applicable to a specific filing status."""
        applicable_rules: list[TaxRule] = []
        if "all" in self.rules:
            applicable_rules.extend(self.rules["all"])
        if status in self.rules:
            applicable_rules.extend(self.rules[status])
        return applicable_rules
