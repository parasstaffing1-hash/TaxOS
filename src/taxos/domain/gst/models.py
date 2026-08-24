"""India GST (Goods and Services Tax) Domain Models."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class SupplyType(StrEnum):
    """Type of supply under GST."""

    INTRA_STATE = "intra_state"  # Same state: CGST + SGST (or UTGST)
    INTER_STATE = "inter_state"  # Different state / Export / Import / SEZ: IGST
    EXPORT_WITH_LUT = "export_with_lut"  # Zero-rated without payment of tax
    EXPORT_WITH_TAX = "export_with_tax"  # Zero-rated with payment of IGST


class GSTTransactionType(StrEnum):
    """Transaction direction."""

    B2B = "b2b"  # Business to Business
    B2C_LARGE = "b2c_large"  # Inter-state B2C > ₹2.5 Lakhs
    B2C_SMALL = "b2c_small"  # Intra-state or Inter-state <= ₹2.5 Lakhs
    EXPORT = "export"
    NIL_EXEMPT = "nil_exempt"
    NON_GST = "non_gst"


class GSTItem(BaseModel):
    """Individual line item in a GST calculation or invoice."""

    item_name: str
    hsn_sac_code: str | None = None
    quantity: Decimal = Decimal("1.0")
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0.0")
    gst_rate: Decimal = Field(
        description="e.g. 0.18 for 18%, 0.05 for 5%, 0.12 for 12%, 0.28 for 28%"
    )
    cess_rate: Decimal = Decimal("0.0")
    cess_amount: Decimal = Decimal("0.0")


class GSTCalculationResult(BaseModel):
    """Detailed GST computation result."""

    taxable_value: Decimal
    gst_rate_percent: Decimal
    supply_type: SupplyType

    cgst_rate_percent: Decimal = Decimal("0.0")
    cgst_amount: Decimal = Decimal("0.0")
    sgst_rate_percent: Decimal = Decimal("0.0")
    sgst_amount: Decimal = Decimal("0.0")
    igst_rate_percent: Decimal = Decimal("0.0")
    igst_amount: Decimal = Decimal("0.0")
    utgst_rate_percent: Decimal = Decimal("0.0")
    utgst_amount: Decimal = Decimal("0.0")
    cess_amount: Decimal = Decimal("0.0")

    total_gst_amount: Decimal
    gross_invoice_amount: Decimal
    round_off_adjustment: Decimal = Decimal("0.0")
    net_payable_amount: Decimal
    is_inclusive_calculation: bool = False
    explanation: str


class GSTINValidationResult(BaseModel):
    """Verification result for a 15-character GSTIN."""

    gstin: str
    is_valid: bool
    state_code: str | None = None
    state_name: str | None = None
    pan: str | None = None
    entity_code: str | None = None  # 1 to 9 or A to Z
    checksum_valid: bool = False
    error_message: str | None = None


class HSNCodeInfo(BaseModel):
    """HSN or SAC code specification."""

    code: str
    description: str
    standard_gst_rate: Decimal
    category: str  # "Goods" or "Services"
    compensation_cess_rate: Decimal = Decimal("0.0")
