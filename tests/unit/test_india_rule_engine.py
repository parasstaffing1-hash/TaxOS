"""Unit tests for India Income Tax calculation engine loaded from versioned rule packs."""

from decimal import Decimal

from taxos.domain.india.income_tax import IndiaIncomeTaxEngine
from taxos.domain.india.models import IndiaIncomeTaxInput


def test_ay_2024_25_rule_pack_calculation():
    """Verify AY 2024-25 calculation uses ₹50,000 standard deduction and 2024 slabs."""
    engine = IndiaIncomeTaxEngine(assessment_year="2024-25")
    # Gross salary ₹12,00,000 -> S/D ₹50,000 -> Taxable ₹11,50,000
    # Slabs 2024-25:
    # 0 - 3L: 0
    # 3L - 6L (3L @ 5%): 15,000
    # 6L - 9L (3L @ 10%): 30,000
    # 9L - 11.5L (2.5L @ 15%): 37,500
    # Base Tax = 82,500. 4% Cess = 3,300. Total = 85,800.
    inp = IndiaIncomeTaxInput(
        financial_year="2023-24",
        assessment_year="2024-25",
        salary_income=Decimal("1200000.0"),
    )
    result = engine.calculate_new_regime(inp)

    assert result.jurisdiction == "IN"
    assert result.rule_version == "IN-IT-2024.1"
    assert result.effective_date == "2024-04-01"
    assert len(result.official_sources) >= 2
    assert result.official_sources[0].url == "https://incometaxindia.gov.in"
    assert result.calculation["standard_deduction"] == Decimal("50000.0")
    assert result.calculation["taxable_income"] == Decimal("1150000.0")
    assert result.calculation["base_tax"] == Decimal("82500.0")
    assert result.calculation["health_and_education_cess"] == Decimal("3300.0")
    assert result.calculation["total_tax_liability"] == Decimal("85800.0")


def test_ay_2025_26_rule_pack_calculation():
    """Verify AY 2025-26 calculation uses ₹75,000 standard deduction and Budget 2024 slabs."""
    engine = IndiaIncomeTaxEngine(assessment_year="2025-26")
    # Gross salary ₹12,00,000 -> S/D ₹75,000 -> Taxable ₹11,25,000
    # Slabs 2025-26:
    # 0 - 3L: 0
    # 3L - 7L (4L @ 5%): 20,000
    # 7L - 10L (3L @ 10%): 30,000
    # 10L - 11.25L (1.25L @ 15%): 18,750
    # Base Tax = 68,750. 4% Cess = 2,750. Total = 71,500.
    inp = IndiaIncomeTaxInput(
        financial_year="2024-25",
        assessment_year="2025-26",
        salary_income=Decimal("1200000.0"),
    )
    result = engine.calculate_new_regime(inp)

    assert result.rule_version == "IN-IT-2025.1"
    assert result.effective_date == "2025-04-01"
    assert result.calculation["standard_deduction"] == Decimal("75000.0")
    assert result.calculation["taxable_income"] == Decimal("1125000.0")
    assert result.calculation["base_tax"] == Decimal("68750.0")
    assert result.calculation["health_and_education_cess"] == Decimal("2750.0")
    assert result.calculation["total_tax_liability"] == Decimal("71500.0")


def test_ay_2025_26_marginal_relief_boundary():
    """Verify 87A rebate & marginal relief boundary cases in AY 2025-26."""
    engine = IndiaIncomeTaxEngine(assessment_year="2025-26")

    # Case 1: Taxable income exactly ₹7,00,000 -> ₹0 Tax Liability
    inp_7l = IndiaIncomeTaxInput(
        financial_year="2024-25",
        assessment_year="2025-26",
        salary_income=Decimal("775000.0"),  # S/D ₹75k -> Taxable ₹7L
    )
    res_7l = engine.calculate_new_regime(inp_7l)
    assert res_7l.calculation["taxable_income"] == Decimal("700000.0")
    assert res_7l.calculation["total_tax_liability"] == Decimal("0.0")

    # Case 2: Taxable income ₹7,20,000 (Excess over 7L is ₹20,000)
    # Slab tax before rebate = ₹20,000 (3-7L) + ₹2,000 (7-7.2L) = ₹22,000.
    # Marginal relief = 22,000 - 20,000 = ₹2,000.
    # Tax after rebate = ₹20,000. Cess 4% = ₹800. Total Tax = ₹20,800.
    inp_720k = IndiaIncomeTaxInput(
        financial_year="2024-25",
        assessment_year="2025-26",
        salary_income=Decimal("795000.0"),  # S/D ₹75k -> Taxable ₹7.2L
    )
    res_720k = engine.calculate_new_regime(inp_720k)
    assert res_720k.calculation["taxable_income"] == Decimal("720000.0")
    assert res_720k.calculation["base_tax"] == Decimal("22000.0")
    assert res_720k.calculation["rebate_87a"] == Decimal("2000.0")
    assert res_720k.calculation["total_tax_liability"] == Decimal("20800.0")
