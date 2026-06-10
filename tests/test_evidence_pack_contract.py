import ast
import json
from pathlib import Path

from src.reporting.dashboard.adapters.evidence_pack_builder import build_evidence_pack_contract
from src.reporting.dashboard.contracts import evidence_pack_contract as module
from src.reporting.dashboard.contracts.evidence_pack_contract import (
    CONTRACT_TYPE,
    CONTRACT_VERSION,
    EvidenceAvailabilityStatus,
    EvidenceDomain,
    EvidencePackValidationStatus,
    LLMExplanationStatus,
    VisualizationKind,
    evidence_pack_from_dict,
    evidence_pack_to_dict,
    get_allowed_visualizations_by_domain,
    get_llm_explanation_eligibility_by_domain,
    get_missing_evidence_by_domain,
    is_evidence_pack_valid,
    validate_evidence_pack_contract,
)
from src.reporting.dashboard.contracts.selected_review_scope_contract import (
    ComparisonTargetIdentity,
    ReviewMode,
    ReviewModeIntent,
    RuntimeScopeIdentity,
    SelectionProvenance,
    SnapshotWindowIdentity,
    SourceMode,
    build_selected_review_scope_contract,
)


def selected_scope():
    return build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        runtime_scope=RuntimeScopeIdentity(
            scope_id="runtime-1",
            report_id="awr-current",
            database_id="db-prod",
            workload_id="oltp",
            snapshot_window_id="snap-current",
            alignment_key="db-prod",
        ),
        selected_window=SnapshotWindowIdentity(window_id="hist-window"),
        target_a=ComparisonTargetIdentity(target_id="target-a", alignment_key="db-prod"),
        target_b=ComparisonTargetIdentity(target_id="target-b", alignment_key="db-prod"),
        review_mode_intent=ReviewModeIntent(
            requested_modes=(ReviewMode.DEEP_ANALYSIS,),
            historical_evidence_available=True,
            deep_analysis_requested=True,
            deep_analysis_available=True,
        ),
        provenance=SelectionProvenance(source_system="screen2_backend_contract_builder"),
    )


def deterministic_payload(name: str):
    return {
        "evidence_ids": [f"{name}-evidence"],
        "rows": [{"row_id": f"{name}-row", "metric": "db_cpu", "value": 42}],
        "metrics": {"db_cpu": 42},
        "trends": [{"trend_name": f"{name}-trend", "direction": "up", "points": [{"x": 1, "y": 2}]}],
        "anomalies": [{"anomaly_name": f"{name}-anomaly", "severity": "warning"}],
        "similarity_context": [{"context_id": f"{name}-similarity", "similar_case_ids": ["case-1"]}],
        "confidence_basis": [{"basis_id": f"{name}-confidence", "confidence": "high"}],
        "summary": f"{name} deterministic evidence",
    }


def full_pack():
    return build_evidence_pack_contract(
        selected_scope(),
        diagnostic_payload=deterministic_payload("diagnostic"),
        historical_payload=deterministic_payload("historical"),
        comparative_payload=deterministic_payload("comparative"),
        deep_analysis_payload=deterministic_payload("deep"),
        recommendation_action_payload=deterministic_payload("action"),
        learning_governance_payload=deterministic_payload("learning"),
        provenance={"source_system": "deterministic_builder", "builder_version": "test"},
    )


def payload_text(pack) -> str:
    return json.dumps(evidence_pack_to_dict(pack), sort_keys=True)


def test_contract_construction_has_type_version_linkage_id_provenance_and_status():
    pack = full_pack()
    rebuilt = full_pack()

    assert pack.contract_type == CONTRACT_TYPE == "evidence_pack_contract"
    assert pack.contract_version == CONTRACT_VERSION
    assert pack.selected_flow_id == selected_scope().selected_flow_id
    assert pack.source_selected_review_scope_id == selected_scope().selected_flow_id
    assert pack.source_selected_review_scope_contract_type == "selected_review_scope_contract"
    assert pack.evidence_pack_id == rebuilt.evidence_pack_id
    assert pack.evidence_pack_id.startswith("evidence-pack:")
    assert pack.provenance.is_present()
    assert pack.validation_status == EvidencePackValidationStatus.VALID
    assert is_evidence_pack_valid(pack)


def test_contract_separates_all_evidence_domains():
    pack = full_pack()

    assert pack.diagnostic_evidence.availability_status == EvidenceAvailabilityStatus.PRESENT
    assert pack.historical_evidence.availability_status == EvidenceAvailabilityStatus.PRESENT
    assert pack.comparative_evidence.availability_status == EvidenceAvailabilityStatus.PRESENT
    assert pack.deep_analysis_evidence.availability_status == EvidenceAvailabilityStatus.PRESENT
    assert pack.recommendation_action_evidence.availability_status == EvidenceAvailabilityStatus.PRESENT
    assert pack.learning_governance_evidence.availability_status == EvidenceAvailabilityStatus.PRESENT
    assert {row.domain for row in pack.evidence_rows} == set(EvidenceDomain)


def test_contract_helper_queries_missing_visualizations_and_llm_eligibility_by_domain():
    pack = build_evidence_pack_contract(
        selected_scope(),
        diagnostic_payload=None,
        historical_payload=deterministic_payload("historical"),
        comparative_payload=deterministic_payload("comparative"),
        deep_analysis_payload=deterministic_payload("deep"),
        recommendation_action_payload=deterministic_payload("action"),
        learning_governance_payload=deterministic_payload("learning"),
        provenance="deterministic_builder",
    )

    assert get_missing_evidence_by_domain(pack, EvidenceDomain.DIAGNOSTIC)
    assert not get_allowed_visualizations_by_domain(pack, EvidenceDomain.DIAGNOSTIC)
    assert get_allowed_visualizations_by_domain(pack, EvidenceDomain.HISTORICAL)
    diagnostic_llm = get_llm_explanation_eligibility_by_domain(pack, EvidenceDomain.DIAGNOSTIC)
    historical_llm = get_llm_explanation_eligibility_by_domain(pack, EvidenceDomain.HISTORICAL)
    assert diagnostic_llm[0].status == LLMExplanationStatus.BLOCKED
    assert historical_llm[0].status == LLMExplanationStatus.ALLOWED


def test_allowed_visualizations_reference_present_deterministic_evidence_only():
    pack = full_pack()

    for visual in pack.allowed_visualizations:
        assert visual.source_evidence_ids
        domain_evidence_ids = {
            EvidenceDomain.DIAGNOSTIC: pack.diagnostic_evidence.evidence_ids,
            EvidenceDomain.HISTORICAL: pack.historical_evidence.evidence_ids,
            EvidenceDomain.COMPARATIVE: pack.comparative_evidence.evidence_ids,
            EvidenceDomain.DEEP_ANALYSIS: pack.deep_analysis_evidence.evidence_ids,
            EvidenceDomain.RECOMMENDATION_ACTION: pack.recommendation_action_evidence.evidence_ids,
            EvidenceDomain.LEARNING_GOVERNANCE: pack.learning_governance_evidence.evidence_ids,
        }[visual.domain]
        assert set(visual.source_evidence_ids).issubset(set(domain_evidence_ids))
    assert any(visual.kind == VisualizationKind.COMPARISON_DELTA for visual in pack.allowed_visualizations)


def test_serialization_round_trip_preserves_validation_and_deterministic_identity():
    pack = build_evidence_pack_contract(
        selected_scope(),
        diagnostic_payload=None,
        historical_payload=deterministic_payload("historical"),
        comparative_payload=deterministic_payload("comparative"),
        deep_analysis_payload=deterministic_payload("deep"),
        recommendation_action_payload=deterministic_payload("action"),
        learning_governance_payload=deterministic_payload("learning"),
        provenance="deterministic_builder",
    )
    encoded = json.dumps(evidence_pack_to_dict(pack), sort_keys=True)
    restored = evidence_pack_from_dict(json.loads(encoded))

    assert restored.evidence_pack_id == pack.evidence_pack_id
    assert restored.validation_status == pack.validation_status
    assert [item.to_dict() for item in restored.missing_evidence] == [
        item.to_dict() for item in pack.missing_evidence
    ]
    assert validate_evidence_pack_contract(restored).evidence_pack_id == pack.evidence_pack_id


def test_contract_payload_does_not_contain_rendered_html_browser_or_llm_facts():
    pack = full_pack()
    text = payload_text(pack)

    assert "<html" not in text.lower()
    assert "localStorage" not in text
    assert "browser_state" not in text
    assert "generated_html" not in text
    assert "llm_facts" not in text
    assert "llm_generated_evidence" not in text


def test_import_purity_for_evidence_pack_contract():
    source = Path(module.__file__).read_text()
    tree = ast.parse(source)
    imported_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_names.append(node.module or "")

    forbidden_fragments = ("html_dashboard", "renderer", "llm", "awr_dashboard", "browser")
    assert not any(fragment in name.lower() for name in imported_names for fragment in forbidden_fragments)
    assert set(imported_names).issubset(
        {
            "__future__",
            "hashlib",
            "json",
            "collections.abc",
            "dataclasses",
            "enum",
            "typing",
            "src.reporting.dashboard.contracts.selected_review_scope_contract",
        }
    )

