"""Screen 4 review renderer adapter.

This renderer consumes Screen4ReviewViewModel only. It keeps Historical Review,
Comparative Review, and Deep Analysis separated and does not compute evidence
or infer visualizations.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.reporting.dashboard.renderers.common import (
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
from src.reporting.dashboard.view_models.screen4_review_view_model import (
    Screen4ReviewModeViewModel,
    Screen4ReviewViewModel,
)


def render_screen4_review(view_model: Screen4ReviewViewModel) -> str:
    """Render product Screen 4 review-mode HTML fragments."""

    return render_root(
        view_model.screen_id,
        "Review",
        (
            render_identity(view_model.selected_flow_id, view_model.evidence_pack_id),
            render_review_mode("Historical Review", view_model.historical_review),
            render_review_mode("Comparative Review", view_model.comparative_review),
            render_review_mode("Deep Analysis", view_model.deep_analysis),
            render_mapping("Pack provenance", view_model.provenance),
        ),
    )


def render_review_mode(title: str, mode: Screen4ReviewModeViewModel) -> str:
    if mode.availability_status != "present":
        return _unavailable_review_mode(title, mode)

    product_rows = _product_rows(mode)
    body = [
        render_summary(mode.availability_status, mode.summary),
        _mode_context(title, mode),
        render_rows(f"{title} evidence cards", product_rows),
        render_metric_cards(f"{title} metric cards", mode.metric_summaries),
        render_trend_cards(f"{title} trend cards", mode.trend_summaries),
        render_anomaly_cards(f"{title} anomaly cards", mode.anomaly_summaries),
        _action_posture(title, product_rows),
        render_visualizations(
            mode.allowed_visualizations,
            trends=mode.trend_summaries,
            rows=product_rows,
            title=f"{title} visual evidence",
        ),
        render_confidence_cards(f"{title} confidence", mode.confidence_basis),
        render_state_lists(
            missing_evidence=mode.missing_evidence,
            unavailable_evidence=mode.unavailable_evidence,
            stale_evidence=mode.stale_evidence,
        ),
        render_mapping(f"{title} provenance", mode.provenance),
        render_llm_eligibility(mode.llm_explanation_eligibility),
    ]
    return render_group(title, body, f"screen4-{mode.mode_id}")


def _unavailable_review_mode(title: str, mode: Screen4ReviewModeViewModel) -> str:
    if mode.mode_id == "comparative_review":
        message = "Target A and Target B deterministic selections are required before comparative review can render."
    elif mode.mode_id == "deep_analysis":
        message = "Deep-analysis deterministic input is required before deep analysis can render."
    else:
        message = "Historical deterministic evidence is required before historical review can render."
    body = [
        render_summary(mode.availability_status, mode.summary),
        render_unavailable_card(f"{title} unavailable", message),
        render_state_lists(
            missing_evidence=mode.missing_evidence,
            unavailable_evidence=mode.unavailable_evidence,
            stale_evidence=mode.stale_evidence,
        ),
        render_mapping(f"{title} provenance", mode.provenance),
        render_llm_eligibility(mode.llm_explanation_eligibility),
    ]
    return render_group(title, body, f"screen4-{mode.mode_id}")


def _mode_context(title: str, mode: Screen4ReviewModeViewModel) -> str:
    return render_status_panel(
        f"{title} context",
        {
            "domain": mode.domain,
            "availability": mode.availability_status,
            "evidence_rows": len(mode.evidence_rows),
            "trend_count": len(mode.trend_summaries),
            "anomaly_count": len(mode.anomaly_summaries),
        },
    )


def _action_posture(title: str, rows: Sequence[Mapping[str, Any]]) -> str:
    facts = {}
    for row in rows:
        values = row.get("values") if isinstance(row.get("values"), dict) else row
        if not isinstance(values, dict):
            continue
        for key in ("posture", "risk_level", "recommendation", "action", "impact"):
            if key in values and key not in facts:
                facts[key] = values[key]
    return render_status_panel(f"{title} action posture", facts)


def _product_rows(mode: Screen4ReviewModeViewModel) -> tuple[Mapping[str, Any], ...]:
    rows = []
    for row in mode.evidence_rows:
        if _contains_legacy_scope_contamination(row):
            continue
        rows.append(row)
    return tuple(rows)


def _contains_legacy_scope_contamination(item: Mapping[str, Any]) -> bool:
    text = " ".join(str(value).lower() for value in _flatten(item))
    return any(
        phrase in text
        for phrase in (
            "selected-scope explanation",
            "multi-snapshot summary",
            "24 snapshots were analyzed",
            "chronological order",
            "current window 24 / 106h",
            "historical artifact context",
        )
    )


def _flatten(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Mapping):
        flattened: list[Any] = []
        for key, child in value.items():
            flattened.append(key)
            flattened.extend(_flatten(child))
        return tuple(flattened)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        flattened = []
        for child in value:
            flattened.extend(_flatten(child))
        return tuple(flattened)
    return (value,)
