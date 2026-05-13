"""Proposal-only Phase 7O adaptive scoring review model.

Adaptive scoring review records describe proposed scoring configuration
changes that originate from validated scoring materialization artifacts. They
do not import, mutate, activate, or otherwise influence runtime scoring.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import re
from typing import Any, Mapping, Sequence

from src.learning.materialization_artifact import (
    MATERIALIZED,
    SCORING_REVIEW_ARTIFACT,
    VALIDATED,
    MaterializationArtifact,
    MaterializationArtifactError,
    is_runtime_sensitive_artifact_type,
    materialization_artifact_from_dict,
    validate_materialization_artifact,
)


SCORING_WEIGHT_REVIEW = "scoring_weight_review"
DOMAIN_WEIGHT_REVIEW = "domain_weight_review"
THRESHOLD_REVIEW = "threshold_review"
SEVERITY_CUTOFF_REVIEW = "severity_cutoff_review"
CONFIDENCE_LOGIC_REVIEW = "confidence_logic_review"
TREND_SENSITIVITY_REVIEW = "trend_sensitivity_review"
ANOMALY_SENSITIVITY_REVIEW = "anomaly_sensitivity_review"
RECURRING_ISSUE_SENSITIVITY_REVIEW = "recurring_issue_sensitivity_review"
SCORE_NORMALIZATION_REVIEW = "score_normalization_review"
SCORE_LABEL_REVIEW = "score_label_review"

SCORING_REVIEW_TYPES = (
    SCORING_WEIGHT_REVIEW,
    DOMAIN_WEIGHT_REVIEW,
    THRESHOLD_REVIEW,
    SEVERITY_CUTOFF_REVIEW,
    CONFIDENCE_LOGIC_REVIEW,
    TREND_SENSITIVITY_REVIEW,
    ANOMALY_SENSITIVITY_REVIEW,
    RECURRING_ISSUE_SENSITIVITY_REVIEW,
    SCORE_NORMALIZATION_REVIEW,
    SCORE_LABEL_REVIEW,
)

PROPOSED = "PROPOSED"
UNDER_REVIEW = "UNDER_REVIEW"
APPROVED_FOR_VALIDATION = "APPROVED_FOR_VALIDATION"
VALIDATED_STATUS = "VALIDATED"
REJECTED = "REJECTED"
ROLLED_BACK = "ROLLED_BACK"
CLOSED = "CLOSED"

PROPOSED_SCORING_CONFIG_STATUSES = (
    PROPOSED,
    UNDER_REVIEW,
    APPROVED_FOR_VALIDATION,
    VALIDATED_STATUS,
    REJECTED,
    ROLLED_BACK,
    CLOSED,
)

REQUIRED_SCORING_VALIDATION_REQUIREMENTS = (
    "versioned scoring config",
    "before/after comparison",
    "scoring regression tests",
    "Phase 4I scores contract validation",
    "rollback plan",
    "deterministic runtime remains authoritative",
)

ADAPTIVE_SCORING_REVIEW_FIELDS = (
    "review_id",
    "source_materialization_id",
    "source_candidate_id",
    "review_type",
    "affected_domain",
    "affected_component",
    "proposed_change_summary",
    "proposed_config_version",
    "proposed_config",
    "baseline_reference",
    "before_after_summary",
    "validation_requirements",
    "rollback_plan",
    "runtime_influence_requested",
    "runtime_influence_granted",
    "status",
    "actor",
    "created_at",
    "validation_reference",
    "source_evidence",
)

PROPOSED_SCORING_CONFIG_FIELDS = (
    "config_id",
    "version",
    "config_type",
    "domain_weights",
    "thresholds",
    "severity_cutoffs",
    "confidence_rules",
    "trend_sensitivity",
    "anomaly_sensitivity",
    "status",
    "runtime_active",
    "runtime_influence_granted",
    "source_review_id",
)

_BASE_VALIDATION_CONCEPTS = (
    ("versioned", "scoring", "config"),
    ("before", "after", "comparison"),
    ("scoring", "regression", "test"),
    ("phase", "4i", "scores", "contract"),
    ("rollback", "plan"),
    ("deterministic", "runtime", "remains", "authoritative"),
)

_REVIEW_TYPE_VALIDATION_REQUIREMENTS = {
    DOMAIN_WEIGHT_REVIEW: (
        "domain score distribution comparison",
    ),
    THRESHOLD_REVIEW: (
        "threshold regression tests",
    ),
    SEVERITY_CUTOFF_REVIEW: (
        "severity distribution comparison",
    ),
    CONFIDENCE_LOGIC_REVIEW: (
        "confidence calibration validation",
    ),
    TREND_SENSITIVITY_REVIEW: (
        "trend regression validation",
    ),
    ANOMALY_SENSITIVITY_REVIEW: (
        "anomaly false positive/false negative review",
    ),
}

_REVIEW_TYPE_VALIDATION_CONCEPTS = {
    DOMAIN_WEIGHT_REVIEW: (
        ("domain", "score", "distribution", "comparison"),
    ),
    THRESHOLD_REVIEW: (
        ("threshold", "regression"),
    ),
    SEVERITY_CUTOFF_REVIEW: (
        ("severity", "distribution", "comparison"),
    ),
    CONFIDENCE_LOGIC_REVIEW: (
        ("confidence", "calibration"),
    ),
    TREND_SENSITIVITY_REVIEW: (
        ("trend", "regression"),
    ),
    ANOMALY_SENSITIVITY_REVIEW: (
        ("anomaly", "false", "positive", "negative"),
    ),
}


class AdaptiveScoringReviewError(ValueError):
    """Raised when a Phase 7O scoring review violates proposal-only rules."""


@dataclass(frozen=True)
class AdaptiveScoringReview:
    """Serializable proposal-only scoring review record."""

    review_id: str
    source_materialization_id: str
    source_candidate_id: str
    review_type: str
    affected_domain: str | None
    affected_component: str | None
    proposed_change_summary: str
    proposed_config_version: str
    proposed_config: dict[str, object]
    baseline_reference: str | None
    before_after_summary: str
    validation_requirements: list[str]
    rollback_plan: str
    runtime_influence_requested: bool = False
    runtime_influence_granted: bool = False
    status: str = PROPOSED
    actor: str = ""
    created_at: str | None = None
    validation_reference: str | None = None
    source_evidence: list[dict[str, object]] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_non_empty_string(self.review_id, "review_id")
        _require_non_empty_string(
            self.source_materialization_id,
            "source_materialization_id",
        )
        _require_non_empty_string(self.source_candidate_id, "source_candidate_id")
        _validate_review_type(self.review_type)
        _validate_optional_string(self.affected_domain, "affected_domain")
        _validate_optional_string(self.affected_component, "affected_component")
        _require_non_empty_string(self.proposed_change_summary, "proposed_change_summary")
        _require_non_empty_string(self.proposed_config_version, "proposed_config_version")
        _validate_optional_string(self.baseline_reference, "baseline_reference")
        _require_non_empty_string(self.before_after_summary, "before_after_summary")
        _require_non_empty_string(self.rollback_plan, "rollback_plan")
        _validate_status(self.status)
        _require_non_empty_string(self.actor, "actor")
        _validate_optional_string(self.created_at, "created_at")
        _validate_optional_string(self.validation_reference, "validation_reference")

        if not isinstance(self.runtime_influence_requested, bool):
            raise AdaptiveScoringReviewError("runtime_influence_requested must be a bool.")
        if self.runtime_influence_granted is not False:
            raise AdaptiveScoringReviewError(
                "Phase 7O adaptive scoring review cannot grant runtime influence."
            )

        proposed_config = _normalize_object_mapping(
            self.proposed_config,
            "proposed_config",
            allow_empty=False,
        )
        object.__setattr__(self, "proposed_config", proposed_config)

        requirements = _normalize_validation_requirements(self.validation_requirements)
        _validate_scoring_validation_concepts(self.review_type, requirements)
        object.__setattr__(self, "validation_requirements", requirements)
        object.__setattr__(
            self,
            "source_evidence",
            _normalize_source_evidence(self.source_evidence),
        )
        object.__setattr__(self, "runtime_influence_granted", False)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic serializable dictionary for this review."""

        return {
            field_name: deepcopy(getattr(self, field_name))
            for field_name in ADAPTIVE_SCORING_REVIEW_FIELDS
        }


@dataclass(frozen=True)
class ProposedScoringConfig:
    """Inactive versioned scoring configuration proposal."""

    config_id: str
    version: str
    config_type: str
    domain_weights: dict[str, float] = field(default_factory=dict)
    thresholds: dict[str, float] = field(default_factory=dict)
    severity_cutoffs: dict[str, float] = field(default_factory=dict)
    confidence_rules: dict[str, object] = field(default_factory=dict)
    trend_sensitivity: dict[str, object] = field(default_factory=dict)
    anomaly_sensitivity: dict[str, object] = field(default_factory=dict)
    status: str = PROPOSED
    runtime_active: bool = False
    runtime_influence_granted: bool = False
    source_review_id: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.config_id, "config_id")
        _require_non_empty_string(self.version, "version")
        _require_non_empty_string(self.config_type, "config_type")
        _validate_status(self.status)
        _validate_optional_string(self.source_review_id, "source_review_id")
        if self.runtime_active is not False:
            raise AdaptiveScoringReviewError(
                "Phase 7O proposed scoring configs cannot be runtime active."
            )
        if self.runtime_influence_granted is not False:
            raise AdaptiveScoringReviewError(
                "Phase 7O proposed scoring configs cannot grant runtime influence."
            )

        object.__setattr__(
            self,
            "domain_weights",
            _normalize_float_mapping(self.domain_weights, "domain_weights"),
        )
        object.__setattr__(
            self,
            "thresholds",
            _normalize_float_mapping(self.thresholds, "thresholds"),
        )
        object.__setattr__(
            self,
            "severity_cutoffs",
            _normalize_float_mapping(self.severity_cutoffs, "severity_cutoffs"),
        )
        object.__setattr__(
            self,
            "confidence_rules",
            _normalize_object_mapping(self.confidence_rules, "confidence_rules"),
        )
        object.__setattr__(
            self,
            "trend_sensitivity",
            _normalize_object_mapping(self.trend_sensitivity, "trend_sensitivity"),
        )
        object.__setattr__(
            self,
            "anomaly_sensitivity",
            _normalize_object_mapping(self.anomaly_sensitivity, "anomaly_sensitivity"),
        )
        object.__setattr__(self, "runtime_active", False)
        object.__setattr__(self, "runtime_influence_granted", False)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic serializable dictionary for this config."""

        return {
            field_name: deepcopy(getattr(self, field_name))
            for field_name in PROPOSED_SCORING_CONFIG_FIELDS
        }


def create_adaptive_scoring_review(
    materialization_artifact: MaterializationArtifact | Mapping[str, Any],
    actor: str,
    review_type: str,
    proposed_config: Mapping[str, Any],
    proposed_config_version: str,
    proposed_change_summary: str,
    before_after_summary: str,
    validation_requirements: Sequence[str] | None = None,
    rollback_plan: str | None = None,
    runtime_influence_requested: bool = False,
    baseline_reference: str | None = None,
) -> AdaptiveScoringReview:
    """Create an inactive scoring review from a scoring materialization artifact."""

    source = _coerce_source_artifact(materialization_artifact)
    _validate_source_artifact_for_review(source)
    _require_non_empty_string(actor, "actor")
    _validate_review_type(review_type)
    _require_non_empty_string(proposed_config_version, "proposed_config_version")
    _require_non_empty_string(proposed_change_summary, "proposed_change_summary")
    _require_non_empty_string(before_after_summary, "before_after_summary")
    _require_non_empty_string(rollback_plan, "rollback_plan")

    requirements = (
        required_scoring_validation_requirements(review_type)
        if validation_requirements is None
        else list(validation_requirements)
    )

    review = AdaptiveScoringReview(
        review_id=create_scoring_review_id(
            source.materialization_id,
            review_type,
            proposed_config_version,
        ),
        source_materialization_id=source.materialization_id,
        source_candidate_id=source.source_candidate_id,
        review_type=review_type,
        affected_domain=source.affected_domain,
        affected_component=source.affected_component,
        proposed_change_summary=proposed_change_summary,
        proposed_config_version=proposed_config_version,
        proposed_config=deepcopy(dict(proposed_config)),
        baseline_reference=baseline_reference,
        before_after_summary=before_after_summary,
        validation_requirements=requirements,
        rollback_plan="" if rollback_plan is None else rollback_plan,
        runtime_influence_requested=runtime_influence_requested,
        runtime_influence_granted=False,
        status=PROPOSED,
        actor=actor,
        created_at=None,
        validation_reference=None,
        source_evidence=deepcopy(source.source_evidence),
    )
    return validate_adaptive_scoring_review(review)


def validate_adaptive_scoring_review(
    review: AdaptiveScoringReview,
) -> AdaptiveScoringReview:
    """Validate and return a scoring review without activating runtime."""

    if not isinstance(review, AdaptiveScoringReview):
        raise AdaptiveScoringReviewError("review must be an AdaptiveScoringReview.")
    AdaptiveScoringReview(**review.to_dict())
    return review


def adaptive_scoring_review_to_dict(review: AdaptiveScoringReview) -> dict[str, Any]:
    """Return a deterministic dictionary for one scoring review."""

    return validate_adaptive_scoring_review(review).to_dict()


def adaptive_scoring_review_from_dict(data: Mapping[str, Any]) -> AdaptiveScoringReview:
    """Reconstruct and validate one scoring review from dictionary data."""

    if not isinstance(data, Mapping):
        raise AdaptiveScoringReviewError("review data must be a mapping.")
    missing = [
        field_name
        for field_name in (
            "review_id",
            "source_materialization_id",
            "source_candidate_id",
            "review_type",
            "proposed_change_summary",
            "proposed_config_version",
            "proposed_config",
            "before_after_summary",
            "validation_requirements",
            "rollback_plan",
            "actor",
        )
        if field_name not in data
    ]
    if missing:
        raise AdaptiveScoringReviewError(
            f"Missing adaptive scoring review fields: {', '.join(missing)}."
        )
    values = {
        field_name: deepcopy(data[field_name])
        for field_name in ADAPTIVE_SCORING_REVIEW_FIELDS
        if field_name in data
    }
    return AdaptiveScoringReview(**values)


def adaptive_scoring_reviews_to_dicts(
    reviews: Sequence[AdaptiveScoringReview],
) -> list[dict[str, Any]]:
    """Return deterministic dictionaries for scoring reviews."""

    return [adaptive_scoring_review_to_dict(review) for review in reviews]


def create_scoring_review_id(
    materialization_id: str,
    review_type: str,
    proposed_config_version: str,
) -> str:
    """Create a deterministic scoring review identifier from stable inputs."""

    _require_non_empty_string(materialization_id, "materialization_id")
    _validate_review_type(review_type)
    _require_non_empty_string(proposed_config_version, "proposed_config_version")
    return (
        f"SCORING-REVIEW-{_identifier_fragment(review_type)}-"
        f"{_identifier_fragment(materialization_id)}-"
        f"{_identifier_fragment(proposed_config_version)}"
    )


def create_proposed_scoring_config(
    review: AdaptiveScoringReview,
    config_type: str = "scoring_review",
) -> ProposedScoringConfig:
    """Create an inactive versioned proposed scoring config from a review."""

    review = validate_adaptive_scoring_review(review)
    _require_non_empty_string(config_type, "config_type")
    proposed_config = deepcopy(review.proposed_config)
    config = ProposedScoringConfig(
        config_id=_create_proposed_scoring_config_id(
            config_type,
            review.proposed_config_version,
            review.review_id,
        ),
        version=review.proposed_config_version,
        config_type=config_type,
        domain_weights=deepcopy(proposed_config.get("domain_weights", {})),
        thresholds=deepcopy(proposed_config.get("thresholds", {})),
        severity_cutoffs=deepcopy(proposed_config.get("severity_cutoffs", {})),
        confidence_rules=deepcopy(proposed_config.get("confidence_rules", {})),
        trend_sensitivity=deepcopy(proposed_config.get("trend_sensitivity", {})),
        anomaly_sensitivity=deepcopy(proposed_config.get("anomaly_sensitivity", {})),
        status=PROPOSED,
        runtime_active=False,
        runtime_influence_granted=False,
        source_review_id=review.review_id,
    )
    return validate_proposed_scoring_config(config)


def validate_proposed_scoring_config(
    config: ProposedScoringConfig,
) -> ProposedScoringConfig:
    """Validate and return a proposed scoring config without activating it."""

    if not isinstance(config, ProposedScoringConfig):
        raise AdaptiveScoringReviewError("config must be a ProposedScoringConfig.")
    ProposedScoringConfig(**config.to_dict())
    return config


def proposed_scoring_config_to_dict(config: ProposedScoringConfig) -> dict[str, Any]:
    """Return a deterministic dictionary for one proposed scoring config."""

    return validate_proposed_scoring_config(config).to_dict()


def proposed_scoring_config_from_dict(data: Mapping[str, Any]) -> ProposedScoringConfig:
    """Reconstruct and validate one proposed scoring config from dictionary data."""

    if not isinstance(data, Mapping):
        raise AdaptiveScoringReviewError("config data must be a mapping.")
    missing = [
        field_name
        for field_name in ("config_id", "version", "config_type")
        if field_name not in data
    ]
    if missing:
        raise AdaptiveScoringReviewError(
            f"Missing proposed scoring config fields: {', '.join(missing)}."
        )
    values = {
        field_name: deepcopy(data[field_name])
        for field_name in PROPOSED_SCORING_CONFIG_FIELDS
        if field_name in data
    }
    return ProposedScoringConfig(**values)


def required_scoring_validation_requirements(review_type: str) -> list[str]:
    """Return required scoring validation requirements for one review type."""

    _validate_review_type(review_type)
    requirements = list(REQUIRED_SCORING_VALIDATION_REQUIREMENTS)
    requirements.extend(_REVIEW_TYPE_VALIDATION_REQUIREMENTS.get(review_type, ()))
    return requirements


def is_supported_scoring_review_type(review_type: str) -> bool:
    """Return True when review_type is supported by Phase 7O."""

    return review_type in SCORING_REVIEW_TYPES


def _coerce_source_artifact(
    materialization_artifact: MaterializationArtifact | Mapping[str, Any],
) -> MaterializationArtifact:
    if isinstance(materialization_artifact, MaterializationArtifact):
        source = materialization_artifact
    elif isinstance(materialization_artifact, Mapping):
        try:
            source = materialization_artifact_from_dict(materialization_artifact)
        except MaterializationArtifactError as exc:
            raise AdaptiveScoringReviewError(str(exc)) from exc
    else:
        raise AdaptiveScoringReviewError(
            "materialization_artifact must be a MaterializationArtifact or mapping."
        )

    try:
        return validate_materialization_artifact(source)
    except MaterializationArtifactError as exc:
        raise AdaptiveScoringReviewError(str(exc)) from exc


def _validate_source_artifact_for_review(source: MaterializationArtifact) -> None:
    if source.proposed_artifact_type != SCORING_REVIEW_ARTIFACT:
        raise AdaptiveScoringReviewError(
            "Adaptive scoring review requires a scoring_review_artifact source."
        )
    if not is_runtime_sensitive_artifact_type(source.proposed_artifact_type):
        raise AdaptiveScoringReviewError(
            "Adaptive scoring review source artifact must be runtime-sensitive."
        )
    if source.runtime_influence_granted is not False:
        raise AdaptiveScoringReviewError(
            "Adaptive scoring review source cannot have runtime influence granted."
        )
    if source.status not in (MATERIALIZED, VALIDATED):
        raise AdaptiveScoringReviewError(
            "Adaptive scoring review source must be MATERIALIZED or VALIDATED."
        )


def _create_proposed_scoring_config_id(
    config_type: str,
    version: str,
    source_review_id: str,
) -> str:
    _require_non_empty_string(config_type, "config_type")
    _require_non_empty_string(version, "version")
    _require_non_empty_string(source_review_id, "source_review_id")
    return (
        f"SCORING-CONFIG-{_identifier_fragment(config_type)}-"
        f"{_identifier_fragment(version)}-{_identifier_fragment(source_review_id)}"
    )


def _validate_scoring_validation_concepts(
    review_type: str,
    requirements: Sequence[str],
) -> None:
    normalized_requirements = [_normalize_text(requirement) for requirement in requirements]
    concepts = list(_BASE_VALIDATION_CONCEPTS)
    concepts.extend(_REVIEW_TYPE_VALIDATION_CONCEPTS.get(review_type, ()))
    for concept in concepts:
        if not any(
            all(token in normalized_requirement for token in concept)
            for normalized_requirement in normalized_requirements
        ):
            raise AdaptiveScoringReviewError(
                "validation_requirements missing required concept: "
                f"{' '.join(concept)}."
            )


def _validate_review_type(review_type: Any) -> None:
    if review_type not in SCORING_REVIEW_TYPES:
        raise AdaptiveScoringReviewError(f"Unsupported scoring review type: {review_type!r}.")


def _validate_status(status: Any) -> None:
    if status not in PROPOSED_SCORING_CONFIG_STATUSES:
        raise AdaptiveScoringReviewError(f"Unsupported scoring review status: {status!r}.")


def _normalize_validation_requirements(requirements: Any) -> list[str]:
    if not isinstance(requirements, list):
        raise AdaptiveScoringReviewError("validation_requirements must be a list.")
    if not requirements:
        raise AdaptiveScoringReviewError("validation_requirements must not be empty.")
    normalized: list[str] = []
    for requirement in requirements:
        if not isinstance(requirement, str) or not requirement.strip():
            raise AdaptiveScoringReviewError(
                "validation_requirements must contain non-empty strings."
            )
        normalized.append(requirement.strip())
    return normalized


def _normalize_source_evidence(source_evidence: Any) -> list[dict[str, object]]:
    if source_evidence is None:
        return []
    if not isinstance(source_evidence, list):
        raise AdaptiveScoringReviewError("source_evidence must be a list.")
    normalized: list[dict[str, object]] = []
    for item in source_evidence:
        if not isinstance(item, Mapping):
            raise AdaptiveScoringReviewError(
                "source_evidence must contain mapping objects only."
            )
        normalized.append(deepcopy(dict(item)))
    return normalized


def _normalize_float_mapping(data: Any, field_name: str) -> dict[str, float]:
    if data is None:
        return {}
    if not isinstance(data, Mapping):
        raise AdaptiveScoringReviewError(f"{field_name} must be a mapping.")
    normalized: dict[str, float] = {}
    for key, value in data.items():
        _require_non_empty_string(key, f"{field_name} key")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise AdaptiveScoringReviewError(f"{field_name} values must be numeric.")
        normalized[str(key)] = float(value)
    return normalized


def _normalize_object_mapping(
    data: Any,
    field_name: str,
    allow_empty: bool = True,
) -> dict[str, object]:
    if data is None:
        data = {}
    if not isinstance(data, Mapping):
        raise AdaptiveScoringReviewError(f"{field_name} must be a mapping.")
    normalized = deepcopy(dict(data))
    if not allow_empty and not normalized:
        raise AdaptiveScoringReviewError(f"{field_name} must not be empty.")
    return normalized


def _require_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise AdaptiveScoringReviewError(f"{field_name} must be a non-empty string.")


def _validate_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise AdaptiveScoringReviewError(f"{field_name} must be None or a string.")
    if isinstance(value, str) and not value.strip():
        raise AdaptiveScoringReviewError(f"{field_name} must not be blank.")


def _identifier_fragment(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "UNSPECIFIED"


def _normalize_text(value: str) -> str:
    text = value.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()
