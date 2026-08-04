"""JSON document generator.

Generates a structured JSON representation of calculator results
with full metadata.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from taxos.domain.calculators.schema import CalculatorConfig
from taxos.domain.documents.schema import ReportTemplateConfig


class JSONDocumentGenerator:
    """Generates JSON exports from any calculator's results."""

    def generate(
        self,
        calculator_config: CalculatorConfig,
        results: dict[str, Any],
        template: ReportTemplateConfig,
        inputs_data: dict[str, Any] | None = None,
    ) -> bytes:
        """Generate a JSON byte string with full report metadata."""
        report: dict[str, Any] = {
            "meta": {
                "calculator": calculator_config.slug,
                "title": calculator_config.title,
                "description": calculator_config.description,
                "template": template.id,
                "generated_at": datetime.now(UTC).isoformat(),
                "currency": template.locale.currency_code,
                "version": template.version,
            },
            "inputs": {},
            "results": {},
            "breakdown": [],
        }

        # Inputs
        if inputs_data:
            for inp in calculator_config.inputs:
                val = inputs_data.get(inp.id, inp.default)
                report["inputs"][inp.id] = {
                    "label": inp.label,
                    "value": val,
                    "type": inp.type,
                }

        # Results — only is_result formulas
        for formula in calculator_config.formulas:
            if formula.is_result:
                val = results.get(formula.id)
                report["results"][formula.id] = {
                    "label": formula.label or formula.id,
                    "value": val,
                    "format": formula.format,
                }

        # Full breakdown — all formulas
        for formula in calculator_config.formulas:
            val = results.get(formula.id)
            report["breakdown"].append(
                {
                    "id": formula.id,
                    "label": formula.label or formula.id,
                    "value": val,
                    "format": formula.format,
                    "is_result": formula.is_result,
                }
            )

        return json.dumps(report, indent=2, default=str).encode("utf-8")
