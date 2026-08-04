"""Coordinator for the Automatic Tax Update Engine."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from taxos.application.updater.downloader import DownloadManager
from taxos.application.updater.normalizer import NormalizerEngine
from taxos.application.updater.validator import TaxRuleValidator, RuleValidationError
from taxos.application.updater.versioning import VersioningService
from taxos.infrastructure.database.models.updater import TaxUpdateJob, TaxUpdateLog
from taxos.plugins.updater.base import AbstractUpdaterPlugin

# In a real system, plugins would be discovered dynamically via pkg_resources or similar.
from taxos.plugins.updater.countries.us_plugin import USUpdaterPlugin
from taxos.plugins.updater.countries.ca_plugin import CanadaUpdaterPlugin
from taxos.plugins.updater.countries.uk_plugin import UnitedKingdomUpdaterPlugin
from taxos.plugins.updater.countries.au_plugin import AustraliaUpdaterPlugin
from taxos.plugins.updater.countries.in_plugin import IndiaUpdaterPlugin
from taxos.plugins.updater.countries.de_plugin import GermanyUpdaterPlugin
from taxos.plugins.updater.countries.fr_plugin import FranceUpdaterPlugin
from taxos.plugins.updater.countries.sg_plugin import SingaporeUpdaterPlugin
from taxos.plugins.updater.countries.uae_plugin import UAEUpdaterPlugin
from taxos.plugins.updater.countries.nz_plugin import NewZealandUpdaterPlugin

logger = structlog.get_logger(__name__)


class UpdateCoordinator:
    """Orchestrates fetching, normalizing, and validating rules from all country plugins."""

    def __init__(self, engine: AsyncEngine):
        self.session_maker = async_sessionmaker(engine, expire_on_commit=False)
        self.downloader = DownloadManager()
        self.normalizer = NormalizerEngine()
        self.validator = TaxRuleValidator()
        
        self.plugins: list[AbstractUpdaterPlugin] = [
            USUpdaterPlugin(),
            CanadaUpdaterPlugin(),
            UnitedKingdomUpdaterPlugin(),
            AustraliaUpdaterPlugin(),
            IndiaUpdaterPlugin(),
            GermanyUpdaterPlugin(),
            FranceUpdaterPlugin(),
            SingaporeUpdaterPlugin(),
            UAEUpdaterPlugin(),
            NewZealandUpdaterPlugin(),
        ]

    async def run_update_cycle(self, tax_year: int) -> int:
        """Run a full update cycle for a specific tax year."""
        updates_applied = 0

        async with self.session_maker() as session:
            job = TaxUpdateJob(status="RUNNING")
            session.add(job)
            await session.commit()

            versioning_service = VersioningService(session)

            for plugin in self.plugins:
                try:
                    logger.info("pipeline_started", country=plugin.country_code, year=tax_year)
                    
                    # 1. Discovery & Download (delegated to plugin which uses its specific logic)
                    # We pass the downloader to the plugin so it can fetch its bespoke sources.
                    results = await plugin.fetch_updates(tax_year)

                    for result in results:
                        # 2. Normalize (if the plugin returned raw dicts, the normalizer can enforce schema)
                        # Currently, plugins might already return normalized data if they don't have a dedicated normalizer registered,
                        # but ideally we run it through the validator.
                        
                        # 3. Validate
                        # We must convert rule_payload into a TaxRuleSet to validate.
                        # For now, we assume rule_payload is a valid dict representing TaxRuleSet.
                        from taxos.domain.rules import TaxRuleSet
                        try:
                            ruleset = TaxRuleSet.model_validate(result.rule_payload)
                            self.validator.validate(ruleset)
                        except Exception as e:
                            logger.error("validation_failed", country=plugin.country_code, exc_info=True)
                            session.add(TaxUpdateLog(job_id=job.id, level="ERROR", message=f"Validation failed for {plugin.country_code}: {e}"))
                            continue

                        # 4. Store (Versioning)
                        was_applied = await versioning_service.apply_update(result)
                        if was_applied:
                            updates_applied += 1

                    session.add(TaxUpdateLog(
                        job_id=job.id,
                        level="INFO",
                        message=f"Successfully processed {plugin.country_code} for {tax_year}"
                    ))

                except Exception as e:
                    logger.error("pipeline_failed", country=plugin.country_code, exc_info=True)
                    session.add(TaxUpdateLog(
                        job_id=job.id,
                        level="ERROR",
                        message=f"Failed to process {plugin.country_code}",
                        error_details=str(e)
                    ))

            job.status = "SUCCESS"
            job.total_rules_updated = updates_applied
            job.completed_at = datetime.now()
            session.add(job)
            await session.commit()

            return updates_applied
