"""India Salary, CTC, HRA, and Take-Home Salary Calculation Engine."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel

from taxos.domain.financial.trace import (
    TaxRegime,
)
from taxos.domain.india.income_tax import IndiaIncomeTaxEngine
from taxos.domain.india.models import IndiaIncomeTaxInput, SalaryStructureInput


class HRAExemptionResult(BaseModel):
    """Detailed HRA exemption breakdown u/s 10(13A)."""

    actual_hra_received: Decimal
    rent_minus_ten_percent_basic: Decimal
    salary_percentage_limit: Decimal  # 50% metro or 40% non-metro
    exempt_hra_amount: Decimal
    taxable_hra_amount: Decimal
    is_metro: bool
    explanation: str


class SalaryTakeHomeBreakdown(BaseModel):
    """Monthly and annual breakdown of CTC to Take-Home salary."""

    # Annual figures
    annual_ctc: Decimal
    basic_salary: Decimal
    hra: Decimal
    special_allowance: Decimal
    other_allowances: Decimal
    bonus: Decimal

    # Retirals & Employer deductions (Part of CTC but not paid monthly)
    employer_epf: Decimal
    employer_nps: Decimal
    gratuity_provision: Decimal
    gross_salary: Decimal

    # Employee Deductions from Paycheck
    employee_epf: Decimal
    professional_tax: Decimal
    annual_income_tax: Decimal
    total_employee_deductions: Decimal

    # Net In-Hand / Take-Home
    annual_take_home: Decimal
    monthly_take_home: Decimal
    monthly_gross_salary: Decimal

    # Tax regime applied
    applied_regime: TaxRegime
    hra_exemption_amount: Decimal


class IndiaSalaryEngine:
    """Enterprise engine for Indian salary structure optimization, HRA exemption, and take-home pay."""

    def __init__(self, assessment_year: str = "2025-26") -> None:
        self.assessment_year = assessment_year
        self.tax_engine = IndiaIncomeTaxEngine(assessment_year=assessment_year)

    def calculate_hra_exemption(
        self,
        basic_salary: Decimal,
        hra_received: Decimal,
        annual_rent_paid: Decimal,
        is_metro: bool = True,
    ) -> HRAExemptionResult:
        """Calculate HRA exemption under Section 10(13A) read with Rule 2A.

        Exemption is least of:
        1. Actual HRA received
        2. Rent paid in excess of 10% of Basic salary
        3. 50% of Basic (Metro: Delhi, Mumbai, Kolkata, Chennai) or 40% (Non-Metro)
        """
        ten_percent_basic = (basic_salary * Decimal("0.10")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        rent_excess = max(Decimal("0.0"), annual_rent_paid - ten_percent_basic)

        percent_rate = Decimal("0.50") if is_metro else Decimal("0.40")
        percent_limit = (basic_salary * percent_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        exempt_hra = min(hra_received, rent_excess, percent_limit)
        taxable_hra = max(Decimal("0.0"), hra_received - exempt_hra)

        metro_str = "50% of Basic (Metro City)" if is_metro else "40% of Basic (Non-Metro City)"
        explanation = (
            f"HRA Exemption is the minimum of: "
            f"(a) Actual HRA received: ₹{hra_received:,.0f}, "
            f"(b) Rent paid minus 10% Basic: ₹{rent_excess:,.0f}, "
            f"(c) {metro_str}: ₹{percent_limit:,.0f}. "
            f"Exempt HRA: ₹{exempt_hra:,.0f}, Taxable HRA: ₹{taxable_hra:,.0f}."
        )

        return HRAExemptionResult(
            actual_hra_received=hra_received,
            rent_minus_ten_percent_basic=rent_excess,
            salary_percentage_limit=percent_limit,
            exempt_hra_amount=exempt_hra,
            taxable_hra_amount=taxable_hra,
            is_metro=is_metro,
            explanation=explanation,
        )

    def calculate_take_home(
        self,
        salary_input: SalaryStructureInput,
        regime: TaxRegime = TaxRegime.NEW,
    ) -> SalaryTakeHomeBreakdown:
        """Calculate complete monthly and annual in-hand salary with EPF, PT, HRA, and tax deductions."""
        ctc = salary_input.annual_ctc

        # 1. Base components
        basic = (ctc * salary_input.basic_percentage).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        hra = (ctc * salary_input.hra_percentage).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Employer Retirals (Part of CTC)
        # EPF: 12% of Basic salary
        employer_epf = (basic * Decimal("0.12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        # Employer NPS: up to 14% of Basic
        employer_nps = (basic * salary_input.employer_nps_percentage).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        # Gratuity provision: 4.81% of Basic (15 days per year / 26 working days = 15/26 / 12 = 4.81%)
        gratuity = (basic * Decimal("0.0481")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        bonus = salary_input.bonus_annual
        food_allowance = salary_input.food_other_allowances

        # Balance goes into Special Allowance
        retirals_and_direct = (
            basic + hra + employer_epf + employer_nps + gratuity + bonus + food_allowance
        )
        special_allowance = max(Decimal("0.0"), ctc - retirals_and_direct)

        # Gross Salary (CTC less employer retiral provisions)
        gross_salary = basic + hra + special_allowance + food_allowance + bonus

        # 2. HRA Exemption (Only in Old Regime)
        if regime == TaxRegime.OLD and salary_input.actual_rent_paid_annually > 0:
            hra_res = self.calculate_hra_exemption(
                basic_salary=basic,
                hra_received=hra,
                annual_rent_paid=salary_input.actual_rent_paid_annually,
                is_metro=salary_input.is_metro_city,
            )
            hra_exempt = hra_res.exempt_hra_amount
        else:
            hra_exempt = Decimal("0.0")

        # 3. Employee Paycheck Deductions
        employee_epf = employer_epf  # Employee EPF is 12% matching
        prof_tax = salary_input.professional_tax_annual

        # 4. Tax Calculation
        # Taxable salary = Gross Salary - HRA Exemption - LTA Exemption - Professional Tax
        taxable_salary_basis = max(
            Decimal("0.0"),
            gross_salary
            - hra_exempt
            - salary_input.lta_claimed
            - (prof_tax if regime == TaxRegime.OLD else Decimal("0.0")),
        )

        tax_input = IndiaIncomeTaxInput(
            financial_year="2024-25",
            assessment_year=self.assessment_year,
            salary_income=taxable_salary_basis,
            section_80c=employee_epf,  # EPF counts towards 80C
            section_80ccd_2=employer_nps,
        )

        if regime == TaxRegime.NEW:
            tax_res = self.tax_engine.calculate_new_regime(tax_input)
        else:
            tax_res = self.tax_engine.calculate_old_regime(tax_input)

        annual_tax = tax_res.calculation["total_tax_liability"]
        total_employee_deductions = employee_epf + prof_tax + annual_tax

        # Net Take-Home (Gross Salary minus Employee EPF, Professional Tax, and Income Tax)
        annual_take_home = max(Decimal("0.0"), gross_salary - total_employee_deductions)
        monthly_take_home = (annual_take_home / Decimal("12")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        monthly_gross = (gross_salary / Decimal("12")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return SalaryTakeHomeBreakdown(
            annual_ctc=ctc,
            basic_salary=basic,
            hra=hra,
            special_allowance=special_allowance,
            other_allowances=food_allowance,
            bonus=bonus,
            employer_epf=employer_epf,
            employer_nps=employer_nps,
            gratuity_provision=gratuity,
            gross_salary=gross_salary,
            employee_epf=employee_epf,
            professional_tax=prof_tax,
            annual_income_tax=annual_tax,
            total_employee_deductions=total_employee_deductions,
            annual_take_home=annual_take_home,
            monthly_take_home=monthly_take_home,
            monthly_gross_salary=monthly_gross,
            applied_regime=regime,
            hra_exemption_amount=hra_exempt,
        )
