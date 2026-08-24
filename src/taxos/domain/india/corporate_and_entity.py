"""India Corporate, Partnership, LLP & Entity Tax Engine."""

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


class EntityType(StrEnum):
    DOMESTIC_COMPANY_115BAA = "domestic_company_115baa"  # 22%
    DOMESTIC_COMPANY_115BAB = "domestic_company_115bab"  # 15%
    DOMESTIC_COMPANY_STANDARD = "domestic_company_standard"  # 25% or 30%
    FOREIGN_COMPANY = "foreign_company"  # 40% (35% in AY 2025-26)
    PARTNERSHIP_FIRM_OR_LLP = "partnership_firm_or_llp"  # 30%
    HUF = "huf"  # Slab tax


class EntityTaxInputs(BaseModel):
    entity_type: EntityType = EntityType.DOMESTIC_COMPANY_115BAA
    taxable_income: Decimal = Field(ge=0)
    book_profits_for_mat: Decimal = Field(default=Decimal("0.0"), ge=0)
    turnover_in_base_year_cr: Decimal = Field(default=Decimal("100.0"), ge=0)

    # Partnership 40(b) parameters
    firm_book_profit: Decimal = Field(default=Decimal("0.0"), ge=0)
    partner_remuneration_claimed: Decimal = Field(default=Decimal("0.0"), ge=0)
    partner_capital_interest_rate: Decimal = Field(default=Decimal("12.0"), ge=0)
    partner_capital_amount: Decimal = Field(default=Decimal("0.0"), ge=0)


class EntityTaxResult(BaseModel):
    entity_type: EntityType
    base_tax_rate: Decimal
    base_tax: Decimal
    surcharge_rate: Decimal
    surcharge_amount: Decimal
    cess_amount: Decimal
    total_normal_tax_liability: Decimal

    # MAT / AMT fields
    is_mat_applicable: bool
    mat_amount: Decimal
    final_tax_payable: Decimal
    mat_credit_generated: Decimal

    # Partnership 40(b)
    partner_remuneration_allowed_40b: Decimal
    partner_interest_disallowed: Decimal
    notes: list[str]


class IndiaEntityTaxEngine:
    """Computes corporate and entity tax liabilities under the Income-tax Act, 1961."""

    def calculate_entity_tax(  # noqa: PLR0912, PLR0915
        self, inputs: EntityTaxInputs, tax_year: str = "2024-25"
    ) -> tuple[EntityTaxResult, StandardTaxCalculationResponse]:
        income = inputs.taxable_income
        steps: list[ExplanationStep] = []
        warnings: list[str] = []
        step_num = 1

        base_tax = Decimal("0.00")
        base_rate = Decimal("0.00")
        surcharge_rate = Decimal("0.00")
        is_mat = False
        mat_amount = Decimal("0.00")
        mat_credit = Decimal("0.00")
        remun_allowed = Decimal("0.00")
        interest_disallowed = Decimal("0.00")

        # 1. Base Tax Rate Selection
        if inputs.entity_type == EntityType.DOMESTIC_COMPANY_115BAA:
            base_rate = Decimal("0.22")  # 22%
            surcharge_rate = Decimal("0.10")  # Flat 10%
            is_mat = False
            base_tax = income * base_rate
        elif inputs.entity_type == EntityType.DOMESTIC_COMPANY_115BAB:
            base_rate = Decimal("0.15")  # 15%
            surcharge_rate = Decimal("0.10")  # Flat 10%
            is_mat = False
            base_tax = income * base_rate
        elif inputs.entity_type == EntityType.DOMESTIC_COMPANY_STANDARD:
            # 25% if base turnover <= ₹400 Cr, else 30%
            base_rate = (
                Decimal("0.25")
                if inputs.turnover_in_base_year_cr <= Decimal("400.0")
                else Decimal("0.30")
            )
            base_tax = income * base_rate
            # Surcharge: 7% if income > 1 Cr <= 10 Cr, 12% if > 10 Cr
            if income > Decimal("100000000.00"):  # 10 Cr
                surcharge_rate = Decimal("0.12")
            elif income > Decimal("10000000.00"):  # 1 Cr
                surcharge_rate = Decimal("0.07")
            is_mat = True
        elif inputs.entity_type == EntityType.FOREIGN_COMPANY:
            # 35% from AY 2025-26, 40% previously
            base_rate = (
                Decimal("0.35") if int(tax_year[:4]) >= 2024 else Decimal("0.40")  # noqa: PLR2004
            )
            base_tax = income * base_rate
            if income > Decimal("100000000.00"):
                surcharge_rate = Decimal("0.05")
            elif income > Decimal("10000000.00"):
                surcharge_rate = Decimal("0.02")
            is_mat = True
        elif inputs.entity_type == EntityType.PARTNERSHIP_FIRM_OR_LLP:
            base_rate = Decimal("0.30")  # 30%
            base_tax = income * base_rate
            if income > Decimal("10000000.00"):  # 1 Cr
                surcharge_rate = Decimal("0.12")
            is_mat = False

            # Section 40(b) calculation
            # Book profit rules:
            bp = inputs.firm_book_profit
            if bp <= Decimal("300000.00"):
                max_remun = max(Decimal("150000.00"), bp * Decimal("0.90"))
            else:
                max_remun = Decimal("270000.00") + ((bp - Decimal("300000.00")) * Decimal("0.60"))
            remun_allowed = min(inputs.partner_remuneration_claimed, max_remun)

            # Partner interest: max 12% p.a.
            if inputs.partner_capital_interest_rate > Decimal("12.0"):
                excess_rate = inputs.partner_capital_interest_rate - Decimal("12.0")
                interest_disallowed = inputs.partner_capital_amount * (
                    excess_rate / Decimal("100.0")
                )

        steps.append(
            ExplanationStep(
                step_number=step_num,
                label=f"Base Income Tax ({base_rate * 100}%)",
                formula_or_rule="Taxable Income * Base Rate",
                inputs={"taxable_income": str(income), "entity_type": inputs.entity_type.value},
                applied_rate_or_limit=base_rate,
                result=apply_bankers_rounding(base_tax),
                notes=f"Statutory corporate/entity base rate for {inputs.entity_type.value}.",
            )
        )
        step_num += 1

        surcharge_amount = base_tax * surcharge_rate
        steps.append(
            ExplanationStep(
                step_number=step_num,
                label=f"Surcharge ({surcharge_rate * 100}%)",
                formula_or_rule="Base Tax * Surcharge Rate",
                inputs={"surcharge_rate": str(surcharge_rate)},
                applied_rate_or_limit=surcharge_rate,
                result=apply_bankers_rounding(surcharge_amount),
                notes="Statutory surcharge on corporate/entity tax.",
            )
        )
        step_num += 1

        tax_and_surcharge = base_tax + surcharge_amount
        cess_amount = tax_and_surcharge * Decimal("0.04")
        normal_tax = tax_and_surcharge + cess_amount

        steps.append(
            ExplanationStep(
                step_number=step_num,
                label="Health & Education Cess (4%)",
                formula_or_rule="(Base Tax + Surcharge) * 4%",
                inputs={"tax_and_surcharge": str(tax_and_surcharge)},
                applied_rate_or_limit=Decimal("0.04"),
                result=apply_bankers_rounding(cess_amount),
                notes="Mandatory 4% statutory cess.",
            )
        )
        step_num += 1

        # MAT Calculation u/s 115JB (15% on Book Profits)
        final_payable = normal_tax
        if is_mat and inputs.book_profits_for_mat > 0:
            mat_base = inputs.book_profits_for_mat * Decimal("0.15")
            mat_surcharge = mat_base * surcharge_rate
            mat_cess = (mat_base + mat_surcharge) * Decimal("0.04")
            mat_amount = mat_base + mat_surcharge + mat_cess

            if mat_amount > normal_tax:
                final_payable = mat_amount
                mat_credit = mat_amount - normal_tax
                warnings.append(
                    f"MAT liability (₹{mat_amount}) exceeds normal tax liability (₹{normal_tax}). MAT applies. ₹{mat_credit} MAT credit generated u/s 115JAA."
                )

        res = EntityTaxResult(
            entity_type=inputs.entity_type,
            base_tax_rate=base_rate,
            base_tax=apply_bankers_rounding(base_tax),
            surcharge_rate=surcharge_rate,
            surcharge_amount=apply_bankers_rounding(surcharge_amount),
            cess_amount=apply_bankers_rounding(cess_amount),
            total_normal_tax_liability=apply_bankers_rounding(normal_tax),
            is_mat_applicable=is_mat,
            mat_amount=apply_bankers_rounding(mat_amount),
            final_tax_payable=apply_bankers_rounding(final_payable),
            mat_credit_generated=apply_bankers_rounding(mat_credit),
            partner_remuneration_allowed_40b=apply_bankers_rounding(remun_allowed),
            partner_interest_disallowed=apply_bankers_rounding(interest_disallowed),
            notes=warnings,
        )

        trace_response = StandardTaxCalculationResponse(
            jurisdiction="IN",
            tax_type="corporate_entity_tax",
            tax_year=tax_year,
            assessment_year=f"{int(tax_year[:4]) + 1}-{str(int(tax_year[:4]) + 2)[2:]}",
            effective_date=f"{tax_year[:4]}-04-01",
            rule_version=f"IN-CORP-{tax_year}.1",
            taxpayer_type=inputs.entity_type.value,
            inputs=inputs.model_dump(),
            calculation={
                "base_tax": str(res.base_tax),
                "surcharge": str(res.surcharge_amount),
                "cess": str(res.cess_amount),
                "normal_tax": str(res.total_normal_tax_liability),
                "final_tax_payable": str(res.final_tax_payable),
                "mat_credit_generated": str(res.mat_credit_generated),
            },
            steps=steps,
            warnings=warnings,
            assumptions=[
                "Companies opting for Section 115BAA/115BAB are permanently exempt from Minimum Alternate Tax (MAT)."
            ],
            official_sources=[
                OfficialSourceReference(
                    source_id="IN-ACT-CORP",
                    title="Special provisions relating to certain domestic companies & firms",
                    section_or_rule="Sections 115BAA, 115BAB, 115JB, 40(b)",
                    act_name="Income-tax Act, 1961",
                    url="https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx",
                    effective_date=f"{tax_year[:4]}-04-01",
                )
            ],
        )

        return res, trace_response
