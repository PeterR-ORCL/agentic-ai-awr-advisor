"""Deterministic Phase 7U trend-aware scoring helpers.

This module implements local advisory Score(x, t) support only. It does not
replace runtime scoring, modify thresholds, change parser output, change
decisions, change recommendations, train models, call services, write
databases, or activate runtime behavior.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


TREND_DIRECTIONS = (
    "improving",
    "stable",
    "degrading",
    "volatile",
    "insufficient_data",
)

ANOMALY_PATTERNS = (
    "none",
    "isolated",
    "recurring",
    "severe",
    "noisy",
    "insufficient_data",
)

TREND_AWARE_SCORING_STATUSES = (
    "SHADOW_ONLY",
    "ADVISORY_ONLY",
    "INSUFFICIENT_CONTEXT",
)

DOMAIN_NAMES = (
    "CPU",
    "IO",
    "MEMORY",
    "COMMIT",
    "RAC",
    "ADG",
)

TREND_CONTEXT_FIELDS = (
    "trend_id",
    "domain",
    "trend_direction",
    "trend_strength",
    "trend_window",
    "trend_confidence",
    "trend_signal_count",
    "evidence_reference",
    "notes",
)

ANOMALY_CONTEXT_FIELDS = (
    "anomaly_id",
    "domain",
    "anomaly_count",
    "anomaly_severity",
    "anomaly_confidence",
    "anomaly_pattern",
    "recurrence_count",
    "evidence_reference",
    "notes",
)

TREND_AWARE_INPUT_FIELDS = (
    "input_id",
    "run_id",
    "awr_id",
    "domain",
    "baseline_score",
    "trend_context",
    "anomaly_context",
    "feature_reference",
    "score_version",
    "runtime_influence",
    "runtime_active",
)

TREND_AWARE_RESULT_FIELDS = (
    "result_id",
    "input_id",
    "domain",
    "baseline_score",
    "trend_aware_score",
    "score_delta",
    "trend_influence",
    "anomaly_influence",
    "advisory_status",
    "explanation",
    "confidence",
    "runtime_influence",
    "runtime_active",
    "deterministic_runtime_remains_authoritative",
)

MAX_TREND_INFLUENCE = 12.0
MAX_ANOMALY_INFLUENCE = 15.0
MAX_CONFIDENCE = 0.95


class TrendAwareScoringError(ValueError):
    """Raised when Phase 7U trend-aware scoring rules are violated."""


@dataclass(frozen=True)
class TrendContext:
    """Explicit local trend context for advisory Score(x, t)."""

    trend_id: str
    domain: str
    trend_direction: str
    trend_strength: float
    trend_window: str | None
    trend_confidence: float
    trend_signal_count: int
    evidence_reference: str | None
    notes: str | None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.trend_id, "trend_id")
        domain = _normalize_domain(self.domain)
        trend_direction = _normalize_token(self.trend_direction, "trend_direction")
        _validate_trend_direction(trend_direction)
        _validate_numeric_range(self.trend_strength, "trend_strength", 0.0, 1.0)
        _validate_optional_string(self.trend_window, "trend_window")
        _validate_numeric_range(self.trend_confidence, "trend_confidence", 0.0, 1.0)
        _validate_nonnegative_int(self.trend_signal_count, "trend_signal_count")
        _validate_optional_string(self.evidence_reference, "evidence_reference")
        _validate_optional_string(self.notes, "notes")
        object.__setattr__(self, "domain", domain)
        object.__setattr__(self, "trend_direction", trend_direction)
        object.__setattr__(self, "trend_strength", float(self.trend_strength))
        object.__setattr__(self, "trend_confidence", float(self.trend_confidence))


@dataclass(frozen=True)
class AnomalyContext:
    """Explicit local anomaly context for advisory Score(x, t)."""

    anomaly_id: str
    domain: str
    anomaly_count: int
    anomaly_severity: float
    anomaly_confidence: float
    anomaly_pattern: str
    recurrence_count: int
    evidence_reference: str | None
    notes: str | None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.anomaly_id, "anomaly_id")
        domain = _normalize_domain(self.domain)
        _validate_nonnegative_int(self.anomaly_count, "anomaly_count")
        _validate_numeric_range(self.anomaly_severity, "anomaly_severity", 0.0, 1.0)
        _validate_numeric_range(
            self.anomaly_confidence,
            "anomaly_confidence",
            0.0,
            1.0,
        )
        anomaly_pattern = _normalize_token(self.anomaly_pattern, "anomaly_pattern")
        _validate_anomaly_pattern(anomaly_pattern)
        _validate_nonnegative_int(self.recurrence_count, "recurrence_count")
        _validate_optional_string(self.evidence_reference, "evidence_reference")
        _validate_optional_string(self.notes, "notes")
        object.__setattr__(self, "domain", domain)
        object.__setattr__(self, "anomaly_severity", float(self.anomaly_severity))
        object.__setattr__(self, "anomaly_confidence", float(self.anomaly_confidence))
        object.__setattr__(self, "anomaly_pattern", anomaly_pattern)


@dataclass(frozen=True)
class TrendAwareScoringInput:
    """Serializable local advisory scoring input for baseline Score(x) plus t."""

    input_id: str
    run_id: str | None
    awr_id: str | None
    domain: str
    baseline_score: float
    trend_context: TrendContext | None
    anomaly_context: AnomalyContext | None
    feature_reference: str | None
    score_version: str
    runtime_influence: bool
    runtime_active: bool

    def __post_init__(self) -> None:
        _require_non_empty_string(self.input_id, "input_id")
        _validate_optional_string(self.run_id, "run_id")
        _validate_optional_string(self.awr_id, "awr_id")
        _require_any_identifier(self.run_id, self.awr_id)
        domain = _normalize_domain(self.domain)
        _validate_numeric_range(self.baseline_score, "baseline_score", 0.0, 100.0)
        trend_context = (
            None
            if self.trend_context is None
            else validate_trend_context(self.trend_context)
        )
        anomaly_context = (
            None
            if self.anomaly_context is None
            else validate_anomaly_context(self.anomaly_context)
        )
        if trend_context is not None and trend_context.domain != domain:
            raise TrendAwareScoringError(
                "trend_context domain must match trend-aware scoring input domain."
            )
        if anomaly_context is not None and anomaly_context.domain != domain:
            raise TrendAwareScoringError(
                "anomaly_context domain must match trend-aware scoring input domain."
            )
        _validate_optional_string(self.feature_reference, "feature_reference")
        _require_non_empty_string(self.score_version, "score_version")
        if self.runtime_influence is not False:
            raise TrendAwareScoringError(
                "Phase 7U trend-aware scoring inputs must keep runtime_influence=false."
            )
        if self.runtime_active is not False:
            raise TrendAwareScoringError(
                "Phase 7U trend-aware scoring inputs must keep runtime_active=false."
            )
        object.__setattr__(self, "domain", domain)
        object.__setattr__(self, "baseline_score", float(self.baseline_score))
        object.__setattr__(self, "trend_context", trend_context)
        object.__setattr__(self, "anomaly_context", anomaly_context)
        object.__setattr__(self, "runtime_influence", False)
        object.__setattr__(self, "runtime_active", False)


@dataclass(frozen=True)
class TrendAwareScoreResult:
    """Serializable advisory result; it never becomes runtime score truth."""

    result_id: str
    input_id: str
    domain: str
    baseline_score: float
    trend_aware_score: float
    score_delta: float
    trend_influence: float
    anomaly_influence: float
    advisory_status: str
    explanation: str
    confidence: float
    runtime_influence: bool
    runtime_active: bool
    deterministic_runtime_remains_authoritative: bool

    def __post_init__(self) -> None:
        _require_non_empty_string(self.result_id, "result_id")
        _require_non_empty_string(self.input_id, "input_id")
        domain = _normalize_domain(self.domain)
        _validate_numeric_range(self.baseline_score, "baseline_score", 0.0, 100.0)
        _validate_numeric_range(
            self.trend_aware_score,
            "trend_aware_score",
            0.0,
            100.0,
        )
        _validate_numeric(self.score_delta, "score_delta")
        expected_delta = _round_score(
            float(self.trend_aware_score) - float(self.baseline_score)
        )
        if _round_score(self.score_delta) != expected_delta:
            raise TrendAwareScoringError(
                "score_delta must equal trend_aware_score minus baseline_score."
            )
        _validate_numeric(self.trend_influence, "trend_influence")
        _validate_numeric(self.anomaly_influence, "anomaly_influence")
        _validate_advisory_status(self.advisory_status)
        _require_non_empty_string(self.explanation, "explanation")
        _validate_numeric_range(self.confidence, "confidence", 0.0, MAX_CONFIDENCE)
        if self.runtime_influence is not False:
            raise TrendAwareScoringError(
                "Phase 7U trend-aware scoring results must keep runtime_influence=false."
            )
        if self.runtime_active is not False:
            raise TrendAwareScoringError(
                "Phase 7U trend-aware scoring results must keep runtime_active=false."
            )
        if self.deterministic_runtime_remains_authoritative is not True:
            raise TrendAwareScoringError(
                "Deterministic runtime must remain authoritative for Phase 7U results."
            )
        object.__setattr__(self, "domain", domain)
        object.__setattr__(self, "baseline_score", float(self.baseline_score))
        object.__setattr__(
            self,
            "trend_aware_score",
            float(self.trend_aware_score),
        )
        object.__setattr__(self, "score_delta", float(self.score_delta))
        object.__setattr__(self, "trend_influence", float(self.trend_influence))
        object.__setattr__(self, "anomaly_influence", float(self.anomaly_influence))
        object.__setattr__(self, "confidence", float(self.confidence))
        object.__setattr__(self, "runtime_influence", False)
        object.__setattr__(self, "runtime_active", False)
        object.__setattr__(
            self,
            "deterministic_runtime_remains_authoritative",
            True,
        )


def create_trend_id(
    domain: str,
    trend_direction: str,
    trend_window: str | None = None,
) -> str:
    """Create a deterministic trend context identifier from stable inputs."""

    normalized_domain = _normalize_domain(domain)
    normalized_direction = _normalize_token(trend_direction, "trend_direction")
    _validate_trend_direction(normalized_direction)
    _validate_optional_string(trend_window, "trend_window")
    window = trend_window if _has_text(trend_window) else "none"
    return (
        f"TREND-{_identifier_fragment(normalized_domain)}-"
        f"{_identifier_fragment(normalized_direction)}-"
        f"{_identifier_fragment(window)}"
    )


def create_anomaly_id(
    domain: str,
    anomaly_pattern: str,
    recurrence_count: int = 0,
) -> str:
    """Create a deterministic anomaly context identifier from stable inputs."""

    normalized_domain = _normalize_domain(domain)
    normalized_pattern = _normalize_token(anomaly_pattern, "anomaly_pattern")
    _validate_anomaly_pattern(normalized_pattern)
    _validate_nonnegative_int(recurrence_count, "recurrence_count")
    return (
        f"ANOMALY-{_identifier_fragment(normalized_domain)}-"
        f"{_identifier_fragment(normalized_pattern)}-"
        f"R{recurrence_count}"
    )


def create_trend_aware_input_id(
    run_id: str | None,
    awr_id: str | None,
    domain: str,
    score_version: str,
) -> str:
    """Create a deterministic advisory scoring input identifier."""

    _validate_optional_string(run_id, "run_id")
    _validate_optional_string(awr_id, "awr_id")
    _require_any_identifier(run_id, awr_id)
    normalized_domain = _normalize_domain(domain)
    _require_non_empty_string(score_version, "score_version")
    source_id = run_id if _has_text(run_id) else awr_id
    return (
        f"TREND-AWARE-INPUT-{_identifier_fragment(score_version)}-"
        f"{_identifier_fragment(source_id)}-"
        f"{_identifier_fragment(normalized_domain)}"
    )


def create_trend_aware_result_id(input_id: str, score_version: str) -> str:
    """Create a deterministic advisory score result identifier."""

    _require_non_empty_string(input_id, "input_id")
    _require_non_empty_string(score_version, "score_version")
    digest = _stable_hash((input_id, score_version))
    return (
        f"TREND-AWARE-RESULT-{_identifier_fragment(score_version)}-"
        f"{_identifier_fragment(input_id)}-{digest}"
    )


def validate_trend_context(
    context: TrendContext | Mapping[str, Any],
) -> TrendContext:
    """Validate and return explicit local trend context."""

    if isinstance(context, Mapping):
        return trend_context_from_dict(context)
    if not isinstance(context, TrendContext):
        raise TrendAwareScoringError("context must be a TrendContext.")
    return TrendContext(**trend_context_to_dict(context))


def validate_anomaly_context(
    context: AnomalyContext | Mapping[str, Any],
) -> AnomalyContext:
    """Validate and return explicit local anomaly context."""

    if isinstance(context, Mapping):
        return anomaly_context_from_dict(context)
    if not isinstance(context, AnomalyContext):
        raise TrendAwareScoringError("context must be an AnomalyContext.")
    return AnomalyContext(**anomaly_context_to_dict(context))


def validate_trend_aware_scoring_input(
    input_record: TrendAwareScoringInput | Mapping[str, Any],
) -> TrendAwareScoringInput:
    """Validate and return a local advisory trend-aware scoring input."""

    if isinstance(input_record, Mapping):
        return trend_aware_input_from_dict(input_record)
    if not isinstance(input_record, TrendAwareScoringInput):
        raise TrendAwareScoringError(
            "input_record must be a TrendAwareScoringInput."
        )
    return TrendAwareScoringInput(**trend_aware_input_to_dict(input_record))


def compute_trend_influence(trend_context: TrendContext | Mapping[str, Any] | None) -> float:
    """Compute a bounded deterministic trend adjustment for advisory scoring."""

    if trend_context is None:
        return 0.0
    context = validate_trend_context(trend_context)
    confidence = context.trend_confidence
    strength = context.trend_strength
    if context.trend_direction == "improving":
        adjustment = -MAX_TREND_INFLUENCE * strength * confidence
    elif context.trend_direction == "stable":
        adjustment = 0.0
    elif context.trend_direction == "degrading":
        adjustment = MAX_TREND_INFLUENCE * strength * confidence
    elif context.trend_direction == "volatile":
        adjustment = 8.0 * (0.5 + (strength / 2.0)) * confidence
    else:
        adjustment = 0.0
    return _round_score(_clamp(adjustment, -MAX_TREND_INFLUENCE, MAX_TREND_INFLUENCE))


def compute_anomaly_influence(
    anomaly_context: AnomalyContext | Mapping[str, Any] | None,
) -> float:
    """Compute a bounded deterministic anomaly adjustment for advisory scoring."""

    if anomaly_context is None:
        return 0.0
    context = validate_anomaly_context(anomaly_context)
    base_weights = {
        "none": 0.0,
        "isolated": 4.0,
        "recurring": 8.0,
        "severe": 14.0,
        "noisy": 3.0,
        "insufficient_data": 0.0,
    }
    base = base_weights[context.anomaly_pattern]
    if base == 0.0:
        return 0.0

    count_bonus = min(context.anomaly_count, 5) * 0.2
    recurrence_bonus = 0.0
    if context.anomaly_pattern in ("recurring", "severe"):
        recurrence_bonus = min(context.recurrence_count, 4) * 0.75
    adjustment = (
        (base * context.anomaly_severity * context.anomaly_confidence)
        + count_bonus
        + recurrence_bonus
    )
    return _round_score(_clamp(adjustment, 0.0, MAX_ANOMALY_INFLUENCE))


def compute_trend_aware_score(
    input_record: TrendAwareScoringInput | Mapping[str, Any],
) -> TrendAwareScoreResult:
    """Compute deterministic advisory Score(x, t) without runtime mutation."""

    validated = validate_trend_aware_scoring_input(input_record)
    trend_influence = compute_trend_influence(validated.trend_context)
    anomaly_influence = compute_anomaly_influence(validated.anomaly_context)
    trend_aware_score = _round_score(
        _clamp(
            validated.baseline_score + trend_influence + anomaly_influence,
            0.0,
            100.0,
        )
    )
    score_delta = _round_score(trend_aware_score - validated.baseline_score)
    advisory_status = _advisory_status(validated, score_delta)
    confidence = _result_confidence(validated)
    explanation = _explanation(
        validated,
        trend_influence,
        anomaly_influence,
        score_delta,
        advisory_status,
    )
    result = TrendAwareScoreResult(
        result_id=create_trend_aware_result_id(
            validated.input_id,
            validated.score_version,
        ),
        input_id=validated.input_id,
        domain=validated.domain,
        baseline_score=validated.baseline_score,
        trend_aware_score=trend_aware_score,
        score_delta=score_delta,
        trend_influence=trend_influence,
        anomaly_influence=anomaly_influence,
        advisory_status=advisory_status,
        explanation=explanation,
        confidence=confidence,
        runtime_influence=False,
        runtime_active=False,
        deterministic_runtime_remains_authoritative=True,
    )
    return validate_trend_aware_score_result(result)


def validate_trend_aware_score_result(
    result: TrendAwareScoreResult | Mapping[str, Any],
) -> TrendAwareScoreResult:
    """Validate an advisory trend-aware scoring result."""

    if isinstance(result, Mapping):
        return trend_aware_score_result_from_dict(result)
    if not isinstance(result, TrendAwareScoreResult):
        raise TrendAwareScoringError("result must be a TrendAwareScoreResult.")
    validated = TrendAwareScoreResult(**trend_aware_score_result_to_dict(result))
    expected_delta = _round_score(validated.trend_aware_score - validated.baseline_score)
    if _round_score(validated.score_delta) != expected_delta:
        raise TrendAwareScoringError(
            "score_delta must equal trend_aware_score minus baseline_score."
        )
    return validated


def trend_context_to_dict(context: TrendContext) -> dict[str, object]:
    """Return a deterministic dictionary for one trend context."""

    if not isinstance(context, TrendContext):
        raise TrendAwareScoringError("context must be a TrendContext.")
    return {
        field_name: deepcopy(getattr(context, field_name))
        for field_name in TREND_CONTEXT_FIELDS
    }


def trend_context_from_dict(data: Mapping[str, Any]) -> TrendContext:
    """Reconstruct and validate one trend context from dictionary data."""

    if not isinstance(data, Mapping):
        raise TrendAwareScoringError("trend context data must be a mapping.")
    _reject_runtime_activation_fields(data)
    values = _values_from_mapping(
        data,
        TREND_CONTEXT_FIELDS,
        optional_defaults={
            "trend_window": None,
            "evidence_reference": None,
            "notes": None,
        },
    )
    return TrendContext(**values)


def anomaly_context_to_dict(context: AnomalyContext) -> dict[str, object]:
    """Return a deterministic dictionary for one anomaly context."""

    if not isinstance(context, AnomalyContext):
        raise TrendAwareScoringError("context must be an AnomalyContext.")
    return {
        field_name: deepcopy(getattr(context, field_name))
        for field_name in ANOMALY_CONTEXT_FIELDS
    }


def anomaly_context_from_dict(data: Mapping[str, Any]) -> AnomalyContext:
    """Reconstruct and validate one anomaly context from dictionary data."""

    if not isinstance(data, Mapping):
        raise TrendAwareScoringError("anomaly context data must be a mapping.")
    _reject_runtime_activation_fields(data)
    values = _values_from_mapping(
        data,
        ANOMALY_CONTEXT_FIELDS,
        optional_defaults={
            "evidence_reference": None,
            "notes": None,
        },
    )
    return AnomalyContext(**values)


def trend_aware_input_to_dict(
    input_record: TrendAwareScoringInput,
) -> dict[str, object]:
    """Return a deterministic dictionary for one advisory scoring input."""

    if not isinstance(input_record, TrendAwareScoringInput):
        raise TrendAwareScoringError(
            "input_record must be a TrendAwareScoringInput."
        )
    return {
        "input_id": input_record.input_id,
        "run_id": input_record.run_id,
        "awr_id": input_record.awr_id,
        "domain": input_record.domain,
        "baseline_score": input_record.baseline_score,
        "trend_context": (
            None
            if input_record.trend_context is None
            else trend_context_to_dict(input_record.trend_context)
        ),
        "anomaly_context": (
            None
            if input_record.anomaly_context is None
            else anomaly_context_to_dict(input_record.anomaly_context)
        ),
        "feature_reference": input_record.feature_reference,
        "score_version": input_record.score_version,
        "runtime_influence": False,
        "runtime_active": False,
    }


def trend_aware_input_from_dict(data: Mapping[str, Any]) -> TrendAwareScoringInput:
    """Reconstruct and validate one advisory scoring input from dictionary data."""

    if not isinstance(data, Mapping):
        raise TrendAwareScoringError("trend-aware scoring input data must be a mapping.")
    values = _values_from_mapping(
        data,
        TREND_AWARE_INPUT_FIELDS,
        optional_defaults={
            "run_id": None,
            "awr_id": None,
            "trend_context": None,
            "anomaly_context": None,
            "feature_reference": None,
            "runtime_influence": False,
            "runtime_active": False,
        },
    )
    if isinstance(values["trend_context"], Mapping):
        values["trend_context"] = trend_context_from_dict(values["trend_context"])
    elif values["trend_context"] is not None:
        values["trend_context"] = validate_trend_context(values["trend_context"])

    if isinstance(values["anomaly_context"], Mapping):
        values["anomaly_context"] = anomaly_context_from_dict(
            values["anomaly_context"]
        )
    elif values["anomaly_context"] is not None:
        values["anomaly_context"] = validate_anomaly_context(
            values["anomaly_context"]
        )
    return TrendAwareScoringInput(**values)


def trend_aware_score_result_to_dict(
    result: TrendAwareScoreResult,
) -> dict[str, object]:
    """Return a deterministic dictionary for one advisory scoring result."""

    if not isinstance(result, TrendAwareScoreResult):
        raise TrendAwareScoringError("result must be a TrendAwareScoreResult.")
    return {
        field_name: deepcopy(getattr(result, field_name))
        for field_name in TREND_AWARE_RESULT_FIELDS
    }


def trend_aware_score_result_from_dict(
    data: Mapping[str, Any],
) -> TrendAwareScoreResult:
    """Reconstruct and validate one advisory scoring result from dictionary data."""

    if not isinstance(data, Mapping):
        raise TrendAwareScoringError("trend-aware score result data must be a mapping.")
    values = _values_from_mapping(
        data,
        TREND_AWARE_RESULT_FIELDS,
        optional_defaults={
            "runtime_influence": False,
            "runtime_active": False,
            "deterministic_runtime_remains_authoritative": True,
        },
    )
    return TrendAwareScoreResult(**values)


def _validate_trend_direction(trend_direction: Any) -> None:
    if trend_direction not in TREND_DIRECTIONS:
        raise TrendAwareScoringError(
            f"Unsupported trend_direction: {trend_direction!r}."
        )


def _validate_anomaly_pattern(anomaly_pattern: Any) -> None:
    if anomaly_pattern not in ANOMALY_PATTERNS:
        raise TrendAwareScoringError(
            f"Unsupported anomaly_pattern: {anomaly_pattern!r}."
        )


def _validate_advisory_status(status: Any) -> None:
    if status not in TREND_AWARE_SCORING_STATUSES:
        raise TrendAwareScoringError(f"Unsupported advisory_status: {status!r}.")


def _advisory_status(
    input_record: TrendAwareScoringInput,
    score_delta: float,
) -> str:
    if _has_insufficient_context(input_record):
        return "INSUFFICIENT_CONTEXT"
    if abs(score_delta) > 0.0:
        return "ADVISORY_ONLY"
    return "SHADOW_ONLY"


def _has_insufficient_context(input_record: TrendAwareScoringInput) -> bool:
    trend_context = input_record.trend_context
    anomaly_context = input_record.anomaly_context
    if trend_context is None and anomaly_context is None:
        return True
    if trend_context is not None:
        if trend_context.trend_direction == "insufficient_data":
            return True
        if trend_context.trend_signal_count == 0:
            return True
    if anomaly_context is not None:
        if anomaly_context.anomaly_pattern == "insufficient_data":
            return True
    return False


def _result_confidence(input_record: TrendAwareScoringInput) -> float:
    confidence_values: list[float] = []
    missing_contexts = 0
    insufficient_contexts = 0

    if input_record.trend_context is None:
        missing_contexts += 1
    else:
        trend_context = input_record.trend_context
        confidence_values.append(trend_context.trend_confidence)
        if (
            trend_context.trend_direction == "insufficient_data"
            or trend_context.trend_signal_count == 0
        ):
            insufficient_contexts += 1

    if input_record.anomaly_context is None:
        missing_contexts += 1
    else:
        anomaly_context = input_record.anomaly_context
        confidence_values.append(anomaly_context.anomaly_confidence)
        if anomaly_context.anomaly_pattern == "insufficient_data":
            insufficient_contexts += 1

    if not confidence_values:
        return 0.2

    confidence = sum(confidence_values) / len(confidence_values)
    if missing_contexts:
        confidence *= 0.9
    if insufficient_contexts:
        confidence *= 0.6
    return _round_confidence(_clamp(confidence, 0.0, MAX_CONFIDENCE))


def _explanation(
    input_record: TrendAwareScoringInput,
    trend_influence: float,
    anomaly_influence: float,
    score_delta: float,
    advisory_status: str,
) -> str:
    parts = [
        (
            f"Phase 7U advisory Score(x, t) compared baseline "
            f"{_format_number(input_record.baseline_score)} with explicit trend "
            "and anomaly context."
        )
    ]
    if input_record.trend_context is None:
        parts.append("No trend context was supplied; trend influence is 0.")
    else:
        trend = input_record.trend_context
        parts.append(
            "Trend context "
            f"{trend.trend_direction} with strength "
            f"{_format_number(trend.trend_strength)} and confidence "
            f"{_format_number(trend.trend_confidence)} contributed "
            f"{_format_number(trend_influence)}."
        )
    if input_record.anomaly_context is None:
        parts.append("No anomaly context was supplied; anomaly influence is 0.")
    else:
        anomaly = input_record.anomaly_context
        parts.append(
            "Anomaly context "
            f"{anomaly.anomaly_pattern} with severity "
            f"{_format_number(anomaly.anomaly_severity)} and confidence "
            f"{_format_number(anomaly.anomaly_confidence)} contributed "
            f"{_format_number(anomaly_influence)}."
        )
    parts.append(
        f"Advisory delta is {_format_number(score_delta)} with status "
        f"{advisory_status}; deterministic runtime remains authoritative."
    )
    return " ".join(parts)


def _normalize_domain(domain: Any) -> str:
    if not isinstance(domain, str) or not domain.strip():
        raise TrendAwareScoringError("domain must be a non-empty string.")
    normalized = domain.strip().upper()
    normalized = re.sub(r"\s+", " ", normalized)
    aliases = {
        "I/O": "IO",
        "I O": "IO",
        "I-O": "IO",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in DOMAIN_NAMES:
        raise TrendAwareScoringError(f"Unsupported domain: {domain!r}.")
    return normalized


def _normalize_token(value: Any, field_name: str) -> str:
    _require_non_empty_string(value, field_name)
    return str(value).strip().lower()


def _values_from_mapping(
    data: Mapping[str, Any],
    fields: Sequence[str],
    optional_defaults: Mapping[str, Any],
) -> dict[str, Any]:
    missing = [
        field_name
        for field_name in fields
        if field_name not in data and field_name not in optional_defaults
    ]
    if missing:
        raise TrendAwareScoringError(
            "Missing required fields: " + ", ".join(missing) + "."
        )
    return {
        field_name: deepcopy(data[field_name])
        if field_name in data
        else deepcopy(optional_defaults[field_name])
        for field_name in fields
    }


def _reject_runtime_activation_fields(data: Mapping[str, Any]) -> None:
    for field_name in (
        "runtime_influence",
        "runtime_active",
        "runtime_influence_granted",
    ):
        if data.get(field_name) is True:
            raise TrendAwareScoringError(
                f"{field_name} cannot be true on Phase 7U advisory scoring records."
            )


def _require_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise TrendAwareScoringError(f"{field_name} must be a non-empty string.")


def _validate_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise TrendAwareScoringError(f"{field_name} must be None or a string.")
    if isinstance(value, str) and not value.strip():
        raise TrendAwareScoringError(f"{field_name} must not be blank.")


def _require_any_identifier(run_id: str | None, awr_id: str | None) -> None:
    if not _has_text(run_id) and not _has_text(awr_id):
        raise TrendAwareScoringError(
            "At least one of run_id or awr_id is required."
        )


def _validate_nonnegative_int(value: Any, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TrendAwareScoringError(f"{field_name} must be an integer.")
    if value < 0:
        raise TrendAwareScoringError(f"{field_name} must be greater than or equal to 0.")


def _validate_numeric_range(
    value: Any,
    field_name: str,
    minimum: float,
    maximum: float,
) -> None:
    _validate_numeric(value, field_name)
    if value < minimum or value > maximum:
        raise TrendAwareScoringError(
            f"{field_name} must be between {minimum} and {maximum}."
        )


def _validate_numeric(value: Any, field_name: str) -> None:
    if not _is_number(value):
        raise TrendAwareScoringError(f"{field_name} must be numeric.")


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))


def _round_score(value: float) -> float:
    return round(float(value), 6)


def _round_confidence(value: float) -> float:
    return round(float(value), 6)


def _identifier_fragment(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "UNSPECIFIED"


def _stable_hash(values: Sequence[str]) -> str:
    payload = json.dumps(list(values), separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12].upper()


def _format_number(value: float) -> str:
    rounded = _round_score(value)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.6f}".rstrip("0").rstrip(".")
