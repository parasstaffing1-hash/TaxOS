"""API v1 router construction."""

from __future__ import annotations

from fastapi import APIRouter

from taxos.api.v1.endpoints import (
    analytics,
    auth,
    calculator,
    catalog,
    compliance,
    documents,
    dynamic_calculators,
    global_tax,
    gst,
    health,
    india_tax,
    organizations,
    reconciliation,
    saved_calculations,
    seo,
    taxpayers,
    universal_calculator,
    updater,
    verification,
)
from taxos.core.config import Settings


def create_v1_router(settings: Settings) -> APIRouter:
    """Create the public API surface for the current deployment settings."""
    router = APIRouter()
    router.include_router(health.router)
    router.include_router(auth.router)
    router.include_router(organizations.router)
    router.include_router(taxpayers.router)
    router.include_router(saved_calculations.router)
    router.include_router(catalog.router)
    router.include_router(india_tax.router)
    router.include_router(gst.router)
    router.include_router(reconciliation.router)
    router.include_router(global_tax.router)
    router.include_router(compliance.router)
    router.include_router(calculator.router, prefix="/after-tax-salary-calculator")
    router.include_router(calculator.router, prefix="/paycheck-calculator")
    router.include_router(seo.router, prefix="/seo")
    router.include_router(dynamic_calculators.router, prefix="/dynamic-calculators")
    router.include_router(universal_calculator.router)
    router.include_router(documents.router)

    if settings.internal_tools_enabled:
        router.include_router(updater.router, prefix="/updater")
        router.include_router(analytics.router, prefix="/analytics")
        router.include_router(verification.router)

    return router
