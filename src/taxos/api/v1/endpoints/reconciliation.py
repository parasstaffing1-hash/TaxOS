"""Tax Reconciliation API Endpoints."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter
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


@router.post("/run", response_model=ReconciliationReport)
async def run_reconciliation(payload: ReconciliationRunPayload) -> ReconciliationReport:
    """Execute multi-pass reconciliation between accounting books and portal returns (e.g. GSTR-2B vs Purchases or Form 16 vs 26AS)."""
    engine = ReusableReconciliationEngine(
        amount_tolerance_absolute=payload.amount_tolerance,
        date_tolerance_days=payload.date_tolerance_days,
    )
    return engine.reconcile(
        books_records=payload.books_records,
        portal_records=payload.portal_records,
    )
