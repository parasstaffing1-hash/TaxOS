"""API v1 aggregate router.

Collects all v1 endpoint routers into a single router
for mounting on the main application.
"""

from __future__ import annotations

from fastapi import APIRouter

from taxos.api.v1.endpoints import analytics, calculator, documents, dynamic_calculators, health, seo, updater, universal_calculator, verification, auth, organizations

v1_router = APIRouter()
v1_router.include_router(health.router)
v1_router.include_router(auth.router)
v1_router.include_router(organizations.router)
v1_router.include_router(calculator.router, prefix="/after-tax-salary-calculator")
v1_router.include_router(calculator.router, prefix="/paycheck-calculator")
v1_router.include_router(updater.router, prefix="/updater")
v1_router.include_router(seo.router, prefix="/seo")
v1_router.include_router(dynamic_calculators.router, prefix="/dynamic-calculators")
v1_router.include_router(analytics.router, prefix="/analytics")
v1_router.include_router(universal_calculator.router)
v1_router.include_router(verification.router)
v1_router.include_router(documents.router)
