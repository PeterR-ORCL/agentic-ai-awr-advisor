"""Inert Phase 7BE Screen 5 recommendation/action workflow boundary metadata.

This module exposes static boundary metadata only. It does not create
recommendation decision records, action records, outcome records, feedback
records, learning candidate intents, implement UI, implement a write path, call
run_analysis.py, modify dashboards, modify CLI behavior, write databases, write
files, import runtime parser, scoring, decision, or recommendation modules, or
mutate Phase 4I.
"""

from __future__ import annotations

from typing import Any


SCREEN5_WORKFLOW_TARGET_TYPES = (
    "recommendation",
    "recommendation_domain",
    "recommendation_category",
    "recommendation_evidence",
    "recommendation_action",
    "assigned_action",
    "action_status",
    "implementation_date",
    "outcome",
    "feedback",
    "recommendation_effectiveness",
    "recommendation_rule_candidate",
    "learning_candidate_intent",
)

SCREEN5_WORKFLOW_ACTIONS = (
    "accept_recommendation",
    "reject_recommendation",
    "defer_recommendation",
    "mark_not_applicable",
    "assign_owner",
    "create_action_item",
    "update_action_status",
    "record_implementation_date",
    "capture_outcome",
    "mark_effective",
    "mark_ineffective",
    "add_feedback",
    "request_recommendation_review",
    "request_learning_candidate",
)

RECOMMENDATION_DECISION_STATUSES = (
    "proposed",
    "accepted",
    "rejected",
    "deferred",
    "not_applicable",
    "under_review",
    "closed",
)

ACTION_STATUSES = (
    "proposed",
    "assigned",
    "in_progress",
    "implemented",
    "blocked",
    "cancelled",
    "closed",
)

OUTCOME_STATUSES = (
    "pending",
    "improved",
    "worsened",
    "no_change",
    "issue_recurred",
    "inconclusive",
    "closed",
)

FEEDBACK_STATUSES = (
    "proposed",
    "reviewed",
    "routed_to_learning",
    "closed",
)

SCREEN5_WORKFLOW_REQUIRED_GATES = (
    "actor identity",
    "request validation",
    "governed write path",
    "audit trail",
    "recommendation truth protection",
    "recommendation ranking protection",
    "recommendation evidence mapping protection",
    "recommendation text protection",
    "Phase 4I contract preservation",
    "parser/scoring/decision runtime protection",
    "feedback-to-learning future 7BI",
    "recommendation rule evolution governance",
)

_SUPPORTED_BOUNDARY_MODES = ("boundary_only",)


class Screen5ActionWorkflowBoundaryError(ValueError):
    """Raised when Phase 7BE boundary metadata is asked to do real work."""


def validate_screen5_action_workflow_boundary(
    mode: str = "boundary_only",
) -> dict[str, Any]:
    """Validate and return static Phase 7BE boundary metadata only."""

    if mode not in _SUPPORTED_BOUNDARY_MODES:
        raise Screen5ActionWorkflowBoundaryError(
            f"Unsupported Screen 5 action workflow boundary mode: {mode}"
        )
    return {
        "phase": "Phase 7BE",
        "boundary": "Screen 5 Recommendation Action Workflow Boundary",
        "mode": mode,
        "boundary_only": True,
        "target_types": list(SCREEN5_WORKFLOW_TARGET_TYPES),
        "actions": list(SCREEN5_WORKFLOW_ACTIONS),
        "recommendation_decision_statuses": list(
            RECOMMENDATION_DECISION_STATUSES
        ),
        "action_statuses": list(ACTION_STATUSES),
        "outcome_statuses": list(OUTCOME_STATUSES),
        "feedback_statuses": list(FEEDBACK_STATUSES),
        "required_gates": list(SCREEN5_WORKFLOW_REQUIRED_GATES),
        "workflow_implemented": False,
        "screen5_action_ui_added": False,
        "recommendation_decision_records_created": False,
        "action_records_created": False,
        "outcome_records_created": False,
        "feedback_records_created": False,
        "learning_candidate_intents_created": False,
        "learning_candidates_created": False,
        "recommendation_rule_candidates_created": False,
        "backend_write_path_invoked": False,
        "backend_calls_added": False,
        "run_analysis_wiring_added": False,
        "recommendation_truth_changed": False,
        "recommendation_ranking_changed": False,
        "recommendation_evidence_mapping_changed": False,
        "recommendation_text_changed": False,
        "recommendation_action_sequencing_changed": False,
        "score_changed": False,
        "decision_changed": False,
        "parser_behavior_changed": False,
        "phase4i_mutation_added": False,
        "deterministic_runtime_authoritative": True,
        "feedback_to_learning_future_phase": "7BI",
        "phase8_sizing_tco_implemented": False,
    }


def screen5_action_workflow_boundary_summary() -> dict[str, Any]:
    """Return a deterministic local summary of the Phase 7BE boundary."""

    boundary = validate_screen5_action_workflow_boundary(mode="boundary_only")
    return {
        **boundary,
        "summary": (
            "Phase 7BE is boundary-only; no Screen 5 action workflow is "
            "implemented; no Screen 5 action UI is added; no recommendation "
            "decision, action, outcome, or feedback records are created; no "
            "backend write path is invoked; deterministic recommendation "
            "truth and deterministic runtime remain authoritative; "
            "feedback-to-learning remains future 7BI"
        ),
    }
