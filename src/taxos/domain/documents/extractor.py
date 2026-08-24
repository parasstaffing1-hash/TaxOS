"""Document Intelligence, Safe Ingestion & Extraction Models."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field
from pypdf import PdfReader


class DocumentType(StrEnum):
    """Tax document classification."""

    FORM_16 = "form_16"
    FORM_26AS = "form_26as"
    AIS_TIS = "ais_tis"
    TAX_INVOICE = "tax_invoice"
    BROKER_STATEMENT = "broker_statement"
    BANK_STATEMENT = "bank_statement"
    RENT_RECEIPT = "rent_receipt"


class ExtractedField(BaseModel):
    """An individual extracted field with confidence score and review flag."""

    field_name: str
    raw_value: str | None = None
    normalized_value: Decimal | str | None = None
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    is_verified: bool = False
    needs_human_review: bool = False


class Form16ExtractionResult(BaseModel):
    """Structured extraction of Form 16 Part A and Part B."""

    employer_name: ExtractedField
    employer_tan: ExtractedField
    employer_pan: ExtractedField
    employee_pan: ExtractedField
    employee_name: ExtractedField
    financial_year: ExtractedField
    assessment_year: ExtractedField

    gross_salary_sec17_1: ExtractedField
    perquisites_sec17_2: ExtractedField
    allowances_exempt_sec10: ExtractedField
    standard_deduction_sec16: ExtractedField
    professional_tax_sec16: ExtractedField
    income_chargeable_salaries: ExtractedField

    total_chapter_via_deductions: ExtractedField
    total_taxable_income: ExtractedField
    tax_on_total_income: ExtractedField
    rebate_87a: ExtractedField
    surcharge: ExtractedField
    cess: ExtractedField
    total_tax_payable: ExtractedField
    total_tds_deducted: ExtractedField

    overall_confidence_score: float = 0.95
    review_required: bool = False
    review_reasons: list[str] = Field(default_factory=list)


class AIS26ASExtractionResult(BaseModel):
    """Structured extraction of AIS/TIS and Form 26AS."""

    taxpayer_pan: ExtractedField
    financial_year: ExtractedField
    total_tds_credited: ExtractedField
    total_tcs_credited: ExtractedField
    total_advance_tax_self_assessment: ExtractedField
    high_value_transactions_count: int = 0
    salary_entries_count: int = 0
    dividend_interest_entries_count: int = 0
    overall_confidence_score: float = 0.95
    review_required: bool = False


class DocumentExtractionResult(BaseModel):
    """Safe, reviewable result returned by the document ingestion endpoint."""

    document_id: str
    filename: str
    content_type: str
    document_type: DocumentType
    source_checksum_sha256: str
    fields: list[ExtractedField] = Field(default_factory=list)
    row_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    overall_confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    review_required: bool = True


class DocumentExtractionEngine:
    """Deterministic, conservative extraction for common tax input formats.

    This engine intentionally returns review flags instead of pretending that
    arbitrary PDFs or poorly structured statements were perfectly understood.
    """

    MAX_BYTES = 15 * 1024 * 1024

    @staticmethod
    def infer_document_type(filename: str) -> DocumentType:
        name = filename.lower()
        filename_rules = (
            (("form16", "form-16"), DocumentType.FORM_16),
            (("26as",), DocumentType.FORM_26AS),
            (("ais", "tis"), DocumentType.AIS_TIS),
            (("invoice", "gst", "vat"), DocumentType.TAX_INVOICE),
            (("broker", "trade"), DocumentType.BROKER_STATEMENT),
            (("bank",), DocumentType.BANK_STATEMENT),
            (("rent",), DocumentType.RENT_RECEIPT),
        )
        for keywords, document_type in filename_rules:
            if any(keyword in name for keyword in keywords):
                return document_type
        return DocumentType.TAX_INVOICE

    def extract(
        self,
        *,
        filename: str,
        content_type: str,
        payload: bytes,
        document_type: DocumentType | None = None,
    ) -> DocumentExtractionResult:
        if len(payload) > self.MAX_BYTES:
            raise ValueError(f"Document exceeds the {self.MAX_BYTES // (1024 * 1024)} MB limit")

        checksum = hashlib.sha256(payload).hexdigest()
        kind = document_type or self.infer_document_type(filename)
        warnings: list[str] = []
        fields: list[ExtractedField] = []
        row_count = 0
        text = self._extract_text(filename, content_type, payload, warnings)

        if filename.lower().endswith((".csv", ".tsv")) or "csv" in content_type:
            fields, row_count = self._extract_delimited(payload, filename, warnings)
        elif filename.lower().endswith(".json") or "json" in content_type:
            fields = self._extract_json(payload, warnings)
        else:
            fields = self._extract_text_fields(text, kind)

        if not fields:
            warnings.append(
                "No structured fields were confidently extracted; manual review is required."
            )

        confidence = (
            round(sum(field.confidence_score for field in fields) / len(fields), 3)
            if fields
            else 0.0
        )
        review_required = bool(warnings) or any(field.needs_human_review for field in fields)
        return DocumentExtractionResult(
            document_id=f"doc_{checksum[:16]}",
            filename=filename,
            content_type=content_type,
            document_type=kind,
            source_checksum_sha256=checksum,
            fields=fields,
            row_count=row_count,
            warnings=warnings,
            overall_confidence_score=confidence,
            review_required=review_required,
        )

    @staticmethod
    def _extract_text(
        filename: str, content_type: str, payload: bytes, warnings: list[str]
    ) -> str:
        if filename.lower().endswith(".pdf") or "pdf" in content_type:
            try:
                reader = PdfReader(io.BytesIO(payload))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception as exc:  # pragma: no cover - parser-specific failures
                warnings.append(f"PDF text extraction failed: {type(exc).__name__}")
                return ""
            else:
                if not text.strip():
                    warnings.append(
                        "PDF contained no extractable text; OCR/manual review is required."
                    )
                return text
        return payload.decode("utf-8", errors="replace")

    @staticmethod
    def _extract_delimited(
        payload: bytes, filename: str, warnings: list[str]
    ) -> tuple[list[ExtractedField], int]:
        delimiter = "\t" if filename.lower().endswith(".tsv") else ","
        try:
            reader = csv.DictReader(
                io.StringIO(payload.decode("utf-8-sig", errors="replace")), delimiter=delimiter
            )
            rows = list(reader)
        except csv.Error as exc:
            warnings.append(f"Delimited file parsing failed: {exc}")
            return [], 0
        if not rows:
            warnings.append("Delimited file has no data rows.")
            return [], 0
        first = rows[0]
        fields = [
            ExtractedField(
                field_name=str(key),
                raw_value=value,
                normalized_value=value,
                confidence_score=0.8,
                needs_human_review=True,
            )
            for key, value in first.items()
            if key
        ]
        return fields, len(rows)

    @staticmethod
    def _extract_json(payload: bytes, warnings: list[str]) -> list[ExtractedField]:
        try:
            value = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            warnings.append(f"JSON parsing failed: {type(exc).__name__}")
            return []
        if not isinstance(value, dict):
            warnings.append("JSON root must be an object for field extraction.")
            return []
        return [
            ExtractedField(
                field_name=str(key),
                raw_value=str(raw),
                normalized_value=raw if isinstance(raw, (str, int, float)) else str(raw),
                confidence_score=0.9,
                needs_human_review=False,
            )
            for key, raw in value.items()
        ]

    @staticmethod
    def _extract_text_fields(text: str, document_type: DocumentType) -> list[ExtractedField]:
        patterns = {
            "pan": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
            "tan": r"\b[A-Z]{4}[0-9]{5}[A-Z]\b",
            "financial_year": r"\bFY\s*20\d{2}(?:-|\u2013)20?\d{2}\b",
            "assessment_year": r"\bAY\s*20\d{2}(?:-|\u2013)20?\d{2}\b",
            "gstin": r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b",
        }
        fields: list[ExtractedField] = []
        for name, pattern in patterns.items():
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                value = match.group(0).upper().replace("\u2013", "-")
                fields.append(
                    ExtractedField(
                        field_name=name,
                        raw_value=value,
                        normalized_value=value,
                        confidence_score=0.85,
                        needs_human_review=document_type
                        in (DocumentType.FORM_16, DocumentType.AIS_TIS),
                    )
                )
        if text.strip() and not fields:
            fields.append(
                ExtractedField(
                    field_name="document_text",
                    raw_value=text[:2000],
                    confidence_score=0.4,
                    needs_human_review=True,
                )
            )
        return fields
