"""Salary Calculator Orchestration Service."""

from __future__ import annotations

from decimal import Decimal

from taxos.api.schemas.calculator import CalculationResponse, CalculatorRequest
from taxos.application.calculations.engine import UniversalTaxEngine
from taxos.application.services.currency import CurrencyEngine
from taxos.application.services.rule_engine import RuleEngineService
from taxos.core.exceptions import NotFoundError
from taxos.domain.financial.currency import Currency
from taxos.domain.financial.validation import DeductionsProfile
from taxos.domain.rules import (
    ApplicableTaxRule,
    DeductionRule,
    FlatTaxRule,
    ProgressiveTaxRule,
    ScopedTaxRule,
    unwrap_tax_rule,
)


class SalaryCalculatorService:
    """Orchestrates validation, rule fetching, and calculations."""

    def __init__(
        self,
        rule_service: RuleEngineService,
        currency_engine: CurrencyEngine,
        tax_calculator: UniversalTaxEngine,
    ) -> None:
        self.rule_service = rule_service
        self.currency_engine = currency_engine
        self.tax_calculator = tax_calculator

    async def calculate(self, request: CalculatorRequest) -> CalculationResponse:
        """Calculate the full after-tax salary breakdown."""
        try:
            rules_list = await self.rule_service.get_applicable_rules(
                country=request.location.country,
                year=request.demographics.tax_year,
                filing_status=request.demographics.filing_status,
                state=request.location.state,
                city=request.location.city,
            )
        except NotFoundError as e:
            jurisdiction = (
                request.location.city or request.location.state or request.location.country
            )
            raise NotFoundError(f"No tax rules found for jurisdiction: {jurisdiction}") from e

        return await self.calculate_with_rules(request, rules_list)

    async def calculate_with_rules(
        self,
        request: CalculatorRequest,
        rules_list: list[ApplicableTaxRule],
    ) -> CalculationResponse:
        """Calculate from an already selected subset of applicable tax rules."""

        base_income = request.income.gross_income or Decimal("0")
        source_currency = request.currency or request.income.currency
        calc_income = await self.currency_engine.convert(
            amount=base_income, from_currency=source_currency, to_currency=Currency.USD
        )
        declared_deduction = self._declared_pre_tax_deduction(request.deductions)
        if declared_deduction:
            converted_deduction = await self.currency_engine.convert(
                amount=declared_deduction,
                from_currency=source_currency,
                to_currency=Currency.USD,
            )
            rules_list = self._add_declared_pre_tax_deduction(rules_list, converted_deduction)

        if hasattr(self.tax_calculator, "calculate_for_api"):
            calc_result = self.tax_calculator.calculate_for_api(calc_income, rules_list)
        else:
            legacy_result = self.tax_calculator.calculate(calc_income, rules_list)
            calc_result = self._adapt_legacy_result(legacy_result)
        calc_result["currency"] = Currency.USD

        return CalculationResponse.model_validate(calc_result)

    @staticmethod
    def _declared_pre_tax_deduction(profile: DeductionsProfile) -> Decimal:
        """Sum user-entered deductions that are explicitly pre-tax in this model."""
        return sum(
            (
                profile.retirement_contribution,
                profile.health_insurance,
                profile.pre_tax_401k,
                profile.pension_contribution,
            ),
            Decimal("0"),
        )

    @staticmethod
    def _add_declared_pre_tax_deduction(
        rules: list[ApplicableTaxRule], amount: Decimal
    ) -> list[ApplicableTaxRule]:
        """Apply an eligible employee deduction to each income-tax jurisdiction.

        Payroll taxes continue to use gross wages, while country and state income
        tax rules each receive their own tax-basis deduction.
        """
        declared_rules: list[ApplicableTaxRule] = []
        seen_scopes: set[tuple[str, str]] = set()
        cash_impact_assigned = False

        for applicable_rule in rules:
            raw_rule = unwrap_tax_rule(applicable_rule)
            if not isinstance(raw_rule, (ProgressiveTaxRule, FlatTaxRule)):
                continue
            if not isinstance(applicable_rule, ScopedTaxRule):
                continue

            scope = (applicable_rule.level.value, applicable_rule.jurisdiction)
            if scope in seen_scopes:
                continue
            seen_scopes.add(scope)
            declared_rules.append(
                ScopedTaxRule(
                    rule=DeductionRule(
                        name="Declared eligible pre-tax deductions",
                        amount=amount,
                        reduces_take_home=not cash_impact_assigned,
                    ),
                    jurisdiction=applicable_rule.jurisdiction,
                    level=applicable_rule.level,
                )
            )
            cash_impact_assigned = True

        return declared_rules + rules

    @staticmethod
    def _adapt_legacy_result(result: dict[str, object]) -> dict[str, object]:
        """Adapt annual scalar calculator output to the public API shape."""

        def frequencies(value: object) -> dict[str, str]:
            amount = Decimal(str(value))
            return UniversalTaxEngine().build_frequencies(amount)

        adapted = dict(result)
        for key in (
            "gross_income",
            "taxable_income",
            "total_tax_before_credits",
            "total_deductions",
            "total_credits",
            "final_tax",
            "net_income",
            "employer_cost",
        ):
            if key in result:
                adapted[key] = frequencies(result[key])
        adapted["effective_tax_rate"] = str(Decimal(str(result["effective_tax_rate"])) * 100)
        adapted["marginal_tax_rate"] = str(Decimal(str(result["marginal_tax_rate"])) * 100)
        return adapted

    async def calculate_net_to_gross(
        self, target_net: Decimal, request: CalculatorRequest
    ) -> CalculationResponse:
        """Goal-seek algorithm to find gross income for a target net."""
        low = target_net
        high = target_net * Decimal("3.0")
        tolerance = Decimal("0.01")
        max_iterations = 50

        best_response = None

        for _ in range(max_iterations):
            guess_gross = (low + high) / Decimal("2.0")

            req_copy = request.model_copy(deep=True)
            req_copy.income = req_copy.income.model_copy(update={"gross_income": guess_gross})

            response = await self.calculate(req_copy)
            current_net = response.net_income.annual

            best_response = response

            diff = current_net - target_net
            if abs(diff) <= tolerance:
                break

            if current_net < target_net:
                low = guess_gross
            else:
                high = guess_gross

        if not best_response:
            raise ValueError("Failed to converge on a gross income.")

        return best_response
