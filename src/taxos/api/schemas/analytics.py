"""Analytics Schemas."""

from pydantic import BaseModel, Field

from taxos.api.schemas.calculator import CalculationResponse, CalculatorRequest
from taxos.domain.financial.validation import LocationProfile


class LocationComparisonRequest(BaseModel):
    """Request to compare multiple locations for a fixed income."""
    base_request: CalculatorRequest
    locations: list[LocationProfile] = Field(..., description="List of locations to compare")


class LocationComparisonResponse(BaseModel):
    """Response for location comparison."""
    results: dict[str, CalculationResponse] = Field(..., description="Keyed by Location string representation")


class TrendAnalysisRequest(BaseModel):
    """Request to compare historical tax trends over time."""
    base_request: CalculatorRequest
    years: list[int] = Field(..., description="List of tax years to analyze")


class TrendAnalysisResponse(BaseModel):
    """Response for historical trend analysis."""
    results: dict[int, CalculationResponse] = Field(..., description="Keyed by Tax Year")


class IncomeDistributionRequest(BaseModel):
    """Request to generate an income distribution curve."""
    base_request: CalculatorRequest
    start_income: float = Field(..., description="Starting gross income")
    end_income: float = Field(..., description="Ending gross income")
    step: float = Field(..., description="Step size (e.g., 10000)")


class IncomeDistributionResponse(BaseModel):
    """Response for income distribution curves."""
    results: dict[float, CalculationResponse] = Field(..., description="Keyed by Gross Income")
