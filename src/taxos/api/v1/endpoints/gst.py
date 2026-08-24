"""India Goods & Services Tax (GST) API Endpoints."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from taxos.domain.gst.calculator import IndiaGSTEngine
from taxos.domain.gst.models import (
    GSTCalculationResult,
    GSTINValidationResult,
    HSNCodeInfo,
    SupplyType,
)
from taxos.domain.gst.validator import IndiaGSTValidator

router = APIRouter(prefix="/gst", tags=["India GST Engine"])


class GSTExclusivePayload(BaseModel):
    taxable_value: Decimal = Field(ge=0, description="Base amount before GST")
    gst_rate: Decimal = Field(
        default=Decimal("0.18"), description="e.g. 0.18 for 18%, 0.05 for 5%"
    )
    supply_type: SupplyType = SupplyType.INTRA_STATE
    cess_rate: Decimal = Decimal("0.0")
    is_union_territory: bool = False


class GSTInclusivePayload(BaseModel):
    gross_amount: Decimal = Field(ge=0, description="Inclusive MRP or total invoice value")
    gst_rate: Decimal = Field(
        default=Decimal("0.18"), description="e.g. 0.18 for 18%, 0.05 for 5%"
    )
    supply_type: SupplyType = SupplyType.INTRA_STATE
    cess_rate: Decimal = Decimal("0.0")
    is_union_territory: bool = False


class GSTINPayload(BaseModel):
    gstin: str = Field(description="15-character GSTIN to validate")


@router.post("/calculate-exclusive", response_model=GSTCalculationResult)
async def calculate_exclusive_gst(payload: GSTExclusivePayload) -> GSTCalculationResult:
    """Calculate CGST, SGST, IGST, UTGST, and Cess added on top of base taxable amount."""
    engine = IndiaGSTEngine()
    return engine.calculate_exclusive(
        taxable_value=payload.taxable_value,
        gst_rate=payload.gst_rate,
        supply_type=payload.supply_type,
        cess_rate=payload.cess_rate,
        is_union_territory=payload.is_union_territory,
    )


@router.post("/calculate-inclusive", response_model=GSTCalculationResult)
async def calculate_inclusive_gst(payload: GSTInclusivePayload) -> GSTCalculationResult:
    """Extract base price and GST components from an inclusive MRP price."""
    engine = IndiaGSTEngine()
    return engine.calculate_inclusive(
        gross_amount=payload.gross_amount,
        gst_rate=payload.gst_rate,
        supply_type=payload.supply_type,
        cess_rate=payload.cess_rate,
        is_union_territory=payload.is_union_territory,
    )


@router.post("/validate-gstin", response_model=GSTINValidationResult)
async def validate_gstin(payload: GSTINPayload) -> GSTINValidationResult:
    """Validate 15-character GSTIN with state code, PAN integrity, and Luhn Mod-36 checksum verification."""
    return IndiaGSTValidator.validate_gstin(payload.gstin)


@router.get("/hsn-search", response_model=list[HSNCodeInfo])
async def search_hsn_sac_codes(
    query: str = Query(
        description="Search by code (e.g. 998311, 8471) or description (e.g. software, laptop)"
    ),
) -> list[HSNCodeInfo]:
    """Search master directory of HSN (Goods) and SAC (Services) codes and rates."""
    return IndiaGSTValidator.search_hsn_sac(query)
