"""Universal REST API for Tax Calculations."""

from __future__ import annotations

from typing import Annotated, Any
import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel

from taxos.api.v1.deps import get_rule_engine
from taxos.api.schemas.calculator import CalculationResponse, CalculatorRequest
from taxos.application.calculations.engine import UniversalTaxEngine
from taxos.application.services.rule_engine import RuleEngineService
from taxos.core.exceptions import NotFoundError
from taxos.domain.rules import (
    ProgressiveTaxRule,
    FlatTaxRule,
    PayrollTaxRule,
    VATRule,
    TaxCreditRule,
    DeductionRule,
)

router = APIRouter(prefix="/calculate", tags=["universal-calculator"])

engine = UniversalTaxEngine()

# Simple in-memory cache for high-volume SEO programmatic pages
_CACHE: dict[str, dict[str, Any]] = {}

def get_cache_key(request: CalculatorRequest, endpoint: str) -> str:
    payload_str = request.model_dump_json()
    return hashlib.sha256(f"{endpoint}:{payload_str}".encode()).hexdigest()


@router.post("/", response_model=CalculationResponse)
async def calculate_all_taxes(
    request: CalculatorRequest,
    rule_service: Annotated[RuleEngineService, Depends(get_rule_engine)],
) -> CalculationResponse:
    """Master endpoint to calculate all applicable taxes."""
    cache_key = get_cache_key(request, "all")
    if cache_key in _CACHE:
        return CalculationResponse.model_validate(_CACHE[cache_key])

    try:
        rules = await rule_service.get_applicable_rules(
            country=request.location.country,
            year=request.demographics.tax_year,
            filing_status=request.demographics.filing_status,
            state=request.location.state,
            city=request.location.city,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    result = engine.calculate(request.income.annual_salary, rules)
    result["currency"] = request.currency
    _CACHE[cache_key] = result
    return CalculationResponse.model_validate(result)


@router.post("/income-tax", response_model=CalculationResponse)
async def calculate_income_tax(
    request: CalculatorRequest,
    rule_service: Annotated[RuleEngineService, Depends(get_rule_engine)],
) -> CalculationResponse:
    """Endpoint specifically for income tax and deductions."""
    try:
        rules = await rule_service.get_applicable_rules(
            country=request.location.country,
            year=request.demographics.tax_year,
            filing_status=request.demographics.filing_status,
            state=request.location.state,
            city=request.location.city,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    # Filter to only income-related rules
    filtered_rules = [
        r for r in rules if isinstance(r, (ProgressiveTaxRule, FlatTaxRule, DeductionRule, TaxCreditRule))
    ]
    result = engine.calculate(request.income.annual_salary, filtered_rules)
    result["currency"] = request.currency
    return CalculationResponse.model_validate(result)


@router.post("/payroll-tax", response_model=CalculationResponse)
async def calculate_payroll_tax(
    request: CalculatorRequest,
    rule_service: Annotated[RuleEngineService, Depends(get_rule_engine)],
) -> CalculationResponse:
    """Endpoint specifically for payroll taxes."""
    try:
        rules = await rule_service.get_applicable_rules(
            country=request.location.country,
            year=request.demographics.tax_year,
            filing_status=request.demographics.filing_status,
            state=request.location.state,
            city=request.location.city,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    filtered_rules = [r for r in rules if isinstance(r, PayrollTaxRule)]
    result = engine.calculate(request.income.annual_salary, filtered_rules)
    result["currency"] = request.currency
    return CalculationResponse.model_validate(result)


@router.post("/vat", response_model=CalculationResponse)
async def calculate_vat(
    request: CalculatorRequest,
    rule_service: Annotated[RuleEngineService, Depends(get_rule_engine)],
) -> CalculationResponse:
    """Endpoint specifically for VAT and Sales Tax."""
    try:
        rules = await rule_service.get_applicable_rules(
            country=request.location.country,
            year=request.demographics.tax_year,
            filing_status=request.demographics.filing_status,
            state=request.location.state,
            city=request.location.city,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    filtered_rules = [r for r in rules if isinstance(r, VATRule)]
    result = engine.calculate(request.income.annual_salary, filtered_rules)
    result["currency"] = request.currency
    return CalculationResponse.model_validate(result)
