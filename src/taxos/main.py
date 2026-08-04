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

from taxos.api.middleware import RequestIdMiddleware, register_exception_handlers
from taxos.api.v1.router import v1_router
from taxos.core.config import get_settings
from taxos.infrastructure.database.session import build_engine, build_session_factory
from taxos.infrastructure.logging.setup import configure_logging

logger = structlog.get_logger(__name__)


from taxos.application.updater.scheduler import UpdaterScheduler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle."""
    settings = get_settings()
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

    # Start updater scheduler
    scheduler = UpdaterScheduler(engine)
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("updater_scheduler_started")

    yield

    # Shutdown
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
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    from taxos.api.middleware import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestIdMiddleware)

    # ── Exception handlers ───────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ──────────────────────────────────────────────────
    app.include_router(v1_router, prefix=settings.API_V1_PREFIX)

    return app


# Module-level app instance for uvicorn
app = create_app()
