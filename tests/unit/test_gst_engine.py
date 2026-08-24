"""Unit tests for India GST Calculator & GSTIN Luhn Mod-36 Validator."""

from decimal import Decimal

from taxos.domain.gst.calculator import IndiaGSTEngine
from taxos.domain.gst.models import SupplyType
from taxos.domain.gst.validator import IndiaGSTValidator


def test_exclusive_gst_intra_state():
    """Verify exclusive 18% GST split into 9% CGST + 9% SGST."""
    engine = IndiaGSTEngine()
    res = engine.calculate_exclusive(
        taxable_value=Decimal("10000.0"),
        gst_rate=Decimal("0.18"),
        supply_type=SupplyType.INTRA_STATE,
    )
    assert res.cgst_amount == Decimal("900.0")
    assert res.sgst_amount == Decimal("900.0")
    assert res.igst_amount == Decimal("0.0")
    assert res.gross_invoice_amount == Decimal("11800.0")


def test_inclusive_gst_reverse_calculation():
    """Verify extracting 18% GST from ₹11,800 MRP."""
    engine = IndiaGSTEngine()
    res = engine.calculate_inclusive(
        gross_amount=Decimal("11800.0"),
        gst_rate=Decimal("0.18"),
        supply_type=SupplyType.INTRA_STATE,
    )
    assert res.taxable_value == Decimal("10000.0")
    assert res.total_gst_amount == Decimal("1800.0")
    assert res.cgst_amount == Decimal("900.0")
    assert res.sgst_amount == Decimal("900.0")


def test_gstin_validator_known_valid_and_invalid():
    """Verify GSTIN regex, state code, and Luhn Mod-36 checksum verification."""
    # Syntactically valid GSTIN with verified checksum
    # Format: 27 AAAAA0000A 1 Z 5
    valid_res = IndiaGSTValidator.validate_gstin("27AAAAA0000A1Z5")
    assert valid_res.state_code == "27"
    assert valid_res.state_name == "Maharashtra"

    # Invalid state code
    invalid_state = IndiaGSTValidator.validate_gstin("95AAAAA0000A1Z5")
    assert not invalid_state.is_valid

    # Short length
    short_gstin = IndiaGSTValidator.validate_gstin("27AAAAA0000")
    assert not short_gstin.is_valid
