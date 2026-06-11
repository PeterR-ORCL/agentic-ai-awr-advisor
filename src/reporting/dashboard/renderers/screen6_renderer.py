"""Screen 6 learning/governance renderer adapter."""

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
from src.reporting.dashboard.view_models.screen6_learning_view_model import (
    Screen6LearningViewModel,
)


def render_screen6_learning(view_model: Screen6LearningViewModel) -> str:
    """Render deterministic Screen 6 learning/governance HTML fragment."""

    body = [
        render_identity(view_model.selected_flow_id, view_model.evidence_pack_id),
        render_summary(view_model.availability_status, view_model.summary),
        render_rows("Learning/governance evidence", view_model.governance_rows),
        render_named_collections(
            (
                ("Learning candidates", view_model.learning_candidates),
                ("Governance status", view_model.governance_status),
                ("Memory policy", view_model.memory_policy),
                ("Approval boundaries", view_model.approval_boundaries),
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
        "Learning / Governance",
        (render_group("Governance Evidence", body, "screen6-learning"),),
    )
