from decimal import Decimal

import pytest

from taxos.application.updater.validator import RuleValidationError, TaxRuleValidator
from taxos.domain.rules import JurisdictionLevel, ProgressiveTaxRule, TaxBracket, TaxRuleSet


@pytest.fixture
def base_ruleset():
    return TaxRuleSet(
        jurisdiction="US",
        level=JurisdictionLevel.COUNTRY,
        tax_year=2024,
        currency="USD",
        rules={
            "single": [
                ProgressiveTaxRule(
                    name="Federal Income Tax",
                    brackets=[
                        TaxBracket(
                            min_amount=Decimal("0"),
                            max_amount=Decimal("11600"),
                            rate=Decimal("0.10"),
                        ),
                        TaxBracket(
                            min_amount=Decimal("11600"),
                            max_amount=Decimal("47150"),
                            rate=Decimal("0.12"),
                        ),
                        TaxBracket(
                            min_amount=Decimal("47150"), max_amount=None, rate=Decimal("0.22")
                        ),
                    ],
                )
            ]
        },
    )


def test_valid_ruleset(base_ruleset):
    validator = TaxRuleValidator()
    validator.validate(base_ruleset)


def test_validator_overlapping_brackets(base_ruleset):
    rule = base_ruleset.rules["single"][0]
    # min_amount=10000 overlaps with max_amount=11600 from previous
    bad_bracket = TaxBracket(
        min_amount=Decimal("10000"), max_amount=Decimal("47150"), rate=Decimal("0.12")
    )
    new_rule = rule.model_copy(
        update={"brackets": [rule.brackets[0], bad_bracket, rule.brackets[2]]}
    )
    new_ruleset = base_ruleset.model_copy(update={"rules": {"single": [new_rule]}})

    validator = TaxRuleValidator()
    with pytest.raises(RuleValidationError, match="Overlapping brackets"):
        validator.validate(new_ruleset)
