"""Shared runtime explanation contract helpers.

DB calls, provider calls, and runtime side effects are not categorically forbidden.
This contract forbids ungoverned access, hidden mutation, and wording-only explanation causing or claiming state changes.
Screen 3 through Screen 6 may require future runtime DB calls, provider calls,
and governed workflow side effects. Those are allowed when owned by proper
backend/service/provider layers and validated/audited as designed.

This helper module is intentionally data-only and deterministic: it does not
call an LLM provider, write audit records, query a database, or alter dashboard
state.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping


RUNTIME_EXPLANATION_PROVIDER_MODES = frozenset({"off", "mock", "local", "oci"})

RUNTIME_EXPLANATION_TRUTH_SOURCE_AUTHORITY: dict[str, dict[str, Any]] = {
    "deterministic_phase4_output": {
        "authority": "highest",
        "owns": (
            "diagnosis",
            "scores",
            "recommendations",
            "evidence",
            "trends",
            "similarity",
            "confidence",
            "classification",
            "thresholds",
            "phase4i_output",
        ),
        "llm_may_explain": True,
        "llm_must_not_change": True,
        "cache_only": False,
    },
    "generated_dashboard_state": {
        "authority": "presentation_snapshot",
        "owns": ("rendered_screen_state", "operator_visible_copy"),
        "llm_may_explain": True,
        "llm_must_not_change": True,
        "cache_only": False,
    },
    "governed_workflow_service_response": {
        "authority": "governed_service_result",
        "owns": ("request_validation", "request_status", "result", "audit_reference"),
        "llm_may_explain": True,
        "llm_must_not_change": True,
        "cache_only": False,
    },
    "persisted_memory_phase6": {
        "authority": "recorded_history",
        "owns": (
            "run_history",
            "recommendation_history",
            "action_history",
            "outcome_history",
            "feedback_history",
            "unknown_signal_history",
            "parser_mapping_candidates",
            "knowledge_update_requests",
        ),
        "llm_may_explain": True,
        "llm_must_not_change": True,
        "cache_only": False,
    },
    "runtime_ui_state": {
        "authority": "current_explicit_operator_state",
        "owns": ("current_selection", "current_scope", "current_screen_context"),
        "llm_may_explain": True,
        "llm_must_not_change": True,
        "cache_only": False,
    },
    "cache_continuity_only": {
        "authority": "continuity_only",
        "owns": ("cached_ui_context",),
        "llm_may_explain": True,
        "llm_must_not_change": True,
        "cache_only": True,
    },
    "provider_generated_wording": {
        "authority": "non_authoritative_wording",
        "owns": ("explanation_text",),
        "llm_may_explain": True,
        "llm_must_not_change": True,
        "cache_only": False,
    },
}

RUNTIME_EXPLANATION_SCREEN_ROLES: dict[str, str] = {
    "index_source_mode": "Home / Index - Platform Entry / Source Intake",
    "screen_1": "Screen 1 - Ingestion / Parser / Source Governance",
    "screen_2": "Screen 2 - Runtime Scope & Analysis Control",
    "screen_3": "Screen 3 - Diagnostic Snapshot",
    "screen_4": "Screen 4 - Evidence Review",
    "screen_5": "Screen 5 - Recommendation Action & Outcome",
    "screen_6": "Screen 6 - Learning Governance",
}

RUNTIME_EXPLANATION_ALLOWED_SCOPES: dict[str, tuple[str, ...]] = {
    "index_source_mode": (
        "source-entry paths",
        "platform entry choices",
        "local source vs Object Storage vs existing platform evidence",
        "local source path meaning",
        "Object Storage source path meaning",
        "existing platform evidence path meaning",
        "Screen 1 new-source handoff meaning",
        "Screen 2 existing-evidence handoff meaning",
        "generated artifact versus active downstream evidence",
        "downstream evidence handoff requirements",
    ),
    "screen_1": (
        "ingestion",
        "validation",
        "parser governance",
        "source intake context",
        "source validation result meaning",
        "parser health state",
        "parse confidence meaning",
        "unknown signals",
        "unknown parser signal meaning",
        "new AWR sections/elements/signals",
        "New AWR Mapping Candidates",
        "parser mapping candidates",
        "potential feature/domain candidates",
        "artifact readiness meaning",
        "downstream handoff eligibility meaning",
        "governance request meaning",
        "deterministic analysis separation",
    ),
    "screen_2": (
        "runtime options",
        "existing evidence inventory",
        "source-table coverage",
        "runtime scope",
        "row/window selection meaning",
        "Target A/B assignment meaning",
        "comparison readiness meaning",
        "cache continuity",
        "governed request meaning",
    ),
    "screen_3": (
        "diagnostic meaning",
        "confidence",
        "severity",
        "primary issue/domain",
        "score meaning",
        "recommendation meaning",
        "conceptual diagnostic change meaning",
    ),
    "screen_4": (
        "trends",
        "anomalies",
        "similarity",
        "historical evidence",
        "comparative evidence",
        "deep analysis evidence meaning",
    ),
    "screen_5": (
        "recommendation rationale",
        "action/outcome capture",
        "validation checklist meaning",
        "post-action comparison meaning",
        "operator next-step context",
    ),
    "screen_6": (
        "learning governance",
        "candidate meaning",
        "materialization meaning",
        "runtime eligibility meaning",
        "model registry state",
        "why governance is required",
    ),
}

RUNTIME_EXPLANATION_FORBIDDEN_MUTATIONS: dict[str, tuple[str, ...]] = {
    "index_source_mode": (
        "select source path",
        "validate source availability",
        "load source",
        "load existing platform evidence",
        "parse source",
        "parse AWR content",
        "load runtime options",
        "select existing run",
        "choose runtime scope",
        "assign Target A/B",
        "decide comparison readiness",
        "set dashboardEvidenceReady",
        "decide readiness",
        "unlock downstream screens",
        "submit governed actions",
        "create hidden workflow records",
        "create hidden DB writes",
        "perform deterministic analysis",
        "perform comparison",
        "change source state",
    ),
    "screen_1": (
        "change parser output",
        "change field mappings",
        "approve parser mappings",
        "reject parser mappings",
        "map parser candidates",
        "classify unknown signals",
        "change source validation",
        "change generated artifact readiness",
        "change completed_artifact_ready",
        "change dashboardEvidenceReady",
        "create hidden workflow records",
        "create hidden DB writes",
        "create hidden governance/audit records",
        "create scoring features",
        "assign diagnostic domains",
        "load runtime options",
        "choose runtime scope",
        "assign Target A/B",
        "decide comparison readiness",
        "execute analysis",
        "execute comparison",
        "change diagnosis",
        "change score",
        "change recommendation",
        "change learning",
        "change materialization",
        "change runtime eligibility",
        "select downstream evidence",
        "change future-run behavior",
    ),
    "screen_2": (
        "load or select runtime rows",
        "choose runtime scope",
        "assign Target A/B",
        "decide comparison readiness",
        "set evidence readiness",
        "submit approve or reject requests",
        "change diagnosis",
        "change score",
        "change recommendation",
        "change parser output",
        "change learning",
        "change materialization",
        "change runtime eligibility",
        "change future-run behavior",
    ),
    "screen_3": (
        "change diagnosis",
        "change primary issue/domain",
        "change domain score",
        "change severity",
        "change confidence",
        "change decision posture",
        "change evidence values",
        "change thresholds",
        "change recommendations",
        "change runtime behavior",
        "change parser output",
        "change learning",
        "change materialization",
        "change runtime eligibility",
        "change future-run behavior",
    ),
    "screen_4": (
        "change trend values",
        "change anomaly classification",
        "change similarity result",
        "change comparison result",
        "change raw evidence",
        "change derived metrics",
        "change domain scores",
        "change diagnosis",
        "change recommendations",
        "change thresholds",
    ),
    "screen_5": (
        "change recommendation content",
        "change recommendation priority",
        "change owner/status truth",
        "change action state",
        "change outcome state",
        "change validation checklist result",
        "change diagnosis",
        "change score",
        "change learning",
        "change materialization",
        "change runtime eligibility",
    ),
    "screen_6": (
        "accept or reject candidates",
        "materialize learning",
        "change runtime eligibility",
        "change model registry state",
        "train models",
        "change future-run behavior",
        "bypass governance",
    ),
}

RUNTIME_EXPLANATION_GLOBAL_FORBIDDEN_FIELDS = frozenset(
    {
        "action_type",
        "workflow_type",
        "audit_record",
        "audit_path",
        "audit_id",
        "request_id",
        "governance_record",
        "review_record",
        "feedback_record",
        "diagnosis_update",
        "primary_issue_update",
        "score_update",
        "severity_update",
        "confidence_update",
        "recommendation_update",
        "evidence_update",
        "threshold_update",
        "source_selection_update",
        "source_validation_update",
        "source_load",
        "source_execution",
        "parser_mutation",
        "parser_output_mutation",
        "parse_action",
        "unknown_signal_classification",
        "existing_run_selection",
        "runtime_action",
        "runtime_execution",
        "runtime_options_load",
        "runtime_scope_selection",
        "target_assignment",
        "comparison_readiness_decision",
        "comparison_action",
        "readiness_update",
        "dashboardEvidenceReady_update",
        "analysis_action",
        "materialization_action",
        "runtime_eligibility_action",
        "learning_candidate_action",
        "future_run_behavior_action",
        "phase8_sizing_action",
        "phase8_tco_action",
        "phase8_prediction_action",
        "emcc_oem_runtime_action",
        "create_audit_record",
        "create_review_record",
        "create_governance_record",
        "create_feedback_record",
        "create_learning_candidate",
        "create_materialization_candidate",
        "create_runtime_eligibility_record",
    }
)

RUNTIME_EXPLANATION_UNSAFE_OUTPUT_MARKERS = (
    "changed the diagnosis",
    "changes the diagnosis",
    "updated the diagnosis",
    "updates the diagnosis",
    "changed the score",
    "changes the score",
    "updated the score",
    "updates the score",
    "changed confidence",
    "updates confidence",
    "updated the recommendation",
    "changes the recommendation",
    "changed evidence",
    "updates evidence",
    "changed the threshold",
    "updates the threshold",
    "source was selected",
    "selected the source path",
    "validated the source",
    "validated source availability",
    "loaded evidence",
    "loaded the source",
    "loaded runtime options",
    "selected existing run",
    "parsed awr",
    "parsed the awr",
    "performed deterministic analysis",
    "performed analysis",
    "analyzed the awr",
    "compared evidence",
    "performed comparison",
    "unlocked downstream",
    "set dashboardevidenceready",
    "parser output changed",
    "changed parser output",
    "changed the parser output",
    "approved parser mapping",
    "approved the parser mapping",
    "rejected parser mapping",
    "rejected the parser mapping",
    "mapped the parser candidate",
    "classified the unknown signal",
    "created scoring feature",
    "created scoring features",
    "assigned diagnostic domain",
    "assigned diagnostic domains",
    "changed artifact readiness",
    "selected runtime scope",
    "chose the runtime scope",
    "assigned target a",
    "assigned target b",
    "decided comparison readiness",
    "submitted the request",
    "approved the request",
    "rejected the request",
    "runtime behavior changed",
    "changes runtime behavior",
    "changed memory",
    "created audit",
    "created governance",
    "created review",
    "created workflow",
    "created feedback",
    "accepted the candidate",
    "rejected the candidate",
    "materialized",
    "activated runtime eligibility",
    "changed runtime eligibility",
    "runtime eligible",
    "normal runtime eligibility",
    "runtime eligibility aligns",
    "runtime eligibility is normal",
    "trained the model",
    "updated the model",
    "future runs will",
    "phase 8 is active",
    "activated sizing",
    "sizing is active",
    "tco is active",
    "what-if is active",
    "predictive analytics is active",
    "emcc runtime is active",
    "oem runtime is active",
    "below concern threshold",
    "below concern thresholds",
    "above concern threshold",
    "above concern thresholds",
)

# Defaults for wording-only explanation responses. Explicit governed workflows
# including future Screen 3 through Screen 6 workflow work may still create
# records or audit references through their approved service paths; wording-only
# explanation must not create or claim those side effects.
RUNTIME_EXPLANATION_RECORDS_CREATED_EXPECTED = False
RUNTIME_EXPLANATION_AUDIT_REFERENCE_EXPECTED: None = None


def normalize_runtime_explanation_provider_mode(value: Any) -> str:
    """Normalize an explanation provider mode without changing semantics."""

    return str(value or "off").strip().lower()


def build_runtime_explanation_contract(
    screen_id: str,
    *,
    screen_role: str | None = None,
    runtime_context_type: str = "runtime_explanation",
    truth_source: str = "provider_generated_wording",
    truth_source_authority: str | None = None,
    allowed_scope_screen_id: str | None = None,
    forbidden_mutation_screen_id: str | None = None,
    provider_mode: str = "off",
) -> dict[str, Any]:
    """Build the deterministic contract envelope for a runtime explanation."""

    normalized_screen_id = str(screen_id or "").strip()
    scope_key = allowed_scope_screen_id or normalized_screen_id
    forbidden_key = forbidden_mutation_screen_id or normalized_screen_id
    truth = RUNTIME_EXPLANATION_TRUTH_SOURCE_AUTHORITY.get(truth_source, {})
    return {
        "screen_id": normalized_screen_id,
        "screen_role": screen_role or RUNTIME_EXPLANATION_SCREEN_ROLES.get(normalized_screen_id, ""),
        "runtime_context_type": runtime_context_type,
        "truth_source": truth_source,
        "truth_source_authority": truth_source_authority or str(truth.get("authority") or ""),
        "provider_mode": normalize_runtime_explanation_provider_mode(provider_mode),
        "allowed_explanation_scope": list(
            RUNTIME_EXPLANATION_ALLOWED_SCOPES.get(scope_key, ())
        ),
        "forbidden_mutations": list(
            RUNTIME_EXPLANATION_FORBIDDEN_MUTATIONS.get(forbidden_key, ())
        ),
        "non_mutating_explanation_only": True,
        "records_created_expected": RUNTIME_EXPLANATION_RECORDS_CREATED_EXPECTED,
        "audit_reference_expected": RUNTIME_EXPLANATION_AUDIT_REFERENCE_EXPECTED,
    }


def validate_runtime_explanation_payload(
    payload: Mapping[str, Any],
    *,
    expected_screen_id: str | None = None,
    required_fields: Iterable[str] = (),
    forbidden_fields: Iterable[str] | None = None,
    provider_modes: Iterable[str] = RUNTIME_EXPLANATION_PROVIDER_MODES,
    allow_records_created: bool = False,
    allow_audit_reference: bool = False,
) -> str:
    """Return an empty string when a runtime explanation payload is safe."""

    if not isinstance(payload, Mapping):
        return "Runtime explanation request must be a JSON object."
    if expected_screen_id is not None and payload.get("screen_id") != expected_screen_id:
        return f"Runtime explanation request must use screen_id={expected_screen_id}."
    if payload.get("non_mutating_explanation_only") is not True:
        return "Runtime explanation request must be marked non-mutating."
    provider_mode = normalize_runtime_explanation_provider_mode(payload.get("provider_mode"))
    if provider_mode not in set(provider_modes):
        return "Unsupported runtime explanation provider mode."
    present_forbidden = sorted(
        key for key in (forbidden_fields or RUNTIME_EXPLANATION_GLOBAL_FORBIDDEN_FIELDS)
        if key in payload
    )
    if present_forbidden:
        return "Runtime explanation request cannot include mutation/workflow fields: " + ", ".join(
            present_forbidden
        )
    if not allow_records_created and payload.get("records_created") is True:
        return "Runtime explanation request cannot create records."
    if not allow_audit_reference and str(payload.get("audit_reference") or "").strip():
        return "Runtime explanation request cannot provide an audit reference."
    for key in required_fields:
        if not str(payload.get(key) or "").strip():
            return f"Runtime explanation request is missing {key}."
    return ""


def runtime_explanation_violates_boundary(
    explanation: str,
    *,
    unsafe_markers: Iterable[str] = RUNTIME_EXPLANATION_UNSAFE_OUTPUT_MARKERS,
) -> bool:
    """Return True when provider wording claims a forbidden state mutation."""

    lowered = str(explanation or "").lower()
    return any(str(marker).lower() in lowered for marker in unsafe_markers)


def normalize_runtime_explanation_response(
    response: Mapping[str, Any],
    *,
    boundary_validation_result: str | None = None,
) -> dict[str, Any]:
    """Normalize wording-only explanation responses to the shared contract."""

    normalized = dict(response)
    normalized["records_created"] = False
    normalized["audit_reference"] = None
    normalized.setdefault("records_created_expected", RUNTIME_EXPLANATION_RECORDS_CREATED_EXPECTED)
    normalized.setdefault("audit_reference_expected", RUNTIME_EXPLANATION_AUDIT_REFERENCE_EXPECTED)
    normalized.setdefault("provider_output_status", normalized.get("status") or "unknown")
    normalized.setdefault(
        "boundary_validation_result",
        boundary_validation_result or "not_checked",
    )
    normalized.setdefault("non_mutating_explanation_only", True)
    return normalized
