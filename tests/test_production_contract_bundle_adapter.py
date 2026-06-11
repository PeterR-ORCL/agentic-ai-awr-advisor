import copy
import hashlib
import inspect
from pathlib import Path

import pytest

from src.reporting.dashboard.adapters.production_contract_bundle_adapter import (
    build_production_dashboard_screen_render_bundle,
    build_production_selected_review_scope_contract,
    inspect_production_contract_bundle_readiness,
    require_production_contract_bundle_ready,
)


ROOT = Path(__file__).resolve().parents[1]
GENERATED_DASHBOARD_FILES = (
    ROOT / "awr_dashboard" / "index.html",
    ROOT / "awr_dashboard" / "screen_1_ingestion.html",
    ROOT / "awr_dashboard" / "screen_2_control.html",
    ROOT / "awr_dashboard" / "screen_3_analysis.html",
    ROOT / "awr_dashboard" / "screen_4_historical_review.html",
    ROOT / "awr_dashboard" / "screen_5_recommendation_action.html",
    ROOT / "awr_dashboard" / "screen_6_fleet_overview.html",
)


def _production_like_report_data():
    return {
        "title": "AWR Performance Intelligence Dashboard",
        "generated_at": "2026-06-10T12:00:00",
        "metadata": {
            "awr_id": 42,
            "db_name": "PRODDB",
            "dbid": "123456789",
            "instance_name": "PROD1",
            "host_name": "prod-host-1",
            "file_name": "prod_awr.html",
            "snapshot_begin": "2026-06-10 10:00:00",
            "snapshot_end": "2026-06-10 11:00:00",
        },
        "ingestion_context": {
            "source_mode": "LOCAL",
            "run_label": "2026-06-10T12:00:00",
            "report_rows": [
                {
                    "file_name": "prod_awr.html",
                    "parse_status": "SUCCESS",
                    "db_name": "PRODDB",
                    "dbid": "123456789",
                    "snapshot_begin": "2026-06-10 10:00:00",
                    "snapshot_end": "2026-06-10 11:00:00",
                }
            ],
        },
        "analysis_context": {
            "source_database": "PRODDB | DBID 123456789",
            "time_window": "1 hour",
            "latest_snapshot_interval": "10:00 -> 11:00",
            "awr_count_and_window": "2 / 2 hours",
        },
        "comparison_context": {
            "snapshot_count": 2,
            "comparison_window": "2 / 2 hours",
            "analysis_scope_label": "PRODDB | DBID 123456789",
        },
        "snapshot_labels": ["09:00 -> 10:00", "10:00 -> 11:00"],
        "scores": {"domain_scores": {"cpu": 91, "io": 12}},
        "trends": {"findings": ["CPU rising"]},
        "anomalies": {"count": 1, "windows": [{"metric": "DB CPU", "severity": "warning"}]},
        "decision": {"primary_domain": "cpu", "risk_level": "warning", "confidence": 0.88},
        "recommendations": [
            {"action": "Review SQL CPU", "impact": "High", "confidence": "high"}
        ],
        "grouped_deterministic_findings": {"primary_evidence": {"reasons": []}},
        "analysis_output": {"metadata": {"source": "AWR_ANALYSIS"}},
        "time_series": {"cpu_trend": [55, 72, 91]},
        "db_scope_metrics": {"available": True},
        "derived_scalar_metrics": {"hard_parses_per_sec": 1.2},
        "summary_key_signals": ["CPU pressure is elevated."],
        "confidence": {"level": "HIGH", "reasons": ["two snapshots"]},
        "memory_runtime": {"enabled": True, "success": True, "state": "Active"},
        "llm_explanation": {"authoritative": False, "technical_explanation": "LLM"},
        "ai_generated_narrative": "Narrative text",
        "compatibility": {"issues": []},
        "screen_models": {"screen_2_analysis": {"fallback_copy": "legacy"}},
        "time_series_charts": {"cpu": [55, 72, 91]},
        "violin_panel": {"groups": []},
    }


def _artifact_fingerprints():
    fingerprints = {}
    for path in GENERATED_DASHBOARD_FILES:
        if not path.exists():
            fingerprints[str(path.relative_to(ROOT))] = ("missing", None, None)
            continue
        payload = path.read_bytes()
        stat = path.stat()
        fingerprints[str(path.relative_to(ROOT))] = (
            "present",
            stat.st_mtime_ns,
            hashlib.sha256(payload).hexdigest(),
        )
    return fingerprints


def test_readiness_accepts_normalizable_runtime_report_window_inputs():
    readiness = inspect_production_contract_bundle_readiness(
        _production_like_report_data()
    )

    assert readiness.is_ready is True
    assert readiness.selected_scope_ready is True
    assert readiness.evidence_payloads_ready is True
    assert readiness.blockers == ()
    assert "metadata" in readiness.authoritative_fields
    assert "ingestion_context" in readiness.authoritative_fields
    assert "analysis_context" in readiness.authoritative_fields
    assert "scores" in readiness.deterministic_evidence_fields
    assert "recommendations" in readiness.deterministic_evidence_fields


def test_selected_scope_is_normalized_from_authoritative_production_identity():
    contract = build_production_selected_review_scope_contract(
        _production_like_report_data()
    )

    assert contract.runtime_scope is not None
    assert contract.selected_report is not None
    assert contract.selected_database is not None
    assert contract.selected_window is not None
    assert contract.provenance.source_system == "scripts.run_analysis.report_data"
    assert "diagnostic_snapshot" in [mode.value for mode in contract.eligible_review_modes]
    assert "historical_review" in [mode.value for mode in contract.eligible_review_modes]
    assert "comparative_review" not in [mode.value for mode in contract.eligible_review_modes]


def test_builds_real_dashboard_screen_bundle_without_smoke_fragments():
    bundle = build_production_dashboard_screen_render_bundle(
        _production_like_report_data()
    )

    assert bundle.selected_flow_id.startswith("selected-flow:")
    assert bundle.evidence_pack_id.startswith("evidence-pack:")
    assert "CONTRACT_SCREEN3_SMOKE_FRAGMENT" not in bundle.screen3_html
    assert "CONTRACT_SCREEN4_SMOKE_FRAGMENT" not in bundle.screen4_html
    assert "Diagnostic" in bundle.screen3_html
    assert "Comparative" in bundle.screen4_html
    assert bundle.errors == ()


def test_rejects_browser_generated_llm_and_legacy_fields_as_authority():
    report_data = {
        **_production_like_report_data(),
        "browser_state": {"selected": "runtime"},
        "hash_state": "#runtime",
        "generated_html_path": "awr_dashboard/screen_3_analysis.html",
        "nested": {
            "localStorage": {"scope": "cached"},
            "llm_facts": "not evidence",
            "chart_markup": "<canvas></canvas>",
        },
    }

    readiness = inspect_production_contract_bundle_readiness(report_data)
    rejected = {item.field_path: item.category for item in readiness.rejected_fields}

    assert rejected["llm_explanation"] == "LLM explanation"
    assert rejected["ai_generated_narrative"] == "LLM explanation"
    assert rejected["compatibility"] == "legacy fallback copy"
    assert rejected["screen_models"] == "transitional compatibility/display field"
    assert rejected["browser_state"] == "browser/cache/UI state"
    assert rejected["hash_state"] == "browser/cache/UI state"
    assert rejected["generated_html_path"] == "generated HTML/output"
    assert rejected["nested.localStorage"] == "browser/cache/UI state"
    assert rejected["nested.llm_facts"] == "LLM explanation"
    assert rejected["nested.chart_markup"] == "generated HTML/output"


def test_artifact_regeneration_is_blocked_when_selection_identity_is_missing():
    incomplete = {
        "metadata": {"awr_id": 42},
        "scores": {"domain_scores": {"cpu": 91}},
    }

    with pytest.raises(RuntimeError, match="Do not regenerate production dashboard artifacts"):
        require_production_contract_bundle_ready(incomplete)


def test_readiness_inspection_does_not_mutate_report_data():
    report_data = _production_like_report_data()
    original = copy.deepcopy(report_data)

    inspect_production_contract_bundle_readiness(report_data)

    assert report_data == original


def test_bundle_construction_does_not_mutate_report_data():
    report_data = _production_like_report_data()
    original = copy.deepcopy(report_data)

    build_production_dashboard_screen_render_bundle(report_data)

    assert report_data == original


def test_readiness_and_bundle_construction_do_not_write_generated_artifacts():
    before = _artifact_fingerprints()

    inspect_production_contract_bundle_readiness(_production_like_report_data())
    build_production_dashboard_screen_render_bundle(_production_like_report_data())

    after = _artifact_fingerprints()
    assert before == after


def test_adapter_source_has_no_generated_html_browser_cache_or_llm_authority():
    import src.reporting.dashboard.adapters.production_contract_bundle_adapter as adapter

    source = inspect.getsource(adapter)

    assert "generate_html_dashboard(" not in source
    assert "read_text" not in source
    assert "open(" not in source
    assert "provider_adapter" not in source
    assert "generate_ai_response" not in source
