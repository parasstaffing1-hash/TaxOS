"""India Business & Presumptive Taxation Engine (Sections 44AD, 44ADA, 44AE, 44AB, 43B(h))."""

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


class PresumptiveSchemeType(StrEnum):
    SEC_44AD_BUSINESS = "44AD"
    SEC_44ADA_PROFESSION = "44ADA"
    SEC_44AE_TRANSPORTER = "44AE"
    REGULAR_PGBP = "regular_pgbp"


class BusinessTaxInputs(BaseModel):
    scheme_type: PresumptiveSchemeType = PresumptiveSchemeType.SEC_44AD_BUSINESS
    gross_turnover_digital: Decimal = Field(default=Decimal("0.0"), ge=0)
    gross_turnover_cash: Decimal = Field(default=Decimal("0.0"), ge=0)
    actual_net_profit_declared: Decimal = Field(default=Decimal("0.0"), ge=0)

    # 44AE Vehicles
    num_heavy_goods_vehicles: int = Field(default=0, ge=0)
    heavy_vehicle_avg_gross_tonnage: Decimal = Field(default=Decimal("0.0"), ge=0)
    heavy_vehicle_operating_months: int = Field(default=12, ge=0, le=12)
    num_other_goods_vehicles: int = Field(default=0, ge=0)
    other_vehicle_operating_months: int = Field(default=12, ge=0, le=12)

    # 43B(h) MSME Disallowances
    msme_overdue_payments_unpaid_at_year_end: Decimal = Field(default=Decimal("0.0"), ge=0)

    # Other Disallowances
    sec_40a3_cash_payments_exceeding_10k: Decimal = Field(default=Decimal("0.0"), ge=0)
    sec_40a_ia_tds_default_expenses: Decimal = Field(
        default=Decimal("0.0"), ge=0
    )  # 30% disallowed


class BusinessTaxResult(BaseModel):
    total_turnover_or_receipts: Decimal
    is_digital_threshold_met_95pct: bool
    presumptive_turnover_limit: Decimal
    is_eligible_for_presumptive: bool
    statutory_minimum_presumptive_profit: Decimal
    taxable_business_profit: Decimal
    tax_audit_required_sec_44ab: bool
    msme_disallowance_sec_43bh: Decimal
    other_disallowances_added_back: Decimal
    notes: list[str]


class IndiaBusinessTaxEngine:
    """Computes business income, presumptive profits, and audit requirements under PGBP."""

    def calculate_business_tax(  # noqa: PLR0915
        self, inputs: BusinessTaxInputs, tax_year: str = "2024-25"
    ) -> tuple[BusinessTaxResult, StandardTaxCalculationResponse]:
        total_turnover = inputs.gross_turnover_digital + inputs.gross_turnover_cash
        steps: list[ExplanationStep] = []
        warnings: list[str] = []
        step_num = 1

        is_95_pct_digital = (
            (inputs.gross_turnover_digital / total_turnover) >= Decimal("0.95")
            if total_turnover > 0
            else True
        )

        min_profit = Decimal("0.00")
        is_eligible = True
        limit = Decimal("0.00")
        audit_required = False

        if inputs.scheme_type == PresumptiveSchemeType.SEC_44AD_BUSINESS:
            # 44AD: ₹2 Crore standard, increased to ₹3 Crore if cash receipts <= 5%
            limit = Decimal("30000000.00") if is_95_pct_digital else Decimal("20000000.00")
            is_eligible = total_turnover <= limit

            digital_profit = inputs.gross_turnover_digital * Decimal("0.06")
            cash_profit = inputs.gross_turnover_cash * Decimal("0.08")
            min_profit = digital_profit + cash_profit

            steps.append(
                ExplanationStep(
                    step_number=step_num,
                    label="Section 44AD Presumptive Business Profit",
                    formula_or_rule="6% on Digital Receipts + 8% on Cash Receipts",
                    inputs={
                        "digital_turnover": str(inputs.gross_turnover_digital),
                        "cash_turnover": str(inputs.gross_turnover_cash),
                    },
                    applied_rate_or_limit=limit,
                    result=apply_bankers_rounding(min_profit),
                    notes="Eligible for turnover up to ₹3 Crore (when 95%+ digital).",
                )
            )
            step_num += 1

            if not is_eligible:
                warnings.append(
                    f"Turnover ₹{total_turnover} exceeds Section 44AD limit of ₹{limit}. Regular books & audit apply."
                )
                audit_required = True

            # If assessee declares lower than 6%/8% and income exceeds basic exemption
            taxable_profit = max(min_profit, inputs.actual_net_profit_declared)
            if (
                inputs.actual_net_profit_declared > 0
                and inputs.actual_net_profit_declared < min_profit
            ):
                warnings.append(
                    "Declared profit is below statutory presumptive rate (6%/8%). Tax audit u/s 44AB(e) is mandatory."
                )
                audit_required = True

        elif inputs.scheme_type == PresumptiveSchemeType.SEC_44ADA_PROFESSION:
            # 44ADA: ₹50 Lakhs standard, increased to ₹75 Lakhs if cash receipts <= 5%
            limit = Decimal("7500000.00") if is_95_pct_digital else Decimal("5000000.00")
            is_eligible = total_turnover <= limit
            min_profit = total_turnover * Decimal("0.50")

            steps.append(
                ExplanationStep(
                    step_number=step_num,
                    label="Section 44ADA Presumptive Professional Profit",
                    formula_or_rule="50% of Gross Professional Receipts",
                    inputs={"gross_receipts": str(total_turnover)},
                    applied_rate_or_limit=limit,
                    result=apply_bankers_rounding(min_profit),
                    notes="Eligible for specified professionals with receipts up to ₹75 Lakhs (when 95%+ digital).",
                )
            )
            step_num += 1

            if not is_eligible:
                warnings.append(
                    f"Gross receipts ₹{total_turnover} exceed Section 44ADA limit of ₹{limit}."
                )
                audit_required = True

            taxable_profit = max(min_profit, inputs.actual_net_profit_declared)

        elif inputs.scheme_type == PresumptiveSchemeType.SEC_44AE_TRANSPORTER:
            # 44AE: ₹1,000/ton/month for Heavy Goods Vehicle (> 12 MT), ₹7,500/vehicle/month for other
            heavy_profit = (
                Decimal(str(inputs.num_heavy_goods_vehicles))
                * inputs.heavy_vehicle_avg_gross_tonnage
                * Decimal("1000.00")
                * Decimal(str(inputs.heavy_vehicle_operating_months))
            )
            other_profit = (
                Decimal(str(inputs.num_other_goods_vehicles))
                * Decimal("7500.00")
                * Decimal(str(inputs.other_vehicle_operating_months))
            )
            min_profit = heavy_profit + other_profit
            total_vehicles = inputs.num_heavy_goods_vehicles + inputs.num_other_goods_vehicles
            is_eligible = total_vehicles <= 10  # noqa: PLR2004
            limit = Decimal("10")

            steps.append(
                ExplanationStep(
                    step_number=step_num,
                    label="Section 44AE Goods Carriage Presumptive Profit",
                    formula_or_rule="₹1,000/ton/month (Heavy) + ₹7,500/vehicle/month (Other)",
                    inputs={"heavy_profit": str(heavy_profit), "other_profit": str(other_profit)},
                    applied_rate_or_limit=limit,
                    result=apply_bankers_rounding(min_profit),
                    notes="Available to goods carriage operators owning up to 10 vehicles.",
                )
            )
            step_num += 1

            if not is_eligible:
                warnings.append(
                    "Assessee owns more than 10 goods carriages. Section 44AE does not apply."
                )
                audit_required = True

            taxable_profit = max(min_profit, inputs.actual_net_profit_declared)

        else:
            # Regular PGBP
            taxable_profit = inputs.actual_net_profit_declared
            # Check 44AB threshold: ₹10 Cr if 95% digital, else ₹1 Cr
            audit_limit = Decimal("100000000.00") if is_95_pct_digital else Decimal("10000000.00")
            audit_required = total_turnover > audit_limit
            limit = audit_limit

        # Disallowances
        # 1. Section 43B(h): MSME overdue payments
        msme_disallowance = inputs.msme_overdue_payments_unpaid_at_year_end
        if msme_disallowance > 0:
            warnings.append(
                f"Section 43B(h): ₹{msme_disallowance} overdue to Micro/Small enterprises beyond 45 days is disallowed and added back."
            )

        # 2. Section 40A(3): Cash payments > ₹10,000
        # 3. Section 40(a)(ia): 30% of expense disallowed for TDS default
        tds_disallowance = inputs.sec_40a_ia_tds_default_expenses * Decimal("0.30")
        other_disallowance = inputs.sec_40a3_cash_payments_exceeding_10k + tds_disallowance

        final_taxable_profit = taxable_profit + msme_disallowance + other_disallowance

        res = BusinessTaxResult(
            total_turnover_or_receipts=apply_bankers_rounding(total_turnover),
            is_digital_threshold_met_95pct=is_95_pct_digital,
            presumptive_turnover_limit=apply_bankers_rounding(limit),
            is_eligible_for_presumptive=is_eligible,
            statutory_minimum_presumptive_profit=apply_bankers_rounding(min_profit),
            taxable_business_profit=apply_bankers_rounding(final_taxable_profit),
            tax_audit_required_sec_44ab=audit_required,
            msme_disallowance_sec_43bh=apply_bankers_rounding(msme_disallowance),
            other_disallowances_added_back=apply_bankers_rounding(other_disallowance),
            notes=warnings,
        )

        trace_response = StandardTaxCalculationResponse(
            jurisdiction="IN",
            tax_type="business_pgbp_income",
            tax_year=tax_year,
            assessment_year=f"{int(tax_year[:4]) + 1}-{str(int(tax_year[:4]) + 2)[2:]}",
            effective_date=f"{tax_year[:4]}-04-01",
            rule_version=f"IN-PGBP-{tax_year}.1",
            taxpayer_type="individual_business",
            inputs=inputs.model_dump(),
            calculation={
                "total_turnover": str(res.total_turnover_or_receipts),
                "presumptive_profit": str(res.statutory_minimum_presumptive_profit),
                "taxable_business_profit": str(res.taxable_business_profit),
                "audit_required": str(res.tax_audit_required_sec_44ab),
                "msme_disallowance_43bh": str(res.msme_disallowance_sec_43bh),
            },
            steps=steps,
            warnings=warnings,
            assumptions=[
                "For Section 44AD and 44ADA, 100% of advance tax is payable in a single installment on or before 15th March."
            ],
            official_sources=[
                OfficialSourceReference(
                    source_id="IN-ACT-PGBP",
                    title="Profits and Gains of Business or Profession",
                    section_or_rule="Sections 28, 44AD, 44ADA, 44AE, 44AB, 43B(h)",
                    act_name="Income-tax Act, 1961",
                    url="https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx",
                    effective_date=f"{tax_year[:4]}-04-01",
                )
            ],
        )

        return res, trace_response
