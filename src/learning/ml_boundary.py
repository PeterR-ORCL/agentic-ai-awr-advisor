"""Inert Phase 7S ML / adaptive scoring boundary helpers.

This module exposes static boundary metadata only. It does not train models,
score runtime data, build datasets, write files, write databases, call
services, import runtime parser/scoring/recommendation modules, or activate
runtime behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ML_BOUNDARY_MODES = (
    "shadow",
)

ML_ALLOWED_OBSERVATION_SOURCES = (
    "feature vectors",
    "trends",
    "anomalies",
    "historical outcomes",
    "governed feedback",
    "action/outcome records",
    "recommendation results",
    "parser unknown records",
    "Phase 7M-7R materialization artifacts",
)

ML_FORBIDDEN_RUNTIME_ACTIONS = (
    "replace deterministic score",
    "change severity",
    "change confidence",
    "change recommendation truth",
    "classify parser output",
    "modify parser output",
    "modify Phase 4I output",
    "activate itself",
    "bypass review",
    "bypass Phase 7M-7R materialization",
    "train a model",
    "implement learned_model(x)",
    "implement Score_ml(x)",
    "implement Score(x, t)",
)

ML_REQUIRED_RUNTIME_ELIGIBILITY_GATES = (
    "model registry approval",
    "validation",
    "backtesting",
    "explainability checks",
    "controlled materialization",
    "rollback plan",
    "certification",
    "explicit runtime eligibility decision",
)


class MLBoundaryError(ValueError):
    """Raised when a requested ML boundary mode violates Phase 7S rules."""


@dataclass(frozen=True)
class MLBoundary:
    """Static non-authoritative boundary description for Phase 7S."""

    mode: str = "shadow"
    runtime_active: bool = False
    runtime_influence_granted: bool = False
    non_authoritative: bool = True
    deterministic_runtime_authoritative: bool = True
    learned_model_implemented: bool = False
    score_ml_implemented: bool = False
    trend_aware_score_implemented: bool = False
    training_implemented: bool = False

    def __post_init__(self) -> None:
        if self.mode not in ML_BOUNDARY_MODES:
            raise MLBoundaryError(f"Unsupported ML boundary mode: {self.mode}")
        if self.runtime_active is not False:
            raise MLBoundaryError("Phase 7S ML boundary cannot be runtime active.")
        if self.runtime_influence_granted is not False:
            raise MLBoundaryError("Phase 7S ML boundary cannot grant runtime influence.")
        if self.non_authoritative is not True:
            raise MLBoundaryError("Phase 7S ML boundary must remain non-authoritative.")
        if self.deterministic_runtime_authoritative is not True:
            raise MLBoundaryError(
                "Phase 7S requires deterministic runtime to remain authoritative."
            )
        if self.learned_model_implemented is not False:
            raise MLBoundaryError("learned_model(x) is not implemented in Phase 7S.")
        if self.score_ml_implemented is not False:
            raise MLBoundaryError("Score_ml(x) is not implemented in Phase 7S.")
        if self.trend_aware_score_implemented is not False:
            raise MLBoundaryError("Score(x, t) is not implemented in Phase 7S.")
        if self.training_implemented is not False:
            raise MLBoundaryError("Training is not implemented in Phase 7S.")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic local summary of the Phase 7S boundary."""

        return {
            "phase": "Phase 7S",
            "boundary": "ML / adaptive scoring boundary",
            "mode": self.mode,
            "shadow_mode": self.mode == "shadow",
            "runtime_active": self.runtime_active,
            "runtime_influence_granted": self.runtime_influence_granted,
            "non_authoritative": self.non_authoritative,
            "deterministic_runtime_authoritative": (
                self.deterministic_runtime_authoritative
            ),
            "deterministic_scoring_remains_authoritative": True,
            "ml_starts_in_shadow_mode": True,
            "ml_may_compare_explain_and_propose_only": True,
            "learned_model_x_not_implemented": not self.learned_model_implemented,
            "score_ml_x_not_implemented": not self.score_ml_implemented,
            "score_x_t_not_implemented": not self.trend_aware_score_implemented,
            "training_implemented": self.training_implemented,
            "allowed_observation_sources": list(ML_ALLOWED_OBSERVATION_SOURCES),
            "forbidden_runtime_actions": list(ML_FORBIDDEN_RUNTIME_ACTIONS),
            "required_runtime_eligibility_gates": list(
                ML_REQUIRED_RUNTIME_ELIGIBILITY_GATES
            ),
        }


def validate_ml_runtime_boundary(mode: str = "shadow") -> dict[str, Any]:
    """Validate and return the inert Phase 7S ML runtime boundary."""

    return MLBoundary(mode=mode).to_dict()


def ml_boundary_summary() -> dict[str, Any]:
    """Return a deterministic local summary of Phase 7S ML boundaries."""

    boundary = validate_ml_runtime_boundary(mode="shadow")
    return {
        **boundary,
        "summary": (
            "shadow mode; non-authoritative; deterministic runtime remains "
            "authoritative; runtime_influence_granted=false; runtime_active=false; "
            "learned_model(x) not implemented"
        ),
    }
