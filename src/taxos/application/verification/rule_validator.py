"""Validates Tax Rule JSONs for integrity and consistency."""

import json
from pathlib import Path
from typing import Any

import yaml

from taxos.application.updater.validator import TaxRuleValidator
from taxos.domain.rules import TaxRuleSet


class RuleValidationError(Exception):
    """Exception raised for rule validation failures."""


class RuleValidator:
    """Validates tax rule invariants."""

    def __init__(self, rules_dir: str | Path | None = None) -> None:
        self.rules_dir = (
            Path(rules_dir) if rules_dir else Path(__file__).resolve().parents[4] / "rules"
        )

    def validate_all(self) -> dict[str, Any]:
        """Validates all rules in the directory."""
        results: dict[str, Any] = {
            "total_files": 0,
            "passed": 0,
            "failed": 0,
            "failures": [],
        }

        for path in self.rules_dir.rglob("*"):
            if path.suffix not in {".json", ".yaml", ".yml"}:
                continue
            if "calculators" in path.parts or "report_templates" in path.parts:
                continue

            results["total_files"] += 1
            try:
                self.validate_file(path)
                results["passed"] += 1
            except Exception as exc:
                results["failed"] += 1
                results["failures"].append(
                    {"file": str(path.relative_to(self.rules_dir)), "error": str(exc)}
                )

        return results

    def validate_file(self, path: Path) -> None:
        with path.open(encoding="utf-8") as f:
            data: Any = yaml.safe_load(f) if path.suffix in {".yaml", ".yml"} else json.load(f)

        if isinstance(data, dict) and isinstance(data.get("rules"), dict):
            ruleset = TaxRuleSet.model_validate(data)
            TaxRuleValidator().validate(ruleset)
            return

        if not isinstance(data, dict):
            raise RuleValidationError("Rule file must contain a JSON or YAML object.")

        self._validate_metadata(data)

        # Each rule file should have a list of rules
        if "rules" not in data or not isinstance(data["rules"], list):
            raise RuleValidationError("Missing or invalid 'rules' list.")

        for rule in data["rules"]:
            self._validate_rule(rule)

    def _validate_metadata(self, data: dict[str, Any]) -> None:
        required_keys = ["jurisdiction", "tax_year", "level"]
        for k in required_keys:
            if k not in data:
                raise RuleValidationError(f"Missing required metadata key: {k}")

    def _validate_rule(self, rule: dict[str, Any]) -> None:
        if "type" not in rule:
            raise RuleValidationError("Rule missing 'type'.")

        if rule["type"] == "progressive":
            self._validate_progressive_brackets(rule.get("brackets", []))
        elif rule["type"] == "flat":
            self._validate_flat_rate(rule.get("rate"))

    def _validate_progressive_brackets(self, brackets: list[dict[str, Any]]) -> None:
        if not brackets:
            raise RuleValidationError("Progressive rule has no brackets.")

        prev_max = -1.0
        for index, bracket in enumerate(brackets):
            if "rate" not in bracket:
                raise RuleValidationError(f"Bracket {index} missing rate.")

            rate = float(bracket["rate"])
            if not (0.0 <= rate <= 1.0):
                raise RuleValidationError(f"Invalid rate {rate} in bracket {index}.")

            min_val = float(bracket.get("min", bracket.get("min_amount", 0.0)))
            if min_val <= prev_max and index != 0:
                raise RuleValidationError(
                    "Bracket "
                    f"{index} overlaps with previous bracket (min={min_val}, prev_max={prev_max})."
                )

            max_val = bracket.get("max", bracket.get("max_amount"))
            if max_val is not None:
                max_val = float(max_val)
                if min_val >= max_val:
                    raise RuleValidationError(f"Bracket {index} has min >= max.")
                prev_max = max_val
            else:
                prev_max = float("inf")

    def _validate_flat_rate(self, rate: Any) -> None:
        if rate is None:
            raise RuleValidationError("Flat rule missing rate.")
        rate_val = float(rate)
        if not (0.0 <= rate_val <= 1.0):
            raise RuleValidationError(f"Invalid flat rate {rate_val}.")
