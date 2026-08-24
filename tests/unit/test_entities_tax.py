"""Unit tests for India Non-Individual Entities Tax and Presumptive Business Income."""

from decimal import Decimal

from taxos.domain.india.business_income import (
    IndiaPresumptiveTaxEngine,
    PresumptiveSchemeType,
    PresumptiveTaxInput,
)
from taxos.domain.india.entities import (
    EntityTaxInput,
    IndiaEntityTaxEngine,
    TaxpayerEntityType,
)


def test_partnership_firm_tax_calculation():
    """Verify flat 30% tax + 4% cess on Partnership Firm with profit under ₹1 Cr."""
    engine = IndiaEntityTaxEngine()
    # Profit ₹50 Lakhs -> 30% Base Tax = ₹15 Lakhs. 4% Cess = ₹60,000. Total = ₹15,60,000.
    inp = EntityTaxInput(
        entity_type=TaxpayerEntityType.PARTNERSHIP_FIRM,
        net_taxable_profit=Decimal("5000000.0"),
    )
    res = engine.calculate_entity_tax(inp)
    assert res.calculation["base_tax"] == Decimal("1500000.0")
    assert res.calculation["surcharge"] == Decimal("0.0")
    assert res.calculation["health_and_education_cess"] == Decimal("60000.0")
    assert res.calculation["total_tax_liability"] == Decimal("1560000.0")


def test_domestic_company_concessional_115baa():
    """Verify 22% tax + 10% mandatory surcharge + 4% cess u/s 115BAA for Domestic Company."""
    engine = IndiaEntityTaxEngine()
    # Profit ₹1 Crore -> 22% Base = ₹22 Lakhs. Surcharge 10% = ₹2.2 Lakhs. Tax = ₹24.2 Lakhs.
    # Cess 4% on 24.2L = ₹96,800. Total Tax = ₹25,16,800. (Effective rate = 25.168%).
    inp = EntityTaxInput(
        entity_type=TaxpayerEntityType.DOMESTIC_COMPANY,
        net_taxable_profit=Decimal("10000000.0"),
        is_concessional_115baa=True,
    )
    res = engine.calculate_entity_tax(inp)
    assert res.calculation["base_tax"] == Decimal("2200000.0")
    assert res.calculation["surcharge"] == Decimal("220000.0")
    assert res.calculation["health_and_education_cess"] == Decimal("96800.0")
    assert res.calculation["total_tax_liability"] == Decimal("2516800.0")


def test_presumptive_business_44ad_digital_vs_cash():
    """Verify Section 44AD 6% digital vs 8% cash deemed profit rates."""
    engine = IndiaPresumptiveTaxEngine()
    # ₹80L digital (6% = ₹4.8L) + ₹20L cash (8% = ₹1.6L). Total deemed profit = ₹6.4L.
    inp = PresumptiveTaxInput(
        scheme_type=PresumptiveSchemeType.SEC_44AD_BUSINESS,
        digital_turnover_or_receipts=Decimal("8000000.0"),
        cash_turnover_or_receipts=Decimal("2000000.0"),
    )
    res = engine.calculate_presumptive_income(inp)
    assert res.total_turnover_or_receipts == Decimal("10000000.0")
    assert res.minimum_presumed_income == Decimal("640000.0")
    assert res.taxable_business_income == Decimal("640000.0")


def test_presumptive_professional_44ada():
    """Verify Section 44ADA 50% deemed profit rate for professionals."""
    engine = IndiaPresumptiveTaxEngine()
    # Gross receipts ₹40 Lakhs -> 50% deemed profit = ₹20 Lakhs.
    inp = PresumptiveTaxInput(
        scheme_type=PresumptiveSchemeType.SEC_44ADA_PROFESSIONAL,
        digital_turnover_or_receipts=Decimal("4000000.0"),
    )
    res = engine.calculate_presumptive_income(inp)
    assert res.taxable_business_income == Decimal("2000000.0")
