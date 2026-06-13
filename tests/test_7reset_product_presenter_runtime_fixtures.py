import os
from dataclasses import fields, is_dataclass
from pathlib import Path

import pytest


_RUN_7RESET_PRESENTER_FIXTURES = os.environ.get("AWR_RUN_7RESET_PRESENTER_FIXTURES") == "1"

pytestmark = pytest.mark.skipif(
    not _RUN_7RESET_PRESENTER_FIXTURES,
    reason=(
        "7RESET product presenter runtime fixture gate is intentionally opt-in. "
        "Run with AWR_RUN_7RESET_PRESENTER_FIXTURES=1."
    ),
)


def presenters():
    from src.reporting.dashboard import presenters as presenter_module

    return presenter_module


def product_types():
    from src.reporting.dashboard.view_models.screen3_diagnostic_snapshot import (
        Screen3DiagnosticSnapshotViewModel,
    )
    from src.reporting.dashboard.view_models.screen4_evidence_review import (
        Screen4EvidenceReviewViewModel,
    )
    from src.reporting.dashboard.view_models.screen5_recommendation_action import (
        Screen5RecommendationActionViewModel,
    )
    from src.reporting.dashboard.view_models.screen6_learning_governance import (
        Screen6LearningGovernanceViewModel,
    )
    from src.reporting.dashboard.view_models.shared_product_shapes import UnavailableVisualState
    from src.reporting.dashboard.view_models.visual_contracts import (
        ComparisonDeltaVisual,
        DistributionVisual,
        TimeSeriesVisual,
        ViolinVisual,
    )

    return {
        "screen3": Screen3DiagnosticSnapshotViewModel,
        "screen4": Screen4EvidenceReviewViewModel,
        "screen5": Screen5RecommendationActionViewModel,
        "screen6": Screen6LearningGovernanceViewModel,
        "visuals": (TimeSeriesVisual, DistributionVisual, ViolinVisual, ComparisonDeltaVisual, UnavailableVisualState),
        "unavailable": UnavailableVisualState,
    }


def deterministic_scope(flow_kind, **overrides):
    scope = {
        "contract_type": "selected_review_scope_contract",
        "contract_version": "7reset.selected_review_scope.v1",
        "selected_flow_id": f"selected-flow-{flow_kind}",
        "flow_kind": flow_kind,
        "validation_status": "valid",
        "source_of_truth": {"authority": "database_contract"},
        "provenance": {"source_system": "deterministic_scope_fixture"},
        "selected_report": {"report_id": "awr-current", "label": "AWR current"},
        "selected_window": {"window_id": "snap-100-101", "begin_time": "2026-06-01T00:00:00Z"},
        "runtime_scope": {
            "scope_id": "runtime-current",
            "label": "Runtime scope",
            "database_id": "db-prod",
            "snapshot_window_id": "snap-100-101",
        },
    }
    scope.update(overrides)
    return scope


def deterministic_evidence_pack(**channels):
    pack = {
        "contract_type": "evidence_pack_contract",
        "contract_version": "7reset.evidence_pack.v1",
        "evidence_pack_id": "evidence-pack-runtime-fixture",
        "provenance": {"source_system": "deterministic_evidence_fixture"},
        "llm_explanation_eligibility": {"source_evidence_ids": ("selected-diagnostic",)},
        "missing_evidence": (),
        "unavailable_states": (),
    }
    pack.update(channels)
    return pack


def selected_diagnostic_evidence(**overrides):
    evidence = {
        "summary": "CPU pressure from deterministic evidence",
        "severity_score": 0.82,
        "confidence_score": 0.91,
        "top_driver_labels": ("DB CPU", "log file sync"),
        "rows": (
            {
                "row_id": "selected-diagnostic",
                "metric": "DB CPU",
                "values": {
                    "value": 82,
                    "unit": "percent",
                    "interpretation": "CPU pressure from selected AWR",
                },
            },
        ),
    }
    evidence.update(overrides)
    return evidence


def deep_analysis_evidence():
    return {
        "summary": "Deep detail evidence exists",
        "rows": ({"row_id": "deep-1", "metric": "SQL detail", "values": {"value": "ready"}},),
    }


def temporal_evidence():
    return {
        "summary": "Window-level diagnostic posture is degrading",
        "rows": ({"row_id": "temporal-1", "metric": "trend", "values": {"value": "degrading"}},),
    }


def comparison_evidence(targets=("target-a", "target-b")):
    return {
        "summary": "Comparative diagnostic posture shows target delta",
        "delta_drivers": ("DB CPU delta", "IO latency delta"),
        "targets": tuple(targets),
        "rows": ({"row_id": "comparison-1", "metric": "delta", "values": {"value": "worse on target-b"}},),
    }


def recommendation_evidence(summary="Scale CPU after deterministic validation"):
    return {
        "summary": summary,
        "rows": ({"row_id": "rec-1", "metric": "recommendation", "values": {"recommendation": summary}},),
    }


def governance_evidence(summary="Governed recurring pattern candidate"):
    return {
        "summary": summary,
        "rows": ({"row_id": "gov-1", "metric": "candidate", "values": {"value": summary}},),
    }


def visualization(kind="time_series", **overrides):
    item = {
        "visual_id": f"visual-{kind}",
        "visual_kind": kind,
        "title": f"{kind} evidence",
        "source_evidence_ids": ("visual-source-1",),
        "metric_name": "DB CPU",
        "target_a": "target-a",
        "target_b": "target-b",
    }
    item.update(overrides)
    return item


def build_all(scope, pack):
    module = presenters()
    return (
        module.build_screen3_diagnostic_snapshot_view_model(scope, pack),
        module.build_screen4_evidence_review_view_model(scope, pack),
        module.build_screen5_recommendation_action_view_model(scope, pack),
        module.build_screen6_learning_governance_view_model(scope, pack),
    )


def all_text(value):
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        return " ".join(all_text(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return " ".join(all_text(item) for item in value)
    if is_dataclass(value):
        return " ".join(all_text(getattr(value, field.name)) for field in fields(value))
    return str(value)


def rows_by_label(section):
    return {row.label: row for row in getattr(section, "rows", ())}


def assert_product_scope_summary(view_model, flow_kind):
    assert view_model.scope_summary.flow_kind == flow_kind
    assert view_model.scope_summary.validation_status == "valid"


def assert_no_internal_ids_in_first_fold(view_model):
    text = all_text(view_model.first_fold)
    assert "selected-flow-" not in text
    assert "evidence-pack-" not in text
    assert not hasattr(view_model, "selected_flow_id")
    assert not hasattr(view_model, "evidence_pack_id")


def assert_explanation_not_evidence(explanation):
    assert getattr(explanation, "prohibited_as_evidence", False) is True


def assert_has_unavailable_state(items, reason_fragment=None):
    text = all_text(items)
    assert "unavailable" in text.lower()
    if reason_fragment:
        assert reason_fragment.lower() in text.lower()


def assert_mode_availability(screen4_vm, mode, expected):
    assert getattr(screen4_vm, mode).availability == expected


def assert_visuals_are_contracts(visuals):
    visual_types = product_types()["visuals"]
    for visual in visuals:
        assert isinstance(visual, visual_types), f"Unexpected visual contract type: {type(visual)!r}"
        assert not isinstance(visual, dict)


def test_single_awr_diagnostic_projection_and_screen4_modes():
    types = product_types()
    scope = deterministic_scope("single_awr")
    pack = deterministic_evidence_pack(
        selected_diagnostic_evidence=selected_diagnostic_evidence(),
        deep_analysis_evidence=deep_analysis_evidence(),
        missing_evidence=({"reason_code": "temporal_absent", "message": "No temporal evidence for single AWR."},),
    )

    screen3, screen4, _, _ = build_all(scope, pack)

    assert isinstance(screen3, types["screen3"])
    assert screen3.screen_id == "screen3_diagnostic_snapshot"
    assert_product_scope_summary(screen3, "single_awr")
    assert screen3.first_fold.status_label == "point-in-time diagnostic snapshot"
    assert screen3.first_fold.primary_issue_label == "CPU pressure from deterministic evidence"
    assert screen3.first_fold.confidence_score == 0.91
    assert "DB CPU" in screen3.first_fold.top_driver_labels
    assert screen3.missing_evidence == ("No temporal evidence for single AWR.",)
    assert_no_internal_ids_in_first_fold(screen3)
    assert_explanation_not_evidence(screen3.llm_explanation)

    assert isinstance(screen4, types["screen4"])
    assert_mode_availability(screen4, "deep_analysis", "ready")
    assert_mode_availability(screen4, "historical", "unavailable")
    assert_mode_availability(screen4, "comparative", "unavailable")


def test_historical_multi_snapshot_window_projection_and_visual_gap_state():
    scope = deterministic_scope(
        "historical_multi_snapshot",
        selected_reports=({"report_id": "awr-1"}, {"report_id": "awr-2"}, {"report_id": "awr-3"}),
        selected_window={"window_id": "window-3-snapshots"},
    )
    pack = deterministic_evidence_pack(
        temporal_evidence=temporal_evidence(),
        supporting_historical_context={"summary": "Supporting only"},
    )

    screen3, screen4, _, _ = build_all(scope, pack)

    assert_product_scope_summary(screen3, "historical_multi_snapshot")
    assert screen3.first_fold.status_label == "window-level diagnostic posture"
    assert "single-AWR" not in all_text(screen3.first_fold)
    assert_mode_availability(screen4, "historical", "ready")
    assert_mode_availability(screen4, "comparative", "unavailable")
    assert_visuals_are_contracts(screen4.historical.visuals)
    assert_has_unavailable_state(
        screen4.historical.unavailable_states or screen4.historical.visuals,
        "visual",
    )


def test_multi_awr_set_projection_keeps_set_distinct_from_comparison():
    scope = deterministic_scope(
        "multi_awr_set",
        target_a=None,
        target_b=None,
        selected_reports=({"report_id": "awr-1"}, {"report_id": "awr-2"}, {"report_id": "awr-3"}),
        analysis_set_members=("awr-1", "awr-2", "awr-3"),
    )
    pack = deterministic_evidence_pack(
        selected_set_evidence={"selected_count": 3, "summary": "Three selected AWRs"},
        aggregate_evidence={"summary": "Set-level CPU pressure", "repeated_drivers": ("DB CPU", "IO latency")},
        member_diagnostic_evidence=({"row_id": "member-1", "values": {"value": "awr-2 outlier"}},),
        recommendation_evidence=recommendation_evidence("Set-level backlog ready"),
        governance_evidence=governance_evidence("Repeated pattern candidate"),
    )

    screen3, screen4, screen5, screen6 = build_all(scope, pack)

    rows = rows_by_label(screen3.primary_cards[0])
    assert rows["selected_count"].value == 3
    assert rows["aggregate_posture"].value == "Set-level CPU pressure"
    assert "DB CPU" in str(rows["repeated_drivers"].value)
    assert "selected_scope_analysis_set" in " ".join(screen4.cross_mode_warnings)
    assert_mode_availability(screen4, "comparative", "unavailable")
    assert "comparison" not in screen3.first_fold.status_label.lower()
    assert screen5.recommendation_decision == "Set-level backlog ready"
    assert screen6.governance_status == "ready"


def test_comparison_projection_requires_comparison_evidence_and_targets():
    comparison_scope = deterministic_scope(
        "comparison",
        target_a={"target_id": "target-a"},
        target_b={"target_id": "target-b"},
    )
    comparison_pack = deterministic_evidence_pack(
        comparison_evidence=comparison_evidence(),
        recommendation_evidence=recommendation_evidence("Delta-based recommendation ready"),
    )
    screen3, screen4, screen5, _ = build_all(comparison_scope, comparison_pack)

    assert screen3.first_fold.status_label == "comparative diagnostic posture"
    assert "DB CPU delta" in screen3.first_fold.top_driver_labels
    assert_mode_availability(screen4, "comparative", "ready")
    assert screen4.active_mode == "comparative"
    assert screen5.recommendation_decision == "Delta-based recommendation ready"

    missing_pack = deterministic_evidence_pack()
    missing_screen3, missing_screen4, missing_screen5, _ = build_all(comparison_scope, missing_pack)

    assert missing_screen3.first_fold.status_label == "unavailable"
    assert_mode_availability(missing_screen4, "comparative", "unavailable")
    assert missing_screen5.recommendation_decision == "unavailable"


def test_multi_target_comparison_keeps_n_way_target_resolution():
    scope = deterministic_scope(
        "multi_target_comparison",
        comparison_targets=({"target_id": "a"}, {"target_id": "b"}, {"target_id": "c"}),
    )
    pack = deterministic_evidence_pack(
        comparison_evidence=comparison_evidence(("a", "b", "c")),
        visualization_evidence=(visualization("comparison_delta"),),
    )

    screen3, screen4, _, _ = build_all(scope, pack)

    assert screen3.first_fold.status_label == "comparative diagnostic posture"
    assert_mode_availability(screen4, "comparative", "ready")
    assert "N-way" in all_text(screen4.comparative.secondary_sections)
    assert "target-a" not in all_text(screen4.comparative.first_fold_summary)


def test_fleet_projection_uses_governed_evidence_for_runtime_eligibility():
    scope = deterministic_scope(
        "fleet",
        fleet={"fleet_id": "fleet-east"},
        member_refs=("db1", "db2", "db3"),
    )
    pack = deterministic_evidence_pack(
        fleet_or_cohort_evidence={"summary": "Fleet/cohort posture degraded", "outlier_members": ("db2",)},
        recommendation_evidence=recommendation_evidence("Fleet action backlog ready"),
        governance_evidence=governance_evidence("Fleet-level governed eligibility"),
    )

    screen3, screen4, screen5, screen6 = build_all(scope, pack)

    assert screen3.first_fold.status_label == "fleet/cohort diagnostic posture"
    assert "db2" in screen3.first_fold.top_driver_labels
    assert "fleet" in all_text(screen4).lower() or assert_has_unavailable_state(screen4, "fleet") is None
    assert screen5.recommendation_decision == "Fleet action backlog ready"
    assert screen6.governance_status == "ready"
    assert screen6.runtime_eligibility == "governed eligibility"


@pytest.mark.parametrize("flow_kind", ("predictive_sizing", "comparative_sizing"))
def test_future_sizing_without_sizing_contracts_is_explicitly_unavailable(flow_kind):
    scope = deterministic_scope(flow_kind)
    pack = deterministic_evidence_pack(
        selected_diagnostic_evidence={"summary": "LLM says sizing is good"},
        recommendation_evidence=(),
        visualization_evidence=(),
    )

    screen3, screen4, screen5, screen6 = build_all(scope, pack)

    assert screen3.first_fold.status_label == "unavailable"
    assert_has_unavailable_state(screen3.secondary_sections, "sizing")
    assert "LLM says sizing is good" not in screen5.recommendation_decision
    assert screen5.recommendation_decision == "unavailable"
    assert screen6.runtime_eligibility == "unavailable"
    assert screen4.historical.availability == "unavailable"


def test_supporting_historical_context_is_not_selected_diagnostic_truth():
    scope = deterministic_scope("single_awr")
    pack = deterministic_evidence_pack(
        supporting_historical_context={"summary": "24 snapshots were analyzed"},
        missing_evidence=({"reason_code": "selected_diagnostic_missing", "message": "Selected diagnostic missing."},),
    )

    screen3, screen4, _, _ = build_all(scope, pack)

    assert screen3.first_fold.status_label == "unavailable"
    assert "24 snapshots were analyzed" not in all_text(screen3.first_fold)
    assert "Selected diagnostic missing." in screen3.missing_evidence
    assert screen4.historical.availability == "partial"
    assert "supporting" in screen4.historical.first_fold_summary.lower()


def test_allowed_visualizations_without_visualization_evidence_is_not_product_visual():
    scope = deterministic_scope("single_awr")
    pack = deterministic_evidence_pack(
        selected_diagnostic_evidence=selected_diagnostic_evidence(),
        allowed_visualizations=({"kind": "time_series", "title": "Metadata only"},),
    )

    screen3, screen4, _, _ = build_all(scope, pack)

    assert screen3.visuals == ()
    assert screen4.historical.visuals == ()
    assert "Metadata only" not in all_text((screen3, screen4))


@pytest.mark.parametrize(
    "marker,payload",
    (
        ("local" + "Storage", {"local" + "Storage": {"flow_kind": "single_awr"}}),
        ("generated_html", {"generated_html": "<section>single_awr</section>"}),
        ("browser_cache", {"browser_cache": {"validation_status": "valid"}}),
        ("url_hash", {"url_hash": "#screen3"}),
        ("cached_continuity_only", {"cached_continuity_only": True}),
    ),
)
def test_source_truth_rejects_browser_cache_generated_html_mappings(marker, payload):
    pack = deterministic_evidence_pack(selected_diagnostic_evidence=selected_diagnostic_evidence())

    with pytest.raises((TypeError, ValueError), match="deterministic authority|SelectedReviewScopeContract"):
        presenters().build_screen3_diagnostic_snapshot_view_model(payload, pack)


def test_product_model_type_integrity_for_valid_outputs():
    types = product_types()
    scope = deterministic_scope("single_awr")
    pack = deterministic_evidence_pack(
        selected_diagnostic_evidence=selected_diagnostic_evidence(),
        deep_analysis_evidence=deep_analysis_evidence(),
        visualization_evidence=(
            visualization("time_series"),
            visualization("distribution"),
            visualization("violin"),
            visualization("comparison_delta"),
        ),
        recommendation_evidence=recommendation_evidence(),
        governance_evidence=governance_evidence(),
    )

    screen3, screen4, screen5, screen6 = build_all(scope, pack)

    assert isinstance(screen3, types["screen3"])
    assert isinstance(screen4, types["screen4"])
    assert isinstance(screen5, types["screen5"])
    assert isinstance(screen6, types["screen6"])
    assert not isinstance(screen3, str)
    assert not isinstance(screen4, str)
    assert not isinstance(screen5, str)
    assert not isinstance(screen6, str)
    assert_visuals_are_contracts(screen3.visuals)
    assert_visuals_are_contracts(screen4.deep_analysis.visuals)


def test_internal_refs_and_first_fold_are_product_safe_not_raw_dumps():
    scope = deterministic_scope("single_awr")
    pack = deterministic_evidence_pack(
        selected_diagnostic_evidence=selected_diagnostic_evidence(),
        deep_analysis_evidence=deep_analysis_evidence(),
    )

    screen3, _, screen5, _ = build_all(scope, pack)

    assert_no_internal_ids_in_first_fold(screen3)
    assert is_dataclass(screen3.first_fold)
    assert not isinstance(screen3.first_fold, dict)
    assert not isinstance(screen3.first_fold, list)
    assert "selected-flow-single_awr" in screen3.internal_refs
    assert "evidence-pack-runtime-fixture" in screen3.internal_refs
    assert "selected-flow-single_awr" not in all_text(screen5.first_fold)
    assert "evidence-pack-runtime-fixture" not in all_text(screen5.first_fold)


def test_pf_gate_does_not_use_generated_artifacts_or_renderers_as_truth():
    text = Path(__file__).read_text(encoding="utf-8")

    forbidden = (
        "read_text(\"awr_" + "dashboard/",
        "Path(\"awr_" + "dashboard/",
        "src.reporting.dashboard." + "renderers",
        "src.reporting." + "html_dashboard",
        "local" + "Storage",
    )
    found = [token for token in forbidden if token in text]
    assert not found, f"Presenter runtime fixture tests must not use artifact/browser/renderer truth: {found}"
