import ast
import json
from pathlib import Path

from src.reporting.dashboard.adapters.evidence_pack_builder import build_evidence_pack_contract
from src.reporting.dashboard.contracts.evidence_pack_contract import EvidenceDomain
from src.reporting.dashboard.contracts.selected_review_scope_contract import (
    ComparisonTargetIdentity,
    ReviewMode,
    ReviewModeIntent,
    RuntimeScopeIdentity,
    SelectionProvenance,
    SourceMode,
    build_selected_review_scope_contract,
)
from src.reporting.dashboard.view_models import screen4_review_view_model as module
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


def test_screen4_view_model_does_not_mutate_evidence_pack():
    pack = build_evidence_pack_contract(
        selected_scope(),
        historical_payload=payload("historical"),
        comparative_payload=payload("comparative"),
        deep_analysis_payload=payload("deep"),
        provenance="deterministic_builder",
    )
    before = pack.to_dict()

    build_screen4_review_view_model(pack)

    assert pack.to_dict() == before


def test_screen4_review_modes_build_only_from_their_evidence_domains():
    model = model_for_pack(
        historical_payload=payload("historical"),
        comparative_payload=payload("comparative"),
        deep_analysis_payload=payload("deep"),
    )

    assert model.historical_review.domain == EvidenceDomain.HISTORICAL.value
    assert model.historical_review.evidence_rows[0]["row_id"] == "historical-row"
    assert model.comparative_review.domain == EvidenceDomain.COMPARATIVE.value
    assert model.comparative_review.evidence_rows[0]["row_id"] == "comparative-row"
    assert model.deep_analysis.domain == EvidenceDomain.DEEP_ANALYSIS.value
    assert model.deep_analysis.evidence_rows[0]["row_id"] == "deep-row"
    assert "diagnostic-row" not in json.dumps(model.to_dict())


def test_screen4_missing_unavailable_and_stale_states_are_explicit():
    missing = model_for_pack(
        historical_payload=None,
        comparative_payload=payload("comparative"),
        deep_analysis_payload=payload("deep"),
    )
    unavailable_scope = selected_scope(target_b=ComparisonTargetIdentity(target_id="target-b", alignment_key="other"))
    unavailable = model_for_pack(scope=unavailable_scope, comparative_payload=payload("comparative"))
    stale = model_for_pack(
        historical_payload=payload("historical"),
        comparative_payload={"evidence_ids": ["comparative-evidence"], "rows": [{"row_id": "comparative-row"}], "stale": True},
        deep_analysis_payload=payload("deep"),
    )

    assert missing.historical_review.missing_evidence
    assert unavailable.comparative_review.unavailable_evidence
    assert stale.comparative_review.stale_evidence


def test_screen4_visualizations_and_llm_eligibility_are_mode_specific_and_evidence_backed():
    model = model_for_pack(
        historical_payload=payload("historical"),
        comparative_payload=payload("comparative"),
        deep_analysis_payload=payload("deep"),
    )

    assert model.historical_review.allowed_visualizations[0]["domain"] == EvidenceDomain.HISTORICAL.value
    assert model.comparative_review.allowed_visualizations[0]["domain"] == EvidenceDomain.COMPARATIVE.value
    assert model.deep_analysis.allowed_visualizations[0]["domain"] == EvidenceDomain.DEEP_ANALYSIS.value
    assert model.historical_review.llm_explanation_eligibility[0]["source_evidence_ids"]
    assert model.comparative_review.llm_explanation_eligibility[0]["source_evidence_ids"]
    assert model.deep_analysis.llm_explanation_eligibility[0]["source_evidence_ids"]


def test_screen4_view_model_does_not_compute_comparison_deltas_or_use_ui_state():
    model = model_for_pack(
        comparative_payload={
            "evidence_ids": ["comparative-evidence"],
            "rows": [{"row_id": "comparative-row", "metric": "known_delta", "value": 5}],
            "metrics": {"known_delta": 5},
        }
    )
    text = json.dumps(model.to_dict(), sort_keys=True)

    assert "browser_state" not in text
    assert "ui_flags" not in text
    assert "computed_delta" not in text
    assert "known_delta" in text


def test_screen4_view_model_import_purity_and_no_rendered_html():
    source = Path(module.__file__).read_text()
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    forbidden = ("html_dashboard", "renderer", "llm", "awr_dashboard", "browser", "screen3", "selector")
    assert not any(fragment in name.lower() for name in imports for fragment in forbidden)
    model = model_for_pack(historical_payload=payload("historical"))
    assert "<html" not in json.dumps(model.to_dict()).lower()
