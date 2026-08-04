"""Analytics Endpoints."""

import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse

from taxos.api.dependencies.auth import get_current_admin
from taxos.api.schemas.analytics import (
    IncomeDistributionRequest,
    IncomeDistributionResponse,
    LocationComparisonRequest,
    LocationComparisonResponse,
    TrendAnalysisRequest,
    TrendAnalysisResponse,
)
from taxos.api.v1.deps import get_salary_calculator_service
from taxos.application.services.analytics import AsyncMemoizer, TaxAnalyticsService
from taxos.application.services.reporting import ReportingEngine
from taxos.application.services.salary_calculator import SalaryCalculatorService

router = APIRouter(tags=["analytics"], dependencies=[Depends(get_current_admin)])

# Create a global cache for demo purposes so memory persists across requests
_global_cache = AsyncMemoizer()


def get_cached_analytics_service(
    salary_service: SalaryCalculatorService = Depends(get_salary_calculator_service),
) -> TaxAnalyticsService:
    return TaxAnalyticsService(salary_service, cache=_global_cache)


@router.post("/compare-locations", response_model=LocationComparisonResponse)
async def compare_locations(
    request: LocationComparisonRequest,
    analytics_service: TaxAnalyticsService = Depends(get_cached_analytics_service),
) -> LocationComparisonResponse:
    return await analytics_service.compare_locations(request)


@router.post("/trend-analysis", response_model=TrendAnalysisResponse)
async def analyze_trends(
    request: TrendAnalysisRequest,
    analytics_service: TaxAnalyticsService = Depends(get_cached_analytics_service),
) -> TrendAnalysisResponse:
    return await analytics_service.analyze_trends(request)


@router.post("/distribution", response_model=IncomeDistributionResponse)
async def analyze_distribution(
    request: IncomeDistributionRequest,
    analytics_service: TaxAnalyticsService = Depends(get_cached_analytics_service),
) -> IncomeDistributionResponse:
    return await analytics_service.analyze_income_distribution(request)


@router.post("/reports/generate")
async def generate_report(
    background_tasks: BackgroundTasks,
    request: LocationComparisonRequest,
    analytics_service: TaxAnalyticsService = Depends(get_cached_analytics_service),
) -> dict[str, Any]:
    # First get the data
    data = await analytics_service.compare_locations(request)

    # Enqueue job
    job_id = ReportingEngine.start_report_generation(
        background_tasks, "Location_Comparison", data.results
    )

    return {"job_id": job_id, "status": "processing"}


@router.get("/reports/{job_id}")
async def get_report_status(job_id: str) -> Any:
    job = ReportingEngine.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] == "completed":
        file_path = job["file_path"]
        if file_path and os.path.exists(file_path):
            return FileResponse(file_path, filename=f"report_{job_id}.xlsx")

    return {"job_id": job_id, "status": job["status"], "error": job.get("error")}
