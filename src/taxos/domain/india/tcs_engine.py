"""India Tax Collected at Source (TCS) Engine (Section 206C)."""

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


class TCSCategory(StrEnum):
    MOTOR_VEHICLE_1F = "206C(1F)_motor_vehicle"
    LRS_OVERSEAS_TOUR_PACKAGE = "206C(1G)_tour_package"
    LRS_EDUCATION_MEDICAL = "206C(1G)_education_medical"
    LRS_EDUCATION_LOAN = "206C(1G)_education_loan"
    LRS_OTHER_REMITTANCE = "206C(1G)_other_remittance"
    SALE_OF_GOODS_1H = "206C(1H)_goods_above_50l"
    SCRAP_1 = "206C(1)_scrap"
    MINERALS_1 = "206C(1)_minerals"
    TENDU_LEAVES_1 = "206C(1)_tendu_leaves"
    TIMBER_1 = "206C(1)_timber"
    ALCOHOLIC_LIQUOR_1 = "206C(1)_liquor"


class TCSInputs(BaseModel):
    category: TCSCategory = TCSCategory.MOTOR_VEHICLE_1F
    transaction_amount: Decimal = Field(ge=0)
    cumulative_amount_financial_year: Decimal = Field(default=Decimal("0.0"), ge=0)
    has_valid_pan: bool = True
    seller_preceding_fy_turnover_above_10cr: bool = True
    is_tds_194q_deducted_by_buyer: bool = False


class TCSResult(BaseModel):
    category: TCSCategory
    section_code: str
    taxable_amount: Decimal
    applicable_tcs_rate: Decimal
    is_penalty_rate_applied_206cc: bool
    tcs_amount: Decimal
    threshold_limit: Decimal
    notes: list[str]


class IndiaTCSEngine:
    """Computes Tax Collected at Source under Section 206C of the Income-tax Act, 1961."""

    def calculate_tcs(  # noqa: PLR0912, PLR0915
        self, inputs: TCSInputs, tax_year: str = "2024-25"
    ) -> tuple[TCSResult, StandardTaxCalculationResponse]:
        steps: list[ExplanationStep] = []
        warnings: list[str] = []
        step_num = 1

        tcs_amount = Decimal("0.00")
        taxable_amount = Decimal("0.00")
        base_rate = Decimal("0.00")
        penalty_applied = False
        threshold = Decimal("0.00")
        section = "206C"

        if inputs.category == TCSCategory.MOTOR_VEHICLE_1F:
            section = "206C(1F)"
            threshold = Decimal("1000000.00")
            base_rate = Decimal("0.01")  # 1%
            if inputs.transaction_amount > threshold:
                taxable_amount = inputs.transaction_amount
                tcs_amount = taxable_amount * base_rate
            else:
                warnings.append(
                    "Vehicle value does not exceed ₹10,00,000 threshold. No TCS applicable."
                )

        elif inputs.category == TCSCategory.LRS_OVERSEAS_TOUR_PACKAGE:
            section = "206C(1G)"
            threshold = Decimal("700000.00")
            # 5% up to ₹7 Lakhs, 20% on excess
            total_cum = inputs.cumulative_amount_financial_year + inputs.transaction_amount
            if total_cum <= threshold:
                base_rate = Decimal("0.05")
                taxable_amount = inputs.transaction_amount
                tcs_amount = inputs.transaction_amount * Decimal("0.05")
            elif inputs.cumulative_amount_financial_year >= threshold:
                base_rate = Decimal("0.20")
                taxable_amount = inputs.transaction_amount
                tcs_amount = inputs.transaction_amount * Decimal("0.20")
            else:
                # Straddles ₹7L boundary
                portion_5pct = threshold - inputs.cumulative_amount_financial_year
                portion_20pct = inputs.transaction_amount - portion_5pct
                tcs_amount = (portion_5pct * Decimal("0.05")) + (portion_20pct * Decimal("0.20"))
                taxable_amount = inputs.transaction_amount
                base_rate = Decimal("0.20")

        elif inputs.category == TCSCategory.LRS_EDUCATION_MEDICAL:
            section = "206C(1G)"
            threshold = Decimal("700000.00")
            total_cum = inputs.cumulative_amount_financial_year + inputs.transaction_amount
            if total_cum > threshold:
                taxable_portion = max(
                    Decimal("0.00"),
                    total_cum - max(threshold, inputs.cumulative_amount_financial_year),
                )
                taxable_amount = taxable_portion
                base_rate = Decimal("0.05")
                tcs_amount = taxable_portion * Decimal("0.05")
            else:
                warnings.append(
                    "Cumulative LRS remittance is within ₹7,00,000 annual exemption limit."
                )

        elif inputs.category == TCSCategory.LRS_EDUCATION_LOAN:
            section = "206C(1G)"
            threshold = Decimal("700000.00")
            total_cum = inputs.cumulative_amount_financial_year + inputs.transaction_amount
            if total_cum > threshold:
                taxable_portion = max(
                    Decimal("0.00"),
                    total_cum - max(threshold, inputs.cumulative_amount_financial_year),
                )
                taxable_amount = taxable_portion
                base_rate = Decimal("0.005")  # 0.5%
                tcs_amount = taxable_portion * Decimal("0.005")

        elif inputs.category == TCSCategory.LRS_OTHER_REMITTANCE:
            section = "206C(1G)"
            threshold = Decimal("700000.00")
            total_cum = inputs.cumulative_amount_financial_year + inputs.transaction_amount
            if total_cum > threshold:
                taxable_portion = max(
                    Decimal("0.00"),
                    total_cum - max(threshold, inputs.cumulative_amount_financial_year),
                )
                taxable_amount = taxable_portion
                base_rate = Decimal("0.20")  # 20%
                tcs_amount = taxable_portion * Decimal("0.20")
            else:
                warnings.append("Cumulative LRS remittance is within ₹7,00,000 exemption limit.")

        elif inputs.category == TCSCategory.SALE_OF_GOODS_1H:
            section = "206C(1H)"
            threshold = Decimal("5000000.00")
            base_rate = Decimal("0.001")  # 0.1%
            if inputs.is_tds_194q_deducted_by_buyer:
                warnings.append(
                    "TDS deducted by buyer under Section 194Q takes precedence. No TCS u/s 206C(1H) collected."
                )
                taxable_amount = Decimal("0.00")
                tcs_amount = Decimal("0.00")
            elif not inputs.seller_preceding_fy_turnover_above_10cr:
                warnings.append(
                    "Seller turnover in preceding FY is below ₹10 Crore threshold. Section 206C(1H) does not apply."
                )
            else:
                total_cum = inputs.cumulative_amount_financial_year + inputs.transaction_amount
                if total_cum > threshold:
                    taxable_portion = max(
                        Decimal("0.00"),
                        total_cum - max(threshold, inputs.cumulative_amount_financial_year),
                    )
                    taxable_amount = taxable_portion
                    tcs_amount = taxable_portion * base_rate

        elif inputs.category in (TCSCategory.SCRAP_1, TCSCategory.MINERALS_1):
            section = "206C(1)"
            base_rate = Decimal("0.01")
            taxable_amount = inputs.transaction_amount
            tcs_amount = taxable_amount * base_rate

        elif inputs.category == TCSCategory.TENDU_LEAVES_1:
            section = "206C(1)"
            base_rate = Decimal("0.05")
            taxable_amount = inputs.transaction_amount
            tcs_amount = taxable_amount * base_rate

        elif inputs.category == TCSCategory.TIMBER_1:
            section = "206C(1)"
            base_rate = Decimal("0.025")
            taxable_amount = inputs.transaction_amount
            tcs_amount = taxable_amount * base_rate

        elif inputs.category == TCSCategory.ALCOHOLIC_LIQUOR_1:
            section = "206C(1)"
            base_rate = Decimal("0.01")
            taxable_amount = inputs.transaction_amount
            tcs_amount = taxable_amount * base_rate

        # Penalty rate under Section 206CC for Non-PAN
        effective_rate = base_rate
        if not inputs.has_valid_pan and taxable_amount > 0:
            penalty_applied = True
            if inputs.category == TCSCategory.SALE_OF_GOODS_1H:
                effective_rate = Decimal("0.01")  # 1% for 206C(1H)
            else:
                effective_rate = max(base_rate * Decimal("2.0"), Decimal("0.05"))
            tcs_amount = taxable_amount * effective_rate
            warnings.append(
                f"Section 206CC penalty rate of {effective_rate * 100}% applied due to absence/invalidity of PAN."
            )

        steps.append(
            ExplanationStep(
                step_number=step_num,
                label=f"Tax Collected at Source u/s {section}",
                formula_or_rule=f"Taxable Amount * Rate ({effective_rate * 100}%)",
                inputs={
                    "transaction_amount": str(inputs.transaction_amount),
                    "taxable_amount": str(taxable_amount),
                    "has_valid_pan": str(inputs.has_valid_pan),
                },
                applied_rate_or_limit=effective_rate,
                result=apply_bankers_rounding(tcs_amount),
                notes=f"Statutory Section {section} TCS collection.",
            )
        )

        res = TCSResult(
            category=inputs.category,
            section_code=section,
            taxable_amount=apply_bankers_rounding(taxable_amount),
            applicable_tcs_rate=effective_rate,
            is_penalty_rate_applied_206cc=penalty_applied,
            tcs_amount=apply_bankers_rounding(tcs_amount),
            threshold_limit=apply_bankers_rounding(threshold),
            notes=warnings,
        )

        trace_response = StandardTaxCalculationResponse(
            jurisdiction="IN",
            tax_type="tcs_collection",
            tax_year=tax_year,
            assessment_year=f"{int(tax_year[:4]) + 1}-{str(int(tax_year[:4]) + 2)[2:]}",
            effective_date=f"{tax_year[:4]}-04-01",
            rule_version=f"IN-TCS-{tax_year}.1",
            taxpayer_type="collector_seller",
            inputs=inputs.model_dump(),
            calculation={
                "section": res.section_code,
                "taxable_amount": str(res.taxable_amount),
                "tcs_rate": str(res.applicable_tcs_rate),
                "tcs_collected": str(res.tcs_amount),
            },
            steps=steps,
            warnings=warnings,
            assumptions=[
                "TCS collected is credited to the buyer's Form 26AS/AIS and can be claimed against final income tax liability."
            ],
            official_sources=[
                OfficialSourceReference(
                    source_id="IN-ACT-TCS",
                    title="Profits and gains from the business of trading in alcoholic liquor, forest produce, scrap, etc.",
                    section_or_rule="Section 206C, Section 206CC",
                    act_name="Income-tax Act, 1961",
                    url="https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx",
                    effective_date=f"{tax_year[:4]}-04-01",
                )
            ],
        )

        return res, trace_response
