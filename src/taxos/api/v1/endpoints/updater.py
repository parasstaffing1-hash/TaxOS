"""Administrator endpoints for the tax-rule updater."""

from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from taxos.api.dependencies.auth import get_current_admin
from taxos.api.v1.deps import get_db
from taxos.application.updater.coordinator import UpdateCoordinator
from taxos.application.updater.versioning import VersioningService
from taxos.infrastructure.database.models.updater import TaxRuleVersion, TaxUpdateJob, TaxUpdateLog

router = APIRouter(tags=["updater"], dependencies=[Depends(get_current_admin)])
templates = Jinja2Templates(directory="src/taxos/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def updater_dashboard(request: Request, db: AsyncSession = Depends(get_db)) -> HTMLResponse:
    """Render the administrator dashboard for the updater."""
    job_stmt = select(TaxUpdateJob).order_by(desc(TaxUpdateJob.started_at)).limit(1)
    last_job = (await db.execute(job_stmt)).scalars().first()

    version_stmt = (
        select(TaxRuleVersion)
        .where(TaxRuleVersion.is_active.is_(True))
        .order_by(TaxRuleVersion.jurisdiction)
    )
    active_versions = (await db.execute(version_stmt)).scalars().all()

    log_stmt = select(TaxUpdateLog).order_by(desc(TaxUpdateLog.timestamp)).limit(20)
    logs = (await db.execute(log_stmt)).scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "current_year": datetime.now(UTC).year,
            "last_job": last_job,
            "active_versions": active_versions,
            "logs": logs,
        },
    )


async def run_update_background(db_engine: AsyncEngine) -> None:
    """Run one update cycle in a background task."""
    coordinator = UpdateCoordinator(db_engine)
    await coordinator.run_update_cycle(datetime.now(UTC).year)


@router.post("/run")
async def manual_run_update(
    request: Request, background_tasks: BackgroundTasks
) -> RedirectResponse:
    """Trigger an administrator-requested update in the background."""
    background_tasks.add_task(run_update_background, request.app.state.engine)
    return RedirectResponse(url="/api/v1/updater/dashboard", status_code=303)


@router.post("/rollback/{version_hash}")
async def rollback_version(
    version_hash: str, db: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    """Rollback to a previously stored tax-rule version."""
    if not await VersioningService(db).rollback(version_hash):
        raise HTTPException(status_code=404, detail="Tax rule version not found")
    return RedirectResponse(url="/api/v1/updater/dashboard", status_code=303)
