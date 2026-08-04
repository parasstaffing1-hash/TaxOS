"""Salary Calculator Orchestration Service."""

from __future__ import annotations

from decimal import Decimal

from taxos.api.schemas.calculator import CalculationResponse, CalculatorRequest
from taxos.application.calculations.engine import UniversalTaxEngine
from taxos.application.services.currency import CurrencyEngine
from taxos.application.services.rule_engine import RuleEngineService
from taxos.core.exceptions import NotFoundError
from taxos.domain.financial.currency import Currency


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
            jurisdiction = request.location.city or request.location.state or request.location.country
            raise NotFoundError(f"No tax rules found for jurisdiction: {jurisdiction}") from e

        base_income = request.income.annual_salary
        calc_income = await self.currency_engine.convert(
            amount=base_income, from_currency=request.currency, to_currency=Currency.USD
        )

        calc_result = self.tax_calculator.calculate(calc_income, rules_list)
        calc_result["currency"] = Currency.USD

        return CalculationResponse.model_validate(calc_result)

    async def calculate_net_to_gross(self, target_net: Decimal, request: CalculatorRequest) -> CalculationResponse:
        """Goal-seek algorithm to find gross income for a target net."""
        low = target_net
        high = target_net * Decimal("3.0")
        tolerance = Decimal("0.01")
        max_iterations = 50

        best_response = None

        for _ in range(max_iterations):
            guess_gross = (low + high) / Decimal("2.0")

            req_copy = request.model_copy(deep=True)
            req_copy.income = req_copy.income.model_copy(update={"annual_salary": guess_gross})

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

