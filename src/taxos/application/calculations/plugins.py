"""Tax Plugin Architecture.

Maps domain rules to the Universal Formula Engine.
"""

from __future__ import annotations

from typing import Protocol, Any

from taxos.application.calculations.base import CalculationContext, CalculationResult
from taxos.domain.financial.formulas import (
    calculate_flat_tax,
    calculate_payroll_tax,
    calculate_progressive_tax,
    calculate_vat,
    apply_bankers_rounding,
)
from taxos.domain.rules import (
    DeductionRule,
    FlatTaxRule,
    PayrollTaxRule,
    ProgressiveTaxRule,
    TaxCreditRule,
    TaxRule,
    VATRule,
)


class TaxPlugin(Protocol):
    """Interface for all tax calculation plugins."""
    
    def can_handle(self, rule: TaxRule) -> bool:
        """Return True if this plugin can process the given rule."""
        ...
        
    def calculate(self, rule: TaxRule, context: CalculationContext) -> CalculationResult:
        """Process the rule and return a CalculationResult."""
        ...


class ProgressiveTaxPlugin:
    def can_handle(self, rule: TaxRule) -> bool:
        return isinstance(rule, ProgressiveTaxRule)

    def calculate(self, rule: TaxRule, context: CalculationContext) -> CalculationResult:
        assert isinstance(rule, ProgressiveTaxRule)
        tax, details = calculate_progressive_tax(context.taxable_income, rule.brackets)
        return CalculationResult(rule_name=rule.name, tax_amount=tax, details={"brackets_applied": details})


class FlatTaxPlugin:
    def can_handle(self, rule: TaxRule) -> bool:
        return isinstance(rule, FlatTaxRule)

    def calculate(self, rule: TaxRule, context: CalculationContext) -> CalculationResult:
        assert isinstance(rule, FlatTaxRule)
        tax = calculate_flat_tax(context.taxable_income, rule.rate)
        return CalculationResult(
            rule_name=rule.name,
            tax_amount=tax,
            details={"rate": str(rule.rate), "basis": str(context.taxable_income)},
        )


class DeductionPlugin:
    def can_handle(self, rule: TaxRule) -> bool:
        return isinstance(rule, DeductionRule)

    def calculate(self, rule: TaxRule, context: CalculationContext) -> CalculationResult:
        assert isinstance(rule, DeductionRule)
        if rule.is_percentage:
            deduction = apply_bankers_rounding(context.gross_income * rule.amount)
        else:
            deduction = rule.amount

        if rule.max_limit is not None:
            deduction = min(deduction, rule.max_limit)

        actual_deduction = min(deduction, context.taxable_income)
        return CalculationResult(
            rule_name=rule.name,
            deduction_amount=actual_deduction,
            details={"calculated_deduction": str(deduction), "actual_deduction": str(actual_deduction)},
        )


class TaxCreditPlugin:
    def can_handle(self, rule: TaxRule) -> bool:
        return isinstance(rule, TaxCreditRule)

    def calculate(self, rule: TaxRule, context: CalculationContext) -> CalculationResult:
        assert isinstance(rule, TaxCreditRule)
        credit = rule.amount
        if rule.max_limit is not None:
            credit = min(credit, rule.max_limit)

        if not rule.is_refundable:
            credit = min(credit, context.total_tax)

        return CalculationResult(
            rule_name=rule.name, credit_amount=credit, details={"refundable": rule.is_refundable}
        )


class PayrollTaxPlugin:
    def can_handle(self, rule: TaxRule) -> bool:
        return isinstance(rule, PayrollTaxRule)

    def calculate(self, rule: TaxRule, context: CalculationContext) -> CalculationResult:
        assert isinstance(rule, PayrollTaxRule)
        employee_tax, employer_tax = calculate_payroll_tax(
            context.gross_income, rule.employee_rate, rule.employer_rate, rule.wage_base_limit
        )

        return CalculationResult(
            rule_name=rule.name,
            tax_amount=employee_tax,
            employer_cost=employer_tax,
            details={
                "employer_portion": str(employer_tax),
                "employee_portion": str(employee_tax),
            },
        )


class VATPlugin:
    def can_handle(self, rule: TaxRule) -> bool:
        return isinstance(rule, VATRule)

    def calculate(self, rule: TaxRule, context: CalculationContext) -> CalculationResult:
        assert isinstance(rule, VATRule)
        tax = calculate_vat(context.gross_income, rule.standard_rate)
        return CalculationResult(
            rule_name=rule.name, tax_amount=tax, details={"rate": str(rule.standard_rate)}
        )
