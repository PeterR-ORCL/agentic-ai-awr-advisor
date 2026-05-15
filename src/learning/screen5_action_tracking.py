"""Phase 7BG Screen 5 action tracking preview metadata.

This module exposes local deterministic preview metadata only. It does not
persist action records, update action state, create outcomes, create feedback,
invoke write paths, call backend code, import dashboard modules, or import
runtime parser, scoring, decision, or recommendation modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


ACTION_TRACKING_STATUSES = (
    "proposed",
    "assigned",
    "in_progress",
    "implemented",
    "blocked",
    "cancelled",
    "closed",
)

ACTION_TRACKING_VALIDATION_STATUSES = (
    "valid",
    "invalid",
    "needs_actor",
    "needs_recommendation",
    "write_not_allowed_in_this_phase",
)


class Screen5ActionTrackingError(ValueError):
    """Raised when Phase 7BG action tracking preview metadata is invalid."""


@dataclass(frozen=True)
class ActionAssignmentPreview:
    """Preview metadata for future Screen 5 action assignment."""

    action_preview_id: str
    recommendation_id: str | None
    action_title: str
    assigned_owner: str | None = None
    owner_role: str | None = None
    due_date: str | None = None
    action_status: str = "proposed"
    actor_id: str | None = None
    actor_audit_context: dict[str, Any] | None = None
    write_performed: bool = False
    outcome_created: bool = False
    feedback_created: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.action_preview_id, "action_preview_id")
        _require_optional_string(self.recommendation_id, "recommendation_id")
        _require_nonempty_string(self.action_title, "action_title")
        _require_optional_string(self.assigned_owner, "assigned_owner")
        _require_optional_string(self.owner_role, "owner_role")
        _require_optional_string(self.due_date, "due_date")
        _require_supported(self.action_status, ACTION_TRACKING_STATUSES, "action_status")
        _require_optional_string(self.actor_id, "actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        _require_boolean(self.write_performed, "write_performed")
        _require_boolean(self.outcome_created, "outcome_created")
        _require_boolean(self.feedback_created, "feedback_created")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _require_boolean(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _reject_true(self.write_performed, "write_performed")
        _reject_true(self.outcome_created, "outcome_created")
        _reject_true(self.feedback_created, "feedback_created")
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class ActionTrackingValidation:
    """Validation metadata for a Screen 5 action tracking preview."""

    validation_id: str
    action_preview_id: str
    valid: bool
    validation_status: str
    actor_present: bool
    recommendation_present: bool
    write_performed: bool = False
    outcome_created: bool = False
    feedback_created: bool = False
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_nonempty_string(self.validation_id, "validation_id")
        _require_nonempty_string(self.action_preview_id, "action_preview_id")
        _require_boolean(self.valid, "valid")
        _require_supported(
            self.validation_status,
            ACTION_TRACKING_VALIDATION_STATUSES,
            "validation_status",
        )
        _require_boolean(self.actor_present, "actor_present")
        _require_boolean(self.recommendation_present, "recommendation_present")
        _require_boolean(self.write_performed, "write_performed")
        _require_boolean(self.outcome_created, "outcome_created")
        _require_boolean(self.feedback_created, "feedback_created")
        _require_string_list(self.denied_reasons, "denied_reasons")
        _require_string_list(self.warnings, "warnings")
        _require_string_list(self.required_next_steps, "required_next_steps")
        _reject_true(self.write_performed, "write_performed")
        _reject_true(self.outcome_created, "outcome_created")
        _reject_true(self.feedback_created, "feedback_created")


def build_action_assignment_preview_id(
    recommendation_id: str | None,
    action_title: str,
) -> str:
    """Create a deterministic Screen 5 action assignment preview id."""

    _require_optional_string(recommendation_id, "recommendation_id")
    _require_nonempty_string(action_title, "action_title")
    return (
        "SCREEN5-ACTION-PREVIEW-"
        f"{_normalize_token(recommendation_id or 'missing-recommendation')}-"
        f"{_normalize_token(action_title)}"
    )


def build_action_tracking_validation_id(action_preview_id: str) -> str:
    """Create a deterministic Screen 5 action preview validation id."""

    _require_nonempty_string(action_preview_id, "action_preview_id")
    return f"SCREEN5-ACTION-VALIDATION-{_normalize_token(action_preview_id)}"


def validate_action_assignment_preview(
    preview: ActionAssignmentPreview,
) -> ActionAssignmentPreview:
    """Validate and return action assignment preview metadata."""

    if not isinstance(preview, ActionAssignmentPreview):
        raise Screen5ActionTrackingError(
            "preview must be an ActionAssignmentPreview instance."
        )
    preview.__post_init__()
    return preview


def validate_action_tracking_validation(
    validation: ActionTrackingValidation,
) -> ActionTrackingValidation:
    """Validate and return action tracking validation metadata."""

    if not isinstance(validation, ActionTrackingValidation):
        raise Screen5ActionTrackingError(
            "validation must be an ActionTrackingValidation instance."
        )
    validation.__post_init__()
    return validation


def evaluate_action_assignment_preview(
    preview: ActionAssignmentPreview,
) -> ActionTrackingValidation:
    """Evaluate preview metadata without writing action state."""

    validate_action_assignment_preview(preview)
    actor_present = bool(_optional_text(preview.actor_id))
    recommendation_present = bool(_optional_text(preview.recommendation_id))
    denied_reasons: list[str] = []
    required_next_steps: list[str] = []
    warnings = [
        "Action assignment is disabled in Phase 7BG.",
        "Governed write path is required before future action records.",
    ]

    if not actor_present:
        validation_status = "needs_actor"
        denied_reasons.append("actor_id is required before future action assignment")
        required_next_steps.append("provide Phase 7AE actor identity")
    elif not recommendation_present:
        validation_status = "needs_recommendation"
        denied_reasons.append("recommendation_id is required")
        required_next_steps.append("provide recommendation reference")
    else:
        validation_status = "valid"
        required_next_steps.append("route through future governed write path")

    return ActionTrackingValidation(
        validation_id=build_action_tracking_validation_id(preview.action_preview_id),
        action_preview_id=preview.action_preview_id,
        valid=validation_status == "valid",
        validation_status=validation_status,
        actor_present=actor_present,
        recommendation_present=recommendation_present,
        write_performed=False,
        outcome_created=False,
        feedback_created=False,
        denied_reasons=denied_reasons,
        warnings=warnings,
        required_next_steps=required_next_steps,
    )


def action_assignment_preview_to_dict(
    preview: ActionAssignmentPreview,
) -> dict[str, Any]:
    """Serialize action assignment preview metadata."""

    preview = validate_action_assignment_preview(preview)
    return {
        "action_preview_id": preview.action_preview_id,
        "recommendation_id": preview.recommendation_id,
        "action_title": preview.action_title,
        "assigned_owner": preview.assigned_owner,
        "owner_role": preview.owner_role,
        "due_date": preview.due_date,
        "action_status": preview.action_status,
        "actor_id": preview.actor_id,
        "actor_audit_context": _copy_optional_mapping(preview.actor_audit_context),
        "write_performed": preview.write_performed,
        "outcome_created": preview.outcome_created,
        "feedback_created": preview.feedback_created,
        "runtime_influence": preview.runtime_influence,
        "phase4i_mutation_requested": preview.phase4i_mutation_requested,
        "notes": preview.notes,
    }


def action_assignment_preview_from_dict(
    data: dict[str, Any],
) -> ActionAssignmentPreview:
    """Deserialize action assignment preview metadata."""

    _require_mapping(data, "data")
    return ActionAssignmentPreview(
        action_preview_id=str(data["action_preview_id"]),
        recommendation_id=_optional_text(data.get("recommendation_id")),
        action_title=str(data["action_title"]),
        assigned_owner=_optional_text(data.get("assigned_owner")),
        owner_role=_optional_text(data.get("owner_role")),
        due_date=_optional_text(data.get("due_date")),
        action_status=str(data.get("action_status", "proposed")),
        actor_id=_optional_text(data.get("actor_id")),
        actor_audit_context=_copy_optional_mapping(data.get("actor_audit_context")),
        write_performed=_bool_from_mapping(data, "write_performed", False),
        outcome_created=_bool_from_mapping(data, "outcome_created", False),
        feedback_created=_bool_from_mapping(data, "feedback_created", False),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        notes=_optional_text(data.get("notes")),
    )


def action_tracking_validation_to_dict(
    validation: ActionTrackingValidation,
) -> dict[str, Any]:
    """Serialize action tracking validation metadata."""

    validation = validate_action_tracking_validation(validation)
    return {
        "validation_id": validation.validation_id,
        "action_preview_id": validation.action_preview_id,
        "valid": validation.valid,
        "validation_status": validation.validation_status,
        "actor_present": validation.actor_present,
        "recommendation_present": validation.recommendation_present,
        "write_performed": validation.write_performed,
        "outcome_created": validation.outcome_created,
        "feedback_created": validation.feedback_created,
        "denied_reasons": list(validation.denied_reasons),
        "warnings": list(validation.warnings),
        "required_next_steps": list(validation.required_next_steps),
    }


def action_tracking_validation_from_dict(
    data: dict[str, Any],
) -> ActionTrackingValidation:
    """Deserialize action tracking validation metadata."""

    _require_mapping(data, "data")
    return ActionTrackingValidation(
        validation_id=str(data["validation_id"]),
        action_preview_id=str(data["action_preview_id"]),
        valid=_bool_from_mapping(data, "valid", False),
        validation_status=str(data["validation_status"]),
        actor_present=_bool_from_mapping(data, "actor_present", False),
        recommendation_present=_bool_from_mapping(
            data,
            "recommendation_present",
            False,
        ),
        write_performed=_bool_from_mapping(data, "write_performed", False),
        outcome_created=_bool_from_mapping(data, "outcome_created", False),
        feedback_created=_bool_from_mapping(data, "feedback_created", False),
        denied_reasons=list(data.get("denied_reasons") or []),
        warnings=list(data.get("warnings") or []),
        required_next_steps=list(data.get("required_next_steps") or []),
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
    raise Screen5ActionTrackingError(f"{field_name} must be a boolean.")


def _copy_optional_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Screen5ActionTrackingError("mapping value must be a dictionary.")
    return dict(value)


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise Screen5ActionTrackingError(f"{field_name} must be a mapping.")


def _require_optional_mapping(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, dict):
        raise Screen5ActionTrackingError(
            f"{field_name} must be a mapping or None."
        )


def _require_nonempty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise Screen5ActionTrackingError(
            f"{field_name} must be a non-empty string."
        )


def _require_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise Screen5ActionTrackingError(
            f"{field_name} must be a string or None."
        )


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        raise Screen5ActionTrackingError(
            f"{field_name} must be one of: {', '.join(supported)}."
        )


def _require_boolean(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise Screen5ActionTrackingError(f"{field_name} must be a boolean.")


def _require_string_list(value: Any, field_name: str) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise Screen5ActionTrackingError(
            f"{field_name} must be a list of strings."
        )


def _reject_true(value: bool, field_name: str) -> None:
    if value:
        raise Screen5ActionTrackingError(
            f"{field_name} must remain false in Phase 7BG."
        )


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text).strip("-")
    return text or "NONE"
