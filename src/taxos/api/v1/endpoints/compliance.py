"""Tax Compliance & Statutory Obligations API Endpoints with SQLAlchemy Persistence & Multi-Tenancy."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxos.api.dependencies.auth import get_current_active_user
from taxos.api.v1.deps import get_db
from taxos.domain.compliance.calendar import (
    INDIA_COMPLIANCE_OBLIGATIONS,
    ComplianceObligation,
    ComplianceTask,
    FilingStatus,
    IndiaComplianceCalendarEngine,
)
from taxos.infrastructure.database.models.iam import Organization, OrganizationMember, User
from taxos.infrastructure.database.models.tax_models import ComplianceTaskModel

router = APIRouter(prefix="/compliance", tags=["Compliance Engine"])


class ComplianceTaskCreate(BaseModel):
    obligation_id: str
    status: FilingStatus = FilingStatus.PENDING
    due_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class ComplianceTaskUpdate(BaseModel):
    status: FilingStatus | None = None
    due_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


async def _resolve_user_organization(
    user: User,
    session: AsyncSession,
    org_id_header: int | None = None,
) -> int:
    """Resolve and verify user's organization membership.

    Raises HTTPException 403 if user is not a member of the requested organization.
    Creates a default personal organization if the user has no existing memberships.
    """
    if org_id_header is not None:
        stmt = select(OrganizationMember).where(
            OrganizationMember.user_id == user.id,
            OrganizationMember.organization_id == org_id_header,
        )
        membership = (await session.execute(stmt)).scalar_one_or_none()
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Not an active member of this organization",
            )
        return org_id_header

    # Fetch user's primary organization membership
    stmt = select(OrganizationMember).where(OrganizationMember.user_id == user.id)
    membership = (await session.execute(stmt)).scalars().first()
    if membership:
        return membership.organization_id

    # Create a personal workspace organization for the user
    new_org = Organization(name=f"{user.email}'s Workspace")
    session.add(new_org)
    await session.commit()
    await session.refresh(new_org)

    new_member = OrganizationMember(user_id=user.id, organization_id=new_org.id, role="owner")
    session.add(new_member)
    await session.commit()
    return new_org.id


def _to_compliance_task_domain(model: ComplianceTaskModel) -> ComplianceTask:
    """Convert an ORM ComplianceTaskModel to a domain ComplianceTask."""
    due_d: date | None = None
    if model.due_date:
        try:
            due_d = date.fromisoformat(model.due_date)
        except ValueError:
            due_d = None

    status_val = FilingStatus.PENDING
    for fs in FilingStatus:
        if fs.value == model.status:
            status_val = fs
            break

    updated_d = model.updated_at.date() if model.updated_at else datetime.now(UTC).date()

    return ComplianceTask(
        task_id=model.id,
        obligation_id=model.obligation_id,
        status=status_val,
        due_date=due_d,
        notes=model.notes,
        updated_at=updated_d,
    )


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
async def list_compliance_tasks(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    x_organization_id: int | None = Header(default=None, alias="X-Organization-ID"),
    org_id: int | None = Query(default=None),
) -> list[ComplianceTask]:
    """List tracked compliance tasks scoped to the user's organization."""
    target_org_id = x_organization_id or org_id
    scoped_org_id = await _resolve_user_organization(current_user, session, target_org_id)

    stmt = (
        select(ComplianceTaskModel)
        .where(ComplianceTaskModel.organization_id == scoped_org_id)
        .order_by(ComplianceTaskModel.created_at.desc())
    )
    result = await session.execute(stmt)
    records = result.scalars().all()
    return [_to_compliance_task_domain(record) for record in records]


@router.post("/tasks", response_model=ComplianceTask, status_code=201)
async def create_compliance_task(
    payload: ComplianceTaskCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    x_organization_id: int | None = Header(default=None, alias="X-Organization-ID"),
    org_id: int | None = Query(default=None),
) -> ComplianceTask:
    """Create a tracked task scoped to the user's organization."""
    target_org_id = x_organization_id or org_id
    scoped_org_id = await _resolve_user_organization(current_user, session, target_org_id)

    # Validate against known obligations
    obligation_map = {item.obligation_id: item for item in INDIA_COMPLIANCE_OBLIGATIONS}
    if payload.obligation_id not in obligation_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unknown compliance obligation"
        )

    obligation = obligation_map[payload.obligation_id]
    task_model = ComplianceTaskModel(
        id=uuid4().hex,
        organization_id=scoped_org_id,
        user_id=current_user.id,
        obligation_id=payload.obligation_id,
        obligation_name=obligation.form_or_filing_name,
        tax_family=obligation.tax_family,
        due_date=str(payload.due_date) if payload.due_date else None,
        status=payload.status.value if hasattr(payload.status, "value") else str(payload.status),
        is_completed=payload.status in (FilingStatus.FILED_ON_TIME, FilingStatus.FILED_LATE),
        notes=payload.notes,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(task_model)
    await session.commit()
    await session.refresh(task_model)
    return _to_compliance_task_domain(task_model)


@router.patch("/tasks/{task_id}", response_model=ComplianceTask)
async def update_compliance_task(  # noqa: PLR0917
    task_id: str,
    payload: ComplianceTaskUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    x_organization_id: int | None = Header(default=None, alias="X-Organization-ID"),
    org_id: int | None = Query(default=None),
) -> ComplianceTask:
    """Update tracking state for a task scoped to the user's organization."""
    target_org_id = x_organization_id or org_id
    scoped_org_id = await _resolve_user_organization(current_user, session, target_org_id)

    stmt = select(ComplianceTaskModel).where(
        ComplianceTaskModel.id == task_id,
        ComplianceTaskModel.organization_id == scoped_org_id,
    )
    task_model = (await session.execute(stmt)).scalar_one_or_none()
    if task_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Compliance task not found"
        )

    if payload.status is not None:
        task_model.status = (
            payload.status.value if hasattr(payload.status, "value") else str(payload.status)
        )
        task_model.is_completed = payload.status in (
            FilingStatus.FILED_ON_TIME,
            FilingStatus.FILED_LATE,
        )
    if payload.due_date is not None:
        task_model.due_date = str(payload.due_date)
    if payload.notes is not None:
        task_model.notes = payload.notes

    task_model.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(task_model)
    return _to_compliance_task_domain(task_model)


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_compliance_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    x_organization_id: int | None = Header(default=None, alias="X-Organization-ID"),
    org_id: int | None = Query(default=None),
) -> None:
    """Delete a task strictly scoped to the user's organization."""
    target_org_id = x_organization_id or org_id
    scoped_org_id = await _resolve_user_organization(current_user, session, target_org_id)

    stmt = select(ComplianceTaskModel).where(
        ComplianceTaskModel.id == task_id,
        ComplianceTaskModel.organization_id == scoped_org_id,
    )
    task_model = (await session.execute(stmt)).scalar_one_or_none()
    if task_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Compliance task not found"
        )

    await session.delete(task_model)
    await session.commit()
