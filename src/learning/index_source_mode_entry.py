"""Phase 7BQ dashboard index source mode entry metadata.

The records in this module describe source options shown at the dashboard
entry point. They validate metadata shape only. They do not read files, call
object storage, inspect databases, invoke run_analysis.py, or perform Screen 3
handoff.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


INDEX_SOURCE_MODES = (
    "local_staged",
    "local_file",
    "existing_run",
    "object_storage",
    "future_upload",
    "future_em_extract",
)

INDEX_SOURCE_DISPLAY_NAMES = {
    "local_staged": "Local Staged AWR",
    "local_file": "Local File",
    "existing_run": "Existing Run",
    "object_storage": "Object Storage",
    "future_upload": "Future Upload",
    "future_em_extract": "Future EM Extract",
}

_INDEX_SOURCE_DESCRIPTIONS = {
    "local_staged": (
        "Preview the default local staged AWR entry option without checking "
        "the staging directory or reading files."
    ),
    "local_file": (
        "Preview a future local file entry option without opening a path, "
        "reading content, or validating file existence."
    ),
    "existing_run": (
        "Preview an existing run entry option without querying persisted run "
        "history or looking up database state."
    ),
    "object_storage": (
        "Preview object storage as a source option without importing OCI, "
        "validating configuration, listing buckets, or downloading objects."
    ),
    "future_upload": (
        "Preview a future upload option only; upload handling is not "
        "implemented in Phase 7BQ."
    ),
    "future_em_extract": (
        "Preview a future Enterprise Manager extract option only; EM Extract "
        "implementation belongs to Phase 8."
    ),
}

_IMPLEMENTED_SOURCE_MODES = (
    "local_staged",
    "local_file",
    "existing_run",
    "object_storage",
)
_REQUIRES_CONFIGURATION_SOURCE_MODES = ("object_storage",)
_REQUIRES_VALIDATION_SOURCE_MODES = INDEX_SOURCE_MODES


class IndexSourceModeEntryError(ValueError):
    """Raised when Phase 7BQ index source mode entry metadata is invalid."""


@dataclass(frozen=True)
class IndexSourceModeEntry:
    """Metadata for one preview-only dashboard entry source option."""

    source_mode: str
    display_name: str
    description: str
    enabled_for_preview: bool
    implemented: bool
    requires_configuration: bool
    requires_validation: bool
    target_screen: str
    handoff_supported: bool
    execution_supported: bool
    status_label: str
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_supported_source_mode(self.source_mode)
        _require_nonempty_string(self.display_name, "display_name")
        _require_nonempty_string(self.description, "description")
        _require_bool(self.enabled_for_preview, "enabled_for_preview")
        _require_bool(self.implemented, "implemented")
        _require_bool(self.requires_configuration, "requires_configuration")
        _require_bool(self.requires_validation, "requires_validation")
        _require_nonempty_string(self.target_screen, "target_screen")
        _require_bool(self.handoff_supported, "handoff_supported")
        _require_bool(self.execution_supported, "execution_supported")
        _require_nonempty_string(self.status_label, "status_label")
        _require_optional_string(self.notes, "notes")
        if self.handoff_supported:
            raise IndexSourceModeEntryError(
                "handoff_supported must remain false in Phase 7BQ."
            )
        if self.execution_supported:
            raise IndexSourceModeEntryError(
                "execution_supported must remain false in Phase 7BQ."
            )


@dataclass(frozen=True)
class IndexSourceModeEntrySummary:
    """Summary of preview-only dashboard entry source options."""

    summary_id: str
    entries: list[IndexSourceModeEntry]
    default_source_mode: str
    source_mode_count: int
    implemented_count: int
    preview_only_count: int
    handoff_supported: bool
    execution_supported: bool
    object_storage_available_hint: bool
    future_em_extract_available_hint: bool
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.summary_id, "summary_id")
        _require_entry_list(self.entries, "entries")
        _require_supported_source_mode(self.default_source_mode)
        _require_int(self.source_mode_count, "source_mode_count")
        _require_int(self.implemented_count, "implemented_count")
        _require_int(self.preview_only_count, "preview_only_count")
        _require_bool(self.handoff_supported, "handoff_supported")
        _require_bool(self.execution_supported, "execution_supported")
        _require_bool(
            self.object_storage_available_hint,
            "object_storage_available_hint",
        )
        _require_bool(
            self.future_em_extract_available_hint,
            "future_em_extract_available_hint",
        )
        _require_optional_string(self.notes, "notes")
        if self.source_mode_count != len(self.entries):
            raise IndexSourceModeEntryError(
                "source_mode_count must match entries length."
            )
        if self.implemented_count != sum(1 for entry in self.entries if entry.implemented):
            raise IndexSourceModeEntryError(
                "implemented_count must match implemented entries."
            )
        if self.preview_only_count != sum(
            1
            for entry in self.entries
            if entry.enabled_for_preview and not entry.execution_supported
        ):
            raise IndexSourceModeEntryError(
                "preview_only_count must match preview-only entries."
            )
        if self.handoff_supported:
            raise IndexSourceModeEntryError(
                "handoff_supported must remain false in Phase 7BQ."
            )
        if self.execution_supported:
            raise IndexSourceModeEntryError(
                "execution_supported must remain false in Phase 7BQ."
            )


def create_index_source_mode_entry(
    source_mode: str,
    notes: str | None = None,
) -> IndexSourceModeEntry:
    """Create one deterministic preview-only index source mode entry."""

    _require_supported_source_mode(source_mode)
    _require_optional_string(notes, "notes")
    implemented = source_mode in _IMPLEMENTED_SOURCE_MODES
    status_label = "Preview only" if implemented else "Future placeholder"
    if source_mode == "future_em_extract":
        status_label = "Phase 8 placeholder"
    return IndexSourceModeEntry(
        source_mode=source_mode,
        display_name=INDEX_SOURCE_DISPLAY_NAMES[source_mode],
        description=_INDEX_SOURCE_DESCRIPTIONS[source_mode],
        enabled_for_preview=True,
        implemented=implemented,
        requires_configuration=source_mode in _REQUIRES_CONFIGURATION_SOURCE_MODES,
        requires_validation=source_mode in _REQUIRES_VALIDATION_SOURCE_MODES,
        target_screen="screen3",
        handoff_supported=False,
        execution_supported=False,
        status_label=status_label,
        notes=notes,
    )


def create_default_index_source_mode_entries() -> list[IndexSourceModeEntry]:
    """Create deterministic entries for every Phase 7BQ source mode."""

    return [
        create_index_source_mode_entry(source_mode)
        for source_mode in INDEX_SOURCE_MODES
    ]


def create_index_source_mode_summary(
    entries: list[IndexSourceModeEntry] | None = None,
    default_source_mode: str = "local_staged",
    notes: str | None = None,
) -> IndexSourceModeEntrySummary:
    """Create a preview-only summary without loading or executing sources."""

    _require_supported_source_mode(default_source_mode)
    _require_optional_string(notes, "notes")
    normalized_entries = (
        create_default_index_source_mode_entries()
        if entries is None
        else list(entries)
    )
    for entry in normalized_entries:
        validate_index_source_mode_entry(entry)
    return IndexSourceModeEntrySummary(
        summary_id="INDEX-SOURCE-MODE-ENTRY-SUMMARY-7BQ",
        entries=normalized_entries,
        default_source_mode=default_source_mode,
        source_mode_count=len(normalized_entries),
        implemented_count=sum(1 for entry in normalized_entries if entry.implemented),
        preview_only_count=sum(
            1
            for entry in normalized_entries
            if entry.enabled_for_preview and not entry.execution_supported
        ),
        handoff_supported=False,
        execution_supported=False,
        object_storage_available_hint=False,
        future_em_extract_available_hint=False,
        notes=notes,
    )


def validate_index_source_mode_entry(
    entry: IndexSourceModeEntry,
) -> IndexSourceModeEntry:
    """Validate one index source mode entry metadata record."""

    if not isinstance(entry, IndexSourceModeEntry):
        raise IndexSourceModeEntryError(
            "entry must be an IndexSourceModeEntry instance."
        )
    entry.__post_init__()
    return entry


def validate_index_source_mode_summary(
    summary: IndexSourceModeEntrySummary,
) -> IndexSourceModeEntrySummary:
    """Validate a Phase 7BQ index source mode summary metadata record."""

    if not isinstance(summary, IndexSourceModeEntrySummary):
        raise IndexSourceModeEntryError(
            "summary must be an IndexSourceModeEntrySummary instance."
        )
    summary.__post_init__()
    seen_modes: set[str] = set()
    for entry in summary.entries:
        validate_index_source_mode_entry(entry)
        if entry.source_mode in seen_modes:
            raise IndexSourceModeEntryError(
                f"Duplicate source_mode: {entry.source_mode!r}."
            )
        seen_modes.add(entry.source_mode)
    return summary


def index_source_mode_entry_to_dict(
    entry: IndexSourceModeEntry,
) -> dict[str, Any]:
    """Serialize one index source mode entry metadata record."""

    entry = validate_index_source_mode_entry(entry)
    return {
        "source_mode": entry.source_mode,
        "display_name": entry.display_name,
        "description": entry.description,
        "enabled_for_preview": entry.enabled_for_preview,
        "implemented": entry.implemented,
        "requires_configuration": entry.requires_configuration,
        "requires_validation": entry.requires_validation,
        "target_screen": entry.target_screen,
        "handoff_supported": entry.handoff_supported,
        "execution_supported": entry.execution_supported,
        "status_label": entry.status_label,
        "notes": entry.notes,
    }


def index_source_mode_entry_from_dict(data: dict[str, Any]) -> IndexSourceModeEntry:
    """Deserialize one index source mode entry metadata record."""

    _require_mapping(data, "index_source_mode_entry")
    return IndexSourceModeEntry(
        source_mode=data.get("source_mode"),
        display_name=data.get("display_name"),
        description=data.get("description"),
        enabled_for_preview=data.get("enabled_for_preview"),
        implemented=data.get("implemented"),
        requires_configuration=data.get("requires_configuration"),
        requires_validation=data.get("requires_validation"),
        target_screen=data.get("target_screen"),
        handoff_supported=data.get("handoff_supported"),
        execution_supported=data.get("execution_supported"),
        status_label=data.get("status_label"),
        notes=data.get("notes"),
    )


def index_source_mode_summary_to_dict(
    summary: IndexSourceModeEntrySummary,
) -> dict[str, Any]:
    """Serialize an index source mode entry summary metadata record."""

    summary = validate_index_source_mode_summary(summary)
    return {
        "summary_id": summary.summary_id,
        "entries": [
            index_source_mode_entry_to_dict(entry)
            for entry in summary.entries
        ],
        "default_source_mode": summary.default_source_mode,
        "source_mode_count": summary.source_mode_count,
        "implemented_count": summary.implemented_count,
        "preview_only_count": summary.preview_only_count,
        "handoff_supported": summary.handoff_supported,
        "execution_supported": summary.execution_supported,
        "object_storage_available_hint": summary.object_storage_available_hint,
        "future_em_extract_available_hint": (
            summary.future_em_extract_available_hint
        ),
        "notes": summary.notes,
    }


def index_source_mode_summary_from_dict(
    data: dict[str, Any],
) -> IndexSourceModeEntrySummary:
    """Deserialize an index source mode entry summary metadata record."""

    _require_mapping(data, "index_source_mode_entry_summary")
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise IndexSourceModeEntryError("entries must be a list.")
    return IndexSourceModeEntrySummary(
        summary_id=data.get("summary_id"),
        entries=[
            index_source_mode_entry_from_dict(entry_data)
            for entry_data in entries
        ],
        default_source_mode=data.get("default_source_mode"),
        source_mode_count=data.get("source_mode_count"),
        implemented_count=data.get("implemented_count"),
        preview_only_count=data.get("preview_only_count"),
        handoff_supported=data.get("handoff_supported"),
        execution_supported=data.get("execution_supported"),
        object_storage_available_hint=data.get(
            "object_storage_available_hint",
            False,
        ),
        future_em_extract_available_hint=data.get(
            "future_em_extract_available_hint",
            False,
        ),
        notes=data.get("notes"),
    )


def _require_supported_source_mode(value: Any) -> str:
    if not isinstance(value, str) or value not in INDEX_SOURCE_MODES:
        raise IndexSourceModeEntryError(f"Unsupported source_mode: {value!r}.")
    return value


def _require_entry_list(
    value: Any,
    field_name: str,
) -> list[IndexSourceModeEntry]:
    if not isinstance(value, list):
        raise IndexSourceModeEntryError(f"{field_name} must be a list.")
    for entry in value:
        if not isinstance(entry, IndexSourceModeEntry):
            raise IndexSourceModeEntryError(
                f"{field_name} must contain IndexSourceModeEntry instances."
            )
    return value


def _require_nonempty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IndexSourceModeEntryError(f"{field_name} is required.")
    return value


def _require_optional_string(value: Any, field_name: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise IndexSourceModeEntryError(
            f"{field_name} must be a string or None."
        )
    return value


def _require_bool(value: Any, field_name: str) -> bool:
    if type(value) is not bool:
        raise IndexSourceModeEntryError(f"{field_name} must be boolean.")
    return value


def _require_int(value: Any, field_name: str) -> int:
    if type(value) is not int:
        raise IndexSourceModeEntryError(f"{field_name} must be an integer.")
    return value


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise IndexSourceModeEntryError(f"{field_name} must be a mapping.")
    return value
