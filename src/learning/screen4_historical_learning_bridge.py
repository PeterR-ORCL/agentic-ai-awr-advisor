"""Phase 7BC Screen 4 historical review to learning intent bridge.

The records in this module describe local intent metadata derived from Screen 4
historical review. They do not persist intents, create candidates, create
dataset labels, execute governance actions, invoke write paths, execute
analysis, modify dashboards, modify CLI behavior, or mutate deterministic
historical truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from src.learning.screen4_trend_anomaly_review import (
    HistoricalAnomalyReviewRecord,
    HistoricalTrendReviewRecord,
    HISTORICAL_REVIEW_DECISIONS,
)


HISTORICAL_CANDIDATE_TYPES = (
    "scoring_weight_review_candidate",
    "recommendation_rule_candidate",
    "validation_candidate",
    "documentation_candidate",
    "parser_mapping_candidate",
)

HISTORICAL_LEARNING_SIGNAL_TYPES = (
    "trend_review_signal",
    "anomaly_review_signal",
    "recurrence_signal",
    "false_positive_signal",
    "evidence_quality_signal",
    "baseline_quality_signal",
    "scoring_review_signal",
)

HISTORICAL_LEARNING_LABEL_NAMES = (
    "issue_recurred",
    "false_positive",
    "false_negative",
    "no_change",
    "risk_confirmed",
    "unknown_outcome",
)

HISTORICAL_GOVERNANCE_ROUTE_TYPES = (
    "scoring_review",
    "recommendation_review",
    "evidence_validation",
    "human_review",
    "learning_candidate_request",
    "documentation_review",
)

HISTORICAL_GOVERNANCE_ROUTE_TARGETS = (
    "scoring_governance",
    "recommendation_governance",
    "evidence_quality",
    "human_review_queue",
    "learning_candidate_queue",
    "documentation_queue",
)

HISTORICAL_BRIDGE_STATUSES = (
    "valid_intents_only",
    "no_reviews",
    "invalid",
    "blocked",
)

_DECISION_TO_CANDIDATE_TYPE = {
    "request_trend_aware_scoring_review": "scoring_weight_review_candidate",
    "request_anomaly_sensitivity_review": "scoring_weight_review_candidate",
    "request_scoring_threshold_review": "scoring_weight_review_candidate",
    "request_learning_candidate": "validation_candidate",
    "mark_anomaly_false_positive": "validation_candidate",
    "dispute_trend": "validation_candidate",
    "mark_trend_insufficient": "validation_candidate",
    "mark_anomaly_insufficient": "validation_candidate",
    "add_historical_review_note": "documentation_candidate",
    "approve_trend": "documentation_candidate",
    "approve_anomaly": "documentation_candidate",
}

_DECISION_TO_SIGNAL_TYPE = {
    "approve_trend": "trend_review_signal",
    "dispute_trend": "trend_review_signal",
    "mark_trend_insufficient": "evidence_quality_signal",
    "approve_anomaly": "anomaly_review_signal",
    "mark_anomaly_false_positive": "false_positive_signal",
    "mark_anomaly_insufficient": "evidence_quality_signal",
    "request_trend_aware_scoring_review": "scoring_review_signal",
    "request_anomaly_sensitivity_review": "scoring_review_signal",
    "request_scoring_threshold_review": "scoring_review_signal",
    "request_learning_candidate": "recurrence_signal",
    "add_historical_review_note": "baseline_quality_signal",
}

_DECISION_TO_LABEL_NAME = {
    "approve_trend": "risk_confirmed",
    "dispute_trend": "unknown_outcome",
    "mark_trend_insufficient": "unknown_outcome",
    "approve_anomaly": "risk_confirmed",
    "mark_anomaly_false_positive": "false_positive",
    "mark_anomaly_insufficient": "unknown_outcome",
    "request_trend_aware_scoring_review": "unknown_outcome",
    "request_anomaly_sensitivity_review": "unknown_outcome",
    "request_scoring_threshold_review": "unknown_outcome",
    "request_learning_candidate": "issue_recurred",
    "add_historical_review_note": "unknown_outcome",
}

_DECISION_TO_ROUTE = {
    "approve_trend": ("documentation_review", "documentation_queue"),
    "dispute_trend": ("human_review", "human_review_queue"),
    "mark_trend_insufficient": ("evidence_validation", "evidence_quality"),
    "approve_anomaly": ("documentation_review", "documentation_queue"),
    "mark_anomaly_false_positive": ("evidence_validation", "evidence_quality"),
    "mark_anomaly_insufficient": ("evidence_validation", "evidence_quality"),
    "request_trend_aware_scoring_review": ("scoring_review", "scoring_governance"),
    "request_anomaly_sensitivity_review": (
        "scoring_review",
        "scoring_governance",
    ),
    "request_scoring_threshold_review": ("scoring_review", "scoring_governance"),
    "request_learning_candidate": (
        "learning_candidate_request",
        "learning_candidate_queue",
    ),
    "add_historical_review_note": ("documentation_review", "documentation_queue"),
}


class Screen4HistoricalLearningBridgeError(ValueError):
    """Raised when Phase 7BC historical learning bridge metadata is invalid."""


@dataclass(frozen=True)
class HistoricalLearningCandidateIntent:
    """Local intent for a future candidate derived from historical review."""

    intent_id: str
    source_review_id: str | None = None
    source_trend_review_id: str | None = None
    source_anomaly_review_id: str | None = None
    source_baseline_candidate_id: str | None = None
    candidate_type: str = "validation_candidate"
    affected_domain: str | None = None
    affected_component: str | None = None
    rationale: str = ""
    source_evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    requires_human_review: bool = True
    candidate_created: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.intent_id, "intent_id")
        _require_optional_string(self.source_review_id, "source_review_id")
        _require_optional_string(
            self.source_trend_review_id,
            "source_trend_review_id",
        )
        _require_optional_string(
            self.source_anomaly_review_id,
            "source_anomaly_review_id",
        )
        _require_optional_string(
            self.source_baseline_candidate_id,
            "source_baseline_candidate_id",
        )
        _require_supported(
            self.candidate_type,
            HISTORICAL_CANDIDATE_TYPES,
            "candidate_type",
        )
        _require_optional_string(self.affected_domain, "affected_domain")
        _require_optional_string(self.affected_component, "affected_component")
        _require_nonempty_string(self.rationale, "rationale")
        _require_string_list(self.source_evidence, "source_evidence")
        _require_confidence(self.confidence, "confidence")
        _require_boolean(self.requires_human_review, "requires_human_review")
        _require_true(self.requires_human_review, "requires_human_review")
        _require_boolean(self.candidate_created, "candidate_created")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _require_boolean(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _reject_true(self.candidate_created, "candidate_created")
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class HistoricalLearningSignalIntent:
    """Local learning signal intent derived from historical review."""

    signal_intent_id: str
    signal_type: str
    label_name: str
    label_value: str
    source_review_id: str | None = None
    source_trend_review_id: str | None = None
    source_anomaly_review_id: str | None = None
    affected_domain: str | None = None
    confidence: float = 0.0
    dataset_label_created: bool = False
    requires_human_review: bool = True
    runtime_influence: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.signal_intent_id, "signal_intent_id")
        _require_supported(
            self.signal_type,
            HISTORICAL_LEARNING_SIGNAL_TYPES,
            "signal_type",
        )
        _require_supported(
            self.label_name,
            HISTORICAL_LEARNING_LABEL_NAMES,
            "label_name",
        )
        _require_nonempty_string(self.label_value, "label_value")
        _require_optional_string(self.source_review_id, "source_review_id")
        _require_optional_string(
            self.source_trend_review_id,
            "source_trend_review_id",
        )
        _require_optional_string(
            self.source_anomaly_review_id,
            "source_anomaly_review_id",
        )
        _require_optional_string(self.affected_domain, "affected_domain")
        _require_confidence(self.confidence, "confidence")
        _require_boolean(self.dataset_label_created, "dataset_label_created")
        _require_boolean(self.requires_human_review, "requires_human_review")
        _require_true(self.requires_human_review, "requires_human_review")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _reject_true(self.dataset_label_created, "dataset_label_created")
        _reject_true(self.runtime_influence, "runtime_influence")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class HistoricalGovernanceRoute:
    """Local governance route intent derived from historical review."""

    route_id: str
    route_type: str
    route_target: str
    source_review_id: str | None = None
    affected_domain: str | None = None
    recommended_action: str = ""
    governance_workflow: str | None = None
    route_status: str = "proposed"
    governance_action_performed: bool = False
    candidate_created: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.route_id, "route_id")
        _require_supported(
            self.route_type,
            HISTORICAL_GOVERNANCE_ROUTE_TYPES,
            "route_type",
        )
        _require_supported(
            self.route_target,
            HISTORICAL_GOVERNANCE_ROUTE_TARGETS,
            "route_target",
        )
        _require_optional_string(self.source_review_id, "source_review_id")
        _require_optional_string(self.affected_domain, "affected_domain")
        _require_nonempty_string(self.recommended_action, "recommended_action")
        _require_optional_string(self.governance_workflow, "governance_workflow")
        _require_nonempty_string(self.route_status, "route_status")
        _require_boolean(
            self.governance_action_performed,
            "governance_action_performed",
        )
        _require_boolean(self.candidate_created, "candidate_created")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _require_boolean(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _reject_true(
            self.governance_action_performed,
            "governance_action_performed",
        )
        _reject_true(self.candidate_created, "candidate_created")
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class HistoricalReviewLearningBridgeResult:
    """Summary of local historical review bridge intent metadata."""

    bridge_result_id: str
    source_review_count: int
    candidate_intent_count: int
    learning_signal_intent_count: int
    governance_route_count: int
    candidate_intents: list[HistoricalLearningCandidateIntent] = field(default_factory=list)
    learning_signal_intents: list[HistoricalLearningSignalIntent] = field(default_factory=list)
    governance_routes: list[HistoricalGovernanceRoute] = field(default_factory=list)
    bridge_status: str = "valid_intents_only"
    candidates_created: bool = False
    dataset_labels_created: bool = False
    governance_actions_performed: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.bridge_result_id, "bridge_result_id")
        _require_nonnegative_int(self.source_review_count, "source_review_count")
        _require_nonnegative_int(self.candidate_intent_count, "candidate_intent_count")
        _require_nonnegative_int(
            self.learning_signal_intent_count,
            "learning_signal_intent_count",
        )
        _require_nonnegative_int(self.governance_route_count, "governance_route_count")
        _require_intent_list(
            self.candidate_intents,
            HistoricalLearningCandidateIntent,
            "candidate_intents",
        )
        _require_intent_list(
            self.learning_signal_intents,
            HistoricalLearningSignalIntent,
            "learning_signal_intents",
        )
        _require_intent_list(
            self.governance_routes,
            HistoricalGovernanceRoute,
            "governance_routes",
        )
        _require_supported(
            self.bridge_status,
            HISTORICAL_BRIDGE_STATUSES,
            "bridge_status",
        )
        _require_boolean(self.candidates_created, "candidates_created")
        _require_boolean(self.dataset_labels_created, "dataset_labels_created")
        _require_boolean(
            self.governance_actions_performed,
            "governance_actions_performed",
        )
        _require_boolean(self.runtime_influence, "runtime_influence")
        _require_boolean(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _reject_true(self.candidates_created, "candidates_created")
        _reject_true(self.dataset_labels_created, "dataset_labels_created")
        _reject_true(
            self.governance_actions_performed,
            "governance_actions_performed",
        )
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_string_list(self.denied_reasons, "denied_reasons")
        _require_string_list(self.warnings, "warnings")
        _require_string_list(self.required_next_steps, "required_next_steps")
        _require_optional_string(self.notes, "notes")


def create_historical_candidate_intent_id(
    source_review_id: str,
    candidate_type: str,
) -> str:
    """Create a deterministic historical candidate intent id."""

    _require_nonempty_string(source_review_id, "source_review_id")
    _require_supported(candidate_type, HISTORICAL_CANDIDATE_TYPES, "candidate_type")
    return (
        "SCREEN4-HIST-CANDIDATE-INTENT-"
        f"{_normalize_token(source_review_id)}-"
        f"{_normalize_token(candidate_type)}"
    )


def create_historical_signal_intent_id(
    source_review_id: str,
    signal_type: str,
    label_name: str,
) -> str:
    """Create a deterministic historical signal intent id."""

    _require_nonempty_string(source_review_id, "source_review_id")
    _require_supported(signal_type, HISTORICAL_LEARNING_SIGNAL_TYPES, "signal_type")
    _require_supported(label_name, HISTORICAL_LEARNING_LABEL_NAMES, "label_name")
    return (
        "SCREEN4-HIST-SIGNAL-INTENT-"
        f"{_normalize_token(source_review_id)}-"
        f"{_normalize_token(signal_type)}-"
        f"{_normalize_token(label_name)}"
    )


def create_historical_governance_route_id(
    source_review_id: str,
    route_type: str,
    route_target: str,
) -> str:
    """Create a deterministic historical governance route id."""

    _require_nonempty_string(source_review_id, "source_review_id")
    _require_supported(route_type, HISTORICAL_GOVERNANCE_ROUTE_TYPES, "route_type")
    _require_supported(
        route_target,
        HISTORICAL_GOVERNANCE_ROUTE_TARGETS,
        "route_target",
    )
    return (
        "SCREEN4-HIST-GOVERNANCE-ROUTE-"
        f"{_normalize_token(source_review_id)}-"
        f"{_normalize_token(route_type)}-"
        f"{_normalize_token(route_target)}"
    )


def create_historical_bridge_result_id(source_review_count: int) -> str:
    """Create a deterministic historical bridge result id."""

    _require_nonnegative_int(source_review_count, "source_review_count")
    return f"SCREEN4-HIST-BRIDGE-RESULT-{source_review_count}"


def validate_historical_learning_candidate_intent(
    intent: HistoricalLearningCandidateIntent,
) -> HistoricalLearningCandidateIntent:
    """Validate and return historical candidate intent metadata."""

    if not isinstance(intent, HistoricalLearningCandidateIntent):
        raise Screen4HistoricalLearningBridgeError(
            "intent must be a HistoricalLearningCandidateIntent instance."
        )
    intent.__post_init__()
    return intent


def validate_historical_learning_signal_intent(
    intent: HistoricalLearningSignalIntent,
) -> HistoricalLearningSignalIntent:
    """Validate and return historical learning signal intent metadata."""

    if not isinstance(intent, HistoricalLearningSignalIntent):
        raise Screen4HistoricalLearningBridgeError(
            "intent must be a HistoricalLearningSignalIntent instance."
        )
    intent.__post_init__()
    return intent


def validate_historical_governance_route(
    route: HistoricalGovernanceRoute,
) -> HistoricalGovernanceRoute:
    """Validate and return historical governance route metadata."""

    if not isinstance(route, HistoricalGovernanceRoute):
        raise Screen4HistoricalLearningBridgeError(
            "route must be a HistoricalGovernanceRoute instance."
        )
    route.__post_init__()
    return route


def validate_historical_review_learning_bridge_result(
    result: HistoricalReviewLearningBridgeResult,
) -> HistoricalReviewLearningBridgeResult:
    """Validate and return historical bridge result metadata."""

    if not isinstance(result, HistoricalReviewLearningBridgeResult):
        raise Screen4HistoricalLearningBridgeError(
            "result must be a HistoricalReviewLearningBridgeResult instance."
        )
    result.__post_init__()
    return result


def candidate_type_for_historical_decision(
    decision: str,
    context: dict[str, Any] | None = None,
) -> str:
    """Return candidate intent type metadata for a historical review decision."""

    _require_supported(decision, HISTORICAL_REVIEW_DECISIONS, "decision")
    context = dict(context or {})
    requested_type = _optional_text(context.get("candidate_type"))
    if requested_type:
        _require_supported(
            requested_type,
            HISTORICAL_CANDIDATE_TYPES,
            "candidate_type",
        )
        return requested_type
    if context.get("recurrence_pattern") and context.get("recommendation_context"):
        return "recommendation_rule_candidate"
    if context.get("recurrence_pattern"):
        return "scoring_weight_review_candidate"
    return _DECISION_TO_CANDIDATE_TYPE[decision]


def signal_type_for_historical_decision(decision: str) -> str:
    """Return learning signal intent type metadata for a historical decision."""

    _require_supported(decision, HISTORICAL_REVIEW_DECISIONS, "decision")
    return _DECISION_TO_SIGNAL_TYPE[decision]


def label_name_for_historical_decision(decision: str) -> str:
    """Return label name metadata for a historical decision."""

    _require_supported(decision, HISTORICAL_REVIEW_DECISIONS, "decision")
    return _DECISION_TO_LABEL_NAME[decision]


def route_historical_review_to_governance(
    review: HistoricalTrendReviewRecord | HistoricalAnomalyReviewRecord,
) -> list[HistoricalGovernanceRoute]:
    """Create local governance route intent metadata for a review."""

    source_review_id = _source_review_id(review)
    decision = _review_decision(review)
    route_type, route_target = _DECISION_TO_ROUTE[decision]
    route = HistoricalGovernanceRoute(
        route_id=create_historical_governance_route_id(
            source_review_id,
            route_type,
            route_target,
        ),
        route_type=route_type,
        route_target=route_target,
        source_review_id=source_review_id,
        affected_domain=_optional_text(getattr(review, "domain", None)),
        recommended_action=(
            f"Review {decision.replace('_', ' ')} through future governed workflow"
        ),
        governance_workflow=f"{route_type}_workflow_preview",
        route_status="proposed",
        governance_action_performed=False,
        candidate_created=False,
        runtime_influence=False,
        phase4i_mutation_requested=False,
        notes=_optional_text(getattr(review, "notes", None)),
    )
    return [route]


def create_candidate_intents_from_historical_reviews(
    reviews: list[HistoricalTrendReviewRecord | HistoricalAnomalyReviewRecord],
) -> list[HistoricalLearningCandidateIntent]:
    """Create local candidate intent metadata from historical reviews."""

    _require_review_list(reviews, "reviews")
    intents: list[HistoricalLearningCandidateIntent] = []
    for review in reviews:
        decision = _review_decision(review)
        source_review_id = _source_review_id(review)
        context = {
            "recurrence_pattern": "recurrence" in _optional_text(
                getattr(review, "review_notes", "")
            ).lower(),
        }
        candidate_type = candidate_type_for_historical_decision(decision, context)
        intents.append(
            HistoricalLearningCandidateIntent(
                intent_id=create_historical_candidate_intent_id(
                    source_review_id,
                    candidate_type,
                ),
                source_review_id=source_review_id,
                source_trend_review_id=(
                    source_review_id
                    if isinstance(review, HistoricalTrendReviewRecord)
                    else None
                ),
                source_anomaly_review_id=(
                    source_review_id
                    if isinstance(review, HistoricalAnomalyReviewRecord)
                    else None
                ),
                source_baseline_candidate_id=_optional_text(
                    getattr(review, "baseline_candidate_id", None)
                ),
                candidate_type=candidate_type,
                affected_domain=_optional_text(getattr(review, "domain", None)),
                affected_component=_review_component(review),
                rationale=f"Historical review decision {decision} requires future review.",
                source_evidence=_review_source_evidence(review),
                confidence=0.7,
                requires_human_review=True,
                candidate_created=False,
                runtime_influence=False,
                phase4i_mutation_requested=False,
                notes=_optional_text(getattr(review, "notes", None)),
            )
        )
    return intents


def create_learning_signal_intents_from_historical_reviews(
    reviews: list[HistoricalTrendReviewRecord | HistoricalAnomalyReviewRecord],
) -> list[HistoricalLearningSignalIntent]:
    """Create local learning signal intent metadata from historical reviews."""

    _require_review_list(reviews, "reviews")
    intents: list[HistoricalLearningSignalIntent] = []
    for review in reviews:
        decision = _review_decision(review)
        source_review_id = _source_review_id(review)
        signal_type = signal_type_for_historical_decision(decision)
        label_name = label_name_for_historical_decision(decision)
        intents.append(
            HistoricalLearningSignalIntent(
                signal_intent_id=create_historical_signal_intent_id(
                    source_review_id,
                    signal_type,
                    label_name,
                ),
                signal_type=signal_type,
                label_name=label_name,
                label_value=_label_value_for_decision(decision),
                source_review_id=source_review_id,
                source_trend_review_id=(
                    source_review_id
                    if isinstance(review, HistoricalTrendReviewRecord)
                    else None
                ),
                source_anomaly_review_id=(
                    source_review_id
                    if isinstance(review, HistoricalAnomalyReviewRecord)
                    else None
                ),
                affected_domain=_optional_text(getattr(review, "domain", None)),
                confidence=0.7,
                dataset_label_created=False,
                requires_human_review=True,
                runtime_influence=False,
                notes=_optional_text(getattr(review, "notes", None)),
            )
        )
    return intents


def bridge_historical_reviews(
    trend_reviews: list[HistoricalTrendReviewRecord] | None = None,
    anomaly_reviews: list[HistoricalAnomalyReviewRecord] | None = None,
    notes: str | None = None,
) -> HistoricalReviewLearningBridgeResult:
    """Bridge historical reviews to local intent metadata only."""

    trend_reviews = list(trend_reviews or [])
    anomaly_reviews = list(anomaly_reviews or [])
    _require_review_list(trend_reviews, "trend_reviews")
    _require_review_list(anomaly_reviews, "anomaly_reviews")
    reviews: list[HistoricalTrendReviewRecord | HistoricalAnomalyReviewRecord] = [
        *trend_reviews,
        *anomaly_reviews,
    ]
    candidate_intents = create_candidate_intents_from_historical_reviews(reviews)
    learning_signal_intents = create_learning_signal_intents_from_historical_reviews(
        reviews
    )
    governance_routes: list[HistoricalGovernanceRoute] = []
    for review in reviews:
        governance_routes.extend(route_historical_review_to_governance(review))

    source_review_count = len(reviews)
    bridge_status = "valid_intents_only" if reviews else "no_reviews"
    return HistoricalReviewLearningBridgeResult(
        bridge_result_id=create_historical_bridge_result_id(source_review_count),
        source_review_count=source_review_count,
        candidate_intent_count=len(candidate_intents),
        learning_signal_intent_count=len(learning_signal_intents),
        governance_route_count=len(governance_routes),
        candidate_intents=candidate_intents,
        learning_signal_intents=learning_signal_intents,
        governance_routes=governance_routes,
        bridge_status=bridge_status,
        candidates_created=False,
        dataset_labels_created=False,
        governance_actions_performed=False,
        runtime_influence=False,
        phase4i_mutation_requested=False,
        denied_reasons=[],
        warnings=[
            "Historical review bridge emits intents only.",
            "Candidate intents are not candidates.",
            "Learning signal intents are not dataset labels.",
        ],
        required_next_steps=["Route through future governed workflow before creation."],
        notes=notes,
    )


def historical_learning_candidate_intent_to_dict(
    intent: HistoricalLearningCandidateIntent,
) -> dict[str, Any]:
    """Serialize historical candidate intent metadata."""

    intent = validate_historical_learning_candidate_intent(intent)
    return {
        "intent_id": intent.intent_id,
        "source_review_id": intent.source_review_id,
        "source_trend_review_id": intent.source_trend_review_id,
        "source_anomaly_review_id": intent.source_anomaly_review_id,
        "source_baseline_candidate_id": intent.source_baseline_candidate_id,
        "candidate_type": intent.candidate_type,
        "affected_domain": intent.affected_domain,
        "affected_component": intent.affected_component,
        "rationale": intent.rationale,
        "source_evidence": list(intent.source_evidence),
        "confidence": intent.confidence,
        "requires_human_review": intent.requires_human_review,
        "candidate_created": intent.candidate_created,
        "runtime_influence": intent.runtime_influence,
        "phase4i_mutation_requested": intent.phase4i_mutation_requested,
        "notes": intent.notes,
    }


def historical_learning_candidate_intent_from_dict(
    data: dict[str, Any],
) -> HistoricalLearningCandidateIntent:
    """Deserialize historical candidate intent metadata."""

    _require_mapping(data, "candidate_intent")
    return HistoricalLearningCandidateIntent(
        intent_id=str(data["intent_id"]),
        source_review_id=_optional_text(data.get("source_review_id")),
        source_trend_review_id=_optional_text(data.get("source_trend_review_id")),
        source_anomaly_review_id=_optional_text(data.get("source_anomaly_review_id")),
        source_baseline_candidate_id=_optional_text(
            data.get("source_baseline_candidate_id")
        ),
        candidate_type=str(data["candidate_type"]),
        affected_domain=_optional_text(data.get("affected_domain")),
        affected_component=_optional_text(data.get("affected_component")),
        rationale=str(data["rationale"]),
        source_evidence=list(data.get("source_evidence") or []),
        confidence=float(data.get("confidence", 0.0)),
        requires_human_review=_bool_from_mapping(
            data,
            "requires_human_review",
            True,
        ),
        candidate_created=_bool_from_mapping(data, "candidate_created", False),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        notes=_optional_text(data.get("notes")),
    )


def historical_learning_signal_intent_to_dict(
    intent: HistoricalLearningSignalIntent,
) -> dict[str, Any]:
    """Serialize historical learning signal intent metadata."""

    intent = validate_historical_learning_signal_intent(intent)
    return {
        "signal_intent_id": intent.signal_intent_id,
        "signal_type": intent.signal_type,
        "label_name": intent.label_name,
        "label_value": intent.label_value,
        "source_review_id": intent.source_review_id,
        "source_trend_review_id": intent.source_trend_review_id,
        "source_anomaly_review_id": intent.source_anomaly_review_id,
        "affected_domain": intent.affected_domain,
        "confidence": intent.confidence,
        "dataset_label_created": intent.dataset_label_created,
        "requires_human_review": intent.requires_human_review,
        "runtime_influence": intent.runtime_influence,
        "notes": intent.notes,
    }


def historical_learning_signal_intent_from_dict(
    data: dict[str, Any],
) -> HistoricalLearningSignalIntent:
    """Deserialize historical learning signal intent metadata."""

    _require_mapping(data, "signal_intent")
    return HistoricalLearningSignalIntent(
        signal_intent_id=str(data["signal_intent_id"]),
        signal_type=str(data["signal_type"]),
        label_name=str(data["label_name"]),
        label_value=str(data["label_value"]),
        source_review_id=_optional_text(data.get("source_review_id")),
        source_trend_review_id=_optional_text(data.get("source_trend_review_id")),
        source_anomaly_review_id=_optional_text(data.get("source_anomaly_review_id")),
        affected_domain=_optional_text(data.get("affected_domain")),
        confidence=float(data.get("confidence", 0.0)),
        dataset_label_created=_bool_from_mapping(
            data,
            "dataset_label_created",
            False,
        ),
        requires_human_review=_bool_from_mapping(
            data,
            "requires_human_review",
            True,
        ),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        notes=_optional_text(data.get("notes")),
    )


def historical_governance_route_to_dict(
    route: HistoricalGovernanceRoute,
) -> dict[str, Any]:
    """Serialize historical governance route metadata."""

    route = validate_historical_governance_route(route)
    return {
        "route_id": route.route_id,
        "route_type": route.route_type,
        "route_target": route.route_target,
        "source_review_id": route.source_review_id,
        "affected_domain": route.affected_domain,
        "recommended_action": route.recommended_action,
        "governance_workflow": route.governance_workflow,
        "route_status": route.route_status,
        "governance_action_performed": route.governance_action_performed,
        "candidate_created": route.candidate_created,
        "runtime_influence": route.runtime_influence,
        "phase4i_mutation_requested": route.phase4i_mutation_requested,
        "notes": route.notes,
    }


def historical_governance_route_from_dict(
    data: dict[str, Any],
) -> HistoricalGovernanceRoute:
    """Deserialize historical governance route metadata."""

    _require_mapping(data, "governance_route")
    return HistoricalGovernanceRoute(
        route_id=str(data["route_id"]),
        route_type=str(data["route_type"]),
        route_target=str(data["route_target"]),
        source_review_id=_optional_text(data.get("source_review_id")),
        affected_domain=_optional_text(data.get("affected_domain")),
        recommended_action=str(data["recommended_action"]),
        governance_workflow=_optional_text(data.get("governance_workflow")),
        route_status=str(data.get("route_status", "proposed")),
        governance_action_performed=_bool_from_mapping(
            data,
            "governance_action_performed",
            False,
        ),
        candidate_created=_bool_from_mapping(data, "candidate_created", False),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        notes=_optional_text(data.get("notes")),
    )


def historical_review_learning_bridge_result_to_dict(
    result: HistoricalReviewLearningBridgeResult,
) -> dict[str, Any]:
    """Serialize historical bridge result metadata."""

    result = validate_historical_review_learning_bridge_result(result)
    return {
        "bridge_result_id": result.bridge_result_id,
        "source_review_count": result.source_review_count,
        "candidate_intent_count": result.candidate_intent_count,
        "learning_signal_intent_count": result.learning_signal_intent_count,
        "governance_route_count": result.governance_route_count,
        "candidate_intents": [
            historical_learning_candidate_intent_to_dict(intent)
            for intent in result.candidate_intents
        ],
        "learning_signal_intents": [
            historical_learning_signal_intent_to_dict(intent)
            for intent in result.learning_signal_intents
        ],
        "governance_routes": [
            historical_governance_route_to_dict(route)
            for route in result.governance_routes
        ],
        "bridge_status": result.bridge_status,
        "candidates_created": result.candidates_created,
        "dataset_labels_created": result.dataset_labels_created,
        "governance_actions_performed": result.governance_actions_performed,
        "runtime_influence": result.runtime_influence,
        "phase4i_mutation_requested": result.phase4i_mutation_requested,
        "denied_reasons": list(result.denied_reasons),
        "warnings": list(result.warnings),
        "required_next_steps": list(result.required_next_steps),
        "notes": result.notes,
    }


def historical_review_learning_bridge_result_from_dict(
    data: dict[str, Any],
) -> HistoricalReviewLearningBridgeResult:
    """Deserialize historical bridge result metadata."""

    _require_mapping(data, "bridge_result")
    return HistoricalReviewLearningBridgeResult(
        bridge_result_id=str(data["bridge_result_id"]),
        source_review_count=int(data.get("source_review_count", 0)),
        candidate_intent_count=int(data.get("candidate_intent_count", 0)),
        learning_signal_intent_count=int(
            data.get("learning_signal_intent_count", 0)
        ),
        governance_route_count=int(data.get("governance_route_count", 0)),
        candidate_intents=[
            historical_learning_candidate_intent_from_dict(intent)
            for intent in data.get("candidate_intents", [])
        ],
        learning_signal_intents=[
            historical_learning_signal_intent_from_dict(intent)
            for intent in data.get("learning_signal_intents", [])
        ],
        governance_routes=[
            historical_governance_route_from_dict(route)
            for route in data.get("governance_routes", [])
        ],
        bridge_status=str(data.get("bridge_status", "valid_intents_only")),
        candidates_created=_bool_from_mapping(data, "candidates_created", False),
        dataset_labels_created=_bool_from_mapping(
            data,
            "dataset_labels_created",
            False,
        ),
        governance_actions_performed=_bool_from_mapping(
            data,
            "governance_actions_performed",
            False,
        ),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        denied_reasons=list(data.get("denied_reasons") or []),
        warnings=list(data.get("warnings") or []),
        required_next_steps=list(data.get("required_next_steps") or []),
        notes=_optional_text(data.get("notes")),
    )


def _source_review_id(
    review: HistoricalTrendReviewRecord | HistoricalAnomalyReviewRecord,
) -> str:
    if isinstance(review, HistoricalTrendReviewRecord):
        return review.trend_review_id
    if isinstance(review, HistoricalAnomalyReviewRecord):
        return review.anomaly_review_id
    raise Screen4HistoricalLearningBridgeError(
        "review must be a historical trend or anomaly review record."
    )


def _review_decision(
    review: HistoricalTrendReviewRecord | HistoricalAnomalyReviewRecord,
) -> str:
    _source_review_id(review)
    return str(getattr(review, "review_decision"))


def _review_component(
    review: HistoricalTrendReviewRecord | HistoricalAnomalyReviewRecord,
) -> str | None:
    if isinstance(review, HistoricalTrendReviewRecord):
        return _optional_text(review.trend_name or review.trend_id)
    if isinstance(review, HistoricalAnomalyReviewRecord):
        return _optional_text(review.anomaly_name or review.anomaly_id)
    return None


def _review_source_evidence(
    review: HistoricalTrendReviewRecord | HistoricalAnomalyReviewRecord,
) -> list[str]:
    evidence = [
        _source_review_id(review),
        _optional_text(getattr(review, "baseline_candidate_id", None)),
        _optional_text(getattr(review, "comparison_context_id", None)),
        _optional_text(getattr(review, "review_notes", None)),
    ]
    return [item for item in evidence if item]


def _label_value_for_decision(decision: str) -> str:
    if decision == "mark_anomaly_false_positive":
        return "true"
    if decision in ("approve_trend", "approve_anomaly"):
        return "confirmed"
    if decision == "request_learning_candidate":
        return "requested"
    return "review_required"


def _require_review_list(value: Any, field_name: str) -> None:
    if not isinstance(value, list):
        raise Screen4HistoricalLearningBridgeError(f"{field_name} must be a list.")
    for item in value:
        _source_review_id(item)


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _bool_from_mapping(data: dict[str, Any], field_name: str, default: bool) -> bool:
    value = data.get(field_name, default)
    if isinstance(value, bool):
        return value
    raise Screen4HistoricalLearningBridgeError(f"{field_name} must be a boolean.")


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise Screen4HistoricalLearningBridgeError(
            f"{field_name} must be a mapping."
        )


def _require_nonempty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise Screen4HistoricalLearningBridgeError(
            f"{field_name} must be a non-empty string."
        )


def _require_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise Screen4HistoricalLearningBridgeError(
            f"{field_name} must be a string or None."
        )


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        raise Screen4HistoricalLearningBridgeError(
            f"{field_name} must be one of: {', '.join(supported)}."
        )


def _require_confidence(value: Any, field_name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise Screen4HistoricalLearningBridgeError(f"{field_name} must be numeric.")
    if value < 0.0 or value > 0.95:
        raise Screen4HistoricalLearningBridgeError(
            f"{field_name} must be between 0.0 and 0.95."
        )


def _require_nonnegative_int(value: Any, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise Screen4HistoricalLearningBridgeError(
            f"{field_name} must be an integer."
        )
    if value < 0:
        raise Screen4HistoricalLearningBridgeError(f"{field_name} must be >= 0.")


def _require_boolean(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise Screen4HistoricalLearningBridgeError(
            f"{field_name} must be a boolean."
        )


def _require_true(value: bool, field_name: str) -> None:
    if not value:
        raise Screen4HistoricalLearningBridgeError(
            f"{field_name} must remain true in Phase 7BC."
        )


def _require_string_list(value: Any, field_name: str) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise Screen4HistoricalLearningBridgeError(
            f"{field_name} must be a list of strings."
        )


def _require_intent_list(value: Any, expected_type: type, field_name: str) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, expected_type) for item in value
    ):
        raise Screen4HistoricalLearningBridgeError(
            f"{field_name} must be a list of {expected_type.__name__}."
        )


def _reject_true(value: bool, field_name: str) -> None:
    if value:
        raise Screen4HistoricalLearningBridgeError(
            f"{field_name} must remain false in Phase 7BC."
        )


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text).strip("-")
    return text or "NONE"
