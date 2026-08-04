"""Unit tests for FileBasedRuleRepository."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from taxos.core.exceptions import InfrastructureError
from taxos.infrastructure.rules.file_repository import FileBasedRuleRepository


@pytest.fixture
def repo_dir(tmp_path: Path) -> Path:
    """Create a temporary directory structure for testing."""
    base = tmp_path / "rules"
    base.mkdir()

    # US Federal 2024
    us_2024 = base / "US" / "2024"
    us_2024.mkdir(parents=True)
    us_fed_data = {
        "jurisdiction": "US",
        "level": "country",
        "tax_year": 2024,
        "currency": "USD",
        "rules": {"all": [{"type": "flat", "name": "Test Fed", "rate": 0.1}]},
    }
    (us_2024 / "federal.yaml").write_text(yaml.dump(us_fed_data))

    # US CA State 2024
    ca_2024 = us_2024 / "CA"
    ca_2024.mkdir()
    ca_state_data = {
        "jurisdiction": "CA",
        "level": "state",
        "tax_year": 2024,
        "rules": {"single": [{"type": "flat", "name": "Test CA", "rate": 0.05}]},
    }
    (ca_2024 / "state.json").write_text(json.dumps(ca_state_data))

    # Invalid data
    uk_2024 = base / "UK" / "2024"
    uk_2024.mkdir(parents=True)
    (uk_2024 / "national.yaml").write_text("invalid: [yaml")

    return base


@pytest.fixture
def repo(repo_dir: Path) -> FileBasedRuleRepository:
    return FileBasedRuleRepository(base_dir=repo_dir)


@pytest.mark.asyncio
class TestFileBasedRuleRepository:
    """Tests for file-based repository operations."""

    async def test_load_federal_yaml(self, repo: FileBasedRuleRepository) -> None:
        """Test loading country-level YAML rules."""
        ruleset = await repo.get_rule_set(country="US", year=2024)
        assert ruleset is not None
        assert ruleset.jurisdiction == "US"
        assert ruleset.currency == "USD"
        assert len(ruleset.rules["all"]) == 1

    async def test_load_state_json(self, repo: FileBasedRuleRepository) -> None:
        """Test loading state-level JSON rules."""
        ruleset = await repo.get_rule_set(country="US", year=2024, state="CA")
        assert ruleset is not None
        assert ruleset.jurisdiction == "CA"
        assert ruleset.currency == "USD"  # default
        assert len(ruleset.rules["single"]) == 1

    async def test_cache_hits(self, repo: FileBasedRuleRepository) -> None:
        """Test that repeated calls use the cache."""
        ruleset1 = await repo.get_rule_set(country="US", year=2024)
        ruleset2 = await repo.get_rule_set(country="US", year=2024)
        # Should be the exact same object
        assert ruleset1 is ruleset2

    async def test_not_found(self, repo: FileBasedRuleRepository) -> None:
        """Test missing file returns None."""
        ruleset = await repo.get_rule_set(country="FR", year=2024)
        assert ruleset is None

    async def test_invalid_yaml(self, repo: FileBasedRuleRepository) -> None:
        """Test invalid YAML structure raises InfrastructureError."""
        with pytest.raises(InfrastructureError, match="Failed to read"):
            await repo.get_rule_set(country="UK", year=2024)

    async def test_list_available_years(self, repo: FileBasedRuleRepository) -> None:
        """Test listing available years."""
        years = await repo.list_available_years("US")
        assert years == [2024]

        years_none = await repo.list_available_years("FR")
        assert years_none == []
