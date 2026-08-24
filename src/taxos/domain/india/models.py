"""Domain input/output models for India Tax Engines."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from taxos.domain.financial.trace import TaxRegime


class TaxpayerAgeCategory(StrEnum):
    """Age category for Indian individual taxpayers."""

    BELOW_60 = "below_60"  # Regular individual (<60 yrs)
    SENIOR_CITIZEN = "senior_60_to_80"  # Senior citizen (60 to 80 yrs)
    SUPER_SENIOR_CITIZEN = "super_senior_above_80"  # Super senior citizen (80+ yrs)


class ResidencyStatus(StrEnum):
    """Residency status under Income-tax Act."""

    RESIDENT = "resident"
    NON_RESIDENT = "non_resident"
    RNOR = "rnor"  # Resident but Not Ordinarily Resident


class IndiaIncomeTaxInput(BaseModel):
    """Input payload for India personal income tax calculation."""

    financial_year: str = Field(
        default="2024-25", description="FY e.g. '2024-25', '2025-26', '2026-27'"
    )
    assessment_year: str = Field(default="2025-26", description="AY e.g. '2025-26', '2026-27'")
    age_category: TaxpayerAgeCategory = TaxpayerAgeCategory.BELOW_60
    residency: ResidencyStatus = ResidencyStatus.RESIDENT

    # Heads of Income (All Decimals)
    salary_income: Decimal = Field(
        default=Decimal("0.0"), ge=0, description="Gross salary before standard deduction"
    )
    house_property_income: Decimal = Field(
        default=Decimal("0.0"),
        description="Net annual value less deductions or home loan interest (can be negative)",
    )
    capital_gains_stcg_111a: Decimal = Field(
        default=Decimal("0.0"), ge=0, description="STCG on listed equity (15% / 20%)"
    )
    capital_gains_stcg_other: Decimal = Field(
        default=Decimal("0.0"), ge=0, description="STCG at normal slab rates"
    )
    capital_gains_ltcg_112a: Decimal = Field(
        default=Decimal("0.0"),
        ge=0,
        description="LTCG on listed equity (10% / 12.5% above threshold)",
    )
    capital_gains_ltcg_other: Decimal = Field(
        default=Decimal("0.0"),
        ge=0,
        description="LTCG on property/unlisted/gold (20% with indexation / 12.5%)",
    )
    business_profession_income: Decimal = Field(
        default=Decimal("0.0"), ge=0, description="Net business or professional profit"
    )
    other_sources_income: Decimal = Field(
        default=Decimal("0.0"), ge=0, description="Interest, dividend, lottery, and other income"
    )

    # Chapter VI-A Deductions (Applicable in Old Regime)
    section_80c: Decimal = Field(
        default=Decimal("0.0"),
        ge=0,
        description="EPF, PPF, ELSS, Life Insurance, Principal on Home Loan (capped at ₹1.5L)",
    )
    section_80ccd_1b: Decimal = Field(
        default=Decimal("0.0"), ge=0, description="Additional NPS contribution (capped at ₹50,000)"
    )
    section_80ccd_2: Decimal = Field(
        default=Decimal("0.0"),
        ge=0,
        description="Employer NPS contribution (Allowed in BOTH Old and New Regimes!)",
    )
    section_80d_self: Decimal = Field(
        default=Decimal("0.0"),
        ge=0,
        description="Medical insurance for self/family (₹25k or ₹50k if senior)",
    )
    section_80d_parents: Decimal = Field(
        default=Decimal("0.0"),
        ge=0,
        description="Medical insurance for parents (₹25k or ₹50k if senior)",
    )
    section_80e: Decimal = Field(
        default=Decimal("0.0"),
        ge=0,
        description="Interest on higher education loan (no cap for 8 years)",
    )
    section_80g: Decimal = Field(
        default=Decimal("0.0"), ge=0, description="Eligible charitable donations"
    )
    section_80tta_ttb: Decimal = Field(
        default=Decimal("0.0"),
        ge=0,
        description="Savings account interest (80TTA ₹10k) or senior deposit interest (80TTB ₹50k)",
    )
    other_chapter_via_deductions: Decimal = Field(
        default=Decimal("0.0"), ge=0, description="80DD, 80DDB, 80U, 80GG, etc."
    )

    # Taxes already paid / credits
    tds_tcs_paid: Decimal = Field(
        default=Decimal("0.0"), ge=0, description="TDS and TCS credits from Form 26AS / AIS"
    )
    advance_tax_paid: Decimal = Field(
        default=Decimal("0.0"), ge=0, description="Advance tax already deposited"
    )


class SalaryStructureInput(BaseModel):
    """Input payload for Indian salary & CTC structure analysis."""

    annual_ctc: Decimal = Field(ge=0, description="Total annual Cost to Company (CTC)")
    basic_percentage: Decimal = Field(
        default=Decimal("0.40"),
        ge=0.1,
        le=0.8,
        description="Basic salary as fraction of CTC (e.g. 0.40 for 40%)",
    )
    hra_percentage: Decimal = Field(
        default=Decimal("0.20"), ge=0, le=0.5, description="HRA as fraction of CTC"
    )
    is_metro_city: bool = Field(
        default=True,
        description="Metro city (Delhi, Mumbai, Kolkata, Chennai - 50%) vs Non-Metro (40%)",
    )
    actual_rent_paid_annually: Decimal = Field(
        default=Decimal("0.0"), ge=0, description="Actual rent paid per year"
    )
    lta_claimed: Decimal = Field(
        default=Decimal("0.0"), ge=0, description="Leave Travel Allowance exemption claimed"
    )
    employer_nps_percentage: Decimal = Field(
        default=Decimal("0.0"),
        ge=0,
        le=0.14,
        description="Employer NPS contribution fraction of Basic+DA (up to 14%)",
    )
    professional_tax_annual: Decimal = Field(
        default=Decimal("2400.0"),
        ge=0,
        description="Annual state professional tax (usually ₹2,400)",
    )
    bonus_annual: Decimal = Field(
        default=Decimal("0.0"), ge=0, description="Annual performance bonus"
    )
    food_other_allowances: Decimal = Field(
        default=Decimal("0.0"), ge=0, description="Food coupons, books, uniform allowances"
    )


class RegimeComparisonResult(BaseModel):
    """Detailed side-by-side comparison between Old and New Tax Regimes."""

    financial_year: str
    assessment_year: str
    gross_total_income: Decimal

    # Old Regime Values
    old_regime_deductions: Decimal
    old_regime_taxable_income: Decimal
    old_regime_base_tax: Decimal
    old_regime_rebate_87a: Decimal
    old_regime_surcharge: Decimal
    old_regime_cess: Decimal
    old_regime_total_tax: Decimal

    # New Regime Values
    new_regime_deductions: Decimal
    new_regime_taxable_income: Decimal
    new_regime_base_tax: Decimal
    new_regime_rebate_87a: Decimal
    new_regime_surcharge: Decimal
    new_regime_cess: Decimal
    new_regime_total_tax: Decimal

    # Decision Recommendation
    recommended_regime: TaxRegime
    tax_savings: Decimal
    break_even_deductions_needed: Decimal
    summary_explanation: str
