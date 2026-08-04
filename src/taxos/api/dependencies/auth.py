"""Authentication dependencies for FastAPI."""

from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxos.api.v1.deps import get_db
from taxos.application.iam.auth_service import AuthService
from taxos.application.iam.organization_service import OrganizationService
from taxos.core.config import get_settings
from taxos.infrastructure.database.models.iam import User
from taxos.infrastructure.security.jwt import decode_access_token

# We use standard OAuth2 bearer flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(session)


def get_organization_service(session: AsyncSession = Depends(get_db)) -> OrganizationService:
    return OrganizationService(session)


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    access_token = token or request.cookies.get(get_settings().AUTH_COOKIE_NAME)
    if not access_token:
        raise credentials_exception

    try:
        payload = decode_access_token(access_token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise credentials_exception from exc

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


async def get_current_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Require an explicitly configured, active administrator account."""
    admin_emails = get_settings().admin_emails
    if not admin_emails or current_user.email.lower() not in admin_emails:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
