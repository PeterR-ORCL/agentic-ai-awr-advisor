"""Local Phase 7AH dashboard output lifecycle metadata.

This module defines deterministic records for future dashboard workflow
outputs and refresh instructions. It validates metadata shape only. It does
not create output files, invoke backend actions, modify dashboard state, or
mutate runtime truth.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


OUTPUT_ARTIFACT_TYPES = (
    "validation_response",
    "analysis_run_record",
    "phase4i_payload_reference",
    "dashboard_artifact_reference",
    "comparison_artifact",
    "error_artifact",
    "source_validation_artifact",
    "object_storage_load_artifact",
    "workflow_audit_artifact",
    "governance_review_artifact",
    "outcome_capture_artifact",
)

OUTPUT_REFRESH_MODES = (
    "no_refresh",
    "show_message",
    "link_to_artifact",
    "link_to_run",
    "regenerate_dashboard_requested",
    "future_live_refresh",
)

OUTPUT_LIFECYCLE_STATUSES = (
    "PROPOSED",
    "VALIDATED",
    "AVAILABLE",
    "FAILED",
    "SUPERSEDED",
    "CLOSED",
)


class DashboardOutputLifecycleError(ValueError):
    """Raised when dashboard output lifecycle metadata violates 7AH rules."""


@dataclass(frozen=True)
class DashboardOutputArtifact:
    """Metadata describing an output from a future dashboard workflow."""

    artifact_id: str
    artifact_type: str
    source_request_id: str | None = None
    source_validation_id: str | None = None
    source_audit_id: str | None = None
    run_id: str | None = None
    phase4i_reference: str | None = None
    dashboard_reference: str | None = None
    comparison_reference: str | None = None
    artifact_uri: str | None = None
    artifact_summary: str = ""
    lifecycle_status: str = "PROPOSED"
    validation_status: str | None = None
    error_summary: str | None = None
    created_by: str | None = None
    created_at: str | None = None
    output_written: bool = False
    dashboard_regenerated: bool = False
    phase4i_mutated: bool = False
    runtime_mutation_performed: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.artifact_id, "artifact_id")
        _require_supported(self.artifact_type, OUTPUT_ARTIFACT_TYPES, "artifact_type")
        _require_optional_string(self.source_request_id, "source_request_id")
        _require_optional_string(self.source_validation_id, "source_validation_id")
        _require_optional_string(self.source_audit_id, "source_audit_id")
        _require_optional_string(self.run_id, "run_id")
        _require_optional_string(self.phase4i_reference, "phase4i_reference")
        _require_optional_string(self.dashboard_reference, "dashboard_reference")
        _require_optional_string(self.comparison_reference, "comparison_reference")
        _require_optional_string(self.artifact_uri, "artifact_uri")
        _require_nonempty_string(self.artifact_summary, "artifact_summary")
        _require_supported(
            self.lifecycle_status,
            OUTPUT_LIFECYCLE_STATUSES,
            "lifecycle_status",
        )
        _require_optional_string(self.validation_status, "validation_status")
        _require_optional_string(self.error_summary, "error_summary")
        _require_optional_string(self.created_by, "created_by")
        _require_optional_string(self.created_at, "created_at")
        _require_boolean(self.output_written, "output_written")
        _require_boolean(self.dashboard_regenerated, "dashboard_regenerated")
        _require_boolean(self.phase4i_mutated, "phase4i_mutated")
        _require_boolean(
            self.runtime_mutation_performed,
            "runtime_mutation_performed",
        )
        _require_optional_string(self.notes, "notes")
        if self.output_written:
            raise DashboardOutputLifecycleError(
                "output_written must remain false in Phase 7AH."
            )
        if self.dashboard_regenerated:
            raise DashboardOutputLifecycleError(
                "dashboard_regenerated must remain false in Phase 7AH."
            )
        if self.phase4i_mutated:
            raise DashboardOutputLifecycleError(
                "phase4i_mutated must remain false in Phase 7AH."
            )
        if self.runtime_mutation_performed:
            raise DashboardOutputLifecycleError(
                "runtime_mutation_performed must remain false in Phase 7AH."
            )
        if self.artifact_type == "error_artifact":
            _require_nonempty_string(self.error_summary, "error_summary")
        if self.artifact_type == "phase4i_payload_reference":
            _require_nonempty_string(self.phase4i_reference, "phase4i_reference")
        if self.artifact_type == "dashboard_artifact_reference":
            _require_nonempty_string(self.dashboard_reference, "dashboard_reference")
        if self.artifact_type == "comparison_artifact":
            _require_nonempty_string(self.comparison_reference, "comparison_reference")
        if self.artifact_type == "analysis_run_record":
            _require_nonempty_string(self.run_id, "run_id")


@dataclass(frozen=True)
class DashboardOutputRefreshInstruction:
    """Metadata describing how a future UI may present an output artifact."""

    refresh_id: str
    artifact_id: str
    refresh_mode: str
    message: str
    link_target: str | None = None
    run_id: str | None = None
    dashboard_reference: str | None = None
    safe_to_display: bool = True
    requires_manual_action: bool = True
    refresh_performed: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.refresh_id, "refresh_id")
        _require_nonempty_string(self.artifact_id, "artifact_id")
        _require_supported(self.refresh_mode, OUTPUT_REFRESH_MODES, "refresh_mode")
        _require_nonempty_string(self.message, "message")
        _require_optional_string(self.link_target, "link_target")
        _require_optional_string(self.run_id, "run_id")
        _require_optional_string(self.dashboard_reference, "dashboard_reference")
        _require_boolean(self.safe_to_display, "safe_to_display")
        _require_boolean(self.requires_manual_action, "requires_manual_action")
        _require_boolean(self.refresh_performed, "refresh_performed")
        _require_optional_string(self.notes, "notes")
        if self.refresh_performed:
            raise DashboardOutputLifecycleError(
                "refresh_performed must remain false in Phase 7AH."
            )
        if self.refresh_mode == "link_to_run":
            _require_nonempty_string(self.run_id, "run_id")
        if self.refresh_mode == "link_to_artifact":
            if not self.link_target and not self.artifact_id:
                raise DashboardOutputLifecycleError(
                    "link_to_artifact requires link_target or artifact_id."
                )
        if self.refresh_mode == "future_live_refresh" and not self.requires_manual_action:
            raise DashboardOutputLifecycleError(
                "future_live_refresh requires manual action in Phase 7AH."
            )


def create_output_artifact_id(
    artifact_type: str,
    source_request_id: str | None = None,
    run_id: str | None = None,
) -> str:
    """Create a deterministic output artifact id."""

    _require_supported(artifact_type, OUTPUT_ARTIFACT_TYPES, "artifact_type")
    _require_optional_string(source_request_id, "source_request_id")
    _require_optional_string(run_id, "run_id")
    source = source_request_id or run_id or "NO-SOURCE"
    return f"DASHBOARD-OUTPUT-{_normalize_token(artifact_type)}-{_normalize_token(source)}"


def create_output_refresh_id(artifact_id: str, refresh_mode: str) -> str:
    """Create a deterministic output refresh instruction id."""

    _require_nonempty_string(artifact_id, "artifact_id")
    _require_supported(refresh_mode, OUTPUT_REFRESH_MODES, "refresh_mode")
    return (
        "DASHBOARD-REFRESH-"
        f"{_normalize_token(artifact_id)}-"
        f"{_normalize_token(refresh_mode)}"
    )


def validate_dashboard_output_artifact(
    artifact: DashboardOutputArtifact,
) -> DashboardOutputArtifact:
    """Validate output artifact metadata without creating any output."""

    if not isinstance(artifact, DashboardOutputArtifact):
        raise DashboardOutputLifecycleError(
            "artifact must be a DashboardOutputArtifact instance."
        )
    artifact.__post_init__()
    return artifact


def validate_dashboard_output_refresh_instruction(
    instruction: DashboardOutputRefreshInstruction,
) -> DashboardOutputRefreshInstruction:
    """Validate refresh instruction metadata without performing refresh."""

    if not isinstance(instruction, DashboardOutputRefreshInstruction):
        raise DashboardOutputLifecycleError(
            "instruction must be a DashboardOutputRefreshInstruction instance."
        )
    instruction.__post_init__()
    return instruction


def dashboard_output_artifact_to_dict(
    artifact: DashboardOutputArtifact,
) -> dict[str, Any]:
    """Serialize dashboard output artifact metadata."""

    artifact = validate_dashboard_output_artifact(artifact)
    return {
        "artifact_id": artifact.artifact_id,
        "artifact_type": artifact.artifact_type,
        "source_request_id": artifact.source_request_id,
        "source_validation_id": artifact.source_validation_id,
        "source_audit_id": artifact.source_audit_id,
        "run_id": artifact.run_id,
        "phase4i_reference": artifact.phase4i_reference,
        "dashboard_reference": artifact.dashboard_reference,
        "comparison_reference": artifact.comparison_reference,
        "artifact_uri": artifact.artifact_uri,
        "artifact_summary": artifact.artifact_summary,
        "lifecycle_status": artifact.lifecycle_status,
        "validation_status": artifact.validation_status,
        "error_summary": artifact.error_summary,
        "created_by": artifact.created_by,
        "created_at": artifact.created_at,
        "output_written": artifact.output_written,
        "dashboard_regenerated": artifact.dashboard_regenerated,
        "phase4i_mutated": artifact.phase4i_mutated,
        "runtime_mutation_performed": artifact.runtime_mutation_performed,
        "notes": artifact.notes,
    }


def dashboard_output_artifact_from_dict(data: dict[str, Any]) -> DashboardOutputArtifact:
    """Deserialize dashboard output artifact metadata."""

    _require_mapping(data, "artifact")
    return DashboardOutputArtifact(
        artifact_id=data.get("artifact_id"),
        artifact_type=data.get("artifact_type"),
        source_request_id=data.get("source_request_id"),
        source_validation_id=data.get("source_validation_id"),
        source_audit_id=data.get("source_audit_id"),
        run_id=data.get("run_id"),
        phase4i_reference=data.get("phase4i_reference"),
        dashboard_reference=data.get("dashboard_reference"),
        comparison_reference=data.get("comparison_reference"),
        artifact_uri=data.get("artifact_uri"),
        artifact_summary=data.get("artifact_summary", ""),
        lifecycle_status=data.get("lifecycle_status", "PROPOSED"),
        validation_status=data.get("validation_status"),
        error_summary=data.get("error_summary"),
        created_by=data.get("created_by"),
        created_at=data.get("created_at"),
        output_written=data.get("output_written", False),
        dashboard_regenerated=data.get("dashboard_regenerated", False),
        phase4i_mutated=data.get("phase4i_mutated", False),
        runtime_mutation_performed=data.get("runtime_mutation_performed", False),
        notes=data.get("notes"),
    )


def dashboard_output_refresh_instruction_to_dict(
    instruction: DashboardOutputRefreshInstruction,
) -> dict[str, Any]:
    """Serialize dashboard output refresh instruction metadata."""

    instruction = validate_dashboard_output_refresh_instruction(instruction)
    return {
        "refresh_id": instruction.refresh_id,
        "artifact_id": instruction.artifact_id,
        "refresh_mode": instruction.refresh_mode,
        "message": instruction.message,
        "link_target": instruction.link_target,
        "run_id": instruction.run_id,
        "dashboard_reference": instruction.dashboard_reference,
        "safe_to_display": instruction.safe_to_display,
        "requires_manual_action": instruction.requires_manual_action,
        "refresh_performed": instruction.refresh_performed,
        "notes": instruction.notes,
    }


def dashboard_output_refresh_instruction_from_dict(
    data: dict[str, Any],
) -> DashboardOutputRefreshInstruction:
    """Deserialize dashboard output refresh instruction metadata."""

    _require_mapping(data, "instruction")
    return DashboardOutputRefreshInstruction(
        refresh_id=data.get("refresh_id"),
        artifact_id=data.get("artifact_id"),
        refresh_mode=data.get("refresh_mode"),
        message=data.get("message"),
        link_target=data.get("link_target"),
        run_id=data.get("run_id"),
        dashboard_reference=data.get("dashboard_reference"),
        safe_to_display=data.get("safe_to_display", True),
        requires_manual_action=data.get("requires_manual_action", True),
        refresh_performed=data.get("refresh_performed", False),
        notes=data.get("notes"),
    )


def create_validation_response_artifact(
    source_request_id: str,
    summary: str,
    validation_status: str,
    created_by: str | None = None,
    notes: str | None = None,
) -> DashboardOutputArtifact:
    """Create validation response artifact metadata only."""

    _require_nonempty_string(source_request_id, "source_request_id")
    _require_nonempty_string(summary, "summary")
    _require_nonempty_string(validation_status, "validation_status")
    _require_optional_string(created_by, "created_by")
    _require_optional_string(notes, "notes")
    return DashboardOutputArtifact(
        artifact_id=create_output_artifact_id(
            "validation_response",
            source_request_id=source_request_id,
        ),
        artifact_type="validation_response",
        source_request_id=source_request_id,
        artifact_summary=summary,
        lifecycle_status="VALIDATED",
        validation_status=validation_status,
        created_by=created_by,
        created_at=None,
        output_written=False,
        dashboard_regenerated=False,
        phase4i_mutated=False,
        runtime_mutation_performed=False,
        notes=notes,
    )


def create_error_artifact(
    source_request_id: str,
    error_summary: str,
    created_by: str | None = None,
    notes: str | None = None,
) -> DashboardOutputArtifact:
    """Create error artifact metadata only."""

    _require_nonempty_string(source_request_id, "source_request_id")
    _require_nonempty_string(error_summary, "error_summary")
    _require_optional_string(created_by, "created_by")
    _require_optional_string(notes, "notes")
    return DashboardOutputArtifact(
        artifact_id=create_output_artifact_id(
            "error_artifact",
            source_request_id=source_request_id,
        ),
        artifact_type="error_artifact",
        source_request_id=source_request_id,
        artifact_summary=error_summary,
        lifecycle_status="FAILED",
        error_summary=error_summary,
        created_by=created_by,
        created_at=None,
        output_written=False,
        dashboard_regenerated=False,
        phase4i_mutated=False,
        runtime_mutation_performed=False,
        notes=notes,
    )


def create_refresh_instruction_for_artifact(
    artifact: DashboardOutputArtifact,
    refresh_mode: str = "show_message",
    message: str | None = None,
) -> DashboardOutputRefreshInstruction:
    """Create refresh instruction metadata for an artifact."""

    artifact = validate_dashboard_output_artifact(artifact)
    _require_supported(refresh_mode, OUTPUT_REFRESH_MODES, "refresh_mode")
    _require_optional_string(message, "message")
    final_message = message or artifact.artifact_summary
    manual_action_required = refresh_mode not in ("no_refresh", "show_message")
    return DashboardOutputRefreshInstruction(
        refresh_id=create_output_refresh_id(artifact.artifact_id, refresh_mode),
        artifact_id=artifact.artifact_id,
        refresh_mode=refresh_mode,
        message=final_message,
        link_target=artifact.artifact_uri if refresh_mode == "link_to_artifact" else None,
        run_id=artifact.run_id if refresh_mode == "link_to_run" else None,
        dashboard_reference=artifact.dashboard_reference,
        safe_to_display=True,
        requires_manual_action=manual_action_required,
        refresh_performed=False,
        notes=artifact.notes,
    )


def _normalize_token(value: str) -> str:
    _require_nonempty_string(value, "value")
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().upper())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "NONE"


def _require_nonempty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DashboardOutputLifecycleError(f"{field_name} is required.")
    return value


def _require_optional_string(value: Any, field_name: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise DashboardOutputLifecycleError(
            f"{field_name} must be a string or None."
        )
    return value


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> str:
    if not isinstance(value, str) or value not in supported:
        raise DashboardOutputLifecycleError(f"Unsupported {field_name}: {value!r}.")
    return value


def _require_boolean(value: Any, field_name: str) -> bool:
    if type(value) is not bool:
        raise DashboardOutputLifecycleError(f"{field_name} must be boolean.")
    return value


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DashboardOutputLifecycleError(f"{field_name} must be a dictionary.")
    return value
