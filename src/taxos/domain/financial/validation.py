"""Data validation models and sanitization utilities."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from taxos.domain.financial.currency import Currency
from taxos.domain.rules import FilingStatus


def sanitize_financial_input(value: Any) -> Any:
    """
    Sanitize incoming financial strings before parsing to Decimal.
    Removes currency symbols, commas, and whitespace.
    E.g. '$1,234.56' -> '1234.56'
    """
    if isinstance(value, str):
        # Remove anything that isn't a digit, minus sign, or period
        cleaned = re.sub(r"[^\d.-]", "", value)
        return cleaned if cleaned else "0"
    return value


# Type alias for a sanitized, strictly positive Decimal
SanitizedDecimal = Annotated[
    Decimal,
    BeforeValidator(sanitize_financial_input),
    Field(ge=Decimal("0.0")),
]

# ISO-3166 Country Code (e.g., US, GB)
CountryCode = Annotated[
    str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=2, max_length=3)
]

# ZIP or Postal Code (allow alphanumeric and dash for international compatibility, e.g., '90210' or 'SW1A 1AA')
PostalCode = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_upper=True,
        pattern=r"^[A-Z0-9\s-]+$",
        min_length=2,
        max_length=12,
    ),
]


class IncomeProfile(BaseModel):
    """
    Validates income inputs and standardizes them.
    Supports either an explicit annual gross_income or computing it from salary/hourly components.
    """

    model_config = ConfigDict(frozen=True)

    currency: Currency = Field(default=Currency.USD)

    # Direct Annual Income
    gross_income: SanitizedDecimal | None = None

    # Or computed components
    salary: SanitizedDecimal | None = None
    hourly_wage: SanitizedDecimal | None = None
    hours_per_week: SanitizedDecimal | None = Field(
        default=Decimal("40.0"), ge=Decimal("0.0"), le=Decimal("168.0")
    )

    # Additional income
    bonus: SanitizedDecimal = Field(default=Decimal("0.0"))
    overtime: SanitizedDecimal = Field(default=Decimal("0.0"))
    commission: SanitizedDecimal = Field(default=Decimal("0.0"))
    contractor_income: SanitizedDecimal = Field(default=Decimal("0.0"))
    freelance_income: SanitizedDecimal = Field(default=Decimal("0.0"))
    rsu_income: SanitizedDecimal = Field(default=Decimal("0.0"))
    stock_option_income: SanitizedDecimal = Field(default=Decimal("0.0"))

    @model_validator(mode="after")
    def compute_gross_income(self) -> IncomeProfile:
        """Ensure a single source of truth for total gross income."""
        # If gross_income is provided, use it directly (plus bonus/overtime if they are provided)
        # If not, compute from salary or hourly_wage
        total = Decimal("0.0")

        if self.gross_income is not None:
            total += self.gross_income
        elif self.salary is not None:
            total += self.salary
        elif self.hourly_wage is not None and self.hours_per_week is not None:
            total += self.hourly_wage * self.hours_per_week * Decimal("52.0")
        else:
            raise ValueError("Must provide either gross_income, salary, or hourly_wage.")

        total += self.bonus
        total += self.overtime
        total += self.commission
        total += self.contractor_income
        total += self.freelance_income
        total += self.rsu_income
        total += self.stock_option_income

        # Pydantic V2 frozen models require returning a new instance or using object.__setattr__ if we want to mutate
        # But we can just validate here that it computes to something > 0
        if total < 0:
            raise ValueError("Total computed income cannot be negative.")

        # We inject the computed total back into gross_income for ease of use down the line
        object.__setattr__(self, "gross_income", total)
        return self


class LocationProfile(BaseModel):
    """Validates jurisdictional location details."""

    model_config = ConfigDict(frozen=True)

    country: CountryCode
    state: (
        Annotated[
            str,
            StringConstraints(strip_whitespace=True, to_upper=True, min_length=2, max_length=3),
        ]
        | None
    ) = None
    city: Annotated[str, StringConstraints(strip_whitespace=True)] | None = None
    zip_code: PostalCode | None = None


class DemographicProfile(BaseModel):
    """Validates personal tax demographic data."""

    model_config = ConfigDict(frozen=True)

    filing_status: FilingStatus
    dependents: int = Field(default=0, ge=0, le=50)
    tax_year: int = Field(default_factory=lambda: date.today().year, ge=1900, le=2100)
    
    age: int = Field(default=30, ge=0, le=120)
    blindness_status: bool = Field(default=False)
    student_loan: bool = Field(default=False)
    military_status: bool = Field(default=False)


class DeductionsProfile(BaseModel):
    """Validates incoming pre-tax deductions and limits."""

    model_config = ConfigDict(frozen=True)

    # General pre-tax
    retirement_contribution: SanitizedDecimal = Field(default=Decimal("0.0"))
    health_insurance: SanitizedDecimal = Field(default=Decimal("0.0"))
    
    # Specific US/Global Retirement
    pre_tax_401k: SanitizedDecimal = Field(default=Decimal("0.0"))
    roth_401k: SanitizedDecimal = Field(default=Decimal("0.0"))
    traditional_ira: SanitizedDecimal = Field(default=Decimal("0.0"))
    roth_ira: SanitizedDecimal = Field(default=Decimal("0.0"))
    pension_contribution: SanitizedDecimal = Field(default=Decimal("0.0"))
    employer_match: SanitizedDecimal = Field(default=Decimal("0.0"))

    # Other deductions
    post_tax_deductions: SanitizedDecimal = Field(default=Decimal("0.0"))
    custom_deductions: dict[str, SanitizedDecimal] = Field(default_factory=dict)
