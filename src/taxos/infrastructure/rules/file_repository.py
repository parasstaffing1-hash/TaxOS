"""File-based implementation of the RuleRepository."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

import structlog
import yaml
from cachetools import TTLCache
from pydantic import ValidationError

from taxos.application.interfaces.rule_repository import AbstractRuleRepository
from taxos.core.exceptions import InfrastructureError
from taxos.domain.rules import TaxRuleSet

logger = structlog.get_logger(__name__)


class FileBasedRuleRepository(AbstractRuleRepository):
    """Loads tax rules from JSON/YAML files on disk with caching."""

    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        if not self.base_dir.exists():
            logger.warning("rules_directory_missing", path=str(self.base_dir))

        # We'll use a simple in-memory cache for loaded rule sets (TTL: 1 hour)
        self._cache: TTLCache[str, TaxRuleSet] = TTLCache(maxsize=1000, ttl=3600)

    async def get_rule_set(
        self,
        country: str,
        year: int,
        state: str | None = None,
        city: str | None = None,
    ) -> TaxRuleSet | None:
        """
        Locate and parse the appropriate rule file.
        Uses structure: base_dir / {country} / {year} / [{state} /] [{city}.yaml | federal.yaml]
        """
        cache_key = f"{country}:{year}:{state}:{city}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        target_path = self._build_path(country, year, state, city)

        if not target_path or not target_path.exists():
            return None
        try:
            raw_data = self._read_file(target_path)
            rule_set = TaxRuleSet.model_validate(raw_data)
        except ValidationError as e:
            logger.exception("rule_validation_failed", path=str(target_path), errors=e.errors())
            raise InfrastructureError(f"Invalid rule schema in {target_path}") from e
        except Exception as e:
            logger.exception("rule_read_failed", path=str(target_path), error=str(e))
            raise InfrastructureError(f"Failed to read {target_path}") from e
        else:
            self._cache[cache_key] = rule_set
            return rule_set

    async def list_available_years(self, country: str) -> list[int]:
        country_dir = self.base_dir / country
        if not country_dir.exists() or not country_dir.is_dir():
            return []

        years = []
        for p in country_dir.iterdir():
            if p.is_dir() and p.name.isdigit():
                years.append(int(p.name))
        return sorted(years)

    def _build_path(
        self, country: str, year: int, state: str | None, city: str | None
    ) -> Path | None:
        """Construct the expected file path."""
        country_segment = self._safe_segment(country)
        state_segment = self._safe_segment(state) if state else None
        city_segment = self._safe_segment(city) if city else None
        if not country_segment or (state and not state_segment) or (city and not city_segment):
            return None

        base = self.base_dir / country_segment.upper() / str(year)

        if city_segment and state_segment:
            file_name = city_segment.lower()
            path_candidates = [
                base / state_segment.upper() / f"{file_name}.yaml",
                base / state_segment.upper() / f"{file_name}.json",
            ]
        elif state_segment:
            file_name = state_segment.lower()
            path_candidates = [
                base / state_segment.upper() / "state.yaml",
                base / state_segment.upper() / "state.json",
                base / f"{file_name}.yaml",
                base / f"{file_name}.json",
            ]
        else:
            path_candidates = [
                base / "federal.yaml",
                base / "federal.json",
                base / "national.yaml",
                base / "national.json",
            ]

        resolved_base = self.base_dir.resolve()
        for path in path_candidates:
            try:
                path.resolve().relative_to(resolved_base)
            except ValueError:
                continue
            if path.exists():
                return path

        return None

    def _read_file(self, path: Path) -> dict[str, Any]:
        """Read YAML or JSON based on extension."""
        text = path.read_text(encoding="utf-8")
        if path.suffix in {".yaml", ".yml"}:
            return cast("dict[str, Any]", yaml.safe_load(text))
        if path.suffix == ".json":
            return cast("dict[str, Any]", json.loads(text))
        raise ValueError(f"Unsupported file extension: {path.suffix}")

    @staticmethod
    def _safe_segment(value: str | None) -> str | None:
        """Normalize a user-controlled path segment without allowing traversal."""
        if value is None:
            return None
        normalized = re.sub(r"\s+", "_", value.strip())
        if not re.fullmatch(r"[A-Za-z0-9_-]+", normalized):
            return None
        return normalized
