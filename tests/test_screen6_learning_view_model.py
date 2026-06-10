import ast
import json
from pathlib import Path

from src.reporting.dashboard.adapters.evidence_pack_builder import build_evidence_pack_contract
from src.reporting.dashboard.contracts.selected_review_scope_contract import (
    RuntimeScopeIdentity,
    SelectionProvenance,
    SourceMode,
    build_selected_review_scope_contract,
)
from src.reporting.dashboard.view_models import screen6_learning_view_model as module
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
        "summary": "Learning governance evidence",
    }


def learning_model(**payloads):
    pack = build_evidence_pack_contract(selected_scope(), provenance="deterministic_builder", **payloads)
    return build_screen6_learning_view_model(pack)


def test_screen6_view_model_does_not_mutate_evidence_pack():
    pack = build_evidence_pack_contract(
        selected_scope(),
        learning_governance_payload=learning_payload(),
        provenance="deterministic_builder",
    )
    before = pack.to_dict()

    build_screen6_learning_view_model(pack)

    assert pack.to_dict() == before


def test_screen6_view_model_builds_from_learning_governance_evidence():
    model = learning_model(learning_governance_payload=learning_payload())

    assert model.screen_id == "screen6_learning_governance"
    assert model.availability_status == "present"
    assert model.governance_rows[0]["row_id"] == "learning-row"
    assert model.learning_candidates
    assert model.governance_status
    assert model.memory_policy
    assert model.approval_boundaries
    assert model.confidence_basis


def test_screen6_missing_unavailable_and_stale_governance_evidence_are_explicit():
    missing = learning_model()
    unavailable = learning_model(learning_governance_payload={"llm_text": "approve", "rows": [{"row_id": "x"}]})
    stale = learning_model(
        learning_governance_payload={
            "evidence_ids": ["learning-evidence"],
            "rows": [{"row_id": "learning-row", "learning_candidate": "candidate-1"}],
            "stale": True,
        }
    )

    assert missing.availability_status == "missing"
    assert missing.missing_evidence
    assert unavailable.availability_status == "unavailable"
    assert unavailable.unavailable_evidence
    assert stale.availability_status == "stale"
    assert stale.stale_evidence


def test_screen6_llm_eligibility_does_not_create_learning_evidence_or_activation():
    model = learning_model()
    text = json.dumps(model.to_dict(), sort_keys=True).lower()

    assert model.llm_explanation_eligibility[0]["status"] == "blocked"
    assert not model.learning_candidates
    assert "llm_text" not in text
    assert "activate_learning" not in text
    assert "activated" not in text


def test_screen6_view_model_excludes_non_learning_domains():
    model = learning_model(
        diagnostic_payload={
            "evidence_ids": ["diagnostic-evidence"],
            "rows": [{"row_id": "diagnostic-row", "learning_candidate": "not governance"}],
        },
        learning_governance_payload=learning_payload(),
    )
    text = json.dumps(model.to_dict(), sort_keys=True)

    assert "learning-row" in text
    assert "diagnostic-row" not in text


def test_screen6_view_model_import_purity_and_no_rendered_html_or_ui_state():
    source = Path(module.__file__).read_text()
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    forbidden = ("html_dashboard", "renderer", "llm", "awr_dashboard", "browser", "selector")
    assert not any(fragment in name.lower() for name in imports for fragment in forbidden)
    model = learning_model(learning_governance_payload=learning_payload())
    text = json.dumps(model.to_dict()).lower()
    assert "<html" not in text
    assert "browser_state" not in text
