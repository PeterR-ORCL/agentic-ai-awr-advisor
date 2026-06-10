import ast
import json
from pathlib import Path

from src.reporting.dashboard.contracts import selected_review_scope_contract as module
from src.reporting.dashboard.contracts.selected_review_scope_contract import (
    CONTRACT_TYPE,
    CONTRACT_VERSION,
    CacheContinuityMetadata,
    CacheContinuityStatus,
    ComparisonTargetIdentity,
    ReviewMode,
    ReviewModeIntent,
    ScopeValidationStatus,
    SelectionProvenance,
    SelectionRole,
    SourceMode,
    TargetAlignmentStatus,
    RuntimeScopeIdentity,
    SnapshotWindowIdentity,
    apply_selection_event,
    build_selected_review_scope_contract,
    clear_all_selections,
    clear_comparison_targets,
    clear_selection_role,
    compute_selected_flow_id,
    is_comparative_review_eligible,
    is_deep_analysis_eligible,
    is_diagnostic_snapshot_eligible,
    is_historical_review_eligible,
    unavailable_reasons_for,
    validate_selected_review_scope_contract,
)


def provenance() -> SelectionProvenance:
    return SelectionProvenance(
        source_system="screen2_backend_contract_builder",
        operator_action_id="op-7reset-d",
        submitted_by="operator",
        created_at="2026-06-09T00:00:00Z",
    )


def runtime_scope(scope_id: str = "runtime-1", alignment_key: str = "db-prod") -> RuntimeScopeIdentity:
    return RuntimeScopeIdentity(
        scope_id=scope_id,
        label="Runtime Scope",
        report_id="awr-current",
        database_id="db-prod",
        workload_id="oltp",
        snapshot_window_id="snap-current",
        alignment_key=alignment_key,
    )


def target(target_id: str, alignment_key: str = "db-prod") -> ComparisonTargetIdentity:
    return ComparisonTargetIdentity(
        target_id=target_id,
        label=target_id,
        report_id=f"awr-{target_id}",
        database_id="db-prod",
        workload_id="oltp",
        snapshot_window_id=f"snap-{target_id}",
        alignment_key=alignment_key,
    )


def base_contract(**overrides):
    payload = {
        "source_mode": SourceMode.EXISTING_EVIDENCE,
        "runtime_scope": runtime_scope(),
        "provenance": provenance(),
    }
    payload.update(overrides)
    return build_selected_review_scope_contract(**payload)


def reason_codes(contract, mode: ReviewMode) -> set[str]:
    return {reason.code for reason in unavailable_reasons_for(contract, mode)}


def json_text(payload) -> str:
    return json.dumps(payload, sort_keys=True)


def test_runtime_scope_only_contract_has_type_version_deterministic_id_and_explicit_validation():
    contract = base_contract()
    rebuilt = base_contract()

    assert contract.contract_type == CONTRACT_TYPE == "selected_review_scope_contract"
    assert contract.contract_version == CONTRACT_VERSION
    assert contract.selected_flow_id == rebuilt.selected_flow_id
    assert contract.selected_flow_id.startswith("selected-flow:")
    assert contract.validation_status == ScopeValidationStatus.VALID
    assert contract.provenance.is_present()
    assert is_diagnostic_snapshot_eligible(contract)


def test_compute_selected_flow_id_is_stable_for_authoritative_fields_only():
    selected_flow_id = compute_selected_flow_id(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        runtime_scope=runtime_scope(),
    )
    same_selected_flow_id = compute_selected_flow_id(
        source_mode="existing_evidence",
        runtime_scope=runtime_scope(),
    )

    assert selected_flow_id == same_selected_flow_id


def test_missing_provenance_is_an_explicit_validation_error():
    contract = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        runtime_scope=runtime_scope(),
    )

    assert contract.validation_status == ScopeValidationStatus.PARTIAL
    assert "provenance_required" in {issue.code for issue in contract.validation_errors}
    assert not is_diagnostic_snapshot_eligible(contract)


def test_runtime_scope_selected_makes_diagnostic_snapshot_eligible():
    contract = base_contract()

    assert is_diagnostic_snapshot_eligible(contract)
    assert ReviewMode.DIAGNOSTIC_SNAPSHOT in contract.eligible_review_modes


def test_target_a_only_is_not_diagnostic_authority():
    contract = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        target_a=target("target-a"),
        provenance=provenance(),
    )

    assert not is_diagnostic_snapshot_eligible(contract)
    assert "missing_runtime_scope" in {issue.code for issue in contract.validation_errors}


def test_target_b_only_is_not_diagnostic_authority():
    contract = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        target_b=target("target-b"),
        provenance=provenance(),
    )

    assert not is_diagnostic_snapshot_eligible(contract)
    assert "missing_runtime_scope" in {issue.code for issue in contract.validation_errors}


def test_target_a_and_b_without_runtime_scope_are_not_diagnostic_authority():
    contract = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        target_a=target("target-a"),
        target_b=target("target-b"),
        provenance=provenance(),
    )

    assert not is_diagnostic_snapshot_eligible(contract)
    assert contract.target_alignment_status == TargetAlignmentStatus.MISSING_RUNTIME_SCOPE
    assert "missing_runtime_scope" in reason_codes(contract, ReviewMode.COMPARATIVE_REVIEW)


def test_clearing_runtime_scope_removes_diagnostic_eligibility_but_preserves_targets():
    contract = base_contract(target_a=target("target-a"), target_b=target("target-b"))

    cleared = clear_selection_role(contract, SelectionRole.RUNTIME_SCOPE)

    assert cleared.runtime_scope is None
    assert cleared.target_a == contract.target_a
    assert cleared.target_b == contract.target_b
    assert not is_diagnostic_snapshot_eligible(cleared)


def test_selection_event_sets_and_reclicks_runtime_scope_without_mutating_other_roles():
    contract = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        target_a=target("target-a"),
        target_b=target("target-b"),
        provenance=provenance(),
    )

    selected = apply_selection_event(contract, runtime_scope("runtime-1"), SelectionRole.RUNTIME_SCOPE)
    cleared = apply_selection_event(selected, runtime_scope("runtime-1"), SelectionRole.RUNTIME_SCOPE)

    assert selected.runtime_scope == runtime_scope("runtime-1")
    assert cleared.runtime_scope is None
    assert cleared.target_a == target("target-a")
    assert cleared.target_b == target("target-b")
    assert contract.runtime_scope is None


def test_selection_event_sets_and_reclicks_target_a_without_mutating_other_roles():
    contract = base_contract(target_b=target("target-b"))

    selected = apply_selection_event(contract, target("target-a"), SelectionRole.TARGET_A)
    cleared = apply_selection_event(selected, target("target-a"), SelectionRole.TARGET_A)

    assert selected.target_a == target("target-a")
    assert cleared.target_a is None
    assert cleared.runtime_scope == contract.runtime_scope
    assert cleared.target_b == target("target-b")
    assert contract.target_a is None


def test_selection_event_sets_and_reclicks_target_b_without_mutating_other_roles():
    contract = base_contract(target_a=target("target-a"))

    selected = apply_selection_event(contract, target("target-b"), SelectionRole.TARGET_B)
    cleared = apply_selection_event(selected, target("target-b"), SelectionRole.TARGET_B)

    assert selected.target_b == target("target-b")
    assert cleared.target_b is None
    assert cleared.runtime_scope == contract.runtime_scope
    assert cleared.target_a == target("target-a")
    assert contract.target_b is None


def test_clear_runtime_scope_target_a_and_target_b_are_role_specific():
    contract = base_contract(target_a=target("target-a"), target_b=target("target-b"))

    clear_runtime = clear_selection_role(contract, SelectionRole.RUNTIME_SCOPE)
    clear_a = clear_selection_role(contract, SelectionRole.TARGET_A)
    clear_b = clear_selection_role(contract, SelectionRole.TARGET_B)

    assert clear_runtime.runtime_scope is None
    assert clear_runtime.target_a == contract.target_a
    assert clear_runtime.target_b == contract.target_b
    assert clear_a.runtime_scope == contract.runtime_scope
    assert clear_a.target_a is None
    assert clear_a.target_b == contract.target_b
    assert clear_b.runtime_scope == contract.runtime_scope
    assert clear_b.target_a == contract.target_a
    assert clear_b.target_b is None


def test_clear_comparison_targets_preserves_runtime_scope():
    contract = base_contract(target_a=target("target-a"), target_b=target("target-b"))

    cleared = clear_comparison_targets(contract)

    assert cleared.runtime_scope == contract.runtime_scope
    assert cleared.target_a is None
    assert cleared.target_b is None
    assert is_diagnostic_snapshot_eligible(cleared)


def test_clear_all_selections_clears_runtime_scope_and_targets():
    contract = base_contract(target_a=target("target-a"), target_b=target("target-b"))

    cleared = clear_all_selections(contract)

    assert cleared.runtime_scope is None
    assert cleared.target_a is None
    assert cleared.target_b is None
    assert not is_diagnostic_snapshot_eligible(cleared)


def test_aligned_runtime_scope_and_targets_make_comparative_review_eligible():
    contract = base_contract(target_a=target("target-a"), target_b=target("target-b"))

    assert contract.target_alignment_status == TargetAlignmentStatus.ALIGNED
    assert is_comparative_review_eligible(contract)
    assert is_diagnostic_snapshot_eligible(contract)
    assert "screen3_comparison" not in contract.to_dict()


def test_target_a_and_b_without_runtime_scope_make_comparative_review_unavailable():
    contract = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        target_a=target("target-a"),
        target_b=target("target-b"),
        provenance=provenance(),
    )

    assert not is_comparative_review_eligible(contract)
    assert contract.target_alignment_status == TargetAlignmentStatus.MISSING_RUNTIME_SCOPE
    assert "missing_runtime_scope" in reason_codes(contract, ReviewMode.COMPARATIVE_REVIEW)


def test_runtime_scope_and_target_a_only_make_comparative_review_unavailable_with_missing_target_b():
    contract = base_contract(target_a=target("target-a"))

    assert not is_comparative_review_eligible(contract)
    assert contract.target_alignment_status == TargetAlignmentStatus.MISSING_TARGET_B
    assert "missing_target_b" in reason_codes(contract, ReviewMode.COMPARATIVE_REVIEW)


def test_runtime_scope_and_target_b_only_make_comparative_review_unavailable_with_missing_target_a():
    contract = base_contract(target_b=target("target-b"))

    assert not is_comparative_review_eligible(contract)
    assert contract.target_alignment_status == TargetAlignmentStatus.MISSING_TARGET_A
    assert "missing_target_a" in reason_codes(contract, ReviewMode.COMPARATIVE_REVIEW)


def test_mismatched_targets_make_comparative_review_unavailable_with_mismatch_reason():
    contract = base_contract(
        target_a=target("target-a", alignment_key="db-prod"),
        target_b=target("target-b", alignment_key="db-other"),
    )

    assert contract.validation_status == ScopeValidationStatus.PARTIAL
    assert contract.target_alignment_status == TargetAlignmentStatus.MISMATCH
    assert not is_comparative_review_eligible(contract)
    assert "target_alignment_mismatch" in reason_codes(contract, ReviewMode.COMPARATIVE_REVIEW)


def test_comparative_eligibility_is_separate_from_screen3_diagnostic_role():
    contract = base_contract(target_a=target("target-a"), target_b=target("target-b"))

    assert is_comparative_review_eligible(contract)
    assert is_diagnostic_snapshot_eligible(contract)
    assert ReviewMode.COMPARATIVE_REVIEW in contract.eligible_review_modes
    assert ReviewMode.DIAGNOSTIC_SNAPSHOT in contract.eligible_review_modes
    assert "comparison_delta" not in json_text(contract.to_dict())


def test_historical_review_eligibility_requires_explicit_window_or_evidence_availability():
    unavailable = base_contract()
    with_window = base_contract(selected_window=SnapshotWindowIdentity(window_id="historical-window"))
    with_intent = base_contract(
        review_mode_intent=ReviewModeIntent(historical_evidence_available=True)
    )

    assert not is_historical_review_eligible(unavailable)
    assert "historical_evidence_unavailable" in reason_codes(unavailable, ReviewMode.HISTORICAL_REVIEW)
    assert is_historical_review_eligible(with_window)
    assert is_historical_review_eligible(with_intent)


def test_deep_analysis_eligibility_requires_explicit_request_and_availability():
    not_requested = base_contract()
    requested_without_contract = base_contract(
        review_mode_intent=ReviewModeIntent(deep_analysis_requested=True)
    )
    available = base_contract(
        review_mode_intent=ReviewModeIntent(
            requested_modes=(ReviewMode.DEEP_ANALYSIS,),
            deep_analysis_requested=True,
            deep_analysis_available=True,
        )
    )

    assert not is_deep_analysis_eligible(not_requested)
    assert "deep_analysis_not_requested" in reason_codes(not_requested, ReviewMode.DEEP_ANALYSIS)
    assert not is_deep_analysis_eligible(requested_without_contract)
    assert "deep_analysis_contract_unavailable" in reason_codes(
        requested_without_contract,
        ReviewMode.DEEP_ANALYSIS,
    )
    assert is_deep_analysis_eligible(available)


def test_ui_flags_do_not_create_historical_or_deep_analysis_eligibility():
    contract = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        runtime_scope={"row_id": "runtime-1", "alignment_key": "db-prod"},
        review_mode_intent={
            "ui_flags": {"historical": True, "deep_analysis": True},
            "browser_hash": "#deep-analysis",
        },
        provenance=provenance(),
    )

    assert is_diagnostic_snapshot_eligible(contract)
    assert not is_historical_review_eligible(contract)
    assert not is_deep_analysis_eligible(contract)


def test_cache_continuity_display_only_does_not_make_missing_runtime_scope_valid():
    contract = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        cache_continuity=CacheContinuityMetadata(
            status=CacheContinuityStatus.DISPLAY_ONLY,
            prior_selected_flow_id="selected-flow:old",
        ),
        provenance=provenance(),
    )

    assert contract.validation_status == ScopeValidationStatus.INVALID
    assert not is_diagnostic_snapshot_eligible(contract)
    assert "cache_continuity_not_authority" in {warning.code for warning in contract.warnings}


def test_stale_cache_cannot_create_selected_flow_id_authority():
    contract = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        cache_continuity={"status": "stale", "prior_selected_flow_id": "selected-flow:old"},
        provenance=provenance(),
    )

    assert contract.selected_flow_id == "selected-flow:none"
    assert not is_diagnostic_snapshot_eligible(contract)


def test_invalidated_cache_cannot_create_eligibility():
    contract = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        cache_continuity={"status": "invalidated", "displayed_scope_id": "runtime-1"},
        provenance=provenance(),
    )

    assert not contract.eligible_review_modes
    assert not is_comparative_review_eligible(contract)


def test_contract_shape_contains_no_browser_or_generated_artifact_authority_fields():
    contract = base_contract()
    payload_text = json_text(contract.to_dict())

    for forbidden in ("localStorage", "browser_hash", "hash_state", "generated_html_path", "html_path"):
        assert forbidden not in payload_text


def test_generated_html_reference_is_rejected_as_source_authority():
    contract = build_selected_review_scope_contract(
        source_mode=SourceMode.GENERATED_ARTIFACT_REFERENCE,
        runtime_scope=runtime_scope(),
        provenance=provenance(),
    )

    assert not is_diagnostic_snapshot_eligible(contract)
    assert "generated_artifact_not_authority" in {issue.code for issue in contract.validation_errors}


def test_generated_html_path_string_is_ignored_as_runtime_scope_authority():
    contract = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        runtime_scope={"generated_html_path": "awr_dashboard/screen_3_analysis.html"},
        provenance=provenance(),
    )

    assert contract.runtime_scope is None
    assert "generated_artifact_not_authority" in {warning.code for warning in contract.warnings}
    assert not is_diagnostic_snapshot_eligible(contract)


def test_ui_selector_labels_do_not_determine_validity():
    contract = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        runtime_scope={"ui_selector_label": "Looks selected in the browser"},
        provenance=provenance(),
    )

    assert contract.runtime_scope is None
    assert not is_diagnostic_snapshot_eligible(contract)
    assert "missing_runtime_scope" in {issue.code for issue in contract.validation_errors}


def test_chart_payloads_are_not_accepted_as_contract_evidence():
    contract = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        runtime_scope={"chart_payload": {"cpu": [1, 2, 3]}},
        provenance=provenance(),
    )

    assert contract.runtime_scope is None
    assert "non_authoritative_input_ignored" in {warning.code for warning in contract.warnings}
    assert "chart_payload" not in json_text(contract.to_dict())


def test_selected_review_scope_contract_does_not_contain_evidence_outputs():
    contract = base_contract(
        runtime_scope={
            "row_id": "runtime-1",
            "alignment_key": "db-prod",
            "metric_deltas": {"cpu": 12},
            "recommendations": ["scale up"],
            "learning_output": {"candidate": True},
            "llm_facts": "invented fact",
        }
    )
    payload_text = json_text(contract.to_dict())

    assert "metric_deltas" not in payload_text
    assert "recommendations" not in payload_text
    assert "learning_output" not in payload_text
    assert "llm_facts" not in payload_text
    assert any(warning.code == "non_authoritative_input_ignored" for warning in contract.warnings)


def test_contract_serializes_to_json_safe_shape_and_deserializes_with_same_validation():
    contract = base_contract(target_a=target("target-a"), target_b=target("target-b"))
    payload = contract.to_dict()
    encoded = json.dumps(payload, sort_keys=True)
    decoded = json.loads(encoded)

    restored = validate_selected_review_scope_contract(decoded)

    assert restored.selected_flow_id == contract.selected_flow_id
    assert restored.validation_status == contract.validation_status
    assert restored.target_alignment_status == contract.target_alignment_status
    assert restored.eligible_review_modes == contract.eligible_review_modes


def test_validation_errors_survive_serialization_by_revalidation():
    contract = build_selected_review_scope_contract(
        source_mode=SourceMode.EXISTING_EVIDENCE,
        target_a=target("target-a"),
        provenance=provenance(),
    )
    restored = validate_selected_review_scope_contract(json.loads(json.dumps(contract.to_dict())))

    assert restored.selected_flow_id == contract.selected_flow_id
    assert restored.validation_status == contract.validation_status
    assert {issue.code for issue in restored.validation_errors} == {
        issue.code for issue in contract.validation_errors
    }


def test_selected_review_scope_contract_imports_only_pure_stdlib_dependencies():
    source = Path(module.__file__).read_text()
    tree = ast.parse(source)
    imported_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_names.append(node.module or "")

    assert "src.reporting.html_dashboard" not in imported_names
    assert "html_dashboard" not in imported_names
    assert not any("renderer" in name for name in imported_names)
    assert not any("llm" in name.lower() for name in imported_names)
    assert not any("awr_dashboard" in name for name in imported_names)
    assert set(imported_names).issubset(
        {
            "__future__",
            "hashlib",
            "json",
            "collections.abc",
            "dataclasses",
            "enum",
            "typing",
        }
    )

