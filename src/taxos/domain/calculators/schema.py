"""Configuration schemas for the Dynamic Calculator Framework."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class InputField(BaseModel):
    """Defines a single UI input field and its validation rules."""

    id: str
    label: str
    type: Literal["currency", "number", "percentage", "select", "boolean"]
    required: bool = True
    default: Any = None
    min_value: float | None = None
    max_value: float | None = None
    options: list[dict[str, str]] | None = None  # For select inputs: [{"label": "Yes", "value": "yes"}]
    help_text: str | None = None


class FormulaConfig(BaseModel):
    """Defines a single calculation step."""

    id: str
    expression: str
    label: str | None = None
    format: Literal["currency", "percentage", "number"] = "currency"
    is_result: bool = False  # If True, this is surfaced to the main output UI


class ChartConfig(BaseModel):
    """Defines a chart to render."""

    id: str
    type: Literal["pie", "bar", "line"]
    title: str
    data_sources: list[str]  # IDs of formulas or inputs to include in this chart


class OutputConfig(BaseModel):
    """Defines how to display the final results."""

    summary_cards: list[str]  # IDs of formulas to show as large cards
    charts: list[ChartConfig] = Field(default_factory=list)


class CalculatorConfig(BaseModel):
    """The root configuration for a dynamic calculator."""

    slug: str
    title: str
    description: str
    inputs: list[InputField]
    formulas: list[FormulaConfig]
    output: OutputConfig
