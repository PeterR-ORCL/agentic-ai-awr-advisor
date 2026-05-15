"""Phase 7AO Screen 3 re-analysis readiness metadata.

This module provides local validation/readiness records and evidence availability
classification for the Screen 3 re-analysis control plane. It does not execute
analysis, load sources, call object storage, query databases, mutate Phase 4I,
change diagnosis/scoring/recommendations, or create learning candidates.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


EVIDENCE_TYPES = (
    "metric",
    "wait_event",
    "sql_signal",
    "trend",
    "anomaly",
    "topology",
    "platform",
    "source_option",
    "score",
    "recommendation_context",
    "unknown",
)

AVAILABILITY_STATUSES = (
    "available",
    "missing",
    "unavailable",
    "unsupported",
    "not_extracted",
    "not_reliable",
    "not_applicable",
    "unknown",
)

RELIABILITY_STATUSES = (
    "reliable",
    "partially_reliable",
    "unreliable",
    "insufficient_context",
    "unknown",
)

MISSING_REASONS = (
    "absent_from_report",
    "unsupported_by_topology",
    "unsupported_by_platform",
    "parser_gap",
    "source_not_collected",
    "source_misconfigured",
    "value_not_reliable",
    "not_applicable",
    "unknown",
)

CONFIDENCE_IMPACTS = (
    "none",
    "low",
    "medium",
    "high",
    "unknown",
)

REANALYSIS_READINESS_STATUSES = (
    "READY_METADATA_ONLY",
    "NOT_READY",
    "NEEDS_SOURCE_SELECTION",
    "NEEDS_REQUEST_VALIDATION",
    "NEEDS_COMPARISON_INPUTS",
    "NEEDS_EVIDENCE_REVIEW",
    "EXECUTION_BLOCKED_IN_THIS_PHASE",
)

UNAVAILABLE_STATUSES = (
    "missing",
    "unavailable",
    "not_extracted",
    "not_reliable",
    "unknown",
)


class ReAnalysisReadinessError(ValueError):
    """Raised when Phase 7AO readiness metadata is invalid."""


@dataclass(frozen=True)
class EvidenceAvailabilityRecord:
    """Availability classification for one evidence item."""

    evidence_id: str
    evidence_name: str
    evidence_type: str
    domain: str | None = None
    source_report_id: str | None = None
    source_run_id: str | None = None
    availability_status: str = "unknown"
    reliability_status: str = "unknown"
    missing_reason: str = "unknown"
    confidence_impact: str = "unknown"
    affects_diagnosis: bool = False
    affects_comparison: bool = False
    parser_review_recommended: bool = False
    source_review_recommended: bool = False
    scoring_review_recommended: bool = False
    fallback_evidence: list[str] | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.evidence_id, "evidence_id")
        _require_nonempty_string(self.evidence_name, "evidence_name")
        _require_supported(self.evidence_type, EVIDENCE_TYPES, "evidence_type")
        _require_optional_string(self.domain, "domain")
        _require_optional_string(self.source_report_id, "source_report_id")
        _require_optional_string(self.source_run_id, "source_run_id")
        _require_supported(
            self.availability_status,
            AVAILABILITY_STATUSES,
            "availability_status",
        )
        _require_supported(
            self.reliability_status,
            RELIABILITY_STATUSES,
            "reliability_status",
        )
        _require_supported(self.missing_reason, MISSING_REASONS, "missing_reason")
        _require_supported(
            self.confidence_impact,
            CONFIDENCE_IMPACTS,
            "confidence_impact",
        )
        _require_bool(self.affects_diagnosis, "affects_diagnosis")
        _require_bool(self.affects_comparison, "affects_comparison")
        _require_bool(self.parser_review_recommended, "parser_review_recommended")
        _require_bool(self.source_review_recommended, "source_review_recommended")
        _require_bool(self.scoring_review_recommended, "scoring_review_recommended")
        _require_list_of_strings(
            [] if self.fallback_evidence is None else self.fallback_evidence,
            "fallback_evidence",
        )
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class EvidenceAvailabilitySummary:
    """Summary of evidence availability classifications."""

    summary_id: str
    source_report_count: int
    total_evidence_count: int
    available_count: int
    missing_count: int
    unreliable_count: int
    unsupported_count: int
    parser_gap_count: int
    confidence_impact_summary: str
    parser_review_recommended: bool
    source_review_recommended: bool
    scoring_review_recommended: bool
    records: list[EvidenceAvailabilityRecord]
    warnings: list[str]
    required_next_steps: list[str]

    def __post_init__(self) -> None:
        _require_nonempty_string(self.summary_id, "summary_id")
        for field_name in (
            "source_report_count",
            "total_evidence_count",
            "available_count",
            "missing_count",
            "unreliable_count",
            "unsupported_count",
            "parser_gap_count",
        ):
            _require_nonnegative_int(getattr(self, field_name), field_name)
        _require_nonempty_string(
            self.confidence_impact_summary,
            "confidence_impact_summary",
        )
        _require_bool(self.parser_review_recommended, "parser_review_recommended")
        _require_bool(self.source_review_recommended, "source_review_recommended")
        _require_bool(self.scoring_review_recommended, "scoring_review_recommended")
        if not isinstance(self.records, list):
            raise ReAnalysisReadinessError("records must be a list.")
        for record in self.records:
            validate_evidence_availability_record(record)
        _require_list_of_strings(self.warnings, "warnings")
        _require_list_of_strings(self.required_next_steps, "required_next_steps")
        expected = _evidence_summary_counts(self.records)
        for key, expected_value in expected.items():
            if getattr(self, key) != expected_value:
                raise ReAnalysisReadinessError(
                    f"{key} must match evidence records: expected {expected_value}."
                )


@dataclass(frozen=True)
class ReAnalysisReadinessResult:
    """Block readiness result for the Screen 3 re-analysis control plane."""

    readiness_id: str
    screen3_reanalysis_ready: bool
    source_selection_ready: bool
    request_model_ready: bool
    controller_ready: bool
    comparison_ready: bool
    missing_metric_handling_ready: bool
    action_ui_preview_only: bool
    backend_execution_performed: bool
    run_analysis_called: bool
    object_storage_called: bool
    local_file_read_performed: bool
    db_lookup_performed: bool
    phase4i_mutated: bool
    dashboard_regenerated: bool
    readiness_status: str
    denied_reasons: list[str]
    warnings: list[str]
    required_next_steps: list[str]

    def __post_init__(self) -> None:
        _require_nonempty_string(self.readiness_id, "readiness_id")
        for field_name in (
            "screen3_reanalysis_ready",
            "source_selection_ready",
            "request_model_ready",
            "controller_ready",
            "comparison_ready",
            "missing_metric_handling_ready",
            "action_ui_preview_only",
            "backend_execution_performed",
            "run_analysis_called",
            "object_storage_called",
            "local_file_read_performed",
            "db_lookup_performed",
            "phase4i_mutated",
            "dashboard_regenerated",
        ):
            _require_bool(getattr(self, field_name), field_name)
        _require_supported(
            self.readiness_status,
            REANALYSIS_READINESS_STATUSES,
            "readiness_status",
        )
        _require_list_of_strings(self.denied_reasons, "denied_reasons")
        _require_list_of_strings(self.warnings, "warnings")
        _require_list_of_strings(self.required_next_steps, "required_next_steps")
        _reject_true(self.backend_execution_performed, "backend_execution_performed")
        _reject_true(self.run_analysis_called, "run_analysis_called")
        _reject_true(self.object_storage_called, "object_storage_called")
        _reject_true(self.local_file_read_performed, "local_file_read_performed")
        _reject_true(self.db_lookup_performed, "db_lookup_performed")
        _reject_true(self.phase4i_mutated, "phase4i_mutated")
        _reject_true(self.dashboard_regenerated, "dashboard_regenerated")


def create_evidence_id(
    evidence_name: str,
    evidence_type: str,
    source_report_id: str | None = None,
    source_run_id: str | None = None,
) -> str:
    """Create a deterministic evidence id."""

    _require_nonempty_string(evidence_name, "evidence_name")
    _require_supported(evidence_type, EVIDENCE_TYPES, "evidence_type")
    _require_optional_string(source_report_id, "source_report_id")
    _require_optional_string(source_run_id, "source_run_id")
    return (
        "REANALYSIS-EVIDENCE-"
        f"{_normalize_token(evidence_type)}-"
        f"{_normalize_token(evidence_name)}-"
        f"{_normalize_token(source_report_id or 'NO-REPORT')}-"
        f"{_normalize_token(source_run_id or 'NO-RUN')}"
    )


def create_evidence_summary_id(
    source_report_count: int,
    total_evidence_count: int,
) -> str:
    """Create a deterministic evidence summary id."""

    _require_nonnegative_int(source_report_count, "source_report_count")
    _require_nonnegative_int(total_evidence_count, "total_evidence_count")
    return (
        "REANALYSIS-EVIDENCE-SUMMARY-"
        f"{source_report_count}-REPORTS-"
        f"{total_evidence_count}-ITEMS"
    )


def create_reanalysis_readiness_id(context_label: str | None = None) -> str:
    """Create a deterministic readiness id."""

    _require_optional_string(context_label, "context_label")
    return f"SCREEN3-REANALYSIS-READINESS-{_normalize_token(context_label or 'PHASE-7AO')}"


def validate_evidence_availability_record(
    record: EvidenceAvailabilityRecord,
) -> EvidenceAvailabilityRecord:
    """Validate one evidence availability record."""

    if not isinstance(record, EvidenceAvailabilityRecord):
        raise ReAnalysisReadinessError(
            "record must be an EvidenceAvailabilityRecord instance."
        )
    record.__post_init__()
    return record


def validate_evidence_availability_summary(
    summary: EvidenceAvailabilitySummary,
) -> EvidenceAvailabilitySummary:
    """Validate evidence availability summary metadata."""

    if not isinstance(summary, EvidenceAvailabilitySummary):
        raise ReAnalysisReadinessError(
            "summary must be an EvidenceAvailabilitySummary instance."
        )
    summary.__post_init__()
    return summary


def validate_reanalysis_readiness_result(
    result: ReAnalysisReadinessResult,
) -> ReAnalysisReadinessResult:
    """Validate Screen 3 re-analysis readiness metadata."""

    if not isinstance(result, ReAnalysisReadinessResult):
        raise ReAnalysisReadinessError(
            "result must be a ReAnalysisReadinessResult instance."
        )
    result.__post_init__()
    return result


def classify_evidence_availability(
    record_like: EvidenceAvailabilityRecord | dict[str, Any],
) -> EvidenceAvailabilityRecord:
    """Classify supplied evidence metadata without changing runtime truth."""

    if isinstance(record_like, EvidenceAvailabilityRecord):
        return validate_evidence_availability_record(record_like)
    if not isinstance(record_like, dict):
        raise ReAnalysisReadinessError("record_like must be a mapping or record.")

    evidence_name = _first_text(
        record_like.get("evidence_name"),
        record_like.get("metric_name"),
        record_like.get("name"),
        "unknown_evidence",
    )
    evidence_type = _normalize_supported(
        _first_text(record_like.get("evidence_type"), "unknown"),
        EVIDENCE_TYPES,
        "unknown",
    )
    domain = _optional_text(record_like.get("domain"))
    source_report_id = _optional_text(record_like.get("source_report_id"))
    source_run_id = _optional_text(record_like.get("source_run_id"))
    missing_reason = _normalize_missing_reason(record_like.get("missing_reason"))
    reliability_hint = _normalize_text(record_like.get("reliability"))
    reliability_status = _normalize_supported(
        reliability_hint,
        RELIABILITY_STATUSES,
        "unknown",
    )
    availability_status = _normalize_supported(
        _normalize_text(record_like.get("availability_status")),
        AVAILABILITY_STATUSES,
        "unknown",
    )

    value_present = "value" in record_like and record_like.get("value") is not None
    available_flag = record_like.get("available")
    supported_flag = record_like.get("supported")
    extracted_flag = record_like.get("extracted")

    if supported_flag is False:
        availability_status = "unsupported"
        missing_reason = _unsupported_reason(missing_reason)
        reliability_status = (
            reliability_status if reliability_status != "unknown" else "insufficient_context"
        )
    elif extracted_flag is False:
        availability_status = "not_extracted"
        missing_reason = "parser_gap"
        reliability_status = (
            reliability_status if reliability_status != "unknown" else "insufficient_context"
        )
    elif reliability_hint in ("unreliable", "not_reliable") or reliability_hint == "false":
        availability_status = "not_reliable"
        missing_reason = "value_not_reliable"
        reliability_status = "unreliable"
    elif available_flag is False:
        availability_status = "missing"
        if missing_reason == "unknown":
            missing_reason = "absent_from_report"
        reliability_status = (
            reliability_status if reliability_status != "unknown" else "insufficient_context"
        )
    elif value_present:
        availability_status = "available"
        if reliability_status == "unknown":
            reliability_status = "reliable"
        if missing_reason == "unknown":
            missing_reason = "not_applicable"
    elif availability_status == "unknown":
        availability_status = "unavailable"
        if missing_reason == "unknown":
            missing_reason = "absent_from_report"
        reliability_status = (
            reliability_status if reliability_status != "unknown" else "insufficient_context"
        )

    confidence_impact = _normalize_supported(
        _normalize_text(record_like.get("confidence_impact")),
        CONFIDENCE_IMPACTS,
        _default_confidence_impact(availability_status, evidence_type),
    )
    affects_diagnosis = _optional_bool(
        record_like.get("affects_diagnosis"),
        confidence_impact in ("medium", "high")
        and evidence_type in ("metric", "wait_event", "sql_signal", "trend", "anomaly", "score"),
    )
    affects_comparison = _optional_bool(
        record_like.get("affects_comparison"),
        availability_status != "available",
    )
    parser_review = _optional_bool(
        record_like.get("parser_review_recommended"),
        availability_status == "not_extracted" or missing_reason == "parser_gap",
    )
    source_review = _optional_bool(
        record_like.get("source_review_recommended"),
        missing_reason in ("source_not_collected", "source_misconfigured"),
    )
    scoring_review = _optional_bool(
        record_like.get("scoring_review_recommended"),
        confidence_impact == "high" and evidence_type == "score",
    )
    fallback_evidence = _string_list(record_like.get("fallback_evidence"))

    return EvidenceAvailabilityRecord(
        evidence_id=create_evidence_id(
            evidence_name,
            evidence_type,
            source_report_id=source_report_id,
            source_run_id=source_run_id,
        ),
        evidence_name=evidence_name,
        evidence_type=evidence_type,
        domain=domain,
        source_report_id=source_report_id,
        source_run_id=source_run_id,
        availability_status=availability_status,
        reliability_status=reliability_status,
        missing_reason=missing_reason,
        confidence_impact=confidence_impact,
        affects_diagnosis=affects_diagnosis,
        affects_comparison=affects_comparison,
        parser_review_recommended=parser_review,
        source_review_recommended=source_review,
        scoring_review_recommended=scoring_review,
        fallback_evidence=fallback_evidence,
        notes=_optional_text(record_like.get("notes")),
    )


def build_evidence_availability_summary(
    records: list[EvidenceAvailabilityRecord | dict[str, Any]],
) -> EvidenceAvailabilitySummary:
    """Build a deterministic evidence availability summary."""

    if not isinstance(records, list):
        raise ReAnalysisReadinessError("records must be a list.")
    classified = [classify_evidence_availability(record) for record in records]
    counts = _evidence_summary_counts(classified)
    source_reports = {
        record.source_report_id for record in classified if record.source_report_id
    }
    source_runs = {record.source_run_id for record in classified if record.source_run_id}
    source_report_count = len(source_reports or source_runs)
    confidence_summary = _confidence_summary(classified)
    parser_review = any(record.parser_review_recommended for record in classified)
    source_review = any(record.source_review_recommended for record in classified)
    scoring_review = any(record.scoring_review_recommended for record in classified)
    warnings: list[str] = []
    next_steps: list[str] = []
    if counts["missing_count"]:
        warnings.append("missing or unavailable evidence detected")
        next_steps.append("review evidence availability before future execution")
    if parser_review:
        warnings.append("parser review recommended for one or more evidence items")
        next_steps.append("route parser gaps to future review workflow")
    if source_review:
        warnings.append("source review recommended for one or more evidence items")
        next_steps.append("review source collection/configuration")
    if scoring_review:
        warnings.append("scoring review recommended for high-impact score evidence")
        next_steps.append("review scoring impact before future runtime use")

    return EvidenceAvailabilitySummary(
        summary_id=create_evidence_summary_id(
            source_report_count,
            len(classified),
        ),
        source_report_count=source_report_count,
        total_evidence_count=len(classified),
        available_count=counts["available_count"],
        missing_count=counts["missing_count"],
        unreliable_count=counts["unreliable_count"],
        unsupported_count=counts["unsupported_count"],
        parser_gap_count=counts["parser_gap_count"],
        confidence_impact_summary=confidence_summary,
        parser_review_recommended=parser_review,
        source_review_recommended=source_review,
        scoring_review_recommended=scoring_review,
        records=classified,
        warnings=warnings,
        required_next_steps=next_steps,
    )


def evaluate_reanalysis_readiness(
    *,
    source_selection_ready: bool = True,
    request_model_ready: bool = True,
    controller_ready: bool = True,
    comparison_ready: bool = True,
    missing_metric_handling_ready: bool = True,
    action_ui_preview_only: bool = True,
    evidence_summary: EvidenceAvailabilitySummary | None = None,
    context_label: str | None = None,
) -> ReAnalysisReadinessResult:
    """Evaluate metadata-only readiness for the Screen 3 re-analysis block."""

    for field_name, value in (
        ("source_selection_ready", source_selection_ready),
        ("request_model_ready", request_model_ready),
        ("controller_ready", controller_ready),
        ("comparison_ready", comparison_ready),
        ("missing_metric_handling_ready", missing_metric_handling_ready),
        ("action_ui_preview_only", action_ui_preview_only),
    ):
        _require_bool(value, field_name)
    if evidence_summary is not None:
        validate_evidence_availability_summary(evidence_summary)

    denied: list[str] = []
    warnings: list[str] = []
    next_steps: list[str] = []
    status = "READY_METADATA_ONLY"
    if not source_selection_ready:
        status = "NEEDS_SOURCE_SELECTION"
        denied.append("source selection model is not ready")
        next_steps.append("complete source selection validation")
    elif not request_model_ready:
        status = "NEEDS_REQUEST_VALIDATION"
        denied.append("request model validation is not ready")
        next_steps.append("complete request validation")
    elif not controller_ready:
        status = "NOT_READY"
        denied.append("controller model is not ready")
        next_steps.append("complete controller validation")
    elif not comparison_ready:
        status = "NEEDS_COMPARISON_INPUTS"
        denied.append("comparison validation is not ready")
        next_steps.append("complete in-memory comparison validation")
    elif not missing_metric_handling_ready:
        status = "NEEDS_EVIDENCE_REVIEW"
        denied.append("missing metric handling is not ready")
        next_steps.append("complete evidence availability validation")
    elif not action_ui_preview_only:
        status = "EXECUTION_BLOCKED_IN_THIS_PHASE"
        denied.append("action UI must remain preview-only")
        next_steps.append("disable active action behavior")

    if evidence_summary is not None and (
        evidence_summary.parser_review_recommended
        or evidence_summary.source_review_recommended
        or evidence_summary.scoring_review_recommended
    ):
        warnings.extend(evidence_summary.warnings)
        next_steps.extend(evidence_summary.required_next_steps)

    ready = not denied
    return ReAnalysisReadinessResult(
        readiness_id=create_reanalysis_readiness_id(context_label),
        screen3_reanalysis_ready=ready,
        source_selection_ready=source_selection_ready,
        request_model_ready=request_model_ready,
        controller_ready=controller_ready,
        comparison_ready=comparison_ready,
        missing_metric_handling_ready=missing_metric_handling_ready,
        action_ui_preview_only=action_ui_preview_only,
        backend_execution_performed=False,
        run_analysis_called=False,
        object_storage_called=False,
        local_file_read_performed=False,
        db_lookup_performed=False,
        phase4i_mutated=False,
        dashboard_regenerated=False,
        readiness_status=status,
        denied_reasons=denied,
        warnings=warnings,
        required_next_steps=next_steps,
    )


def evidence_availability_record_to_dict(
    record: EvidenceAvailabilityRecord,
) -> dict[str, Any]:
    """Serialize evidence availability record metadata."""

    record = validate_evidence_availability_record(record)
    return {
        "evidence_id": record.evidence_id,
        "evidence_name": record.evidence_name,
        "evidence_type": record.evidence_type,
        "domain": record.domain,
        "source_report_id": record.source_report_id,
        "source_run_id": record.source_run_id,
        "availability_status": record.availability_status,
        "reliability_status": record.reliability_status,
        "missing_reason": record.missing_reason,
        "confidence_impact": record.confidence_impact,
        "affects_diagnosis": record.affects_diagnosis,
        "affects_comparison": record.affects_comparison,
        "parser_review_recommended": record.parser_review_recommended,
        "source_review_recommended": record.source_review_recommended,
        "scoring_review_recommended": record.scoring_review_recommended,
        "fallback_evidence": list(record.fallback_evidence or []),
        "notes": record.notes,
    }


def evidence_availability_record_from_dict(
    data: dict[str, Any],
) -> EvidenceAvailabilityRecord:
    """Deserialize evidence availability record metadata."""

    _require_mapping(data, "data")
    return EvidenceAvailabilityRecord(
        evidence_id=str(data["evidence_id"]),
        evidence_name=str(data["evidence_name"]),
        evidence_type=str(data["evidence_type"]),
        domain=_optional_text(data.get("domain")),
        source_report_id=_optional_text(data.get("source_report_id")),
        source_run_id=_optional_text(data.get("source_run_id")),
        availability_status=str(data["availability_status"]),
        reliability_status=str(data["reliability_status"]),
        missing_reason=str(data["missing_reason"]),
        confidence_impact=str(data["confidence_impact"]),
        affects_diagnosis=bool(data["affects_diagnosis"]),
        affects_comparison=bool(data["affects_comparison"]),
        parser_review_recommended=bool(data["parser_review_recommended"]),
        source_review_recommended=bool(data["source_review_recommended"]),
        scoring_review_recommended=bool(data["scoring_review_recommended"]),
        fallback_evidence=_string_list(data.get("fallback_evidence")),
        notes=_optional_text(data.get("notes")),
    )


def evidence_availability_summary_to_dict(
    summary: EvidenceAvailabilitySummary,
) -> dict[str, Any]:
    """Serialize evidence availability summary metadata."""

    summary = validate_evidence_availability_summary(summary)
    return {
        "summary_id": summary.summary_id,
        "source_report_count": summary.source_report_count,
        "total_evidence_count": summary.total_evidence_count,
        "available_count": summary.available_count,
        "missing_count": summary.missing_count,
        "unreliable_count": summary.unreliable_count,
        "unsupported_count": summary.unsupported_count,
        "parser_gap_count": summary.parser_gap_count,
        "confidence_impact_summary": summary.confidence_impact_summary,
        "parser_review_recommended": summary.parser_review_recommended,
        "source_review_recommended": summary.source_review_recommended,
        "scoring_review_recommended": summary.scoring_review_recommended,
        "records": [
            evidence_availability_record_to_dict(record) for record in summary.records
        ],
        "warnings": list(summary.warnings),
        "required_next_steps": list(summary.required_next_steps),
    }


def evidence_availability_summary_from_dict(
    data: dict[str, Any],
) -> EvidenceAvailabilitySummary:
    """Deserialize evidence availability summary metadata."""

    _require_mapping(data, "data")
    records = [
        evidence_availability_record_from_dict(item)
        for item in list(data.get("records") or [])
    ]
    return EvidenceAvailabilitySummary(
        summary_id=str(data["summary_id"]),
        source_report_count=int(data["source_report_count"]),
        total_evidence_count=int(data["total_evidence_count"]),
        available_count=int(data["available_count"]),
        missing_count=int(data["missing_count"]),
        unreliable_count=int(data["unreliable_count"]),
        unsupported_count=int(data["unsupported_count"]),
        parser_gap_count=int(data["parser_gap_count"]),
        confidence_impact_summary=str(data["confidence_impact_summary"]),
        parser_review_recommended=bool(data["parser_review_recommended"]),
        source_review_recommended=bool(data["source_review_recommended"]),
        scoring_review_recommended=bool(data["scoring_review_recommended"]),
        records=records,
        warnings=_string_list(data.get("warnings")),
        required_next_steps=_string_list(data.get("required_next_steps")),
    )


def reanalysis_readiness_result_to_dict(
    result: ReAnalysisReadinessResult,
) -> dict[str, Any]:
    """Serialize re-analysis readiness metadata."""

    result = validate_reanalysis_readiness_result(result)
    return {
        "readiness_id": result.readiness_id,
        "screen3_reanalysis_ready": result.screen3_reanalysis_ready,
        "source_selection_ready": result.source_selection_ready,
        "request_model_ready": result.request_model_ready,
        "controller_ready": result.controller_ready,
        "comparison_ready": result.comparison_ready,
        "missing_metric_handling_ready": result.missing_metric_handling_ready,
        "action_ui_preview_only": result.action_ui_preview_only,
        "backend_execution_performed": result.backend_execution_performed,
        "run_analysis_called": result.run_analysis_called,
        "object_storage_called": result.object_storage_called,
        "local_file_read_performed": result.local_file_read_performed,
        "db_lookup_performed": result.db_lookup_performed,
        "phase4i_mutated": result.phase4i_mutated,
        "dashboard_regenerated": result.dashboard_regenerated,
        "readiness_status": result.readiness_status,
        "denied_reasons": list(result.denied_reasons),
        "warnings": list(result.warnings),
        "required_next_steps": list(result.required_next_steps),
    }


def reanalysis_readiness_result_from_dict(
    data: dict[str, Any],
) -> ReAnalysisReadinessResult:
    """Deserialize re-analysis readiness metadata."""

    _require_mapping(data, "data")
    return ReAnalysisReadinessResult(
        readiness_id=str(data["readiness_id"]),
        screen3_reanalysis_ready=bool(data["screen3_reanalysis_ready"]),
        source_selection_ready=bool(data["source_selection_ready"]),
        request_model_ready=bool(data["request_model_ready"]),
        controller_ready=bool(data["controller_ready"]),
        comparison_ready=bool(data["comparison_ready"]),
        missing_metric_handling_ready=bool(data["missing_metric_handling_ready"]),
        action_ui_preview_only=bool(data["action_ui_preview_only"]),
        backend_execution_performed=bool(data["backend_execution_performed"]),
        run_analysis_called=bool(data["run_analysis_called"]),
        object_storage_called=bool(data["object_storage_called"]),
        local_file_read_performed=bool(data["local_file_read_performed"]),
        db_lookup_performed=bool(data["db_lookup_performed"]),
        phase4i_mutated=bool(data["phase4i_mutated"]),
        dashboard_regenerated=bool(data["dashboard_regenerated"]),
        readiness_status=str(data["readiness_status"]),
        denied_reasons=_string_list(data.get("denied_reasons")),
        warnings=_string_list(data.get("warnings")),
        required_next_steps=_string_list(data.get("required_next_steps")),
    )


def _evidence_summary_counts(records: list[EvidenceAvailabilityRecord]) -> dict[str, int]:
    return {
        "total_evidence_count": len(records),
        "available_count": sum(1 for record in records if record.availability_status == "available"),
        "missing_count": sum(
            1 for record in records if record.availability_status in UNAVAILABLE_STATUSES
        ),
        "unreliable_count": sum(
            1
            for record in records
            if record.availability_status == "not_reliable"
            or record.reliability_status in ("partially_reliable", "unreliable")
        ),
        "unsupported_count": sum(
            1 for record in records if record.availability_status == "unsupported"
        ),
        "parser_gap_count": sum(
            1
            for record in records
            if record.availability_status == "not_extracted"
            or record.missing_reason == "parser_gap"
        ),
    }


def _confidence_summary(records: list[EvidenceAvailabilityRecord]) -> str:
    counts = {impact: 0 for impact in CONFIDENCE_IMPACTS}
    for record in records:
        counts[record.confidence_impact] += 1
    return ", ".join(f"{impact}:{counts[impact]}" for impact in CONFIDENCE_IMPACTS)


def _normalize_missing_reason(value: Any) -> str:
    normalized = _normalize_text(value)
    if normalized in MISSING_REASONS:
        return normalized
    if "topology" in normalized:
        return "unsupported_by_topology"
    if "platform" in normalized:
        return "unsupported_by_platform"
    if "parser" in normalized:
        return "parser_gap"
    if "misconfig" in normalized:
        return "source_misconfigured"
    if "not_collected" in normalized or "not collected" in normalized:
        return "source_not_collected"
    if "reliable" in normalized:
        return "value_not_reliable"
    if "absent" in normalized:
        return "absent_from_report"
    return "unknown"


def _unsupported_reason(current_reason: str) -> str:
    if current_reason in ("unsupported_by_topology", "unsupported_by_platform"):
        return current_reason
    return "unsupported_by_topology"


def _default_confidence_impact(availability_status: str, evidence_type: str) -> str:
    if availability_status == "available":
        return "none"
    if evidence_type == "score":
        return "high"
    if evidence_type in ("metric", "wait_event", "sql_signal", "trend", "anomaly"):
        return "medium"
    if availability_status == "unsupported":
        return "low"
    return "unknown"


def _first_text(*values: Any) -> str:
    for value in values:
        text = _optional_text(value)
        if text:
            return text
    return ""


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_text(value: Any) -> str:
    text = _optional_text(value)
    if text is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _normalize_supported(value: str, supported: tuple[str, ...], fallback: str) -> str:
    return value if value in supported else fallback


def _optional_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y")
    return bool(value)


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise ReAnalysisReadinessError(f"{field_name} must be a mapping.")


def _require_nonempty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ReAnalysisReadinessError(f"{field_name} must be a non-empty string.")


def _require_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise ReAnalysisReadinessError(f"{field_name} must be a string or None.")


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        raise ReAnalysisReadinessError(
            f"{field_name} must be one of: {', '.join(supported)}."
        )


def _require_bool(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise ReAnalysisReadinessError(f"{field_name} must be a boolean.")


def _require_nonnegative_int(value: Any, field_name: str) -> None:
    if not isinstance(value, int) or value < 0:
        raise ReAnalysisReadinessError(f"{field_name} must be a non-negative integer.")


def _require_list_of_strings(values: Any, field_name: str) -> None:
    if not isinstance(values, list):
        raise ReAnalysisReadinessError(f"{field_name} must be a list.")
    if not all(isinstance(value, str) for value in values):
        raise ReAnalysisReadinessError(f"{field_name} must contain only strings.")


def _reject_true(value: bool, field_name: str) -> None:
    if value:
        raise ReAnalysisReadinessError(f"{field_name} must remain false in Phase 7AO.")


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text).strip("-")
    return text or "NONE"
