"""Phase 7X deterministic ML explainability records.

This module explains advisory trend-aware and shadow ML outputs without making
them runtime truth. It is local-only, deterministic, and does not train models,
activate models, alter scoring, update decisions, update recommendations, call
services, or write databases.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence


CONTRIBUTION_DIRECTIONS = (
    "increases_risk",
    "decreases_risk",
    "neutral",
    "insufficient_context",
)

DISAGREEMENT_LEVELS = (
    "none",
    "low",
    "moderate",
    "high",
    "insufficient_context",
)

EXPLAINABILITY_STATUSES = (
    "EXPLANATION_ONLY",
    "SHADOW_EXPLANATION",
    "INSUFFICIENT_CONTEXT",
)

FEATURE_CONTRIBUTION_FIELDS = (
    "feature_name",
    "feature_domain",
    "contribution_direction",
    "contribution_strength",
    "contribution_weight",
    "evidence_reference",
    "explanation_text",
)

SCORE_COMPARISON_FIELDS = (
    "deterministic_score",
    "trend_aware_score",
    "shadow_ml_score",
    "trend_delta",
    "shadow_delta",
    "disagreement_level",
    "disagreement_summary",
)

CONFIDENCE_EXPLANATION_FIELDS = (
    "confidence",
    "uncertainty_reason",
    "confidence_factors",
    "insufficient_context_flags",
)

ML_EXPLANATION_RECORD_FIELDS = (
    "explanation_id",
    "source_output_id",
    "model_id",
    "domain",
    "feature_contributions",
    "score_comparison",
    "confidence_explanation",
    "top_positive_features",
    "top_negative_features",
    "boundary_summary",
    "evidence_references",
    "advisory_status",
    "runtime_influence",
    "runtime_active",
    "runtime_influence_granted",
    "deterministic_runtime_remains_authoritative",
)

MAX_CONFIDENCE = 0.95
BOUNDARY_SUMMARY = (
    "Phase 7X explanation is advisory/shadow only; explainability is not "
    "runtime truth; explanations do not change runtime scoring; deterministic "
    "scoring remains authoritative; runtime_influence=false; "
    "runtime_active=false; runtime_influence_granted=false."
)

RISK_FEATURE_TOKENS = (
    "risk",
    "pressure",
    "wait",
    "load",
    "latency",
    "contention",
    "severity",
    "bottleneck",
    "anomaly",
    "degradation",
)

DECREASES_RISK_FEATURE_TOKENS = (
    "headroom",
    "available",
    "availability",
    "free",
    "healthy",
    "health",
    "improvement",
    "improving",
    "reduction",
    "capacity",
)

DOMAIN_ALIASES = {
    "cpu": "CPU",
    "io": "IO",
    "i/o": "IO",
    "memory": "MEMORY",
    "mem": "MEMORY",
    "commit": "COMMIT",
    "rac": "RAC",
    "adg": "ADG",
}

_MISSING = object()


class MLExplainabilityError(ValueError):
    """Raised when Phase 7X explainability rules are violated."""


@dataclass(frozen=True)
class FeatureContribution:
    """Explanatory-only feature contribution for an advisory output."""

    feature_name: str
    feature_domain: str | None
    contribution_direction: str
    contribution_strength: float
    contribution_weight: float
    evidence_reference: str | None
    explanation_text: str

    def __post_init__(self) -> None:
        _require_non_empty_string(self.feature_name, "feature_name")
        _validate_optional_string(self.feature_domain, "feature_domain")
        direction = _normalize_direction(self.contribution_direction)
        _validate_numeric_range(
            self.contribution_strength,
            "contribution_strength",
            0.0,
            1.0,
        )
        _validate_numeric_range(
            self.contribution_weight,
            "contribution_weight",
            -1.0,
            1.0,
        )
        _validate_optional_string(self.evidence_reference, "evidence_reference")
        _require_non_empty_string(self.explanation_text, "explanation_text")
        object.__setattr__(self, "feature_name", self.feature_name.strip())
        object.__setattr__(
            self,
            "feature_domain",
            None if self.feature_domain is None else self.feature_domain.strip(),
        )
        object.__setattr__(self, "contribution_direction", direction)
        object.__setattr__(
            self,
            "contribution_strength",
            float(self.contribution_strength),
        )
        object.__setattr__(
            self,
            "contribution_weight",
            float(self.contribution_weight),
        )
        object.__setattr__(
            self,
            "evidence_reference",
            None if self.evidence_reference is None else self.evidence_reference.strip(),
        )
        object.__setattr__(self, "explanation_text", self.explanation_text.strip())


@dataclass(frozen=True)
class ScoreComparisonExplanation:
    """Comparison of deterministic, trend-aware, and shadow ML scores."""

    deterministic_score: float
    trend_aware_score: float | None
    shadow_ml_score: float | None
    trend_delta: float | None
    shadow_delta: float | None
    disagreement_level: str
    disagreement_summary: str

    def __post_init__(self) -> None:
        _validate_score(self.deterministic_score, "deterministic_score")
        if self.trend_aware_score is not None:
            _validate_score(self.trend_aware_score, "trend_aware_score")
        if self.shadow_ml_score is not None:
            _validate_score(self.shadow_ml_score, "shadow_ml_score")
        _validate_delta_pair(
            self.trend_aware_score,
            self.trend_delta,
            self.deterministic_score,
            "trend_delta",
        )
        _validate_delta_pair(
            self.shadow_ml_score,
            self.shadow_delta,
            self.deterministic_score,
            "shadow_delta",
        )
        level = _normalize_disagreement_level(self.disagreement_level)
        expected_level = _derive_disagreement_level(
            [self.trend_delta, self.shadow_delta]
        )
        if level != expected_level:
            raise MLExplainabilityError(
                "disagreement_level must match deterministic score deltas."
            )
        _require_non_empty_string(self.disagreement_summary, "disagreement_summary")
        object.__setattr__(self, "deterministic_score", float(self.deterministic_score))
        object.__setattr__(
            self,
            "trend_aware_score",
            None if self.trend_aware_score is None else float(self.trend_aware_score),
        )
        object.__setattr__(
            self,
            "shadow_ml_score",
            None if self.shadow_ml_score is None else float(self.shadow_ml_score),
        )
        object.__setattr__(
            self,
            "trend_delta",
            None if self.trend_delta is None else float(self.trend_delta),
        )
        object.__setattr__(
            self,
            "shadow_delta",
            None if self.shadow_delta is None else float(self.shadow_delta),
        )
        object.__setattr__(self, "disagreement_level", level)
        object.__setattr__(
            self,
            "disagreement_summary",
            self.disagreement_summary.strip(),
        )


@dataclass(frozen=True)
class ConfidenceExplanation:
    """Confidence and uncertainty context separate from 0-100 scoring."""

    confidence: float
    uncertainty_reason: str
    confidence_factors: list[str]
    insufficient_context_flags: list[str]

    def __post_init__(self) -> None:
        _validate_numeric_range(self.confidence, "confidence", 0.0, MAX_CONFIDENCE)
        _require_non_empty_string(self.uncertainty_reason, "uncertainty_reason")
        factors = _normalize_string_list(
            self.confidence_factors,
            "confidence_factors",
            allow_empty=True,
        )
        flags = _normalize_string_list(
            self.insufficient_context_flags,
            "insufficient_context_flags",
            allow_empty=True,
        )
        object.__setattr__(self, "confidence", float(self.confidence))
        object.__setattr__(
            self,
            "uncertainty_reason",
            self.uncertainty_reason.strip(),
        )
        object.__setattr__(self, "confidence_factors", factors)
        object.__setattr__(self, "insufficient_context_flags", flags)


@dataclass(frozen=True)
class MLExplanationRecord:
    """Complete advisory-only ML explanation record."""

    explanation_id: str
    source_output_id: str
    model_id: str | None
    domain: str | None
    feature_contributions: list[FeatureContribution]
    score_comparison: ScoreComparisonExplanation
    confidence_explanation: ConfidenceExplanation
    top_positive_features: list[str]
    top_negative_features: list[str]
    boundary_summary: str
    evidence_references: list[str]
    advisory_status: str
    runtime_influence: bool
    runtime_active: bool
    runtime_influence_granted: bool
    deterministic_runtime_remains_authoritative: bool

    def __post_init__(self) -> None:
        _require_non_empty_string(self.explanation_id, "explanation_id")
        _require_non_empty_string(self.source_output_id, "source_output_id")
        _validate_optional_string(self.model_id, "model_id")
        _validate_optional_string(self.domain, "domain")
        contributions = _validate_feature_contribution_list(
            self.feature_contributions
        )
        comparison = validate_score_comparison_explanation(self.score_comparison)
        confidence = validate_confidence_explanation(self.confidence_explanation)
        top_positive = _normalize_string_list(
            self.top_positive_features,
            "top_positive_features",
            allow_empty=True,
        )
        top_negative = _normalize_string_list(
            self.top_negative_features,
            "top_negative_features",
            allow_empty=True,
        )
        _require_non_empty_string(self.boundary_summary, "boundary_summary")
        evidence = _normalize_string_list(
            self.evidence_references,
            "evidence_references",
            allow_empty=True,
        )
        advisory_status = _normalize_explainability_status(self.advisory_status)
        if self.runtime_influence is not False:
            raise MLExplainabilityError(
                "Phase 7X explanation records must keep runtime_influence=false."
            )
        if self.runtime_active is not False:
            raise MLExplainabilityError(
                "Phase 7X explanation records must keep runtime_active=false."
            )
        if self.runtime_influence_granted is not False:
            raise MLExplainabilityError(
                "Phase 7X explanation records must keep "
                "runtime_influence_granted=false."
            )
        if self.deterministic_runtime_remains_authoritative is not True:
            raise MLExplainabilityError(
                "Phase 7X requires deterministic scoring to remain authoritative."
            )
        object.__setattr__(self, "explanation_id", self.explanation_id.strip())
        object.__setattr__(self, "source_output_id", self.source_output_id.strip())
        object.__setattr__(
            self,
            "model_id",
            None if self.model_id is None else self.model_id.strip(),
        )
        object.__setattr__(
            self,
            "domain",
            None if self.domain is None else self.domain.strip(),
        )
        object.__setattr__(self, "feature_contributions", contributions)
        object.__setattr__(self, "score_comparison", comparison)
        object.__setattr__(self, "confidence_explanation", confidence)
        object.__setattr__(self, "top_positive_features", top_positive)
        object.__setattr__(self, "top_negative_features", top_negative)
        object.__setattr__(self, "boundary_summary", self.boundary_summary.strip())
        object.__setattr__(self, "evidence_references", evidence)
        object.__setattr__(self, "advisory_status", advisory_status)
        object.__setattr__(self, "runtime_influence", False)
        object.__setattr__(self, "runtime_active", False)
        object.__setattr__(self, "runtime_influence_granted", False)
        object.__setattr__(
            self,
            "deterministic_runtime_remains_authoritative",
            True,
        )


def create_explanation_id(
    source_output_id: str,
    model_id: str | None = None,
    domain: str | None = None,
) -> str:
    """Create a deterministic Phase 7X explanation identifier."""

    _require_non_empty_string(source_output_id, "source_output_id")
    _validate_optional_string(model_id, "model_id")
    _validate_optional_string(domain, "domain")
    model_fragment = model_id if _has_text(model_id) else "NO-MODEL"
    domain_fragment = domain if _has_text(domain) else "NO-DOMAIN"
    return (
        f"ML-EXPLAIN-{_identifier_fragment(source_output_id)}-"
        f"{_identifier_fragment(model_fragment)}-"
        f"{_identifier_fragment(domain_fragment)}"
    )


def validate_feature_contribution(
    contribution: FeatureContribution | Mapping[str, Any],
) -> FeatureContribution:
    """Validate and return a feature contribution."""

    if isinstance(contribution, Mapping):
        return feature_contribution_from_dict(contribution)
    if not isinstance(contribution, FeatureContribution):
        raise MLExplainabilityError("contribution must be FeatureContribution.")
    return FeatureContribution(**feature_contribution_to_dict(contribution))


def validate_score_comparison_explanation(
    comparison: ScoreComparisonExplanation | Mapping[str, Any],
) -> ScoreComparisonExplanation:
    """Validate and return a score comparison explanation."""

    if isinstance(comparison, Mapping):
        return score_comparison_from_dict(comparison)
    if not isinstance(comparison, ScoreComparisonExplanation):
        raise MLExplainabilityError(
            "comparison must be ScoreComparisonExplanation."
        )
    return ScoreComparisonExplanation(**score_comparison_to_dict(comparison))


def validate_confidence_explanation(
    explanation: ConfidenceExplanation | Mapping[str, Any],
) -> ConfidenceExplanation:
    """Validate and return a confidence explanation."""

    if isinstance(explanation, Mapping):
        return confidence_explanation_from_dict(explanation)
    if not isinstance(explanation, ConfidenceExplanation):
        raise MLExplainabilityError("explanation must be ConfidenceExplanation.")
    return ConfidenceExplanation(**confidence_explanation_to_dict(explanation))


def validate_ml_explanation_record(
    record: MLExplanationRecord | Mapping[str, Any],
) -> MLExplanationRecord:
    """Validate and return an ML explanation record."""

    if isinstance(record, Mapping):
        return ml_explanation_record_from_dict(record)
    if not isinstance(record, MLExplanationRecord):
        raise MLExplainabilityError("record must be MLExplanationRecord.")
    return MLExplanationRecord(**ml_explanation_record_to_dict(record))


def build_score_comparison_explanation(
    deterministic_score: float,
    trend_aware_score: float | None = None,
    shadow_ml_score: float | None = None,
) -> ScoreComparisonExplanation:
    """Build a deterministic advisory score comparison explanation."""

    _validate_score(deterministic_score, "deterministic_score")
    if trend_aware_score is not None:
        _validate_score(trend_aware_score, "trend_aware_score")
    if shadow_ml_score is not None:
        _validate_score(shadow_ml_score, "shadow_ml_score")

    trend_delta = (
        None
        if trend_aware_score is None
        else _round_number(float(trend_aware_score) - float(deterministic_score))
    )
    shadow_delta = (
        None
        if shadow_ml_score is None
        else _round_number(float(shadow_ml_score) - float(deterministic_score))
    )
    disagreement_level = _derive_disagreement_level([trend_delta, shadow_delta])
    summary = _score_disagreement_summary(
        deterministic_score,
        trend_aware_score,
        shadow_ml_score,
        trend_delta,
        shadow_delta,
        disagreement_level,
    )
    return validate_score_comparison_explanation(
        ScoreComparisonExplanation(
            deterministic_score=deterministic_score,
            trend_aware_score=trend_aware_score,
            shadow_ml_score=shadow_ml_score,
            trend_delta=trend_delta,
            shadow_delta=shadow_delta,
            disagreement_level=disagreement_level,
            disagreement_summary=summary,
        )
    )


def build_confidence_explanation(
    confidence: float,
    factors: Sequence[str] | None = None,
    insufficient_context_flags: Sequence[str] | None = None,
) -> ConfidenceExplanation:
    """Build confidence context that remains separate from score."""

    confidence_factors = _normalize_string_list(
        [] if factors is None else factors,
        "confidence_factors",
        allow_empty=True,
    )
    flags = _normalize_string_list(
        [] if insufficient_context_flags is None else insufficient_context_flags,
        "insufficient_context_flags",
        allow_empty=True,
    )
    if flags:
        reason = (
            "Confidence is limited by insufficient context flags: "
            + ", ".join(flags)
            + ". Confidence is not score."
        )
    elif confidence_factors:
        reason = (
            "Confidence reflects supplied advisory explanation factors only; "
            "confidence is not score."
        )
    else:
        reason = (
            "No confidence factors were supplied; confidence is advisory only "
            "and confidence is not score."
        )
    return validate_confidence_explanation(
        ConfidenceExplanation(
            confidence=confidence,
            uncertainty_reason=reason,
            confidence_factors=confidence_factors,
            insufficient_context_flags=flags,
        )
    )


def build_feature_contributions(
    feature_values: Mapping[str, object],
    evidence_reference: str | None = None,
) -> list[FeatureContribution]:
    """Build deterministic explanatory-only feature contributions."""

    if not isinstance(feature_values, Mapping):
        raise MLExplainabilityError("feature_values must be a mapping.")
    _validate_optional_string(evidence_reference, "evidence_reference")
    contributions = [
        _build_feature_contribution(feature_name, value, evidence_reference)
        for feature_name, value in feature_values.items()
    ]
    return sorted(
        (validate_feature_contribution(contribution) for contribution in contributions),
        key=lambda contribution: (
            -abs(contribution.contribution_strength),
            contribution.feature_name,
        ),
    )


def build_ml_explanation_record(
    shadow_output: Mapping[str, Any] | object,
    feature_values: Mapping[str, object] | None = None,
    trend_result: Mapping[str, Any] | object | None = None,
    evidence_references: Sequence[str] | None = None,
) -> MLExplanationRecord:
    """Build a complete advisory-only explanation for a shadow output."""

    _reject_runtime_truth_fields(shadow_output, "shadow_output")
    if trend_result is not None:
        _reject_runtime_truth_fields(trend_result, "trend_result")

    source_output_id = _first_value(
        shadow_output,
        ("output_id", "source_output_id"),
        "source_output_id",
    )
    model_id = _optional_first_value(shadow_output, ("model_id",))
    deterministic_score = _first_value(
        shadow_output,
        ("deterministic_score",),
        "deterministic_score",
    )
    shadow_ml_score = _first_value(
        shadow_output,
        ("shadow_ml_score",),
        "shadow_ml_score",
    )
    shadow_trend_score = _optional_first_value(shadow_output, ("trend_aware_score",))
    trend_result_score = (
        None
        if trend_result is None
        else _optional_first_value(trend_result, ("trend_aware_score",))
    )
    trend_aware_score = _resolve_trend_score(
        shadow_trend_score,
        trend_result_score,
    )
    confidence = _first_value(shadow_output, ("confidence",), "confidence")
    domain = _resolve_domain(shadow_output, trend_result)

    supplied_features = {} if feature_values is None else feature_values
    contributions = build_feature_contributions(supplied_features)
    comparison = build_score_comparison_explanation(
        deterministic_score=deterministic_score,
        trend_aware_score=trend_aware_score,
        shadow_ml_score=shadow_ml_score,
    )
    insufficient_flags = _insufficient_context_flags(
        feature_values=supplied_features,
        trend_aware_score=trend_aware_score,
    )
    confidence_explanation = build_confidence_explanation(
        confidence=confidence,
        factors=_confidence_factors(contributions, comparison),
        insufficient_context_flags=insufficient_flags,
    )
    top_positive = [
        contribution.feature_name
        for contribution in contributions
        if contribution.contribution_direction == "increases_risk"
    ][:5]
    top_negative = [
        contribution.feature_name
        for contribution in contributions
        if contribution.contribution_direction == "decreases_risk"
    ][:5]
    evidence = _merge_evidence_references(
        evidence_references,
        contributions,
    )
    advisory_status = _record_status(shadow_output, insufficient_flags)
    record = MLExplanationRecord(
        explanation_id=create_explanation_id(source_output_id, model_id, domain),
        source_output_id=source_output_id,
        model_id=model_id,
        domain=domain,
        feature_contributions=contributions,
        score_comparison=comparison,
        confidence_explanation=confidence_explanation,
        top_positive_features=top_positive,
        top_negative_features=top_negative,
        boundary_summary=BOUNDARY_SUMMARY,
        evidence_references=evidence,
        advisory_status=advisory_status,
        runtime_influence=False,
        runtime_active=False,
        runtime_influence_granted=False,
        deterministic_runtime_remains_authoritative=True,
    )
    return validate_ml_explanation_record(record)


def feature_contribution_to_dict(
    contribution: FeatureContribution,
) -> dict[str, object]:
    """Return a deterministic dictionary for a feature contribution."""

    if not isinstance(contribution, FeatureContribution):
        raise MLExplainabilityError("contribution must be FeatureContribution.")
    return {
        field_name: deepcopy(getattr(contribution, field_name))
        for field_name in FEATURE_CONTRIBUTION_FIELDS
    }


def feature_contribution_from_dict(data: Mapping[str, Any]) -> FeatureContribution:
    """Reconstruct and validate a feature contribution from dictionary data."""

    if not isinstance(data, Mapping):
        raise MLExplainabilityError("feature contribution data must be a mapping.")
    values = _values_from_mapping(
        data,
        FEATURE_CONTRIBUTION_FIELDS,
        optional_defaults={
            "feature_domain": None,
            "evidence_reference": None,
        },
    )
    return FeatureContribution(**values)


def score_comparison_to_dict(
    comparison: ScoreComparisonExplanation,
) -> dict[str, object]:
    """Return a deterministic dictionary for a score comparison."""

    if not isinstance(comparison, ScoreComparisonExplanation):
        raise MLExplainabilityError(
            "comparison must be ScoreComparisonExplanation."
        )
    return {
        field_name: deepcopy(getattr(comparison, field_name))
        for field_name in SCORE_COMPARISON_FIELDS
    }


def score_comparison_from_dict(
    data: Mapping[str, Any],
) -> ScoreComparisonExplanation:
    """Reconstruct and validate a score comparison from dictionary data."""

    if not isinstance(data, Mapping):
        raise MLExplainabilityError("score comparison data must be a mapping.")
    values = _values_from_mapping(
        data,
        SCORE_COMPARISON_FIELDS,
        optional_defaults={
            "trend_aware_score": None,
            "shadow_ml_score": None,
            "trend_delta": None,
            "shadow_delta": None,
        },
    )
    return ScoreComparisonExplanation(**values)


def confidence_explanation_to_dict(
    explanation: ConfidenceExplanation,
) -> dict[str, object]:
    """Return a deterministic dictionary for a confidence explanation."""

    if not isinstance(explanation, ConfidenceExplanation):
        raise MLExplainabilityError("explanation must be ConfidenceExplanation.")
    return {
        field_name: deepcopy(getattr(explanation, field_name))
        for field_name in CONFIDENCE_EXPLANATION_FIELDS
    }


def confidence_explanation_from_dict(
    data: Mapping[str, Any],
) -> ConfidenceExplanation:
    """Reconstruct and validate a confidence explanation from dictionary data."""

    if not isinstance(data, Mapping):
        raise MLExplainabilityError("confidence explanation data must be a mapping.")
    values = _values_from_mapping(
        data,
        CONFIDENCE_EXPLANATION_FIELDS,
        optional_defaults={
            "confidence_factors": [],
            "insufficient_context_flags": [],
        },
    )
    return ConfidenceExplanation(**values)


def ml_explanation_record_to_dict(record: MLExplanationRecord) -> dict[str, object]:
    """Return a deterministic dictionary for an ML explanation record."""

    if not isinstance(record, MLExplanationRecord):
        raise MLExplainabilityError("record must be MLExplanationRecord.")
    return {
        "explanation_id": record.explanation_id,
        "source_output_id": record.source_output_id,
        "model_id": record.model_id,
        "domain": record.domain,
        "feature_contributions": [
            feature_contribution_to_dict(contribution)
            for contribution in record.feature_contributions
        ],
        "score_comparison": score_comparison_to_dict(record.score_comparison),
        "confidence_explanation": confidence_explanation_to_dict(
            record.confidence_explanation
        ),
        "top_positive_features": deepcopy(record.top_positive_features),
        "top_negative_features": deepcopy(record.top_negative_features),
        "boundary_summary": record.boundary_summary,
        "evidence_references": deepcopy(record.evidence_references),
        "advisory_status": record.advisory_status,
        "runtime_influence": False,
        "runtime_active": False,
        "runtime_influence_granted": False,
        "deterministic_runtime_remains_authoritative": True,
    }


def ml_explanation_record_from_dict(data: Mapping[str, Any]) -> MLExplanationRecord:
    """Reconstruct and validate an ML explanation record from dictionary data."""

    if not isinstance(data, Mapping):
        raise MLExplainabilityError("ML explanation record data must be a mapping.")
    _reject_runtime_truth_fields(data, "ML explanation record")
    values = _values_from_mapping(
        data,
        ML_EXPLANATION_RECORD_FIELDS,
        optional_defaults={
            "model_id": None,
            "domain": None,
            "runtime_influence": False,
            "runtime_active": False,
            "runtime_influence_granted": False,
            "deterministic_runtime_remains_authoritative": True,
        },
    )
    values["feature_contributions"] = [
        validate_feature_contribution(contribution)
        for contribution in values["feature_contributions"]
    ]
    values["score_comparison"] = validate_score_comparison_explanation(
        values["score_comparison"]
    )
    values["confidence_explanation"] = validate_confidence_explanation(
        values["confidence_explanation"]
    )
    return MLExplanationRecord(**values)


def _build_feature_contribution(
    feature_name: Any,
    value: object,
    evidence_reference: str | None,
) -> FeatureContribution:
    _require_non_empty_string(feature_name, "feature_name")
    name = str(feature_name).strip()
    domain = _infer_feature_domain(name)
    direction, strength, weight = _contribution_signal(name, value)
    explanation = _feature_explanation_text(name, domain, direction)
    return FeatureContribution(
        feature_name=name,
        feature_domain=domain,
        contribution_direction=direction,
        contribution_strength=strength,
        contribution_weight=weight,
        evidence_reference=evidence_reference,
        explanation_text=explanation,
    )


def _contribution_signal(name: str, value: object) -> tuple[str, float, float]:
    if value is None:
        return "insufficient_context", 0.0, 0.0
    if isinstance(value, str) and not value.strip():
        return "insufficient_context", 0.0, 0.0

    if isinstance(value, bool):
        if value and _is_risk_feature_name(name):
            return "increases_risk", 1.0, 1.0
        if value and _is_decreases_risk_feature_name(name):
            return "decreases_risk", 1.0, -1.0
        return "neutral", 0.0, 0.0

    if _is_number(value):
        numeric_value = float(value)
        if numeric_value <= 0.0:
            return "neutral", 0.0, 0.0
        strength = _numeric_strength(numeric_value)
        if _is_risk_feature_name(name):
            return "increases_risk", strength, strength
        if _is_decreases_risk_feature_name(name):
            return "decreases_risk", strength, -strength
        return "neutral", 0.0, 0.0

    return "neutral", 0.0, 0.0


def _feature_explanation_text(
    feature_name: str,
    domain: str | None,
    direction: str,
) -> str:
    domain_text = f" in the {domain} domain" if domain else ""
    if direction == "increases_risk":
        signal = "suggests increased risk"
    elif direction == "decreases_risk":
        signal = "suggests decreased risk"
    elif direction == "insufficient_context":
        signal = "lacks sufficient context"
    else:
        signal = "is neutral for this deterministic placeholder"
    return (
        f"Feature {feature_name}{domain_text} {signal}; feature contributions "
        "are explanatory only and do not change runtime scoring."
    )


def _score_disagreement_summary(
    deterministic_score: float,
    trend_aware_score: float | None,
    shadow_ml_score: float | None,
    trend_delta: float | None,
    shadow_delta: float | None,
    disagreement_level: str,
) -> str:
    if trend_aware_score is None and shadow_ml_score is None:
        return (
            "No trend-aware or shadow ML score was supplied for comparison; "
            "disagreement level is insufficient_context and deterministic "
            "scoring remains authoritative."
        )
    parts = [
        "Deterministic score "
        f"{_format_number(float(deterministic_score))} remains authoritative."
    ]
    if trend_aware_score is not None:
        parts.append(
            "Trend-aware score "
            f"{_format_number(float(trend_aware_score))} differs by "
            f"{_format_number(float(trend_delta))}."
        )
    if shadow_ml_score is not None:
        parts.append(
            "Shadow ML score "
            f"{_format_number(float(shadow_ml_score))} differs by "
            f"{_format_number(float(shadow_delta))}."
        )
    parts.append(
        f"Disagreement level is {disagreement_level}; explanations do not "
        "change runtime scoring."
    )
    return " ".join(parts)


def _validate_feature_contribution_list(
    contributions: Any,
) -> list[FeatureContribution]:
    if not isinstance(contributions, list):
        raise MLExplainabilityError("feature_contributions must be a list.")
    return [
        validate_feature_contribution(contribution)
        for contribution in contributions
    ]


def _resolve_trend_score(
    shadow_trend_score: Any,
    trend_result_score: Any,
) -> float | None:
    if shadow_trend_score is not None:
        _validate_score(shadow_trend_score, "trend_aware_score")
    if trend_result_score is not None:
        _validate_score(trend_result_score, "trend_aware_score")
    if shadow_trend_score is not None and trend_result_score is not None:
        if _round_number(float(shadow_trend_score)) != _round_number(
            float(trend_result_score)
        ):
            raise MLExplainabilityError(
                "trend_result trend_aware_score must match shadow_output "
                "trend_aware_score when both are supplied."
            )
    if trend_result_score is not None:
        return float(trend_result_score)
    if shadow_trend_score is not None:
        return float(shadow_trend_score)
    return None


def _resolve_domain(
    shadow_output: Mapping[str, Any] | object,
    trend_result: Mapping[str, Any] | object | None,
) -> str | None:
    trend_domain = (
        None
        if trend_result is None
        else _optional_first_value(trend_result, ("domain",))
    )
    shadow_domain = _optional_first_value(shadow_output, ("domain",))
    domain = trend_domain if _has_text(trend_domain) else shadow_domain
    if domain is None:
        return None
    _validate_optional_string(domain, "domain")
    return str(domain).strip()


def _insufficient_context_flags(
    feature_values: Mapping[str, object],
    trend_aware_score: float | None,
) -> list[str]:
    flags: list[str] = []
    if not feature_values:
        flags.append("missing_feature_values")
    if trend_aware_score is None:
        flags.append("missing_trend_aware_score")
    return flags


def _confidence_factors(
    contributions: Sequence[FeatureContribution],
    comparison: ScoreComparisonExplanation,
) -> list[str]:
    factors = ["shadow_ml_output"]
    if comparison.trend_aware_score is not None:
        factors.append("trend_aware_score_available")
    if comparison.shadow_ml_score is not None:
        factors.append("shadow_ml_score_available")
    if contributions:
        factors.append(f"feature_contributions:{len(contributions)}")
    return factors


def _merge_evidence_references(
    evidence_references: Sequence[str] | None,
    contributions: Sequence[FeatureContribution],
) -> list[str]:
    merged: list[str] = []
    for reference in _normalize_string_list(
        [] if evidence_references is None else evidence_references,
        "evidence_references",
        allow_empty=True,
    ):
        if reference not in merged:
            merged.append(reference)
    for contribution in contributions:
        reference = contribution.evidence_reference
        if reference is not None and reference not in merged:
            merged.append(reference)
    return merged


def _record_status(
    shadow_output: Mapping[str, Any] | object,
    insufficient_flags: Sequence[str],
) -> str:
    source_status = _optional_first_value(shadow_output, ("advisory_status",))
    if source_status in ("INSUFFICIENT_MODEL_CONTEXT", "INVALID_INPUT"):
        return "INSUFFICIENT_CONTEXT"
    if insufficient_flags:
        return "INSUFFICIENT_CONTEXT"
    return "SHADOW_EXPLANATION"


def _first_value(
    source: Mapping[str, Any] | object,
    names: Sequence[str],
    field_name: str,
) -> Any:
    value = _optional_first_value(source, names)
    if value is None:
        raise MLExplainabilityError(f"{field_name} is required.")
    return value


def _optional_first_value(
    source: Mapping[str, Any] | object,
    names: Sequence[str],
) -> Any:
    for name in names:
        value = _get_value(source, name, _MISSING)
        if value is not _MISSING:
            return value
    return None


def _get_value(
    source: Mapping[str, Any] | object,
    name: str,
    default: Any = None,
) -> Any:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)


def _reject_runtime_truth_fields(source: Mapping[str, Any] | object, label: str) -> None:
    runtime_checks = (
        ("runtime_influence", True),
        ("runtime_active", True),
        ("runtime_influence_granted", True),
        ("deterministic_runtime_remains_authoritative", False),
    )
    for field_name, forbidden_value in runtime_checks:
        value = _get_value(source, field_name, _MISSING)
        if value is forbidden_value:
            raise MLExplainabilityError(
                f"{label} cannot set {field_name}={forbidden_value!r}."
            )


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
        raise MLExplainabilityError(
            "Missing required fields: " + ", ".join(missing) + "."
        )
    return {
        field_name: deepcopy(data[field_name])
        if field_name in data
        else deepcopy(optional_defaults[field_name])
        for field_name in fields
    }


def _normalize_direction(value: Any) -> str:
    _require_non_empty_string(value, "contribution_direction")
    normalized = str(value).strip().lower()
    if normalized not in CONTRIBUTION_DIRECTIONS:
        raise MLExplainabilityError(
            f"Unsupported contribution_direction: {value!r}."
        )
    return normalized


def _normalize_disagreement_level(value: Any) -> str:
    _require_non_empty_string(value, "disagreement_level")
    normalized = str(value).strip().lower()
    if normalized not in DISAGREEMENT_LEVELS:
        raise MLExplainabilityError(f"Unsupported disagreement_level: {value!r}.")
    return normalized


def _normalize_explainability_status(value: Any) -> str:
    _require_non_empty_string(value, "advisory_status")
    normalized = str(value).strip().upper()
    if normalized not in EXPLAINABILITY_STATUSES:
        raise MLExplainabilityError(f"Unsupported advisory_status: {value!r}.")
    return normalized


def _derive_disagreement_level(deltas: Sequence[float | None]) -> str:
    available = [abs(float(delta)) for delta in deltas if delta is not None]
    if not available:
        return "insufficient_context"
    largest = max(available)
    if largest >= 15.0:
        return "high"
    if largest >= 5.0:
        return "moderate"
    if largest > 0.0:
        return "low"
    return "none"


def _validate_delta_pair(
    score: float | None,
    delta: float | None,
    deterministic_score: float,
    field_name: str,
) -> None:
    if score is None:
        if delta is not None:
            raise MLExplainabilityError(
                f"{field_name} must be None when matching score is None."
            )
        return
    _validate_numeric(delta, field_name)
    expected = _round_number(float(score) - float(deterministic_score))
    if _round_number(delta) != expected:
        raise MLExplainabilityError(
            f"{field_name} must equal comparison score minus deterministic_score."
        )


def _validate_score(value: Any, field_name: str) -> None:
    _validate_numeric_range(value, field_name, 0.0, 100.0)


def _validate_numeric_range(
    value: Any,
    field_name: str,
    minimum: float,
    maximum: float,
) -> None:
    _validate_numeric(value, field_name)
    if value < minimum or value > maximum:
        raise MLExplainabilityError(
            f"{field_name} must be between {minimum} and {maximum}."
        )


def _validate_numeric(value: Any, field_name: str) -> None:
    if not _is_number(value):
        raise MLExplainabilityError(f"{field_name} must be numeric.")


def _validate_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise MLExplainabilityError(f"{field_name} must be None or a string.")
    if isinstance(value, str) and not value.strip():
        raise MLExplainabilityError(f"{field_name} must not be blank.")


def _require_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise MLExplainabilityError(f"{field_name} must be a non-empty string.")


def _normalize_string_list(
    values: Any,
    field_name: str,
    allow_empty: bool,
) -> list[str]:
    if not isinstance(values, list) and not isinstance(values, tuple):
        raise MLExplainabilityError(f"{field_name} must be a list.")
    normalized: list[str] = []
    for value in values:
        _require_non_empty_string(value, field_name)
        normalized.append(str(value).strip())
    if not allow_empty and not normalized:
        raise MLExplainabilityError(f"{field_name} must not be empty.")
    return normalized


def _infer_feature_domain(feature_name: str) -> str | None:
    tokens = re.split(r"[^a-zA-Z0-9/]+", feature_name.strip().lower())
    for token in tokens:
        if token in DOMAIN_ALIASES:
            return DOMAIN_ALIASES[token]
    return None


def _is_risk_feature_name(name: str) -> bool:
    normalized = name.strip().lower()
    return any(token in normalized for token in RISK_FEATURE_TOKENS)


def _is_decreases_risk_feature_name(name: str) -> bool:
    normalized = name.strip().lower()
    return any(token in normalized for token in DECREASES_RISK_FEATURE_TOKENS)


def _numeric_strength(value: float) -> float:
    if 0.0 <= value <= 1.0:
        return _round_number(value)
    return _round_number(min(abs(value) / 100.0, 1.0))


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _round_number(value: Any) -> float:
    return round(float(value), 6)


def _identifier_fragment(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "UNSPECIFIED"


def _format_number(value: float) -> str:
    rounded = _round_number(value)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.6f}".rstrip("0").rstrip(".")
