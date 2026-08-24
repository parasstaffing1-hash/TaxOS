"""Unit tests for GST Invoicing, E-Invoice IRN Validator, and ITC Blocked Credit."""

from decimal import Decimal

from taxos.domain.gst.einvoice import IndiaEInvoiceValidator
from taxos.domain.gst.invoicing import (
    GSTInvoiceRequest,
    GSTPartyInfo,
    IndiaGSTInvoiceEngine,
    InvoiceDocumentType,
    InvoiceItem,
)
from taxos.domain.gst.itc_eligibility import (
    IndiaITCEligibilityEngine,
    ITCCategory,
)


def test_gst_invoice_generation_intra_state():
    """Verify Rule 46 compliant intra-state GST invoice with CGST/SGST split and rounding."""
    engine = IndiaGSTInvoiceEngine()
    req = GSTInvoiceRequest(
        document_type=InvoiceDocumentType.TAX_INVOICE,
        invoice_number="INV/2024-25/001",
        invoice_date="2024-11-10",
        supplier=GSTPartyInfo(
            legal_name="Acme Tech Solutions LLP",
            gstin="27AAAAA0000A1Z5",
            state_code="27",
            state_name="Maharashtra",
            address="Mumbai, MH",
        ),
        recipient=GSTPartyInfo(
            legal_name="Zenith Consulting Pvt Ltd",
            gstin="27BBBBB0000B1Z6",
            state_code="27",
            state_name="Maharashtra",
            address="Pune, MH",
        ),
        items=[
            InvoiceItem(
                item_name="Cloud Architecture Consulting",
                hsn_sac_code="998311",
                quantity=Decimal("1.0"),
                unit_price=Decimal("100000.0"),
                gst_rate=Decimal("0.18"),
            )
        ],
    )
    res = engine.generate_invoice(req)

    assert not res.is_inter_state
    assert res.total_taxable_value == Decimal("100000.0")
    assert res.total_cgst == Decimal("9000.0")
    assert res.total_sgst == Decimal("9000.0")
    assert res.total_igst == Decimal("0.0")
    assert res.rounded_off_amount == Decimal("118000.0")


def test_einvoice_irn_generation_and_validation():
    """Verify official NIC SHA-256 IRN hash calculation and validation."""
    supplier_gstin = "27AAAAA0000A1Z5"
    fy = "2024-25"
    doc_type = "INV"
    doc_num = "INV-001"

    expected_irn = IndiaEInvoiceValidator.generate_expected_irn(
        supplier_gstin, fy, doc_type, doc_num
    )
    assert len(expected_irn) == 64

    valid_res = IndiaEInvoiceValidator.validate_irn(
        expected_irn, supplier_gstin, fy, doc_type, doc_num
    )
    assert valid_res.is_valid

    invalid_res = IndiaEInvoiceValidator.validate_irn(
        "0" * 64, supplier_gstin, fy, doc_type, doc_num
    )
    assert not invalid_res.is_valid


def test_itc_section_17_5_blocked_credits():
    """Verify Section 17(5) blocked credit rules."""
    engine = IndiaITCEligibilityEngine()

    # Motor vehicle for staff transport <= 13 seats -> BLOCKED u/s 17(5)(a)
    mv_res = engine.evaluate_itc(
        category=ITCCategory.MOTOR_VEHICLES_SEATING_UNDER_13,
        tax_amount=Decimal("50000.0"),
    )
    assert not mv_res.is_eligible
    assert mv_res.blocked_under_section_17_5
    assert mv_res.statutory_clause == "Section 17(5)(a)"

    # General Machinery -> ELIGIBLE
    machinery_res = engine.evaluate_itc(
        category=ITCCategory.CAPITAL_GOODS_MACHINERY,
        tax_amount=Decimal("18000.0"),
    )
    assert machinery_res.is_eligible
    assert not machinery_res.blocked_under_section_17_5
