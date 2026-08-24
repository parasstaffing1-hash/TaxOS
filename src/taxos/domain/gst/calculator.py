"""India GST Calculation Engine (Inclusive, Exclusive, Reverse & Multi-Rate)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from taxos.domain.gst.models import GSTCalculationResult, SupplyType


def round_cur(val: Decimal) -> Decimal:
    """Standard 2-decimal rounding for monetary amounts."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class IndiaGSTEngine:
    """Enterprise computation engine for Indian Goods and Services Tax."""

    def calculate_exclusive(
        self,
        taxable_value: Decimal,
        gst_rate: Decimal,
        supply_type: SupplyType = SupplyType.INTRA_STATE,
        cess_rate: Decimal = Decimal("0.0"),
        is_union_territory: bool = False,
    ) -> GSTCalculationResult:
        """Calculate GST added on top of a net taxable value (Exclusive Calculation)."""
        taxable = round_cur(taxable_value)
        rate_percent = round_cur(gst_rate * Decimal("100.0"))

        cgst_rate = Decimal("0.0")
        cgst_amt = Decimal("0.0")
        sgst_rate = Decimal("0.0")
        sgst_amt = Decimal("0.0")
        igst_rate = Decimal("0.0")
        igst_amt = Decimal("0.0")
        utgst_rate = Decimal("0.0")
        utgst_amt = Decimal("0.0")

        if supply_type == SupplyType.INTRA_STATE:
            half_rate = gst_rate / Decimal("2.0")
            half_percent = rate_percent / Decimal("2.0")
            cgst_rate = half_percent
            cgst_amt = round_cur(taxable * half_rate)

            if is_union_territory:
                utgst_rate = half_percent
                utgst_amt = round_cur(taxable * half_rate)
            else:
                sgst_rate = half_percent
                sgst_amt = round_cur(taxable * half_rate)

            total_gst = cgst_amt + sgst_amt + utgst_amt
        elif supply_type == SupplyType.INTER_STATE:
            igst_rate = rate_percent
            igst_amt = round_cur(taxable * gst_rate)
            total_gst = igst_amt
        elif supply_type == SupplyType.EXPORT_WITH_LUT:
            total_gst = Decimal("0.0")
        else:  # EXPORT_WITH_TAX
            igst_rate = rate_percent
            igst_amt = round_cur(taxable * gst_rate)
            total_gst = igst_amt

        cess_amt = round_cur(taxable * cess_rate)
        gross_total = taxable + total_gst + cess_amt

        # Round off to nearest whole rupee per Section 170
        net_payable = gross_total.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        round_off = net_payable - gross_total

        explanation = (
            f"Taxable: ₹{taxable:,.2f} + GST @ {rate_percent}% (₹{total_gst:,.2f}) = Gross: ₹{gross_total:,.2f}. "
            f"Net Payable (rounded): ₹{net_payable:,.0f}."
        )

        return GSTCalculationResult(
            taxable_value=taxable,
            gst_rate_percent=rate_percent,
            supply_type=supply_type,
            cgst_rate_percent=cgst_rate,
            cgst_amount=cgst_amt,
            sgst_rate_percent=sgst_rate,
            sgst_amount=sgst_amt,
            igst_rate_percent=igst_rate,
            igst_amount=igst_amt,
            utgst_rate_percent=utgst_rate,
            utgst_amount=utgst_amt,
            cess_amount=cess_amt,
            total_gst_amount=total_gst + cess_amt,
            gross_invoice_amount=gross_total,
            round_off_adjustment=round_off,
            net_payable_amount=net_payable,
            is_inclusive_calculation=False,
            explanation=explanation,
        )

    def calculate_inclusive(
        self,
        gross_amount: Decimal,
        gst_rate: Decimal,
        supply_type: SupplyType = SupplyType.INTRA_STATE,
        cess_rate: Decimal = Decimal("0.0"),
        is_union_territory: bool = False,
    ) -> GSTCalculationResult:
        """Extract base taxable value and GST from an inclusive MRP/Gross amount."""
        gross = round_cur(gross_amount)
        rate_percent = round_cur(gst_rate * Decimal("100.0"))

        # Inclusive base uses the combined GST and compensation-cess divisor.
        divisor = Decimal("1.0") + gst_rate + cess_rate
        taxable = (gross / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_tax_extracted = gross - taxable

        cgst_rate = Decimal("0.0")
        cgst_amt = Decimal("0.0")
        sgst_rate = Decimal("0.0")
        sgst_amt = Decimal("0.0")
        igst_rate = Decimal("0.0")
        igst_amt = Decimal("0.0")
        utgst_rate = Decimal("0.0")
        utgst_amt = Decimal("0.0")

        cess_amt = (taxable * cess_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        pure_gst = total_tax_extracted - cess_amt

        if supply_type == SupplyType.INTRA_STATE:
            half_percent = rate_percent / Decimal("2.0")
            cgst_rate = half_percent
            cgst_amt = (pure_gst / Decimal("2.0")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            if is_union_territory:
                utgst_rate = half_percent
                utgst_amt = pure_gst - cgst_amt
            else:
                sgst_rate = half_percent
                sgst_amt = pure_gst - cgst_amt
        else:
            igst_rate = rate_percent
            igst_amt = pure_gst

        explanation = (
            f"From Inclusive MRP ₹{gross:,.2f} at {rate_percent}% GST: "
            f"Extracted Taxable Value = ₹{taxable:,.2f}, Total Tax = ₹{total_tax_extracted:,.2f}."
        )

        return GSTCalculationResult(
            taxable_value=taxable,
            gst_rate_percent=rate_percent,
            supply_type=supply_type,
            cgst_rate_percent=cgst_rate,
            cgst_amount=cgst_amt,
            sgst_rate_percent=sgst_rate,
            sgst_amount=sgst_amt,
            igst_rate_percent=igst_rate,
            igst_amount=igst_amt,
            utgst_rate_percent=utgst_rate,
            utgst_amount=utgst_amt,
            cess_amount=cess_amt,
            total_gst_amount=total_tax_extracted,
            gross_invoice_amount=gross,
            round_off_adjustment=Decimal("0.0"),
            net_payable_amount=gross,
            is_inclusive_calculation=True,
            explanation=explanation,
        )
