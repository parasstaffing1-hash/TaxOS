"""Shared test fixtures.

Provides async database engine (aiosqlite), session factory,
and FastAPI test client for all tests.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from taxos.core.config import Settings
from taxos.infrastructure.database import models


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    """Create a session-scoped event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Provide test-specific settings."""
    return Settings(
        APP_NAME="TaxOS-Test",
        ENVIRONMENT="testing",
        DATABASE_URL="sqlite+aiosqlite:///",
        LOG_LEVEL="DEBUG",
        LOG_FORMAT="console",
    )


@pytest.fixture(scope="session")
async def engine(test_settings: Settings) -> AsyncGenerator[AsyncEngine]:
    """Create a test database engine."""
    test_engine = create_async_engine(
        test_settings.DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with test_engine.begin() as conn:
        # Importing the package registers every ORM model before metadata is created.
        await conn.run_sync(models.User.metadata.create_all)

    yield test_engine

    async with test_engine.begin() as conn:
        await conn.run_sync(models.User.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def session(
    engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession]:
    """Provide a transactional test session that rolls back after each test."""
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as test_session:
        yield test_session
        await test_session.rollback()


@pytest.fixture
def setup_database(engine: AsyncEngine) -> None:
    """Ensure integration tests have a named database setup fixture."""
    del engine


@pytest.fixture
async def client(
    test_settings: Settings,
    engine: AsyncEngine,
) -> AsyncGenerator[AsyncClient]:
    """Provide an async HTTP test client."""
    from taxos.infrastructure.database.session import build_session_factory
    from taxos.main import create_app

    app = create_app()
    app.state.engine = engine
    app.state.session_factory = build_session_factory(engine)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
