import hashlib
import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import run_analysis


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


def _report_data():
    return {
        "title": "Contract Invocation Test Dashboard",
        "generated_at": "2026-06-10T00:00:00",
        "screen_models": {},
    }


def _bundle():
    return SimpleNamespace(
        screen3_html="<section>CONTRACT_SCREEN3_SMOKE_FRAGMENT</section>",
        screen4_html="<section>CONTRACT_SCREEN4_SMOKE_FRAGMENT</section>",
        screen5_html="<section>CONTRACT_SCREEN5_SMOKE_FRAGMENT</section>",
        screen6_html="<section>CONTRACT_SCREEN6_SMOKE_FRAGMENT</section>",
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


def test_invocation_path_passes_bundle_to_generate_html_dashboard(monkeypatch):
    observed = {}

    def fake_generate_html_dashboard(
        report_data,
        output_file="awr_dashboard.html",
        contract_screen_render_bundle=None,
    ):
        observed["report_data"] = report_data
        observed["output_file"] = output_file
        observed["contract_screen_render_bundle"] = contract_screen_render_bundle
        return "/tmp/contract-dashboard/index.html"

    monkeypatch.setattr(
        run_analysis,
        "generate_html_dashboard",
        fake_generate_html_dashboard,
    )
    report_data = _report_data()
    bundle = _bundle()

    result = run_analysis.generate_dashboard_with_contract_screen_render_bundle(
        report_data,
        contract_screen_render_bundle=bundle,
        output_file="/tmp/contract-dashboard.html",
    )

    assert result == "/tmp/contract-dashboard/index.html"
    assert observed["report_data"] is report_data
    assert observed["output_file"] == "/tmp/contract-dashboard.html"
    assert observed["contract_screen_render_bundle"] is bundle


def test_invocation_path_requires_bundle_before_artifact_generation(monkeypatch):
    called = False

    def fake_generate_html_dashboard(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(
        run_analysis,
        "generate_html_dashboard",
        fake_generate_html_dashboard,
    )

    with pytest.raises(ValueError, match="contract_screen_render_bundle is required"):
        run_analysis.generate_dashboard_with_contract_screen_render_bundle(
            _report_data(),
            contract_screen_render_bundle=None,
            output_file="/tmp/should-not-write.html",
        )

    assert called is False


def test_contract_backed_temp_write_uses_bundle_fragments(tmp_path):
    output_file = tmp_path / "contract_smoke_dashboard.html"

    index_path = run_analysis.generate_dashboard_with_contract_screen_render_bundle(
        _report_data(),
        contract_screen_render_bundle=_bundle(),
        output_file=str(output_file),
    )

    output_dir = tmp_path / "contract_smoke_dashboard"
    assert Path(index_path) == output_dir / "index.html"
    assert "CONTRACT_SCREEN3_SMOKE_FRAGMENT" in (
        output_dir / "screen_3_analysis.html"
    ).read_text(encoding="utf-8")
    assert "CONTRACT_SCREEN4_SMOKE_FRAGMENT" in (
        output_dir / "screen_4_historical_review.html"
    ).read_text(encoding="utf-8")
    assert "CONTRACT_SCREEN5_SMOKE_FRAGMENT" in (
        output_dir / "screen_5_recommendation_action.html"
    ).read_text(encoding="utf-8")
    assert "CONTRACT_SCREEN6_SMOKE_FRAGMENT" in (
        output_dir / "screen_6_fleet_overview.html"
    ).read_text(encoding="utf-8")


def test_contract_backed_temp_write_does_not_modify_tracked_dashboard_artifacts(tmp_path):
    before = _artifact_fingerprints()

    run_analysis.generate_dashboard_with_contract_screen_render_bundle(
        _report_data(),
        contract_screen_render_bundle=_bundle(),
        output_file=str(tmp_path / "contract_no_repo_write.html"),
    )

    after = _artifact_fingerprints()
    assert before == after


def test_invocation_path_does_not_read_generated_html_or_browser_cache_authority():
    source = inspect.getsource(
        run_analysis.generate_dashboard_with_contract_screen_render_bundle
    )

    assert "read_text" not in source
    assert "open(" not in source
    assert "awr_dashboard" not in source
    assert "localStorage" not in source
    assert "hash_state" not in source
    assert "browser_state" not in source
    assert "cache_continuity" not in source


def test_invocation_path_does_not_compute_evidence_or_call_llm():
    source = inspect.getsource(
        run_analysis.generate_dashboard_with_contract_screen_render_bundle
    )

    assert "build_selected_review_scope_contract" not in source
    assert "selected_review_scope_contract" not in source
    assert "build_evidence_pack_contract" not in source
    assert "evidence_pack_builder" not in source
    assert "dashboard_screen_adapter" not in source
    assert "generate_ai_narrative" not in source
    assert "llm" not in source.lower()


def test_current_run_analysis_generation_call_uses_explicit_contract_bundle_helper():
    source = (ROOT / "scripts" / "run_analysis.py").read_text(encoding="utf-8")

    assert "build_production_dashboard_screen_render_bundle(" in source
    assert "report_data" in source
    assert "dashboard_file = generate_dashboard_with_contract_screen_render_bundle" in source
    assert "dashboard_file = generate_html_dashboard(report_data)" not in source
