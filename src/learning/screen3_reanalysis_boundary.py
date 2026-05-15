"""Inert Phase 7AJ Screen 3 backend re-analysis boundary metadata.

This module exposes static boundary metadata only. It does not implement a
request model, execute backend analysis, call run_analysis.py, call object
storage, modify dashboards, modify CLI behavior, write databases, write files,
or import runtime parser, scoring, decision, or recommendation modules.
"""

from __future__ import annotations

from typing import Any


SCREEN3_REANALYSIS_SELECTED_STATE_FIELDS = (
    "selected_awr",
    "selected_run",
    "selected_database",
    "selected_system",
    "selected_snapshot",
    "selected_comparison_baseline",
    "selected_issue_domain",
    "selected_severity_status",
    "selected_source_mode",
    "selected_object_storage_reference",
    "selected_local_source_reference",
    "selected_execution_mode",
)

SCREEN3_REANALYSIS_ACTIONS = (
    "analyze_selection",
    "rerun_analysis",
    "build_comparison",
    "load_from_object_storage",
)

SCREEN3_REANALYSIS_REQUIRED_GATES = (
    "explicit user action",
    "actor identity",
    "backend execution mode",
    "governed write path",
    "request validation",
    "source validation",
    "output lifecycle",
    "deterministic default",
    "Phase 7AA controlled adaptive gate",
    "Phase 4I contract preservation",
)

SCREEN3_REANALYSIS_SOURCE_MODES = (
    "existing_run",
    "local_source",
    "object_storage",
)

_SUPPORTED_BOUNDARY_MODES = ("boundary_only",)


class Screen3ReanalysisBoundaryError(ValueError):
    """Raised when Phase 7AJ boundary metadata is asked to do real work."""


def validate_screen3_reanalysis_boundary(
    mode: str = "boundary_only",
) -> dict[str, Any]:
    """Validate and return static Phase 7AJ boundary metadata only."""

    if mode not in _SUPPORTED_BOUNDARY_MODES:
        raise Screen3ReanalysisBoundaryError(
            f"Unsupported Screen 3 re-analysis boundary mode: {mode}"
        )
    return {
        "phase": "Phase 7AJ",
        "boundary": "Screen 3 Backend Re-Analysis Boundary",
        "mode": mode,
        "boundary_only": True,
        "selected_state_fields": list(SCREEN3_REANALYSIS_SELECTED_STATE_FIELDS),
        "future_actions": list(SCREEN3_REANALYSIS_ACTIONS),
        "required_gates": list(SCREEN3_REANALYSIS_REQUIRED_GATES),
        "source_modes": list(SCREEN3_REANALYSIS_SOURCE_MODES),
        "selection_is_execution": False,
        "screen3_buttons_added": False,
        "backend_execution_implemented": False,
        "source_selection_implemented": False,
        "object_storage_calls_added": False,
        "run_analysis_wiring_added": False,
        "phase4i_mutation_added": False,
        "dashboard_behavior_changed": False,
        "cli_behavior_changed": False,
        "deterministic_execution_default": True,
        "controlled_adaptive_execution_requires_gate": True,
        "comparison_future_phase": "7AM.1",
        "missing_metric_future_phase": "7AO.1 / 7AQ.1",
        "phase8_sizing_tco_implemented": False,
    }


def screen3_reanalysis_boundary_summary() -> dict[str, Any]:
    """Return a deterministic local summary of the Phase 7AJ boundary."""

    boundary = validate_screen3_reanalysis_boundary(mode="boundary_only")
    return {
        **boundary,
        "summary": (
            "Phase 7AJ is boundary-only; selection is not execution; "
            "no backend execution is implemented; no Screen 3 buttons are "
            "added; deterministic execution is default; controlled adaptive "
            "execution requires gate; AWR/report comparison is future 7AM.1; "
            "missing metric handling is future 7AO.1 / 7AQ.1"
        ),
    }
