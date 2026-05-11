"""Phase 7F local governance bridge for learning candidates.

This module records deterministic review transitions for Phase 7C learning
candidate records. It is local-only, audit-focused, and cannot activate or
modify runtime behavior.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Mapping

from src.learning.learning_candidate_model import (
    APPROVED_FOR_IMPLEMENTATION,
    CLOSED,
    IMPLEMENTED,
    NEEDS_REVISION,
    PROPOSED,
    REJECTED,
    UNDER_REVIEW,
    VALIDATED,
    LearningCandidate,
    attach_materialization_reference,
    transition_candidate_status,
    validate_candidate,
)


MARK_UNDER_REVIEW = "mark_under_review"
REJECT_CANDIDATE = "reject_candidate"
REQUEST_REVISION = "request_revision"
APPROVE_FOR_IMPLEMENTATION = "approve_for_implementation"
ATTACH_MATERIALIZATION = "attach_materialization"
MARK_IMPLEMENTED = "mark_implemented"
MARK_VALIDATED = "mark_validated"
CLOSE_CANDIDATE = "close_candidate"

DECISION_FIELDS = (
    "decision_id",
    "candidate_id",
    "from_status",
    "to_status",
    "actor",
    "decision_type",
    "review_notes",
    "materialization_reference",
    "runtime_influence",
    "approved_for_implementation_only",
    "created_at",
    "audit_records",
)

ALLOWED_TRANSITIONS = {
    PROPOSED: frozenset((UNDER_REVIEW, REJECTED, NEEDS_REVISION)),
    UNDER_REVIEW: frozenset((APPROVED_FOR_IMPLEMENTATION, REJECTED, NEEDS_REVISION)),
    APPROVED_FOR_IMPLEMENTATION: frozenset((IMPLEMENTED, NEEDS_REVISION, CLOSED)),
    IMPLEMENTED: frozenset((VALIDATED,)),
    VALIDATED: frozenset((CLOSED,)),
    NEEDS_REVISION: frozenset((UNDER_REVIEW, CLOSED)),
    REJECTED: frozenset((CLOSED,)),
    CLOSED: frozenset(),
}


class LearningGovernanceBridgeError(ValueError):
    """Raised when a governance action violates Phase 7F boundaries."""


@dataclass(frozen=True)
class GovernanceDecision:
    """Auditable local decision record for one governance action."""

    decision_id: str
    candidate_id: str
    from_status: str
    to_status: str
    actor: str
    decision_type: str
    review_notes: str | None = None
    materialization_reference: str | None = None
    runtime_influence: bool = False
    approved_for_implementation_only: bool = False
    created_at: str | None = None
    audit_records: list[Any] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_text(self.decision_id, "decision_id")
        _require_text(self.candidate_id, "candidate_id")
        _require_text(self.from_status, "from_status")
        _require_text(self.to_status, "to_status")
        _require_text(self.actor, "actor")
        decision_type_text = _require_text(self.decision_type, "decision_type")

        if self.runtime_influence is not False:
            raise LearningGovernanceBridgeError(
                "Governance decisions cannot influence runtime behavior."
            )
        if not isinstance(self.approved_for_implementation_only, bool):
            raise LearningGovernanceBridgeError(
                "approved_for_implementation_only must be a boolean."
            )
        if not isinstance(self.audit_records, list):
            raise LearningGovernanceBridgeError("audit_records must be a list.")

        object.__setattr__(self, "decision_id", self.decision_id.strip())
        object.__setattr__(self, "candidate_id", self.candidate_id.strip())
        object.__setattr__(self, "from_status", self.from_status.strip())
        object.__setattr__(self, "to_status", self.to_status.strip())
        object.__setattr__(self, "actor", self.actor.strip())
        object.__setattr__(self, "decision_type", decision_type_text)
        object.__setattr__(self, "review_notes", _optional_text(self.review_notes))
        object.__setattr__(
            self,
            "materialization_reference",
            _optional_text(self.materialization_reference),
        )
        if _normalize_action(decision_type_text) == APPROVE_FOR_IMPLEMENTATION:
            object.__setattr__(self, "approved_for_implementation_only", True)
        object.__setattr__(self, "audit_records", deepcopy(self.audit_records))


class LearningGovernanceBridge:
    """Controlled review bridge over immutable learning candidate records."""

    def mark_under_review(
        self,
        candidate: LearningCandidate,
        actor: str,
        review_notes: str | None = None,
    ) -> tuple[LearningCandidate, GovernanceDecision]:
        """Move a proposed or revised candidate into human review."""

        return self._transition(candidate, MARK_UNDER_REVIEW, UNDER_REVIEW, actor, review_notes)

    def reject_candidate(
        self,
        candidate: LearningCandidate,
        actor: str,
        review_notes: str,
    ) -> tuple[LearningCandidate, GovernanceDecision]:
        """Reject a proposed or reviewed candidate with required notes."""

        _require_text(review_notes, "review_notes")
        return self._transition(candidate, REJECT_CANDIDATE, REJECTED, actor, review_notes)

    def request_revision(
        self,
        candidate: LearningCandidate,
        actor: str,
        review_notes: str,
    ) -> tuple[LearningCandidate, GovernanceDecision]:
        """Return a proposed, reviewed, or approved candidate for revision."""

        _require_text(review_notes, "review_notes")
        return self._transition(candidate, REQUEST_REVISION, NEEDS_REVISION, actor, review_notes)

    def approve_for_implementation(
        self,
        candidate: LearningCandidate,
        actor: str,
        review_notes: str | None = None,
    ) -> tuple[LearningCandidate, GovernanceDecision]:
        """Approve a reviewed candidate for implementation work only."""

        return self._transition(
            candidate,
            APPROVE_FOR_IMPLEMENTATION,
            APPROVED_FOR_IMPLEMENTATION,
            actor,
            review_notes,
            approved_for_implementation_only=True,
        )

    def attach_materialization(
        self,
        candidate: LearningCandidate,
        actor: str,
        materialization_reference: str,
        review_notes: str | None = None,
    ) -> tuple[LearningCandidate, GovernanceDecision]:
        """Attach an implementation reference without changing runtime behavior."""

        validate_candidate(candidate)
        actor_text = _require_text(actor, "actor")
        reference_text = _require_text(materialization_reference, "materialization_reference")
        if candidate.status == CLOSED:
            raise LearningGovernanceBridgeError(
                "Cannot attach materialization reference to a CLOSED candidate."
            )

        updated = attach_materialization_reference(
            candidate,
            reference_text,
            actor=actor_text,
            review_notes=_optional_text(review_notes),
        )
        decision = _build_decision(
            candidate,
            ATTACH_MATERIALIZATION,
            candidate.status,
            actor_text,
            review_notes=_optional_text(review_notes),
            materialization_reference=reference_text,
        )
        return updated, decision

    def mark_implemented(
        self,
        candidate: LearningCandidate,
        actor: str,
        materialization_reference: str | None = None,
        review_notes: str | None = None,
    ) -> tuple[LearningCandidate, GovernanceDecision]:
        """Mark an approved candidate implemented with an audit reference."""

        validate_candidate(candidate)
        actor_text = _require_text(actor, "actor")
        reference_text = _optional_text(materialization_reference)
        existing_reference = _optional_text(candidate.materialization_reference)
        effective_reference = reference_text or existing_reference
        if effective_reference is None:
            raise LearningGovernanceBridgeError(
                "materialization_reference is required before a candidate can be IMPLEMENTED."
            )

        source_candidate = candidate
        if reference_text is not None:
            source_candidate = attach_materialization_reference(
                candidate,
                reference_text,
                actor=actor_text,
                review_notes=_optional_text(review_notes),
            )

        updated, decision = self._transition(
            source_candidate,
            MARK_IMPLEMENTED,
            IMPLEMENTED,
            actor_text,
            review_notes,
            materialization_reference=effective_reference,
        )
        return updated, decision

    def mark_validated(
        self,
        candidate: LearningCandidate,
        actor: str,
        review_notes: str | None = None,
    ) -> tuple[LearningCandidate, GovernanceDecision]:
        """Mark an implemented candidate validated without enabling runtime influence."""

        return self._transition(candidate, MARK_VALIDATED, VALIDATED, actor, review_notes)

    def close_candidate(
        self,
        candidate: LearningCandidate,
        actor: str,
        review_notes: str | None = None,
    ) -> tuple[LearningCandidate, GovernanceDecision]:
        """Close a candidate at the end of a governed review path."""

        return self._transition(candidate, CLOSE_CANDIDATE, CLOSED, actor, review_notes)

    def _transition(
        self,
        candidate: LearningCandidate,
        action: str,
        to_status: str,
        actor: str,
        review_notes: str | None = None,
        materialization_reference: str | None = None,
        approved_for_implementation_only: bool = False,
    ) -> tuple[LearningCandidate, GovernanceDecision]:
        validate_candidate(candidate)
        actor_text = _require_text(actor, "actor")
        notes_text = _optional_text(review_notes)
        reference_text = _optional_text(materialization_reference)
        _validate_transition(candidate.status, to_status)

        updated = transition_candidate_status(
            candidate,
            to_status,
            actor=actor_text,
            review_notes=notes_text,
        )
        if reference_text is not None:
            updated = attach_materialization_reference(
                updated,
                reference_text,
                actor=actor_text,
                review_notes=notes_text,
            )

        decision = _build_decision(
            candidate,
            action,
            to_status,
            actor_text,
            review_notes=notes_text,
            materialization_reference=reference_text,
            approved_for_implementation_only=approved_for_implementation_only,
        )
        return updated, decision


def governance_decision_to_dict(decision: GovernanceDecision) -> dict[str, Any]:
    """Return a deterministic serializable dictionary for a decision."""

    if not isinstance(decision, GovernanceDecision):
        raise LearningGovernanceBridgeError("decision must be a GovernanceDecision.")
    return {field_name: deepcopy(getattr(decision, field_name)) for field_name in DECISION_FIELDS}


def governance_decision_from_dict(data: Mapping[str, Any]) -> GovernanceDecision:
    """Reconstruct and validate a governance decision from dictionary data."""

    if not isinstance(data, Mapping):
        raise LearningGovernanceBridgeError("decision data must be a mapping.")
    values = {
        field_name: deepcopy(data[field_name])
        for field_name in DECISION_FIELDS
        if field_name in data
    }
    return GovernanceDecision(**values)


def apply_governance_action(
    candidate: LearningCandidate,
    action: str,
    actor: str,
    review_notes: str | None = None,
    materialization_reference: str | None = None,
) -> tuple[LearningCandidate, GovernanceDecision]:
    """Apply a named governance action through the local bridge."""

    action_key = _normalize_action(action)
    bridge = LearningGovernanceBridge()
    if action_key == MARK_UNDER_REVIEW:
        return bridge.mark_under_review(candidate, actor, review_notes)
    if action_key == REJECT_CANDIDATE:
        return bridge.reject_candidate(candidate, actor, _required_notes(review_notes))
    if action_key == REQUEST_REVISION:
        return bridge.request_revision(candidate, actor, _required_notes(review_notes))
    if action_key == APPROVE_FOR_IMPLEMENTATION:
        return bridge.approve_for_implementation(candidate, actor, review_notes)
    if action_key == ATTACH_MATERIALIZATION:
        return bridge.attach_materialization(
            candidate,
            actor,
            _required_reference(materialization_reference),
            review_notes,
        )
    if action_key == MARK_IMPLEMENTED:
        return bridge.mark_implemented(candidate, actor, materialization_reference, review_notes)
    if action_key == MARK_VALIDATED:
        return bridge.mark_validated(candidate, actor, review_notes)
    if action_key == CLOSE_CANDIDATE:
        return bridge.close_candidate(candidate, actor, review_notes)
    raise LearningGovernanceBridgeError(f"Unsupported governance action: {action!r}.")


def _validate_transition(from_status: str, to_status: str) -> None:
    allowed = ALLOWED_TRANSITIONS.get(from_status)
    if allowed is None or to_status not in allowed:
        raise LearningGovernanceBridgeError(
            f"Invalid governance status transition: {from_status} -> {to_status}."
        )


def _build_decision(
    candidate: LearningCandidate,
    action: str,
    to_status: str,
    actor: str,
    review_notes: str | None = None,
    materialization_reference: str | None = None,
    approved_for_implementation_only: bool = False,
) -> GovernanceDecision:
    notes_text = _optional_text(review_notes)
    reference_text = _optional_text(materialization_reference)
    decision_id = _create_decision_id(
        action,
        candidate.candidate_id,
        candidate.status,
        to_status,
        actor,
        reference_text,
    )
    audit_record = {
        "candidate_id": candidate.candidate_id,
        "action": action,
        "from_status": candidate.status,
        "to_status": to_status,
        "actor": actor,
        "decision_type": action,
        "runtime_influence": False,
        "requires_human_review": True,
        "approved_for_implementation_only": approved_for_implementation_only,
    }
    if notes_text is not None:
        audit_record["review_notes"] = notes_text
    if reference_text is not None:
        audit_record["materialization_reference"] = reference_text

    return GovernanceDecision(
        decision_id=decision_id,
        candidate_id=candidate.candidate_id,
        from_status=candidate.status,
        to_status=to_status,
        actor=actor,
        decision_type=action,
        review_notes=notes_text,
        materialization_reference=reference_text,
        runtime_influence=False,
        approved_for_implementation_only=approved_for_implementation_only,
        created_at=None,
        audit_records=[audit_record],
    )


def _create_decision_id(
    action: str,
    candidate_id: str,
    from_status: str,
    to_status: str,
    actor: str,
    materialization_reference: str | None = None,
) -> str:
    seed = {
        "action": _normalize_action(action),
        "candidate_id": candidate_id,
        "from_status": from_status,
        "to_status": to_status,
        "actor": actor.strip(),
        "materialization_reference": materialization_reference or "",
    }
    digest = hashlib.sha256(
        json.dumps(seed, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:12].upper()
    return (
        f"GOVDEC-{_identifier_fragment(action)}-"
        f"{_identifier_fragment(candidate_id)}-{_identifier_fragment(to_status)}-{digest}"
    )


def _normalize_action(action: Any) -> str:
    text = _require_text(action, "action").lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    aliases = {
        "under_review": MARK_UNDER_REVIEW,
        "mark_under_review": MARK_UNDER_REVIEW,
        "reject": REJECT_CANDIDATE,
        "reject_candidate": REJECT_CANDIDATE,
        "request_revision": REQUEST_REVISION,
        "needs_revision": REQUEST_REVISION,
        "approve": APPROVE_FOR_IMPLEMENTATION,
        "approve_for_implementation": APPROVE_FOR_IMPLEMENTATION,
        "approved_for_implementation": APPROVE_FOR_IMPLEMENTATION,
        "attach_materialization": ATTACH_MATERIALIZATION,
        "attach_materialization_reference": ATTACH_MATERIALIZATION,
        "mark_implemented": MARK_IMPLEMENTED,
        "implemented": MARK_IMPLEMENTED,
        "mark_validated": MARK_VALIDATED,
        "validated": MARK_VALIDATED,
        "close": CLOSE_CANDIDATE,
        "close_candidate": CLOSE_CANDIDATE,
        "closed": CLOSE_CANDIDATE,
    }
    return aliases.get(text, text)


def _required_notes(review_notes: str | None) -> str:
    return _require_text(review_notes, "review_notes")


def _required_reference(materialization_reference: str | None) -> str:
    return _require_text(materialization_reference, "materialization_reference")


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LearningGovernanceBridgeError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _identifier_fragment(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "UNKNOWN"
