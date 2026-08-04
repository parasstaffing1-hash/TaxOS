"""Calculator API Endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path
from fastapi.responses import Response
from structlog import get_logger

from taxos.api.schemas.calculator import CalculationResponse, CalculatorRequest
from taxos.api.v1.deps import get_salary_calculator_service
from taxos.application.services.exports import (
    generate_csv_report,
    generate_excel_report,
    generate_pdf_report,
)
from taxos.application.services.salary_calculator import SalaryCalculatorService

logger = get_logger(__name__)

router = APIRouter(tags=["calculator"])

CalculatorServiceDep = Annotated[SalaryCalculatorService, Depends(get_salary_calculator_service)]
JurisdictionPath = Annotated[
    str, Path(description="The jurisdiction (country, state, or city) to calculate for.")
]


@router.post("/{jurisdiction}", response_model=CalculationResponse)
async def calculate_salary(
    jurisdiction: JurisdictionPath,
    request: CalculatorRequest,
    service: CalculatorServiceDep,
) -> CalculationResponse:
    """
    Calculate after-tax salary and provide a complete breakdown.

    The jurisdiction in the URL must match the location profiles provided
    or it can act as a generic proxy for routing. The service will load
    the exact rules based on the request's LocationProfile.
    """
    # Overwrite the request location if needed for routing context,
    # though in our architecture the LocationProfile is fully populated in the body.
    # We could assert that jurisdiction matches state or country.

    logger.info("calculating_salary", jurisdiction=jurisdiction)
    return await service.calculate(request)


@router.post("/{jurisdiction}/pdf", response_class=Response)
async def calculate_salary_pdf(
    jurisdiction: JurisdictionPath,
    request: CalculatorRequest,
    service: CalculatorServiceDep,
) -> Response:
    """Return the tax calculation as a downloadable PDF report."""
    result = await service.calculate(request)
    pdf_bytes = generate_pdf_report(result)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="tax_report_{jurisdiction}.pdf"'},
    )


@router.post("/{jurisdiction}/excel", response_class=Response)
async def calculate_salary_excel(
    jurisdiction: JurisdictionPath,
    request: CalculatorRequest,
    service: CalculatorServiceDep,
) -> Response:
    """Return the tax calculation as a downloadable Excel report."""
    result = await service.calculate(request)
    excel_bytes = generate_excel_report(result)

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="tax_report_{jurisdiction}.xlsx"'},
    )


@router.post("/{jurisdiction}/csv", response_class=Response)
async def calculate_salary_csv(
    jurisdiction: JurisdictionPath,
    request: CalculatorRequest,
    service: CalculatorServiceDep,
) -> Response:
    """Return the tax calculation as a downloadable CSV report."""
    result = await service.calculate(request)
    csv_bytes = generate_csv_report(result)

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="tax_report_{jurisdiction}.csv"'},
    )
