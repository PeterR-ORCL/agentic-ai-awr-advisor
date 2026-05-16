"""Phase 7BM Screen 6 materialization review preview models.

The records in this module describe local metadata for future Screen 6
materialization review. They do not persist review records, transition
materialization status, attach validation or rollback references, invoke
governed write paths, execute analysis, modify dashboards, modify CLI
behavior, write databases, write files, import runtime
parser/scoring/decision/recommendation modules, activate runtime, or mutate
Phase 4I.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


MATERIALIZATION_REVIEW_ACTIONS = (
    "mark_under_review",
    "approve_for_validation",
    "reject",
    "request_revision",
    "attach_validation_reference",
    "attach_rollback_reference",
    "mark_validated",
    "mark_implemented",
    "close_materialization",
    "add_materialization_note",
)

MATERIALIZATION_REVIEW_RESULT_STATUSES = (
    "preview_only",
    "valid_for_future_review",
    "needs_actor",
    "needs_materialization",
    "needs_validation_reference",
    "needs_rollback_reference",
    "unsupported_action",
    "write_not_allowed_in_this_phase",
    "blocked_by_runtime_safety",
)

MATERIALIZATION_REVIEW_TYPES = (
    "parser_mapping_artifact",
    "scoring_review_artifact",
    "recommendation_rule_artifact",
    "dashboard_wording_artifact",
    "dashboard_interaction_artifact",
    "governance_workflow_artifact",
    "semantic_summary_artifact",
    "documentation_artifact",
    "validation_artifact",
    "unknown",
)

ACTION_TO_PROPOSED_NEXT_STATUS = {
    "mark_under_review": "under_review",
    "approve_for_validation": "approved_for_validation",
    "reject": "rejected",
    "request_revision": "needs_revision",
    "attach_validation_reference": "proposed",
    "attach_rollback_reference": "proposed",
    "mark_validated": "validated",
    "mark_implemented": "implemented",
    "close_materialization": "closed",
    "add_materialization_note": "proposed",
}


class Screen6MaterializationReviewError(ValueError):
    """Raised when Phase 7BM materialization review metadata is invalid."""


@dataclass(frozen=True)
class MaterializationReviewRequest:
    """A future request to review a Screen 6 materialization artifact."""

    review_request_id: str
    materialization_id: str | None
    materialization_type: str
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
    materialization_status_changed: bool = False
    validation_reference_attached: bool = False
    rollback_reference_attached: bool = False
    runtime_activation_requested: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.review_request_id, "review_request_id")
        _require_optional_string(self.materialization_id, "materialization_id")
        _require_nonempty_string(self.materialization_type, "materialization_type")
        _require_nonempty_string(self.requested_action, "requested_action")
        _require_optional_string(self.actor_id, "actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        _require_optional_string(self.governance_note, "governance_note")
        _require_optional_string(self.validation_reference, "validation_reference")
        _require_optional_string(self.rollback_reference, "rollback_reference")
        _require_mapping(self.payload, "payload")
        _require_supported(
            self.validation_status,
            MATERIALIZATION_REVIEW_RESULT_STATUSES,
            "validation_status",
        )
        _require_boolean(self.can_route_to_write_path, "can_route_to_write_path")
        _require_false(self.write_performed, "write_performed")
        _require_false(
            self.materialization_status_changed,
            "materialization_status_changed",
        )
        _require_false(
            self.validation_reference_attached,
            "validation_reference_attached",
        )
        _require_false(
            self.rollback_reference_attached,
            "rollback_reference_attached",
        )
        _require_false(
            self.runtime_activation_requested,
            "runtime_activation_requested",
        )
        _require_false(self.runtime_influence, "runtime_influence")
        _require_false(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class MaterializationReviewResult:
    """A local preview result for a materialization review request."""

    review_result_id: str
    review_request_id: str
    materialization_id: str
    materialization_type: str
    requested_action: str
    result_status: str
    materialization_status_changed: bool = False
    proposed_next_status: str | None = None
    governance_action_performed: bool = False
    validation_reference_attached: bool = False
    rollback_reference_attached: bool = False
    write_performed: bool = False
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    runtime_activation_requested: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.review_result_id, "review_result_id")
        _require_nonempty_string(self.review_request_id, "review_request_id")
        _require_nonempty_string(self.materialization_id, "materialization_id")
        _require_supported(
            self.materialization_type,
            MATERIALIZATION_REVIEW_TYPES,
            "materialization_type",
        )
        _require_nonempty_string(self.requested_action, "requested_action")
        _require_supported(
            self.result_status,
            MATERIALIZATION_REVIEW_RESULT_STATUSES,
            "result_status",
        )
        _require_false(
            self.materialization_status_changed,
            "materialization_status_changed",
        )
        _require_optional_string(self.proposed_next_status, "proposed_next_status")
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
            self.runtime_activation_requested,
            "runtime_activation_requested",
        )
        _require_false(self.runtime_influence, "runtime_influence")
        _require_false(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.notes, "notes")


def create_materialization_review_request_id(
    materialization_id: str,
    requested_action: str,
) -> str:
    """Create a deterministic Screen 6 materialization review request id."""

    _require_nonempty_string(materialization_id, "materialization_id")
    _require_supported(
        requested_action,
        MATERIALIZATION_REVIEW_ACTIONS,
        "requested_action",
    )
    return (
        "SCREEN6-MATERIALIZATION-REVIEW-REQUEST-"
        f"{_normalize_token(materialization_id)}-"
        f"{_normalize_token(requested_action)}"
    )


def create_materialization_review_result_id(review_request_id: str) -> str:
    """Create a deterministic Screen 6 materialization review result id."""

    _require_nonempty_string(review_request_id, "review_request_id")
    return f"SCREEN6-MATERIALIZATION-REVIEW-RESULT-{_normalize_token(review_request_id)}"


def proposed_next_status_for_action(requested_action: str) -> str:
    """Return the preview-only status implied by a materialization action."""

    _require_supported(
        requested_action,
        MATERIALIZATION_REVIEW_ACTIONS,
        "requested_action",
    )
    return ACTION_TO_PROPOSED_NEXT_STATUS[requested_action]


def validate_materialization_review_request(
    request: MaterializationReviewRequest,
) -> MaterializationReviewRequest:
    """Validate and return materialization review request metadata."""

    if not isinstance(request, MaterializationReviewRequest):
        raise Screen6MaterializationReviewError(
            "request must be a MaterializationReviewRequest instance."
        )
    request.__post_init__()
    _require_nonempty_string(request.materialization_id, "materialization_id")
    _require_supported(
        request.materialization_type,
        MATERIALIZATION_REVIEW_TYPES,
        "materialization_type",
    )
    _require_supported(
        request.requested_action,
        MATERIALIZATION_REVIEW_ACTIONS,
        "requested_action",
    )
    _require_nonempty_string(request.actor_id, "actor_id")
    return request


def validate_materialization_review_result(
    result: MaterializationReviewResult,
) -> MaterializationReviewResult:
    """Validate and return materialization review result metadata."""

    if not isinstance(result, MaterializationReviewResult):
        raise Screen6MaterializationReviewError(
            "result must be a MaterializationReviewResult instance."
        )
    result.__post_init__()
    _require_supported(
        result.requested_action,
        MATERIALIZATION_REVIEW_ACTIONS,
        "requested_action",
    )
    _require_supported(
        result.result_status,
        MATERIALIZATION_REVIEW_RESULT_STATUSES,
        "result_status",
    )
    return result


def evaluate_materialization_review_request(
    request: MaterializationReviewRequest,
) -> MaterializationReviewResult:
    """Evaluate request metadata without writes or materialization mutation."""

    if not isinstance(request, MaterializationReviewRequest):
        raise Screen6MaterializationReviewError(
            "request must be a MaterializationReviewRequest instance."
        )
    request.__post_init__()

    actor_present = bool(_optional_text(request.actor_id))
    materialization_present = bool(_optional_text(request.materialization_id))
    action_supported = request.requested_action in MATERIALIZATION_REVIEW_ACTIONS
    denied_reasons: list[str] = []
    required_next_steps: list[str] = []
    warnings = [
        "Materialization review is preview-only in Phase 7BM.",
        "Governed write path is required before future state changes.",
        "Materialization status is not changed in this phase.",
    ]

    if not actor_present:
        result_status = "needs_actor"
        denied_reasons.append("actor_id is required for materialization review")
        required_next_steps.append("provide Phase 7AE actor identity")
    elif not materialization_present:
        result_status = "needs_materialization"
        denied_reasons.append("materialization_id is required")
        required_next_steps.append("provide materialization artifact reference")
    elif not action_supported:
        result_status = "unsupported_action"
        denied_reasons.append("requested_action is not supported")
        required_next_steps.append("choose a supported Phase 7BM preview action")
    elif (
        request.requested_action == "attach_validation_reference"
        and not _optional_text(request.validation_reference)
    ):
        result_status = "needs_validation_reference"
        denied_reasons.append("validation_reference is required for this preview")
        required_next_steps.append("provide validation reference before future write routing")
    elif (
        request.requested_action == "attach_rollback_reference"
        and not _optional_text(request.rollback_reference)
    ):
        result_status = "needs_rollback_reference"
        denied_reasons.append("rollback_reference is required for this preview")
        required_next_steps.append("provide rollback reference before future write routing")
    else:
        result_status = "valid_for_future_review"
        required_next_steps.append("route through future Phase 7AG governed write path")
        required_next_steps.append("capture audit through future Screen 6 governance workflow")

    if request.materialization_type not in MATERIALIZATION_REVIEW_TYPES:
        warnings.append("Materialization type must be supported before future write routing.")

    if (
        request.write_performed
        or request.materialization_status_changed
        or request.validation_reference_attached
        or request.rollback_reference_attached
        or request.runtime_activation_requested
        or request.runtime_influence
        or request.phase4i_mutation_requested
    ):
        result_status = "blocked_by_runtime_safety"
        denied_reasons.append("runtime or mutation flags are not allowed in Phase 7BM")

    proposed_next_status = (
        ACTION_TO_PROPOSED_NEXT_STATUS.get(request.requested_action)
        if action_supported
        else None
    )

    return MaterializationReviewResult(
        review_result_id=create_materialization_review_result_id(
            request.review_request_id
        ),
        review_request_id=request.review_request_id,
        materialization_id=(
            _optional_text(request.materialization_id) or "MISSING-MATERIALIZATION"
        ),
        materialization_type=(
            request.materialization_type
            if request.materialization_type in MATERIALIZATION_REVIEW_TYPES
            else "unknown"
        ),
        requested_action=request.requested_action,
        result_status=result_status,
        materialization_status_changed=False,
        proposed_next_status=proposed_next_status,
        governance_action_performed=False,
        validation_reference_attached=False,
        rollback_reference_attached=False,
        write_performed=False,
        denied_reasons=denied_reasons,
        warnings=warnings,
        required_next_steps=required_next_steps,
        runtime_activation_requested=False,
        runtime_influence=False,
        phase4i_mutation_requested=False,
        notes=request.notes,
    )


def materialization_review_request_to_dict(
    request: MaterializationReviewRequest,
) -> dict[str, Any]:
    """Serialize materialization review request metadata."""

    request.__post_init__()
    return {
        "review_request_id": request.review_request_id,
        "materialization_id": request.materialization_id,
        "materialization_type": request.materialization_type,
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
        "materialization_status_changed": request.materialization_status_changed,
        "validation_reference_attached": request.validation_reference_attached,
        "rollback_reference_attached": request.rollback_reference_attached,
        "runtime_activation_requested": request.runtime_activation_requested,
        "runtime_influence": request.runtime_influence,
        "phase4i_mutation_requested": request.phase4i_mutation_requested,
        "created_at": request.created_at,
        "notes": request.notes,
    }


def materialization_review_request_from_dict(
    data: dict[str, Any],
) -> MaterializationReviewRequest:
    """Deserialize materialization review request metadata from a dictionary."""

    _require_mapping(data, "data")
    return MaterializationReviewRequest(
        review_request_id=str(data["review_request_id"]),
        materialization_id=_optional_text(data.get("materialization_id")),
        materialization_type=str(data["materialization_type"]),
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
        materialization_status_changed=_bool_from_mapping(
            data,
            "materialization_status_changed",
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
        runtime_activation_requested=_bool_from_mapping(
            data,
            "runtime_activation_requested",
            False,
        ),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        created_at=_optional_text(data.get("created_at")),
        notes=_optional_text(data.get("notes")),
    )


def materialization_review_result_to_dict(
    result: MaterializationReviewResult,
) -> dict[str, Any]:
    """Serialize materialization review result metadata."""

    result.__post_init__()
    return {
        "review_result_id": result.review_result_id,
        "review_request_id": result.review_request_id,
        "materialization_id": result.materialization_id,
        "materialization_type": result.materialization_type,
        "requested_action": result.requested_action,
        "result_status": result.result_status,
        "materialization_status_changed": result.materialization_status_changed,
        "proposed_next_status": result.proposed_next_status,
        "governance_action_performed": result.governance_action_performed,
        "validation_reference_attached": result.validation_reference_attached,
        "rollback_reference_attached": result.rollback_reference_attached,
        "write_performed": result.write_performed,
        "denied_reasons": list(result.denied_reasons),
        "warnings": list(result.warnings),
        "required_next_steps": list(result.required_next_steps),
        "runtime_activation_requested": result.runtime_activation_requested,
        "runtime_influence": result.runtime_influence,
        "phase4i_mutation_requested": result.phase4i_mutation_requested,
        "notes": result.notes,
    }


def materialization_review_result_from_dict(
    data: dict[str, Any],
) -> MaterializationReviewResult:
    """Deserialize materialization review result metadata from a dictionary."""

    _require_mapping(data, "data")
    return MaterializationReviewResult(
        review_result_id=str(data["review_result_id"]),
        review_request_id=str(data["review_request_id"]),
        materialization_id=str(data["materialization_id"]),
        materialization_type=str(data["materialization_type"]),
        requested_action=str(data["requested_action"]),
        result_status=str(data["result_status"]),
        materialization_status_changed=_bool_from_mapping(
            data,
            "materialization_status_changed",
            False,
        ),
        proposed_next_status=_optional_text(data.get("proposed_next_status")),
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
        runtime_activation_requested=_bool_from_mapping(
            data,
            "runtime_activation_requested",
            False,
        ),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
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
    raise Screen6MaterializationReviewError(f"{field_name} must be a boolean.")


def _copy_optional_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Screen6MaterializationReviewError(
            "mapping value must be a dictionary."
        )
    return dict(value)


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise Screen6MaterializationReviewError(
            f"{field_name} must be a mapping."
        )


def _require_optional_mapping(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, dict):
        raise Screen6MaterializationReviewError(
            f"{field_name} must be a mapping or None."
        )


def _require_nonempty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise Screen6MaterializationReviewError(
            f"{field_name} must be a non-empty string."
        )


def _require_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise Screen6MaterializationReviewError(
            f"{field_name} must be a string or None."
        )


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        raise Screen6MaterializationReviewError(
            f"{field_name} must be one of: {', '.join(supported)}."
        )


def _require_boolean(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise Screen6MaterializationReviewError(
            f"{field_name} must be a boolean."
        )


def _require_false(value: Any, field_name: str) -> None:
    _require_boolean(value, field_name)
    if value:
        raise Screen6MaterializationReviewError(
            f"{field_name} must remain false in Phase 7BM."
        )


def _require_string_list(value: Any, field_name: str) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise Screen6MaterializationReviewError(
            f"{field_name} must be a list of strings."
        )


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text).strip("-")
    return text or "NONE"
