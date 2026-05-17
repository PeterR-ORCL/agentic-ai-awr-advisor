"""Phase 7CC active Screen 3 AWR/report comparison execution.

This module wraps the existing in-memory Screen 3 comparison engine with a
governed execution envelope and optional workflow metadata persistence. It does
not read files, fetch report content from a database, call Object Storage,
invoke run_analysis.py, regenerate dashboards, mutate Phase 4I, use adaptive
runtime behavior, or implement Phase 8 sizing/TCO comparison.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any

from src.learning.governed_workflow_repository import (
    GovernedWorkflowRepository,
    GovernedWorkflowRepositoryError,
    PersistedWorkflowAudit,
    PersistedWorkflowOutputArtifact,
    PersistedWorkflowRequest,
    PersistedWorkflowTransaction,
    PersistedWorkflowValidation,
    create_workflow_audit_id,
    create_workflow_output_id,
    create_workflow_request_id,
    create_workflow_validation_id,
    hash_payload,
)
from src.learning.screen3_reanalysis_controller import (
    AWRReportComparisonArtifact,
    awr_report_comparison_artifact_from_dict,
    awr_report_comparison_artifact_to_dict,
    build_awr_report_comparison,
    validate_awr_report_comparison_artifact,
)
from src.learning.screen3_reanalysis_request import (
    BackendReAnalysisRequest,
    SCREEN3_REANALYSIS_SOURCE_MODES,
    backend_reanalysis_request_from_dict,
    backend_reanalysis_request_to_dict,
)


COMPARISON_EXECUTION_STATUSES = (
    "blocked_invalid_request",
    "blocked_insufficient_inputs",
    "comparison_built_in_memory",
    "comparison_persisted_metadata",
    "idempotent_replay",
    "failed_safely",
)

COMPARISON_INPUT_READINESS_STATUSES = (
    "comparison_ready",
    "already_loaded",
    "staged_needs_load",
    "needs_reanalysis",
    "missing_structured_payload",
    "invalid",
)

_WORKFLOW_TYPE = "screen3_comparison_execution"
_WORKFLOW_SCOPE = "screen3_comparison_execution"
_REQUESTED_ACTION = "build_comparison"
_ARTIFACT_TYPE = "comparison_artifact"
_STAGED_INPUT_DENIED_REASON = (
    "Selected AWR is staged but not loaded; run deterministic load/re-analysis "
    "before comparison."
)
_MISSING_STRUCTURED_PAYLOAD_DENIED_REASON = (
    "Selected AWR lacks a structured comparison-ready payload; run deterministic "
    "load/re-analysis before comparison."
)
_STRUCTURED_COMPARISON_SECTION_NAMES = (
    "scores",
    "domain_scores",
    "waits",
    "wait_events",
    "sql_concentration",
    "top_sql_concentration",
    "trends",
    "anomalies",
    "topology",
    "platform_target",
    "target_platform",
    "source_options",
    "metrics",
    "data_availability",
    "missing_metrics",
)
_TOKEN_PATTERN = re.compile(r"[^A-Za-z0-9]+")


class Screen3ComparisonExecutionError(ValueError):
    """Raised when Phase 7CC comparison execution metadata is unsafe."""


@dataclass(frozen=True)
class ComparisonExecutionRequestEnvelope:
    """Governed request envelope for active Screen 3 comparison execution."""

    comparison_execution_id: str
    reanalysis_request: BackendReAnalysisRequest
    actor_id: str
    actor_audit_context: dict[str, Any]
    idempotency_key: str
    transaction_group_id: str
    comparison_name: str
    comparison_inputs: list[dict[str, Any]]
    baseline_reference: str | None
    requested_action: str
    source_mode: str
    deterministic_default: bool = True
    adaptive_runtime_requested: bool = False
    dry_run: bool = False
    validation_reference: str | None = None
    rollback_reference: str | None = None
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.comparison_execution_id, "comparison_execution_id")
        if not isinstance(self.reanalysis_request, BackendReAnalysisRequest):
            raise Screen3ComparisonExecutionError(
                "reanalysis_request must be a BackendReAnalysisRequest instance."
            )
        self.reanalysis_request.__post_init__()
        _require_text(self.actor_id, "actor_id")
        _require_mapping(self.actor_audit_context, "actor_audit_context")
        _require_text(self.idempotency_key, "idempotency_key")
        _require_text(self.transaction_group_id, "transaction_group_id")
        _require_text(self.comparison_name, "comparison_name")
        _require_comparison_inputs(self.comparison_inputs, require_two=False)
        _require_optional_text(self.baseline_reference, "baseline_reference")
        _require_text(self.requested_action, "requested_action")
        _require_supported(self.source_mode, SCREEN3_REANALYSIS_SOURCE_MODES, "source_mode")
        _require_bool(self.deterministic_default, "deterministic_default")
        _require_bool(self.adaptive_runtime_requested, "adaptive_runtime_requested")
        _require_bool(self.dry_run, "dry_run")
        _require_optional_text(self.validation_reference, "validation_reference")
        _require_optional_text(self.rollback_reference, "rollback_reference")
        _require_optional_text(self.created_at, "created_at")
        _require_optional_text(self.notes, "notes")
        if not self.deterministic_default:
            raise Screen3ComparisonExecutionError(
                "deterministic_default must remain true in Phase 7CC."
            )
        if self.adaptive_runtime_requested:
            raise Screen3ComparisonExecutionError(
                "adaptive_runtime_requested must remain false in Phase 7CC."
            )


@dataclass(frozen=True)
class ComparisonOutputReference:
    """Metadata reference for a comparison artifact."""

    output_reference_id: str
    comparison_id: str
    artifact_type: str
    artifact_reference: str
    artifact_summary: str
    persisted: bool = False
    output_written: bool = False
    dashboard_regenerated: bool = False
    phase4i_mutated: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.output_reference_id, "output_reference_id")
        _require_text(self.comparison_id, "comparison_id")
        _require_supported(self.artifact_type, (_ARTIFACT_TYPE,), "artifact_type")
        _require_text(self.artifact_reference, "artifact_reference")
        _require_text(self.artifact_summary, "artifact_summary")
        _require_bool(self.persisted, "persisted")
        _require_bool(self.output_written, "output_written")
        _require_bool(self.dashboard_regenerated, "dashboard_regenerated")
        _require_bool(self.phase4i_mutated, "phase4i_mutated")
        _require_optional_text(self.notes, "notes")
        _reject_true(self.output_written, "output_written")
        _reject_true(self.dashboard_regenerated, "dashboard_regenerated")
        _reject_true(self.phase4i_mutated, "phase4i_mutated")


@dataclass(frozen=True)
class ComparisonExecutionResult:
    """Result record for active Screen 3 comparison execution."""

    comparison_execution_id: str
    request_id: str
    idempotency_key: str
    transaction_group_id: str
    execution_status: str
    comparison_built: bool
    comparison_artifact: AWRReportComparisonArtifact | None
    workflow_request_persisted: bool
    workflow_validation_persisted: bool
    workflow_audit_persisted: bool
    output_artifacts_persisted: bool
    idempotent_replay: bool
    run_analysis_called: bool
    subprocess_called: bool
    object_storage_called: bool
    local_file_read_performed: bool
    parser_called: bool
    db_lookup_performed: bool
    dashboard_regenerated: bool
    phase4i_mutated: bool
    adaptive_runtime_used: bool
    phase8_sizing_tco_used: bool
    output_references: tuple[ComparisonOutputReference, ...] = ()
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.comparison_execution_id, "comparison_execution_id")
        _require_text(self.request_id, "request_id")
        _require_text(self.idempotency_key, "idempotency_key")
        _require_text(self.transaction_group_id, "transaction_group_id")
        _require_supported(
            self.execution_status,
            COMPARISON_EXECUTION_STATUSES,
            "execution_status",
        )
        _require_bool(self.comparison_built, "comparison_built")
        if self.comparison_artifact is not None:
            validate_awr_report_comparison_artifact(self.comparison_artifact)
        for field_name in (
            "workflow_request_persisted",
            "workflow_validation_persisted",
            "workflow_audit_persisted",
            "output_artifacts_persisted",
            "idempotent_replay",
            "run_analysis_called",
            "subprocess_called",
            "object_storage_called",
            "local_file_read_performed",
            "parser_called",
            "db_lookup_performed",
            "dashboard_regenerated",
            "phase4i_mutated",
            "adaptive_runtime_used",
            "phase8_sizing_tco_used",
        ):
            _require_bool(getattr(self, field_name), field_name)
        if not isinstance(self.output_references, tuple):
            raise Screen3ComparisonExecutionError("output_references must be a tuple.")
        for reference in self.output_references:
            validate_comparison_output_reference(reference)
        _require_string_list(self.denied_reasons, "denied_reasons")
        _require_string_list(self.warnings, "warnings")
        _require_string_list(self.required_next_steps, "required_next_steps")
        _require_optional_text(self.notes, "notes")
        _reject_true(self.run_analysis_called, "run_analysis_called")
        _reject_true(self.subprocess_called, "subprocess_called")
        _reject_true(self.object_storage_called, "object_storage_called")
        _reject_true(self.local_file_read_performed, "local_file_read_performed")
        _reject_true(self.parser_called, "parser_called")
        _reject_true(self.db_lookup_performed, "db_lookup_performed")
        _reject_true(self.dashboard_regenerated, "dashboard_regenerated")
        _reject_true(self.phase4i_mutated, "phase4i_mutated")
        _reject_true(self.adaptive_runtime_used, "adaptive_runtime_used")
        _reject_true(self.phase8_sizing_tco_used, "phase8_sizing_tco_used")
        if self.comparison_built and self.comparison_artifact is None:
            raise Screen3ComparisonExecutionError(
                "comparison_artifact is required when comparison_built is true."
            )
        if self.execution_status == "idempotent_replay" and not self.idempotent_replay:
            raise Screen3ComparisonExecutionError(
                "idempotent_replay must be true for idempotent_replay status."
            )


def create_comparison_execution_id(request_id: str, idempotency_key: str) -> str:
    """Create a deterministic Phase 7CC comparison execution id."""

    _require_text(request_id, "request_id")
    _require_text(idempotency_key, "idempotency_key")
    return _stable_id("SCREEN3-COMPARISON-EXECUTION", request_id, idempotency_key)


def validate_comparison_execution_envelope(
    envelope: ComparisonExecutionRequestEnvelope,
) -> ComparisonExecutionRequestEnvelope:
    """Validate a comparison execution envelope before building a comparison."""

    if not isinstance(envelope, ComparisonExecutionRequestEnvelope):
        raise Screen3ComparisonExecutionError(
            "envelope must be a ComparisonExecutionRequestEnvelope instance."
        )
    envelope.__post_init__()
    if envelope.requested_action != _REQUESTED_ACTION:
        raise Screen3ComparisonExecutionError(
            "requested_action must be build_comparison in Phase 7CC."
        )
    if envelope.requested_action != envelope.reanalysis_request.requested_action:
        raise Screen3ComparisonExecutionError(
            "requested_action must match reanalysis_request.requested_action."
        )
    if envelope.source_mode != envelope.reanalysis_request.selected_state.selected_source_mode:
        raise Screen3ComparisonExecutionError(
            "source_mode must match reanalysis_request selected source mode."
        )
    _require_comparison_inputs(envelope.comparison_inputs, require_two=True)
    _validate_comparison_input_readiness(envelope.comparison_inputs)
    if not envelope.actor_audit_context.get("actor_id"):
        raise Screen3ComparisonExecutionError(
            "actor_audit_context.actor_id is required."
        )
    if envelope.actor_audit_context.get("actor_id") != envelope.actor_id:
        raise Screen3ComparisonExecutionError(
            "actor_audit_context.actor_id must match actor_id."
        )
    if not envelope.rollback_reference:
        raise Screen3ComparisonExecutionError(
            "rollback_reference is required for Phase 7CC execution."
        )
    if envelope.source_mode == "object_storage":
        raise Screen3ComparisonExecutionError(
            "Object Storage load execution belongs to Phase 7CD."
        )
    return envelope


def execute_awr_report_comparison(
    envelope: ComparisonExecutionRequestEnvelope,
    repository: GovernedWorkflowRepository | None = None,
) -> ComparisonExecutionResult:
    """Build an in-memory comparison and optionally persist governed metadata."""

    try:
        envelope = validate_comparison_execution_envelope(envelope)
    except Screen3ComparisonExecutionError as exc:
        return _blocked_result(envelope, str(exc))

    if repository is not None and not isinstance(repository, GovernedWorkflowRepository):
        raise Screen3ComparisonExecutionError(
            "repository must be a GovernedWorkflowRepository instance or None."
        )

    if repository is not None:
        existing = repository.get_by_idempotency_key(envelope.idempotency_key)
        if existing is not None:
            return validate_comparison_execution_result(
                ComparisonExecutionResult(
                    comparison_execution_id=envelope.comparison_execution_id,
                    request_id=envelope.reanalysis_request.request_id,
                    idempotency_key=envelope.idempotency_key,
                    transaction_group_id=existing.transaction_group_id,
                    execution_status="idempotent_replay",
                    comparison_built=False,
                    comparison_artifact=None,
                    workflow_request_persisted=True,
                    workflow_validation_persisted=True,
                    workflow_audit_persisted=True,
                    output_artifacts_persisted=False,
                    idempotent_replay=True,
                    run_analysis_called=False,
                    subprocess_called=False,
                    object_storage_called=False,
                    local_file_read_performed=False,
                    parser_called=False,
                    db_lookup_performed=False,
                    dashboard_regenerated=False,
                    phase4i_mutated=False,
                    adaptive_runtime_used=False,
                    phase8_sizing_tco_used=False,
                    warnings=[
                        "idempotency key already persisted; comparison was not rebuilt"
                    ],
                    required_next_steps=["return existing governed workflow metadata"],
                    notes=envelope.notes,
                )
            )

    try:
        comparison_inputs = _comparison_ready_payloads(envelope.comparison_inputs)
        comparison_artifact = build_awr_report_comparison(
            comparison_inputs=comparison_inputs,
            comparison_name=envelope.comparison_name,
            baseline_reference=envelope.baseline_reference,
            created_by=envelope.actor_id,
            notes=envelope.notes,
        )
    except Exception as exc:  # noqa: BLE001
        return _record_safe_failure(envelope, repository, exc)

    output_references = (
        _build_output_reference(
            envelope,
            comparison_artifact,
            persisted=False,
        ),
    )
    if repository is None:
        return validate_comparison_execution_result(
            ComparisonExecutionResult(
                comparison_execution_id=envelope.comparison_execution_id,
                request_id=envelope.reanalysis_request.request_id,
                idempotency_key=envelope.idempotency_key,
                transaction_group_id=envelope.transaction_group_id,
                execution_status="comparison_built_in_memory",
                comparison_built=True,
                comparison_artifact=comparison_artifact,
                workflow_request_persisted=False,
                workflow_validation_persisted=False,
                workflow_audit_persisted=False,
                output_artifacts_persisted=False,
                idempotent_replay=False,
                run_analysis_called=False,
                subprocess_called=False,
                object_storage_called=False,
                local_file_read_performed=False,
                parser_called=False,
                db_lookup_performed=False,
                dashboard_regenerated=False,
                phase4i_mutated=False,
                adaptive_runtime_used=False,
                phase8_sizing_tco_used=False,
                output_references=output_references,
                warnings=[
                    "comparison built from supplied in-memory payloads only",
                    "repository not supplied; metadata was not persisted",
                ],
                required_next_steps=["persist comparison metadata through 7CA repository"],
                notes=envelope.notes,
            )
        )

    try:
        persistence_result = repository.persist_workflow_bundle(
            request=_build_workflow_request(envelope, comparison_artifact),
            transaction=_build_workflow_transaction(envelope),
            validation=_build_workflow_validation(envelope),
            audit=_build_workflow_audit(envelope, comparison_artifact),
            output_artifacts=tuple(
                _output_reference_to_persisted_artifact(
                    envelope,
                    reference,
                    comparison_artifact,
                )
                for reference in output_references
            ),
        )
    except GovernedWorkflowRepositoryError as exc:
        return _record_safe_failure(envelope, repository, exc, comparison_artifact)

    if persistence_result.duplicate:
        return validate_comparison_execution_result(
            ComparisonExecutionResult(
                comparison_execution_id=envelope.comparison_execution_id,
                request_id=envelope.reanalysis_request.request_id,
                idempotency_key=envelope.idempotency_key,
                transaction_group_id=envelope.transaction_group_id,
                execution_status="idempotent_replay",
                comparison_built=False,
                comparison_artifact=None,
                workflow_request_persisted=True,
                workflow_validation_persisted=True,
                workflow_audit_persisted=True,
                output_artifacts_persisted=False,
                idempotent_replay=True,
                run_analysis_called=False,
                subprocess_called=False,
                object_storage_called=False,
                local_file_read_performed=False,
                parser_called=False,
                db_lookup_performed=False,
                dashboard_regenerated=False,
                phase4i_mutated=False,
                adaptive_runtime_used=False,
                phase8_sizing_tco_used=False,
                warnings=[
                    "idempotency key replay detected during repository persistence"
                ],
                required_next_steps=["return existing governed workflow metadata"],
                notes=envelope.notes,
            )
        )

    persisted_references = tuple(_with_persisted(reference) for reference in output_references)
    return validate_comparison_execution_result(
        ComparisonExecutionResult(
            comparison_execution_id=envelope.comparison_execution_id,
            request_id=envelope.reanalysis_request.request_id,
            idempotency_key=envelope.idempotency_key,
            transaction_group_id=envelope.transaction_group_id,
            execution_status="comparison_persisted_metadata",
            comparison_built=True,
            comparison_artifact=comparison_artifact,
            workflow_request_persisted=bool(persistence_result.request),
            workflow_validation_persisted=bool(persistence_result.validation),
            workflow_audit_persisted=bool(persistence_result.audit),
            output_artifacts_persisted=bool(persistence_result.output_artifacts),
            idempotent_replay=False,
            run_analysis_called=False,
            subprocess_called=False,
            object_storage_called=False,
            local_file_read_performed=False,
            parser_called=False,
            db_lookup_performed=False,
            dashboard_regenerated=False,
            phase4i_mutated=False,
            adaptive_runtime_used=False,
            phase8_sizing_tco_used=False,
            output_references=persisted_references,
            warnings=[
                "comparison built from supplied in-memory payloads only",
                "comparison artifact metadata persisted; no artifact file was written",
            ],
            required_next_steps=["review persisted comparison artifact metadata"],
            notes=envelope.notes,
        )
    )


def validate_comparison_execution_result(
    result: ComparisonExecutionResult,
) -> ComparisonExecutionResult:
    """Validate comparison execution result metadata."""

    if not isinstance(result, ComparisonExecutionResult):
        raise Screen3ComparisonExecutionError(
            "result must be a ComparisonExecutionResult instance."
        )
    result.__post_init__()
    if result.output_artifacts_persisted and not all(
        reference.persisted for reference in result.output_references
    ):
        raise Screen3ComparisonExecutionError(
            "persisted output artifacts require persisted output references."
        )
    return result


def comparison_execution_result_to_dict(
    result: ComparisonExecutionResult,
) -> dict[str, Any]:
    """Serialize comparison execution result metadata."""

    result = validate_comparison_execution_result(result)
    return {
        "comparison_execution_id": result.comparison_execution_id,
        "request_id": result.request_id,
        "idempotency_key": result.idempotency_key,
        "transaction_group_id": result.transaction_group_id,
        "execution_status": result.execution_status,
        "comparison_built": result.comparison_built,
        "comparison_artifact": (
            awr_report_comparison_artifact_to_dict(result.comparison_artifact)
            if result.comparison_artifact
            else None
        ),
        "workflow_request_persisted": result.workflow_request_persisted,
        "workflow_validation_persisted": result.workflow_validation_persisted,
        "workflow_audit_persisted": result.workflow_audit_persisted,
        "output_artifacts_persisted": result.output_artifacts_persisted,
        "idempotent_replay": result.idempotent_replay,
        "run_analysis_called": result.run_analysis_called,
        "subprocess_called": result.subprocess_called,
        "object_storage_called": result.object_storage_called,
        "local_file_read_performed": result.local_file_read_performed,
        "parser_called": result.parser_called,
        "db_lookup_performed": result.db_lookup_performed,
        "dashboard_regenerated": result.dashboard_regenerated,
        "phase4i_mutated": result.phase4i_mutated,
        "adaptive_runtime_used": result.adaptive_runtime_used,
        "phase8_sizing_tco_used": result.phase8_sizing_tco_used,
        "output_references": [
            comparison_output_reference_to_dict(reference)
            for reference in result.output_references
        ],
        "denied_reasons": list(result.denied_reasons),
        "warnings": list(result.warnings),
        "required_next_steps": list(result.required_next_steps),
        "notes": result.notes,
    }


def comparison_execution_result_from_dict(
    data: dict[str, Any],
) -> ComparisonExecutionResult:
    """Deserialize comparison execution result metadata."""

    _require_mapping(data, "comparison_execution_result")
    artifact_data = data.get("comparison_artifact")
    return ComparisonExecutionResult(
        comparison_execution_id=data.get("comparison_execution_id"),
        request_id=data.get("request_id"),
        idempotency_key=data.get("idempotency_key"),
        transaction_group_id=data.get("transaction_group_id"),
        execution_status=data.get("execution_status"),
        comparison_built=data.get("comparison_built", False),
        comparison_artifact=(
            awr_report_comparison_artifact_from_dict(artifact_data)
            if artifact_data is not None
            else None
        ),
        workflow_request_persisted=data.get("workflow_request_persisted", False),
        workflow_validation_persisted=data.get("workflow_validation_persisted", False),
        workflow_audit_persisted=data.get("workflow_audit_persisted", False),
        output_artifacts_persisted=data.get("output_artifacts_persisted", False),
        idempotent_replay=data.get("idempotent_replay", False),
        run_analysis_called=data.get("run_analysis_called", False),
        subprocess_called=data.get("subprocess_called", False),
        object_storage_called=data.get("object_storage_called", False),
        local_file_read_performed=data.get("local_file_read_performed", False),
        parser_called=data.get("parser_called", False),
        db_lookup_performed=data.get("db_lookup_performed", False),
        dashboard_regenerated=data.get("dashboard_regenerated", False),
        phase4i_mutated=data.get("phase4i_mutated", False),
        adaptive_runtime_used=data.get("adaptive_runtime_used", False),
        phase8_sizing_tco_used=data.get("phase8_sizing_tco_used", False),
        output_references=tuple(
            comparison_output_reference_from_dict(reference)
            for reference in data.get("output_references", [])
        ),
        denied_reasons=list(data.get("denied_reasons", [])),
        warnings=list(data.get("warnings", [])),
        required_next_steps=list(data.get("required_next_steps", [])),
        notes=data.get("notes"),
    )


def comparison_output_reference_to_dict(
    ref: ComparisonOutputReference,
) -> dict[str, Any]:
    """Serialize comparison output reference metadata."""

    ref = validate_comparison_output_reference(ref)
    return {
        "output_reference_id": ref.output_reference_id,
        "comparison_id": ref.comparison_id,
        "artifact_type": ref.artifact_type,
        "artifact_reference": ref.artifact_reference,
        "artifact_summary": ref.artifact_summary,
        "persisted": ref.persisted,
        "output_written": ref.output_written,
        "dashboard_regenerated": ref.dashboard_regenerated,
        "phase4i_mutated": ref.phase4i_mutated,
        "notes": ref.notes,
    }


def comparison_output_reference_from_dict(
    data: dict[str, Any],
) -> ComparisonOutputReference:
    """Deserialize comparison output reference metadata."""

    _require_mapping(data, "comparison_output_reference")
    return ComparisonOutputReference(
        output_reference_id=data.get("output_reference_id"),
        comparison_id=data.get("comparison_id"),
        artifact_type=data.get("artifact_type"),
        artifact_reference=data.get("artifact_reference"),
        artifact_summary=data.get("artifact_summary"),
        persisted=data.get("persisted", False),
        output_written=data.get("output_written", False),
        dashboard_regenerated=data.get("dashboard_regenerated", False),
        phase4i_mutated=data.get("phase4i_mutated", False),
        notes=data.get("notes"),
    )


def comparison_execution_envelope_to_dict(
    envelope: ComparisonExecutionRequestEnvelope,
) -> dict[str, Any]:
    """Serialize comparison execution envelope metadata."""

    envelope = validate_comparison_execution_envelope(envelope)
    return {
        "comparison_execution_id": envelope.comparison_execution_id,
        "reanalysis_request": backend_reanalysis_request_to_dict(
            envelope.reanalysis_request
        ),
        "actor_id": envelope.actor_id,
        "actor_audit_context": dict(envelope.actor_audit_context),
        "idempotency_key": envelope.idempotency_key,
        "transaction_group_id": envelope.transaction_group_id,
        "comparison_name": envelope.comparison_name,
        "comparison_inputs": list(envelope.comparison_inputs),
        "baseline_reference": envelope.baseline_reference,
        "requested_action": envelope.requested_action,
        "source_mode": envelope.source_mode,
        "deterministic_default": envelope.deterministic_default,
        "adaptive_runtime_requested": envelope.adaptive_runtime_requested,
        "dry_run": envelope.dry_run,
        "validation_reference": envelope.validation_reference,
        "rollback_reference": envelope.rollback_reference,
        "created_at": envelope.created_at,
        "notes": envelope.notes,
    }


def comparison_execution_envelope_from_dict(
    data: dict[str, Any],
) -> ComparisonExecutionRequestEnvelope:
    """Deserialize comparison execution envelope metadata."""

    _require_mapping(data, "comparison_execution_envelope")
    request_data = data.get("reanalysis_request")
    if not isinstance(request_data, dict):
        raise Screen3ComparisonExecutionError("reanalysis_request is required.")
    return ComparisonExecutionRequestEnvelope(
        comparison_execution_id=data.get("comparison_execution_id"),
        reanalysis_request=backend_reanalysis_request_from_dict(request_data),
        actor_id=data.get("actor_id"),
        actor_audit_context=data.get("actor_audit_context"),
        idempotency_key=data.get("idempotency_key"),
        transaction_group_id=data.get("transaction_group_id"),
        comparison_name=data.get("comparison_name"),
        comparison_inputs=data.get("comparison_inputs", []),
        baseline_reference=data.get("baseline_reference"),
        requested_action=data.get("requested_action"),
        source_mode=data.get("source_mode"),
        deterministic_default=data.get("deterministic_default", True),
        adaptive_runtime_requested=data.get("adaptive_runtime_requested", False),
        dry_run=data.get("dry_run", False),
        validation_reference=data.get("validation_reference"),
        rollback_reference=data.get("rollback_reference"),
        created_at=data.get("created_at"),
        notes=data.get("notes"),
    )


def validate_comparison_output_reference(
    reference: ComparisonOutputReference,
) -> ComparisonOutputReference:
    """Validate a comparison output reference."""

    if not isinstance(reference, ComparisonOutputReference):
        raise Screen3ComparisonExecutionError(
            "reference must be a ComparisonOutputReference instance."
        )
    reference.__post_init__()
    return reference


def _build_workflow_request(
    envelope: ComparisonExecutionRequestEnvelope,
    comparison_artifact: AWRReportComparisonArtifact,
) -> PersistedWorkflowRequest:
    request_id = _workflow_request_id(envelope)
    payload = {
        "comparison_execution_id": envelope.comparison_execution_id,
        "comparison_id": comparison_artifact.comparison_id,
        "reanalysis_request": backend_reanalysis_request_to_dict(
            envelope.reanalysis_request
        ),
        "comparison_name": envelope.comparison_name,
        "comparison_input_count": len(envelope.comparison_inputs),
        "baseline_reference": envelope.baseline_reference,
        "validation_reference": envelope.validation_reference,
        "rollback_reference": envelope.rollback_reference,
        "requested_action": envelope.requested_action,
        "source_mode": envelope.source_mode,
        "comparison_input_readiness_statuses": [
            _comparison_input_readiness_status(item)
            for item in envelope.comparison_inputs
        ],
        "deterministic_default": True,
        "adaptive_runtime_requested": False,
        "file_read_requested": False,
        "parser_call_requested": False,
        "object_storage_requested": False,
        "db_report_lookup_requested": False,
        "dashboard_regeneration_requested": False,
        "phase4i_mutation_requested": False,
        "phase8_sizing_tco_requested": False,
    }
    return PersistedWorkflowRequest(
        workflow_request_id=request_id,
        transaction_group_id=envelope.transaction_group_id,
        idempotency_key=envelope.idempotency_key,
        source_screen="screen_3",
        workflow_type=_WORKFLOW_TYPE,
        requested_action=envelope.requested_action,
        target_type="screen3_reanalysis_request",
        target_id=envelope.reanalysis_request.request_id,
        actor_id=envelope.actor_id,
        payload=payload,
        status="VALIDATED",
        notes=envelope.notes,
    )


def _build_workflow_transaction(
    envelope: ComparisonExecutionRequestEnvelope,
) -> PersistedWorkflowTransaction:
    return PersistedWorkflowTransaction(
        transaction_group_id=envelope.transaction_group_id,
        idempotency_key=envelope.idempotency_key,
        transaction_scope=_WORKFLOW_SCOPE,
        rollback_reference=envelope.rollback_reference or "",
        status="IN_PROGRESS",
        notes=envelope.notes,
    )


def _build_workflow_validation(
    envelope: ComparisonExecutionRequestEnvelope,
) -> PersistedWorkflowValidation:
    request_id = _workflow_request_id(envelope)
    return PersistedWorkflowValidation(
        workflow_validation_id=create_workflow_validation_id(request_id),
        workflow_request_id=request_id,
        validation_status="comparison_built_in_memory",
        valid_flag=True,
        warnings=[
            "comparison uses supplied in-memory payloads only",
            "comparison input readiness was validated before comparison",
            "no file read, parser call, object storage call, report DB lookup, or dashboard regeneration",
        ],
        required_next_steps=["review persisted comparison artifact metadata"],
        notes=envelope.notes,
    )


def _build_workflow_audit(
    envelope: ComparisonExecutionRequestEnvelope,
    comparison_artifact: AWRReportComparisonArtifact,
) -> PersistedWorkflowAudit:
    request_id = _workflow_request_id(envelope)
    payload = {
        "comparison_execution_id": envelope.comparison_execution_id,
        "comparison_id": comparison_artifact.comparison_id,
        "request_id": envelope.reanalysis_request.request_id,
        "requested_action": envelope.requested_action,
        "actor_id": envelope.actor_id,
        "compared_report_count": comparison_artifact.compared_report_count,
        "phase8_sizing_tco_used": False,
    }
    return PersistedWorkflowAudit(
        workflow_audit_id=create_workflow_audit_id(
            request_id,
            "screen3_comparison_execution_recorded",
        ),
        workflow_request_id=request_id,
        transaction_group_id=envelope.transaction_group_id,
        actor_id=envelope.actor_id,
        action="screen3_comparison_execution_recorded",
        audit_summary=(
            "Phase 7CC Screen 3 comparison metadata recorded; comparison used "
            "supplied in-memory payloads only and runtime truth was not mutated."
        ),
        payload_hash=hash_payload(payload),
        notes=envelope.notes,
    )


def _build_output_reference(
    envelope: ComparisonExecutionRequestEnvelope,
    comparison_artifact: AWRReportComparisonArtifact,
    *,
    persisted: bool,
) -> ComparisonOutputReference:
    request_id = _workflow_request_id(envelope)
    artifact_reference = f"comparison:{comparison_artifact.comparison_id}"
    return ComparisonOutputReference(
        output_reference_id=create_workflow_output_id(
            request_id,
            _ARTIFACT_TYPE,
            artifact_reference,
        ),
        comparison_id=comparison_artifact.comparison_id,
        artifact_type=_ARTIFACT_TYPE,
        artifact_reference=artifact_reference,
        artifact_summary=comparison_artifact.difference_summary,
        persisted=persisted,
        output_written=False,
        dashboard_regenerated=False,
        phase4i_mutated=False,
        notes=envelope.notes,
    )


def _output_reference_to_persisted_artifact(
    envelope: ComparisonExecutionRequestEnvelope,
    reference: ComparisonOutputReference,
    comparison_artifact: AWRReportComparisonArtifact,
) -> PersistedWorkflowOutputArtifact:
    reference = validate_comparison_output_reference(reference)
    return PersistedWorkflowOutputArtifact(
        workflow_output_id=reference.output_reference_id,
        workflow_request_id=_workflow_request_id(envelope),
        artifact_type=reference.artifact_type,
        artifact_reference=reference.artifact_reference,
        artifact_summary=reference.artifact_summary,
        artifact_metadata={
            "comparison_artifact": awr_report_comparison_artifact_to_dict(
                comparison_artifact
            ),
            "artifact_written": False,
            "dashboard_regenerated": False,
            "phase4i_mutated": False,
            "phase8_sizing_tco_used": False,
        },
        status="RECORDED",
        notes=reference.notes,
    )


def _with_persisted(reference: ComparisonOutputReference) -> ComparisonOutputReference:
    return ComparisonOutputReference(
        output_reference_id=reference.output_reference_id,
        comparison_id=reference.comparison_id,
        artifact_type=reference.artifact_type,
        artifact_reference=reference.artifact_reference,
        artifact_summary=reference.artifact_summary,
        persisted=True,
        output_written=False,
        dashboard_regenerated=False,
        phase4i_mutated=False,
        notes=reference.notes,
    )


def _record_safe_failure(
    envelope: ComparisonExecutionRequestEnvelope,
    repository: GovernedWorkflowRepository | None,
    exc: Exception,
    comparison_artifact: AWRReportComparisonArtifact | None = None,
) -> ComparisonExecutionResult:
    error_message = f"{type(exc).__name__}: {exc}"
    if repository is not None:
        try:
            repository.record_workflow_failure(
                transaction_group_id=envelope.transaction_group_id,
                idempotency_key=envelope.idempotency_key,
                actor_id=envelope.actor_id,
                action="screen3_comparison_execution_failed",
                error_message=error_message,
                rollback_reference=envelope.rollback_reference or "comparison-failure",
                workflow_request_id=_workflow_request_id(envelope),
                transaction_scope=_WORKFLOW_SCOPE,
                notes=envelope.notes,
            )
        except Exception:  # noqa: BLE001
            pass
    return validate_comparison_execution_result(
        ComparisonExecutionResult(
            comparison_execution_id=envelope.comparison_execution_id,
            request_id=envelope.reanalysis_request.request_id,
            idempotency_key=envelope.idempotency_key,
            transaction_group_id=envelope.transaction_group_id,
            execution_status="failed_safely",
            comparison_built=False,
            comparison_artifact=None,
            workflow_request_persisted=False,
            workflow_validation_persisted=False,
            workflow_audit_persisted=False,
            output_artifacts_persisted=False,
            idempotent_replay=False,
            run_analysis_called=False,
            subprocess_called=False,
            object_storage_called=False,
            local_file_read_performed=False,
            parser_called=False,
            db_lookup_performed=False,
            dashboard_regenerated=False,
            phase4i_mutated=False,
            adaptive_runtime_used=False,
            phase8_sizing_tco_used=False,
            denied_reasons=[error_message],
            warnings=[
                "comparison execution failed safely; runtime truth was not mutated"
            ],
            required_next_steps=["review failure metadata"],
            notes=envelope.notes,
        )
    )


def _blocked_result(
    envelope: Any,
    reason: str,
) -> ComparisonExecutionResult:
    status = (
        "blocked_insufficient_inputs"
        if "at least two" in reason or "comparison_inputs" in reason
        else "blocked_invalid_request"
    )
    return validate_comparison_execution_result(
        ComparisonExecutionResult(
            comparison_execution_id=getattr(envelope, "comparison_execution_id", "INVALID"),
            request_id=getattr(
                getattr(envelope, "reanalysis_request", None),
                "request_id",
                "INVALID",
            ),
            idempotency_key=getattr(envelope, "idempotency_key", "INVALID"),
            transaction_group_id=getattr(envelope, "transaction_group_id", "INVALID"),
            execution_status=status,
            comparison_built=False,
            comparison_artifact=None,
            workflow_request_persisted=False,
            workflow_validation_persisted=False,
            workflow_audit_persisted=False,
            output_artifacts_persisted=False,
            idempotent_replay=False,
            run_analysis_called=False,
            subprocess_called=False,
            object_storage_called=False,
            local_file_read_performed=False,
            parser_called=False,
            db_lookup_performed=False,
            dashboard_regenerated=False,
            phase4i_mutated=False,
            adaptive_runtime_used=False,
            phase8_sizing_tco_used=False,
            denied_reasons=[reason],
            required_next_steps=["correct comparison execution envelope metadata"],
            notes=getattr(envelope, "notes", None),
        )
    )


def _workflow_request_id(envelope: ComparisonExecutionRequestEnvelope) -> str:
    return create_workflow_request_id(_WORKFLOW_TYPE, envelope.idempotency_key)


def _require_comparison_inputs(
    comparison_inputs: list[dict[str, Any]],
    *,
    require_two: bool,
) -> None:
    if not isinstance(comparison_inputs, list):
        raise Screen3ComparisonExecutionError("comparison_inputs must be a list.")
    if require_two and len(comparison_inputs) < 2:
        raise Screen3ComparisonExecutionError(
            "at least two supplied in-memory comparison inputs are required."
        )
    for index, item in enumerate(comparison_inputs):
        if not isinstance(item, dict):
            raise Screen3ComparisonExecutionError(
                f"comparison_inputs[{index}] must be a dict."
            )


def _validate_comparison_input_readiness(
    comparison_inputs: list[dict[str, Any]],
) -> None:
    for item in comparison_inputs:
        status = _comparison_input_readiness_status(item)
        if status == "staged_needs_load":
            raise Screen3ComparisonExecutionError(_STAGED_INPUT_DENIED_REASON)
        if status == "needs_reanalysis":
            raise Screen3ComparisonExecutionError(
                "Selected AWR needs deterministic re-analysis before comparison."
            )
        if status == "missing_structured_payload":
            raise Screen3ComparisonExecutionError(
                _MISSING_STRUCTURED_PAYLOAD_DENIED_REASON
            )
        if status == "invalid":
            raise Screen3ComparisonExecutionError(
                "Selected AWR comparison input readiness is invalid."
            )


def _comparison_ready_payloads(
    comparison_inputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [_structured_comparison_payload(item) for item in comparison_inputs]


def _comparison_input_readiness_status(item: dict[str, Any]) -> str:
    declared = _declared_readiness_status(item)
    if declared in ("staged_needs_load", "needs_reanalysis", "invalid"):
        return declared
    if _has_staged_or_raw_only_marker(item):
        return "staged_needs_load"
    payload = _structured_comparison_payload(item)
    if not _has_structured_comparison_payload(payload):
        return "missing_structured_payload"
    if declared in ("comparison_ready", "already_loaded"):
        return declared
    if declared == "missing_structured_payload":
        return declared
    return "comparison_ready"


def _declared_readiness_status(item: dict[str, Any]) -> str | None:
    for field_name in (
        "comparison_input_status",
        "comparison_readiness_status",
        "input_readiness_status",
        "readiness_status",
    ):
        value = item.get(field_name)
        if value is None:
            continue
        if not isinstance(value, str):
            return "invalid"
        status = value.strip().lower()
        if status not in COMPARISON_INPUT_READINESS_STATUSES:
            return "invalid"
        return status
    return None


def _structured_comparison_payload(item: dict[str, Any]) -> dict[str, Any]:
    for field_name in (
        "structured_payload",
        "comparison_ready_payload",
        "comparison_payload",
    ):
        payload = item.get(field_name)
        if payload is None:
            continue
        if not isinstance(payload, dict):
            raise Screen3ComparisonExecutionError(
                _MISSING_STRUCTURED_PAYLOAD_DENIED_REASON
            )
        return payload
    return item


def _has_structured_comparison_payload(payload: dict[str, Any]) -> bool:
    for field_name in _STRUCTURED_COMPARISON_SECTION_NAMES:
        value = payload.get(field_name)
        if isinstance(value, dict) and value:
            return True
        if isinstance(value, list) and value:
            return True
        if value is not None and not isinstance(value, (dict, list)):
            return True
    return False


def _has_staged_or_raw_only_marker(item: dict[str, Any]) -> bool:
    for field_name in ("staged_only", "raw_file_only", "file_only"):
        if item.get(field_name) is True:
            return True
    for field_name in ("source_mode", "source_state", "load_status"):
        value = item.get(field_name)
        if isinstance(value, str) and value.strip().lower() in (
            "local_file",
            "local_staged",
            "raw_file_only",
            "staged",
            "staged_only",
            "staged_needs_load",
        ):
            return True
    if any(
        item.get(field_name)
        for field_name in (
            "staged_file_reference",
            "staged_source_reference",
            "raw_file_reference",
            "raw_source_reference",
            "local_file_reference",
        )
    ):
        return not _has_structured_comparison_payload(
            _structured_comparison_payload(item)
        )
    return False


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Screen3ComparisonExecutionError(f"{field_name} is required.")
    return value


def _require_optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise Screen3ComparisonExecutionError(f"{field_name} must be a string.")
    return value


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise Screen3ComparisonExecutionError(f"{field_name} must be a dict.")
    return value


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise Screen3ComparisonExecutionError(f"{field_name} must be a boolean.")
    return value


def _require_supported(value: Any, allowed: tuple[str, ...], field_name: str) -> str:
    value = _require_text(value, field_name)
    if value not in allowed:
        raise Screen3ComparisonExecutionError(
            f"{field_name} must be one of: {', '.join(allowed)}."
        )
    return value


def _require_string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise Screen3ComparisonExecutionError(f"{field_name} must be a list of strings.")
    return value


def _reject_true(value: bool, field_name: str) -> None:
    if value:
        raise Screen3ComparisonExecutionError(
            f"{field_name} must remain false in Phase 7CC."
        )


def _stable_id(prefix: str, *parts: str) -> str:
    encoded = json.dumps([prefix, *parts], sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:24].upper()
    token = _TOKEN_PATTERN.sub("-", prefix).strip("-").upper()
    return f"{token}:{digest}"
