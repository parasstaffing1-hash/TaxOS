"""Validation Engine for ensuring integrity of normalized tax rules."""

from __future__ import annotations

from decimal import Decimal

import structlog

from taxos.domain.rules import ProgressiveTaxRule, TaxRuleSet

logger = structlog.get_logger(__name__)


class RuleValidationError(ValueError):
    """Raised when normalized tax rules violate business logic constraints."""


class TaxRuleValidator:
    """Validates structural and mathematical integrity of normalized tax data."""

    def validate(self, ruleset: TaxRuleSet) -> None:
        """Run all validation checks against a TaxRuleSet.

        Raises:
            RuleValidationError: If any constraint is violated.
        """
        self._validate_brackets(ruleset)
        self._validate_dates(ruleset)

        logger.debug("ruleset_validation_passed", jurisdiction=ruleset.jurisdiction)

    def _validate_brackets(self, ruleset: TaxRuleSet) -> None:
        """Ensure brackets are contiguous and non-negative."""
        for _status, rules in ruleset.rules.items():
            for rule in rules:
                if not isinstance(rule, ProgressiveTaxRule):
                    continue

                brackets = rule.brackets
                if not brackets:
                    continue

                sorted_brackets = sorted(brackets, key=lambda b: b.min_amount)

                # Check for negatives
                for b in sorted_brackets:
                    if b.min_amount < 0:
                        raise RuleValidationError(f"Negative min_amount found in {rule.name}")
                    if b.rate < 0:
                        raise RuleValidationError(f"Negative rate found in {rule.name}")

                if sorted_brackets[0].min_amount != Decimal("0"):
                    raise RuleValidationError(f"First bracket in {rule.name} must start at zero")

                # Check for gaps and overlaps
                for i in range(len(sorted_brackets) - 1):
                    current = sorted_brackets[i]
                    next_bracket = sorted_brackets[i + 1]

                    if current.max_amount is None:
                        raise RuleValidationError(
                            f"Non-terminal bracket in {rule.name} missing max_amount"
                        )

                    curr_max = current.max_amount
                    next_min = next_bracket.min_amount
                    if curr_max is None:
                        raise RuleValidationError(
                            f"Non-terminal bracket in {rule.name} missing max_amount"
                        )

                    diff = next_min - curr_max
                    if diff < 0:
                        raise RuleValidationError(f"Overlapping brackets in {rule.name}")
                    if diff > Decimal("0"):
                        raise RuleValidationError(f"Gap found between brackets in {rule.name}")

    def _validate_dates(self, ruleset: TaxRuleSet) -> None:
        """Ensure effective dates are logically ordered."""
        if ruleset.valid_from and ruleset.valid_to and ruleset.valid_from > ruleset.valid_to:
            raise RuleValidationError("valid_from date after valid_to date")
