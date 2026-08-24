"""Presumptive Business & Professional Income Engine (Section 44AD, 44ADA, 44AE)."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class PresumptiveSchemeType(StrEnum):
    """Statutory presumptive taxation sections."""

    SEC_44AD_BUSINESS = "44AD"
    SEC_44ADA_PROFESSIONAL = "44ADA"
    SEC_44AE_TRANSPORTER = "44AE"


class PresumptiveTaxInput(BaseModel):
    """Input parameters for presumptive taxation schemes."""

    scheme_type: PresumptiveSchemeType
    assessment_year: str = "2025-26"
    digital_turnover_or_receipts: Decimal = Field(default=Decimal("0.0"), ge=0)
    cash_turnover_or_receipts: Decimal = Field(default=Decimal("0.0"), ge=0)
    declared_profit: Decimal | None = Field(
        default=None, ge=0, description="Optional higher profit declared by taxpayer"
    )
    heavy_goods_vehicles_count: int = 0
    other_goods_vehicles_count: int = 0
    months_operated: int = 12


class PresumptiveTaxResult(BaseModel):
    """Calculation result for presumptive business income."""

    total_turnover_or_receipts: Decimal
    digital_turnover_percentage: Decimal
    is_higher_turnover_threshold_eligible: bool
    minimum_presumed_income: Decimal
    taxable_business_income: Decimal
    explanation: str


class IndiaPresumptiveTaxEngine:
    """Engine computing deemed business and professional income u/s 44AD, 44ADA, 44AE."""

    def calculate_presumptive_income(self, payload: PresumptiveTaxInput) -> PresumptiveTaxResult:
        """Calculate minimum deemed taxable income under Section 44AD, 44ADA, or 44AE."""
        total_turnover = payload.digital_turnover_or_receipts + payload.cash_turnover_or_receipts
        digital_pct = (
            (payload.digital_turnover_or_receipts / total_turnover) * Decimal("100.0")
            if total_turnover > Decimal("0.0")
            else Decimal("0.0")
        )
        is_high_threshold = digital_pct >= Decimal("95.0")

        if payload.scheme_type == PresumptiveSchemeType.SEC_44AD_BUSINESS:
            # 6% on digital, 8% on cash
            digital_profit = payload.digital_turnover_or_receipts * Decimal("0.06")
            cash_profit = payload.cash_turnover_or_receipts * Decimal("0.08")
            min_profit = (digital_profit + cash_profit).quantize(Decimal("1.0"))
            chosen_profit = max(min_profit, payload.declared_profit or min_profit)
            explanation = (
                f"Section 44AD: Deemed profit of 6% (₹{digital_profit:,.2f}) on digital receipts "
                f"and 8% (₹{cash_profit:,.2f}) on cash receipts."
            )

        elif payload.scheme_type == PresumptiveSchemeType.SEC_44ADA_PROFESSIONAL:
            # 50% on gross receipts
            min_profit = (total_turnover * Decimal("0.50")).quantize(Decimal("1.0"))
            chosen_profit = max(min_profit, payload.declared_profit or min_profit)
            explanation = f"Section 44ADA: Deemed professional profit of 50% on gross receipts of ₹{total_turnover:,.2f}."

        else:
            # 44AE: ₹7,500 per month per light vehicle, ₹1,000 per ton per month for heavy vehicles
            light_profit = Decimal(
                str(payload.other_goods_vehicles_count * 7500 * payload.months_operated)
            )
            heavy_profit = Decimal(
                str(payload.heavy_goods_vehicles_count * 12000 * payload.months_operated)
            )
            min_profit = light_profit + heavy_profit
            chosen_profit = max(min_profit, payload.declared_profit or min_profit)
            explanation = f"Section 44AE: Deemed vehicle transporter income for {payload.months_operated} months."

        return PresumptiveTaxResult(
            total_turnover_or_receipts=total_turnover,
            digital_turnover_percentage=digital_pct,
            is_higher_turnover_threshold_eligible=is_high_threshold,
            minimum_presumed_income=min_profit,
            taxable_business_income=chosen_profit,
            explanation=explanation,
        )
