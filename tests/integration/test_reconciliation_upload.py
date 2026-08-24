"""Integration tests for file-upload-based automated tax reconciliation."""

import io
from decimal import Decimal

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_reconciliation_upload_and_match(client: AsyncClient):
    """Verify CSV file upload and matching between books and GSTR-2B."""
    books_csv = (
        "invoice_number,gstin,transaction_date,taxable_amount,tax_amount,total_amount\n"
        "INV-101,27AAAPA1234C1Z1,2025-01-15,100000.00,18000.00,118000.00\n"
        "INV-102,29BBBPA5678D1Z2,2025-01-20,50000.00,9000.00,59000.00\n"
    )

    portal_csv = (
        "inv_no,vendor_gstin,invoice_date,taxable_value,tax,total_value\n"
        "INV-101,27AAAPA1234C1Z1,2025-01-15,100000.00,18000.00,118000.00\n"
        "INV-999,29BBBPA5678D1Z2,2025-01-20,20000.00,3600.00,23600.00\n"
    )

    files = {
        "books_file": ("books.csv", io.BytesIO(books_csv.encode("utf-8")), "text/csv"),
        "portal_file": ("gstr2b.csv", io.BytesIO(portal_csv.encode("utf-8")), "text/csv"),
    }
    data = {
        "amount_tolerance": "1.0",
        "date_tolerance_days": "60",
    }

    resp = await client.post("/api/v1/reconciliation/upload-and-match", data=data, files=files)
    assert resp.status_code == 200, resp.text
    report = resp.json()

    assert report["total_books_records"] == 2
    assert report["total_portal_records"] == 2
    assert report["matched_count"] >= 1
    assert Decimal(str(report["total_matched_itc_or_tax"])) == Decimal("18000.00")
