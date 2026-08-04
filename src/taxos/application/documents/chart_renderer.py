"""Chart renderer — generates PNG images from calculator results using matplotlib.

Used by the PDF generator to embed charts, and can be used standalone.
"""

from __future__ import annotations

import io
from typing import Any

from taxos.domain.calculators.schema import CalculatorConfig
from taxos.domain.documents.schema import ReportChartConfig


# Default color palette
_DEFAULT_COLORS = [
    "#1a56db", "#059669", "#d97706", "#dc2626", "#7c3aed",
    "#0891b2", "#be185d", "#4f46e5", "#65a30d", "#ea580c",
]


def render_chart_to_png(
    chart_config: ReportChartConfig,
    results: dict[str, Any],
    calculator_config: CalculatorConfig,
    dpi: int = 150,
) -> bytes:
    """Render a chart as a PNG byte string using matplotlib.

    Args:
        chart_config: Chart configuration (type, title, data sources, colors).
        results: The calculated results dict from the calculator evaluator.
        calculator_config: The calculator configuration (for label lookups).
        dpi: Output resolution.

    Returns:
        PNG image bytes.
    """
    # Lazy import — matplotlib is heavy, only load when needed
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt

    colors = chart_config.colors or _DEFAULT_COLORS

    # Build label → value pairs from data sources
    labels: list[str] = []
    values: list[float] = []

    for source_id in chart_config.data_sources:
        raw_val = results.get(source_id)
        if raw_val is None:
            continue
        try:
            val = float(raw_val)
        except (TypeError, ValueError):
            continue

        # Find a human label from formulas or inputs
        label = source_id
        for formula in calculator_config.formulas:
            if formula.id == source_id and formula.label:
                label = formula.label
                break
        else:
            for inp in calculator_config.inputs:
                if inp.id == source_id:
                    label = inp.label
                    break

        labels.append(label)
        values.append(val)

    if not values:
        # Return a tiny transparent PNG if no data
        fig, ax = plt.subplots(figsize=(4, 2))
        ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=12, color="#999")
        ax.axis("off")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", transparent=True)
        plt.close(fig)
        return buf.getvalue()

    chart_type = chart_config.type
    fig_w = chart_config.width / dpi * 1.2
    fig_h = chart_config.height / dpi * 1.2

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    chart_colors = colors[: len(values)]

    if chart_type == "pie":
        # Filter out zero/negative values for pie charts
        filtered = [(l, v) for l, v in zip(labels, values) if v > 0]
        if filtered:
            pie_labels, pie_values = zip(*filtered)
            pie_colors = chart_colors[: len(pie_values)]
            ax.pie(
                pie_values,
                labels=pie_labels,
                autopct="%1.1f%%",
                colors=pie_colors,
                startangle=90,
            )
        ax.set_title(chart_config.title, fontsize=14, fontweight="bold", pad=15)

    elif chart_type == "line":
        ax.plot(labels, values, marker="o", color=chart_colors[0], linewidth=2)
        ax.set_title(chart_config.title, fontsize=14, fontweight="bold")
        ax.set_ylabel("Value")
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=30, ha="right")

    elif chart_type == "area":
        ax.fill_between(range(len(values)), values, alpha=0.4, color=chart_colors[0])
        ax.plot(range(len(values)), values, color=chart_colors[0], linewidth=2)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=30, ha="right")
        ax.set_title(chart_config.title, fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)

    elif chart_type == "stacked_bar":
        # For stacked, treat each value as a segment of a single bar
        bottom = 0.0
        for i, (label, val) in enumerate(zip(labels, values)):
            ax.bar("Total", val, bottom=bottom, color=chart_colors[i % len(chart_colors)], label=label)
            bottom += val
        ax.set_title(chart_config.title, fontsize=14, fontweight="bold")
        ax.legend(loc="upper right", fontsize=8)

    else:  # "bar" or default
        bars = ax.bar(labels, values, color=chart_colors[: len(values)])
        ax.set_title(chart_config.title, fontsize=14, fontweight="bold")
        ax.set_ylabel("Value")
        plt.xticks(rotation=30, ha="right")
        # Add value labels on bars
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height(),
                f"{val:,.0f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()
