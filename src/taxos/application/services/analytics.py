"""Tax Analytics Orchestration Service."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any, cast

from cachetools import TTLCache

from taxos.api.schemas.analytics import (
    IncomeDistributionRequest,
    IncomeDistributionResponse,
    LocationComparisonRequest,
    LocationComparisonResponse,
    TrendAnalysisRequest,
    TrendAnalysisResponse,
)
from taxos.application.services.salary_calculator import SalaryCalculatorService


# Simple Async Cache Wrapper
class AsyncMemoizer:
    def __init__(self, ttl: int = 3600, maxsize: int = 1000):
        self._cache: TTLCache[str, Any] = TTLCache(maxsize=maxsize, ttl=ttl)

    async def get_or_set(self, key: str, coro: Any) -> Any:
        if key in self._cache:
            return self._cache[key]
        result = await coro
        self._cache[key] = result
        return result


class TaxAnalyticsService:
    """Orchestrates multi-dimensional tax calculations with massive concurrency."""

    def __init__(
        self,
        salary_service: SalaryCalculatorService,
        cache: AsyncMemoizer | None = None,
    ) -> None:
        self.salary_service = salary_service
        self._cache = cache or AsyncMemoizer(ttl=3600)  # 1 hour cache

    async def compare_locations(
        self, request: LocationComparisonRequest
    ) -> LocationComparisonResponse:
        """Run calculations across multiple locations concurrently."""
        cache_key = f"loc_{request.model_dump_json()}"

        async def _compute() -> LocationComparisonResponse:
            tasks = []
            keys = []

            for loc in request.locations:
                req_copy = request.base_request.model_copy(deep=True)
                req_copy.location = loc

                tasks.append(self.salary_service.calculate(req_copy))
                key = f"{loc.city or ''}_{loc.state or ''}_{loc.country}"
                keys.append(key.strip("_"))

            results = await asyncio.gather(*tasks, return_exceptions=False)

            output = dict(zip(keys, results, strict=True))
            return LocationComparisonResponse(results=output)

        return cast(
            "LocationComparisonResponse", await self._cache.get_or_set(cache_key, _compute())
        )

    async def analyze_trends(self, request: TrendAnalysisRequest) -> TrendAnalysisResponse:
        """Run calculations across multiple historical years concurrently."""
        cache_key = f"trend_{request.model_dump_json()}"

        async def _compute() -> TrendAnalysisResponse:
            tasks = []

            for year in request.years:
                req_copy = request.base_request.model_copy(deep=True)
                req_copy.demographics = req_copy.demographics.model_copy(update={"tax_year": year})
                tasks.append(self.salary_service.calculate(req_copy))

            results = await asyncio.gather(*tasks, return_exceptions=False)

            output = dict(zip(request.years, results, strict=True))
            return TrendAnalysisResponse(results=output)

        return cast("TrendAnalysisResponse", await self._cache.get_or_set(cache_key, _compute()))

    async def analyze_income_distribution(
        self, request: IncomeDistributionRequest
    ) -> IncomeDistributionResponse:
        """Run calculations across a spread of income values concurrently."""
        cache_key = f"dist_{request.model_dump_json()}"

        async def _compute() -> IncomeDistributionResponse:
            tasks = []
            incomes = []

            current_income = request.start_income
            while current_income <= request.end_income:
                req_copy = request.base_request.model_copy(deep=True)
                req_copy.income = req_copy.income.model_copy(
                    update={"gross_income": Decimal(str(current_income))}
                )
                tasks.append(self.salary_service.calculate(req_copy))
                incomes.append(current_income)
                current_income += request.step

            results = await asyncio.gather(*tasks, return_exceptions=False)

            output = dict(zip(incomes, results, strict=True))
            return IncomeDistributionResponse(results=output)

        return cast(
            "IncomeDistributionResponse", await self._cache.get_or_set(cache_key, _compute())
        )
