from decimal import Decimal

from taxos.domain.financial.formulas import (
    apply_bankers_rounding,
    calculate_effective_tax_rate,
    calculate_flat_tax,
    calculate_payroll_tax,
    calculate_progressive_tax,
    calculate_vat,
)
from taxos.domain.rules import TaxBracket


def test_apply_bankers_rounding():
    assert apply_bankers_rounding(Decimal("2.555"), 2) == Decimal("2.56")
    assert apply_bankers_rounding(Decimal("2.545"), 2) == Decimal("2.54")  # half-even


def test_calculate_progressive_tax():
    brackets = [
        TaxBracket(min_amount=Decimal("0"), max_amount=Decimal("100"), rate=Decimal("0.10")),
        TaxBracket(min_amount=Decimal("100"), max_amount=None, rate=Decimal("0.20")),
    ]
    tax, details = calculate_progressive_tax(Decimal("200"), brackets)
    # first 100 at 10% = 10
    # next 100 at 20% = 20
    # total = 30
    assert tax == Decimal("30.00")
    assert len(details) == 2


def test_calculate_flat_tax():
    tax = calculate_flat_tax(Decimal("100"), Decimal("0.15"))
    assert tax == Decimal("15.00")


def test_calculate_payroll_tax():
    emp, er = calculate_payroll_tax(
        Decimal("200"), Decimal("0.05"), Decimal("0.10"), Decimal("100")
    )
    assert emp == Decimal("5.00")  # Capped at 100
    assert er == Decimal("10.00")


def test_calculate_vat():
    vat = calculate_vat(Decimal("100"), Decimal("0.20"))
    assert vat == Decimal("20.00")


def test_effective_tax_rate():
    rate = calculate_effective_tax_rate(Decimal("30"), Decimal("200"))
    assert rate == Decimal("0.1500")
