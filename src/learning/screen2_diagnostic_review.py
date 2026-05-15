"""Phase 7AQ Screen 2 diagnostic review object models.

The records in this module describe future Screen 2 reviewer assessment and
evidence availability review metadata only. They do not persist records,
implement UI, invoke write paths, execute analysis, modify dashboards, modify
CLI behavior, or mutate deterministic diagnostic truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from src.learning.screen2_review_boundary import (
    SCREEN2_REVIEW_DECISIONS,
    SCREEN2_REVIEW_STATUSES,
    SCREEN2_REVIEW_TARGET_TYPES,
)


EVIDENCE_REVIEW_TYPES = (
    "metric",
    "wait_event",
    "sql_signal",
    "trend",
    "anomaly",
    "topology",
    "platform",
    "source_option",
    "score",
    "domain_score",
    "recommendation_context",
    "parser_derived_evidence",
    "diagnostic_section",
    "missing_metric",
    "unavailable_evidence",
    "unknown",
)

EVIDENCE_STATUSES = (
    "available",
    "unavailable",
    "missing",
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

REVIEW_REQUEST_VALIDATION_STATUSES = (
    "VALID_METADATA_ONLY",
    "INVALID",
    "NEEDS_ACTOR",
    "NEEDS_TARGET",
    "UNSUPPORTED_TARGET",
    "UNSUPPORTED_DECISION",
    "WRITE_BLOCKED_IN_7AQ",
)


class Screen2DiagnosticReviewError(ValueError):
    """Raised when Phase 7AQ diagnostic review metadata is invalid."""


@dataclass(frozen=True)
class DiagnosticReviewRecord:
    """Governed review metadata for a Screen 2 diagnostic target."""

    review_id: str
    review_target_type: str
    review_target_id: str
    review_decision: str
    review_status: str
    reviewer_actor_id: str | None
    screen_id: str = "screen_2"
    run_id: str | None = None
    awr_id: str | None = None
    domain: str | None = None
    current_value: Any = None
    actor_audit_context: dict[str, Any] | None = None
    review_notes: str | None = None
    linked_candidate_id: str | None = None
    linked_parser_signal_id: str | None = None
    linked_scoring_review_id: str | None = None
    linked_recommendation_review_id: str | None = None
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.review_id, "review_id")
        _require_exact(self.screen_id, "screen_2", "screen_id")
        _require_optional_string(self.run_id, "run_id")
        _require_optional_string(self.awr_id, "awr_id")
        _require_at_least_one_identifier(
            ("run_id", self.run_id),
            ("awr_id", self.awr_id),
        )
        _require_supported(
            self.review_target_type,
            SCREEN2_REVIEW_TARGET_TYPES,
            "review_target_type",
        )
        _require_nonempty_string(self.review_target_id, "review_target_id")
        _require_optional_string(self.domain, "domain")
        _require_supported(
            self.review_decision,
            SCREEN2_REVIEW_DECISIONS,
            "review_decision",
        )
        _require_supported(
            self.review_status,
            SCREEN2_REVIEW_STATUSES,
            "review_status",
        )
        _require_optional_string(self.reviewer_actor_id, "reviewer_actor_id")
        if self.review_decision != "add_reviewer_note":
            _require_nonempty_string(self.reviewer_actor_id, "reviewer_actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        _require_optional_string(self.review_notes, "review_notes")
        _require_optional_string(self.linked_candidate_id, "linked_candidate_id")
        _require_optional_string(
            self.linked_parser_signal_id,
            "linked_parser_signal_id",
        )
        _require_optional_string(
            self.linked_scoring_review_id,
            "linked_scoring_review_id",
        )
        _require_optional_string(
            self.linked_recommendation_review_id,
            "linked_recommendation_review_id",
        )
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
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class EvidenceReviewRecord:
    """Review metadata for a specific Screen 2 diagnostic evidence item."""

    evidence_review_id: str
    parent_review_id: str
    evidence_type: str
    evidence_id: str
    evidence_name: str
    evidence_status: str
    reliability_status: str
    review_decision: str
    domain: str | None = None
    current_value: Any = None
    missing_reason: str = "unknown"
    confidence_impact: str = "unknown"
    reviewer_actor_id: str | None = None
    review_notes: str | None = None
    parser_review_recommended: bool = False
    scoring_review_recommended: bool = False
    recommendation_review_recommended: bool = False
    source_review_recommended: bool = False
    candidate_created: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.evidence_review_id, "evidence_review_id")
        _require_nonempty_string(self.parent_review_id, "parent_review_id")
        _require_supported(self.evidence_type, EVIDENCE_REVIEW_TYPES, "evidence_type")
        _require_nonempty_string(self.evidence_id, "evidence_id")
        _require_nonempty_string(self.evidence_name, "evidence_name")
        _require_optional_string(self.domain, "domain")
        _require_supported(
            self.evidence_status,
            EVIDENCE_STATUSES,
            "evidence_status",
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
        _require_supported(
            self.review_decision,
            SCREEN2_REVIEW_DECISIONS,
            "review_decision",
        )
        _require_optional_string(self.reviewer_actor_id, "reviewer_actor_id")
        _require_optional_string(self.review_notes, "review_notes")
        _require_boolean(
            self.parser_review_recommended,
            "parser_review_recommended",
        )
        _require_boolean(
            self.scoring_review_recommended,
            "scoring_review_recommended",
        )
        _require_boolean(
            self.recommendation_review_recommended,
            "recommendation_review_recommended",
        )
        _require_boolean(self.source_review_recommended, "source_review_recommended")
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
class DiagnosticApprovalDecision:
    """Decision metadata for a diagnostic review record."""

    decision_id: str
    review_id: str
    decision_type: str
    decision_status: str
    actor_id: str
    actor_audit_context: dict[str, Any] | None = None
    decision_summary: str | None = None
    requires_followup: bool = False
    followup_type: str | None = None
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.decision_id, "decision_id")
        _require_nonempty_string(self.review_id, "review_id")
        _require_supported(self.decision_type, SCREEN2_REVIEW_DECISIONS, "decision_type")
        _require_supported(
            self.decision_status,
            SCREEN2_REVIEW_STATUSES,
            "decision_status",
        )
        _require_nonempty_string(self.actor_id, "actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        _require_optional_string(self.decision_summary, "decision_summary")
        _require_boolean(self.requires_followup, "requires_followup")
        _require_optional_string(self.followup_type, "followup_type")
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
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class DiagnosticReviewRequest:
    """Request metadata for future Screen 2 review workflow handling."""

    request_id: str
    review_target_type: str
    review_target_id: str
    requested_decision: str
    actor_id: str
    actor_audit_context: dict[str, Any] | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    validation_status: str = "VALID_METADATA_ONLY"
    can_route_to_governance: bool = False
    write_performed: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.request_id, "request_id")
        _require_supported(
            self.review_target_type,
            SCREEN2_REVIEW_TARGET_TYPES,
            "review_target_type",
        )
        _require_nonempty_string(self.review_target_id, "review_target_id")
        _require_supported(
            self.requested_decision,
            SCREEN2_REVIEW_DECISIONS,
            "requested_decision",
        )
        _require_nonempty_string(self.actor_id, "actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        _require_mapping(self.payload, "payload")
        _require_supported(
            self.validation_status,
            REVIEW_REQUEST_VALIDATION_STATUSES,
            "validation_status",
        )
        _require_boolean(self.can_route_to_governance, "can_route_to_governance")
        _require_boolean(self.write_performed, "write_performed")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _require_boolean(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _reject_true(self.write_performed, "write_performed")
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.notes, "notes")


def create_diagnostic_review_id(
    run_id: str | None,
    awr_id: str | None,
    review_target_type: str,
    review_target_id: str,
) -> str:
    """Create a deterministic Screen 2 diagnostic review id."""

    _require_optional_string(run_id, "run_id")
    _require_optional_string(awr_id, "awr_id")
    _require_at_least_one_identifier(("run_id", run_id), ("awr_id", awr_id))
    _require_supported(
        review_target_type,
        SCREEN2_REVIEW_TARGET_TYPES,
        "review_target_type",
    )
    _require_nonempty_string(review_target_id, "review_target_id")
    run_or_awr = run_id or awr_id
    return (
        "SCREEN2-DIAG-REVIEW-"
        f"{_normalize_token(run_or_awr)}-"
        f"{_normalize_token(review_target_type)}-"
        f"{_normalize_token(review_target_id)}"
    )


def create_evidence_review_id(
    parent_review_id: str,
    evidence_type: str,
    evidence_id: str,
) -> str:
    """Create a deterministic Screen 2 evidence review id."""

    _require_nonempty_string(parent_review_id, "parent_review_id")
    _require_supported(evidence_type, EVIDENCE_REVIEW_TYPES, "evidence_type")
    _require_nonempty_string(evidence_id, "evidence_id")
    return (
        "SCREEN2-EVIDENCE-REVIEW-"
        f"{_normalize_token(parent_review_id)}-"
        f"{_normalize_token(evidence_type)}-"
        f"{_normalize_token(evidence_id)}"
    )


def create_diagnostic_decision_id(review_id: str, decision_type: str) -> str:
    """Create a deterministic diagnostic approval decision id."""

    _require_nonempty_string(review_id, "review_id")
    _require_supported(decision_type, SCREEN2_REVIEW_DECISIONS, "decision_type")
    return (
        "SCREEN2-DIAG-DECISION-"
        f"{_normalize_token(review_id)}-"
        f"{_normalize_token(decision_type)}"
    )


def create_diagnostic_review_request_id(
    review_target_type: str,
    review_target_id: str,
    requested_decision: str,
) -> str:
    """Create a deterministic Screen 2 diagnostic review request id."""

    _require_supported(
        review_target_type,
        SCREEN2_REVIEW_TARGET_TYPES,
        "review_target_type",
    )
    _require_nonempty_string(review_target_id, "review_target_id")
    _require_supported(
        requested_decision,
        SCREEN2_REVIEW_DECISIONS,
        "requested_decision",
    )
    return (
        "SCREEN2-REVIEW-REQUEST-"
        f"{_normalize_token(review_target_type)}-"
        f"{_normalize_token(review_target_id)}-"
        f"{_normalize_token(requested_decision)}"
    )


def validate_diagnostic_review_record(
    record: DiagnosticReviewRecord,
) -> DiagnosticReviewRecord:
    """Validate and return diagnostic review metadata."""

    if not isinstance(record, DiagnosticReviewRecord):
        raise Screen2DiagnosticReviewError(
            "record must be a DiagnosticReviewRecord instance."
        )
    record.__post_init__()
    return record


def validate_evidence_review_record(
    record: EvidenceReviewRecord,
) -> EvidenceReviewRecord:
    """Validate and return evidence review metadata."""

    if not isinstance(record, EvidenceReviewRecord):
        raise Screen2DiagnosticReviewError(
            "record must be an EvidenceReviewRecord instance."
        )
    record.__post_init__()
    return record


def validate_diagnostic_approval_decision(
    decision: DiagnosticApprovalDecision,
) -> DiagnosticApprovalDecision:
    """Validate and return diagnostic approval decision metadata."""

    if not isinstance(decision, DiagnosticApprovalDecision):
        raise Screen2DiagnosticReviewError(
            "decision must be a DiagnosticApprovalDecision instance."
        )
    decision.__post_init__()
    return decision


def validate_diagnostic_review_request(
    request: DiagnosticReviewRequest,
) -> DiagnosticReviewRequest:
    """Validate and return diagnostic review request metadata."""

    if not isinstance(request, DiagnosticReviewRequest):
        raise Screen2DiagnosticReviewError(
            "request must be a DiagnosticReviewRequest instance."
        )
    request.__post_init__()
    return request


def diagnostic_review_record_to_dict(
    record: DiagnosticReviewRecord,
) -> dict[str, Any]:
    """Serialize diagnostic review metadata to a deterministic dictionary."""

    record = validate_diagnostic_review_record(record)
    return {
        "review_id": record.review_id,
        "screen_id": record.screen_id,
        "run_id": record.run_id,
        "awr_id": record.awr_id,
        "review_target_type": record.review_target_type,
        "review_target_id": record.review_target_id,
        "domain": record.domain,
        "current_value": record.current_value,
        "review_decision": record.review_decision,
        "review_status": record.review_status,
        "reviewer_actor_id": record.reviewer_actor_id,
        "actor_audit_context": _copy_optional_mapping(record.actor_audit_context),
        "review_notes": record.review_notes,
        "linked_candidate_id": record.linked_candidate_id,
        "linked_parser_signal_id": record.linked_parser_signal_id,
        "linked_scoring_review_id": record.linked_scoring_review_id,
        "linked_recommendation_review_id": record.linked_recommendation_review_id,
        "runtime_influence": record.runtime_influence,
        "phase4i_mutation_requested": record.phase4i_mutation_requested,
        "created_at": record.created_at,
        "notes": record.notes,
    }


def diagnostic_review_record_from_dict(
    data: dict[str, Any],
) -> DiagnosticReviewRecord:
    """Deserialize diagnostic review metadata from a dictionary."""

    _require_mapping(data, "data")
    return DiagnosticReviewRecord(
        review_id=str(data["review_id"]),
        screen_id=str(data.get("screen_id", "screen_2")),
        run_id=_optional_text(data.get("run_id")),
        awr_id=_optional_text(data.get("awr_id")),
        review_target_type=str(data["review_target_type"]),
        review_target_id=str(data["review_target_id"]),
        domain=_optional_text(data.get("domain")),
        current_value=data.get("current_value"),
        review_decision=str(data["review_decision"]),
        review_status=str(data["review_status"]),
        reviewer_actor_id=_optional_text(data.get("reviewer_actor_id")),
        actor_audit_context=_copy_optional_mapping(data.get("actor_audit_context")),
        review_notes=_optional_text(data.get("review_notes")),
        linked_candidate_id=_optional_text(data.get("linked_candidate_id")),
        linked_parser_signal_id=_optional_text(data.get("linked_parser_signal_id")),
        linked_scoring_review_id=_optional_text(data.get("linked_scoring_review_id")),
        linked_recommendation_review_id=_optional_text(
            data.get("linked_recommendation_review_id")
        ),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        created_at=_optional_text(data.get("created_at")),
        notes=_optional_text(data.get("notes")),
    )


def evidence_review_record_to_dict(record: EvidenceReviewRecord) -> dict[str, Any]:
    """Serialize evidence review metadata to a deterministic dictionary."""

    record = validate_evidence_review_record(record)
    return {
        "evidence_review_id": record.evidence_review_id,
        "parent_review_id": record.parent_review_id,
        "evidence_type": record.evidence_type,
        "evidence_id": record.evidence_id,
        "evidence_name": record.evidence_name,
        "domain": record.domain,
        "current_value": record.current_value,
        "evidence_status": record.evidence_status,
        "reliability_status": record.reliability_status,
        "missing_reason": record.missing_reason,
        "confidence_impact": record.confidence_impact,
        "review_decision": record.review_decision,
        "reviewer_actor_id": record.reviewer_actor_id,
        "review_notes": record.review_notes,
        "parser_review_recommended": record.parser_review_recommended,
        "scoring_review_recommended": record.scoring_review_recommended,
        "recommendation_review_recommended": (
            record.recommendation_review_recommended
        ),
        "source_review_recommended": record.source_review_recommended,
        "candidate_created": record.candidate_created,
        "runtime_influence": record.runtime_influence,
        "phase4i_mutation_requested": record.phase4i_mutation_requested,
        "notes": record.notes,
    }


def evidence_review_record_from_dict(data: dict[str, Any]) -> EvidenceReviewRecord:
    """Deserialize evidence review metadata from a dictionary."""

    _require_mapping(data, "data")
    return EvidenceReviewRecord(
        evidence_review_id=str(data["evidence_review_id"]),
        parent_review_id=str(data["parent_review_id"]),
        evidence_type=str(data["evidence_type"]),
        evidence_id=str(data["evidence_id"]),
        evidence_name=str(data["evidence_name"]),
        domain=_optional_text(data.get("domain")),
        current_value=data.get("current_value"),
        evidence_status=str(data["evidence_status"]),
        reliability_status=str(data["reliability_status"]),
        missing_reason=str(data.get("missing_reason", "unknown")),
        confidence_impact=str(data.get("confidence_impact", "unknown")),
        review_decision=str(data["review_decision"]),
        reviewer_actor_id=_optional_text(data.get("reviewer_actor_id")),
        review_notes=_optional_text(data.get("review_notes")),
        parser_review_recommended=_bool_from_mapping(
            data,
            "parser_review_recommended",
            False,
        ),
        scoring_review_recommended=_bool_from_mapping(
            data,
            "scoring_review_recommended",
            False,
        ),
        recommendation_review_recommended=_bool_from_mapping(
            data,
            "recommendation_review_recommended",
            False,
        ),
        source_review_recommended=_bool_from_mapping(
            data,
            "source_review_recommended",
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


def diagnostic_approval_decision_to_dict(
    decision: DiagnosticApprovalDecision,
) -> dict[str, Any]:
    """Serialize diagnostic approval decision metadata."""

    decision = validate_diagnostic_approval_decision(decision)
    return {
        "decision_id": decision.decision_id,
        "review_id": decision.review_id,
        "decision_type": decision.decision_type,
        "decision_status": decision.decision_status,
        "actor_id": decision.actor_id,
        "actor_audit_context": _copy_optional_mapping(decision.actor_audit_context),
        "decision_summary": decision.decision_summary,
        "requires_followup": decision.requires_followup,
        "followup_type": decision.followup_type,
        "runtime_influence": decision.runtime_influence,
        "phase4i_mutation_requested": decision.phase4i_mutation_requested,
        "created_at": decision.created_at,
        "notes": decision.notes,
    }


def diagnostic_approval_decision_from_dict(
    data: dict[str, Any],
) -> DiagnosticApprovalDecision:
    """Deserialize diagnostic approval decision metadata."""

    _require_mapping(data, "data")
    return DiagnosticApprovalDecision(
        decision_id=str(data["decision_id"]),
        review_id=str(data["review_id"]),
        decision_type=str(data["decision_type"]),
        decision_status=str(data["decision_status"]),
        actor_id=str(data["actor_id"]),
        actor_audit_context=_copy_optional_mapping(data.get("actor_audit_context")),
        decision_summary=_optional_text(data.get("decision_summary")),
        requires_followup=_bool_from_mapping(data, "requires_followup", False),
        followup_type=_optional_text(data.get("followup_type")),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        created_at=_optional_text(data.get("created_at")),
        notes=_optional_text(data.get("notes")),
    )


def diagnostic_review_request_to_dict(
    request: DiagnosticReviewRequest,
) -> dict[str, Any]:
    """Serialize diagnostic review request metadata."""

    request = validate_diagnostic_review_request(request)
    return {
        "request_id": request.request_id,
        "review_target_type": request.review_target_type,
        "review_target_id": request.review_target_id,
        "requested_decision": request.requested_decision,
        "actor_id": request.actor_id,
        "actor_audit_context": _copy_optional_mapping(request.actor_audit_context),
        "payload": dict(request.payload),
        "validation_status": request.validation_status,
        "can_route_to_governance": request.can_route_to_governance,
        "write_performed": request.write_performed,
        "runtime_influence": request.runtime_influence,
        "phase4i_mutation_requested": request.phase4i_mutation_requested,
        "notes": request.notes,
    }


def diagnostic_review_request_from_dict(
    data: dict[str, Any],
) -> DiagnosticReviewRequest:
    """Deserialize diagnostic review request metadata."""

    _require_mapping(data, "data")
    return DiagnosticReviewRequest(
        request_id=str(data["request_id"]),
        review_target_type=str(data["review_target_type"]),
        review_target_id=str(data["review_target_id"]),
        requested_decision=str(data["requested_decision"]),
        actor_id=str(data["actor_id"]),
        actor_audit_context=_copy_optional_mapping(data.get("actor_audit_context")),
        payload=dict(data.get("payload") or {}),
        validation_status=str(data.get("validation_status", "VALID_METADATA_ONLY")),
        can_route_to_governance=_bool_from_mapping(
            data,
            "can_route_to_governance",
            False,
        ),
        write_performed=_bool_from_mapping(data, "write_performed", False),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        notes=_optional_text(data.get("notes")),
    )


def classify_evidence_review_from_availability(
    record_like: EvidenceReviewRecord | dict[str, Any],
) -> EvidenceReviewRecord:
    """Classify Screen 2 evidence availability as review metadata only."""

    if isinstance(record_like, EvidenceReviewRecord):
        return validate_evidence_review_record(record_like)
    if not isinstance(record_like, dict):
        raise Screen2DiagnosticReviewError(
            "record_like must be a mapping or EvidenceReviewRecord."
        )

    parent_review_id = _first_text(
        record_like.get("parent_review_id"),
        record_like.get("review_id"),
        "SCREEN2-DIAG-REVIEW-UNSPECIFIED",
    )
    evidence_name = _first_text(
        record_like.get("evidence_name"),
        record_like.get("metric_name"),
        record_like.get("name"),
        "unknown_evidence",
    )
    evidence_type = _normalize_supported(
        _normalize_text(
            _first_text(
                record_like.get("evidence_type"),
                record_like.get("review_target_type"),
                "unknown",
            )
        ),
        EVIDENCE_REVIEW_TYPES,
        "unknown",
    )
    evidence_id = _first_text(
        record_like.get("evidence_id"),
        record_like.get("metric_id"),
        _create_evidence_item_id(evidence_type, evidence_name),
    )
    evidence_status = _normalize_supported(
        _normalize_text(
            _first_text(
                record_like.get("evidence_status"),
                record_like.get("availability_status"),
                "unknown",
            )
        ),
        EVIDENCE_STATUSES,
        "unknown",
    )
    reliability_status = _normalize_supported(
        _normalize_text(
            _first_text(
                record_like.get("reliability_status"),
                record_like.get("reliability"),
                "unknown",
            )
        ),
        RELIABILITY_STATUSES,
        "unknown",
    )
    missing_reason = _normalize_missing_reason(record_like.get("missing_reason"))

    value_present = "value" in record_like and record_like.get("value") is not None
    available_flag = record_like.get("available")
    supported_flag = record_like.get("supported")
    extracted_flag = record_like.get("extracted")
    reliability_hint = _normalize_text(record_like.get("reliability"))

    if supported_flag is False:
        evidence_status = "unsupported"
        missing_reason = _unsupported_reason(missing_reason)
        reliability_status = _default_reliability(reliability_status)
    elif extracted_flag is False:
        evidence_status = "not_extracted"
        missing_reason = "parser_gap"
        reliability_status = _default_reliability(reliability_status)
    elif reliability_hint in ("unreliable", "not_reliable", "false"):
        evidence_status = "not_reliable"
        missing_reason = "value_not_reliable"
        reliability_status = "unreliable"
    elif available_flag is False:
        evidence_status = "missing"
        if missing_reason == "unknown":
            missing_reason = "absent_from_report"
        reliability_status = _default_reliability(reliability_status)
    elif value_present:
        evidence_status = "available"
        if reliability_status == "unknown":
            reliability_status = "reliable"
        if missing_reason == "unknown":
            missing_reason = "not_applicable"
    elif evidence_status == "unknown":
        evidence_status = "unavailable"
        if missing_reason == "unknown":
            missing_reason = "absent_from_report"
        reliability_status = _default_reliability(reliability_status)

    confidence_impact = _normalize_supported(
        _normalize_text(record_like.get("confidence_impact")),
        CONFIDENCE_IMPACTS,
        _default_confidence_impact(evidence_status, evidence_type),
    )
    review_decision = _normalize_supported(
        _normalize_text(record_like.get("review_decision")),
        SCREEN2_REVIEW_DECISIONS,
        _default_review_decision(evidence_status, missing_reason, evidence_type),
    )
    parser_review = _optional_bool(
        record_like.get("parser_review_recommended"),
        evidence_status == "not_extracted" or missing_reason == "parser_gap",
    )
    source_review = _optional_bool(
        record_like.get("source_review_recommended"),
        missing_reason in ("source_not_collected", "source_misconfigured"),
    )
    scoring_review = _optional_bool(
        record_like.get("scoring_review_recommended"),
        evidence_type in ("score", "domain_score")
        and evidence_status != "available",
    )
    recommendation_review = _optional_bool(
        record_like.get("recommendation_review_recommended"),
        evidence_type == "recommendation_context"
        and evidence_status != "available",
    )

    return EvidenceReviewRecord(
        evidence_review_id=create_evidence_review_id(
            parent_review_id,
            evidence_type,
            evidence_id,
        ),
        parent_review_id=parent_review_id,
        evidence_type=evidence_type,
        evidence_id=evidence_id,
        evidence_name=evidence_name,
        domain=_optional_text(record_like.get("domain")),
        current_value=record_like.get("current_value", record_like.get("value")),
        evidence_status=evidence_status,
        reliability_status=reliability_status,
        missing_reason=missing_reason,
        confidence_impact=confidence_impact,
        review_decision=review_decision,
        reviewer_actor_id=_optional_text(
            _first_text(record_like.get("reviewer_actor_id"), record_like.get("actor_id"))
        ),
        review_notes=_optional_text(record_like.get("review_notes")),
        parser_review_recommended=parser_review,
        scoring_review_recommended=scoring_review,
        recommendation_review_recommended=recommendation_review,
        source_review_recommended=source_review,
        candidate_created=False,
        runtime_influence=False,
        phase4i_mutation_requested=False,
        notes=_optional_text(record_like.get("notes")),
    )


def _create_evidence_item_id(evidence_type: str, evidence_name: str) -> str:
    return (
        "SCREEN2-EVIDENCE-"
        f"{_normalize_token(evidence_type)}-"
        f"{_normalize_token(evidence_name)}"
    )


def _default_reliability(current: str) -> str:
    return current if current != "unknown" else "insufficient_context"


def _default_review_decision(
    evidence_status: str,
    missing_reason: str,
    evidence_type: str,
) -> str:
    if evidence_status == "available":
        return "confirm"
    if evidence_status == "not_extracted" or missing_reason == "parser_gap":
        return "needs_parser_review"
    if evidence_type in ("score", "domain_score"):
        return "needs_scoring_review"
    if evidence_type == "recommendation_context":
        return "needs_recommendation_review"
    return "insufficient_evidence"


def _default_confidence_impact(evidence_status: str, evidence_type: str) -> str:
    if evidence_status == "available":
        return "none"
    if evidence_type in ("score", "domain_score"):
        return "high"
    if evidence_type in ("metric", "wait_event", "sql_signal", "trend", "anomaly"):
        return "medium"
    if evidence_status == "unsupported":
        return "low"
    return "unknown"


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


def _bool_from_mapping(data: dict[str, Any], field_name: str, default: bool) -> bool:
    value = data.get(field_name, default)
    if isinstance(value, bool):
        return value
    raise Screen2DiagnosticReviewError(f"{field_name} must be a boolean.")


def _copy_optional_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Screen2DiagnosticReviewError("mapping value must be a dictionary.")
    return dict(value)


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise Screen2DiagnosticReviewError(f"{field_name} must be a mapping.")


def _require_optional_mapping(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, dict):
        raise Screen2DiagnosticReviewError(f"{field_name} must be a mapping or None.")


def _require_nonempty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise Screen2DiagnosticReviewError(
            f"{field_name} must be a non-empty string."
        )


def _require_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise Screen2DiagnosticReviewError(f"{field_name} must be a string or None.")


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        raise Screen2DiagnosticReviewError(
            f"{field_name} must be one of: {', '.join(supported)}."
        )


def _require_exact(value: Any, expected: str, field_name: str) -> None:
    if value != expected:
        raise Screen2DiagnosticReviewError(f"{field_name} must be {expected}.")


def _require_boolean(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise Screen2DiagnosticReviewError(f"{field_name} must be a boolean.")


def _require_at_least_one_identifier(*pairs: tuple[str, str | None]) -> None:
    if not any(value for _, value in pairs):
        names = ", ".join(name for name, _ in pairs)
        raise Screen2DiagnosticReviewError(f"one of {names} must be provided.")


def _reject_true(value: bool, field_name: str) -> None:
    if value:
        raise Screen2DiagnosticReviewError(
            f"{field_name} must remain false in Phase 7AQ."
        )


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text).strip("-")
    return text or "NONE"
