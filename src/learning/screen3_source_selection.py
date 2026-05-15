"""Phase 7AK Screen 3 source selection metadata.

The records in this module describe source intent for future Screen 3
re-analysis. They validate metadata shape only. They do not load inputs, call
external services, inspect databases, write state, modify dashboard behavior,
or start analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


SCREEN3_SOURCE_MODES = (
    "none",
    "local_staged",
    "local_file",
    "existing_run",
    "object_storage",
    "future_upload",
    "future_em_extract",
)

SOURCE_VALIDATION_STATUSES = (
    "VALID_METADATA_ONLY",
    "INVALID",
    "NO_SOURCE_SELECTED",
    "NEEDS_LOCAL_SOURCE",
    "NEEDS_OBJECT_STORAGE_CONFIG",
    "NEEDS_EXISTING_RUN_REFERENCE",
    "FUTURE_SOURCE_NOT_IMPLEMENTED",
    "EXECUTION_NOT_ALLOWED_IN_THIS_PHASE",
)

EXPECTED_SOURCE_FILE_TYPES = (
    "awr",
    "html",
    "txt",
    "zip",
    "json",
    "xml",
)

OBJECT_STORAGE_CREDENTIAL_MODES = (
    "env",
    "instance_principal",
    "resource_principal",
    "config_file",
    "unknown",
)


class Screen3SourceSelectionError(ValueError):
    """Raised when 7AK source selection metadata is invalid."""


@dataclass(frozen=True)
class LocalSourceReference:
    """Metadata for a local source reference. Existence hints are not checked."""

    local_source_id: str
    staged_file_id: str | None = None
    local_path: str | None = None
    file_name: str | None = None
    expected_file_type: str | None = None
    checksum: str | None = None
    exists_hint: bool | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.local_source_id, "local_source_id")
        _require_optional_string(self.staged_file_id, "staged_file_id")
        _require_optional_string(self.local_path, "local_path")
        _require_optional_string(self.file_name, "file_name")
        _require_optional_string(self.expected_file_type, "expected_file_type")
        if self.expected_file_type is not None:
            _require_supported(
                self.expected_file_type,
                EXPECTED_SOURCE_FILE_TYPES,
                "expected_file_type",
            )
        _require_optional_string(self.checksum, "checksum")
        _require_optional_bool(self.exists_hint, "exists_hint")
        _require_optional_string(self.notes, "notes")
        if not any((self.staged_file_id, self.local_path, self.file_name)):
            raise Screen3SourceSelectionError(
                "local source requires staged_file_id, local_path, or file_name."
            )


@dataclass(frozen=True)
class ObjectStorageSourceReference:
    """Metadata for an object storage source reference."""

    object_source_id: str
    namespace: str
    bucket: str
    object_name: str
    region: str
    compartment_id: str | None = None
    credential_mode: str = "unknown"
    uri: str | None = None
    configured_hint: bool | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.object_source_id, "object_source_id")
        _require_nonempty_string(self.namespace, "namespace")
        _require_nonempty_string(self.bucket, "bucket")
        _require_nonempty_string(self.object_name, "object_name")
        _require_nonempty_string(self.region, "region")
        _require_optional_string(self.compartment_id, "compartment_id")
        _require_supported(
            self.credential_mode,
            OBJECT_STORAGE_CREDENTIAL_MODES,
            "credential_mode",
        )
        _require_optional_string(self.uri, "uri")
        _require_optional_bool(self.configured_hint, "configured_hint")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class ExistingRunSourceReference:
    """Metadata for a prior run source reference. No persistence is inspected."""

    run_source_id: str
    run_id: str | None = None
    awr_id: str | None = None
    dbid: str | None = None
    database_name: str | None = None
    snapshot_label: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.run_source_id, "run_source_id")
        _require_optional_string(self.run_id, "run_id")
        _require_optional_string(self.awr_id, "awr_id")
        _require_optional_string(self.dbid, "dbid")
        _require_optional_string(self.database_name, "database_name")
        _require_optional_string(self.snapshot_label, "snapshot_label")
        _require_optional_string(self.notes, "notes")
        if not any((self.run_id, self.awr_id)):
            raise Screen3SourceSelectionError(
                "existing run source requires run_id or awr_id."
            )


@dataclass(frozen=True)
class FutureEMExtractSourceReference:
    """Placeholder metadata for future Enterprise Manager extract support."""

    em_source_id: str
    extract_id: str | None = None
    extract_format: str | None = None
    em_version: str | None = None
    target_name: str | None = None
    target_type: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.em_source_id, "em_source_id")
        _require_optional_string(self.extract_id, "extract_id")
        _require_optional_string(self.extract_format, "extract_format")
        _require_optional_string(self.em_version, "em_version")
        _require_optional_string(self.target_name, "target_name")
        _require_optional_string(self.target_type, "target_type")
        _require_optional_string(self.notes, "notes")
        if not any((self.extract_id, self.target_name)):
            raise Screen3SourceSelectionError(
                "future EM extract source requires extract_id or target_name."
            )


@dataclass(frozen=True)
class SourceSelection:
    """Selected source mode and source reference metadata."""

    source_selection_id: str
    source_mode: str
    source_label: str | None = None
    local_source: LocalSourceReference | None = None
    object_storage_source: ObjectStorageSourceReference | None = None
    existing_run_source: ExistingRunSourceReference | None = None
    future_em_extract_source: FutureEMExtractSourceReference | None = None
    selected_by_actor_id: str | None = None
    validation_status: str = "NO_SOURCE_SELECTED"
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.source_selection_id, "source_selection_id")
        _require_supported(self.source_mode, SCREEN3_SOURCE_MODES, "source_mode")
        _require_optional_string(self.source_label, "source_label")
        _require_optional_reference(
            self.local_source,
            LocalSourceReference,
            "local_source",
        )
        _require_optional_reference(
            self.object_storage_source,
            ObjectStorageSourceReference,
            "object_storage_source",
        )
        _require_optional_reference(
            self.existing_run_source,
            ExistingRunSourceReference,
            "existing_run_source",
        )
        _require_optional_reference(
            self.future_em_extract_source,
            FutureEMExtractSourceReference,
            "future_em_extract_source",
        )
        _require_optional_string(self.selected_by_actor_id, "selected_by_actor_id")
        _require_supported(
            self.validation_status,
            SOURCE_VALIDATION_STATUSES,
            "validation_status",
        )
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class SourceValidationResult:
    """Metadata result for source validation in Phase 7AK."""

    validation_id: str
    source_selection_id: str
    valid: bool
    validation_status: str
    source_mode: str
    denied_reasons: list[str]
    warnings: list[str]
    required_next_steps: list[str]
    can_execute: bool = False
    execution_blocked: bool = True
    object_storage_call_performed: bool = False
    local_file_read_performed: bool = False
    db_lookup_performed: bool = False
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.validation_id, "validation_id")
        _require_nonempty_string(self.source_selection_id, "source_selection_id")
        _require_bool(self.valid, "valid")
        _require_supported(
            self.validation_status,
            SOURCE_VALIDATION_STATUSES,
            "validation_status",
        )
        _require_supported(self.source_mode, SCREEN3_SOURCE_MODES, "source_mode")
        _require_list_of_strings(self.denied_reasons, "denied_reasons")
        _require_list_of_strings(self.warnings, "warnings")
        _require_list_of_strings(self.required_next_steps, "required_next_steps")
        _require_bool(self.can_execute, "can_execute")
        _require_bool(self.execution_blocked, "execution_blocked")
        _require_bool(
            self.object_storage_call_performed,
            "object_storage_call_performed",
        )
        _require_bool(self.local_file_read_performed, "local_file_read_performed")
        _require_bool(self.db_lookup_performed, "db_lookup_performed")
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")
        if self.can_execute:
            raise Screen3SourceSelectionError(
                "can_execute must remain false in Phase 7AK."
            )
        if not self.execution_blocked:
            raise Screen3SourceSelectionError(
                "execution_blocked must remain true in Phase 7AK."
            )
        if self.object_storage_call_performed:
            raise Screen3SourceSelectionError(
                "object_storage_call_performed must remain false in Phase 7AK."
            )
        if self.local_file_read_performed:
            raise Screen3SourceSelectionError(
                "local_file_read_performed must remain false in Phase 7AK."
            )
        if self.db_lookup_performed:
            raise Screen3SourceSelectionError(
                "db_lookup_performed must remain false in Phase 7AK."
            )


def create_source_selection_id(source_mode: str, source_label: str | None = None) -> str:
    """Create a deterministic source selection id."""

    _require_supported(source_mode, SCREEN3_SOURCE_MODES, "source_mode")
    _require_optional_string(source_label, "source_label")
    label_token = source_label or "NO-SOURCE"
    return (
        "SCREEN3-SOURCE-SELECTION-"
        f"{_normalize_token(source_mode)}-"
        f"{_normalize_token(label_token)}"
    )


def create_local_source_id(
    file_name: str | None = None,
    local_path: str | None = None,
    staged_file_id: str | None = None,
) -> str:
    """Create a deterministic local source id."""

    _require_optional_string(file_name, "file_name")
    _require_optional_string(local_path, "local_path")
    _require_optional_string(staged_file_id, "staged_file_id")
    token = file_name or local_path or staged_file_id or "NO-LOCAL-SOURCE"
    return f"LOCAL-SOURCE-{_normalize_token(token)}"


def create_object_source_id(
    namespace: str | None = None,
    bucket: str | None = None,
    object_name: str | None = None,
    region: str | None = None,
) -> str:
    """Create a deterministic object storage source id."""

    _require_optional_string(namespace, "namespace")
    _require_optional_string(bucket, "bucket")
    _require_optional_string(object_name, "object_name")
    _require_optional_string(region, "region")
    return (
        "OBJECT-SOURCE-"
        f"{_normalize_token(namespace or 'NO-NAMESPACE')}-"
        f"{_normalize_token(bucket or 'NO-BUCKET')}-"
        f"{_normalize_token(object_name or 'NO-OBJECT')}-"
        f"{_normalize_token(region or 'NO-REGION')}"
    )


def create_existing_run_source_id(
    run_id: str | None = None,
    awr_id: str | None = None,
    dbid: str | None = None,
) -> str:
    """Create a deterministic existing run source id."""

    _require_optional_string(run_id, "run_id")
    _require_optional_string(awr_id, "awr_id")
    _require_optional_string(dbid, "dbid")
    token = run_id or awr_id or dbid or "NO-RUN-SOURCE"
    return f"EXISTING-RUN-SOURCE-{_normalize_token(token)}"


def create_future_em_extract_source_id(
    extract_id: str | None = None,
    target_name: str | None = None,
) -> str:
    """Create a deterministic future EM extract source id."""

    _require_optional_string(extract_id, "extract_id")
    _require_optional_string(target_name, "target_name")
    token = extract_id or target_name or "NO-EM-SOURCE"
    return f"FUTURE-EM-EXTRACT-SOURCE-{_normalize_token(token)}"


def create_source_validation_id(source_selection_id: str) -> str:
    """Create a deterministic source validation id."""

    _require_nonempty_string(source_selection_id, "source_selection_id")
    return f"SOURCE-VALIDATION-{_normalize_token(source_selection_id)}"


def validate_local_source_reference(
    ref: LocalSourceReference,
) -> LocalSourceReference:
    """Validate local source metadata only."""

    if not isinstance(ref, LocalSourceReference):
        raise Screen3SourceSelectionError(
            "ref must be a LocalSourceReference instance."
        )
    ref.__post_init__()
    return ref


def validate_object_storage_source_reference(
    ref: ObjectStorageSourceReference,
) -> ObjectStorageSourceReference:
    """Validate object storage source metadata only."""

    if not isinstance(ref, ObjectStorageSourceReference):
        raise Screen3SourceSelectionError(
            "ref must be an ObjectStorageSourceReference instance."
        )
    ref.__post_init__()
    return ref


def validate_existing_run_source_reference(
    ref: ExistingRunSourceReference,
) -> ExistingRunSourceReference:
    """Validate existing run source metadata only."""

    if not isinstance(ref, ExistingRunSourceReference):
        raise Screen3SourceSelectionError(
            "ref must be an ExistingRunSourceReference instance."
        )
    ref.__post_init__()
    return ref


def validate_future_em_extract_source_reference(
    ref: FutureEMExtractSourceReference,
) -> FutureEMExtractSourceReference:
    """Validate future EM extract placeholder metadata only."""

    if not isinstance(ref, FutureEMExtractSourceReference):
        raise Screen3SourceSelectionError(
            "ref must be a FutureEMExtractSourceReference instance."
        )
    ref.__post_init__()
    return ref


def validate_source_selection(selection: SourceSelection) -> SourceSelection:
    """Validate source selection metadata only."""

    if not isinstance(selection, SourceSelection):
        raise Screen3SourceSelectionError(
            "selection must be a SourceSelection instance."
        )
    selection.__post_init__()
    if selection.source_mode in ("local_staged", "local_file"):
        if selection.local_source is None:
            raise Screen3SourceSelectionError(
                f"{selection.source_mode} requires local_source."
            )
        validate_local_source_reference(selection.local_source)
    elif selection.source_mode == "object_storage":
        if selection.object_storage_source is None:
            raise Screen3SourceSelectionError(
                "object_storage requires object_storage_source."
            )
        validate_object_storage_source_reference(selection.object_storage_source)
    elif selection.source_mode == "existing_run":
        if selection.existing_run_source is None:
            raise Screen3SourceSelectionError(
                "existing_run requires existing_run_source."
            )
        validate_existing_run_source_reference(selection.existing_run_source)
    elif selection.source_mode == "future_em_extract":
        if selection.future_em_extract_source is None:
            raise Screen3SourceSelectionError(
                "future_em_extract requires future_em_extract_source."
            )
        validate_future_em_extract_source_reference(
            selection.future_em_extract_source
        )
    return selection


def evaluate_source_selection(selection: SourceSelection) -> SourceValidationResult:
    """Evaluate source metadata without permitting execution."""

    if not isinstance(selection, SourceSelection):
        raise Screen3SourceSelectionError(
            "selection must be a SourceSelection instance."
        )
    selection.__post_init__()

    denied_reasons: list[str] = ["execution is not allowed in Phase 7AK"]
    warnings: list[str] = []
    required_next_steps: list[str] = ["validate source during a future execution phase"]
    valid = False
    status = "INVALID"

    validation_error: str | None = None
    try:
        validate_source_selection(selection)
    except Screen3SourceSelectionError as exc:
        validation_error = str(exc)

    if selection.source_mode == "none":
        status = "NO_SOURCE_SELECTED"
        denied_reasons.append("no source selected")
        required_next_steps.append("select a supported source before execution")
    elif validation_error is not None:
        status = _status_for_missing_reference(selection.source_mode)
        denied_reasons.append(validation_error)
        required_next_steps.append("provide required source metadata")
    elif selection.source_mode in ("future_upload", "future_em_extract"):
        status = "FUTURE_SOURCE_NOT_IMPLEMENTED"
        denied_reasons.append(f"{selection.source_mode} is placeholder metadata only")
        required_next_steps.append("wait for the future source implementation phase")
    elif selection.source_mode == "object_storage":
        if selection.object_storage_source and selection.object_storage_source.configured_hint:
            status = "VALID_METADATA_ONLY"
            valid = True
            warnings.append("object storage metadata was not verified externally")
        else:
            status = "NEEDS_OBJECT_STORAGE_CONFIG"
            denied_reasons.append("object storage configuration is not confirmed")
            required_next_steps.append("validate object storage configuration later")
    else:
        status = "VALID_METADATA_ONLY"
        valid = True

    return SourceValidationResult(
        validation_id=create_source_validation_id(selection.source_selection_id),
        source_selection_id=selection.source_selection_id,
        valid=valid,
        validation_status=status,
        source_mode=selection.source_mode,
        denied_reasons=denied_reasons,
        warnings=warnings,
        required_next_steps=required_next_steps,
        can_execute=False,
        execution_blocked=True,
        object_storage_call_performed=False,
        local_file_read_performed=False,
        db_lookup_performed=False,
        created_at=None,
        notes=selection.notes,
    )


def validate_source_validation_result(
    result: SourceValidationResult,
) -> SourceValidationResult:
    """Validate source validation result metadata only."""

    if not isinstance(result, SourceValidationResult):
        raise Screen3SourceSelectionError(
            "result must be a SourceValidationResult instance."
        )
    result.__post_init__()
    return result


def source_selection_to_dict(selection: SourceSelection) -> dict[str, Any]:
    """Serialize source selection metadata."""

    selection.__post_init__()
    return {
        "source_selection_id": selection.source_selection_id,
        "source_mode": selection.source_mode,
        "source_label": selection.source_label,
        "local_source": (
            local_source_reference_to_dict(selection.local_source)
            if selection.local_source
            else None
        ),
        "object_storage_source": (
            object_storage_source_reference_to_dict(selection.object_storage_source)
            if selection.object_storage_source
            else None
        ),
        "existing_run_source": (
            existing_run_source_reference_to_dict(selection.existing_run_source)
            if selection.existing_run_source
            else None
        ),
        "future_em_extract_source": (
            future_em_extract_source_reference_to_dict(
                selection.future_em_extract_source
            )
            if selection.future_em_extract_source
            else None
        ),
        "selected_by_actor_id": selection.selected_by_actor_id,
        "validation_status": selection.validation_status,
        "created_at": selection.created_at,
        "notes": selection.notes,
    }


def source_selection_from_dict(data: dict[str, Any]) -> SourceSelection:
    """Deserialize source selection metadata."""

    _require_mapping(data, "source_selection")
    local_source_data = data.get("local_source")
    object_source_data = data.get("object_storage_source")
    existing_run_data = data.get("existing_run_source")
    em_source_data = data.get("future_em_extract_source")
    return SourceSelection(
        source_selection_id=data.get("source_selection_id"),
        source_mode=data.get("source_mode"),
        source_label=data.get("source_label"),
        local_source=(
            local_source_reference_from_dict(local_source_data)
            if local_source_data is not None
            else None
        ),
        object_storage_source=(
            object_storage_source_reference_from_dict(object_source_data)
            if object_source_data is not None
            else None
        ),
        existing_run_source=(
            existing_run_source_reference_from_dict(existing_run_data)
            if existing_run_data is not None
            else None
        ),
        future_em_extract_source=(
            future_em_extract_source_reference_from_dict(em_source_data)
            if em_source_data is not None
            else None
        ),
        selected_by_actor_id=data.get("selected_by_actor_id"),
        validation_status=data.get("validation_status", "NO_SOURCE_SELECTED"),
        created_at=data.get("created_at"),
        notes=data.get("notes"),
    )


def source_validation_result_to_dict(result: SourceValidationResult) -> dict[str, Any]:
    """Serialize source validation result metadata."""

    result = validate_source_validation_result(result)
    return {
        "validation_id": result.validation_id,
        "source_selection_id": result.source_selection_id,
        "valid": result.valid,
        "validation_status": result.validation_status,
        "source_mode": result.source_mode,
        "denied_reasons": list(result.denied_reasons),
        "warnings": list(result.warnings),
        "required_next_steps": list(result.required_next_steps),
        "can_execute": result.can_execute,
        "execution_blocked": result.execution_blocked,
        "object_storage_call_performed": result.object_storage_call_performed,
        "local_file_read_performed": result.local_file_read_performed,
        "db_lookup_performed": result.db_lookup_performed,
        "created_at": result.created_at,
        "notes": result.notes,
    }


def source_validation_result_from_dict(data: dict[str, Any]) -> SourceValidationResult:
    """Deserialize source validation result metadata."""

    _require_mapping(data, "source_validation_result")
    return SourceValidationResult(
        validation_id=data.get("validation_id"),
        source_selection_id=data.get("source_selection_id"),
        valid=data.get("valid"),
        validation_status=data.get("validation_status"),
        source_mode=data.get("source_mode"),
        denied_reasons=data.get("denied_reasons", []),
        warnings=data.get("warnings", []),
        required_next_steps=data.get("required_next_steps", []),
        can_execute=data.get("can_execute", False),
        execution_blocked=data.get("execution_blocked", True),
        object_storage_call_performed=data.get("object_storage_call_performed", False),
        local_file_read_performed=data.get("local_file_read_performed", False),
        db_lookup_performed=data.get("db_lookup_performed", False),
        created_at=data.get("created_at"),
        notes=data.get("notes"),
    )


def local_source_reference_to_dict(ref: LocalSourceReference) -> dict[str, Any]:
    """Serialize local source metadata."""

    ref = validate_local_source_reference(ref)
    return {
        "local_source_id": ref.local_source_id,
        "staged_file_id": ref.staged_file_id,
        "local_path": ref.local_path,
        "file_name": ref.file_name,
        "expected_file_type": ref.expected_file_type,
        "checksum": ref.checksum,
        "exists_hint": ref.exists_hint,
        "notes": ref.notes,
    }


def local_source_reference_from_dict(data: dict[str, Any]) -> LocalSourceReference:
    """Deserialize local source metadata."""

    _require_mapping(data, "local_source")
    return LocalSourceReference(
        local_source_id=data.get("local_source_id"),
        staged_file_id=data.get("staged_file_id"),
        local_path=data.get("local_path"),
        file_name=data.get("file_name"),
        expected_file_type=data.get("expected_file_type"),
        checksum=data.get("checksum"),
        exists_hint=data.get("exists_hint"),
        notes=data.get("notes"),
    )


def object_storage_source_reference_to_dict(
    ref: ObjectStorageSourceReference,
) -> dict[str, Any]:
    """Serialize object storage source metadata."""

    ref = validate_object_storage_source_reference(ref)
    return {
        "object_source_id": ref.object_source_id,
        "namespace": ref.namespace,
        "bucket": ref.bucket,
        "object_name": ref.object_name,
        "region": ref.region,
        "compartment_id": ref.compartment_id,
        "credential_mode": ref.credential_mode,
        "uri": ref.uri,
        "configured_hint": ref.configured_hint,
        "notes": ref.notes,
    }


def object_storage_source_reference_from_dict(
    data: dict[str, Any],
) -> ObjectStorageSourceReference:
    """Deserialize object storage source metadata."""

    _require_mapping(data, "object_storage_source")
    return ObjectStorageSourceReference(
        object_source_id=data.get("object_source_id"),
        namespace=data.get("namespace"),
        bucket=data.get("bucket"),
        object_name=data.get("object_name"),
        region=data.get("region"),
        compartment_id=data.get("compartment_id"),
        credential_mode=data.get("credential_mode", "unknown"),
        uri=data.get("uri"),
        configured_hint=data.get("configured_hint"),
        notes=data.get("notes"),
    )


def existing_run_source_reference_to_dict(
    ref: ExistingRunSourceReference,
) -> dict[str, Any]:
    """Serialize existing run source metadata."""

    ref = validate_existing_run_source_reference(ref)
    return {
        "run_source_id": ref.run_source_id,
        "run_id": ref.run_id,
        "awr_id": ref.awr_id,
        "dbid": ref.dbid,
        "database_name": ref.database_name,
        "snapshot_label": ref.snapshot_label,
        "notes": ref.notes,
    }


def existing_run_source_reference_from_dict(
    data: dict[str, Any],
) -> ExistingRunSourceReference:
    """Deserialize existing run source metadata."""

    _require_mapping(data, "existing_run_source")
    return ExistingRunSourceReference(
        run_source_id=data.get("run_source_id"),
        run_id=data.get("run_id"),
        awr_id=data.get("awr_id"),
        dbid=data.get("dbid"),
        database_name=data.get("database_name"),
        snapshot_label=data.get("snapshot_label"),
        notes=data.get("notes"),
    )


def future_em_extract_source_reference_to_dict(
    ref: FutureEMExtractSourceReference,
) -> dict[str, Any]:
    """Serialize future EM extract placeholder metadata."""

    ref = validate_future_em_extract_source_reference(ref)
    return {
        "em_source_id": ref.em_source_id,
        "extract_id": ref.extract_id,
        "extract_format": ref.extract_format,
        "em_version": ref.em_version,
        "target_name": ref.target_name,
        "target_type": ref.target_type,
        "notes": ref.notes,
    }


def future_em_extract_source_reference_from_dict(
    data: dict[str, Any],
) -> FutureEMExtractSourceReference:
    """Deserialize future EM extract placeholder metadata."""

    _require_mapping(data, "future_em_extract_source")
    return FutureEMExtractSourceReference(
        em_source_id=data.get("em_source_id"),
        extract_id=data.get("extract_id"),
        extract_format=data.get("extract_format"),
        em_version=data.get("em_version"),
        target_name=data.get("target_name"),
        target_type=data.get("target_type"),
        notes=data.get("notes"),
    )


def default_no_source_selection(notes: str | None = None) -> SourceSelection:
    """Create a deterministic placeholder for no selected source."""

    _require_optional_string(notes, "notes")
    return SourceSelection(
        source_selection_id=create_source_selection_id("none", "NO-SOURCE"),
        source_mode="none",
        source_label="No source selected",
        validation_status="NO_SOURCE_SELECTED",
        notes=notes,
    )


def _status_for_missing_reference(source_mode: str) -> str:
    if source_mode in ("local_staged", "local_file"):
        return "NEEDS_LOCAL_SOURCE"
    if source_mode == "object_storage":
        return "NEEDS_OBJECT_STORAGE_CONFIG"
    if source_mode == "existing_run":
        return "NEEDS_EXISTING_RUN_REFERENCE"
    if source_mode in ("future_upload", "future_em_extract"):
        return "FUTURE_SOURCE_NOT_IMPLEMENTED"
    return "INVALID"


def _normalize_token(value: str) -> str:
    _require_nonempty_string(value, "value")
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().upper())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "NONE"


def _require_nonempty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Screen3SourceSelectionError(f"{field_name} is required.")
    return value


def _require_optional_string(value: Any, field_name: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise Screen3SourceSelectionError(
            f"{field_name} must be a string or None."
        )
    return value


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> str:
    if not isinstance(value, str) or value not in supported:
        raise Screen3SourceSelectionError(f"Unsupported {field_name}: {value!r}.")
    return value


def _require_bool(value: Any, field_name: str) -> bool:
    if type(value) is not bool:
        raise Screen3SourceSelectionError(f"{field_name} must be boolean.")
    return value


def _require_optional_bool(value: Any, field_name: str) -> bool | None:
    if value is not None and type(value) is not bool:
        raise Screen3SourceSelectionError(
            f"{field_name} must be boolean or None."
        )
    return value


def _require_list_of_strings(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise Screen3SourceSelectionError(
            f"{field_name} must be a list of strings."
        )
    return value


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise Screen3SourceSelectionError(f"{field_name} must be a dictionary.")
    return value


def _require_optional_reference(value: Any, expected_type: type, field_name: str) -> Any:
    if value is not None and not isinstance(value, expected_type):
        raise Screen3SourceSelectionError(
            f"{field_name} must be a {expected_type.__name__} instance or None."
        )
    return value
