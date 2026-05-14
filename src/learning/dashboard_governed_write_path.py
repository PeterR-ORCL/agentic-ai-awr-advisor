"""Local Phase 7AG dashboard governed write-path framework.

This module defines deterministic request, validation, and audit metadata for
future governed dashboard workflows. It validates envelope shape only. It does
not persist state, invoke backend actions, modify dashboard output, or mutate
runtime truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from src.learning.dashboard_actor_identity import (
    DashboardActorIdentityError,
    actor_audit_context_from_dict,
)
from src.learning.dashboard_backend_execution_mode import (
    DashboardBackendExecutionModeError,
    backend_execution_request_from_dict,
)


GOVERNED_WRITE_TARGET_TYPES = (
    "diagnostic_evidence",
    "recommendation",
    "action",
    "outcome",
    "parser_unknown",
    "learning_candidate",
    "materialization_artifact",
    "model_registry_entry",
    "runtime_gate",
    "backend_execution_request",
    "source_selection",
    "historical_baseline",
    "trend_anomaly_review",
    "governance_item",
)

GOVERNED_WRITE_INTENTS = (
    "read_only",
    "review",
    "approve",
    "reject",
    "request_revision",
    "defer",
    "assign",
    "execute",
    "capture_outcome",
    "create_candidate",
    "link_artifact",
    "validate",
    "close",
)

GOVERNED_WRITE_VALIDATION_STATUSES = (
    "VALID",
    "INVALID",
    "NEEDS_ACTOR",
    "NEEDS_PERMISSION_SCOPE",
    "NEEDS_TARGET",
    "NEEDS_BACKEND_EXECUTION_MODE",
    "READ_ONLY_ONLY",
    "UNSUPPORTED_ACTION",
)

GOVERNED_WRITE_MODES = (
    "dry_run",
)


class DashboardGovernedWritePathError(ValueError):
    """Raised when governed write-path metadata violates Phase 7AG rules."""


@dataclass(frozen=True)
class GovernedWriteRequest:
    """Dry-run request envelope for a future governed dashboard action."""

    request_id: str
    target_type: str
    target_id: str
    write_intent: str
    actor_id: str | None = None
    actor_audit_context: dict[str, object] | None = None
    backend_execution_request: dict[str, object] | None = None
    payload: dict[str, object] = field(default_factory=dict)
    dry_run: bool = True
    requires_actor: bool = True
    requires_audit: bool = True
    requires_backend_validation: bool = True
    runtime_mutation_requested: bool = False
    phase4i_mutation_requested: bool = False
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.request_id, "request_id")
        _require_supported(self.target_type, GOVERNED_WRITE_TARGET_TYPES, "target_type")
        _require_nonempty_string(self.target_id, "target_id")
        _require_supported(self.write_intent, GOVERNED_WRITE_INTENTS, "write_intent")
        _require_optional_string(self.actor_id, "actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        if self.actor_audit_context is not None:
            _validate_actor_audit_context_mapping(self.actor_audit_context)
        _require_optional_mapping(
            self.backend_execution_request,
            "backend_execution_request",
        )
        if self.backend_execution_request is not None:
            _validate_backend_request_mapping(self.backend_execution_request)
        _require_mapping(self.payload, "payload")
        _require_boolean(self.dry_run, "dry_run")
        _require_boolean(self.requires_actor, "requires_actor")
        _require_boolean(self.requires_audit, "requires_audit")
        _require_boolean(self.requires_backend_validation, "requires_backend_validation")
        _require_boolean(self.runtime_mutation_requested, "runtime_mutation_requested")
        _require_boolean(self.phase4i_mutation_requested, "phase4i_mutation_requested")
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")
        if not self.dry_run:
            raise DashboardGovernedWritePathError(
                "dry_run must remain true in Phase 7AG."
            )
        if not self.requires_audit:
            raise DashboardGovernedWritePathError(
                "requires_audit must remain true in Phase 7AG."
            )
        if self.write_intent == "read_only" and self.requires_actor:
            raise DashboardGovernedWritePathError(
                "read_only intent may not require actor metadata in Phase 7AG."
            )
        if self.write_intent != "read_only" and not self.requires_actor:
            raise DashboardGovernedWritePathError(
                "non-read-only intents must require actor metadata."
            )
        if self.write_intent == "execute" and not self.requires_backend_validation:
            raise DashboardGovernedWritePathError(
                "execute intent must require backend validation metadata."
            )
        if self.runtime_mutation_requested:
            raise DashboardGovernedWritePathError(
                "runtime mutation is forbidden in Phase 7AG."
            )
        if self.phase4i_mutation_requested:
            raise DashboardGovernedWritePathError(
                "Phase 4I mutation is forbidden in Phase 7AG."
            )


@dataclass(frozen=True)
class GovernedWriteValidation:
    """Validation metadata for a governed write request."""

    validation_id: str
    request_id: str
    valid: bool
    validation_status: str
    write_allowed_for_future_handling: bool
    write_performed: bool
    dry_run: bool
    actor_required: bool
    actor_present: bool
    audit_required: bool
    backend_validation_required: bool
    backend_validation_present: bool
    runtime_mutation_requested: bool
    phase4i_mutation_requested: bool
    denied_reasons: list[str]
    warnings: list[str]
    required_next_steps: list[str]

    def __post_init__(self) -> None:
        _require_nonempty_string(self.validation_id, "validation_id")
        _require_nonempty_string(self.request_id, "request_id")
        _require_boolean(self.valid, "valid")
        _require_supported(
            self.validation_status,
            GOVERNED_WRITE_VALIDATION_STATUSES,
            "validation_status",
        )
        _require_boolean(
            self.write_allowed_for_future_handling,
            "write_allowed_for_future_handling",
        )
        _require_boolean(self.write_performed, "write_performed")
        _require_boolean(self.dry_run, "dry_run")
        _require_boolean(self.actor_required, "actor_required")
        _require_boolean(self.actor_present, "actor_present")
        _require_boolean(self.audit_required, "audit_required")
        _require_boolean(
            self.backend_validation_required,
            "backend_validation_required",
        )
        _require_boolean(self.backend_validation_present, "backend_validation_present")
        _require_boolean(self.runtime_mutation_requested, "runtime_mutation_requested")
        _require_boolean(self.phase4i_mutation_requested, "phase4i_mutation_requested")
        _require_list_of_strings(self.denied_reasons, "denied_reasons")
        _require_list_of_strings(self.warnings, "warnings")
        _require_list_of_strings(self.required_next_steps, "required_next_steps")
        if self.write_performed:
            raise DashboardGovernedWritePathError(
                "write_performed must remain false in Phase 7AG."
            )
        if not self.dry_run:
            raise DashboardGovernedWritePathError(
                "dry_run must remain true in Phase 7AG."
            )
        if self.runtime_mutation_requested:
            raise DashboardGovernedWritePathError(
                "runtime mutation is forbidden in Phase 7AG."
            )
        if self.phase4i_mutation_requested:
            raise DashboardGovernedWritePathError(
                "Phase 4I mutation is forbidden in Phase 7AG."
            )
        if self.write_allowed_for_future_handling and not self.valid:
            raise DashboardGovernedWritePathError(
                "future handling can be allowed only when validation is valid."
            )


@dataclass(frozen=True)
class GovernedWriteAuditRecord:
    """Audit metadata for a requested and validated governed action."""

    audit_id: str
    request_id: str
    validation_id: str
    actor_id: str | None
    target_type: str
    target_id: str
    write_intent: str
    dry_run: bool
    write_performed: bool
    validation_status: str
    audit_summary: str
    runtime_mutation_performed: bool
    phase4i_mutation_performed: bool
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.audit_id, "audit_id")
        _require_nonempty_string(self.request_id, "request_id")
        _require_nonempty_string(self.validation_id, "validation_id")
        _require_optional_string(self.actor_id, "actor_id")
        _require_supported(self.target_type, GOVERNED_WRITE_TARGET_TYPES, "target_type")
        _require_nonempty_string(self.target_id, "target_id")
        _require_supported(self.write_intent, GOVERNED_WRITE_INTENTS, "write_intent")
        _require_boolean(self.dry_run, "dry_run")
        _require_boolean(self.write_performed, "write_performed")
        _require_supported(
            self.validation_status,
            GOVERNED_WRITE_VALIDATION_STATUSES,
            "validation_status",
        )
        _require_nonempty_string(self.audit_summary, "audit_summary")
        _require_boolean(
            self.runtime_mutation_performed,
            "runtime_mutation_performed",
        )
        _require_boolean(
            self.phase4i_mutation_performed,
            "phase4i_mutation_performed",
        )
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")
        if not self.dry_run:
            raise DashboardGovernedWritePathError(
                "dry_run must remain true in Phase 7AG audit records."
            )
        if self.write_performed:
            raise DashboardGovernedWritePathError(
                "write_performed must remain false in Phase 7AG audit records."
            )
        if self.runtime_mutation_performed:
            raise DashboardGovernedWritePathError(
                "runtime mutation must not be performed in Phase 7AG."
            )
        if self.phase4i_mutation_performed:
            raise DashboardGovernedWritePathError(
                "Phase 4I mutation must not be performed in Phase 7AG."
            )


def create_governed_write_request_id(
    target_type: str,
    target_id: str,
    write_intent: str,
) -> str:
    """Create a deterministic governed write request id."""

    _require_supported(target_type, GOVERNED_WRITE_TARGET_TYPES, "target_type")
    _require_nonempty_string(target_id, "target_id")
    _require_supported(write_intent, GOVERNED_WRITE_INTENTS, "write_intent")
    return (
        "GOVERNED-WRITE-REQUEST-"
        f"{_normalize_token(target_type)}-"
        f"{_normalize_token(target_id)}-"
        f"{_normalize_token(write_intent)}"
    )


def create_governed_write_validation_id(request_id: str) -> str:
    """Create a deterministic governed write validation id."""

    _require_nonempty_string(request_id, "request_id")
    return f"GOVERNED-WRITE-VALIDATION-{_normalize_token(request_id)}"


def create_governed_write_audit_id(request_id: str, validation_id: str) -> str:
    """Create a deterministic governed write audit id."""

    _require_nonempty_string(request_id, "request_id")
    _require_nonempty_string(validation_id, "validation_id")
    return (
        "GOVERNED-WRITE-AUDIT-"
        f"{_normalize_token(request_id)}-"
        f"{_normalize_token(validation_id)}"
    )


def validate_governed_write_request(
    request: GovernedWriteRequest,
) -> GovernedWriteRequest:
    """Validate a governed write request envelope without changing state."""

    if not isinstance(request, GovernedWriteRequest):
        raise DashboardGovernedWritePathError(
            "request must be a GovernedWriteRequest instance."
        )
    request.__post_init__()
    if request.requires_actor and not _actor_present(request):
        raise DashboardGovernedWritePathError(
            "non-read-only intents require actor_id or actor_audit_context."
        )
    if request.write_intent == "execute" and request.backend_execution_request is None:
        raise DashboardGovernedWritePathError(
            "execute intent requires backend execution validation metadata."
        )
    return request


def evaluate_governed_write_request(
    request: GovernedWriteRequest,
) -> GovernedWriteValidation:
    """Evaluate a governed write request for future handling only."""

    if not isinstance(request, GovernedWriteRequest):
        raise DashboardGovernedWritePathError(
            "request must be a GovernedWriteRequest instance."
        )
    request.__post_init__()

    denied_reasons: list[str] = []
    warnings: list[str] = []
    required_next_steps: list[str] = []
    validation_status = "VALID"
    actor_present = _actor_present(request)
    backend_present = request.backend_execution_request is not None
    valid = True

    warnings.append("dry_run=true; no write is performed in Phase 7AG")

    if not request.target_id.strip():
        valid = False
        validation_status = "NEEDS_TARGET"
        denied_reasons.append("target_id is required")

    if request.runtime_mutation_requested:
        valid = False
        validation_status = "INVALID"
        denied_reasons.append("runtime mutation is forbidden")

    if request.phase4i_mutation_requested:
        valid = False
        validation_status = "INVALID"
        denied_reasons.append("Phase 4I mutation is forbidden")

    if request.write_intent != "read_only" and request.requires_actor and not actor_present:
        valid = False
        validation_status = "NEEDS_ACTOR"
        denied_reasons.append("actor metadata is required for non-read-only intents")
        required_next_steps.append("attach actor_id or actor_audit_context")

    if request.write_intent == "execute":
        if not backend_present:
            valid = False
            validation_status = "NEEDS_BACKEND_EXECUTION_MODE"
            denied_reasons.append(
                "execute intent requires backend execution validation metadata"
            )
            required_next_steps.append("attach backend execution request metadata")
        else:
            required_next_steps.append("validate backend execution mode in future 7AG flow")

    if valid and request.write_intent != "read_only":
        required_next_steps.append("future workflow may consider this validated envelope")
        required_next_steps.append("create audit metadata before any future handling")

    validation = GovernedWriteValidation(
        validation_id=create_governed_write_validation_id(request.request_id),
        request_id=request.request_id,
        valid=valid,
        validation_status=validation_status,
        write_allowed_for_future_handling=valid,
        write_performed=False,
        dry_run=True,
        actor_required=request.requires_actor,
        actor_present=actor_present,
        audit_required=request.requires_audit,
        backend_validation_required=request.requires_backend_validation,
        backend_validation_present=backend_present,
        runtime_mutation_requested=False,
        phase4i_mutation_requested=False,
        denied_reasons=denied_reasons,
        warnings=warnings,
        required_next_steps=required_next_steps,
    )
    return validate_governed_write_validation(validation)


def validate_governed_write_validation(
    validation: GovernedWriteValidation,
) -> GovernedWriteValidation:
    """Validate governed write validation metadata."""

    if not isinstance(validation, GovernedWriteValidation):
        raise DashboardGovernedWritePathError(
            "validation must be a GovernedWriteValidation instance."
        )
    validation.__post_init__()
    return validation


def create_governed_write_audit_record(
    request: GovernedWriteRequest,
    validation: GovernedWriteValidation,
    notes: str | None = None,
) -> GovernedWriteAuditRecord:
    """Create deterministic audit metadata for a governed write request."""

    request.__post_init__()
    validation = validate_governed_write_validation(validation)
    _require_optional_string(notes, "notes")
    return GovernedWriteAuditRecord(
        audit_id=create_governed_write_audit_id(
            request.request_id,
            validation.validation_id,
        ),
        request_id=request.request_id,
        validation_id=validation.validation_id,
        actor_id=request.actor_id,
        target_type=request.target_type,
        target_id=request.target_id,
        write_intent=request.write_intent,
        dry_run=True,
        write_performed=False,
        validation_status=validation.validation_status,
        audit_summary=(
            f"Dry-run governed write {request.write_intent} for "
            f"{request.target_type}:{request.target_id}; "
            f"validation={validation.validation_status}; write_performed=false"
        ),
        runtime_mutation_performed=False,
        phase4i_mutation_performed=False,
        created_at=None,
        notes=notes,
    )


def validate_governed_write_audit_record(
    record: GovernedWriteAuditRecord,
) -> GovernedWriteAuditRecord:
    """Validate governed write audit metadata."""

    if not isinstance(record, GovernedWriteAuditRecord):
        raise DashboardGovernedWritePathError(
            "record must be a GovernedWriteAuditRecord instance."
        )
    record.__post_init__()
    return record


def governed_write_request_to_dict(request: GovernedWriteRequest) -> dict[str, Any]:
    """Serialize governed write request metadata."""

    request.__post_init__()
    return {
        "request_id": request.request_id,
        "target_type": request.target_type,
        "target_id": request.target_id,
        "write_intent": request.write_intent,
        "actor_id": request.actor_id,
        "actor_audit_context": request.actor_audit_context,
        "backend_execution_request": request.backend_execution_request,
        "payload": dict(request.payload),
        "dry_run": request.dry_run,
        "requires_actor": request.requires_actor,
        "requires_audit": request.requires_audit,
        "requires_backend_validation": request.requires_backend_validation,
        "runtime_mutation_requested": request.runtime_mutation_requested,
        "phase4i_mutation_requested": request.phase4i_mutation_requested,
        "created_at": request.created_at,
        "notes": request.notes,
    }


def governed_write_request_from_dict(data: dict[str, Any]) -> GovernedWriteRequest:
    """Deserialize governed write request metadata."""

    _require_mapping(data, "request")
    return GovernedWriteRequest(
        request_id=data.get("request_id"),
        target_type=data.get("target_type"),
        target_id=data.get("target_id"),
        write_intent=data.get("write_intent"),
        actor_id=data.get("actor_id"),
        actor_audit_context=data.get("actor_audit_context"),
        backend_execution_request=data.get("backend_execution_request"),
        payload=data.get("payload", {}),
        dry_run=data.get("dry_run", True),
        requires_actor=data.get("requires_actor", True),
        requires_audit=data.get("requires_audit", True),
        requires_backend_validation=data.get("requires_backend_validation", True),
        runtime_mutation_requested=data.get("runtime_mutation_requested", False),
        phase4i_mutation_requested=data.get("phase4i_mutation_requested", False),
        created_at=data.get("created_at"),
        notes=data.get("notes"),
    )


def governed_write_validation_to_dict(
    validation: GovernedWriteValidation,
) -> dict[str, Any]:
    """Serialize governed write validation metadata."""

    validation = validate_governed_write_validation(validation)
    return {
        "validation_id": validation.validation_id,
        "request_id": validation.request_id,
        "valid": validation.valid,
        "validation_status": validation.validation_status,
        "write_allowed_for_future_handling": (
            validation.write_allowed_for_future_handling
        ),
        "write_performed": validation.write_performed,
        "dry_run": validation.dry_run,
        "actor_required": validation.actor_required,
        "actor_present": validation.actor_present,
        "audit_required": validation.audit_required,
        "backend_validation_required": validation.backend_validation_required,
        "backend_validation_present": validation.backend_validation_present,
        "runtime_mutation_requested": validation.runtime_mutation_requested,
        "phase4i_mutation_requested": validation.phase4i_mutation_requested,
        "denied_reasons": list(validation.denied_reasons),
        "warnings": list(validation.warnings),
        "required_next_steps": list(validation.required_next_steps),
    }


def governed_write_validation_from_dict(
    data: dict[str, Any],
) -> GovernedWriteValidation:
    """Deserialize governed write validation metadata."""

    _require_mapping(data, "validation")
    return GovernedWriteValidation(
        validation_id=data.get("validation_id"),
        request_id=data.get("request_id"),
        valid=data.get("valid"),
        validation_status=data.get("validation_status"),
        write_allowed_for_future_handling=data.get(
            "write_allowed_for_future_handling"
        ),
        write_performed=data.get("write_performed"),
        dry_run=data.get("dry_run"),
        actor_required=data.get("actor_required"),
        actor_present=data.get("actor_present"),
        audit_required=data.get("audit_required"),
        backend_validation_required=data.get("backend_validation_required"),
        backend_validation_present=data.get("backend_validation_present"),
        runtime_mutation_requested=data.get("runtime_mutation_requested"),
        phase4i_mutation_requested=data.get("phase4i_mutation_requested"),
        denied_reasons=data.get("denied_reasons", []),
        warnings=data.get("warnings", []),
        required_next_steps=data.get("required_next_steps", []),
    )


def governed_write_audit_record_to_dict(
    record: GovernedWriteAuditRecord,
) -> dict[str, Any]:
    """Serialize governed write audit metadata."""

    record = validate_governed_write_audit_record(record)
    return {
        "audit_id": record.audit_id,
        "request_id": record.request_id,
        "validation_id": record.validation_id,
        "actor_id": record.actor_id,
        "target_type": record.target_type,
        "target_id": record.target_id,
        "write_intent": record.write_intent,
        "dry_run": record.dry_run,
        "write_performed": record.write_performed,
        "validation_status": record.validation_status,
        "audit_summary": record.audit_summary,
        "runtime_mutation_performed": record.runtime_mutation_performed,
        "phase4i_mutation_performed": record.phase4i_mutation_performed,
        "created_at": record.created_at,
        "notes": record.notes,
    }


def governed_write_audit_record_from_dict(
    data: dict[str, Any],
) -> GovernedWriteAuditRecord:
    """Deserialize governed write audit metadata."""

    _require_mapping(data, "record")
    return GovernedWriteAuditRecord(
        audit_id=data.get("audit_id"),
        request_id=data.get("request_id"),
        validation_id=data.get("validation_id"),
        actor_id=data.get("actor_id"),
        target_type=data.get("target_type"),
        target_id=data.get("target_id"),
        write_intent=data.get("write_intent"),
        dry_run=data.get("dry_run"),
        write_performed=data.get("write_performed"),
        validation_status=data.get("validation_status"),
        audit_summary=data.get("audit_summary"),
        runtime_mutation_performed=data.get("runtime_mutation_performed"),
        phase4i_mutation_performed=data.get("phase4i_mutation_performed"),
        created_at=data.get("created_at"),
        notes=data.get("notes"),
    )


def default_read_only_write_request(
    target_type: str,
    target_id: str,
    notes: str | None = None,
) -> GovernedWriteRequest:
    """Create default read-only governed request metadata."""

    _require_supported(target_type, GOVERNED_WRITE_TARGET_TYPES, "target_type")
    _require_nonempty_string(target_id, "target_id")
    _require_optional_string(notes, "notes")
    return GovernedWriteRequest(
        request_id=create_governed_write_request_id(
            target_type,
            target_id,
            "read_only",
        ),
        target_type=target_type,
        target_id=target_id,
        write_intent="read_only",
        actor_id=None,
        actor_audit_context=None,
        backend_execution_request=None,
        payload={},
        dry_run=True,
        requires_actor=False,
        requires_audit=True,
        requires_backend_validation=True,
        runtime_mutation_requested=False,
        phase4i_mutation_requested=False,
        created_at=None,
        notes=notes,
    )


def _actor_present(request: GovernedWriteRequest) -> bool:
    return bool(request.actor_id) or request.actor_audit_context is not None


def _validate_actor_audit_context_mapping(data: dict[str, object]) -> None:
    try:
        actor_audit_context_from_dict(dict(data))
    except DashboardActorIdentityError as exc:
        raise DashboardGovernedWritePathError(
            f"invalid actor_audit_context: {exc}"
        ) from exc


def _validate_backend_request_mapping(data: dict[str, object]) -> None:
    try:
        backend_execution_request_from_dict(dict(data))
    except DashboardBackendExecutionModeError as exc:
        raise DashboardGovernedWritePathError(
            f"invalid backend_execution_request: {exc}"
        ) from exc


def _normalize_token(value: str) -> str:
    _require_nonempty_string(value, "value")
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().upper())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "NONE"


def _require_nonempty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DashboardGovernedWritePathError(f"{field_name} is required.")
    return value


def _require_optional_string(value: Any, field_name: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise DashboardGovernedWritePathError(
            f"{field_name} must be a string or None."
        )
    return value


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> str:
    if not isinstance(value, str) or value not in supported:
        raise DashboardGovernedWritePathError(f"Unsupported {field_name}: {value!r}.")
    return value


def _require_boolean(value: Any, field_name: str) -> bool:
    if type(value) is not bool:
        raise DashboardGovernedWritePathError(f"{field_name} must be boolean.")
    return value


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DashboardGovernedWritePathError(f"{field_name} must be a dictionary.")
    return value


def _require_optional_mapping(value: Any, field_name: str) -> dict[str, Any] | None:
    if value is not None and not isinstance(value, dict):
        raise DashboardGovernedWritePathError(
            f"{field_name} must be a dictionary or None."
        )
    return value


def _require_list_of_strings(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise DashboardGovernedWritePathError(
            f"{field_name} must be a list of strings."
        )
    return value
