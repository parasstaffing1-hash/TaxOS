"""Health check API endpoints.

Provides liveness and readiness probes for container
orchestration and monitoring systems.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from taxos.api.deps import DbSessionDep, HealthServiceDep
from taxos.api.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Returns basic app information. Always returns 200 if the process is alive.",
)
async def liveness(service: HealthServiceDep) -> HealthResponse:
    """Application liveness check."""
    result = await service.check_health()
    return HealthResponse(**result)


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Checks application readiness including database connectivity.",
)
async def readiness(
    service: HealthServiceDep,
    session: DbSessionDep,
) -> ReadinessResponse:
    """Application readiness check including dependencies."""
    result = await service.check_readiness(session)
    return ReadinessResponse(**result)
