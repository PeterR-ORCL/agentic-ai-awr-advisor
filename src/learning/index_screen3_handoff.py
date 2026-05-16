"""Phase 7BT index to Screen 3 handoff metadata.

The records in this module describe a future index-to-Screen-3 source mode
handoff. They validate metadata shape only. They do not update dashboard
state, write URL hash/localStorage, call a backend, call object storage, read
files, query databases, invoke run_analysis.py, or perform an active handoff.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from src.learning.index_source_mode_entry import INDEX_SOURCE_MODES


INDEX_SCREEN3_HANDOFF_STATUSES = (
    "VALID_METADATA_ONLY",
    "INVALID",
    "NEEDS_SOURCE_MODE",
    "NEEDS_SOURCE_STATUS",
    "NEEDS_OBJECT_STORAGE_METADATA",
    "FUTURE_EM_EXTRACT_PLACEHOLDER",
    "HANDOFF_NOT_ALLOWED_IN_THIS_PHASE",
)


class IndexScreen3HandoffError(ValueError):
    """Raised when Phase 7BT index-to-Screen-3 handoff metadata is invalid."""


@dataclass(frozen=True)
class IndexToScreen3Handoff:
    """Metadata-only future handoff from the index to Screen 3."""

    handoff_id: str
    source_mode: str
    source_mode_entry_id: str | None
    source_status_id: str | None
    object_storage_config_id: str | None
    target_screen: str
    target_state_key: str
    selected_source_mode: str
    handoff_label: str
    handoff_summary: str
    handoff_supported: bool
    handoff_performed: bool
    screen3_state_updated: bool
    backend_request_created: bool
    source_access_performed: bool
    run_analysis_called: bool
    object_storage_called: bool
    local_file_read_performed: bool
    db_lookup_performed: bool
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.handoff_id, "handoff_id")
        _require_supported_source_mode(self.source_mode)
        _require_optional_string(self.source_mode_entry_id, "source_mode_entry_id")
        _require_optional_string(self.source_status_id, "source_status_id")
        _require_optional_string(
            self.object_storage_config_id,
            "object_storage_config_id",
        )
        _require_nonempty_string(self.target_screen, "target_screen")
        if self.target_screen != "screen_3":
            raise IndexScreen3HandoffError("target_screen must be screen_3.")
        _require_nonempty_string(self.target_state_key, "target_state_key")
        _require_supported_source_mode(self.selected_source_mode)
        if self.selected_source_mode != self.source_mode:
            raise IndexScreen3HandoffError(
                "selected_source_mode must match source_mode."
            )
        _require_nonempty_string(self.handoff_label, "handoff_label")
        _require_nonempty_string(self.handoff_summary, "handoff_summary")
        _require_bool(self.handoff_supported, "handoff_supported")
        _require_bool(self.handoff_performed, "handoff_performed")
        _require_bool(self.screen3_state_updated, "screen3_state_updated")
        _require_bool(self.backend_request_created, "backend_request_created")
        _require_bool(self.source_access_performed, "source_access_performed")
        _require_bool(self.run_analysis_called, "run_analysis_called")
        _require_bool(self.object_storage_called, "object_storage_called")
        _require_bool(
            self.local_file_read_performed,
            "local_file_read_performed",
        )
        _require_bool(self.db_lookup_performed, "db_lookup_performed")
        _require_optional_string(self.notes, "notes")
        if self.handoff_supported:
            raise IndexScreen3HandoffError(
                "handoff_supported must remain false in Phase 7BT."
            )
        if self.handoff_performed:
            raise IndexScreen3HandoffError(
                "handoff_performed must remain false in Phase 7BT."
            )
        if self.screen3_state_updated:
            raise IndexScreen3HandoffError(
                "screen3_state_updated must remain false in Phase 7BT."
            )
        if self.backend_request_created:
            raise IndexScreen3HandoffError(
                "backend_request_created must remain false in Phase 7BT."
            )
        if self.source_access_performed:
            raise IndexScreen3HandoffError(
                "source_access_performed must remain false in Phase 7BT."
            )
        if self.run_analysis_called:
            raise IndexScreen3HandoffError(
                "run_analysis_called must remain false in Phase 7BT."
            )
        if self.object_storage_called:
            raise IndexScreen3HandoffError(
                "object_storage_called must remain false in Phase 7BT."
            )
        if self.local_file_read_performed:
            raise IndexScreen3HandoffError(
                "local_file_read_performed must remain false in Phase 7BT."
            )
        if self.db_lookup_performed:
            raise IndexScreen3HandoffError(
                "db_lookup_performed must remain false in Phase 7BT."
            )


@dataclass(frozen=True)
class IndexToScreen3HandoffValidation:
    """Validation result for metadata-only index-to-Screen-3 handoff."""

    validation_id: str
    handoff_id: str
    valid: bool
    validation_status: str
    source_mode: str
    target_screen: str
    source_status_ready: bool
    object_storage_metadata_valid: bool
    future_em_extract_placeholder: bool
    can_handoff: bool
    handoff_blocked: bool
    handoff_performed: bool
    screen3_state_updated: bool
    backend_request_created: bool
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.validation_id, "validation_id")
        _require_nonempty_string(self.handoff_id, "handoff_id")
        _require_bool(self.valid, "valid")
        _require_supported(
            self.validation_status,
            INDEX_SCREEN3_HANDOFF_STATUSES,
            "validation_status",
        )
        _require_supported_source_mode(self.source_mode)
        _require_nonempty_string(self.target_screen, "target_screen")
        if self.target_screen != "screen_3":
            raise IndexScreen3HandoffError("target_screen must be screen_3.")
        _require_bool(self.source_status_ready, "source_status_ready")
        _require_bool(
            self.object_storage_metadata_valid,
            "object_storage_metadata_valid",
        )
        _require_bool(
            self.future_em_extract_placeholder,
            "future_em_extract_placeholder",
        )
        _require_bool(self.can_handoff, "can_handoff")
        _require_bool(self.handoff_blocked, "handoff_blocked")
        _require_bool(self.handoff_performed, "handoff_performed")
        _require_bool(self.screen3_state_updated, "screen3_state_updated")
        _require_bool(self.backend_request_created, "backend_request_created")
        _require_list_of_strings(self.denied_reasons, "denied_reasons")
        _require_list_of_strings(self.warnings, "warnings")
        _require_list_of_strings(
            self.required_next_steps,
            "required_next_steps",
        )
        _require_optional_string(self.notes, "notes")
        if self.can_handoff:
            raise IndexScreen3HandoffError(
                "can_handoff must remain false in Phase 7BT."
            )
        if not self.handoff_blocked:
            raise IndexScreen3HandoffError(
                "handoff_blocked must remain true in Phase 7BT."
            )
        if self.handoff_performed:
            raise IndexScreen3HandoffError(
                "handoff_performed must remain false in Phase 7BT."
            )
        if self.screen3_state_updated:
            raise IndexScreen3HandoffError(
                "screen3_state_updated must remain false in Phase 7BT."
            )
        if self.backend_request_created:
            raise IndexScreen3HandoffError(
                "backend_request_created must remain false in Phase 7BT."
            )


@dataclass(frozen=True)
class IndexSourceEntryReadiness:
    """Block-level 7BQ-7BT readiness metadata."""

    readiness_id: str
    source_mode_entry_ready: bool
    source_status_ready: bool
    object_storage_config_metadata_ready: bool
    handoff_metadata_ready: bool
    handoff_performed: bool
    execution_performed: bool
    object_storage_called: bool
    local_file_read_performed: bool
    db_lookup_performed: bool
    run_analysis_called: bool
    future_em_extract_placeholder: bool
    phase8_implemented: bool
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.readiness_id, "readiness_id")
        _require_bool(self.source_mode_entry_ready, "source_mode_entry_ready")
        _require_bool(self.source_status_ready, "source_status_ready")
        _require_bool(
            self.object_storage_config_metadata_ready,
            "object_storage_config_metadata_ready",
        )
        _require_bool(self.handoff_metadata_ready, "handoff_metadata_ready")
        _require_bool(self.handoff_performed, "handoff_performed")
        _require_bool(self.execution_performed, "execution_performed")
        _require_bool(self.object_storage_called, "object_storage_called")
        _require_bool(
            self.local_file_read_performed,
            "local_file_read_performed",
        )
        _require_bool(self.db_lookup_performed, "db_lookup_performed")
        _require_bool(self.run_analysis_called, "run_analysis_called")
        _require_bool(
            self.future_em_extract_placeholder,
            "future_em_extract_placeholder",
        )
        _require_bool(self.phase8_implemented, "phase8_implemented")
        _require_list_of_strings(self.denied_reasons, "denied_reasons")
        _require_list_of_strings(self.warnings, "warnings")
        _require_list_of_strings(
            self.required_next_steps,
            "required_next_steps",
        )
        _require_optional_string(self.notes, "notes")
        if self.handoff_performed:
            raise IndexScreen3HandoffError(
                "handoff_performed must remain false in Phase 7BT."
            )
        if self.execution_performed:
            raise IndexScreen3HandoffError(
                "execution_performed must remain false in Phase 7BT."
            )
        if self.object_storage_called:
            raise IndexScreen3HandoffError(
                "object_storage_called must remain false in Phase 7BT."
            )
        if self.local_file_read_performed:
            raise IndexScreen3HandoffError(
                "local_file_read_performed must remain false in Phase 7BT."
            )
        if self.db_lookup_performed:
            raise IndexScreen3HandoffError(
                "db_lookup_performed must remain false in Phase 7BT."
            )
        if self.run_analysis_called:
            raise IndexScreen3HandoffError(
                "run_analysis_called must remain false in Phase 7BT."
            )
        if not self.future_em_extract_placeholder:
            raise IndexScreen3HandoffError(
                "future_em_extract_placeholder must remain true in Phase 7BT."
            )
        if self.phase8_implemented:
            raise IndexScreen3HandoffError(
                "phase8_implemented must remain false in Phase 7BT."
            )


def create_index_screen3_handoff_id(
    source_mode: str,
    target_screen: str = "screen_3",
) -> str:
    """Create a deterministic index-to-Screen-3 handoff id."""

    _require_supported_source_mode(source_mode)
    _require_nonempty_string(target_screen, "target_screen")
    return (
        "INDEX-SCREEN3-HANDOFF-"
        f"{_normalize_token(source_mode)}-"
        f"{_normalize_token(target_screen)}"
    )


def create_index_screen3_handoff_validation_id(handoff_id: str) -> str:
    """Create a deterministic handoff validation id."""

    _require_nonempty_string(handoff_id, "handoff_id")
    return f"INDEX-SCREEN3-HANDOFF-VALIDATION-{_normalize_token(handoff_id)}"


def create_index_source_entry_readiness_id(
    context_label: str | None = None,
) -> str:
    """Create a deterministic index source entry readiness id."""

    _require_optional_string(context_label, "context_label")
    return (
        "INDEX-SOURCE-ENTRY-READINESS-"
        f"{_normalize_token(context_label or '7BQ-7BT')}"
    )


def create_index_screen3_handoff(
    source_mode: str,
    *,
    source_mode_entry_id: str | None = None,
    source_status_id: str | None = None,
    object_storage_config_id: str | None = None,
    notes: str | None = None,
) -> IndexToScreen3Handoff:
    """Create metadata for a future index-to-Screen-3 handoff."""

    _require_supported_source_mode(source_mode)
    _require_optional_string(source_mode_entry_id, "source_mode_entry_id")
    _require_optional_string(source_status_id, "source_status_id")
    _require_optional_string(
        object_storage_config_id,
        "object_storage_config_id",
    )
    _require_optional_string(notes, "notes")
    return IndexToScreen3Handoff(
        handoff_id=create_index_screen3_handoff_id(source_mode),
        source_mode=source_mode,
        source_mode_entry_id=source_mode_entry_id,
        source_status_id=source_status_id,
        object_storage_config_id=object_storage_config_id,
        target_screen="screen_3",
        target_state_key="selectedSourceMode",
        selected_source_mode=source_mode,
        handoff_label=f"Index source mode to Screen 3: {source_mode}",
        handoff_summary=(
            "Metadata-only preview for a future index to Screen 3 source "
            f"handoff using source_mode={source_mode}."
        ),
        handoff_supported=False,
        handoff_performed=False,
        screen3_state_updated=False,
        backend_request_created=False,
        source_access_performed=False,
        run_analysis_called=False,
        object_storage_called=False,
        local_file_read_performed=False,
        db_lookup_performed=False,
        notes=notes,
    )


def validate_index_screen3_handoff(
    handoff: IndexToScreen3Handoff,
) -> IndexToScreen3Handoff:
    """Validate handoff metadata without performing a handoff."""

    if not isinstance(handoff, IndexToScreen3Handoff):
        raise IndexScreen3HandoffError(
            "handoff must be an IndexToScreen3Handoff instance."
        )
    handoff.__post_init__()
    return handoff


def evaluate_index_screen3_handoff(
    handoff: IndexToScreen3Handoff,
) -> IndexToScreen3HandoffValidation:
    """Evaluate handoff metadata while keeping handoff blocked in Phase 7BT."""

    handoff = validate_index_screen3_handoff(handoff)
    source_status_ready = bool(handoff.source_status_id)
    object_storage_metadata_valid = (
        handoff.source_mode != "object_storage"
        or bool(handoff.object_storage_config_id)
    )
    future_em_extract_placeholder = handoff.source_mode == "future_em_extract"
    denied_reasons = ["handoff is not allowed in Phase 7BT"]
    warnings = [
        "Index-to-Screen-3 handoff is metadata-only.",
        "No Screen 3 state is updated.",
        "No backend request is created.",
    ]
    required_next_steps = [
        "Implement active handoff in a future controlled workflow.",
    ]
    valid = True
    status = "VALID_METADATA_ONLY"

    if not source_status_ready and not future_em_extract_placeholder:
        valid = False
        status = "NEEDS_SOURCE_STATUS"
        denied_reasons.append("source status metadata is required")
        required_next_steps.append("attach source status metadata")
    elif not object_storage_metadata_valid:
        valid = False
        status = "NEEDS_OBJECT_STORAGE_METADATA"
        denied_reasons.append("object storage config metadata is required")
        required_next_steps.append("attach object storage config metadata")
    elif future_em_extract_placeholder:
        status = "FUTURE_EM_EXTRACT_PLACEHOLDER"
        denied_reasons.append("future EM Extract belongs to Phase 8")
        required_next_steps.append("wait for Phase 8 EM Extract implementation")

    return IndexToScreen3HandoffValidation(
        validation_id=create_index_screen3_handoff_validation_id(
            handoff.handoff_id,
        ),
        handoff_id=handoff.handoff_id,
        valid=valid,
        validation_status=status,
        source_mode=handoff.source_mode,
        target_screen=handoff.target_screen,
        source_status_ready=source_status_ready,
        object_storage_metadata_valid=object_storage_metadata_valid,
        future_em_extract_placeholder=future_em_extract_placeholder,
        can_handoff=False,
        handoff_blocked=True,
        handoff_performed=False,
        screen3_state_updated=False,
        backend_request_created=False,
        denied_reasons=denied_reasons,
        warnings=warnings,
        required_next_steps=required_next_steps,
        notes=handoff.notes,
    )


def validate_index_screen3_handoff_validation(
    validation: IndexToScreen3HandoffValidation,
) -> IndexToScreen3HandoffValidation:
    """Validate a handoff validation result metadata record."""

    if not isinstance(validation, IndexToScreen3HandoffValidation):
        raise IndexScreen3HandoffError(
            "validation must be an IndexToScreen3HandoffValidation instance."
        )
    validation.__post_init__()
    return validation


def build_index_source_entry_readiness(
    *,
    source_mode_entry_ready: bool = True,
    source_status_ready: bool = True,
    object_storage_config_metadata_ready: bool = True,
    handoff_metadata_ready: bool = True,
    notes: str | None = None,
) -> IndexSourceEntryReadiness:
    """Build block-level 7BQ-7BT readiness metadata."""

    _require_bool(source_mode_entry_ready, "source_mode_entry_ready")
    _require_bool(source_status_ready, "source_status_ready")
    _require_bool(
        object_storage_config_metadata_ready,
        "object_storage_config_metadata_ready",
    )
    _require_bool(handoff_metadata_ready, "handoff_metadata_ready")
    _require_optional_string(notes, "notes")
    denied_reasons: list[str] = []
    if not source_mode_entry_ready:
        denied_reasons.append("source mode entry metadata is not ready")
    if not source_status_ready:
        denied_reasons.append("source status metadata is not ready")
    if not object_storage_config_metadata_ready:
        denied_reasons.append("object storage config metadata is not ready")
    if not handoff_metadata_ready:
        denied_reasons.append("handoff metadata is not ready")
    return IndexSourceEntryReadiness(
        readiness_id=create_index_source_entry_readiness_id(),
        source_mode_entry_ready=source_mode_entry_ready,
        source_status_ready=source_status_ready,
        object_storage_config_metadata_ready=object_storage_config_metadata_ready,
        handoff_metadata_ready=handoff_metadata_ready,
        handoff_performed=False,
        execution_performed=False,
        object_storage_called=False,
        local_file_read_performed=False,
        db_lookup_performed=False,
        run_analysis_called=False,
        future_em_extract_placeholder=True,
        phase8_implemented=False,
        denied_reasons=denied_reasons,
        warnings=[
            "Index source entry block is certified as metadata-only.",
            "Active Screen 3 handoff remains future work.",
            "Future EM Extract belongs to Phase 8.",
        ],
        required_next_steps=[
            "Implement active handoff only in a future controlled workflow.",
        ],
        notes=notes,
    )


def validate_index_source_entry_readiness(
    readiness: IndexSourceEntryReadiness,
) -> IndexSourceEntryReadiness:
    """Validate block-level index source entry readiness metadata."""

    if not isinstance(readiness, IndexSourceEntryReadiness):
        raise IndexScreen3HandoffError(
            "readiness must be an IndexSourceEntryReadiness instance."
        )
    readiness.__post_init__()
    return readiness


def index_screen3_handoff_to_dict(
    handoff: IndexToScreen3Handoff,
) -> dict[str, Any]:
    """Serialize handoff metadata."""

    handoff = validate_index_screen3_handoff(handoff)
    return {
        "handoff_id": handoff.handoff_id,
        "source_mode": handoff.source_mode,
        "source_mode_entry_id": handoff.source_mode_entry_id,
        "source_status_id": handoff.source_status_id,
        "object_storage_config_id": handoff.object_storage_config_id,
        "target_screen": handoff.target_screen,
        "target_state_key": handoff.target_state_key,
        "selected_source_mode": handoff.selected_source_mode,
        "handoff_label": handoff.handoff_label,
        "handoff_summary": handoff.handoff_summary,
        "handoff_supported": handoff.handoff_supported,
        "handoff_performed": handoff.handoff_performed,
        "screen3_state_updated": handoff.screen3_state_updated,
        "backend_request_created": handoff.backend_request_created,
        "source_access_performed": handoff.source_access_performed,
        "run_analysis_called": handoff.run_analysis_called,
        "object_storage_called": handoff.object_storage_called,
        "local_file_read_performed": handoff.local_file_read_performed,
        "db_lookup_performed": handoff.db_lookup_performed,
        "notes": handoff.notes,
    }


def index_screen3_handoff_from_dict(
    data: dict[str, Any],
) -> IndexToScreen3Handoff:
    """Deserialize handoff metadata."""

    _require_mapping(data, "index_screen3_handoff")
    return IndexToScreen3Handoff(
        handoff_id=data.get("handoff_id"),
        source_mode=data.get("source_mode"),
        source_mode_entry_id=data.get("source_mode_entry_id"),
        source_status_id=data.get("source_status_id"),
        object_storage_config_id=data.get("object_storage_config_id"),
        target_screen=data.get("target_screen"),
        target_state_key=data.get("target_state_key"),
        selected_source_mode=data.get("selected_source_mode"),
        handoff_label=data.get("handoff_label"),
        handoff_summary=data.get("handoff_summary"),
        handoff_supported=data.get("handoff_supported"),
        handoff_performed=data.get("handoff_performed"),
        screen3_state_updated=data.get("screen3_state_updated"),
        backend_request_created=data.get("backend_request_created"),
        source_access_performed=data.get("source_access_performed"),
        run_analysis_called=data.get("run_analysis_called"),
        object_storage_called=data.get("object_storage_called"),
        local_file_read_performed=data.get("local_file_read_performed"),
        db_lookup_performed=data.get("db_lookup_performed"),
        notes=data.get("notes"),
    )


def index_screen3_handoff_validation_to_dict(
    validation: IndexToScreen3HandoffValidation,
) -> dict[str, Any]:
    """Serialize handoff validation metadata."""

    validation = validate_index_screen3_handoff_validation(validation)
    return {
        "validation_id": validation.validation_id,
        "handoff_id": validation.handoff_id,
        "valid": validation.valid,
        "validation_status": validation.validation_status,
        "source_mode": validation.source_mode,
        "target_screen": validation.target_screen,
        "source_status_ready": validation.source_status_ready,
        "object_storage_metadata_valid": validation.object_storage_metadata_valid,
        "future_em_extract_placeholder": validation.future_em_extract_placeholder,
        "can_handoff": validation.can_handoff,
        "handoff_blocked": validation.handoff_blocked,
        "handoff_performed": validation.handoff_performed,
        "screen3_state_updated": validation.screen3_state_updated,
        "backend_request_created": validation.backend_request_created,
        "denied_reasons": list(validation.denied_reasons),
        "warnings": list(validation.warnings),
        "required_next_steps": list(validation.required_next_steps),
        "notes": validation.notes,
    }


def index_screen3_handoff_validation_from_dict(
    data: dict[str, Any],
) -> IndexToScreen3HandoffValidation:
    """Deserialize handoff validation metadata."""

    _require_mapping(data, "index_screen3_handoff_validation")
    return IndexToScreen3HandoffValidation(
        validation_id=data.get("validation_id"),
        handoff_id=data.get("handoff_id"),
        valid=data.get("valid"),
        validation_status=data.get("validation_status"),
        source_mode=data.get("source_mode"),
        target_screen=data.get("target_screen"),
        source_status_ready=data.get("source_status_ready"),
        object_storage_metadata_valid=data.get("object_storage_metadata_valid"),
        future_em_extract_placeholder=data.get("future_em_extract_placeholder"),
        can_handoff=data.get("can_handoff"),
        handoff_blocked=data.get("handoff_blocked"),
        handoff_performed=data.get("handoff_performed"),
        screen3_state_updated=data.get("screen3_state_updated"),
        backend_request_created=data.get("backend_request_created"),
        denied_reasons=data.get("denied_reasons", []),
        warnings=data.get("warnings", []),
        required_next_steps=data.get("required_next_steps", []),
        notes=data.get("notes"),
    )


def index_source_entry_readiness_to_dict(
    readiness: IndexSourceEntryReadiness,
) -> dict[str, Any]:
    """Serialize index source entry readiness metadata."""

    readiness = validate_index_source_entry_readiness(readiness)
    return {
        "readiness_id": readiness.readiness_id,
        "source_mode_entry_ready": readiness.source_mode_entry_ready,
        "source_status_ready": readiness.source_status_ready,
        "object_storage_config_metadata_ready": (
            readiness.object_storage_config_metadata_ready
        ),
        "handoff_metadata_ready": readiness.handoff_metadata_ready,
        "handoff_performed": readiness.handoff_performed,
        "execution_performed": readiness.execution_performed,
        "object_storage_called": readiness.object_storage_called,
        "local_file_read_performed": readiness.local_file_read_performed,
        "db_lookup_performed": readiness.db_lookup_performed,
        "run_analysis_called": readiness.run_analysis_called,
        "future_em_extract_placeholder": readiness.future_em_extract_placeholder,
        "phase8_implemented": readiness.phase8_implemented,
        "denied_reasons": list(readiness.denied_reasons),
        "warnings": list(readiness.warnings),
        "required_next_steps": list(readiness.required_next_steps),
        "notes": readiness.notes,
    }


def index_source_entry_readiness_from_dict(
    data: dict[str, Any],
) -> IndexSourceEntryReadiness:
    """Deserialize index source entry readiness metadata."""

    _require_mapping(data, "index_source_entry_readiness")
    return IndexSourceEntryReadiness(
        readiness_id=data.get("readiness_id"),
        source_mode_entry_ready=data.get("source_mode_entry_ready"),
        source_status_ready=data.get("source_status_ready"),
        object_storage_config_metadata_ready=data.get(
            "object_storage_config_metadata_ready",
        ),
        handoff_metadata_ready=data.get("handoff_metadata_ready"),
        handoff_performed=data.get("handoff_performed"),
        execution_performed=data.get("execution_performed"),
        object_storage_called=data.get("object_storage_called"),
        local_file_read_performed=data.get("local_file_read_performed"),
        db_lookup_performed=data.get("db_lookup_performed"),
        run_analysis_called=data.get("run_analysis_called"),
        future_em_extract_placeholder=data.get("future_em_extract_placeholder"),
        phase8_implemented=data.get("phase8_implemented"),
        denied_reasons=data.get("denied_reasons", []),
        warnings=data.get("warnings", []),
        required_next_steps=data.get("required_next_steps", []),
        notes=data.get("notes"),
    )


def _normalize_token(value: str) -> str:
    _require_nonempty_string(value, "value")
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().upper())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "NONE"


def _require_supported_source_mode(value: Any) -> str:
    if not isinstance(value, str) or value not in INDEX_SOURCE_MODES:
        raise IndexScreen3HandoffError(f"Unsupported source_mode: {value!r}.")
    return value


def _require_supported(
    value: Any,
    supported: tuple[str, ...],
    field_name: str,
) -> str:
    if not isinstance(value, str) or value not in supported:
        raise IndexScreen3HandoffError(f"Unsupported {field_name}: {value!r}.")
    return value


def _require_nonempty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IndexScreen3HandoffError(f"{field_name} is required.")
    return value


def _require_optional_string(value: Any, field_name: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise IndexScreen3HandoffError(
            f"{field_name} must be a string or None."
        )
    return value


def _require_bool(value: Any, field_name: str) -> bool:
    if type(value) is not bool:
        raise IndexScreen3HandoffError(f"{field_name} must be boolean.")
    return value


def _require_list_of_strings(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str)
        for item in value
    ):
        raise IndexScreen3HandoffError(
            f"{field_name} must be a list of strings."
        )
    return value


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise IndexScreen3HandoffError(f"{field_name} must be a mapping.")
    return value
