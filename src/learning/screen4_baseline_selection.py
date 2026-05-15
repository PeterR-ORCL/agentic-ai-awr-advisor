"""Phase 7BA Screen 4 historical baseline selection metadata models.

The records in this module describe local metadata for future Screen 4
historical baseline selection. They do not persist records, make baselines
official, implement UI, invoke write paths, execute analysis, modify
dashboards, modify CLI behavior, or mutate deterministic historical truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


HISTORICAL_BASELINE_STATUSES = (
    "proposed",
    "under_review",
    "validated",
    "rejected",
    "insufficient_evidence",
    "superseded",
    "closed",
)

HISTORICAL_EVIDENCE_QUALITY_VALUES = (
    "high",
    "medium",
    "low",
    "insufficient",
    "unknown",
)

HISTORICAL_COMPARISON_PURPOSES = (
    "before_after_tuning",
    "stable_vs_degraded",
    "current_vs_baseline",
    "workload_regression",
    "anomaly_review",
    "trend_review",
    "general_historical_review",
)

HISTORICAL_COMPARISON_TYPES = (
    "single_baseline_to_target",
    "before_after",
    "multi_snapshot_baseline",
    "workload_class_baseline",
    "historical_window_baseline",
)

HISTORICAL_BASELINE_VALIDATION_STATUSES = (
    "valid_metadata_only",
    "invalid",
    "needs_actor",
    "needs_candidate",
    "insufficient_evidence",
    "high_anomaly_risk",
    "high_missing_metric_risk",
    "workload_mismatch",
    "not_official_in_this_phase",
)


class Screen4BaselineSelectionError(ValueError):
    """Raised when Phase 7BA baseline selection metadata is invalid."""


@dataclass(frozen=True)
class HistoricalBaselineCandidate:
    """A possible baseline interval, run, or snapshot for comparison."""

    baseline_candidate_id: str
    baseline_name: str
    run_id: str | None = None
    awr_id: str | None = None
    dbid: str | None = None
    database_name: str | None = None
    snapshot_label: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    workload_class: str | None = None
    stability_score: float = 0.0
    evidence_quality: str = "unknown"
    missing_metric_count: int = 0
    anomaly_count: int = 0
    trend_volatility: float = 0.0
    candidate_status: str = "proposed"
    source_context: dict[str, Any] | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.baseline_candidate_id, "baseline_candidate_id")
        _require_nonempty_string(self.baseline_name, "baseline_name")
        _require_optional_string(self.run_id, "run_id")
        _require_optional_string(self.awr_id, "awr_id")
        _require_optional_string(self.dbid, "dbid")
        _require_optional_string(self.database_name, "database_name")
        _require_optional_string(self.snapshot_label, "snapshot_label")
        _require_optional_string(self.start_time, "start_time")
        _require_optional_string(self.end_time, "end_time")
        _require_optional_string(self.workload_class, "workload_class")
        _require_at_least_one_identifier(
            ("run_id", self.run_id),
            ("awr_id", self.awr_id),
        )
        _require_score_range(self.stability_score, "stability_score")
        _require_supported(
            self.evidence_quality,
            HISTORICAL_EVIDENCE_QUALITY_VALUES,
            "evidence_quality",
        )
        _require_nonnegative_int(self.missing_metric_count, "missing_metric_count")
        _require_nonnegative_int(self.anomaly_count, "anomaly_count")
        _require_nonnegative_number(self.trend_volatility, "trend_volatility")
        _require_supported(
            self.candidate_status,
            HISTORICAL_BASELINE_STATUSES,
            "candidate_status",
        )
        _require_optional_mapping(self.source_context, "source_context")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class HistoricalBaselineSelectionRequest:
    """A future request to select a Screen 4 historical baseline."""

    selection_request_id: str
    candidate_id: str
    requested_by_actor_id: str | None
    actor_audit_context: dict[str, Any] | None = None
    selection_reason: str | None = None
    comparison_purpose: str = "general_historical_review"
    target_run_id: str | None = None
    target_awr_id: str | None = None
    target_snapshot_label: str | None = None
    target_domain: str | None = None
    requested_status: str = "proposed"
    write_performed: bool = False
    baseline_official: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.selection_request_id, "selection_request_id")
        _require_nonempty_string(self.candidate_id, "candidate_id")
        _require_optional_string(self.requested_by_actor_id, "requested_by_actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        _require_optional_string(self.selection_reason, "selection_reason")
        _require_supported(
            self.comparison_purpose,
            HISTORICAL_COMPARISON_PURPOSES,
            "comparison_purpose",
        )
        _require_optional_string(self.target_run_id, "target_run_id")
        _require_optional_string(self.target_awr_id, "target_awr_id")
        _require_optional_string(self.target_snapshot_label, "target_snapshot_label")
        _require_optional_string(self.target_domain, "target_domain")
        _require_supported(
            self.requested_status,
            HISTORICAL_BASELINE_STATUSES,
            "requested_status",
        )
        _require_boolean(self.write_performed, "write_performed")
        _require_boolean(self.baseline_official, "baseline_official")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _require_boolean(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _reject_true(self.write_performed, "write_performed")
        _reject_true(self.baseline_official, "baseline_official")
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class HistoricalBaselineValidation:
    """Validation metadata for a historical baseline selection request."""

    validation_id: str
    selection_request_id: str
    candidate_id: str
    valid: bool
    validation_status: str
    evidence_quality: str
    stability_acceptable: bool
    missing_metric_risk: str
    anomaly_risk: str
    workload_similarity: str
    comparison_valid: bool
    baseline_official: bool = False
    write_performed: bool = False
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.validation_id, "validation_id")
        _require_nonempty_string(self.selection_request_id, "selection_request_id")
        _require_nonempty_string(self.candidate_id, "candidate_id")
        _require_boolean(self.valid, "valid")
        _require_supported(
            self.validation_status,
            HISTORICAL_BASELINE_VALIDATION_STATUSES,
            "validation_status",
        )
        _require_supported(
            self.evidence_quality,
            HISTORICAL_EVIDENCE_QUALITY_VALUES,
            "evidence_quality",
        )
        _require_boolean(self.stability_acceptable, "stability_acceptable")
        _require_nonempty_string(self.missing_metric_risk, "missing_metric_risk")
        _require_nonempty_string(self.anomaly_risk, "anomaly_risk")
        _require_nonempty_string(self.workload_similarity, "workload_similarity")
        _require_boolean(self.comparison_valid, "comparison_valid")
        _require_boolean(self.baseline_official, "baseline_official")
        _require_boolean(self.write_performed, "write_performed")
        _require_string_list(self.denied_reasons, "denied_reasons")
        _require_string_list(self.warnings, "warnings")
        _require_string_list(self.required_next_steps, "required_next_steps")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _require_boolean(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _reject_true(self.baseline_official, "baseline_official")
        _reject_true(self.write_performed, "write_performed")
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class HistoricalComparisonContext:
    """Local metadata describing what a baseline is compared against."""

    comparison_context_id: str
    baseline_candidate_id: str
    target_run_id: str | None = None
    target_awr_id: str | None = None
    comparison_type: str = "single_baseline_to_target"
    comparison_purpose: str = "general_historical_review"
    compared_domains: list[str] = field(default_factory=list)
    baseline_snapshot_label: str | None = None
    target_snapshot_label: str | None = None
    limitations: list[str] = field(default_factory=list)
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.comparison_context_id, "comparison_context_id")
        _require_nonempty_string(self.baseline_candidate_id, "baseline_candidate_id")
        _require_optional_string(self.target_run_id, "target_run_id")
        _require_optional_string(self.target_awr_id, "target_awr_id")
        _require_supported(
            self.comparison_type,
            HISTORICAL_COMPARISON_TYPES,
            "comparison_type",
        )
        _require_supported(
            self.comparison_purpose,
            HISTORICAL_COMPARISON_PURPOSES,
            "comparison_purpose",
        )
        _require_string_list(self.compared_domains, "compared_domains")
        _require_optional_string(
            self.baseline_snapshot_label,
            "baseline_snapshot_label",
        )
        _require_optional_string(self.target_snapshot_label, "target_snapshot_label")
        _require_string_list(self.limitations, "limitations")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _require_boolean(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.notes, "notes")


def create_baseline_candidate_id(
    run_id: str | None = None,
    awr_id: str | None = None,
    snapshot_label: str | None = None,
) -> str:
    """Create a deterministic historical baseline candidate id."""

    _require_optional_string(run_id, "run_id")
    _require_optional_string(awr_id, "awr_id")
    _require_optional_string(snapshot_label, "snapshot_label")
    run_or_awr = run_id or awr_id or "NO-RUN-OR-AWR"
    snapshot = snapshot_label or "NO-SNAPSHOT"
    return (
        "HIST-BASELINE-CANDIDATE-"
        f"{_normalize_token(run_or_awr)}-"
        f"{_normalize_token(snapshot)}"
    )


def create_baseline_selection_request_id(
    candidate_id: str,
    comparison_purpose: str,
) -> str:
    """Create a deterministic baseline selection request id."""

    _require_nonempty_string(candidate_id, "candidate_id")
    _require_supported(
        comparison_purpose,
        HISTORICAL_COMPARISON_PURPOSES,
        "comparison_purpose",
    )
    return (
        "HIST-BASELINE-REQUEST-"
        f"{_normalize_token(candidate_id)}-"
        f"{_normalize_token(comparison_purpose)}"
    )


def create_baseline_validation_id(selection_request_id: str) -> str:
    """Create a deterministic baseline validation id."""

    _require_nonempty_string(selection_request_id, "selection_request_id")
    return f"HIST-BASELINE-VALIDATION-{_normalize_token(selection_request_id)}"


def create_historical_comparison_context_id(
    candidate_id: str,
    target_run_id: str | None = None,
    target_awr_id: str | None = None,
    comparison_type: str | None = None,
) -> str:
    """Create a deterministic historical comparison context id."""

    _require_nonempty_string(candidate_id, "candidate_id")
    _require_optional_string(target_run_id, "target_run_id")
    _require_optional_string(target_awr_id, "target_awr_id")
    if comparison_type is not None:
        _require_supported(
            comparison_type,
            HISTORICAL_COMPARISON_TYPES,
            "comparison_type",
        )
    target = target_run_id or target_awr_id or "NO-TARGET"
    context_type = comparison_type or "single_baseline_to_target"
    return (
        "HIST-COMPARISON-CONTEXT-"
        f"{_normalize_token(candidate_id)}-"
        f"{_normalize_token(target)}-"
        f"{_normalize_token(context_type)}"
    )


def validate_historical_baseline_candidate(
    candidate: HistoricalBaselineCandidate,
) -> HistoricalBaselineCandidate:
    """Validate and return local baseline candidate metadata."""

    if not isinstance(candidate, HistoricalBaselineCandidate):
        raise Screen4BaselineSelectionError(
            "candidate must be a HistoricalBaselineCandidate instance."
        )
    candidate.__post_init__()
    return candidate


def validate_historical_baseline_selection_request(
    request: HistoricalBaselineSelectionRequest,
) -> HistoricalBaselineSelectionRequest:
    """Validate and return local baseline selection request metadata."""

    if not isinstance(request, HistoricalBaselineSelectionRequest):
        raise Screen4BaselineSelectionError(
            "request must be a HistoricalBaselineSelectionRequest instance."
        )
    request.__post_init__()
    _require_nonempty_string(request.requested_by_actor_id, "requested_by_actor_id")
    return request


def validate_historical_baseline_validation(
    validation: HistoricalBaselineValidation,
) -> HistoricalBaselineValidation:
    """Validate and return baseline validation metadata."""

    if not isinstance(validation, HistoricalBaselineValidation):
        raise Screen4BaselineSelectionError(
            "validation must be a HistoricalBaselineValidation instance."
        )
    validation.__post_init__()
    return validation


def validate_historical_comparison_context(
    context: HistoricalComparisonContext,
) -> HistoricalComparisonContext:
    """Validate and return local historical comparison context metadata."""

    if not isinstance(context, HistoricalComparisonContext):
        raise Screen4BaselineSelectionError(
            "context must be a HistoricalComparisonContext instance."
        )
    context.__post_init__()
    return context


def evaluate_baseline_selection(
    candidate: HistoricalBaselineCandidate | None,
    request: HistoricalBaselineSelectionRequest,
) -> HistoricalBaselineValidation:
    """Evaluate baseline metadata without persistence or runtime influence."""

    if not isinstance(request, HistoricalBaselineSelectionRequest):
        raise Screen4BaselineSelectionError(
            "request must be a HistoricalBaselineSelectionRequest instance."
        )
    request.__post_init__()

    denied_reasons: list[str] = []
    warnings: list[str] = [
        "Baseline selection validation is metadata only.",
        "Future governed write path is required before record creation.",
        "Selected baseline is not official in Phase 7BA.",
    ]
    required_next_steps: list[str] = ["keep baseline_official=false"]

    actor_present = bool(_optional_text(request.requested_by_actor_id))
    if not actor_present:
        validation_status = "needs_actor"
        denied_reasons.append("requested_by_actor_id is required")
        required_next_steps.append("provide Phase 7AE actor identity")
        return _baseline_validation_from_status(
            request=request,
            candidate_id=request.candidate_id,
            validation_status=validation_status,
            evidence_quality="unknown",
            stability_acceptable=False,
            missing_metric_risk="unknown",
            anomaly_risk="unknown",
            workload_similarity="unknown",
            comparison_valid=False,
            denied_reasons=denied_reasons,
            warnings=warnings,
            required_next_steps=required_next_steps,
        )

    if candidate is None:
        validation_status = "needs_candidate"
        denied_reasons.append("candidate metadata is required")
        required_next_steps.append("provide baseline candidate metadata")
        return _baseline_validation_from_status(
            request=request,
            candidate_id=request.candidate_id,
            validation_status=validation_status,
            evidence_quality="unknown",
            stability_acceptable=False,
            missing_metric_risk="unknown",
            anomaly_risk="unknown",
            workload_similarity="unknown",
            comparison_valid=False,
            denied_reasons=denied_reasons,
            warnings=warnings,
            required_next_steps=required_next_steps,
        )

    candidate = validate_historical_baseline_candidate(candidate)
    if candidate.baseline_candidate_id != request.candidate_id:
        validation_status = "needs_candidate"
        denied_reasons.append("request candidate_id does not match candidate")
        required_next_steps.append("align request candidate_id with candidate")
    elif candidate.evidence_quality in ("low", "insufficient"):
        validation_status = "insufficient_evidence"
        denied_reasons.append("baseline evidence quality blocks selection")
        required_next_steps.append("select a candidate with stronger evidence")
    elif candidate.missing_metric_count > 0:
        validation_status = "high_missing_metric_risk"
        warnings.append("baseline candidate has missing metrics")
        required_next_steps.append("review missing metric limitations")
    elif candidate.anomaly_count > 0:
        validation_status = "high_anomaly_risk"
        warnings.append("baseline candidate includes anomalies")
        required_next_steps.append("review anomaly limitations")
    elif candidate.stability_score < 50.0:
        validation_status = "insufficient_evidence"
        denied_reasons.append("baseline stability is below threshold")
        required_next_steps.append("select a more stable baseline candidate")
    else:
        validation_status = "valid_metadata_only"
        required_next_steps.append("route through future governed write path")

    stability_acceptable = candidate.stability_score >= 50.0
    missing_metric_risk = "high" if candidate.missing_metric_count > 0 else "none"
    anomaly_risk = "high" if candidate.anomaly_count > 0 else "none"
    workload_similarity = "not_evaluated"
    comparison_valid = validation_status == "valid_metadata_only"

    return _baseline_validation_from_status(
        request=request,
        candidate_id=candidate.baseline_candidate_id,
        validation_status=validation_status,
        evidence_quality=candidate.evidence_quality,
        stability_acceptable=stability_acceptable,
        missing_metric_risk=missing_metric_risk,
        anomaly_risk=anomaly_risk,
        workload_similarity=workload_similarity,
        comparison_valid=comparison_valid,
        denied_reasons=denied_reasons,
        warnings=warnings,
        required_next_steps=required_next_steps,
    )


def historical_baseline_candidate_to_dict(
    candidate: HistoricalBaselineCandidate,
) -> dict[str, Any]:
    """Serialize baseline candidate metadata to a deterministic dict."""

    candidate = validate_historical_baseline_candidate(candidate)
    return {
        "baseline_candidate_id": candidate.baseline_candidate_id,
        "baseline_name": candidate.baseline_name,
        "run_id": candidate.run_id,
        "awr_id": candidate.awr_id,
        "dbid": candidate.dbid,
        "database_name": candidate.database_name,
        "snapshot_label": candidate.snapshot_label,
        "start_time": candidate.start_time,
        "end_time": candidate.end_time,
        "workload_class": candidate.workload_class,
        "stability_score": candidate.stability_score,
        "evidence_quality": candidate.evidence_quality,
        "missing_metric_count": candidate.missing_metric_count,
        "anomaly_count": candidate.anomaly_count,
        "trend_volatility": candidate.trend_volatility,
        "candidate_status": candidate.candidate_status,
        "source_context": _copy_optional_mapping(candidate.source_context),
        "notes": candidate.notes,
    }


def historical_baseline_candidate_from_dict(
    data: dict[str, Any],
) -> HistoricalBaselineCandidate:
    """Deserialize baseline candidate metadata from a dictionary."""

    _require_mapping(data, "candidate")
    return HistoricalBaselineCandidate(
        baseline_candidate_id=str(data["baseline_candidate_id"]),
        baseline_name=str(data["baseline_name"]),
        run_id=_optional_text(data.get("run_id")),
        awr_id=_optional_text(data.get("awr_id")),
        dbid=_optional_text(data.get("dbid")),
        database_name=_optional_text(data.get("database_name")),
        snapshot_label=_optional_text(data.get("snapshot_label")),
        start_time=_optional_text(data.get("start_time")),
        end_time=_optional_text(data.get("end_time")),
        workload_class=_optional_text(data.get("workload_class")),
        stability_score=float(data.get("stability_score", 0.0)),
        evidence_quality=str(data.get("evidence_quality", "unknown")),
        missing_metric_count=int(data.get("missing_metric_count", 0)),
        anomaly_count=int(data.get("anomaly_count", 0)),
        trend_volatility=float(data.get("trend_volatility", 0.0)),
        candidate_status=str(data.get("candidate_status", "proposed")),
        source_context=_copy_optional_mapping(data.get("source_context")),
        notes=_optional_text(data.get("notes")),
    )


def historical_baseline_selection_request_to_dict(
    request: HistoricalBaselineSelectionRequest,
) -> dict[str, Any]:
    """Serialize baseline selection request metadata."""

    request = validate_historical_baseline_selection_request(request)
    return {
        "selection_request_id": request.selection_request_id,
        "candidate_id": request.candidate_id,
        "requested_by_actor_id": request.requested_by_actor_id,
        "actor_audit_context": _copy_optional_mapping(request.actor_audit_context),
        "selection_reason": request.selection_reason,
        "comparison_purpose": request.comparison_purpose,
        "target_run_id": request.target_run_id,
        "target_awr_id": request.target_awr_id,
        "target_snapshot_label": request.target_snapshot_label,
        "target_domain": request.target_domain,
        "requested_status": request.requested_status,
        "write_performed": request.write_performed,
        "baseline_official": request.baseline_official,
        "runtime_influence": request.runtime_influence,
        "phase4i_mutation_requested": request.phase4i_mutation_requested,
        "created_at": request.created_at,
        "notes": request.notes,
    }


def historical_baseline_selection_request_from_dict(
    data: dict[str, Any],
) -> HistoricalBaselineSelectionRequest:
    """Deserialize baseline selection request metadata from a dictionary."""

    _require_mapping(data, "selection_request")
    return HistoricalBaselineSelectionRequest(
        selection_request_id=str(data["selection_request_id"]),
        candidate_id=str(data["candidate_id"]),
        requested_by_actor_id=str(data["requested_by_actor_id"]),
        actor_audit_context=_copy_optional_mapping(data.get("actor_audit_context")),
        selection_reason=_optional_text(data.get("selection_reason")),
        comparison_purpose=str(
            data.get("comparison_purpose", "general_historical_review")
        ),
        target_run_id=_optional_text(data.get("target_run_id")),
        target_awr_id=_optional_text(data.get("target_awr_id")),
        target_snapshot_label=_optional_text(data.get("target_snapshot_label")),
        target_domain=_optional_text(data.get("target_domain")),
        requested_status=str(data.get("requested_status", "proposed")),
        write_performed=_bool_from_mapping(data, "write_performed", False),
        baseline_official=_bool_from_mapping(data, "baseline_official", False),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        created_at=_optional_text(data.get("created_at")),
        notes=_optional_text(data.get("notes")),
    )


def historical_baseline_validation_to_dict(
    validation: HistoricalBaselineValidation,
) -> dict[str, Any]:
    """Serialize baseline validation metadata."""

    validation = validate_historical_baseline_validation(validation)
    return {
        "validation_id": validation.validation_id,
        "selection_request_id": validation.selection_request_id,
        "candidate_id": validation.candidate_id,
        "valid": validation.valid,
        "validation_status": validation.validation_status,
        "evidence_quality": validation.evidence_quality,
        "stability_acceptable": validation.stability_acceptable,
        "missing_metric_risk": validation.missing_metric_risk,
        "anomaly_risk": validation.anomaly_risk,
        "workload_similarity": validation.workload_similarity,
        "comparison_valid": validation.comparison_valid,
        "baseline_official": validation.baseline_official,
        "write_performed": validation.write_performed,
        "denied_reasons": list(validation.denied_reasons),
        "warnings": list(validation.warnings),
        "required_next_steps": list(validation.required_next_steps),
        "runtime_influence": validation.runtime_influence,
        "phase4i_mutation_requested": validation.phase4i_mutation_requested,
        "notes": validation.notes,
    }


def historical_baseline_validation_from_dict(
    data: dict[str, Any],
) -> HistoricalBaselineValidation:
    """Deserialize baseline validation metadata from a dictionary."""

    _require_mapping(data, "validation")
    return HistoricalBaselineValidation(
        validation_id=str(data["validation_id"]),
        selection_request_id=str(data["selection_request_id"]),
        candidate_id=str(data["candidate_id"]),
        valid=_bool_from_mapping(data, "valid", False),
        validation_status=str(data["validation_status"]),
        evidence_quality=str(data["evidence_quality"]),
        stability_acceptable=_bool_from_mapping(
            data,
            "stability_acceptable",
            False,
        ),
        missing_metric_risk=str(data["missing_metric_risk"]),
        anomaly_risk=str(data["anomaly_risk"]),
        workload_similarity=str(data["workload_similarity"]),
        comparison_valid=_bool_from_mapping(data, "comparison_valid", False),
        baseline_official=_bool_from_mapping(data, "baseline_official", False),
        write_performed=_bool_from_mapping(data, "write_performed", False),
        denied_reasons=list(data.get("denied_reasons") or []),
        warnings=list(data.get("warnings") or []),
        required_next_steps=list(data.get("required_next_steps") or []),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        notes=_optional_text(data.get("notes")),
    )


def historical_comparison_context_to_dict(
    context: HistoricalComparisonContext,
) -> dict[str, Any]:
    """Serialize historical comparison context metadata."""

    context = validate_historical_comparison_context(context)
    return {
        "comparison_context_id": context.comparison_context_id,
        "baseline_candidate_id": context.baseline_candidate_id,
        "target_run_id": context.target_run_id,
        "target_awr_id": context.target_awr_id,
        "comparison_type": context.comparison_type,
        "comparison_purpose": context.comparison_purpose,
        "compared_domains": list(context.compared_domains),
        "baseline_snapshot_label": context.baseline_snapshot_label,
        "target_snapshot_label": context.target_snapshot_label,
        "limitations": list(context.limitations),
        "runtime_influence": context.runtime_influence,
        "phase4i_mutation_requested": context.phase4i_mutation_requested,
        "notes": context.notes,
    }


def historical_comparison_context_from_dict(
    data: dict[str, Any],
) -> HistoricalComparisonContext:
    """Deserialize historical comparison context metadata from a dict."""

    _require_mapping(data, "comparison_context")
    return HistoricalComparisonContext(
        comparison_context_id=str(data["comparison_context_id"]),
        baseline_candidate_id=str(data["baseline_candidate_id"]),
        target_run_id=_optional_text(data.get("target_run_id")),
        target_awr_id=_optional_text(data.get("target_awr_id")),
        comparison_type=str(data.get("comparison_type", "single_baseline_to_target")),
        comparison_purpose=str(
            data.get("comparison_purpose", "general_historical_review")
        ),
        compared_domains=list(data.get("compared_domains") or []),
        baseline_snapshot_label=_optional_text(data.get("baseline_snapshot_label")),
        target_snapshot_label=_optional_text(data.get("target_snapshot_label")),
        limitations=list(data.get("limitations") or []),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        notes=_optional_text(data.get("notes")),
    )


def _baseline_validation_from_status(
    *,
    request: HistoricalBaselineSelectionRequest,
    candidate_id: str,
    validation_status: str,
    evidence_quality: str,
    stability_acceptable: bool,
    missing_metric_risk: str,
    anomaly_risk: str,
    workload_similarity: str,
    comparison_valid: bool,
    denied_reasons: list[str],
    warnings: list[str],
    required_next_steps: list[str],
) -> HistoricalBaselineValidation:
    return HistoricalBaselineValidation(
        validation_id=create_baseline_validation_id(request.selection_request_id),
        selection_request_id=request.selection_request_id,
        candidate_id=candidate_id,
        valid=validation_status == "valid_metadata_only",
        validation_status=validation_status,
        evidence_quality=evidence_quality,
        stability_acceptable=stability_acceptable,
        missing_metric_risk=missing_metric_risk,
        anomaly_risk=anomaly_risk,
        workload_similarity=workload_similarity,
        comparison_valid=comparison_valid,
        baseline_official=False,
        write_performed=False,
        denied_reasons=list(denied_reasons),
        warnings=list(warnings),
        required_next_steps=list(required_next_steps),
        runtime_influence=False,
        phase4i_mutation_requested=False,
        notes=request.notes,
    )


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _bool_from_mapping(data: dict[str, Any], field_name: str, default: bool) -> bool:
    value = data.get(field_name, default)
    if isinstance(value, bool):
        return value
    raise Screen4BaselineSelectionError(f"{field_name} must be a boolean.")


def _copy_optional_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Screen4BaselineSelectionError(
            "mapping value must be a dictionary."
        )
    return dict(value)


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise Screen4BaselineSelectionError(f"{field_name} must be a mapping.")


def _require_optional_mapping(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, dict):
        raise Screen4BaselineSelectionError(
            f"{field_name} must be a mapping or None."
        )


def _require_nonempty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise Screen4BaselineSelectionError(
            f"{field_name} must be a non-empty string."
        )


def _require_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise Screen4BaselineSelectionError(
            f"{field_name} must be a string or None."
        )


def _require_at_least_one_identifier(*pairs: tuple[str, str | None]) -> None:
    if not any(_optional_text(value) for _, value in pairs):
        names = ", ".join(name for name, _ in pairs)
        raise Screen4BaselineSelectionError(
            f"at least one of {names} is required."
        )


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        raise Screen4BaselineSelectionError(
            f"{field_name} must be one of: {', '.join(supported)}."
        )


def _require_score_range(value: Any, field_name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise Screen4BaselineSelectionError(f"{field_name} must be numeric.")
    if value < 0.0 or value > 100.0:
        raise Screen4BaselineSelectionError(
            f"{field_name} must be between 0.0 and 100.0."
        )


def _require_nonnegative_int(value: Any, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise Screen4BaselineSelectionError(f"{field_name} must be an integer.")
    if value < 0:
        raise Screen4BaselineSelectionError(f"{field_name} must be >= 0.")


def _require_nonnegative_number(value: Any, field_name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise Screen4BaselineSelectionError(f"{field_name} must be numeric.")
    if value < 0.0:
        raise Screen4BaselineSelectionError(f"{field_name} must be >= 0.0.")


def _require_boolean(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise Screen4BaselineSelectionError(f"{field_name} must be a boolean.")


def _require_string_list(value: Any, field_name: str) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise Screen4BaselineSelectionError(
            f"{field_name} must be a list of strings."
        )


def _reject_true(value: bool, field_name: str) -> None:
    if value:
        raise Screen4BaselineSelectionError(
            f"{field_name} must remain false in Phase 7BA."
        )


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text).strip("-")
    return text or "NONE"
