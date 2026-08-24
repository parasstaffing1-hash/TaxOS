"""Golden test suite for India Personal Income Tax Engine (Old vs New Regime, 87A, Surcharge, Relief)."""

from decimal import Decimal

from taxos.domain.financial.trace import TaxRegime
from taxos.domain.india.income_tax import IndiaIncomeTaxEngine, round_to_10
from taxos.domain.india.models import IndiaIncomeTaxInput


def test_round_to_10():
    """Verify Section 288A/288B round off to nearest ₹10."""
    assert round_to_10(Decimal("1054.4")) == Decimal("1050")
    assert round_to_10(Decimal("1055.0")) == Decimal("1060")
    assert round_to_10(Decimal("1056.8")) == Decimal("1060")


def test_new_regime_zero_tax_up_to_7_lakhs_ay2025_26():
    """Golden Test 1: Salaried employee with ₹7,75,000 CTC has zero tax under AY 2025-26 New Regime.

    Gross Salary: ₹7,75,000
    Standard Deduction: ₹75,000
    Taxable Income: ₹7,00,000
    Tax before rebate: (3L-7L @ 5%) = ₹20,000
    Rebate u/s 87A: ₹20,000
    Total Tax: ₹0
    """
    engine = IndiaIncomeTaxEngine(assessment_year="2025-26")
    inp = IndiaIncomeTaxInput(
        salary_income=Decimal("775000.0"),
        assessment_year="2025-26",
    )
    res = engine.calculate_new_regime(inp)

    calc = res.calculation
    assert calc["gross_total_income"] == Decimal("700000.0")
    assert calc["standard_deduction"] == Decimal("75000.0")
    assert calc["taxable_income"] == Decimal("700000.0")
    assert calc["base_tax"] == Decimal("20000.0")
    assert calc["rebate_87a"] == Decimal("20000.0")
    assert calc["total_tax_liability"] == Decimal("0.0")


def test_new_regime_marginal_relief_slightly_above_7_lakhs():
    """Golden Test 2: Section 87A Marginal Relief in New Regime.

    If Taxable Income is ₹7,10,000 (₹10,000 above ₹7L threshold):
    Normal Tax on ₹7.1L:
      0 - 3L: Nil
      3L - 7L (4L @ 5%): ₹20,000
      7L - 7.1L (10k @ 10%): ₹1,000
      Base Tax = ₹21,000
    Without marginal relief, a person earning ₹10,000 extra would pay ₹21,000 tax + cess!
    Marginal Relief Rule: Tax payable cannot exceed excess income (₹7,10,000 - ₹7,00,000 = ₹10,000).
    Tax after rebate & marginal relief = ₹10,000.
    Cess @ 4% on ₹10,000 = ₹400.
    Total Tax = ₹10,400.
    """
    engine = IndiaIncomeTaxEngine(assessment_year="2025-26")
    inp = IndiaIncomeTaxInput(
        salary_income=Decimal("785000.0"),  # Gross 7.85L - 75k std ded = 7.10L taxable
        assessment_year="2025-26",
    )
    res = engine.calculate_new_regime(inp)
    calc = res.calculation

    assert calc["taxable_income"] == Decimal("710000.0")
    assert calc["base_tax"] == Decimal("21000.0")
    assert calc["rebate_87a"] == Decimal("11000.0")  # Marginal relief = 21,000 - 10,000 = 11,000
    assert calc["health_and_education_cess"] == Decimal("400.0")
    assert calc["total_tax_liability"] == Decimal("10400.0")


def test_old_vs_new_regime_high_deduction_scenario():
    """Golden Test 3: Old vs New Regime Comparator.

    Salary: ₹15,00,000
    80C: ₹1,50,000
    80D: ₹50,000
    80CCD(1B): ₹50,000
    HRA Exemption: ₹2,00,000
    Home Loan Interest (House Property Loss): -₹2,00,000

    Total Deductions in Old Regime: ₹50k (std ded) + ₹1.5L + ₹50k + ₹50k + ₹2L + ₹2L = ₹7,00,000.
    Taxable in Old: ₹8,00,000.
    """
    engine = IndiaIncomeTaxEngine(assessment_year="2025-26")
    inp = IndiaIncomeTaxInput(
        salary_income=Decimal("1300000.0"),  # Net salary after 2L HRA
        house_property_income=Decimal("-200000.0"),
        section_80c=Decimal("150000.0"),
        section_80d_self=Decimal("25000.0"),
        section_80d_parents=Decimal("25000.0"),
        section_80ccd_1b=Decimal("50000.0"),
        assessment_year="2025-26",
    )
    comparison = engine.compare_regimes(inp)

    assert comparison.old_regime_total_tax < comparison.new_regime_total_tax
    assert comparison.recommended_regime == TaxRegime.OLD
    assert comparison.tax_savings > 0


def test_surcharge_and_marginal_relief_high_net_worth():
    """Golden Test 4: Surcharge & Marginal Relief for income slightly over ₹50 Lakhs.

    Taxable Income = ₹50,50,000 (₹50k above ₹50L threshold).
    Tax + Surcharge cannot exceed (Tax on ₹50L + Excess ₹50,000).
    """
    engine = IndiaIncomeTaxEngine(assessment_year="2025-26")
    inp = IndiaIncomeTaxInput(
        salary_income=Decimal("5125000.0"),  # 51.25L - 75k std ded = 50.50L taxable
        assessment_year="2025-26",
    )
    res = engine.calculate_new_regime(inp)
    calc = res.calculation

    assert calc["taxable_income"] == Decimal("5050000.0")
    assert calc["surcharge"] > 0
    assert calc["surcharge_marginal_relief"] > 0
