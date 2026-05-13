"""Inert Phase 7M materialization boundary classification helpers.

This module documents candidate materialization boundaries in code form. It
does not create materialization artifacts, transition candidate status, persist
records, call services, or activate runtime behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PARSER_MAPPING_CANDIDATE = "parser_mapping_candidate"
RECOMMENDATION_RULE_CANDIDATE = "recommendation_rule_candidate"
SCORING_WEIGHT_REVIEW_CANDIDATE = "scoring_weight_review_candidate"
DASHBOARD_WORDING_CANDIDATE = "dashboard_wording_candidate"
DASHBOARD_INTERACTION_CANDIDATE = "dashboard_interaction_candidate"
GOVERNANCE_WORKFLOW_CANDIDATE = "governance_workflow_candidate"
SEMANTIC_SUMMARY_CANDIDATE = "semantic_summary_candidate"
DOCUMENTATION_CANDIDATE = "documentation_candidate"
VALIDATION_CANDIDATE = "validation_candidate"

MATERIALIZABLE_CANDIDATE_TYPES = (
    PARSER_MAPPING_CANDIDATE,
    RECOMMENDATION_RULE_CANDIDATE,
    SCORING_WEIGHT_REVIEW_CANDIDATE,
    DASHBOARD_WORDING_CANDIDATE,
    DASHBOARD_INTERACTION_CANDIDATE,
    GOVERNANCE_WORKFLOW_CANDIDATE,
    SEMANTIC_SUMMARY_CANDIDATE,
    DOCUMENTATION_CANDIDATE,
    VALIDATION_CANDIDATE,
)

RUNTIME_SENSITIVE_CANDIDATE_TYPES = (
    PARSER_MAPPING_CANDIDATE,
    RECOMMENDATION_RULE_CANDIDATE,
    SCORING_WEIGHT_REVIEW_CANDIDATE,
)

NON_RUNTIME_MATERIALIZATION_TYPES = (
    DASHBOARD_WORDING_CANDIDATE,
    DASHBOARD_INTERACTION_CANDIDATE,
    GOVERNANCE_WORKFLOW_CANDIDATE,
    SEMANTIC_SUMMARY_CANDIDATE,
    DOCUMENTATION_CANDIDATE,
    VALIDATION_CANDIDATE,
)


class MaterializationBoundaryError(ValueError):
    """Raised when a candidate type violates Phase 7M boundary rules."""


@dataclass(frozen=True)
class MaterializationBoundary:
    """Static boundary description for one candidate type."""

    candidate_type: str
    affected_component: str | None
    materializable: bool
    proposed_artifact_type: str
    runtime_sensitive: bool
    can_ever_influence_runtime: bool
    runtime_influence_requested: bool = False
    runtime_influence_granted: bool = False
    approval_required: tuple[str, ...] = ()
    validation_required: tuple[str, ...] = ()
    rollback_required: tuple[str, ...] = ()
    forbidden: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.candidate_type not in MATERIALIZABLE_CANDIDATE_TYPES:
            raise MaterializationBoundaryError(
                f"Unsupported materialization candidate type: {self.candidate_type}"
            )
        if self.runtime_influence_requested is not False:
            raise MaterializationBoundaryError(
                "Phase 7M does not request runtime influence."
            )
        if self.runtime_influence_granted is not False:
            raise MaterializationBoundaryError(
                "Phase 7M does not grant runtime influence."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic local summary for this boundary."""

        return {
            "candidate_type": self.candidate_type,
            "affected_component": self.affected_component,
            "materializable": self.materializable,
            "proposed_artifact_type": self.proposed_artifact_type,
            "runtime_sensitive": self.runtime_sensitive,
            "can_ever_influence_runtime": self.can_ever_influence_runtime,
            "runtime_influence_requested": self.runtime_influence_requested,
            "runtime_influence_granted": self.runtime_influence_granted,
            "approval_required": list(self.approval_required),
            "validation_required": list(self.validation_required),
            "rollback_required": list(self.rollback_required),
            "forbidden": list(self.forbidden),
            "candidate_approval_is_runtime_activation": False,
            "materialization_is_activation": False,
        }


_BOUNDARY_RULES: dict[str, dict[str, Any]] = {
    PARSER_MAPPING_CANDIDATE: {
        "affected_component": "parser",
        "proposed_artifact_type": "parser materialization artifact",
        "runtime_sensitive": True,
        "can_ever_influence_runtime": True,
        "approval_required": (
            "human approval for implementation consideration",
            "parser owner review",
        ),
        "validation_required": (
            "parser tests",
            "AWR regression validation",
            "Phase 4I contract validation",
            "scoring regression checks",
        ),
        "rollback_required": (
            "parser mapping rollback plan",
            "regression validation rerun",
        ),
        "forbidden": (
            "automatic parser mutation",
            "semantic context changing parser behavior",
            "dashboard approval rewriting parser logic",
            "CLI approval rewriting parser logic",
            "unknown signal auto-classification",
        ),
    },
    RECOMMENDATION_RULE_CANDIDATE: {
        "affected_component": "recommendation",
        "proposed_artifact_type": "versioned recommendation rules",
        "runtime_sensitive": True,
        "can_ever_influence_runtime": True,
        "approval_required": (
            "human approval for implementation consideration",
            "recommendation owner review",
        ),
        "validation_required": (
            "recommendation regression tests",
            "evidence mapping validation",
            "output contract preservation",
        ),
        "rollback_required": (
            "recommendation rule rollback plan",
            "recommendation regression rerun",
        ),
        "forbidden": (
            "automatic recommendation mutation",
            "semantic context changing recommendations",
            "approval directly changing recommendations",
        ),
    },
    SCORING_WEIGHT_REVIEW_CANDIDATE: {
        "affected_component": "scoring",
        "proposed_artifact_type": "versioned scoring config",
        "runtime_sensitive": True,
        "can_ever_influence_runtime": True,
        "approval_required": (
            "human approval for implementation consideration",
            "scoring owner review",
        ),
        "validation_required": (
            "before/after comparison",
            "scoring regression tests",
            "Phase 4I scores contract validation",
        ),
        "rollback_required": (
            "versioned scoring config rollback plan",
            "scoring regression rerun",
        ),
        "forbidden": (
            "automatic scoring mutation",
            "approval directly changing scoring",
            "semantic context directly modifying score",
        ),
    },
    DASHBOARD_WORDING_CANDIDATE: {
        "affected_component": "dashboard",
        "proposed_artifact_type": "dashboard wording proposal",
        "runtime_sensitive": False,
        "can_ever_influence_runtime": False,
        "validation_required": ("dashboard copy review", "dashboard regression checks"),
        "rollback_required": ("wording rollback note",),
        "forbidden": ("changing diagnostic truth", "changing recommendation truth"),
    },
    DASHBOARD_INTERACTION_CANDIDATE: {
        "affected_component": "dashboard",
        "proposed_artifact_type": "dashboard interaction proposal",
        "runtime_sensitive": False,
        "can_ever_influence_runtime": False,
        "validation_required": ("dashboard interactivity tests", "read-only validation"),
        "rollback_required": ("interaction rollback note",),
        "forbidden": ("backend writes", "approval controls", "write controls", "API calls"),
    },
    GOVERNANCE_WORKFLOW_CANDIDATE: {
        "affected_component": "governance",
        "proposed_artifact_type": "governance workflow proposal",
        "runtime_sensitive": False,
        "can_ever_influence_runtime": False,
        "validation_required": ("actor-gating validation", "governance safety tests"),
        "rollback_required": ("workflow rollback or reversal note",),
        "forbidden": ("automatic approval", "automatic activation"),
    },
    SEMANTIC_SUMMARY_CANDIDATE: {
        "affected_component": "semantic_reviewer_assist",
        "proposed_artifact_type": "semantic summary proposal",
        "runtime_sensitive": False,
        "can_ever_influence_runtime": False,
        "validation_required": ("non-authoritative semantic boundary validation",),
        "rollback_required": ("summary rollback note",),
        "forbidden": ("semantic context becoming implementation truth",),
    },
    DOCUMENTATION_CANDIDATE: {
        "affected_component": "documentation",
        "proposed_artifact_type": "documentation change proposal",
        "runtime_sensitive": False,
        "can_ever_influence_runtime": False,
        "validation_required": ("documentation review", "link validation"),
        "rollback_required": ("documentation rollback note",),
        "forbidden": ("claiming unsupported runtime behavior",),
    },
    VALIDATION_CANDIDATE: {
        "affected_component": "validation",
        "proposed_artifact_type": "validation plan or test proposal",
        "runtime_sensitive": False,
        "can_ever_influence_runtime": False,
        "validation_required": ("test review", "deterministic local validation"),
        "rollback_required": ("test rollback note",),
        "forbidden": ("treating tests as runtime activation", "bypassing validation"),
    },
}


def validate_materialization_boundary(
    candidate_type: str,
    affected_component: str | None = None,
) -> MaterializationBoundary:
    """Return the inert Phase 7M boundary for a candidate type."""

    if candidate_type not in _BOUNDARY_RULES:
        raise MaterializationBoundaryError(
            f"Unsupported materialization candidate type: {candidate_type}"
        )
    rule = _BOUNDARY_RULES[candidate_type]
    component = affected_component or rule["affected_component"]
    return MaterializationBoundary(
        candidate_type=candidate_type,
        affected_component=component,
        materializable=True,
        proposed_artifact_type=rule["proposed_artifact_type"],
        runtime_sensitive=rule["runtime_sensitive"],
        can_ever_influence_runtime=rule["can_ever_influence_runtime"],
        approval_required=tuple(
            rule.get(
                "approval_required",
                ("human approval for implementation consideration",),
            )
        ),
        validation_required=tuple(rule["validation_required"]),
        rollback_required=tuple(rule["rollback_required"]),
        forbidden=tuple(rule["forbidden"]),
    )


def materialization_boundary_summary() -> dict[str, Any]:
    """Return a deterministic local summary of Phase 7M boundaries."""

    boundaries = [
        validate_materialization_boundary(candidate_type).to_dict()
        for candidate_type in MATERIALIZABLE_CANDIDATE_TYPES
    ]
    return {
        "phase": "Phase 7M",
        "boundary": "learning materialization boundary",
        "materialization_active": False,
        "runtime_activation_active": False,
        "runtime_influence_granted": False,
        "candidate_approval_is_runtime_activation": False,
        "candidate_approval_is_not_runtime_activation": True,
        "materialization_is_separate_from_approval": True,
        "materialization_is_activation": False,
        "materialization_is_not_activation": True,
        "deterministic_runtime_remains_authoritative": True,
        "candidate_types": list(MATERIALIZABLE_CANDIDATE_TYPES),
        "runtime_sensitive_candidate_types": list(RUNTIME_SENSITIVE_CANDIDATE_TYPES),
        "non_runtime_materialization_types": list(NON_RUNTIME_MATERIALIZATION_TYPES),
        "boundaries": boundaries,
    }
