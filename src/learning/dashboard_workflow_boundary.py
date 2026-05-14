"""Inert Phase 7AD dashboard workflow boundary helpers.

This module exposes static boundary metadata only. It does not create workflow
records, implement actor identity, execute backend analysis, write files, write
databases, call services, import dashboard modules, import runtime parser,
scoring, decision, or recommendation modules, or activate runtime behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DASHBOARD_WORKFLOW_TYPES = (
    "read-only selection workflow",
    "diagnostic review workflow",
    "backend re-analysis workflow",
    "parser governance workflow",
    "recommendation/action/outcome workflow",
    "historical review workflow",
    "governance control workflow",
    "source mode workflow",
)

DASHBOARD_WORKFLOW_STAGES = (
    "read-only exploration",
    "actor identification",
    "action request",
    "request validation",
    "authorization / gate",
    "backend execution",
    "output artifact",
    "audit trail",
    "error / failure",
    "rollback / fallback",
    "closure",
)

DASHBOARD_WORKFLOW_REQUIRED_GATES = (
    "actor identity",
    "request validation",
    "authorization boundary",
    "execution mode declaration",
    "audit trail",
    "output artifact traceability",
    "deterministic fallback",
    "Phase 4I contract preservation",
    "Phase 7AA runtime gate",
)

_SUPPORTED_BOUNDARY_MODES = ("boundary_only",)


class DashboardWorkflowBoundaryError(ValueError):
    """Raised when a dashboard workflow boundary request violates Phase 7AD."""


@dataclass(frozen=True)
class DashboardWorkflowBoundary:
    """Static non-executing boundary description for Phase 7AD."""

    mode: str = "boundary_only"
    workflow_implemented: bool = False
    dashboard_buttons_added: bool = False
    dashboard_write_controls_added: bool = False
    backend_execution_added: bool = False
    actor_model_implemented: bool = False
    governed_write_path_implemented: bool = False
    output_lifecycle_implemented: bool = False
    run_analysis_wiring_added: bool = False
    phase4i_mutation_added: bool = False
    deterministic_runtime_authoritative: bool = True
    phase8_sizing_tco_implemented: bool = False

    def __post_init__(self) -> None:
        if self.mode not in _SUPPORTED_BOUNDARY_MODES:
            raise DashboardWorkflowBoundaryError(
                f"Unsupported dashboard workflow boundary mode: {self.mode}"
            )
        if self.workflow_implemented:
            raise DashboardWorkflowBoundaryError(
                "No workflow is implemented in Phase 7AD."
            )
        if self.dashboard_buttons_added:
            raise DashboardWorkflowBoundaryError(
                "Phase 7AD cannot add dashboard buttons."
            )
        if self.dashboard_write_controls_added:
            raise DashboardWorkflowBoundaryError(
                "Phase 7AD cannot add dashboard write controls."
            )
        if self.backend_execution_added:
            raise DashboardWorkflowBoundaryError(
                "Phase 7AD cannot add backend execution."
            )
        if self.actor_model_implemented:
            raise DashboardWorkflowBoundaryError(
                "Phase 7AD cannot implement the actor model."
            )
        if self.governed_write_path_implemented:
            raise DashboardWorkflowBoundaryError(
                "Phase 7AD cannot implement the governed write path."
            )
        if self.output_lifecycle_implemented:
            raise DashboardWorkflowBoundaryError(
                "Phase 7AD cannot implement the output lifecycle."
            )
        if self.run_analysis_wiring_added:
            raise DashboardWorkflowBoundaryError(
                "Phase 7AD cannot add run_analysis.py wiring."
            )
        if self.phase4i_mutation_added:
            raise DashboardWorkflowBoundaryError(
                "Phase 7AD cannot add Phase 4I mutation."
            )
        if not self.deterministic_runtime_authoritative:
            raise DashboardWorkflowBoundaryError(
                "Deterministic runtime remains authoritative in Phase 7AD."
            )
        if self.phase8_sizing_tco_implemented:
            raise DashboardWorkflowBoundaryError(
                "Phase 8 sizing/TCO is not implemented in Phase 7AD."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic local summary of the Phase 7AD boundary."""

        return {
            "phase": "Phase 7AD",
            "boundary": "Dashboard Workflow Infrastructure Boundary",
            "mode": self.mode,
            "boundary_only": self.mode == "boundary_only",
            "workflow_implemented": self.workflow_implemented,
            "dashboard_buttons_added": self.dashboard_buttons_added,
            "dashboard_write_controls_added": self.dashboard_write_controls_added,
            "backend_execution_added": self.backend_execution_added,
            "actor_model_implemented": self.actor_model_implemented,
            "governed_write_path_implemented": (
                self.governed_write_path_implemented
            ),
            "output_lifecycle_implemented": self.output_lifecycle_implemented,
            "run_analysis_wiring_added": self.run_analysis_wiring_added,
            "phase4i_mutation_added": self.phase4i_mutation_added,
            "deterministic_runtime_authoritative": (
                self.deterministic_runtime_authoritative
            ),
            "phase8_sizing_tco_implemented": self.phase8_sizing_tco_implemented,
            "workflow_types": list(DASHBOARD_WORKFLOW_TYPES),
            "workflow_stages": list(DASHBOARD_WORKFLOW_STAGES),
            "required_gates": list(DASHBOARD_WORKFLOW_REQUIRED_GATES),
        }


def validate_dashboard_workflow_boundary(
    mode: str = "boundary_only",
) -> dict[str, Any]:
    """Validate and return the inert Phase 7AD dashboard workflow boundary."""

    return DashboardWorkflowBoundary(mode=mode).to_dict()


def dashboard_workflow_boundary_summary() -> dict[str, Any]:
    """Return a deterministic local summary of Phase 7AD boundaries."""

    boundary = validate_dashboard_workflow_boundary(mode="boundary_only")
    return {
        **boundary,
        "summary": (
            "Phase 7AD is boundary-only; no workflow is implemented in 7AD; "
            "future workflow actions require actor identity, validation, "
            "audit trail, execution mode declaration, and Phase 7AA gate "
            "protection; deterministic runtime remains authoritative"
        ),
    }
