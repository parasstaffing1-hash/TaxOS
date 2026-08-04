"""Inflation adjustment utilities for tax rules."""

from __future__ import annotations

import copy
from decimal import Decimal

from taxos.application.calculations.utils import round_currency
from taxos.domain.rules import (
    DeductionRule,
    ProgressiveTaxRule,
    TaxBracket,
    TaxCreditRule,
    TaxRule,
)


class InflationAdjuster:
    """Utility to scale tax thresholds and amounts by an inflation index multiplier."""

    @staticmethod
    def adjust_rule(rule: TaxRule, inflation_multiplier: Decimal) -> TaxRule:
        """
        Adjust a single tax rule for inflation.
        Returns a new deep-copied and adjusted rule instance.
        """
        if inflation_multiplier <= 0:
            raise ValueError("Inflation multiplier must be greater than zero.")

        # We only want to adjust fixed financial thresholds/amounts, not percentages
        if isinstance(rule, ProgressiveTaxRule):
            new_brackets = []
            for bracket in rule.brackets:
                new_min = round_currency(bracket.min_amount * inflation_multiplier)
                new_max = None
                if bracket.max_amount is not None:
                    new_max = round_currency(bracket.max_amount * inflation_multiplier)

                new_fixed = None
                if bracket.fixed_amount is not None:
                    new_fixed = round_currency(bracket.fixed_amount * inflation_multiplier)

                new_brackets.append(
                    TaxBracket(
                        min_amount=new_min,
                        max_amount=new_max,
                        rate=bracket.rate,  # Rate stays the same
                        fixed_amount=new_fixed,
                    )
                )
            return rule.model_copy(update={"brackets": new_brackets})

        if isinstance(rule, DeductionRule):
            new_amount = (
                rule.amount
                if rule.is_percentage
                else round_currency(rule.amount * inflation_multiplier)
            )
            new_max = None
            if rule.max_limit is not None:
                new_max = round_currency(rule.max_limit * inflation_multiplier)
            return rule.model_copy(update={"amount": new_amount, "max_limit": new_max})

        if isinstance(rule, TaxCreditRule):
            new_amount = round_currency(rule.amount * inflation_multiplier)
            new_max = None
            if rule.max_limit is not None:
                new_max = round_currency(rule.max_limit * inflation_multiplier)
            return rule.model_copy(update={"amount": new_amount, "max_limit": new_max})

        # Flat taxes, percentage deductions, VAT, etc., typically don't scale by inflation
        # as their basis scales naturally with inflated income.
        return copy.deepcopy(rule)
