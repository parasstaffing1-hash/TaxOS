"""Background scheduler for the Auto Updater."""

from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncEngine

from taxos.application.updater.coordinator import UpdateCoordinator


class UpdaterScheduler:
    """Manages the background execution of the UpdateCoordinator."""

    def __init__(self, engine: AsyncEngine):
        self.coordinator = UpdateCoordinator(engine)
        self.scheduler = AsyncIOScheduler()

    def start(self) -> None:
        """Start the background scheduler."""
        # Schedule the job to run every day at 3:00 AM
        self.scheduler.add_job(
            self._scheduled_task,
            CronTrigger(hour=3, minute=0),
            id="daily_tax_update",
            replace_existing=True,
        )
        self.scheduler.start()

    def shutdown(self) -> None:
        """Gracefully shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()

    async def _scheduled_task(self) -> None:
        """The actual task executed by APScheduler."""
        # By default, check current year and next year
        current_year = datetime.now(UTC).year
        await self.coordinator.run_update_cycle(current_year)
        await self.coordinator.run_update_cycle(current_year + 1)
