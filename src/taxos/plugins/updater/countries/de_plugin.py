"Germany tax updater plugin."

from __future__ import annotations

from taxos.plugins.updater.base import AbstractUpdaterPlugin, PluginUpdateResult


class GermanyUpdaterPlugin(AbstractUpdaterPlugin):
    @property
    def country_code(self) -> str:
        return "DE"

    async def fetch_updates(self, tax_year: int) -> list[PluginUpdateResult]:
        # TODO: Implement data collection pipeline for Germany
        return []
