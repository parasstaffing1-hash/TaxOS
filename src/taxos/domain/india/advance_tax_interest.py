"""India Advance Tax, Installments & Sections 234A, 234B, 234C, 234F Interest Engine."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel, Field


class AdvanceTaxInstallment(BaseModel):
    """Quarterly advance tax installment calculation and status."""

    quarter_number: int
    due_date: str
    statutory_cumulative_percent: Decimal
    statutory_required_amount: Decimal
    actual_amount_paid: Decimal
    shortfall_amount: Decimal
    interest_234c: Decimal
    status: str  # "PAID", "SHORTFALL", "PENDING"


class AdvanceTaxInterestResult(BaseModel):
    """Comprehensive calculation result of Advance Tax and Interest penalties."""

    total_tax_assessed: Decimal
    less_tds_tcs_credits: Decimal
    net_assessed_tax: Decimal  # Advance tax liability basis
    is_advance_tax_applicable: bool  # True if net_assessed_tax >= 10,000

    installments: list[AdvanceTaxInstallment]
    total_advance_tax_paid: Decimal

    # Interest penal components
    interest_234a_late_filing: Decimal
    interest_234b_advance_tax_default: Decimal
    interest_234c_deferment_total: Decimal
    late_filing_fee_234f: Decimal
    total_interest_and_fees: Decimal

    grand_total_payable: Decimal
    explanation: list[str] = Field(default_factory=list)


class IndiaAdvanceTaxEngine:
    """Enterprise engine for Indian Advance Tax estimation and statutory interest computations."""

    def calculate_advance_tax_and_interest(  # noqa: PLR0915, PLR0917
        self,
        total_tax_assessed: Decimal,
        tds_tcs_credits: Decimal,
        q1_paid_by_jun15: Decimal = Decimal("0.0"),
        q2_paid_by_sep15: Decimal = Decimal("0.0"),
        q3_paid_by_dec15: Decimal = Decimal("0.0"),
        q4_paid_by_mar15: Decimal = Decimal("0.0"),
        months_delay_filing_234a: int = 0,
        months_delay_payment_234b: int = 0,
        is_return_late_234f: bool = False,
        total_taxable_income: Decimal = Decimal("0.0"),
    ) -> AdvanceTaxInterestResult:
        """Calculate advance tax installments and statutory interest under sections 234A, 234B, 234C, and 234F."""
        net_tax = max(Decimal("0.0"), total_tax_assessed - tds_tcs_credits)
        is_applicable = net_tax >= Decimal("10000.0")

        installments: list[AdvanceTaxInstallment] = []
        int_234c_total = Decimal("0.0")
        notes: list[str] = []

        if not is_applicable:
            notes.append(
                "Advance tax is not mandatory as net tax liability is below ₹10,000 threshold u/s 208."
            )

        # 1. Section 234C Deferment of Installments Calculation:
        # Q1: 15% by 15 June. Safe harbor: if paid >= 12%, no 234C; else 1% per month for 3 months on (15% - paid)
        req_q1 = (net_tax * Decimal("0.15")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        safe_q1 = (net_tax * Decimal("0.12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        shortfall_q1 = max(Decimal("0.0"), req_q1 - q1_paid_by_jun15)
        if is_applicable and q1_paid_by_jun15 < safe_q1:
            int_q1 = (shortfall_q1 * Decimal("0.01") * 3).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            int_q1 = Decimal("0.0")
        int_234c_total += int_q1

        installments.append(
            AdvanceTaxInstallment(
                quarter_number=1,
                due_date="15 June",
                statutory_cumulative_percent=Decimal("0.15"),
                statutory_required_amount=req_q1,
                actual_amount_paid=q1_paid_by_jun15,
                shortfall_amount=shortfall_q1,
                interest_234c=int_q1,
                status="PAID" if q1_paid_by_jun15 >= req_q1 else "SHORTFALL",
            )
        )

        # Q2: 45% cumulative by 15 Sept. Safe harbor: if paid >= 36%, no 234C; else 1% per month for 3 months on (45% - paid)
        cum_paid_q2 = q1_paid_by_jun15 + q2_paid_by_sep15
        req_q2 = (net_tax * Decimal("0.45")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        safe_q2 = (net_tax * Decimal("0.36")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        shortfall_q2 = max(Decimal("0.0"), req_q2 - cum_paid_q2)
        if is_applicable and cum_paid_q2 < safe_q2:
            int_q2 = (shortfall_q2 * Decimal("0.01") * 3).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            int_q2 = Decimal("0.0")
        int_234c_total += int_q2

        installments.append(
            AdvanceTaxInstallment(
                quarter_number=2,
                due_date="15 September",
                statutory_cumulative_percent=Decimal("0.45"),
                statutory_required_amount=req_q2,
                actual_amount_paid=cum_paid_q2,
                shortfall_amount=shortfall_q2,
                interest_234c=int_q2,
                status="PAID" if cum_paid_q2 >= req_q2 else "SHORTFALL",
            )
        )

        # Q3: 75% cumulative by 15 Dec. If paid < 75%, 1% per month for 3 months on (75% - paid)
        cum_paid_q3 = cum_paid_q2 + q3_paid_by_dec15
        req_q3 = (net_tax * Decimal("0.75")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        shortfall_q3 = max(Decimal("0.0"), req_q3 - cum_paid_q3)
        if is_applicable and cum_paid_q3 < req_q3:
            int_q3 = (shortfall_q3 * Decimal("0.01") * 3).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            int_q3 = Decimal("0.0")
        int_234c_total += int_q3

        installments.append(
            AdvanceTaxInstallment(
                quarter_number=3,
                due_date="15 December",
                statutory_cumulative_percent=Decimal("0.75"),
                statutory_required_amount=req_q3,
                actual_amount_paid=cum_paid_q3,
                shortfall_amount=shortfall_q3,
                interest_234c=int_q3,
                status="PAID" if cum_paid_q3 >= req_q3 else "SHORTFALL",
            )
        )

        # Q4: 100% cumulative by 15 March. If paid < 100%, 1% per month for 1 month on (100% - paid)
        cum_paid_q4 = cum_paid_q3 + q4_paid_by_mar15
        req_q4 = net_tax
        shortfall_q4 = max(Decimal("0.0"), req_q4 - cum_paid_q4)
        if is_applicable and cum_paid_q4 < req_q4:
            int_q4 = (shortfall_q4 * Decimal("0.01") * 1).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            int_q4 = Decimal("0.0")
        int_234c_total += int_q4

        installments.append(
            AdvanceTaxInstallment(
                quarter_number=4,
                due_date="15 March",
                statutory_cumulative_percent=Decimal("1.00"),
                statutory_required_amount=req_q4,
                actual_amount_paid=cum_paid_q4,
                shortfall_amount=shortfall_q4,
                interest_234c=int_q4,
                status="PAID" if cum_paid_q4 >= req_q4 else "SHORTFALL",
            )
        )

        total_advance_tax_paid = cum_paid_q4

        # 2. Section 234B Interest (Default in payment of Advance Tax):
        # Triggered if total advance tax paid before 31st March is < 90% of Assessed Tax
        # Interest rate: 1% per month from 1st April of AY to date of payment
        int_234b = Decimal("0.0")
        if is_applicable and total_advance_tax_paid < (net_tax * Decimal("0.90")):
            shortfall_234b = max(Decimal("0.0"), net_tax - total_advance_tax_paid)
            effective_months_b = max(1, months_delay_payment_234b)
            int_234b = (shortfall_234b * Decimal("0.01") * effective_months_b).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            notes.append(
                f"Section 234B interest triggered: Advance tax paid (₹{total_advance_tax_paid:,.0f}) is less than 90% of assessed tax (₹{net_tax * Decimal('0.90'):,.0f})."
            )

        # 3. Section 234A Interest (Delay in filing ITR):
        # Triggered if return is filed after statutory due date (e.g. 31 July) on tax remaining unpaid
        int_234a = Decimal("0.0")
        if months_delay_filing_234a > 0:
            unpaid_tax_at_filing = max(Decimal("0.0"), net_tax - total_advance_tax_paid)
            int_234a = (
                unpaid_tax_at_filing * Decimal("0.01") * months_delay_filing_234a
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            notes.append(
                f"Section 234A interest levied for {months_delay_filing_234a} months delay in return filing."
            )

        # 4. Section 234F Late Filing Fee:
        # ₹5,000 if total income > ₹5,00,000; ₹1,000 if total income <= ₹5,00,000
        fee_234f = Decimal("0.0")
        if is_return_late_234f:
            fee_234f = (
                Decimal("1000.0")
                if total_taxable_income <= Decimal("500000.0")
                else Decimal("5000.0")
            )
            notes.append(f"Section 234F statutory late filing fee of ₹{fee_234f:,.0f} applied.")

        total_interest_fees = int_234a + int_234b + int_234c_total + fee_234f
        remaining_tax = max(Decimal("0.0"), net_tax - total_advance_tax_paid)
        grand_total = remaining_tax + total_interest_fees

        return AdvanceTaxInterestResult(
            total_tax_assessed=total_tax_assessed,
            less_tds_tcs_credits=tds_tcs_credits,
            net_assessed_tax=net_tax,
            is_advance_tax_applicable=is_applicable,
            installments=installments,
            total_advance_tax_paid=total_advance_tax_paid,
            interest_234a_late_filing=int_234a,
            interest_234b_advance_tax_default=int_234b,
            interest_234c_deferment_total=int_234c_total,
            late_filing_fee_234f=fee_234f,
            total_interest_and_fees=total_interest_fees,
            grand_total_payable=grand_total,
            explanation=notes,
        )
