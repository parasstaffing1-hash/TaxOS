"""Unit tests for the RuleEngineService."""

from __future__ import annotations

from decimal import Decimal

import pytest

from taxos.application.interfaces.rule_repository import AbstractRuleRepository
from taxos.application.services.rule_engine import RuleEngineService
from taxos.core.exceptions import NotFoundError
from taxos.domain.rules import (
    FilingStatus,
    FlatTaxRule,
    JurisdictionLevel,
    ScopedTaxRule,
    TaxRuleSet,
)


class DummyRepository(AbstractRuleRepository):
    """In-memory repository for testing."""

    def __init__(self) -> None:
        self.rules: dict[str, TaxRuleSet] = {}

    def add_rule_set(self, rs: TaxRuleSet) -> None:
        key = f"{rs.jurisdiction}:{rs.level.value}"
        self.rules[key] = rs

    async def get_rule_set(
        self, country: str, year: int, state: str | None = None, city: str | None = None
    ) -> TaxRuleSet | None:
        del year
        if city:
            return self.rules.get(f"{city}:city")
        if state:
            return self.rules.get(f"{state}:state")
        return self.rules.get(f"{country}:country")

    async def list_available_years(self, country: str) -> list[int]:
        del country
        return [2024]


@pytest.fixture
def repo() -> DummyRepository:
    repo = DummyRepository()

    # Country rules
    fed_rule = FlatTaxRule(name="Fed", rate=Decimal("0.1"))
    repo.add_rule_set(
        TaxRuleSet(
            jurisdiction="US",
            level=JurisdictionLevel.COUNTRY,
            tax_year=2024,
            rules={"all": [fed_rule]},
        )
    )

    # State rules
    state_rule = FlatTaxRule(name="State", rate=Decimal("0.05"))
    repo.add_rule_set(
        TaxRuleSet(
            jurisdiction="CA",
            level=JurisdictionLevel.STATE,
            tax_year=2024,
            rules={FilingStatus.SINGLE: [state_rule]},
        )
    )

    # City rules
    city_rule = FlatTaxRule(name="City", rate=Decimal("0.01"))
    repo.add_rule_set(
        TaxRuleSet(
            jurisdiction="SF",
            level=JurisdictionLevel.CITY,
            tax_year=2024,
            rules={"all": [city_rule]},
        )
    )

    return repo


@pytest.fixture
def engine(repo: DummyRepository) -> RuleEngineService:
    return RuleEngineService(repository=repo)


@pytest.mark.asyncio
class TestRuleEngineService:
    """Tests for inheritance and merging in RuleEngineService."""

    async def test_get_country_only(self, engine: RuleEngineService) -> None:
        """Test getting only country-level rules."""
        rules = await engine.get_applicable_rules("US", 2024, FilingStatus.SINGLE)
        assert len(rules) == 1
        assert rules[0].name == "Fed"

    async def test_get_country_and_state(self, engine: RuleEngineService) -> None:
        """Test merging country and state rules."""
        rules = await engine.get_applicable_rules("US", 2024, FilingStatus.SINGLE, state="CA")
        assert len(rules) == 2
        names = {r.name for r in rules}
        assert names == {"Fed", "State"}
        assert all(isinstance(rule, ScopedTaxRule) for rule in rules)
        assert {(rule.jurisdiction, rule.level) for rule in rules} == {
            ("US", JurisdictionLevel.COUNTRY),
            ("CA", JurisdictionLevel.STATE),
        }

    async def test_get_full_inheritance(self, engine: RuleEngineService) -> None:
        """Test merging country, state, and city rules."""
        rules = await engine.get_applicable_rules(
            "US", 2024, FilingStatus.SINGLE, state="CA", city="SF"
        )
        assert len(rules) == 3
        names = {r.name for r in rules}
        assert names == {"Fed", "State", "City"}

    async def test_filing_status_filtering(self, engine: RuleEngineService) -> None:
        """Test that filing status correctly filters state rules in this dataset."""
        # Married should only get the "all" rules (Fed and City), skipping "single" (State)
        rules = await engine.get_applicable_rules(
            "US", 2024, FilingStatus.MARRIED_JOINTLY, state="CA", city="SF"
        )
        assert len(rules) == 2
        names = {r.name for r in rules}
        assert names == {"Fed", "City"}

    async def test_country_not_found(self, engine: RuleEngineService) -> None:
        """Test exception when base country rules are missing."""
        with pytest.raises(NotFoundError, match="No rules found for UK in 2024"):
            await engine.get_applicable_rules("UK", 2024, FilingStatus.SINGLE)

    async def test_missing_state_is_rejected(self, engine: RuleEngineService) -> None:
        """Do not present a federal-only result as a verified state calculation."""
        with pytest.raises(NotFoundError, match="No verified state rules found for US-NV in 2024"):
            await engine.get_applicable_rules("US", 2024, FilingStatus.SINGLE, state="NV")
