"""Global Jurisdiction Rule Pack & Calculation Models."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from taxos.domain.financial.trace import TaxSlabBreakdown


class GlobalTaxType(StrEnum):
    """Global tax category."""

    INCOME_TAX = "income_tax"
    CORPORATE_TAX = "corporate_tax"
    VAT_GST = "vat_gst"
    PAYROLL_TAX = "payroll_tax"
    WITHHOLDING_TAX = "withholding_tax"


class CountryTaxProfile(BaseModel):
    """Statutory tax profile and rule pack for a specific country."""

    country_code: str  # e.g. "US", "GB", "AE", "CA", "AU", "SG", "DE", etc.
    country_name: str
    currency_code: str  # "USD", "GBP", "AED", "CAD", "AUD", "SGD", "EUR", etc.
    currency_symbol: str

    # Personal Income Tax Slabs
    income_tax_slabs: list[tuple[Decimal, Decimal | None, Decimal]] = Field(default_factory=list)
    personal_allowance_or_standard_deduction: Decimal = Decimal("0.0")

    # Payroll & Social Contributions
    employee_social_security_rate: Decimal = Decimal("0.0")
    employer_social_security_rate: Decimal = Decimal("0.0")
    social_security_cap: Decimal | None = None

    # Corporate Tax
    corporate_tax_standard_rate: Decimal = Decimal("0.0")
    corporate_tax_threshold: Decimal = Decimal("0.0")
    corporate_tax_reduced_rate: Decimal = Decimal("0.0")

    # Indirect Tax (VAT / GST / Sales Tax)
    vat_gst_standard_rate: Decimal = Decimal("0.0")
    vat_gst_reduced_rate: Decimal | None = None
    vat_registration_threshold: Decimal = Decimal("0.0")

    official_tax_authority_name: str
    tax_authority_website: str
    rule_version: str = "2025.1"
    effective_from: str = "2025-01-01"
    effective_to: str | None = None
    supported_tax_types: list[GlobalTaxType] = Field(default_factory=list)
    official_sources: list[str] = Field(default_factory=list)
    known_limitations: list[str] = Field(default_factory=list)


class GlobalCalculationInput(BaseModel):
    """Input payload for global tax calculations."""

    country_code: str
    gross_income_or_revenue: Decimal = Field(ge=0)
    tax_type: GlobalTaxType = GlobalTaxType.INCOME_TAX
    is_married_or_joint: bool = False
    expenses_or_deductions: Decimal = Field(default=Decimal("0.0"), ge=0)
    tax_year: str = "2025"
    taxpayer_type: str = "individual"
    residency: str = "resident"
    entity_type: str = "individual"
    transaction_type: str = "general"


class GlobalCalculationResult(BaseModel):
    """Standardized global calculation result."""

    country_code: str
    country_name: str
    currency_code: str
    currency_symbol: str
    tax_type: GlobalTaxType

    gross_basis: Decimal
    allowances_and_deductions: Decimal
    taxable_basis: Decimal
    calculated_tax: Decimal
    effective_tax_rate_percent: Decimal
    net_after_tax: Decimal

    slabs_breakdown: list[TaxSlabBreakdown] = Field(default_factory=list)
    official_source_reference: str
    notes: list[str] = Field(default_factory=list)
    tax_year: str = "2025"
    rule_version: str = "2025.1"
    taxpayer_type: str = "individual"
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: str = "moderate"
    review_required: bool = False
