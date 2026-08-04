"""Versioning logic for the auto updater."""

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxos.infrastructure.database.models.updater import TaxRuleData, TaxRuleVersion
from taxos.plugins.updater.base import PluginUpdateResult


class VersioningService:
    """Handles hashing, diffing, and storing new rule versions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _hash_payload(self, payload: dict[str, Any]) -> str:
        """Create a deterministic hash of the rule payload."""
        # Sort keys to ensure deterministic output
        json_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    async def _get_active_version(self, jurisdiction: str, tax_year: int) -> TaxRuleVersion | None:
        """Get the currently active version for a given jurisdiction and year."""
        stmt = select(TaxRuleVersion).where(
            TaxRuleVersion.jurisdiction == jurisdiction,
            TaxRuleVersion.tax_year == tax_year,
            TaxRuleVersion.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def apply_update(self, update: PluginUpdateResult) -> bool:
        """Apply an update if it differs from the active version.

        Returns:
            True if a new version was created, False if there was no change.
        """
        payload_hash = self._hash_payload(update.rule_payload)

        # Check if this exact hash already exists (even if inactive)
        stmt = select(TaxRuleVersion).where(TaxRuleVersion.version_hash == payload_hash)
        result = await self.session.execute(stmt)
        if result.scalars().first():
            return False  # Already have this version

        # Get current active version to archive it
        active_version = await self._get_active_version(update.jurisdiction, update.tax_year)
        if active_version:
            active_version.is_active = False
            self.session.add(active_version)

        # Extract level from payload metadata
        level = update.rule_payload.get("metadata", {}).get("level", "country")

        # Create new version
        new_version = TaxRuleVersion(
            jurisdiction=update.jurisdiction,
            level=level,
            tax_year=update.tax_year,
            version_hash=payload_hash,
            effective_from=update.effective_from,
            is_active=True,
        )
        self.session.add(new_version)
        await self.session.flush()  # To get new_version.id

        # Save actual rule data
        new_data = TaxRuleData(version_id=new_version.id, payload=update.rule_payload)
        self.session.add(new_data)

        await self.session.commit()
        return True

    async def rollback(self, version_hash: str) -> bool:
        """Rollback the active version to a specific previous hash."""
        # Find the target version
        stmt = select(TaxRuleVersion).where(TaxRuleVersion.version_hash == version_hash)
        result = await self.session.execute(stmt)
        target = result.scalars().first()

        if not target:
            return False

        # Find current active version and deactivate it
        active = await self._get_active_version(target.jurisdiction, target.tax_year)
        if active:
            active.is_active = False
            self.session.add(active)

        # Activate target
        target.is_active = True
        self.session.add(target)
        await self.session.commit()
        return True
