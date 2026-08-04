"""Base interfaces and context for calculation strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from taxos.domain.rules import TaxRule


@dataclass
class CalculationResult:
    """The result of applying a single tax rule."""

    rule_name: str
    tax_amount: Decimal = Decimal("0.0")
    deduction_amount: Decimal = Decimal("0.0")
    cash_deduction_amount: Decimal = Decimal("0.0")
    credit_amount: Decimal = Decimal("0.0")
    employer_cost: Decimal = Decimal("0.0")
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class CalculationContext:
    """State context passed between strategies during calculation."""

    gross_income: Decimal
    taxable_income: Decimal  # Mutated by deductions
    total_tax: Decimal = Decimal("0.0")
    total_deductions: Decimal = Decimal("0.0")
    total_cash_deductions: Decimal = Decimal("0.0")
    total_credits: Decimal = Decimal("0.0")
    employer_cost: Decimal = Decimal("0.0")
    results: list[CalculationResult] = field(default_factory=list)

    @classmethod
    def create(cls, gross_income: Decimal) -> CalculationContext:
        """Initialize a new calculation context."""
        return cls(
            gross_income=gross_income,
            taxable_income=gross_income,
        )

    def apply_result(self, result: CalculationResult) -> None:
        """Apply a result to the running totals."""
        self.total_tax += result.tax_amount
        self.total_deductions += result.deduction_amount
        self.total_cash_deductions += result.cash_deduction_amount
        self.total_credits += result.credit_amount
        self.employer_cost += result.employer_cost

        # Deductions lower the taxable income for subsequent calculations
        self.taxable_income -= result.deduction_amount
        if self.taxable_income < 0:
            self.taxable_income = Decimal("0.0")

        self.results.append(result)


class AbstractCalculationStrategy(ABC):
    """Base interface for all tax calculation strategies."""

    @abstractmethod
    def calculate(self, rule: TaxRule, context: CalculationContext) -> CalculationResult:
        """
        Calculate the tax, deduction, or credit based on the rule and current context.

        Args:
            rule: The tax rule to apply.
            context: The current calculation state.

        Returns:
            The calculated result.
        """
        ...
