"""Phase 7BH Screen 5 outcome capture preview metadata.

This module exposes local deterministic preview metadata only. It does not
persist outcome records, update action records, create feedback, create labels,
create candidates, invoke write paths, call backend code, import dashboard
modules, or import runtime parser, scoring, decision, or recommendation modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


OUTCOME_CAPTURE_STATUSES = (
    "pending",
    "improved",
    "worsened",
    "no_change",
    "issue_recurred",
    "inconclusive",
    "closed",
)

OUTCOME_EFFECTIVENESS_VALUES = (
    "effective",
    "ineffective",
    "partially_effective",
    "not_applicable",
    "unknown",
)

OUTCOME_CAPTURE_VALIDATION_STATUSES = (
    "valid",
    "invalid",
    "needs_actor",
    "needs_recommendation",
    "needs_action",
    "write_not_allowed_in_this_phase",
)


class Screen5OutcomeCaptureError(ValueError):
    """Raised when Phase 7BH outcome capture preview metadata is invalid."""


@dataclass(frozen=True)
class OutcomeCapturePreview:
    """Preview metadata for future Screen 5 outcome capture."""

    outcome_preview_id: str
    recommendation_id: str | None
    linked_action_id: str | None
    outcome_status: str = "pending"
    outcome_effectiveness: str = "unknown"
    issue_recurred: bool | None = None
    followup_awr: str | None = None
    followup_run: str | None = None
    implementation_date: str | None = None
    outcome_notes: str | None = None
    actor_id: str | None = None
    actor_audit_context: dict[str, Any] | None = None
    write_performed: bool = False
    outcome_created: bool = False
    feedback_created: bool = False
    label_created: bool = False
    candidate_created: bool = False
    scoring_mutation_requested: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.outcome_preview_id, "outcome_preview_id")
        _require_optional_string(self.recommendation_id, "recommendation_id")
        _require_optional_string(self.linked_action_id, "linked_action_id")
        _require_supported(self.outcome_status, OUTCOME_CAPTURE_STATUSES, "outcome_status")
        _require_supported(
            self.outcome_effectiveness,
            OUTCOME_EFFECTIVENESS_VALUES,
            "outcome_effectiveness",
        )
        _require_optional_boolean(self.issue_recurred, "issue_recurred")
        _require_optional_string(self.followup_awr, "followup_awr")
        _require_optional_string(self.followup_run, "followup_run")
        _require_optional_string(self.implementation_date, "implementation_date")
        _require_optional_string(self.outcome_notes, "outcome_notes")
        _require_optional_string(self.actor_id, "actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        _require_boolean(self.write_performed, "write_performed")
        _require_boolean(self.outcome_created, "outcome_created")
        _require_boolean(self.feedback_created, "feedback_created")
        _require_boolean(self.label_created, "label_created")
        _require_boolean(self.candidate_created, "candidate_created")
        _require_boolean(self.scoring_mutation_requested, "scoring_mutation_requested")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _require_boolean(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _reject_true(self.write_performed, "write_performed")
        _reject_true(self.outcome_created, "outcome_created")
        _reject_true(self.feedback_created, "feedback_created")
        _reject_true(self.label_created, "label_created")
        _reject_true(self.candidate_created, "candidate_created")
        _reject_true(self.scoring_mutation_requested, "scoring_mutation_requested")
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class OutcomeCaptureValidation:
    """Validation metadata for a Screen 5 outcome capture preview."""

    validation_id: str
    outcome_preview_id: str
    valid: bool
    validation_status: str
    actor_present: bool
    recommendation_present: bool
    action_present: bool
    write_performed: bool = False
    outcome_created: bool = False
    feedback_created: bool = False
    label_created: bool = False
    candidate_created: bool = False
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_nonempty_string(self.validation_id, "validation_id")
        _require_nonempty_string(self.outcome_preview_id, "outcome_preview_id")
        _require_boolean(self.valid, "valid")
        _require_supported(
            self.validation_status,
            OUTCOME_CAPTURE_VALIDATION_STATUSES,
            "validation_status",
        )
        _require_boolean(self.actor_present, "actor_present")
        _require_boolean(self.recommendation_present, "recommendation_present")
        _require_boolean(self.action_present, "action_present")
        _require_boolean(self.write_performed, "write_performed")
        _require_boolean(self.outcome_created, "outcome_created")
        _require_boolean(self.feedback_created, "feedback_created")
        _require_boolean(self.label_created, "label_created")
        _require_boolean(self.candidate_created, "candidate_created")
        _require_string_list(self.denied_reasons, "denied_reasons")
        _require_string_list(self.warnings, "warnings")
        _require_string_list(self.required_next_steps, "required_next_steps")
        _reject_true(self.write_performed, "write_performed")
        _reject_true(self.outcome_created, "outcome_created")
        _reject_true(self.feedback_created, "feedback_created")
        _reject_true(self.label_created, "label_created")
        _reject_true(self.candidate_created, "candidate_created")


def build_outcome_preview_id(
    recommendation_id: str | None,
    linked_action_id: str | None,
) -> str:
    """Create a deterministic Screen 5 outcome preview id."""

    _require_optional_string(recommendation_id, "recommendation_id")
    _require_optional_string(linked_action_id, "linked_action_id")
    return (
        "SCREEN5-OUTCOME-PREVIEW-"
        f"{_normalize_token(recommendation_id or 'missing-recommendation')}-"
        f"{_normalize_token(linked_action_id or 'missing-action')}"
    )


def build_outcome_validation_id(outcome_preview_id: str) -> str:
    """Create a deterministic Screen 5 outcome validation id."""

    _require_nonempty_string(outcome_preview_id, "outcome_preview_id")
    return f"SCREEN5-OUTCOME-VALIDATION-{_normalize_token(outcome_preview_id)}"


def validate_outcome_capture_preview(
    preview: OutcomeCapturePreview,
) -> OutcomeCapturePreview:
    """Validate and return outcome capture preview metadata."""

    if not isinstance(preview, OutcomeCapturePreview):
        raise Screen5OutcomeCaptureError(
            "preview must be an OutcomeCapturePreview instance."
        )
    preview.__post_init__()
    return preview


def validate_outcome_capture_validation(
    validation: OutcomeCaptureValidation,
) -> OutcomeCaptureValidation:
    """Validate and return outcome capture validation metadata."""

    if not isinstance(validation, OutcomeCaptureValidation):
        raise Screen5OutcomeCaptureError(
            "validation must be an OutcomeCaptureValidation instance."
        )
    validation.__post_init__()
    return validation


def evaluate_outcome_capture_preview(
    preview: OutcomeCapturePreview,
) -> OutcomeCaptureValidation:
    """Evaluate preview metadata without writing outcome state."""

    validate_outcome_capture_preview(preview)
    actor_present = bool(_optional_text(preview.actor_id))
    recommendation_present = bool(_optional_text(preview.recommendation_id))
    action_present = bool(_optional_text(preview.linked_action_id))
    denied_reasons: list[str] = []
    required_next_steps: list[str] = []
    warnings = [
        "Outcome capture is disabled in Phase 7BH.",
        "Governed write path is required before future outcome records.",
    ]

    if not actor_present:
        validation_status = "needs_actor"
        denied_reasons.append("actor_id is required before future outcome capture")
        required_next_steps.append("provide Phase 7AE actor identity")
    elif not recommendation_present:
        validation_status = "needs_recommendation"
        denied_reasons.append("recommendation_id is required")
        required_next_steps.append("provide recommendation reference")
    elif not action_present:
        validation_status = "needs_action"
        denied_reasons.append("linked_action_id is required")
        required_next_steps.append("provide future action reference")
    else:
        validation_status = "valid"
        required_next_steps.append("route through future governed write path")

    return OutcomeCaptureValidation(
        validation_id=build_outcome_validation_id(preview.outcome_preview_id),
        outcome_preview_id=preview.outcome_preview_id,
        valid=validation_status == "valid",
        validation_status=validation_status,
        actor_present=actor_present,
        recommendation_present=recommendation_present,
        action_present=action_present,
        write_performed=False,
        outcome_created=False,
        feedback_created=False,
        label_created=False,
        candidate_created=False,
        denied_reasons=denied_reasons,
        warnings=warnings,
        required_next_steps=required_next_steps,
    )


def outcome_capture_preview_to_dict(
    preview: OutcomeCapturePreview,
) -> dict[str, Any]:
    """Serialize outcome capture preview metadata."""

    preview = validate_outcome_capture_preview(preview)
    return {
        "outcome_preview_id": preview.outcome_preview_id,
        "recommendation_id": preview.recommendation_id,
        "linked_action_id": preview.linked_action_id,
        "outcome_status": preview.outcome_status,
        "outcome_effectiveness": preview.outcome_effectiveness,
        "issue_recurred": preview.issue_recurred,
        "followup_awr": preview.followup_awr,
        "followup_run": preview.followup_run,
        "implementation_date": preview.implementation_date,
        "outcome_notes": preview.outcome_notes,
        "actor_id": preview.actor_id,
        "actor_audit_context": _copy_optional_mapping(preview.actor_audit_context),
        "write_performed": preview.write_performed,
        "outcome_created": preview.outcome_created,
        "feedback_created": preview.feedback_created,
        "label_created": preview.label_created,
        "candidate_created": preview.candidate_created,
        "scoring_mutation_requested": preview.scoring_mutation_requested,
        "runtime_influence": preview.runtime_influence,
        "phase4i_mutation_requested": preview.phase4i_mutation_requested,
        "notes": preview.notes,
    }


def outcome_capture_preview_from_dict(
    data: dict[str, Any],
) -> OutcomeCapturePreview:
    """Deserialize outcome capture preview metadata."""

    _require_mapping(data, "data")
    return OutcomeCapturePreview(
        outcome_preview_id=str(data["outcome_preview_id"]),
        recommendation_id=_optional_text(data.get("recommendation_id")),
        linked_action_id=_optional_text(data.get("linked_action_id")),
        outcome_status=str(data.get("outcome_status", "pending")),
        outcome_effectiveness=str(data.get("outcome_effectiveness", "unknown")),
        issue_recurred=_optional_bool_from_mapping(data, "issue_recurred"),
        followup_awr=_optional_text(data.get("followup_awr")),
        followup_run=_optional_text(data.get("followup_run")),
        implementation_date=_optional_text(data.get("implementation_date")),
        outcome_notes=_optional_text(data.get("outcome_notes")),
        actor_id=_optional_text(data.get("actor_id")),
        actor_audit_context=_copy_optional_mapping(data.get("actor_audit_context")),
        write_performed=_bool_from_mapping(data, "write_performed", False),
        outcome_created=_bool_from_mapping(data, "outcome_created", False),
        feedback_created=_bool_from_mapping(data, "feedback_created", False),
        label_created=_bool_from_mapping(data, "label_created", False),
        candidate_created=_bool_from_mapping(data, "candidate_created", False),
        scoring_mutation_requested=_bool_from_mapping(
            data,
            "scoring_mutation_requested",
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


def outcome_capture_validation_to_dict(
    validation: OutcomeCaptureValidation,
) -> dict[str, Any]:
    """Serialize outcome capture validation metadata."""

    validation = validate_outcome_capture_validation(validation)
    return {
        "validation_id": validation.validation_id,
        "outcome_preview_id": validation.outcome_preview_id,
        "valid": validation.valid,
        "validation_status": validation.validation_status,
        "actor_present": validation.actor_present,
        "recommendation_present": validation.recommendation_present,
        "action_present": validation.action_present,
        "write_performed": validation.write_performed,
        "outcome_created": validation.outcome_created,
        "feedback_created": validation.feedback_created,
        "label_created": validation.label_created,
        "candidate_created": validation.candidate_created,
        "denied_reasons": list(validation.denied_reasons),
        "warnings": list(validation.warnings),
        "required_next_steps": list(validation.required_next_steps),
    }


def outcome_capture_validation_from_dict(
    data: dict[str, Any],
) -> OutcomeCaptureValidation:
    """Deserialize outcome capture validation metadata."""

    _require_mapping(data, "data")
    return OutcomeCaptureValidation(
        validation_id=str(data["validation_id"]),
        outcome_preview_id=str(data["outcome_preview_id"]),
        valid=_bool_from_mapping(data, "valid", False),
        validation_status=str(data["validation_status"]),
        actor_present=_bool_from_mapping(data, "actor_present", False),
        recommendation_present=_bool_from_mapping(
            data,
            "recommendation_present",
            False,
        ),
        action_present=_bool_from_mapping(data, "action_present", False),
        write_performed=_bool_from_mapping(data, "write_performed", False),
        outcome_created=_bool_from_mapping(data, "outcome_created", False),
        feedback_created=_bool_from_mapping(data, "feedback_created", False),
        label_created=_bool_from_mapping(data, "label_created", False),
        candidate_created=_bool_from_mapping(data, "candidate_created", False),
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
    raise Screen5OutcomeCaptureError(f"{field_name} must be a boolean.")


def _optional_bool_from_mapping(data: dict[str, Any], field_name: str) -> bool | None:
    value = data.get(field_name)
    if value is None or isinstance(value, bool):
        return value
    raise Screen5OutcomeCaptureError(f"{field_name} must be a boolean or None.")


def _copy_optional_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Screen5OutcomeCaptureError("mapping value must be a dictionary.")
    return dict(value)


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise Screen5OutcomeCaptureError(f"{field_name} must be a mapping.")


def _require_optional_mapping(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, dict):
        raise Screen5OutcomeCaptureError(
            f"{field_name} must be a mapping or None."
        )


def _require_nonempty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise Screen5OutcomeCaptureError(
            f"{field_name} must be a non-empty string."
        )


def _require_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise Screen5OutcomeCaptureError(
            f"{field_name} must be a string or None."
        )


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        raise Screen5OutcomeCaptureError(
            f"{field_name} must be one of: {', '.join(supported)}."
        )


def _require_boolean(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise Screen5OutcomeCaptureError(f"{field_name} must be a boolean.")


def _require_optional_boolean(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, bool):
        raise Screen5OutcomeCaptureError(
            f"{field_name} must be a boolean or None."
        )


def _require_string_list(value: Any, field_name: str) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise Screen5OutcomeCaptureError(
            f"{field_name} must be a list of strings."
        )


def _reject_true(value: bool, field_name: str) -> None:
    if value:
        raise Screen5OutcomeCaptureError(
            f"{field_name} must remain false in Phase 7BH."
        )


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text).strip("-")
    return text or "NONE"
