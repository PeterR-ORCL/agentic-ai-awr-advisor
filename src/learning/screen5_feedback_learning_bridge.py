"""Phase 7BI Screen 5 feedback-to-learning bridge intent metadata.

This module exposes local deterministic intent metadata only. It creates no
records, labels, candidates, action updates, outcome updates, runtime changes,
or dashboard behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


RECOMMENDATION_FEEDBACK_TYPES = (
    "accepted",
    "rejected",
    "deferred",
    "not_applicable",
    "effective",
    "ineffective",
    "partially_effective",
    "improved",
    "worsened",
    "no_change",
    "issue_recurred",
    "inconclusive",
    "false_positive",
    "false_negative",
    "needs_review",
)

LEARNING_SIGNAL_TYPES = (
    "recommendation_outcome",
    "action_effectiveness",
    "performance_result",
    "recurrence_signal",
    "false_positive_signal",
    "false_negative_signal",
    "validation_signal",
    "review_signal",
)

LEARNING_LABEL_NAMES = (
    "recommendation_accepted",
    "recommendation_rejected",
    "action_effective",
    "action_ineffective",
    "performance_improved",
    "performance_worsened",
    "no_change",
    "issue_recurred",
    "false_positive",
    "false_negative",
    "unknown_outcome",
)

RECOMMENDATION_CANDIDATE_INTENT_TYPES = (
    "recommendation_rule_candidate",
    "validation_candidate",
    "scoring_weight_review_candidate",
    "documentation_candidate",
)

FEEDBACK_BRIDGE_STATUSES = (
    "proposed",
    "ready_for_review",
    "insufficient_context",
    "invalid",
)

FEEDBACK_TO_LABEL_MAP = {
    "accepted": "recommendation_accepted",
    "rejected": "recommendation_rejected",
    "deferred": "unknown_outcome",
    "not_applicable": "recommendation_rejected",
    "effective": "action_effective",
    "ineffective": "action_ineffective",
    "partially_effective": "action_effective",
    "improved": "performance_improved",
    "worsened": "performance_worsened",
    "no_change": "no_change",
    "issue_recurred": "issue_recurred",
    "inconclusive": "unknown_outcome",
    "false_positive": "false_positive",
    "false_negative": "false_negative",
    "needs_review": "unknown_outcome",
}

FEEDBACK_TO_CANDIDATE_TYPE_MAP = {
    "accepted": "documentation_candidate",
    "rejected": "recommendation_rule_candidate",
    "deferred": "validation_candidate",
    "not_applicable": "recommendation_rule_candidate",
    "effective": "documentation_candidate",
    "ineffective": "recommendation_rule_candidate",
    "partially_effective": "recommendation_rule_candidate",
    "improved": "documentation_candidate",
    "worsened": "validation_candidate",
    "no_change": "validation_candidate",
    "issue_recurred": "scoring_weight_review_candidate",
    "inconclusive": "validation_candidate",
    "false_positive": "validation_candidate",
    "false_negative": "validation_candidate",
    "needs_review": "validation_candidate",
}

DECISION_TYPE_TO_FEEDBACK_TYPE = {
    "accept_recommendation": "accepted",
    "reject_recommendation": "rejected",
    "defer_recommendation": "deferred",
    "mark_not_applicable": "not_applicable",
    "request_recommendation_review": "needs_review",
    "request_learning_candidate": "needs_review",
}


class Screen5FeedbackLearningBridgeError(ValueError):
    """Raised when Phase 7BI feedback-to-learning intent metadata is invalid."""


@dataclass(frozen=True)
class RecommendationFeedbackIntent:
    """Future feedback record intent derived from Screen 5 workflow context."""

    feedback_intent_id: str
    recommendation_id: str
    feedback_type: str
    feedback_status: str
    feedback_summary: str
    decision_id: str | None = None
    action_preview_id: str | None = None
    outcome_preview_id: str | None = None
    actor_id: str | None = None
    actor_audit_context: dict[str, Any] | None = None
    source_payload: dict[str, Any] = field(default_factory=dict)
    feedback_created: bool = False
    write_performed: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.feedback_intent_id, "feedback_intent_id")
        _require_nonempty_string(self.recommendation_id, "recommendation_id")
        _require_optional_string(self.decision_id, "decision_id")
        _require_optional_string(self.action_preview_id, "action_preview_id")
        _require_optional_string(self.outcome_preview_id, "outcome_preview_id")
        _require_supported(
            self.feedback_type,
            RECOMMENDATION_FEEDBACK_TYPES,
            "feedback_type",
        )
        _require_supported(
            self.feedback_status,
            FEEDBACK_BRIDGE_STATUSES,
            "feedback_status",
        )
        _require_nonempty_string(self.feedback_summary, "feedback_summary")
        _require_optional_string(self.actor_id, "actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        _require_mapping(self.source_payload, "source_payload")
        _require_boolean(self.feedback_created, "feedback_created")
        _require_boolean(self.write_performed, "write_performed")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _require_boolean(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _reject_true(self.feedback_created, "feedback_created")
        _reject_true(self.write_performed, "write_performed")
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class LearningSignalIntent:
    """Future learning signal and label intent metadata."""

    signal_intent_id: str
    recommendation_id: str
    outcome_status: str
    outcome_effectiveness: str
    signal_type: str
    label_name: str
    label_value: str
    supervised_label_eligible: bool
    source_feedback_intent_id: str
    source_evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    dataset_label_created: bool = False
    requires_human_review: bool = True
    runtime_influence: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.signal_intent_id, "signal_intent_id")
        _require_nonempty_string(self.recommendation_id, "recommendation_id")
        _require_nonempty_string(self.outcome_status, "outcome_status")
        _require_nonempty_string(self.outcome_effectiveness, "outcome_effectiveness")
        _require_supported(self.signal_type, LEARNING_SIGNAL_TYPES, "signal_type")
        _require_supported(self.label_name, LEARNING_LABEL_NAMES, "label_name")
        _require_nonempty_string(self.label_value, "label_value")
        _require_boolean(
            self.supervised_label_eligible,
            "supervised_label_eligible",
        )
        _require_boolean(self.dataset_label_created, "dataset_label_created")
        _require_nonempty_string(
            self.source_feedback_intent_id,
            "source_feedback_intent_id",
        )
        _require_string_list(self.source_evidence, "source_evidence")
        _require_confidence(self.confidence)
        _require_boolean(self.requires_human_review, "requires_human_review")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _reject_true(self.dataset_label_created, "dataset_label_created")
        _reject_false(self.requires_human_review, "requires_human_review")
        _reject_true(self.runtime_influence, "runtime_influence")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class RecommendationCandidateIntent:
    """Future candidate request intent derived from feedback and signal context."""

    candidate_intent_id: str
    source_feedback_intent_id: str
    candidate_type: str
    rationale: str
    affected_domain: str | None = None
    affected_component: str | None = None
    source_evidence: list[str] = field(default_factory=list)
    candidate_created: bool = False
    requires_human_review: bool = True
    runtime_influence: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.candidate_intent_id, "candidate_intent_id")
        _require_nonempty_string(
            self.source_feedback_intent_id,
            "source_feedback_intent_id",
        )
        _require_supported(
            self.candidate_type,
            RECOMMENDATION_CANDIDATE_INTENT_TYPES,
            "candidate_type",
        )
        _require_optional_string(self.affected_domain, "affected_domain")
        _require_optional_string(self.affected_component, "affected_component")
        _require_nonempty_string(self.rationale, "rationale")
        _require_string_list(self.source_evidence, "source_evidence")
        _require_boolean(self.candidate_created, "candidate_created")
        _require_boolean(self.requires_human_review, "requires_human_review")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _reject_true(self.candidate_created, "candidate_created")
        _reject_false(self.requires_human_review, "requires_human_review")
        _reject_true(self.runtime_influence, "runtime_influence")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class RecommendationFeedbackBridgeResult:
    """Summary of feedback, signal, and candidate intent bridge outputs."""

    bridge_result_id: str
    recommendation_id: str
    bridge_status: str
    feedback_intents: list[RecommendationFeedbackIntent] = field(default_factory=list)
    learning_signal_intents: list[LearningSignalIntent] = field(default_factory=list)
    candidate_intents: list[RecommendationCandidateIntent] = field(default_factory=list)
    feedback_created: bool = False
    dataset_labels_created: bool = False
    candidates_created: bool = False
    write_performed: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.bridge_result_id, "bridge_result_id")
        _require_nonempty_string(self.recommendation_id, "recommendation_id")
        _require_intent_list(
            self.feedback_intents,
            RecommendationFeedbackIntent,
            "feedback_intents",
        )
        _require_intent_list(
            self.learning_signal_intents,
            LearningSignalIntent,
            "learning_signal_intents",
        )
        _require_intent_list(
            self.candidate_intents,
            RecommendationCandidateIntent,
            "candidate_intents",
        )
        _require_boolean(self.feedback_created, "feedback_created")
        _require_boolean(self.dataset_labels_created, "dataset_labels_created")
        _require_boolean(self.candidates_created, "candidates_created")
        _require_boolean(self.write_performed, "write_performed")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _require_boolean(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_supported(
            self.bridge_status,
            FEEDBACK_BRIDGE_STATUSES,
            "bridge_status",
        )
        _require_string_list(self.denied_reasons, "denied_reasons")
        _require_string_list(self.warnings, "warnings")
        _require_string_list(self.required_next_steps, "required_next_steps")
        _reject_true(self.feedback_created, "feedback_created")
        _reject_true(self.dataset_labels_created, "dataset_labels_created")
        _reject_true(self.candidates_created, "candidates_created")
        _reject_true(self.write_performed, "write_performed")
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        for intent in self.feedback_intents:
            validate_recommendation_feedback_intent(intent)
        for intent in self.learning_signal_intents:
            validate_learning_signal_intent(intent)
        for intent in self.candidate_intents:
            validate_recommendation_candidate_intent(intent)
        _require_optional_string(self.notes, "notes")


def create_feedback_intent_id(recommendation_id: str, feedback_type: str) -> str:
    """Create a deterministic feedback intent id."""

    _require_nonempty_string(recommendation_id, "recommendation_id")
    _require_supported(feedback_type, RECOMMENDATION_FEEDBACK_TYPES, "feedback_type")
    return (
        "SCREEN5-FEEDBACK-INTENT-"
        f"{_normalize_token(recommendation_id)}-"
        f"{_normalize_token(feedback_type)}"
    )


def create_learning_signal_intent_id(
    recommendation_id: str,
    signal_type: str,
    label_name: str,
) -> str:
    """Create a deterministic learning signal intent id."""

    _require_nonempty_string(recommendation_id, "recommendation_id")
    _require_supported(signal_type, LEARNING_SIGNAL_TYPES, "signal_type")
    _require_supported(label_name, LEARNING_LABEL_NAMES, "label_name")
    return (
        "SCREEN5-LEARNING-SIGNAL-"
        f"{_normalize_token(recommendation_id)}-"
        f"{_normalize_token(signal_type)}-"
        f"{_normalize_token(label_name)}"
    )


def create_recommendation_candidate_intent_id(
    recommendation_id: str,
    candidate_type: str,
) -> str:
    """Create a deterministic recommendation candidate intent id."""

    _require_nonempty_string(recommendation_id, "recommendation_id")
    _require_supported(
        candidate_type,
        RECOMMENDATION_CANDIDATE_INTENT_TYPES,
        "candidate_type",
    )
    return (
        "SCREEN5-CANDIDATE-INTENT-"
        f"{_normalize_token(recommendation_id)}-"
        f"{_normalize_token(candidate_type)}"
    )


def create_feedback_bridge_result_id(recommendation_id: str) -> str:
    """Create a deterministic feedback bridge result id."""

    _require_nonempty_string(recommendation_id, "recommendation_id")
    return f"SCREEN5-FEEDBACK-BRIDGE-{_normalize_token(recommendation_id)}"


def validate_recommendation_feedback_intent(
    intent: RecommendationFeedbackIntent,
) -> RecommendationFeedbackIntent:
    """Validate and return recommendation feedback intent metadata."""

    if not isinstance(intent, RecommendationFeedbackIntent):
        raise Screen5FeedbackLearningBridgeError(
            "intent must be a RecommendationFeedbackIntent instance."
        )
    intent.__post_init__()
    return intent


def validate_learning_signal_intent(
    intent: LearningSignalIntent,
) -> LearningSignalIntent:
    """Validate and return learning signal intent metadata."""

    if not isinstance(intent, LearningSignalIntent):
        raise Screen5FeedbackLearningBridgeError(
            "intent must be a LearningSignalIntent instance."
        )
    intent.__post_init__()
    return intent


def validate_recommendation_candidate_intent(
    intent: RecommendationCandidateIntent,
) -> RecommendationCandidateIntent:
    """Validate and return recommendation candidate intent metadata."""

    if not isinstance(intent, RecommendationCandidateIntent):
        raise Screen5FeedbackLearningBridgeError(
            "intent must be a RecommendationCandidateIntent instance."
        )
    intent.__post_init__()
    return intent


def validate_feedback_bridge_result(
    result: RecommendationFeedbackBridgeResult,
) -> RecommendationFeedbackBridgeResult:
    """Validate and return feedback bridge result metadata."""

    if not isinstance(result, RecommendationFeedbackBridgeResult):
        raise Screen5FeedbackLearningBridgeError(
            "result must be a RecommendationFeedbackBridgeResult instance."
        )
    result.__post_init__()
    return result


def build_feedback_intent_from_decision(
    decision: Any,
    action_preview: Any | None = None,
    outcome_preview: Any | None = None,
    actor_id: str | None = None,
    notes: str | None = None,
) -> RecommendationFeedbackIntent:
    """Build feedback intent metadata from a recommendation decision."""

    if decision is None:
        raise Screen5FeedbackLearningBridgeError("decision is required.")
    decision_type = _optional_text(_field_value(decision, "decision_type"))
    if not decision_type:
        decision_type = _decision_type_from_status(
            _optional_text(_field_value(decision, "decision_status"))
        )
    if decision_type not in DECISION_TYPE_TO_FEEDBACK_TYPE:
        raise Screen5FeedbackLearningBridgeError("unsupported decision type.")
    recommendation_id = _first_text(
        _field_value(decision, "recommendation_id"),
        _field_value(action_preview, "recommendation_id"),
        _field_value(outcome_preview, "recommendation_id"),
    )
    _require_nonempty_string(recommendation_id, "recommendation_id")
    feedback_type = DECISION_TYPE_TO_FEEDBACK_TYPE[decision_type]
    return _build_feedback_intent(
        recommendation_id=recommendation_id,
        feedback_type=feedback_type,
        decision_id=_optional_text(_field_value(decision, "decision_id")),
        action_preview_id=_optional_text(_field_value(action_preview, "action_preview_id")),
        outcome_preview_id=_optional_text(_field_value(outcome_preview, "outcome_preview_id")),
        actor_id=_first_text(
            actor_id,
            _field_value(decision, "actor_id"),
            _field_value(action_preview, "actor_id"),
            _field_value(outcome_preview, "actor_id"),
        ),
        actor_audit_context=_first_mapping(
            _field_value(decision, "actor_audit_context"),
            _field_value(action_preview, "actor_audit_context"),
            _field_value(outcome_preview, "actor_audit_context"),
        ),
        source_payload=_source_payload(decision, action_preview, outcome_preview),
        notes=notes,
    )


def build_learning_signal_intent(
    feedback_intent: RecommendationFeedbackIntent,
    outcome_preview: Any | None = None,
    notes: str | None = None,
) -> LearningSignalIntent:
    """Build learning signal intent metadata without creating labels."""

    feedback_intent = validate_recommendation_feedback_intent(feedback_intent)
    signal_type, label_name, confidence = _signal_mapping(
        feedback_intent.feedback_type,
        outcome_preview,
    )
    outcome_status = _optional_text(_field_value(outcome_preview, "outcome_status"))
    outcome_effectiveness = _optional_text(
        _field_value(outcome_preview, "outcome_effectiveness")
    )
    source_evidence = [
        f"feedback_intent:{feedback_intent.feedback_intent_id}",
        f"feedback_type:{feedback_intent.feedback_type}",
        f"label_name:{label_name}",
    ]
    if outcome_status:
        source_evidence.append(f"outcome_status:{outcome_status}")
    if outcome_effectiveness:
        source_evidence.append(f"outcome_effectiveness:{outcome_effectiveness}")
    return LearningSignalIntent(
        signal_intent_id=create_learning_signal_intent_id(
            feedback_intent.recommendation_id,
            signal_type,
            label_name,
        ),
        recommendation_id=feedback_intent.recommendation_id,
        outcome_status=outcome_status or "unknown",
        outcome_effectiveness=outcome_effectiveness or "unknown",
        signal_type=signal_type,
        label_name=label_name,
        label_value=_label_value(label_name),
        supervised_label_eligible=(
            label_name != "unknown_outcome" and confidence >= 0.50
        ),
        dataset_label_created=False,
        source_feedback_intent_id=feedback_intent.feedback_intent_id,
        source_evidence=source_evidence,
        confidence=confidence,
        requires_human_review=True,
        runtime_influence=False,
        notes=notes,
    )


def build_candidate_intent(
    feedback_intent: RecommendationFeedbackIntent,
    learning_signal: LearningSignalIntent | None = None,
    affected_domain: str | None = None,
    affected_component: str | None = None,
    notes: str | None = None,
) -> RecommendationCandidateIntent:
    """Build candidate intent metadata without creating candidates."""

    feedback_intent = validate_recommendation_feedback_intent(feedback_intent)
    if learning_signal is not None:
        learning_signal = validate_learning_signal_intent(learning_signal)
    candidate_type = _candidate_type_for_context(
        feedback_intent.feedback_type,
        learning_signal.label_name if learning_signal else None,
        affected_domain,
        affected_component,
    )
    source_evidence = [
        f"feedback_intent:{feedback_intent.feedback_intent_id}",
        f"feedback_type:{feedback_intent.feedback_type}",
    ]
    if learning_signal:
        source_evidence.extend(
            [
                f"signal_intent:{learning_signal.signal_intent_id}",
                f"label_name:{learning_signal.label_name}",
            ]
        )
    return RecommendationCandidateIntent(
        candidate_intent_id=create_recommendation_candidate_intent_id(
            feedback_intent.recommendation_id,
            candidate_type,
        ),
        source_feedback_intent_id=feedback_intent.feedback_intent_id,
        candidate_type=candidate_type,
        affected_domain=affected_domain,
        affected_component=affected_component,
        rationale=(
            f"Candidate intent only for {candidate_type} from "
            f"{feedback_intent.feedback_type} feedback."
        ),
        source_evidence=source_evidence,
        candidate_created=False,
        requires_human_review=True,
        runtime_influence=False,
        notes=notes,
    )


def bridge_recommendation_feedback(
    decision: Any | None = None,
    action_preview: Any | None = None,
    outcome_preview: Any | None = None,
    actor_id: str | None = None,
    notes: str | None = None,
) -> RecommendationFeedbackBridgeResult:
    """Bridge Screen 5 workflow metadata into intent records only."""

    recommendation_id = _first_text(
        _field_value(decision, "recommendation_id"),
        _field_value(action_preview, "recommendation_id"),
        _field_value(outcome_preview, "recommendation_id"),
    )
    if not recommendation_id:
        return RecommendationFeedbackBridgeResult(
            bridge_result_id=create_feedback_bridge_result_id(
                "missing-recommendation"
            ),
            recommendation_id="missing-recommendation",
            feedback_intents=[],
            learning_signal_intents=[],
            candidate_intents=[],
            feedback_created=False,
            dataset_labels_created=False,
            candidates_created=False,
            write_performed=False,
            runtime_influence=False,
            phase4i_mutation_requested=False,
            bridge_status="insufficient_context",
            denied_reasons=["recommendation_id is required"],
            warnings=["Bridge created intent metadata only."],
            required_next_steps=["provide recommendation context"],
            notes=notes,
        )

    feedback_intents: list[RecommendationFeedbackIntent] = []
    learning_signal_intents: list[LearningSignalIntent] = []
    candidate_intents: list[RecommendationCandidateIntent] = []
    denied_reasons: list[str] = []
    required_next_steps = [
        "review feedback intent before future feedback persistence",
        "review learning signal intent before future dataset labeling",
        "review candidate intent before future candidate creation",
    ]
    warnings = [
        "Intent is not persistence.",
        "No runtime mutation is performed.",
    ]

    if decision is not None:
        feedback_intent = build_feedback_intent_from_decision(
            decision,
            action_preview=action_preview,
            outcome_preview=outcome_preview,
            actor_id=actor_id,
            notes=notes,
        )
    elif outcome_preview is not None:
        feedback_intent = _build_feedback_intent(
            recommendation_id=recommendation_id,
            feedback_type=_feedback_type_from_outcome(outcome_preview),
            decision_id=None,
            action_preview_id=_optional_text(
                _field_value(action_preview, "action_preview_id")
            ),
            outcome_preview_id=_optional_text(
                _field_value(outcome_preview, "outcome_preview_id")
            ),
            actor_id=_first_text(
                actor_id,
                _field_value(action_preview, "actor_id"),
                _field_value(outcome_preview, "actor_id"),
            ),
            actor_audit_context=_first_mapping(
                _field_value(action_preview, "actor_audit_context"),
                _field_value(outcome_preview, "actor_audit_context"),
            ),
            source_payload=_source_payload(None, action_preview, outcome_preview),
            notes=notes,
        )
    else:
        feedback_intent = None
        denied_reasons.append("decision or outcome context is required")

    if feedback_intent:
        feedback_intents.append(feedback_intent)
        learning_signal = build_learning_signal_intent(
            feedback_intent,
            outcome_preview=outcome_preview,
            notes=notes,
        )
        learning_signal_intents.append(learning_signal)
        candidate_intents.append(
            build_candidate_intent(
                feedback_intent,
                learning_signal=learning_signal,
                affected_domain=_first_text(
                    _field_value(decision, "domain"),
                    _field_value(action_preview, "owner_role"),
                ),
                affected_component=_first_text(
                    _field_value(decision, "recommendation_title"),
                    _field_value(action_preview, "action_title"),
                ),
                notes=notes,
            )
        )

    bridge_status = "ready_for_review" if feedback_intents else "insufficient_context"
    return RecommendationFeedbackBridgeResult(
        bridge_result_id=create_feedback_bridge_result_id(recommendation_id),
        recommendation_id=recommendation_id,
        feedback_intents=feedback_intents,
        learning_signal_intents=learning_signal_intents,
        candidate_intents=candidate_intents,
        feedback_created=False,
        dataset_labels_created=False,
        candidates_created=False,
        write_performed=False,
        runtime_influence=False,
        phase4i_mutation_requested=False,
        bridge_status=bridge_status,
        denied_reasons=denied_reasons,
        warnings=warnings,
        required_next_steps=required_next_steps,
        notes=notes,
    )


def recommendation_feedback_intent_to_dict(
    intent: RecommendationFeedbackIntent,
) -> dict[str, Any]:
    """Serialize feedback intent metadata."""

    intent = validate_recommendation_feedback_intent(intent)
    return {
        "feedback_intent_id": intent.feedback_intent_id,
        "recommendation_id": intent.recommendation_id,
        "decision_id": intent.decision_id,
        "action_preview_id": intent.action_preview_id,
        "outcome_preview_id": intent.outcome_preview_id,
        "feedback_type": intent.feedback_type,
        "feedback_status": intent.feedback_status,
        "feedback_summary": intent.feedback_summary,
        "actor_id": intent.actor_id,
        "actor_audit_context": _copy_optional_mapping(intent.actor_audit_context),
        "source_payload": dict(intent.source_payload),
        "feedback_created": intent.feedback_created,
        "write_performed": intent.write_performed,
        "runtime_influence": intent.runtime_influence,
        "phase4i_mutation_requested": intent.phase4i_mutation_requested,
        "notes": intent.notes,
    }


def recommendation_feedback_intent_from_dict(
    data: dict[str, Any],
) -> RecommendationFeedbackIntent:
    """Deserialize feedback intent metadata."""

    _require_mapping(data, "data")
    return RecommendationFeedbackIntent(
        feedback_intent_id=str(data["feedback_intent_id"]),
        recommendation_id=str(data["recommendation_id"]),
        decision_id=_optional_text(data.get("decision_id")),
        action_preview_id=_optional_text(data.get("action_preview_id")),
        outcome_preview_id=_optional_text(data.get("outcome_preview_id")),
        feedback_type=str(data["feedback_type"]),
        feedback_status=str(data["feedback_status"]),
        feedback_summary=str(data["feedback_summary"]),
        actor_id=_optional_text(data.get("actor_id")),
        actor_audit_context=_copy_optional_mapping(data.get("actor_audit_context")),
        source_payload=dict(data.get("source_payload") or {}),
        feedback_created=_bool_from_mapping(data, "feedback_created", False),
        write_performed=_bool_from_mapping(data, "write_performed", False),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        notes=_optional_text(data.get("notes")),
    )


def learning_signal_intent_to_dict(intent: LearningSignalIntent) -> dict[str, Any]:
    """Serialize learning signal intent metadata."""

    intent = validate_learning_signal_intent(intent)
    return {
        "signal_intent_id": intent.signal_intent_id,
        "recommendation_id": intent.recommendation_id,
        "outcome_status": intent.outcome_status,
        "outcome_effectiveness": intent.outcome_effectiveness,
        "signal_type": intent.signal_type,
        "label_name": intent.label_name,
        "label_value": intent.label_value,
        "supervised_label_eligible": intent.supervised_label_eligible,
        "dataset_label_created": intent.dataset_label_created,
        "source_feedback_intent_id": intent.source_feedback_intent_id,
        "source_evidence": list(intent.source_evidence),
        "confidence": intent.confidence,
        "requires_human_review": intent.requires_human_review,
        "runtime_influence": intent.runtime_influence,
        "notes": intent.notes,
    }


def learning_signal_intent_from_dict(data: dict[str, Any]) -> LearningSignalIntent:
    """Deserialize learning signal intent metadata."""

    _require_mapping(data, "data")
    return LearningSignalIntent(
        signal_intent_id=str(data["signal_intent_id"]),
        recommendation_id=str(data["recommendation_id"]),
        outcome_status=str(data["outcome_status"]),
        outcome_effectiveness=str(data["outcome_effectiveness"]),
        signal_type=str(data["signal_type"]),
        label_name=str(data["label_name"]),
        label_value=str(data["label_value"]),
        supervised_label_eligible=_bool_from_mapping(
            data,
            "supervised_label_eligible",
            False,
        ),
        dataset_label_created=_bool_from_mapping(data, "dataset_label_created", False),
        source_feedback_intent_id=str(data["source_feedback_intent_id"]),
        source_evidence=list(data.get("source_evidence") or []),
        confidence=_float_from_mapping(data, "confidence", 0.0),
        requires_human_review=_bool_from_mapping(data, "requires_human_review", True),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        notes=_optional_text(data.get("notes")),
    )


def recommendation_candidate_intent_to_dict(
    intent: RecommendationCandidateIntent,
) -> dict[str, Any]:
    """Serialize recommendation candidate intent metadata."""

    intent = validate_recommendation_candidate_intent(intent)
    return {
        "candidate_intent_id": intent.candidate_intent_id,
        "source_feedback_intent_id": intent.source_feedback_intent_id,
        "candidate_type": intent.candidate_type,
        "affected_domain": intent.affected_domain,
        "affected_component": intent.affected_component,
        "rationale": intent.rationale,
        "source_evidence": list(intent.source_evidence),
        "candidate_created": intent.candidate_created,
        "requires_human_review": intent.requires_human_review,
        "runtime_influence": intent.runtime_influence,
        "notes": intent.notes,
    }


def recommendation_candidate_intent_from_dict(
    data: dict[str, Any],
) -> RecommendationCandidateIntent:
    """Deserialize recommendation candidate intent metadata."""

    _require_mapping(data, "data")
    return RecommendationCandidateIntent(
        candidate_intent_id=str(data["candidate_intent_id"]),
        source_feedback_intent_id=str(data["source_feedback_intent_id"]),
        candidate_type=str(data["candidate_type"]),
        affected_domain=_optional_text(data.get("affected_domain")),
        affected_component=_optional_text(data.get("affected_component")),
        rationale=str(data["rationale"]),
        source_evidence=list(data.get("source_evidence") or []),
        candidate_created=_bool_from_mapping(data, "candidate_created", False),
        requires_human_review=_bool_from_mapping(data, "requires_human_review", True),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        notes=_optional_text(data.get("notes")),
    )


def recommendation_feedback_bridge_result_to_dict(
    result: RecommendationFeedbackBridgeResult,
) -> dict[str, Any]:
    """Serialize feedback bridge result metadata."""

    result = validate_feedback_bridge_result(result)
    return {
        "bridge_result_id": result.bridge_result_id,
        "recommendation_id": result.recommendation_id,
        "feedback_intents": [
            recommendation_feedback_intent_to_dict(intent)
            for intent in result.feedback_intents
        ],
        "learning_signal_intents": [
            learning_signal_intent_to_dict(intent)
            for intent in result.learning_signal_intents
        ],
        "candidate_intents": [
            recommendation_candidate_intent_to_dict(intent)
            for intent in result.candidate_intents
        ],
        "feedback_created": result.feedback_created,
        "dataset_labels_created": result.dataset_labels_created,
        "candidates_created": result.candidates_created,
        "write_performed": result.write_performed,
        "runtime_influence": result.runtime_influence,
        "phase4i_mutation_requested": result.phase4i_mutation_requested,
        "bridge_status": result.bridge_status,
        "denied_reasons": list(result.denied_reasons),
        "warnings": list(result.warnings),
        "required_next_steps": list(result.required_next_steps),
        "notes": result.notes,
    }


def recommendation_feedback_bridge_result_from_dict(
    data: dict[str, Any],
) -> RecommendationFeedbackBridgeResult:
    """Deserialize feedback bridge result metadata."""

    _require_mapping(data, "data")
    return RecommendationFeedbackBridgeResult(
        bridge_result_id=str(data["bridge_result_id"]),
        recommendation_id=str(data["recommendation_id"]),
        feedback_intents=[
            recommendation_feedback_intent_from_dict(item)
            for item in data.get("feedback_intents", [])
        ],
        learning_signal_intents=[
            learning_signal_intent_from_dict(item)
            for item in data.get("learning_signal_intents", [])
        ],
        candidate_intents=[
            recommendation_candidate_intent_from_dict(item)
            for item in data.get("candidate_intents", [])
        ],
        feedback_created=_bool_from_mapping(data, "feedback_created", False),
        dataset_labels_created=_bool_from_mapping(
            data,
            "dataset_labels_created",
            False,
        ),
        candidates_created=_bool_from_mapping(data, "candidates_created", False),
        write_performed=_bool_from_mapping(data, "write_performed", False),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        bridge_status=str(data["bridge_status"]),
        denied_reasons=list(data.get("denied_reasons") or []),
        warnings=list(data.get("warnings") or []),
        required_next_steps=list(data.get("required_next_steps") or []),
        notes=_optional_text(data.get("notes")),
    )


def _build_feedback_intent(
    recommendation_id: str,
    feedback_type: str,
    decision_id: str | None,
    action_preview_id: str | None,
    outcome_preview_id: str | None,
    actor_id: str | None,
    actor_audit_context: dict[str, Any] | None,
    source_payload: dict[str, Any],
    notes: str | None,
) -> RecommendationFeedbackIntent:
    _require_nonempty_string(recommendation_id, "recommendation_id")
    _require_supported(feedback_type, RECOMMENDATION_FEEDBACK_TYPES, "feedback_type")
    return RecommendationFeedbackIntent(
        feedback_intent_id=create_feedback_intent_id(
            recommendation_id,
            feedback_type,
        ),
        recommendation_id=recommendation_id,
        decision_id=decision_id,
        action_preview_id=action_preview_id,
        outcome_preview_id=outcome_preview_id,
        feedback_type=feedback_type,
        feedback_status="ready_for_review",
        feedback_summary=(
            f"Feedback intent only for {feedback_type}; no feedback record is "
            "created in Phase 7BI."
        ),
        actor_id=actor_id,
        actor_audit_context=actor_audit_context,
        source_payload=source_payload,
        feedback_created=False,
        write_performed=False,
        runtime_influence=False,
        phase4i_mutation_requested=False,
        notes=notes,
    )


def _source_payload(
    decision: Any | None,
    action_preview: Any | None,
    outcome_preview: Any | None,
) -> dict[str, Any]:
    return {
        "decision_id": _optional_text(_field_value(decision, "decision_id")),
        "decision_type": _optional_text(_field_value(decision, "decision_type")),
        "decision_status": _optional_text(_field_value(decision, "decision_status")),
        "action_preview_id": _optional_text(
            _field_value(action_preview, "action_preview_id")
        ),
        "action_status": _optional_text(_field_value(action_preview, "action_status")),
        "outcome_preview_id": _optional_text(
            _field_value(outcome_preview, "outcome_preview_id")
        ),
        "outcome_status": _optional_text(
            _field_value(outcome_preview, "outcome_status")
        ),
        "outcome_effectiveness": _optional_text(
            _field_value(outcome_preview, "outcome_effectiveness")
        ),
    }


def _decision_type_from_status(status: str | None) -> str | None:
    return {
        "accepted": "accept_recommendation",
        "rejected": "reject_recommendation",
        "deferred": "defer_recommendation",
        "not_applicable": "mark_not_applicable",
        "under_review": "request_recommendation_review",
        "routed_to_governance": "request_learning_candidate",
    }.get(status or "")


def _feedback_type_from_outcome(outcome_preview: Any) -> str:
    status = _optional_text(_field_value(outcome_preview, "outcome_status"))
    effectiveness = _optional_text(
        _field_value(outcome_preview, "outcome_effectiveness")
    )
    if status in {
        "improved",
        "worsened",
        "no_change",
        "issue_recurred",
        "inconclusive",
    }:
        return status
    if effectiveness in {
        "effective",
        "ineffective",
        "partially_effective",
    }:
        return effectiveness
    return "inconclusive"


def _signal_mapping(
    feedback_type: str,
    outcome_preview: Any | None,
) -> tuple[str, str, float]:
    status = _optional_text(_field_value(outcome_preview, "outcome_status"))
    effectiveness = _optional_text(
        _field_value(outcome_preview, "outcome_effectiveness")
    )
    if status == "improved":
        return "performance_result", "performance_improved", 0.90
    if status == "worsened":
        return "performance_result", "performance_worsened", 0.90
    if status == "no_change":
        return "performance_result", "no_change", 0.82
    if status == "issue_recurred":
        return "recurrence_signal", "issue_recurred", 0.88
    if status == "inconclusive":
        return "validation_signal", "unknown_outcome", 0.35
    if effectiveness == "effective":
        return "action_effectiveness", "action_effective", 0.90
    if effectiveness == "ineffective":
        return "action_effectiveness", "action_ineffective", 0.90
    if effectiveness == "partially_effective":
        return "action_effectiveness", "action_effective", 0.60
    if feedback_type == "false_positive":
        return "false_positive_signal", "false_positive", 0.86
    if feedback_type == "false_negative":
        return "false_negative_signal", "false_negative", 0.86
    if feedback_type == "needs_review":
        return "review_signal", "unknown_outcome", 0.45
    label_name = FEEDBACK_TO_LABEL_MAP[feedback_type]
    return "recommendation_outcome", label_name, _confidence_for_label(label_name)


def _candidate_type_for_context(
    feedback_type: str,
    label_name: str | None,
    affected_domain: str | None,
    affected_component: str | None,
) -> str:
    label_name = label_name or FEEDBACK_TO_LABEL_MAP[feedback_type]
    if label_name in {"false_positive", "false_negative", "unknown_outcome"}:
        return "validation_candidate"
    if label_name == "issue_recurred":
        context = f"{affected_domain or ''} {affected_component or ''}".lower()
        if "recommendation" in context or "action" in context:
            return "recommendation_rule_candidate"
        return "scoring_weight_review_candidate"
    if label_name == "action_ineffective":
        return "recommendation_rule_candidate"
    if feedback_type in {"rejected", "not_applicable", "ineffective"}:
        return "recommendation_rule_candidate"
    if label_name in {
        "recommendation_accepted",
        "action_effective",
        "performance_improved",
    }:
        return "documentation_candidate"
    return FEEDBACK_TO_CANDIDATE_TYPE_MAP[feedback_type]


def _confidence_for_label(label_name: str) -> float:
    if label_name == "unknown_outcome":
        return 0.40
    if label_name in {"recommendation_accepted", "recommendation_rejected"}:
        return 0.80
    if label_name in {"false_positive", "false_negative"}:
        return 0.86
    return 0.75


def _label_value(label_name: str) -> str:
    return "unknown" if label_name == "unknown_outcome" else "true"


def _field_value(source: Any, field_name: str) -> Any:
    if source is None:
        return None
    if isinstance(source, dict):
        return source.get(field_name)
    return getattr(source, field_name, None)


def _first_text(*values: Any) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text:
            return text
    return None


def _first_mapping(*values: Any) -> dict[str, Any] | None:
    for value in values:
        if isinstance(value, dict):
            return dict(value)
    return None


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _bool_from_mapping(data: dict[str, Any], field_name: str, default: bool) -> bool:
    value = data.get(field_name, default)
    if isinstance(value, bool):
        return value
    raise Screen5FeedbackLearningBridgeError(f"{field_name} must be a boolean.")


def _float_from_mapping(data: dict[str, Any], field_name: str, default: float) -> float:
    value = data.get(field_name, default)
    if isinstance(value, bool):
        raise Screen5FeedbackLearningBridgeError(f"{field_name} must be a float.")
    if isinstance(value, (float, int)):
        return float(value)
    raise Screen5FeedbackLearningBridgeError(f"{field_name} must be a float.")


def _copy_optional_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Screen5FeedbackLearningBridgeError(
            "mapping value must be a dictionary."
        )
    return dict(value)


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise Screen5FeedbackLearningBridgeError(
            f"{field_name} must be a mapping."
        )


def _require_optional_mapping(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, dict):
        raise Screen5FeedbackLearningBridgeError(
            f"{field_name} must be a mapping or None."
        )


def _require_nonempty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise Screen5FeedbackLearningBridgeError(
            f"{field_name} must be a non-empty string."
        )


def _require_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise Screen5FeedbackLearningBridgeError(
            f"{field_name} must be a string or None."
        )


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        raise Screen5FeedbackLearningBridgeError(
            f"{field_name} must be one of: {', '.join(supported)}."
        )


def _require_boolean(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise Screen5FeedbackLearningBridgeError(f"{field_name} must be a boolean.")


def _require_confidence(value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise Screen5FeedbackLearningBridgeError("confidence must be a float.")
    if not 0.0 <= float(value) <= 0.95:
        raise Screen5FeedbackLearningBridgeError(
            "confidence must be between 0.0 and 0.95."
        )


def _require_string_list(value: Any, field_name: str) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise Screen5FeedbackLearningBridgeError(
            f"{field_name} must be a list of strings."
        )


def _require_intent_list(value: Any, expected_type: type, field_name: str) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, expected_type) for item in value
    ):
        raise Screen5FeedbackLearningBridgeError(
            f"{field_name} must be a list of {expected_type.__name__}."
        )


def _reject_true(value: bool, field_name: str) -> None:
    if value:
        raise Screen5FeedbackLearningBridgeError(
            f"{field_name} must remain false in Phase 7BI."
        )


def _reject_false(value: bool, field_name: str) -> None:
    if not value:
        raise Screen5FeedbackLearningBridgeError(
            f"{field_name} must remain true in Phase 7BI."
        )


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text).strip("-")
    return text or "NONE"
