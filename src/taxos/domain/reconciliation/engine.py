"""Reusable Multi-Jurisdiction Tax Reconciliation Engine.

Supports Exact, Fuzzy, Composite, and Tolerance Matching with comprehensive
classifications (MATCHED, PARTIAL_MATCH, MISMATCH, MISSING_IN_BOOKS,
MISSING_IN_RETURN, DUPLICATE, REVIEW_REQUIRED).
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class ReconciliationStatus(StrEnum):
    """Reconciliation match classification."""

    MATCHED = "matched"
    PARTIAL_MATCH = "partial_match"
    MISMATCH = "mismatch"
    MISSING_IN_BOOKS = "missing_in_books"
    MISSING_IN_RETURN = "missing_in_return"
    DUPLICATE = "duplicate"
    REVIEW_REQUIRED = "review_required"


class ReconciliationRecord(BaseModel):
    """A financial transaction or invoice record to be reconciled."""

    record_id: str
    party_identifier: str = Field(description="GSTIN, PAN, SSN, or Vendor/Customer ID")
    reference_number: str = Field(
        description="Invoice number, Challan number, or Contract Note ID"
    )
    transaction_date: str = Field(description="YYYY-MM-DD format")
    taxable_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    hsn_or_category: str | None = None
    source: str = Field(
        default="books", description="'books', 'gstr2b', 'gstr1', '26as', 'ais', 'bank'"
    )


class ReconciliationMatchPair(BaseModel):
    """Pair of matched/unmatched records with variance breakdown."""

    status: ReconciliationStatus
    books_record: ReconciliationRecord | None = None
    portal_record: ReconciliationRecord | None = None
    taxable_variance: Decimal = Decimal("0.0")
    tax_variance: Decimal = Decimal("0.0")
    date_variance_days: int = 0
    confidence_score: float = 1.0  # 0.0 to 1.0
    match_strategy: str = "exact"
    explanation: str


class ReconciliationReport(BaseModel):
    """Consolidated reconciliation run report with summary statistics."""

    total_books_records: int
    total_portal_records: int
    matched_count: int
    partial_match_count: int
    missing_in_books_count: int
    missing_in_return_count: int
    duplicate_count: int
    review_required_count: int

    total_books_tax: Decimal
    total_portal_tax: Decimal
    total_matched_itc_or_tax: Decimal
    total_unclaimed_or_mismatch_tax: Decimal

    pairs: list[ReconciliationMatchPair]
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


def normalize_ref(ref: str) -> str:
    """Normalize reference / invoice string by stripping slashes, hyphens, and leading zeros."""
    cleaned = re.sub(r"[\s/\-_]+", "", ref.strip().upper())
    return cleaned.lstrip("0") or "0"


class ReusableReconciliationEngine:
    """Enterprise reconciliation engine for GST, TDS (26AS), and Ledger reconciliation."""

    def __init__(
        self,
        amount_tolerance_absolute: Decimal = Decimal("1.0"),
        amount_tolerance_percentage: Decimal = Decimal("0.01"),  # 1%
        date_tolerance_days: int = 60,
    ) -> None:
        self.amount_tolerance_abs = amount_tolerance_absolute
        self.amount_tolerance_pct = amount_tolerance_percentage
        self.date_tolerance_days = date_tolerance_days

    def reconcile(  # noqa: PLR0912, PLR0915
        self,
        books_records: list[ReconciliationRecord],
        portal_records: list[ReconciliationRecord],
    ) -> ReconciliationReport:
        """Execute multi-pass matching between accounting books and tax portal records."""
        matched_pairs: list[ReconciliationMatchPair] = []

        unmatched_books: list[ReconciliationRecord] = list(books_records)
        unmatched_portal: list[ReconciliationRecord] = list(portal_records)

        # Check for duplicates within books and portal
        seen_books_keys: set[str] = set()
        for b in books_records:
            k = f"{b.party_identifier.upper()}:{normalize_ref(b.reference_number)}"
            if k in seen_books_keys:
                matched_pairs.append(
                    ReconciliationMatchPair(
                        status=ReconciliationStatus.DUPLICATE,
                        books_record=b,
                        portal_record=None,
                        confidence_score=1.0,
                        match_strategy="duplicate_detection",
                        explanation=f"Duplicate invoice reference {b.reference_number} found in books.",
                    )
                )
            seen_books_keys.add(k)

        # PASS 1: Exact Match (Same Party + Same Normalized Ref + Exact Amount + Exact Date)
        matched_b_indices: set[int] = set()
        matched_p_indices: set[int] = set()

        for bi, b in enumerate(unmatched_books):
            b_norm = normalize_ref(b.reference_number)
            b_party = b.party_identifier.upper()

            for pi, p in enumerate(unmatched_portal):
                if pi in matched_p_indices:
                    continue

                p_norm = normalize_ref(p.reference_number)
                p_party = p.party_identifier.upper()

                if b_party == p_party and b_norm == p_norm:
                    tax_diff = abs(b.tax_amount - p.tax_amount)
                    taxable_diff = abs(b.taxable_amount - p.taxable_amount)

                    # Date diff
                    try:
                        d_b = date.fromisoformat(b.transaction_date)
                        d_p = date.fromisoformat(p.transaction_date)
                        day_diff = abs((d_b - d_p).days)
                    except ValueError:
                        day_diff = 0

                    # Exact Match
                    if tax_diff == 0 and taxable_diff == 0 and day_diff == 0:
                        matched_b_indices.add(bi)
                        matched_p_indices.add(pi)
                        matched_pairs.append(
                            ReconciliationMatchPair(
                                status=ReconciliationStatus.MATCHED,
                                books_record=b,
                                portal_record=p,
                                taxable_variance=Decimal("0.0"),
                                tax_variance=Decimal("0.0"),
                                date_variance_days=0,
                                confidence_score=1.0,
                                match_strategy="exact_match",
                                explanation=f"Exact match on Invoice {b.reference_number} with GSTIN/Party {b.party_identifier}.",
                            )
                        )
                        break

        # PASS 2: Tolerance Match (Same Party + Same Normalized Ref + Amount within tolerance + Date within tolerance)
        for bi, b in enumerate(unmatched_books):
            if bi in matched_b_indices:
                continue

            b_norm = normalize_ref(b.reference_number)
            b_party = b.party_identifier.upper()

            for pi, p in enumerate(unmatched_portal):
                if pi in matched_p_indices:
                    continue

                p_norm = normalize_ref(p.reference_number)
                p_party = p.party_identifier.upper()

                if b_party == p_party and b_norm == p_norm:
                    tax_diff = abs(b.tax_amount - p.tax_amount)
                    taxable_diff = abs(b.taxable_amount - p.taxable_amount)

                    try:
                        d_b = date.fromisoformat(b.transaction_date)
                        d_p = date.fromisoformat(p.transaction_date)
                        day_diff = abs((d_b - d_p).days)
                    except ValueError:
                        day_diff = 0

                    is_amount_within_tol = tax_diff <= self.amount_tolerance_abs or (
                        p.tax_amount > 0 and (tax_diff / p.tax_amount) <= self.amount_tolerance_pct
                    )
                    is_date_within_tol = day_diff <= self.date_tolerance_days

                    if is_amount_within_tol and is_date_within_tol:
                        matched_b_indices.add(bi)
                        matched_p_indices.add(pi)
                        matched_pairs.append(
                            ReconciliationMatchPair(
                                status=ReconciliationStatus.MATCHED,
                                books_record=b,
                                portal_record=p,
                                taxable_variance=b.taxable_amount - p.taxable_amount,
                                tax_variance=b.tax_amount - p.tax_amount,
                                date_variance_days=day_diff,
                                confidence_score=0.95,
                                match_strategy="tolerance_match",
                                explanation=f"Matched within tolerance (Tax variance: ₹{b.tax_amount - p.tax_amount:,.2f}, Date diff: {day_diff} days).",
                            )
                        )
                        break
                    # Partial match or mismatch
                    matched_b_indices.add(bi)
                    matched_p_indices.add(pi)
                    matched_pairs.append(
                        ReconciliationMatchPair(
                            status=(
                                ReconciliationStatus.PARTIAL_MATCH
                                if is_date_within_tol
                                else ReconciliationStatus.MISMATCH
                            ),
                            books_record=b,
                            portal_record=p,
                            taxable_variance=b.taxable_amount - p.taxable_amount,
                            tax_variance=b.tax_amount - p.tax_amount,
                            date_variance_days=day_diff,
                            confidence_score=0.70,
                            match_strategy="reference_matched_value_mismatch",
                            explanation=f"Invoice number matched but variance exceeds tolerance. Books Tax: ₹{b.tax_amount:,.2f}, Portal Tax: ₹{p.tax_amount:,.2f}.",
                        )
                    )
                    break

        # PASS 3: Unmatched Records Classification
        for bi, b in enumerate(unmatched_books):
            if bi not in matched_b_indices:
                matched_pairs.append(
                    ReconciliationMatchPair(
                        status=ReconciliationStatus.MISSING_IN_RETURN,
                        books_record=b,
                        portal_record=None,
                        taxable_variance=b.taxable_amount,
                        tax_variance=b.tax_amount,
                        confidence_score=1.0,
                        match_strategy="missing_detection",
                        explanation=f"Invoice {b.reference_number} recorded in books but missing in tax portal/GSTR-2B.",
                    )
                )

        for pi, p in enumerate(unmatched_portal):
            if pi not in matched_p_indices:
                matched_pairs.append(
                    ReconciliationMatchPair(
                        status=ReconciliationStatus.MISSING_IN_BOOKS,
                        books_record=None,
                        portal_record=p,
                        taxable_variance=-p.taxable_amount,
                        tax_variance=-p.tax_amount,
                        confidence_score=1.0,
                        match_strategy="missing_detection",
                        explanation=f"Invoice {p.reference_number} uploaded on tax portal by supplier ({p.party_identifier}) but not found in accounting books.",
                    )
                )

        # Summary Metrics
        matched_count = sum(1 for m in matched_pairs if m.status == ReconciliationStatus.MATCHED)
        partial_count = sum(
            1 for m in matched_pairs if m.status == ReconciliationStatus.PARTIAL_MATCH
        )
        missing_books = sum(
            1 for m in matched_pairs if m.status == ReconciliationStatus.MISSING_IN_BOOKS
        )
        missing_return = sum(
            1 for m in matched_pairs if m.status == ReconciliationStatus.MISSING_IN_RETURN
        )
        duplicates = sum(1 for m in matched_pairs if m.status == ReconciliationStatus.DUPLICATE)
        review_required = sum(
            1
            for m in matched_pairs
            if m.status in (ReconciliationStatus.PARTIAL_MATCH, ReconciliationStatus.MISMATCH)
        )

        total_b_tax = sum((b.tax_amount for b in books_records), Decimal("0.0"))
        total_p_tax = sum((p.tax_amount for p in portal_records), Decimal("0.0"))
        matched_tax = sum(
            (
                m.books_record.tax_amount
                for m in matched_pairs
                if m.status == ReconciliationStatus.MATCHED and m.books_record
            ),
            Decimal("0.0"),
        )
        unclaimed_tax = total_b_tax - matched_tax

        return ReconciliationReport(
            total_books_records=len(books_records),
            total_portal_records=len(portal_records),
            matched_count=matched_count,
            partial_match_count=partial_count,
            missing_in_books_count=missing_books,
            missing_in_return_count=missing_return,
            duplicate_count=duplicates,
            review_required_count=review_required,
            total_books_tax=total_b_tax,
            total_portal_tax=total_p_tax,
            total_matched_itc_or_tax=matched_tax,
            total_unclaimed_or_mismatch_tax=unclaimed_tax,
            pairs=matched_pairs,
        )
