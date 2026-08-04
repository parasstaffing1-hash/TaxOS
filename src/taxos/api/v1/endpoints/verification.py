"""Administrator-only verification status endpoint."""

from fastapi import APIRouter, Depends

from taxos.api.dependencies.auth import get_current_admin

router = APIRouter(
    prefix="/verification",
    tags=["Verification"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/status")
async def get_verification_status() -> dict[str, str | None]:
    """Report whether a CI-produced verification result has been configured.

    This deployment does not persist verification results, so it must not return
    a fictional readiness score. CI remains the source of truth for release
    verification until a result store is introduced.
    """
    return {
        "status": "not_configured",
        "detail": "Verification status is supplied by the release CI pipeline.",
        "latest_score": None,
    }
