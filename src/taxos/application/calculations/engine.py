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
from taxos.domain.financial.formulas import (
    apply_bankers_rounding,
    calculate_effective_tax_rate,
)
from taxos.domain.rules import (
    ApplicableTaxRule,
    DeductionRule,
    FlatTaxRule,
    JurisdictionLevel,
    PayrollTaxRule,
    ProgressiveTaxRule,
    ScopedTaxRule,
    TaxCreditRule,
    TaxRule,
    VATRule,
    unwrap_tax_rule,
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

    def calculate(self, gross_income: Decimal, rules: list[ApplicableTaxRule]) -> dict[str, Any]:
        """
        Execute the strict tax calculation pipeline.

        Execution Order:
        1. Validation & Setup
        2. Deductions (lowers taxable income)
        3. Taxes (Progressive, Flat, Payroll, VAT)
        4. Credits (lowers final tax liability)
        5. Net Income & Frequencies Aggregation
        """
        if gross_income < 0:
            raise ValueError("Gross income cannot be negative")

        contexts: dict[str, CalculationContext] = {}
        scope_metadata: dict[str, tuple[str, JurisdictionLevel] | None] = {}
        rules_by_scope: dict[str, list[TaxRule]] = {}
        scoped_rules: list[tuple[TaxRule, str]] = []

        for applicable_rule in rules:
            rule = unwrap_tax_rule(applicable_rule)
            if isinstance(applicable_rule, ScopedTaxRule):
                scope = f"{applicable_rule.level.value}:{applicable_rule.jurisdiction}"
                scope_metadata[scope] = (
                    applicable_rule.jurisdiction,
                    applicable_rule.level,
                )
            else:
                scope = "global"
                scope_metadata.setdefault(scope, None)

            contexts.setdefault(scope, CalculationContext.create(gross_income))
            rules_by_scope.setdefault(scope, []).append(rule)
            scoped_rules.append((rule, scope))

        # An empty rule list is a valid zero-tax calculation.
        if not contexts:
            contexts["global"] = CalculationContext.create(gross_income)
            scope_metadata["global"] = None

        ordered_results: list[tuple[CalculationResult, str]] = []

        # 1. Deductions
        for rule, scope in scoped_rules:
            if isinstance(rule, DeductionRule):
                ordered_results.append((self._apply_rule(rule, contexts[scope]), scope))

        # 2. Taxes
        for rule, scope in scoped_rules:
            if not isinstance(rule, (DeductionRule, TaxCreditRule)):
                ordered_results.append((self._apply_rule(rule, contexts[scope]), scope))

        # 3. Credits
        for rule, scope in scoped_rules:
            if isinstance(rule, TaxCreditRule):
                ordered_results.append((self._apply_rule(rule, contexts[scope]), scope))

        # 4. Final Aggregations
        total_tax_before_credits = sum(
            (context.total_tax for context in contexts.values()), Decimal("0.0")
        )
        total_credits = sum(
            (context.total_credits for context in contexts.values()), Decimal("0.0")
        )
        total_deductions = sum(
            (context.total_deductions for context in contexts.values()), Decimal("0.0")
        )
        cash_deductions = sum(
            (context.total_cash_deductions for context in contexts.values()), Decimal("0.0")
        )
        employer_cost = sum(
            (context.employer_cost for context in contexts.values()), Decimal("0.0")
        )
        final_tax = max(Decimal("0.0"), total_tax_before_credits - total_credits)
        net_income = max(Decimal("0.0"), gross_income - final_tax - cash_deductions)
        effective_rate_ratio = calculate_effective_tax_rate(final_tax, gross_income)
        effective_rate = apply_bankers_rounding(effective_rate_ratio * 100)
        employee_deductions = cash_deductions + final_tax
        marginal_rate = max(
            (
                self._marginal_rate(contexts[scope].taxable_income, scope_rules)
                for scope, scope_rules in rules_by_scope.items()
            ),
            default=Decimal("0"),
        )
        primary_context = self._get_primary_context(contexts, scope_metadata)
        gross_income_frequencies = self.build_frequencies(gross_income)
        final_tax_frequencies = self.build_frequencies(final_tax)
        net_income_frequencies = self.build_frequencies(net_income)

        return {
            "gross_income": gross_income_frequencies,
            "taxable_income": self.build_frequencies(primary_context.taxable_income),
            "taxable_income_by_jurisdiction": {
                scope: self.build_frequencies(context.taxable_income)
                for scope, context in contexts.items()
            },
            "total_tax_before_credits": self.build_frequencies(total_tax_before_credits),
            "total_credits": self.build_frequencies(total_credits),
            "final_tax": final_tax_frequencies,
            "net_income": net_income_frequencies,
            "employer_cost": self.build_frequencies(employer_cost),
            "employee_deductions": self.build_frequencies(employee_deductions),
            "total_deductions": self.build_frequencies(total_deductions),
            "effective_tax_rate": str(effective_rate),
            "marginal_tax_rate": str(marginal_rate),
            # Compatibility aliases used by verification tooling and older clients.
            "total_tax": final_tax_frequencies["annual"],
            "net_pay": net_income_frequencies["annual"],
            "gross_pay": gross_income_frequencies["annual"],
            "breakdown": [
                self._serialize_breakdown_item(result, scope, scope_metadata)
                for result, scope in ordered_results
            ],
        }

    def calculate_for_api(
        self, gross_income: Decimal, rules: list[ApplicableTaxRule]
    ) -> dict[str, Any]:
        """Return the structured response used by the public API."""
        return UniversalTaxEngine.calculate(self, gross_income, rules)

    def _apply_rule(self, rule: TaxRule, context: CalculationContext) -> CalculationResult:
        """Find the applicable plugin for the rule and execute it."""
        for plugin in self._plugins:
            if plugin.can_handle(rule):
                result = plugin.calculate(rule, context)
                context.apply_result(result)
                return result

        raise NotImplementedError(f"No plugin registered for rule type {type(rule).__name__}")

    @staticmethod
    def _get_primary_context(
        contexts: dict[str, CalculationContext],
        scope_metadata: dict[str, tuple[str, JurisdictionLevel] | None],
    ) -> CalculationContext:
        """Use the national taxable-income basis for the legacy summary field."""
        for scope, metadata in scope_metadata.items():
            if metadata and metadata[1] is JurisdictionLevel.COUNTRY:
                return contexts[scope]
        return next(iter(contexts.values()))

    @staticmethod
    def _serialize_breakdown_item(
        result: CalculationResult,
        scope: str,
        scope_metadata: dict[str, tuple[str, JurisdictionLevel] | None],
    ) -> dict[str, Any]:
        """Serialize a rule result while preserving its source jurisdiction."""
        details = dict(result.details)
        metadata = scope_metadata[scope]
        if metadata:
            details["jurisdiction"] = metadata[0]
            details["jurisdiction_level"] = metadata[1].value
        return {
            "rule": result.rule_name,
            "name": result.rule_name,
            "tax": str(result.tax_amount),
            "deduction": str(result.deduction_amount),
            "credit": str(result.credit_amount),
            "employer_cost": str(result.employer_cost),
            "details": details,
        }

    @staticmethod
    def _marginal_rate(income: Decimal, rules: list[TaxRule]) -> Decimal:
        """Return the highest applicable employee tax rate as a percentage."""
        applicable_rates: list[Decimal] = []
        for rule in rules:
            if isinstance(rule, ProgressiveTaxRule):
                for bracket in sorted(rule.brackets, key=lambda item: item.min_amount):
                    if income > bracket.min_amount and (
                        bracket.max_amount is None or income <= bracket.max_amount
                    ):
                        applicable_rates.append(bracket.rate * 100)
                        break
            elif isinstance(rule, FlatTaxRule):
                applicable_rates.append(rule.rate * 100)
            elif isinstance(rule, PayrollTaxRule):
                applicable_rates.append(rule.employee_rate * 100)
            elif isinstance(rule, VATRule):
                applicable_rates.append(rule.standard_rate * 100)
        return apply_bankers_rounding(max(applicable_rates, default=Decimal("0")))

    def build_frequencies(self, annual_amount: Decimal) -> dict[str, str]:
        """Generate common time frequencies from an annual amount."""
        return {
            "annual": str(annual_amount),
            "monthly": str((annual_amount / 12).quantize(Decimal("0.01"))),
            "biweekly": str((annual_amount / 26).quantize(Decimal("0.01"))),
            "weekly": str((annual_amount / 52).quantize(Decimal("0.01"))),
            "daily": str((annual_amount / 260).quantize(Decimal("0.01"))),
            "hourly": str((annual_amount / 2080).quantize(Decimal("0.01"))),
        }


class TaxCalculator(UniversalTaxEngine):
    """Backward-compatible flat-result adapter for the original calculator API.

    New endpoints should use :class:`UniversalTaxEngine` directly.  Keeping this
    adapter avoids breaking integrations while the platform migrates to the
    structured period-based response.
    """

    def calculate(self, gross_income: Decimal, rules: list[ApplicableTaxRule]) -> dict[str, Any]:
        """Return annual scalar values for legacy callers."""
        result = super().calculate(gross_income, rules)
        return {
            "gross_income": result["gross_income"]["annual"],
            "taxable_income": result["taxable_income"]["annual"],
            "total_tax_before_credits": result["total_tax_before_credits"]["annual"],
            "total_deductions": result["total_deductions"]["annual"],
            "total_credits": result["total_credits"]["annual"],
            "final_tax": result["final_tax"]["annual"],
            "net_income": result["net_income"]["annual"],
            "net_pay": result["net_pay"],
            "total_tax": result["total_tax"],
            "employer_cost": result["employer_cost"]["annual"],
            "effective_tax_rate": str(Decimal(result["effective_tax_rate"]) / Decimal("100")),
            "marginal_tax_rate": str(Decimal(result["marginal_tax_rate"]) / Decimal("100")),
            "breakdown": result["breakdown"],
        }

    def calculate_for_api(
        self, gross_income: Decimal, rules: list[ApplicableTaxRule]
    ) -> dict[str, Any]:
        """Return the current structured response for service adapters."""
        return super().calculate_for_api(gross_income, rules)
