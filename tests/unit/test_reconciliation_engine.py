"""Unit tests for Reusable Tax Reconciliation Engine."""

from decimal import Decimal

from taxos.domain.reconciliation.engine import (
    ReconciliationRecord,
    ReusableReconciliationEngine,
)


def test_reconciliation_exact_and_missing():
    """Verify exact matching, tolerance matching, and missing detection."""
    engine = ReusableReconciliationEngine(amount_tolerance_absolute=Decimal("1.0"))

    books = [
        ReconciliationRecord(
            record_id="B1",
            party_identifier="27AAAAA0000A1Z5",
            reference_number="INV/2024/001",
            transaction_date="2024-05-10",
            taxable_amount=Decimal("10000.0"),
            tax_amount=Decimal("1800.0"),
            total_amount=Decimal("11800.0"),
            source="books",
        ),
        ReconciliationRecord(
            record_id="B2",
            party_identifier="29BBBBB0000B1Z6",
            reference_number="INV-2024-002",
            transaction_date="2024-05-15",
            taxable_amount=Decimal("5000.0"),
            tax_amount=Decimal("900.0"),
            total_amount=Decimal("5900.0"),
            source="books",
        ),
    ]

    portal = [
        # Match for B1 with slight slash/dash difference normalized
        ReconciliationRecord(
            record_id="P1",
            party_identifier="27AAAAA0000A1Z5",
            reference_number="INV-2024-001",
            transaction_date="2024-05-10",
            taxable_amount=Decimal("10000.0"),
            tax_amount=Decimal("1800.0"),
            total_amount=Decimal("11800.0"),
            source="gstr2b",
        ),
        # Extra invoice on portal not in books
        ReconciliationRecord(
            record_id="P3",
            party_identifier="27CCCCC0000C1Z7",
            reference_number="INV-999",
            transaction_date="2024-05-20",
            taxable_amount=Decimal("20000.0"),
            tax_amount=Decimal("3600.0"),
            total_amount=Decimal("23600.0"),
            source="gstr2b",
        ),
    ]

    report = engine.reconcile(books_records=books, portal_records=portal)

    assert report.matched_count == 1
    assert report.missing_in_return_count == 1  # B2 missing in portal
    assert report.missing_in_books_count == 1  # P3 missing in books
    assert report.total_matched_itc_or_tax == Decimal("1800.0")
