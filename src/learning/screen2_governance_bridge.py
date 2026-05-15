"""Phase 7AR Screen 2 governance bridge preview models.

This module converts Screen 2 diagnostic and evidence review metadata into
local governance routing recommendations only. It does not execute governance
actions, persist governance records, create candidates, invoke write paths,
call run_analysis.py, modify dashboards, or mutate deterministic runtime truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from src.learning.screen2_diagnostic_review import (
    DiagnosticReviewRecord,
    EvidenceReviewRecord,
    diagnostic_review_record_to_dict,
    evidence_review_record_to_dict,
    validate_diagnostic_review_record,
    validate_evidence_review_record,
)


SCREEN2_GOVERNANCE_ROUTE_TYPES = (
    "no_action",
    "close_review",
    "human_review",
    "parser_review",
    "scoring_review",
    "recommendation_review",
    "evidence_validation",
    "source_review",
    "learning_candidate_request",
)

SCREEN2_GOVERNANCE_ROUTE_TARGETS = (
    "parser_governance",
    "scoring_governance",
    "recommendation_governance",
    "evidence_quality",
    "source_quality",
    "learning_candidate_queue",
    "human_review_queue",
    "review_closure",
)

SCREEN2_GOVERNANCE_WORKFLOWS = (
    "parser_mapping_review",
    "scoring_review",
    "recommendation_rule_review",
    "evidence_availability_review",
    "source_validation_review",
    "learning_candidate_review",
    "human_review",
    "closure",
)

SCREEN2_GOVERNANCE_BRIDGE_STATUSES = (
    "ROUTING_RECOMMENDED",
    "NO_ROUTES",
    "INVALID",
    "PREVIEW_ONLY",
)

SCREEN2_REVIEW_DECISION_ROUTE_MAP = {
    "confirm": "close_review",
    "dispute": "human_review",
    "insufficient_evidence": "evidence_validation",
    "needs_parser_review": "parser_review",
    "needs_scoring_review": "scoring_review",
    "needs_recommendation_review": "recommendation_review",
    "needs_learning_candidate": "learning_candidate_request",
    "add_reviewer_note": "human_review",
}

SCREEN2_CANDIDATE_TYPE_MAP = {
    "parser_review": "parser_mapping_candidate",
    "scoring_review": "scoring_weight_review_candidate",
    "recommendation_review": "recommendation_rule_candidate",
    "evidence_validation": "validation_candidate",
    "source_review": "validation_candidate",
    "learning_candidate_request": "validation_candidate",
    "parser_gap": "parser_mapping_candidate",
    "source_not_collected": "validation_candidate",
    "source_misconfigured": "validation_candidate",
    "domain_score": "scoring_weight_review_candidate",
    "recommendation_context": "recommendation_rule_candidate",
}

SCREEN2_CANDIDATE_TYPES = (
    "parser_mapping_candidate",
    "scoring_weight_review_candidate",
    "recommendation_rule_candidate",
    "validation_candidate",
)

_ROUTE_TYPE_DETAILS = {
    "no_action": ("review_closure", "closure", "no governance action recommended"),
    "close_review": ("review_closure", "closure", "close review"),
    "human_review": ("human_review_queue", "human_review", "route to human review"),
    "parser_review": (
        "parser_governance",
        "parser_mapping_review",
        "request parser review",
    ),
    "scoring_review": (
        "scoring_governance",
        "scoring_review",
        "request scoring review",
    ),
    "recommendation_review": (
        "recommendation_governance",
        "recommendation_rule_review",
        "request recommendation review",
    ),
    "evidence_validation": (
        "evidence_quality",
        "evidence_availability_review",
        "request evidence validation",
    ),
    "source_review": (
        "source_quality",
        "source_validation_review",
        "request source review",
    ),
    "learning_candidate_request": (
        "learning_candidate_queue",
        "learning_candidate_review",
        "request learning candidate review",
    ),
}

_EVIDENCE_ROUTE_ORDER = (
    "parser_review",
    "scoring_review",
    "recommendation_review",
    "source_review",
    "evidence_validation",
    "human_review",
    "learning_candidate_request",
    "close_review",
)


class Screen2GovernanceBridgeError(ValueError):
    """Raised when Phase 7AR governance bridge metadata is invalid."""


@dataclass(frozen=True)
class Screen2GovernanceRoute:
    """Proposed routing decision from Screen 2 review to governance."""

    route_id: str
    source_review_id: str
    route_type: str
    route_target: str
    reason: str
    recommended_action: str
    governance_workflow: str
    source_evidence_review_id: str | None = None
    source_decision_id: str | None = None
    domain: str | None = None
    candidate_type: str | None = None
    actor_id: str | None = None
    actor_audit_context: dict[str, Any] | None = None
    source_payload: dict[str, Any] = field(default_factory=dict)
    route_status: str = "PREVIEW_ONLY"
    can_route_to_governance: bool = True
    governance_action_performed: bool = False
    candidate_created: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.route_id, "route_id")
        _require_nonempty_string(self.source_review_id, "source_review_id")
        _require_optional_string(
            self.source_evidence_review_id,
            "source_evidence_review_id",
        )
        _require_optional_string(self.source_decision_id, "source_decision_id")
        _require_supported(self.route_type, SCREEN2_GOVERNANCE_ROUTE_TYPES, "route_type")
        _require_supported(
            self.route_target,
            SCREEN2_GOVERNANCE_ROUTE_TARGETS,
            "route_target",
        )
        _require_optional_string(self.domain, "domain")
        _require_nonempty_string(self.reason, "reason")
        _require_nonempty_string(self.recommended_action, "recommended_action")
        _require_optional_supported(self.candidate_type, SCREEN2_CANDIDATE_TYPES, "candidate_type")
        _require_supported(
            self.governance_workflow,
            SCREEN2_GOVERNANCE_WORKFLOWS,
            "governance_workflow",
        )
        _require_optional_string(self.actor_id, "actor_id")
        _require_optional_mapping(self.actor_audit_context, "actor_audit_context")
        _require_mapping(self.source_payload, "source_payload")
        _require_supported(
            self.route_status,
            SCREEN2_GOVERNANCE_BRIDGE_STATUSES,
            "route_status",
        )
        _require_boolean(self.can_route_to_governance, "can_route_to_governance")
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
        _reject_true(self.governance_action_performed, "governance_action_performed")
        _reject_true(self.candidate_created, "candidate_created")
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class Screen2CandidateRequestIntent:
    """Proposed candidate request intent, not an actual candidate."""

    intent_id: str
    source_route_id: str
    candidate_type: str
    affected_component: str
    affected_domain: str | None
    rationale: str
    source_evidence: list[str]
    requires_human_review: bool = True
    runtime_influence: bool = False
    candidate_created: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.intent_id, "intent_id")
        _require_nonempty_string(self.source_route_id, "source_route_id")
        _require_supported(self.candidate_type, SCREEN2_CANDIDATE_TYPES, "candidate_type")
        _require_nonempty_string(self.affected_component, "affected_component")
        _require_optional_string(self.affected_domain, "affected_domain")
        _require_nonempty_string(self.rationale, "rationale")
        _require_list_of_strings(self.source_evidence, "source_evidence")
        _require_boolean(self.requires_human_review, "requires_human_review")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _require_boolean(self.candidate_created, "candidate_created")
        if not self.requires_human_review:
            raise Screen2GovernanceBridgeError(
                "requires_human_review must remain true in Phase 7AR."
            )
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(self.candidate_created, "candidate_created")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class Screen2GovernanceBridgeResult:
    """Summary of Screen 2 governance routing recommendations."""

    bridge_result_id: str
    source_review_id: str
    route_count: int
    candidate_intent_count: int
    routes: list[Screen2GovernanceRoute]
    candidate_intents: list[Screen2CandidateRequestIntent]
    bridge_status: str
    governance_actions_performed: bool = False
    candidates_created: bool = False
    runtime_influence: bool = False
    phase4i_mutation_requested: bool = False
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.bridge_result_id, "bridge_result_id")
        _require_nonempty_string(self.source_review_id, "source_review_id")
        _require_nonnegative_int(self.route_count, "route_count")
        _require_nonnegative_int(
            self.candidate_intent_count,
            "candidate_intent_count",
        )
        if not isinstance(self.routes, list):
            raise Screen2GovernanceBridgeError("routes must be a list.")
        if not isinstance(self.candidate_intents, list):
            raise Screen2GovernanceBridgeError("candidate_intents must be a list.")
        for route in self.routes:
            validate_screen2_governance_route(route)
        for intent in self.candidate_intents:
            validate_screen2_candidate_request_intent(intent)
        if self.route_count != len(self.routes):
            raise Screen2GovernanceBridgeError("route_count must match routes.")
        if self.candidate_intent_count != len(self.candidate_intents):
            raise Screen2GovernanceBridgeError(
                "candidate_intent_count must match candidate_intents."
            )
        _require_supported(
            self.bridge_status,
            SCREEN2_GOVERNANCE_BRIDGE_STATUSES,
            "bridge_status",
        )
        _require_boolean(
            self.governance_actions_performed,
            "governance_actions_performed",
        )
        _require_boolean(self.candidates_created, "candidates_created")
        _require_boolean(self.runtime_influence, "runtime_influence")
        _require_boolean(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _reject_true(self.governance_actions_performed, "governance_actions_performed")
        _reject_true(self.candidates_created, "candidates_created")
        _reject_true(self.runtime_influence, "runtime_influence")
        _reject_true(
            self.phase4i_mutation_requested,
            "phase4i_mutation_requested",
        )
        _require_list_of_strings(self.denied_reasons, "denied_reasons")
        _require_list_of_strings(self.warnings, "warnings")
        _require_list_of_strings(self.required_next_steps, "required_next_steps")
        _require_optional_string(self.notes, "notes")


def create_screen2_governance_route_id(
    source_review_id: str,
    route_type: str,
    route_target: str,
) -> str:
    """Create a deterministic Screen 2 governance route id."""

    _require_nonempty_string(source_review_id, "source_review_id")
    _require_supported(route_type, SCREEN2_GOVERNANCE_ROUTE_TYPES, "route_type")
    _require_supported(route_target, SCREEN2_GOVERNANCE_ROUTE_TARGETS, "route_target")
    return (
        "SCREEN2-GOV-ROUTE-"
        f"{_normalize_token(source_review_id)}-"
        f"{_normalize_token(route_type)}-"
        f"{_normalize_token(route_target)}"
    )


def create_screen2_candidate_intent_id(
    source_route_id: str,
    candidate_type: str,
) -> str:
    """Create a deterministic Screen 2 candidate intent id."""

    _require_nonempty_string(source_route_id, "source_route_id")
    _require_supported(candidate_type, SCREEN2_CANDIDATE_TYPES, "candidate_type")
    return (
        "SCREEN2-CANDIDATE-INTENT-"
        f"{_normalize_token(source_route_id)}-"
        f"{_normalize_token(candidate_type)}"
    )


def create_screen2_governance_bridge_result_id(source_review_id: str) -> str:
    """Create a deterministic Screen 2 governance bridge result id."""

    _require_nonempty_string(source_review_id, "source_review_id")
    return f"SCREEN2-GOV-BRIDGE-{_normalize_token(source_review_id)}"


def validate_screen2_governance_route(
    route: Screen2GovernanceRoute,
) -> Screen2GovernanceRoute:
    """Validate and return a governance route preview."""

    if not isinstance(route, Screen2GovernanceRoute):
        raise Screen2GovernanceBridgeError(
            "route must be a Screen2GovernanceRoute instance."
        )
    route.__post_init__()
    return route


def validate_screen2_candidate_request_intent(
    intent: Screen2CandidateRequestIntent,
) -> Screen2CandidateRequestIntent:
    """Validate and return a candidate request intent."""

    if not isinstance(intent, Screen2CandidateRequestIntent):
        raise Screen2GovernanceBridgeError(
            "intent must be a Screen2CandidateRequestIntent instance."
        )
    intent.__post_init__()
    return intent


def validate_screen2_governance_bridge_result(
    result: Screen2GovernanceBridgeResult,
) -> Screen2GovernanceBridgeResult:
    """Validate and return a governance bridge result."""

    if not isinstance(result, Screen2GovernanceBridgeResult):
        raise Screen2GovernanceBridgeError(
            "result must be a Screen2GovernanceBridgeResult instance."
        )
    result.__post_init__()
    return result


def route_diagnostic_review(
    record: DiagnosticReviewRecord,
) -> list[Screen2GovernanceRoute]:
    """Map one diagnostic review record to governance route previews."""

    record = validate_diagnostic_review_record(record)
    route_type = SCREEN2_REVIEW_DECISION_ROUTE_MAP[record.review_decision]
    if record.review_decision == "add_reviewer_note" and not record.review_notes:
        route_type = "no_action"
    candidate_type = _candidate_type_for_diagnostic_route(record, route_type)
    return [
        _build_route(
            source_review_id=record.review_id,
            source_evidence_review_id=None,
            source_decision_id=None,
            route_type=route_type,
            domain=record.domain,
            reason=f"diagnostic review decision: {record.review_decision}",
            candidate_type=candidate_type,
            actor_id=record.reviewer_actor_id,
            actor_audit_context=record.actor_audit_context,
            source_payload=diagnostic_review_record_to_dict(record),
            notes=record.notes,
        )
    ]


def route_evidence_review(record: EvidenceReviewRecord) -> list[Screen2GovernanceRoute]:
    """Map one evidence review record to governance route previews."""

    record = validate_evidence_review_record(record)
    selected: list[str] = []
    if record.parser_review_recommended:
        selected.append("parser_review")
    if record.scoring_review_recommended:
        selected.append("scoring_review")
    if record.recommendation_review_recommended:
        selected.append("recommendation_review")
    if record.source_review_recommended:
        selected.append("source_review")
    if (
        record.evidence_status in ("missing", "unavailable", "unsupported", "not_reliable")
        or record.review_decision == "insufficient_evidence"
    ):
        selected.append("evidence_validation")
    if record.review_decision == "dispute":
        selected.append("human_review")
    if record.review_decision == "needs_learning_candidate":
        selected.append("learning_candidate_request")
    if record.review_decision == "confirm" and not selected:
        selected.append("close_review")

    ordered = [route_type for route_type in _EVIDENCE_ROUTE_ORDER if route_type in selected]
    routes: list[Screen2GovernanceRoute] = []
    for route_type in ordered:
        routes.append(
            _build_route(
                source_review_id=record.parent_review_id,
                source_evidence_review_id=record.evidence_review_id,
                source_decision_id=None,
                route_type=route_type,
                domain=record.domain,
                reason=_evidence_route_reason(record, route_type),
                candidate_type=_candidate_type_for_evidence_route(record, route_type),
                actor_id=record.reviewer_actor_id,
                actor_audit_context=None,
                source_payload=evidence_review_record_to_dict(record),
                notes=record.notes,
            )
        )
    return routes


def create_candidate_intents_from_routes(
    routes: list[Screen2GovernanceRoute],
) -> list[Screen2CandidateRequestIntent]:
    """Create candidate request intents from route previews only."""

    if not isinstance(routes, list):
        raise Screen2GovernanceBridgeError("routes must be a list.")
    intents: list[Screen2CandidateRequestIntent] = []
    for route in routes:
        route = validate_screen2_governance_route(route)
        if route.candidate_type is None:
            continue
        source_evidence = [
            value
            for value in (
                route.source_evidence_review_id,
                route.source_decision_id,
                route.source_review_id,
            )
            if value
        ]
        intent = Screen2CandidateRequestIntent(
            intent_id=create_screen2_candidate_intent_id(
                route.route_id,
                route.candidate_type,
            ),
            source_route_id=route.route_id,
            candidate_type=route.candidate_type,
            affected_component=_affected_component(route),
            affected_domain=route.domain,
            rationale=route.reason,
            source_evidence=source_evidence,
            requires_human_review=True,
            runtime_influence=False,
            candidate_created=False,
            notes=route.notes,
        )
        intents.append(validate_screen2_candidate_request_intent(intent))
    return intents


def bridge_screen2_reviews(
    diagnostic_reviews: list[DiagnosticReviewRecord] | None = None,
    evidence_reviews: list[EvidenceReviewRecord] | None = None,
    actor_id: str | None = None,
    notes: str | None = None,
) -> Screen2GovernanceBridgeResult:
    """Build a deterministic governance bridge result without performing actions."""

    _require_optional_string(actor_id, "actor_id")
    _require_optional_string(notes, "notes")
    diagnostic_reviews = [] if diagnostic_reviews is None else diagnostic_reviews
    evidence_reviews = [] if evidence_reviews is None else evidence_reviews
    if not isinstance(diagnostic_reviews, list):
        raise Screen2GovernanceBridgeError("diagnostic_reviews must be a list.")
    if not isinstance(evidence_reviews, list):
        raise Screen2GovernanceBridgeError("evidence_reviews must be a list.")

    routes: list[Screen2GovernanceRoute] = []
    for review in diagnostic_reviews:
        routes.extend(route_diagnostic_review(review))
    for review in evidence_reviews:
        routes.extend(route_evidence_review(review))

    if actor_id:
        routes = [_route_with_actor(route, actor_id) for route in routes]
    intents = create_candidate_intents_from_routes(routes)
    source_review_id = _bridge_source_review_id(diagnostic_reviews, evidence_reviews)
    warnings: list[str] = []
    required_next_steps: list[str] = []
    if routes:
        required_next_steps.append(
            "review routing recommendations before future governance handling"
        )
    else:
        warnings.append("no routing recommendations produced")

    return Screen2GovernanceBridgeResult(
        bridge_result_id=create_screen2_governance_bridge_result_id(source_review_id),
        source_review_id=source_review_id,
        route_count=len(routes),
        candidate_intent_count=len(intents),
        routes=routes,
        candidate_intents=intents,
        bridge_status="ROUTING_RECOMMENDED" if routes else "NO_ROUTES",
        governance_actions_performed=False,
        candidates_created=False,
        runtime_influence=False,
        phase4i_mutation_requested=False,
        denied_reasons=[],
        warnings=warnings,
        required_next_steps=required_next_steps,
        notes=notes,
    )


def screen2_governance_route_to_dict(
    route: Screen2GovernanceRoute,
) -> dict[str, Any]:
    """Serialize governance route preview metadata."""

    route = validate_screen2_governance_route(route)
    return {
        "route_id": route.route_id,
        "source_review_id": route.source_review_id,
        "source_evidence_review_id": route.source_evidence_review_id,
        "source_decision_id": route.source_decision_id,
        "route_type": route.route_type,
        "route_target": route.route_target,
        "domain": route.domain,
        "reason": route.reason,
        "recommended_action": route.recommended_action,
        "candidate_type": route.candidate_type,
        "governance_workflow": route.governance_workflow,
        "actor_id": route.actor_id,
        "actor_audit_context": _copy_optional_mapping(route.actor_audit_context),
        "source_payload": dict(route.source_payload),
        "route_status": route.route_status,
        "can_route_to_governance": route.can_route_to_governance,
        "governance_action_performed": route.governance_action_performed,
        "candidate_created": route.candidate_created,
        "runtime_influence": route.runtime_influence,
        "phase4i_mutation_requested": route.phase4i_mutation_requested,
        "notes": route.notes,
    }


def screen2_governance_route_from_dict(
    data: dict[str, Any],
) -> Screen2GovernanceRoute:
    """Deserialize governance route preview metadata."""

    _require_mapping(data, "data")
    return Screen2GovernanceRoute(
        route_id=str(data["route_id"]),
        source_review_id=str(data["source_review_id"]),
        source_evidence_review_id=_optional_text(data.get("source_evidence_review_id")),
        source_decision_id=_optional_text(data.get("source_decision_id")),
        route_type=str(data["route_type"]),
        route_target=str(data["route_target"]),
        domain=_optional_text(data.get("domain")),
        reason=str(data["reason"]),
        recommended_action=str(data["recommended_action"]),
        candidate_type=_optional_text(data.get("candidate_type")),
        governance_workflow=str(data["governance_workflow"]),
        actor_id=_optional_text(data.get("actor_id")),
        actor_audit_context=_copy_optional_mapping(data.get("actor_audit_context")),
        source_payload=dict(data.get("source_payload") or {}),
        route_status=str(data.get("route_status", "PREVIEW_ONLY")),
        can_route_to_governance=_bool_from_mapping(
            data,
            "can_route_to_governance",
            True,
        ),
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


def screen2_candidate_request_intent_to_dict(
    intent: Screen2CandidateRequestIntent,
) -> dict[str, Any]:
    """Serialize candidate request intent metadata."""

    intent = validate_screen2_candidate_request_intent(intent)
    return {
        "intent_id": intent.intent_id,
        "source_route_id": intent.source_route_id,
        "candidate_type": intent.candidate_type,
        "affected_component": intent.affected_component,
        "affected_domain": intent.affected_domain,
        "rationale": intent.rationale,
        "source_evidence": list(intent.source_evidence),
        "requires_human_review": intent.requires_human_review,
        "runtime_influence": intent.runtime_influence,
        "candidate_created": intent.candidate_created,
        "notes": intent.notes,
    }


def screen2_candidate_request_intent_from_dict(
    data: dict[str, Any],
) -> Screen2CandidateRequestIntent:
    """Deserialize candidate request intent metadata."""

    _require_mapping(data, "data")
    return Screen2CandidateRequestIntent(
        intent_id=str(data["intent_id"]),
        source_route_id=str(data["source_route_id"]),
        candidate_type=str(data["candidate_type"]),
        affected_component=str(data["affected_component"]),
        affected_domain=_optional_text(data.get("affected_domain")),
        rationale=str(data["rationale"]),
        source_evidence=_string_list(data.get("source_evidence")),
        requires_human_review=_bool_from_mapping(data, "requires_human_review", True),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        candidate_created=_bool_from_mapping(data, "candidate_created", False),
        notes=_optional_text(data.get("notes")),
    )


def screen2_governance_bridge_result_to_dict(
    result: Screen2GovernanceBridgeResult,
) -> dict[str, Any]:
    """Serialize governance bridge result metadata."""

    result = validate_screen2_governance_bridge_result(result)
    return {
        "bridge_result_id": result.bridge_result_id,
        "source_review_id": result.source_review_id,
        "route_count": result.route_count,
        "candidate_intent_count": result.candidate_intent_count,
        "routes": [screen2_governance_route_to_dict(route) for route in result.routes],
        "candidate_intents": [
            screen2_candidate_request_intent_to_dict(intent)
            for intent in result.candidate_intents
        ],
        "bridge_status": result.bridge_status,
        "governance_actions_performed": result.governance_actions_performed,
        "candidates_created": result.candidates_created,
        "runtime_influence": result.runtime_influence,
        "phase4i_mutation_requested": result.phase4i_mutation_requested,
        "denied_reasons": list(result.denied_reasons),
        "warnings": list(result.warnings),
        "required_next_steps": list(result.required_next_steps),
        "notes": result.notes,
    }


def screen2_governance_bridge_result_from_dict(
    data: dict[str, Any],
) -> Screen2GovernanceBridgeResult:
    """Deserialize governance bridge result metadata."""

    _require_mapping(data, "data")
    routes = [
        screen2_governance_route_from_dict(item)
        for item in list(data.get("routes") or [])
    ]
    intents = [
        screen2_candidate_request_intent_from_dict(item)
        for item in list(data.get("candidate_intents") or [])
    ]
    return Screen2GovernanceBridgeResult(
        bridge_result_id=str(data["bridge_result_id"]),
        source_review_id=str(data["source_review_id"]),
        route_count=int(data["route_count"]),
        candidate_intent_count=int(data["candidate_intent_count"]),
        routes=routes,
        candidate_intents=intents,
        bridge_status=str(data["bridge_status"]),
        governance_actions_performed=_bool_from_mapping(
            data,
            "governance_actions_performed",
            False,
        ),
        candidates_created=_bool_from_mapping(data, "candidates_created", False),
        runtime_influence=_bool_from_mapping(data, "runtime_influence", False),
        phase4i_mutation_requested=_bool_from_mapping(
            data,
            "phase4i_mutation_requested",
            False,
        ),
        denied_reasons=_string_list(data.get("denied_reasons")),
        warnings=_string_list(data.get("warnings")),
        required_next_steps=_string_list(data.get("required_next_steps")),
        notes=_optional_text(data.get("notes")),
    )


def _build_route(
    *,
    source_review_id: str,
    source_evidence_review_id: str | None,
    source_decision_id: str | None,
    route_type: str,
    domain: str | None,
    reason: str,
    candidate_type: str | None,
    actor_id: str | None,
    actor_audit_context: dict[str, Any] | None,
    source_payload: dict[str, Any],
    notes: str | None,
) -> Screen2GovernanceRoute:
    route_target, workflow, action = _ROUTE_TYPE_DETAILS[route_type]
    route_source_id = source_evidence_review_id or source_decision_id or source_review_id
    return Screen2GovernanceRoute(
        route_id=create_screen2_governance_route_id(
            route_source_id,
            route_type,
            route_target,
        ),
        source_review_id=source_review_id,
        source_evidence_review_id=source_evidence_review_id,
        source_decision_id=source_decision_id,
        route_type=route_type,
        route_target=route_target,
        domain=domain,
        reason=reason,
        recommended_action=action,
        candidate_type=candidate_type,
        governance_workflow=workflow,
        actor_id=actor_id,
        actor_audit_context=_copy_optional_mapping(actor_audit_context),
        source_payload=dict(source_payload),
        route_status="PREVIEW_ONLY",
        can_route_to_governance=route_type != "no_action",
        governance_action_performed=False,
        candidate_created=False,
        runtime_influence=False,
        phase4i_mutation_requested=False,
        notes=notes,
    )


def _candidate_type_for_diagnostic_route(
    record: DiagnosticReviewRecord,
    route_type: str,
) -> str | None:
    if route_type == "learning_candidate_request":
        if record.review_target_type == "recommendation_context":
            return "recommendation_rule_candidate"
        return "validation_candidate"
    return SCREEN2_CANDIDATE_TYPE_MAP.get(route_type)


def _candidate_type_for_evidence_route(
    record: EvidenceReviewRecord,
    route_type: str,
) -> str | None:
    if route_type == "learning_candidate_request":
        if record.evidence_type == "recommendation_context":
            return "recommendation_rule_candidate"
        return "validation_candidate"
    if record.missing_reason == "parser_gap" and route_type == "parser_review":
        return "parser_mapping_candidate"
    if record.missing_reason in ("source_not_collected", "source_misconfigured"):
        if route_type in ("source_review", "evidence_validation"):
            return "validation_candidate"
    if record.evidence_type == "domain_score" and route_type == "scoring_review":
        return "scoring_weight_review_candidate"
    if record.evidence_type == "recommendation_context":
        if route_type == "recommendation_review":
            return "recommendation_rule_candidate"
    return SCREEN2_CANDIDATE_TYPE_MAP.get(route_type)


def _evidence_route_reason(record: EvidenceReviewRecord, route_type: str) -> str:
    return (
        f"evidence review {route_type}: status={record.evidence_status}; "
        f"missing_reason={record.missing_reason}; decision={record.review_decision}"
    )


def _affected_component(route: Screen2GovernanceRoute) -> str:
    if route.route_type == "parser_review":
        return "parser"
    if route.route_type == "scoring_review":
        return "scoring"
    if route.route_type == "recommendation_review":
        return "recommendation"
    if route.route_type == "source_review":
        return "source"
    if route.route_type == "evidence_validation":
        return "evidence"
    return "learning"


def _route_with_actor(
    route: Screen2GovernanceRoute,
    actor_id: str,
) -> Screen2GovernanceRoute:
    data = screen2_governance_route_to_dict(route)
    data["actor_id"] = actor_id
    return screen2_governance_route_from_dict(data)


def _bridge_source_review_id(
    diagnostic_reviews: list[DiagnosticReviewRecord],
    evidence_reviews: list[EvidenceReviewRecord],
) -> str:
    if diagnostic_reviews:
        return validate_diagnostic_review_record(diagnostic_reviews[0]).review_id
    if evidence_reviews:
        return validate_evidence_review_record(evidence_reviews[0]).parent_review_id
    return "NO-SOURCE-REVIEW"


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _bool_from_mapping(data: dict[str, Any], field_name: str, default: bool) -> bool:
    value = data.get(field_name, default)
    if isinstance(value, bool):
        return value
    raise Screen2GovernanceBridgeError(f"{field_name} must be a boolean.")


def _copy_optional_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Screen2GovernanceBridgeError("mapping value must be a dictionary.")
    return dict(value)


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise Screen2GovernanceBridgeError(f"{field_name} must be a mapping.")


def _require_optional_mapping(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, dict):
        raise Screen2GovernanceBridgeError(f"{field_name} must be a mapping or None.")


def _require_nonempty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise Screen2GovernanceBridgeError(
            f"{field_name} must be a non-empty string."
        )


def _require_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise Screen2GovernanceBridgeError(f"{field_name} must be a string or None.")


def _require_boolean(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise Screen2GovernanceBridgeError(f"{field_name} must be a boolean.")


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        raise Screen2GovernanceBridgeError(
            f"{field_name} must be one of: {', '.join(supported)}."
        )


def _require_optional_supported(
    value: Any,
    supported: tuple[str, ...],
    field_name: str,
) -> None:
    if value is not None and value not in supported:
        raise Screen2GovernanceBridgeError(
            f"{field_name} must be one of: {', '.join(supported)}."
        )


def _require_nonnegative_int(value: Any, field_name: str) -> None:
    if not isinstance(value, int) or value < 0:
        raise Screen2GovernanceBridgeError(
            f"{field_name} must be a non-negative integer."
        )


def _require_list_of_strings(values: Any, field_name: str) -> None:
    if not isinstance(values, list):
        raise Screen2GovernanceBridgeError(f"{field_name} must be a list.")
    if not all(isinstance(value, str) for value in values):
        raise Screen2GovernanceBridgeError(
            f"{field_name} must contain only strings."
        )


def _reject_true(value: bool, field_name: str) -> None:
    if value:
        raise Screen2GovernanceBridgeError(
            f"{field_name} must remain false in Phase 7AR."
        )


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text).strip("-")
    return text or "NONE"
