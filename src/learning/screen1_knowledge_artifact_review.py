"""Phase 7AX Screen 1 knowledge artifact review metadata.

The records in this module describe future knowledge artifact review intent for
Screen 1. They validate and route metadata only. They do not persist reviews,
approve artifacts, reject artifacts, request revision at runtime, create
candidates, create materialization artifacts, invoke governed write paths,
write state, modify dashboard behavior, modify CLI behavior, or mutate runtime
output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


KNOWLEDGE_ARTIFACT_TYPES = (
    "parser_mapping_guidance",
    "scoring_review_guidance",
    "recommendation_rule_guidance",
    "semantic_summary",
    "documentation",
    "validation",
    "materialization_reference",
    "governance_workflow",
    "unknown",
)

KNOWLEDGE_ARTIFACT_REVIEW_DECISIONS = (
    "approve_for_review",
    "reject_artifact",
    "request_revision",
    "link_to_candidate",
    "link_to_materialization",
    "link_to_parser_review",
    "link_to_scoring_review",
    "link_to_recommendation_review",
    "mark_superseded",
    "add_review_note",
)

KNOWLEDGE_ARTIFACT_REVIEW_STATUSES = (
    "proposed",
    "under_review",
    "approved_for_review",
    "rejected",
    "needs_revision",
    "linked_to_candidate",
    "linked_to_materialization",
    "superseded",
    "closed",
)

KNOWLEDGE_ARTIFACT_FOLLOWUP_TYPES = (
    "none",
    "candidate_review_required",
    "materialization_review_required",
    "parser_review_required",
    "scoring_review_required",
    "recommendation_review_required",
    "artifact_revision_required",
    "human_review_required",
)

KNOWLEDGE_ARTIFACT_REVIEW_VALIDATION_STATUSES = (
    "VALID_METADATA_ONLY",
    "INVALID",
    "NEEDS_ACTOR",
    "NEEDS_ARTIFACT",
    "REVIEW_NOT_PERSISTED_IN_THIS_PHASE",
)

ARTIFACT_CANDIDATE_TYPE_MAPPING = {
    "parser_mapping_guidance": "parser_mapping_candidate",
    "scoring_review_guidance": "scoring_weight_review_candidate",
    "recommendation_rule_guidance": "recommendation_rule_candidate",
    "semantic_summary": "semantic_summary_candidate",
    "documentation": "documentation_candidate",
    "validation": "validation_candidate",
    "governance_workflow": "governance_workflow_candidate",
    "materialization_reference": "validation_candidate",
    "unknown": "documentation_candidate",
}

ARTIFACT_MATERIALIZATION_TYPE_MAPPING = {
    "parser_mapping_guidance": "parser_mapping_artifact",
    "scoring_review_guidance": "scoring_review_artifact",
    "recommendation_rule_guidance": "recommendation_rule_artifact",
    "semantic_summary": "semantic_summary_artifact",
    "documentation": "documentation_artifact",
    "validation": "validation_artifact",
    "governance_workflow": "governance_workflow_artifact",
    "materialization_reference": "validation_artifact",
    "unknown": "documentation_artifact",
}


class Screen1KnowledgeArtifactReviewError(ValueError):
    """Raised when Phase 7AX artifact review metadata is invalid."""


@dataclass(frozen=True)
class KnowledgeArtifactReviewRecord:
    """Local review metadata for a knowledge artifact."""

    artifact_review_id: str
    artifact_id: str
    artifact_type: str = "unknown"
    artifact_title: str | None = None
    source_request_id: str | None = None
    review_decision: str = "add_review_note"
    review_status: str = "proposed"
    reviewer_actor_id: str | None = None
    actor_audit_context: dict[str, Any] | None = None
    review_notes: list[str] = field(default_factory=list)
    linked_candidate_intent_id: str | None = None
    linked_materialization_intent_id: str | None = None
    linked_parser_review_id: str | None = None
    linked_scoring_review_id: str | None = None
    linked_recommendation_review_id: str | None = None
    write_performed: bool = False
    artifact_approved: bool = False
    artifact_rejected: bool = False
    artifact_revision_requested: bool = False
    materialization_created: bool = False
    candidate_created: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.artifact_review_id, "artifact_review_id")
        _require_nonempty_string(self.artifact_id, "artifact_id")
        _require_supported(self.artifact_type, KNOWLEDGE_ARTIFACT_TYPES, "artifact_type")
        _require_optional_string(self.artifact_title, "artifact_title")
        _require_optional_string(self.source_request_id, "source_request_id")
        _require_supported(
            self.review_decision,
            KNOWLEDGE_ARTIFACT_REVIEW_DECISIONS,
            "review_decision",
        )
        _require_supported(
            self.review_status,
            KNOWLEDGE_ARTIFACT_REVIEW_STATUSES,
            "review_status",
        )
        _require_optional_string(self.reviewer_actor_id, "reviewer_actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        _require_list_of_strings(self.review_notes, "review_notes")
        _require_optional_string(
            self.linked_candidate_intent_id,
            "linked_candidate_intent_id",
        )
        _require_optional_string(
            self.linked_materialization_intent_id,
            "linked_materialization_intent_id",
        )
        _require_optional_string(self.linked_parser_review_id, "linked_parser_review_id")
        _require_optional_string(self.linked_scoring_review_id, "linked_scoring_review_id")
        _require_optional_string(
            self.linked_recommendation_review_id,
            "linked_recommendation_review_id",
        )
        _validate_artifact_safety_flags(
            write_performed=self.write_performed,
            artifact_approved=self.artifact_approved,
            artifact_rejected=self.artifact_rejected,
            artifact_revision_requested=self.artifact_revision_requested,
            materialization_created=self.materialization_created,
            candidate_created=self.candidate_created,
            runtime_influence=self.runtime_influence,
            phase4i_mutation_requested=self.phase4i_mutation_requested,
        )
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class KnowledgeArtifactReviewRequest:
    """Future request metadata for artifact review workflow."""

    artifact_review_request_id: str
    artifact_id: str | None
    requested_decision: str
    actor_id: str | None = None
    actor_audit_context: dict[str, Any] | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    validation_status: str = "VALID_METADATA_ONLY"
    can_route_to_write_path: bool = False
    write_performed: bool = False
    artifact_approved: bool = False
    artifact_rejected: bool = False
    artifact_revision_requested: bool = False
    materialization_created: bool = False
    candidate_created: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(
            self.artifact_review_request_id,
            "artifact_review_request_id",
        )
        _require_optional_string(self.artifact_id, "artifact_id")
        _require_supported(
            self.requested_decision,
            KNOWLEDGE_ARTIFACT_REVIEW_DECISIONS,
            "requested_decision",
        )
        _require_optional_string(self.actor_id, "actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        _require_mapping(self.payload, "payload")
        _require_supported(
            self.validation_status,
            KNOWLEDGE_ARTIFACT_REVIEW_VALIDATION_STATUSES,
            "validation_status",
        )
        _require_bool(self.can_route_to_write_path, "can_route_to_write_path")
        _validate_artifact_safety_flags(
            write_performed=self.write_performed,
            artifact_approved=self.artifact_approved,
            artifact_rejected=self.artifact_rejected,
            artifact_revision_requested=self.artifact_revision_requested,
            materialization_created=self.materialization_created,
            candidate_created=self.candidate_created,
            runtime_influence=self.runtime_influence,
            phase4i_mutation_requested=self.phase4i_mutation_requested,
        )
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class KnowledgeArtifactDecision:
    """Local artifact decision metadata."""

    artifact_decision_id: str
    artifact_review_id: str
    decision_type: str
    decision_status: str
    actor_id: str | None = None
    actor_audit_context: dict[str, Any] | None = None
    decision_summary: str | None = None
    requires_followup: bool = False
    followup_type: str = "none"
    write_performed: bool = False
    materialization_created: bool = False
    candidate_created: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.artifact_decision_id, "artifact_decision_id")
        _require_nonempty_string(self.artifact_review_id, "artifact_review_id")
        _require_supported(
            self.decision_type,
            KNOWLEDGE_ARTIFACT_REVIEW_DECISIONS,
            "decision_type",
        )
        _require_supported(
            self.decision_status,
            KNOWLEDGE_ARTIFACT_REVIEW_STATUSES,
            "decision_status",
        )
        _require_optional_string(self.actor_id, "actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        _require_optional_string(self.decision_summary, "decision_summary")
        _require_bool(self.requires_followup, "requires_followup")
        _require_supported(
            self.followup_type,
            KNOWLEDGE_ARTIFACT_FOLLOWUP_TYPES,
            "followup_type",
        )
        _validate_artifact_safety_flags(
            write_performed=self.write_performed,
            materialization_created=self.materialization_created,
            candidate_created=self.candidate_created,
            runtime_influence=self.runtime_influence,
            phase4i_mutation_requested=self.phase4i_mutation_requested,
        )
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class ArtifactCandidateLinkIntent:
    """Local intent to link an artifact to a future candidate."""

    link_intent_id: str
    artifact_id: str
    candidate_type: str
    affected_component: str | None = None
    affected_domain: str | None = None
    rationale: str | None = None
    source_evidence: list[str] = field(default_factory=list)
    candidate_created: bool = False
    requires_human_review: bool = True
    runtime_influence: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.link_intent_id, "link_intent_id")
        _require_nonempty_string(self.artifact_id, "artifact_id")
        _require_nonempty_string(self.candidate_type, "candidate_type")
        _require_optional_string(self.affected_component, "affected_component")
        _require_optional_string(self.affected_domain, "affected_domain")
        _require_optional_string(self.rationale, "rationale")
        _require_list_of_strings(self.source_evidence, "source_evidence")
        _require_bool(self.candidate_created, "candidate_created")
        _require_bool(self.requires_human_review, "requires_human_review")
        _require_bool(self.runtime_influence, "runtime_influence")
        _require_optional_string(self.notes, "notes")
        if self.candidate_created:
            raise Screen1KnowledgeArtifactReviewError(
                "candidate_created must remain false in Phase 7AX."
            )
        if not self.requires_human_review:
            raise Screen1KnowledgeArtifactReviewError(
                "requires_human_review must remain true in Phase 7AX."
            )
        if self.runtime_influence:
            raise Screen1KnowledgeArtifactReviewError(
                "runtime_influence must remain false in Phase 7AX."
            )


@dataclass(frozen=True)
class ArtifactMaterializationLinkIntent:
    """Local intent to link an artifact to future materialization."""

    materialization_intent_id: str
    artifact_id: str
    materialization_type: str
    affected_component: str | None = None
    affected_domain: str | None = None
    rationale: str | None = None
    materialization_created: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(
            self.materialization_intent_id,
            "materialization_intent_id",
        )
        _require_nonempty_string(self.artifact_id, "artifact_id")
        _require_nonempty_string(self.materialization_type, "materialization_type")
        _require_optional_string(self.affected_component, "affected_component")
        _require_optional_string(self.affected_domain, "affected_domain")
        _require_optional_string(self.rationale, "rationale")
        _validate_artifact_safety_flags(
            materialization_created=self.materialization_created,
            runtime_influence=self.runtime_influence,
            phase4i_mutation_requested=self.phase4i_mutation_requested,
        )
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class KnowledgeArtifactReviewValidation:
    """Validation metadata for artifact review requests."""

    validation_id: str
    artifact_review_request_id: str
    valid: bool
    validation_status: str
    requested_decision: str
    actor_present: bool
    artifact_present: bool
    can_route_to_write_path: bool
    write_performed: bool = False
    artifact_approved: bool = False
    artifact_rejected: bool = False
    artifact_revision_requested: bool = False
    materialization_created: bool = False
    candidate_created: bool = False
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.validation_id, "validation_id")
        _require_nonempty_string(
            self.artifact_review_request_id,
            "artifact_review_request_id",
        )
        _require_bool(self.valid, "valid")
        _require_supported(
            self.validation_status,
            KNOWLEDGE_ARTIFACT_REVIEW_VALIDATION_STATUSES,
            "validation_status",
        )
        _require_supported(
            self.requested_decision,
            KNOWLEDGE_ARTIFACT_REVIEW_DECISIONS,
            "requested_decision",
        )
        _require_bool(self.actor_present, "actor_present")
        _require_bool(self.artifact_present, "artifact_present")
        _require_bool(self.can_route_to_write_path, "can_route_to_write_path")
        _require_list_of_strings(self.denied_reasons, "denied_reasons")
        _require_list_of_strings(self.warnings, "warnings")
        _require_list_of_strings(self.required_next_steps, "required_next_steps")
        _validate_artifact_safety_flags(
            write_performed=self.write_performed,
            artifact_approved=self.artifact_approved,
            artifact_rejected=self.artifact_rejected,
            artifact_revision_requested=self.artifact_revision_requested,
            materialization_created=self.materialization_created,
            candidate_created=self.candidate_created,
            runtime_influence=self.runtime_influence,
            phase4i_mutation_requested=self.phase4i_mutation_requested,
        )
        _require_optional_string(self.notes, "notes")


def make_artifact_review_id(artifact_id: str, review_decision: str) -> str:
    """Create a deterministic artifact review id."""

    _require_nonempty_string(artifact_id, "artifact_id")
    _require_supported(
        review_decision,
        KNOWLEDGE_ARTIFACT_REVIEW_DECISIONS,
        "review_decision",
    )
    return (
        "SCREEN1-KNOWLEDGE-ARTIFACT-REVIEW-"
        f"{_normalize_token(artifact_id)}-{_normalize_token(review_decision)}"
    )


def make_artifact_review_request_id(
    artifact_id: str,
    requested_decision: str,
) -> str:
    """Create a deterministic artifact review request id."""

    _require_nonempty_string(artifact_id, "artifact_id")
    _require_supported(
        requested_decision,
        KNOWLEDGE_ARTIFACT_REVIEW_DECISIONS,
        "requested_decision",
    )
    return (
        "SCREEN1-KNOWLEDGE-ARTIFACT-REQUEST-"
        f"{_normalize_token(artifact_id)}-{_normalize_token(requested_decision)}"
    )


def make_artifact_decision_id(artifact_review_id: str, decision_type: str) -> str:
    """Create a deterministic artifact decision id."""

    _require_nonempty_string(artifact_review_id, "artifact_review_id")
    _require_supported(
        decision_type,
        KNOWLEDGE_ARTIFACT_REVIEW_DECISIONS,
        "decision_type",
    )
    return (
        "SCREEN1-KNOWLEDGE-ARTIFACT-DECISION-"
        f"{_normalize_token(artifact_review_id)}-{_normalize_token(decision_type)}"
    )


def make_artifact_candidate_link_intent_id(
    artifact_id: str,
    candidate_type: str,
) -> str:
    """Create a deterministic artifact candidate link intent id."""

    _require_nonempty_string(artifact_id, "artifact_id")
    _require_nonempty_string(candidate_type, "candidate_type")
    return (
        "SCREEN1-ARTIFACT-CANDIDATE-LINK-INTENT-"
        f"{_normalize_token(artifact_id)}-{_normalize_token(candidate_type)}"
    )


def make_artifact_materialization_link_intent_id(
    artifact_id: str,
    materialization_type: str,
) -> str:
    """Create a deterministic artifact materialization link intent id."""

    _require_nonempty_string(artifact_id, "artifact_id")
    _require_nonempty_string(materialization_type, "materialization_type")
    return (
        "SCREEN1-ARTIFACT-MATERIALIZATION-LINK-INTENT-"
        f"{_normalize_token(artifact_id)}-{_normalize_token(materialization_type)}"
    )


def make_artifact_review_validation_id(artifact_review_request_id: str) -> str:
    """Create a deterministic artifact review validation id."""

    _require_nonempty_string(
        artifact_review_request_id,
        "artifact_review_request_id",
    )
    return (
        "SCREEN1-KNOWLEDGE-ARTIFACT-VALIDATION-"
        f"{_normalize_token(artifact_review_request_id)}"
    )


def candidate_type_for_artifact_type(artifact_type: str) -> str:
    """Return the candidate type for an artifact type."""

    _require_supported(artifact_type, KNOWLEDGE_ARTIFACT_TYPES, "artifact_type")
    return ARTIFACT_CANDIDATE_TYPE_MAPPING[artifact_type]


def materialization_type_for_artifact_type(artifact_type: str) -> str:
    """Return the materialization type for an artifact type."""

    _require_supported(artifact_type, KNOWLEDGE_ARTIFACT_TYPES, "artifact_type")
    return ARTIFACT_MATERIALIZATION_TYPE_MAPPING[artifact_type]


def validate_artifact_review_record(
    record: KnowledgeArtifactReviewRecord,
) -> KnowledgeArtifactReviewRecord:
    """Validate artifact review metadata without persisting it."""

    if not isinstance(record, KnowledgeArtifactReviewRecord):
        raise Screen1KnowledgeArtifactReviewError(
            "record must be a KnowledgeArtifactReviewRecord instance."
        )
    record.__post_init__()
    return record


def validate_artifact_review_request(
    request: KnowledgeArtifactReviewRequest,
) -> KnowledgeArtifactReviewRequest:
    """Validate artifact review request metadata."""

    if not isinstance(request, KnowledgeArtifactReviewRequest):
        raise Screen1KnowledgeArtifactReviewError(
            "request must be a KnowledgeArtifactReviewRequest instance."
        )
    request.__post_init__()
    if not _actor_present(request):
        raise Screen1KnowledgeArtifactReviewError(
            "artifact review requests require actor metadata."
        )
    return request


def validate_artifact_decision(
    decision: KnowledgeArtifactDecision,
) -> KnowledgeArtifactDecision:
    """Validate artifact decision metadata."""

    if not isinstance(decision, KnowledgeArtifactDecision):
        raise Screen1KnowledgeArtifactReviewError(
            "decision must be a KnowledgeArtifactDecision instance."
        )
    decision.__post_init__()
    if not _has_display_value(decision.actor_id) and decision.actor_audit_context is None:
        raise Screen1KnowledgeArtifactReviewError(
            "artifact decisions require actor metadata."
        )
    return decision


def validate_candidate_link_intent(
    intent: ArtifactCandidateLinkIntent,
) -> ArtifactCandidateLinkIntent:
    """Validate artifact candidate link intent metadata."""

    if not isinstance(intent, ArtifactCandidateLinkIntent):
        raise Screen1KnowledgeArtifactReviewError(
            "intent must be an ArtifactCandidateLinkIntent instance."
        )
    intent.__post_init__()
    return intent


def validate_materialization_link_intent(
    intent: ArtifactMaterializationLinkIntent,
) -> ArtifactMaterializationLinkIntent:
    """Validate artifact materialization link intent metadata."""

    if not isinstance(intent, ArtifactMaterializationLinkIntent):
        raise Screen1KnowledgeArtifactReviewError(
            "intent must be an ArtifactMaterializationLinkIntent instance."
        )
    intent.__post_init__()
    return intent


def validate_artifact_review_validation(
    validation: KnowledgeArtifactReviewValidation,
) -> KnowledgeArtifactReviewValidation:
    """Validate artifact review validation metadata."""

    if not isinstance(validation, KnowledgeArtifactReviewValidation):
        raise Screen1KnowledgeArtifactReviewError(
            "validation must be a KnowledgeArtifactReviewValidation instance."
        )
    validation.__post_init__()
    return validation


def evaluate_artifact_review_request(
    request: KnowledgeArtifactReviewRequest,
) -> KnowledgeArtifactReviewValidation:
    """Evaluate artifact review request metadata without persisting it."""

    if not isinstance(request, KnowledgeArtifactReviewRequest):
        raise Screen1KnowledgeArtifactReviewError(
            "request must be a KnowledgeArtifactReviewRequest instance."
        )
    request.__post_init__()
    actor_present = _actor_present(request)
    artifact_present = bool(request.artifact_id)
    denied_reasons = ["artifact review is not persisted in Phase 7AX"]
    warnings: list[str] = []
    required_next_steps = [
        "route through a future governed write path before persistence"
    ]
    valid = False
    status = "INVALID"
    can_route = False

    if not actor_present:
        status = "NEEDS_ACTOR"
        denied_reasons.append("actor metadata is required")
        required_next_steps.append("provide actor identity through Phase 7AE")
    elif not artifact_present:
        status = "NEEDS_ARTIFACT"
        denied_reasons.append("artifact reference is required")
        required_next_steps.append("provide artifact_id")
    else:
        status = "REVIEW_NOT_PERSISTED_IN_THIS_PHASE"
        valid = True
        can_route = bool(request.can_route_to_write_path)
        if can_route:
            warnings.append("can_route_to_write_path is future eligibility only")

    return KnowledgeArtifactReviewValidation(
        validation_id=make_artifact_review_validation_id(
            request.artifact_review_request_id
        ),
        artifact_review_request_id=request.artifact_review_request_id,
        valid=valid,
        validation_status=status,
        requested_decision=request.requested_decision,
        actor_present=actor_present,
        artifact_present=artifact_present,
        can_route_to_write_path=can_route,
        write_performed=False,
        artifact_approved=False,
        artifact_rejected=False,
        artifact_revision_requested=False,
        materialization_created=False,
        candidate_created=False,
        denied_reasons=denied_reasons,
        warnings=warnings,
        required_next_steps=required_next_steps,
        runtime_influence=False,
        phase4i_mutation_requested=False,
        notes=request.notes,
    )


def build_candidate_link_intent_for_request(
    request: KnowledgeArtifactReviewRequest,
) -> ArtifactCandidateLinkIntent | None:
    """Build candidate link intent metadata for link_to_candidate requests."""

    validate_artifact_review_request(request)
    if request.requested_decision != "link_to_candidate":
        return None
    artifact_type = _payload_artifact_type(request.payload)
    candidate_type = candidate_type_for_artifact_type(artifact_type)
    return ArtifactCandidateLinkIntent(
        link_intent_id=make_artifact_candidate_link_intent_id(
            request.artifact_id or "ARTIFACT",
            candidate_type,
        ),
        artifact_id=request.artifact_id or "ARTIFACT",
        candidate_type=candidate_type,
        affected_component=_optional_payload_string(request.payload, "affected_component"),
        affected_domain=_optional_payload_string(request.payload, "affected_domain"),
        rationale=_optional_payload_string(request.payload, "rationale"),
        source_evidence=_payload_string_list(request.payload, "source_evidence"),
        candidate_created=False,
        requires_human_review=True,
        runtime_influence=False,
        notes=request.notes,
    )


def build_materialization_link_intent_for_request(
    request: KnowledgeArtifactReviewRequest,
) -> ArtifactMaterializationLinkIntent | None:
    """Build materialization link intent metadata for link_to_materialization."""

    validate_artifact_review_request(request)
    if request.requested_decision != "link_to_materialization":
        return None
    artifact_type = _payload_artifact_type(request.payload)
    materialization_type = materialization_type_for_artifact_type(artifact_type)
    return ArtifactMaterializationLinkIntent(
        materialization_intent_id=make_artifact_materialization_link_intent_id(
            request.artifact_id or "ARTIFACT",
            materialization_type,
        ),
        artifact_id=request.artifact_id or "ARTIFACT",
        materialization_type=materialization_type,
        affected_component=_optional_payload_string(request.payload, "affected_component"),
        affected_domain=_optional_payload_string(request.payload, "affected_domain"),
        rationale=_optional_payload_string(request.payload, "rationale"),
        materialization_created=False,
        runtime_influence=False,
        phase4i_mutation_requested=False,
        notes=request.notes,
    )


def build_artifact_decision_for_request(
    request: KnowledgeArtifactReviewRequest,
) -> KnowledgeArtifactDecision:
    """Build local artifact decision metadata without executing it."""

    validate_artifact_review_request(request)
    artifact_review_id = make_artifact_review_id(
        request.artifact_id or "ARTIFACT",
        request.requested_decision,
    )
    return KnowledgeArtifactDecision(
        artifact_decision_id=make_artifact_decision_id(
            artifact_review_id,
            request.requested_decision,
        ),
        artifact_review_id=artifact_review_id,
        decision_type=request.requested_decision,
        decision_status=_status_for_decision(request.requested_decision),
        actor_id=request.actor_id,
        actor_audit_context=request.actor_audit_context,
        decision_summary=_optional_payload_string(request.payload, "decision_summary"),
        requires_followup=_followup_type_for_decision(request.requested_decision) != "none",
        followup_type=_followup_type_for_decision(request.requested_decision),
        write_performed=False,
        materialization_created=False,
        candidate_created=False,
        runtime_influence=False,
        phase4i_mutation_requested=False,
        notes=request.notes,
    )


def route_artifact_review_request(request: KnowledgeArtifactReviewRequest) -> dict[str, Any]:
    """Route artifact review metadata without creating runtime records."""

    validation = evaluate_artifact_review_request(request)
    if not validation.valid:
        return {
            "validation": artifact_review_validation_to_dict(validation),
            "review_record": None,
            "decision": None,
            "candidate_link_intent": None,
            "materialization_link_intent": None,
            "recommended_next_step": validation.required_next_steps[0],
        }

    candidate_intent = build_candidate_link_intent_for_request(request)
    materialization_intent = build_materialization_link_intent_for_request(request)
    decision = build_artifact_decision_for_request(request)
    artifact_type = _payload_artifact_type(request.payload)
    review_record = KnowledgeArtifactReviewRecord(
        artifact_review_id=decision.artifact_review_id,
        artifact_id=request.artifact_id or "ARTIFACT",
        artifact_type=artifact_type,
        artifact_title=_optional_payload_string(request.payload, "artifact_title"),
        source_request_id=_optional_payload_string(request.payload, "source_request_id"),
        review_decision=request.requested_decision,
        review_status=decision.decision_status,
        reviewer_actor_id=request.actor_id,
        actor_audit_context=request.actor_audit_context,
        review_notes=_payload_string_list(request.payload, "review_notes"),
        linked_candidate_intent_id=(
            candidate_intent.link_intent_id if candidate_intent else None
        ),
        linked_materialization_intent_id=(
            materialization_intent.materialization_intent_id
            if materialization_intent
            else None
        ),
        linked_parser_review_id=_optional_payload_string(
            request.payload,
            "linked_parser_review_id",
        ),
        linked_scoring_review_id=_optional_payload_string(
            request.payload,
            "linked_scoring_review_id",
        ),
        linked_recommendation_review_id=_optional_payload_string(
            request.payload,
            "linked_recommendation_review_id",
        ),
        write_performed=False,
        artifact_approved=False,
        artifact_rejected=False,
        artifact_revision_requested=False,
        materialization_created=False,
        candidate_created=False,
        runtime_influence=False,
        phase4i_mutation_requested=False,
        notes=request.notes,
    )
    return {
        "validation": artifact_review_validation_to_dict(validation),
        "review_record": artifact_review_record_to_dict(review_record),
        "decision": artifact_decision_to_dict(decision),
        "candidate_link_intent": (
            candidate_link_intent_to_dict(candidate_intent)
            if candidate_intent
            else None
        ),
        "materialization_link_intent": (
            materialization_link_intent_to_dict(materialization_intent)
            if materialization_intent
            else None
        ),
        "recommended_next_step": _next_step_for_decision(request.requested_decision),
    }


def artifact_review_record_to_dict(
    record: KnowledgeArtifactReviewRecord,
) -> dict[str, Any]:
    """Serialize artifact review metadata."""

    record = validate_artifact_review_record(record)
    return {
        "artifact_review_id": record.artifact_review_id,
        "artifact_id": record.artifact_id,
        "artifact_type": record.artifact_type,
        "artifact_title": record.artifact_title,
        "source_request_id": record.source_request_id,
        "review_decision": record.review_decision,
        "review_status": record.review_status,
        "reviewer_actor_id": record.reviewer_actor_id,
        "actor_audit_context": _copy_optional_mapping(record.actor_audit_context),
        "review_notes": list(record.review_notes),
        "linked_candidate_intent_id": record.linked_candidate_intent_id,
        "linked_materialization_intent_id": record.linked_materialization_intent_id,
        "linked_parser_review_id": record.linked_parser_review_id,
        "linked_scoring_review_id": record.linked_scoring_review_id,
        "linked_recommendation_review_id": record.linked_recommendation_review_id,
        "write_performed": record.write_performed,
        "artifact_approved": record.artifact_approved,
        "artifact_rejected": record.artifact_rejected,
        "artifact_revision_requested": record.artifact_revision_requested,
        "materialization_created": record.materialization_created,
        "candidate_created": record.candidate_created,
        "runtime_influence": record.runtime_influence,
        "phase4i_mutation_requested": record.phase4i_mutation_requested,
        "created_at": record.created_at,
        "notes": record.notes,
    }


def artifact_review_record_from_dict(data: dict[str, Any]) -> KnowledgeArtifactReviewRecord:
    """Deserialize artifact review metadata."""

    _require_mapping(data, "knowledge_artifact_review_record")
    return KnowledgeArtifactReviewRecord(
        artifact_review_id=data.get("artifact_review_id"),
        artifact_id=data.get("artifact_id"),
        artifact_type=data.get("artifact_type", "unknown"),
        artifact_title=data.get("artifact_title"),
        source_request_id=data.get("source_request_id"),
        review_decision=data.get("review_decision", "add_review_note"),
        review_status=data.get("review_status", "proposed"),
        reviewer_actor_id=data.get("reviewer_actor_id"),
        actor_audit_context=data.get("actor_audit_context"),
        review_notes=data.get("review_notes", []),
        linked_candidate_intent_id=data.get("linked_candidate_intent_id"),
        linked_materialization_intent_id=data.get("linked_materialization_intent_id"),
        linked_parser_review_id=data.get("linked_parser_review_id"),
        linked_scoring_review_id=data.get("linked_scoring_review_id"),
        linked_recommendation_review_id=data.get("linked_recommendation_review_id"),
        write_performed=data.get("write_performed", False),
        artifact_approved=data.get("artifact_approved", False),
        artifact_rejected=data.get("artifact_rejected", False),
        artifact_revision_requested=data.get("artifact_revision_requested", False),
        materialization_created=data.get("materialization_created", False),
        candidate_created=data.get("candidate_created", False),
        runtime_influence=data.get("runtime_influence", False),
        phase4i_mutation_requested=data.get("phase4i_mutation_requested", False),
        created_at=data.get("created_at"),
        notes=data.get("notes"),
    )


def artifact_review_request_to_dict(
    request: KnowledgeArtifactReviewRequest,
) -> dict[str, Any]:
    """Serialize artifact review request metadata."""

    request.__post_init__()
    return {
        "artifact_review_request_id": request.artifact_review_request_id,
        "artifact_id": request.artifact_id,
        "requested_decision": request.requested_decision,
        "actor_id": request.actor_id,
        "actor_audit_context": _copy_optional_mapping(request.actor_audit_context),
        "payload": dict(request.payload),
        "validation_status": request.validation_status,
        "can_route_to_write_path": request.can_route_to_write_path,
        "write_performed": request.write_performed,
        "artifact_approved": request.artifact_approved,
        "artifact_rejected": request.artifact_rejected,
        "artifact_revision_requested": request.artifact_revision_requested,
        "materialization_created": request.materialization_created,
        "candidate_created": request.candidate_created,
        "runtime_influence": request.runtime_influence,
        "phase4i_mutation_requested": request.phase4i_mutation_requested,
        "notes": request.notes,
    }


def artifact_review_request_from_dict(
    data: dict[str, Any],
) -> KnowledgeArtifactReviewRequest:
    """Deserialize artifact review request metadata."""

    _require_mapping(data, "knowledge_artifact_review_request")
    return KnowledgeArtifactReviewRequest(
        artifact_review_request_id=data.get("artifact_review_request_id"),
        artifact_id=data.get("artifact_id"),
        requested_decision=data.get("requested_decision"),
        actor_id=data.get("actor_id"),
        actor_audit_context=data.get("actor_audit_context"),
        payload=data.get("payload", {}),
        validation_status=data.get("validation_status", "VALID_METADATA_ONLY"),
        can_route_to_write_path=data.get("can_route_to_write_path", False),
        write_performed=data.get("write_performed", False),
        artifact_approved=data.get("artifact_approved", False),
        artifact_rejected=data.get("artifact_rejected", False),
        artifact_revision_requested=data.get("artifact_revision_requested", False),
        materialization_created=data.get("materialization_created", False),
        candidate_created=data.get("candidate_created", False),
        runtime_influence=data.get("runtime_influence", False),
        phase4i_mutation_requested=data.get("phase4i_mutation_requested", False),
        notes=data.get("notes"),
    )


def artifact_decision_to_dict(decision: KnowledgeArtifactDecision) -> dict[str, Any]:
    """Serialize artifact decision metadata."""

    decision.__post_init__()
    return {
        "artifact_decision_id": decision.artifact_decision_id,
        "artifact_review_id": decision.artifact_review_id,
        "decision_type": decision.decision_type,
        "decision_status": decision.decision_status,
        "actor_id": decision.actor_id,
        "actor_audit_context": _copy_optional_mapping(decision.actor_audit_context),
        "decision_summary": decision.decision_summary,
        "requires_followup": decision.requires_followup,
        "followup_type": decision.followup_type,
        "write_performed": decision.write_performed,
        "materialization_created": decision.materialization_created,
        "candidate_created": decision.candidate_created,
        "runtime_influence": decision.runtime_influence,
        "phase4i_mutation_requested": decision.phase4i_mutation_requested,
        "created_at": decision.created_at,
        "notes": decision.notes,
    }


def artifact_decision_from_dict(data: dict[str, Any]) -> KnowledgeArtifactDecision:
    """Deserialize artifact decision metadata."""

    _require_mapping(data, "knowledge_artifact_decision")
    return KnowledgeArtifactDecision(
        artifact_decision_id=data.get("artifact_decision_id"),
        artifact_review_id=data.get("artifact_review_id"),
        decision_type=data.get("decision_type"),
        decision_status=data.get("decision_status"),
        actor_id=data.get("actor_id"),
        actor_audit_context=data.get("actor_audit_context"),
        decision_summary=data.get("decision_summary"),
        requires_followup=data.get("requires_followup", False),
        followup_type=data.get("followup_type", "none"),
        write_performed=data.get("write_performed", False),
        materialization_created=data.get("materialization_created", False),
        candidate_created=data.get("candidate_created", False),
        runtime_influence=data.get("runtime_influence", False),
        phase4i_mutation_requested=data.get("phase4i_mutation_requested", False),
        created_at=data.get("created_at"),
        notes=data.get("notes"),
    )


def candidate_link_intent_to_dict(intent: ArtifactCandidateLinkIntent) -> dict[str, Any]:
    """Serialize artifact candidate link intent metadata."""

    intent = validate_candidate_link_intent(intent)
    return {
        "link_intent_id": intent.link_intent_id,
        "artifact_id": intent.artifact_id,
        "candidate_type": intent.candidate_type,
        "affected_component": intent.affected_component,
        "affected_domain": intent.affected_domain,
        "rationale": intent.rationale,
        "source_evidence": list(intent.source_evidence),
        "candidate_created": intent.candidate_created,
        "requires_human_review": intent.requires_human_review,
        "runtime_influence": intent.runtime_influence,
        "notes": intent.notes,
    }


def candidate_link_intent_from_dict(data: dict[str, Any]) -> ArtifactCandidateLinkIntent:
    """Deserialize artifact candidate link intent metadata."""

    _require_mapping(data, "artifact_candidate_link_intent")
    return ArtifactCandidateLinkIntent(
        link_intent_id=data.get("link_intent_id"),
        artifact_id=data.get("artifact_id"),
        candidate_type=data.get("candidate_type"),
        affected_component=data.get("affected_component"),
        affected_domain=data.get("affected_domain"),
        rationale=data.get("rationale"),
        source_evidence=data.get("source_evidence", []),
        candidate_created=data.get("candidate_created", False),
        requires_human_review=data.get("requires_human_review", True),
        runtime_influence=data.get("runtime_influence", False),
        notes=data.get("notes"),
    )


def materialization_link_intent_to_dict(
    intent: ArtifactMaterializationLinkIntent,
) -> dict[str, Any]:
    """Serialize artifact materialization link intent metadata."""

    intent = validate_materialization_link_intent(intent)
    return {
        "materialization_intent_id": intent.materialization_intent_id,
        "artifact_id": intent.artifact_id,
        "materialization_type": intent.materialization_type,
        "affected_component": intent.affected_component,
        "affected_domain": intent.affected_domain,
        "rationale": intent.rationale,
        "materialization_created": intent.materialization_created,
        "runtime_influence": intent.runtime_influence,
        "phase4i_mutation_requested": intent.phase4i_mutation_requested,
        "notes": intent.notes,
    }


def materialization_link_intent_from_dict(
    data: dict[str, Any],
) -> ArtifactMaterializationLinkIntent:
    """Deserialize artifact materialization link intent metadata."""

    _require_mapping(data, "artifact_materialization_link_intent")
    return ArtifactMaterializationLinkIntent(
        materialization_intent_id=data.get("materialization_intent_id"),
        artifact_id=data.get("artifact_id"),
        materialization_type=data.get("materialization_type"),
        affected_component=data.get("affected_component"),
        affected_domain=data.get("affected_domain"),
        rationale=data.get("rationale"),
        materialization_created=data.get("materialization_created", False),
        runtime_influence=data.get("runtime_influence", False),
        phase4i_mutation_requested=data.get("phase4i_mutation_requested", False),
        notes=data.get("notes"),
    )


def artifact_review_validation_to_dict(
    validation: KnowledgeArtifactReviewValidation,
) -> dict[str, Any]:
    """Serialize artifact review validation metadata."""

    validation = validate_artifact_review_validation(validation)
    return {
        "validation_id": validation.validation_id,
        "artifact_review_request_id": validation.artifact_review_request_id,
        "valid": validation.valid,
        "validation_status": validation.validation_status,
        "requested_decision": validation.requested_decision,
        "actor_present": validation.actor_present,
        "artifact_present": validation.artifact_present,
        "can_route_to_write_path": validation.can_route_to_write_path,
        "write_performed": validation.write_performed,
        "artifact_approved": validation.artifact_approved,
        "artifact_rejected": validation.artifact_rejected,
        "artifact_revision_requested": validation.artifact_revision_requested,
        "materialization_created": validation.materialization_created,
        "candidate_created": validation.candidate_created,
        "denied_reasons": list(validation.denied_reasons),
        "warnings": list(validation.warnings),
        "required_next_steps": list(validation.required_next_steps),
        "runtime_influence": validation.runtime_influence,
        "phase4i_mutation_requested": validation.phase4i_mutation_requested,
        "notes": validation.notes,
    }


def artifact_review_validation_from_dict(
    data: dict[str, Any],
) -> KnowledgeArtifactReviewValidation:
    """Deserialize artifact review validation metadata."""

    _require_mapping(data, "knowledge_artifact_review_validation")
    return KnowledgeArtifactReviewValidation(
        validation_id=data.get("validation_id"),
        artifact_review_request_id=data.get("artifact_review_request_id"),
        valid=data.get("valid"),
        validation_status=data.get("validation_status"),
        requested_decision=data.get("requested_decision"),
        actor_present=data.get("actor_present"),
        artifact_present=data.get("artifact_present"),
        can_route_to_write_path=data.get("can_route_to_write_path"),
        write_performed=data.get("write_performed", False),
        artifact_approved=data.get("artifact_approved", False),
        artifact_rejected=data.get("artifact_rejected", False),
        artifact_revision_requested=data.get("artifact_revision_requested", False),
        materialization_created=data.get("materialization_created", False),
        candidate_created=data.get("candidate_created", False),
        denied_reasons=data.get("denied_reasons", []),
        warnings=data.get("warnings", []),
        required_next_steps=data.get("required_next_steps", []),
        runtime_influence=data.get("runtime_influence", False),
        phase4i_mutation_requested=data.get("phase4i_mutation_requested", False),
        notes=data.get("notes"),
    )


def _status_for_decision(decision: str) -> str:
    _require_supported(decision, KNOWLEDGE_ARTIFACT_REVIEW_DECISIONS, "decision")
    if decision == "approve_for_review":
        return "approved_for_review"
    if decision == "reject_artifact":
        return "rejected"
    if decision == "request_revision":
        return "needs_revision"
    if decision == "link_to_candidate":
        return "linked_to_candidate"
    if decision == "link_to_materialization":
        return "linked_to_materialization"
    if decision == "mark_superseded":
        return "superseded"
    return "under_review"


def _followup_type_for_decision(decision: str) -> str:
    _require_supported(decision, KNOWLEDGE_ARTIFACT_REVIEW_DECISIONS, "decision")
    if decision == "link_to_candidate":
        return "candidate_review_required"
    if decision == "link_to_materialization":
        return "materialization_review_required"
    if decision == "link_to_parser_review":
        return "parser_review_required"
    if decision == "link_to_scoring_review":
        return "scoring_review_required"
    if decision == "link_to_recommendation_review":
        return "recommendation_review_required"
    if decision == "request_revision":
        return "artifact_revision_required"
    if decision == "add_review_note":
        return "human_review_required"
    return "none"


def _next_step_for_decision(decision: str) -> str:
    followup = _followup_type_for_decision(decision)
    if followup == "none":
        return "close through future governed artifact review"
    return f"route to {followup} through future governance"


def _actor_present(request: KnowledgeArtifactReviewRequest) -> bool:
    return bool(request.actor_id or request.actor_audit_context)


def _payload_artifact_type(payload: dict[str, Any]) -> str:
    artifact_type = payload.get("artifact_type", "unknown")
    _require_supported(artifact_type, KNOWLEDGE_ARTIFACT_TYPES, "artifact_type")
    return artifact_type


def _optional_payload_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    _require_optional_string(value, key)
    return value


def _payload_string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key, [])
    if isinstance(value, str):
        return [value]
    _require_list_of_strings(value, key)
    return list(value)


def _copy_optional_mapping(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    _require_mapping(value, "mapping")
    return dict(value)


def _validate_artifact_safety_flags(
    *,
    write_performed: bool = False,
    artifact_approved: bool = False,
    artifact_rejected: bool = False,
    artifact_revision_requested: bool = False,
    materialization_created: bool = False,
    candidate_created: bool = False,
    runtime_influence: bool = False,
    phase4i_mutation_requested: bool = False,
) -> None:
    for field_name, value in (
        ("write_performed", write_performed),
        ("artifact_approved", artifact_approved),
        ("artifact_rejected", artifact_rejected),
        ("artifact_revision_requested", artifact_revision_requested),
        ("materialization_created", materialization_created),
        ("candidate_created", candidate_created),
        ("runtime_influence", runtime_influence),
        ("phase4i_mutation_requested", phase4i_mutation_requested),
    ):
        _require_bool(value, field_name)
        if value:
            raise Screen1KnowledgeArtifactReviewError(
                f"{field_name} must remain false in Phase 7AX."
            )


def _normalize_token(value: str) -> str:
    _require_nonempty_string(value, "value")
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().upper())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "NONE"


def _has_display_value(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _require_nonempty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Screen1KnowledgeArtifactReviewError(f"{field_name} is required.")
    return value


def _require_optional_string(value: Any, field_name: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise Screen1KnowledgeArtifactReviewError(
            f"{field_name} must be a string or None."
        )
    return value


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> str:
    if not isinstance(value, str) or value not in supported:
        raise Screen1KnowledgeArtifactReviewError(
            f"Unsupported {field_name}: {value!r}."
        )
    return value


def _require_bool(value: Any, field_name: str) -> bool:
    if type(value) is not bool:
        raise Screen1KnowledgeArtifactReviewError(f"{field_name} must be boolean.")
    return value


def _require_list_of_strings(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise Screen1KnowledgeArtifactReviewError(
            f"{field_name} must be a list of strings."
        )
    return value


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise Screen1KnowledgeArtifactReviewError(
            f"{field_name} must be a dictionary."
        )
    return value


def _require_optional_mapping(
    value: Any,
    field_name: str,
) -> dict[str, Any] | None:
    if value is not None and not isinstance(value, dict):
        raise Screen1KnowledgeArtifactReviewError(
            f"{field_name} must be a dictionary or None."
        )
    return value
