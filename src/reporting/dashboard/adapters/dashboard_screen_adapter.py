"""Dashboard screen adapter for contract-backed Screen 3/4/5/6 rendering.

This module is the integration boundary between selected-review scope,
deterministic evidence packs, screen view models, and renderer fragments. It
does not import the dashboard shell, read generated dashboard artifacts, inspect
browser state, call LLMs, or compute evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from src.reporting.dashboard.adapters.evidence_pack_builder import (
    build_evidence_pack_contract,
)
from src.reporting.dashboard.contracts.evidence_pack_contract import (
    EvidenceProvenance,
)
from src.reporting.dashboard.contracts.selected_review_scope_contract import (
    SelectedReviewScopeContract,
    validate_selected_review_scope_contract,
)
from src.reporting.dashboard.renderers.screen3_renderer import render_screen3_diagnostic
from src.reporting.dashboard.renderers.screen4_renderer import render_screen4_review
from src.reporting.dashboard.renderers.screen5_renderer import render_screen5_action
from src.reporting.dashboard.renderers.screen6_renderer import render_screen6_learning
from src.reporting.dashboard.view_models.screen3_diagnostic_view_model import (
    build_screen3_diagnostic_view_model,
)
from src.reporting.dashboard.view_models.screen4_review_view_model import (
    build_screen4_review_view_model,
)
from src.reporting.dashboard.view_models.screen5_action_view_model import (
    build_screen5_action_view_model,
)
from src.reporting.dashboard.view_models.screen6_learning_view_model import (
    build_screen6_learning_view_model,
)


@dataclass(frozen=True)
class DashboardScreenRenderBundle:
    selected_flow_id: str
    evidence_pack_id: str
    selected_scope_status: str
    evidence_pack_status: str
    screen3_html: str
    screen4_html: str
    screen5_html: str
    screen6_html: str
    warnings: tuple[dict[str, Any], ...] = ()
    errors: tuple[dict[str, Any], ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_flow_id": self.selected_flow_id,
            "evidence_pack_id": self.evidence_pack_id,
            "selected_scope_status": self.selected_scope_status,
            "evidence_pack_status": self.evidence_pack_status,
            "screen3_html": self.screen3_html,
            "screen4_html": self.screen4_html,
            "screen5_html": self.screen5_html,
            "screen6_html": self.screen6_html,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "provenance": self.provenance,
        }


def build_dashboard_screen_render_bundle(
    selected_scope_contract: SelectedReviewScopeContract | Mapping[str, Any],
    *,
    diagnostic_payload: Mapping[str, Any] | None = None,
    historical_payload: Mapping[str, Any] | None = None,
    comparative_payload: Mapping[str, Any] | None = None,
    deep_analysis_payload: Mapping[str, Any] | None = None,
    recommendation_action_payload: Mapping[str, Any] | None = None,
    learning_governance_payload: Mapping[str, Any] | None = None,
    provenance: EvidenceProvenance | Mapping[str, Any] | str | None = None,
) -> DashboardScreenRenderBundle:
    """Build Screen 3/4/5/6 renderer fragments from the contract spine."""

    if selected_scope_contract is None:
        raise ValueError("selected_scope_contract is required.")

    selected_scope = validate_selected_review_scope_contract(selected_scope_contract)
    evidence_pack = build_evidence_pack_contract(
        selected_scope,
        diagnostic_payload=diagnostic_payload,
        historical_payload=historical_payload,
        comparative_payload=comparative_payload,
        deep_analysis_payload=deep_analysis_payload,
        recommendation_action_payload=recommendation_action_payload,
        learning_governance_payload=learning_governance_payload,
        provenance=provenance,
    )

    screen3_view_model = build_screen3_diagnostic_view_model(evidence_pack)
    screen4_view_model = build_screen4_review_view_model(evidence_pack)
    screen5_view_model = build_screen5_action_view_model(evidence_pack)
    screen6_view_model = build_screen6_learning_view_model(evidence_pack)

    return DashboardScreenRenderBundle(
        selected_flow_id=selected_scope.selected_flow_id,
        evidence_pack_id=evidence_pack.evidence_pack_id,
        selected_scope_status=selected_scope.validation_status.value,
        evidence_pack_status=evidence_pack.validation_status.value,
        screen3_html=render_screen3_diagnostic(screen3_view_model),
        screen4_html=render_screen4_review(screen4_view_model),
        screen5_html=render_screen5_action(screen5_view_model),
        screen6_html=render_screen6_learning(screen6_view_model),
        warnings=_issue_dicts((*selected_scope.warnings, *evidence_pack.warnings)),
        errors=_issue_dicts((*selected_scope.validation_errors, *evidence_pack.validation_errors)),
        provenance={
            "selected_scope": selected_scope.provenance.to_dict(),
            "evidence_pack": evidence_pack.provenance.to_dict(),
        },
    )


def _issue_dicts(issues: tuple[Any, ...]) -> tuple[dict[str, Any], ...]:
    normalized: list[dict[str, Any]] = []
    for issue in issues:
        if hasattr(issue, "to_dict"):
            normalized.append(issue.to_dict())
        elif isinstance(issue, Mapping):
            normalized.append(dict(issue))
        else:
            normalized.append({"message": str(issue)})
    return tuple(normalized)
