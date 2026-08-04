"""Application service for organization management."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from taxos.infrastructure.database.models.iam import Organization, OrganizationMember, User

class OrganizationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_organization(self, name: str, owner_id: int) -> Organization:
        org = Organization(name=name)
        self.session.add(org)
        await self.session.commit()
        await self.session.refresh(org)
        
        member = OrganizationMember(user_id=owner_id, organization_id=org.id, role="owner")
        self.session.add(member)
        await self.session.commit()
        return org

    async def invite_user(self, org_id: int, email: str, role: str) -> OrganizationMember | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return None
            
        member = OrganizationMember(user_id=user.id, organization_id=org_id, role=role)
        self.session.add(member)
        await self.session.commit()
        await self.session.refresh(member)
        return member
