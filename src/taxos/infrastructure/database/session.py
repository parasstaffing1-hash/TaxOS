"""Async database engine and session management.

Provides the async engine factory and session generator
for dependency injection throughout the application.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from taxos.core.config import Settings


def build_engine(settings: Settings) -> AsyncEngine:
    """Create a configured async SQLAlchemy engine."""
    engine_options: dict[str, object] = {
        "echo": settings.DATABASE_ECHO,
        "pool_pre_ping": True,
    }
    if not settings.DATABASE_URL.startswith("sqlite"):
        engine_options.update(
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
        )
    return create_async_engine(settings.DATABASE_URL, **engine_options)


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory bound to the given engine."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    """Yield an async session and ensure cleanup."""
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
