"""Selected review scope contract.

This module defines the backend authority for the operator's selected review
scope. It validates identity-level selection only. It does not render HTML,
read browser state, inspect generated dashboard artifacts, compute evidence,
run comparisons, create recommendations, mutate learning state, or call LLMs.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


CONTRACT_TYPE = "selected_review_scope_contract"
CONTRACT_VERSION = "7reset.selected_review_scope.v1"


class SourceMode(str, Enum):
    NEW_SOURCE = "new_source"
    EXISTING_EVIDENCE = "existing_evidence"
    OBJECT_STORAGE = "object_storage"
    GENERATED_ARTIFACT_REFERENCE = "generated_artifact_reference"
    UNAVAILABLE = "unavailable"


class ReviewFlowKind(str, Enum):
    SINGLE_AWR = "single_awr"
    HISTORICAL = "historical"
    COMPARATIVE = "comparative"
    DEEP_ANALYSIS = "deep_analysis"
    UNAVAILABLE = "unavailable"


class ReviewMode(str, Enum):
    DIAGNOSTIC_SNAPSHOT = "diagnostic_snapshot"
    HISTORICAL_REVIEW = "historical_review"
    COMPARATIVE_REVIEW = "comparative_review"
    DEEP_ANALYSIS = "deep_analysis"
    RECOMMENDATION_ACTION = "recommendation_action"
    LEARNING_GOVERNANCE = "learning_governance"


class ScopeValidationStatus(str, Enum):
    VALID = "valid"
    PARTIAL = "partial"
    INVALID = "invalid"
    UNAVAILABLE = "unavailable"


class TargetAlignmentStatus(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    MISSING_RUNTIME_SCOPE = "missing_runtime_scope"
    MISSING_TARGET_A = "missing_target_a"
    MISSING_TARGET_B = "missing_target_b"
    PREPARED_ONLY = "prepared_only"
    ALIGNED = "aligned"
    MISMATCH = "mismatch"


class CacheContinuityStatus(str, Enum):
    NONE = "none"
    DISPLAY_ONLY = "display_only"
    STALE = "stale"
    INVALIDATED = "invalidated"


class SelectionRole(str, Enum):
    RUNTIME_SCOPE = "runtime_scope"
    TARGET_A = "target_a"
    TARGET_B = "target_b"


NON_AUTHORITY_INPUT_FIELDS = {
    "browser_hash",
    "browser_state",
    "chart_payload",
    "css_class",
    "dashboard_hash",
    "dom_id",
    "generated_artifact_path",
    "generated_html",
    "generated_html_path",
    "hash_state",
    "html",
    "html_path",
    "learning_output",
    "llm_facts",
    "llm_text",
    "local_storage",
    "localStorage",
    "metric_delta",
    "metric_deltas",
    "recommendation",
    "recommendations",
    "selector",
    "selector_label",
    "ui_flags",
    "ui_selector_label",
}
GENERATED_ARTIFACT_INPUT_FIELDS = {
    "generated_artifact_path",
    "generated_html",
    "generated_html_path",
    "html",
    "html_path",
}


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _enum_value(enum_type: type[Enum], value: Any, default: Enum) -> Enum:
    if isinstance(value, enum_type):
        return value
    if value is None:
        return default
    text = _clean_string(value)
    if not text:
        return default
    normalized = text.lower()
    for item in enum_type:
        if normalized in {item.value.lower(), item.name.lower()}:
            return item
    return default


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y", "enabled", "available"}


def _first_string(mapping: Mapping[str, Any], keys: Sequence[str]) -> str | None:
    for key in keys:
        value = _clean_string(mapping.get(key))
        if value:
            return value
    return None


def _is_generated_html_reference(value: Any) -> bool:
    text = _clean_string(value)
    if not text:
        return False
    normalized = text.replace("\\", "/").lower()
    return normalized.endswith(".html") and (
        "/awr_dashboard/" in normalized or normalized.startswith("awr_dashboard/")
    )


def _ignored_input_warnings(mapping: Mapping[str, Any], field: str) -> tuple["ScopeValidationIssue", ...]:
    warnings: list[ScopeValidationIssue] = []
    for key in sorted(set(mapping).intersection(NON_AUTHORITY_INPUT_FIELDS)):
        if key in GENERATED_ARTIFACT_INPUT_FIELDS:
            warnings.append(
                ScopeValidationIssue(
                    code="generated_artifact_not_authority",
                    message="Generated dashboard artifact references cannot define selected scope authority.",
                    field=field,
                    severity="warning",
                )
            )
            continue
        warnings.append(
            ScopeValidationIssue(
                code="non_authoritative_input_ignored",
                message="Non-authoritative browser, UI, LLM, evidence, recommendation, or learning input was ignored.",
                field=field,
                severity="warning",
            )
        )
    for key in ("source_path", "path", "artifact_path"):
        if key in mapping and _is_generated_html_reference(mapping.get(key)):
            warnings.append(
                ScopeValidationIssue(
                    code="generated_artifact_not_authority",
                    message="Generated dashboard artifact references cannot define selected scope authority.",
                    field=field,
                    severity="warning",
                )
            )
    return tuple(warnings)


def _canonical_dict(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: payload[key] for key in sorted(payload) if payload[key] is not None}


@dataclass(frozen=True)
class ScopeValidationIssue:
    code: str
    message: str
    field: str | None = None
    severity: str = "error"

    def __post_init__(self) -> None:
        if not _clean_string(self.code):
            raise ValueError("validation issue code is required.")
        if not _clean_string(self.message):
            raise ValueError("validation issue message is required.")
        if self.severity not in {"error", "warning", "info"}:
            raise ValueError("validation issue severity must be error, warning, or info.")

    def to_dict(self) -> dict[str, str]:
        payload = {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }
        if self.field:
            payload["field"] = self.field
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ScopeValidationIssue":
        return cls(
            code=str(payload.get("code") or ""),
            message=str(payload.get("message") or ""),
            field=_clean_string(payload.get("field")),
            severity=str(payload.get("severity") or "error"),
        )


@dataclass(frozen=True)
class RuntimeScopeIdentity:
    scope_id: str
    label: str | None = None
    report_id: str | None = None
    database_id: str | None = None
    workload_id: str | None = None
    snapshot_window_id: str | None = None
    alignment_key: str | None = None

    def __post_init__(self) -> None:
        if not _clean_string(self.scope_id):
            raise ValueError("runtime scope_id is required.")

    def alignment_identity(self) -> str | None:
        return _clean_string(
            self.alignment_key
            or "|".join(
                part
                for part in (self.database_id, self.workload_id, self.report_id)
                if _clean_string(part)
            )
        )

    def to_dict(self) -> dict[str, str]:
        return _canonical_dict(
            {
                "scope_id": self.scope_id,
                "label": self.label,
                "report_id": self.report_id,
                "database_id": self.database_id,
                "workload_id": self.workload_id,
                "snapshot_window_id": self.snapshot_window_id,
                "alignment_key": self.alignment_key,
            }
        )

    @classmethod
    def from_value(
        cls,
        value: Any,
        field_name: str = "runtime_scope",
    ) -> tuple["RuntimeScopeIdentity | None", tuple[ScopeValidationIssue, ...]]:
        if value is None:
            return None, ()
        if isinstance(value, cls):
            return value, ()
        if isinstance(value, str):
            scope_id = _clean_string(value)
            return (cls(scope_id=scope_id), ()) if scope_id else (None, ())
        if not isinstance(value, Mapping):
            return None, (
                ScopeValidationIssue(
                    code="runtime_scope_identity_invalid",
                    message="Runtime Scope identity must be a mapping, string, or RuntimeScopeIdentity.",
                    field=field_name,
                ),
            )

        warnings = list(_ignored_input_warnings(value, field_name))
        scope_id = _first_string(value, ("scope_id", "runtime_scope_id", "row_id", "id"))
        if not scope_id:
            return None, tuple(warnings)
        return cls(
            scope_id=scope_id,
            label=_first_string(value, ("label", "name", "display_name")),
            report_id=_first_string(value, ("report_id", "awr_id")),
            database_id=_first_string(value, ("database_id", "dbid", "db_name")),
            workload_id=_first_string(value, ("workload_id", "workload_key")),
            snapshot_window_id=_first_string(value, ("snapshot_window_id", "window_id")),
            alignment_key=_first_string(value, ("alignment_key", "comparison_group_key")),
        ), tuple(warnings)


@dataclass(frozen=True)
class ReportIdentity:
    report_id: str
    label: str | None = None
    source_path: str | None = None

    def __post_init__(self) -> None:
        if not _clean_string(self.report_id):
            raise ValueError("report_id is required.")

    def to_dict(self) -> dict[str, str]:
        return _canonical_dict(
            {
                "report_id": self.report_id,
                "label": self.label,
                "source_path": self.source_path,
            }
        )

    @classmethod
    def from_value(
        cls,
        value: Any,
        field_name: str = "selected_report",
    ) -> tuple["ReportIdentity | None", tuple[ScopeValidationIssue, ...]]:
        if value is None:
            return None, ()
        if isinstance(value, cls):
            return value, ()
        if isinstance(value, str):
            report_id = _clean_string(value)
            return (cls(report_id=report_id), ()) if report_id else (None, ())
        if not isinstance(value, Mapping):
            return None, (
                ScopeValidationIssue(
                    code="report_identity_invalid",
                    message="Report identity must be a mapping, string, or ReportIdentity.",
                    field=field_name,
                ),
            )
        warnings = list(_ignored_input_warnings(value, field_name))
        report_id = _first_string(value, ("report_id", "awr_id", "id", "row_id"))
        if not report_id:
            return None, tuple(warnings)
        source_path = _first_string(value, ("source_path", "path"))
        if _is_generated_html_reference(source_path):
            source_path = None
        return cls(
            report_id=report_id,
            label=_first_string(value, ("label", "name", "display_name")),
            source_path=source_path,
        ), tuple(warnings)


@dataclass(frozen=True)
class DatabaseIdentity:
    database_id: str
    database_name: str | None = None
    instance_name: str | None = None

    def __post_init__(self) -> None:
        if not _clean_string(self.database_id):
            raise ValueError("database_id is required.")

    def to_dict(self) -> dict[str, str]:
        return _canonical_dict(
            {
                "database_id": self.database_id,
                "database_name": self.database_name,
                "instance_name": self.instance_name,
            }
        )

    @classmethod
    def from_value(
        cls,
        value: Any,
        field_name: str = "selected_database",
    ) -> tuple["DatabaseIdentity | None", tuple[ScopeValidationIssue, ...]]:
        if value is None:
            return None, ()
        if isinstance(value, cls):
            return value, ()
        if isinstance(value, str):
            database_id = _clean_string(value)
            return (cls(database_id=database_id), ()) if database_id else (None, ())
        if not isinstance(value, Mapping):
            return None, (
                ScopeValidationIssue(
                    code="database_identity_invalid",
                    message="Database identity must be a mapping, string, or DatabaseIdentity.",
                    field=field_name,
                ),
            )
        warnings = list(_ignored_input_warnings(value, field_name))
        database_id = _first_string(value, ("database_id", "dbid", "db_name", "id"))
        if not database_id:
            return None, tuple(warnings)
        return cls(
            database_id=database_id,
            database_name=_first_string(value, ("database_name", "db_name", "name")),
            instance_name=_first_string(value, ("instance_name", "instance")),
        ), tuple(warnings)


@dataclass(frozen=True)
class SnapshotWindowIdentity:
    window_id: str
    begin_time: str | None = None
    end_time: str | None = None
    label: str | None = None

    def __post_init__(self) -> None:
        if not _clean_string(self.window_id):
            raise ValueError("window_id is required.")

    def to_dict(self) -> dict[str, str]:
        return _canonical_dict(
            {
                "window_id": self.window_id,
                "begin_time": self.begin_time,
                "end_time": self.end_time,
                "label": self.label,
            }
        )

    @classmethod
    def from_value(
        cls,
        value: Any,
        field_name: str = "selected_window",
    ) -> tuple["SnapshotWindowIdentity | None", tuple[ScopeValidationIssue, ...]]:
        if value is None:
            return None, ()
        if isinstance(value, cls):
            return value, ()
        if isinstance(value, str):
            window_id = _clean_string(value)
            return (cls(window_id=window_id), ()) if window_id else (None, ())
        if not isinstance(value, Mapping):
            return None, (
                ScopeValidationIssue(
                    code="snapshot_window_identity_invalid",
                    message="Snapshot window identity must be a mapping, string, or SnapshotWindowIdentity.",
                    field=field_name,
                ),
            )
        warnings = list(_ignored_input_warnings(value, field_name))
        window_id = _first_string(value, ("window_id", "snapshot_window_id", "id", "row_id"))
        if not window_id:
            return None, tuple(warnings)
        return cls(
            window_id=window_id,
            begin_time=_first_string(value, ("begin_time", "start_time", "begin")),
            end_time=_first_string(value, ("end_time", "finish_time", "end")),
            label=_first_string(value, ("label", "name", "display_name")),
        ), tuple(warnings)


@dataclass(frozen=True)
class ComparisonTargetIdentity:
    target_id: str
    label: str | None = None
    report_id: str | None = None
    database_id: str | None = None
    workload_id: str | None = None
    snapshot_window_id: str | None = None
    alignment_key: str | None = None

    def __post_init__(self) -> None:
        if not _clean_string(self.target_id):
            raise ValueError("comparison target_id is required.")

    def alignment_identity(self) -> str | None:
        return _clean_string(
            self.alignment_key
            or "|".join(
                part
                for part in (self.database_id, self.workload_id, self.report_id)
                if _clean_string(part)
            )
        )

    def to_dict(self) -> dict[str, str]:
        return _canonical_dict(
            {
                "target_id": self.target_id,
                "label": self.label,
                "report_id": self.report_id,
                "database_id": self.database_id,
                "workload_id": self.workload_id,
                "snapshot_window_id": self.snapshot_window_id,
                "alignment_key": self.alignment_key,
            }
        )

    @classmethod
    def from_value(
        cls,
        value: Any,
        field_name: str,
    ) -> tuple["ComparisonTargetIdentity | None", tuple[ScopeValidationIssue, ...]]:
        if value is None:
            return None, ()
        if isinstance(value, cls):
            return value, ()
        if isinstance(value, str):
            target_id = _clean_string(value)
            return (cls(target_id=target_id), ()) if target_id else (None, ())
        if not isinstance(value, Mapping):
            return None, (
                ScopeValidationIssue(
                    code="comparison_target_identity_invalid",
                    message="Comparison target identity must be a mapping, string, or ComparisonTargetIdentity.",
                    field=field_name,
                ),
            )
        warnings = list(_ignored_input_warnings(value, field_name))
        target_id = _first_string(value, ("target_id", "comparison_target_id", "row_id", "id"))
        if not target_id:
            return None, tuple(warnings)
        return cls(
            target_id=target_id,
            label=_first_string(value, ("label", "name", "display_name")),
            report_id=_first_string(value, ("report_id", "awr_id")),
            database_id=_first_string(value, ("database_id", "dbid", "db_name")),
            workload_id=_first_string(value, ("workload_id", "workload_key")),
            snapshot_window_id=_first_string(value, ("snapshot_window_id", "window_id")),
            alignment_key=_first_string(value, ("alignment_key", "comparison_group_key")),
        ), tuple(warnings)


@dataclass(frozen=True)
class CacheContinuityMetadata:
    status: CacheContinuityStatus = CacheContinuityStatus.NONE
    prior_selected_flow_id: str | None = None
    displayed_scope_id: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, str]:
        return _canonical_dict(
            {
                "status": self.status.value,
                "prior_selected_flow_id": self.prior_selected_flow_id,
                "displayed_scope_id": self.displayed_scope_id,
                "reason": self.reason,
            }
        )

    @classmethod
    def from_value(cls, value: Any) -> "CacheContinuityMetadata":
        if value is None:
            return cls()
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            return cls(status=CacheContinuityStatus.DISPLAY_ONLY, reason=str(value))
        return cls(
            status=_enum_value(
                CacheContinuityStatus,
                value.get("status"),
                CacheContinuityStatus.NONE,
            ),
            prior_selected_flow_id=_clean_string(value.get("prior_selected_flow_id")),
            displayed_scope_id=_clean_string(value.get("displayed_scope_id")),
            reason=_clean_string(value.get("reason")),
        )


@dataclass(frozen=True)
class SelectionProvenance:
    source_system: str | None = None
    operator_action_id: str | None = None
    submitted_by: str | None = None
    created_at: str | None = None

    def is_present(self) -> bool:
        return bool(_clean_string(self.source_system))

    def to_dict(self) -> dict[str, str]:
        return _canonical_dict(
            {
                "source_system": self.source_system,
                "operator_action_id": self.operator_action_id,
                "submitted_by": self.submitted_by,
                "created_at": self.created_at,
            }
        )

    @classmethod
    def from_value(cls, value: Any) -> "SelectionProvenance":
        if value is None:
            return cls()
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls(source_system=_clean_string(value))
        if not isinstance(value, Mapping):
            return cls(source_system=str(value))
        return cls(
            source_system=_first_string(value, ("source_system", "source", "system")),
            operator_action_id=_first_string(value, ("operator_action_id", "action_id")),
            submitted_by=_first_string(value, ("submitted_by", "operator", "user")),
            created_at=_first_string(value, ("created_at", "generated_at", "timestamp")),
        )


@dataclass(frozen=True)
class ReviewModeIntent:
    requested_modes: tuple[ReviewMode, ...] = ()
    historical_evidence_available: bool = False
    deep_analysis_requested: bool = False
    deep_analysis_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested_modes": [mode.value for mode in self.requested_modes],
            "historical_evidence_available": self.historical_evidence_available,
            "deep_analysis_requested": self.deep_analysis_requested,
            "deep_analysis_available": self.deep_analysis_available,
        }

    @classmethod
    def from_value(cls, value: Any) -> "ReviewModeIntent":
        if value is None:
            return cls()
        if isinstance(value, cls):
            return value
        if isinstance(value, ReviewMode):
            return cls(requested_modes=(value,))
        if isinstance(value, str):
            return cls(requested_modes=(_enum_value(ReviewMode, value, ReviewMode.DIAGNOSTIC_SNAPSHOT),))
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray, Mapping)):
            return cls(
                requested_modes=tuple(
                    _enum_value(ReviewMode, item, ReviewMode.DIAGNOSTIC_SNAPSHOT)
                    for item in value
                )
            )
        if not isinstance(value, Mapping):
            return cls()

        requested_value = value.get("requested_modes", ())
        if isinstance(requested_value, (str, ReviewMode)):
            requested_values = (requested_value,)
        else:
            requested_values = tuple(requested_value or ())
        requested_modes = tuple(
            _enum_value(ReviewMode, item, ReviewMode.DIAGNOSTIC_SNAPSHOT)
            for item in requested_values
        )
        return cls(
            requested_modes=requested_modes,
            historical_evidence_available=_bool_value(value.get("historical_evidence_available")),
            deep_analysis_requested=_bool_value(value.get("deep_analysis_requested"))
            or ReviewMode.DEEP_ANALYSIS in requested_modes,
            deep_analysis_available=_bool_value(value.get("deep_analysis_available")),
        )


@dataclass(frozen=True)
class SelectedFlowIdentity:
    selected_flow_id: str
    source_mode: SourceMode
    flow_kind: ReviewFlowKind
    runtime_scope_id: str | None = None
    target_a_id: str | None = None
    target_b_id: str | None = None

    def to_dict(self) -> dict[str, str]:
        return _canonical_dict(
            {
                "selected_flow_id": self.selected_flow_id,
                "source_mode": self.source_mode.value,
                "flow_kind": self.flow_kind.value,
                "runtime_scope_id": self.runtime_scope_id,
                "target_a_id": self.target_a_id,
                "target_b_id": self.target_b_id,
            }
        )


@dataclass(frozen=True)
class ReviewModeUnavailableReason:
    mode: ReviewMode
    reasons: tuple[ScopeValidationIssue, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "reasons": [reason.to_dict() for reason in self.reasons],
        }


@dataclass(frozen=True)
class SelectedReviewScopeContract:
    contract_type: str = CONTRACT_TYPE
    contract_version: str = CONTRACT_VERSION
    selected_flow_id: str = "selected-flow:none"
    source_mode: SourceMode = SourceMode.UNAVAILABLE
    flow_kind: ReviewFlowKind = ReviewFlowKind.UNAVAILABLE
    runtime_scope: RuntimeScopeIdentity | None = None
    selected_report: ReportIdentity | None = None
    selected_database: DatabaseIdentity | None = None
    selected_window: SnapshotWindowIdentity | None = None
    target_a: ComparisonTargetIdentity | None = None
    target_b: ComparisonTargetIdentity | None = None
    target_alignment_status: TargetAlignmentStatus = TargetAlignmentStatus.NOT_APPLICABLE
    review_mode_intent: ReviewModeIntent = field(default_factory=ReviewModeIntent)
    eligible_review_modes: tuple[ReviewMode, ...] = ()
    unavailable_review_modes: tuple[ReviewModeUnavailableReason, ...] = ()
    cache_continuity: CacheContinuityMetadata = field(default_factory=CacheContinuityMetadata)
    provenance: SelectionProvenance = field(default_factory=SelectionProvenance)
    validation_status: ScopeValidationStatus = ScopeValidationStatus.INVALID
    validation_errors: tuple[ScopeValidationIssue, ...] = ()
    warnings: tuple[ScopeValidationIssue, ...] = ()

    def selected_flow_identity(self) -> SelectedFlowIdentity:
        return SelectedFlowIdentity(
            selected_flow_id=self.selected_flow_id,
            source_mode=self.source_mode,
            flow_kind=self.flow_kind,
            runtime_scope_id=self.runtime_scope.scope_id if self.runtime_scope else None,
            target_a_id=self.target_a.target_id if self.target_a else None,
            target_b_id=self.target_b.target_id if self.target_b else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_type": self.contract_type,
            "contract_version": self.contract_version,
            "selected_flow_id": self.selected_flow_id,
            "source_mode": self.source_mode.value,
            "flow_kind": self.flow_kind.value,
            "runtime_scope": self.runtime_scope.to_dict() if self.runtime_scope else None,
            "selected_report": self.selected_report.to_dict() if self.selected_report else None,
            "selected_database": self.selected_database.to_dict() if self.selected_database else None,
            "selected_window": self.selected_window.to_dict() if self.selected_window else None,
            "target_a": self.target_a.to_dict() if self.target_a else None,
            "target_b": self.target_b.to_dict() if self.target_b else None,
            "target_alignment_status": self.target_alignment_status.value,
            "review_mode_intent": self.review_mode_intent.to_dict(),
            "eligible_review_modes": [mode.value for mode in self.eligible_review_modes],
            "unavailable_review_modes": [
                unavailable.to_dict() for unavailable in self.unavailable_review_modes
            ],
            "cache_continuity": self.cache_continuity.to_dict(),
            "provenance": self.provenance.to_dict(),
            "validation_status": self.validation_status.value,
            "validation_errors": [issue.to_dict() for issue in self.validation_errors],
            "warnings": [issue.to_dict() for issue in self.warnings],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SelectedReviewScopeContract":
        return build_selected_review_scope_contract(
            source_mode=payload.get("source_mode", SourceMode.UNAVAILABLE),
            runtime_scope=payload.get("runtime_scope"),
            selected_report=payload.get("selected_report"),
            selected_database=payload.get("selected_database"),
            selected_window=payload.get("selected_window"),
            target_a=payload.get("target_a"),
            target_b=payload.get("target_b"),
            review_mode_intent=payload.get("review_mode_intent"),
            cache_continuity=payload.get("cache_continuity"),
            provenance=payload.get("provenance"),
        )


def build_selected_review_scope_contract(
    *,
    source_mode: SourceMode | str = SourceMode.EXISTING_EVIDENCE,
    runtime_scope: RuntimeScopeIdentity | Mapping[str, Any] | str | None = None,
    selected_report: ReportIdentity | Mapping[str, Any] | str | None = None,
    selected_database: DatabaseIdentity | Mapping[str, Any] | str | None = None,
    selected_window: SnapshotWindowIdentity | Mapping[str, Any] | str | None = None,
    target_a: ComparisonTargetIdentity | Mapping[str, Any] | str | None = None,
    target_b: ComparisonTargetIdentity | Mapping[str, Any] | str | None = None,
    review_mode_intent: ReviewModeIntent | Mapping[str, Any] | Sequence[Any] | str | None = None,
    cache_continuity: CacheContinuityMetadata | Mapping[str, Any] | str | None = None,
    provenance: SelectionProvenance | Mapping[str, Any] | str | None = None,
) -> SelectedReviewScopeContract:
    """Build and validate the selected review scope contract."""

    normalized_source_mode = _enum_value(SourceMode, source_mode, SourceMode.UNAVAILABLE)
    normalized_runtime_scope, runtime_warnings = RuntimeScopeIdentity.from_value(runtime_scope)
    normalized_report, report_warnings = ReportIdentity.from_value(selected_report)
    normalized_database, database_warnings = DatabaseIdentity.from_value(selected_database)
    normalized_window, window_warnings = SnapshotWindowIdentity.from_value(selected_window)
    normalized_target_a, target_a_warnings = ComparisonTargetIdentity.from_value(target_a, "target_a")
    normalized_target_b, target_b_warnings = ComparisonTargetIdentity.from_value(target_b, "target_b")
    normalized_intent = ReviewModeIntent.from_value(review_mode_intent)
    normalized_cache = CacheContinuityMetadata.from_value(cache_continuity)
    normalized_provenance = SelectionProvenance.from_value(provenance)

    warnings = (
        runtime_warnings
        + report_warnings
        + database_warnings
        + window_warnings
        + target_a_warnings
        + target_b_warnings
    )

    selected_flow_id = compute_selected_flow_id(
        source_mode=normalized_source_mode,
        runtime_scope=normalized_runtime_scope,
        selected_report=normalized_report,
        selected_database=normalized_database,
        selected_window=normalized_window,
        target_a=normalized_target_a,
        target_b=normalized_target_b,
    )
    return _evaluate_contract(
        source_mode=normalized_source_mode,
        selected_flow_id=selected_flow_id,
        runtime_scope=normalized_runtime_scope,
        selected_report=normalized_report,
        selected_database=normalized_database,
        selected_window=normalized_window,
        target_a=normalized_target_a,
        target_b=normalized_target_b,
        review_mode_intent=normalized_intent,
        cache_continuity=normalized_cache,
        provenance=normalized_provenance,
        input_warnings=warnings,
    )


def validate_selected_review_scope_contract(
    contract: SelectedReviewScopeContract | Mapping[str, Any],
) -> SelectedReviewScopeContract:
    """Return a recalculated copy of the selected review scope contract."""

    if isinstance(contract, Mapping):
        return SelectedReviewScopeContract.from_dict(contract)
    if not isinstance(contract, SelectedReviewScopeContract):
        raise TypeError("contract must be SelectedReviewScopeContract or mapping.")
    return build_selected_review_scope_contract(
        source_mode=contract.source_mode,
        runtime_scope=contract.runtime_scope,
        selected_report=contract.selected_report,
        selected_database=contract.selected_database,
        selected_window=contract.selected_window,
        target_a=contract.target_a,
        target_b=contract.target_b,
        review_mode_intent=contract.review_mode_intent,
        cache_continuity=contract.cache_continuity,
        provenance=contract.provenance,
    )


def compute_selected_flow_id(
    *,
    source_mode: SourceMode | str = SourceMode.EXISTING_EVIDENCE,
    runtime_scope: RuntimeScopeIdentity | None = None,
    selected_report: ReportIdentity | None = None,
    selected_database: DatabaseIdentity | None = None,
    selected_window: SnapshotWindowIdentity | None = None,
    target_a: ComparisonTargetIdentity | None = None,
    target_b: ComparisonTargetIdentity | None = None,
) -> str:
    """Return a deterministic selected-flow id from authoritative fields only."""

    normalized_source_mode = _enum_value(SourceMode, source_mode, SourceMode.UNAVAILABLE)
    if not any((runtime_scope, selected_report, selected_database, selected_window, target_a, target_b)):
        return "selected-flow:none"
    payload = {
        "contract_type": CONTRACT_TYPE,
        "contract_version": CONTRACT_VERSION,
        "source_mode": normalized_source_mode.value,
        "runtime_scope": runtime_scope.to_dict() if runtime_scope else None,
        "selected_report": selected_report.to_dict() if selected_report else None,
        "selected_database": selected_database.to_dict() if selected_database else None,
        "selected_window": selected_window.to_dict() if selected_window else None,
        "target_a": target_a.to_dict() if target_a else None,
        "target_b": target_b.to_dict() if target_b else None,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"selected-flow:{digest[:24]}"


def apply_selection_event(
    contract: SelectedReviewScopeContract,
    clicked_row_identity: RuntimeScopeIdentity | ComparisonTargetIdentity | Mapping[str, Any] | str,
    role: SelectionRole | str,
) -> SelectedReviewScopeContract:
    """Apply a single click selection event and return a new contract."""

    normalized_role = _enum_value(SelectionRole, role, SelectionRole.RUNTIME_SCOPE)
    if normalized_role == SelectionRole.RUNTIME_SCOPE:
        clicked, _warnings = RuntimeScopeIdentity.from_value(clicked_row_identity)
        runtime_scope = None if _same_runtime_scope(contract.runtime_scope, clicked) else clicked
        return build_selected_review_scope_contract(
            source_mode=contract.source_mode,
            runtime_scope=runtime_scope,
            selected_report=contract.selected_report,
            selected_database=contract.selected_database,
            selected_window=contract.selected_window,
            target_a=contract.target_a,
            target_b=contract.target_b,
            review_mode_intent=contract.review_mode_intent,
            cache_continuity=contract.cache_continuity,
            provenance=contract.provenance,
        )

    clicked_target, _warnings = ComparisonTargetIdentity.from_value(
        clicked_row_identity,
        normalized_role.value,
    )
    target_a = contract.target_a
    target_b = contract.target_b
    if normalized_role == SelectionRole.TARGET_A:
        target_a = None if _same_target(contract.target_a, clicked_target) else clicked_target
    elif normalized_role == SelectionRole.TARGET_B:
        target_b = None if _same_target(contract.target_b, clicked_target) else clicked_target
    return build_selected_review_scope_contract(
        source_mode=contract.source_mode,
        runtime_scope=contract.runtime_scope,
        selected_report=contract.selected_report,
        selected_database=contract.selected_database,
        selected_window=contract.selected_window,
        target_a=target_a,
        target_b=target_b,
        review_mode_intent=contract.review_mode_intent,
        cache_continuity=contract.cache_continuity,
        provenance=contract.provenance,
    )


def clear_selection_role(
    contract: SelectedReviewScopeContract,
    role: SelectionRole | str,
) -> SelectedReviewScopeContract:
    """Clear one selection role and return a new contract."""

    normalized_role = _enum_value(SelectionRole, role, SelectionRole.RUNTIME_SCOPE)
    return build_selected_review_scope_contract(
        source_mode=contract.source_mode,
        runtime_scope=None if normalized_role == SelectionRole.RUNTIME_SCOPE else contract.runtime_scope,
        selected_report=contract.selected_report,
        selected_database=contract.selected_database,
        selected_window=contract.selected_window,
        target_a=None if normalized_role == SelectionRole.TARGET_A else contract.target_a,
        target_b=None if normalized_role == SelectionRole.TARGET_B else contract.target_b,
        review_mode_intent=contract.review_mode_intent,
        cache_continuity=contract.cache_continuity,
        provenance=contract.provenance,
    )


def clear_comparison_targets(contract: SelectedReviewScopeContract) -> SelectedReviewScopeContract:
    """Clear Target A and Target B without clearing Runtime Scope."""

    return build_selected_review_scope_contract(
        source_mode=contract.source_mode,
        runtime_scope=contract.runtime_scope,
        selected_report=contract.selected_report,
        selected_database=contract.selected_database,
        selected_window=contract.selected_window,
        target_a=None,
        target_b=None,
        review_mode_intent=contract.review_mode_intent,
        cache_continuity=contract.cache_continuity,
        provenance=contract.provenance,
    )


def clear_all_selections(contract: SelectedReviewScopeContract) -> SelectedReviewScopeContract:
    """Clear Runtime Scope, Target A, and Target B."""

    return build_selected_review_scope_contract(
        source_mode=contract.source_mode,
        runtime_scope=None,
        selected_report=contract.selected_report,
        selected_database=contract.selected_database,
        selected_window=contract.selected_window,
        target_a=None,
        target_b=None,
        review_mode_intent=contract.review_mode_intent,
        cache_continuity=contract.cache_continuity,
        provenance=contract.provenance,
    )


def is_diagnostic_snapshot_eligible(contract: SelectedReviewScopeContract) -> bool:
    return ReviewMode.DIAGNOSTIC_SNAPSHOT in contract.eligible_review_modes


def is_historical_review_eligible(contract: SelectedReviewScopeContract) -> bool:
    return ReviewMode.HISTORICAL_REVIEW in contract.eligible_review_modes


def is_comparative_review_eligible(contract: SelectedReviewScopeContract) -> bool:
    return ReviewMode.COMPARATIVE_REVIEW in contract.eligible_review_modes


def is_deep_analysis_eligible(contract: SelectedReviewScopeContract) -> bool:
    return ReviewMode.DEEP_ANALYSIS in contract.eligible_review_modes


def unavailable_reasons_for(
    contract: SelectedReviewScopeContract,
    mode: ReviewMode | str,
) -> tuple[ScopeValidationIssue, ...]:
    normalized_mode = _enum_value(ReviewMode, mode, ReviewMode.DIAGNOSTIC_SNAPSHOT)
    for unavailable in contract.unavailable_review_modes:
        if unavailable.mode == normalized_mode:
            return unavailable.reasons
    return ()


def _same_runtime_scope(
    current: RuntimeScopeIdentity | None,
    clicked: RuntimeScopeIdentity | None,
) -> bool:
    return bool(current and clicked and current.scope_id == clicked.scope_id)


def _same_target(
    current: ComparisonTargetIdentity | None,
    clicked: ComparisonTargetIdentity | None,
) -> bool:
    return bool(current and clicked and current.target_id == clicked.target_id)


def _evaluate_contract(
    *,
    source_mode: SourceMode,
    selected_flow_id: str,
    runtime_scope: RuntimeScopeIdentity | None,
    selected_report: ReportIdentity | None,
    selected_database: DatabaseIdentity | None,
    selected_window: SnapshotWindowIdentity | None,
    target_a: ComparisonTargetIdentity | None,
    target_b: ComparisonTargetIdentity | None,
    review_mode_intent: ReviewModeIntent,
    cache_continuity: CacheContinuityMetadata,
    provenance: SelectionProvenance,
    input_warnings: tuple[ScopeValidationIssue, ...],
) -> SelectedReviewScopeContract:
    errors: list[ScopeValidationIssue] = []
    warnings: list[ScopeValidationIssue] = list(input_warnings)

    if source_mode == SourceMode.UNAVAILABLE:
        errors.append(
            _issue("source_mode_unavailable", "Source mode is unavailable.", "source_mode")
        )
    if source_mode == SourceMode.GENERATED_ARTIFACT_REFERENCE:
        errors.append(
            _issue(
                "generated_artifact_not_authority",
                "Generated dashboard artifacts cannot define selected review scope authority.",
                "source_mode",
            )
        )
    if not provenance.is_present():
        errors.append(_issue("provenance_required", "Selection provenance is required.", "provenance"))
    if runtime_scope is None:
        errors.append(
            _issue(
                "missing_runtime_scope",
                "Runtime Scope is required for selected review scope authority.",
                "runtime_scope",
            )
        )

    alignment_status = _determine_target_alignment_status(runtime_scope, target_a, target_b)
    if alignment_status == TargetAlignmentStatus.MISMATCH:
        errors.append(
            _issue(
                "target_alignment_mismatch",
                "Runtime Scope, Target A, and Target B are not aligned.",
                "target_alignment_status",
            )
        )
    if ReviewMode.COMPARATIVE_REVIEW in review_mode_intent.requested_modes:
        if alignment_status == TargetAlignmentStatus.MISSING_TARGET_A:
            errors.append(_issue("missing_target_a", "Target A is required for Comparative Review.", "target_a"))
        elif alignment_status == TargetAlignmentStatus.MISSING_TARGET_B:
            errors.append(_issue("missing_target_b", "Target B is required for Comparative Review.", "target_b"))
        elif alignment_status == TargetAlignmentStatus.PREPARED_ONLY:
            errors.append(
                _issue(
                    "target_alignment_unvalidated",
                    "Target A/B selections are prepared but not aligned by deterministic identity.",
                    "target_alignment_status",
                )
            )

    if cache_continuity.status != CacheContinuityStatus.NONE:
        warnings.append(
            ScopeValidationIssue(
                code="cache_continuity_not_authority",
                message="Cache continuity may be displayed but cannot create selected review scope authority.",
                field="cache_continuity",
                severity="warning",
            )
        )

    base_authority_available = (
        runtime_scope is not None
        and source_mode not in {SourceMode.UNAVAILABLE, SourceMode.GENERATED_ARTIFACT_REFERENCE}
        and provenance.is_present()
    )
    eligible_modes: list[ReviewMode] = []
    unavailable_modes: list[ReviewModeUnavailableReason] = []

    if base_authority_available:
        eligible_modes.append(ReviewMode.DIAGNOSTIC_SNAPSHOT)
    else:
        unavailable_modes.append(
            _unavailable(
                ReviewMode.DIAGNOSTIC_SNAPSHOT,
                _base_unavailable_reasons(runtime_scope, source_mode, provenance),
            )
        )

    if base_authority_available and (
        selected_window is not None or review_mode_intent.historical_evidence_available
    ):
        eligible_modes.append(ReviewMode.HISTORICAL_REVIEW)
    else:
        unavailable_modes.append(
            _unavailable(
                ReviewMode.HISTORICAL_REVIEW,
                _historical_unavailable_reasons(
                    runtime_scope,
                    source_mode,
                    provenance,
                    selected_window,
                    review_mode_intent,
                ),
            )
        )

    if base_authority_available and alignment_status == TargetAlignmentStatus.ALIGNED:
        eligible_modes.append(ReviewMode.COMPARATIVE_REVIEW)
    else:
        unavailable_modes.append(
            _unavailable(
                ReviewMode.COMPARATIVE_REVIEW,
                _comparative_unavailable_reasons(
                    runtime_scope,
                    source_mode,
                    provenance,
                    alignment_status,
                ),
            )
        )

    if (
        base_authority_available
        and review_mode_intent.deep_analysis_requested
        and review_mode_intent.deep_analysis_available
    ):
        eligible_modes.append(ReviewMode.DEEP_ANALYSIS)
    else:
        unavailable_modes.append(
            _unavailable(
                ReviewMode.DEEP_ANALYSIS,
                _deep_analysis_unavailable_reasons(
                    runtime_scope,
                    source_mode,
                    provenance,
                    review_mode_intent,
                ),
            )
        )

    unavailable_modes.append(
        _unavailable(
            ReviewMode.RECOMMENDATION_ACTION,
            (
                _issue(
                    "evidence_pack_required",
                    "Recommendation/action rendering requires an evidence_pack_contract.",
                    "eligible_review_modes",
                ),
            ),
        )
    )
    unavailable_modes.append(
        _unavailable(
            ReviewMode.LEARNING_GOVERNANCE,
            (
                _issue(
                    "evidence_pack_required",
                    "Learning/governance rendering requires an evidence_pack_contract.",
                    "eligible_review_modes",
                ),
            ),
        )
    )

    flow_kind = _determine_flow_kind(eligible_modes)
    validation_status = _determine_validation_status(source_mode, runtime_scope, errors)

    return SelectedReviewScopeContract(
        contract_type=CONTRACT_TYPE,
        contract_version=CONTRACT_VERSION,
        selected_flow_id=selected_flow_id,
        source_mode=source_mode,
        flow_kind=flow_kind,
        runtime_scope=runtime_scope,
        selected_report=selected_report,
        selected_database=selected_database,
        selected_window=selected_window,
        target_a=target_a,
        target_b=target_b,
        target_alignment_status=alignment_status,
        review_mode_intent=review_mode_intent,
        eligible_review_modes=tuple(eligible_modes),
        unavailable_review_modes=tuple(unavailable_modes),
        cache_continuity=cache_continuity,
        provenance=provenance,
        validation_status=validation_status,
        validation_errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _determine_target_alignment_status(
    runtime_scope: RuntimeScopeIdentity | None,
    target_a: ComparisonTargetIdentity | None,
    target_b: ComparisonTargetIdentity | None,
) -> TargetAlignmentStatus:
    if target_a is None and target_b is None:
        return TargetAlignmentStatus.NOT_APPLICABLE
    if runtime_scope is None:
        return TargetAlignmentStatus.MISSING_RUNTIME_SCOPE
    if target_a is None:
        return TargetAlignmentStatus.MISSING_TARGET_A
    if target_b is None:
        return TargetAlignmentStatus.MISSING_TARGET_B

    runtime_alignment = runtime_scope.alignment_identity()
    target_a_alignment = target_a.alignment_identity()
    target_b_alignment = target_b.alignment_identity()
    if not all((runtime_alignment, target_a_alignment, target_b_alignment)):
        return TargetAlignmentStatus.PREPARED_ONLY
    if runtime_alignment == target_a_alignment == target_b_alignment:
        return TargetAlignmentStatus.ALIGNED
    return TargetAlignmentStatus.MISMATCH


def _determine_flow_kind(eligible_modes: Sequence[ReviewMode]) -> ReviewFlowKind:
    if ReviewMode.DEEP_ANALYSIS in eligible_modes:
        return ReviewFlowKind.DEEP_ANALYSIS
    if ReviewMode.COMPARATIVE_REVIEW in eligible_modes:
        return ReviewFlowKind.COMPARATIVE
    if ReviewMode.HISTORICAL_REVIEW in eligible_modes:
        return ReviewFlowKind.HISTORICAL
    if ReviewMode.DIAGNOSTIC_SNAPSHOT in eligible_modes:
        return ReviewFlowKind.SINGLE_AWR
    return ReviewFlowKind.UNAVAILABLE


def _determine_validation_status(
    source_mode: SourceMode,
    runtime_scope: RuntimeScopeIdentity | None,
    errors: Sequence[ScopeValidationIssue],
) -> ScopeValidationStatus:
    if source_mode == SourceMode.UNAVAILABLE:
        return ScopeValidationStatus.UNAVAILABLE
    if not errors:
        return ScopeValidationStatus.VALID
    if runtime_scope is not None:
        return ScopeValidationStatus.PARTIAL
    return ScopeValidationStatus.INVALID


def _base_unavailable_reasons(
    runtime_scope: RuntimeScopeIdentity | None,
    source_mode: SourceMode,
    provenance: SelectionProvenance,
) -> tuple[ScopeValidationIssue, ...]:
    reasons: list[ScopeValidationIssue] = []
    if runtime_scope is None:
        reasons.append(_issue("missing_runtime_scope", "Runtime Scope is required.", "runtime_scope"))
    if source_mode == SourceMode.UNAVAILABLE:
        reasons.append(_issue("source_mode_unavailable", "Source mode is unavailable.", "source_mode"))
    if source_mode == SourceMode.GENERATED_ARTIFACT_REFERENCE:
        reasons.append(
            _issue(
                "generated_artifact_not_authority",
                "Generated dashboard artifacts are not selected scope authority.",
                "source_mode",
            )
        )
    if not provenance.is_present():
        reasons.append(_issue("provenance_required", "Selection provenance is required.", "provenance"))
    return tuple(reasons)


def _historical_unavailable_reasons(
    runtime_scope: RuntimeScopeIdentity | None,
    source_mode: SourceMode,
    provenance: SelectionProvenance,
    selected_window: SnapshotWindowIdentity | None,
    review_mode_intent: ReviewModeIntent,
) -> tuple[ScopeValidationIssue, ...]:
    reasons = list(_base_unavailable_reasons(runtime_scope, source_mode, provenance))
    if runtime_scope is not None and not (
        selected_window is not None or review_mode_intent.historical_evidence_available
    ):
        reasons.append(
            _issue(
                "historical_evidence_unavailable",
                "Historical Review requires explicit historical window or evidence availability.",
                "review_mode_intent",
            )
        )
    return tuple(reasons)


def _comparative_unavailable_reasons(
    runtime_scope: RuntimeScopeIdentity | None,
    source_mode: SourceMode,
    provenance: SelectionProvenance,
    alignment_status: TargetAlignmentStatus,
) -> tuple[ScopeValidationIssue, ...]:
    reasons = list(_base_unavailable_reasons(runtime_scope, source_mode, provenance))
    if alignment_status == TargetAlignmentStatus.MISSING_RUNTIME_SCOPE:
        reasons.append(_issue("missing_runtime_scope", "Runtime Scope is required for Comparative Review.", "runtime_scope"))
    elif alignment_status == TargetAlignmentStatus.MISSING_TARGET_A:
        reasons.append(_issue("missing_target_a", "Target A is required for Comparative Review.", "target_a"))
    elif alignment_status == TargetAlignmentStatus.MISSING_TARGET_B:
        reasons.append(_issue("missing_target_b", "Target B is required for Comparative Review.", "target_b"))
    elif alignment_status == TargetAlignmentStatus.PREPARED_ONLY:
        reasons.append(
            _issue(
                "target_alignment_unvalidated",
                "Target A/B selections require deterministic alignment before Comparative Review.",
                "target_alignment_status",
            )
        )
    elif alignment_status == TargetAlignmentStatus.MISMATCH:
        reasons.append(
            _issue(
                "target_alignment_mismatch",
                "Runtime Scope, Target A, and Target B are not aligned for Comparative Review.",
                "target_alignment_status",
            )
        )
    elif alignment_status == TargetAlignmentStatus.NOT_APPLICABLE:
        reasons.append(
            _issue(
                "comparison_targets_missing",
                "Target A and Target B are required for Comparative Review.",
                "target_alignment_status",
            )
        )
    return tuple(_dedupe_issues(reasons))


def _deep_analysis_unavailable_reasons(
    runtime_scope: RuntimeScopeIdentity | None,
    source_mode: SourceMode,
    provenance: SelectionProvenance,
    review_mode_intent: ReviewModeIntent,
) -> tuple[ScopeValidationIssue, ...]:
    reasons = list(_base_unavailable_reasons(runtime_scope, source_mode, provenance))
    if runtime_scope is not None and not review_mode_intent.deep_analysis_requested:
        reasons.append(
            _issue(
                "deep_analysis_not_requested",
                "Deep Analysis eligibility must be explicitly requested.",
                "review_mode_intent",
            )
        )
    elif runtime_scope is not None and not review_mode_intent.deep_analysis_available:
        reasons.append(
            _issue(
                "deep_analysis_contract_unavailable",
                "Deep Analysis eligibility requires explicit deterministic availability.",
                "review_mode_intent",
            )
        )
    return tuple(_dedupe_issues(reasons))


def _issue(code: str, message: str, field: str | None = None) -> ScopeValidationIssue:
    return ScopeValidationIssue(code=code, message=message, field=field)


def _unavailable(
    mode: ReviewMode,
    reasons: tuple[ScopeValidationIssue, ...],
) -> ReviewModeUnavailableReason:
    normalized_reasons = tuple(_dedupe_issues(reasons))
    if not normalized_reasons:
        normalized_reasons = (_issue("mode_unavailable", "Review mode is unavailable."),)
    return ReviewModeUnavailableReason(mode=mode, reasons=normalized_reasons)


def _dedupe_issues(issues: Sequence[ScopeValidationIssue]) -> tuple[ScopeValidationIssue, ...]:
    seen: set[tuple[str, str | None]] = set()
    deduped: list[ScopeValidationIssue] = []
    for issue in issues:
        key = (issue.code, issue.field)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    return tuple(deduped)
