"""Inert Phase 7AZ Screen 4 historical review workflow boundary metadata.

This module exposes static boundary metadata only. It does not create baseline
selection records, trend/anomaly review records, learning candidate intents,
learning candidates, implement UI, implement a write path, call run_analysis.py,
modify dashboards, modify CLI behavior, write databases, write files, import
runtime parser, scoring, decision, or recommendation modules, or mutate Phase
4I.
"""

from __future__ import annotations

from typing import Any


SCREEN4_WORKFLOW_TARGET_TYPES = (
    "historical_baseline",
    "comparison_baseline",
    "trend_summary",
    "trend_metric",
    "anomaly_group",
    "anomaly_event",
    "distribution_view",
    "similar_case",
    "recurrence_pattern",
    "historical_confidence",
    "missing_historical_evidence",
    "trend_aware_scoring_reference",
    "learning_candidate_intent",
)

SCREEN4_WORKFLOW_ACTIONS = (
    "select_official_baseline",
    "approve_trend",
    "dispute_trend",
    "mark_trend_insufficient",
    "approve_anomaly",
    "mark_anomaly_false_positive",
    "mark_anomaly_insufficient",
    "request_trend_aware_scoring_review",
    "request_anomaly_sensitivity_review",
    "request_scoring_threshold_review",
    "request_learning_candidate",
    "add_historical_review_note",
)

SCREEN4_WORKFLOW_STATUSES = (
    "proposed",
    "under_review",
    "approved",
    "disputed",
    "insufficient_evidence",
    "false_positive",
    "routed_to_governance",
    "linked_to_candidate",
    "closed",
)

SCREEN4_WORKFLOW_REQUIRED_GATES = (
    "actor identity",
    "request validation",
    "governed write path",
    "audit trail",
    "output artifact lifecycle",
    "historical truth protection",
    "trend/anomaly truth protection",
    "scoring runtime protection",
    "recommendation truth protection",
    "Phase 4I contract preservation",
    "learning candidate governance",
    "Phase 8 exclusion",
)

_SUPPORTED_BOUNDARY_MODES = ("boundary_only",)


class Screen4HistoricalReviewBoundaryError(ValueError):
    """Raised when Phase 7AZ boundary metadata is asked to do real work."""


def validate_screen4_historical_review_boundary(
    mode: str = "boundary_only",
) -> dict[str, Any]:
    """Validate and return static Phase 7AZ boundary metadata only."""

    if mode not in _SUPPORTED_BOUNDARY_MODES:
        raise Screen4HistoricalReviewBoundaryError(
            f"Unsupported Screen 4 historical review boundary mode: {mode}"
        )
    return {
        "phase": "Phase 7AZ",
        "boundary": "Screen 4 Historical Review Workflow Boundary",
        "mode": mode,
        "boundary_only": True,
        "target_types": list(SCREEN4_WORKFLOW_TARGET_TYPES),
        "actions": list(SCREEN4_WORKFLOW_ACTIONS),
        "statuses": list(SCREEN4_WORKFLOW_STATUSES),
        "required_gates": list(SCREEN4_WORKFLOW_REQUIRED_GATES),
        "workflow_implemented": False,
        "screen4_workflow_ui_added": False,
        "baseline_selection_records_created": False,
        "trend_review_records_created": False,
        "anomaly_review_records_created": False,
        "trend_anomaly_review_records_created": False,
        "learning_candidate_intents_created": False,
        "learning_candidates_created": False,
        "backend_write_path_invoked": False,
        "backend_calls_added": False,
        "run_analysis_wiring_added": False,
        "historical_truth_changed": False,
        "trend_truth_changed": False,
        "anomaly_truth_changed": False,
        "trend_anomaly_truth_changed": False,
        "scoring_behavior_changed": False,
        "trend_aware_scoring_changed": False,
        "confidence_changed": False,
        "recommendation_truth_changed": False,
        "parser_behavior_changed": False,
        "parser_output_changed": False,
        "phase4i_mutation_added": False,
        "deterministic_runtime_authoritative": True,
        "future_baseline_selection_phase": "7BA",
        "future_trend_anomaly_review_phase": "7BB",
        "future_historical_learning_bridge_phase": "7BC",
        "future_validation_certification_phase": "7BD",
        "phase8_sizing_tco_implemented": False,
    }


def screen4_historical_review_boundary_summary() -> dict[str, Any]:
    """Return a deterministic local summary of the Phase 7AZ boundary."""

    boundary = validate_screen4_historical_review_boundary(
        mode="boundary_only"
    )
    return {
        **boundary,
        "summary": (
            "Phase 7AZ is boundary-only; no Screen 4 historical review "
            "workflow is implemented; no Screen 4 workflow UI is added; no "
            "baseline selection records are created; no trend/anomaly review "
            "records are created; no learning candidates are created; no "
            "backend write path is invoked; deterministic historical truth "
            "and deterministic runtime remain authoritative"
        ),
    }
