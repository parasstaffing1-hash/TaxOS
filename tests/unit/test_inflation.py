"""Unit tests for the Inflation Adjuster."""

from __future__ import annotations

from decimal import Decimal

import pytest

from taxos.application.calculations.inflation import InflationAdjuster
from taxos.domain.rules import (
    DeductionRule,
    ProgressiveTaxRule,
    TaxBracket,
)


class TestInflationAdjuster:
    """Test scaling tax brackets and limits."""

    def test_progressive_bracket_scaling(self) -> None:
        """Test that bracket thresholds scale with inflation but rates stay the same."""
        rule = ProgressiveTaxRule(
            name="Fed",
            brackets=[
                TaxBracket(
                    min_amount=Decimal("0"), max_amount=Decimal("10000"), rate=Decimal("0.10")
                ),
                TaxBracket(min_amount=Decimal("10000"), rate=Decimal("0.20")),
            ],
        )

        # 5% inflation
        multiplier = Decimal("1.05")
        adjusted_rule = InflationAdjuster.adjust_rule(rule, multiplier)

        # Ensure deep copy
        assert adjusted_rule is not rule

        if isinstance(adjusted_rule, ProgressiveTaxRule):
            assert adjusted_rule.brackets[0].max_amount == Decimal("10500.00")
            assert adjusted_rule.brackets[0].rate == Decimal("0.10")  # unchanged

            assert adjusted_rule.brackets[1].min_amount == Decimal("10500.00")
            assert adjusted_rule.brackets[1].max_amount is None

    def test_deduction_scaling(self) -> None:
        """Test flat deductions scale but percentages do not."""
        flat = DeductionRule(name="Standard", amount=Decimal("10000"))
        pct = DeductionRule(
            name="401k", amount=Decimal("0.20"), is_percentage=True, max_limit=Decimal("20000")
        )

        multiplier = Decimal("1.10")  # 10% inflation

        adj_flat = InflationAdjuster.adjust_rule(flat, multiplier)
        if isinstance(adj_flat, DeductionRule):
            assert adj_flat.amount == Decimal("11000.00")

        adj_pct = InflationAdjuster.adjust_rule(pct, multiplier)
        if isinstance(adj_pct, DeductionRule):
            assert adj_pct.amount == Decimal("0.20")  # pct rate unchanged
            assert adj_pct.max_limit == Decimal("22000.00")  # flat limit changed

    def test_zero_inflation_raises(self) -> None:
        """Test invalid multipliers."""
        rule = DeductionRule(name="Rule", amount=Decimal("100"))
        with pytest.raises(ValueError, match="greater than zero"):
            InflationAdjuster.adjust_rule(rule, Decimal("0.0"))
