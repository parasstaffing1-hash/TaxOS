"""Authentication API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from taxos.domain.iam.schema import UserCreate, UserResponse, TokenResponse
from taxos.application.iam.auth_service import AuthService
from taxos.api.dependencies.auth import get_auth_service, get_current_active_user
from taxos.infrastructure.database.models.iam import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Register a new user."""
    try:
        user = await auth_service.register_user(user_in)
        return user
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Assuming DB constraint violation for email uniqueness or similar
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Email might already be taken."
        )

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """OAuth2 compatible token login, getting an access token for future requests."""
    from taxos.domain.iam.schema import UserLogin
    
    # Map OAuth form to our schema
    login_data = UserLogin(email=form_data.username, password=form_data.password)
    
    token = await auth_service.login_user(login_data)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user information."""
    return current_user
