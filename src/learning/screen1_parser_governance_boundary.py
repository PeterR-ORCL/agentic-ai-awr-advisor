"""Inert Phase 7AU Screen 1 ingestion/parser governance boundary metadata.

This module exposes static boundary metadata only. It does not create source
intake records, parser unknown review records, parser mapping records, parser
candidates, backlog items, knowledge artifact review records, implement UI,
implement a write path, call run_analysis.py, call object storage, query
databases, read files, modify dashboards, modify CLI behavior, import runtime
parser, scoring, decision, or recommendation modules, or mutate Phase 4I.
"""

from __future__ import annotations

from typing import Any


SCREEN1_WORKFLOW_TARGET_TYPES = (
    "source_intake",
    "local_source",
    "object_storage_source",
    "existing_run_source",
    "parser_unknown_signal",
    "parser_section",
    "parser_confidence",
    "parser_diagnostic",
    "parser_mapping_candidate",
    "parser_backlog_item",
    "knowledge_request",
    "knowledge_artifact",
    "artifact_materialization",
    "source_validation_result",
    "ingestion_run",
)

SCREEN1_WORKFLOW_ACTIONS = (
    "validate_source",
    "request_source_intake",
    "classify_unknown_signal",
    "mark_unknown_false_positive",
    "mark_unknown_not_applicable",
    "request_parser_mapping",
    "link_unknown_to_candidate",
    "link_unknown_to_backlog",
    "request_artifact_revision",
    "approve_artifact_for_review",
    "reject_artifact",
    "link_artifact_to_candidate",
    "add_parser_review_note",
)

SCREEN1_WORKFLOW_STATUSES = (
    "proposed",
    "under_review",
    "validated",
    "rejected",
    "needs_revision",
    "routed_to_governance",
    "linked_to_candidate",
    "linked_to_backlog",
    "closed",
)

SCREEN1_WORKFLOW_REQUIRED_GATES = (
    "actor identity",
    "request validation",
    "source validation",
    "governed write path",
    "audit trail",
    "backend execution mode",
    "output artifact lifecycle",
    "parser runtime protection",
    "Phase 4I contract preservation",
    "artifact materialization separation",
    "Phase 8 exclusion",
)

_SUPPORTED_BOUNDARY_MODES = ("boundary_only",)


class Screen1ParserGovernanceBoundaryError(ValueError):
    """Raised when Phase 7AU boundary metadata is asked to do real work."""


def validate_screen1_parser_governance_boundary(
    mode: str = "boundary_only",
) -> dict[str, Any]:
    """Validate and return static Phase 7AU boundary metadata only."""

    if mode not in _SUPPORTED_BOUNDARY_MODES:
        raise Screen1ParserGovernanceBoundaryError(
            f"Unsupported Screen 1 parser governance boundary mode: {mode}"
        )
    return {
        "phase": "Phase 7AU",
        "boundary": "Screen 1 Ingestion / Parser Governance Workflow Boundary",
        "mode": mode,
        "boundary_only": True,
        "target_types": list(SCREEN1_WORKFLOW_TARGET_TYPES),
        "actions": list(SCREEN1_WORKFLOW_ACTIONS),
        "statuses": list(SCREEN1_WORKFLOW_STATUSES),
        "required_gates": list(SCREEN1_WORKFLOW_REQUIRED_GATES),
        "workflow_implemented": False,
        "screen1_workflow_ui_added": False,
        "source_intake_controls_added": False,
        "parser_unknown_action_buttons_added": False,
        "knowledge_artifact_approval_buttons_added": False,
        "source_intake_invoked": False,
        "local_file_read_performed": False,
        "object_storage_call_performed": False,
        "db_lookup_performed": False,
        "parser_unknown_classification_performed": False,
        "parser_mapping_records_created": False,
        "parser_candidates_created": False,
        "parser_backlog_items_created": False,
        "knowledge_artifacts_approved_rejected": False,
        "artifact_materialization_performed": False,
        "governed_write_path_invoked": False,
        "backend_calls_added": False,
        "run_analysis_wiring_added": False,
        "source_ingestion_behavior_changed": False,
        "parser_behavior_changed": False,
        "parser_output_changed": False,
        "scoring_behavior_changed": False,
        "decision_behavior_changed": False,
        "recommendation_behavior_changed": False,
        "phase4i_mutation_added": False,
        "deterministic_runtime_authoritative": True,
        "parser_runtime_authoritative": True,
        "future_source_intake_phase": "7AV",
        "future_parser_unknown_review_phase": "7AW",
        "future_knowledge_artifact_review_phase": "7AX",
        "future_validation_certification_phase": "7AY",
        "phase8_em_extract_implemented": False,
        "phase8_sizing_tco_implemented": False,
    }


def screen1_parser_governance_boundary_summary() -> dict[str, Any]:
    """Return a deterministic local summary of the Phase 7AU boundary."""

    boundary = validate_screen1_parser_governance_boundary(
        mode="boundary_only"
    )
    return {
        **boundary,
        "summary": (
            "Phase 7AU is boundary-only; no Screen 1 ingestion/parser "
            "governance workflow is implemented; no Screen 1 workflow UI is "
            "added; no source intake is invoked; no parser unknown "
            "classification is performed; no parser mapping records or "
            "parser candidates are created; no knowledge artifacts are "
            "approved/rejected; parser runtime and deterministic runtime "
            "remain authoritative"
        ),
    }
