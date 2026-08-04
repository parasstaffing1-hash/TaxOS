"""Performance benchmarks for the Universal Tax Calculation Engine."""

from __future__ import annotations

from decimal import Decimal

from taxos.application.calculations.engine import TaxCalculator
from taxos.domain.financial.validation import IncomeProfile
from taxos.domain.rules import (
    DeductionRule,
    PayrollTaxRule,
    ProgressiveTaxRule,
    TaxBracket,
    TaxCreditRule,
)


def build_complex_ruleset() -> list:
    """Build a complex set of rules typical for a full US tax calculation."""
    return [
        DeductionRule(
            name="Pre-tax 401k",
            amount=Decimal("0.05"),
            is_percentage=True,
            max_limit=Decimal("23000"),
        ),
        DeductionRule(name="Standard Deduction", amount=Decimal("14600")),
        PayrollTaxRule(
            name="Social Security",
            employee_rate=Decimal("0.062"),
            employer_rate=Decimal("0.062"),
            wage_base_limit=Decimal("168600"),
        ),
        PayrollTaxRule(
            name="Medicare", employee_rate=Decimal("0.0145"), employer_rate=Decimal("0.0145")
        ),
        ProgressiveTaxRule(
            name="Federal Income Tax",
            brackets=[
                TaxBracket(
                    min_amount=Decimal("0"), max_amount=Decimal("11600"), rate=Decimal("0.10")
                ),
                TaxBracket(
                    min_amount=Decimal("11600"), max_amount=Decimal("47150"), rate=Decimal("0.12")
                ),
                TaxBracket(
                    min_amount=Decimal("47150"), max_amount=Decimal("100525"), rate=Decimal("0.22")
                ),
                TaxBracket(
                    min_amount=Decimal("100525"),
                    max_amount=Decimal("191950"),
                    rate=Decimal("0.24"),
                ),
                TaxBracket(
                    min_amount=Decimal("191950"),
                    max_amount=Decimal("243725"),
                    rate=Decimal("0.32"),
                ),
                TaxBracket(min_amount=Decimal("243725"), rate=Decimal("0.35")),
            ],
        ),
        ProgressiveTaxRule(
            name="State Income Tax",
            brackets=[
                TaxBracket(
                    min_amount=Decimal("0"), max_amount=Decimal("10000"), rate=Decimal("0.04")
                ),
                TaxBracket(min_amount=Decimal("10000"), rate=Decimal("0.06")),
            ],
        ),
        TaxCreditRule(name="Child Tax Credit", amount=Decimal("2000"), is_refundable=True),
    ]


def run_calculations(calculator: TaxCalculator, rules: list, iterations: int) -> None:
    """Run the calculator multiple times to simulate batch payroll processing."""
    base_income = Decimal("50000")
    increment = Decimal("1000")

    for i in range(iterations):
        income = base_income + (increment * i)
        calculator.calculate(income, rules)


def test_calculation_engine_throughput(benchmark) -> None:
    """
    Benchmark the calculation engine.
    Tests how fast it can process 1,000 distinct complex tax calculations.
    """
    calculator = TaxCalculator()
    rules = build_complex_ruleset()

    # We benchmark running 1,000 full calculations
    benchmark(run_calculations, calculator, rules, 1000)


def run_validations(iterations: int) -> None:
    for i in range(iterations):
        IncomeProfile(salary=f"$ {50000 + i},000.50", bonus="1,000")


def test_validation_throughput(benchmark) -> None:
    """Benchmark the overhead of strict Pydantic parsing and sanitization."""
    benchmark(run_validations, 1000)
