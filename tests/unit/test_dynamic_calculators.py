"""Unit tests for the Dynamic Calculator Framework."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from taxos.application.calculators.evaluator import AsyncSafeEvaluator, FormulaError, evaluate_calculator
from taxos.application.calculators.factory import CalculatorFactory
from taxos.domain.calculators.schema import CalculatorConfig, InputField, FormulaConfig, OutputConfig


@pytest.mark.asyncio
async def test_safe_evaluator_basic_math() -> None:
    evaluator = AsyncSafeEvaluator({"income": 100000.0, "deduction": 12000.0, "rate": 0.25})
    
    # Addition / Subtraction
    assert await evaluator.eval("income - deduction") == 88000.0
    
    # Multiplication / Division
    assert await evaluator.eval("(income - deduction) * rate") == 22000.0
    assert await evaluator.eval("income / 2") == 50000.0
    
    # Unary
    assert await evaluator.eval("-income") == -100000.0

@pytest.mark.asyncio
async def test_safe_evaluator_security() -> None:
    evaluator = AsyncSafeEvaluator({"x": 10})
    
    # Block function calls
    with pytest.raises(FormulaError):
        await evaluator.eval("print('hello')")
        
    # Block imports
    with pytest.raises(FormulaError):
        await evaluator.eval("__import__('os').system('echo hi')")
        
    # Block unknown variables
    with pytest.raises(FormulaError):
        await evaluator.eval("x + y")

@pytest.mark.asyncio
async def test_evaluate_calculator() -> None:
    config = CalculatorConfig(
        slug="test",
        title="Test",
        description="Test",
        inputs=[
            InputField(id="a", label="A", type="number", default=10),
            InputField(id="b", label="B", type="number", default=5),
        ],
        formulas=[
            FormulaConfig(id="c", expression="a + b", is_result=True)
        ],
        output=OutputConfig(summary_cards=["c"])
    )
    
    # Test with defaults
    res1 = await evaluate_calculator(config, {})
    assert res1["c"] == 15.0
    
    # Test with overrides
    res2 = await evaluate_calculator(config, {"a": 20, "b": 10})
    assert res2["c"] == 30.0


def test_calculator_factory(tmp_path) -> None:
    # Write a fake JSON
    rules_dir = tmp_path / "calculators"
    rules_dir.mkdir()
    config_file = rules_dir / "test.json"
    
    config_file.write_text('''
    {
      "slug": "factory-test",
      "title": "Test",
      "description": "Test",
      "inputs": [
        {"id": "amt", "label": "Amount", "type": "number", "required": true, "min_value": 0}
      ],
      "formulas": [],
      "output": {"summary_cards": []}
    }
    ''')
    
    factory = CalculatorFactory(config_dir=rules_dir)
    assert "factory-test" in factory.calculators
    
    model = factory.get_request_model("factory-test")
    assert model is not None
    
    # Test validation
    with pytest.raises(ValidationError):
        model(amt=-5)  # min_value=0
        
    valid = model(amt=100)
    assert valid.amt == 100
