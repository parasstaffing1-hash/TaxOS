"""Saved Calculations & Audit Trace Persistence API Endpoints."""

from __future__ import annotations

import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxos.api.dependencies.auth import get_current_active_user
from taxos.api.v1.deps import get_db
from taxos.api.v1.endpoints.compliance import _resolve_user_organization
from taxos.infrastructure.database.models.iam import User
from taxos.infrastructure.database.models.tax_models import SavedCalculationModel

router = APIRouter(prefix="/calculations", tags=["Saved Calculations"])


class SaveCalculationCreate(BaseModel):
    taxpayer_profile_id: str | None = None
    tool_id: str = Field(min_length=2, max_length=128)
    jurisdiction: str = Field(default="IN", max_length=8)
    financial_year: str = Field(min_length=4, max_length=16)
    assessment_year: str | None = Field(default=None, max_length=16)
    rule_version: str = Field(min_length=2, max_length=64)
    inputs: dict[str, Any]
    results: dict[str, Any]
    trace_steps: list[Any] = Field(default_factory=list)
    total_tax_payable: float = 0.0
    effective_tax_rate: float = 0.0
    is_favourite: bool = False


class SavedCalculationResponse(BaseModel):
    id: str
    organization_id: int
    user_id: int
    taxpayer_profile_id: str | None = None
    tool_id: str
    jurisdiction: str
    financial_year: str
    assessment_year: str | None = None
    rule_version: str
    inputs: dict[str, Any]
    results: dict[str, Any]
    trace_steps: list[Any] = Field(default_factory=list)
    total_tax_payable: float
    effective_tax_rate: float
    is_favourite: bool
    created_at: datetime.datetime


def _to_response_dto(model: SavedCalculationModel) -> SavedCalculationResponse:
    return SavedCalculationResponse(
        id=model.id,
        organization_id=model.organization_id,
        user_id=model.user_id,
        taxpayer_profile_id=model.taxpayer_profile_id,
        tool_id=model.tool_id,
        jurisdiction=model.jurisdiction,
        financial_year=model.financial_year,
        assessment_year=model.assessment_year,
        rule_version=model.rule_version,
        inputs=model.inputs_json,
        results=model.results_json,
        trace_steps=model.trace_steps_json,
        total_tax_payable=model.total_tax_payable,
        effective_tax_rate=model.effective_tax_rate,
        is_favourite=model.is_favourite,
        created_at=model.created_at,
    )


@router.get("", response_model=list[SavedCalculationResponse])
async def list_saved_calculations(  # noqa: PLR0917
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    x_organization_id: int | None = Header(default=None, alias="X-Organization-ID"),
    org_id: int | None = Query(default=None),
    tool_id: str | None = Query(default=None),
    jurisdiction: str | None = Query(default=None),
    is_favourite: bool | None = Query(default=None),
) -> list[SavedCalculationResponse]:
    """List saved calculations with optional filtering, scoped to organization."""
    target_org_id = x_organization_id or org_id
    scoped_org_id = await _resolve_user_organization(current_user, session, target_org_id)

    stmt = select(SavedCalculationModel).where(
        SavedCalculationModel.organization_id == scoped_org_id
    )

    if tool_id:
        stmt = stmt.where(SavedCalculationModel.tool_id == tool_id)
    if jurisdiction:
        stmt = stmt.where(SavedCalculationModel.jurisdiction == jurisdiction.upper())
    if is_favourite is not None:
        stmt = stmt.where(SavedCalculationModel.is_favourite == is_favourite)

    stmt = stmt.order_by(SavedCalculationModel.created_at.desc())
    result = await session.execute(stmt)
    records = result.scalars().all()
    return [_to_response_dto(r) for r in records]


@router.post("", response_model=SavedCalculationResponse, status_code=201)
async def save_calculation(
    payload: SaveCalculationCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    x_organization_id: int | None = Header(default=None, alias="X-Organization-ID"),
    org_id: int | None = Query(default=None),
) -> SavedCalculationResponse:
    """Save calculation snapshot with complete formula audit trail."""
    target_org_id = x_organization_id or org_id
    scoped_org_id = await _resolve_user_organization(current_user, session, target_org_id)

    model = SavedCalculationModel(
        id=uuid4().hex,
        organization_id=scoped_org_id,
        user_id=current_user.id,
        taxpayer_profile_id=payload.taxpayer_profile_id,
        tool_id=payload.tool_id,
        jurisdiction=payload.jurisdiction.upper(),
        financial_year=payload.financial_year,
        assessment_year=payload.assessment_year,
        rule_version=payload.rule_version,
        inputs_json=payload.inputs,
        results_json=payload.results,
        trace_steps_json=payload.trace_steps,
        total_tax_payable=payload.total_tax_payable,
        effective_tax_rate=payload.effective_tax_rate,
        is_favourite=payload.is_favourite,
        created_at=datetime.datetime.now(datetime.UTC),
    )
    session.add(model)
    await session.commit()
    await session.refresh(model)
    return _to_response_dto(model)


@router.get("/{calculation_id}", response_model=SavedCalculationResponse)
async def get_saved_calculation(
    calculation_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    x_organization_id: int | None = Header(default=None, alias="X-Organization-ID"),
    org_id: int | None = Query(default=None),
) -> SavedCalculationResponse:
    """Retrieve a single saved calculation audit trail."""
    target_org_id = x_organization_id or org_id
    scoped_org_id = await _resolve_user_organization(current_user, session, target_org_id)

    stmt = select(SavedCalculationModel).where(
        SavedCalculationModel.id == calculation_id,
        SavedCalculationModel.organization_id == scoped_org_id,
    )
    model = (await session.execute(stmt)).scalar_one_or_none()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved calculation not found"
        )
    return _to_response_dto(model)


@router.patch("/{calculation_id}/favourite", response_model=SavedCalculationResponse)
async def toggle_favourite_calculation(
    calculation_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    x_organization_id: int | None = Header(default=None, alias="X-Organization-ID"),
    org_id: int | None = Query(default=None),
) -> SavedCalculationResponse:
    """Toggle favourite bookmark flag on a saved calculation."""
    target_org_id = x_organization_id or org_id
    scoped_org_id = await _resolve_user_organization(current_user, session, target_org_id)

    stmt = select(SavedCalculationModel).where(
        SavedCalculationModel.id == calculation_id,
        SavedCalculationModel.organization_id == scoped_org_id,
    )
    model = (await session.execute(stmt)).scalar_one_or_none()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved calculation not found"
        )

    model.is_favourite = not model.is_favourite
    await session.commit()
    await session.refresh(model)
    return _to_response_dto(model)


@router.delete("/{calculation_id}", status_code=204)
async def delete_saved_calculation(
    calculation_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    x_organization_id: int | None = Header(default=None, alias="X-Organization-ID"),
    org_id: int | None = Query(default=None),
) -> None:
    """Delete a saved calculation."""
    target_org_id = x_organization_id or org_id
    scoped_org_id = await _resolve_user_organization(current_user, session, target_org_id)

    stmt = select(SavedCalculationModel).where(
        SavedCalculationModel.id == calculation_id,
        SavedCalculationModel.organization_id == scoped_org_id,
    )
    model = (await session.execute(stmt)).scalar_one_or_none()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved calculation not found"
        )

    await session.delete(model)
    await session.commit()
