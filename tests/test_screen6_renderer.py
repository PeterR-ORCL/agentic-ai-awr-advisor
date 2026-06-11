import ast
from pathlib import Path

from src.reporting.dashboard.adapters.evidence_pack_builder import build_evidence_pack_contract
from src.reporting.dashboard.contracts.selected_review_scope_contract import (
    RuntimeScopeIdentity,
    SelectionProvenance,
    SourceMode,
    build_selected_review_scope_contract,
)
from src.reporting.dashboard.renderers import screen6_renderer as module
from src.reporting.dashboard.renderers.screen6_renderer import render_screen6_learning
from src.reporting.dashboard.view_models.screen6_learning_view_model import build_screen6_learning_view_model


def selected_scope():
    return build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        runtime_scope=RuntimeScopeIdentity(scope_id="runtime-1", alignment_key="db-prod"),
        provenance=SelectionProvenance(source_system="screen2_backend_contract_builder"),
    )


def learning_payload():
    return {
        "evidence_ids": ["learning-evidence"],
        "rows": [
            {
                "row_id": "learning-row",
                "learning_candidate": "candidate-1",
                "governance_status": "pending_review",
                "memory_policy": "approval_required",
                "approval_boundary": "human_gate",
                "activation_boundary": "not_active",
            }
        ],
        "confidence_basis": [{"basis_id": "learning-confidence", "confidence": "medium"}],
        "summary": "Learning governance evidence <script>alert(1)</script>",
    }


def learning_model(**payloads):
    pack = build_evidence_pack_contract(selected_scope(), provenance="deterministic_builder", **payloads)
    return build_screen6_learning_view_model(pack)


def test_screen6_renderer_renders_learning_governance_evidence():
    html = render_screen6_learning(learning_model(learning_governance_payload=learning_payload()))

    assert "Learning / Governance" in html
    assert "learning-row" in html
    assert "candidate-1" in html
    assert "pending_review" in html
    assert "approval_required" in html
    assert "human_gate" in html
    assert "<script" not in html.lower()
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_screen6_renderer_renders_missing_unavailable_and_stale_governance_states():
    missing = render_screen6_learning(learning_model())
    unavailable = render_screen6_learning(
        learning_model(learning_governance_payload={"llm_text": "approve", "rows": [{"row_id": "x"}]})
    )
    stale = render_screen6_learning(
        learning_model(
            learning_governance_payload={
                "evidence_ids": ["learning-evidence"],
                "rows": [{"row_id": "learning-row", "learning_candidate": "candidate-1"}],
                "stale": True,
            }
        )
    )

    assert "Missing evidence" in missing
    assert "payload_missing" in missing
    assert "Unavailable evidence" in unavailable
    assert "payload_rejected" in unavailable
    assert "approve" not in unavailable
    assert "Stale evidence" in stale
    assert "payload_stale" in stale


def test_screen6_renderer_does_not_activate_learning_or_render_llm_governance():
    html = render_screen6_learning(learning_model(learning_governance_payload={"llm_text": "activate"}))

    assert "activate" not in html
    assert "activate_learning" not in html
    assert "activated" not in html
    assert "Learning candidates" not in html
    assert "llm_text" not in html


def test_screen6_renderer_import_boundary():
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


def _imports_for(imported_module):
    tree = ast.parse(Path(imported_module.__file__).read_text())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    return imports
