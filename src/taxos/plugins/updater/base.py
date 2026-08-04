"""Base classes for updater plugins."""

import abc
from datetime import date
from typing import Any

from pydantic import BaseModel


class PluginUpdateResult(BaseModel):
    """Result of a single country plugin update run."""

    jurisdiction: str
    tax_year: int
    rule_payload: dict[str, Any]
    effective_from: date | None = None
    source_url: str | None = None


class AbstractUpdaterPlugin(abc.ABC):
    """Interface that all country updater plugins must implement.

    Each plugin is responsible for scraping its respective tax authority's
    websites, parsing the documents (PDF, CSV, HTML), and transforming the
    found data into the standard TaxRuleSet JSON schema.
    """

    @property
    @abc.abstractmethod
    def country_code(self) -> str:
        """The ISO 3166-1 alpha-2 code of the country this plugin handles (e.g. 'US')."""

    @abc.abstractmethod
    async def fetch_updates(self, tax_year: int) -> list[PluginUpdateResult]:
        """Fetch, parse, and return the tax rules for the given year.

        Args:
            tax_year: The year to check for rules.

        Returns:
            A list of update results containing the structured rules.
            Should return an empty list if no new data is found or available.
        """
