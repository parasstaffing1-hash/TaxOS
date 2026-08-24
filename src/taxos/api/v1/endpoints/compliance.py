"""Tax Compliance & Statutory Obligations API Endpoints."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from taxos.domain.compliance.calendar import (
    INDIA_COMPLIANCE_OBLIGATIONS,
    ComplianceObligation,
    ComplianceTask,
    FilingStatus,
    IndiaComplianceCalendarEngine,
)

router = APIRouter(prefix="/compliance", tags=["Compliance Engine"])
_tasks: dict[str, ComplianceTask] = {}


class ComplianceTaskCreate(BaseModel):
    obligation_id: str
    status: FilingStatus = FilingStatus.PENDING
    due_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class ComplianceTaskUpdate(BaseModel):
    status: FilingStatus | None = None
    due_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


@router.get("/obligations", response_model=list[ComplianceObligation])
async def list_compliance_obligations(
    tax_family: str | None = Query(
        default=None, description="Filter by family: income_tax, gst, tds, advance_tax"
    ),
    taxpayer_category: str | None = Query(
        default=None, description="Filter by category: individual, salaried, tax_audit_company"
    ),
    assessment_year: str = Query(default="2025-26", pattern=r"^\d{4}-\d{2}$"),
) -> list[ComplianceObligation]:
    """Retrieve statutory tax filing due dates, frequencies, and legal consequences for delay."""
    engine = IndiaComplianceCalendarEngine()
    obligations = engine.list_obligations(
        tax_family=tax_family,
        taxpayer_category=taxpayer_category,
    )
    return engine.resolve_due_dates(obligations, assessment_year)


@router.get("/tasks", response_model=list[ComplianceTask])
async def list_compliance_tasks() -> list[ComplianceTask]:
    """List tracked compliance tasks for the current process/workspace."""
    return list(_tasks.values())


@router.post("/tasks", response_model=ComplianceTask, status_code=201)
async def create_compliance_task(payload: ComplianceTaskCreate) -> ComplianceTask:
    """Create a tracked task without mutating the statutory rule catalog."""
    obligation_ids = {item.obligation_id for item in INDIA_COMPLIANCE_OBLIGATIONS}
    if payload.obligation_id not in obligation_ids:
        raise HTTPException(status_code=404, detail="Unknown compliance obligation")
    task = ComplianceTask(task_id=uuid4().hex, **payload.model_dump())
    _tasks[task.task_id] = task
    return task


@router.patch("/tasks/{task_id}", response_model=ComplianceTask)
async def update_compliance_task(task_id: str, payload: ComplianceTaskUpdate) -> ComplianceTask:
    """Update tracking state while preserving the source obligation."""
    task = _tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Compliance task not found")
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(UTC).date()
    updated = task.model_copy(update=updates)
    _tasks[task_id] = updated
    return updated
