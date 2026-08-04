"""Authentication dependencies for FastAPI."""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from taxos.infrastructure.database.models.iam import User
from taxos.api.v1.deps import get_db
from taxos.infrastructure.security.jwt import decode_access_token
from taxos.application.iam.auth_service import AuthService
from taxos.application.iam.organization_service import OrganizationService

# We use standard OAuth2 bearer flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(session)

def get_organization_service(session: AsyncSession = Depends(get_db)) -> OrganizationService:
    return OrganizationService(session)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    stmt = select(User).where(User.id == int(user_id))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
