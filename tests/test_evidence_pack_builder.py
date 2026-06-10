import ast
import json
from pathlib import Path

import pytest

from src.reporting.dashboard.adapters import evidence_pack_builder as builder_module
from src.reporting.dashboard.adapters.evidence_pack_builder import build_evidence_pack_contract
from src.reporting.dashboard.contracts.evidence_pack_contract import (
    EvidenceAvailabilityStatus,
    EvidenceDomain,
    EvidencePackValidationStatus,
    LLMExplanationStatus,
    get_allowed_visualizations_by_domain,
    get_llm_explanation_eligibility_by_domain,
    get_missing_evidence_by_domain,
)
from src.reporting.dashboard.contracts.selected_review_scope_contract import (
    CacheContinuityStatus,
    ComparisonTargetIdentity,
    ReviewMode,
    ReviewModeIntent,
    RuntimeScopeIdentity,
    SelectionProvenance,
    SourceMode,
    build_selected_review_scope_contract,
)


def provenance():
    return SelectionProvenance(source_system="screen2_backend_contract_builder")


def runtime_scope(alignment_key="db-prod"):
    return RuntimeScopeIdentity(
        scope_id="runtime-1",
        report_id="awr-current",
        database_id="db-prod",
        workload_id="oltp",
        snapshot_window_id="snap-current",
        alignment_key=alignment_key,
    )


def target(name, alignment_key="db-prod"):
    return ComparisonTargetIdentity(target_id=name, report_id=f"awr-{name}", alignment_key=alignment_key)


def scope_runtime_only(**overrides):
    payload = {
        "source_mode": SourceMode.EXISTING_EVIDENCE,
        "runtime_scope": runtime_scope(),
        "provenance": provenance(),
    }
    payload.update(overrides)
    return build_selected_review_scope_contract(**payload)


def scope_full(**overrides):
    payload = {
        "source_mode": SourceMode.EXISTING_EVIDENCE,
        "runtime_scope": runtime_scope(),
        "target_a": target("target-a"),
        "target_b": target("target-b"),
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


def deterministic_payload(name):
    return {
        "evidence_ids": [f"{name}-evidence"],
        "rows": [{"row_id": f"{name}-row", "metric": "db_cpu", "value": 42}],
        "metrics": {"db_cpu": 42},
        "summary": f"{name} deterministic evidence",
    }


def full_payloads():
    return {
        "diagnostic_payload": deterministic_payload("diagnostic"),
        "historical_payload": deterministic_payload("historical"),
        "comparative_payload": deterministic_payload("comparative"),
        "deep_analysis_payload": deterministic_payload("deep"),
        "recommendation_action_payload": deterministic_payload("action"),
        "learning_governance_payload": deterministic_payload("learning"),
        "provenance": "deterministic_builder",
    }


def codes(items):
    return {item.reason_code for item in items}


def error_codes(pack):
    return {issue.code for issue in pack.validation_errors}


def test_builder_requires_selected_scope_contract():
    with pytest.raises(ValueError):
        build_evidence_pack_contract(None)  # type: ignore[arg-type]


def test_invalid_selected_scope_yields_invalid_pack_and_no_evidence_from_payloads():
    invalid_scope = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        target_a=target("target-a"),
        provenance=provenance(),
    )

    pack = build_evidence_pack_contract(
        invalid_scope,
        diagnostic_payload=deterministic_payload("diagnostic"),
        provenance="deterministic_builder",
    )

    assert pack.validation_status == EvidencePackValidationStatus.INVALID
    assert pack.diagnostic_evidence.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE
    assert "selected_scope_invalid" in error_codes(pack)
    assert all(item.reason_code == "selected_scope_invalid" for item in pack.unavailable_evidence)


def test_evidence_pack_links_to_selected_scope_and_does_not_mutate_it():
    selected_scope = scope_full()
    before = selected_scope.to_dict()

    pack = build_evidence_pack_contract(selected_scope, **full_payloads())

    assert pack.selected_flow_id == selected_scope.selected_flow_id
    assert pack.source_selected_review_scope_id == selected_scope.selected_flow_id
    assert selected_scope.to_dict() == before


def test_diagnostic_payload_is_allowed_when_runtime_scope_is_eligible():
    pack = build_evidence_pack_contract(
        scope_runtime_only(),
        diagnostic_payload=deterministic_payload("diagnostic"),
        provenance="deterministic_builder",
    )

    assert pack.diagnostic_evidence.availability_status == EvidenceAvailabilityStatus.PRESENT
    assert not get_missing_evidence_by_domain(pack, EvidenceDomain.DIAGNOSTIC)
    assert pack.comparative_evidence.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE


def test_missing_diagnostic_payload_creates_missing_evidence_not_fallback_copy():
    pack = build_evidence_pack_contract(scope_runtime_only(), provenance="deterministic_builder")

    missing = get_missing_evidence_by_domain(pack, EvidenceDomain.DIAGNOSTIC)
    assert missing
    assert missing[0].reason_code == "payload_missing"
    assert "fallback" not in json.dumps(pack.to_dict()).lower()


def test_target_a_b_without_runtime_scope_cannot_create_diagnostic_evidence():
    selected_scope = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        target_a=target("target-a"),
        target_b=target("target-b"),
        provenance=provenance(),
    )

    pack = build_evidence_pack_contract(
        selected_scope,
        diagnostic_payload=deterministic_payload("diagnostic"),
        provenance="deterministic_builder",
    )

    assert pack.validation_status == EvidencePackValidationStatus.INVALID
    assert pack.diagnostic_evidence.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE


def test_diagnostic_evidence_does_not_include_comparative_deltas():
    pack = build_evidence_pack_contract(
        scope_runtime_only(),
        diagnostic_payload={
            "evidence_ids": ["diagnostic-evidence"],
            "rows": [{"row_id": "diagnostic-row", "metric": "db_cpu", "value": 42}],
            "metrics": {"db_cpu": 42},
        },
        provenance="deterministic_builder",
    )

    diagnostic_text = json.dumps(pack.diagnostic_evidence.to_dict(), sort_keys=True)
    assert "comparison_delta" not in diagnostic_text
    assert "target-a" not in diagnostic_text
    assert "target-b" not in diagnostic_text


def test_comparative_evidence_requires_selected_scope_comparative_eligibility():
    pack = build_evidence_pack_contract(
        scope_runtime_only(),
        comparative_payload=deterministic_payload("comparative"),
        provenance="deterministic_builder",
    )

    assert pack.comparative_evidence.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE
    assert any(item.domain == EvidenceDomain.COMPARATIVE for item in pack.unavailable_evidence)


def test_aligned_runtime_scope_and_targets_allow_comparative_evidence():
    pack = build_evidence_pack_contract(
        scope_full(),
        comparative_payload=deterministic_payload("comparative"),
        diagnostic_payload=deterministic_payload("diagnostic"),
        historical_payload=deterministic_payload("historical"),
        deep_analysis_payload=deterministic_payload("deep"),
        recommendation_action_payload=deterministic_payload("action"),
        learning_governance_payload=deterministic_payload("learning"),
        provenance="deterministic_builder",
    )

    assert pack.comparative_evidence.availability_status == EvidenceAvailabilityStatus.PRESENT
    assert get_allowed_visualizations_by_domain(pack, EvidenceDomain.COMPARATIVE)


def test_mismatch_target_alignment_blocks_comparative_evidence():
    selected_scope = scope_full(target_b=target("target-b", alignment_key="db-other"))

    pack = build_evidence_pack_contract(
        selected_scope,
        comparative_payload=deterministic_payload("comparative"),
        provenance="deterministic_builder",
    )

    assert pack.comparative_evidence.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE
    assert any(item.domain == EvidenceDomain.COMPARATIVE for item in pack.unavailable_evidence)


def test_comparative_evidence_does_not_make_screen3_comparative():
    pack = build_evidence_pack_contract(scope_full(), **full_payloads())

    text = json.dumps(pack.to_dict(), sort_keys=True)
    assert "screen3_comparison" not in text
    assert "screen3" not in text


def test_historical_evidence_requires_historical_eligibility_and_payload():
    unavailable = build_evidence_pack_contract(
        scope_runtime_only(),
        historical_payload=deterministic_payload("historical"),
        provenance="deterministic_builder",
    )
    eligible_missing = build_evidence_pack_contract(
        scope_runtime_only(review_mode_intent=ReviewModeIntent(historical_evidence_available=True)),
        provenance="deterministic_builder",
    )

    assert unavailable.historical_evidence.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE
    assert get_missing_evidence_by_domain(eligible_missing, EvidenceDomain.HISTORICAL)


def test_ui_flags_cannot_create_historical_evidence():
    selected_scope = scope_runtime_only(review_mode_intent={"ui_flags": {"historical": True}})

    pack = build_evidence_pack_contract(
        selected_scope,
        historical_payload=deterministic_payload("historical"),
        provenance="deterministic_builder",
    )

    assert pack.historical_evidence.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE


def test_deep_analysis_requires_explicit_eligibility_and_payload():
    not_eligible = build_evidence_pack_contract(
        scope_runtime_only(),
        deep_analysis_payload=deterministic_payload("deep"),
        provenance="deterministic_builder",
    )
    eligible_missing = build_evidence_pack_contract(
        scope_runtime_only(
            review_mode_intent=ReviewModeIntent(
                requested_modes=(ReviewMode.DEEP_ANALYSIS,),
                deep_analysis_requested=True,
                deep_analysis_available=True,
            )
        ),
        provenance="deterministic_builder",
    )

    assert not_eligible.deep_analysis_evidence.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE
    assert get_missing_evidence_by_domain(eligible_missing, EvidenceDomain.DEEP_ANALYSIS)


def test_ui_filters_are_rejected_as_deep_analysis_evidence():
    pack = build_evidence_pack_contract(
        scope_full(),
        deep_analysis_payload={"ui_flags": {"selected_metric": "cpu"}, "rows": [{"row_id": "deep-row"}]},
        provenance="deterministic_builder",
    )

    assert pack.deep_analysis_evidence.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE
    assert "non_authoritative_payload_rejected" in error_codes(pack)


def test_deterministic_recommendation_action_payload_can_be_included():
    pack = build_evidence_pack_contract(
        scope_runtime_only(),
        diagnostic_payload=deterministic_payload("diagnostic"),
        recommendation_action_payload=deterministic_payload("action"),
        provenance="deterministic_builder",
    )

    assert pack.recommendation_action_evidence.availability_status == EvidenceAvailabilityStatus.PRESENT


def test_llm_recommendation_is_rejected_as_action_evidence():
    pack = build_evidence_pack_contract(
        scope_runtime_only(),
        recommendation_action_payload={"llm_recommendation": "do something", "rows": [{"row_id": "action-row"}]},
        provenance="deterministic_builder",
    )

    assert pack.recommendation_action_evidence.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE
    assert "non_authoritative_payload_rejected" in error_codes(pack)


def test_deterministic_learning_governance_payload_can_be_included():
    pack = build_evidence_pack_contract(
        scope_runtime_only(),
        diagnostic_payload=deterministic_payload("diagnostic"),
        learning_governance_payload=deterministic_payload("learning"),
        provenance="deterministic_builder",
    )

    assert pack.learning_governance_evidence.availability_status == EvidenceAvailabilityStatus.PRESENT


def test_llm_learning_text_is_rejected_as_governance_evidence():
    pack = build_evidence_pack_contract(
        scope_runtime_only(),
        learning_governance_payload={"llm_text": "approve this", "rows": [{"row_id": "learning-row"}]},
        provenance="deterministic_builder",
    )

    assert pack.learning_governance_evidence.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE
    assert "non_authoritative_payload_rejected" in error_codes(pack)


def test_missing_unavailable_and_stale_evidence_are_explicit_by_domain():
    pack = build_evidence_pack_contract(
        scope_full(),
        diagnostic_payload={"evidence_ids": ["diagnostic-evidence"], "stale": True, "rows": [{"row_id": "d"}]},
        historical_payload=None,
        comparative_payload=deterministic_payload("comparative"),
        deep_analysis_payload=deterministic_payload("deep"),
        recommendation_action_payload=deterministic_payload("action"),
        learning_governance_payload=deterministic_payload("learning"),
        provenance="deterministic_builder",
    )

    assert any(item.domain == EvidenceDomain.DIAGNOSTIC for item in pack.stale_evidence)
    assert any(item.domain == EvidenceDomain.HISTORICAL for item in pack.missing_evidence)
    assert pack.validation_status == EvidencePackValidationStatus.PARTIAL


def test_no_visualization_allowed_for_missing_evidence_and_chart_markup_is_rejected():
    missing_pack = build_evidence_pack_contract(scope_runtime_only(), provenance="deterministic_builder")
    rejected_pack = build_evidence_pack_contract(
        scope_runtime_only(),
        diagnostic_payload={"chart_markup": "<svg></svg>", "rows": [{"row_id": "diagnostic-row"}]},
        provenance="deterministic_builder",
    )

    assert not get_allowed_visualizations_by_domain(missing_pack, EvidenceDomain.DIAGNOSTIC)
    assert rejected_pack.diagnostic_evidence.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE
    assert "non_authoritative_payload_rejected" in error_codes(rejected_pack)


def test_generated_html_and_browser_state_are_rejected_as_evidence_authority():
    pack = build_evidence_pack_contract(
        scope_runtime_only(),
        diagnostic_payload={
            "generated_html_path": "awr_dashboard/screen_3_analysis.html",
            "browser_state": {"selected": True},
            "rows": [{"row_id": "diagnostic-row"}],
        },
        provenance="deterministic_builder",
    )

    assert pack.diagnostic_evidence.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE
    text = json.dumps(pack.to_dict(), sort_keys=True)
    assert "awr_dashboard/screen_3_analysis.html" not in text
    assert "browser_state" not in text


def test_llm_explanation_eligibility_only_references_present_deterministic_evidence():
    present = build_evidence_pack_contract(
        scope_runtime_only(),
        diagnostic_payload=deterministic_payload("diagnostic"),
        provenance="deterministic_builder",
    )
    missing = build_evidence_pack_contract(scope_runtime_only(), provenance="deterministic_builder")

    present_llm = get_llm_explanation_eligibility_by_domain(present, EvidenceDomain.DIAGNOSTIC)[0]
    missing_llm = get_llm_explanation_eligibility_by_domain(missing, EvidenceDomain.DIAGNOSTIC)[0]
    assert present_llm.status == LLMExplanationStatus.ALLOWED
    assert present_llm.source_evidence_ids == present.diagnostic_evidence.evidence_ids
    assert missing_llm.status == LLMExplanationStatus.BLOCKED
    text = json.dumps(present.to_dict()).lower()
    assert "llm_facts" not in text
    assert "llm_generated_evidence" not in text
    assert "llm_recommendation" not in text


def test_cache_continuity_does_not_create_evidence():
    selected_scope = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        cache_continuity={"status": CacheContinuityStatus.DISPLAY_ONLY.value, "displayed_scope_id": "runtime-1"},
        provenance=provenance(),
    )

    pack = build_evidence_pack_contract(selected_scope, provenance="deterministic_builder")

    assert pack.validation_status == EvidencePackValidationStatus.INVALID
    assert pack.diagnostic_evidence.availability_status == EvidenceAvailabilityStatus.UNAVAILABLE


def test_builder_import_purity():
    source = Path(builder_module.__file__).read_text()
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
            "typing",
            "src.reporting.dashboard.contracts.evidence_pack_contract",
            "src.reporting.dashboard.contracts.selected_review_scope_contract",
        }
    )
