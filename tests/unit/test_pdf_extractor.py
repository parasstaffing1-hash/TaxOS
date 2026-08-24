"""Unit tests for PDF Document Extractor using pypdf."""

from decimal import Decimal

from fpdf import FPDF

from taxos.domain.documents.pdf_extractor import TaxPDFExtractor


def _create_sample_form_16_pdf() -> bytes:
    """Helper to generate a sample Form 16 PDF in-memory."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text="FORM NO. 16 - Certificate under section 203 of the Income-tax Act, 1961")
    pdf.ln(10)
    pdf.cell(text="PAN of the Deductor: ABCDE1234F")
    pdf.ln(8)
    pdf.cell(text="TAN of the Deductor: BLRP01234A")
    pdf.ln(8)
    pdf.cell(text="PAN of the Employee: BNZPK5678L")
    pdf.ln(8)
    pdf.cell(text="Gross Salary u/s 17(1): 1,500,000.00")
    pdf.ln(8)
    pdf.cell(text="Standard Deduction u/s 16(ia): 75,000.00")
    pdf.ln(8)
    pdf.cell(text="Total Taxable Income: 1,425,000.00")

    # Output to byte stream
    return bytes(pdf.output())


def test_form_16_pdf_extraction():
    """Verify structured parsing of Form 16 PDF."""
    pdf_bytes = _create_sample_form_16_pdf()
    result = TaxPDFExtractor.parse_form_16(pdf_bytes)

    assert result.employee_pan.normalized_value == "BNZPK5678L"
    assert result.employer_tan.normalized_value == "BLRP01234A"
    assert result.employer_pan.normalized_value == "ABCDE1234F"
    assert result.gross_salary_sec17_1.normalized_value == Decimal("1500000.0")
    assert result.standard_deduction_sec16.normalized_value == Decimal("75000.0")
    assert result.overall_confidence_score >= 0.90
    assert not result.review_required
