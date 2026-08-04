"""Unit tests for Rule Engine Domain Models."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from taxos.domain.rules import (
    FilingStatus,
    JurisdictionLevel,
    ProgressiveTaxRule,
    TaxBracket,
    TaxRuleSet,
)


class TestRulesDomain:
    """Tests for Pydantic domain models."""

    def test_tax_bracket_validation(self) -> None:
        """Valid brackets should pass, invalid should fail."""
        # Valid
        bracket = TaxBracket(
            min_amount=Decimal("0"), max_amount=Decimal("1000"), rate=Decimal("0.10")
        )
        assert bracket.rate == Decimal("0.10")

        # Invalid rate
        with pytest.raises(ValidationError):
            TaxBracket(min_amount=Decimal("0"), rate=Decimal("1.5"))  # > 1

        # Invalid min
        with pytest.raises(ValidationError):
            TaxBracket(min_amount=Decimal("-100"), rate=Decimal("0.1"))

    def test_progressive_rule(self) -> None:
        """Test progressive rule construction."""
        rule = ProgressiveTaxRule(
            name="Income Tax",
            brackets=[
                TaxBracket(
                    min_amount=Decimal("0"), max_amount=Decimal("1000"), rate=Decimal("0.10")
                ),
                TaxBracket(min_amount=Decimal("1000"), rate=Decimal("0.20")),
            ],
        )
        assert rule.type == "progressive"
        assert len(rule.brackets) == 2

    def test_tax_rule_set_get_rules(self) -> None:
        """Test retrieving rules for specific filing status."""
        rule1 = ProgressiveTaxRule(
            name="R1", brackets=[TaxBracket(min_amount=Decimal("0"), rate=Decimal("0.1"))]
        )
        rule2 = ProgressiveTaxRule(
            name="R2", brackets=[TaxBracket(min_amount=Decimal("0"), rate=Decimal("0.2"))]
        )

        rule_set = TaxRuleSet(
            jurisdiction="US",
            level=JurisdictionLevel.COUNTRY,
            tax_year=2024,
            rules={
                FilingStatus.SINGLE: [rule1],
                "all": [rule2],
            },
        )

        single_rules = rule_set.get_rules_for_status(FilingStatus.SINGLE)
        assert len(single_rules) == 2
        assert rule2 in single_rules
        assert rule1 in single_rules

        married_rules = rule_set.get_rules_for_status(FilingStatus.MARRIED_JOINTLY)
        assert len(married_rules) == 1
        assert rule2 in married_rules
