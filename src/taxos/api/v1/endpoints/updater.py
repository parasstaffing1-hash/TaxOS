"""Admin endpoints for the Auto Updater."""

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from taxos.api.v1.deps import get_db
from taxos.application.updater.coordinator import UpdateCoordinator
from taxos.infrastructure.database.models.updater import TaxRuleVersion, TaxUpdateJob, TaxUpdateLog

router = APIRouter(tags=["updater"])
templates = Jinja2Templates(directory="src/taxos/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def updater_dashboard(request: Request, db: AsyncSession = Depends(get_db)) -> HTMLResponse:
    """Render the admin dashboard for the updater."""

    # Get last job
    job_stmt = select(TaxUpdateJob).order_by(desc(TaxUpdateJob.started_at)).limit(1)
    job_res = await db.execute(job_stmt)
    last_job = job_res.scalars().first()

    # Get active versions
    ver_stmt = select(TaxRuleVersion).where(TaxRuleVersion.is_active == True).order_by(TaxRuleVersion.jurisdiction)
    ver_res = await db.execute(ver_stmt)
    active_versions = ver_res.scalars().all()

    # Get recent logs
    log_stmt = select(TaxUpdateLog).order_by(desc(TaxUpdateLog.timestamp)).limit(20)
    log_res = await db.execute(log_stmt)
    logs = log_res.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "current_year": datetime.now().year,
            "last_job": last_job,
            "active_versions": active_versions,
            "logs": logs
        }
    )


from sqlalchemy.ext.asyncio import AsyncEngine


async def run_update_background(db_engine: AsyncEngine) -> None:
    """Background task to run the update coordinator."""
    coordinator = UpdateCoordinator(db_engine)
    await coordinator.run_update_cycle(datetime.now().year)


@router.post("/run")
async def manual_run_update(request: Request, background_tasks: BackgroundTasks) -> RedirectResponse:
    """Trigger a manual update in the background."""
    engine = request.app.state.engine
    background_tasks.add_task(run_update_background, engine)

    # Redirect back to dashboard
    return RedirectResponse(url="/api/v1/updater/dashboard", status_code=303)


@router.post("/rollback/{version_hash}")
async def rollback_version(version_hash: str, db: AsyncSession = Depends(get_db)) -> RedirectResponse:
    """Rollback to a specific version (mock endpoint)."""
    from taxos.application.updater.versioning import VersioningService
    service = VersioningService(db)
    success = await service.rollback(version_hash)

    return RedirectResponse(url="/api/v1/updater/dashboard", status_code=303)
