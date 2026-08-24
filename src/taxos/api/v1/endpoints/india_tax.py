"""India Personal Income Tax, Salary & Capital Gains API Endpoints."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel

from taxos.domain.financial.trace import StandardTaxCalculationResponse, TaxRegime
from taxos.domain.india.advance_tax_interest import (
    AdvanceTaxInterestResult,
    IndiaAdvanceTaxEngine,
)
from taxos.domain.india.capital_gains import (
    CapitalGainsSummaryResult,
    CapitalGainsTransaction,
    IndiaCapitalGainsEngine,
)
from taxos.domain.india.income_tax import IndiaIncomeTaxEngine
from taxos.domain.india.models import (
    IndiaIncomeTaxInput,
    RegimeComparisonResult,
    SalaryStructureInput,
)
from taxos.domain.india.salary_ctc import (
    HRAExemptionResult,
    IndiaSalaryEngine,
    SalaryTakeHomeBreakdown,
)
from taxos.domain.india.tds_tcs import (
    IndiaTDSEngine,
    TDSCalculationResult,
    TDSRuleDefinition,
)

router = APIRouter(prefix="/india", tags=["India Tax Engine"])


@router.post("/income-tax/calculate-new-regime", response_model=StandardTaxCalculationResponse)
async def calculate_india_new_regime(
    payload: IndiaIncomeTaxInput,
) -> StandardTaxCalculationResponse:
    """Calculate India Personal Income Tax under Section 115BAC (New Tax Regime)."""
    engine = IndiaIncomeTaxEngine(assessment_year=payload.assessment_year)
    return engine.calculate_new_regime(payload)


@router.post("/income-tax/calculate-old-regime", response_model=StandardTaxCalculationResponse)
async def calculate_india_old_regime(
    payload: IndiaIncomeTaxInput,
) -> StandardTaxCalculationResponse:
    """Calculate India Personal Income Tax under the Old Tax Regime with Chapter VI-A deductions."""
    engine = IndiaIncomeTaxEngine(assessment_year=payload.assessment_year)
    return engine.calculate_old_regime(payload)


@router.post("/income-tax/compare-regimes", response_model=RegimeComparisonResult)
async def compare_india_tax_regimes(payload: IndiaIncomeTaxInput) -> RegimeComparisonResult:
    """Compare Old vs New Tax Regimes and get optimal tax recommendation."""
    engine = IndiaIncomeTaxEngine(assessment_year=payload.assessment_year)
    return engine.compare_regimes(payload)


@router.post("/salary/take-home", response_model=SalaryTakeHomeBreakdown)
async def calculate_salary_take_home(
    payload: SalaryStructureInput,
    regime: TaxRegime = TaxRegime.NEW,
) -> SalaryTakeHomeBreakdown:
    """Calculate monthly in-hand take-home salary, EPF, HRA, and tax deductions from CTC."""
    engine = IndiaSalaryEngine(assessment_year="2025-26")
    return engine.calculate_take_home(payload, regime=regime)


class HRARequest(BaseModel):
    basic_salary: Decimal
    hra_received: Decimal
    annual_rent_paid: Decimal
    is_metro: bool = True


@router.post("/salary/hra-exemption", response_model=HRAExemptionResult)
async def calculate_hra_exemption(payload: HRARequest) -> HRAExemptionResult:
    """Calculate statutory HRA exemption under Section 10(13A) and Rule 2A."""
    engine = IndiaSalaryEngine()
    return engine.calculate_hra_exemption(
        basic_salary=payload.basic_salary,
        hra_received=payload.hra_received,
        annual_rent_paid=payload.annual_rent_paid,
        is_metro=payload.is_metro,
    )


class CapitalGainsPayload(BaseModel):
    assessment_year: str = "2025-26"
    transactions: list[CapitalGainsTransaction]


@router.post("/capital-gains/calculate", response_model=CapitalGainsSummaryResult)
async def calculate_capital_gains(payload: CapitalGainsPayload) -> CapitalGainsSummaryResult:
    """Calculate STCG (111A), LTCG (112A with ₹1.25L exemption), VDA (115BBH), and loss set-offs."""
    engine = IndiaCapitalGainsEngine(assessment_year=payload.assessment_year)
    return engine.calculate_gains(payload.transactions)


class AdvanceTaxPayload(BaseModel):
    total_tax_assessed: Decimal
    tds_tcs_credits: Decimal = Decimal("0.0")
    q1_paid_by_jun15: Decimal = Decimal("0.0")
    q2_paid_by_sep15: Decimal = Decimal("0.0")
    q3_paid_by_dec15: Decimal = Decimal("0.0")
    q4_paid_by_mar15: Decimal = Decimal("0.0")
    months_delay_filing_234a: int = 0
    months_delay_payment_234b: int = 0
    is_return_late_234f: bool = False
    total_taxable_income: Decimal = Decimal("0.0")


@router.post("/advance-tax/calculate", response_model=AdvanceTaxInterestResult)
async def calculate_advance_tax_and_interest(
    payload: AdvanceTaxPayload,
) -> AdvanceTaxInterestResult:
    """Calculate quarterly Advance Tax installments and Section 234A/B/C/F interest."""
    engine = IndiaAdvanceTaxEngine()
    return engine.calculate_advance_tax_and_interest(
        total_tax_assessed=payload.total_tax_assessed,
        tds_tcs_credits=payload.tds_tcs_credits,
        q1_paid_by_jun15=payload.q1_paid_by_jun15,
        q2_paid_by_sep15=payload.q2_paid_by_sep15,
        q3_paid_by_dec15=payload.q3_paid_by_dec15,
        q4_paid_by_mar15=payload.q4_paid_by_mar15,
        months_delay_filing_234a=payload.months_delay_filing_234a,
        months_delay_payment_234b=payload.months_delay_payment_234b,
        is_return_late_234f=payload.is_return_late_234f,
        total_taxable_income=payload.total_taxable_income,
    )


class TDSPayload(BaseModel):
    section_code: str
    payment_amount: Decimal
    is_payee_individual_or_huf: bool = True
    has_valid_pan: bool = True


@router.post("/tds/calculate", response_model=TDSCalculationResult)
async def calculate_tds_deduction(payload: TDSPayload) -> TDSCalculationResult:
    """Calculate statutory TDS amount and net payable for specified section code."""
    engine = IndiaTDSEngine()
    return engine.calculate_tds(
        section_code=payload.section_code,
        payment_amount=payload.payment_amount,
        is_payee_individual_or_huf=payload.is_payee_individual_or_huf,
        has_valid_pan=payload.has_valid_pan,
    )


@router.get("/tds/sections", response_model=list[TDSRuleDefinition])
async def list_tds_sections() -> list[TDSRuleDefinition]:
    """List all supported statutory TDS and TCS sections with rates and thresholds."""
    engine = IndiaTDSEngine()
    return engine.list_all_sections()
