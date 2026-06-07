"""Screen 4 Deep Analysis static visualization rendering helpers.

This module renders only from eligible visualization candidates selected from a
validated Deep Analysis contract. It does not call services, execute parsers or
comparisons, invoke LLMs, mutate runtime state, read/write files, or depend on
generated dashboard artifacts.
"""

from __future__ import annotations

from collections.abc import Mapping
from html import escape
from numbers import Real
import re
from typing import Any

from src.reporting.dashboard.screen4.deep_analysis_visual_selection import (
    DeepAnalysisVisualizationCandidate,
    DeepAnalysisVisualizationSelectionResult,
    VisualizationFamily,
    VisualizationStatus,
)


BLOCKED_SCOPES = {
    "comparative_output",
    "prepared_only",
    "cache_only",
    "fleet_population",
    "llm_explanation_only",
    "unknown_or_mixed",
}
STALE_FRESHNESS = {"stale", "cache_only", "cached_continuity_only"}
PLACEHOLDER_FLAGS = (
    "synthetic",
    "synthetic_row",
    "demo",
    "demo_row",
    "placeholder",
    "placeholder_row",
    "hard_coded",
    "hardcoded",
    "example",
)


def render_deep_analysis_visualizations(
    contract: Mapping[str, Any],
    selection_result: DeepAnalysisVisualizationSelectionResult | Mapping[str, Any] | None,
) -> str:
    """Render eligible Deep Analysis visualization candidates as static markup."""

    if not isinstance(contract, Mapping) or not contract:
        return ""
    rendered = [
        render_deep_analysis_visual_candidate(contract, candidate)
        for candidate in _eligible_candidates(selection_result)
    ]
    rendered = [item for item in rendered if item.strip()]
    if not rendered:
        return ""
    return f"""
      <section class="card secondary screen4-deep-analysis-visual-evidence"
               data-screen4-mode-section="deep-analysis"
               data-screen4-deep-analysis-visuals="selection-contract">
        <div class="section-kicker">Deep Analysis</div>
        <h2>Contract-Backed Visual Evidence</h2>
        <p class="meta">
          Visual evidence renders only from eligible visualization candidates selected from validated Deep Analysis contract rows.
          Deep Analysis uses its current-scope evidence contract; Comparative Review uses its own deterministic comparison output contract.
          No page identity, cache state, prepared target context, comparative output, or LLM text is used as visual proof.
        </p>
        {"".join(rendered)}
      </section>
    """


def render_deep_analysis_visual_candidate(
    contract: Mapping[str, Any],
    candidate: DeepAnalysisVisualizationCandidate | Mapping[str, Any],
) -> str:
    """Render one eligible candidate, or return an empty string."""

    if _candidate_status(candidate) != VisualizationStatus.ELIGIBLE.value:
        return ""
    family = _candidate_family(candidate)
    if family in {"fleet_population", "table_only"}:
        return ""
    rows = _candidate_rows(contract, candidate)
    if not rows:
        return ""
    section = _section_for_candidate(contract, candidate)
    if not _candidate_scope_allowed(candidate, rows):
        return ""

    if family in {"contribution", "ranked_contribution"}:
        body = _render_contribution_visual(rows, ranked=family == "ranked_contribution")
    elif family in {"time_series", "aligned_overlay"}:
        body = _render_time_series_visual(rows, aligned=family == "aligned_overlay")
    elif family == "distribution_evidence":
        body = _render_distribution_evidence_visual(rows)
    elif family == "pressure_band":
        body = _render_pressure_band_visual(rows)
    elif family == "topology_fact_map":
        body = _render_fact_cards(rows, "Topology / Fact Map")
    elif family == "anomaly_timeline":
        body = _render_timeline_visual(rows)
    elif family == "similarity_neighborhood":
        body = _render_fact_cards(rows, "Similarity Neighborhood")
    else:
        return ""

    if not body.strip():
        return ""

    title = _candidate_title(candidate)
    scope = _candidate_scope(candidate)
    supporting = _candidate_supporting(candidate)
    scope_label = (
        "Historical Supporting Context"
        if supporting or scope == "historical_supporting_context"
        else "Current Diagnostic Evidence"
    )
    support_note = (
        "Supporting visual; does not override selected-scope diagnostic truth."
        if supporting or scope == "historical_supporting_context"
        else "Current Diagnostic Evidence visual from the validated deterministic contract."
    )
    visual_id = f"screen4-deep-analysis-visual-{_slug(_candidate_id(candidate))}"
    return f"""
        <section class="evidence-pane screen4-deep-analysis-visual-candidate"
                 data-screen4-deep-analysis-visual-family="{escape(family, quote=True)}"
                 data-screen4-deep-analysis-visual-scope="{escape(scope, quote=True)}">
          <div class="section-kicker">{escape(scope_label)}</div>
          <h3 id="{escape(visual_id, quote=True)}">{escape(title)}</h3>
          <p class="meta">{escape(support_note)}</p>
          {_render_candidate_metadata(candidate, section)}
          <div class="screen4-deep-analysis-static-visual"
               role="group"
               aria-labelledby="{escape(visual_id, quote=True)}">
            {body}
          </div>
        </section>
    """


def _render_contribution_visual(
    rows: list[Mapping[str, Any]],
    *,
    ranked: bool,
) -> str:
    items = [
        (_row_label(row), _numeric_value(row), _unit(row))
        for row in rows
        if _numeric_value(row) is not None
    ]
    if not items:
        return ""
    if ranked:
        items = sorted(items, key=lambda item: abs(item[1]), reverse=True)
    max_value = max(abs(value) for _label, value, _unit_text in items) or 1.0
    row_html = []
    for index, (label, value, unit_text) in enumerate(items[:12], start=1):
        width = max(4.0, min(100.0, abs(value) / max_value * 100.0))
        prefix = f"{index}. " if ranked else ""
        row_html.append(
            f"""
            <div class="screen4-deep-analysis-bar-row">
              <span>{escape(prefix + label)}</span>
              <div class="screen4-deep-analysis-bar-track"
                   style="display:block;background:#e5e7eb;border-radius:4px;height:10px;overflow:hidden;">
                <span style="display:block;width:{width:.2f}%;height:10px;background:#2563eb;"></span>
              </div>
              <strong>{escape(_format_number(value))}{escape(_unit_suffix(unit_text))}</strong>
            </div>
            """
        )
    return f"""
        <div class="screen4-deep-analysis-bar-list"
             data-screen4-deep-analysis-static-visual="contribution-bars">
          {"".join(row_html)}
        </div>
    """


def _render_time_series_visual(
    rows: list[Mapping[str, Any]],
    *,
    aligned: bool,
) -> str:
    series = _series_points(rows, aligned=aligned)
    if not series:
        return ""
    all_points = [point for points in series.values() for point in points]
    if len(all_points) < 2:
        return ""

    width = 360
    height = 140
    left = 28
    right = 12
    top = 12
    bottom = 28
    values = [point[1] for point in all_points]
    min_value = min(values)
    max_value = max(values)
    if min_value == max_value:
        max_value = min_value + 1.0
    max_len = max(len(points) for points in series.values())
    if max_len < 2:
        return ""

    colors = ("#2563eb", "#0f766e", "#9333ea", "#b45309")
    line_html = []
    labels_html = []
    for index, (name, points) in enumerate(series.items()):
        if len(points) < 2:
            continue
        svg_points = []
        ordered = sorted(points, key=lambda item: item[0])
        for position, (_timestamp, value) in enumerate(ordered):
            x = left + (width - left - right) * position / max(1, len(ordered) - 1)
            y = top + (height - top - bottom) * (max_value - value) / (max_value - min_value)
            svg_points.append(f"{x:.2f},{y:.2f}")
        color = colors[index % len(colors)]
        line_html.append(
            f'<polyline points="{" ".join(svg_points)}" fill="none" stroke="{color}" stroke-width="2.5" />'
        )
        labels_html.append(
            f'<span><i style="display:inline-block;width:10px;height:10px;background:{color};"></i> {escape(name)}</span>'
        )
    if not line_html:
        return ""

    title = "Deep Analysis Time-Series Evidence"
    desc = f"Static trend from {len(all_points)} validated time-indexed evidence points."
    return f"""
        <figure class="screen4-deep-analysis-trend"
                data-screen4-deep-analysis-static-visual="time-series">
          <svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="deep-analysis-trend-title deep-analysis-trend-desc">
            <title id="deep-analysis-trend-title">{escape(title)}</title>
            <desc id="deep-analysis-trend-desc">{escape(desc)}</desc>
            <line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" stroke="#94a3b8" stroke-width="1" />
            <line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" stroke="#94a3b8" stroke-width="1" />
            {"".join(line_html)}
          </svg>
          <figcaption>{escape(desc)}</figcaption>
          <div class="screen4-deep-analysis-legend">{"".join(labels_html)}</div>
        </figure>
    """


def _render_distribution_evidence_visual(rows: list[Mapping[str, Any]]) -> str:
    samples: list[float] = []
    for row in rows:
        samples.extend(_numeric_samples(row))
    if len(samples) < 3:
        return ""
    min_value = min(samples)
    max_value = max(samples)
    if min_value == max_value:
        max_value = min_value + 1.0
    width = 360
    height = 82
    left = 24
    right = 24
    axis_y = 42
    dot_html = []
    for index, sample in enumerate(samples[:80]):
        x = left + (width - left - right) * (sample - min_value) / (max_value - min_value)
        y = axis_y - 6 if index % 2 else axis_y + 6
        dot_html.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#0f766e" opacity="0.78" />'
        )
    title = "Distribution Evidence"
    desc = f"Static dot strip from {len(samples)} real numeric samples; no density curve is estimated."
    return f"""
        <figure class="screen4-deep-analysis-distribution"
                data-screen4-deep-analysis-static-visual="distribution-evidence">
          <svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="deep-analysis-dist-title deep-analysis-dist-desc">
            <title id="deep-analysis-dist-title">{escape(title)}</title>
            <desc id="deep-analysis-dist-desc">{escape(desc)}</desc>
            <line x1="{left}" y1="{axis_y}" x2="{width - right}" y2="{axis_y}" stroke="#94a3b8" stroke-width="1.5" />
            {"".join(dot_html)}
            <text x="{left}" y="{height - 10}" font-size="10" fill="#475569">{escape(_format_number(min_value))}</text>
            <text x="{width - right}" y="{height - 10}" text-anchor="end" font-size="10" fill="#475569">{escape(_format_number(max_value))}</text>
          </svg>
          <figcaption>{escape(desc)} Label: Distribution Evidence.</figcaption>
        </figure>
    """


def _render_pressure_band_visual(rows: list[Mapping[str, Any]]) -> str:
    rendered = []
    for row in rows:
        value = _numeric_value(row)
        threshold = _threshold_value(row)
        if value is None or threshold is None:
            continue
        denominator = max(abs(value), abs(threshold), 1.0)
        value_width = min(100.0, abs(value) / denominator * 100.0)
        threshold_width = min(100.0, abs(threshold) / denominator * 100.0)
        rendered.append(
            f"""
            <div class="screen4-deep-analysis-pressure-row">
              <strong>{escape(_row_label(row))}</strong>
              <div style="position:relative;background:#e5e7eb;border-radius:4px;height:14px;overflow:hidden;">
                <span style="display:block;width:{value_width:.2f}%;height:14px;background:#dc2626;"></span>
                <span aria-label="threshold" style="position:absolute;left:{threshold_width:.2f}%;top:0;width:2px;height:14px;background:#111827;"></span>
              </div>
              <small>Value {escape(_format_number(value))}; threshold {escape(_format_number(threshold))}</small>
            </div>
            """
        )
    if not rendered:
        return ""
    return f"""
        <div class="screen4-deep-analysis-pressure-band"
             data-screen4-deep-analysis-static-visual="pressure-band">
          {"".join(rendered)}
        </div>
    """


def _render_fact_cards(rows: list[Mapping[str, Any]], visual_kind: str) -> str:
    cards = []
    for row in rows[:12]:
        value = _compact_value(row.get("deterministic_value"))
        if not value:
            continue
        cards.append(
            f"""
            <article class="screen4-deep-analysis-fact-card">
              <strong>{escape(_row_label(row))}</strong>
              <p>{escape(value)}</p>
            </article>
            """
        )
    if not cards:
        return ""
    return f"""
        <div class="screen4-deep-analysis-fact-grid"
             data-screen4-deep-analysis-static-visual="{escape(_slug(visual_kind), quote=True)}">
          {"".join(cards)}
        </div>
    """


def _render_timeline_visual(rows: list[Mapping[str, Any]]) -> str:
    events = []
    for row in rows:
        label = _row_label(row)
        value = _compact_value(row.get("deterministic_value"))
        timestamp = _time_value(row)
        if not timestamp and isinstance(row.get("deterministic_value"), Mapping):
            value_map = row.get("deterministic_value")
            timestamp = _first_text(value_map.get("start"), value_map.get("timestamp"), value_map.get("time_index"))
        if not timestamp:
            timestamp = "validated event"
        events.append((timestamp, label, value))
    if not events:
        return ""
    event_html = []
    for timestamp, label, value in events[:12]:
        event_html.append(
            f"""
            <li>
              <strong>{escape(timestamp)}</strong>
              <span>{escape(label)}</span>
              <small>{escape(value)}</small>
            </li>
            """
        )
    return f"""
        <ol class="screen4-deep-analysis-timeline"
            data-screen4-deep-analysis-static-visual="anomaly-timeline">
          {"".join(event_html)}
        </ol>
    """


def _render_candidate_metadata(
    candidate: DeepAnalysisVisualizationCandidate | Mapping[str, Any],
    section: Mapping[str, Any],
) -> str:
    items = [
        ("Visual", _visual_family_label(_candidate_family(candidate))),
        ("Shape", _evidence_shape_label(_candidate_shape(candidate))),
        ("Mode", _scope_label(_candidate_scope(candidate))),
        ("Provenance", _first_text(_candidate_value(candidate, "provenance_summary"), _provenance_summary(section))),
        ("Freshness", _first_text(_candidate_value(candidate, "freshness_summary"), _first_text(section.get("freshness_status")))),
    ]
    boxes = []
    for label, value in items:
        if not _has_text(value):
            continue
        boxes.append(
            f"""
            <div class="info-box">
              <strong>{escape(label)}</strong>
              <div>{escape(value)}</div>
            </div>
            """
        )
    return f'<div class="info-grid screen4-deep-analysis-visual-grid">{"".join(boxes)}</div>' if boxes else ""


def _eligible_candidates(
    selection_result: DeepAnalysisVisualizationSelectionResult | Mapping[str, Any] | None,
) -> list[DeepAnalysisVisualizationCandidate | Mapping[str, Any]]:
    if selection_result is None:
        return []
    if isinstance(selection_result, Mapping):
        raw = selection_result.get("eligible_candidates") or selection_result.get("candidates") or []
        return [
            candidate
            for candidate in raw
            if isinstance(candidate, Mapping)
            and candidate.get("status") == VisualizationStatus.ELIGIBLE.value
        ]
    return list(getattr(selection_result, "eligible_candidates", ()) or ())


def _candidate_rows(
    contract: Mapping[str, Any],
    candidate: DeepAnalysisVisualizationCandidate | Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    row_ids = set(_candidate_row_ids(candidate))
    if not row_ids:
        return []
    rows_by_id = {
        _first_text(row.get("row_id"), row.get("id")): row
        for row in (contract.get("evidence_rows") or [])
        if isinstance(row, Mapping)
    }
    rows = [rows_by_id[row_id] for row_id in row_ids if row_id in rows_by_id]
    if len(rows) != len(row_ids):
        return []
    return [row for row in rows if _row_is_renderable(row)]


def _row_is_renderable(row: Mapping[str, Any]) -> bool:
    scope = _first_text(row.get("scope_classification"))
    if scope in BLOCKED_SCOPES:
        return False
    if scope not in {"current_scope", "historical_supporting_context"}:
        return False
    if _normalized_text(row.get("freshness_status")) in STALE_FRESHNESS:
        return False
    if row.get("llm_generated") is True:
        return False
    if "llm" in _normalized_text(row.get("generated_by")) or "browser" in _normalized_text(row.get("generated_by")):
        return False
    for flag in PLACEHOLDER_FLAGS:
        if row.get(flag) is True:
            return False
    if "deterministic_value" not in row:
        return False
    if scope == "current_scope" and not isinstance(row.get("supports_existing_truth_ref"), Mapping):
        return False
    return True


def _section_for_candidate(
    contract: Mapping[str, Any],
    candidate: DeepAnalysisVisualizationCandidate | Mapping[str, Any],
) -> Mapping[str, Any]:
    section_id = _candidate_section_id(candidate)
    for section in contract.get("evidence_sections") or []:
        if isinstance(section, Mapping) and section.get("section_id") == section_id:
            return section
    return {}


def _candidate_scope_allowed(
    candidate: DeepAnalysisVisualizationCandidate | Mapping[str, Any],
    rows: list[Mapping[str, Any]],
) -> bool:
    scope = _candidate_scope(candidate)
    if scope in BLOCKED_SCOPES:
        return False
    if scope not in {"current_scope", "historical_supporting_context"}:
        return False
    return all(row.get("scope_classification") == scope for row in rows)


def _series_points(
    rows: list[Mapping[str, Any]],
    *,
    aligned: bool,
) -> dict[str, list[tuple[str, float]]]:
    series: dict[str, list[tuple[str, float]]] = {}
    for row in rows:
        value = row.get("deterministic_value")
        if isinstance(value, Mapping) and isinstance(value.get("series"), Mapping):
            timestamp = _first_text(value.get("timestamp"), row.get("timestamp"), row.get("time_index"))
            for series_name, series_value in value.get("series", {}).items():
                numeric = _numeric_from_any(series_value)
                if timestamp and numeric is not None:
                    series.setdefault(str(series_name), []).append((timestamp, numeric))
            continue
        timestamp = _time_value(row)
        numeric = _numeric_value(row)
        if timestamp and numeric is not None:
            series_name = _first_text(row.get("series_id"), row.get("series_key"), row.get("target"), "Evidence")
            series.setdefault(series_name if aligned else "Evidence", []).append((timestamp, numeric))
    return {name: points for name, points in series.items() if len(points) >= 2}


def _numeric_samples(row: Mapping[str, Any]) -> list[float]:
    value = row.get("deterministic_value")
    if isinstance(value, Mapping):
        for key in ("samples", "numeric_samples", "sample_values", "values"):
            samples = _numeric_list(value.get(key))
            if samples:
                return samples
        return []
    return _numeric_list(value)


def _numeric_list(value: Any) -> list[float]:
    if not isinstance(value, (list, tuple)):
        return []
    samples: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, Real):
            continue
        samples.append(float(item))
    return samples


def _numeric_value(row: Mapping[str, Any]) -> float | None:
    value = row.get("deterministic_value")
    return _numeric_from_any(value)


def _numeric_from_any(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, Real):
        return float(value)
    if isinstance(value, Mapping):
        for key in ("value", "current_value", "metric_value", "y"):
            numeric = _numeric_from_any(value.get(key))
            if numeric is not None:
                return numeric
    return None


def _threshold_value(row: Mapping[str, Any]) -> float | None:
    for key in ("threshold", "threshold_value"):
        numeric = _numeric_from_any(row.get(key))
        if numeric is not None:
            return numeric
    value = row.get("deterministic_value")
    if isinstance(value, Mapping):
        for key in ("threshold", "threshold_value", "comparator"):
            numeric = _numeric_from_any(value.get(key))
            if numeric is not None:
                return numeric
    ref = row.get("comparator_or_threshold_ref")
    if isinstance(ref, Mapping):
        return _numeric_from_any(ref.get("value") or ref.get("threshold"))
    return None


def _time_value(row: Mapping[str, Any]) -> str:
    return _first_text(row.get("timestamp"), row.get("time_index"), row.get("snapshot"))


def _row_label(row: Mapping[str, Any]) -> str:
    return _first_text(
        row.get("display_label"),
        row.get("evidence_name"),
        row.get("metric_name"),
        row.get("row_id"),
        "Evidence",
    )


def _unit(row: Mapping[str, Any]) -> str:
    return _first_text(row.get("unit"))


def _unit_suffix(unit_text: str) -> str:
    return f" {unit_text}" if unit_text else ""


def _compact_value(value: Any) -> str:
    if isinstance(value, Mapping):
        parts = []
        for key, item in list(value.items())[:5]:
            if _has_text(item) or isinstance(item, Real):
                parts.append(f"{key}: {_compact_value(item)}")
        return "; ".join(parts)
    if isinstance(value, (list, tuple)):
        if all(isinstance(item, Real) and not isinstance(item, bool) for item in value):
            return f"{len(value)} numeric samples"
        return f"{len(value)} values"
    return _first_text(value)


def _provenance_summary(section: Mapping[str, Any]) -> str:
    provenance = section.get("provenance")
    if not isinstance(provenance, Mapping):
        return ""
    return _first_text(
        provenance.get("source_contract_ref"),
        provenance.get("source_path"),
        provenance.get("deterministic_engine_version"),
    )


def _candidate_value(
    candidate: DeepAnalysisVisualizationCandidate | Mapping[str, Any],
    field: str,
) -> Any:
    if isinstance(candidate, Mapping):
        return candidate.get(field)
    return getattr(candidate, field, None)


def _candidate_status(candidate: DeepAnalysisVisualizationCandidate | Mapping[str, Any]) -> str:
    value = _candidate_value(candidate, "status")
    return str(getattr(value, "value", value) or "")


def _candidate_family(candidate: DeepAnalysisVisualizationCandidate | Mapping[str, Any]) -> str:
    value = _candidate_value(candidate, "visualization_family")
    return str(getattr(value, "value", value) or "")


def _candidate_shape(candidate: DeepAnalysisVisualizationCandidate | Mapping[str, Any]) -> str:
    value = _candidate_value(candidate, "evidence_shape")
    return str(getattr(value, "value", value) or "")


def _candidate_title(candidate: DeepAnalysisVisualizationCandidate | Mapping[str, Any]) -> str:
    return _first_text(_candidate_value(candidate, "suggested_title"), "Deep Analysis Visual Evidence")


def _candidate_scope(candidate: DeepAnalysisVisualizationCandidate | Mapping[str, Any]) -> str:
    return _first_text(_candidate_value(candidate, "scope_classification"))


def _candidate_id(candidate: DeepAnalysisVisualizationCandidate | Mapping[str, Any]) -> str:
    return _first_text(_candidate_value(candidate, "candidate_id"), "deep-analysis-visual")


def _candidate_section_id(candidate: DeepAnalysisVisualizationCandidate | Mapping[str, Any]) -> str:
    return _first_text(_candidate_value(candidate, "section_id"))


def _candidate_row_ids(candidate: DeepAnalysisVisualizationCandidate | Mapping[str, Any]) -> tuple[str, ...]:
    values = _candidate_value(candidate, "row_ids")
    if not isinstance(values, (list, tuple)):
        return ()
    return tuple(str(value) for value in values if _has_text(value))


def _candidate_supporting(candidate: DeepAnalysisVisualizationCandidate | Mapping[str, Any]) -> bool:
    return bool(_candidate_value(candidate, "is_supporting_context"))


def _visual_family_label(value: Any) -> str:
    labels = {
        "contribution": "Contribution",
        "ranked_contribution": "Ranked Contribution",
        "time_series": "Time Series",
        "aligned_overlay": "Aligned Overlay",
        "distribution_evidence": "Distribution Evidence",
        "anomaly_timeline": "Anomaly Timeline",
        "pressure_band": "Pressure Band",
        "topology_fact_map": "Topology Fact Map",
        "similarity_neighborhood": "Similarity Neighborhood",
        "fleet_population": "Fleet Population",
        "table_only": "Table Only",
    }
    text = _first_text(value)
    return labels.get(text, text.replace("_", " ").title())


def _evidence_shape_label(value: Any) -> str:
    labels = {
        "categorical_contribution": "Categorical Contribution",
        "ranked_rows": "Ranked Rows",
        "time_indexed_series": "Time-Indexed Series",
        "aligned_multi_series": "Aligned Multi-Series",
        "numeric_samples": "Numeric Samples",
        "interval_events": "Interval Events",
        "scalar_threshold": "Scalar Threshold",
        "topology_facts": "Topology Facts",
        "identity_rows": "Identity Rows",
        "score_vector": "Score Vector",
        "similarity_cases": "Similarity Cases",
        "population_samples": "Population Samples",
    }
    text = _first_text(value)
    return labels.get(text, text.replace("_", " ").title())


def _scope_label(value: Any) -> str:
    labels = {
        "current_scope": "Current Diagnostic Evidence",
        "historical_supporting_context": "Historical Supporting Context",
        "comparative_output": "Comparative Review Only",
        "prepared_only": "Prepared Context Only",
        "cache_only": "Cache Continuity Only",
        "fleet_population": "Fleet / Population",
        "llm_explanation_only": "Explanation Only",
        "unknown_or_mixed": "Unknown or Mixed",
    }
    text = _first_text(value)
    return labels.get(text, text.replace("_", " ").title())


def _format_number(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}".rstrip("0").rstrip(".")
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _first_text(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _has_text(value: Any) -> bool:
    return _first_text(value) != ""


def _normalized_text(value: Any) -> str:
    return _first_text(value).lower().replace("-", "_").replace(" ", "_")


def _slug(value: Any) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", _first_text(value).lower()).strip("-")
    return slug or "value"
