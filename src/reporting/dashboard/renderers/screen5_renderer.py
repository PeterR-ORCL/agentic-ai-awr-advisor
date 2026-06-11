"""Screen 5 recommendation/action renderer adapter."""

from __future__ import annotations

from src.reporting.dashboard.renderers.common import (
    render_confidence_cards,
    render_group,
    render_identity,
    render_llm_eligibility,
    render_mapping,
    render_root,
    render_rows,
    render_state_lists,
    render_status_panel,
    render_summary,
    render_unavailable_card,
    render_visualizations,
)
from src.reporting.dashboard.view_models.screen5_action_view_model import (
    Screen5ActionViewModel,
)


def render_screen5_action(view_model: Screen5ActionViewModel) -> str:
    """Render product Screen 5 recommendation/action HTML fragment."""

    body = [
        render_identity(view_model.selected_flow_id, view_model.evidence_pack_id),
        render_summary(view_model.availability_status, view_model.summary),
        _action_status(view_model),
        _action_cards(view_model),
        render_confidence_cards("Action confidence", view_model.confidence_basis),
        render_state_lists(
            missing_evidence=view_model.missing_evidence,
            unavailable_evidence=view_model.unavailable_evidence,
            stale_evidence=view_model.stale_evidence,
        ),
        render_visualizations(
            view_model.allowed_visualizations,
            rows=view_model.action_rows,
            title="Action visual evidence",
        ),
        render_mapping("Evidence provenance", view_model.evidence_provenance),
        render_mapping("Pack provenance", view_model.provenance),
        render_llm_eligibility(view_model.llm_explanation_eligibility),
    ]
    return render_root(
        view_model.screen_id,
        "Recommendation / Action",
        (render_group("Action Evidence", body, "screen5-action"),),
    )


def _action_status(view_model: Screen5ActionViewModel) -> str:
    facts = {"availability": view_model.availability_status}
    for row in view_model.action_rows:
        values = row.get("values") if isinstance(row.get("values"), dict) else row
        if not isinstance(values, dict):
            continue
        for key in ("recommendation", "action", "risk", "impact", "confidence", "outcome"):
            if key in values and key not in facts:
                facts[key] = values[key]
    return render_status_panel("Recommendation/action posture", facts)


def _action_cards(view_model: Screen5ActionViewModel) -> str:
    if not view_model.action_rows:
        return render_unavailable_card(
            "Recommendation/action evidence missing",
            "No deterministic recommendation/action evidence is available for this selection.",
        )
    return render_rows("Recommendation/action cards", view_model.action_rows)
