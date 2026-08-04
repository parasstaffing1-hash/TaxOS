"""CSV document generator.

Generates a flat CSV representation of calculator results.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from taxos.domain.calculators.schema import CalculatorConfig
from taxos.domain.documents.schema import ReportTemplateConfig


class CSVDocumentGenerator:
    """Generates CSV exports from any calculator's results."""

    def generate(
        self,
        calculator_config: CalculatorConfig,
        results: dict[str, Any],
        template: ReportTemplateConfig,
        inputs_data: dict[str, Any] | None = None,
    ) -> bytes:
        """Generate a CSV byte string."""
        stream = io.StringIO()
        writer = csv.writer(stream)

        sym = template.locale.currency_symbol

        # Header
        writer.writerow([f"{calculator_config.title} — Calculation Report"])
        writer.writerow([])

        # Inputs section
        if inputs_data:
            writer.writerow(["--- Inputs ---"])
            writer.writerow(["Field", "Value"])
            for inp in calculator_config.inputs:
                val = inputs_data.get(inp.id, inp.default)
                writer.writerow([inp.label, val])
            writer.writerow([])

        # Results section
        writer.writerow(["--- Results ---"])
        writer.writerow(["Item", "Value", "Format"])

        for formula in calculator_config.formulas:
            val = results.get(formula.id)
            if val is None:
                continue
            label = formula.label or formula.id

            if formula.format == "currency":
                display = f"{sym}{float(val):,.2f}"
            elif formula.format == "percentage":
                display = f"{float(val):.2f}%"
            else:
                display = str(val)

            writer.writerow([label, display, formula.format])

        return stream.getvalue().encode("utf-8")
