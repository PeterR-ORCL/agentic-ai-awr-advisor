"""Screen 6 learning/governance renderer adapter."""

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
from src.reporting.dashboard.view_models.screen6_learning_view_model import (
    Screen6LearningViewModel,
)


def render_screen6_learning(view_model: Screen6LearningViewModel) -> str:
    """Render product Screen 6 learning/governance HTML fragment."""

    body = [
        render_identity(view_model.selected_flow_id, view_model.evidence_pack_id),
        render_summary(view_model.availability_status, view_model.summary),
        _governance_status(view_model),
        _governance_cards(view_model),
        render_confidence_cards("Governance confidence", view_model.confidence_basis),
        render_state_lists(
            missing_evidence=view_model.missing_evidence,
            unavailable_evidence=view_model.unavailable_evidence,
            stale_evidence=view_model.stale_evidence,
        ),
        render_visualizations(
            view_model.allowed_visualizations,
            rows=view_model.governance_rows,
            title="Governance visual evidence",
        ),
        render_mapping("Evidence provenance", view_model.evidence_provenance),
        render_mapping("Pack provenance", view_model.provenance),
        render_llm_eligibility(view_model.llm_explanation_eligibility),
    ]
    return render_root(
        view_model.screen_id,
        "Learning / Governance",
        (render_group("Governance Evidence", body, "screen6-learning"),),
    )


def _governance_status(view_model: Screen6LearningViewModel) -> str:
    facts = {"availability": view_model.availability_status}
    for row in view_model.governance_rows:
        values = row.get("values") if isinstance(row.get("values"), dict) else row
        if not isinstance(values, dict):
            continue
        for key in (
            "governance_status",
            "memory_policy",
            "approval_boundary",
            "activation_boundary",
            "materialization_boundary",
            "state",
            "enabled",
            "success",
        ):
            if key in values and key not in facts:
                facts[key] = values[key]
    return render_status_panel("Learning/governance state", facts)


def _governance_cards(view_model: Screen6LearningViewModel) -> str:
    if not view_model.governance_rows:
        return render_unavailable_card(
            "Learning/governance evidence missing",
            "No deterministic governed learning evidence is available for this selection.",
        )
    return render_rows("Learning/governance cards", view_model.governance_rows)
