"""HTML document generator.

Generates a self-contained HTML report with inline CSS
suitable for browser viewing, printing, or email.
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from typing import Any

import structlog

from taxos.application.documents.chart_renderer import render_chart_to_png
from taxos.domain.calculators.schema import CalculatorConfig
from taxos.domain.documents.schema import ReportTemplateConfig

logger = structlog.get_logger(__name__)


def _hex_to_rgb(hex_color: str) -> str:
    """Convert #RRGGBB to 'R, G, B' string."""
    h = hex_color.lstrip("#")
    return ", ".join(str(int(h[i : i + 2], 16)) for i in (0, 2, 4))


def _format_value(val: Any, fmt: str, currency_symbol: str) -> str:
    """Format a value based on its format type."""
    if val is None:
        return "—"
    try:
        fval = float(val)
    except (TypeError, ValueError):
        return str(val)

    if fmt == "currency":
        return f"{currency_symbol}{fval:,.2f}"
    if fmt == "percentage":
        return f"{fval:.2f}%"
    return f"{fval:,.2f}"


class HTMLDocumentGenerator:
    """Generates self-contained HTML reports from any calculator's results."""

    def generate(
        self,
        calculator_config: CalculatorConfig,
        results: dict[str, Any],
        template: ReportTemplateConfig,
        inputs_data: dict[str, Any] | None = None,
    ) -> bytes:
        """Generate an HTML byte string."""
        b = template.branding
        sym = template.locale.currency_symbol
        primary = b.primary_color
        primary_rgb = _hex_to_rgb(primary)
        now = datetime.now(UTC).strftime(template.locale.date_format)

        # Build result rows
        summary_rows = ""
        for formula in calculator_config.formulas:
            if formula.is_result:
                val = _format_value(results.get(formula.id), formula.format, sym)
                label = formula.label or formula.id
                summary_rows += f'<div class="card"><div class="card-label">{label}</div><div class="card-value">{val}</div></div>\n'

        # Build inputs table rows
        inputs_html = ""
        if inputs_data:
            for inp in calculator_config.inputs:
                val = inputs_data.get(inp.id, inp.default)
                inputs_html += f"<tr><td>{inp.label}</td><td>{val}</td></tr>\n"

        # Build breakdown table rows
        breakdown_rows = ""
        for formula in calculator_config.formulas:
            val = _format_value(results.get(formula.id), formula.format, sym)
            label = formula.label or formula.id
            breakdown_rows += f"<tr><td>{label}</td><td>{val}</td></tr>\n"

        # Build chart images (embedded as base64)
        chart_images = ""
        for section in template.sections:
            if section.type == "chart" and section.chart:
                try:
                    png_bytes = render_chart_to_png(section.chart, results, calculator_config)
                    b64 = base64.b64encode(png_bytes).decode("ascii")
                    chart_images += (
                        f'<div class="chart-container">'
                        f"<h3>{section.chart.title}</h3>"
                        f'<img src="data:image/png;base64,{b64}" alt="{section.chart.title}" />'
                        f"</div>\n"
                    )
                except Exception:
                    logger.warning("chart_rendering_failed", exc_info=True)

        # Disclaimer
        disclaimer = ""
        for section in template.sections:
            if section.type == "disclaimer" and section.content:
                disclaimer = f'<div class="disclaimer">{section.content}</div>'

        html = f"""<!DOCTYPE html>
<html lang="{template.locale.language}" dir="{'rtl' if template.locale.rtl else 'ltr'}">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{calculator_config.title} — Report</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1f2937; background: #f9fafb; line-height: 1.6; }}
  .container {{ max-width: 900px; margin: 0 auto; padding: 2rem; }}
  .header {{ background: {primary}; color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; }}
  .header h1 {{ font-size: 1.75rem; margin-bottom: 0.25rem; }}
  .header p {{ opacity: 0.85; font-size: 0.95rem; }}
  .meta {{ font-size: 0.8rem; opacity: 0.7; margin-top: 0.5rem; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
  .card {{ background: white; border: 1px solid #e5e7eb; border-radius: 10px; padding: 1.25rem; }}
  .card-label {{ font-size: 0.85rem; color: #6b7280; margin-bottom: 0.25rem; }}
  .card-value {{ font-size: 1.5rem; font-weight: 700; color: {primary}; }}
  .section {{ background: white; border: 1px solid #e5e7eb; border-radius: 10px; padding: 1.5rem; margin-bottom: 1.5rem; }}
  .section h2 {{ font-size: 1.15rem; color: {primary}; margin-bottom: 1rem; border-bottom: 2px solid {primary}; padding-bottom: 0.5rem; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ text-align: left; padding: 0.6rem 0.75rem; border-bottom: 1px solid #e5e7eb; }}
  th {{ background: rgba({primary_rgb}, 0.08); font-weight: 600; font-size: 0.85rem; color: #374151; }}
  tr:hover {{ background: #f9fafb; }}
  .chart-container {{ text-align: center; margin: 1rem 0; }}
  .chart-container img {{ max-width: 100%; height: auto; border-radius: 8px; }}
  .chart-container h3 {{ font-size: 1rem; color: #374151; margin-bottom: 0.75rem; }}
  .disclaimer {{ font-size: 0.8rem; color: #9ca3af; padding: 1rem; border-top: 1px solid #e5e7eb; margin-top: 2rem; }}
  .footer {{ text-align: center; font-size: 0.75rem; color: #9ca3af; margin-top: 2rem; padding: 1rem 0; }}
  @media print {{
    body {{ background: white; }}
    .container {{ padding: 0; }}
    .header {{ border-radius: 0; }}
  }}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>{calculator_config.title}</h1>
  <p>{calculator_config.description}</p>
  <div class="meta">{b.company_name} &middot; Generated {now}</div>
</div>

<div class="cards">
{summary_rows}
</div>

{f'''<div class="section">
<h2>Calculation Inputs</h2>
<table><tr><th>Field</th><th>Value</th></tr>
{inputs_html}
</table>
</div>''' if inputs_html else ''}

<div class="section">
<h2>Detailed Breakdown</h2>
<table><tr><th>Item</th><th>Value</th></tr>
{breakdown_rows}
</table>
</div>

{chart_images}

{disclaimer}

<div class="footer">{b.footer_text}</div>

</div>
</body>
</html>"""

        return html.encode("utf-8")
