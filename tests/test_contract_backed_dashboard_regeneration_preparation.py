import hashlib
import inspect
from pathlib import Path
from types import SimpleNamespace

from src.reporting import html_dashboard


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
        "title": "Contract-Backed Regeneration Preparation",
        "generated_at": "2026-06-10T00:00:00",
        "screen_models": {},
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


def _build_pages(bundle=None):
    return html_dashboard._build_dashboard_pages(
        _report_data(),
        contract_screen_render_bundle=bundle,
    )


def _fragment_mapping(prefix):
    return {
        "screen3_html": f"<section>{prefix}_SCREEN3</section>",
        "screen4_html": f"<section>{prefix}_SCREEN4</section>",
        "screen5_html": f"<section>{prefix}_SCREEN5</section>",
        "screen6_html": f"<section>{prefix}_SCREEN6</section>",
    }


def test_shell_hook_dry_run_places_contract_fragments_without_artifact_write():
    before = _artifact_fingerprints()
    pages = _build_pages(_fragment_mapping("DRY_RUN"))
    after = _artifact_fingerprints()

    assert "DRY_RUN_SCREEN3" in pages["screen_3_analysis.html"]
    assert "DRY_RUN_SCREEN4" in pages["screen_4_historical_review.html"]
    assert "DRY_RUN_SCREEN5" in pages["screen_5_recommendation_action.html"]
    assert "DRY_RUN_SCREEN6" in pages["screen_6_fleet_overview.html"]
    assert before == after


def test_bundle_shape_compatibility_for_mapping_object_and_to_dict():
    mapping_pages = _build_pages(_fragment_mapping("MAPPING"))
    object_pages = _build_pages(SimpleNamespace(**_fragment_mapping("OBJECT")))
    dict_pages = _build_pages(
        SimpleNamespace(to_dict=lambda: _fragment_mapping("TO_DICT"))
    )

    assert "MAPPING_SCREEN3" in mapping_pages["screen_3_analysis.html"]
    assert "MAPPING_SCREEN4" in mapping_pages["screen_4_historical_review.html"]
    assert "MAPPING_SCREEN5" in mapping_pages["screen_5_recommendation_action.html"]
    assert "MAPPING_SCREEN6" in mapping_pages["screen_6_fleet_overview.html"]

    assert "OBJECT_SCREEN3" in object_pages["screen_3_analysis.html"]
    assert "OBJECT_SCREEN4" in object_pages["screen_4_historical_review.html"]
    assert "OBJECT_SCREEN5" in object_pages["screen_5_recommendation_action.html"]
    assert "OBJECT_SCREEN6" in object_pages["screen_6_fleet_overview.html"]

    assert "TO_DICT_SCREEN3" in dict_pages["screen_3_analysis.html"]
    assert "TO_DICT_SCREEN4" in dict_pages["screen_4_historical_review.html"]
    assert "TO_DICT_SCREEN5" in dict_pages["screen_5_recommendation_action.html"]
    assert "TO_DICT_SCREEN6" in dict_pages["screen_6_fleet_overview.html"]


def test_legacy_fallback_is_explicit_when_no_contract_bundle_is_supplied(monkeypatch):
    monkeypatch.setattr(
        html_dashboard,
        "_render_screen_2_page",
        lambda *args, **kwargs: "LEGACY_FALLBACK_SCREEN3",
    )
    monkeypatch.setattr(
        html_dashboard,
        "_render_screen_4_page",
        lambda *args, **kwargs: "LEGACY_FALLBACK_SCREEN4",
    )
    monkeypatch.setattr(
        html_dashboard,
        "_render_screen_5_page",
        lambda *args, **kwargs: "LEGACY_FALLBACK_SCREEN5",
    )
    monkeypatch.setattr(
        html_dashboard,
        "_render_screen_6_page",
        lambda *args, **kwargs: "LEGACY_FALLBACK_SCREEN6",
    )

    pages = _build_pages()

    assert "LEGACY_FALLBACK_SCREEN3" in pages["screen_3_analysis.html"]
    assert "LEGACY_FALLBACK_SCREEN4" in pages["screen_4_historical_review.html"]
    assert "LEGACY_FALLBACK_SCREEN5" in pages["screen_5_recommendation_action.html"]
    assert "LEGACY_FALLBACK_SCREEN6" in pages["screen_6_fleet_overview.html"]
    assert "Evidence Handoff Required" in pages["screen_3_analysis.html"]
    assert "Evidence Handoff Required" in pages["screen_4_historical_review.html"]
    assert "Evidence Handoff Required" in pages["screen_5_recommendation_action.html"]
    assert "Evidence Handoff Required" in pages["screen_6_fleet_overview.html"]


def test_shell_hook_source_does_not_read_generated_html_or_browser_cache_authority():
    hook_text = (
        inspect.getsource(html_dashboard._contract_screen_render_fragments)
        + inspect.getsource(html_dashboard._build_dashboard_pages)
    )

    assert "read_text" not in hook_text
    assert "open(" not in hook_text
    assert "awr_dashboard" not in hook_text
    assert "localStorage" not in hook_text
    assert "hash_state" not in hook_text
    assert "browser_state" not in hook_text
    assert "cache_continuity" not in hook_text


def test_shell_hook_does_not_compute_selected_scope_or_evidence_pack():
    hook_text = (
        inspect.getsource(html_dashboard._contract_screen_render_fragments)
        + inspect.getsource(html_dashboard._build_dashboard_pages)
    )

    assert "build_selected_review_scope_contract" not in hook_text
    assert "selected_review_scope_contract" not in hook_text
    assert "build_evidence_pack_contract" not in hook_text
    assert "evidence_pack_contract" not in hook_text
    assert "evidence_pack_builder" not in hook_text
    assert "dashboard_screen_adapter" not in hook_text
    assert "generate_ai_response" not in hook_text
    assert "llm" not in hook_text.lower()


def test_regeneration_readiness_guard_public_writer_accepts_contract_bundle():
    generate_signature = inspect.signature(html_dashboard.generate_html_dashboard)
    page_builder_signature = inspect.signature(html_dashboard._build_dashboard_pages)

    assert "contract_screen_render_bundle" in generate_signature.parameters
    assert "contract_screen_render_bundle" in page_builder_signature.parameters


def test_current_src_and_script_generation_callers_do_not_pass_contract_bundle():
    production_sources = [
        path
        for root in (ROOT / "src", ROOT / "scripts")
        for path in root.rglob("*.py")
        if path.name != "html_dashboard.py"
    ]
    callers = []
    bundle_usages = []
    for path in production_sources:
        text = path.read_text(encoding="utf-8")
        if "generate_html_dashboard(" in text:
            callers.append(str(path.relative_to(ROOT)))
        if "contract_screen_render_bundle" in text:
            bundle_usages.append(str(path.relative_to(ROOT)))

    assert callers == ["scripts/run_analysis.py"]
    assert bundle_usages == []


def test_artifact_fingerprints_unchanged_after_smoke_page_builder_calls():
    before = _artifact_fingerprints()

    _build_pages(_fragment_mapping("HASH_GUARD"))
    _build_pages(SimpleNamespace(**_fragment_mapping("HASH_OBJECT_GUARD")))
    _build_pages(SimpleNamespace(to_dict=lambda: _fragment_mapping("HASH_DICT_GUARD")))

    after = _artifact_fingerprints()
    assert before == after
