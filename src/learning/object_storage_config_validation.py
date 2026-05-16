"""Phase 7BS object storage configuration metadata validation.

The records in this module validate object storage configuration metadata
shape only. They do not import OCI, call object storage, validate real
credentials, read config files, list buckets, download objects, query
databases, invoke run_analysis.py, or perform Screen 3 handoff.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


OBJECT_STORAGE_CREDENTIAL_MODES = (
    "env",
    "instance_principal",
    "resource_principal",
    "config_file",
    "unknown",
)

OBJECT_STORAGE_CONFIG_VALIDATION_STATUSES = (
    "VALID_METADATA_ONLY",
    "INVALID",
    "MISSING_NAMESPACE",
    "MISSING_BUCKET",
    "MISSING_OBJECT_OR_PREFIX",
    "MISSING_REGION",
    "MISSING_COMPARTMENT",
    "UNSUPPORTED_CREDENTIAL_MODE",
    "EXECUTION_NOT_ALLOWED_IN_THIS_PHASE",
)

SECRET_FIELD_NAMES = (
    "password",
    "secret",
    "token",
    "api_key",
    "private_key",
    "key_file_content",
)


class ObjectStorageConfigValidationError(ValueError):
    """Raised when Phase 7BS object storage config metadata is invalid."""


@dataclass(frozen=True)
class ObjectStorageConfiguration:
    """Metadata-only object storage configuration values."""

    config_id: str
    namespace: str | None = None
    bucket: str | None = None
    object_name: str | None = None
    prefix: str | None = None
    region: str | None = None
    compartment_id: str | None = None
    credential_mode: str = "unknown"
    profile_name: str | None = None
    uri: str | None = None
    configured_hint: bool = False
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_no_secret_attributes(self)
        _require_nonempty_string(self.config_id, "config_id")
        _require_optional_string(self.namespace, "namespace")
        _require_optional_string(self.bucket, "bucket")
        _require_optional_string(self.object_name, "object_name")
        _require_optional_string(self.prefix, "prefix")
        _require_optional_string(self.region, "region")
        _require_optional_string(self.compartment_id, "compartment_id")
        _require_nonempty_string(self.credential_mode, "credential_mode")
        _require_optional_string(self.profile_name, "profile_name")
        _require_optional_string(self.uri, "uri")
        _require_bool(self.configured_hint, "configured_hint")
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class ObjectStorageConfigurationValidation:
    """Validation result for object storage metadata only."""

    validation_id: str
    config_id: str
    valid_metadata: bool
    validation_status: str
    namespace_present: bool
    bucket_present: bool
    object_or_prefix_present: bool
    region_present: bool
    compartment_present: bool
    credential_mode_supported: bool
    credential_validation_performed: bool
    object_storage_call_performed: bool
    bucket_list_performed: bool
    object_download_performed: bool
    can_attempt_future_access: bool
    execution_blocked: bool
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.validation_id, "validation_id")
        _require_nonempty_string(self.config_id, "config_id")
        _require_bool(self.valid_metadata, "valid_metadata")
        _require_supported(
            self.validation_status,
            OBJECT_STORAGE_CONFIG_VALIDATION_STATUSES,
            "validation_status",
        )
        _require_bool(self.namespace_present, "namespace_present")
        _require_bool(self.bucket_present, "bucket_present")
        _require_bool(self.object_or_prefix_present, "object_or_prefix_present")
        _require_bool(self.region_present, "region_present")
        _require_bool(self.compartment_present, "compartment_present")
        _require_bool(
            self.credential_mode_supported,
            "credential_mode_supported",
        )
        _require_bool(
            self.credential_validation_performed,
            "credential_validation_performed",
        )
        _require_bool(
            self.object_storage_call_performed,
            "object_storage_call_performed",
        )
        _require_bool(self.bucket_list_performed, "bucket_list_performed")
        _require_bool(
            self.object_download_performed,
            "object_download_performed",
        )
        _require_bool(
            self.can_attempt_future_access,
            "can_attempt_future_access",
        )
        _require_bool(self.execution_blocked, "execution_blocked")
        _require_list_of_strings(self.denied_reasons, "denied_reasons")
        _require_list_of_strings(self.warnings, "warnings")
        _require_list_of_strings(
            self.required_next_steps,
            "required_next_steps",
        )
        _require_optional_string(self.notes, "notes")
        if self.credential_validation_performed:
            raise ObjectStorageConfigValidationError(
                "credential_validation_performed must remain false in Phase 7BS."
            )
        if self.object_storage_call_performed:
            raise ObjectStorageConfigValidationError(
                "object_storage_call_performed must remain false in Phase 7BS."
            )
        if self.bucket_list_performed:
            raise ObjectStorageConfigValidationError(
                "bucket_list_performed must remain false in Phase 7BS."
            )
        if self.object_download_performed:
            raise ObjectStorageConfigValidationError(
                "object_download_performed must remain false in Phase 7BS."
            )
        if not self.execution_blocked:
            raise ObjectStorageConfigValidationError(
                "execution_blocked must remain true in Phase 7BS."
            )


@dataclass(frozen=True)
class ObjectStorageConfigurationSummary:
    """Summary of object storage configuration validation metadata."""

    summary_id: str
    configured_count: int
    valid_metadata_count: int
    incomplete_count: int
    unsupported_credential_count: int
    execution_supported: bool
    handoff_supported: bool
    object_storage_call_performed: bool
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.summary_id, "summary_id")
        _require_nonnegative_int(self.configured_count, "configured_count")
        _require_nonnegative_int(
            self.valid_metadata_count,
            "valid_metadata_count",
        )
        _require_nonnegative_int(self.incomplete_count, "incomplete_count")
        _require_nonnegative_int(
            self.unsupported_credential_count,
            "unsupported_credential_count",
        )
        _require_bool(self.execution_supported, "execution_supported")
        _require_bool(self.handoff_supported, "handoff_supported")
        _require_bool(
            self.object_storage_call_performed,
            "object_storage_call_performed",
        )
        _require_list_of_strings(self.warnings, "warnings")
        _require_list_of_strings(self.required_next_steps, "required_next_steps")
        _require_optional_string(self.notes, "notes")
        if self.valid_metadata_count > self.configured_count:
            raise ObjectStorageConfigValidationError(
                "valid_metadata_count cannot exceed configured_count."
            )
        if self.incomplete_count > self.configured_count:
            raise ObjectStorageConfigValidationError(
                "incomplete_count cannot exceed configured_count."
            )
        if self.unsupported_credential_count > self.configured_count:
            raise ObjectStorageConfigValidationError(
                "unsupported_credential_count cannot exceed configured_count."
            )
        if self.execution_supported:
            raise ObjectStorageConfigValidationError(
                "execution_supported must remain false in Phase 7BS."
            )
        if self.handoff_supported:
            raise ObjectStorageConfigValidationError(
                "handoff_supported must remain false in Phase 7BS."
            )
        if self.object_storage_call_performed:
            raise ObjectStorageConfigValidationError(
                "object_storage_call_performed must remain false in Phase 7BS."
            )


def create_object_storage_config_id(
    namespace: str | None = None,
    bucket: str | None = None,
    object_name: str | None = None,
    prefix: str | None = None,
    region: str | None = None,
) -> str:
    """Create a deterministic object storage config id."""

    _require_optional_string(namespace, "namespace")
    _require_optional_string(bucket, "bucket")
    _require_optional_string(object_name, "object_name")
    _require_optional_string(prefix, "prefix")
    _require_optional_string(region, "region")
    return (
        "OBJECT-STORAGE-CONFIG-"
        f"{_normalize_token(namespace or 'NO-NAMESPACE')}-"
        f"{_normalize_token(bucket or 'NO-BUCKET')}-"
        f"{_normalize_token(object_name or prefix or 'NO-OBJECT-OR-PREFIX')}-"
        f"{_normalize_token(region or 'NO-REGION')}"
    )


def create_object_storage_config_validation_id(config_id: str) -> str:
    """Create a deterministic object storage config validation id."""

    _require_nonempty_string(config_id, "config_id")
    return f"OBJECT-STORAGE-CONFIG-VALIDATION-{_normalize_token(config_id)}"


def create_object_storage_config_summary_id(config_count: int) -> str:
    """Create a deterministic object storage config summary id."""

    _require_nonnegative_int(config_count, "config_count")
    return f"OBJECT-STORAGE-CONFIG-SUMMARY-COUNT-{config_count}"


def validate_object_storage_configuration(
    config: ObjectStorageConfiguration,
) -> ObjectStorageConfiguration:
    """Validate object storage configuration metadata shape only."""

    if not isinstance(config, ObjectStorageConfiguration):
        raise ObjectStorageConfigValidationError(
            "config must be an ObjectStorageConfiguration instance."
        )
    config.__post_init__()
    _require_supported(
        config.credential_mode,
        OBJECT_STORAGE_CREDENTIAL_MODES,
        "credential_mode",
    )
    return config


def evaluate_object_storage_configuration(
    config: ObjectStorageConfiguration,
) -> ObjectStorageConfigurationValidation:
    """Evaluate object storage metadata without performing object storage access."""

    if not isinstance(config, ObjectStorageConfiguration):
        raise ObjectStorageConfigValidationError(
            "config must be an ObjectStorageConfiguration instance."
        )
    config.__post_init__()
    namespace_present = _has_text(config.namespace)
    bucket_present = _has_text(config.bucket)
    object_or_prefix_present = _has_text(config.object_name) or _has_text(config.prefix)
    region_present = _has_text(config.region)
    compartment_present = _has_text(config.compartment_id)
    credential_mode_supported = config.credential_mode in OBJECT_STORAGE_CREDENTIAL_MODES

    denied_reasons = ["execution is not allowed in Phase 7BS"]
    warnings = [
        "Object storage configuration validation is metadata only.",
        "No credential validation is performed.",
        "No object storage call is made.",
    ]
    required_next_steps = [
        "Perform real object storage validation in a future execution phase.",
    ]
    status = "VALID_METADATA_ONLY"
    valid_metadata = True

    if not namespace_present:
        status = "MISSING_NAMESPACE"
        valid_metadata = False
        denied_reasons.append("namespace is required")
        required_next_steps.append("provide object storage namespace metadata")
    elif not bucket_present:
        status = "MISSING_BUCKET"
        valid_metadata = False
        denied_reasons.append("bucket is required")
        required_next_steps.append("provide bucket metadata")
    elif not object_or_prefix_present:
        status = "MISSING_OBJECT_OR_PREFIX"
        valid_metadata = False
        denied_reasons.append("object_name or prefix is required")
        required_next_steps.append("provide object name or prefix metadata")
    elif not region_present:
        status = "MISSING_REGION"
        valid_metadata = False
        denied_reasons.append("region is required")
        required_next_steps.append("provide region metadata")
    elif not compartment_present:
        status = "MISSING_COMPARTMENT"
        valid_metadata = False
        denied_reasons.append("compartment_id is required")
        required_next_steps.append("provide compartment metadata")
    elif not credential_mode_supported:
        status = "UNSUPPORTED_CREDENTIAL_MODE"
        valid_metadata = False
        denied_reasons.append("credential_mode is unsupported")
        required_next_steps.append("choose a metadata-supported credential mode")

    return ObjectStorageConfigurationValidation(
        validation_id=create_object_storage_config_validation_id(config.config_id),
        config_id=config.config_id,
        valid_metadata=valid_metadata,
        validation_status=status,
        namespace_present=namespace_present,
        bucket_present=bucket_present,
        object_or_prefix_present=object_or_prefix_present,
        region_present=region_present,
        compartment_present=compartment_present,
        credential_mode_supported=credential_mode_supported,
        credential_validation_performed=False,
        object_storage_call_performed=False,
        bucket_list_performed=False,
        object_download_performed=False,
        can_attempt_future_access=valid_metadata and credential_mode_supported,
        execution_blocked=True,
        denied_reasons=denied_reasons,
        warnings=warnings,
        required_next_steps=required_next_steps,
        notes=config.notes,
    )


def validate_object_storage_configuration_validation(
    validation: ObjectStorageConfigurationValidation,
) -> ObjectStorageConfigurationValidation:
    """Validate object storage configuration validation metadata."""

    if not isinstance(validation, ObjectStorageConfigurationValidation):
        raise ObjectStorageConfigValidationError(
            "validation must be an ObjectStorageConfigurationValidation instance."
        )
    validation.__post_init__()
    return validation


def build_object_storage_configuration_summary(
    validations: list[ObjectStorageConfigurationValidation],
) -> ObjectStorageConfigurationSummary:
    """Build a summary from object storage metadata validation results."""

    if not isinstance(validations, list):
        raise ObjectStorageConfigValidationError("validations must be a list.")
    normalized_validations = [
        validate_object_storage_configuration_validation(validation)
        for validation in validations
    ]
    config_count = len(normalized_validations)
    return ObjectStorageConfigurationSummary(
        summary_id=create_object_storage_config_summary_id(config_count),
        configured_count=config_count,
        valid_metadata_count=sum(
            1
            for validation in normalized_validations
            if validation.valid_metadata
        ),
        incomplete_count=sum(
            1
            for validation in normalized_validations
            if not validation.valid_metadata
            and validation.validation_status != "UNSUPPORTED_CREDENTIAL_MODE"
        ),
        unsupported_credential_count=sum(
            1
            for validation in normalized_validations
            if validation.validation_status == "UNSUPPORTED_CREDENTIAL_MODE"
        ),
        execution_supported=False,
        handoff_supported=False,
        object_storage_call_performed=False,
        warnings=[
            "Summary is metadata-only; no object storage call is made.",
            "Credential validation is not performed in Phase 7BS.",
        ],
        required_next_steps=[
            "Keep execution blocked until a future source access phase.",
            "Keep Screen 3 handoff deferred to future Phase 7BT.",
        ],
        notes=None,
    )


def validate_object_storage_configuration_summary(
    summary: ObjectStorageConfigurationSummary,
) -> ObjectStorageConfigurationSummary:
    """Validate an object storage configuration summary metadata record."""

    if not isinstance(summary, ObjectStorageConfigurationSummary):
        raise ObjectStorageConfigValidationError(
            "summary must be an ObjectStorageConfigurationSummary instance."
        )
    summary.__post_init__()
    return summary


def object_storage_configuration_to_dict(
    config: ObjectStorageConfiguration,
) -> dict[str, Any]:
    """Serialize object storage configuration metadata."""

    config = validate_object_storage_configuration(config)
    return {
        "config_id": config.config_id,
        "namespace": config.namespace,
        "bucket": config.bucket,
        "object_name": config.object_name,
        "prefix": config.prefix,
        "region": config.region,
        "compartment_id": config.compartment_id,
        "credential_mode": config.credential_mode,
        "profile_name": config.profile_name,
        "uri": config.uri,
        "configured_hint": config.configured_hint,
        "created_at": config.created_at,
        "notes": config.notes,
    }


def object_storage_configuration_from_dict(
    data: dict[str, Any],
) -> ObjectStorageConfiguration:
    """Deserialize object storage configuration metadata."""

    _require_mapping(data, "object_storage_configuration")
    _reject_secret_fields(data)
    return ObjectStorageConfiguration(
        config_id=data.get("config_id"),
        namespace=data.get("namespace"),
        bucket=data.get("bucket"),
        object_name=data.get("object_name"),
        prefix=data.get("prefix"),
        region=data.get("region"),
        compartment_id=data.get("compartment_id"),
        credential_mode=data.get("credential_mode", "unknown"),
        profile_name=data.get("profile_name"),
        uri=data.get("uri"),
        configured_hint=data.get("configured_hint", False),
        created_at=data.get("created_at"),
        notes=data.get("notes"),
    )


def object_storage_configuration_validation_to_dict(
    validation: ObjectStorageConfigurationValidation,
) -> dict[str, Any]:
    """Serialize object storage configuration validation metadata."""

    validation = validate_object_storage_configuration_validation(validation)
    return {
        "validation_id": validation.validation_id,
        "config_id": validation.config_id,
        "valid_metadata": validation.valid_metadata,
        "validation_status": validation.validation_status,
        "namespace_present": validation.namespace_present,
        "bucket_present": validation.bucket_present,
        "object_or_prefix_present": validation.object_or_prefix_present,
        "region_present": validation.region_present,
        "compartment_present": validation.compartment_present,
        "credential_mode_supported": validation.credential_mode_supported,
        "credential_validation_performed": (
            validation.credential_validation_performed
        ),
        "object_storage_call_performed": validation.object_storage_call_performed,
        "bucket_list_performed": validation.bucket_list_performed,
        "object_download_performed": validation.object_download_performed,
        "can_attempt_future_access": validation.can_attempt_future_access,
        "execution_blocked": validation.execution_blocked,
        "denied_reasons": list(validation.denied_reasons),
        "warnings": list(validation.warnings),
        "required_next_steps": list(validation.required_next_steps),
        "notes": validation.notes,
    }


def object_storage_configuration_validation_from_dict(
    data: dict[str, Any],
) -> ObjectStorageConfigurationValidation:
    """Deserialize object storage configuration validation metadata."""

    _require_mapping(data, "object_storage_configuration_validation")
    return ObjectStorageConfigurationValidation(
        validation_id=data.get("validation_id"),
        config_id=data.get("config_id"),
        valid_metadata=data.get("valid_metadata"),
        validation_status=data.get("validation_status"),
        namespace_present=data.get("namespace_present"),
        bucket_present=data.get("bucket_present"),
        object_or_prefix_present=data.get("object_or_prefix_present"),
        region_present=data.get("region_present"),
        compartment_present=data.get("compartment_present"),
        credential_mode_supported=data.get("credential_mode_supported"),
        credential_validation_performed=data.get(
            "credential_validation_performed",
            False,
        ),
        object_storage_call_performed=data.get(
            "object_storage_call_performed",
            False,
        ),
        bucket_list_performed=data.get("bucket_list_performed", False),
        object_download_performed=data.get("object_download_performed", False),
        can_attempt_future_access=data.get("can_attempt_future_access"),
        execution_blocked=data.get("execution_blocked", True),
        denied_reasons=data.get("denied_reasons", []),
        warnings=data.get("warnings", []),
        required_next_steps=data.get("required_next_steps", []),
        notes=data.get("notes"),
    )


def object_storage_configuration_summary_to_dict(
    summary: ObjectStorageConfigurationSummary,
) -> dict[str, Any]:
    """Serialize object storage configuration summary metadata."""

    summary = validate_object_storage_configuration_summary(summary)
    return {
        "summary_id": summary.summary_id,
        "configured_count": summary.configured_count,
        "valid_metadata_count": summary.valid_metadata_count,
        "incomplete_count": summary.incomplete_count,
        "unsupported_credential_count": summary.unsupported_credential_count,
        "execution_supported": summary.execution_supported,
        "handoff_supported": summary.handoff_supported,
        "object_storage_call_performed": summary.object_storage_call_performed,
        "warnings": list(summary.warnings),
        "required_next_steps": list(summary.required_next_steps),
        "notes": summary.notes,
    }


def object_storage_configuration_summary_from_dict(
    data: dict[str, Any],
) -> ObjectStorageConfigurationSummary:
    """Deserialize object storage configuration summary metadata."""

    _require_mapping(data, "object_storage_configuration_summary")
    return ObjectStorageConfigurationSummary(
        summary_id=data.get("summary_id"),
        configured_count=data.get("configured_count"),
        valid_metadata_count=data.get("valid_metadata_count"),
        incomplete_count=data.get("incomplete_count"),
        unsupported_credential_count=data.get("unsupported_credential_count"),
        execution_supported=data.get("execution_supported", False),
        handoff_supported=data.get("handoff_supported", False),
        object_storage_call_performed=data.get(
            "object_storage_call_performed",
            False,
        ),
        warnings=data.get("warnings", []),
        required_next_steps=data.get("required_next_steps", []),
        notes=data.get("notes"),
    )


def default_object_storage_configuration(
    notes: str | None = None,
) -> ObjectStorageConfiguration:
    """Create an empty metadata-only object storage configuration placeholder."""

    _require_optional_string(notes, "notes")
    return ObjectStorageConfiguration(
        config_id=create_object_storage_config_id(),
        credential_mode="unknown",
        configured_hint=False,
        notes=notes,
    )


def _normalize_token(value: str) -> str:
    _require_nonempty_string(value, "value")
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().upper())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "NONE"


def _has_text(value: str | None) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require_no_secret_attributes(config: ObjectStorageConfiguration) -> None:
    for field_name in SECRET_FIELD_NAMES:
        if hasattr(config, field_name):
            raise ObjectStorageConfigValidationError(
                f"Secret field is not allowed: {field_name}."
            )


def _reject_secret_fields(data: dict[str, Any]) -> None:
    for field_name in SECRET_FIELD_NAMES:
        if field_name in data:
            raise ObjectStorageConfigValidationError(
                f"Secret field is not allowed: {field_name}."
            )


def _require_nonempty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ObjectStorageConfigValidationError(f"{field_name} is required.")
    return value


def _require_optional_string(value: Any, field_name: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise ObjectStorageConfigValidationError(
            f"{field_name} must be a string or None."
        )
    return value


def _require_supported(
    value: Any,
    supported: tuple[str, ...],
    field_name: str,
) -> str:
    if not isinstance(value, str) or value not in supported:
        raise ObjectStorageConfigValidationError(
            f"Unsupported {field_name}: {value!r}."
        )
    return value


def _require_bool(value: Any, field_name: str) -> bool:
    if type(value) is not bool:
        raise ObjectStorageConfigValidationError(
            f"{field_name} must be boolean."
        )
    return value


def _require_nonnegative_int(value: Any, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise ObjectStorageConfigValidationError(
            f"{field_name} must be a non-negative integer."
        )
    return value


def _require_list_of_strings(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str)
        for item in value
    ):
        raise ObjectStorageConfigValidationError(
            f"{field_name} must be a list of strings."
        )
    return value


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ObjectStorageConfigValidationError(f"{field_name} must be a mapping.")
    return value
