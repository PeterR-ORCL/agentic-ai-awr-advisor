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


def payload(name):
    return {
        "evidence_ids": [f"{name}-evidence"],
        "rows": [{"row_id": f"{name}-row", "metric": name, "value": 7}],
        "metrics": {f"{name}_metric": 7},
        "trends": [{"trend_name": f"{name}-trend", "direction": "flat"}],
        "summary": f"{name} evidence",
    }


def model_for_pack(scope=None, **payloads):
    pack = build_evidence_pack_contract(scope or selected_scope(), provenance="deterministic_builder", **payloads)
    return build_screen4_review_view_model(pack)


def test_screen4_renderer_keeps_review_modes_separate():
    html = render_screen4_review(
        model_for_pack(
            historical_payload=payload("historical"),
            comparative_payload=payload("comparative"),
            deep_analysis_payload=payload("deep"),
        )
    )

    assert "Historical Review" in html
    assert "historical-row" in html
    assert "Comparative Review" in html
    assert "comparative-row" in html
    assert "Deep Analysis" in html
    assert "deep-row" in html
    assert "Diagnostic Snapshot" not in html


def test_screen4_renderer_renders_missing_unavailable_and_stale_per_mode():
    missing = render_screen4_review(
        model_for_pack(comparative_payload=payload("comparative"), deep_analysis_payload=payload("deep"))
    )
    unavailable_scope = selected_scope(
        target_b=ComparisonTargetIdentity(target_id="target-b", alignment_key="other")
    )
    unavailable = render_screen4_review(
        model_for_pack(scope=unavailable_scope, comparative_payload=payload("comparative"))
    )
    stale = render_screen4_review(
        model_for_pack(
            historical_payload=payload("historical"),
            comparative_payload={
                "evidence_ids": ["comparative-evidence"],
                "rows": [{"row_id": "comparative-row"}],
                "stale": True,
            },
            deep_analysis_payload=payload("deep"),
        )
    )

    assert "Missing evidence" in missing
    assert "payload_missing" in missing
    assert "Unavailable evidence" in unavailable
    assert "mode_unavailable" in unavailable
    assert "Stale evidence" in stale
    assert "payload_stale" in stale


def test_screen4_renderer_renders_allowed_visualizations_only_when_present():
    present_html = render_screen4_review(
        model_for_pack(
            historical_payload=payload("historical"),
            comparative_payload=payload("comparative"),
            deep_analysis_payload=payload("deep"),
        )
    )
    missing_html = render_screen4_review(model_for_pack())

    assert "Allowed visualizations" in present_html
    assert "historical evidence table" in present_html
    assert "comparative metric summary" in present_html
    assert "deep_analysis trend" in present_html
    assert "allowed-visualizations" not in missing_html


def test_screen4_renderer_does_not_compute_deltas_or_infer_domains():
    html = render_screen4_review(
        model_for_pack(
            comparative_payload={
                "evidence_ids": ["comparative-evidence"],
                "rows": [{"row_id": "comparative-row", "metric": "known_delta", "value": 5}],
                "metrics": {"known_delta": 5},
                "summary": "comparative evidence",
            }
        )
    )

    assert "known_delta" in html
    assert "computed_delta" not in html
    assert "inferred_domain" not in html
    assert "progressive selector" not in html.lower()
    assert "show everything" not in html.lower()


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


def _imports_for(imported_module):
    tree = ast.parse(Path(imported_module.__file__).read_text())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    return imports
