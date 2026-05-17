"""Phase 7CE dashboard output refresh and artifact reference handling.

This module records controlled dashboard refresh metadata for active Screen 3
execution outputs. It uses an injected renderer only; it does not import
dashboard rendering code, call run_analysis.py, invoke parser/scoring/
recommendation modules, call Object Storage, overwrite dashboard files, mutate
Phase 4I, or implement Phase 8 behavior.
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


DASHBOARD_REFRESH_MODES = (
    "metadata_only",
    "link_existing_dashboard",
    "regenerate_with_renderer",
    "validation_response_only",
    "error_artifact_only",
)

DASHBOARD_REFRESH_STATUSES = (
    "dry_run_only",
    "blocked_no_renderer",
    "blocked_missing_phase4i_reference",
    "metadata_persisted",
    "linked_existing_dashboard",
    "regenerated_with_injected_renderer",
    "validation_response_persisted",
    "error_artifact_persisted",
    "idempotent_replay",
    "failed_safely",
)

DASHBOARD_REFRESH_VALIDATION_STATUSES = (
    "dry_run_only",
    "blocked_no_renderer",
    "blocked_missing_phase4i_reference",
    "can_refresh_metadata",
    "can_link_existing_dashboard",
    "can_regenerate_with_renderer",
    "validation_response_only",
    "error_artifact_only",
)

_WORKFLOW_TYPE = "screen3_dashboard_output_refresh"
_WORKFLOW_SCOPE = "screen3_dashboard_output_refresh"
_REQUESTED_ACTION = "dashboard_output_refresh"
_TOKEN_PATTERN = re.compile(r"[^A-Za-z0-9]+")
_SAFETY_FIELDS = (
    "phase4i_mutated",
    "run_analysis_called",
    "parser_invoked",
    "scoring_invoked",
    "recommendation_invoked",
    "object_storage_called",
)


class DashboardOutputRefreshError(ValueError):
    """Raised when Phase 7CE refresh metadata is unsafe."""


@dataclass(frozen=True)
class DashboardRefreshRequestEnvelope:
    """Governed request envelope for dashboard output refresh metadata."""

    refresh_execution_id: str
    source_execution_id: str
    source_execution_type: str
    workflow_request_id: str | None
    idempotency_key: str
    transaction_group_id: str
    actor_id: str
    actor_audit_context: dict[str, Any]
    phase4i_reference: str | None = None
    dashboard_reference: str | None = None
    comparison_reference: str | None = None
    object_storage_reference: str | None = None
    refresh_mode: str = "metadata_only"
    renderer_requested: bool = False
    dry_run: bool = False
    validation_reference: str | None = None
    rollback_reference: str | None = None
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.refresh_execution_id, "refresh_execution_id")
        _require_text(self.source_execution_id, "source_execution_id")
        _require_text(self.source_execution_type, "source_execution_type")
        _require_optional_text(self.workflow_request_id, "workflow_request_id")
        _require_text(self.idempotency_key, "idempotency_key")
        _require_text(self.transaction_group_id, "transaction_group_id")
        _require_text(self.actor_id, "actor_id")
        _require_mapping(self.actor_audit_context, "actor_audit_context")
        _require_optional_text(self.phase4i_reference, "phase4i_reference")
        _require_optional_text(self.dashboard_reference, "dashboard_reference")
        _require_optional_text(self.comparison_reference, "comparison_reference")
        _require_optional_text(self.object_storage_reference, "object_storage_reference")
        _require_supported(self.refresh_mode, DASHBOARD_REFRESH_MODES, "refresh_mode")
        _require_bool(self.renderer_requested, "renderer_requested")
        _require_bool(self.dry_run, "dry_run")
        _require_optional_text(self.validation_reference, "validation_reference")
        _require_optional_text(self.rollback_reference, "rollback_reference")
        _require_optional_text(self.created_at, "created_at")
        _require_optional_text(self.notes, "notes")
        if self.actor_audit_context.get("actor_id") != self.actor_id:
            raise DashboardOutputRefreshError(
                "actor_audit_context.actor_id must match actor_id."
            )


@dataclass(frozen=True)
class DashboardRefreshValidation:
    """Validation metadata for one dashboard refresh request."""

    refresh_validation_id: str
    refresh_execution_id: str
    valid: bool
    validation_status: str
    source_execution_present: bool
    phase4i_reference_present: bool
    renderer_present: bool
    can_refresh: bool
    refresh_blocked: bool
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    dashboard_regeneration_performed: bool = False
    output_written: bool = False
    phase4i_mutated: bool = False
    run_analysis_called: bool = False
    parser_invoked: bool = False
    scoring_invoked: bool = False
    recommendation_invoked: bool = False
    object_storage_called: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.refresh_validation_id, "refresh_validation_id")
        _require_text(self.refresh_execution_id, "refresh_execution_id")
        _require_bool(self.valid, "valid")
        _require_supported(
            self.validation_status,
            DASHBOARD_REFRESH_VALIDATION_STATUSES,
            "validation_status",
        )
        for field_name in (
            "source_execution_present",
            "phase4i_reference_present",
            "renderer_present",
            "can_refresh",
            "refresh_blocked",
            "dashboard_regeneration_performed",
            "output_written",
            "phase4i_mutated",
            "run_analysis_called",
            "parser_invoked",
            "scoring_invoked",
            "recommendation_invoked",
            "object_storage_called",
        ):
            _require_bool(getattr(self, field_name), field_name)
        _require_string_list(self.denied_reasons, "denied_reasons")
        _require_string_list(self.warnings, "warnings")
        _require_string_list(self.required_next_steps, "required_next_steps")
        _require_optional_text(self.notes, "notes")
        for field_name in _SAFETY_FIELDS:
            _reject_true(getattr(self, field_name), field_name)
        if self.valid and self.refresh_blocked:
            raise DashboardOutputRefreshError(
                "valid refresh validation cannot also be refresh_blocked."
            )
        if self.can_refresh and self.refresh_blocked:
            raise DashboardOutputRefreshError(
                "can_refresh cannot be true when refresh_blocked is true."
            )


@dataclass(frozen=True)
class RegeneratedDashboardArtifactReference:
    """Metadata reference for a dashboard artifact."""

    dashboard_artifact_id: str
    refresh_execution_id: str
    artifact_type: str
    artifact_reference: str
    artifact_summary: str
    output_path: str | None = None
    renderer_name: str | None = None
    renderer_version: str | None = None
    dashboard_generated: bool = False
    output_written: bool = False
    overwrite_performed: bool = False
    generated_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.dashboard_artifact_id, "dashboard_artifact_id")
        _require_text(self.refresh_execution_id, "refresh_execution_id")
        _require_supported(
            self.artifact_type,
            ("dashboard_artifact_reference", "validation_response", "error_artifact"),
            "artifact_type",
        )
        _require_text(self.artifact_reference, "artifact_reference")
        _require_text(self.artifact_summary, "artifact_summary")
        _require_optional_text(self.output_path, "output_path")
        _require_optional_text(self.renderer_name, "renderer_name")
        _require_optional_text(self.renderer_version, "renderer_version")
        _require_bool(self.dashboard_generated, "dashboard_generated")
        _require_bool(self.output_written, "output_written")
        _require_bool(self.overwrite_performed, "overwrite_performed")
        _require_optional_text(self.generated_at, "generated_at")
        _require_optional_text(self.notes, "notes")
        if self.output_written and not self.dashboard_generated:
            raise DashboardOutputRefreshError(
                "output_written requires dashboard_generated=true."
            )


@dataclass(frozen=True)
class Phase4IPayloadReference:
    """Metadata reference for a Phase 4I payload contract."""

    phase4i_reference_id: str
    source_execution_id: str
    payload_reference: str
    payload_summary: str
    payload_version: str | None = None
    phase4i_contract_preserved: bool = True
    phase4i_mutated: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.phase4i_reference_id, "phase4i_reference_id")
        _require_text(self.source_execution_id, "source_execution_id")
        _require_text(self.payload_reference, "payload_reference")
        _require_text(self.payload_summary, "payload_summary")
        _require_optional_text(self.payload_version, "payload_version")
        _require_bool(self.phase4i_contract_preserved, "phase4i_contract_preserved")
        _require_bool(self.phase4i_mutated, "phase4i_mutated")
        _require_optional_text(self.notes, "notes")
        if not self.phase4i_contract_preserved:
            raise DashboardOutputRefreshError(
                "phase4i_contract_preserved must remain true in Phase 7CE."
            )
        _reject_true(self.phase4i_mutated, "phase4i_mutated")


@dataclass(frozen=True)
class DashboardRefreshResult:
    """Result metadata for dashboard output refresh handling."""

    refresh_execution_id: str
    idempotency_key: str
    transaction_group_id: str
    refresh_status: str
    refresh_validation: DashboardRefreshValidation
    phase4i_payload_reference: Phase4IPayloadReference | None = None
    dashboard_artifact_reference: RegeneratedDashboardArtifactReference | None = None
    output_artifacts_persisted: bool = False
    workflow_request_persisted: bool = False
    workflow_validation_persisted: bool = False
    workflow_audit_persisted: bool = False
    idempotent_replay: bool = False
    dashboard_regenerated: bool = False
    output_written: bool = False
    phase4i_mutated: bool = False
    run_analysis_called: bool = False
    parser_invoked: bool = False
    scoring_invoked: bool = False
    recommendation_invoked: bool = False
    object_storage_called: bool = False
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.refresh_execution_id, "refresh_execution_id")
        _require_text(self.idempotency_key, "idempotency_key")
        _require_text(self.transaction_group_id, "transaction_group_id")
        _require_supported(self.refresh_status, DASHBOARD_REFRESH_STATUSES, "refresh_status")
        validate_dashboard_refresh_validation(self.refresh_validation)
        if self.phase4i_payload_reference is not None:
            validate_phase4i_payload_reference(self.phase4i_payload_reference)
        if self.dashboard_artifact_reference is not None:
            validate_dashboard_artifact_reference(self.dashboard_artifact_reference)
        for field_name in (
            "output_artifacts_persisted",
            "workflow_request_persisted",
            "workflow_validation_persisted",
            "workflow_audit_persisted",
            "idempotent_replay",
            "dashboard_regenerated",
            "output_written",
            "phase4i_mutated",
            "run_analysis_called",
            "parser_invoked",
            "scoring_invoked",
            "recommendation_invoked",
            "object_storage_called",
        ):
            _require_bool(getattr(self, field_name), field_name)
        _require_string_list(self.denied_reasons, "denied_reasons")
        _require_string_list(self.warnings, "warnings")
        _require_string_list(self.required_next_steps, "required_next_steps")
        _require_optional_text(self.notes, "notes")
        for field_name in _SAFETY_FIELDS:
            _reject_true(getattr(self, field_name), field_name)
        if self.dashboard_regenerated and self.dashboard_artifact_reference is None:
            raise DashboardOutputRefreshError(
                "dashboard_regenerated requires a dashboard_artifact_reference."
            )
        if self.output_written and not self.dashboard_regenerated:
            raise DashboardOutputRefreshError(
                "output_written requires dashboard_regenerated=true."
            )


def create_dashboard_refresh_execution_id(
    source_execution_id: str,
    idempotency_key: str,
) -> str:
    """Create a deterministic Phase 7CE refresh execution id."""

    _require_text(source_execution_id, "source_execution_id")
    _require_text(idempotency_key, "idempotency_key")
    return _stable_id("DASHBOARD-REFRESH-EXECUTION", source_execution_id, idempotency_key)


def create_dashboard_refresh_validation_id(refresh_execution_id: str) -> str:
    """Create a deterministic refresh validation id."""

    _require_text(refresh_execution_id, "refresh_execution_id")
    return _stable_id("DASHBOARD-REFRESH-VALIDATION", refresh_execution_id)


def create_phase4i_payload_reference_id(
    source_execution_id: str,
    payload_reference: str,
) -> str:
    """Create a deterministic Phase 4I payload reference id."""

    _require_text(source_execution_id, "source_execution_id")
    _require_text(payload_reference, "payload_reference")
    return _stable_id("PHASE4I-PAYLOAD-REFERENCE", source_execution_id, payload_reference)


def create_dashboard_artifact_reference_id(
    refresh_execution_id: str,
    artifact_reference: str,
) -> str:
    """Create a deterministic dashboard artifact reference id."""

    _require_text(refresh_execution_id, "refresh_execution_id")
    _require_text(artifact_reference, "artifact_reference")
    return _stable_id(
        "DASHBOARD-ARTIFACT-REFERENCE",
        refresh_execution_id,
        artifact_reference,
    )


def validate_dashboard_refresh_envelope(
    envelope: DashboardRefreshRequestEnvelope,
) -> DashboardRefreshRequestEnvelope:
    """Validate dashboard refresh envelope shape and actor metadata."""

    if not isinstance(envelope, DashboardRefreshRequestEnvelope):
        raise DashboardOutputRefreshError(
            "envelope must be a DashboardRefreshRequestEnvelope instance."
        )
    envelope.__post_init__()
    if not envelope.rollback_reference:
        raise DashboardOutputRefreshError(
            "rollback_reference is required for Phase 7CE refresh metadata."
        )
    return envelope


def evaluate_dashboard_refresh_request(
    envelope: DashboardRefreshRequestEnvelope,
    renderer: Any | None = None,
) -> DashboardRefreshValidation:
    """Evaluate whether a refresh request can proceed without unsafe actions."""

    envelope = validate_dashboard_refresh_envelope(envelope)
    denied_reasons: list[str] = []
    warnings: list[str] = []
    required_next_steps: list[str] = []

    source_execution_present = bool(envelope.source_execution_id)
    phase4i_reference_present = bool(envelope.phase4i_reference)
    renderer_present = renderer is not None

    if envelope.dry_run:
        validation_status = "dry_run_only"
        can_refresh = False
        refresh_blocked = False
        warnings.append("dry run requested; no dashboard output refresh was performed")
        required_next_steps.append("submit without dry_run to persist refresh metadata")
    elif _mode_requires_phase4i_reference(envelope.refresh_mode) and not phase4i_reference_present:
        validation_status = "blocked_missing_phase4i_reference"
        can_refresh = False
        refresh_blocked = True
        denied_reasons.append("phase4i_reference is required for dashboard refresh")
        required_next_steps.append("provide a Phase 4I payload reference from deterministic execution")
    elif envelope.refresh_mode == "regenerate_with_renderer" and not renderer_present:
        validation_status = "blocked_no_renderer"
        can_refresh = False
        refresh_blocked = True
        denied_reasons.append("injected dashboard renderer is required")
        required_next_steps.append("provide an injected renderer or use metadata_only")
    else:
        validation_status = {
            "metadata_only": "can_refresh_metadata",
            "link_existing_dashboard": "can_link_existing_dashboard",
            "regenerate_with_renderer": "can_regenerate_with_renderer",
            "validation_response_only": "validation_response_only",
            "error_artifact_only": "error_artifact_only",
        }[envelope.refresh_mode]
        can_refresh = True
        refresh_blocked = False
        warnings.append("dashboard refresh is governed metadata only unless renderer is injected")
        required_next_steps.append("review persisted dashboard output references")

    return DashboardRefreshValidation(
        refresh_validation_id=create_dashboard_refresh_validation_id(
            envelope.refresh_execution_id
        ),
        refresh_execution_id=envelope.refresh_execution_id,
        valid=can_refresh and not refresh_blocked,
        validation_status=validation_status,
        source_execution_present=source_execution_present,
        phase4i_reference_present=phase4i_reference_present,
        renderer_present=renderer_present,
        can_refresh=can_refresh,
        refresh_blocked=refresh_blocked,
        denied_reasons=denied_reasons,
        warnings=warnings,
        required_next_steps=required_next_steps,
        dashboard_regeneration_performed=False,
        output_written=False,
        phase4i_mutated=False,
        run_analysis_called=False,
        parser_invoked=False,
        scoring_invoked=False,
        recommendation_invoked=False,
        object_storage_called=False,
        notes=envelope.notes,
    )


def execute_dashboard_output_refresh(
    envelope: DashboardRefreshRequestEnvelope,
    repository: GovernedWorkflowRepository | None = None,
    renderer: Any | None = None,
) -> DashboardRefreshResult:
    """Execute governed dashboard refresh metadata handling."""

    try:
        envelope = validate_dashboard_refresh_envelope(envelope)
    except DashboardOutputRefreshError as exc:
        return _invalid_result(envelope, str(exc))

    if repository is not None and not isinstance(repository, GovernedWorkflowRepository):
        raise DashboardOutputRefreshError(
            "repository must be a GovernedWorkflowRepository instance or None."
        )

    if repository is not None:
        existing = repository.get_by_idempotency_key(envelope.idempotency_key)
        if existing is not None:
            return _idempotent_replay_result(envelope, existing.transaction_group_id)

    validation = evaluate_dashboard_refresh_request(envelope, renderer=renderer)
    if envelope.dry_run:
        return _result_from_metadata(
            envelope,
            validation,
            refresh_status="dry_run_only",
            repository=None,
            phase4i_reference=None,
            dashboard_reference=None,
        )

    phase4i_reference = (
        _build_phase4i_payload_reference(envelope)
        if envelope.phase4i_reference
        else None
    )
    dashboard_reference: RegeneratedDashboardArtifactReference | None = None
    refresh_status = _status_for_mode(envelope.refresh_mode)

    if validation.refresh_blocked:
        refresh_status = validation.validation_status
        return _result_from_metadata(
            envelope,
            validation,
            refresh_status=refresh_status,
            repository=repository,
            phase4i_reference=phase4i_reference,
            dashboard_reference=dashboard_reference,
        )

    if envelope.refresh_mode == "regenerate_with_renderer":
        try:
            renderer_output = _invoke_renderer(renderer, phase4i_reference, envelope)
            dashboard_reference = _dashboard_reference_from_renderer_output(
                envelope,
                renderer_output,
            )
            validation = _validation_with_renderer_output(validation, dashboard_reference)
        except Exception as exc:  # noqa: BLE001
            return _record_safe_failure(envelope, repository, exc)
    elif envelope.refresh_mode == "link_existing_dashboard" and envelope.dashboard_reference:
        dashboard_reference = _build_existing_dashboard_reference(envelope)
    elif envelope.refresh_mode == "metadata_only" and envelope.dashboard_reference:
        dashboard_reference = _build_existing_dashboard_reference(envelope)
    elif envelope.refresh_mode in {
        "validation_response_only",
        "error_artifact_only",
    }:
        dashboard_reference = _build_status_artifact_reference(
            envelope,
            artifact_type=(
                "validation_response"
                if envelope.refresh_mode == "validation_response_only"
                else "error_artifact"
            ),
        )

    return _result_from_metadata(
        envelope,
        validation,
        refresh_status=refresh_status,
        repository=repository,
        phase4i_reference=phase4i_reference,
        dashboard_reference=dashboard_reference,
    )


def validate_dashboard_refresh_validation(
    validation: DashboardRefreshValidation,
) -> DashboardRefreshValidation:
    """Validate refresh validation metadata."""

    if not isinstance(validation, DashboardRefreshValidation):
        raise DashboardOutputRefreshError(
            "validation must be a DashboardRefreshValidation instance."
        )
    validation.__post_init__()
    return validation


def validate_dashboard_artifact_reference(
    ref: RegeneratedDashboardArtifactReference,
) -> RegeneratedDashboardArtifactReference:
    """Validate a dashboard artifact reference."""

    if not isinstance(ref, RegeneratedDashboardArtifactReference):
        raise DashboardOutputRefreshError(
            "ref must be a RegeneratedDashboardArtifactReference instance."
        )
    ref.__post_init__()
    return ref


def validate_phase4i_payload_reference(
    ref: Phase4IPayloadReference,
) -> Phase4IPayloadReference:
    """Validate a Phase 4I payload reference."""

    if not isinstance(ref, Phase4IPayloadReference):
        raise DashboardOutputRefreshError(
            "ref must be a Phase4IPayloadReference instance."
        )
    ref.__post_init__()
    return ref


def validate_dashboard_refresh_result(
    result: DashboardRefreshResult,
) -> DashboardRefreshResult:
    """Validate dashboard refresh result metadata."""

    if not isinstance(result, DashboardRefreshResult):
        raise DashboardOutputRefreshError(
            "result must be a DashboardRefreshResult instance."
        )
    result.__post_init__()
    if result.output_artifacts_persisted and not result.workflow_request_persisted:
        raise DashboardOutputRefreshError(
            "persisted output artifacts require a persisted workflow request."
        )
    return result


def dashboard_refresh_envelope_to_dict(
    envelope: DashboardRefreshRequestEnvelope,
) -> dict[str, Any]:
    """Serialize a dashboard refresh envelope."""

    envelope = validate_dashboard_refresh_envelope(envelope)
    return {
        "refresh_execution_id": envelope.refresh_execution_id,
        "source_execution_id": envelope.source_execution_id,
        "source_execution_type": envelope.source_execution_type,
        "workflow_request_id": envelope.workflow_request_id,
        "idempotency_key": envelope.idempotency_key,
        "transaction_group_id": envelope.transaction_group_id,
        "actor_id": envelope.actor_id,
        "actor_audit_context": dict(envelope.actor_audit_context),
        "phase4i_reference": envelope.phase4i_reference,
        "dashboard_reference": envelope.dashboard_reference,
        "comparison_reference": envelope.comparison_reference,
        "object_storage_reference": envelope.object_storage_reference,
        "refresh_mode": envelope.refresh_mode,
        "renderer_requested": envelope.renderer_requested,
        "dry_run": envelope.dry_run,
        "validation_reference": envelope.validation_reference,
        "rollback_reference": envelope.rollback_reference,
        "created_at": envelope.created_at,
        "notes": envelope.notes,
    }


def dashboard_refresh_envelope_from_dict(
    data: dict[str, Any],
) -> DashboardRefreshRequestEnvelope:
    """Deserialize a dashboard refresh envelope."""

    _require_mapping(data, "dashboard_refresh_envelope")
    return DashboardRefreshRequestEnvelope(
        refresh_execution_id=data.get("refresh_execution_id"),
        source_execution_id=data.get("source_execution_id"),
        source_execution_type=data.get("source_execution_type"),
        workflow_request_id=data.get("workflow_request_id"),
        idempotency_key=data.get("idempotency_key"),
        transaction_group_id=data.get("transaction_group_id"),
        actor_id=data.get("actor_id"),
        actor_audit_context=data.get("actor_audit_context"),
        phase4i_reference=data.get("phase4i_reference"),
        dashboard_reference=data.get("dashboard_reference"),
        comparison_reference=data.get("comparison_reference"),
        object_storage_reference=data.get("object_storage_reference"),
        refresh_mode=data.get("refresh_mode", "metadata_only"),
        renderer_requested=data.get("renderer_requested", False),
        dry_run=data.get("dry_run", False),
        validation_reference=data.get("validation_reference"),
        rollback_reference=data.get("rollback_reference"),
        created_at=data.get("created_at"),
        notes=data.get("notes"),
    )


def dashboard_refresh_validation_to_dict(
    validation: DashboardRefreshValidation,
) -> dict[str, Any]:
    """Serialize refresh validation metadata."""

    validation = validate_dashboard_refresh_validation(validation)
    return {
        "refresh_validation_id": validation.refresh_validation_id,
        "refresh_execution_id": validation.refresh_execution_id,
        "valid": validation.valid,
        "validation_status": validation.validation_status,
        "source_execution_present": validation.source_execution_present,
        "phase4i_reference_present": validation.phase4i_reference_present,
        "renderer_present": validation.renderer_present,
        "can_refresh": validation.can_refresh,
        "refresh_blocked": validation.refresh_blocked,
        "denied_reasons": list(validation.denied_reasons),
        "warnings": list(validation.warnings),
        "required_next_steps": list(validation.required_next_steps),
        "dashboard_regeneration_performed": validation.dashboard_regeneration_performed,
        "output_written": validation.output_written,
        "phase4i_mutated": validation.phase4i_mutated,
        "run_analysis_called": validation.run_analysis_called,
        "parser_invoked": validation.parser_invoked,
        "scoring_invoked": validation.scoring_invoked,
        "recommendation_invoked": validation.recommendation_invoked,
        "object_storage_called": validation.object_storage_called,
        "notes": validation.notes,
    }


def dashboard_refresh_validation_from_dict(
    data: dict[str, Any],
) -> DashboardRefreshValidation:
    """Deserialize refresh validation metadata."""

    _require_mapping(data, "dashboard_refresh_validation")
    return DashboardRefreshValidation(
        refresh_validation_id=data.get("refresh_validation_id"),
        refresh_execution_id=data.get("refresh_execution_id"),
        valid=data.get("valid"),
        validation_status=data.get("validation_status"),
        source_execution_present=data.get("source_execution_present"),
        phase4i_reference_present=data.get("phase4i_reference_present"),
        renderer_present=data.get("renderer_present"),
        can_refresh=data.get("can_refresh"),
        refresh_blocked=data.get("refresh_blocked"),
        denied_reasons=list(data.get("denied_reasons", [])),
        warnings=list(data.get("warnings", [])),
        required_next_steps=list(data.get("required_next_steps", [])),
        dashboard_regeneration_performed=data.get(
            "dashboard_regeneration_performed",
            False,
        ),
        output_written=data.get("output_written", False),
        phase4i_mutated=data.get("phase4i_mutated", False),
        run_analysis_called=data.get("run_analysis_called", False),
        parser_invoked=data.get("parser_invoked", False),
        scoring_invoked=data.get("scoring_invoked", False),
        recommendation_invoked=data.get("recommendation_invoked", False),
        object_storage_called=data.get("object_storage_called", False),
        notes=data.get("notes"),
    )


def dashboard_artifact_reference_to_dict(
    ref: RegeneratedDashboardArtifactReference,
) -> dict[str, Any]:
    """Serialize dashboard artifact reference metadata."""

    ref = validate_dashboard_artifact_reference(ref)
    return {
        "dashboard_artifact_id": ref.dashboard_artifact_id,
        "refresh_execution_id": ref.refresh_execution_id,
        "artifact_type": ref.artifact_type,
        "artifact_reference": ref.artifact_reference,
        "artifact_summary": ref.artifact_summary,
        "output_path": ref.output_path,
        "renderer_name": ref.renderer_name,
        "renderer_version": ref.renderer_version,
        "dashboard_generated": ref.dashboard_generated,
        "output_written": ref.output_written,
        "overwrite_performed": ref.overwrite_performed,
        "generated_at": ref.generated_at,
        "notes": ref.notes,
    }


def dashboard_artifact_reference_from_dict(
    data: dict[str, Any],
) -> RegeneratedDashboardArtifactReference:
    """Deserialize dashboard artifact reference metadata."""

    _require_mapping(data, "dashboard_artifact_reference")
    return RegeneratedDashboardArtifactReference(
        dashboard_artifact_id=data.get("dashboard_artifact_id"),
        refresh_execution_id=data.get("refresh_execution_id"),
        artifact_type=data.get("artifact_type"),
        artifact_reference=data.get("artifact_reference"),
        artifact_summary=data.get("artifact_summary"),
        output_path=data.get("output_path"),
        renderer_name=data.get("renderer_name"),
        renderer_version=data.get("renderer_version"),
        dashboard_generated=data.get("dashboard_generated", False),
        output_written=data.get("output_written", False),
        overwrite_performed=data.get("overwrite_performed", False),
        generated_at=data.get("generated_at"),
        notes=data.get("notes"),
    )


def phase4i_payload_reference_to_dict(ref: Phase4IPayloadReference) -> dict[str, Any]:
    """Serialize Phase 4I payload reference metadata."""

    ref = validate_phase4i_payload_reference(ref)
    return {
        "phase4i_reference_id": ref.phase4i_reference_id,
        "source_execution_id": ref.source_execution_id,
        "payload_reference": ref.payload_reference,
        "payload_summary": ref.payload_summary,
        "payload_version": ref.payload_version,
        "phase4i_contract_preserved": ref.phase4i_contract_preserved,
        "phase4i_mutated": ref.phase4i_mutated,
        "notes": ref.notes,
    }


def phase4i_payload_reference_from_dict(data: dict[str, Any]) -> Phase4IPayloadReference:
    """Deserialize Phase 4I payload reference metadata."""

    _require_mapping(data, "phase4i_payload_reference")
    return Phase4IPayloadReference(
        phase4i_reference_id=data.get("phase4i_reference_id"),
        source_execution_id=data.get("source_execution_id"),
        payload_reference=data.get("payload_reference"),
        payload_summary=data.get("payload_summary"),
        payload_version=data.get("payload_version"),
        phase4i_contract_preserved=data.get("phase4i_contract_preserved", True),
        phase4i_mutated=data.get("phase4i_mutated", False),
        notes=data.get("notes"),
    )


def dashboard_refresh_result_to_dict(result: DashboardRefreshResult) -> dict[str, Any]:
    """Serialize dashboard refresh result metadata."""

    result = validate_dashboard_refresh_result(result)
    return {
        "refresh_execution_id": result.refresh_execution_id,
        "idempotency_key": result.idempotency_key,
        "transaction_group_id": result.transaction_group_id,
        "refresh_status": result.refresh_status,
        "refresh_validation": dashboard_refresh_validation_to_dict(
            result.refresh_validation
        ),
        "phase4i_payload_reference": (
            phase4i_payload_reference_to_dict(result.phase4i_payload_reference)
            if result.phase4i_payload_reference
            else None
        ),
        "dashboard_artifact_reference": (
            dashboard_artifact_reference_to_dict(result.dashboard_artifact_reference)
            if result.dashboard_artifact_reference
            else None
        ),
        "output_artifacts_persisted": result.output_artifacts_persisted,
        "workflow_request_persisted": result.workflow_request_persisted,
        "workflow_validation_persisted": result.workflow_validation_persisted,
        "workflow_audit_persisted": result.workflow_audit_persisted,
        "idempotent_replay": result.idempotent_replay,
        "dashboard_regenerated": result.dashboard_regenerated,
        "output_written": result.output_written,
        "phase4i_mutated": result.phase4i_mutated,
        "run_analysis_called": result.run_analysis_called,
        "parser_invoked": result.parser_invoked,
        "scoring_invoked": result.scoring_invoked,
        "recommendation_invoked": result.recommendation_invoked,
        "object_storage_called": result.object_storage_called,
        "denied_reasons": list(result.denied_reasons),
        "warnings": list(result.warnings),
        "required_next_steps": list(result.required_next_steps),
        "notes": result.notes,
    }


def dashboard_refresh_result_from_dict(data: dict[str, Any]) -> DashboardRefreshResult:
    """Deserialize dashboard refresh result metadata."""

    _require_mapping(data, "dashboard_refresh_result")
    phase4i_data = data.get("phase4i_payload_reference")
    dashboard_data = data.get("dashboard_artifact_reference")
    return DashboardRefreshResult(
        refresh_execution_id=data.get("refresh_execution_id"),
        idempotency_key=data.get("idempotency_key"),
        transaction_group_id=data.get("transaction_group_id"),
        refresh_status=data.get("refresh_status"),
        refresh_validation=dashboard_refresh_validation_from_dict(
            data.get("refresh_validation")
        ),
        phase4i_payload_reference=(
            phase4i_payload_reference_from_dict(phase4i_data)
            if phase4i_data
            else None
        ),
        dashboard_artifact_reference=(
            dashboard_artifact_reference_from_dict(dashboard_data)
            if dashboard_data
            else None
        ),
        output_artifacts_persisted=data.get("output_artifacts_persisted", False),
        workflow_request_persisted=data.get("workflow_request_persisted", False),
        workflow_validation_persisted=data.get("workflow_validation_persisted", False),
        workflow_audit_persisted=data.get("workflow_audit_persisted", False),
        idempotent_replay=data.get("idempotent_replay", False),
        dashboard_regenerated=data.get("dashboard_regenerated", False),
        output_written=data.get("output_written", False),
        phase4i_mutated=data.get("phase4i_mutated", False),
        run_analysis_called=data.get("run_analysis_called", False),
        parser_invoked=data.get("parser_invoked", False),
        scoring_invoked=data.get("scoring_invoked", False),
        recommendation_invoked=data.get("recommendation_invoked", False),
        object_storage_called=data.get("object_storage_called", False),
        denied_reasons=list(data.get("denied_reasons", [])),
        warnings=list(data.get("warnings", [])),
        required_next_steps=list(data.get("required_next_steps", [])),
        notes=data.get("notes"),
    )


def _result_from_metadata(
    envelope: DashboardRefreshRequestEnvelope,
    validation: DashboardRefreshValidation,
    *,
    refresh_status: str,
    repository: GovernedWorkflowRepository | None,
    phase4i_reference: Phase4IPayloadReference | None,
    dashboard_reference: RegeneratedDashboardArtifactReference | None,
) -> DashboardRefreshResult:
    if repository is None:
        return _build_result(
            envelope,
            validation,
            refresh_status=refresh_status,
            phase4i_reference=phase4i_reference,
            dashboard_reference=dashboard_reference,
            workflow_request_persisted=False,
            workflow_validation_persisted=False,
            workflow_audit_persisted=False,
            output_artifacts_persisted=False,
            idempotent_replay=False,
        )

    try:
        persistence_result = repository.persist_workflow_bundle(
            request=_build_workflow_request(envelope, validation, refresh_status),
            transaction=_build_workflow_transaction(envelope),
            validation=_build_workflow_validation(envelope, validation),
            audit=_build_workflow_audit(envelope, refresh_status),
            output_artifacts=_build_output_artifacts(
                envelope,
                validation,
                phase4i_reference,
                dashboard_reference,
                refresh_status,
            ),
        )
    except GovernedWorkflowRepositoryError as exc:
        return _record_safe_failure(envelope, repository, exc)

    if persistence_result.duplicate:
        return _idempotent_replay_result(envelope, persistence_result.transaction_group_id)

    return _build_result(
        envelope,
        validation,
        refresh_status=refresh_status,
        phase4i_reference=phase4i_reference,
        dashboard_reference=dashboard_reference,
        workflow_request_persisted=bool(persistence_result.request),
        workflow_validation_persisted=bool(persistence_result.validation),
        workflow_audit_persisted=bool(persistence_result.audit),
        output_artifacts_persisted=bool(persistence_result.output_artifacts),
        idempotent_replay=False,
    )


def _build_result(
    envelope: DashboardRefreshRequestEnvelope,
    validation: DashboardRefreshValidation,
    *,
    refresh_status: str,
    phase4i_reference: Phase4IPayloadReference | None,
    dashboard_reference: RegeneratedDashboardArtifactReference | None,
    workflow_request_persisted: bool,
    workflow_validation_persisted: bool,
    workflow_audit_persisted: bool,
    output_artifacts_persisted: bool,
    idempotent_replay: bool,
) -> DashboardRefreshResult:
    dashboard_regenerated = bool(
        dashboard_reference and dashboard_reference.dashboard_generated
    )
    output_written = bool(dashboard_reference and dashboard_reference.output_written)
    return validate_dashboard_refresh_result(
        DashboardRefreshResult(
            refresh_execution_id=envelope.refresh_execution_id,
            idempotency_key=envelope.idempotency_key,
            transaction_group_id=envelope.transaction_group_id,
            refresh_status=refresh_status,
            refresh_validation=validation,
            phase4i_payload_reference=phase4i_reference,
            dashboard_artifact_reference=dashboard_reference,
            output_artifacts_persisted=output_artifacts_persisted,
            workflow_request_persisted=workflow_request_persisted,
            workflow_validation_persisted=workflow_validation_persisted,
            workflow_audit_persisted=workflow_audit_persisted,
            idempotent_replay=idempotent_replay,
            dashboard_regenerated=dashboard_regenerated,
            output_written=output_written,
            phase4i_mutated=False,
            run_analysis_called=False,
            parser_invoked=False,
            scoring_invoked=False,
            recommendation_invoked=False,
            object_storage_called=False,
            denied_reasons=list(validation.denied_reasons),
            warnings=list(validation.warnings),
            required_next_steps=list(validation.required_next_steps),
            notes=envelope.notes,
        )
    )


def _build_phase4i_payload_reference(
    envelope: DashboardRefreshRequestEnvelope,
) -> Phase4IPayloadReference:
    phase4i_reference = _require_text(envelope.phase4i_reference, "phase4i_reference")
    return Phase4IPayloadReference(
        phase4i_reference_id=create_phase4i_payload_reference_id(
            envelope.source_execution_id,
            phase4i_reference,
        ),
        source_execution_id=envelope.source_execution_id,
        payload_reference=phase4i_reference,
        payload_summary=(
            "Phase 4I payload reference preserved for dashboard refresh metadata."
        ),
        payload_version="phase4i",
        phase4i_contract_preserved=True,
        phase4i_mutated=False,
        notes=envelope.notes,
    )


def _build_existing_dashboard_reference(
    envelope: DashboardRefreshRequestEnvelope,
) -> RegeneratedDashboardArtifactReference:
    dashboard_reference = _require_text(
        envelope.dashboard_reference,
        "dashboard_reference",
    )
    return RegeneratedDashboardArtifactReference(
        dashboard_artifact_id=create_dashboard_artifact_reference_id(
            envelope.refresh_execution_id,
            dashboard_reference,
        ),
        refresh_execution_id=envelope.refresh_execution_id,
        artifact_type="dashboard_artifact_reference",
        artifact_reference=dashboard_reference,
        artifact_summary="Existing dashboard artifact reference linked.",
        dashboard_generated=False,
        output_written=False,
        overwrite_performed=False,
        notes=envelope.notes,
    )


def _build_status_artifact_reference(
    envelope: DashboardRefreshRequestEnvelope,
    *,
    artifact_type: str,
) -> RegeneratedDashboardArtifactReference:
    reference = f"{artifact_type}:{envelope.refresh_execution_id}"
    return RegeneratedDashboardArtifactReference(
        dashboard_artifact_id=create_dashboard_artifact_reference_id(
            envelope.refresh_execution_id,
            reference,
        ),
        refresh_execution_id=envelope.refresh_execution_id,
        artifact_type=artifact_type,
        artifact_reference=reference,
        artifact_summary=f"{artifact_type} refresh metadata reference.",
        dashboard_generated=False,
        output_written=False,
        overwrite_performed=False,
        notes=envelope.notes,
    )


def _invoke_renderer(
    renderer: Any,
    phase4i_reference: Phase4IPayloadReference | None,
    envelope: DashboardRefreshRequestEnvelope,
) -> dict[str, Any]:
    if renderer is None:
        raise DashboardOutputRefreshError("renderer is required.")
    if phase4i_reference is None:
        raise DashboardOutputRefreshError("phase4i_reference is required.")
    if hasattr(renderer, "validate_render_input"):
        validation_output = renderer.validate_render_input(phase4i_reference)
        _normalize_renderer_output(validation_output or {})
    if not hasattr(renderer, "render_dashboard"):
        raise DashboardOutputRefreshError(
            "renderer must expose render_dashboard(payload_reference, output_reference)."
        )
    output_reference = {
        "refresh_execution_id": envelope.refresh_execution_id,
        "dashboard_reference": envelope.dashboard_reference,
    }
    return _normalize_renderer_output(
        renderer.render_dashboard(phase4i_reference, output_reference)
    )


def _normalize_renderer_output(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise DashboardOutputRefreshError("dashboard renderer must return a dictionary.")
    for field_name in _SAFETY_FIELDS:
        if value.get(field_name) is True:
            raise DashboardOutputRefreshError(
                f"dashboard renderer may not report {field_name}=true."
            )
    if value.get("subprocess_called") is True:
        raise DashboardOutputRefreshError(
            "dashboard renderer may not report subprocess_called=true."
        )
    return dict(value)


def _dashboard_reference_from_renderer_output(
    envelope: DashboardRefreshRequestEnvelope,
    renderer_output: dict[str, Any],
) -> RegeneratedDashboardArtifactReference:
    artifact_reference = str(
        renderer_output.get("artifact_reference")
        or renderer_output.get("dashboard_reference")
        or envelope.dashboard_reference
        or f"dashboard-refresh:{envelope.refresh_execution_id}"
    )
    return RegeneratedDashboardArtifactReference(
        dashboard_artifact_id=create_dashboard_artifact_reference_id(
            envelope.refresh_execution_id,
            artifact_reference,
        ),
        refresh_execution_id=envelope.refresh_execution_id,
        artifact_type="dashboard_artifact_reference",
        artifact_reference=artifact_reference,
        artifact_summary=str(
            renderer_output.get("artifact_summary")
            or "Dashboard artifact generated by injected renderer."
        ),
        output_path=_optional_string_value(renderer_output.get("output_path")),
        renderer_name=_optional_string_value(renderer_output.get("renderer_name")),
        renderer_version=_optional_string_value(renderer_output.get("renderer_version")),
        dashboard_generated=bool(renderer_output.get("dashboard_generated", True)),
        output_written=bool(renderer_output.get("output_written", False)),
        overwrite_performed=bool(renderer_output.get("overwrite_performed", False)),
        generated_at=_optional_string_value(renderer_output.get("generated_at")),
        notes=envelope.notes,
    )


def _validation_with_renderer_output(
    validation: DashboardRefreshValidation,
    dashboard_reference: RegeneratedDashboardArtifactReference,
) -> DashboardRefreshValidation:
    return DashboardRefreshValidation(
        refresh_validation_id=validation.refresh_validation_id,
        refresh_execution_id=validation.refresh_execution_id,
        valid=validation.valid,
        validation_status=validation.validation_status,
        source_execution_present=validation.source_execution_present,
        phase4i_reference_present=validation.phase4i_reference_present,
        renderer_present=validation.renderer_present,
        can_refresh=validation.can_refresh,
        refresh_blocked=validation.refresh_blocked,
        denied_reasons=list(validation.denied_reasons),
        warnings=list(validation.warnings),
        required_next_steps=list(validation.required_next_steps),
        dashboard_regeneration_performed=dashboard_reference.dashboard_generated,
        output_written=dashboard_reference.output_written,
        phase4i_mutated=False,
        run_analysis_called=False,
        parser_invoked=False,
        scoring_invoked=False,
        recommendation_invoked=False,
        object_storage_called=False,
        notes=validation.notes,
    )


def _build_workflow_request(
    envelope: DashboardRefreshRequestEnvelope,
    validation: DashboardRefreshValidation,
    refresh_status: str,
) -> PersistedWorkflowRequest:
    payload = {
        "refresh_execution_id": envelope.refresh_execution_id,
        "source_execution_id": envelope.source_execution_id,
        "source_execution_type": envelope.source_execution_type,
        "workflow_request_id": envelope.workflow_request_id,
        "phase4i_reference": envelope.phase4i_reference,
        "dashboard_reference": envelope.dashboard_reference,
        "comparison_reference": envelope.comparison_reference,
        "object_storage_reference": envelope.object_storage_reference,
        "refresh_mode": envelope.refresh_mode,
        "refresh_status": refresh_status,
        "refresh_validation": dashboard_refresh_validation_to_dict(validation),
        "renderer_requested": envelope.renderer_requested,
        "dashboard_regenerated": validation.dashboard_regeneration_performed,
        "output_written": validation.output_written,
        "phase4i_mutated": False,
        "run_analysis_called": False,
        "parser_invoked": False,
        "scoring_invoked": False,
        "recommendation_invoked": False,
        "object_storage_called": False,
    }
    return PersistedWorkflowRequest(
        workflow_request_id=_workflow_request_id(envelope),
        transaction_group_id=envelope.transaction_group_id,
        idempotency_key=envelope.idempotency_key,
        source_screen="screen_3",
        workflow_type=_WORKFLOW_TYPE,
        requested_action=_REQUESTED_ACTION,
        target_type="dashboard_output_refresh",
        target_id=envelope.source_execution_id,
        actor_id=envelope.actor_id,
        payload=payload,
        status="VALIDATED" if validation.valid else "FAILED",
        notes=envelope.notes,
    )


def _build_workflow_transaction(
    envelope: DashboardRefreshRequestEnvelope,
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
    envelope: DashboardRefreshRequestEnvelope,
    validation: DashboardRefreshValidation,
) -> PersistedWorkflowValidation:
    return PersistedWorkflowValidation(
        workflow_validation_id=create_workflow_validation_id(_workflow_request_id(envelope)),
        workflow_request_id=_workflow_request_id(envelope),
        validation_status=validation.validation_status,
        valid_flag=validation.valid,
        denied_reasons=list(validation.denied_reasons),
        warnings=list(validation.warnings),
        required_next_steps=list(validation.required_next_steps),
        notes=envelope.notes,
    )


def _build_workflow_audit(
    envelope: DashboardRefreshRequestEnvelope,
    refresh_status: str,
) -> PersistedWorkflowAudit:
    payload = {
        "refresh_execution_id": envelope.refresh_execution_id,
        "source_execution_id": envelope.source_execution_id,
        "refresh_status": refresh_status,
        "refresh_mode": envelope.refresh_mode,
        "actor_id": envelope.actor_id,
        "dashboard_regeneration_by_injected_renderer_only": True,
        "runtime_truth_mutated": False,
    }
    return PersistedWorkflowAudit(
        workflow_audit_id=create_workflow_audit_id(
            _workflow_request_id(envelope),
            "screen3_dashboard_output_refresh_recorded",
        ),
        workflow_request_id=_workflow_request_id(envelope),
        transaction_group_id=envelope.transaction_group_id,
        actor_id=envelope.actor_id,
        action="screen3_dashboard_output_refresh_recorded",
        audit_summary=(
            "Phase 7CE dashboard refresh metadata recorded; no run_analysis.py, "
            "parser/scoring/recommendation, Object Storage, or Phase 4I mutation occurred."
        ),
        payload_hash=hash_payload(payload),
        notes=envelope.notes,
    )


def _build_output_artifacts(
    envelope: DashboardRefreshRequestEnvelope,
    validation: DashboardRefreshValidation,
    phase4i_reference: Phase4IPayloadReference | None,
    dashboard_reference: RegeneratedDashboardArtifactReference | None,
    refresh_status: str,
) -> tuple[PersistedWorkflowOutputArtifact, ...]:
    request_id = _workflow_request_id(envelope)
    artifacts: list[PersistedWorkflowOutputArtifact] = [
        PersistedWorkflowOutputArtifact(
            workflow_output_id=create_workflow_output_id(
                request_id,
                "validation_response",
                validation.refresh_validation_id,
            ),
            workflow_request_id=request_id,
            artifact_type="validation_response",
            artifact_reference=f"dashboard-refresh-validation:{validation.refresh_validation_id}",
            artifact_summary="Dashboard refresh validation metadata.",
            artifact_metadata=dashboard_refresh_validation_to_dict(validation),
            status="RECORDED" if validation.valid else "FAILED",
            notes=envelope.notes,
        )
    ]
    if phase4i_reference is not None:
        artifacts.append(
            PersistedWorkflowOutputArtifact(
                workflow_output_id=create_workflow_output_id(
                    request_id,
                    "phase4i_payload_reference",
                    phase4i_reference.payload_reference,
                ),
                workflow_request_id=request_id,
                artifact_type="phase4i_payload_reference",
                artifact_reference=phase4i_reference.payload_reference,
                artifact_summary=phase4i_reference.payload_summary,
                artifact_metadata=phase4i_payload_reference_to_dict(phase4i_reference),
                status="RECORDED",
                notes=envelope.notes,
            )
        )
    if dashboard_reference is not None:
        artifacts.append(
            PersistedWorkflowOutputArtifact(
                workflow_output_id=create_workflow_output_id(
                    request_id,
                    dashboard_reference.artifact_type,
                    dashboard_reference.artifact_reference,
                ),
                workflow_request_id=request_id,
                artifact_type=dashboard_reference.artifact_type,
                artifact_reference=dashboard_reference.artifact_reference,
                artifact_summary=dashboard_reference.artifact_summary,
                artifact_metadata=dashboard_artifact_reference_to_dict(dashboard_reference),
                status="RECORDED" if refresh_status != "failed_safely" else "FAILED",
                notes=envelope.notes,
            )
        )
    for artifact_type, reference in (
        ("comparison_artifact", envelope.comparison_reference),
        ("object_storage_load_artifact", envelope.object_storage_reference),
    ):
        if reference:
            artifacts.append(
                PersistedWorkflowOutputArtifact(
                    workflow_output_id=create_workflow_output_id(
                        request_id,
                        artifact_type,
                        reference,
                    ),
                    workflow_request_id=request_id,
                    artifact_type=artifact_type,
                    artifact_reference=reference,
                    artifact_summary=f"{artifact_type} consumed by dashboard refresh.",
                    artifact_metadata={
                        "refresh_execution_id": envelope.refresh_execution_id,
                        "runtime_mutation": False,
                    },
                    status="RECORDED",
                    notes=envelope.notes,
                )
            )
    return tuple(artifacts)


def _record_safe_failure(
    envelope: DashboardRefreshRequestEnvelope,
    repository: GovernedWorkflowRepository | None,
    exc: Exception,
) -> DashboardRefreshResult:
    error_message = f"{type(exc).__name__}: {exc}"
    if repository is not None:
        try:
            repository.record_workflow_failure(
                transaction_group_id=envelope.transaction_group_id,
                idempotency_key=envelope.idempotency_key,
                actor_id=envelope.actor_id,
                action="screen3_dashboard_output_refresh_failed",
                error_message=error_message,
                rollback_reference=(
                    envelope.rollback_reference or "dashboard-refresh-failure"
                ),
                workflow_request_id=_workflow_request_id(envelope),
                transaction_scope=_WORKFLOW_SCOPE,
                notes=envelope.notes,
            )
        except Exception:  # noqa: BLE001
            pass
    validation = DashboardRefreshValidation(
        refresh_validation_id=create_dashboard_refresh_validation_id(
            envelope.refresh_execution_id
        ),
        refresh_execution_id=envelope.refresh_execution_id,
        valid=False,
        validation_status="error_artifact_only",
        source_execution_present=True,
        phase4i_reference_present=bool(envelope.phase4i_reference),
        renderer_present=False,
        can_refresh=False,
        refresh_blocked=True,
        denied_reasons=[error_message],
        required_next_steps=["review error artifact metadata and retry safely"],
        notes=envelope.notes,
    )
    error_reference = _build_status_artifact_reference(
        envelope,
        artifact_type="error_artifact",
    )
    return _build_result(
        envelope,
        validation,
        refresh_status="failed_safely",
        phase4i_reference=None,
        dashboard_reference=error_reference,
        workflow_request_persisted=False,
        workflow_validation_persisted=False,
        workflow_audit_persisted=False,
        output_artifacts_persisted=False,
        idempotent_replay=False,
    )


def _invalid_result(envelope: Any, reason: str) -> DashboardRefreshResult:
    refresh_execution_id = getattr(
        envelope,
        "refresh_execution_id",
        "DASHBOARD-REFRESH-INVALID",
    )
    idempotency_key = getattr(envelope, "idempotency_key", "UNKNOWN-IDEMPOTENCY")
    transaction_group_id = getattr(envelope, "transaction_group_id", "UNKNOWN-TX")
    validation = DashboardRefreshValidation(
        refresh_validation_id=create_dashboard_refresh_validation_id(
            refresh_execution_id
        ),
        refresh_execution_id=refresh_execution_id,
        valid=False,
        validation_status="error_artifact_only",
        source_execution_present=bool(getattr(envelope, "source_execution_id", None)),
        phase4i_reference_present=bool(getattr(envelope, "phase4i_reference", None)),
        renderer_present=False,
        can_refresh=False,
        refresh_blocked=True,
        denied_reasons=[reason],
        required_next_steps=["fix dashboard refresh envelope metadata"],
    )
    return validate_dashboard_refresh_result(
        DashboardRefreshResult(
            refresh_execution_id=refresh_execution_id,
            idempotency_key=idempotency_key,
            transaction_group_id=transaction_group_id,
            refresh_status="failed_safely",
            refresh_validation=validation,
            denied_reasons=[reason],
            required_next_steps=["fix dashboard refresh envelope metadata"],
        )
    )


def _idempotent_replay_result(
    envelope: DashboardRefreshRequestEnvelope,
    transaction_group_id: str,
) -> DashboardRefreshResult:
    validation = DashboardRefreshValidation(
        refresh_validation_id=create_dashboard_refresh_validation_id(
            envelope.refresh_execution_id
        ),
        refresh_execution_id=envelope.refresh_execution_id,
        valid=True,
        validation_status="can_refresh_metadata",
        source_execution_present=True,
        phase4i_reference_present=bool(envelope.phase4i_reference),
        renderer_present=False,
        can_refresh=False,
        refresh_blocked=False,
        warnings=[
            "idempotency key already persisted; renderer was not called"
        ],
        required_next_steps=["return existing governed workflow metadata"],
        notes=envelope.notes,
    )
    return validate_dashboard_refresh_result(
        DashboardRefreshResult(
            refresh_execution_id=envelope.refresh_execution_id,
            idempotency_key=envelope.idempotency_key,
            transaction_group_id=transaction_group_id,
            refresh_status="idempotent_replay",
            refresh_validation=validation,
            output_artifacts_persisted=False,
            workflow_request_persisted=True,
            workflow_validation_persisted=True,
            workflow_audit_persisted=True,
            idempotent_replay=True,
            dashboard_regenerated=False,
            output_written=False,
            phase4i_mutated=False,
            run_analysis_called=False,
            parser_invoked=False,
            scoring_invoked=False,
            recommendation_invoked=False,
            object_storage_called=False,
            warnings=list(validation.warnings),
            required_next_steps=list(validation.required_next_steps),
            notes=envelope.notes,
        )
    )


def _workflow_request_id(envelope: DashboardRefreshRequestEnvelope) -> str:
    return create_workflow_request_id(_WORKFLOW_TYPE, envelope.idempotency_key)


def _status_for_mode(refresh_mode: str) -> str:
    return {
        "metadata_only": "metadata_persisted",
        "link_existing_dashboard": "linked_existing_dashboard",
        "regenerate_with_renderer": "regenerated_with_injected_renderer",
        "validation_response_only": "validation_response_persisted",
        "error_artifact_only": "error_artifact_persisted",
    }[refresh_mode]


def _mode_requires_phase4i_reference(refresh_mode: str) -> bool:
    return refresh_mode in {
        "metadata_only",
        "link_existing_dashboard",
        "regenerate_with_renderer",
    }


def _optional_string_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _stable_id(prefix: str, *parts: str) -> str:
    tokens = [_normalize_token(prefix)]
    tokens.extend(_normalize_token(part) for part in parts if part)
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()
    return "-".join(tokens + [digest[:12].upper()])


def _normalize_token(value: Any) -> str:
    text = str(value or "UNKNOWN").strip().upper()
    text = _TOKEN_PATTERN.sub("-", text).strip("-")
    return text or "UNKNOWN"


def _json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str)


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DashboardOutputRefreshError(f"{field_name} is required.")
    return value.strip()


def _require_optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise DashboardOutputRefreshError(f"{field_name} must be a string.")
    return value


def _require_bool(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise DashboardOutputRefreshError(f"{field_name} must be a boolean.")


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise DashboardOutputRefreshError(f"{field_name} must be a dictionary.")


def _require_supported(value: Any, allowed: tuple[str, ...], field_name: str) -> str:
    _require_text(value, field_name)
    if value not in allowed:
        raise DashboardOutputRefreshError(
            f"{field_name} must be one of: {', '.join(allowed)}."
        )
    return value


def _require_string_list(value: Any, field_name: str) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise DashboardOutputRefreshError(f"{field_name} must be a list of strings.")


def _reject_true(value: bool, field_name: str) -> None:
    if value:
        raise DashboardOutputRefreshError(
            f"{field_name} must remain false in Phase 7CE."
        )
