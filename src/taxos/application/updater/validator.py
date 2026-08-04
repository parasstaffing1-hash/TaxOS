"""Validation Engine for ensuring integrity of normalized tax rules."""

from __future__ import annotations

import structlog

from taxos.domain.rules import TaxRuleSet

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
        from taxos.domain.rules import ProgressiveTaxRule

        for status, rules in ruleset.rules.items():
            for rule in rules:
                if not isinstance(rule, ProgressiveTaxRule):
                    continue
                    
                brackets = rule.brackets
                if not brackets:
                    continue
                    
                sorted_brackets = sorted(brackets, key=lambda b: float(b.min_amount))
                
                # Check for negatives
                for b in sorted_brackets:
                    if float(b.min_amount) < 0:
                        raise RuleValidationError(f"Negative min_amount found in {rule.name}")
                    if float(b.rate) < 0:
                        raise RuleValidationError(f"Negative rate found in {rule.name}")
                
                # Check for gaps and overlaps
                for i in range(len(sorted_brackets) - 1):
                    current = sorted_brackets[i]
                    next_bracket = sorted_brackets[i + 1]
                    
                    if current.max_amount is None:
                        raise RuleValidationError(
                            f"Non-terminal bracket in {rule.name} missing max_amount"
                        )
                        
                    curr_max = float(current.max_amount)
                    next_min = float(next_bracket.min_amount)
                    
                    diff = next_min - curr_max
                    if diff < 0:
                        raise RuleValidationError(f"Overlapping brackets in {rule.name}")
                    if diff > 1.0:
                        raise RuleValidationError(f"Gap found between brackets in {rule.name}")

    def _validate_dates(self, ruleset: TaxRuleSet) -> None:
        """Ensure effective dates are logically ordered."""
        if ruleset.valid_from and ruleset.valid_to:
            if ruleset.valid_from > ruleset.valid_to:
                raise RuleValidationError("valid_from date after valid_to date")
