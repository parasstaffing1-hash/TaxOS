"Canada tax updater plugin."

from __future__ import annotations

from taxos.plugins.updater.base import AbstractUpdaterPlugin, PluginUpdateResult


class CanadaUpdaterPlugin(AbstractUpdaterPlugin):
    @property
    def country_code(self) -> str:
        return "CA"

    async def fetch_updates(self, tax_year: int) -> list[PluginUpdateResult]:
        # TODO: Implement data collection pipeline for Canada
        return []
