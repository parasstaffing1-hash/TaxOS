"Singapore tax updater plugin."

from __future__ import annotations

from taxos.plugins.updater.base import AbstractUpdaterPlugin, PluginUpdateResult


class SingaporeUpdaterPlugin(AbstractUpdaterPlugin):
    @property
    def country_code(self) -> str:
        return "SG"

    async def fetch_updates(self, tax_year: int) -> list[PluginUpdateResult]:
        """Return no update until an approved Singaporean source is configured."""
        return []
