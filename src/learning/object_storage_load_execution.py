"""Phase 7CD controlled Object Storage load execution.

This module provides a governed Object Storage source-load path with injected
clients only. It does not import OCI, construct clients, read credential files,
write object content to disk, parse AWR files, call run_analysis.py, regenerate
dashboards, mutate Phase 4I, or implement Phase 8 EM Extract behavior.
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
from src.learning.object_storage_config_validation import (
    ObjectStorageConfiguration,
    ObjectStorageConfigurationValidation,
    object_storage_configuration_to_dict,
    object_storage_configuration_validation_to_dict,
    validate_object_storage_configuration,
    validate_object_storage_configuration_validation,
)
from src.learning.screen3_source_selection import (
    SourceSelection,
    source_selection_from_dict,
    source_selection_to_dict,
)


OBJECT_STORAGE_LOAD_MODES = (
    "metadata_only",
    "head_object",
    "get_object",
    "list_prefix",
)

OBJECT_STORAGE_LOAD_STATUSES = (
    "dry_run_only",
    "blocked_invalid_config",
    "blocked_no_client",
    "blocked_secret_detected",
    "metadata_validated",
    "object_metadata_loaded",
    "object_content_loaded_in_memory",
    "prefix_listed",
    "persisted_metadata_only",
    "idempotent_replay",
    "failed_safely",
)

OBJECT_STORAGE_LOAD_VALIDATION_STATUSES = (
    "valid_metadata_only",
    "blocked_invalid_config",
    "blocked_no_client",
    "blocked_secret_detected",
    "dry_run_only",
    "can_attempt_load",
)

SECRET_FIELD_NAMES = (
    "password",
    "secret",
    "token",
    "api_key",
    "private_key",
    "key_file_content",
    "auth_token",
    "credential_value",
)

_WORKFLOW_TYPE = "screen3_object_storage_load"
_WORKFLOW_SCOPE = "screen3_object_storage_load_execution"
_TOKEN_PATTERN = re.compile(r"[^A-Za-z0-9]+")


class ObjectStorageLoadExecutionError(ValueError):
    """Raised when Phase 7CD Object Storage load metadata is unsafe."""


@dataclass(frozen=True)
class ObjectStorageLoadRequestEnvelope:
    """Governed request envelope for Object Storage load execution."""

    load_execution_id: str
    source_selection: SourceSelection | dict[str, Any]
    object_storage_config: ObjectStorageConfiguration
    object_storage_validation: ObjectStorageConfigurationValidation
    actor_id: str
    actor_audit_context: dict[str, Any]
    idempotency_key: str
    transaction_group_id: str
    requested_object_name: str | None = None
    requested_prefix: str | None = None
    load_mode: str = "metadata_only"
    expected_file_type: str | None = None
    validation_reference: str | None = None
    rollback_reference: str | None = None
    dry_run: bool = False
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.load_execution_id, "load_execution_id")
        _normalize_source_selection(self.source_selection)
        if not isinstance(self.object_storage_config, ObjectStorageConfiguration):
            raise ObjectStorageLoadExecutionError(
                "object_storage_config must be an ObjectStorageConfiguration instance."
            )
        validate_object_storage_configuration(self.object_storage_config)
        if not isinstance(
            self.object_storage_validation,
            ObjectStorageConfigurationValidation,
        ):
            raise ObjectStorageLoadExecutionError(
                "object_storage_validation must be an ObjectStorageConfigurationValidation instance."
            )
        validate_object_storage_configuration_validation(self.object_storage_validation)
        _require_text(self.actor_id, "actor_id")
        _require_mapping(self.actor_audit_context, "actor_audit_context")
        _require_text(self.idempotency_key, "idempotency_key")
        _require_text(self.transaction_group_id, "transaction_group_id")
        _require_optional_text(self.requested_object_name, "requested_object_name")
        _require_optional_text(self.requested_prefix, "requested_prefix")
        _require_supported(self.load_mode, OBJECT_STORAGE_LOAD_MODES, "load_mode")
        _require_optional_text(self.expected_file_type, "expected_file_type")
        _require_optional_text(self.validation_reference, "validation_reference")
        _require_optional_text(self.rollback_reference, "rollback_reference")
        _require_bool(self.dry_run, "dry_run")
        _require_optional_text(self.created_at, "created_at")
        _require_optional_text(self.notes, "notes")


@dataclass(frozen=True)
class ObjectStorageLoadValidation:
    """Validation metadata for one Object Storage load request."""

    load_validation_id: str
    load_execution_id: str
    valid: bool
    validation_status: str
    actor_present: bool
    config_metadata_valid: bool
    object_storage_validation_present: bool
    object_name_or_prefix_present: bool
    client_present: bool
    can_attempt_load: bool
    load_blocked: bool
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    credential_value_present: bool = False
    secret_detected: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.load_validation_id, "load_validation_id")
        _require_text(self.load_execution_id, "load_execution_id")
        _require_bool(self.valid, "valid")
        _require_supported(
            self.validation_status,
            OBJECT_STORAGE_LOAD_VALIDATION_STATUSES,
            "validation_status",
        )
        for field_name in (
            "actor_present",
            "config_metadata_valid",
            "object_storage_validation_present",
            "object_name_or_prefix_present",
            "client_present",
            "can_attempt_load",
            "load_blocked",
            "credential_value_present",
            "secret_detected",
        ):
            _require_bool(getattr(self, field_name), field_name)
        _require_string_list(self.denied_reasons, "denied_reasons")
        _require_string_list(self.warnings, "warnings")
        _require_string_list(self.required_next_steps, "required_next_steps")
        _require_optional_text(self.notes, "notes")
        _reject_true(self.credential_value_present, "credential_value_present")
        _reject_true(self.secret_detected, "secret_detected")
        if self.can_attempt_load and not (
            self.config_metadata_valid and self.client_present
        ):
            raise ObjectStorageLoadExecutionError(
                "can_attempt_load requires valid metadata and an injected client."
            )
        if self.valid and self.load_blocked:
            raise ObjectStorageLoadExecutionError(
                "valid load validation cannot also be load_blocked."
            )


@dataclass(frozen=True)
class ObjectStorageLoadedObjectReference:
    """Metadata reference for one loaded or listed Object Storage object."""

    object_reference_id: str
    namespace: str
    bucket: str
    object_name: str
    region: str | None = None
    size_bytes: int | None = None
    etag: str | None = None
    content_type: str | None = None
    checksum: str | None = None
    artifact_reference: str | None = None
    local_file_written: bool = False
    object_downloaded: bool = False
    object_content_persisted: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.object_reference_id, "object_reference_id")
        _require_text(self.namespace, "namespace")
        _require_text(self.bucket, "bucket")
        _require_text(self.object_name, "object_name")
        _require_optional_text(self.region, "region")
        _require_optional_nonnegative_int(self.size_bytes, "size_bytes")
        _require_optional_text(self.etag, "etag")
        _require_optional_text(self.content_type, "content_type")
        _require_optional_text(self.checksum, "checksum")
        _require_optional_text(self.artifact_reference, "artifact_reference")
        _require_bool(self.local_file_written, "local_file_written")
        _require_bool(self.object_downloaded, "object_downloaded")
        _require_bool(self.object_content_persisted, "object_content_persisted")
        _require_optional_text(self.notes, "notes")
        _reject_true(self.local_file_written, "local_file_written")
        _reject_true(self.object_content_persisted, "object_content_persisted")


@dataclass(frozen=True)
class ObjectStorageLoadResult:
    """Result record for controlled Object Storage load execution."""

    load_execution_id: str
    idempotency_key: str
    transaction_group_id: str
    load_status: str
    object_storage_call_performed: bool
    object_head_performed: bool
    object_download_performed: bool
    local_file_written: bool
    db_lookup_performed: bool
    run_analysis_called: bool
    parser_invoked: bool
    phase4i_mutated: bool
    dashboard_regenerated: bool
    workflow_request_persisted: bool
    workflow_validation_persisted: bool
    workflow_audit_persisted: bool
    output_artifacts_persisted: bool
    loaded_objects: tuple[ObjectStorageLoadedObjectReference, ...] = ()
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.load_execution_id, "load_execution_id")
        _require_text(self.idempotency_key, "idempotency_key")
        _require_text(self.transaction_group_id, "transaction_group_id")
        _require_supported(self.load_status, OBJECT_STORAGE_LOAD_STATUSES, "load_status")
        for field_name in (
            "object_storage_call_performed",
            "object_head_performed",
            "object_download_performed",
            "local_file_written",
            "db_lookup_performed",
            "run_analysis_called",
            "parser_invoked",
            "phase4i_mutated",
            "dashboard_regenerated",
            "workflow_request_persisted",
            "workflow_validation_persisted",
            "workflow_audit_persisted",
            "output_artifacts_persisted",
        ):
            _require_bool(getattr(self, field_name), field_name)
        if not isinstance(self.loaded_objects, tuple):
            raise ObjectStorageLoadExecutionError("loaded_objects must be a tuple.")
        for ref in self.loaded_objects:
            validate_loaded_object_reference(ref)
        _require_string_list(self.denied_reasons, "denied_reasons")
        _require_string_list(self.warnings, "warnings")
        _require_string_list(self.required_next_steps, "required_next_steps")
        _require_optional_text(self.notes, "notes")
        _reject_true(self.local_file_written, "local_file_written")
        _reject_true(self.db_lookup_performed, "db_lookup_performed")
        _reject_true(self.run_analysis_called, "run_analysis_called")
        _reject_true(self.parser_invoked, "parser_invoked")
        _reject_true(self.phase4i_mutated, "phase4i_mutated")
        _reject_true(self.dashboard_regenerated, "dashboard_regenerated")


def create_object_storage_load_execution_id(
    idempotency_key: str,
    object_name: str | None = None,
    prefix: str | None = None,
) -> str:
    """Create a deterministic Phase 7CD load execution id."""

    _require_text(idempotency_key, "idempotency_key")
    _require_optional_text(object_name, "object_name")
    _require_optional_text(prefix, "prefix")
    return _stable_id(
        "OBJECT-STORAGE-LOAD-EXECUTION",
        idempotency_key,
        object_name or prefix or "NO-OBJECT-OR-PREFIX",
    )


def validate_object_storage_load_envelope(
    envelope: ObjectStorageLoadRequestEnvelope,
) -> ObjectStorageLoadRequestEnvelope:
    """Validate a 7CD Object Storage load envelope."""

    if not isinstance(envelope, ObjectStorageLoadRequestEnvelope):
        raise ObjectStorageLoadExecutionError(
            "envelope must be an ObjectStorageLoadRequestEnvelope instance."
        )
    envelope.__post_init__()
    if envelope.actor_audit_context.get("actor_id") != envelope.actor_id:
        raise ObjectStorageLoadExecutionError(
            "actor_audit_context.actor_id must match actor_id."
        )
    if not envelope.rollback_reference:
        raise ObjectStorageLoadExecutionError(
            "rollback_reference is required for Phase 7CD execution."
        )
    if envelope.object_storage_validation.config_id != envelope.object_storage_config.config_id:
        raise ObjectStorageLoadExecutionError(
            "object_storage_validation.config_id must match object_storage_config.config_id."
        )
    return envelope


def evaluate_object_storage_load_request(
    envelope: ObjectStorageLoadRequestEnvelope,
    client: Any | None = None,
) -> ObjectStorageLoadValidation:
    """Evaluate Object Storage load readiness without reading secrets."""

    envelope = validate_object_storage_load_envelope(envelope)
    secret_fields = detect_secret_fields(_envelope_secret_scan_payload(envelope))
    actor_present = bool(envelope.actor_id and envelope.actor_audit_context.get("actor_id"))
    object_name_or_prefix_present = bool(
        envelope.requested_object_name
        or envelope.requested_prefix
        or envelope.object_storage_config.object_name
        or envelope.object_storage_config.prefix
    )
    config_metadata_valid = (
        envelope.object_storage_validation.valid_metadata
        and envelope.object_storage_validation.can_attempt_future_access
    )
    client_present = client is not None
    denied_reasons: list[str] = []
    warnings = [
        "Object Storage load execution is controlled by injected client only.",
        "No parser, run_analysis.py, dashboard regeneration, or Phase 4I mutation occurs.",
    ]
    required_next_steps: list[str] = []
    status = "can_attempt_load"
    valid = True

    if secret_fields:
        status = "blocked_secret_detected"
        valid = False
        denied_reasons.append(
            "secret-like field names are not allowed in Object Storage load metadata"
        )
        required_next_steps.append("remove credential values from workflow metadata")
    elif not actor_present:
        status = "blocked_invalid_config"
        valid = False
        denied_reasons.append("actor metadata is required")
        required_next_steps.append("provide actor audit metadata")
    elif not config_metadata_valid:
        status = "blocked_invalid_config"
        valid = False
        denied_reasons.extend(envelope.object_storage_validation.denied_reasons)
        required_next_steps.extend(envelope.object_storage_validation.required_next_steps)
    elif not object_name_or_prefix_present:
        status = "blocked_invalid_config"
        valid = False
        denied_reasons.append("object_name or prefix is required")
        required_next_steps.append("provide object name or prefix metadata")
    elif envelope.load_mode != "metadata_only" and client is None:
        status = "blocked_no_client"
        valid = False
        denied_reasons.append("injected Object Storage client is required")
        required_next_steps.append("provide an injected object storage client")
    elif envelope.dry_run:
        status = "dry_run_only"
        valid = False
        denied_reasons.append("dry_run=true; object storage client was not called")
        required_next_steps.append("submit with dry_run=false to perform controlled load")
    elif envelope.load_mode == "metadata_only":
        status = "valid_metadata_only"
        valid = True

    return ObjectStorageLoadValidation(
        load_validation_id=create_object_storage_load_validation_id(
            envelope.load_execution_id
        ),
        load_execution_id=envelope.load_execution_id,
        valid=valid,
        validation_status=status,
        actor_present=actor_present,
        config_metadata_valid=config_metadata_valid,
        object_storage_validation_present=True,
        object_name_or_prefix_present=object_name_or_prefix_present,
        client_present=client_present,
        can_attempt_load=(
            valid
            and config_metadata_valid
            and client_present
            and envelope.load_mode != "metadata_only"
        ),
        load_blocked=not valid,
        denied_reasons=denied_reasons,
        warnings=warnings,
        required_next_steps=required_next_steps,
        credential_value_present=False,
        secret_detected=False,
        notes=envelope.notes,
    )


def execute_object_storage_load(
    envelope: ObjectStorageLoadRequestEnvelope,
    repository: GovernedWorkflowRepository | None = None,
    client: Any | None = None,
) -> ObjectStorageLoadResult:
    """Execute a controlled Object Storage load through an injected client."""

    try:
        envelope = validate_object_storage_load_envelope(envelope)
    except ObjectStorageLoadExecutionError as exc:
        return _blocked_result_from_any(envelope, "blocked_invalid_config", str(exc))

    if repository is None or not isinstance(repository, GovernedWorkflowRepository):
        return _blocked_result(
            envelope,
            "blocked_invalid_config",
            "governed workflow repository is required",
            ["provide a GovernedWorkflowRepository"],
        )

    existing = repository.get_by_idempotency_key(envelope.idempotency_key)
    if existing is not None:
        return validate_object_storage_load_result(
            ObjectStorageLoadResult(
                load_execution_id=envelope.load_execution_id,
                idempotency_key=envelope.idempotency_key,
                transaction_group_id=existing.transaction_group_id,
                load_status="idempotent_replay",
                object_storage_call_performed=False,
                object_head_performed=False,
                object_download_performed=False,
                local_file_written=False,
                db_lookup_performed=False,
                run_analysis_called=False,
                parser_invoked=False,
                phase4i_mutated=False,
                dashboard_regenerated=False,
                workflow_request_persisted=True,
                workflow_validation_persisted=True,
                workflow_audit_persisted=True,
                output_artifacts_persisted=False,
                warnings=[
                    "idempotency key already persisted; Object Storage client was not called"
                ],
                required_next_steps=["return existing governed workflow metadata"],
                notes=envelope.notes,
            )
        )

    validation = evaluate_object_storage_load_request(envelope, client=client)
    if validation.load_blocked:
        return _persist_and_return(
            envelope,
            repository,
            validation,
            load_status=_blocked_status_from_validation(validation),
            loaded_objects=(),
            object_storage_call_performed=False,
            object_head_performed=False,
            object_download_performed=False,
        )

    if envelope.load_mode == "metadata_only":
        return _persist_and_return(
            envelope,
            repository,
            validation,
            load_status="metadata_validated",
            loaded_objects=(),
            object_storage_call_performed=False,
            object_head_performed=False,
            object_download_performed=False,
        )

    try:
        if envelope.load_mode == "head_object":
            loaded_objects = (_head_object(envelope, client),)
            status = "object_metadata_loaded"
            object_head_performed = True
            object_download_performed = False
        elif envelope.load_mode == "get_object":
            loaded_objects = (_get_object(envelope, client),)
            status = "object_content_loaded_in_memory"
            object_head_performed = False
            object_download_performed = True
        elif envelope.load_mode == "list_prefix":
            loaded_objects = tuple(_list_prefix(envelope, client))
            status = "prefix_listed"
            object_head_performed = False
            object_download_performed = False
        else:
            raise ObjectStorageLoadExecutionError(
                f"unsupported load_mode: {envelope.load_mode}"
            )
    except Exception as exc:  # noqa: BLE001
        return _record_safe_failure(envelope, repository, exc)

    return _persist_and_return(
        envelope,
        repository,
        validation,
        load_status=status,
        loaded_objects=loaded_objects,
        object_storage_call_performed=True,
        object_head_performed=object_head_performed,
        object_download_performed=object_download_performed,
    )


def validate_object_storage_load_validation(
    validation: ObjectStorageLoadValidation,
) -> ObjectStorageLoadValidation:
    """Validate Object Storage load validation metadata."""

    if not isinstance(validation, ObjectStorageLoadValidation):
        raise ObjectStorageLoadExecutionError(
            "validation must be an ObjectStorageLoadValidation instance."
        )
    validation.__post_init__()
    return validation


def validate_loaded_object_reference(
    ref: ObjectStorageLoadedObjectReference,
) -> ObjectStorageLoadedObjectReference:
    """Validate a loaded object metadata reference."""

    if not isinstance(ref, ObjectStorageLoadedObjectReference):
        raise ObjectStorageLoadExecutionError(
            "ref must be an ObjectStorageLoadedObjectReference instance."
        )
    ref.__post_init__()
    return ref


def validate_object_storage_load_result(
    result: ObjectStorageLoadResult,
) -> ObjectStorageLoadResult:
    """Validate Object Storage load result metadata."""

    if not isinstance(result, ObjectStorageLoadResult):
        raise ObjectStorageLoadExecutionError(
            "result must be an ObjectStorageLoadResult instance."
        )
    result.__post_init__()
    return result


def detect_secret_fields(payload: Any) -> list[str]:
    """Return secret-like field paths without exposing values."""

    findings: list[str] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                key_text = str(key)
                key_path = f"{path}.{key_text}" if path else key_text
                if _is_secret_field_name(key_text):
                    findings.append(key_path)
                visit(nested, key_path)
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                visit(nested, f"{path}[{index}]")

    visit(payload, "")
    return sorted(set(findings))


def object_storage_load_envelope_to_dict(
    envelope: ObjectStorageLoadRequestEnvelope,
) -> dict[str, Any]:
    """Serialize a load envelope without credential values."""

    envelope = validate_object_storage_load_envelope(envelope)
    source_selection = _normalize_source_selection(envelope.source_selection)
    return {
        "load_execution_id": envelope.load_execution_id,
        "source_selection": source_selection_to_dict(source_selection),
        "object_storage_config": object_storage_configuration_to_dict(
            envelope.object_storage_config
        ),
        "object_storage_validation": object_storage_configuration_validation_to_dict(
            envelope.object_storage_validation
        ),
        "actor_id": envelope.actor_id,
        "actor_audit_context": dict(envelope.actor_audit_context),
        "idempotency_key": envelope.idempotency_key,
        "transaction_group_id": envelope.transaction_group_id,
        "requested_object_name": envelope.requested_object_name,
        "requested_prefix": envelope.requested_prefix,
        "load_mode": envelope.load_mode,
        "expected_file_type": envelope.expected_file_type,
        "validation_reference": envelope.validation_reference,
        "rollback_reference": envelope.rollback_reference,
        "dry_run": envelope.dry_run,
        "created_at": envelope.created_at,
        "notes": envelope.notes,
    }


def object_storage_load_envelope_from_dict(
    data: dict[str, Any],
) -> ObjectStorageLoadRequestEnvelope:
    """Deserialize a load envelope."""

    _require_mapping(data, "object_storage_load_envelope")
    secret_fields = detect_secret_fields(data)
    if secret_fields:
        raise ObjectStorageLoadExecutionError(
            "secret-like field names are not allowed in Object Storage load metadata"
        )
    from src.learning.object_storage_config_validation import (  # local, no network
        object_storage_configuration_from_dict,
        object_storage_configuration_validation_from_dict,
    )

    source_selection = data.get("source_selection")
    if not isinstance(source_selection, dict):
        raise ObjectStorageLoadExecutionError("source_selection is required.")
    config = data.get("object_storage_config")
    validation = data.get("object_storage_validation")
    if not isinstance(config, dict) or not isinstance(validation, dict):
        raise ObjectStorageLoadExecutionError(
            "object_storage_config and object_storage_validation are required."
        )
    return ObjectStorageLoadRequestEnvelope(
        load_execution_id=data.get("load_execution_id"),
        source_selection=source_selection_from_dict(source_selection),
        object_storage_config=object_storage_configuration_from_dict(config),
        object_storage_validation=object_storage_configuration_validation_from_dict(
            validation
        ),
        actor_id=data.get("actor_id"),
        actor_audit_context=data.get("actor_audit_context"),
        idempotency_key=data.get("idempotency_key"),
        transaction_group_id=data.get("transaction_group_id"),
        requested_object_name=data.get("requested_object_name"),
        requested_prefix=data.get("requested_prefix"),
        load_mode=data.get("load_mode", "metadata_only"),
        expected_file_type=data.get("expected_file_type"),
        validation_reference=data.get("validation_reference"),
        rollback_reference=data.get("rollback_reference"),
        dry_run=data.get("dry_run", False),
        created_at=data.get("created_at"),
        notes=data.get("notes"),
    )


def object_storage_load_validation_to_dict(
    validation: ObjectStorageLoadValidation,
) -> dict[str, Any]:
    """Serialize load validation metadata."""

    validation = validate_object_storage_load_validation(validation)
    return {
        "load_validation_id": validation.load_validation_id,
        "load_execution_id": validation.load_execution_id,
        "valid": validation.valid,
        "validation_status": validation.validation_status,
        "actor_present": validation.actor_present,
        "config_metadata_valid": validation.config_metadata_valid,
        "object_storage_validation_present": validation.object_storage_validation_present,
        "object_name_or_prefix_present": validation.object_name_or_prefix_present,
        "client_present": validation.client_present,
        "can_attempt_load": validation.can_attempt_load,
        "load_blocked": validation.load_blocked,
        "denied_reasons": list(validation.denied_reasons),
        "warnings": list(validation.warnings),
        "required_next_steps": list(validation.required_next_steps),
        "credential_value_present": validation.credential_value_present,
        "secret_detected": validation.secret_detected,
        "notes": validation.notes,
    }


def object_storage_load_validation_from_dict(
    data: dict[str, Any],
) -> ObjectStorageLoadValidation:
    """Deserialize load validation metadata."""

    _require_mapping(data, "object_storage_load_validation")
    return ObjectStorageLoadValidation(
        load_validation_id=data.get("load_validation_id"),
        load_execution_id=data.get("load_execution_id"),
        valid=data.get("valid"),
        validation_status=data.get("validation_status"),
        actor_present=data.get("actor_present"),
        config_metadata_valid=data.get("config_metadata_valid"),
        object_storage_validation_present=data.get(
            "object_storage_validation_present"
        ),
        object_name_or_prefix_present=data.get("object_name_or_prefix_present"),
        client_present=data.get("client_present"),
        can_attempt_load=data.get("can_attempt_load"),
        load_blocked=data.get("load_blocked"),
        denied_reasons=list(data.get("denied_reasons", [])),
        warnings=list(data.get("warnings", [])),
        required_next_steps=list(data.get("required_next_steps", [])),
        credential_value_present=data.get("credential_value_present", False),
        secret_detected=data.get("secret_detected", False),
        notes=data.get("notes"),
    )


def loaded_object_reference_to_dict(
    ref: ObjectStorageLoadedObjectReference,
) -> dict[str, Any]:
    """Serialize loaded object metadata."""

    ref = validate_loaded_object_reference(ref)
    return {
        "object_reference_id": ref.object_reference_id,
        "namespace": ref.namespace,
        "bucket": ref.bucket,
        "object_name": ref.object_name,
        "region": ref.region,
        "size_bytes": ref.size_bytes,
        "etag": ref.etag,
        "content_type": ref.content_type,
        "checksum": ref.checksum,
        "artifact_reference": ref.artifact_reference,
        "local_file_written": ref.local_file_written,
        "object_downloaded": ref.object_downloaded,
        "object_content_persisted": ref.object_content_persisted,
        "notes": ref.notes,
    }


def loaded_object_reference_from_dict(
    data: dict[str, Any],
) -> ObjectStorageLoadedObjectReference:
    """Deserialize loaded object metadata."""

    _require_mapping(data, "loaded_object_reference")
    return ObjectStorageLoadedObjectReference(
        object_reference_id=data.get("object_reference_id"),
        namespace=data.get("namespace"),
        bucket=data.get("bucket"),
        object_name=data.get("object_name"),
        region=data.get("region"),
        size_bytes=data.get("size_bytes"),
        etag=data.get("etag"),
        content_type=data.get("content_type"),
        checksum=data.get("checksum"),
        artifact_reference=data.get("artifact_reference"),
        local_file_written=data.get("local_file_written", False),
        object_downloaded=data.get("object_downloaded", False),
        object_content_persisted=data.get("object_content_persisted", False),
        notes=data.get("notes"),
    )


def object_storage_load_result_to_dict(
    result: ObjectStorageLoadResult,
) -> dict[str, Any]:
    """Serialize load result metadata."""

    result = validate_object_storage_load_result(result)
    return {
        "load_execution_id": result.load_execution_id,
        "idempotency_key": result.idempotency_key,
        "transaction_group_id": result.transaction_group_id,
        "load_status": result.load_status,
        "object_storage_call_performed": result.object_storage_call_performed,
        "object_head_performed": result.object_head_performed,
        "object_download_performed": result.object_download_performed,
        "local_file_written": result.local_file_written,
        "db_lookup_performed": result.db_lookup_performed,
        "run_analysis_called": result.run_analysis_called,
        "parser_invoked": result.parser_invoked,
        "phase4i_mutated": result.phase4i_mutated,
        "dashboard_regenerated": result.dashboard_regenerated,
        "workflow_request_persisted": result.workflow_request_persisted,
        "workflow_validation_persisted": result.workflow_validation_persisted,
        "workflow_audit_persisted": result.workflow_audit_persisted,
        "output_artifacts_persisted": result.output_artifacts_persisted,
        "loaded_objects": [
            loaded_object_reference_to_dict(ref) for ref in result.loaded_objects
        ],
        "denied_reasons": list(result.denied_reasons),
        "warnings": list(result.warnings),
        "required_next_steps": list(result.required_next_steps),
        "notes": result.notes,
    }


def object_storage_load_result_from_dict(
    data: dict[str, Any],
) -> ObjectStorageLoadResult:
    """Deserialize load result metadata."""

    _require_mapping(data, "object_storage_load_result")
    return ObjectStorageLoadResult(
        load_execution_id=data.get("load_execution_id"),
        idempotency_key=data.get("idempotency_key"),
        transaction_group_id=data.get("transaction_group_id"),
        load_status=data.get("load_status"),
        object_storage_call_performed=data.get("object_storage_call_performed", False),
        object_head_performed=data.get("object_head_performed", False),
        object_download_performed=data.get("object_download_performed", False),
        local_file_written=data.get("local_file_written", False),
        db_lookup_performed=data.get("db_lookup_performed", False),
        run_analysis_called=data.get("run_analysis_called", False),
        parser_invoked=data.get("parser_invoked", False),
        phase4i_mutated=data.get("phase4i_mutated", False),
        dashboard_regenerated=data.get("dashboard_regenerated", False),
        workflow_request_persisted=data.get("workflow_request_persisted", False),
        workflow_validation_persisted=data.get("workflow_validation_persisted", False),
        workflow_audit_persisted=data.get("workflow_audit_persisted", False),
        output_artifacts_persisted=data.get("output_artifacts_persisted", False),
        loaded_objects=tuple(
            loaded_object_reference_from_dict(ref)
            for ref in data.get("loaded_objects", [])
        ),
        denied_reasons=list(data.get("denied_reasons", [])),
        warnings=list(data.get("warnings", [])),
        required_next_steps=list(data.get("required_next_steps", [])),
        notes=data.get("notes"),
    )


def create_object_storage_load_validation_id(load_execution_id: str) -> str:
    """Create a deterministic load validation id."""

    _require_text(load_execution_id, "load_execution_id")
    return _stable_id("OBJECT-STORAGE-LOAD-VALIDATION", load_execution_id)


def create_loaded_object_reference_id(
    namespace: str,
    bucket: str,
    object_name: str,
) -> str:
    """Create a deterministic loaded object reference id."""

    _require_text(namespace, "namespace")
    _require_text(bucket, "bucket")
    _require_text(object_name, "object_name")
    return _stable_id("OBJECT-STORAGE-LOADED-OBJECT", namespace, bucket, object_name)


def _persist_and_return(
    envelope: ObjectStorageLoadRequestEnvelope,
    repository: GovernedWorkflowRepository,
    validation: ObjectStorageLoadValidation,
    *,
    load_status: str,
    loaded_objects: tuple[ObjectStorageLoadedObjectReference, ...],
    object_storage_call_performed: bool,
    object_head_performed: bool,
    object_download_performed: bool,
) -> ObjectStorageLoadResult:
    try:
        persistence_result = repository.persist_workflow_bundle(
            request=_build_workflow_request(envelope, validation, load_status),
            transaction=_build_workflow_transaction(envelope),
            validation=_build_workflow_validation(envelope, validation),
            audit=_build_workflow_audit(envelope, load_status),
            output_artifacts=_build_output_artifacts(
                envelope,
                validation,
                loaded_objects,
                load_status,
            ),
        )
    except GovernedWorkflowRepositoryError as exc:
        return _record_safe_failure(envelope, repository, exc)

    if persistence_result.duplicate:
        return validate_object_storage_load_result(
            ObjectStorageLoadResult(
                load_execution_id=envelope.load_execution_id,
                idempotency_key=envelope.idempotency_key,
                transaction_group_id=envelope.transaction_group_id,
                load_status="idempotent_replay",
                object_storage_call_performed=False,
                object_head_performed=False,
                object_download_performed=False,
                local_file_written=False,
                db_lookup_performed=False,
                run_analysis_called=False,
                parser_invoked=False,
                phase4i_mutated=False,
                dashboard_regenerated=False,
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

    return validate_object_storage_load_result(
        ObjectStorageLoadResult(
            load_execution_id=envelope.load_execution_id,
            idempotency_key=envelope.idempotency_key,
            transaction_group_id=envelope.transaction_group_id,
            load_status=load_status,
            object_storage_call_performed=object_storage_call_performed,
            object_head_performed=object_head_performed,
            object_download_performed=object_download_performed,
            local_file_written=False,
            db_lookup_performed=False,
            run_analysis_called=False,
            parser_invoked=False,
            phase4i_mutated=False,
            dashboard_regenerated=False,
            workflow_request_persisted=bool(persistence_result.request),
            workflow_validation_persisted=bool(persistence_result.validation),
            workflow_audit_persisted=bool(persistence_result.audit),
            output_artifacts_persisted=bool(persistence_result.output_artifacts),
            loaded_objects=loaded_objects,
            denied_reasons=list(validation.denied_reasons),
            warnings=list(validation.warnings),
            required_next_steps=list(validation.required_next_steps),
            notes=envelope.notes,
        )
    )


def _head_object(
    envelope: ObjectStorageLoadRequestEnvelope,
    client: Any,
) -> ObjectStorageLoadedObjectReference:
    metadata = _normalize_client_response(
        client.head_object(
            _namespace(envelope),
            _bucket(envelope),
            _object_name(envelope),
        )
    )
    return _reference_from_metadata(envelope, _object_name(envelope), metadata, False)


def _get_object(
    envelope: ObjectStorageLoadRequestEnvelope,
    client: Any,
) -> ObjectStorageLoadedObjectReference:
    response = client.get_object(
        _namespace(envelope),
        _bucket(envelope),
        _object_name(envelope),
    )
    metadata = _normalize_client_response(response)
    content = _extract_content(response)
    if content is not None:
        metadata.setdefault("size_bytes", len(content))
        metadata.setdefault("checksum", hashlib.sha256(content).hexdigest())
    return _reference_from_metadata(envelope, _object_name(envelope), metadata, True)


def _list_prefix(
    envelope: ObjectStorageLoadRequestEnvelope,
    client: Any,
) -> list[ObjectStorageLoadedObjectReference]:
    objects = client.list_objects(
        _namespace(envelope),
        _bucket(envelope),
        _prefix(envelope),
    )
    if hasattr(objects, "data"):
        objects = getattr(objects, "data")
    if hasattr(objects, "objects"):
        objects = getattr(objects, "objects")
    if not isinstance(objects, list):
        raise ObjectStorageLoadExecutionError("list_objects must return a list.")
    references: list[ObjectStorageLoadedObjectReference] = []
    for item in objects:
        metadata = _normalize_client_response(item)
        object_name = str(
            metadata.get("object_name")
            or metadata.get("name")
            or metadata.get("objectName")
            or ""
        ).strip()
        if not object_name:
            raise ObjectStorageLoadExecutionError(
                "listed object metadata must include object_name or name."
            )
        references.append(_reference_from_metadata(envelope, object_name, metadata, False))
    return references


def _reference_from_metadata(
    envelope: ObjectStorageLoadRequestEnvelope,
    object_name: str,
    metadata: dict[str, Any],
    object_downloaded: bool,
) -> ObjectStorageLoadedObjectReference:
    artifact_reference = _object_artifact_reference(
        _namespace(envelope),
        _bucket(envelope),
        object_name,
    )
    size = metadata.get("size_bytes", metadata.get("size"))
    return ObjectStorageLoadedObjectReference(
        object_reference_id=create_loaded_object_reference_id(
            _namespace(envelope),
            _bucket(envelope),
            object_name,
        ),
        namespace=_namespace(envelope),
        bucket=_bucket(envelope),
        object_name=object_name,
        region=envelope.object_storage_config.region,
        size_bytes=int(size) if isinstance(size, (int, float)) else None,
        etag=_optional_string_value(metadata.get("etag")),
        content_type=_optional_string_value(
            metadata.get("content_type", metadata.get("content-type"))
        ),
        checksum=_optional_string_value(metadata.get("checksum")),
        artifact_reference=artifact_reference,
        local_file_written=False,
        object_downloaded=object_downloaded,
        object_content_persisted=False,
        notes=envelope.notes,
    )


def _build_workflow_request(
    envelope: ObjectStorageLoadRequestEnvelope,
    validation: ObjectStorageLoadValidation,
    load_status: str,
) -> PersistedWorkflowRequest:
    payload = {
        "load_execution_id": envelope.load_execution_id,
        "source_selection": source_selection_to_dict(
            _normalize_source_selection(envelope.source_selection)
        ),
        "object_storage_config": object_storage_configuration_to_dict(
            envelope.object_storage_config
        ),
        "object_storage_validation": object_storage_configuration_validation_to_dict(
            envelope.object_storage_validation
        ),
        "load_validation": object_storage_load_validation_to_dict(validation),
        "requested_object_name": envelope.requested_object_name,
        "requested_prefix": envelope.requested_prefix,
        "load_mode": envelope.load_mode,
        "expected_file_type": envelope.expected_file_type,
        "validation_reference": envelope.validation_reference,
        "rollback_reference": envelope.rollback_reference,
        "load_status": load_status,
        "local_file_written": False,
        "run_analysis_called": False,
        "parser_invoked": False,
        "phase4i_mutated": False,
        "dashboard_regenerated": False,
        "credential_values_persisted": False,
    }
    return PersistedWorkflowRequest(
        workflow_request_id=_workflow_request_id(envelope),
        transaction_group_id=envelope.transaction_group_id,
        idempotency_key=envelope.idempotency_key,
        source_screen="screen_3",
        workflow_type=_WORKFLOW_TYPE,
        requested_action="load_from_object_storage",
        target_type="object_storage_source",
        target_id=envelope.requested_object_name or envelope.requested_prefix,
        actor_id=envelope.actor_id,
        payload=payload,
        status="VALIDATED" if validation.valid else "FAILED",
        notes=envelope.notes,
    )


def _build_workflow_transaction(
    envelope: ObjectStorageLoadRequestEnvelope,
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
    envelope: ObjectStorageLoadRequestEnvelope,
    validation: ObjectStorageLoadValidation,
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
    envelope: ObjectStorageLoadRequestEnvelope,
    load_status: str,
) -> PersistedWorkflowAudit:
    payload = {
        "load_execution_id": envelope.load_execution_id,
        "load_status": load_status,
        "load_mode": envelope.load_mode,
        "actor_id": envelope.actor_id,
        "object_name_present": bool(envelope.requested_object_name),
        "prefix_present": bool(envelope.requested_prefix),
        "credential_values_persisted": False,
        "runtime_truth_mutated": False,
    }
    return PersistedWorkflowAudit(
        workflow_audit_id=create_workflow_audit_id(
            _workflow_request_id(envelope),
            "screen3_object_storage_load_recorded",
        ),
        workflow_request_id=_workflow_request_id(envelope),
        transaction_group_id=envelope.transaction_group_id,
        actor_id=envelope.actor_id,
        action="screen3_object_storage_load_recorded",
        audit_summary=(
            "Phase 7CD Object Storage load metadata recorded; no parser, "
            "run_analysis.py, dashboard regeneration, or Phase 4I mutation occurred."
        ),
        payload_hash=hash_payload(payload),
        notes=envelope.notes,
    )


def _build_output_artifacts(
    envelope: ObjectStorageLoadRequestEnvelope,
    validation: ObjectStorageLoadValidation,
    loaded_objects: tuple[ObjectStorageLoadedObjectReference, ...],
    load_status: str,
) -> tuple[PersistedWorkflowOutputArtifact, ...]:
    request_id = _workflow_request_id(envelope)
    artifacts: list[PersistedWorkflowOutputArtifact] = [
        PersistedWorkflowOutputArtifact(
            workflow_output_id=create_workflow_output_id(
                request_id,
                "source_validation_artifact",
                validation.load_validation_id,
            ),
            workflow_request_id=request_id,
            artifact_type="source_validation_artifact",
            artifact_reference=f"object-storage-load-validation:{validation.load_validation_id}",
            artifact_summary="Object Storage load validation metadata.",
            artifact_metadata=object_storage_load_validation_to_dict(validation),
            status="RECORDED" if validation.valid else "FAILED",
            notes=envelope.notes,
        )
    ]
    for ref in loaded_objects:
        artifacts.append(
            PersistedWorkflowOutputArtifact(
                workflow_output_id=create_workflow_output_id(
                    request_id,
                    "object_storage_load_artifact",
                    ref.artifact_reference or ref.object_reference_id,
                ),
                workflow_request_id=request_id,
                artifact_type="object_storage_load_artifact",
                artifact_reference=ref.artifact_reference or ref.object_reference_id,
                artifact_summary=f"Object Storage load metadata: {load_status}.",
                artifact_metadata=loaded_object_reference_to_dict(ref),
                status="RECORDED",
                notes=envelope.notes,
            )
        )
    return tuple(artifacts)


def _record_safe_failure(
    envelope: ObjectStorageLoadRequestEnvelope,
    repository: GovernedWorkflowRepository,
    exc: Exception,
) -> ObjectStorageLoadResult:
    error_message = f"{type(exc).__name__}: {exc}"
    try:
        repository.record_workflow_failure(
            transaction_group_id=envelope.transaction_group_id,
            idempotency_key=envelope.idempotency_key,
            actor_id=envelope.actor_id,
            action="screen3_object_storage_load_failed",
            error_message=error_message,
            rollback_reference=envelope.rollback_reference or "object-storage-load-failure",
            workflow_request_id=_workflow_request_id(envelope),
            transaction_scope=_WORKFLOW_SCOPE,
            notes=envelope.notes,
        )
    except Exception:  # noqa: BLE001
        pass
    return validate_object_storage_load_result(
        ObjectStorageLoadResult(
            load_execution_id=envelope.load_execution_id,
            idempotency_key=envelope.idempotency_key,
            transaction_group_id=envelope.transaction_group_id,
            load_status="failed_safely",
            object_storage_call_performed=False,
            object_head_performed=False,
            object_download_performed=False,
            local_file_written=False,
            db_lookup_performed=False,
            run_analysis_called=False,
            parser_invoked=False,
            phase4i_mutated=False,
            dashboard_regenerated=False,
            workflow_request_persisted=False,
            workflow_validation_persisted=False,
            workflow_audit_persisted=False,
            output_artifacts_persisted=False,
            denied_reasons=[error_message],
            warnings=[
                "Object Storage load failed safely; runtime truth was not mutated."
            ],
            required_next_steps=["review failure metadata"],
            notes=envelope.notes,
        )
    )


def _blocked_result(
    envelope: ObjectStorageLoadRequestEnvelope,
    status: str,
    denied_reason: str,
    required_next_steps: list[str] | None = None,
) -> ObjectStorageLoadResult:
    return validate_object_storage_load_result(
        ObjectStorageLoadResult(
            load_execution_id=envelope.load_execution_id,
            idempotency_key=envelope.idempotency_key,
            transaction_group_id=envelope.transaction_group_id,
            load_status=status,
            object_storage_call_performed=False,
            object_head_performed=False,
            object_download_performed=False,
            local_file_written=False,
            db_lookup_performed=False,
            run_analysis_called=False,
            parser_invoked=False,
            phase4i_mutated=False,
            dashboard_regenerated=False,
            workflow_request_persisted=False,
            workflow_validation_persisted=False,
            workflow_audit_persisted=False,
            output_artifacts_persisted=False,
            denied_reasons=[denied_reason],
            required_next_steps=required_next_steps or [],
            notes=envelope.notes,
        )
    )


def _blocked_result_from_any(
    envelope: Any,
    status: str,
    denied_reason: str,
) -> ObjectStorageLoadResult:
    return validate_object_storage_load_result(
        ObjectStorageLoadResult(
            load_execution_id=getattr(envelope, "load_execution_id", "INVALID"),
            idempotency_key=getattr(envelope, "idempotency_key", "INVALID"),
            transaction_group_id=getattr(envelope, "transaction_group_id", "INVALID"),
            load_status=status,
            object_storage_call_performed=False,
            object_head_performed=False,
            object_download_performed=False,
            local_file_written=False,
            db_lookup_performed=False,
            run_analysis_called=False,
            parser_invoked=False,
            phase4i_mutated=False,
            dashboard_regenerated=False,
            workflow_request_persisted=False,
            workflow_validation_persisted=False,
            workflow_audit_persisted=False,
            output_artifacts_persisted=False,
            denied_reasons=[denied_reason],
            required_next_steps=["correct Object Storage load envelope metadata"],
            notes=getattr(envelope, "notes", None),
        )
    )


def _blocked_status_from_validation(validation: ObjectStorageLoadValidation) -> str:
    if validation.validation_status == "blocked_secret_detected":
        return "blocked_secret_detected"
    if validation.validation_status == "blocked_no_client":
        return "blocked_no_client"
    if validation.validation_status == "dry_run_only":
        return "dry_run_only"
    return "blocked_invalid_config"


def _workflow_request_id(envelope: ObjectStorageLoadRequestEnvelope) -> str:
    return create_workflow_request_id(_WORKFLOW_TYPE, envelope.idempotency_key)


def _namespace(envelope: ObjectStorageLoadRequestEnvelope) -> str:
    return _require_text(envelope.object_storage_config.namespace, "namespace")


def _bucket(envelope: ObjectStorageLoadRequestEnvelope) -> str:
    return _require_text(envelope.object_storage_config.bucket, "bucket")


def _object_name(envelope: ObjectStorageLoadRequestEnvelope) -> str:
    return _require_text(
        envelope.requested_object_name or envelope.object_storage_config.object_name,
        "object_name",
    )


def _prefix(envelope: ObjectStorageLoadRequestEnvelope) -> str | None:
    return envelope.requested_prefix or envelope.object_storage_config.prefix


def _object_artifact_reference(namespace: str, bucket: str, object_name: str) -> str:
    return f"oci://{namespace}/{bucket}/{object_name}"


def _normalize_source_selection(value: SourceSelection | dict[str, Any]) -> SourceSelection:
    if isinstance(value, SourceSelection):
        value.__post_init__()
        return value
    if isinstance(value, dict):
        return source_selection_from_dict(value)
    raise ObjectStorageLoadExecutionError(
        "source_selection must be a SourceSelection instance or dict."
    )


def _normalize_client_response(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        return dict(response)
    if hasattr(response, "headers") and isinstance(getattr(response, "headers"), dict):
        metadata = dict(getattr(response, "headers"))
    else:
        metadata = {}
    data = getattr(response, "data", None)
    if data is not None and not isinstance(data, (bytes, bytearray, str)):
        if isinstance(data, dict):
            metadata.update(data)
        else:
            metadata.update(
                {
                    key: getattr(data, key)
                    for key in (
                        "name",
                        "object_name",
                        "size",
                        "etag",
                        "content_type",
                        "checksum",
                    )
                    if hasattr(data, key)
                }
            )
    for key in (
        "name",
        "object_name",
        "size",
        "size_bytes",
        "etag",
        "content_type",
        "checksum",
    ):
        if hasattr(response, key):
            metadata.setdefault(key, getattr(response, key))
    return metadata


def _extract_content(response: Any) -> bytes | None:
    if isinstance(response, bytes):
        return response
    if isinstance(response, bytearray):
        return bytes(response)
    if isinstance(response, dict):
        content = response.get("content") or response.get("data")
    else:
        content = getattr(response, "content", None)
        if content is None:
            content = getattr(response, "data", None)
    if isinstance(content, bytes):
        return content
    if isinstance(content, bytearray):
        return bytes(content)
    if isinstance(content, str):
        return content.encode("utf-8")
    if hasattr(content, "content"):
        nested = getattr(content, "content")
        if isinstance(nested, bytes):
            return nested
    return None


def _envelope_secret_scan_payload(envelope: ObjectStorageLoadRequestEnvelope) -> dict[str, Any]:
    return {
        "source_selection": (
            source_selection_to_dict(_normalize_source_selection(envelope.source_selection))
        ),
        "object_storage_config": object_storage_configuration_to_dict(
            envelope.object_storage_config
        ),
        "actor_audit_context": dict(envelope.actor_audit_context),
    }


def _is_secret_field_name(field_name: str) -> bool:
    normalized = field_name.lower()
    return any(secret in normalized for secret in SECRET_FIELD_NAMES)


def _optional_string_value(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ObjectStorageLoadExecutionError(f"{field_name} is required.")
    return value


def _require_optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ObjectStorageLoadExecutionError(f"{field_name} must be a string.")
    return value


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ObjectStorageLoadExecutionError(f"{field_name} must be a dict.")
    return value


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ObjectStorageLoadExecutionError(f"{field_name} must be a boolean.")
    return value


def _require_supported(value: Any, allowed: tuple[str, ...], field_name: str) -> str:
    value = _require_text(value, field_name)
    if value not in allowed:
        raise ObjectStorageLoadExecutionError(
            f"{field_name} must be one of: {', '.join(allowed)}."
        )
    return value


def _require_string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ObjectStorageLoadExecutionError(f"{field_name} must be a list of strings.")
    return value


def _require_optional_nonnegative_int(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or value < 0:
        raise ObjectStorageLoadExecutionError(
            f"{field_name} must be a non-negative integer."
        )
    return value


def _reject_true(value: bool, field_name: str) -> None:
    if value:
        raise ObjectStorageLoadExecutionError(
            f"{field_name} must remain false in Phase 7CD."
        )


def _stable_id(prefix: str, *parts: str) -> str:
    tokens = [_normalize_token(prefix)]
    tokens.extend(_normalize_token(str(part)) for part in parts)
    raw_id = "-".join(token for token in tokens if token)
    if len(raw_id) <= 140:
        return raw_id
    digest = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:24].upper()
    return f"{tokens[0]}-{digest}"


def _normalize_token(value: str) -> str:
    normalized = _TOKEN_PATTERN.sub("-", value.strip().upper()).strip("-")
    return normalized or "UNSPECIFIED"
