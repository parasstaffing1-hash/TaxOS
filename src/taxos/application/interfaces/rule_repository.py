"""Abstract repository interface for tax rules."""

from __future__ import annotations

from abc import ABC, abstractmethod

from taxos.domain.rules import TaxRuleSet


class AbstractRuleRepository(ABC):
    """Port for loading tax rules from a storage mechanism (e.g., files, DB)."""

    @abstractmethod
    async def get_rule_set(
        self,
        country: str,
        year: int,
        state: str | None = None,
        city: str | None = None,
    ) -> TaxRuleSet | None:
        """
        Retrieve a specific tax rule set.

        Args:
            country: ISO Country code (e.g., "US", "UK").
            year: Tax year.
            state: State code (e.g., "CA"). Defaults to None for federal/national rules.
            city: City name (e.g., "San Francisco"). Defaults to None.

        Returns:
            The TaxRuleSet if found, else None.
        """
        ...

    @abstractmethod
    async def list_available_years(self, country: str) -> list[int]:
        """List all tax years available for a given country."""
        ...
