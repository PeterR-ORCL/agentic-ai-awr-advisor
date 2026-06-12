import html as html_lib
import os
import re
from pathlib import Path
from types import SimpleNamespace

import pytest


_RUN_7RESET_ACCEPTANCE = os.environ.get("AWR_RUN_7RESET_ACCEPTANCE") == "1"

pytestmark = pytest.mark.skipif(
    not _RUN_7RESET_ACCEPTANCE,
    reason=(
        "7RESET product acceptance red gate is intentionally opt-in. "
        "Run with AWR_RUN_7RESET_ACCEPTANCE=1."
    ),
)

from src.reporting.dashboard.renderers.screen3_renderer import render_screen3_diagnostic
from src.reporting.dashboard.renderers.screen4_renderer import render_screen4_review
from src.reporting.dashboard.renderers.screen5_renderer import render_screen5_action
from src.reporting.dashboard.renderers.screen6_renderer import render_screen6_learning


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return existing_file(relative_path).read_text(encoding="utf-8")


def existing_file(relative_path: str) -> Path:
    path = project_root() / relative_path
    assert path.exists(), f"Required file is missing for 7RESET red gate: {relative_path}"
    return path


def strip_html_scripts_and_styles(html: str) -> str:
    stripped = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    return re.sub(r"<style\b[^>]*>.*?</style>", " ", stripped, flags=re.IGNORECASE | re.DOTALL)


def product_visible_text(html: str) -> str:
    body = strip_html_scripts_and_styles(html)
    body = re.sub(r"<[^>]+>", " ", body)
    body = html_lib.unescape(body)
    return re.sub(r"\s+", " ", body).strip()


def assert_not_contains_any(text: str, forbidden_tokens: tuple[str, ...], rule: str) -> None:
    found = [token for token in forbidden_tokens if token in text]
    assert not found, f"{rule} Violating visible token(s): {found}"


def source_contains(relative_path: str, token: str) -> bool:
    return token in read_text(relative_path)


def artifact_text_if_present(relative_path: str) -> str:
    path = project_root() / relative_path
    if not path.exists():
        pytest.skip(f"Artifact symptom check skipped; file is absent: {relative_path}")
    return product_visible_text(path.read_text(encoding="utf-8"))


def screen3_model(**overrides):
    values = {
        "screen_id": "screen3_diagnostic_snapshot",
        "selected_flow_id": "selected-flow-internal-123",
        "evidence_pack_id": "evidence-pack-internal-456",
        "availability_status": "present",
        "summary": "Selected single-AWR Diagnostic Snapshot",
        "evidence_rows": (
            {
                "row_id": "diagnostic-row-1",
                "metric": "db_cpu",
                "values": {"diagnosis": "CPU pressure", "debug": ["raw", "list"]},
            },
        ),
        "metric_summaries": (),
        "trend_summaries": (),
        "anomaly_summaries": (),
        "similarity_context": (),
        "confidence_basis": (),
        "missing_evidence": (),
        "unavailable_evidence": (),
        "stale_evidence": (),
        "provenance": {"source_system": "deterministic_builder"},
        "evidence_provenance": {"source_system": "diagnostic_engine"},
        "llm_explanation_eligibility": (),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def screen4_mode(mode_id: str, **overrides):
    values = {
        "mode_id": mode_id,
        "domain": mode_id,
        "availability_status": "present",
        "summary": f"{mode_id} evidence",
        "evidence_rows": ({"row_id": f"{mode_id}-row", "metric": mode_id, "value": 1},),
        "metric_summaries": (),
        "trend_summaries": (),
        "anomaly_summaries": (),
        "similarity_context": (),
        "confidence_basis": (),
        "missing_evidence": (),
        "unavailable_evidence": (),
        "stale_evidence": (),
        "allowed_visualizations": (),
        "llm_explanation_eligibility": (),
        "provenance": {"source_system": "deterministic_builder"},
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def screen4_model(**overrides):
    values = {
        "screen_id": "screen4_evidence_review",
        "selected_flow_id": "screen4-flow-internal",
        "evidence_pack_id": "screen4-pack-internal",
        "historical_review": screen4_mode("historical_review"),
        "comparative_review": screen4_mode("comparative_review"),
        "deep_analysis": screen4_mode("deep_analysis"),
        "provenance": {"source_system": "deterministic_builder"},
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def screen5_model(**overrides):
    values = {
        "screen_id": "screen5_recommendation_action",
        "selected_flow_id": "screen5-flow-internal",
        "evidence_pack_id": "screen5-pack-internal",
        "availability_status": "unavailable",
        "summary": "Recommendation unavailable",
        "action_rows": (),
        "recommendation_fields": (),
        "risk_fields": (),
        "impact_fields": (),
        "confidence_basis": (),
        "missing_evidence": (),
        "unavailable_evidence": (),
        "stale_evidence": (),
        "allowed_visualizations": (),
        "llm_explanation_eligibility": (),
        "provenance": {"source_system": "deterministic_builder"},
        "evidence_provenance": {"source_system": "recommendation_engine"},
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def screen6_model(**overrides):
    values = {
        "screen_id": "screen6_learning_governance",
        "selected_flow_id": "screen6-flow-internal",
        "evidence_pack_id": "screen6-pack-internal",
        "availability_status": "unavailable",
        "summary": "Governance unavailable",
        "governance_rows": (),
        "learning_candidates": (),
        "governance_status": (),
        "memory_policy": (),
        "approval_boundaries": (),
        "confidence_basis": (),
        "missing_evidence": (),
        "unavailable_evidence": (),
        "stale_evidence": (),
        "allowed_visualizations": (),
        "llm_explanation_eligibility": (),
        "provenance": {"source_system": "deterministic_builder"},
        "evidence_provenance": {"source_system": "learning_governance"},
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_reset_control_artifact_preserves_required_language():
    text = read_text("docs/architecture/7reset_dashboard_product_recut.md")

    for phrase in (
        "Phase 7 is not complete",
        "Generated HTML is output only",
        "Browser state",
        "localStorage",
        "Deterministic engines decide",
        "LLM explains only already-decided deterministic truth",
        "Do not continue the failed renderer patch chain",
        "Canonical SelectedReviewScopeContract shape",
        "Canonical EvidencePackContract shape",
    ):
        assert phrase in text, f"7RESET control artifact must retain phrase: {phrase}"


def test_common_renderer_does_not_emit_pre_blocks_for_product_items():
    source = read_text("src/reporting/dashboard/renderers/common.py")

    assert "<pre>" not in source, (
        "Product renderer must not expose raw product panel items through visible <pre> blocks."
    )


def test_common_renderer_does_not_format_raw_mappings_as_product_ui():
    source = read_text("src/reporting/dashboard/renderers/common.py")

    assert "def _format_value" not in source and "isinstance(value, Mapping)" not in source, (
        "Product renderer must not use generic dict/list formatting as user-facing evidence UI."
    )


def test_identity_renderer_does_not_surface_internal_ids_in_product_ui():
    source = read_text("src/reporting/dashboard/renderers/common.py")

    assert_not_contains_any(
        source,
        ("selected_flow_id", "evidence_pack_id", "Selected flow", "Evidence pack"),
        "Primary product UI must not expose internal selected-flow or evidence-pack identifiers.",
    )


def test_allowed_visualizations_is_not_rendered_as_product_content():
    source = (
        read_text("src/reporting/dashboard/renderers/common.py")
        + read_text("src/reporting/dashboard/renderers/screen4_renderer.py")
    )

    assert_not_contains_any(
        source,
        ("Allowed visualizations", "allowed-visualizations", "render_visualizations(mode.allowed_visualizations)"),
        "`allowed_visualizations` is renderer metadata and must not become user-facing product evidence.",
    )


def test_screen3_renderer_output_does_not_show_raw_pre_or_debug_structures():
    html = render_screen3_diagnostic(screen3_model())
    visible = product_visible_text(html)

    assert "<pre>" not in html, "Screen 3 product UI must not render raw evidence through <pre> blocks."
    assert_not_contains_any(
        visible,
        ("{ debug:", "{ row_id:", "[raw, list]"),
        "Screen 3 product UI must not expose flattened raw dict/list/debug structures.",
    )


def test_screen3_renderer_does_not_surface_internal_ids_in_primary_ui():
    html = render_screen3_diagnostic(screen3_model())
    visible = product_visible_text(html)

    assert_not_contains_any(
        visible,
        ("selected-flow-internal-123", "evidence-pack-internal-456"),
        "Screen 3 first-fold/product UI must hide internal selected_flow_id and evidence_pack_id.",
    )


def test_screen3_renderer_single_awr_not_polluted_by_multi_snapshot_summary():
    html = render_screen3_diagnostic(
        screen3_model(
            trend_summaries=(
                {
                    "title": "Multi-Snapshot Summary",
                    "summary": "24 snapshots were analyzed in chronological order.",
                },
            )
        )
    )
    visible = product_visible_text(html)

    assert_not_contains_any(
        visible,
        ("Multi-Snapshot Summary", "24 snapshots were analyzed"),
        "Screen 3 selected single-AWR diagnosis must not present historical/multi-snapshot context as truth.",
    )


def test_screen3_artifact_symptom_single_awr_is_not_polluted_by_multi_snapshot_summary():
    """Symptom check only: generated HTML is output, not source truth or acceptance proof."""

    visible = artifact_text_if_present("awr_dashboard/screen_3_analysis.html")

    assert_not_contains_any(
        visible,
        ("Multi-Snapshot Summary", "24 snapshots were analyzed", "Historical Artifact Context"),
        "Screen 3 artifact symptom shows historical/multi-snapshot context in selected diagnostic UI.",
    )


def test_screen4_renderer_modes_are_not_generic_pre_lists():
    html = render_screen4_review(screen4_model())
    visible = product_visible_text(html)

    assert "<pre>" not in html, "Screen 4 modes must not collapse into generic <pre> list rendering."
    assert_not_contains_any(
        visible,
        ("{ metric:", "{ row_id:"),
        "Screen 4 Evidence Review must use typed mode panels, not flattened raw mappings.",
    )


def test_screen4_renderer_does_not_present_trend_ids_and_point_counts_as_evidence():
    historical = screen4_mode(
        "historical_review",
        trend_summaries=(
            {"Trend": "dg_transport_lag_trend", "Point Count": 3},
            {"Trend": "exa_cell_io_trend", "Point Count": 0},
            {"Trend": "gc_wait_trend", "Point Count": 3},
        ),
    )
    html = render_screen4_review(screen4_model(historical_review=historical))
    visible = product_visible_text(html)

    assert_not_contains_any(
        visible,
        (
            "dg_transport_lag_trend",
            "exa_cell_io_trend",
            "gc_wait_trend",
            "Point Count: 0",
            "Point Count: 3",
        ),
        "Screen 4 must not present raw trend IDs and point counts as evidence review.",
    )


def test_screen4_renderer_does_not_render_unavailable_comparative_or_deep_evidence():
    comparative = screen4_mode(
        "comparative_review",
        availability_status="unavailable",
        evidence_rows=({"row_id": "fake-comparison", "value": "fabricated Target A/B delta"},),
    )
    deep = screen4_mode(
        "deep_analysis",
        availability_status="unavailable",
        evidence_rows=({"row_id": "fake-deep", "value": "Deep Analysis fabricated from page state"},),
    )
    html = render_screen4_review(screen4_model(comparative_review=comparative, deep_analysis=deep))
    visible = product_visible_text(html)

    assert_not_contains_any(
        visible,
        ("fabricated Target A/B delta", "Deep Analysis fabricated from page state"),
        "Unavailable Screen 4 modes must not render comparison or Deep Analysis evidence rows.",
    )


def test_screen4_artifact_symptom_allowed_visualizations_not_user_evidence():
    """Symptom check only: generated HTML is output, not source truth or acceptance proof."""

    visible = artifact_text_if_present("awr_dashboard/screen_4_historical_review.html")

    assert "Allowed Visualizations" not in visible, (
        "Screen 4 artifact symptom shows `allowed_visualizations` metadata as user-facing evidence."
    )


def test_visual_contract_gate_allowed_visualizations_is_not_chart_contract():
    source = read_text("src/reporting/dashboard/renderers/screen4_renderer.py")

    assert "render_visualizations" not in source, (
        "`allowed_visualizations` must not be treated as a chart or evidence visual contract."
    )


def test_visual_contract_gate_missing_data_requires_unavailable_state():
    source = (
        read_text("src/reporting/dashboard/renderers/common.py")
        + read_text("src/reporting/dashboard/renderers/screen4_renderer.py")
    )

    assert "render_visualizations" not in source or "UnavailableVisualState" in source, (
        "Product visuals with missing data must render an unavailable state instead of silently omitting evidence."
    )


def test_source_truth_cache_does_not_promote_runtime_or_target_readiness():
    source = read_text("src/reporting/html_dashboard.py")

    assert_not_contains_any(
        source,
        (
            "status: cache.status || 'accepted'",
            "validation_status: cache.validation_status || 'valid'",
            "state.screen3LiveServiceStatus = screen3CachedWorkflowStatusLabel(cache.service_status || 'Available')",
            "cachedState.sourceSelectionActivated = 'true'",
        ),
        "Browser cache/localStorage continuity must not create runtime readiness or Target A/B readiness.",
    )


def test_source_truth_generated_artifact_fragments_are_not_acceptance_gate():
    source = read_text("src/reporting/html_dashboard.py")

    assert_not_contains_any(
        source,
        (
            'content_html=contract_screen_fragments.get("screen3_html")',
            'content_html=contract_screen_fragments.get("screen4_html")',
            'evidence_gate_enabled="screen3_html" not in contract_screen_fragments',
            'evidence_gate_enabled="screen4_html" not in contract_screen_fragments',
        ),
        "Generated or fragment HTML presence must not be treated as product evidence readiness.",
    )


def test_source_truth_llm_text_does_not_create_truth_state():
    source = read_text("src/reporting/html_dashboard.py") + read_text("src/learning/dashboard_runtime_interaction.py")

    assert_not_contains_any(
        source,
        (
            "llm_changes_truth: true",
            '"llm_changed_truth": True',
            '"llm_changed_truth": true',
            "llm_recommendation_truth_mutation_allowed: true",
        ),
        "LLM text must not create diagnosis, recommendation, learning state, materialization, or runtime eligibility.",
    )


def test_screen5_recommendations_require_deterministic_evidence_not_renderer_rows():
    html = render_screen5_action(
        screen5_model(
            action_rows=({"row_id": "llm-action", "recommendation": "LLM-created recommendation: scale now"},),
            recommendation_fields=(
                {"row_id": "llm-action", "values": {"recommendation": "LLM-created recommendation: scale now"}},
            ),
        )
    )
    visible = product_visible_text(html)

    assert "LLM-created recommendation: scale now" not in visible, (
        "Screen 5 recommendations must require deterministic recommendation evidence, not renderer rows or LLM text."
    )


def test_screen6_learning_governance_requires_governed_eligibility_not_renderer_rows():
    html = render_screen6_learning(
        screen6_model(
            governance_rows=(
                {"row_id": "runtime-text", "runtime_influence": "granted by dashboard text"},
            ),
            governance_status=(
                {"row_id": "runtime-text", "values": {"runtime_eligibility": "created by dashboard text"}},
            ),
            memory_policy=(
                {"row_id": "memory-text", "values": {"memory": "semantic recall treated as evidence"}},
            ),
        )
    )
    visible = product_visible_text(html)

    assert_not_contains_any(
        visible,
        (
            "granted by dashboard text",
            "created by dashboard text",
            "semantic recall treated as evidence",
        ),
        "Screen 6 learning/runtime eligibility must require governed deterministic eligibility, not dashboard text or memory recall.",
    )
