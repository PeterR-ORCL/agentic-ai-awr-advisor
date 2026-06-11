import hashlib
import inspect
from pathlib import Path

import pytest

from scripts import run_analysis
from src.reporting.dashboard.adapters.production_contract_bundle_adapter import (
    inspect_production_contract_bundle_readiness,
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


def test_current_production_path_builds_and_passes_contract_screen_render_bundle():
    source = (ROOT / "scripts" / "run_analysis.py").read_text(encoding="utf-8")

    assert "build_production_dashboard_screen_render_bundle(" in source
    assert "report_data" in source
    assert "dashboard_file = generate_dashboard_with_contract_screen_render_bundle" in source
    assert "contract_screen_render_bundle=contract_screen_render_bundle" in source
    assert "dashboard_file = generate_html_dashboard(report_data)" not in source


def test_current_production_path_is_not_plain_legacy_generation():
    source = (ROOT / "scripts" / "run_analysis.py").read_text(encoding="utf-8")
    production_call_index = source.index(
        "dashboard_file = generate_dashboard_with_contract_screen_render_bundle"
    )
    nearby_source = source[production_call_index - 400:production_call_index + 300]

    assert "build_production_dashboard_screen_render_bundle" in nearby_source
    assert "contract_screen_render_bundle" in nearby_source
    assert "generate_html_dashboard(report_data)" not in nearby_source


def test_explicit_helper_still_requires_bundle_and_output_file():
    signature = inspect.signature(
        run_analysis.generate_dashboard_with_contract_screen_render_bundle
    )

    assert "contract_screen_render_bundle" in signature.parameters
    assert signature.parameters["contract_screen_render_bundle"].default is inspect._empty
    assert "output_file" in signature.parameters
    assert signature.parameters["output_file"].default is inspect._empty
    with pytest.raises(ValueError, match="contract_screen_render_bundle is required"):
        run_analysis.generate_dashboard_with_contract_screen_render_bundle(
            {"screen_models": {}},
            contract_screen_render_bundle=None,
            output_file="/tmp/not-written.html",
        )


def test_no_generated_html_browser_cache_or_llm_authority_in_invocation_helper():
    helper_source = inspect.getsource(
        run_analysis.generate_dashboard_with_contract_screen_render_bundle
    )

    assert "read_text" not in helper_source
    assert "open(" not in helper_source
    assert "localStorage" not in helper_source
    assert "hash_state" not in helper_source
    assert "browser_state" not in helper_source
    assert "generate_ai_response" not in helper_source
    assert "generate_ai_narrative" not in helper_source


def test_contract_backed_regeneration_blocks_without_authoritative_selection_inputs():
    readiness = inspect_production_contract_bundle_readiness(
        {
            "metadata": {"awr_id": 100},
            "scores": {"domain_scores": {"cpu": 80}},
            "llm_explanation": {"technical_explanation": "not evidence"},
            "generated_html_path": "awr_dashboard/screen_3_analysis.html",
        }
    )

    assert readiness.is_ready is False
    assert readiness.selected_scope_ready is False
    assert readiness.evidence_payloads_ready is True


def test_plumbing_checks_do_not_write_generated_artifacts():
    before = _artifact_fingerprints()

    inspect_production_contract_bundle_readiness(
        {
            "metadata": {"awr_id": 100},
            "scores": {"domain_scores": {"cpu": 80}},
            "screen_models": {"screen_2_analysis": {}},
        }
    )

    after = _artifact_fingerprints()
    assert before == after
