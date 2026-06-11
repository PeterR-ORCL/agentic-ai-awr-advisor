"""Screen 4 review renderer adapter.

This renderer consumes Screen4ReviewViewModel only. It keeps Historical Review,
Comparative Review, and Deep Analysis separated and does not compute evidence
or infer visualizations.
"""

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
from src.reporting.dashboard.view_models.screen4_review_view_model import (
    Screen4ReviewModeViewModel,
    Screen4ReviewViewModel,
)


def render_screen4_review(view_model: Screen4ReviewViewModel) -> str:
    """Render deterministic Screen 4 review-mode HTML fragments."""

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
    body = [
        render_summary(mode.availability_status, mode.summary),
        render_rows(f"{title} evidence", mode.evidence_rows),
        render_named_collections(
            (
                (f"{title} metric summaries", mode.metric_summaries),
                (f"{title} trend summaries", mode.trend_summaries),
                (f"{title} anomaly summaries", mode.anomaly_summaries),
                (f"{title} similarity context", mode.similarity_context),
                (f"{title} confidence basis", mode.confidence_basis),
            )
        ),
        render_state_lists(
            missing_evidence=mode.missing_evidence,
            unavailable_evidence=mode.unavailable_evidence,
            stale_evidence=mode.stale_evidence,
        ),
        render_visualizations(mode.allowed_visualizations),
        render_mapping(f"{title} provenance", mode.provenance),
        render_llm_eligibility(mode.llm_explanation_eligibility),
    ]
    return render_group(title, body, f"screen4-{mode.mode_id}")
