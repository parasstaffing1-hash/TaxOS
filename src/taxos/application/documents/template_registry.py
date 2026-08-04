"""Report template registry — auto-discovers JSON templates from disk.

Templates are stored in ``rules/report_templates/*.json`` and are loaded
into memory at startup. The registry provides lookup, CRUD, and a
built-in fallback ``default`` template for calculators that don't
specify a template.
"""

from __future__ import annotations

import json
from pathlib import Path

import structlog

from taxos.domain.documents.schema import (
    BrandingConfig,
    LocaleConfig,
    ReportChartConfig,
    ReportTemplateConfig,
    SectionConfig,
)

logger = structlog.get_logger(__name__)


def _build_default_template() -> ReportTemplateConfig:
    """Build the hardcoded fallback template used when no template is specified."""
    return ReportTemplateConfig(
        id="default",
        name="Default Report",
        description="Auto-generated report that works with any calculator.",
        version="1.0",
        orientation="portrait",
        page_size="A4",
        template_style="corporate",
        branding=BrandingConfig(),
        locale=LocaleConfig(),
        sections=[
            SectionConfig(id="cover", type="cover_page", title="Tax Calculation Report"),
            SectionConfig(id="summary", type="summary_cards", title="Summary"),
            SectionConfig(id="inputs", type="inputs_table", title="Calculation Inputs"),
            SectionConfig(id="breakdown", type="breakdown_table", title="Detailed Breakdown"),
            SectionConfig(id="chart_break", type="page_break"),
            SectionConfig(
                id="pie_chart",
                type="chart",
                title="Distribution",
                chart=ReportChartConfig(
                    id="auto_pie",
                    type="pie",
                    title="Tax Distribution",
                    data_sources=[],  # Will be auto-populated from is_result formulas
                ),
            ),
            SectionConfig(
                id="bar_chart",
                type="chart",
                title="Comparison",
                chart=ReportChartConfig(
                    id="auto_bar",
                    type="bar",
                    title="Value Comparison",
                    data_sources=[],
                ),
            ),
            SectionConfig(
                id="disclaimer",
                type="disclaimer",
                content=(
                    "This report is generated for informational purposes only and does not "
                    "constitute professional tax advice. Consult a qualified tax professional "
                    "for guidance specific to your situation."
                ),
            ),
        ],
    )


class TemplateRegistry:
    """Discovers and manages report template configurations."""

    def __init__(self, templates_dir: str | Path = "rules/report_templates") -> None:
        self.templates_dir = Path(templates_dir)
        self._templates: dict[str, ReportTemplateConfig] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Scan the templates directory and load all JSON files."""
        # Always register the built-in default
        default = _build_default_template()
        self._templates[default.id] = default

        if not self.templates_dir.exists():
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            logger.info("created_templates_directory", path=str(self.templates_dir))
            return

        for file_path in self.templates_dir.glob("*.json"):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                template = ReportTemplateConfig(**data)
                self._templates[template.id] = template
                logger.debug("loaded_report_template", id=template.id, name=template.name)
            except Exception:
                logger.exception("template_load_error", file=str(file_path))

    def get(self, template_id: str) -> ReportTemplateConfig | None:
        """Retrieve a template by ID."""
        return self._templates.get(template_id)

    def get_default(self) -> ReportTemplateConfig:
        """Return the default fallback template."""
        return self._templates["default"]

    def list_all(self) -> list[ReportTemplateConfig]:
        """Return all registered templates."""
        return list(self._templates.values())

    def save(self, template: ReportTemplateConfig) -> None:
        """Save a template to disk and update the in-memory cache."""
        if not self.templates_dir.exists():
            self.templates_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.templates_dir / f"{template.id}.json"
        file_path.write_text(template.model_dump_json(indent=2), encoding="utf-8")
        self._templates[template.id] = template

    def delete(self, template_id: str) -> bool:
        """Delete a template from disk and cache."""
        if template_id == "default":
            return False  # Cannot delete the built-in default
        file_path = self.templates_dir / f"{template_id}.json"
        if file_path.exists():
            file_path.unlink()
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False

    def reload(self) -> None:
        """Re-scan the disk and reload all templates."""
        self._templates.clear()
        self._load_templates()
