"""API dependencies."""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from taxos.application.services.salary_calculator import SalaryCalculatorService


async def get_db(request: Request) -> AsyncGenerator[AsyncSession]:
    """Dependency to provide a database session."""
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        yield session

def get_rule_engine() -> "RuleEngineService":
    from taxos.application.services.rule_engine import RuleEngineService
    from taxos.infrastructure.rules.file_repository import FileBasedRuleRepository
    
    repo = FileBasedRuleRepository(base_dir="rules")
    return RuleEngineService(repo)


def get_salary_calculator_service() -> "SalaryCalculatorService":
    from taxos.application.calculations.engine import UniversalTaxEngine
    from taxos.application.services.currency import CurrencyEngine
    from taxos.application.services.salary_calculator import SalaryCalculatorService
    from taxos.infrastructure.currency.mock_provider import MockExchangeRateProvider

    rule_service = get_rule_engine()
    currency_engine = CurrencyEngine(provider=MockExchangeRateProvider())
    tax_calculator = UniversalTaxEngine()
    return SalaryCalculatorService(rule_service, currency_engine, tax_calculator)
