"""Application service for authentication."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxos.domain.iam.schema import TokenResponse, UserCreate, UserLogin
from taxos.infrastructure.database.models.iam import User
from taxos.infrastructure.security.crypto import get_password_hash, verify_password
from taxos.infrastructure.security.jwt import create_access_token


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_user(self, user_in: UserCreate) -> User:
        hashed = get_password_hash(user_in.password)
        new_user = User(email=user_in.email, hashed_password=hashed)
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user

    async def login_user(self, login_in: UserLogin) -> TokenResponse | None:
        stmt = select(User).where(User.email == login_in.email)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(login_in.password, user.hashed_password):
            return None

        token = create_access_token(data={"sub": str(user.id)})
        return TokenResponse(access_token=token)
