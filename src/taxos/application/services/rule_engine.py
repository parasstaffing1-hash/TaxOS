"""Rule Engine Service for orchestration and inheritance."""

from __future__ import annotations

import structlog

from taxos.application.interfaces.rule_repository import AbstractRuleRepository
from taxos.core.exceptions import NotFoundError
from taxos.domain.rules import FilingStatus, TaxRule

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
    ) -> list[TaxRule]:
        """
        Get all applicable tax rules for a given context by merging Country, State, and City rules.

        Raises:
            NotFoundError: If the country-level rules are missing for the given year.
        """
        rules: list[TaxRule] = []

        # 1. Fetch Country Rules (Base)
        country_ruleset = await self._repo.get_rule_set(country=country, year=year)
        if not country_ruleset:
            logger.error("missing_country_rules", country=country, year=year)
            raise NotFoundError(f"No rules found for {country} in {year}")

        rules.extend(country_ruleset.get_rules_for_status(filing_status))

        # 2. Fetch State Rules (if applicable)
        if state:
            state_ruleset = await self._repo.get_rule_set(country=country, year=year, state=state)
            if state_ruleset:
                rules.extend(state_ruleset.get_rules_for_status(filing_status))
            else:
                logger.debug("no_state_rules_found", country=country, state=state, year=year)

        # 3. Fetch City Rules (if applicable)
        if city:
            city_ruleset = await self._repo.get_rule_set(
                country=country, year=year, state=state, city=city
            )
            if city_ruleset:
                rules.extend(city_ruleset.get_rules_for_status(filing_status))
            else:
                logger.debug(
                    "no_city_rules_found", country=country, state=state, city=city, year=year
                )

        return rules
