"""Phase 7BO Screen 6 runtime gate review preview models.

The records in this module describe local metadata for future Screen 6 runtime
gate review. They do not persist review records, transition runtime gate state,
enable adaptive runtime, grant runtime influence, grant runtime eligibility,
execute rollback, invoke governed write paths, execute analysis, modify
dashboards, modify CLI behavior, write databases, write files, import runtime
parser/scoring/decision/recommendation modules, activate runtime, or mutate
Phase 4I.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


RUNTIME_GATE_REVIEW_ACTIONS = (
    "mark_gate_under_review",
    "review_adaptive_runtime_context",
    "review_scoring_integration",
    "review_recommendation_integration",
    "review_parser_integration",
    "review_fallback_posture",
    "request_runtime_review",
    "request_rollback_review",
    "request_gate_revision",
    "close_gate_review",
    "add_runtime_gate_note",
)

RUNTIME_GATE_REVIEW_RESULT_STATUSES = (
    "preview_only",
    "valid_for_future_review",
    "needs_actor",
    "needs_gate",
    "needs_validation_reference",
    "needs_rollback_reference",
    "unsupported_action",
    "write_not_allowed_in_this_phase",
    "blocked_by_runtime_safety",
)

RUNTIME_GATE_REVIEW_GATE_TYPES = (
    "adaptive_runtime_gate",
    "adaptive_runtime_context",
    "scoring_integration_result",
    "recommendation_integration_result",
    "parser_integration_result",
    "runtime_fallback_decision",
    "runtime_readiness_record",
    "unknown",
)

ACTION_TO_PROPOSED_NEXT_STATUS = {
    "mark_gate_under_review": "under_review",
    "review_adaptive_runtime_context": "reviewed_preview",
    "review_scoring_integration": "reviewed_preview",
    "review_recommendation_integration": "reviewed_preview",
    "review_parser_integration": "reviewed_preview",
    "review_fallback_posture": "reviewed_preview",
    "request_runtime_review": "runtime_review_requested_preview",
    "request_rollback_review": "rollback_review_requested_preview",
    "request_gate_revision": "needs_revision",
    "close_gate_review": "closed",
    "add_runtime_gate_note": "proposed",
}


class Screen6RuntimeGateReviewError(ValueError):
    """Raised when Phase 7BO runtime gate review metadata is invalid."""


@dataclass(frozen=True)
class RuntimeGateReviewRequest:
    """A future request to review Screen 6 runtime gate posture."""

    review_request_id: str
    gate_id: str | None
    gate_type: str
    requested_action: str
    actor_id: str | None
    actor_audit_context: dict[str, Any] | None = None
    governance_note: str | None = None
    validation_reference: str | None = None
    rollback_reference: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    validation_status: str = "preview_only"
    can_route_to_write_path: bool = False
    write_performed: bool = False
    gate_state_changed: bool = False
    adaptive_runtime_enabled_changed: bool = False
    runtime_influence_allowed_changed: bool = False
    runtime_review_requested: bool = False
    rollback_review_requested: bool = False
    runtime_influence_granted: bool = False
    runtime_eligibility_granted: bool = False
    runtime_active: bool = False
    validation_reference_attached: bool = False
    rollback_reference_attached: bool = False
    phase4i_mutation_requested: bool = False
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.review_request_id, "review_request_id")
        _require_optional_string(self.gate_id, "gate_id")
        _require_nonempty_string(self.gate_type, "gate_type")
        _require_nonempty_string(self.requested_action, "requested_action")
        _require_optional_string(self.actor_id, "actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        _require_optional_string(self.governance_note, "governance_note")
        _require_optional_string(self.validation_reference, "validation_reference")
        _require_optional_string(self.rollback_reference, "rollback_reference")
        _require_mapping(self.payload, "payload")
        _require_supported(
            self.validation_status,
            RUNTIME_GATE_REVIEW_RESULT_STATUSES,
            "validation_status",
        )
        _require_boolean(self.can_route_to_write_path, "can_route_to_write_path")
        _require_false(self.write_performed, "write_performed")
        _require_false(self.gate_state_changed, "gate_state_changed")
        _require_false(
            self.adaptive_runtime_enabled_changed,
            "adaptive_runtime_enabled_changed",
        )
        _require_false(
            self.runtime_influence_allowed_changed,
            "runtime_influence_allowed_changed",
        )
        _require_false(self.runtime_review_requested, "runtime_review_requested")
        _require_false(self.rollback_review_requested, "rollback_review_requested")
        _require_false(
            self.runtime_influence_granted,
            "runtime_influence_granted",
        )
        _require_false(
            self.runtime_eligibility_granted,
            "runtime_eligibility_granted",
        )
        _require_false(self.runtime_active, "runtime_active")
        _require_false(
            self.validation_reference_attached,
            "validation_reference_attached",
        )
        _require_false(
            self.rollback_reference_attached,
            "rollback_reference_attached",
        )
        _require_false(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class RuntimeGateReviewResult:
    """A local preview result for a runtime gate review request."""

    review_result_id: str
    review_request_id: str
    gate_id: str
    requested_action: str
    result_status: str
    proposed_next_status: str | None = None
    gate_state_changed: bool = False
    adaptive_runtime_enabled_changed: bool = False
    runtime_influence_allowed_changed: bool = False
    runtime_review_requested: bool = False
    rollback_review_requested: bool = False
    runtime_influence_granted: bool = False
    runtime_eligibility_granted: bool = False
    runtime_active: bool = False
    governance_action_performed: bool = False
    validation_reference_attached: bool = False
    rollback_reference_attached: bool = False
    write_performed: bool = False
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.review_result_id, "review_result_id")
        _require_nonempty_string(self.review_request_id, "review_request_id")
        _require_nonempty_string(self.gate_id, "gate_id")
        _require_nonempty_string(self.requested_action, "requested_action")
        _require_supported(
            self.result_status,
            RUNTIME_GATE_REVIEW_RESULT_STATUSES,
            "result_status",
        )
        _require_optional_string(self.proposed_next_status, "proposed_next_status")
        _require_false(self.gate_state_changed, "gate_state_changed")
        _require_false(
            self.adaptive_runtime_enabled_changed,
            "adaptive_runtime_enabled_changed",
        )
        _require_false(
            self.runtime_influence_allowed_changed,
            "runtime_influence_allowed_changed",
        )
        _require_false(self.runtime_review_requested, "runtime_review_requested")
        _require_false(self.rollback_review_requested, "rollback_review_requested")
        _require_false(
            self.runtime_influence_granted,
            "runtime_influence_granted",
        )
        _require_false(
            self.runtime_eligibility_granted,
            "runtime_eligibility_granted",
        )
        _require_false(self.runtime_active, "runtime_active")
        _require_false(
            self.governance_action_performed,
            "governance_action_performed",
        )
        _require_false(
            self.validation_reference_attached,
            "validation_reference_attached",
        )
        _require_false(
            self.rollback_reference_attached,
            "rollback_reference_attached",
        )
        _require_false(self.write_performed, "write_performed")
        _require_string_list(self.denied_reasons, "denied_reasons")
        _require_string_list(self.warnings, "warnings")
        _require_string_list(self.required_next_steps, "required_next_steps")
        _require_false(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.notes, "notes")


def create_runtime_gate_review_request_id(
    gate_id: str,
    requested_action: str,
) -> str:
    """Create a deterministic Screen 6 runtime gate review request id."""

    _require_nonempty_string(gate_id, "gate_id")
    _require_supported(
        requested_action,
        RUNTIME_GATE_REVIEW_ACTIONS,
        "requested_action",
    )
    return (
        "SCREEN6-RUNTIME-GATE-REVIEW-REQUEST-"
        f"{_normalize_token(gate_id)}-"
        f"{_normalize_token(requested_action)}"
    )


def create_runtime_gate_review_result_id(review_request_id: str) -> str:
    """Create a deterministic Screen 6 runtime gate review result id."""

    _require_nonempty_string(review_request_id, "review_request_id")
    return f"SCREEN6-RUNTIME-GATE-REVIEW-RESULT-{_normalize_token(review_request_id)}"


def proposed_next_status_for_action(requested_action: str) -> str:
    """Return the preview-only status implied by a runtime gate action."""

    _require_supported(
        requested_action,
        RUNTIME_GATE_REVIEW_ACTIONS,
        "requested_action",
    )
    return ACTION_TO_PROPOSED_NEXT_STATUS[requested_action]


def validate_runtime_gate_review_request(
    request: RuntimeGateReviewRequest,
) -> RuntimeGateReviewRequest:
    """Validate and return runtime gate review request metadata."""

    if not isinstance(request, RuntimeGateReviewRequest):
        raise Screen6RuntimeGateReviewError(
            "request must be a RuntimeGateReviewRequest instance."
        )
    request.__post_init__()
    _require_nonempty_string(request.gate_id, "gate_id")
    _require_supported(
        request.gate_type,
        RUNTIME_GATE_REVIEW_GATE_TYPES,
        "gate_type",
    )
    _require_supported(
        request.requested_action,
        RUNTIME_GATE_REVIEW_ACTIONS,
        "requested_action",
    )
    _require_nonempty_string(request.actor_id, "actor_id")
    return request


def validate_runtime_gate_review_result(
    result: RuntimeGateReviewResult,
) -> RuntimeGateReviewResult:
    """Validate and return runtime gate review result metadata."""

    if not isinstance(result, RuntimeGateReviewResult):
        raise Screen6RuntimeGateReviewError(
            "result must be a RuntimeGateReviewResult instance."
        )
    result.__post_init__()
    _require_supported(
        result.requested_action,
        RUNTIME_GATE_REVIEW_ACTIONS,
        "requested_action",
    )
    _require_supported(
        result.result_status,
        RUNTIME_GATE_REVIEW_RESULT_STATUSES,
        "result_status",
    )
    return result


def evaluate_runtime_gate_review_request(
    request: RuntimeGateReviewRequest,
) -> RuntimeGateReviewResult:
    """Evaluate request metadata without writes, gate mutation, or activation."""

    if not isinstance(request, RuntimeGateReviewRequest):
        raise Screen6RuntimeGateReviewError(
            "request must be a RuntimeGateReviewRequest instance."
        )
    request.__post_init__()

    actor_present = bool(_optional_text(request.actor_id))
    gate_present = bool(_optional_text(request.gate_id))
    action_supported = request.requested_action in RUNTIME_GATE_REVIEW_ACTIONS
    denied_reasons: list[str] = []
    required_next_steps: list[str] = []
    warnings = [
        "Runtime gate review is preview-only in Phase 7BO.",
        "Governed write path is required before future runtime gate changes.",
        "Adaptive runtime remains disabled in this phase.",
        "Runtime influence and runtime eligibility are not granted.",
        "Runtime remains inactive and deterministic runtime remains authoritative.",
    ]

    if not actor_present:
        result_status = "needs_actor"
        denied_reasons.append("actor_id is required for runtime gate review")
        required_next_steps.append("provide Phase 7AE actor identity")
    elif not gate_present:
        result_status = "needs_gate"
        denied_reasons.append("gate_id is required")
        required_next_steps.append("provide runtime gate reference")
    elif (
        request.requested_action == "attach_validation_reference"
        and not _optional_text(request.validation_reference)
    ):
        result_status = "needs_validation_reference"
        denied_reasons.append("validation_reference is required for this preview")
        required_next_steps.append("provide validation reference before future write routing")
    elif (
        request.requested_action == "request_rollback_review"
        and not _optional_text(request.rollback_reference)
    ):
        result_status = "needs_rollback_reference"
        denied_reasons.append("rollback_reference is required for this preview")
        required_next_steps.append("provide rollback reference before future write routing")
    elif not action_supported:
        result_status = "unsupported_action"
        denied_reasons.append("requested_action is not supported")
        required_next_steps.append("choose a supported Phase 7BO preview action")
    elif request.requested_action == "request_runtime_review":
        result_status = "valid_for_future_review"
        required_next_steps.append("capture future runtime review through governed workflow")
        required_next_steps.append("keep runtime_influence_granted=false")
        required_next_steps.append("keep runtime_eligibility_granted=false")
        required_next_steps.append("keep runtime_active=false")
    else:
        result_status = "valid_for_future_review"
        required_next_steps.append("route through future Phase 7AG governed write path")
        required_next_steps.append("capture audit through future Screen 6 governance workflow")

    if request.gate_type not in RUNTIME_GATE_REVIEW_GATE_TYPES:
        warnings.append("Gate type must be supported before future write routing.")

    if (
        request.write_performed
        or request.gate_state_changed
        or request.adaptive_runtime_enabled_changed
        or request.runtime_influence_allowed_changed
        or request.runtime_review_requested
        or request.rollback_review_requested
        or request.runtime_influence_granted
        or request.runtime_eligibility_granted
        or request.runtime_active
        or request.validation_reference_attached
        or request.rollback_reference_attached
        or request.phase4i_mutation_requested
    ):
        result_status = "blocked_by_runtime_safety"
        denied_reasons.append("runtime, gate, eligibility, or mutation flags are not allowed in Phase 7BO")

    proposed_next_status = (
        ACTION_TO_PROPOSED_NEXT_STATUS.get(request.requested_action)
        if action_supported
        else None
    )

    return RuntimeGateReviewResult(
        review_result_id=create_runtime_gate_review_result_id(
            request.review_request_id
        ),
        review_request_id=request.review_request_id,
        gate_id=_optional_text(request.gate_id) or "MISSING-GATE",
        requested_action=request.requested_action,
        result_status=result_status,
        proposed_next_status=proposed_next_status,
        gate_state_changed=False,
        adaptive_runtime_enabled_changed=False,
        runtime_influence_allowed_changed=False,
        runtime_review_requested=False,
        rollback_review_requested=False,
        runtime_influence_granted=False,
        runtime_eligibility_granted=False,
        runtime_active=False,
        governance_action_performed=False,
        validation_reference_attached=False,
        rollback_reference_attached=False,
        write_performed=False,
        denied_reasons=denied_reasons,
        warnings=warnings,
        required_next_steps=required_next_steps,
        phase4i_mutation_requested=False,
        notes=request.notes,
    )


def runtime_gate_review_request_to_dict(
    request: RuntimeGateReviewRequest,
) -> dict[str, Any]:
    """Serialize runtime gate review request metadata."""

    request.__post_init__()
    return {
        "review_request_id": request.review_request_id,
        "gate_id": request.gate_id,
        "gate_type": request.gate_type,
        "requested_action": request.requested_action,
        "actor_id": request.actor_id,
        "actor_audit_context": _copy_optional_mapping(request.actor_audit_context),
        "governance_note": request.governance_note,
        "validation_reference": request.validation_reference,
        "rollback_reference": request.rollback_reference,
        "payload": dict(request.payload),
        "validation_status": request.validation_status,
        "can_route_to_write_path": request.can_route_to_write_path,
        "write_performed": request.write_performed,
        "gate_state_changed": request.gate_state_changed,
        "adaptive_runtime_enabled_changed": request.adaptive_runtime_enabled_changed,
        "runtime_influence_allowed_changed": request.runtime_influence_allowed_changed,
        "runtime_review_requested": request.runtime_review_requested,
        "rollback_review_requested": request.rollback_review_requested,
        "runtime_influence_granted": request.runtime_influence_granted,
        "runtime_eligibility_granted": request.runtime_eligibility_granted,
        "runtime_active": request.runtime_active,
        "validation_reference_attached": request.validation_reference_attached,
        "rollback_reference_attached": request.rollback_reference_attached,
        "phase4i_mutation_requested": request.phase4i_mutation_requested,
        "created_at": request.created_at,
        "notes": request.notes,
    }


def runtime_gate_review_request_from_dict(
    data: dict[str, Any],
) -> RuntimeGateReviewRequest:
    """Deserialize runtime gate review request metadata from a dictionary."""

    _require_mapping(data, "data")
    return RuntimeGateReviewRequest(
        review_request_id=str(data["review_request_id"]),
        gate_id=_optional_text(data.get("gate_id")),
        gate_type=str(data["gate_type"]),
        requested_action=str(data["requested_action"]),
        actor_id=_optional_text(data.get("actor_id")),
        actor_audit_context=_copy_optional_mapping(data.get("actor_audit_context")),
        governance_note=_optional_text(data.get("governance_note")),
        validation_reference=_optional_text(data.get("validation_reference")),
        rollback_reference=_optional_text(data.get("rollback_reference")),
        payload=dict(data.get("payload") or {}),
        validation_status=str(data.get("validation_status", "preview_only")),
        can_route_to_write_path=_bool_from_mapping(
            data,
            "can_route_to_write_path",
            False,
        ),
        write_performed=_bool_from_mapping(data, "write_performed", False),
        gate_state_changed=_bool_from_mapping(data, "gate_state_changed", False),
        adaptive_runtime_enabled_changed=_bool_from_mapping(
            data,
            "adaptive_runtime_enabled_changed",
            False,
        ),
        runtime_influence_allowed_changed=_bool_from_mapping(
            data,
            "runtime_influence_allowed_changed",
            False,
        ),
        runtime_review_requested=_bool_from_mapping(
            data,
            "runtime_review_requested",
            False,
        ),
        rollback_review_requested=_bool_from_mapping(
            data,
            "rollback_review_requested",
            False,
        ),
        runtime_influence_granted=_bool_from_mapping(
            data,
            "runtime_influence_granted",
            False,
        ),
        runtime_eligibility_granted=_bool_from_mapping(
            data,
            "runtime_eligibility_granted",
            False,
        ),
        runtime_active=_bool_from_mapping(data, "runtime_active", False),
        validation_reference_attached=_bool_from_mapping(
            data,
            "validation_reference_attached",
            False,
        ),
        rollback_reference_attached=_bool_from_mapping(
            data,
            "rollback_reference_attached",
            False,
        ),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        created_at=_optional_text(data.get("created_at")),
        notes=_optional_text(data.get("notes")),
    )


def runtime_gate_review_result_to_dict(
    result: RuntimeGateReviewResult,
) -> dict[str, Any]:
    """Serialize runtime gate review result metadata."""

    result.__post_init__()
    return {
        "review_result_id": result.review_result_id,
        "review_request_id": result.review_request_id,
        "gate_id": result.gate_id,
        "requested_action": result.requested_action,
        "result_status": result.result_status,
        "proposed_next_status": result.proposed_next_status,
        "gate_state_changed": result.gate_state_changed,
        "adaptive_runtime_enabled_changed": result.adaptive_runtime_enabled_changed,
        "runtime_influence_allowed_changed": result.runtime_influence_allowed_changed,
        "runtime_review_requested": result.runtime_review_requested,
        "rollback_review_requested": result.rollback_review_requested,
        "runtime_influence_granted": result.runtime_influence_granted,
        "runtime_eligibility_granted": result.runtime_eligibility_granted,
        "runtime_active": result.runtime_active,
        "governance_action_performed": result.governance_action_performed,
        "validation_reference_attached": result.validation_reference_attached,
        "rollback_reference_attached": result.rollback_reference_attached,
        "write_performed": result.write_performed,
        "denied_reasons": list(result.denied_reasons),
        "warnings": list(result.warnings),
        "required_next_steps": list(result.required_next_steps),
        "phase4i_mutation_requested": result.phase4i_mutation_requested,
        "notes": result.notes,
    }


def runtime_gate_review_result_from_dict(
    data: dict[str, Any],
) -> RuntimeGateReviewResult:
    """Deserialize runtime gate review result metadata from a dictionary."""

    _require_mapping(data, "data")
    return RuntimeGateReviewResult(
        review_result_id=str(data["review_result_id"]),
        review_request_id=str(data["review_request_id"]),
        gate_id=str(data["gate_id"]),
        requested_action=str(data["requested_action"]),
        result_status=str(data["result_status"]),
        proposed_next_status=_optional_text(data.get("proposed_next_status")),
        gate_state_changed=_bool_from_mapping(data, "gate_state_changed", False),
        adaptive_runtime_enabled_changed=_bool_from_mapping(
            data,
            "adaptive_runtime_enabled_changed",
            False,
        ),
        runtime_influence_allowed_changed=_bool_from_mapping(
            data,
            "runtime_influence_allowed_changed",
            False,
        ),
        runtime_review_requested=_bool_from_mapping(
            data,
            "runtime_review_requested",
            False,
        ),
        rollback_review_requested=_bool_from_mapping(
            data,
            "rollback_review_requested",
            False,
        ),
        runtime_influence_granted=_bool_from_mapping(
            data,
            "runtime_influence_granted",
            False,
        ),
        runtime_eligibility_granted=_bool_from_mapping(
            data,
            "runtime_eligibility_granted",
            False,
        ),
        runtime_active=_bool_from_mapping(data, "runtime_active", False),
        governance_action_performed=_bool_from_mapping(
            data,
            "governance_action_performed",
            False,
        ),
        validation_reference_attached=_bool_from_mapping(
            data,
            "validation_reference_attached",
            False,
        ),
        rollback_reference_attached=_bool_from_mapping(
            data,
            "rollback_reference_attached",
            False,
        ),
        write_performed=_bool_from_mapping(data, "write_performed", False),
        denied_reasons=list(data.get("denied_reasons") or []),
        warnings=list(data.get("warnings") or []),
        required_next_steps=list(data.get("required_next_steps") or []),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        notes=_optional_text(data.get("notes")),
    )


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _bool_from_mapping(data: dict[str, Any], field_name: str, default: bool) -> bool:
    value = data.get(field_name, default)
    if isinstance(value, bool):
        return value
    raise Screen6RuntimeGateReviewError(f"{field_name} must be a boolean.")


def _copy_optional_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Screen6RuntimeGateReviewError(
            "mapping value must be a dictionary."
        )
    return dict(value)


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise Screen6RuntimeGateReviewError(
            f"{field_name} must be a mapping."
        )


def _require_optional_mapping(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, dict):
        raise Screen6RuntimeGateReviewError(
            f"{field_name} must be a mapping or None."
        )


def _require_nonempty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise Screen6RuntimeGateReviewError(
            f"{field_name} must be a non-empty string."
        )


def _require_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise Screen6RuntimeGateReviewError(
            f"{field_name} must be a string or None."
        )


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        raise Screen6RuntimeGateReviewError(
            f"{field_name} must be one of: {', '.join(supported)}."
        )


def _require_boolean(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise Screen6RuntimeGateReviewError(
            f"{field_name} must be a boolean."
        )


def _require_false(value: Any, field_name: str) -> None:
    _require_boolean(value, field_name)
    if value:
        raise Screen6RuntimeGateReviewError(
            f"{field_name} must remain false in Phase 7BO."
        )


def _require_string_list(value: Any, field_name: str) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise Screen6RuntimeGateReviewError(
            f"{field_name} must be a list of strings."
        )


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text).strip("-")
    return text or "NONE"
