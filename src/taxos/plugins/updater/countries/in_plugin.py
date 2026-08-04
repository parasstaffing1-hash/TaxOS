"India tax updater plugin."

from __future__ import annotations

from taxos.plugins.updater.base import AbstractUpdaterPlugin, PluginUpdateResult


class IndiaUpdaterPlugin(AbstractUpdaterPlugin):
    @property
    def country_code(self) -> str:
        return "IN"

    async def fetch_updates(self, tax_year: int) -> list[PluginUpdateResult]:
        """Return no update until an approved Indian source is configured."""
        return []
