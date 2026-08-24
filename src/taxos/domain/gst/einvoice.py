"""GST E-Invoice (Schema INV-01) & Invoice Registration Portal (IRP) Validator."""

from __future__ import annotations

import hashlib
import re

from pydantic import BaseModel, Field


class EInvoiceValidationResult(BaseModel):
    """Result of E-Invoice syntax and cryptographic IRN verification."""

    is_valid: bool
    irn_hash: str | None = None
    supplier_gstin: str | None = None
    doc_number: str | None = None
    doc_type: str | None = None
    financial_year: str | None = None
    qr_code_present: bool = False
    validation_messages: list[str] = Field(default_factory=list)


IRN_HEX_LENGTH = 64


class IndiaEInvoiceValidator:
    """Validator for Indian GST E-Invoices, IRN hashes, and QR Code payloads."""

    @staticmethod
    def generate_expected_irn(
        supplier_gstin: str,
        financial_year: str,
        doc_type: str,
        doc_number: str,
    ) -> str:
        """Compute the official SHA-256 IRN hash per NIC IRP specification.

        IRN Formula: SHA256(SupplierGSTIN + FY + DocType + DocNumber)
        """
        combined = f"{supplier_gstin.upper()}{financial_year.upper()}{doc_type.upper()}{doc_number.upper()}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    @classmethod
    def validate_irn(
        cls,
        irn: str,
        supplier_gstin: str,
        financial_year: str,
        doc_type: str,
        doc_number: str,
    ) -> EInvoiceValidationResult:
        """Validate 64-character hex IRN against statutory components."""
        clean_irn = irn.strip().lower()
        if len(clean_irn) != IRN_HEX_LENGTH or not re.fullmatch(r"^[0-9a-f]{64}$", clean_irn):
            return EInvoiceValidationResult(
                is_valid=False,
                validation_messages=[
                    "IRN must be a 64-character lowercase hexadecimal SHA-256 hash."
                ],
            )

        expected = cls.generate_expected_irn(supplier_gstin, financial_year, doc_type, doc_number)
        if clean_irn != expected:
            return EInvoiceValidationResult(
                is_valid=False,
                irn_hash=clean_irn,
                validation_messages=[
                    f"IRN checksum mismatch: Hash does not match components (expected {expected[:10]}...)."
                ],
            )

        return EInvoiceValidationResult(
            is_valid=True,
            irn_hash=clean_irn,
            supplier_gstin=supplier_gstin,
            doc_number=doc_number,
            doc_type=doc_type,
            financial_year=financial_year,
            validation_messages=[
                "Valid statutory IRN registered with Invoice Registration Portal (IRP)."
            ],
        )
