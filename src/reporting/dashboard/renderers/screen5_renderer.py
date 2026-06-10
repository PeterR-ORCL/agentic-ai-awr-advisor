"""Screen 5 recommendation/action renderer adapter."""

from __future__ import annotations

from src.reporting.dashboard.renderers.common import (
    render_group,
    render_identity,
    render_llm_eligibility,
    render_mapping,
    render_named_collections,
    render_root,
    render_rows,
    render_state_lists,
    render_summary,
    render_visualizations,
)
from src.reporting.dashboard.view_models.screen5_action_view_model import (
    Screen5ActionViewModel,
)


def render_screen5_action(view_model: Screen5ActionViewModel) -> str:
    """Render deterministic Screen 5 recommendation/action HTML fragment."""

    body = [
        render_identity(view_model.selected_flow_id, view_model.evidence_pack_id),
        render_summary(view_model.availability_status, view_model.summary),
        render_rows("Recommendation/action evidence", view_model.action_rows),
        render_named_collections(
            (
                ("Recommendation fields", view_model.recommendation_fields),
                ("Risk fields", view_model.risk_fields),
                ("Impact fields", view_model.impact_fields),
                ("Confidence basis", view_model.confidence_basis),
            )
        ),
        render_state_lists(
            missing_evidence=view_model.missing_evidence,
            unavailable_evidence=view_model.unavailable_evidence,
            stale_evidence=view_model.stale_evidence,
        ),
        render_visualizations(view_model.allowed_visualizations),
        render_mapping("Evidence provenance", view_model.evidence_provenance),
        render_mapping("Pack provenance", view_model.provenance),
        render_llm_eligibility(view_model.llm_explanation_eligibility),
    ]
    return render_root(
        view_model.screen_id,
        "Recommendation / Action",
        (render_group("Action Evidence", body, "screen5-action"),),
    )
