"""FastAPI dependency injection providers.

Centralised dependency callables used across all
API endpoints via FastAPI's Depends() mechanism.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from taxos.application.services.health import HealthService
from taxos.core.config import Settings, get_settings


def get_app_settings() -> Settings:
    """Provide the application settings singleton."""
    return get_settings()


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession]:
    """Provide a database session from the app-level session factory."""
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_health_service(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> HealthService:
    """Provide the health check service."""
    return HealthService(settings=settings)


# ── Type aliases for cleaner endpoint signatures ─────────────────
SettingsDep = Annotated[Settings, Depends(get_app_settings)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]
