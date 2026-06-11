"""Shared helpers for contract-backed dashboard product renderers.

The helpers in this module render deterministic HTML fragments from view model
data only. They do not read browser state, generated dashboard artifacts, or
runtime selectors.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from html import escape
from math import isfinite
from typing import Any


_TECHNICAL_KEYS = {
    "domain",
    "row_id",
    "source",
    "source_evidence_ids",
    "visualization_id",
}
_STRUCTURED_KEYS = {"points"}


def escape_text(value: Any) -> str:
    if value is None:
        return ""
    return escape(str(value), quote=True)


def join_fragments(parts: Iterable[str]) -> str:
    return "".join(part for part in parts if part)


def render_root(screen_id: str, title: str, parts: Sequence[str]) -> str:
    return (
        f'<section class="evidence-screen" data-screen="{escape_text(screen_id)}">'
        f"<h2>{escape_text(title)}</h2>"
        f"{join_fragments(parts)}"
        "</section>"
    )


def render_identity(selected_flow_id: str, evidence_pack_id: str) -> str:
    return (
        '<section class="selected-context product-card-grid">'
        f'{render_fact_card("Selected flow", selected_flow_id, "selected-flow-context")}'
        f'{render_fact_card("Evidence pack", evidence_pack_id, "evidence-pack-context")}'
        "</section>"
    )


def render_summary(availability_status: str, summary: str | None) -> str:
    body = [
        '<section class="product-summary-card">',
        "<h3>Summary</h3>",
        f'<p class="availability-status">{escape_text(availability_status)}</p>',
    ]
    if summary:
        body.append(f"<p>{escape_text(summary)}</p>")
    body.append("</section>")
    return join_fragments(body)


def render_mapping(title: str, mapping: Mapping[str, Any] | None) -> str:
    if not mapping:
        return ""
    rows = []
    for key in sorted(mapping):
        rows.append(
            "<tr>"
            f"<th>{escape_text(key)}</th>"
            f"<td>{escape_text(_display_value(mapping[key]))}</td>"
            "</tr>"
        )
    return (
        '<details class="debug-provenance">'
        f"<summary>{escape_text(title)}</summary>"
        f"<table><tbody>{join_fragments(rows)}</tbody></table>"
        "</details>"
    )


def render_items(title: str, items: Sequence[Mapping[str, Any]], class_name: str) -> str:
    if not items:
        return ""
    rendered = [render_product_card(_card_heading(item), _card_values(item)) for item in items]
    return (
        f'<section class="{escape_text(class_name)}">'
        f"<h3>{escape_text(title)}</h3>"
        f'<div class="product-card-grid">{join_fragments(rendered)}</div>'
        "</section>"
    )


def render_rows(title: str, rows: Sequence[Mapping[str, Any]]) -> str:
    return render_items(title, rows, "evidence-card-section")


def render_state_lists(
    *,
    missing_evidence: Sequence[Mapping[str, Any]],
    unavailable_evidence: Sequence[Mapping[str, Any]],
    stale_evidence: Sequence[Mapping[str, Any]],
) -> str:
    return join_fragments(
        (
            render_state_cards("Missing evidence", missing_evidence, "missing-evidence"),
            render_state_cards("Unavailable evidence", unavailable_evidence, "unavailable-evidence"),
            render_state_cards("Stale evidence", stale_evidence, "stale-evidence"),
        )
    )


def render_visualizations(
    visualizations: Sequence[Mapping[str, Any]],
    *,
    trends: Sequence[Mapping[str, Any]] = (),
    rows: Sequence[Mapping[str, Any]] = (),
    title: str = "Visual evidence",
) -> str:
    """Render deterministic visual components from view model data.

    ``allowed_visualizations`` is treated as permission metadata only. The
    rendered components come from deterministic trend points or distribution
    samples, not from the visualization metadata itself.
    """

    time_series = _time_series_from_trends(trends)
    distributions = _distribution_series(rows)
    parts: list[str] = []
    if time_series:
        parts.append(render_time_series_charts(time_series))
    elif _has_requested_visual_kind(visualizations, {"trend", "line", "bar"}):
        parts.append(
            render_unavailable_card(
                "Time-series unavailable",
                "Deterministic time-series point evidence is not available for this selection.",
            )
        )

    if distributions:
        parts.append(render_violin_diagrams(distributions))
    elif _has_requested_visual_kind(visualizations, {"distribution"}):
        parts.append(
            render_unavailable_card(
                "Violin diagram unavailable",
                "Deterministic distribution sample evidence is not available for this selection.",
            )
        )

    if not parts:
        parts.append(
            render_unavailable_card(
                "Visual evidence unavailable",
                "No deterministic visual point or distribution evidence is available for this selection.",
            )
        )
    return (
        '<section class="product-visual-section">'
        f"<h3>{escape_text(title)}</h3>"
        f"{join_fragments(parts)}"
        "</section>"
    )


def render_llm_eligibility(eligibility: Sequence[Mapping[str, Any]]) -> str:
    if not eligibility:
        return ""
    return (
        '<details class="debug-llm-eligibility">'
        "<summary>LLM explanation eligibility</summary>"
        f"{render_items('Eligibility metadata', eligibility, 'llm-explanation-eligibility')}"
        "</details>"
    )


def render_group(title: str, parts: Sequence[str], class_name: str) -> str:
    return (
        f'<section class="{escape_text(class_name)}">'
        f"<h3>{escape_text(title)}</h3>"
        f"{join_fragments(parts)}"
        "</section>"
    )


def render_named_collections(collections: Sequence[tuple[str, Sequence[Mapping[str, Any]]]]) -> str:
    return join_fragments(render_items(title, items, _slug(title)) for title, items in collections)


def render_fact_card(label: str, value: Any, class_name: str = "fact-card") -> str:
    return (
        f'<article class="product-card {escape_text(class_name)}">'
        f"<h4>{escape_text(label)}</h4>"
        f"<p>{escape_text(_display_value(value))}</p>"
        "</article>"
    )


def render_product_card(title: str, values: Mapping[str, Any], class_name: str = "product-card") -> str:
    rows = []
    for key in sorted(values):
        if key in _TECHNICAL_KEYS or key in _STRUCTURED_KEYS:
            continue
        value = values[key]
        if value is None:
            continue
        rows.append(
            "<tr>"
            f"<th>{escape_text(_label(key))}</th>"
            f"<td>{escape_text(_display_value(value))}</td>"
            "</tr>"
        )
    if not rows:
        rows.append("<tr><td>No scalar evidence fields available.</td></tr>")
    return (
        f'<article class="{escape_text(class_name)}">'
        f"<h4>{escape_text(title)}</h4>"
        f"<table><tbody>{join_fragments(rows)}</tbody></table>"
        "</article>"
    )


def render_metric_cards(title: str, metrics: Sequence[Mapping[str, Any]]) -> str:
    if not metrics:
        return ""
    cards = []
    for metric in metrics:
        name = metric.get("metric_name") or metric.get("name") or "Metric"
        value = metric.get("value")
        unit = metric.get("unit")
        display_value = f"{value} {unit}".strip() if unit else value
        cards.append(render_fact_card(str(name), display_value, "metric-card"))
    return (
        '<section class="metric-card-section">'
        f"<h3>{escape_text(title)}</h3>"
        f'<div class="product-card-grid">{join_fragments(cards)}</div>'
        "</section>"
    )


def render_trend_cards(title: str, trends: Sequence[Mapping[str, Any]]) -> str:
    if not trends:
        return ""
    cards = []
    for trend in trends:
        values = {
            "direction": trend.get("direction"),
            "point_count": len(_numeric_points(trend.get("points"))),
        }
        cards.append(render_product_card(str(trend.get("trend_name") or "Trend"), values, "trend-card"))
    return (
        '<section class="trend-card-section">'
        f"<h3>{escape_text(title)}</h3>"
        f'<div class="product-card-grid">{join_fragments(cards)}</div>'
        "</section>"
    )


def render_anomaly_cards(title: str, anomalies: Sequence[Mapping[str, Any]]) -> str:
    if not anomalies:
        return ""
    cards = []
    for anomaly in anomalies:
        values = {
            "severity": anomaly.get("severity"),
            "description": anomaly.get("description"),
        }
        cards.append(render_product_card(str(anomaly.get("anomaly_name") or "Anomaly"), values, "anomaly-card"))
    return (
        '<section class="anomaly-card-section">'
        f"<h3>{escape_text(title)}</h3>"
        f'<div class="product-card-grid">{join_fragments(cards)}</div>'
        "</section>"
    )


def render_confidence_cards(title: str, confidence: Sequence[Mapping[str, Any]]) -> str:
    if not confidence:
        return ""
    cards = []
    for item in confidence:
        cards.append(
            render_product_card(
                str(item.get("basis_id") or "Confidence basis"),
                {
                    "confidence": item.get("confidence"),
                    "factors": item.get("factors"),
                },
                "confidence-card",
            )
        )
    return (
        '<section class="confidence-card-section">'
        f"<h3>{escape_text(title)}</h3>"
        f'<div class="product-card-grid">{join_fragments(cards)}</div>'
        "</section>"
    )


def render_state_cards(title: str, items: Sequence[Mapping[str, Any]], class_name: str) -> str:
    if not items:
        return ""
    cards = []
    for item in items:
        cards.append(
            render_product_card(
                str(item.get("reason_code") or title),
                {
                    "domain": item.get("domain"),
                    "message": item.get("message"),
                    "as_of": item.get("as_of"),
                    "required_for_modes": item.get("required_for_modes"),
                },
                "state-card",
            )
        )
    return (
        f'<section class="{escape_text(class_name)}">'
        f"<h3>{escape_text(title)}</h3>"
        f'<div class="product-card-grid">{join_fragments(cards)}</div>'
        "</section>"
    )


def render_unavailable_card(title: str, message: str) -> str:
    return (
        '<article class="product-card unavailable-card">'
        f"<h4>{escape_text(title)}</h4>"
        f"<p>{escape_text(message)}</p>"
        "</article>"
    )


def render_status_panel(title: str, facts: Mapping[str, Any]) -> str:
    cards = [
        render_fact_card(_label(key), value, "status-fact")
        for key, value in facts.items()
        if value is not None and value != ""
    ]
    if not cards:
        return ""
    return (
        '<section class="status-panel">'
        f"<h3>{escape_text(title)}</h3>"
        f'<div class="product-card-grid">{join_fragments(cards)}</div>'
        "</section>"
    )


def _slug(value: str) -> str:
    return value.lower().replace("/", "-").replace(" ", "-")


def _card_values(item: Mapping[str, Any]) -> Mapping[str, Any]:
    values = item.get("values")
    if isinstance(values, Mapping):
        return values
    return {
        key: value
        for key, value in item.items()
        if key not in _TECHNICAL_KEYS and key not in _STRUCTURED_KEYS
    }


def _card_heading(item: Mapping[str, Any]) -> str:
    values = _card_values(item)
    for key in (
        "metric_name",
        "trend_name",
        "anomaly_name",
        "recommendation",
        "action",
        "learning_candidate",
        "governance_status",
        "signal",
        "primary_domain",
    ):
        value = values.get(key) or item.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return "Evidence item"


def _display_value(value: Any) -> str:
    if isinstance(value, Mapping):
        return "Structured evidence"
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        scalars = [item for item in value if not isinstance(item, (Mapping, Sequence)) or isinstance(item, str)]
        if 0 < len(scalars) <= 3 and len(scalars) == len(value):
            return ", ".join(str(item) for item in scalars)
        return f"{len(value)} values"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return "" if value is None else str(value)


def _label(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").strip().title()


def _has_requested_visual_kind(
    visualizations: Sequence[Mapping[str, Any]],
    kinds: set[str],
) -> bool:
    return any(str(item.get("kind") or "").lower() in kinds for item in visualizations)


def _time_series_from_trends(
    trends: Sequence[Mapping[str, Any]],
) -> list[tuple[str, list[tuple[str, float]]]]:
    series = []
    for trend in trends:
        points = _numeric_points(trend.get("points"))
        if points:
            series.append((str(trend.get("trend_name") or "Trend"), points))
    return series


def _numeric_points(value: Any) -> list[tuple[str, float]]:
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray, str)):
        return []
    points: list[tuple[str, float]] = []
    for index, point in enumerate(value):
        if not isinstance(point, Mapping):
            continue
        numeric = _first_number(point, ("value", "y", "metric_value", "sample"))
        if numeric is None:
            continue
        label = str(point.get("label") or point.get("x") or point.get("timestamp") or point.get("index") or index)
        points.append((label, numeric))
    return points


def _distribution_series(rows: Sequence[Mapping[str, Any]]) -> list[tuple[str, list[float]]]:
    distributions = []
    for row in rows:
        values = row.get("values") if isinstance(row.get("values"), Mapping) else row
        if not isinstance(values, Mapping):
            continue
        for key, value in values.items():
            normalized = str(key).lower()
            if not any(fragment in normalized for fragment in ("distribution", "violin", "samples")):
                continue
            numbers = _number_sequence(value)
            if numbers:
                distributions.append((_label(str(key)), numbers))
    return distributions


def _number_sequence(value: Any) -> list[float]:
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray, str)):
        return []
    numbers = []
    for item in value:
        number = _number(item)
        if number is not None:
            numbers.append(number)
    return numbers


def _first_number(source: Mapping[str, Any], keys: Sequence[str]) -> float | None:
    for key in keys:
        number = _number(source.get(key))
        if number is not None:
            return number
    return None


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if isfinite(number) else None
    try:
        number = float(str(value))
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None


def render_time_series_charts(series: Sequence[tuple[str, Sequence[tuple[str, float]]]]) -> str:
    charts = []
    for name, points in series:
        charts.append(
            '<article class="product-visual time-series-chart">'
            f"<h4>{escape_text(name)}</h4>"
            f'{_polyline_svg(points, "time-series-plot")}'
            "</article>"
        )
    return join_fragments(charts)


def render_violin_diagrams(series: Sequence[tuple[str, Sequence[float]]]) -> str:
    diagrams = []
    for name, values in series:
        diagrams.append(
            '<article class="product-visual violin-visual">'
            f"<h4>{escape_text(name)}</h4>"
            f"{_violin_svg(values)}"
            "</article>"
        )
    return join_fragments(diagrams)


def _polyline_svg(points: Sequence[tuple[str, float]], class_name: str) -> str:
    if not points:
        return ""
    width = 320
    height = 120
    pad = 12
    values = [point[1] for point in points]
    minimum = min(values)
    maximum = max(values)
    span = maximum - minimum or 1.0
    denominator = max(len(points) - 1, 1)
    coords = []
    for index, (_label_text, value) in enumerate(points):
        x = pad + ((width - (pad * 2)) * index / denominator)
        y = height - pad - ((height - (pad * 2)) * (value - minimum) / span)
        coords.append(f"{x:.1f},{y:.1f}")
    return (
        f'<svg class="{escape_text(class_name)}" data-visual-kind="time-series" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Time-series plot">'
        '<line class="chart-axis" x1="12" y1="108" x2="308" y2="108"></line>'
        f'<polyline class="chart-line" fill="none" points="{" ".join(coords)}"></polyline>'
        "</svg>"
    )


def _violin_svg(values: Sequence[float]) -> str:
    if not values:
        return ""
    width = 320
    height = 120
    minimum = min(values)
    maximum = max(values)
    span = maximum - minimum or 1.0
    buckets = [0, 0, 0, 0, 0]
    for value in values:
        bucket = min(int(((value - minimum) / span) * len(buckets)), len(buckets) - 1)
        buckets[bucket] += 1
    max_bucket = max(buckets) or 1
    parts = []
    for index, count in enumerate(buckets):
        y = 16 + index * 18
        half_width = 8 + (count / max_bucket) * 70
        parts.append(
            f'<rect class="violin-band" x="{160 - half_width:.1f}" y="{y}" '
            f'width="{half_width * 2:.1f}" height="12" rx="6"></rect>'
        )
    return (
        '<svg class="violin-diagram" data-visual-kind="violin" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Violin distribution diagram">'
        f"{join_fragments(parts)}"
        "</svg>"
    )
