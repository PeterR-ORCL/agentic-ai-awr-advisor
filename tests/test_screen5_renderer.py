import ast
from pathlib import Path

from src.reporting.dashboard.adapters.evidence_pack_builder import build_evidence_pack_contract
from src.reporting.dashboard.contracts.selected_review_scope_contract import (
    RuntimeScopeIdentity,
    SelectionProvenance,
    SourceMode,
    build_selected_review_scope_contract,
)
from src.reporting.dashboard.renderers import screen5_renderer as module
from src.reporting.dashboard.renderers.screen5_renderer import render_screen5_action
from src.reporting.dashboard.view_models.screen5_action_view_model import build_screen5_action_view_model


RAW_DUMP_MARKERS = (
    "<pre",
    "{ domain:",
    "{ row_id:",
    "values:",
    "source_evidence_ids:",
    "visualization_id:",
    "Allowed visualizations",
    "CONTRACT_SCREEN5_SMOKE_FRAGMENT",
)


def selected_scope():
    return build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        runtime_scope=RuntimeScopeIdentity(scope_id="runtime-1", alignment_key="db-prod"),
        provenance=SelectionProvenance(source_system="screen2_backend_contract_builder"),
    )


def action_payload():
    return {
        "evidence_ids": ["action-evidence"],
        "rows": [
            {
                "row_id": "action-row",
                "values": {
                    "recommendation": "Add deterministic capacity",
                    "action": "scale_db_cpu",
                    "outcome": "reduced pressure",
                    "risk": "medium",
                    "impact": "high",
                },
            }
        ],
        "confidence_basis": [{"basis_id": "action-confidence", "confidence": "medium"}],
        "summary": "Action evidence <script>alert(1)</script>",
    }


def action_model(**payloads):
    pack = build_evidence_pack_contract(selected_scope(), provenance="deterministic_builder", **payloads)
    return build_screen5_action_view_model(pack)


def test_screen5_renderer_renders_recommendation_action_cards():
    html = render_screen5_action(action_model(recommendation_action_payload=action_payload()))

    assert "Recommendation / Action" in html
    assert "Recommendation/action posture" in html
    assert "Recommendation/action cards" in html
    assert "Add deterministic capacity" in html
    assert "scale_db_cpu" in html
    assert "medium" in html
    assert "high" in html
    assert "<script" not in html.lower()
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    _assert_no_raw_dump(html)


def test_screen5_renderer_renders_explicit_missing_action_evidence():
    html = render_screen5_action(action_model())

    assert "Recommendation/action evidence missing" in html
    assert "Missing evidence" in html
    assert "payload_missing" in html
    _assert_no_raw_dump(html)


def test_screen5_renderer_does_not_render_llm_text_as_recommendation():
    html = render_screen5_action(
        action_model(recommendation_action_payload={"llm_recommendation": "LLM says scale now"})
    )

    assert "LLM says scale now" not in html
    assert "llm_recommendation" not in html
    assert "Recommendation/action cards" not in html
    assert "Unavailable evidence" in html
    _assert_no_raw_dump(html)


def test_screen5_renderer_renders_stale_action_state_without_raw_dump():
    html = render_screen5_action(
        action_model(
            recommendation_action_payload={
                "evidence_ids": ["action-evidence"],
                "rows": [{"row_id": "action-row", "recommendation": "deterministic"}],
                "stale": True,
            }
        )
    )

    assert "Stale evidence" in html
    assert "payload_stale" in html
    _assert_no_raw_dump(html)


def test_screen5_renderer_import_boundary():
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
        "runtime",
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
