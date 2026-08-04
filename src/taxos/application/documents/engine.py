"""Universal Document Engine — central dispatcher.

Routes document generation requests to the appropriate format-specific
generator. This is the single entry point that the API layer calls.

Every calculator in TaxOS automatically gets professional document
generation through this engine without writing custom report code.
"""

from __future__ import annotations

from typing import Any, Literal

import structlog

from taxos.domain.calculators.schema import CalculatorConfig
from taxos.domain.documents.schema import ReportTemplateConfig

logger = structlog.get_logger(__name__)

ExportFormat = Literal["pdf", "excel", "csv", "json", "html", "xml", "markdown", "text"]

# Map format → MIME type
MIME_TYPES: dict[str, str] = {
    "pdf": "application/pdf",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
    "json": "application/json",
    "html": "text/html",
    "xml": "application/xml",
    "markdown": "text/markdown",
    "text": "text/plain",
}

FILE_EXTENSIONS: dict[str, str] = {
    "pdf": ".pdf",
    "excel": ".xlsx",
    "csv": ".csv",
    "json": ".json",
    "html": ".html",
    "xml": ".xml",
    "markdown": ".md",
    "text": ".txt",
}


def _auto_populate_chart_sources(
    template: ReportTemplateConfig,
    calculator_config: CalculatorConfig,
) -> ReportTemplateConfig:
    """Fill in empty chart data_sources with is_result formula IDs.

    The default template ships with empty data_sources on its charts
    so that it works generically with any calculator. This function
    populates them from the calculator's formula metadata.
    """
    result_ids = [f.id for f in calculator_config.formulas if f.is_result]

    for section in template.sections:
        if section.type == "chart" and section.chart:
            if not section.chart.data_sources:
                section.chart.data_sources = result_ids

    return template


class DocumentEngine:
    """Central dispatcher for document generation.

    Usage::

        engine = DocumentEngine()
        pdf_bytes = engine.generate(
            format="pdf",
            calculator_config=config,
            results=results_dict,
            template=template_config,
            inputs_data=user_inputs,
        )
    """

    def generate(
        self,
        format: ExportFormat,
        calculator_config: CalculatorConfig,
        results: dict[str, Any],
        template: ReportTemplateConfig,
        inputs_data: dict[str, Any] | None = None,
    ) -> bytes:
        """Generate a document in the specified format.

        Args:
            format: One of: pdf, excel, csv, json, html, xml, markdown, text.
            calculator_config: The calculator configuration that produced the results.
            results: The calculated results dict from the evaluator.
            template: The report template configuration.
            inputs_data: The original user inputs (optional, for the inputs section).

        Returns:
            The generated document as raw bytes.

        Raises:
            ValueError: If the format is not supported.
        """
        # Auto-populate chart data sources if empty
        template = _auto_populate_chart_sources(template, calculator_config)

        logger.info(
            "document_generation_started",
            format=format,
            calculator=calculator_config.slug,
            template=template.id,
        )

        if format == "pdf":
            from taxos.application.documents.pdf_generator import PDFDocumentGenerator
            return PDFDocumentGenerator().generate(calculator_config, results, template, inputs_data)

        if format == "excel":
            from taxos.application.documents.excel_generator import ExcelDocumentGenerator
            return ExcelDocumentGenerator().generate(calculator_config, results, template, inputs_data)

        if format == "csv":
            from taxos.application.documents.csv_generator import CSVDocumentGenerator
            return CSVDocumentGenerator().generate(calculator_config, results, template, inputs_data)

        if format == "json":
            from taxos.application.documents.json_generator import JSONDocumentGenerator
            return JSONDocumentGenerator().generate(calculator_config, results, template, inputs_data)

        if format == "html":
            from taxos.application.documents.html_generator import HTMLDocumentGenerator
            return HTMLDocumentGenerator().generate(calculator_config, results, template, inputs_data)

        if format == "xml":
            from taxos.application.documents.xml_generator import XMLDocumentGenerator
            return XMLDocumentGenerator().generate(calculator_config, results, template, inputs_data)

        if format == "markdown":
            from taxos.application.documents.markdown_generator import MarkdownDocumentGenerator
            return MarkdownDocumentGenerator().generate(calculator_config, results, template, inputs_data)

        if format == "text":
            # Plain text falls back to markdown (it renders well as plain text)
            from taxos.application.documents.markdown_generator import MarkdownDocumentGenerator
            return MarkdownDocumentGenerator().generate(calculator_config, results, template, inputs_data)

        raise ValueError(f"Unsupported export format: {format}")

    @staticmethod
    def get_mime_type(format: ExportFormat) -> str:
        """Return the MIME type for a given format."""
        return MIME_TYPES.get(format, "application/octet-stream")

    @staticmethod
    def get_file_extension(format: ExportFormat) -> str:
        """Return the file extension for a given format."""
        return FILE_EXTENSIONS.get(format, ".bin")
