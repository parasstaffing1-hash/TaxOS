"""Authentication API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from taxos.api.dependencies.auth import get_auth_service, get_current_active_user
from taxos.application.iam.auth_service import AuthService
from taxos.core.config import get_settings
from taxos.domain.iam.schema import TokenResponse, UserCreate, UserLogin, UserResponse
from taxos.infrastructure.database.models.iam import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Register a new user."""
    try:
        return await auth_service.register_user(user_in)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """OAuth2 compatible token login, getting an access token for future requests."""
    # Map OAuth form to our schema
    login_data = UserLogin(email=form_data.username, password=form_data.password)

    token = await auth_service.login_user(login_data)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    settings = get_settings()
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token.access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        domain=settings.AUTH_COOKIE_DOMAIN,
        path="/",
    )
    return token


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> Response:
    """Clear the browser session cookie while keeping bearer-token clients compatible."""
    settings = get_settings()
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        domain=settings.AUTH_COOKIE_DOMAIN,
        path="/",
    )
    return response


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current user information."""
    return current_user
