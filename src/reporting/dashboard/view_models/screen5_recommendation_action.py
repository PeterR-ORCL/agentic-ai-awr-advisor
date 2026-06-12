"""Screen 5 Recommendation Action product-safe view model contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .shared_product_shapes import EvidenceReviewSection, ExplanationBlock, ProductScopeSummary


SCREEN5_GUARDRAILS: tuple[str, ...] = (
    "deterministic recommendation decision reference required",
    "LLM explanation is not recommendation evidence",
    "unavailable recommendation state must be explicit",
    "browser/cache cannot create action readiness",
)


@dataclass(frozen=True)
class Screen5RecommendationActionViewModel:
    screen_id: Literal["screen5_recommendation_action"] = "screen5_recommendation_action"
    contract_version: str = "7reset.product.v1"
    scope_summary: ProductScopeSummary = field(default_factory=ProductScopeSummary)
    first_fold: EvidenceReviewSection = field(default_factory=EvidenceReviewSection)
    recommendation_decision: str = ""
    action_plan: tuple[EvidenceReviewSection, ...] = field(default_factory=tuple)
    validation_checklist: tuple[EvidenceReviewSection, ...] = field(default_factory=tuple)
    risk_impact: tuple[EvidenceReviewSection, ...] = field(default_factory=tuple)
    owner_status: str = "unassigned"
    outcome_capture: tuple[EvidenceReviewSection, ...] = field(default_factory=tuple)
    secondary_sections: tuple[EvidenceReviewSection, ...] = field(default_factory=tuple)
    llm_explanation: ExplanationBlock = field(default_factory=ExplanationBlock)
    provenance: tuple[str, ...] = field(default_factory=tuple)
    freshness: str = "unknown"
    internal_refs: tuple[str, ...] = field(default_factory=tuple)

