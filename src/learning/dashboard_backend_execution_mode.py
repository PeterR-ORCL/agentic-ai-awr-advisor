"""Local Phase 7AF dashboard backend execution mode boundary model.

This module defines deterministic metadata for future dashboard backend
execution intent. It validates request shape and produces validation metadata
only. It does not invoke backend commands, read sources, call services, write
state, modify dashboard output, or mutate runtime behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from src.learning.dashboard_actor_identity import (
    DashboardActorIdentityError,
    actor_audit_context_from_dict,
)


BACKEND_EXECUTION_MODES = (
    "static_read_only",
    "local_command_generation",
    "local_backend_execution",
    "future_api_server_execution",
)

SOURCE_MODES = (
    "none",
    "local_staged",
    "local_file",
    "existing_run",
    "object_storage",
    "future_upload",
)

REQUESTED_ACTIONS = (
    "read_only_view",
    "analyze_selection",
    "rerun_analysis",
    "build_comparison",
    "load_from_object_storage",
    "diagnostic_review",
    "parser_review",
    "recommendation_action",
    "outcome_capture",
    "governance_review",
    "materialization_review",
    "model_registry_review",
    "runtime_gate_review",
)

EXECUTION_VALIDATION_STATUSES = (
    "VALID",
    "INVALID",
    "NEEDS_ACTOR",
    "NEEDS_SOURCE_VALIDATION",
    "UNSUPPORTED_MODE",
    "READ_ONLY_ONLY",
)

_METADATA_ONLY_EXECUTION_MODES = (
    "local_command_generation",
    "local_backend_execution",
    "future_api_server_execution",
)


class DashboardBackendExecutionModeError(ValueError):
    """Raised when backend execution mode metadata violates Phase 7AF."""


@dataclass(frozen=True)
class DashboardBackendExecutionRequest:
    """Metadata describing how a future dashboard action would execute."""

    request_id: str
    execution_mode: str = "static_read_only"
    requested_action: str = "read_only_view"
    source_mode: str = "none"
    actor_id: str | None = None
    actor_audit_context: dict[str, object] | None = None
    target_screen: str | None = None
    selected_state: dict[str, object] = field(default_factory=dict)
    execution_payload: dict[str, object] = field(default_factory=dict)
    adaptive_runtime_requested: bool = False
    deterministic_default: bool = True
    requires_validation: bool = True
    requires_actor: bool = False
    requires_audit: bool = False
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.request_id, "request_id")
        _require_supported(
            self.execution_mode,
            BACKEND_EXECUTION_MODES,
            "execution_mode",
        )
        _require_supported(self.requested_action, REQUESTED_ACTIONS, "requested_action")
        _require_supported(self.source_mode, SOURCE_MODES, "source_mode")
        _require_optional_string(self.actor_id, "actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        if self.actor_audit_context is not None:
            _validate_actor_audit_context_mapping(self.actor_audit_context)
        _require_optional_string(self.target_screen, "target_screen")
        _require_mapping(self.selected_state, "selected_state")
        _require_mapping(self.execution_payload, "execution_payload")
        _require_boolean(self.adaptive_runtime_requested, "adaptive_runtime_requested")
        _require_boolean(self.deterministic_default, "deterministic_default")
        _require_boolean(self.requires_validation, "requires_validation")
        _require_boolean(self.requires_actor, "requires_actor")
        _require_boolean(self.requires_audit, "requires_audit")
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")
        if not self.deterministic_default:
            raise DashboardBackendExecutionModeError(
                "deterministic_default must remain true in Phase 7AF."
            )
        if not self.requires_validation:
            raise DashboardBackendExecutionModeError(
                "requires_validation must remain true in Phase 7AF."
            )
        if self.requested_action == "read_only_view" and self.requires_actor:
            raise DashboardBackendExecutionModeError(
                "read_only_view may not require actor metadata in Phase 7AF."
            )
        if self.requested_action != "read_only_view":
            if not self.requires_actor:
                raise DashboardBackendExecutionModeError(
                    "non-read-only actions must require actor metadata."
                )
            if not self.requires_audit:
                raise DashboardBackendExecutionModeError(
                    "non-read-only actions must require audit metadata."
                )


@dataclass(frozen=True)
class DashboardBackendExecutionValidation:
    """Validation metadata for a backend execution request.

    execution_allowed means valid for future execution consideration. It never
    means execution was performed in Phase 7AF.
    """

    validation_id: str
    request_id: str
    valid: bool
    execution_allowed: bool
    execution_performed: bool
    denied_reasons: list[str]
    warnings: list[str]
    required_next_steps: list[str]
    deterministic_default: bool
    adaptive_runtime_requested: bool
    backend_execution_mode: str
    source_mode: str
    requested_action: str
    actor_required: bool
    actor_present: bool
    audit_required: bool
    validation_status: str

    def __post_init__(self) -> None:
        _require_nonempty_string(self.validation_id, "validation_id")
        _require_nonempty_string(self.request_id, "request_id")
        _require_boolean(self.valid, "valid")
        _require_boolean(self.execution_allowed, "execution_allowed")
        _require_boolean(self.execution_performed, "execution_performed")
        _require_list_of_strings(self.denied_reasons, "denied_reasons")
        _require_list_of_strings(self.warnings, "warnings")
        _require_list_of_strings(self.required_next_steps, "required_next_steps")
        _require_boolean(self.deterministic_default, "deterministic_default")
        _require_boolean(self.adaptive_runtime_requested, "adaptive_runtime_requested")
        _require_supported(
            self.backend_execution_mode,
            BACKEND_EXECUTION_MODES,
            "backend_execution_mode",
        )
        _require_supported(self.source_mode, SOURCE_MODES, "source_mode")
        _require_supported(self.requested_action, REQUESTED_ACTIONS, "requested_action")
        _require_boolean(self.actor_required, "actor_required")
        _require_boolean(self.actor_present, "actor_present")
        _require_boolean(self.audit_required, "audit_required")
        _require_supported(
            self.validation_status,
            EXECUTION_VALIDATION_STATUSES,
            "validation_status",
        )
        if self.execution_performed:
            raise DashboardBackendExecutionModeError(
                "execution_performed must remain false in Phase 7AF."
            )
        if not self.deterministic_default:
            raise DashboardBackendExecutionModeError(
                "deterministic_default must remain true in Phase 7AF."
            )


def create_backend_execution_request_id(
    execution_mode: str,
    requested_action: str,
    source_mode: str,
    target_screen: str | None = None,
) -> str:
    """Create a deterministic backend execution request id."""

    _require_supported(execution_mode, BACKEND_EXECUTION_MODES, "execution_mode")
    _require_supported(requested_action, REQUESTED_ACTIONS, "requested_action")
    _require_supported(source_mode, SOURCE_MODES, "source_mode")
    _require_optional_string(target_screen, "target_screen")
    screen_token = target_screen if target_screen else "none"
    return (
        "DASHBOARD-BACKEND-REQUEST-"
        f"{_normalize_token(execution_mode)}-"
        f"{_normalize_token(requested_action)}-"
        f"{_normalize_token(source_mode)}-"
        f"{_normalize_token(screen_token)}"
    )


def create_backend_execution_validation_id(request_id: str) -> str:
    """Create a deterministic backend execution validation id."""

    _require_nonempty_string(request_id, "request_id")
    return f"DASHBOARD-BACKEND-VALIDATION-{_normalize_token(request_id)}"


def validate_backend_execution_request(
    request: DashboardBackendExecutionRequest,
) -> DashboardBackendExecutionRequest:
    """Validate request metadata without executing anything."""

    if not isinstance(request, DashboardBackendExecutionRequest):
        raise DashboardBackendExecutionModeError(
            "request must be a DashboardBackendExecutionRequest instance."
        )
    request.__post_init__()
    if request.requires_actor and not _actor_present(request):
        raise DashboardBackendExecutionModeError(
            "non-read-only actions require actor_id or actor_audit_context."
        )
    return request


def validate_backend_execution_validation(
    validation: DashboardBackendExecutionValidation,
) -> DashboardBackendExecutionValidation:
    """Validate backend execution validation metadata."""

    if not isinstance(validation, DashboardBackendExecutionValidation):
        raise DashboardBackendExecutionModeError(
            "validation must be a DashboardBackendExecutionValidation instance."
        )
    validation.__post_init__()
    return validation


def evaluate_backend_execution_request(
    request: DashboardBackendExecutionRequest,
) -> DashboardBackendExecutionValidation:
    """Evaluate request metadata for future execution consideration only."""

    if not isinstance(request, DashboardBackendExecutionRequest):
        raise DashboardBackendExecutionModeError(
            "request must be a DashboardBackendExecutionRequest instance."
        )
    request.__post_init__()

    denied_reasons: list[str] = []
    warnings: list[str] = []
    required_next_steps: list[str] = []
    actor_present = _actor_present(request)
    validation_status = "VALID"
    valid = True
    execution_allowed = True

    if request.adaptive_runtime_requested:
        warnings.append(
            "adaptive runtime request metadata requires Phase 7AA gate review"
        )
        required_next_steps.append("validate Phase 7AA runtime gate posture")

    if request.execution_mode in _METADATA_ONLY_EXECUTION_MODES:
        warnings.append(f"{request.execution_mode} is metadata only in Phase 7AF")

    if request.execution_mode == "local_command_generation":
        warnings.append("local command generation does not execute commands in 7AF")

    if request.requested_action == "read_only_view":
        if request.execution_mode != "static_read_only":
            warnings.append("read_only_view does not require backend execution")
        if request.source_mode != "none":
            warnings.append("read_only_view ignores source execution metadata in 7AF")
    elif request.execution_mode == "static_read_only":
        valid = False
        execution_allowed = False
        validation_status = "READ_ONLY_ONLY"
        denied_reasons.append(
            "static_read_only mode cannot request non-read-only action metadata"
        )
        required_next_steps.append("select an explicit future execution mode")
    elif request.requires_actor and not actor_present:
        valid = False
        execution_allowed = False
        validation_status = "NEEDS_ACTOR"
        denied_reasons.append("actor metadata is required for non-read-only actions")
        required_next_steps.append("attach actor_id or actor_audit_context")

    object_storage_requested = (
        request.source_mode == "object_storage"
        or request.requested_action == "load_from_object_storage"
    )
    if object_storage_requested:
        warnings.append("object storage is metadata only in Phase 7AF")
        required_next_steps.append("perform future governed source validation")
        if valid and actor_present:
            valid = False
            execution_allowed = False
            validation_status = "NEEDS_SOURCE_VALIDATION"
            denied_reasons.append(
                "object storage source requires future source validation"
            )

    if valid and request.requested_action != "read_only_view":
        required_next_steps.append("route through future 7AG governed write path")
        required_next_steps.append("create future audit record before execution")

    validation = DashboardBackendExecutionValidation(
        validation_id=create_backend_execution_validation_id(request.request_id),
        request_id=request.request_id,
        valid=valid,
        execution_allowed=execution_allowed,
        execution_performed=False,
        denied_reasons=denied_reasons,
        warnings=warnings,
        required_next_steps=required_next_steps,
        deterministic_default=True,
        adaptive_runtime_requested=request.adaptive_runtime_requested,
        backend_execution_mode=request.execution_mode,
        source_mode=request.source_mode,
        requested_action=request.requested_action,
        actor_required=request.requires_actor,
        actor_present=actor_present,
        audit_required=request.requires_audit,
        validation_status=validation_status,
    )
    return validate_backend_execution_validation(validation)


def backend_execution_request_to_dict(
    request: DashboardBackendExecutionRequest,
) -> dict[str, Any]:
    """Serialize backend execution request metadata to a dictionary."""

    request.__post_init__()
    return {
        "request_id": request.request_id,
        "execution_mode": request.execution_mode,
        "requested_action": request.requested_action,
        "source_mode": request.source_mode,
        "actor_id": request.actor_id,
        "actor_audit_context": request.actor_audit_context,
        "target_screen": request.target_screen,
        "selected_state": dict(request.selected_state),
        "execution_payload": dict(request.execution_payload),
        "adaptive_runtime_requested": request.adaptive_runtime_requested,
        "deterministic_default": request.deterministic_default,
        "requires_validation": request.requires_validation,
        "requires_actor": request.requires_actor,
        "requires_audit": request.requires_audit,
        "created_at": request.created_at,
        "notes": request.notes,
    }


def backend_execution_request_from_dict(
    data: dict[str, Any],
) -> DashboardBackendExecutionRequest:
    """Deserialize backend execution request metadata from a dictionary."""

    _require_mapping(data, "request")
    return DashboardBackendExecutionRequest(
        request_id=data.get("request_id"),
        execution_mode=data.get("execution_mode", "static_read_only"),
        requested_action=data.get("requested_action", "read_only_view"),
        source_mode=data.get("source_mode", "none"),
        actor_id=data.get("actor_id"),
        actor_audit_context=data.get("actor_audit_context"),
        target_screen=data.get("target_screen"),
        selected_state=data.get("selected_state", {}),
        execution_payload=data.get("execution_payload", {}),
        adaptive_runtime_requested=data.get("adaptive_runtime_requested", False),
        deterministic_default=data.get("deterministic_default", True),
        requires_validation=data.get("requires_validation", True),
        requires_actor=data.get("requires_actor", False),
        requires_audit=data.get("requires_audit", False),
        created_at=data.get("created_at"),
        notes=data.get("notes"),
    )


def backend_execution_validation_to_dict(
    validation: DashboardBackendExecutionValidation,
) -> dict[str, Any]:
    """Serialize backend execution validation metadata to a dictionary."""

    validation = validate_backend_execution_validation(validation)
    return {
        "validation_id": validation.validation_id,
        "request_id": validation.request_id,
        "valid": validation.valid,
        "execution_allowed": validation.execution_allowed,
        "execution_performed": validation.execution_performed,
        "denied_reasons": list(validation.denied_reasons),
        "warnings": list(validation.warnings),
        "required_next_steps": list(validation.required_next_steps),
        "deterministic_default": validation.deterministic_default,
        "adaptive_runtime_requested": validation.adaptive_runtime_requested,
        "backend_execution_mode": validation.backend_execution_mode,
        "source_mode": validation.source_mode,
        "requested_action": validation.requested_action,
        "actor_required": validation.actor_required,
        "actor_present": validation.actor_present,
        "audit_required": validation.audit_required,
        "validation_status": validation.validation_status,
    }


def backend_execution_validation_from_dict(
    data: dict[str, Any],
) -> DashboardBackendExecutionValidation:
    """Deserialize backend execution validation metadata from a dictionary."""

    _require_mapping(data, "validation")
    return DashboardBackendExecutionValidation(
        validation_id=data.get("validation_id"),
        request_id=data.get("request_id"),
        valid=data.get("valid"),
        execution_allowed=data.get("execution_allowed"),
        execution_performed=data.get("execution_performed"),
        denied_reasons=data.get("denied_reasons", []),
        warnings=data.get("warnings", []),
        required_next_steps=data.get("required_next_steps", []),
        deterministic_default=data.get("deterministic_default"),
        adaptive_runtime_requested=data.get("adaptive_runtime_requested"),
        backend_execution_mode=data.get("backend_execution_mode"),
        source_mode=data.get("source_mode"),
        requested_action=data.get("requested_action"),
        actor_required=data.get("actor_required"),
        actor_present=data.get("actor_present"),
        audit_required=data.get("audit_required"),
        validation_status=data.get("validation_status"),
    )


def default_static_read_only_request(
    target_screen: str | None = None,
    notes: str | None = None,
) -> DashboardBackendExecutionRequest:
    """Create default static read-only dashboard request metadata."""

    _require_optional_string(target_screen, "target_screen")
    _require_optional_string(notes, "notes")
    return DashboardBackendExecutionRequest(
        request_id=create_backend_execution_request_id(
            "static_read_only",
            "read_only_view",
            "none",
            target_screen=target_screen,
        ),
        execution_mode="static_read_only",
        requested_action="read_only_view",
        source_mode="none",
        target_screen=target_screen,
        selected_state={},
        execution_payload={},
        adaptive_runtime_requested=False,
        deterministic_default=True,
        requires_validation=True,
        requires_actor=False,
        requires_audit=False,
        created_at=None,
        notes=notes,
    )


def _actor_present(request: DashboardBackendExecutionRequest) -> bool:
    return bool(request.actor_id) or request.actor_audit_context is not None


def _validate_actor_audit_context_mapping(data: dict[str, object]) -> None:
    try:
        actor_audit_context_from_dict(dict(data))
    except DashboardActorIdentityError as exc:
        raise DashboardBackendExecutionModeError(
            f"invalid actor_audit_context: {exc}"
        ) from exc


def _normalize_token(value: str) -> str:
    _require_nonempty_string(value, "value")
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().upper())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "NONE"


def _require_nonempty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DashboardBackendExecutionModeError(f"{field_name} is required.")
    return value


def _require_optional_string(value: Any, field_name: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise DashboardBackendExecutionModeError(
            f"{field_name} must be a string or None."
        )
    return value


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> str:
    if not isinstance(value, str) or value not in supported:
        raise DashboardBackendExecutionModeError(f"Unsupported {field_name}: {value!r}.")
    return value


def _require_boolean(value: Any, field_name: str) -> bool:
    if type(value) is not bool:
        raise DashboardBackendExecutionModeError(f"{field_name} must be boolean.")
    return value


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DashboardBackendExecutionModeError(f"{field_name} must be a dictionary.")
    return value


def _require_optional_mapping(value: Any, field_name: str) -> dict[str, Any] | None:
    if value is not None and not isinstance(value, dict):
        raise DashboardBackendExecutionModeError(
            f"{field_name} must be a dictionary or None."
        )
    return value


def _require_list_of_strings(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise DashboardBackendExecutionModeError(
            f"{field_name} must be a list of strings."
        )
    return value
