"""Screen 4 Comparative Review visual rendering helpers.

These helpers render static visual evidence only from a validated Screen 4
deterministic comparison output contract and explicit visual-shaped
evidence_rows. They do not compute comparison truth, create samples, infer
time-series points, use browser-side logic, or render empty visual shells.
"""

from __future__ import annotations

from html import escape
from numbers import Real
from typing import Any

from src.reporting.dashboard.screen4.comparative_visual_eligibility import (
    DISTRIBUTION_VIOLIN,
    STATUS_ELIGIBLE,
    TIME_SERIES_OVERLAY,
    evaluate_screen4_comparative_visual_eligibility,
)


def render_screen4_comparative_visuals(comparative_state: dict[str, Any]) -> str:
    """Render populated Screen 4 comparative visuals from eligible evidence rows."""

    if not isinstance(comparative_state, dict):
        return ""
    if comparative_state.get("state") != "comparison_output_ready":
        return ""
    validation = comparative_state.get("validation")
    if not isinstance(validation, dict) or not validation.get("valid"):
        return ""
    contract = validation.get("output")
    if not isinstance(contract, dict) or not contract:
        return ""

    sections = [
        _render_time_series_visual(contract),
        _render_distribution_visual(contract),
    ]
    rendered_sections = [section for section in sections if section.strip()]
    if not rendered_sections:
        return ""
    return f"""
      <div class="screen4-comparative-visuals"
           data-screen4-comparative-visuals="validated-evidence-rows">
        {"".join(rendered_sections)}
      </div>
    """


def _render_time_series_visual(contract: dict[str, Any]) -> str:
    eligibility = evaluate_screen4_comparative_visual_eligibility(
        contract,
        TIME_SERIES_OVERLAY,
    )
    if eligibility.status != STATUS_ELIGIBLE or not eligibility.rendering_allowed:
        return ""
    metric = _first_time_series_metric(contract)
    if not metric:
        return ""
    rows = metric["rows"]
    if len(rows) < 2:
        return ""
    svg = _render_time_series_svg(metric)
    table = _render_table(
        [
            {
                "timestamp": row["timestamp"],
                "target_a_value": row["target_a_value"],
                "target_b_value": row["target_b_value"],
                "unit": row.get("unit"),
                "alignment_basis": row.get("alignment_basis"),
            }
            for row in rows
        ],
        [
            ("timestamp", "Timestamp"),
            ("target_a_value", "Target A Value"),
            ("target_b_value", "Target B Value"),
            ("unit", "Unit"),
            ("alignment_basis", "Alignment Basis"),
        ],
        "screen4-comparative-time-series-values",
    )
    if not svg or not table:
        return ""
    title = _display_value(metric.get("metric_label") or metric.get("metric_key"))
    unit = _display_value(metric.get("unit"))
    unit_note = f" ({escape(unit)})" if unit else ""
    return f"""
      <section class="evidence-pane screen4-comparative-time-series-evidence"
               data-screen4-comparative-visual="{escape(TIME_SERIES_OVERLAY, quote=True)}">
        <h3>Time-Series Evidence</h3>
        <p class="meta">
          {escape(title)}{unit_note} from validated deterministic comparison output.
        </p>
        {svg}
        {table}
      </section>
    """


def _render_distribution_visual(contract: dict[str, Any]) -> str:
    eligibility = evaluate_screen4_comparative_visual_eligibility(
        contract,
        DISTRIBUTION_VIOLIN,
    )
    if eligibility.status != STATUS_ELIGIBLE or not eligibility.rendering_allowed:
        return ""
    metric = _first_distribution_metric(contract)
    if not metric:
        return ""
    target_a_samples = metric["target_a_samples"]
    target_b_samples = metric["target_b_samples"]
    if len(target_a_samples) < 3 or len(target_b_samples) < 3:
        return ""
    svg = _render_distribution_svg(metric)
    table = _render_table(
        [
            {
                "target": "Target A",
                "sample_count": len(target_a_samples),
                "values": ", ".join(_format_number(value) for value in target_a_samples),
                "unit": metric.get("unit"),
            },
            {
                "target": "Target B",
                "sample_count": len(target_b_samples),
                "values": ", ".join(_format_number(value) for value in target_b_samples),
                "unit": metric.get("unit"),
            },
        ],
        [
            ("target", "Target"),
            ("sample_count", "Sample Count"),
            ("values", "Values"),
            ("unit", "Unit"),
        ],
        "screen4-comparative-distribution-values",
    )
    if not svg or not table:
        return ""
    title = _display_value(metric.get("metric_label") or metric.get("metric_key"))
    unit = _display_value(metric.get("unit"))
    unit_note = f" ({escape(unit)})" if unit else ""
    return f"""
      <section class="evidence-pane screen4-comparative-distribution-evidence"
               data-screen4-comparative-visual="{escape(DISTRIBUTION_VIOLIN, quote=True)}"
               data-screen4-distribution-rendering="sample-plot">
        <h3>Distribution Evidence</h3>
        <p class="meta">
          {escape(title)}{unit_note} as a conservative sample plot from validated Target A/B samples.
          No density curve is estimated.
        </p>
        {svg}
        {table}
      </section>
    """


def _first_time_series_metric(contract: dict[str, Any]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    for row in _visual_rows(contract, TIME_SERIES_OVERLAY):
        metric_key = str(row.get("metric_key") or "").strip()
        if not metric_key:
            continue
        if metric_key not in groups:
            groups[metric_key] = []
            order.append(metric_key)
        groups[metric_key].append(row)
    for metric_key in order:
        rows = sorted(groups[metric_key], key=lambda item: str(item.get("timestamp") or ""))
        if len(rows) < 2:
            continue
        if not all(
            _is_number(row.get("target_a_value"))
            and _is_number(row.get("target_b_value"))
            and _has_text(row.get("timestamp"))
            for row in rows
        ):
            continue
        first = rows[0]
        return {
            "metric_key": metric_key,
            "metric_label": first.get("metric_label") or first.get("metric"),
            "unit": first.get("unit"),
            "rows": rows,
        }
    return {}


def _first_distribution_metric(contract: dict[str, Any]) -> dict[str, Any]:
    paired: list[dict[str, Any]] = []
    separate: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for row in _visual_rows(contract, DISTRIBUTION_VIOLIN):
        metric_key = str(row.get("metric_key") or "").strip()
        if not metric_key:
            continue
        if row.get("target_a_samples") is not None or row.get("target_b_samples") is not None:
            paired.append(row)
            continue
        target = _normalize_target_side(row.get("target"))
        samples = row.get("samples")
        if target not in {"A", "B"} or not _numeric_samples(samples):
            continue
        if metric_key not in separate:
            separate[metric_key] = {}
            order.append(metric_key)
        separate[metric_key][target] = row

    for row in paired:
        target_a_samples = _numeric_samples(row.get("target_a_samples"))
        target_b_samples = _numeric_samples(row.get("target_b_samples"))
        if len(target_a_samples) >= 3 and len(target_b_samples) >= 3:
            return {
                "metric_key": str(row.get("metric_key") or "").strip(),
                "metric_label": row.get("metric_label") or row.get("metric"),
                "unit": row.get("unit"),
                "target_a_samples": target_a_samples,
                "target_b_samples": target_b_samples,
            }

    for metric_key in order:
        rows = separate[metric_key]
        target_a = rows.get("A")
        target_b = rows.get("B")
        if not target_a or not target_b:
            continue
        target_a_samples = _numeric_samples(target_a.get("samples"))
        target_b_samples = _numeric_samples(target_b.get("samples"))
        if len(target_a_samples) >= 3 and len(target_b_samples) >= 3:
            return {
                "metric_key": metric_key,
                "metric_label": target_a.get("metric_label") or target_b.get("metric_label"),
                "unit": target_a.get("unit") or target_b.get("unit"),
                "target_a_samples": target_a_samples,
                "target_b_samples": target_b_samples,
            }
    return {}


def _render_time_series_svg(metric: dict[str, Any]) -> str:
    rows = metric["rows"]
    width = 680
    height = 250
    left = 76
    right = 28
    top = 32
    bottom = 58
    plot_width = width - left - right
    plot_height = height - top - bottom
    values = [
        float(row[value_key])
        for row in rows
        for value_key in ("target_a_value", "target_b_value")
    ]
    min_value = min(values)
    max_value = max(values)
    value_range = max_value - min_value

    def x_at(index: int) -> float:
        if len(rows) == 1:
            return left + plot_width / 2
        return left + (plot_width * index / (len(rows) - 1))

    def y_at(value: float) -> float:
        if value_range == 0:
            return top + plot_height / 2
        return top + plot_height - ((value - min_value) / value_range * plot_height)

    target_a_points = [
        (x_at(index), y_at(float(row["target_a_value"])))
        for index, row in enumerate(rows)
    ]
    target_b_points = [
        (x_at(index), y_at(float(row["target_b_value"])))
        for index, row in enumerate(rows)
    ]
    target_a_path = _svg_path(target_a_points)
    target_b_path = _svg_path(target_b_points)
    if not target_a_path or not target_b_path:
        return ""
    metric_label = _display_value(metric.get("metric_label") or metric.get("metric_key"))
    first_timestamp = _display_value(rows[0].get("timestamp"))
    last_timestamp = _display_value(rows[-1].get("timestamp"))
    target_a_marks = "".join(
        _svg_circle(x, y, "#2563eb", "Target A")
        for x, y in target_a_points
    )
    target_b_marks = "".join(
        _svg_circle(x, y, "#0f766e", "Target B")
        for x, y in target_b_points
    )
    return f"""
      <figure class="screen4-comparative-visual-figure">
        <svg class="screen4-comparative-time-series-svg"
             viewBox="0 0 {width} {height}"
             role="img"
             aria-label="Time-Series Evidence for {escape(metric_label, quote=True)}">
          <rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" rx="8"></rect>
          <line x1="{left}" y1="{top + plot_height}" x2="{width - right}" y2="{top + plot_height}"
                stroke="#94a3b8" stroke-width="1"></line>
          <line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}"
                stroke="#94a3b8" stroke-width="1"></line>
          <text x="{left}" y="20" fill="#0f172a" font-size="13" font-weight="700">{escape(metric_label)}</text>
          <text x="{left}" y="{height - 22}" fill="#475569" font-size="11">{escape(first_timestamp)}</text>
          <text x="{width - right}" y="{height - 22}" fill="#475569" font-size="11" text-anchor="end">{escape(last_timestamp)}</text>
          <text x="{left - 8}" y="{top + 5}" fill="#475569" font-size="11" text-anchor="end">{escape(_format_number(max_value))}</text>
          <text x="{left - 8}" y="{top + plot_height}" fill="#475569" font-size="11" text-anchor="end">{escape(_format_number(min_value))}</text>
          <path d="{target_a_path}" fill="none" stroke="#2563eb" stroke-width="2.5"></path>
          <path d="{target_b_path}" fill="none" stroke="#0f766e" stroke-width="2.5"></path>
          {target_a_marks}
          {target_b_marks}
          <circle cx="{width - 196}" cy="18" r="4" fill="#2563eb"></circle>
          <text x="{width - 186}" y="22" fill="#334155" font-size="11">Target A</text>
          <circle cx="{width - 112}" cy="18" r="4" fill="#0f766e"></circle>
          <text x="{width - 102}" y="22" fill="#334155" font-size="11">Target B</text>
        </svg>
      </figure>
    """


def _render_distribution_svg(metric: dict[str, Any]) -> str:
    target_a_samples = metric["target_a_samples"]
    target_b_samples = metric["target_b_samples"]
    width = 680
    height = 220
    left = 86
    right = 34
    top = 42
    plot_width = width - left - right
    target_a_y = 84
    target_b_y = 146
    values = [float(value) for value in target_a_samples + target_b_samples]
    min_value = min(values)
    max_value = max(values)
    value_range = max_value - min_value

    def x_at(value: float) -> float:
        if value_range == 0:
            return left + plot_width / 2
        return left + ((value - min_value) / value_range * plot_width)

    target_a_marks = "".join(
        _svg_circle(x_at(float(value)), target_a_y, "#2563eb", f"Target A {index + 1}")
        for index, value in enumerate(target_a_samples)
    )
    target_b_marks = "".join(
        _svg_circle(x_at(float(value)), target_b_y, "#0f766e", f"Target B {index + 1}")
        for index, value in enumerate(target_b_samples)
    )
    if not target_a_marks or not target_b_marks:
        return ""
    metric_label = _display_value(metric.get("metric_label") or metric.get("metric_key"))
    return f"""
      <figure class="screen4-comparative-visual-figure">
        <svg class="screen4-comparative-distribution-svg"
             viewBox="0 0 {width} {height}"
             role="img"
             aria-label="Distribution Evidence for {escape(metric_label, quote=True)}">
          <rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" rx="8"></rect>
          <text x="{left}" y="24" fill="#0f172a" font-size="13" font-weight="700">{escape(metric_label)}</text>
          <line x1="{left}" y1="{target_a_y}" x2="{width - right}" y2="{target_a_y}" stroke="#cbd5e1" stroke-width="1"></line>
          <line x1="{left}" y1="{target_b_y}" x2="{width - right}" y2="{target_b_y}" stroke="#cbd5e1" stroke-width="1"></line>
          <text x="{left - 12}" y="{target_a_y + 4}" fill="#334155" font-size="12" text-anchor="end">Target A</text>
          <text x="{left - 12}" y="{target_b_y + 4}" fill="#334155" font-size="12" text-anchor="end">Target B</text>
          <text x="{left}" y="{height - 24}" fill="#475569" font-size="11">{escape(_format_number(min_value))}</text>
          <text x="{width - right}" y="{height - 24}" fill="#475569" font-size="11" text-anchor="end">{escape(_format_number(max_value))}</text>
          {target_a_marks}
          {target_b_marks}
        </svg>
      </figure>
    """


def _visual_rows(contract: dict[str, Any], visualization: str) -> list[dict[str, Any]]:
    return [
        row
        for row in _dict_rows(contract.get("evidence_rows"))
        if _row_visualization(row) == visualization
    ]


def _render_table(
    rows: list[dict[str, Any]],
    columns: list[tuple[str, str]],
    class_name: str,
) -> str:
    if not rows:
        return ""
    active_columns = [
        (key, label)
        for key, label in columns
        if any(_has_display_value(row.get(key)) for row in rows)
    ]
    if not active_columns:
        return ""
    header = "".join(f"<th>{escape(label)}</th>" for _, label in active_columns)
    body_rows = []
    for row in rows:
        cells = "".join(
            f"<td>{escape(_display_value(row.get(key)))}</td>"
            for key, _ in active_columns
        )
        body_rows.append(f"<tr>{cells}</tr>")
    return f"""
      <div class="table-wrap {escape(class_name, quote=True)}">
        <table>
          <thead><tr>{header}</tr></thead>
          <tbody>{"".join(body_rows)}</tbody>
        </table>
      </div>
    """


def _svg_path(points: list[tuple[float, float]]) -> str:
    if not points:
        return ""
    first_x, first_y = points[0]
    parts = [f"M {_format_coord(first_x)} {_format_coord(first_y)}"]
    for x, y in points[1:]:
        parts.append(f"L {_format_coord(x)} {_format_coord(y)}")
    return " ".join(parts)


def _svg_circle(x: float, y: float, color: str, label: str) -> str:
    return (
        f'<circle cx="{_format_coord(x)}" cy="{_format_coord(y)}" r="4.5" '
        f'fill="{escape(color, quote=True)}">'
        f"<title>{escape(label)}</title>"
        "</circle>"
    )


def _dict_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict) and row]


def _row_visualization(row: dict[str, Any]) -> str:
    return str(
        row.get("visualization")
        or row.get("visualization_name")
        or row.get("visual_type")
        or ""
    ).strip()


def _numeric_samples(value: Any) -> list[float]:
    if not isinstance(value, list) or not value:
        return []
    samples = []
    for item in value:
        if not _is_number(item):
            return []
        samples.append(float(item))
    return samples


def _normalize_target_side(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"a", "target_a", "target a", "baseline", "target-a"}:
        return "A"
    if text in {"b", "target_b", "target b", "candidate", "target-b"}:
        return "B"
    return ""


def _format_coord(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _format_number(value: Any) -> str:
    if not _is_number(value):
        return _display_value(value)
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.4f}".rstrip("0").rstrip(".")


def _display_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value if _has_display_value(item))
    return str(value)


def _has_display_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_number(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)
