"""Universal REST API for public tax calculations."""

from __future__ import annotations

import hashlib
from typing import Annotated, Any

from cachetools import TTLCache
from fastapi import APIRouter, Depends, HTTPException, status

from taxos.api.schemas.calculator import CalculationResponse, CalculatorRequest
from taxos.api.v1.deps import get_salary_calculator_service
from taxos.application.services.salary_calculator import SalaryCalculatorService
from taxos.core.exceptions import NotFoundError
from taxos.domain.rules import (
    ApplicableTaxRule,
    DeductionRule,
    FlatTaxRule,
    PayrollTaxRule,
    ProgressiveTaxRule,
    TaxCreditRule,
    VATRule,
    unwrap_tax_rule,
)

router = APIRouter(prefix="/calculate", tags=["universal-calculator"])

# Bound public response caching to avoid unbounded memory growth from arbitrary requests.
_CACHE: TTLCache[str, dict[str, Any]] = TTLCache(maxsize=1000, ttl=300)
CalculatorServiceDep = Annotated[SalaryCalculatorService, Depends(get_salary_calculator_service)]


def get_cache_key(request: CalculatorRequest, endpoint: str) -> str:
    """Build a stable cache key from the validated request payload."""
    payload = request.model_dump_json()
    return hashlib.sha256(f"{endpoint}:{payload}".encode()).hexdigest()


async def _get_rules(
    request: CalculatorRequest, service: SalaryCalculatorService
) -> list[ApplicableTaxRule]:
    try:
        return await service.rule_service.get_applicable_rules(
            country=request.location.country,
            year=request.demographics.tax_year,
            filing_status=request.demographics.filing_status,
            state=request.location.state,
            city=request.location.city,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/", response_model=CalculationResponse)
async def calculate_all_taxes(
    request: CalculatorRequest,
    service: CalculatorServiceDep,
) -> CalculationResponse:
    """Calculate every verified tax layer for a request."""
    cache_key = get_cache_key(request, "all")
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return CalculationResponse.model_validate(cached)

    result = await service.calculate(request)
    _CACHE[cache_key] = result.model_dump(mode="json")
    return result


@router.post("/income-tax", response_model=CalculationResponse)
async def calculate_income_tax(
    request: CalculatorRequest,
    service: CalculatorServiceDep,
) -> CalculationResponse:
    """Calculate income tax, deductions, and credits without payroll taxes."""
    rules = await _get_rules(request, service)
    filtered_rules = [
        rule
        for rule in rules
        if isinstance(
            unwrap_tax_rule(rule),
            (ProgressiveTaxRule, FlatTaxRule, DeductionRule, TaxCreditRule),
        )
    ]
    return await service.calculate_with_rules(request, filtered_rules)


@router.post("/payroll-tax", response_model=CalculationResponse)
async def calculate_payroll_tax(
    request: CalculatorRequest,
    service: CalculatorServiceDep,
) -> CalculationResponse:
    """Calculate payroll-tax layers only."""
    rules = await _get_rules(request, service)
    return await service.calculate_with_rules(
        request,
        [rule for rule in rules if isinstance(unwrap_tax_rule(rule), PayrollTaxRule)],
    )


@router.post("/vat", response_model=CalculationResponse)
async def calculate_vat(
    request: CalculatorRequest,
    service: CalculatorServiceDep,
) -> CalculationResponse:
    """Calculate VAT and sales-tax layers only."""
    rules = await _get_rules(request, service)
    return await service.calculate_with_rules(
        request,
        [rule for rule in rules if isinstance(unwrap_tax_rule(rule), VATRule)],
    )
