"""Tax Reconciliation API Endpoints with JSON and Multi-Format File Upload Support."""

from __future__ import annotations

import csv
import io
import json
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from taxos.domain.reconciliation.engine import (
    ReconciliationRecord,
    ReconciliationReport,
    ReusableReconciliationEngine,
)

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation Engine"])


class ReconciliationRunPayload(BaseModel):
    books_records: list[ReconciliationRecord]
    portal_records: list[ReconciliationRecord]
    amount_tolerance: Decimal = Field(
        default=Decimal("1.0"), description="Absolute currency tolerance e.g. ₹1.00"
    )
    date_tolerance_days: int = Field(default=60, description="Date variance tolerance in days")


def _parse_tabular_records(
    file_bytes: bytes, filename: str, source_tag: str
) -> list[ReconciliationRecord]:
    """Parse CSV or JSON byte streams into a standard list of ReconciliationRecord."""
    records: list[ReconciliationRecord] = []
    fname_lower = filename.lower()

    if fname_lower.endswith(".json"):
        try:
            raw_data = json.loads(file_bytes.decode("utf-8"))
        except Exception as exc:
            msg = f"Failed to parse JSON file {filename}: {exc}"
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg) from exc

        items = raw_data if isinstance(raw_data, list) else raw_data.get("records", [])
        for item in items:
            records.append(
                ReconciliationRecord(
                    record_id=str(item.get("record_id") or uuid4().hex),
                    party_identifier=str(
                        item.get("party_identifier")
                        or item.get("gstin")
                        or item.get("pan")
                        or "UNKNOWN"
                    ),
                    reference_number=str(
                        item.get("reference_number")
                        or item.get("invoice_number")
                        or item.get("inv_no")
                        or "UNKNOWN"
                    ),
                    transaction_date=str(
                        item.get("transaction_date") or item.get("date") or "2025-01-01"
                    ),
                    taxable_amount=Decimal(
                        str(item.get("taxable_amount") or item.get("taxable_value") or "0.0")
                    ),
                    tax_amount=Decimal(str(item.get("tax_amount") or item.get("tax") or "0.0")),
                    total_amount=Decimal(
                        str(item.get("total_amount") or item.get("total_value") or "0.0")
                    ),
                    hsn_or_category=item.get("hsn_or_category"),
                    source=source_tag,
                )
            )
        return records

    # Default: CSV Parser
    try:
        text_content = file_bytes.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text_content))
        raw_rows = list(reader)
    except Exception as exc:
        msg = f"Failed to parse CSV file {filename}: {exc}"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg) from exc

    for row in raw_rows:
        # Case-insensitive column lookup
        norm_row = {k.strip().lower().replace(" ", "_"): v.strip() for k, v in row.items() if k}

        party = (
            norm_row.get("party_identifier")
            or norm_row.get("gstin")
            or norm_row.get("pan")
            or norm_row.get("vendor_gstin")
            or "UNKNOWN"
        )
        ref_num = (
            norm_row.get("reference_number")
            or norm_row.get("invoice_number")
            or norm_row.get("invoice_no")
            or norm_row.get("inv_no")
            or norm_row.get("doc_no")
            or "UNKNOWN"
        )
        tx_date = (
            norm_row.get("transaction_date")
            or norm_row.get("invoice_date")
            or norm_row.get("date")
            or "2025-01-01"
        )
        taxable_raw = norm_row.get("taxable_amount") or norm_row.get("taxable_value") or "0.0"
        tax_raw = (
            norm_row.get("tax_amount") or norm_row.get("tax") or norm_row.get("igst") or "0.0"
        )
        total_raw = (
            norm_row.get("total_amount")
            or norm_row.get("total_value")
            or norm_row.get("invoice_value")
            or "0.0"
        )

        taxable_clean = re_clean_num(taxable_raw)
        tax_clean = re_clean_num(tax_raw)
        total_clean = re_clean_num(total_raw)

        records.append(
            ReconciliationRecord(
                record_id=str(norm_row.get("record_id") or uuid4().hex),
                party_identifier=party,
                reference_number=ref_num,
                transaction_date=tx_date,
                taxable_amount=Decimal(taxable_clean),
                tax_amount=Decimal(tax_clean),
                total_amount=Decimal(total_clean),
                hsn_or_category=norm_row.get("hsn"),
                source=source_tag,
            )
        )
    return records


def re_clean_num(val: str) -> str:
    cleaned = val.replace(",", "").replace("₹", "").replace("$", "").replace(" ", "").strip()
    return cleaned if cleaned else "0.0"


@router.post("/run", response_model=ReconciliationReport)
async def run_reconciliation(payload: ReconciliationRunPayload) -> ReconciliationReport:
    """Execute multi-pass reconciliation between accounting books and portal returns."""
    engine = ReusableReconciliationEngine(
        amount_tolerance_absolute=payload.amount_tolerance,
        date_tolerance_days=payload.date_tolerance_days,
    )
    return engine.reconcile(
        books_records=payload.books_records,
        portal_records=payload.portal_records,
    )


@router.post("/upload-and-match", response_model=ReconciliationReport)
async def upload_and_reconcile(
    books_file: UploadFile = File(
        ..., description="Internal Accounting Ledger / Purchase Register (CSV or JSON)"
    ),
    portal_file: UploadFile = File(
        ..., description="Government Portal Return / GSTR-2B / 26AS (CSV or JSON)"
    ),
    amount_tolerance: Decimal = Form(default=Decimal("1.0")),
    date_tolerance_days: int = Form(default=60),
) -> ReconciliationReport:
    """Upload books & portal documents (CSV/JSON), parse records, and run complete automated tax reconciliation."""
    books_bytes = await books_file.read()
    portal_bytes = await portal_file.read()

    books_records = _parse_tabular_records(
        books_bytes, books_file.filename or "books.csv", "books"
    )
    portal_records = _parse_tabular_records(
        portal_bytes, portal_file.filename or "portal.csv", "portal"
    )

    engine = ReusableReconciliationEngine(
        amount_tolerance_absolute=amount_tolerance,
        date_tolerance_days=date_tolerance_days,
    )
    return engine.reconcile(
        books_records=books_records,
        portal_records=portal_records,
    )
