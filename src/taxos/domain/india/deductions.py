"""India Chapter VI-A Deductions Engine (Sections 80C to 80U)."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from taxos.domain.financial.formulas import apply_bankers_rounding
from taxos.domain.financial.trace import (
    ExplanationStep,
    OfficialSourceReference,
    StandardTaxCalculationResponse,
)


class ChapterVIAInputs(BaseModel):
    # 80C, 80CCC, 80CCD(1)
    sec_80c_epf_ppf_elss_lic_tuition: Decimal = Field(default=Decimal("0.0"), ge=0)
    sec_80ccc_pension_fund: Decimal = Field(default=Decimal("0.0"), ge=0)
    sec_80ccd1_nps_employee: Decimal = Field(default=Decimal("0.0"), ge=0)

    # 80CCD(1B) - Additional NPS
    sec_80ccd1b_nps_additional: Decimal = Field(default=Decimal("0.0"), ge=0)

    # 80D - Health Insurance
    sec_80d_self_family_premium: Decimal = Field(default=Decimal("0.0"), ge=0)
    is_self_senior_citizen: bool = False
    sec_80d_parents_premium: Decimal = Field(default=Decimal("0.0"), ge=0)
    are_parents_senior_citizens: bool = False
    sec_80d_preventive_checkup: Decimal = Field(default=Decimal("0.0"), ge=0)

    # 80E, 80EE, 80EEA, 80EEB
    sec_80e_education_loan_interest: Decimal = Field(default=Decimal("0.0"), ge=0)
    sec_80eea_affordable_housing_interest: Decimal = Field(default=Decimal("0.0"), ge=0)
    sec_80eeb_electric_vehicle_interest: Decimal = Field(default=Decimal("0.0"), ge=0)

    # 80G, 80GG, 80GGA, 80GGC
    sec_80g_donations_100_pct: Decimal = Field(default=Decimal("0.0"), ge=0)
    sec_80g_donations_50_pct: Decimal = Field(default=Decimal("0.0"), ge=0)
    sec_80gg_rent_paid_no_hra: Decimal = Field(default=Decimal("0.0"), ge=0)
    adjusted_total_income_for_80gg: Decimal = Field(default=Decimal("0.0"), ge=0)
    sec_80ggc_political_donations_non_cash: Decimal = Field(default=Decimal("0.0"), ge=0)

    # 80TTA / 80TTB
    sec_80tta_savings_interest: Decimal = Field(default=Decimal("0.0"), ge=0)
    sec_80ttb_senior_deposit_interest: Decimal = Field(default=Decimal("0.0"), ge=0)

    # 80DD / 80DDB / 80U
    sec_80dd_dependent_disability_severe: bool = False
    sec_80dd_has_dependent_disability: bool = False
    sec_80ddb_specified_disease_treatment: Decimal = Field(default=Decimal("0.0"), ge=0)
    is_patient_senior_citizen: bool = False
    sec_80u_self_disability_severe: bool = False
    sec_80u_has_self_disability: bool = False


class ChapterVIAResult(BaseModel):
    total_deductions_allowed: Decimal
    breakdown_by_section: dict[str, Decimal]
    disallowed_excess_by_section: dict[str, Decimal]
    potential_savings_old_regime_at_30pct: Decimal
    notes: list[str]


class IndiaDeductionEngine:
    """Statutory Chapter VI-A deduction calculator and optimizer for the Income-tax Act, 1961."""

    def calculate_deductions(  # noqa: PLR0912, PLR0915
        self, inputs: ChapterVIAInputs, tax_year: str = "2024-25"
    ) -> tuple[ChapterVIAResult, StandardTaxCalculationResponse]:
        allowed: dict[str, Decimal] = {}
        disallowed: dict[str, Decimal] = {}
        steps: list[ExplanationStep] = []
        warnings: list[str] = []
        step_num = 1

        # 1. Section 80CCE Cap (80C + 80CCC + 80CCD(1) <= ₹1,50,000)
        sum_80c_group = (
            inputs.sec_80c_epf_ppf_elss_lic_tuition
            + inputs.sec_80ccc_pension_fund
            + inputs.sec_80ccd1_nps_employee
        )
        limit_80cce = Decimal("150000.00")
        allowed_80cce = min(sum_80c_group, limit_80cce)
        excess_80cce = max(Decimal("0.00"), sum_80c_group - limit_80cce)

        allowed["80C_80CCC_80CCD1"] = apply_bankers_rounding(allowed_80cce)
        if excess_80cce > 0:
            disallowed["80C_80CCC_80CCD1"] = apply_bankers_rounding(excess_80cce)
            warnings.append(
                f"Section 80CCE aggregate cap of ₹1,50,000 exceeded by ₹{excess_80cce}."
            )

        steps.append(
            ExplanationStep(
                step_number=step_num,
                label="Section 80CCE Deduction (80C + 80CCC + 80CCD(1))",
                formula_or_rule="min(Section 80C + 80CCC + 80CCD(1), ₹1,50,000)",
                inputs={"claimed_total": str(sum_80c_group)},
                applied_rate_or_limit=limit_80cce,
                result=allowed["80C_80CCC_80CCD1"],
                notes="Statutory combined cap under Section 80CCE.",
            )
        )
        step_num += 1

        # 2. Section 80CCD(1B) - Additional NPS Contribution (up to ₹50,000)
        limit_80ccd1b = Decimal("50000.00")
        allowed_80ccd1b = min(inputs.sec_80ccd1b_nps_additional, limit_80ccd1b)
        allowed["80CCD_1B"] = apply_bankers_rounding(allowed_80ccd1b)
        excess_80ccd1b = max(Decimal("0.00"), inputs.sec_80ccd1b_nps_additional - limit_80ccd1b)
        if excess_80ccd1b > 0:
            disallowed["80CCD_1B"] = apply_bankers_rounding(excess_80ccd1b)

        steps.append(
            ExplanationStep(
                step_number=step_num,
                label="Section 80CCD(1B) Additional NPS Contribution",
                formula_or_rule="min(Claimed NPS contribution, ₹50,000)",
                inputs={"claimed": str(inputs.sec_80ccd1b_nps_additional)},
                applied_rate_or_limit=limit_80ccd1b,
                result=allowed["80CCD_1B"],
                notes="Exclusive additional deduction over and above Section 80CCE limit.",
            )
        )
        step_num += 1

        # 3. Section 80D - Health Insurance & Preventive Health Checkup
        self_limit = Decimal("50000.00") if inputs.is_self_senior_citizen else Decimal("25000.00")
        parent_limit = (
            Decimal("50000.00") if inputs.are_parents_senior_citizens else Decimal("25000.00")
        )
        checkup_allowed = min(inputs.sec_80d_preventive_checkup, Decimal("5000.00"))

        self_allowed = min(inputs.sec_80d_self_family_premium + checkup_allowed, self_limit)
        parents_allowed = min(inputs.sec_80d_parents_premium, parent_limit)
        total_80d = self_allowed + parents_allowed
        allowed["80D"] = apply_bankers_rounding(total_80d)

        steps.append(
            ExplanationStep(
                step_number=step_num,
                label="Section 80D Health Insurance Deduction",
                formula_or_rule="min(Self/Family + Checkup, Self Limit) + min(Parents, Parent Limit)",
                inputs={
                    "self_limit": str(self_limit),
                    "parent_limit": str(parent_limit),
                    "checkup_claimed": str(inputs.sec_80d_preventive_checkup),
                },
                applied_rate_or_limit=self_limit + parent_limit,
                result=allowed["80D"],
                notes="Includes ₹5,000 sub-limit for preventive health checkup.",
            )
        )
        step_num += 1

        # 4. Section 80E - Interest on Higher Education Loan (No upper limit for 8 years)
        if inputs.sec_80e_education_loan_interest > 0:
            allowed["80E"] = apply_bankers_rounding(inputs.sec_80e_education_loan_interest)
            steps.append(
                ExplanationStep(
                    step_number=step_num,
                    label="Section 80E Higher Education Loan Interest",
                    formula_or_rule="Full interest paid during the year (no monetary ceiling)",
                    inputs={"interest_paid": str(inputs.sec_80e_education_loan_interest)},
                    applied_rate_or_limit=None,
                    result=allowed["80E"],
                    notes="Allowed for 8 consecutive assessment years starting from year of repayment.",
                )
            )
            step_num += 1

        # 5. Section 80EEA - Affordable Housing Interest (up to ₹1,50,000)
        if inputs.sec_80eea_affordable_housing_interest > 0:
            allowed_80eea = min(inputs.sec_80eea_affordable_housing_interest, Decimal("150000.00"))
            allowed["80EEA"] = apply_bankers_rounding(allowed_80eea)
            steps.append(
                ExplanationStep(
                    step_number=step_num,
                    label="Section 80EEA Affordable Housing Loan Interest",
                    formula_or_rule="min(Claimed interest, ₹1,50,000)",
                    inputs={"claimed": str(inputs.sec_80eea_affordable_housing_interest)},
                    applied_rate_or_limit=Decimal("150000.00"),
                    result=allowed["80EEA"],
                    notes="Available for loans sanctioned between 1 Apr 2019 and 31 Mar 2022.",
                )
            )
            step_num += 1

        # 6. Section 80EEB - Electric Vehicle Loan Interest (up to ₹1,50,000)
        if inputs.sec_80eeb_electric_vehicle_interest > 0:
            allowed_80eeb = min(inputs.sec_80eeb_electric_vehicle_interest, Decimal("150000.00"))
            allowed["80EEB"] = apply_bankers_rounding(allowed_80eeb)
            steps.append(
                ExplanationStep(
                    step_number=step_num,
                    label="Section 80EEB Electric Vehicle Loan Interest",
                    formula_or_rule="min(Claimed interest, ₹1,50,000)",
                    inputs={"claimed": str(inputs.sec_80eeb_electric_vehicle_interest)},
                    applied_rate_or_limit=Decimal("150000.00"),
                    result=allowed["80EEB"],
                    notes="Available for EV purchase loans sanctioned between 1 Apr 2019 and 31 Mar 2023.",
                )
            )
            step_num += 1

        # 7. Section 80G - Donations
        total_80g = inputs.sec_80g_donations_100_pct + (
            inputs.sec_80g_donations_50_pct * Decimal("0.5")
        )
        if total_80g > 0:
            allowed["80G"] = apply_bankers_rounding(total_80g)
            steps.append(
                ExplanationStep(
                    step_number=step_num,
                    label="Section 80G Donations to Eligible Funds/Charities",
                    formula_or_rule="100% of eligible 100% funds + 50% of 50% funds",
                    inputs={
                        "100_pct_donations": str(inputs.sec_80g_donations_100_pct),
                        "50_pct_donations": str(inputs.sec_80g_donations_50_pct),
                    },
                    applied_rate_or_limit=None,
                    result=allowed["80G"],
                    notes="Donations exceeding ₹2,000 must be made through non-cash modes.",
                )
            )
            step_num += 1

        # 8. Section 80GG - Rent Paid by Non-HRA Individuals
        if inputs.sec_80gg_rent_paid_no_hra > 0:
            # Rule: least of (1) ₹5,000/mo = ₹60,000/yr, (2) 25% of Adjusted Total Income, (3) Rent paid - 10% of ATI
            ati = inputs.adjusted_total_income_for_80gg
            opt1 = Decimal("60000.00")
            opt2 = ati * Decimal("0.25")
            opt3 = max(Decimal("0.00"), inputs.sec_80gg_rent_paid_no_hra - (ati * Decimal("0.10")))
            allowed_80gg = min(opt1, opt2, opt3) if ati > 0 else opt1
            allowed["80GG"] = apply_bankers_rounding(allowed_80gg)
            steps.append(
                ExplanationStep(
                    step_number=step_num,
                    label="Section 80GG Rent Paid Deduction",
                    formula_or_rule="min(₹60,000, 25% of ATI, Rent - 10% of ATI)",
                    inputs={"rent_paid": str(inputs.sec_80gg_rent_paid_no_hra), "ati": str(ati)},
                    applied_rate_or_limit=Decimal("60000.00"),
                    result=allowed["80GG"],
                    notes="Applicable only if neither employee nor spouse/minor child owns accommodation.",
                )
            )
            step_num += 1

        # 9. Section 80TTA / 80TTB - Interest on Deposits
        if inputs.is_self_senior_citizen:
            allowed_80ttb = min(inputs.sec_80ttb_senior_deposit_interest, Decimal("50000.00"))
            if allowed_80ttb > 0:
                allowed["80TTB"] = apply_bankers_rounding(allowed_80ttb)
                steps.append(
                    ExplanationStep(
                        step_number=step_num,
                        label="Section 80TTB Senior Citizen Deposit Interest",
                        formula_or_rule="min(Savings + FD/RD interest, ₹50,000)",
                        inputs={"claimed": str(inputs.sec_80ttb_senior_deposit_interest)},
                        applied_rate_or_limit=Decimal("50000.00"),
                        result=allowed["80TTB"],
                        notes="Available exclusively to resident senior citizens (age 60+).",
                    )
                )
                step_num += 1
        else:
            allowed_80tta = min(inputs.sec_80tta_savings_interest, Decimal("10000.00"))
            if allowed_80tta > 0:
                allowed["80TTA"] = apply_bankers_rounding(allowed_80tta)
                steps.append(
                    ExplanationStep(
                        step_number=step_num,
                        label="Section 80TTA Savings Account Interest",
                        formula_or_rule="min(Savings bank interest, ₹10,000)",
                        inputs={"claimed": str(inputs.sec_80tta_savings_interest)},
                        applied_rate_or_limit=Decimal("10000.00"),
                        result=allowed["80TTA"],
                        notes="Does not apply to fixed deposits or recurring deposits.",
                    )
                )
                step_num += 1

        # 10. Section 80DD / 80U - Disability Deductions
        if inputs.sec_80u_has_self_disability:
            ded_80u = (
                Decimal("125000.00")
                if inputs.sec_80u_self_disability_severe
                else Decimal("75000.00")
            )
            allowed["80U"] = apply_bankers_rounding(ded_80u)
            steps.append(
                ExplanationStep(
                    step_number=step_num,
                    label="Section 80U Person with Disability",
                    formula_or_rule="₹1,25,000 for severe disability (80%+), ₹75,000 for normal disability (40%-80%)",
                    inputs={"is_severe": str(inputs.sec_80u_self_disability_severe)},
                    applied_rate_or_limit=ded_80u,
                    result=allowed["80U"],
                    notes="Requires Form 10-IA medical certificate from government specialist.",
                )
            )
            step_num += 1

        if inputs.sec_80dd_has_dependent_disability:
            ded_80dd = (
                Decimal("125000.00")
                if inputs.sec_80dd_dependent_disability_severe
                else Decimal("75000.00")
            )
            allowed["80DD"] = apply_bankers_rounding(ded_80dd)
            steps.append(
                ExplanationStep(
                    step_number=step_num,
                    label="Section 80DD Maintenance of Dependent with Disability",
                    formula_or_rule="₹1,25,000 for severe (80%+), ₹75,000 for normal (40%-80%)",
                    inputs={"is_severe": str(inputs.sec_80dd_dependent_disability_severe)},
                    applied_rate_or_limit=ded_80dd,
                    result=allowed["80DD"],
                    notes="Deduction for medical treatment and maintenance of dependent relative.",
                )
            )
            step_num += 1

        total_allowed = sum(allowed.values(), Decimal("0.00"))
        potential_savings = apply_bankers_rounding(
            total_allowed * Decimal("0.312")
        )  # 30% slab + 4% cess

        res = ChapterVIAResult(
            total_deductions_allowed=apply_bankers_rounding(total_allowed),
            breakdown_by_section=allowed,
            disallowed_excess_by_section=disallowed,
            potential_savings_old_regime_at_30pct=potential_savings,
            notes=warnings,
        )

        trace_response = StandardTaxCalculationResponse(
            jurisdiction="IN",
            tax_type="income_tax_deductions",
            tax_year=tax_year,
            assessment_year=f"{int(tax_year[:4]) + 1}-{str(int(tax_year[:4]) + 2)[2:]}",
            effective_date=f"{tax_year[:4]}-04-01",
            rule_version=f"IN-VIA-{tax_year}.1",
            taxpayer_type="individual",
            regime="old",
            inputs=inputs.model_dump(),
            calculation={
                "total_deductions_allowed": str(res.total_deductions_allowed),
                "potential_tax_savings": str(res.potential_savings_old_regime_at_30pct),
                "breakdown": {k: str(v) for k, v in allowed.items()},
            },
            steps=steps,
            warnings=warnings,
            assumptions=[
                "Deductions apply strictly under the Old Tax Regime. In the New Tax Regime (Sec 115BAC), Chapter VI-A deductions are disallowed except 80CCD(2) and 80JJAA."
            ],
            official_sources=[
                OfficialSourceReference(
                    source_id="IN-ACT-VIA",
                    title="Chapter VI-A: Deductions to be made in computing Total Income",
                    section_or_rule="Sections 80C to 80U",
                    act_name="Income-tax Act, 1961",
                    url="https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx",
                    effective_date=f"{tax_year[:4]}-04-01",
                )
            ],
        )

        return res, trace_response
