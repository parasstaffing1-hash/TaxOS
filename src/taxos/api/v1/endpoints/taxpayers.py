"""Taxpayer Profiles API Endpoints with Encryption and Multi-Tenancy Scoping."""

from __future__ import annotations

import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxos.api.dependencies.auth import get_current_active_user
from taxos.api.v1.deps import get_db
from taxos.api.v1.endpoints.compliance import _resolve_user_organization
from taxos.infrastructure.database.models.iam import User
from taxos.infrastructure.database.models.tax_models import TaxpayerProfileModel
from taxos.infrastructure.security.encryption import (
    encrypt_sensitive_field,
    mask_pan,
)

router = APIRouter(prefix="/taxpayers", tags=["Taxpayer Profiles"])


class TaxpayerProfileCreate(BaseModel):
    taxpayer_name: str = Field(min_length=2, max_length=255)
    pan: str | None = Field(default=None, pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
    gstin: str | None = Field(default=None, max_length=15)
    entity_type: str = Field(default="individual", max_length=64)
    jurisdiction: str = Field(default="IN", max_length=8)
    residential_status: str = Field(default="resident_ordinarily", max_length=64)


class TaxpayerProfileUpdate(BaseModel):
    taxpayer_name: str | None = Field(default=None, min_length=2, max_length=255)
    pan: str | None = Field(default=None, pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
    gstin: str | None = Field(default=None, max_length=15)
    entity_type: str | None = Field(default=None, max_length=64)
    residential_status: str | None = Field(default=None, max_length=64)


class TaxpayerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: int
    user_id: int
    taxpayer_name: str
    pan_masked: str | None = None
    gstin: str | None = None
    entity_type: str
    jurisdiction: str
    residential_status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


@router.get("", response_model=list[TaxpayerProfileResponse])
async def list_taxpayers(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    x_organization_id: int | None = Header(default=None, alias="X-Organization-ID"),
    org_id: int | None = Query(default=None),
) -> list[TaxpayerProfileModel]:
    """List taxpayer profiles scoped to the user's active organization."""
    target_org_id = x_organization_id or org_id
    scoped_org_id = await _resolve_user_organization(current_user, session, target_org_id)

    stmt = (
        select(TaxpayerProfileModel)
        .where(TaxpayerProfileModel.organization_id == scoped_org_id)
        .order_by(TaxpayerProfileModel.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=TaxpayerProfileResponse, status_code=201)
async def create_taxpayer(
    payload: TaxpayerProfileCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    x_organization_id: int | None = Header(default=None, alias="X-Organization-ID"),
    org_id: int | None = Query(default=None),
) -> TaxpayerProfileModel:
    """Create a new taxpayer profile with field encryption for PAN."""
    target_org_id = x_organization_id or org_id
    scoped_org_id = await _resolve_user_organization(current_user, session, target_org_id)

    pan_enc = encrypt_sensitive_field(payload.pan) if payload.pan else None
    pan_msk = mask_pan(payload.pan) if payload.pan else None

    profile = TaxpayerProfileModel(
        id=uuid4().hex,
        organization_id=scoped_org_id,
        user_id=current_user.id,
        taxpayer_name=payload.taxpayer_name,
        pan_encrypted=pan_enc,
        pan_masked=pan_msk,
        gstin=payload.gstin,
        entity_type=payload.entity_type,
        jurisdiction=payload.jurisdiction.upper(),
        residential_status=payload.residential_status,
        created_at=datetime.datetime.now(datetime.UTC),
        updated_at=datetime.datetime.now(datetime.UTC),
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


@router.get("/{taxpayer_id}", response_model=TaxpayerProfileResponse)
async def get_taxpayer(
    taxpayer_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    x_organization_id: int | None = Header(default=None, alias="X-Organization-ID"),
    org_id: int | None = Query(default=None),
) -> TaxpayerProfileModel:
    """Retrieve a taxpayer profile by ID scoped to the user's organization."""
    target_org_id = x_organization_id or org_id
    scoped_org_id = await _resolve_user_organization(current_user, session, target_org_id)

    stmt = select(TaxpayerProfileModel).where(
        TaxpayerProfileModel.id == taxpayer_id,
        TaxpayerProfileModel.organization_id == scoped_org_id,
    )
    profile = (await session.execute(stmt)).scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Taxpayer profile not found"
        )
    return profile


@router.patch("/{taxpayer_id}", response_model=TaxpayerProfileResponse)
async def update_taxpayer(  # noqa: PLR0917
    taxpayer_id: str,
    payload: TaxpayerProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    x_organization_id: int | None = Header(default=None, alias="X-Organization-ID"),
    org_id: int | None = Query(default=None),
) -> TaxpayerProfileModel:
    """Update an existing taxpayer profile."""
    target_org_id = x_organization_id or org_id
    scoped_org_id = await _resolve_user_organization(current_user, session, target_org_id)

    stmt = select(TaxpayerProfileModel).where(
        TaxpayerProfileModel.id == taxpayer_id,
        TaxpayerProfileModel.organization_id == scoped_org_id,
    )
    profile = (await session.execute(stmt)).scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Taxpayer profile not found"
        )

    if payload.taxpayer_name is not None:
        profile.taxpayer_name = payload.taxpayer_name
    if payload.pan is not None:
        profile.pan_encrypted = encrypt_sensitive_field(payload.pan)
        profile.pan_masked = mask_pan(payload.pan)
    if payload.gstin is not None:
        profile.gstin = payload.gstin
    if payload.entity_type is not None:
        profile.entity_type = payload.entity_type
    if payload.residential_status is not None:
        profile.residential_status = payload.residential_status

    profile.updated_at = datetime.datetime.now(datetime.UTC)
    await session.commit()
    await session.refresh(profile)
    return profile


@router.delete("/{taxpayer_id}", status_code=204)
async def delete_taxpayer(
    taxpayer_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
    x_organization_id: int | None = Header(default=None, alias="X-Organization-ID"),
    org_id: int | None = Query(default=None),
) -> None:
    """Delete a taxpayer profile scoped to the organization."""
    target_org_id = x_organization_id or org_id
    scoped_org_id = await _resolve_user_organization(current_user, session, target_org_id)

    stmt = select(TaxpayerProfileModel).where(
        TaxpayerProfileModel.id == taxpayer_id,
        TaxpayerProfileModel.organization_id == scoped_org_id,
    )
    profile = (await session.execute(stmt)).scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Taxpayer profile not found"
        )

    await session.delete(profile)
    await session.commit()
