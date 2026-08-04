"""Safe Formula Evaluator."""

from __future__ import annotations

import ast
import operator
from collections.abc import Awaitable, Callable
from decimal import Decimal
from typing import Any, ClassVar, cast

from taxos.api.schemas.calculator import (
    CalculatorRequest,
)
from taxos.application.services.salary_calculator import SalaryCalculatorService
from taxos.domain.calculators.schema import CalculatorConfig
from taxos.domain.financial.validation import DemographicProfile, IncomeProfile, LocationProfile


class FormulaError(Exception):
    pass


class AsyncSafeEvaluator:
    """Safely evaluates mathematical expressions and macros asynchronously using an AST."""

    _OPS: ClassVar[dict[type[ast.AST], Callable[..., Any]]] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.USub: operator.neg,
    }

    def __init__(
        self,
        variables: dict[str, Any],
        salary_service: SalaryCalculatorService | None = None,
    ) -> None:
        self.variables = variables
        self.salary_service = salary_service
        self._macros: dict[str, Callable[..., Awaitable[Any]]] = {
            "tax": self._macro_tax,
            "net_to_gross": self._macro_net_to_gross,
        }

    def _get_tax_year(self) -> int:
        """Return the explicitly supplied tax year or the supported launch year."""
        value = self.variables.get("tax_year", 2024)
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise FormulaError("tax_year must be a whole number") from exc

    @staticmethod
    def _to_formula_value(value: Any) -> Any:
        """Convert API values into primitives safe for arithmetic expressions."""
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, dict):
            return {key: AsyncSafeEvaluator._to_formula_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [AsyncSafeEvaluator._to_formula_value(item) for item in value]
        return value

    async def _macro_tax(self, income: float, country: str, state: str) -> dict[str, Any]:
        if not self.salary_service:
            raise FormulaError("SalaryCalculatorService not injected.")
        req = CalculatorRequest(
            location=LocationProfile(country=country, state=state, city=""),
            demographics=DemographicProfile(tax_year=self._get_tax_year(), filing_status="single"),
            income=IncomeProfile(gross_income=Decimal(str(income))),
            currency="USD",
        )
        res = await self.salary_service.calculate(req)
        return cast("dict[str, Any]", self._to_formula_value(res.model_dump()))

    async def _macro_net_to_gross(
        self, target_net: float, country: str, state: str
    ) -> dict[str, Any]:
        if not self.salary_service:
            raise FormulaError("SalaryCalculatorService not injected.")
        req = CalculatorRequest(
            location=LocationProfile(country=country, state=state, city=""),
            demographics=DemographicProfile(tax_year=self._get_tax_year(), filing_status="single"),
            income=IncomeProfile(gross_income=Decimal("0.0")),  # Will be determined
            currency="USD",
        )
        res = await self.salary_service.calculate_net_to_gross(Decimal(str(target_net)), req)
        return cast("dict[str, Any]", self._to_formula_value(res.model_dump()))

    async def eval(self, expression: str) -> Any:
        try:
            tree = ast.parse(expression, mode="eval")
            return await self._eval_node(tree.body)
        except Exception as e:
            raise FormulaError(f"Error evaluating '{expression}': {e}") from e

    async def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Name):
            if node.id in self.variables:
                return self.variables[node.id]
            raise FormulaError(f"Undefined variable: {node.id}")

        if isinstance(node, ast.BinOp):
            left = await self._eval_node(node.left)
            right = await self._eval_node(node.right)
            op_type = type(node.op)
            if op_type in self._OPS:
                return self._OPS[op_type](left, right)
            raise FormulaError(f"Unsupported operator: {op_type}")

        if isinstance(node, ast.UnaryOp):
            operand = await self._eval_node(node.operand)
            uop_type = type(node.op)
            if uop_type in self._OPS:
                return self._OPS[uop_type](operand)
            raise FormulaError(f"Unsupported unary operator: {uop_type}")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise FormulaError("Only simple function calls are allowed.")
            func_name = node.func.id
            if func_name not in self._macros:
                raise FormulaError(f"Unknown macro function: {func_name}")
            args = [await self._eval_node(arg) for arg in node.args]
            return await self._macros[func_name](*args)

        if isinstance(node, ast.Subscript):
            value = await self._eval_node(node.value)
            if isinstance(node.slice, ast.Constant):
                key = node.slice.value
                if isinstance(value, dict) and key in value:
                    return value[key]
                raise FormulaError(f"Dictionary key not found: {key!r}")
            raise FormulaError("Only constant slices are allowed.")

        raise FormulaError(f"Unsupported syntax: {type(node)}")


async def evaluate_calculator(
    config: CalculatorConfig,
    inputs: dict[str, Any],
    salary_service: SalaryCalculatorService | None = None,
) -> dict[str, Any]:

    state: dict[str, Any] = {}
    for inp in config.inputs:
        val = inputs.get(inp.id, inp.default)
        if val is None and inp.type in ("currency", "number", "percentage"):
            val = 0.0
        state[inp.id] = val

    evaluator = AsyncSafeEvaluator(state, salary_service)

    results: dict[str, Any] = {}

    for formula in config.formulas:
        val = await evaluator.eval(formula.expression)
        # Convert Decimals to float if needed
        if isinstance(val, Decimal):
            val = float(val)
        state[formula.id] = val
        if formula.is_result:
            results[formula.id] = val

    for key, value in state.items():
        if key not in results:
            results[key] = float(value) if isinstance(value, Decimal) else value

    return results
