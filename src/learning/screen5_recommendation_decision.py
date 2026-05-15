"""Phase 7BF Screen 5 recommendation decision object models.

The records in this module describe future Screen 5 recommendation decision
metadata only. They do not persist records, implement UI, invoke write paths,
execute analysis, modify dashboards, modify CLI behavior, or mutate
deterministic recommendation truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


RECOMMENDATION_DECISION_TYPES = (
    "accept_recommendation",
    "reject_recommendation",
    "defer_recommendation",
    "mark_not_applicable",
    "request_recommendation_review",
    "request_learning_candidate",
)

RECOMMENDATION_DECISION_STATUSES = (
    "proposed",
    "accepted",
    "rejected",
    "deferred",
    "not_applicable",
    "under_review",
    "routed_to_governance",
    "closed",
)

RECOMMENDATION_FOLLOWUP_TYPES = (
    "none",
    "action_required",
    "outcome_required",
    "feedback_required",
    "recommendation_review_required",
    "learning_candidate_review_required",
    "human_review_required",
)

RECOMMENDATION_DECISION_VALIDATION_STATUSES = (
    "valid",
    "invalid",
    "needs_actor",
    "needs_recommendation",
    "unsupported_decision",
    "write_not_allowed_in_this_phase",
)

DECISION_TYPE_TO_STATUS = {
    "accept_recommendation": "accepted",
    "reject_recommendation": "rejected",
    "defer_recommendation": "deferred",
    "mark_not_applicable": "not_applicable",
    "request_recommendation_review": "under_review",
    "request_learning_candidate": "routed_to_governance",
}

DECISION_TYPE_TO_FOLLOWUP = {
    "accept_recommendation": "action_required",
    "reject_recommendation": "feedback_required",
    "defer_recommendation": "human_review_required",
    "mark_not_applicable": "feedback_required",
    "request_recommendation_review": "recommendation_review_required",
    "request_learning_candidate": "learning_candidate_review_required",
}


class Screen5RecommendationDecisionError(ValueError):
    """Raised when Phase 7BF recommendation decision metadata is invalid."""


@dataclass(frozen=True)
class RecommendationDecisionRecord:
    """Governed decision metadata for a Screen 5 recommendation."""

    decision_id: str
    recommendation_id: str
    decision_type: str
    decision_status: str
    actor_id: str
    run_id: str | None = None
    awr_id: str | None = None
    domain: str | None = None
    recommendation_title: str | None = None
    actor_audit_context: dict[str, Any] | None = None
    decision_rationale: str | None = None
    decision_notes: str | None = None
    linked_action_id: str | None = None
    linked_outcome_id: str | None = None
    linked_feedback_id: str | None = None
    linked_candidate_intent_id: str | None = None
    requires_followup: bool = False
    followup_type: str = "none"
    write_performed: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.decision_id, "decision_id")
        _require_nonempty_string(self.recommendation_id, "recommendation_id")
        _require_optional_string(self.run_id, "run_id")
        _require_optional_string(self.awr_id, "awr_id")
        _require_optional_string(self.domain, "domain")
        _require_optional_string(
            self.recommendation_title,
            "recommendation_title",
        )
        _require_supported(
            self.decision_type,
            RECOMMENDATION_DECISION_TYPES,
            "decision_type",
        )
        _require_supported(
            self.decision_status,
            RECOMMENDATION_DECISION_STATUSES,
            "decision_status",
        )
        _require_nonempty_string(self.actor_id, "actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        _require_optional_string(self.decision_rationale, "decision_rationale")
        _require_optional_string(self.decision_notes, "decision_notes")
        _require_optional_string(self.linked_action_id, "linked_action_id")
        _require_optional_string(self.linked_outcome_id, "linked_outcome_id")
        _require_optional_string(self.linked_feedback_id, "linked_feedback_id")
        _require_optional_string(
            self.linked_candidate_intent_id,
            "linked_candidate_intent_id",
        )
        _require_boolean(self.requires_followup, "requires_followup")
        _require_supported(
            self.followup_type,
            RECOMMENDATION_FOLLOWUP_TYPES,
            "followup_type",
        )
        _require_boolean(self.write_performed, "write_performed")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _require_boolean(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _reject_true(self.write_performed, "write_performed")
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class RecommendationDecisionRequest:
    """Request metadata for future Screen 5 recommendation decision handling."""

    request_id: str
    recommendation_id: str | None
    requested_decision: str
    actor_id: str | None
    actor_audit_context: dict[str, Any] | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    validation_status: str = "valid"
    can_route_to_write_path: bool = False
    write_performed: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.request_id, "request_id")
        _require_optional_string(self.recommendation_id, "recommendation_id")
        _require_supported(
            self.requested_decision,
            RECOMMENDATION_DECISION_TYPES,
            "requested_decision",
        )
        _require_optional_string(self.actor_id, "actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        _require_mapping(self.payload, "payload")
        _require_supported(
            self.validation_status,
            RECOMMENDATION_DECISION_VALIDATION_STATUSES,
            "validation_status",
        )
        _require_boolean(self.can_route_to_write_path, "can_route_to_write_path")
        _require_boolean(self.write_performed, "write_performed")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _require_boolean(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _reject_true(self.write_performed, "write_performed")
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class RecommendationDecisionValidation:
    """Validation result metadata for a recommendation decision request."""

    validation_id: str
    request_id: str
    valid: bool
    validation_status: str
    requested_decision: str
    actor_present: bool
    recommendation_present: bool
    can_route_to_write_path: bool = False
    write_performed: bool = False
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.validation_id, "validation_id")
        _require_nonempty_string(self.request_id, "request_id")
        _require_boolean(self.valid, "valid")
        _require_supported(
            self.validation_status,
            RECOMMENDATION_DECISION_VALIDATION_STATUSES,
            "validation_status",
        )
        _require_supported(
            self.requested_decision,
            RECOMMENDATION_DECISION_TYPES,
            "requested_decision",
        )
        _require_boolean(self.actor_present, "actor_present")
        _require_boolean(self.recommendation_present, "recommendation_present")
        _require_boolean(self.can_route_to_write_path, "can_route_to_write_path")
        _require_boolean(self.write_performed, "write_performed")
        _require_string_list(self.denied_reasons, "denied_reasons")
        _require_string_list(self.warnings, "warnings")
        _require_string_list(self.required_next_steps, "required_next_steps")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _require_boolean(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _reject_true(self.write_performed, "write_performed")
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.notes, "notes")


def create_recommendation_decision_id(
    recommendation_id: str,
    decision_type: str,
    run_id: str | None = None,
    awr_id: str | None = None,
) -> str:
    """Create a deterministic Screen 5 recommendation decision id."""

    _require_nonempty_string(recommendation_id, "recommendation_id")
    _require_supported(
        decision_type,
        RECOMMENDATION_DECISION_TYPES,
        "decision_type",
    )
    _require_optional_string(run_id, "run_id")
    _require_optional_string(awr_id, "awr_id")
    run_or_awr = run_id or awr_id or "local"
    return (
        "SCREEN5-RECO-DECISION-"
        f"{_normalize_token(recommendation_id)}-"
        f"{_normalize_token(decision_type)}-"
        f"{_normalize_token(run_or_awr)}"
    )


def create_recommendation_decision_request_id(
    recommendation_id: str,
    requested_decision: str,
) -> str:
    """Create a deterministic Screen 5 recommendation decision request id."""

    _require_nonempty_string(recommendation_id, "recommendation_id")
    _require_supported(
        requested_decision,
        RECOMMENDATION_DECISION_TYPES,
        "requested_decision",
    )
    return (
        "SCREEN5-RECO-REQUEST-"
        f"{_normalize_token(recommendation_id)}-"
        f"{_normalize_token(requested_decision)}"
    )


def create_recommendation_decision_validation_id(request_id: str) -> str:
    """Create a deterministic Screen 5 recommendation validation id."""

    _require_nonempty_string(request_id, "request_id")
    return f"SCREEN5-RECO-VALIDATION-{_normalize_token(request_id)}"


def decision_status_for_type(decision_type: str) -> str:
    """Return the metadata-only status implied by a decision type."""

    _require_supported(
        decision_type,
        RECOMMENDATION_DECISION_TYPES,
        "decision_type",
    )
    return DECISION_TYPE_TO_STATUS[decision_type]


def followup_type_for_decision(decision_type: str) -> str:
    """Return the metadata-only follow-up implied by a decision type."""

    _require_supported(
        decision_type,
        RECOMMENDATION_DECISION_TYPES,
        "decision_type",
    )
    return DECISION_TYPE_TO_FOLLOWUP[decision_type]


def validate_recommendation_decision_record(
    record: RecommendationDecisionRecord,
) -> RecommendationDecisionRecord:
    """Validate and return recommendation decision metadata."""

    if not isinstance(record, RecommendationDecisionRecord):
        raise Screen5RecommendationDecisionError(
            "record must be a RecommendationDecisionRecord instance."
        )
    record.__post_init__()
    return record


def validate_recommendation_decision_request(
    request: RecommendationDecisionRequest,
) -> RecommendationDecisionRequest:
    """Validate and return recommendation decision request metadata."""

    if not isinstance(request, RecommendationDecisionRequest):
        raise Screen5RecommendationDecisionError(
            "request must be a RecommendationDecisionRequest instance."
        )
    request.__post_init__()
    _require_nonempty_string(request.recommendation_id, "recommendation_id")
    _require_nonempty_string(request.actor_id, "actor_id")
    return request


def validate_recommendation_decision_validation(
    validation: RecommendationDecisionValidation,
) -> RecommendationDecisionValidation:
    """Validate and return recommendation decision validation metadata."""

    if not isinstance(validation, RecommendationDecisionValidation):
        raise Screen5RecommendationDecisionError(
            "validation must be a RecommendationDecisionValidation instance."
        )
    validation.__post_init__()
    return validation


def evaluate_recommendation_decision_request(
    request: RecommendationDecisionRequest,
) -> RecommendationDecisionValidation:
    """Evaluate request metadata without persistence or runtime mutation."""

    if not isinstance(request, RecommendationDecisionRequest):
        raise Screen5RecommendationDecisionError(
            "request must be a RecommendationDecisionRequest instance."
        )
    request.__post_init__()
    actor_present = bool(_optional_text(request.actor_id))
    recommendation_present = bool(_optional_text(request.recommendation_id))
    denied_reasons: list[str] = []
    required_next_steps: list[str] = []
    warnings = [
        "Recommendation decision metadata is not persistence.",
        "Governed write path is required before future record creation.",
    ]

    if not actor_present:
        validation_status = "needs_actor"
        denied_reasons.append("actor_id is required for recommendation decisions")
        required_next_steps.append("provide Phase 7AE actor identity")
    elif not recommendation_present:
        validation_status = "needs_recommendation"
        denied_reasons.append("recommendation_id is required")
        required_next_steps.append("provide recommendation reference")
    else:
        validation_status = "valid"
        if request.can_route_to_write_path:
            required_next_steps.append("route through future governed write path")
        else:
            required_next_steps.append("declare future governed write-path eligibility")

    return RecommendationDecisionValidation(
        validation_id=create_recommendation_decision_validation_id(
            request.request_id
        ),
        request_id=request.request_id,
        valid=validation_status == "valid",
        validation_status=validation_status,
        requested_decision=request.requested_decision,
        actor_present=actor_present,
        recommendation_present=recommendation_present,
        can_route_to_write_path=(
            request.can_route_to_write_path and validation_status == "valid"
        ),
        write_performed=False,
        denied_reasons=denied_reasons,
        warnings=warnings,
        required_next_steps=required_next_steps,
        runtime_influence=False,
        phase4i_mutation_requested=False,
        notes=request.notes,
    )


def recommendation_decision_record_to_dict(
    record: RecommendationDecisionRecord,
) -> dict[str, Any]:
    """Serialize recommendation decision metadata to a deterministic dict."""

    record = validate_recommendation_decision_record(record)
    return {
        "decision_id": record.decision_id,
        "recommendation_id": record.recommendation_id,
        "run_id": record.run_id,
        "awr_id": record.awr_id,
        "domain": record.domain,
        "recommendation_title": record.recommendation_title,
        "decision_type": record.decision_type,
        "decision_status": record.decision_status,
        "actor_id": record.actor_id,
        "actor_audit_context": _copy_optional_mapping(record.actor_audit_context),
        "decision_rationale": record.decision_rationale,
        "decision_notes": record.decision_notes,
        "linked_action_id": record.linked_action_id,
        "linked_outcome_id": record.linked_outcome_id,
        "linked_feedback_id": record.linked_feedback_id,
        "linked_candidate_intent_id": record.linked_candidate_intent_id,
        "requires_followup": record.requires_followup,
        "followup_type": record.followup_type,
        "write_performed": record.write_performed,
        "runtime_influence": record.runtime_influence,
        "phase4i_mutation_requested": record.phase4i_mutation_requested,
        "created_at": record.created_at,
        "notes": record.notes,
    }


def recommendation_decision_record_from_dict(
    data: dict[str, Any],
) -> RecommendationDecisionRecord:
    """Deserialize recommendation decision metadata from a dictionary."""

    _require_mapping(data, "data")
    return RecommendationDecisionRecord(
        decision_id=str(data["decision_id"]),
        recommendation_id=str(data["recommendation_id"]),
        run_id=_optional_text(data.get("run_id")),
        awr_id=_optional_text(data.get("awr_id")),
        domain=_optional_text(data.get("domain")),
        recommendation_title=_optional_text(data.get("recommendation_title")),
        decision_type=str(data["decision_type"]),
        decision_status=str(data["decision_status"]),
        actor_id=str(data["actor_id"]),
        actor_audit_context=_copy_optional_mapping(data.get("actor_audit_context")),
        decision_rationale=_optional_text(data.get("decision_rationale")),
        decision_notes=_optional_text(data.get("decision_notes")),
        linked_action_id=_optional_text(data.get("linked_action_id")),
        linked_outcome_id=_optional_text(data.get("linked_outcome_id")),
        linked_feedback_id=_optional_text(data.get("linked_feedback_id")),
        linked_candidate_intent_id=_optional_text(
            data.get("linked_candidate_intent_id")
        ),
        requires_followup=_bool_from_mapping(data, "requires_followup", False),
        followup_type=str(data.get("followup_type", "none")),
        write_performed=_bool_from_mapping(data, "write_performed", False),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        created_at=_optional_text(data.get("created_at")),
        notes=_optional_text(data.get("notes")),
    )


def recommendation_decision_request_to_dict(
    request: RecommendationDecisionRequest,
) -> dict[str, Any]:
    """Serialize recommendation decision request metadata."""

    request.__post_init__()
    return {
        "request_id": request.request_id,
        "recommendation_id": request.recommendation_id,
        "requested_decision": request.requested_decision,
        "actor_id": request.actor_id,
        "actor_audit_context": _copy_optional_mapping(request.actor_audit_context),
        "payload": dict(request.payload),
        "validation_status": request.validation_status,
        "can_route_to_write_path": request.can_route_to_write_path,
        "write_performed": request.write_performed,
        "runtime_influence": request.runtime_influence,
        "phase4i_mutation_requested": request.phase4i_mutation_requested,
        "notes": request.notes,
    }


def recommendation_decision_request_from_dict(
    data: dict[str, Any],
) -> RecommendationDecisionRequest:
    """Deserialize recommendation decision request metadata from a dictionary."""

    _require_mapping(data, "data")
    return RecommendationDecisionRequest(
        request_id=str(data["request_id"]),
        recommendation_id=_optional_text(data.get("recommendation_id")),
        requested_decision=str(data["requested_decision"]),
        actor_id=_optional_text(data.get("actor_id")),
        actor_audit_context=_copy_optional_mapping(data.get("actor_audit_context")),
        payload=dict(data.get("payload") or {}),
        validation_status=str(data.get("validation_status", "valid")),
        can_route_to_write_path=_bool_from_mapping(
            data,
            "can_route_to_write_path",
            False,
        ),
        write_performed=_bool_from_mapping(data, "write_performed", False),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        notes=_optional_text(data.get("notes")),
    )


def recommendation_decision_validation_to_dict(
    validation: RecommendationDecisionValidation,
) -> dict[str, Any]:
    """Serialize recommendation decision validation metadata."""

    validation = validate_recommendation_decision_validation(validation)
    return {
        "validation_id": validation.validation_id,
        "request_id": validation.request_id,
        "valid": validation.valid,
        "validation_status": validation.validation_status,
        "requested_decision": validation.requested_decision,
        "actor_present": validation.actor_present,
        "recommendation_present": validation.recommendation_present,
        "can_route_to_write_path": validation.can_route_to_write_path,
        "write_performed": validation.write_performed,
        "denied_reasons": list(validation.denied_reasons),
        "warnings": list(validation.warnings),
        "required_next_steps": list(validation.required_next_steps),
        "runtime_influence": validation.runtime_influence,
        "phase4i_mutation_requested": validation.phase4i_mutation_requested,
        "notes": validation.notes,
    }


def recommendation_decision_validation_from_dict(
    data: dict[str, Any],
) -> RecommendationDecisionValidation:
    """Deserialize recommendation decision validation metadata from a dict."""

    _require_mapping(data, "data")
    return RecommendationDecisionValidation(
        validation_id=str(data["validation_id"]),
        request_id=str(data["request_id"]),
        valid=_bool_from_mapping(data, "valid", False),
        validation_status=str(data["validation_status"]),
        requested_decision=str(data["requested_decision"]),
        actor_present=_bool_from_mapping(data, "actor_present", False),
        recommendation_present=_bool_from_mapping(
            data,
            "recommendation_present",
            False,
        ),
        can_route_to_write_path=_bool_from_mapping(
            data,
            "can_route_to_write_path",
            False,
        ),
        write_performed=_bool_from_mapping(data, "write_performed", False),
        denied_reasons=list(data.get("denied_reasons") or []),
        warnings=list(data.get("warnings") or []),
        required_next_steps=list(data.get("required_next_steps") or []),
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
    raise Screen5RecommendationDecisionError(f"{field_name} must be a boolean.")


def _copy_optional_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Screen5RecommendationDecisionError(
            "mapping value must be a dictionary."
        )
    return dict(value)


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise Screen5RecommendationDecisionError(f"{field_name} must be a mapping.")


def _require_optional_mapping(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, dict):
        raise Screen5RecommendationDecisionError(
            f"{field_name} must be a mapping or None."
        )


def _require_nonempty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise Screen5RecommendationDecisionError(
            f"{field_name} must be a non-empty string."
        )


def _require_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise Screen5RecommendationDecisionError(
            f"{field_name} must be a string or None."
        )


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        raise Screen5RecommendationDecisionError(
            f"{field_name} must be one of: {', '.join(supported)}."
        )


def _require_boolean(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise Screen5RecommendationDecisionError(f"{field_name} must be a boolean.")


def _require_string_list(value: Any, field_name: str) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise Screen5RecommendationDecisionError(
            f"{field_name} must be a list of strings."
        )


def _reject_true(value: bool, field_name: str) -> None:
    if value:
        raise Screen5RecommendationDecisionError(
            f"{field_name} must remain false in Phase 7BF."
        )


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text).strip("-")
    return text or "NONE"
