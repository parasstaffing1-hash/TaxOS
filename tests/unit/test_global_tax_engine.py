"""Unit tests for Global Multi-Jurisdiction Tax Engine."""

from decimal import Decimal

from taxos.domain.global_tax.engine import GlobalTaxEngine
from taxos.domain.global_tax.models import GlobalCalculationInput, GlobalTaxType


def test_us_income_tax_calculation():
    """Verify US federal income tax calculation with standard deduction."""
    engine = GlobalTaxEngine()
    # Gross $100,000. Std Ded $14,600 -> Taxable $85,400.
    # 0 - 11,600 @ 10% = 1,160
    # 11,600 - 47,150 @ 12% = 4,266
    # 47,150 - 85,400 @ 22% = 8,415
    # Base Tax = 13,841 + SS/Med (7.65% on $100k = $7,650) = $21,491
    inp = GlobalCalculationInput(
        country_code="US",
        gross_income_or_revenue=Decimal("100000.0"),
        tax_type=GlobalTaxType.INCOME_TAX,
    )
    res = engine.calculate(inp)

    assert res.country_code == "US"
    assert res.currency_code == "USD"
    assert res.taxable_basis == Decimal("85400.0")
    assert res.calculated_tax > Decimal("13000.0")
    assert res.net_after_tax < Decimal("100000.0")


def test_uk_vat_calculation():
    """Verify UK standard 20% VAT calculation."""
    engine = GlobalTaxEngine()
    inp = GlobalCalculationInput(
        country_code="GB",
        gross_income_or_revenue=Decimal("1000.0"),
        tax_type=GlobalTaxType.VAT_GST,
    )
    res = engine.calculate(inp)

    assert res.country_code == "GB"
    assert res.currency_code == "GBP"
    assert res.calculated_tax == Decimal("200.0")


def test_uae_corporate_tax_calculation():
    """Verify UAE 9% Corporate Tax above AED 375,000."""
    engine = GlobalTaxEngine()
    # Revenue/Profit AED 500,000 -> Taxable = 500,000. Tax = 9% on 500,000 = AED 45,000.
    inp = GlobalCalculationInput(
        country_code="AE",
        gross_income_or_revenue=Decimal("500000.0"),
        tax_type=GlobalTaxType.CORPORATE_TAX,
    )
    res = engine.calculate(inp)

    assert res.country_code == "AE"
    assert res.currency_code == "AED"
    assert res.calculated_tax == Decimal("45000.0")
