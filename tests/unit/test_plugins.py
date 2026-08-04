import pytest
from decimal import Decimal
from taxos.domain.rules import ProgressiveTaxRule, TaxBracket, FlatTaxRule
from taxos.application.calculations.plugins import ProgressiveTaxPlugin, FlatTaxPlugin
from taxos.application.calculations.base import CalculationContext


def test_progressive_tax_plugin():
    rule = ProgressiveTaxRule(
        name="Fed",
        brackets=[
            TaxBracket(min_amount=Decimal("0"), max_amount=Decimal("100"), rate=Decimal("0.10")),
            TaxBracket(min_amount=Decimal("100"), max_amount=None, rate=Decimal("0.20")),
        ]
    )
    plugin = ProgressiveTaxPlugin()
    assert plugin.can_handle(rule)
    
    context = CalculationContext.create(Decimal("200"))
    result = plugin.calculate(rule, context)
    
    assert result.rule_name == "Fed"
    assert result.tax_amount == Decimal("30.00")
    assert "brackets_applied" in result.details


def test_flat_tax_plugin():
    rule = FlatTaxRule(name="Flat", rate=Decimal("0.10"))
    plugin = FlatTaxPlugin()
    assert plugin.can_handle(rule)
    
    context = CalculationContext.create(Decimal("100"))
    result = plugin.calculate(rule, context)
    
    assert result.tax_amount == Decimal("10.00")
