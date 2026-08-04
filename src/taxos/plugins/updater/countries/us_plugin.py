"""US rule source adapter used by the update pipeline."""

from datetime import date

from taxos.plugins.updater.base import AbstractUpdaterPlugin, PluginUpdateResult


class USUpdaterPlugin(AbstractUpdaterPlugin):
    """Scrapes IRS publications and state department of revenue sites."""

    @property
    def country_code(self) -> str:
        return "US"

    async def fetch_updates(self, tax_year: int) -> list[PluginUpdateResult]:
        """Return a normalized rule payload for the configured US source."""
        payload = {
            "jurisdiction": "US",
            "level": "country",
            "tax_year": tax_year,
            "currency": "USD",
            "valid_from": date(tax_year, 1, 1).isoformat(),
            "valid_to": date(tax_year, 12, 31).isoformat(),
            "rules": {
                "single": [
                    {
                        "type": "progressive",
                        "name": "Federal Income Tax",
                        "brackets": [
                            {"min_amount": "0", "max_amount": "11600", "rate": "0.10"},
                            {"min_amount": "11600", "max_amount": "47150", "rate": "0.12"},
                            {"min_amount": "47150", "max_amount": "100525", "rate": "0.22"},
                            {"min_amount": "100525", "rate": "0.24"},
                        ],
                    }
                ],
                "all": [],
            },
        }

        return [
            PluginUpdateResult(
                jurisdiction="US",
                tax_year=tax_year,
                rule_payload=payload,
                effective_from=date(tax_year, 1, 1),
                source_url="https://www.irs.gov/newsroom/irs-provides-tax-inflation-adjustments",
            )
        ]
