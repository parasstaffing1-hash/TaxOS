"""API dependencies."""

from collections.abc import AsyncGenerator
from functools import lru_cache

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from taxos.application.calculations.engine import UniversalTaxEngine
from taxos.application.services.currency import CurrencyEngine
from taxos.application.services.rule_engine import RuleEngineService
from taxos.application.services.salary_calculator import SalaryCalculatorService
from taxos.infrastructure.currency.mock_provider import MockExchangeRateProvider
from taxos.infrastructure.rules.file_repository import FileBasedRuleRepository


async def get_db(request: Request) -> AsyncGenerator[AsyncSession]:
    """Dependency to provide a database session."""
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        yield session


@lru_cache(maxsize=1)
def get_rule_engine() -> RuleEngineService:
    """Reuse the rule repository so its TTL cache survives across requests."""
    repo = FileBasedRuleRepository(base_dir="rules")
    return RuleEngineService(repo)


@lru_cache(maxsize=1)
def get_salary_calculator_service() -> SalaryCalculatorService:
    """Build the stateless calculator service once per worker process."""
    rule_service = get_rule_engine()
    currency_engine = CurrencyEngine(provider=MockExchangeRateProvider())
    tax_calculator = UniversalTaxEngine()
    return SalaryCalculatorService(rule_service, currency_engine, tax_calculator)
