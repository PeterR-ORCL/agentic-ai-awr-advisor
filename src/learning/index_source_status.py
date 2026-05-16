"""Phase 7BR dashboard index source status metadata.

The records in this module describe preview-only readiness status for index
source modes. They validate metadata shape only. They do not read files, check
local paths, call object storage, query databases, invoke run_analysis.py, or
perform Screen 3 handoff.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.learning.index_source_mode_entry import (
    INDEX_SOURCE_DISPLAY_NAMES,
    INDEX_SOURCE_MODES,
)


SOURCE_MODE_STATUSES = (
    "preview_only",
    "ready_metadata_only",
    "needs_configuration",
    "needs_validation",
    "future_not_implemented",
    "blocked",
    "unknown",
)

SOURCE_MODE_READINESS_LEVELS = (
    "ready_metadata_only",
    "needs_configuration",
    "needs_validation",
    "future",
    "blocked",
    "unknown",
)

_SOURCE_MODE_STATUS_LABELS = {
    "preview_only": "Preview only",
    "ready_metadata_only": "Ready metadata only",
    "needs_configuration": "Needs configuration",
    "needs_validation": "Needs validation",
    "future_not_implemented": "Future not implemented",
    "blocked": "Blocked",
    "unknown": "Unknown",
}


class IndexSourceStatusError(ValueError):
    """Raised when Phase 7BR index source status metadata is invalid."""


@dataclass(frozen=True)
class SourceModeStatus:
    """Preview-only readiness metadata for one index source mode."""

    source_mode: str
    display_name: str
    status: str
    status_label: str
    readiness_level: str
    configured_hint: bool
    available_hint: bool
    requires_configuration: bool
    requires_validation: bool
    execution_supported: bool
    handoff_supported: bool
    source_access_performed: bool
    file_read_performed: bool
    object_storage_call_performed: bool
    db_lookup_performed: bool
    run_analysis_called: bool
    future_phase: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_supported_source_mode(self.source_mode)
        _require_nonempty_string(self.display_name, "display_name")
        _require_supported(self.status, SOURCE_MODE_STATUSES, "status")
        _require_nonempty_string(self.status_label, "status_label")
        _require_supported(
            self.readiness_level,
            SOURCE_MODE_READINESS_LEVELS,
            "readiness_level",
        )
        _require_bool(self.configured_hint, "configured_hint")
        _require_bool(self.available_hint, "available_hint")
        _require_bool(self.requires_configuration, "requires_configuration")
        _require_bool(self.requires_validation, "requires_validation")
        _require_bool(self.execution_supported, "execution_supported")
        _require_bool(self.handoff_supported, "handoff_supported")
        _require_bool(self.source_access_performed, "source_access_performed")
        _require_bool(self.file_read_performed, "file_read_performed")
        _require_bool(
            self.object_storage_call_performed,
            "object_storage_call_performed",
        )
        _require_bool(self.db_lookup_performed, "db_lookup_performed")
        _require_bool(self.run_analysis_called, "run_analysis_called")
        _require_optional_string(self.future_phase, "future_phase")
        _require_optional_string(self.notes, "notes")
        if self.source_access_performed:
            raise IndexSourceStatusError(
                "source_access_performed must remain false in Phase 7BR."
            )
        if self.file_read_performed:
            raise IndexSourceStatusError(
                "file_read_performed must remain false in Phase 7BR."
            )
        if self.object_storage_call_performed:
            raise IndexSourceStatusError(
                "object_storage_call_performed must remain false in Phase 7BR."
            )
        if self.db_lookup_performed:
            raise IndexSourceStatusError(
                "db_lookup_performed must remain false in Phase 7BR."
            )
        if self.run_analysis_called:
            raise IndexSourceStatusError(
                "run_analysis_called must remain false in Phase 7BR."
            )
        if self.execution_supported:
            raise IndexSourceStatusError(
                "execution_supported must remain false in Phase 7BR."
            )
        if self.handoff_supported:
            raise IndexSourceStatusError(
                "handoff_supported must remain false in Phase 7BR."
            )


@dataclass(frozen=True)
class SourceModeStatusSummary:
    """Summary of preview-only source status metadata for the index."""

    summary_id: str
    source_count: int
    ready_count: int
    needs_configuration_count: int
    future_count: int
    blocked_count: int
    default_source_mode: str
    statuses: list[SourceModeStatus]
    object_storage_configured_hint: bool
    local_source_available_hint: bool
    future_em_extract_placeholder: bool
    execution_supported: bool
    handoff_supported: bool
    source_access_performed: bool
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.summary_id, "summary_id")
        _require_nonnegative_int(self.source_count, "source_count")
        _require_nonnegative_int(self.ready_count, "ready_count")
        _require_nonnegative_int(
            self.needs_configuration_count,
            "needs_configuration_count",
        )
        _require_nonnegative_int(self.future_count, "future_count")
        _require_nonnegative_int(self.blocked_count, "blocked_count")
        _require_supported_source_mode(self.default_source_mode)
        _require_status_list(self.statuses, "statuses")
        _require_bool(
            self.object_storage_configured_hint,
            "object_storage_configured_hint",
        )
        _require_bool(
            self.local_source_available_hint,
            "local_source_available_hint",
        )
        _require_bool(
            self.future_em_extract_placeholder,
            "future_em_extract_placeholder",
        )
        _require_bool(self.execution_supported, "execution_supported")
        _require_bool(self.handoff_supported, "handoff_supported")
        _require_bool(self.source_access_performed, "source_access_performed")
        _require_list_of_strings(self.warnings, "warnings")
        _require_list_of_strings(self.required_next_steps, "required_next_steps")
        _require_optional_string(self.notes, "notes")
        if self.source_count != len(self.statuses):
            raise IndexSourceStatusError("source_count must match statuses length.")
        if self.ready_count != _count_readiness(
            self.statuses,
            "ready_metadata_only",
        ):
            raise IndexSourceStatusError(
                "ready_count must match ready metadata-only statuses."
            )
        if self.needs_configuration_count != _count_readiness(
            self.statuses,
            "needs_configuration",
        ):
            raise IndexSourceStatusError(
                "needs_configuration_count must match statuses."
            )
        if self.future_count != _count_readiness(self.statuses, "future"):
            raise IndexSourceStatusError("future_count must match statuses.")
        if self.blocked_count != _count_readiness(self.statuses, "blocked"):
            raise IndexSourceStatusError("blocked_count must match statuses.")
        if self.execution_supported:
            raise IndexSourceStatusError(
                "execution_supported must remain false in Phase 7BR."
            )
        if self.handoff_supported:
            raise IndexSourceStatusError(
                "handoff_supported must remain false in Phase 7BR."
            )
        if self.source_access_performed:
            raise IndexSourceStatusError(
                "source_access_performed must remain false in Phase 7BR."
            )
        if not self.future_em_extract_placeholder:
            raise IndexSourceStatusError(
                "future_em_extract_placeholder must remain true in Phase 7BR."
            )


def create_source_mode_status(
    source_mode: str,
    configured_hint: bool = False,
    available_hint: bool = False,
    notes: str | None = None,
) -> SourceModeStatus:
    """Create one deterministic source status without performing source access."""

    _require_supported_source_mode(source_mode)
    _require_bool(configured_hint, "configured_hint")
    _require_bool(available_hint, "available_hint")
    _require_optional_string(notes, "notes")

    status = "needs_validation"
    readiness_level = "needs_validation"
    future_phase = None
    requires_configuration = source_mode == "object_storage"
    requires_validation = source_mode not in ("future_upload", "future_em_extract")

    if source_mode == "local_staged":
        status = "ready_metadata_only"
        readiness_level = "ready_metadata_only"
    elif source_mode == "object_storage" and not configured_hint:
        status = "needs_configuration"
        readiness_level = "needs_configuration"
    elif source_mode == "future_upload":
        status = "future_not_implemented"
        readiness_level = "future"
        future_phase = "future workflow"
    elif source_mode == "future_em_extract":
        status = "future_not_implemented"
        readiness_level = "future"
        future_phase = "Phase 8"

    return SourceModeStatus(
        source_mode=source_mode,
        display_name=INDEX_SOURCE_DISPLAY_NAMES[source_mode],
        status=status,
        status_label=_SOURCE_MODE_STATUS_LABELS[status],
        readiness_level=readiness_level,
        configured_hint=configured_hint,
        available_hint=available_hint,
        requires_configuration=requires_configuration,
        requires_validation=requires_validation,
        execution_supported=False,
        handoff_supported=False,
        source_access_performed=False,
        file_read_performed=False,
        object_storage_call_performed=False,
        db_lookup_performed=False,
        run_analysis_called=False,
        future_phase=future_phase,
        notes=notes,
    )


def create_default_source_mode_statuses(
    object_storage_configured_hint: bool = False,
    local_source_available_hint: bool = False,
) -> list[SourceModeStatus]:
    """Create deterministic source statuses for every index source mode."""

    _require_bool(
        object_storage_configured_hint,
        "object_storage_configured_hint",
    )
    _require_bool(local_source_available_hint, "local_source_available_hint")
    statuses: list[SourceModeStatus] = []
    for source_mode in INDEX_SOURCE_MODES:
        statuses.append(
            create_source_mode_status(
                source_mode,
                configured_hint=(
                    object_storage_configured_hint
                    if source_mode == "object_storage"
                    else False
                ),
                available_hint=(
                    local_source_available_hint
                    if source_mode == "local_staged"
                    else False
                ),
            )
        )
    return statuses


def create_source_mode_status_summary(
    statuses: list[SourceModeStatus] | None = None,
    default_source_mode: str = "local_staged",
    notes: str | None = None,
) -> SourceModeStatusSummary:
    """Create a source status summary without performing source access."""

    _require_supported_source_mode(default_source_mode)
    _require_optional_string(notes, "notes")
    normalized_statuses = (
        create_default_source_mode_statuses()
        if statuses is None
        else list(statuses)
    )
    for status in normalized_statuses:
        validate_source_mode_status(status)
    return SourceModeStatusSummary(
        summary_id="INDEX-SOURCE-MODE-STATUS-SUMMARY-7BR",
        source_count=len(normalized_statuses),
        ready_count=_count_readiness(normalized_statuses, "ready_metadata_only"),
        needs_configuration_count=_count_readiness(
            normalized_statuses,
            "needs_configuration",
        ),
        future_count=_count_readiness(normalized_statuses, "future"),
        blocked_count=_count_readiness(normalized_statuses, "blocked"),
        default_source_mode=default_source_mode,
        statuses=normalized_statuses,
        object_storage_configured_hint=any(
            status.source_mode == "object_storage" and status.configured_hint
            for status in normalized_statuses
        ),
        local_source_available_hint=any(
            status.source_mode in ("local_staged", "local_file")
            and status.available_hint
            for status in normalized_statuses
        ),
        future_em_extract_placeholder=any(
            status.source_mode == "future_em_extract"
            and status.future_phase == "Phase 8"
            and status.status == "future_not_implemented"
            for status in normalized_statuses
        ),
        execution_supported=False,
        handoff_supported=False,
        source_access_performed=False,
        warnings=[
            "Source status is metadata only; no source access performed.",
            "Object storage configuration is a hint only and is not validated.",
            "Future EM Extract remains a Phase 8 placeholder.",
        ],
        required_next_steps=[
            "Validate object storage configuration in future Phase 7BS.",
            "Implement index to Screen 3 handoff in future Phase 7BT.",
        ],
        notes=notes,
    )


def validate_source_mode_status(status: SourceModeStatus) -> SourceModeStatus:
    """Validate one source status metadata record."""

    if not isinstance(status, SourceModeStatus):
        raise IndexSourceStatusError(
            "status must be a SourceModeStatus instance."
        )
    status.__post_init__()
    return status


def validate_source_mode_status_summary(
    summary: SourceModeStatusSummary,
) -> SourceModeStatusSummary:
    """Validate a source status summary metadata record."""

    if not isinstance(summary, SourceModeStatusSummary):
        raise IndexSourceStatusError(
            "summary must be a SourceModeStatusSummary instance."
        )
    summary.__post_init__()
    seen_modes: set[str] = set()
    for status in summary.statuses:
        validate_source_mode_status(status)
        if status.source_mode in seen_modes:
            raise IndexSourceStatusError(
                f"Duplicate source_mode: {status.source_mode!r}."
            )
        seen_modes.add(status.source_mode)
    return summary


def source_mode_status_to_dict(status: SourceModeStatus) -> dict[str, Any]:
    """Serialize one source status metadata record."""

    status = validate_source_mode_status(status)
    return {
        "source_mode": status.source_mode,
        "display_name": status.display_name,
        "status": status.status,
        "status_label": status.status_label,
        "readiness_level": status.readiness_level,
        "configured_hint": status.configured_hint,
        "available_hint": status.available_hint,
        "requires_configuration": status.requires_configuration,
        "requires_validation": status.requires_validation,
        "execution_supported": status.execution_supported,
        "handoff_supported": status.handoff_supported,
        "source_access_performed": status.source_access_performed,
        "file_read_performed": status.file_read_performed,
        "object_storage_call_performed": status.object_storage_call_performed,
        "db_lookup_performed": status.db_lookup_performed,
        "run_analysis_called": status.run_analysis_called,
        "future_phase": status.future_phase,
        "notes": status.notes,
    }


def source_mode_status_from_dict(data: dict[str, Any]) -> SourceModeStatus:
    """Deserialize one source status metadata record."""

    _require_mapping(data, "source_mode_status")
    return SourceModeStatus(
        source_mode=data.get("source_mode"),
        display_name=data.get("display_name"),
        status=data.get("status"),
        status_label=data.get("status_label"),
        readiness_level=data.get("readiness_level"),
        configured_hint=data.get("configured_hint"),
        available_hint=data.get("available_hint"),
        requires_configuration=data.get("requires_configuration"),
        requires_validation=data.get("requires_validation"),
        execution_supported=data.get("execution_supported"),
        handoff_supported=data.get("handoff_supported"),
        source_access_performed=data.get("source_access_performed"),
        file_read_performed=data.get("file_read_performed"),
        object_storage_call_performed=data.get("object_storage_call_performed"),
        db_lookup_performed=data.get("db_lookup_performed"),
        run_analysis_called=data.get("run_analysis_called"),
        future_phase=data.get("future_phase"),
        notes=data.get("notes"),
    )


def source_mode_status_summary_to_dict(
    summary: SourceModeStatusSummary,
) -> dict[str, Any]:
    """Serialize a source status summary metadata record."""

    summary = validate_source_mode_status_summary(summary)
    return {
        "summary_id": summary.summary_id,
        "source_count": summary.source_count,
        "ready_count": summary.ready_count,
        "needs_configuration_count": summary.needs_configuration_count,
        "future_count": summary.future_count,
        "blocked_count": summary.blocked_count,
        "default_source_mode": summary.default_source_mode,
        "statuses": [
            source_mode_status_to_dict(status)
            for status in summary.statuses
        ],
        "object_storage_configured_hint": (
            summary.object_storage_configured_hint
        ),
        "local_source_available_hint": summary.local_source_available_hint,
        "future_em_extract_placeholder": summary.future_em_extract_placeholder,
        "execution_supported": summary.execution_supported,
        "handoff_supported": summary.handoff_supported,
        "source_access_performed": summary.source_access_performed,
        "warnings": list(summary.warnings),
        "required_next_steps": list(summary.required_next_steps),
        "notes": summary.notes,
    }


def source_mode_status_summary_from_dict(
    data: dict[str, Any],
) -> SourceModeStatusSummary:
    """Deserialize a source status summary metadata record."""

    _require_mapping(data, "source_mode_status_summary")
    statuses = data.get("statuses")
    if not isinstance(statuses, list):
        raise IndexSourceStatusError("statuses must be a list.")
    return SourceModeStatusSummary(
        summary_id=data.get("summary_id"),
        source_count=data.get("source_count"),
        ready_count=data.get("ready_count"),
        needs_configuration_count=data.get("needs_configuration_count"),
        future_count=data.get("future_count"),
        blocked_count=data.get("blocked_count"),
        default_source_mode=data.get("default_source_mode"),
        statuses=[
            source_mode_status_from_dict(status_data)
            for status_data in statuses
        ],
        object_storage_configured_hint=data.get(
            "object_storage_configured_hint",
            False,
        ),
        local_source_available_hint=data.get("local_source_available_hint", False),
        future_em_extract_placeholder=data.get(
            "future_em_extract_placeholder",
            True,
        ),
        execution_supported=data.get("execution_supported", False),
        handoff_supported=data.get("handoff_supported", False),
        source_access_performed=data.get("source_access_performed", False),
        warnings=data.get("warnings", []),
        required_next_steps=data.get("required_next_steps", []),
        notes=data.get("notes"),
    )


def _count_readiness(
    statuses: list[SourceModeStatus],
    readiness_level: str,
) -> int:
    return sum(1 for status in statuses if status.readiness_level == readiness_level)


def _require_supported_source_mode(value: Any) -> str:
    if not isinstance(value, str) or value not in INDEX_SOURCE_MODES:
        raise IndexSourceStatusError(f"Unsupported source_mode: {value!r}.")
    return value


def _require_supported(
    value: Any,
    supported: tuple[str, ...],
    field_name: str,
) -> str:
    if not isinstance(value, str) or value not in supported:
        raise IndexSourceStatusError(f"Unsupported {field_name}: {value!r}.")
    return value


def _require_status_list(
    value: Any,
    field_name: str,
) -> list[SourceModeStatus]:
    if not isinstance(value, list):
        raise IndexSourceStatusError(f"{field_name} must be a list.")
    for status in value:
        if not isinstance(status, SourceModeStatus):
            raise IndexSourceStatusError(
                f"{field_name} must contain SourceModeStatus instances."
            )
    return value


def _require_nonempty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IndexSourceStatusError(f"{field_name} is required.")
    return value


def _require_optional_string(value: Any, field_name: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise IndexSourceStatusError(
            f"{field_name} must be a string or None."
        )
    return value


def _require_bool(value: Any, field_name: str) -> bool:
    if type(value) is not bool:
        raise IndexSourceStatusError(f"{field_name} must be boolean.")
    return value


def _require_nonnegative_int(value: Any, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise IndexSourceStatusError(
            f"{field_name} must be a non-negative integer."
        )
    return value


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise IndexSourceStatusError(f"{field_name} must be a mapping.")
    return value


def _require_list_of_strings(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str)
        for item in value
    ):
        raise IndexSourceStatusError(f"{field_name} must be a list of strings.")
    return value
