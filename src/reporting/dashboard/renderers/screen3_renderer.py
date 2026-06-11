"""Screen 3 Diagnostic Snapshot renderer adapter.

This renderer consumes Screen3DiagnosticViewModel only. It does not compute
evidence, render comparisons, read browser state, call LLMs, or integrate with
the dashboard shell.
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
)
from src.reporting.dashboard.view_models.screen3_diagnostic_view_model import (
    Screen3DiagnosticViewModel,
)


def render_screen3_diagnostic(view_model: Screen3DiagnosticViewModel) -> str:
    """Render a deterministic Screen 3 Diagnostic Snapshot HTML fragment."""

    body = [
        render_identity(view_model.selected_flow_id, view_model.evidence_pack_id),
        render_summary(view_model.availability_status, view_model.summary),
        render_rows("Diagnostic evidence", view_model.evidence_rows),
        render_named_collections(
            (
                ("Metric summaries", view_model.metric_summaries),
                ("Trend summaries", view_model.trend_summaries),
                ("Anomaly summaries", view_model.anomaly_summaries),
                ("Similarity context", view_model.similarity_context),
                ("Confidence basis", view_model.confidence_basis),
            )
        ),
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
