"""Screen 3 Diagnostic Snapshot renderer adapter.

This renderer consumes Screen3DiagnosticViewModel only. It does not compute
evidence, render comparisons, read browser state, call LLMs, or integrate with
the dashboard shell.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.reporting.dashboard.renderers.common import (
    join_fragments,
    render_anomaly_cards,
    render_confidence_cards,
    render_group,
    render_identity,
    render_llm_eligibility,
    render_mapping,
    render_metric_cards,
    render_root,
    render_rows,
    render_state_lists,
    render_status_panel,
    render_summary,
    render_trend_cards,
    render_unavailable_card,
    render_visualizations,
)
from src.reporting.dashboard.view_models.screen3_diagnostic_view_model import (
    Screen3DiagnosticViewModel,
)


def render_screen3_diagnostic(view_model: Screen3DiagnosticViewModel) -> str:
    """Render a product Diagnostic Snapshot HTML fragment."""

    body = [
        render_identity(view_model.selected_flow_id, view_model.evidence_pack_id),
        _selected_report_context(view_model),
        render_summary(view_model.availability_status, view_model.summary),
        _diagnostic_posture(view_model),
        render_rows("Top diagnostic drivers", _non_historical_rows(view_model.evidence_rows)),
        render_metric_cards("Metric cards", view_model.metric_summaries),
        render_anomaly_cards("Anomaly / event cards", view_model.anomaly_summaries),
        _healthcheck_cards(view_model),
        render_trend_cards("Diagnostic trend cards", view_model.trend_summaries),
        render_visualizations((), trends=view_model.trend_summaries, title="Diagnostic time-series evidence"),
        _supporting_context(view_model),
        render_confidence_cards("Confidence explanation", view_model.confidence_basis),
        render_state_lists(
            missing_evidence=view_model.missing_evidence,
            unavailable_evidence=view_model.unavailable_evidence,
            stale_evidence=view_model.stale_evidence,
        ),
        render_mapping("Evidence provenance", view_model.evidence_provenance),
        render_mapping("Pack provenance", view_model.provenance),
        render_llm_eligibility(view_model.llm_explanation_eligibility),
    ]
    return render_root(
        view_model.screen_id,
        "Diagnostic Snapshot",
        (render_group("Diagnostic", body, "screen3-diagnostic"),),
    )


def _selected_report_context(view_model: Screen3DiagnosticViewModel) -> str:
    facts: dict[str, Any] = {
        "selected_flow": view_model.selected_flow_id,
        "evidence_pack": view_model.evidence_pack_id,
    }
    for row in view_model.evidence_rows:
        values = _values(row)
        for key in (
            "selected_report",
            "selected_awr",
            "report_id",
            "awr_id",
            "database_id",
            "db_name",
            "snapshot_window",
            "snapshot_begin",
            "snapshot_end",
            "interval",
        ):
            if key in values and key not in facts:
                facts[key] = values[key]
    return render_status_panel("Selected report context", facts)


def _diagnostic_posture(view_model: Screen3DiagnosticViewModel) -> str:
    facts: dict[str, Any] = {
        "availability": view_model.availability_status,
    }
    for row in view_model.evidence_rows:
        values = _values(row)
        for key in ("primary_domain", "risk_level", "posture", "confidence"):
            if key in values and key not in facts:
                facts[key] = values[key]
    for item in view_model.confidence_basis:
        if item.get("confidence") and "confidence" not in facts:
            facts["confidence"] = item.get("confidence")
    if not facts:
        return ""
    return render_status_panel("Diagnostic posture", facts)


def _healthcheck_cards(view_model: Screen3DiagnosticViewModel) -> str:
    healthcheck_rows = [
        row
        for row in view_model.evidence_rows
        if _contains_token(row, ("healthcheck", "health_check", "check_status"))
    ]
    healthcheck_metrics = [
        metric
        for metric in view_model.metric_summaries
        if _contains_token(metric, ("healthcheck", "health_check", "check_status"))
    ]
    return join_fragments(
        (
            render_rows("Healthcheck cards", healthcheck_rows),
            render_metric_cards("Healthcheck metrics", healthcheck_metrics),
        )
    )


def _supporting_context(view_model: Screen3DiagnosticViewModel) -> str:
    context_rows = [
        row
        for row in view_model.evidence_rows
        if _contains_token(row, ("historical_context", "supporting_context"))
    ]
    if not context_rows:
        return render_unavailable_card(
            "Supporting historical context unavailable",
            "No deterministic supporting historical context is available for this diagnostic snapshot.",
        )
    return render_status_panel(
        "Supporting historical context",
        {
            "role": "supporting evidence only",
            "context_items": len(context_rows),
            "selected_truth": "selected report diagnostic evidence remains primary",
        },
    )


def _non_historical_rows(rows: Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        row
        for row in rows
        if not _contains_token(row, ("historical_context", "supporting_context"))
    )


def _values(row: Mapping[str, Any]) -> Mapping[str, Any]:
    values = row.get("values")
    if isinstance(values, Mapping):
        return values
    return row


def _contains_token(item: Mapping[str, Any], tokens: Sequence[str]) -> bool:
    haystack = " ".join(str(value).lower() for value in _flatten_values(item))
    return any(token in haystack for token in tokens)


def _flatten_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Mapping):
        flattened: list[Any] = []
        for key, child in value.items():
            flattened.append(key)
            flattened.extend(_flatten_values(child))
        return tuple(flattened)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        flattened = []
        for child in value:
            flattened.extend(_flatten_values(child))
        return tuple(flattened)
    return (value,)
