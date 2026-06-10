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
from src.reporting.dashboard.view_models import screen5_action_view_model as module
from src.reporting.dashboard.view_models.screen5_action_view_model import build_screen5_action_view_model


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
                "recommendation": "Add deterministic capacity",
                "action": "scale_db_cpu",
                "outcome": "reduced pressure",
                "risk": "medium",
                "impact": "high",
            }
        ],
        "confidence_basis": [{"basis_id": "action-confidence", "confidence": "medium"}],
        "summary": "Action evidence",
    }


def action_model(**payloads):
    pack = build_evidence_pack_contract(selected_scope(), provenance="deterministic_builder", **payloads)
    return build_screen5_action_view_model(pack)


def test_screen5_view_model_does_not_mutate_evidence_pack():
    pack = build_evidence_pack_contract(
        selected_scope(),
        recommendation_action_payload=action_payload(),
        provenance="deterministic_builder",
    )
    before = pack.to_dict()

    build_screen5_action_view_model(pack)

    assert pack.to_dict() == before


def test_screen5_view_model_builds_from_recommendation_action_evidence():
    model = action_model(recommendation_action_payload=action_payload())

    assert model.screen_id == "screen5_recommendation_action"
    assert model.availability_status == "present"
    assert model.action_rows[0]["row_id"] == "action-row"
    assert model.recommendation_fields
    assert model.risk_fields
    assert model.impact_fields
    assert model.confidence_basis


def test_screen5_missing_unavailable_and_stale_action_evidence_are_explicit():
    missing = action_model()
    unavailable = action_model(recommendation_action_payload={"llm_recommendation": "invented", "rows": [{"row_id": "x"}]})
    stale = action_model(
        recommendation_action_payload={
            "evidence_ids": ["action-evidence"],
            "rows": [{"row_id": "action-row", "recommendation": "deterministic"}],
            "stale": True,
        }
    )

    assert missing.availability_status == "missing"
    assert missing.missing_evidence
    assert unavailable.availability_status == "unavailable"
    assert unavailable.unavailable_evidence
    assert stale.availability_status == "stale"
    assert stale.stale_evidence


def test_screen5_llm_eligibility_does_not_create_recommendations():
    model = action_model()
    text = json.dumps(model.to_dict(), sort_keys=True)

    assert model.llm_explanation_eligibility[0]["status"] == "blocked"
    assert not model.recommendation_fields
    assert "llm_recommendation" not in text


def test_screen5_view_model_excludes_non_action_domains():
    model = action_model(
        diagnostic_payload={
            "evidence_ids": ["diagnostic-evidence"],
            "rows": [{"row_id": "diagnostic-row", "recommendation": "not an action"}],
        },
        recommendation_action_payload=action_payload(),
    )
    text = json.dumps(model.to_dict(), sort_keys=True)

    assert "action-row" in text
    assert "diagnostic-row" not in text


def test_screen5_view_model_import_purity_and_no_rendered_html_or_ui_state():
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
    model = action_model(recommendation_action_payload=action_payload())
    text = json.dumps(model.to_dict()).lower()
    assert "<html" not in text
    assert "browser_state" not in text
