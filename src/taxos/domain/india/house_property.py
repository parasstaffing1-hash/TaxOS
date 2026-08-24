"""India House Property Income Engine (Sections 22 to 27)."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from taxos.domain.financial.formulas import apply_bankers_rounding
from taxos.domain.financial.trace import (
    ExplanationStep,
    OfficialSourceReference,
    StandardTaxCalculationResponse,
)


class PropertyOccupancyType(StrEnum):
    SELF_OCCUPIED = "self_occupied"
    LET_OUT = "let_out"
    DEEMED_LET_OUT = "deemed_let_out"


class HousePropertyInputs(BaseModel):
    occupancy_type: PropertyOccupancyType = PropertyOccupancyType.SELF_OCCUPIED
    municipal_value: Decimal = Field(default=Decimal("0.0"), ge=0)
    fair_rent: Decimal = Field(default=Decimal("0.0"), ge=0)
    standard_rent: Decimal = Field(default=Decimal("0.0"), ge=0)
    actual_rent_received_annual: Decimal = Field(default=Decimal("0.0"), ge=0)
    unrealized_rent: Decimal = Field(default=Decimal("0.0"), ge=0)
    vacancy_loss: Decimal = Field(default=Decimal("0.0"), ge=0)
    municipal_taxes_paid_by_owner: Decimal = Field(default=Decimal("0.0"), ge=0)
    home_loan_interest_annual: Decimal = Field(default=Decimal("0.0"), ge=0)
    pre_construction_interest_installment: Decimal = Field(default=Decimal("0.0"), ge=0)
    loan_sanctioned_after_1999: bool = True
    construction_completed_within_5_years: bool = True
    is_joint_ownership: bool = False
    ownership_share_percentage: Decimal = Field(default=Decimal("100.0"), ge=0, le=100)


class HousePropertyResult(BaseModel):
    gross_annual_value: Decimal
    municipal_taxes_deducted: Decimal
    net_annual_value: Decimal
    section_24a_standard_deduction: Decimal
    section_24b_interest_deduction: Decimal
    net_income_or_loss_house_property: Decimal
    set_off_limit_current_year: Decimal
    loss_to_carry_forward: Decimal
    notes: list[str]


class IndiaHousePropertyEngine:
    """Computes income/loss from House Property under Sections 22 to 27 of Income-tax Act, 1961."""

    def calculate_property_income(  # noqa: PLR0915
        self, inputs: HousePropertyInputs, tax_year: str = "2024-25"
    ) -> tuple[HousePropertyResult, StandardTaxCalculationResponse]:
        steps: list[ExplanationStep] = []
        warnings: list[str] = []
        step_num = 1

        if inputs.occupancy_type == PropertyOccupancyType.SELF_OCCUPIED:
            # Self-occupied property has GAV = 0, Municipal taxes = 0, NAV = 0, Standard Ded = 0
            gav = Decimal("0.00")
            muni_tax = Decimal("0.00")
            nav = Decimal("0.00")
            std_ded_24a = Decimal("0.00")

            steps.append(
                ExplanationStep(
                    step_number=step_num,
                    label="Gross Annual Value (GAV) & NAV for Self-Occupied Property",
                    formula_or_rule="GAV = 0, NAV = 0 under Section 23(2)",
                    inputs={"occupancy": "self_occupied"},
                    applied_rate_or_limit=Decimal("0.00"),
                    result=Decimal("0.00"),
                    notes="Annual value of up to 2 self-occupied houses is taken as Nil.",
                )
            )
            step_num += 1

            # Interest deduction cap under Section 24(b)
            total_interest = (
                inputs.home_loan_interest_annual + inputs.pre_construction_interest_installment
            )
            max_limit = (
                Decimal("200000.00")
                if (
                    inputs.loan_sanctioned_after_1999
                    and inputs.construction_completed_within_5_years
                )
                else Decimal("30000.00")
            )

            # Share of interest for joint owners
            share_factor = inputs.ownership_share_percentage / Decimal("100.0")
            user_interest = total_interest * share_factor
            int_ded_24b = min(user_interest, max_limit)

            steps.append(
                ExplanationStep(
                    step_number=step_num,
                    label="Section 24(b) Home Loan Interest Deduction (Self-Occupied)",
                    formula_or_rule="min(Actual Interest Paid * Share %, ₹2,00,000)",
                    inputs={
                        "total_interest": str(total_interest),
                        "share_pct": str(inputs.ownership_share_percentage),
                    },
                    applied_rate_or_limit=max_limit,
                    result=apply_bankers_rounding(int_ded_24b),
                    notes="Deduction capped at ₹2,00,000 for acquisition/construction.",
                )
            )
            step_num += 1

            net_income = -int_ded_24b
            set_off_limit = int_ded_24b
            loss_cf = Decimal("0.00")

        else:
            # Let-Out or Deemed Let-Out Property
            # 1. Expected Rent = Higher of Municipal Value & Fair Rent, subject to Standard Rent
            higher_mf = max(inputs.municipal_value, inputs.fair_rent)
            expected_rent = (
                min(higher_mf, inputs.standard_rent) if inputs.standard_rent > 0 else higher_mf
            )

            # 2. Actual rent received/receivable less unrealized rent
            effective_rent = max(
                Decimal("0.00"), inputs.actual_rent_received_annual - inputs.unrealized_rent
            )

            # 3. GAV is higher of Expected Rent and Actual Rent (adjusted for vacancy)
            if effective_rent > expected_rent:
                gav = effective_rent - inputs.vacancy_loss
            else:
                gav = max(Decimal("0.00"), expected_rent - inputs.vacancy_loss)

            steps.append(
                ExplanationStep(
                    step_number=step_num,
                    label="Gross Annual Value (GAV) Computation",
                    formula_or_rule="max(Expected Rent, Actual Rent) - Vacancy Loss",
                    inputs={
                        "expected_rent": str(expected_rent),
                        "actual_rent": str(effective_rent),
                        "vacancy_loss": str(inputs.vacancy_loss),
                    },
                    applied_rate_or_limit=None,
                    result=apply_bankers_rounding(gav),
                    notes="Section 23(1) of Income-tax Act, 1961.",
                )
            )
            step_num += 1

            # Municipal taxes paid by owner only
            muni_tax = inputs.municipal_taxes_paid_by_owner
            nav = max(Decimal("0.00"), gav - muni_tax)

            steps.append(
                ExplanationStep(
                    step_number=step_num,
                    label="Net Annual Value (NAV) Computation",
                    formula_or_rule="GAV - Municipal Taxes Paid by Owner",
                    inputs={"gav": str(gav), "muni_tax": str(muni_tax)},
                    applied_rate_or_limit=None,
                    result=apply_bankers_rounding(nav),
                    notes="Taxes paid by tenant are not deductible.",
                )
            )
            step_num += 1

            # Standard Deduction u/s 24(a) = 30% of NAV
            std_ded_24a = nav * Decimal("0.30")
            steps.append(
                ExplanationStep(
                    step_number=step_num,
                    label="Section 24(a) Statutory Standard Deduction",
                    formula_or_rule="30% of NAV",
                    inputs={"nav": str(nav)},
                    applied_rate_or_limit=Decimal("0.30"),
                    result=apply_bankers_rounding(std_ded_24a),
                    notes="Flat 30% statutory deduction irrespective of actual maintenance expenditure.",
                )
            )
            step_num += 1

            # Section 24(b) full interest is deductible for let-out property
            total_interest = (
                inputs.home_loan_interest_annual + inputs.pre_construction_interest_installment
            )
            share_factor = inputs.ownership_share_percentage / Decimal("100.0")
            int_ded_24b = total_interest * share_factor

            steps.append(
                ExplanationStep(
                    step_number=step_num,
                    label="Section 24(b) Home Loan Interest (Let-Out)",
                    formula_or_rule="Full interest without statutory ceiling * Share %",
                    inputs={
                        "total_interest": str(total_interest),
                        "share_pct": str(inputs.ownership_share_percentage),
                    },
                    applied_rate_or_limit=None,
                    result=apply_bankers_rounding(int_ded_24b),
                    notes="Entire interest is deductible against let-out house property income.",
                )
            )
            step_num += 1

            raw_income = nav - std_ded_24a - int_ded_24b
            net_income = raw_income * (inputs.ownership_share_percentage / Decimal("100.0"))

            # Set-off cap under Section 71(3A) = ₹2,00,000 per financial year
            if net_income < Decimal("0.00"):
                loss_amount = abs(net_income)
                set_off_limit = min(loss_amount, Decimal("200000.00"))
                loss_cf = max(Decimal("0.00"), loss_amount - Decimal("200000.00"))
                if loss_cf > 0:
                    warnings.append(
                        f"House property loss exceeds current-year inter-head set-off limit of ₹2,00,000. ₹{loss_cf} can be carried forward for 8 AYs."
                    )
            else:
                set_off_limit = Decimal("0.00")
                loss_cf = Decimal("0.00")

        res = HousePropertyResult(
            gross_annual_value=apply_bankers_rounding(gav),
            municipal_taxes_deducted=apply_bankers_rounding(muni_tax),
            net_annual_value=apply_bankers_rounding(nav),
            section_24a_standard_deduction=apply_bankers_rounding(std_ded_24a),
            section_24b_interest_deduction=apply_bankers_rounding(int_ded_24b),
            net_income_or_loss_house_property=apply_bankers_rounding(net_income),
            set_off_limit_current_year=apply_bankers_rounding(set_off_limit),
            loss_to_carry_forward=apply_bankers_rounding(loss_cf),
            notes=warnings,
        )

        trace_response = StandardTaxCalculationResponse(
            jurisdiction="IN",
            tax_type="house_property_income",
            tax_year=tax_year,
            assessment_year=f"{int(tax_year[:4]) + 1}-{str(int(tax_year[:4]) + 2)[2:]}",
            effective_date=f"{tax_year[:4]}-04-01",
            rule_version=f"IN-HP-{tax_year}.1",
            taxpayer_type="individual",
            regime="old",
            inputs=inputs.model_dump(),
            calculation={
                "gross_annual_value": str(res.gross_annual_value),
                "net_annual_value": str(res.net_annual_value),
                "standard_deduction_24a": str(res.section_24a_standard_deduction),
                "interest_deduction_24b": str(res.section_24b_interest_deduction),
                "net_income_or_loss": str(res.net_income_or_loss_house_property),
                "loss_carried_forward": str(res.loss_to_carry_forward),
            },
            steps=steps,
            warnings=warnings,
            assumptions=[
                "Under the New Tax Regime (Section 115BAC), interest on self-occupied property cannot be set off against any head of income."
            ],
            official_sources=[
                OfficialSourceReference(
                    source_id="IN-ACT-HP",
                    title="Income from House Property",
                    section_or_rule="Sections 22 to 27, Section 71(3A)",
                    act_name="Income-tax Act, 1961",
                    url="https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx",
                    effective_date=f"{tax_year[:4]}-04-01",
                )
            ],
        )

        return res, trace_response
