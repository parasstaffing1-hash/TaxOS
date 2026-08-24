"""Universal India Personal Income Tax Engine.

Supports Old & New Tax Regimes, AY 2024-25, AY 2025-26, AY 2026-27+,
Section 87A rebate & marginal relief, Surcharge & mathematical marginal relief,
and Health & Education Cess with complete explainability trace.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from taxos.domain.financial.trace import (
    ConfidenceLevel,
    ExplanationStep,
    OfficialSourceReference,
    StandardTaxCalculationResponse,
    TaxRegime,
    TaxSlabBreakdown,
)
from taxos.domain.india.models import (
    IndiaIncomeTaxInput,
    RegimeComparisonResult,
    TaxpayerAgeCategory,
)


def round_to_10(amount: Decimal) -> Decimal:
    """Round amount to nearest multiple of ₹10 per Section 288A/288B."""
    return (amount / Decimal("10")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal("10")


class IndiaIncomeTaxEngine:
    """Pure Decimal calculation engine for India Income Tax."""

    def __init__(self, assessment_year: str = "2025-26") -> None:
        self.assessment_year = assessment_year

    def calculate_new_regime(  # noqa: PLR0912, PLR0915
        self, user_input: IndiaIncomeTaxInput
    ) -> StandardTaxCalculationResponse:
        """Calculate income tax under Section 115BAC (New Tax Regime)."""
        ay = user_input.assessment_year or self.assessment_year
        steps: list[ExplanationStep] = []
        assumptions: list[str] = [
            "Default tax regime under Section 115BAC(1A)",
            "Most Chapter VI-A deductions (except Section 80CCD(2) Employer NPS) are forgone",
            "Health & Education Cess applied at mandatory statutory rate of 4%",
        ]
        warnings: list[str] = []

        # 1. Standard Deduction on Salary
        # AY 2025-26 & later (Budget 2024): ₹75,000; AY 2024-25 & earlier: ₹50,000
        std_deduction_limit = Decimal("75000.0") if ay >= "2025-26" else Decimal("50000.0")
        std_deduction = min(user_input.salary_income, std_deduction_limit)
        net_salary = max(Decimal("0.0"), user_input.salary_income - std_deduction)

        steps.append(
            ExplanationStep(
                step_number=1,
                label="Standard Deduction on Salary (Section 16(ia))",
                formula_or_rule=f"Min(Gross Salary, ₹{std_deduction_limit:,.0f})",
                inputs={"gross_salary": user_input.salary_income, "limit": std_deduction_limit},
                result=std_deduction,
                notes=f"Applicable under Section 115BAC for AY {ay}",
            )
        )

        # 2. Employer NPS Deduction u/s 80CCD(2) - Allowed in New Regime
        nps_deduction = user_input.section_80ccd_2
        if nps_deduction > 0:
            steps.append(
                ExplanationStep(
                    step_number=2,
                    label="Employer NPS Contribution (Section 80CCD(2))",
                    formula_or_rule="Allowed up to 14% of (Basic + DA)",
                    inputs={"section_80ccd_2": nps_deduction},
                    result=nps_deduction,
                    notes="Specifically retained under Section 115BAC(2)",
                )
            )

        # 3. Gross Total Income across Heads
        # In New Regime: Loss from self-occupied house property CANNOT be set off against salary
        hp_income = user_input.house_property_income
        if hp_income < 0:
            warnings.append(
                "Loss from house property cannot be set off against salary under New Regime."
            )
            hp_income_effective = Decimal("0.0")
        else:
            hp_income_effective = hp_income

        gti = (
            net_salary
            + hp_income_effective
            + user_input.business_profession_income
            + user_input.other_sources_income
            + user_input.capital_gains_stcg_other
            + user_input.capital_gains_ltcg_other
        )

        # Total Deductions in New Regime
        total_deductions = nps_deduction
        taxable_normal_income = max(Decimal("0.0"), gti - total_deductions)
        taxable_normal_income = round_to_10(taxable_normal_income)

        steps.append(
            ExplanationStep(
                step_number=3,
                label="Gross Total Normal Income",
                formula_or_rule="Net Salary + House Property + Business + Other Sources",
                inputs={"net_salary": net_salary, "other_income": gti - net_salary},
                result=gti,
            )
        )

        # 4. Tax Slabs under Section 115BAC
        # AY 2025-26+ (Budget 2024 Slabs):
        # 0-3L: 0%, 3-7L: 5%, 7-10L: 10%, 10-12L: 15%, 12-15L: 20%, >15L: 30%
        # AY 2024-25 (Finance Act 2023 Slabs):
        # 0-3L: 0%, 3-6L: 5%, 6-9L: 10%, 9-12L: 15%, 12-15L: 20%, >15L: 30%
        if ay >= "2025-26":
            slabs_config = [
                (Decimal("0.0"), Decimal("300000.0"), Decimal("0.0")),
                (Decimal("300000.0"), Decimal("700000.0"), Decimal("0.05")),
                (Decimal("700000.0"), Decimal("1000000.0"), Decimal("0.10")),
                (Decimal("1000000.0"), Decimal("1200000.0"), Decimal("0.15")),
                (Decimal("1200000.0"), Decimal("1500000.0"), Decimal("0.20")),
                (Decimal("1500000.0"), None, Decimal("0.30")),
            ]
            rebate_threshold = Decimal("700000.0")
        else:
            slabs_config = [
                (Decimal("0.0"), Decimal("300000.0"), Decimal("0.0")),
                (Decimal("300000.0"), Decimal("600000.0"), Decimal("0.05")),
                (Decimal("600000.0"), Decimal("900000.0"), Decimal("0.10")),
                (Decimal("900000.0"), Decimal("1200000.0"), Decimal("0.15")),
                (Decimal("1200000.0"), Decimal("1500000.0"), Decimal("0.20")),
                (Decimal("1500000.0"), None, Decimal("0.30")),
            ]
            rebate_threshold = Decimal("700000.0")

        base_slab_tax = Decimal("0.0")
        slabs_breakdown: list[TaxSlabBreakdown] = []

        remaining_income = taxable_normal_income
        for min_amt, max_amt, rate in slabs_config:
            if remaining_income <= min_amt:
                continue

            if max_amt is not None:
                taxable_in_slab = min(remaining_income, max_amt) - min_amt
            else:
                taxable_in_slab = remaining_income - min_amt

            tax_in_slab = (taxable_in_slab * rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            base_slab_tax += tax_in_slab

            slabs_breakdown.append(
                TaxSlabBreakdown(
                    min_amount=min_amt,
                    max_amount=max_amt,
                    rate=rate,
                    taxable_in_slab=taxable_in_slab,
                    tax_amount=tax_in_slab,
                )
            )

        # 5. Special Capital Gains Tax (STCG 111A @ 20%/15%, LTCG 112A @ 12.5%/10%)
        # Post Budget 2024 (AY 2025-26): STCG 111A = 20%, LTCG 112A = 12.5% (exemption ₹1.25L)
        # Prior to July 2024: STCG 111A = 15%, LTCG 112A = 10% (exemption ₹1.00L)
        stcg_rate = Decimal("0.20") if ay >= "2025-26" else Decimal("0.15")
        ltcg_rate = Decimal("0.125") if ay >= "2025-26" else Decimal("0.10")
        ltcg_exemption_cap = Decimal("125000.0") if ay >= "2025-26" else Decimal("100000.0")

        stcg_tax = (user_input.capital_gains_stcg_111a * stcg_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        taxable_ltcg = max(Decimal("0.0"), user_input.capital_gains_ltcg_112a - ltcg_exemption_cap)
        ltcg_tax = (taxable_ltcg * ltcg_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total_base_tax = base_slab_tax + stcg_tax + ltcg_tax

        # 6. Section 87A Rebate and Marginal Relief under New Regime
        # Full rebate if total taxable income <= ₹7,00,000
        rebate_87a = Decimal("0.0")
        total_taxable_income = (
            taxable_normal_income + user_input.capital_gains_stcg_111a + taxable_ltcg
        )

        if total_taxable_income <= rebate_threshold:
            rebate_87a = total_base_tax
            tax_after_rebate = Decimal("0.0")
            steps.append(
                ExplanationStep(
                    step_number=4,
                    label="Section 87A Full Tax Rebate",
                    formula_or_rule=f"100% Tax Rebate because Total Taxable Income <= ₹{rebate_threshold:,.0f}",
                    inputs={
                        "total_taxable_income": total_taxable_income,
                        "base_tax": total_base_tax,
                    },
                    result=rebate_87a,
                    notes="Zero tax payable for income up to ₹7.0 Lakhs",
                )
            )
        else:
            # Marginal Relief for New Regime (where income slightly exceeds ₹7 Lakhs)
            # Rule: Tax payable cannot exceed (Total Taxable Income - ₹7,00,000)
            income_over_threshold = total_taxable_income - rebate_threshold
            if total_base_tax > income_over_threshold:
                marginal_relief_87a = total_base_tax - income_over_threshold
                rebate_87a = marginal_relief_87a
                tax_after_rebate = income_over_threshold
                steps.append(
                    ExplanationStep(
                        step_number=4,
                        label="Section 87A Marginal Relief",
                        formula_or_rule="Base Tax - (Total Taxable Income - ₹7,00,000)",
                        inputs={
                            "base_tax": total_base_tax,
                            "excess_income": income_over_threshold,
                        },
                        result=marginal_relief_87a,
                        notes=f"Tax capped at excess income above ₹7 Lakhs (₹{income_over_threshold:,.0f})",
                    )
                )
            else:
                tax_after_rebate = total_base_tax

        # 7. Surcharge & Marginal Relief under New Regime
        # Surcharge rates: >50L: 10%, >1Cr: 15%, >2Cr: 25% (Max 25% under New Regime)
        surcharge = Decimal("0.0")
        surcharge_relief = Decimal("0.0")
        surcharge_rate = Decimal("0.0")

        if total_taxable_income > Decimal("20000000.0"):
            surcharge_rate = Decimal("0.25")
            threshold = Decimal("20000000.0")
        elif total_taxable_income > Decimal("10000000.0"):
            surcharge_rate = Decimal("0.15")
            threshold = Decimal("10000000.0")
        elif total_taxable_income > Decimal("5000000.0"):
            surcharge_rate = Decimal("0.10")
            threshold = Decimal("5000000.0")
        else:
            threshold = Decimal("0.0")

        if surcharge_rate > 0:
            raw_surcharge = (tax_after_rebate * surcharge_rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            # Calculate Marginal Relief on Surcharge
            # Tax + Surcharge cannot exceed (Tax on Threshold + Excess Income over Threshold)
            tax_at_threshold = self._compute_tax_at_amount_new_regime(threshold, ay)
            max_payable = tax_at_threshold + (total_taxable_income - threshold)
            payable_with_surcharge = tax_after_rebate + raw_surcharge

            if payable_with_surcharge > max_payable:
                surcharge_relief = payable_with_surcharge - max_payable
                surcharge = max(Decimal("0.0"), raw_surcharge - surcharge_relief)
            else:
                surcharge = raw_surcharge

            steps.append(
                ExplanationStep(
                    step_number=5,
                    label=f"Surcharge ({surcharge_rate * 100:.0f}%) & Marginal Relief",
                    formula_or_rule=f"Surcharge @ {surcharge_rate * 100:.0f}% with Marginal Relief",
                    inputs={"surcharge_rate": surcharge_rate, "relief": surcharge_relief},
                    result=surcharge,
                )
            )

        # 8. Health & Education Cess (4%)
        tax_before_cess = tax_after_rebate + surcharge
        cess = (tax_before_cess * Decimal("0.04")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        steps.append(
            ExplanationStep(
                step_number=6,
                label="Health & Education Cess (4%)",
                formula_or_rule="4% of (Tax + Surcharge)",
                inputs={"tax_and_surcharge": tax_before_cess},
                result=cess,
                notes="Section 115BAC + Finance Act mandatory 4% cess",
            )
        )

        total_tax_liability = round_to_10(tax_before_cess + cess)
        net_tax_payable = round_to_10(
            max(
                Decimal("0.0"),
                total_tax_liability - user_input.tds_tcs_paid - user_input.advance_tax_paid,
            )
        )
        tax_refund = round_to_10(
            max(
                Decimal("0.0"),
                (user_input.tds_tcs_paid + user_input.advance_tax_paid) - total_tax_liability,
            )
        )

        sources = [
            OfficialSourceReference(
                source_id="sec-115bac",
                title="Special provisions relating to tax on income of individuals and Hindu undivided family",
                section_or_rule="Section 115BAC(1A)",
                act_name="Income-tax Act, 1961 as amended by Finance (No. 2) Act, 2024",
                effective_date=f"AY {ay}",
            ),
            OfficialSourceReference(
                source_id="sec-87a",
                title="Rebate of income-tax in case of certain individuals",
                section_or_rule="Section 87A",
                act_name="Income-tax Act, 1961",
            ),
        ]

        return StandardTaxCalculationResponse(
            jurisdiction="IN",
            tax_type="income_tax",
            tax_year=user_input.financial_year,
            assessment_year=ay,
            rule_version=f"IN-115BAC-{ay}.1",
            taxpayer_type="individual",
            regime=TaxRegime.NEW,
            inputs={
                "salary_income": user_input.salary_income,
                "house_property_income": user_input.house_property_income,
                "business_income": user_input.business_profession_income,
                "capital_gains_stcg": user_input.capital_gains_stcg_111a,
                "capital_gains_ltcg": user_input.capital_gains_ltcg_112a,
                "other_sources": user_input.other_sources_income,
                "employer_nps": user_input.section_80ccd_2,
            },
            calculation={
                "gross_total_income": gti,
                "standard_deduction": std_deduction,
                "other_deductions": total_deductions,
                "taxable_income": total_taxable_income,
                "base_tax": total_base_tax,
                "rebate_87a": rebate_87a,
                "surcharge": surcharge,
                "surcharge_marginal_relief": surcharge_relief,
                "health_and_education_cess": cess,
                "total_tax_liability": total_tax_liability,
                "prepaid_taxes": user_input.tds_tcs_paid + user_input.advance_tax_paid,
                "net_tax_payable": net_tax_payable,
                "tax_refund": tax_refund,
            },
            slabs_breakdown=slabs_breakdown,
            steps=steps,
            warnings=warnings,
            assumptions=assumptions,
            official_sources=sources,
            confidence=ConfidenceLevel.DETERMINISTIC,
            review_required=False,
        )

    def calculate_old_regime(  # noqa: PLR0912, PLR0915
        self, user_input: IndiaIncomeTaxInput
    ) -> StandardTaxCalculationResponse:
        """Calculate income tax under the Old Tax Regime with full Chapter VI-A deductions."""
        ay = user_input.assessment_year or self.assessment_year
        steps: list[ExplanationStep] = []
        assumptions: list[str] = [
            "Old Tax Regime with standard Chapter VI-A deductions and allowances",
            "Health & Education Cess applied at 4%",
        ]
        warnings: list[str] = []

        # 1. Salary Standard Deduction (₹50,000 in Old Regime)
        std_deduction = min(user_input.salary_income, Decimal("50000.0"))
        net_salary = max(Decimal("0.0"), user_input.salary_income - std_deduction)

        steps.append(
            ExplanationStep(
                step_number=1,
                label="Standard Deduction on Salary (Section 16(ia))",
                formula_or_rule="Min(Gross Salary, ₹50,000)",
                inputs={"gross_salary": user_input.salary_income, "limit": Decimal("50000.0")},
                result=std_deduction,
                notes="Standard deduction of ₹50,000 under Old Regime",
            )
        )

        # 2. House property interest loss cap (₹2,00,000 for self-occupied)
        hp_income = user_input.house_property_income
        if hp_income < Decimal("-200000.0"):
            warnings.append(
                "Loss from house property set-off against other heads is capped at ₹2,00,000 u/s 71(3A)."
            )
            effective_hp_loss = Decimal("-200000.0")
        else:
            effective_hp_loss = hp_income

        gti = (
            net_salary
            + effective_hp_loss
            + user_input.business_profession_income
            + user_input.other_sources_income
            + user_input.capital_gains_stcg_other
            + user_input.capital_gains_ltcg_other
        )

        # 3. Chapter VI-A Deductions
        # Section 80C capped at ₹1,50,000
        sec_80c_eligible = min(user_input.section_80c, Decimal("150000.0"))
        # Section 80CCD(1B) additional NPS capped at ₹50,000
        sec_80ccd_1b_eligible = min(user_input.section_80ccd_1b, Decimal("50000.0"))
        # Section 80CCD(2) Employer NPS
        sec_80ccd_2_eligible = user_input.section_80ccd_2

        # Section 80D Medical Insurance:
        # Self/family: ₹25,000 (₹50,000 if senior); Parents: ₹25,000 (₹50,000 if senior)
        sec_80d_self_limit = (
            Decimal("50000.0")
            if user_input.age_category != TaxpayerAgeCategory.BELOW_60
            else Decimal("25000.0")
        )
        sec_80d_self = min(user_input.section_80d_self, sec_80d_self_limit)
        sec_80d_parents = min(user_input.section_80d_parents, Decimal("50000.0"))
        sec_80d_eligible = sec_80d_self + sec_80d_parents

        # 80E (Education loan interest - unlimited), 80G (Donations)
        sec_80e_eligible = user_input.section_80e
        sec_80g_eligible = user_input.section_80g

        # 80TTA (₹10,000) / 80TTB (₹50,000 for senior citizens)
        if user_input.age_category != TaxpayerAgeCategory.BELOW_60:
            sec_80tt_eligible = min(user_input.section_80tta_ttb, Decimal("50000.0"))
        else:
            sec_80tt_eligible = min(user_input.section_80tta_ttb, Decimal("10000.0"))

        total_chapter_via = (
            sec_80c_eligible
            + sec_80ccd_1b_eligible
            + sec_80ccd_2_eligible
            + sec_80d_eligible
            + sec_80e_eligible
            + sec_80g_eligible
            + sec_80tt_eligible
            + user_input.other_chapter_via_deductions
        )

        taxable_normal_income = max(Decimal("0.0"), gti - total_chapter_via)
        taxable_normal_income = round_to_10(taxable_normal_income)

        steps.append(
            ExplanationStep(
                step_number=2,
                label="Chapter VI-A Eligible Deductions",
                formula_or_rule="80C + 80CCD(1B) + 80CCD(2) + 80D + 80E + 80G + 80TTA/TTB",
                inputs={
                    "80C": sec_80c_eligible,
                    "80CCD_1B": sec_80ccd_1b_eligible,
                    "80D": sec_80d_eligible,
                    "other": total_chapter_via
                    - (sec_80c_eligible + sec_80ccd_1b_eligible + sec_80d_eligible),
                },
                result=total_chapter_via,
                notes="Total deductions subtracted from Gross Total Income",
            )
        )

        # 4. Old Regime Tax Slabs by Age Category
        if user_input.age_category == TaxpayerAgeCategory.SUPER_SENIOR_CITIZEN:
            # Super senior (80+ yrs): Nil up to 5L, 20% 5-10L, 30% >10L
            slabs_config = [
                (Decimal("0.0"), Decimal("500000.0"), Decimal("0.0")),
                (Decimal("500000.0"), Decimal("1000000.0"), Decimal("0.20")),
                (Decimal("1000000.0"), None, Decimal("0.30")),
            ]
        elif user_input.age_category == TaxpayerAgeCategory.SENIOR_CITIZEN:
            # Senior (60-80 yrs): Nil up to 3L, 5% 3-5L, 20% 5-10L, 30% >10L
            slabs_config = [
                (Decimal("0.0"), Decimal("300000.0"), Decimal("0.0")),
                (Decimal("300000.0"), Decimal("500000.0"), Decimal("0.05")),
                (Decimal("500000.0"), Decimal("1000000.0"), Decimal("0.20")),
                (Decimal("1000000.0"), None, Decimal("0.30")),
            ]
        else:
            # Regular individual (<60 yrs): Nil up to 2.5L, 5% 2.5-5L, 20% 5-10L, 30% >10L
            slabs_config = [
                (Decimal("0.0"), Decimal("250000.0"), Decimal("0.0")),
                (Decimal("250000.0"), Decimal("500000.0"), Decimal("0.05")),
                (Decimal("500000.0"), Decimal("1000000.0"), Decimal("0.20")),
                (Decimal("1000000.0"), None, Decimal("0.30")),
            ]

        base_slab_tax = Decimal("0.0")
        slabs_breakdown: list[TaxSlabBreakdown] = []
        remaining_income = taxable_normal_income

        for min_amt, max_amt, rate in slabs_config:
            if remaining_income <= min_amt:
                continue

            if max_amt is not None:
                taxable_in_slab = min(remaining_income, max_amt) - min_amt
            else:
                taxable_in_slab = remaining_income - min_amt

            tax_in_slab = (taxable_in_slab * rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            base_slab_tax += tax_in_slab

            slabs_breakdown.append(
                TaxSlabBreakdown(
                    min_amount=min_amt,
                    max_amount=max_amt,
                    rate=rate,
                    taxable_in_slab=taxable_in_slab,
                    tax_amount=tax_in_slab,
                )
            )

        # Special Capital Gains Tax
        stcg_tax = (user_input.capital_gains_stcg_111a * Decimal("0.15")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        taxable_ltcg = max(
            Decimal("0.0"), user_input.capital_gains_ltcg_112a - Decimal("100000.0")
        )
        ltcg_tax = (taxable_ltcg * Decimal("0.10")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        total_base_tax = base_slab_tax + stcg_tax + ltcg_tax
        total_taxable_income = (
            taxable_normal_income + user_input.capital_gains_stcg_111a + taxable_ltcg
        )

        # 5. Section 87A Rebate in Old Regime (If Total Income <= ₹5,00,000, Max ₹12,500)
        rebate_87a = Decimal("0.0")
        if total_taxable_income <= Decimal("500000.0"):
            rebate_87a = min(total_base_tax, Decimal("12500.0"))
            tax_after_rebate = max(Decimal("0.0"), total_base_tax - rebate_87a)
            steps.append(
                ExplanationStep(
                    step_number=3,
                    label="Section 87A Tax Rebate (Old Regime)",
                    formula_or_rule="100% Tax Rebate up to ₹12,500 (Income <= ₹5 Lakhs)",
                    inputs={
                        "total_taxable_income": total_taxable_income,
                        "base_tax": total_base_tax,
                    },
                    result=rebate_87a,
                    notes="Full tax relief up to ₹5.0 Lakhs in Old Regime",
                )
            )
        else:
            tax_after_rebate = total_base_tax

        # 6. Surcharge & Marginal Relief (Old Regime: 10% >50L, 15% >1Cr, 25% >2Cr, 37% >5Cr)
        surcharge = Decimal("0.0")
        surcharge_relief = Decimal("0.0")
        surcharge_rate = Decimal("0.0")

        if total_taxable_income > Decimal("50000000.0"):
            surcharge_rate = Decimal("0.37")
            threshold = Decimal("50000000.0")
        elif total_taxable_income > Decimal("20000000.0"):
            surcharge_rate = Decimal("0.25")
            threshold = Decimal("20000000.0")
        elif total_taxable_income > Decimal("10000000.0"):
            surcharge_rate = Decimal("0.15")
            threshold = Decimal("10000000.0")
        elif total_taxable_income > Decimal("5000000.0"):
            surcharge_rate = Decimal("0.10")
            threshold = Decimal("5000000.0")
        else:
            threshold = Decimal("0.0")

        if surcharge_rate > 0:
            raw_surcharge = (tax_after_rebate * surcharge_rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            tax_at_threshold = self._compute_tax_at_amount_old_regime(
                threshold, user_input.age_category
            )
            max_payable = tax_at_threshold + (total_taxable_income - threshold)
            payable_with_surcharge = tax_after_rebate + raw_surcharge

            if payable_with_surcharge > max_payable:
                surcharge_relief = payable_with_surcharge - max_payable
                surcharge = max(Decimal("0.0"), raw_surcharge - surcharge_relief)
            else:
                surcharge = raw_surcharge

            steps.append(
                ExplanationStep(
                    step_number=4,
                    label=f"Surcharge ({surcharge_rate * 100:.0f}%) & Marginal Relief",
                    formula_or_rule=f"Surcharge @ {surcharge_rate * 100:.0f}% with Marginal Relief",
                    inputs={"surcharge_rate": surcharge_rate, "relief": surcharge_relief},
                    result=surcharge,
                )
            )

        # 7. Health & Education Cess (4%)
        tax_before_cess = tax_after_rebate + surcharge
        cess = (tax_before_cess * Decimal("0.04")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        steps.append(
            ExplanationStep(
                step_number=5,
                label="Health & Education Cess (4%)",
                formula_or_rule="4% of (Tax + Surcharge)",
                inputs={"tax_and_surcharge": tax_before_cess},
                result=cess,
                notes="Statutory 4% Health & Education Cess",
            )
        )

        total_tax_liability = round_to_10(tax_before_cess + cess)
        net_tax_payable = round_to_10(
            max(
                Decimal("0.0"),
                total_tax_liability - user_input.tds_tcs_paid - user_input.advance_tax_paid,
            )
        )
        tax_refund = round_to_10(
            max(
                Decimal("0.0"),
                (user_input.tds_tcs_paid + user_input.advance_tax_paid) - total_tax_liability,
            )
        )

        sources = [
            OfficialSourceReference(
                source_id="sec-individual-slabs",
                title="Rates of Income-tax for Individuals and HUF",
                section_or_rule="First Schedule, Part I",
                act_name=f"Finance Act applicable to AY {ay}",
            ),
            OfficialSourceReference(
                source_id="sec-87a-old",
                title="Rebate of income-tax in case of certain individuals",
                section_or_rule="Section 87A",
                act_name="Income-tax Act, 1961",
            ),
            OfficialSourceReference(
                source_id="chapter-via",
                title="Deductions to be made in computing total income",
                section_or_rule="Chapter VI-A (Sections 80C to 80U)",
                act_name="Income-tax Act, 1961",
            ),
        ]

        return StandardTaxCalculationResponse(
            jurisdiction="IN",
            tax_type="income_tax",
            tax_year=user_input.financial_year,
            assessment_year=ay,
            rule_version=f"IN-OLD-{ay}.1",
            taxpayer_type="individual",
            regime=TaxRegime.OLD,
            inputs={
                "salary_income": user_input.salary_income,
                "house_property_income": user_input.house_property_income,
                "business_income": user_input.business_profession_income,
                "capital_gains_stcg": user_input.capital_gains_stcg_111a,
                "capital_gains_ltcg": user_input.capital_gains_ltcg_112a,
                "other_sources": user_input.other_sources_income,
                "section_80c": sec_80c_eligible,
                "section_80d": sec_80d_eligible,
                "section_80ccd_1b": sec_80ccd_1b_eligible,
                "total_chapter_via": total_chapter_via,
            },
            calculation={
                "gross_total_income": gti,
                "standard_deduction": std_deduction,
                "chapter_via_deductions": total_chapter_via,
                "taxable_income": total_taxable_income,
                "base_tax": total_base_tax,
                "rebate_87a": rebate_87a,
                "surcharge": surcharge,
                "surcharge_marginal_relief": surcharge_relief,
                "health_and_education_cess": cess,
                "total_tax_liability": total_tax_liability,
                "prepaid_taxes": user_input.tds_tcs_paid + user_input.advance_tax_paid,
                "net_tax_payable": net_tax_payable,
                "tax_refund": tax_refund,
            },
            slabs_breakdown=slabs_breakdown,
            steps=steps,
            warnings=warnings,
            assumptions=assumptions,
            official_sources=sources,
            confidence=ConfidenceLevel.DETERMINISTIC,
            review_required=False,
        )

    def compare_regimes(self, user_input: IndiaIncomeTaxInput) -> RegimeComparisonResult:
        """Compare Old vs New Tax Regimes and recommend the optimal tax strategy."""
        old_res = self.calculate_old_regime(user_input)
        new_res = self.calculate_new_regime(user_input)

        old_tax = old_res.calculation["total_tax_liability"]
        new_tax = new_res.calculation["total_tax_liability"]

        if new_tax < old_tax:
            recommended = TaxRegime.NEW
            savings = old_tax - new_tax
            summary = (
                f"New Tax Regime (Section 115BAC) is more beneficial for you. "
                f"You save ₹{savings:,.0f} in tax compared to the Old Regime."
            )
        elif old_tax < new_tax:
            recommended = TaxRegime.OLD
            savings = new_tax - old_tax
            summary = (
                f"Old Tax Regime is more beneficial for you due to eligible deductions. "
                f"You save ₹{savings:,.0f} in tax compared to the New Regime."
            )
        else:
            recommended = TaxRegime.NEW
            savings = Decimal("0.0")
            summary = "Both Old and New Regimes result in identical tax liability. New Regime is recommended due to simpler filing compliance."

        # Approximate break-even deduction needed for Old Regime to match New Regime
        break_even = self._calculate_break_even_deductions(user_input)

        return RegimeComparisonResult(
            financial_year=user_input.financial_year,
            assessment_year=user_input.assessment_year or self.assessment_year,
            gross_total_income=new_res.calculation["gross_total_income"],
            old_regime_deductions=old_res.calculation["standard_deduction"]
            + old_res.calculation["chapter_via_deductions"],
            old_regime_taxable_income=old_res.calculation["taxable_income"],
            old_regime_base_tax=old_res.calculation["base_tax"],
            old_regime_rebate_87a=old_res.calculation["rebate_87a"],
            old_regime_surcharge=old_res.calculation["surcharge"],
            old_regime_cess=old_res.calculation["health_and_education_cess"],
            old_regime_total_tax=old_tax,
            new_regime_deductions=new_res.calculation["standard_deduction"]
            + new_res.calculation["other_deductions"],
            new_regime_taxable_income=new_res.calculation["taxable_income"],
            new_regime_base_tax=new_res.calculation["base_tax"],
            new_regime_rebate_87a=new_res.calculation["rebate_87a"],
            new_regime_surcharge=new_res.calculation["surcharge"],
            new_regime_cess=new_res.calculation["health_and_education_cess"],
            new_regime_total_tax=new_tax,
            recommended_regime=recommended,
            tax_savings=savings,
            break_even_deductions_needed=break_even,
            summary_explanation=summary,
        )

    def _compute_tax_at_amount_new_regime(self, amount: Decimal, ay: str) -> Decimal:
        """Helper to compute exact base tax on a specific income amount under New Regime."""
        if amount <= Decimal("0.0"):
            return Decimal("0.0")
        fake_input = IndiaIncomeTaxInput(
            salary_income=Decimal("0.0"), other_sources_income=amount, assessment_year=ay
        )
        res = self.calculate_new_regime(fake_input)
        return res.calculation["base_tax"]

    def _compute_tax_at_amount_old_regime(
        self, amount: Decimal, age_cat: TaxpayerAgeCategory
    ) -> Decimal:
        """Helper to compute exact base tax on a specific income amount under Old Regime."""
        if amount <= Decimal("0.0"):
            return Decimal("0.0")
        fake_input = IndiaIncomeTaxInput(
            salary_income=Decimal("0.0"), other_sources_income=amount, age_category=age_cat
        )
        res = self.calculate_old_regime(fake_input)
        return res.calculation["base_tax"]

    def _calculate_break_even_deductions(self, user_input: IndiaIncomeTaxInput) -> Decimal:
        """Calculate the total deductions needed in Old Regime to match New Regime tax."""
        new_res = self.calculate_new_regime(user_input)
        target_tax = new_res.calculation["total_tax_liability"]

        # If new tax is zero, break-even is the deduction to make taxable income <= 5L
        gti = new_res.calculation["gross_total_income"]
        if target_tax == Decimal("0.0"):
            return max(Decimal("0.0"), gti - Decimal("500000.0"))

        # Binary search for deduction amount that yields target_tax
        low = Decimal("0.0")
        high = gti
        for _ in range(25):
            mid = (low + high) / Decimal("2.0")
            trial_input = user_input.model_copy(deep=True)
            trial_input.section_80c = min(mid, Decimal("150000.0"))
            trial_input.other_chapter_via_deductions = max(
                Decimal("0.0"), mid - trial_input.section_80c
            )
            trial_res = self.calculate_old_regime(trial_input)
            trial_tax = trial_res.calculation["total_tax_liability"]

            if trial_tax > target_tax:
                low = mid
            else:
                high = mid

        return round_to_10((low + high) / Decimal("2.0"))
