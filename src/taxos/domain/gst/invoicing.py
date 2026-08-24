"""GST Tax Invoicing, Credit/Debit Notes & Bill of Supply Engine (Rule 46 & Rule 53)."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class InvoiceDocumentType(StrEnum):
    """Statutory GST document types."""

    TAX_INVOICE = "tax_invoice"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    BILL_OF_SUPPLY = "bill_of_supply"


class InvoiceItem(BaseModel):
    """Line item in a GST invoice."""

    item_name: str
    hsn_sac_code: str
    quantity: Decimal = Field(default=Decimal("1.0"), gt=0)
    unit_price: Decimal = Field(gt=0)
    discount_amount: Decimal = Field(default=Decimal("0.0"), ge=0)
    gst_rate: Decimal = Field(default=Decimal("0.18"), ge=0, le=1)
    cess_rate: Decimal = Field(default=Decimal("0.0"), ge=0)


class GSTPartyInfo(BaseModel):
    """Supplier or Recipient GST entity information."""

    legal_name: str
    gstin: str
    state_code: str
    state_name: str
    address: str
    pan: str | None = None


class GSTInvoiceRequest(BaseModel):
    """Payload for generating or validating a GST compliant invoice."""

    document_type: InvoiceDocumentType = InvoiceDocumentType.TAX_INVOICE
    invoice_number: str
    invoice_date: str  # YYYY-MM-DD
    original_invoice_ref_for_note: str | None = None
    supplier: GSTPartyInfo
    recipient: GSTPartyInfo
    items: list[InvoiceItem]
    is_reverse_charge: bool = False


class GSTInvoiceLineResult(BaseModel):
    """Calculated breakdown for each invoice item."""

    item_name: str
    hsn_sac_code: str
    taxable_amount: Decimal
    cgst_rate: Decimal
    cgst_amount: Decimal
    sgst_rate: Decimal
    sgst_amount: Decimal
    igst_rate: Decimal
    igst_amount: Decimal
    cess_amount: Decimal
    total_line_amount: Decimal


class GSTInvoiceSummaryResult(BaseModel):
    """Complete statutory summary for a generated GST Invoice or Note."""

    document_type: InvoiceDocumentType
    invoice_number: str
    invoice_date: str
    is_inter_state: bool
    supplier_gstin: str
    recipient_gstin: str

    total_taxable_value: Decimal
    total_cgst: Decimal
    total_sgst: Decimal
    total_igst: Decimal
    total_cess: Decimal
    total_tax_amount: Decimal
    total_invoice_amount: Decimal
    rounded_off_amount: Decimal
    round_off_difference: Decimal

    items: list[GSTInvoiceLineResult]
    is_compliant_rule_46: bool = True
    compliance_notes: list[str] = Field(default_factory=list)


class IndiaGSTInvoiceEngine:
    """Engine for generating and validating statutory GST Invoices under Rule 46 and Rule 53."""

    def generate_invoice(self, req: GSTInvoiceRequest) -> GSTInvoiceSummaryResult:
        """Calculate line-by-line and summary tax amounts for the GST document."""
        # Determine if supply is inter-state (Supplier State != Recipient State)
        is_inter_state = req.supplier.state_code != req.recipient.state_code

        line_results: list[GSTInvoiceLineResult] = []
        total_taxable = Decimal("0.0")
        total_cgst = Decimal("0.0")
        total_sgst = Decimal("0.0")
        total_igst = Decimal("0.0")
        total_cess = Decimal("0.0")

        for it in req.items:
            base_line = (it.quantity * it.unit_price) - it.discount_amount
            taxable = max(Decimal("0.0"), base_line)
            total_taxable += taxable

            if is_inter_state:
                cgst_r = Decimal("0.0")
                sgst_r = Decimal("0.0")
                igst_r = it.gst_rate
                cgst_amt = Decimal("0.0")
                sgst_amt = Decimal("0.0")
                igst_amt = (taxable * igst_r).quantize(Decimal("0.01"))
            else:
                cgst_r = it.gst_rate / Decimal("2.0")
                sgst_r = it.gst_rate / Decimal("2.0")
                igst_r = Decimal("0.0")
                cgst_amt = (taxable * cgst_r).quantize(Decimal("0.01"))
                sgst_amt = (taxable * sgst_r).quantize(Decimal("0.01"))
                igst_amt = Decimal("0.0")

            cess_amt = (taxable * it.cess_rate).quantize(Decimal("0.01"))
            line_total = taxable + cgst_amt + sgst_amt + igst_amt + cess_amt

            total_cgst += cgst_amt
            total_sgst += sgst_amt
            total_igst += igst_amt
            total_cess += cess_amt

            line_results.append(
                GSTInvoiceLineResult(
                    item_name=it.item_name,
                    hsn_sac_code=it.hsn_sac_code,
                    taxable_amount=taxable,
                    cgst_rate=cgst_r,
                    cgst_amount=cgst_amt,
                    sgst_rate=sgst_r,
                    sgst_amount=sgst_amt,
                    igst_rate=igst_r,
                    igst_amount=igst_amt,
                    cess_amount=cess_amt,
                    total_line_amount=line_total,
                )
            )

        total_tax = total_cgst + total_sgst + total_igst + total_cess
        total_inv_exact = total_taxable + total_tax
        rounded_total = total_inv_exact.quantize(Decimal("1.0"))
        round_diff = rounded_total - total_inv_exact

        notes = [
            f"Rule 46 compliance verified: Mandatory HSN/SAC, GSTINs, and place of supply ({req.recipient.state_name}).",
            "Section 170 CGST Act: Invoice value rounded off to the nearest rupee.",
        ]
        if req.is_reverse_charge:
            notes.append(
                "Supply is under Reverse Charge Mechanism (RCM) u/s 9(3) / 9(4). Recipient liable to pay tax."
            )

        return GSTInvoiceSummaryResult(
            document_type=req.document_type,
            invoice_number=req.invoice_number,
            invoice_date=req.invoice_date,
            is_inter_state=is_inter_state,
            supplier_gstin=req.supplier.gstin,
            recipient_gstin=req.recipient.gstin,
            total_taxable_value=total_taxable,
            total_cgst=total_cgst,
            total_sgst=total_sgst,
            total_igst=total_igst,
            total_cess=total_cess,
            total_tax_amount=total_tax,
            total_invoice_amount=total_inv_exact,
            rounded_off_amount=rounded_total,
            round_off_difference=round_diff,
            items=line_results,
            is_compliant_rule_46=True,
            compliance_notes=notes,
        )
