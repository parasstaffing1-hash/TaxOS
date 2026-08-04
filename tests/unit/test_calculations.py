"""Unit tests for the Universal Tax Calculation Engine."""

from __future__ import annotations

from decimal import Decimal

import pytest

from taxos.application.calculations.engine import TaxCalculator
from taxos.application.calculations.utils import round_currency
from taxos.domain.rules import (
    DeductionRule,
    FlatTaxRule,
    PayrollTaxRule,
    ProgressiveTaxRule,
    TaxBracket,
    TaxCreditRule,
)


@pytest.fixture
def calculator() -> TaxCalculator:
    return TaxCalculator()


class TestTaxCalculations:
    """Boundary and module tests for calculation strategies."""

    def test_progressive_tax_exact_boundaries(self, calculator: TaxCalculator) -> None:
        """Test income sitting exactly on bracket edges."""
        rule = ProgressiveTaxRule(
            name="Federal Progressive",
            brackets=[
                TaxBracket(
                    min_amount=Decimal("0"), max_amount=Decimal("10000"), rate=Decimal("0.10")
                ),
                TaxBracket(
                    min_amount=Decimal("10000"), max_amount=Decimal("40000"), rate=Decimal("0.20")
                ),
                TaxBracket(min_amount=Decimal("40000"), rate=Decimal("0.30")),
            ],
        )

        # Test 1: Exactly at the first bracket boundary (10,000 * 10% = 1,000)
        res1 = calculator.calculate(Decimal("10000"), [rule])
        assert Decimal(res1["final_tax"]) == Decimal("1000.00")

        # Test 2: Exactly at second boundary (10k@10% = 1k, 30k@20% = 6k -> 7k total)
        res2 = calculator.calculate(Decimal("40000"), [rule])
        assert Decimal(res2["final_tax"]) == Decimal("7000.00")

        # Test 3: Above last boundary (7k + 10k@30% = 3k -> 10k total)
        res3 = calculator.calculate(Decimal("50000"), [rule])
        assert Decimal(res3["final_tax"]) == Decimal("10000.00")

    def test_flat_tax(self, calculator: TaxCalculator) -> None:
        """Test simple flat tax strategy."""
        rule = FlatTaxRule(name="State Flat", rate=Decimal("0.05"))
        res = calculator.calculate(Decimal("50000"), [rule])
        assert Decimal(res["final_tax"]) == Decimal("2500.00")

    def test_deductions_lower_taxable_income(self, calculator: TaxCalculator) -> None:
        """Test that deductions are processed first and lower the taxable basis."""
        deduction = DeductionRule(name="Standard Deduction", amount=Decimal("10000"))
        flat_tax = FlatTaxRule(name="Flat", rate=Decimal("0.10"))

        # 50k - 10k deduction = 40k taxable * 10% = 4k tax
        res = calculator.calculate(Decimal("50000"), [deduction, flat_tax])

        assert Decimal(res["taxable_income"]) == Decimal("40000.00")
        assert Decimal(res["total_deductions"]) == Decimal("10000.00")
        assert Decimal(res["final_tax"]) == Decimal("4000.00")

    def test_percentage_deduction_with_cap(self, calculator: TaxCalculator) -> None:
        """Test percentage-based deduction with a maximum cap."""
        # 20% deduction, max 5k
        deduction = DeductionRule(
            name="Pension", amount=Decimal("0.20"), is_percentage=True, max_limit=Decimal("5000")
        )
        flat_tax = FlatTaxRule(name="Flat", rate=Decimal("0.10"))

        # 100k * 20% = 20k (capped at 5k) -> 95k taxable * 10% = 9.5k tax
        res = calculator.calculate(Decimal("100000"), [deduction, flat_tax])

        assert Decimal(res["taxable_income"]) == Decimal("95000.00")
        assert Decimal(res["total_deductions"]) == Decimal("5000.00")
        assert Decimal(res["final_tax"]) == Decimal("9500.00")

    def test_tax_credits(self, calculator: TaxCalculator) -> None:
        """Test non-refundable and refundable credits."""
        tax = FlatTaxRule(name="Tax", rate=Decimal("0.10"))
        credit_non_ref = TaxCreditRule(name="NonRef", amount=Decimal("6000"), is_refundable=False)
        credit_ref = TaxCreditRule(name="Ref", amount=Decimal("2000"), is_refundable=True)

        # Income 50k -> Tax 5k
        # Apply non-refundable 6k -> Should only wipe out the 5k, leaving 0 tax
        res1 = calculator.calculate(Decimal("50000"), [tax, credit_non_ref])
        assert Decimal(res1["total_tax_before_credits"]) == Decimal("5000.00")
        assert Decimal(res1["total_credits"]) == Decimal("5000.00")  # Capped at tax liability
        assert Decimal(res1["final_tax"]) == Decimal("0.00")

        # Income 50k -> Tax 5k
        # Apply refundable 2k -> Should reduce tax to 3k
        res2 = calculator.calculate(Decimal("50000"), [tax, credit_ref])
        assert Decimal(res2["total_tax_before_credits"]) == Decimal("5000.00")
        assert Decimal(res2["total_credits"]) == Decimal("2000.00")
        assert Decimal(res2["final_tax"]) == Decimal("3000.00")

    def test_payroll_wage_base_limit(self, calculator: TaxCalculator) -> None:
        """Test payroll taxes capping out at wage base limit."""
        ss_tax = PayrollTaxRule(
            name="Social Security",
            employee_rate=Decimal("0.062"),
            employer_rate=Decimal("0.062"),
            wage_base_limit=Decimal("168600"),
        )

        # Below cap: 100k * 6.2% = 6200
        res1 = calculator.calculate(Decimal("100000"), [ss_tax])
        assert Decimal(res1["final_tax"]) == Decimal("6200.00")

        # Above cap: 200k capped at 168600 * 6.2% = 10453.20
        res2 = calculator.calculate(Decimal("200000"), [ss_tax])
        assert Decimal(res2["final_tax"]) == Decimal("10453.20")

    def test_rounding_rules(self) -> None:
        """Test that round_half_up currency logic works."""
        assert round_currency(Decimal("1.005")) == Decimal("1.01")
        assert round_currency(Decimal("1.004")) == Decimal("1.00")
        assert round_currency(Decimal("1.005"), rounding="ROUND_DOWN") == Decimal("1.00")
