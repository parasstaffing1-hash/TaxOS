"""Unit tests for safe PDF document extraction (Form 16, empty, scanned, partial)."""

from decimal import Decimal

from fpdf import FPDF

from taxos.domain.documents.pdf_extractor import TaxPDFExtractor


def _create_valid_form_16_pdf() -> bytes:
    """Helper to generate a valid, readable Form 16 PDF in-memory."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text="FORM NO. 16 - Certificate under section 203 of the Income-tax Act, 1961")
    pdf.ln(10)
    pdf.cell(text="Name of the Employer: Acme Technologies Private Limited")
    pdf.ln(8)
    pdf.cell(text="PAN of the Deductor: ABCDE1234F")
    pdf.ln(8)
    pdf.cell(text="TAN of the Deductor: BLRP01234A")
    pdf.ln(8)
    pdf.cell(text="Name of the Employee: Rajesh Kumar")
    pdf.ln(8)
    pdf.cell(text="PAN of the Employee: BNZPK5678L")
    pdf.ln(8)
    pdf.cell(text="Assessment Year: 2025-26")
    pdf.ln(8)
    pdf.cell(text="Financial Year: 2024-25")
    pdf.ln(8)
    pdf.cell(text="Gross Salary u/s 17(1): 1,500,000.00")
    pdf.ln(8)
    pdf.cell(text="Standard Deduction u/s 16(ia): 75,000.00")
    pdf.ln(8)
    pdf.cell(text="Total deductions under Chapter VI-A: 150,000.00")
    pdf.ln(8)
    pdf.cell(text="Total Taxable Income: 1,275,000.00")
    pdf.ln(8)
    pdf.cell(text="Total TDS Deducted: 85,000.00")

    return bytes(pdf.output())


def _create_partial_form_16_pdf() -> bytes:
    """Helper to generate a partial Form 16 PDF that has identifiers but no salary tables."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text="FORM NO. 16 (Part A Summary)")
    pdf.ln(10)
    pdf.cell(text="PAN of the Employee: BNZPK5678L")
    pdf.ln(8)
    pdf.cell(text="TAN of the Deductor: BLRP01234A")
    return bytes(pdf.output())


def _create_blank_pdf() -> bytes:
    """Helper to generate an empty/blank PDF with no text layer."""
    pdf = FPDF()
    pdf.add_page()
    return bytes(pdf.output())


def test_valid_form_16_extraction():
    """Verify high-confidence structured extraction of a valid Form 16."""
    pdf_bytes = _create_valid_form_16_pdf()
    result = TaxPDFExtractor.parse_form_16(pdf_bytes)

    assert result.employee_pan.normalized_value == "BNZPK5678L"
    assert result.employer_tan.normalized_value == "BLRP01234A"
    assert result.employer_pan.normalized_value == "ABCDE1234F"
    assert result.gross_salary_sec17_1.normalized_value == Decimal("1500000.0")
    assert result.standard_deduction_sec16.normalized_value == Decimal("75000.0")
    assert result.total_chapter_via_deductions.normalized_value == Decimal("150000.0")
    assert result.total_taxable_income.normalized_value == Decimal("1275000.0")
    assert result.total_tds_deducted.normalized_value == Decimal("85000.0")
    assert result.overall_confidence_score >= 0.85
    assert not result.review_required


def test_empty_or_blank_pdf_extraction():
    """Verify empty/scanned PDF produces zero fabricated values and triggers human review."""
    pdf_bytes = _create_blank_pdf()
    result = TaxPDFExtractor.parse_form_16(pdf_bytes)

    assert (
        result.employee_pan.normalized_value is None
        or result.employee_pan.normalized_value == "UNKNOWN"
    )
    assert result.gross_salary_sec17_1.normalized_value is None
    assert result.total_taxable_income.normalized_value is None
    assert result.overall_confidence_score == 0.0
    assert result.review_required is True
    assert "Empty or scanned document" in result.review_reasons[0]


def test_corrupted_pdf_bytes_handling():
    """Verify corrupted or invalid PDF bytes do not crash and flag review."""
    corrupted_bytes = b"%PDF-1.4 corrupted incomplete stream"
    result = TaxPDFExtractor.parse_form_16(corrupted_bytes)

    assert result.gross_salary_sec17_1.normalized_value is None
    assert result.review_required is True
    assert result.overall_confidence_score == 0.0


def test_partial_form_16_extraction_flags_review():
    """Verify partial Form 16 extracts available PANs but flags missing salary as review required."""
    pdf_bytes = _create_partial_form_16_pdf()
    result = TaxPDFExtractor.parse_form_16(pdf_bytes)

    assert result.employee_pan.normalized_value == "BNZPK5678L"
    assert result.employer_tan.normalized_value == "BLRP01234A"
    assert result.gross_salary_sec17_1.normalized_value is None
    assert result.total_taxable_income.normalized_value is None
    assert result.review_required is True
    assert any("Gross salary" in reason for reason in result.review_reasons)
