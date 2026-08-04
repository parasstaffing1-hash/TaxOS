"""Universal Orchestration Engine for tax calculations."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from taxos.application.calculations.base import (
    CalculationContext,
    CalculationResult,
)
from taxos.application.calculations.plugins import (
    DeductionPlugin,
    FlatTaxPlugin,
    PayrollTaxPlugin,
    ProgressiveTaxPlugin,
    TaxCreditPlugin,
    TaxPlugin,
    VATPlugin,
)
from taxos.domain.financial.formulas import calculate_effective_tax_rate
from taxos.domain.rules import (
    DeductionRule,
    TaxCreditRule,
    TaxRule,
)


class UniversalTaxEngine:
    """Core calculation engine that orchestrates Tax Plugins across a context pipeline."""

    def __init__(self) -> None:
        self._plugins: list[TaxPlugin] = [
            ProgressiveTaxPlugin(),
            FlatTaxPlugin(),
            PayrollTaxPlugin(),
            DeductionPlugin(),
            TaxCreditPlugin(),
            VATPlugin(),
        ]

    def register_plugin(self, plugin: TaxPlugin) -> None:
        """Register a custom strategy plugin."""
        self._plugins.append(plugin)

    def calculate(self, gross_income: Decimal, rules: list[TaxRule]) -> dict[str, Any]:
        """
        Execute the strict tax calculation pipeline.
        
        Execution Order:
        1. Validation & Setup
        2. Deductions (lowers taxable income)
        3. Taxes (Progressive, Flat, Payroll, VAT)
        4. Credits (lowers final tax liability)
        5. Net Income & Frequencies Aggregation
        """
        context = CalculationContext.create(gross_income)

        # 1. Deductions
        deductions = [r for r in rules if isinstance(r, DeductionRule)]
        for d_rule in deductions:
            self._apply_rule(d_rule, context)

        # 2. Taxes
        taxes = [r for r in rules if not isinstance(r, (DeductionRule, TaxCreditRule))]
        for t_rule in taxes:
            self._apply_rule(t_rule, context)

        # 3. Credits
        credits = [r for r in rules if isinstance(r, TaxCreditRule)]
        for c_rule in credits:
            self._apply_rule(c_rule, context)

        # 4. Final Aggregations
        final_tax = max(Decimal("0.0"), context.total_tax - context.total_credits)
        net_income = max(Decimal("0.0"), context.gross_income - final_tax)
        effective_rate = calculate_effective_tax_rate(final_tax, context.gross_income)
        employee_deductions = context.total_deductions + final_tax

        return {
            "gross_income": self._build_frequencies(context.gross_income),
            "taxable_income": self._build_frequencies(context.taxable_income),
            "total_tax_before_credits": self._build_frequencies(context.total_tax),
            "total_credits": self._build_frequencies(context.total_credits),
            "final_tax": self._build_frequencies(final_tax),
            "net_income": self._build_frequencies(net_income),
            "employer_cost": self._build_frequencies(context.employer_cost),
            "employee_deductions": self._build_frequencies(employee_deductions),
            "effective_tax_rate": str(effective_rate),
            "breakdown": [
                {
                    "rule": res.rule_name,
                    "tax": str(res.tax_amount),
                    "deduction": str(res.deduction_amount),
                    "credit": str(res.credit_amount),
                    "employer_cost": str(res.employer_cost),
                    "details": res.details,
                }
                for res in context.results
            ],
        }

    def _apply_rule(self, rule: TaxRule, context: CalculationContext) -> None:
        """Find the applicable plugin for the rule and execute it."""
        for plugin in self._plugins:
            if plugin.can_handle(rule):
                result = plugin.calculate(rule, context)
                context.apply_result(result)
                return
        
        raise NotImplementedError(f"No plugin registered for rule type {type(rule)}")

    def _build_frequencies(self, annual_amount: Decimal) -> dict[str, str]:
        """Generate common time frequencies from an annual amount."""
        return {
            "annual": str(annual_amount),
            "monthly": str((annual_amount / 12).quantize(Decimal("0.01"))),
            "biweekly": str((annual_amount / 26).quantize(Decimal("0.01"))),
            "weekly": str((annual_amount / 52).quantize(Decimal("0.01"))),
            "daily": str((annual_amount / 260).quantize(Decimal("0.01"))),
            "hourly": str((annual_amount / 2080).quantize(Decimal("0.01"))),
        }
