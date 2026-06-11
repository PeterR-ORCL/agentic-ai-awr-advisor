import inspect
from types import SimpleNamespace

from src.reporting import html_dashboard


def report_data():
    return {
        "title": "Contract Hook Test Dashboard",
        "generated_at": "2026-06-10T00:00:00",
        "screen_models": {},
    }


def fragment_bundle():
    return SimpleNamespace(
        screen3_html='<section id="contract-screen3">CONTRACT_SCREEN3_FRAGMENT</section>',
        screen4_html='<section id="contract-screen4">CONTRACT_SCREEN4_FRAGMENT</section>',
        screen5_html='<section id="contract-screen5">CONTRACT_SCREEN5_FRAGMENT</section>',
        screen6_html='<section id="contract-screen6">CONTRACT_SCREEN6_FRAGMENT</section>',
    )


def pages_with_bundle(bundle=None):
    return html_dashboard._build_dashboard_pages(
        report_data(),
        contract_screen_render_bundle=bundle,
    )


def test_contract_bundle_places_each_screen_fragment_on_its_assigned_page():
    pages = pages_with_bundle(fragment_bundle())

    assert "CONTRACT_SCREEN3_FRAGMENT" in pages["screen_3_analysis.html"]
    assert "CONTRACT_SCREEN4_FRAGMENT" not in pages["screen_3_analysis.html"]
    assert "CONTRACT_SCREEN5_FRAGMENT" not in pages["screen_3_analysis.html"]
    assert "CONTRACT_SCREEN6_FRAGMENT" not in pages["screen_3_analysis.html"]

    assert "CONTRACT_SCREEN4_FRAGMENT" in pages["screen_4_historical_review.html"]
    assert "CONTRACT_SCREEN3_FRAGMENT" not in pages["screen_4_historical_review.html"]
    assert "CONTRACT_SCREEN5_FRAGMENT" not in pages["screen_4_historical_review.html"]
    assert "CONTRACT_SCREEN6_FRAGMENT" not in pages["screen_4_historical_review.html"]

    assert "CONTRACT_SCREEN5_FRAGMENT" in pages["screen_5_recommendation_action.html"]
    assert "CONTRACT_SCREEN3_FRAGMENT" not in pages["screen_5_recommendation_action.html"]
    assert "CONTRACT_SCREEN4_FRAGMENT" not in pages["screen_5_recommendation_action.html"]
    assert "CONTRACT_SCREEN6_FRAGMENT" not in pages["screen_5_recommendation_action.html"]

    assert "CONTRACT_SCREEN6_FRAGMENT" in pages["screen_6_fleet_overview.html"]
    assert "CONTRACT_SCREEN3_FRAGMENT" not in pages["screen_6_fleet_overview.html"]
    assert "CONTRACT_SCREEN4_FRAGMENT" not in pages["screen_6_fleet_overview.html"]
    assert "CONTRACT_SCREEN5_FRAGMENT" not in pages["screen_6_fleet_overview.html"]


def test_contract_bundle_fragments_bypass_legacy_downstream_evidence_gate():
    pages = pages_with_bundle(fragment_bundle())

    for page_name in (
        "screen_3_analysis.html",
        "screen_4_historical_review.html",
        "screen_5_recommendation_action.html",
        "screen_6_fleet_overview.html",
    ):
        assert "Evidence Handoff Required" not in pages[page_name]
        assert 'hidden>\n      <section id="contract-' not in pages[page_name]


def test_mapping_and_to_dict_fragment_sources_are_supported_without_shell_authority():
    mapping_pages = pages_with_bundle(
        {
            "screen3_html": "<section>MAP_SCREEN3</section>",
            "screen4_html": "<section>MAP_SCREEN4</section>",
            "screen5_html": "<section>MAP_SCREEN5</section>",
            "screen6_html": "<section>MAP_SCREEN6</section>",
        }
    )
    dict_bundle = SimpleNamespace(
        to_dict=lambda: {
            "screen3_html": "<section>DICT_SCREEN3</section>",
            "screen4_html": "<section>DICT_SCREEN4</section>",
            "screen5_html": "<section>DICT_SCREEN5</section>",
            "screen6_html": "<section>DICT_SCREEN6</section>",
        }
    )
    dict_pages = pages_with_bundle(dict_bundle)

    assert "MAP_SCREEN3" in mapping_pages["screen_3_analysis.html"]
    assert "MAP_SCREEN4" in mapping_pages["screen_4_historical_review.html"]
    assert "MAP_SCREEN5" in mapping_pages["screen_5_recommendation_action.html"]
    assert "MAP_SCREEN6" in mapping_pages["screen_6_fleet_overview.html"]
    assert "DICT_SCREEN3" in dict_pages["screen_3_analysis.html"]
    assert "DICT_SCREEN4" in dict_pages["screen_4_historical_review.html"]
    assert "DICT_SCREEN5" in dict_pages["screen_5_recommendation_action.html"]
    assert "DICT_SCREEN6" in dict_pages["screen_6_fleet_overview.html"]


def test_legacy_fallback_still_returns_downstream_pages_without_contract_bundle(monkeypatch):
    monkeypatch.setattr(html_dashboard, "_render_screen_2_page", lambda *args, **kwargs: "LEGACY_SCREEN3")
    monkeypatch.setattr(html_dashboard, "_render_screen_4_page", lambda *args, **kwargs: "LEGACY_SCREEN4")
    monkeypatch.setattr(html_dashboard, "_render_screen_5_page", lambda *args, **kwargs: "LEGACY_SCREEN5")
    monkeypatch.setattr(html_dashboard, "_render_screen_6_page", lambda *args, **kwargs: "LEGACY_SCREEN6")

    pages = pages_with_bundle()

    expected = {
        "screen_3_analysis.html": "LEGACY_SCREEN3",
        "screen_4_historical_review.html": "LEGACY_SCREEN4",
        "screen_5_recommendation_action.html": "LEGACY_SCREEN5",
        "screen_6_fleet_overview.html": "LEGACY_SCREEN6",
    }
    for page_name, marker in expected.items():
        assert page_name in pages
        assert marker in pages[page_name]
        assert "Evidence Handoff Required" in pages[page_name]
        assert "CONTRACT_SCREEN" not in pages[page_name]


def test_generate_html_dashboard_accepts_explicit_contract_bundle_parameter():
    signature = inspect.signature(html_dashboard.generate_html_dashboard)

    assert "contract_screen_render_bundle" in signature.parameters


def test_contract_hook_does_not_read_generated_html_or_browser_state():
    hook_source = inspect.getsource(html_dashboard._contract_screen_render_fragments)
    page_builder_source = inspect.getsource(html_dashboard._build_dashboard_pages)
    hook_text = hook_source + page_builder_source

    assert "read_text" not in hook_text
    assert "open(" not in hook_text
    assert "awr_dashboard" not in hook_text
    assert "localStorage" not in hook_text
    assert "hash_state" not in hook_text
    assert "browser_state" not in hook_text


def test_contract_hook_does_not_compute_evidence_or_call_llm():
    hook_source = inspect.getsource(html_dashboard._contract_screen_render_fragments)
    page_builder_source = inspect.getsource(html_dashboard._build_dashboard_pages)
    hook_text = hook_source + page_builder_source

    assert "build_evidence_pack_contract" not in hook_text
    assert "build_selected_review_scope_contract" not in hook_text
    assert "evidence_pack_builder" not in hook_text
    assert "generate_ai_response" not in hook_text
    assert "ai_provider" not in hook_text


def test_contract_hook_does_not_duplicate_screen_renderer_functions():
    hook_source = inspect.getsource(html_dashboard._contract_screen_render_fragments)
    page_builder_source = inspect.getsource(html_dashboard._build_dashboard_pages)
    hook_text = hook_source + page_builder_source

    assert "render_screen3_diagnostic" not in hook_text
    assert "render_screen4_review" not in hook_text
    assert "render_screen5_action" not in hook_text
    assert "render_screen6_learning" not in hook_text
