import ast
from pathlib import Path

from src.reporting.dashboard.adapters.evidence_pack_builder import build_evidence_pack_contract
from src.reporting.dashboard.contracts.selected_review_scope_contract import (
    ComparisonTargetIdentity,
    ReviewMode,
    ReviewModeIntent,
    RuntimeScopeIdentity,
    SelectionProvenance,
    SourceMode,
    build_selected_review_scope_contract,
)
from src.reporting.dashboard.renderers import screen4_renderer as module
from src.reporting.dashboard.renderers.screen4_renderer import render_screen4_review
from src.reporting.dashboard.view_models.screen4_review_view_model import build_screen4_review_view_model


RAW_DUMP_MARKERS = (
    "<pre",
    "{ domain:",
    "{ row_id:",
    "values:",
    "source_evidence_ids:",
    "visualization_id:",
    "Allowed visualizations",
    "CONTRACT_SCREEN4_SMOKE_FRAGMENT",
)


def provenance():
    return SelectionProvenance(source_system="screen2_backend_contract_builder")


def selected_scope(**overrides):
    payload = {
        "source_mode": SourceMode.EXISTING_EVIDENCE,
        "runtime_scope": RuntimeScopeIdentity(scope_id="runtime-1", alignment_key="db-prod"),
        "target_a": ComparisonTargetIdentity(target_id="target-a", alignment_key="db-prod"),
        "target_b": ComparisonTargetIdentity(target_id="target-b", alignment_key="db-prod"),
        "review_mode_intent": ReviewModeIntent(
            requested_modes=(ReviewMode.DEEP_ANALYSIS,),
            historical_evidence_available=True,
            deep_analysis_requested=True,
            deep_analysis_available=True,
        ),
        "provenance": provenance(),
    }
    payload.update(overrides)
    return build_selected_review_scope_contract(**payload)


def single_awr_scope():
    return build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        runtime_scope=RuntimeScopeIdentity(
            scope_id="single-awr-scope",
            report_id="awr-prod-001",
            database_id="PRODDB",
            snapshot_window_id="snap-10-11",
            alignment_key="PRODDB",
        ),
        selected_report={"report_id": "awr-prod-001", "label": "AWR PRODDB 10:00-11:00"},
        review_mode_intent=ReviewModeIntent(
            requested_modes=(ReviewMode.HISTORICAL_REVIEW,),
            historical_evidence_available=True,
            deep_analysis_requested=False,
            deep_analysis_available=False,
        ),
        provenance=provenance(),
    )


def historical_payload(include_points=True, include_distribution=True):
    rows = [
        {
            "row_id": "historical-context",
            "values": {
                "trend_posture": "CPU pressure increased during supporting history.",
                "action": "Review SQL CPU drivers",
            },
        }
    ]
    if include_distribution:
        rows.append(
            {
                "row_id": "wait-distribution",
                "values": {"db_cpu_distribution_samples": [12, 18, 24, 30, 42]},
            }
        )
    trends = [{"trend_name": "DB CPU trend", "direction": "up"}]
    if include_points:
        trends[0]["points"] = [
            {"index": 0, "value": 12},
            {"index": 1, "value": 18},
            {"index": 2, "value": 30},
        ]
    return {
        "evidence_ids": ["historical-evidence"],
        "rows": rows,
        "metrics": {"historical_cpu_peak": 42},
        "trends": trends,
        "anomalies": [{"anomaly_name": "CPU burst", "severity": "warning"}],
        "summary": "Historical evidence for supporting review.",
    }


def payload(name):
    return {
        "evidence_ids": [f"{name}-evidence"],
        "rows": [{"row_id": f"{name}-row", "values": {"metric": name, "value": 7}}],
        "metrics": {f"{name}_metric": 7},
        "trends": [{"trend_name": f"{name}-trend", "direction": "flat"}],
        "summary": f"{name} evidence",
    }


def model_for_pack(scope=None, **payloads):
    pack = build_evidence_pack_contract(scope or selected_scope(), provenance="deterministic_builder", **payloads)
    return build_screen4_review_view_model(pack)


def test_screen4_renderer_renders_historical_review_as_product_cards_and_visuals():
    html = render_screen4_review(
        model_for_pack(
            historical_payload=historical_payload(),
            comparative_payload=payload("comparative"),
            deep_analysis_payload=payload("deep"),
        )
    )

    assert "Historical Review" in html
    assert "Historical Review context" in html
    assert "Historical Review evidence cards" in html
    assert "Historical Review trend cards" in html
    assert "Historical Review action posture" in html
    assert "Historical Review visual evidence" in html
    assert 'data-visual-kind="time-series"' in html
    assert 'data-visual-kind="violin"' in html
    _assert_no_raw_dump(html)


def test_screen4_renderer_marks_visuals_unavailable_when_points_are_missing():
    html = render_screen4_review(
        model_for_pack(
            historical_payload=historical_payload(include_points=False, include_distribution=False),
            comparative_payload=payload("comparative"),
            deep_analysis_payload=payload("deep"),
        )
    )

    assert "Time-series unavailable" in html or "Visual evidence unavailable" in html
    assert 'data-visual-kind="time-series"' not in html
    assert 'data-visual-kind="violin"' not in html
    _assert_no_raw_dump(html)


def test_screen4_renderer_keeps_comparative_unavailable_without_target_ab():
    html = render_screen4_review(
        model_for_pack(scope=single_awr_scope(), historical_payload=historical_payload())
    )

    assert "Comparative Review unavailable" in html
    assert "Target A and Target B deterministic selections are required" in html
    assert "target_a_vs_target_b_delta" not in html
    assert "computed_delta" not in html
    _assert_no_raw_dump(html)


def test_screen4_renderer_keeps_deep_analysis_unavailable_without_deep_input():
    html = render_screen4_review(
        model_for_pack(scope=single_awr_scope(), historical_payload=historical_payload())
    )

    assert "Deep Analysis unavailable" in html
    assert "Deep-analysis deterministic input is required" in html
    assert "fabricated" not in html.lower()
    _assert_no_raw_dump(html)


def test_screen4_does_not_present_historical_context_as_selected_scope_truth():
    contaminated = historical_payload()
    contaminated["rows"].append(
        {
            "row_id": "legacy-restored-baseline",
            "values": {
                "historical_context": "Historical Artifact Context",
                "current_window": "Current Window 24 / 106h",
            },
        }
    )

    html = render_screen4_review(
        model_for_pack(scope=single_awr_scope(), historical_payload=contaminated)
    )

    assert "Historical Review" in html
    assert "Selected-Scope Explanation" not in html
    assert "Multi-Snapshot Summary" not in html
    assert "24 snapshots were analyzed" not in html
    assert "Historical Artifact Context" not in html
    assert "Current Window 24 / 106h" not in html
    assert "Selected report context" not in html
    _assert_no_raw_dump(html)


def test_screen4_renderer_import_boundary():
    imports = _imports_for(module)
    forbidden = (
        "html_dashboard",
        "evidence_pack_builder",
        "selected_review_scope_contract",
        "evidence_pack_contract",
        "llm",
        "awr_dashboard",
        "browser",
        "selector",
        "screen3",
    )
    assert not any(fragment in name.lower() for name in imports for fragment in forbidden)


def _assert_no_raw_dump(html):
    for marker in RAW_DUMP_MARKERS:
        assert marker not in html


def _imports_for(imported_module):
    tree = ast.parse(Path(imported_module.__file__).read_text())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    return imports
