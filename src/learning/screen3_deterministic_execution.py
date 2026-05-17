"""Phase 7CB deterministic Screen 3 re-analysis execution service.

This module adds a governed service-layer execution path for Screen 3
re-analysis requests. It uses an injected runner only; it never shells out,
imports run_analysis.py, calls Object Storage, regenerates dashboards, mutates
Phase 4I, or changes parser/scoring/recommendation semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Callable

from src.learning.governed_workflow_repository import (
    GovernedWorkflowRepository,
    GovernedWorkflowRepositoryError,
    PersistedWorkflowAudit,
    PersistedWorkflowOutputArtifact,
    PersistedWorkflowRequest,
    PersistedWorkflowTransaction,
    PersistedWorkflowValidation,
    WorkflowPersistenceResult,
    create_workflow_audit_id,
    create_workflow_output_id,
    create_workflow_request_id,
    create_workflow_validation_id,
    hash_payload,
)
from src.learning.screen3_reanalysis_request import (
    BackendReAnalysisRequest,
    SCREEN3_REANALYSIS_SOURCE_MODES,
    backend_reanalysis_request_from_dict,
    backend_reanalysis_request_to_dict,
)


DETERMINISTIC_EXECUTION_ACTIONS = (
    "analyze_selection",
    "rerun_analysis",
)

DETERMINISTIC_EXECUTION_STATUSES = (
    "dry_run_only",
    "blocked_no_runner",
    "invalid_request",
    "persisted_metadata_only",
    "deterministic_runner_completed",
    "idempotent_replay",
    "failed_safely",
)

DETERMINISTIC_EXECUTION_MODES = (
    "dry_run",
    "runner_injected",
    "metadata_persistence",
)

_TOKEN_PATTERN = re.compile(r"[^A-Za-z0-9]+")
Runner = Callable[["DeterministicExecutionRequestEnvelope"], dict[str, Any]]


class Screen3DeterministicExecutionError(ValueError):
    """Raised when Phase 7CB deterministic execution metadata is unsafe."""


@dataclass(frozen=True)
class DeterministicExecutionRequestEnvelope:
    """Governed request envelope for deterministic Screen 3 execution."""

    execution_id: str
    reanalysis_request: BackendReAnalysisRequest
    actor_id: str
    actor_audit_context: dict[str, Any]
    idempotency_key: str
    transaction_group_id: str
    source_mode: str
    requested_action: str
    deterministic_default: bool = True
    adaptive_runtime_requested: bool = False
    dry_run: bool = True
    validation_reference: str | None = None
    rollback_reference: str | None = None
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.execution_id, "execution_id")
        if not isinstance(self.reanalysis_request, BackendReAnalysisRequest):
            raise Screen3DeterministicExecutionError(
                "reanalysis_request must be a BackendReAnalysisRequest instance."
            )
        self.reanalysis_request.__post_init__()
        _require_text(self.actor_id, "actor_id")
        _require_mapping(self.actor_audit_context, "actor_audit_context")
        _require_text(self.idempotency_key, "idempotency_key")
        _require_text(self.transaction_group_id, "transaction_group_id")
        _require_supported(self.source_mode, SCREEN3_REANALYSIS_SOURCE_MODES, "source_mode")
        _require_text(self.requested_action, "requested_action")
        _require_bool(self.deterministic_default, "deterministic_default")
        _require_bool(self.adaptive_runtime_requested, "adaptive_runtime_requested")
        _require_bool(self.dry_run, "dry_run")
        _require_optional_text(self.validation_reference, "validation_reference")
        _require_optional_text(self.rollback_reference, "rollback_reference")
        _require_optional_text(self.created_at, "created_at")
        _require_optional_text(self.notes, "notes")
        if not self.deterministic_default:
            raise Screen3DeterministicExecutionError(
                "deterministic_default must remain true in Phase 7CB."
            )
        if self.adaptive_runtime_requested:
            raise Screen3DeterministicExecutionError(
                "adaptive_runtime_requested must remain false in Phase 7CB."
            )


@dataclass(frozen=True)
class DeterministicExecutionOutputReference:
    """Metadata reference produced by deterministic execution."""

    output_reference_id: str
    artifact_type: str
    artifact_reference: str
    artifact_summary: str
    phase4i_reference: str | None = None
    dashboard_reference: str | None = None
    comparison_reference: str | None = None
    error_reference: str | None = None
    persisted: bool = False
    output_written: bool = False
    dashboard_regenerated: bool = False
    phase4i_mutated: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.output_reference_id, "output_reference_id")
        _require_supported(
            self.artifact_type,
            (
                "validation_response",
                "analysis_run_record",
                "phase4i_payload_reference",
                "dashboard_artifact_reference",
                "error_artifact",
                "source_validation_artifact",
            ),
            "artifact_type",
        )
        _require_text(self.artifact_reference, "artifact_reference")
        _require_text(self.artifact_summary, "artifact_summary")
        _require_optional_text(self.phase4i_reference, "phase4i_reference")
        _require_optional_text(self.dashboard_reference, "dashboard_reference")
        _require_optional_text(self.comparison_reference, "comparison_reference")
        _require_optional_text(self.error_reference, "error_reference")
        _require_bool(self.persisted, "persisted")
        _require_bool(self.output_written, "output_written")
        _require_bool(self.dashboard_regenerated, "dashboard_regenerated")
        _require_bool(self.phase4i_mutated, "phase4i_mutated")
        _require_optional_text(self.notes, "notes")
        if self.output_written:
            raise Screen3DeterministicExecutionError(
                "output_written must remain false in Phase 7CB."
            )
        if self.dashboard_regenerated:
            raise Screen3DeterministicExecutionError(
                "dashboard_regenerated must remain false in Phase 7CB."
            )
        if self.phase4i_mutated:
            raise Screen3DeterministicExecutionError(
                "phase4i_mutated must remain false in Phase 7CB."
            )


@dataclass(frozen=True)
class DeterministicExecutionResult:
    """Result record for deterministic Screen 3 re-analysis execution."""

    execution_id: str
    request_id: str
    idempotency_key: str
    transaction_group_id: str
    execution_status: str
    deterministic_execution_performed: bool
    runner_invoked: bool
    run_analysis_called: bool
    subprocess_called: bool
    adaptive_runtime_used: bool
    object_storage_called: bool
    dashboard_regenerated: bool
    phase4i_mutated: bool
    workflow_request_persisted: bool
    workflow_validation_persisted: bool
    workflow_audit_persisted: bool
    output_artifacts_persisted: bool
    output_references: tuple[DeterministicExecutionOutputReference, ...] = ()
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.execution_id, "execution_id")
        _require_text(self.request_id, "request_id")
        _require_text(self.idempotency_key, "idempotency_key")
        _require_text(self.transaction_group_id, "transaction_group_id")
        _require_supported(
            self.execution_status,
            DETERMINISTIC_EXECUTION_STATUSES,
            "execution_status",
        )
        for field_name in (
            "deterministic_execution_performed",
            "runner_invoked",
            "run_analysis_called",
            "subprocess_called",
            "adaptive_runtime_used",
            "object_storage_called",
            "dashboard_regenerated",
            "phase4i_mutated",
            "workflow_request_persisted",
            "workflow_validation_persisted",
            "workflow_audit_persisted",
            "output_artifacts_persisted",
        ):
            _require_bool(getattr(self, field_name), field_name)
        if not isinstance(self.output_references, tuple):
            raise Screen3DeterministicExecutionError(
                "output_references must be a tuple."
            )
        for reference in self.output_references:
            validate_output_reference(reference)
        _require_string_list(self.denied_reasons, "denied_reasons")
        _require_string_list(self.warnings, "warnings")
        _require_string_list(self.required_next_steps, "required_next_steps")
        _require_optional_text(self.notes, "notes")
        _reject_true(self.run_analysis_called, "run_analysis_called")
        _reject_true(self.subprocess_called, "subprocess_called")
        _reject_true(self.adaptive_runtime_used, "adaptive_runtime_used")
        _reject_true(self.object_storage_called, "object_storage_called")
        _reject_true(self.dashboard_regenerated, "dashboard_regenerated")
        _reject_true(self.phase4i_mutated, "phase4i_mutated")


def create_deterministic_execution_id(request_id: str, idempotency_key: str) -> str:
    """Create a deterministic Phase 7CB execution id."""

    _require_text(request_id, "request_id")
    _require_text(idempotency_key, "idempotency_key")
    return _stable_id("SCREEN3-DETERMINISTIC-EXECUTION", request_id, idempotency_key)


def validate_deterministic_execution_envelope(
    envelope: DeterministicExecutionRequestEnvelope,
) -> DeterministicExecutionRequestEnvelope:
    """Validate the deterministic execution envelope before running anything."""

    if not isinstance(envelope, DeterministicExecutionRequestEnvelope):
        raise Screen3DeterministicExecutionError(
            "envelope must be a DeterministicExecutionRequestEnvelope instance."
        )
    envelope.__post_init__()
    if envelope.requested_action != envelope.reanalysis_request.requested_action:
        raise Screen3DeterministicExecutionError(
            "requested_action must match reanalysis_request.requested_action."
        )
    if envelope.source_mode != envelope.reanalysis_request.selected_state.selected_source_mode:
        raise Screen3DeterministicExecutionError(
            "source_mode must match reanalysis_request selected source mode."
        )
    _require_supported(
        envelope.requested_action,
        DETERMINISTIC_EXECUTION_ACTIONS,
        "requested_action",
    )
    if envelope.source_mode == "object_storage":
        raise Screen3DeterministicExecutionError(
            "Object Storage execution belongs to Phase 7CD."
        )
    if not envelope.rollback_reference:
        raise Screen3DeterministicExecutionError(
            "rollback_reference is required for Phase 7CB execution."
        )
    if not envelope.actor_audit_context.get("actor_id"):
        raise Screen3DeterministicExecutionError(
            "actor_audit_context.actor_id is required."
        )
    return envelope


def execute_deterministic_reanalysis(
    envelope: DeterministicExecutionRequestEnvelope,
    repository: GovernedWorkflowRepository,
    runner: Runner | None = None,
) -> DeterministicExecutionResult:
    """Execute deterministic Screen 3 re-analysis through an injected runner."""

    try:
        envelope = validate_deterministic_execution_envelope(envelope)
    except Screen3DeterministicExecutionError as exc:
        return _invalid_result(envelope, str(exc))

    if not isinstance(repository, GovernedWorkflowRepository):
        raise Screen3DeterministicExecutionError(
            "repository must be a GovernedWorkflowRepository instance."
        )

    existing = repository.get_by_idempotency_key(envelope.idempotency_key)
    if existing is not None:
        return validate_deterministic_execution_result(
            DeterministicExecutionResult(
                execution_id=envelope.execution_id,
                request_id=envelope.reanalysis_request.request_id,
                idempotency_key=envelope.idempotency_key,
                transaction_group_id=existing.transaction_group_id,
                execution_status="idempotent_replay",
                deterministic_execution_performed=False,
                runner_invoked=False,
                run_analysis_called=False,
                subprocess_called=False,
                adaptive_runtime_used=False,
                object_storage_called=False,
                dashboard_regenerated=False,
                phase4i_mutated=False,
                workflow_request_persisted=True,
                workflow_validation_persisted=True,
                workflow_audit_persisted=True,
                output_artifacts_persisted=False,
                warnings=[
                    "idempotency key already persisted; deterministic runner was not invoked"
                ],
                required_next_steps=["return existing governed workflow metadata"],
                notes=envelope.notes,
            )
        )

    if envelope.dry_run:
        status = "dry_run_only"
        runner_output: dict[str, Any] | None = None
        runner_invoked = False
        performed = False
        warnings = ["dry_run=true; deterministic runner was not invoked"]
        next_steps = ["submit with dry_run=false and an injected runner to execute"]
    elif runner is None:
        status = "blocked_no_runner"
        runner_output = None
        runner_invoked = False
        performed = False
        warnings = ["no deterministic runner was supplied"]
        next_steps = ["provide an injected deterministic runner"]
    else:
        try:
            runner_output = _normalize_runner_output(runner(envelope))
        except Exception as exc:  # noqa: BLE001
            return _record_safe_failure(envelope, repository, exc)
        status = "deterministic_runner_completed"
        runner_invoked = True
        performed = True
        warnings = _string_list_from_runner(runner_output.get("warnings"))
        next_steps = ["review persisted output artifact references"]

    references = _build_output_references(
        envelope,
        runner_output,
        status=status,
        persisted=False,
    )
    try:
        persistence_result = repository.persist_workflow_bundle(
            request=_build_workflow_request(envelope, status),
            transaction=_build_workflow_transaction(envelope),
            validation=_build_workflow_validation(envelope, status),
            audit=_build_workflow_audit(envelope, status),
            output_artifacts=tuple(
                _output_reference_to_persisted_artifact(envelope, reference)
                for reference in references
            ),
        )
    except GovernedWorkflowRepositoryError as exc:
        return _record_safe_failure(envelope, repository, exc)

    if persistence_result.duplicate:
        return validate_deterministic_execution_result(
            DeterministicExecutionResult(
                execution_id=envelope.execution_id,
                request_id=envelope.reanalysis_request.request_id,
                idempotency_key=envelope.idempotency_key,
                transaction_group_id=envelope.transaction_group_id,
                execution_status="idempotent_replay",
                deterministic_execution_performed=False,
                runner_invoked=False,
                run_analysis_called=False,
                subprocess_called=False,
                adaptive_runtime_used=False,
                object_storage_called=False,
                dashboard_regenerated=False,
                phase4i_mutated=False,
                workflow_request_persisted=True,
                workflow_validation_persisted=True,
                workflow_audit_persisted=True,
                output_artifacts_persisted=False,
                warnings=[
                    "idempotency key replay detected during repository persistence"
                ],
                required_next_steps=["return existing governed workflow metadata"],
                notes=envelope.notes,
            )
        )

    persisted_refs = tuple(_with_persisted(reference) for reference in references)
    return validate_deterministic_execution_result(
        DeterministicExecutionResult(
            execution_id=envelope.execution_id,
            request_id=envelope.reanalysis_request.request_id,
            idempotency_key=envelope.idempotency_key,
            transaction_group_id=envelope.transaction_group_id,
            execution_status=status,
            deterministic_execution_performed=performed,
            runner_invoked=runner_invoked,
            run_analysis_called=False,
            subprocess_called=False,
            adaptive_runtime_used=False,
            object_storage_called=False,
            dashboard_regenerated=False,
            phase4i_mutated=False,
            workflow_request_persisted=bool(persistence_result.request),
            workflow_validation_persisted=bool(persistence_result.validation),
            workflow_audit_persisted=bool(persistence_result.audit),
            output_artifacts_persisted=bool(persistence_result.output_artifacts),
            output_references=persisted_refs,
            warnings=warnings,
            required_next_steps=next_steps,
            notes=envelope.notes,
        )
    )


def validate_deterministic_execution_result(
    result: DeterministicExecutionResult,
) -> DeterministicExecutionResult:
    """Validate deterministic execution result metadata."""

    if not isinstance(result, DeterministicExecutionResult):
        raise Screen3DeterministicExecutionError(
            "result must be a DeterministicExecutionResult instance."
        )
    result.__post_init__()
    return result


def deterministic_execution_result_to_dict(
    result: DeterministicExecutionResult,
) -> dict[str, Any]:
    """Serialize deterministic execution result metadata."""

    result = validate_deterministic_execution_result(result)
    return {
        "execution_id": result.execution_id,
        "request_id": result.request_id,
        "idempotency_key": result.idempotency_key,
        "transaction_group_id": result.transaction_group_id,
        "execution_status": result.execution_status,
        "deterministic_execution_performed": result.deterministic_execution_performed,
        "runner_invoked": result.runner_invoked,
        "run_analysis_called": result.run_analysis_called,
        "subprocess_called": result.subprocess_called,
        "adaptive_runtime_used": result.adaptive_runtime_used,
        "object_storage_called": result.object_storage_called,
        "dashboard_regenerated": result.dashboard_regenerated,
        "phase4i_mutated": result.phase4i_mutated,
        "workflow_request_persisted": result.workflow_request_persisted,
        "workflow_validation_persisted": result.workflow_validation_persisted,
        "workflow_audit_persisted": result.workflow_audit_persisted,
        "output_artifacts_persisted": result.output_artifacts_persisted,
        "output_references": [
            output_reference_to_dict(reference)
            for reference in result.output_references
        ],
        "denied_reasons": list(result.denied_reasons),
        "warnings": list(result.warnings),
        "required_next_steps": list(result.required_next_steps),
        "notes": result.notes,
    }


def deterministic_execution_result_from_dict(
    data: dict[str, Any],
) -> DeterministicExecutionResult:
    """Deserialize deterministic execution result metadata."""

    _require_mapping(data, "deterministic_execution_result")
    return DeterministicExecutionResult(
        execution_id=data.get("execution_id"),
        request_id=data.get("request_id"),
        idempotency_key=data.get("idempotency_key"),
        transaction_group_id=data.get("transaction_group_id"),
        execution_status=data.get("execution_status"),
        deterministic_execution_performed=data.get(
            "deterministic_execution_performed",
            False,
        ),
        runner_invoked=data.get("runner_invoked", False),
        run_analysis_called=data.get("run_analysis_called", False),
        subprocess_called=data.get("subprocess_called", False),
        adaptive_runtime_used=data.get("adaptive_runtime_used", False),
        object_storage_called=data.get("object_storage_called", False),
        dashboard_regenerated=data.get("dashboard_regenerated", False),
        phase4i_mutated=data.get("phase4i_mutated", False),
        workflow_request_persisted=data.get("workflow_request_persisted", False),
        workflow_validation_persisted=data.get("workflow_validation_persisted", False),
        workflow_audit_persisted=data.get("workflow_audit_persisted", False),
        output_artifacts_persisted=data.get("output_artifacts_persisted", False),
        output_references=tuple(
            output_reference_from_dict(reference)
            for reference in data.get("output_references", [])
        ),
        denied_reasons=list(data.get("denied_reasons", [])),
        warnings=list(data.get("warnings", [])),
        required_next_steps=list(data.get("required_next_steps", [])),
        notes=data.get("notes"),
    )


def output_reference_to_dict(
    ref: DeterministicExecutionOutputReference,
) -> dict[str, Any]:
    """Serialize deterministic execution output reference metadata."""

    ref = validate_output_reference(ref)
    return {
        "output_reference_id": ref.output_reference_id,
        "artifact_type": ref.artifact_type,
        "artifact_reference": ref.artifact_reference,
        "artifact_summary": ref.artifact_summary,
        "phase4i_reference": ref.phase4i_reference,
        "dashboard_reference": ref.dashboard_reference,
        "comparison_reference": ref.comparison_reference,
        "error_reference": ref.error_reference,
        "persisted": ref.persisted,
        "output_written": ref.output_written,
        "dashboard_regenerated": ref.dashboard_regenerated,
        "phase4i_mutated": ref.phase4i_mutated,
        "notes": ref.notes,
    }


def output_reference_from_dict(
    data: dict[str, Any],
) -> DeterministicExecutionOutputReference:
    """Deserialize deterministic execution output reference metadata."""

    _require_mapping(data, "deterministic_execution_output_reference")
    return DeterministicExecutionOutputReference(
        output_reference_id=data.get("output_reference_id"),
        artifact_type=data.get("artifact_type"),
        artifact_reference=data.get("artifact_reference"),
        artifact_summary=data.get("artifact_summary"),
        phase4i_reference=data.get("phase4i_reference"),
        dashboard_reference=data.get("dashboard_reference"),
        comparison_reference=data.get("comparison_reference"),
        error_reference=data.get("error_reference"),
        persisted=data.get("persisted", False),
        output_written=data.get("output_written", False),
        dashboard_regenerated=data.get("dashboard_regenerated", False),
        phase4i_mutated=data.get("phase4i_mutated", False),
        notes=data.get("notes"),
    )


def envelope_to_dict(envelope: DeterministicExecutionRequestEnvelope) -> dict[str, Any]:
    """Serialize deterministic execution envelope metadata."""

    envelope = validate_deterministic_execution_envelope(envelope)
    return {
        "execution_id": envelope.execution_id,
        "reanalysis_request": backend_reanalysis_request_to_dict(
            envelope.reanalysis_request
        ),
        "actor_id": envelope.actor_id,
        "actor_audit_context": dict(envelope.actor_audit_context),
        "idempotency_key": envelope.idempotency_key,
        "transaction_group_id": envelope.transaction_group_id,
        "source_mode": envelope.source_mode,
        "requested_action": envelope.requested_action,
        "deterministic_default": envelope.deterministic_default,
        "adaptive_runtime_requested": envelope.adaptive_runtime_requested,
        "dry_run": envelope.dry_run,
        "validation_reference": envelope.validation_reference,
        "rollback_reference": envelope.rollback_reference,
        "created_at": envelope.created_at,
        "notes": envelope.notes,
    }


def envelope_from_dict(data: dict[str, Any]) -> DeterministicExecutionRequestEnvelope:
    """Deserialize deterministic execution envelope metadata."""

    _require_mapping(data, "deterministic_execution_envelope")
    request_data = data.get("reanalysis_request")
    if not isinstance(request_data, dict):
        raise Screen3DeterministicExecutionError("reanalysis_request is required.")
    return DeterministicExecutionRequestEnvelope(
        execution_id=data.get("execution_id"),
        reanalysis_request=backend_reanalysis_request_from_dict(request_data),
        actor_id=data.get("actor_id"),
        actor_audit_context=data.get("actor_audit_context"),
        idempotency_key=data.get("idempotency_key"),
        transaction_group_id=data.get("transaction_group_id"),
        source_mode=data.get("source_mode"),
        requested_action=data.get("requested_action"),
        deterministic_default=data.get("deterministic_default", True),
        adaptive_runtime_requested=data.get("adaptive_runtime_requested", False),
        dry_run=data.get("dry_run", True),
        validation_reference=data.get("validation_reference"),
        rollback_reference=data.get("rollback_reference"),
        created_at=data.get("created_at"),
        notes=data.get("notes"),
    )


def validate_output_reference(
    reference: DeterministicExecutionOutputReference,
) -> DeterministicExecutionOutputReference:
    """Validate an output reference."""

    if not isinstance(reference, DeterministicExecutionOutputReference):
        raise Screen3DeterministicExecutionError(
            "reference must be a DeterministicExecutionOutputReference instance."
        )
    reference.__post_init__()
    return reference


def _build_workflow_request(
    envelope: DeterministicExecutionRequestEnvelope,
    status: str,
) -> PersistedWorkflowRequest:
    payload = {
        "execution_id": envelope.execution_id,
        "reanalysis_request": backend_reanalysis_request_to_dict(
            envelope.reanalysis_request
        ),
        "validation_reference": envelope.validation_reference,
        "rollback_reference": envelope.rollback_reference,
        "source_mode": envelope.source_mode,
        "requested_action": envelope.requested_action,
        "deterministic_default": envelope.deterministic_default,
        "adaptive_runtime_requested": False,
        "dry_run": envelope.dry_run,
        "phase4i_mutation_requested": False,
        "dashboard_regeneration_requested": False,
        "object_storage_requested": False,
        "execution_status": status,
    }
    return PersistedWorkflowRequest(
        workflow_request_id=create_workflow_request_id(
            "screen3_deterministic_reanalysis",
            envelope.idempotency_key,
        ),
        transaction_group_id=envelope.transaction_group_id,
        idempotency_key=envelope.idempotency_key,
        source_screen="screen_3",
        workflow_type="screen3_deterministic_reanalysis",
        requested_action=envelope.requested_action,
        target_type="screen3_reanalysis_request",
        target_id=envelope.reanalysis_request.request_id,
        actor_id=envelope.actor_id,
        payload=payload,
        status="VALIDATED",
        notes=envelope.notes,
    )


def _build_workflow_transaction(
    envelope: DeterministicExecutionRequestEnvelope,
) -> PersistedWorkflowTransaction:
    return PersistedWorkflowTransaction(
        transaction_group_id=envelope.transaction_group_id,
        idempotency_key=envelope.idempotency_key,
        transaction_scope="screen3_deterministic_reanalysis_execution",
        rollback_reference=envelope.rollback_reference or "",
        status="IN_PROGRESS",
        notes=envelope.notes,
    )


def _build_workflow_validation(
    envelope: DeterministicExecutionRequestEnvelope,
    status: str,
) -> PersistedWorkflowValidation:
    return PersistedWorkflowValidation(
        workflow_validation_id=create_workflow_validation_id(
            create_workflow_request_id(
                "screen3_deterministic_reanalysis",
                envelope.idempotency_key,
            )
        ),
        workflow_request_id=create_workflow_request_id(
            "screen3_deterministic_reanalysis",
            envelope.idempotency_key,
        ),
        validation_status=status,
        valid_flag=True,
        warnings=[
            "deterministic execution only",
            "adaptive runtime disabled",
            "dashboard regeneration disabled",
        ],
        required_next_steps=["review persisted output references"],
        notes=envelope.notes,
    )


def _build_workflow_audit(
    envelope: DeterministicExecutionRequestEnvelope,
    status: str,
) -> PersistedWorkflowAudit:
    request_id = create_workflow_request_id(
        "screen3_deterministic_reanalysis",
        envelope.idempotency_key,
    )
    payload = {
        "execution_id": envelope.execution_id,
        "request_id": envelope.reanalysis_request.request_id,
        "status": status,
        "requested_action": envelope.requested_action,
        "actor_id": envelope.actor_id,
        "adaptive_runtime_used": False,
    }
    return PersistedWorkflowAudit(
        workflow_audit_id=create_workflow_audit_id(
            request_id,
            "screen3_deterministic_execution_recorded",
        ),
        workflow_request_id=request_id,
        transaction_group_id=envelope.transaction_group_id,
        actor_id=envelope.actor_id,
        action="screen3_deterministic_execution_recorded",
        audit_summary=(
            "Phase 7CB deterministic Screen 3 execution metadata recorded; "
            "runtime truth was not mutated."
        ),
        payload_hash=hash_payload(payload),
        notes=envelope.notes,
    )


def _build_output_references(
    envelope: DeterministicExecutionRequestEnvelope,
    runner_output: dict[str, Any] | None,
    *,
    status: str,
    persisted: bool,
) -> tuple[DeterministicExecutionOutputReference, ...]:
    request_id = create_workflow_request_id(
        "screen3_deterministic_reanalysis",
        envelope.idempotency_key,
    )
    output = runner_output or {}
    summary = str(
        output.get("artifact_summary")
        or output.get("summary")
        or f"Phase 7CB {status} metadata reference."
    )
    analysis_reference = str(
        output.get("analysis_run_reference")
        or output.get("analysis_run_record")
        or output.get("run_id")
        or envelope.execution_id
    )
    references = [
        DeterministicExecutionOutputReference(
            output_reference_id=_output_reference_id(
                request_id,
                "analysis_run_record",
                analysis_reference,
            ),
            artifact_type="analysis_run_record",
            artifact_reference=analysis_reference,
            artifact_summary=summary,
            persisted=persisted,
            notes=envelope.notes,
        )
    ]
    phase4i_reference = output.get("phase4i_reference") or output.get(
        "phase4i_payload_reference"
    )
    if phase4i_reference:
        references.append(
            DeterministicExecutionOutputReference(
                output_reference_id=_output_reference_id(
                    request_id,
                    "phase4i_payload_reference",
                    str(phase4i_reference),
                ),
                artifact_type="phase4i_payload_reference",
                artifact_reference=str(phase4i_reference),
                artifact_summary="Phase 4I payload reference only.",
                phase4i_reference=str(phase4i_reference),
                persisted=persisted,
                notes=envelope.notes,
            )
        )
    dashboard_reference = output.get("dashboard_reference") or output.get(
        "dashboard_artifact_reference"
    )
    if dashboard_reference:
        references.append(
            DeterministicExecutionOutputReference(
                output_reference_id=_output_reference_id(
                    request_id,
                    "dashboard_artifact_reference",
                    str(dashboard_reference),
                ),
                artifact_type="dashboard_artifact_reference",
                artifact_reference=str(dashboard_reference),
                artifact_summary="Dashboard artifact reference only.",
                dashboard_reference=str(dashboard_reference),
                persisted=persisted,
                notes=envelope.notes,
            )
        )
    if status in {"dry_run_only", "blocked_no_runner"}:
        validation_reference = envelope.validation_reference or envelope.execution_id
        references.append(
            DeterministicExecutionOutputReference(
                output_reference_id=_output_reference_id(
                    request_id,
                    "validation_response",
                    validation_reference,
                ),
                artifact_type="validation_response",
                artifact_reference=validation_reference,
                artifact_summary=f"{status} validation response reference.",
                persisted=persisted,
                notes=envelope.notes,
            )
        )
    return tuple(references)


def _output_reference_to_persisted_artifact(
    envelope: DeterministicExecutionRequestEnvelope,
    reference: DeterministicExecutionOutputReference,
) -> PersistedWorkflowOutputArtifact:
    request_id = create_workflow_request_id(
        "screen3_deterministic_reanalysis",
        envelope.idempotency_key,
    )
    metadata = {
        "execution_id": envelope.execution_id,
        "request_id": envelope.reanalysis_request.request_id,
        "output_written": False,
        "dashboard_regenerated": False,
        "phase4i_mutated": False,
    }
    return PersistedWorkflowOutputArtifact(
        workflow_output_id=create_workflow_output_id(
            request_id,
            reference.artifact_type,
            reference.artifact_reference,
        ),
        workflow_request_id=request_id,
        artifact_type=reference.artifact_type,
        artifact_reference=reference.artifact_reference,
        artifact_summary=reference.artifact_summary,
        artifact_metadata=metadata,
        status="RECORDED",
        notes=reference.notes,
    )


def _record_safe_failure(
    envelope: DeterministicExecutionRequestEnvelope,
    repository: GovernedWorkflowRepository,
    exc: Exception,
) -> DeterministicExecutionResult:
    message = f"{type(exc).__name__}: {exc}"
    try:
        repository.record_workflow_failure(
            transaction_group_id=envelope.transaction_group_id,
            idempotency_key=envelope.idempotency_key,
            actor_id=envelope.actor_id,
            action="screen3_deterministic_execution_failed",
            error_message=message,
            rollback_reference=envelope.rollback_reference or "ROLLBACK-UNAVAILABLE",
            transaction_scope="screen3_deterministic_reanalysis_execution",
            notes=envelope.notes,
        )
    except Exception:  # noqa: BLE001
        pass
    reference = DeterministicExecutionOutputReference(
        output_reference_id=_output_reference_id(
            envelope.execution_id,
            "error_artifact",
            hash_payload({"error": message})[:16],
        ),
        artifact_type="error_artifact",
        artifact_reference=f"screen3-deterministic-error:{hash_payload({'error': message})[:16]}",
        artifact_summary="Safe failure metadata reference.",
        error_reference=message,
        persisted=False,
        notes=envelope.notes,
    )
    return validate_deterministic_execution_result(
        DeterministicExecutionResult(
            execution_id=envelope.execution_id,
            request_id=envelope.reanalysis_request.request_id,
            idempotency_key=envelope.idempotency_key,
            transaction_group_id=envelope.transaction_group_id,
            execution_status="failed_safely",
            deterministic_execution_performed=False,
            runner_invoked=False,
            run_analysis_called=False,
            subprocess_called=False,
            adaptive_runtime_used=False,
            object_storage_called=False,
            dashboard_regenerated=False,
            phase4i_mutated=False,
            workflow_request_persisted=False,
            workflow_validation_persisted=False,
            workflow_audit_persisted=False,
            output_artifacts_persisted=False,
            output_references=(reference,),
            denied_reasons=[message],
            required_next_steps=["review failure metadata and retry safely"],
            notes=envelope.notes,
        )
    )


def _invalid_result(envelope: Any, reason: str) -> DeterministicExecutionResult:
    execution_id = getattr(envelope, "execution_id", "SCREEN3-DETERMINISTIC-INVALID")
    reanalysis_request = getattr(envelope, "reanalysis_request", None)
    request_id = getattr(reanalysis_request, "request_id", "UNKNOWN-REQUEST")
    idempotency_key = getattr(envelope, "idempotency_key", "UNKNOWN-IDEMPOTENCY")
    transaction_group_id = getattr(envelope, "transaction_group_id", "UNKNOWN-TX")
    return validate_deterministic_execution_result(
        DeterministicExecutionResult(
            execution_id=execution_id,
            request_id=request_id,
            idempotency_key=idempotency_key,
            transaction_group_id=transaction_group_id,
            execution_status="invalid_request",
            deterministic_execution_performed=False,
            runner_invoked=False,
            run_analysis_called=False,
            subprocess_called=False,
            adaptive_runtime_used=False,
            object_storage_called=False,
            dashboard_regenerated=False,
            phase4i_mutated=False,
            workflow_request_persisted=False,
            workflow_validation_persisted=False,
            workflow_audit_persisted=False,
            output_artifacts_persisted=False,
            denied_reasons=[reason],
            required_next_steps=["fix deterministic execution envelope metadata"],
        )
    )


def _normalize_runner_output(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise Screen3DeterministicExecutionError(
            "deterministic runner must return a dictionary."
        )
    if value.get("adaptive_runtime_used") is True:
        raise Screen3DeterministicExecutionError(
            "deterministic runner may not use adaptive runtime."
        )
    if value.get("run_analysis_called") is True:
        raise Screen3DeterministicExecutionError(
            "deterministic runner may not report run_analysis_called=true."
        )
    if value.get("subprocess_called") is True:
        raise Screen3DeterministicExecutionError(
            "deterministic runner may not report subprocess_called=true."
        )
    if value.get("object_storage_called") is True:
        raise Screen3DeterministicExecutionError(
            "deterministic runner may not report object_storage_called=true."
        )
    if value.get("dashboard_regenerated") is True:
        raise Screen3DeterministicExecutionError(
            "deterministic runner may not regenerate dashboards in Phase 7CB."
        )
    if value.get("phase4i_mutated") is True:
        raise Screen3DeterministicExecutionError(
            "deterministic runner may not mutate Phase 4I."
        )
    return dict(value)


def _string_list_from_runner(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise Screen3DeterministicExecutionError(
            "runner warnings must be a list of strings."
        )
    return value


def _with_persisted(
    reference: DeterministicExecutionOutputReference,
) -> DeterministicExecutionOutputReference:
    return DeterministicExecutionOutputReference(
        output_reference_id=reference.output_reference_id,
        artifact_type=reference.artifact_type,
        artifact_reference=reference.artifact_reference,
        artifact_summary=reference.artifact_summary,
        phase4i_reference=reference.phase4i_reference,
        dashboard_reference=reference.dashboard_reference,
        comparison_reference=reference.comparison_reference,
        error_reference=reference.error_reference,
        persisted=True,
        output_written=False,
        dashboard_regenerated=False,
        phase4i_mutated=False,
        notes=reference.notes,
    )


def _output_reference_id(
    request_id: str,
    artifact_type: str,
    artifact_reference: str,
) -> str:
    return _stable_id(
        "SCREEN3-DETERMINISTIC-OUTPUT",
        request_id,
        artifact_type,
        artifact_reference,
    )


def _stable_id(prefix: str, *parts: str) -> str:
    tokens = [_normalize_token(prefix)]
    tokens.extend(_normalize_token(_require_text(part, "id_part")) for part in parts)
    raw_id = "-".join(tokens)
    if len(raw_id) <= 150:
        return raw_id
    digest = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:24].upper()
    return f"{tokens[0]}-{digest}"


def _normalize_token(value: str) -> str:
    normalized = _TOKEN_PATTERN.sub("-", value.strip().upper()).strip("-")
    return normalized or "UNSPECIFIED"


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Screen3DeterministicExecutionError(f"{field_name} is required.")
    return value.strip()


def _require_optional_text(value: Any | None, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise Screen3DeterministicExecutionError(
            f"{field_name} must be text when set."
        )
    if not value.strip():
        raise Screen3DeterministicExecutionError(
            f"{field_name} cannot be blank when set."
        )
    return value.strip()


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise Screen3DeterministicExecutionError(f"{field_name} must be a mapping.")
    return value


def _require_bool(value: Any, field_name: str) -> bool:
    if type(value) is not bool:
        raise Screen3DeterministicExecutionError(f"{field_name} must be boolean.")
    return value


def _require_string_list(values: Any, field_name: str) -> None:
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise Screen3DeterministicExecutionError(
            f"{field_name} must be a list of strings."
        )


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        raise Screen3DeterministicExecutionError(
            f"{field_name} must be one of: {', '.join(supported)}."
        )


def _reject_true(value: bool, field_name: str) -> None:
    if value:
        raise Screen3DeterministicExecutionError(
            f"{field_name} must remain false in Phase 7CB."
        )


def _json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
