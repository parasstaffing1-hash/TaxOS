"""Validates Tax Rule JSONs for integrity and consistency."""

import json
from pathlib import Path
from typing import Any


class RuleValidationError(Exception):
    """Exception raised for rule validation failures."""
    pass


class RuleValidator:
    """Validates tax rule invariants."""

    def __init__(self, rules_dir: str = "c:/Users/HP/Desktop/Tax/rules"):
        self.rules_dir = Path(rules_dir)

    def validate_all(self) -> dict[str, Any]:
        """Validates all rules in the directory."""
        results = {
            "total_files": 0,
            "passed": 0,
            "failed": 0,
            "failures": []
        }

        for path in self.rules_dir.rglob("*.json"):
            if "calculators" in path.parts:
                continue # Skip calculator configs for now, focus on tax rules

            results["total_files"] += 1
            try:
                self.validate_file(path)
                results["passed"] += 1
            except Exception as e:
                results["failed"] += 1
                results["failures"].append({
                    "file": str(path.relative_to(self.rules_dir)),
                    "error": str(e)
                })

        return results

    def validate_file(self, path: Path) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self._validate_metadata(data)
        
        # Each rule file should have a list of rules
        if "rules" not in data or not isinstance(data["rules"], list):
            raise RuleValidationError("Missing or invalid 'rules' list.")

        for rule in data["rules"]:
            self._validate_rule(rule)

    def _validate_metadata(self, data: dict) -> None:
        required_keys = ["jurisdiction", "tax_year", "level"]
        for k in required_keys:
            if k not in data:
                raise RuleValidationError(f"Missing required metadata key: {k}")

    def _validate_rule(self, rule: dict) -> None:
        if "type" not in rule:
            raise RuleValidationError("Rule missing 'type'.")

        if rule["type"] == "progressive":
            self._validate_progressive_brackets(rule.get("brackets", []))
        elif rule["type"] == "flat":
            self._validate_flat_rate(rule.get("rate"))

    def _validate_progressive_brackets(self, brackets: list[dict]) -> None:
        if not brackets:
            raise RuleValidationError("Progressive rule has no brackets.")

        prev_max = -1
        for i, b in enumerate(brackets):
            if "rate" not in b:
                raise RuleValidationError(f"Bracket {i} missing rate.")
            
            rate = float(b["rate"])
            if not (0.0 <= rate <= 1.0):
                raise RuleValidationError(f"Invalid rate {rate} in bracket {i}.")

            min_val = float(b.get("min", 0.0))
            if min_val <= prev_max and i != 0:
                raise RuleValidationError(f"Bracket {i} overlaps with previous bracket (min={min_val}, prev_max={prev_max}).")

            max_val = b.get("max")
            if max_val is not None:
                max_val = float(max_val)
                if min_val >= max_val:
                    raise RuleValidationError(f"Bracket {i} has min >= max.")
                prev_max = max_val
            else:
                prev_max = float('inf')

    def _validate_flat_rate(self, rate: Any) -> None:
        if rate is None:
            raise RuleValidationError("Flat rule missing rate.")
        rate_val = float(rate)
        if not (0.0 <= rate_val <= 1.0):
            raise RuleValidationError(f"Invalid flat rate {rate_val}.")
