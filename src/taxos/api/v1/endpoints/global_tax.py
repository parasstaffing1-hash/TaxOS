"""Global Multi-Jurisdiction Tax API Endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from taxos.domain.global_tax.engine import GlobalTaxEngine
from taxos.domain.global_tax.models import (
    CountryTaxProfile,
    GlobalCalculationInput,
    GlobalCalculationResult,
)

router = APIRouter(prefix="/global", tags=["Global Tax Engine"])


@router.get("/countries", response_model=list[CountryTaxProfile])
async def list_supported_global_countries() -> list[CountryTaxProfile]:
    """List all supported global country tax profiles and statutory rates."""
    engine = GlobalTaxEngine()
    return engine.list_supported_countries()


@router.post("/calculate", response_model=GlobalCalculationResult)
async def calculate_global_tax(payload: GlobalCalculationInput) -> GlobalCalculationResult:
    """Calculate personal income tax, corporate tax, or VAT for any supported country."""
    engine = GlobalTaxEngine()
    return engine.calculate(payload)
