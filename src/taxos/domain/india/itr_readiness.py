"""ITR Form Eligibility Matrix & Pre-Filing Defect Risk Checker.

Evaluates taxpayer profile, income heads, asset disclosures, and compliance flags
to recommend the exact statutory ITR Form (ITR-1 to ITR-6) and identify filing defects.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class ITRForm(StrEnum):
    """Statutory Indian Income Tax Return Forms."""

    ITR_1_SAHAJ = "ITR-1"
    ITR_2 = "ITR-2"
    ITR_3 = "ITR-3"
    ITR_4_SUGAM = "ITR-4"
    ITR_5 = "ITR-5"
    ITR_6 = "ITR-6"
    ITR_7 = "ITR-7"


class TaxpayerProfileInput(BaseModel):
    """Taxpayer profile and filing parameters for ITR selection."""

    is_resident: bool = True
    is_individual_or_huf: bool = True
    is_company: bool = False
    is_partnership_or_llp: bool = False
    is_trust_or_charity: bool = False

    total_gross_income: Decimal = Field(default=Decimal("0.0"), ge=0)
    has_salary_income: bool = True
    house_properties_count: int = 1
    has_capital_gains: bool = False
    has_business_or_professional_income: bool = False
    is_presumptive_business_44ad_44ada: bool = False
    has_foreign_assets_or_foreign_income: bool = False
    is_director_in_company: bool = False
    holds_unlisted_equity_shares: bool = False
    agricultural_income: Decimal = Field(default=Decimal("0.0"), ge=0)
    has_virtual_digital_assets_crypto: bool = False


class ITRReadinessReport(BaseModel):
    """Comprehensive readiness assessment report for ITR filing."""

    recommended_form: ITRForm
    eligible_forms: list[ITRForm]
    is_filing_ready: bool
    blocking_defects: list[str] = Field(default_factory=list)
    compliance_warnings: list[str] = Field(default_factory=list)
    statutory_mandatory_schedules: list[str] = Field(default_factory=list)


class IndiaITRReadinessEngine:
    """Engine for determining ITR Form eligibility and detecting pre-filing statutory defects."""

    def evaluate_readiness(self, profile: TaxpayerProfileInput) -> ITRReadinessReport:
        """Evaluate taxpayer profile and return eligible ITR Form with defect warnings."""
        blocking_defects: list[str] = []
        compliance_warnings: list[str] = []
        schedules: list[str] = []
        eligible: list[ITRForm] = []

        # 1. Company Cases
        if profile.is_company:
            recommended = ITRForm.ITR_6
            eligible = [ITRForm.ITR_6]
            schedules.extend(
                [
                    "Schedule Balance Sheet",
                    "Schedule P&L",
                    "Schedule MAT/115JB",
                    "Schedule TDS/TCS",
                ]
            )
            return ITRReadinessReport(
                recommended_form=recommended,
                eligible_forms=eligible,
                is_filing_ready=True,
                statutory_mandatory_schedules=schedules,
            )

        # 2. Partnership Firm / LLP Cases
        if profile.is_partnership_or_llp:
            recommended = ITRForm.ITR_5
            eligible = [ITRForm.ITR_5]
            schedules.extend(
                [
                    "Schedule Partner Info",
                    "Schedule Balance Sheet",
                    "Schedule P&L",
                    "Schedule TDS/TCS",
                ]
            )
            return ITRReadinessReport(
                recommended_form=recommended,
                eligible_forms=eligible,
                is_filing_ready=True,
                statutory_mandatory_schedules=schedules,
            )

        # 3. Individual / HUF Cases
        # Check ITR-1 Sahaj eligibility:
        # Conditions: Resident, Income <= 50 Lakhs, Only 1 House Property, No Capital Gains, No Business,
        # No Foreign Assets, Not a Director, No Unlisted Shares, Ag Income <= 5000, No Crypto
        can_use_itr1 = (
            profile.is_resident
            and profile.total_gross_income <= Decimal("5000000.0")
            and profile.house_properties_count <= 1
            and not profile.has_capital_gains
            and not profile.has_business_or_professional_income
            and not profile.has_foreign_assets_or_foreign_income
            and not profile.is_director_in_company
            and not profile.holds_unlisted_equity_shares
            and profile.agricultural_income <= Decimal("5000.0")
            and not profile.has_virtual_digital_assets_crypto
        )

        # Check ITR-4 Sugam eligibility (Presumptive u/s 44AD/44ADA/44AE)
        can_use_itr4 = (
            profile.is_resident
            and profile.total_gross_income <= Decimal("5000000.0")
            and profile.is_presumptive_business_44ad_44ada
            and profile.house_properties_count <= 1
            and not profile.has_capital_gains
            and not profile.has_foreign_assets_or_foreign_income
            and not profile.is_director_in_company
            and not profile.holds_unlisted_equity_shares
            and profile.agricultural_income <= Decimal("5000.0")
            and not profile.has_virtual_digital_assets_crypto
        )

        if (
            profile.has_business_or_professional_income
            and not profile.is_presumptive_business_44ad_44ada
        ):
            recommended = ITRForm.ITR_3
            eligible.append(ITRForm.ITR_3)
            schedules.extend(
                [
                    "Schedule BP (Business & Profession)",
                    "Schedule Depreciation",
                    "Schedule Balance Sheet",
                    "Schedule P&L",
                ]
            )
        elif can_use_itr4:
            recommended = ITRForm.ITR_4_SUGAM
            eligible.extend([ITRForm.ITR_4_SUGAM, ITRForm.ITR_3])
            schedules.extend(
                ["Schedule Presumptive Income (44AD/44ADA)", "Schedule Financial Particulars"]
            )
        elif can_use_itr1:
            recommended = ITRForm.ITR_1_SAHAJ
            eligible.extend([ITRForm.ITR_1_SAHAJ, ITRForm.ITR_2])
            schedules.extend(
                [
                    "Schedule Salary",
                    "Schedule House Property",
                    "Schedule Other Sources",
                    "Schedule TDS",
                ]
            )
        else:
            # ITR-2: Individuals with Capital Gains, Foreign Assets, >1 House Property, Income > 50L
            recommended = ITRForm.ITR_2
            eligible.append(ITRForm.ITR_2)
            schedules.extend(
                [
                    "Schedule Salary",
                    "Schedule House Property",
                    "Schedule Capital Gains (CG)",
                    "Schedule Other Sources (OS)",
                ]
            )

        # Defect checks
        if profile.has_foreign_assets_or_foreign_income:
            schedules.append("Schedule FA (Foreign Assets Disclosure)")
            compliance_warnings.append(
                "Mandatory Schedule FA disclosure required; non-disclosure attracts Black Money Act penalties."
            )

        if profile.has_virtual_digital_assets_crypto:
            schedules.append("Schedule VDA (Virtual Digital Assets)")

        if profile.is_director_in_company:
            schedules.append("Schedule Directorship Details (DIN + Company Name + PAN)")

        if profile.agricultural_income > Decimal("5000.0"):
            schedules.append("Schedule EI (Exempt Income)")

        return ITRReadinessReport(
            recommended_form=recommended,
            eligible_forms=eligible,
            is_filing_ready=len(blocking_defects) == 0,
            blocking_defects=blocking_defects,
            compliance_warnings=compliance_warnings,
            statutory_mandatory_schedules=schedules,
        )
