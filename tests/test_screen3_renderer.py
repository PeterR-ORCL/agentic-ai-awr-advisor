import ast
from pathlib import Path

from src.reporting.dashboard.adapters.evidence_pack_builder import build_evidence_pack_contract
from src.reporting.dashboard.contracts.selected_review_scope_contract import (
    RuntimeScopeIdentity,
    SelectionProvenance,
    SourceMode,
    build_selected_review_scope_contract,
)
from src.reporting.dashboard.renderers import screen3_renderer as module
from src.reporting.dashboard.renderers.screen3_renderer import render_screen3_diagnostic
from src.reporting.dashboard.view_models.screen3_diagnostic_view_model import (
    build_screen3_diagnostic_view_model,
)


RAW_DUMP_MARKERS = (
    "<pre",
    "{ domain:",
    "{ row_id:",
    "values:",
    "source_evidence_ids:",
    "visualization_id:",
    "Allowed visualizations",
    "CONTRACT_SCREEN3_SMOKE_FRAGMENT",
)


def provenance():
    return SelectionProvenance(source_system="screen2_backend_contract_builder")


def selected_scope():
    return build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        runtime_scope=RuntimeScopeIdentity(
            scope_id="single-awr-scope",
            label="Selected AWR PRODDB 10:00-11:00",
            report_id="awr-prod-001",
            database_id="PRODDB",
            snapshot_window_id="snap-10-11",
            alignment_key="PRODDB",
        ),
        selected_report={
            "report_id": "awr-prod-001",
            "label": "AWR PRODDB 10:00-11:00",
            "source_path": "prod_awr.html",
        },
        selected_window={
            "window_id": "snap-10-11",
            "begin_time": "2026-06-10 10:00",
            "end_time": "2026-06-10 11:00",
            "label": "10:00-11:00",
        },
        provenance=provenance(),
    )


def diagnostic_payload(include_points=True):
    trends = [{"trend_name": "DB CPU % DB Time", "direction": "up"}]
    if include_points:
        trends[0]["points"] = [
            {"index": 0, "value": 18.2},
            {"index": 1, "value": 30.4},
        ]
    return {
        "evidence_ids": ["diagnostic-evidence"],
        "rows": [
            {
                "row_id": "selected-context",
                "values": {
                    "selected_awr": "awr-prod-001",
                    "db_name": "PRODDB",
                    "snapshot_window": "10:00-11:00",
                },
            },
            {
                "row_id": "diagnostic-posture",
                "values": {
                    "primary_domain": "cpu",
                    "risk_level": "warning",
                    "confidence": "high",
                    "db_cpu_pct_db_time": 30.4,
                },
            },
            {
                "row_id": "healthcheck-cpu",
                "values": {
                    "healthcheck_status": "warning",
                    "check_status": "DB CPU pressure elevated",
                },
            },
        ],
        "metrics": {
            "DB CPU % DB Time": 30.4,
            "healthcheck_cpu_pressure": "warning",
        },
        "trends": trends,
        "anomalies": [
            {
                "anomaly_name": "DB CPU pressure",
                "severity": "warning",
                "description": "DB CPU % DB Time reached 30.4 for the selected interval.",
            }
        ],
        "confidence_basis": [{"basis_id": "diagnostic-confidence", "confidence": "high"}],
        "summary": "Diagnostic evidence for selected AWR interval.",
    }


def model_for_pack(**payloads):
    pack = build_evidence_pack_contract(selected_scope(), provenance="deterministic_builder", **payloads)
    return build_screen3_diagnostic_view_model(pack)


def test_screen3_renderer_renders_product_diagnostic_cards_and_visuals():
    html = render_screen3_diagnostic(model_for_pack(diagnostic_payload=diagnostic_payload()))

    assert 'data-screen="screen3_diagnostic_snapshot"' in html
    assert "Selected report context" in html
    assert "Diagnostic posture" in html
    assert "Top diagnostic drivers" in html
    assert "Metric cards" in html
    assert "Anomaly / event cards" in html
    assert "Healthcheck cards" in html
    assert "Diagnostic time-series evidence" in html
    assert 'data-visual-kind="time-series"' in html
    assert "DB CPU % DB Time" in html
    assert "30.4" in html
    _assert_no_raw_dump(html)


def test_screen3_renderer_marks_time_series_unavailable_when_points_are_missing():
    html = render_screen3_diagnostic(
        model_for_pack(diagnostic_payload=diagnostic_payload(include_points=False))
    )

    assert "Time-series unavailable" in html or "Visual evidence unavailable" in html
    assert 'data-visual-kind="time-series"' not in html
    _assert_no_raw_dump(html)


def test_screen3_single_awr_scope_rejects_multi_snapshot_selected_scope_contamination():
    contaminated = diagnostic_payload()
    contaminated["rows"].append(
        {
            "row_id": "supporting-history",
            "values": {
                "historical_context": "Multi-Snapshot Summary",
                "narrative": "24 snapshots were analyzed in chronological order.",
                "window": "Current Window 24 / 106h",
            },
        }
    )

    html = render_screen3_diagnostic(model_for_pack(diagnostic_payload=contaminated))

    assert "Selected report context" in html
    assert "awr-prod-001" in html
    assert "Supporting historical context" in html
    assert "supporting evidence only" in html
    assert "Multi-Snapshot Summary" not in html
    assert "24 snapshots were analyzed" not in html
    assert "chronological order" not in html
    assert "Current Window 24 / 106h" not in html
    assert "Historical Artifact Context" not in html
    _assert_no_raw_dump(html)


def test_screen3_renderer_excludes_target_ab_comparison_content_without_comparison_domain():
    html = render_screen3_diagnostic(model_for_pack(diagnostic_payload=diagnostic_payload()))

    assert "Target A" not in html
    assert "Target B" not in html
    assert "target_a_vs_target_b_delta" not in html
    assert "Comparative Review" not in html


def test_screen3_renderer_renders_missing_unavailable_and_stale_states():
    missing_html = render_screen3_diagnostic(model_for_pack())
    stale_html = render_screen3_diagnostic(
        model_for_pack(
            diagnostic_payload={
                "evidence_ids": ["diagnostic-evidence"],
                "rows": [{"row_id": "diagnostic-row", "metric": "db_cpu"}],
                "stale": True,
            }
        )
    )

    assert "Missing evidence" in missing_html
    assert "payload_missing" in missing_html
    assert "Stale evidence" in stale_html
    assert "payload_stale" in stale_html
    _assert_no_raw_dump(missing_html)
    _assert_no_raw_dump(stale_html)


def test_screen3_renderer_import_boundary():
    imports = _imports_for(module)
    forbidden = (
        "html_dashboard",
        "evidence_pack_builder",
        "selected_review_scope_contract",
        "evidence_pack_contract",
        "llm",
        "awr_dashboard",
        "browser",
        "comparison_execution",
        "screen4",
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
