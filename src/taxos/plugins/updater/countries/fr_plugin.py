"France tax updater plugin."

from __future__ import annotations

from taxos.plugins.updater.base import AbstractUpdaterPlugin, PluginUpdateResult


class FranceUpdaterPlugin(AbstractUpdaterPlugin):
    @property
    def country_code(self) -> str:
        return "FR"

    async def fetch_updates(self, tax_year: int) -> list[PluginUpdateResult]:
        # TODO: Implement data collection pipeline for France
        return []
