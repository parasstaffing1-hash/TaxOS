"""Organization API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from taxos.domain.iam.schema import OrganizationCreate, OrganizationResponse, MembershipCreate, MembershipResponse
from taxos.application.iam.organization_service import OrganizationService
from taxos.api.dependencies.auth import get_organization_service, get_current_active_user
from taxos.api.v1.deps import get_db
from taxos.infrastructure.database.models.iam import Organization, User, OrganizationMember

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_in: OrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service)
) -> Organization:
    """Create a new organization and assign the creator as owner."""
    return await org_service.create_organization(org_in.name, current_user.id)

@router.get("", response_model=list[OrganizationResponse])
async def list_user_organizations(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
) -> list[Organization]:
    """List organizations the user belongs to."""
    stmt = (
        select(Organization)
        .join(OrganizationMember)
        .where(OrganizationMember.user_id == current_user.id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

@router.post("/{org_id}/invites", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
async def invite_user_to_organization(
    org_id: int,
    membership_in: MembershipCreate,
    current_user: User = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service),
    session: AsyncSession = Depends(get_db)
) -> OrganizationMember:
    """Invite an existing user to an organization."""
    # Check if current user is owner/admin
    stmt = select(OrganizationMember).where(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.organization_id == org_id,
        OrganizationMember.role.in_(["owner", "admin"])
    )
    res = await session.execute(stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not enough privileges")
        
    member = await org_service.invite_user(org_id, membership_in.email, membership_in.role)
    if not member:
        raise HTTPException(status_code=404, detail="User with this email not found.")
    return member
