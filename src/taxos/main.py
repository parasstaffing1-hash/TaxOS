"""FastAPI application factory.

Creates and configures the FastAPI application instance
with all middleware, routers, and lifespan management.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from taxos.api.middleware import (
    RateLimitMiddleware,
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
    register_exception_handlers,
)
from taxos.api.v1.router import create_v1_router
from taxos.application.updater.scheduler import UpdaterScheduler
from taxos.core.config import get_settings
from taxos.infrastructure.database.session import build_engine, build_session_factory
from taxos.infrastructure.logging.setup import configure_logging

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle."""
    settings = get_settings()
    app.state.settings = settings
    configure_logging(settings)

    logger.info(
        "application_starting",
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        version=settings.APP_VERSION,
    )

    # Initialise database
    engine = build_engine(settings)
    app.state.engine = engine
    app.state.session_factory = build_session_factory(engine)

    logger.info("database_engine_created")

    scheduler: UpdaterScheduler | None = None
    if settings.internal_tools_enabled:
        scheduler = UpdaterScheduler(engine)
        scheduler.start()
        logger.info("updater_scheduler_started")
    app.state.scheduler = scheduler

    yield

    # Shutdown
    if app.state.scheduler is not None:
        app.state.scheduler.shutdown()
        logger.info("updater_scheduler_shutdown")

    await engine.dispose()
    logger.info("application_shutdown_complete")


def create_app() -> FastAPI:
    """Build the configured FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Enterprise Tax Calculation Platform",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = settings

    # ── Middleware ────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    # ── Exception handlers ───────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ──────────────────────────────────────────────────
    app.include_router(create_v1_router(settings), prefix=settings.API_V1_PREFIX)

    return app


# Module-level app instance for uvicorn
app = create_app()
