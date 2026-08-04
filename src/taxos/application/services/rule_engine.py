"""Rule Engine Service for orchestration and inheritance."""

from __future__ import annotations

import structlog

from taxos.application.interfaces.rule_repository import AbstractRuleRepository
from taxos.core.exceptions import NotFoundError
from taxos.domain.rules import (
    ApplicableTaxRule,
    FilingStatus,
    RuleReleaseStatus,
    ScopedTaxRule,
    TaxRuleSet,
)

logger = structlog.get_logger(__name__)


class RuleEngineService:
    """Service to load and merge tax rules applying jurisdictional inheritance."""

    def __init__(self, repository: AbstractRuleRepository) -> None:
        self._repo = repository

    async def get_applicable_rules(
        self,
        country: str,
        year: int,
        filing_status: FilingStatus,
        state: str | None = None,
        city: str | None = None,
    ) -> list[ApplicableTaxRule]:
        """
        Get all applicable tax rules for a given context by merging Country, State, and City rules.

        Raises:
            NotFoundError: If the country-level rules are missing for the given year.
        """
        rules: list[ApplicableTaxRule] = []

        # 1. Fetch Country Rules (Base)
        country_ruleset = await self._repo.get_rule_set(country=country, year=year)
        if not country_ruleset:
            logger.error("missing_country_rules", country=country, year=year)
            raise NotFoundError(f"No rules found for {country} in {year}")
        self._require_verified(country_ruleset)

        rules.extend(self._scope_rules(country_ruleset, filing_status))

        # 2. Fetch State Rules (if applicable)
        if state:
            state_ruleset = await self._repo.get_rule_set(country=country, year=year, state=state)
            if state_ruleset:
                self._require_verified(state_ruleset)
                rules.extend(self._scope_rules(state_ruleset, filing_status))
            else:
                raise NotFoundError(
                    f"No verified state rules found for {country}-{state} in {year}"
                )

        # 3. Fetch City Rules (if applicable)
        if city and state:
            city_ruleset = await self._repo.get_rule_set(
                country=country, year=year, state=state, city=city
            )
            if city_ruleset:
                self._require_verified(city_ruleset)
                rules.extend(self._scope_rules(city_ruleset, filing_status))
            else:
                raise NotFoundError(
                    f"No verified city rules found for {country}-{state}-{city} in {year}"
                )

        return rules

    @staticmethod
    def _require_verified(ruleset: TaxRuleSet) -> None:
        """Prevent draft or incomplete data from powering public estimates."""
        if ruleset.release_status is not RuleReleaseStatus.VERIFIED:
            raise NotFoundError(
                f"Tax rules for {ruleset.jurisdiction} {ruleset.tax_year} are not release-approved"
            )

    @staticmethod
    def _scope_rules(ruleset: TaxRuleSet, filing_status: FilingStatus) -> list[ScopedTaxRule]:
        """Attach the source jurisdiction to every merged rule."""
        return [
            ScopedTaxRule(
                rule=rule,
                jurisdiction=ruleset.jurisdiction,
                level=ruleset.level,
            )
            for rule in ruleset.get_rules_for_status(filing_status)
        ]
