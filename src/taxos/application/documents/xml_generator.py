"""XML document generator.

Generates a structured XML representation of calculator results.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from xml.etree.ElementTree import Element, SubElement, tostring

from taxos.domain.calculators.schema import CalculatorConfig
from taxos.domain.documents.schema import ReportTemplateConfig


class XMLDocumentGenerator:
    """Generates XML exports from any calculator's results."""

    def generate(
        self,
        calculator_config: CalculatorConfig,
        results: dict[str, Any],
        template: ReportTemplateConfig,
        inputs_data: dict[str, Any] | None = None,
    ) -> bytes:
        """Generate an XML byte string."""
        root = Element("TaxReport")
        root.set("calculator", calculator_config.slug)
        root.set("template", template.id)
        root.set("generated", datetime.now(UTC).isoformat())

        # Meta
        meta = SubElement(root, "Meta")
        SubElement(meta, "Title").text = calculator_config.title
        SubElement(meta, "Description").text = calculator_config.description
        SubElement(meta, "Currency").text = template.locale.currency_code
        SubElement(meta, "Version").text = template.version

        # Inputs
        if inputs_data:
            inputs_el = SubElement(root, "Inputs")
            for inp in calculator_config.inputs:
                val = inputs_data.get(inp.id, inp.default)
                field_el = SubElement(inputs_el, "Input")
                field_el.set("id", inp.id)
                field_el.set("type", inp.type)
                SubElement(field_el, "Label").text = inp.label
                SubElement(field_el, "Value").text = str(val) if val is not None else ""

        # Results
        results_el = SubElement(root, "Results")
        for formula in calculator_config.formulas:
            val = results.get(formula.id)
            item = SubElement(results_el, "Item")
            item.set("id", formula.id)
            item.set("format", formula.format)
            item.set("is_result", str(formula.is_result).lower())
            SubElement(item, "Label").text = formula.label or formula.id
            SubElement(item, "Value").text = str(val) if val is not None else ""

        xml_bytes = tostring(root, encoding="unicode", xml_declaration=False)
        return ('<?xml version="1.0" encoding="UTF-8"?>\n' + xml_bytes).encode("utf-8")
