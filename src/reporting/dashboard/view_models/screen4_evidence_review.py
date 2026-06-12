"""Screen 4 Evidence Review product-safe view model contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .shared_product_shapes import (
    EvidenceDisplayRow,
    EvidenceReviewSection,
    ExplanationBlock,
    ProductScopeSummary,
    UnavailableVisualState,
)
from .visual_contracts import (
    ComparisonDeltaVisual,
    DistributionVisual,
    TimeSeriesVisual,
    ViolinVisual,
)


EvidenceReviewMode = Literal["historical", "comparative", "deep_analysis"]
EvidenceAvailability = Literal["ready", "partial", "unavailable", "blocked"]
ProductVisual = TimeSeriesVisual | DistributionVisual | ViolinVisual | ComparisonDeltaVisual


SCREEN4_GUARDRAILS: tuple[str, ...] = (
    "historical, comparative, and deep_analysis must be distinct panels",
    "each evidence row must have scope_classification",
    "comparative mode requires deterministic Target A/B comparison evidence",
    "deep_analysis mode requires deterministic deep-analysis input evidence",
    "historical context cannot be represented as selected-scope truth",
    "unavailable comparative and deep modes must render unavailable state, not fabricated content",
    "trend IDs and point counts are not sufficient product evidence rows",
)


@dataclass(frozen=True)
class EvidenceReviewModePanel:
    mode: EvidenceReviewMode = "historical"
    availability: EvidenceAvailability = "unavailable"
    first_fold_summary: str = ""
    primary_cards: tuple[EvidenceReviewSection, ...] = field(default_factory=tuple)
    secondary_sections: tuple[EvidenceReviewSection, ...] = field(default_factory=tuple)
    visuals: tuple[ProductVisual, ...] = field(default_factory=tuple)
    evidence_table: tuple[EvidenceDisplayRow, ...] = field(default_factory=tuple)
    unavailable_states: tuple[UnavailableVisualState, ...] = field(default_factory=tuple)
    llm_explanation: ExplanationBlock = field(default_factory=ExplanationBlock)


@dataclass(frozen=True)
class Screen4EvidenceReviewViewModel:
    screen_id: Literal["screen4_evidence_review"] = "screen4_evidence_review"
    contract_version: str = "7reset.product.v1"
    scope_summary: ProductScopeSummary = field(default_factory=ProductScopeSummary)
    active_mode: EvidenceReviewMode = "historical"
    mode_tabs: tuple[EvidenceReviewMode, ...] = ("historical", "comparative", "deep_analysis")
    historical: EvidenceReviewModePanel = field(
        default_factory=lambda: EvidenceReviewModePanel(mode="historical")
    )
    comparative: EvidenceReviewModePanel = field(
        default_factory=lambda: EvidenceReviewModePanel(mode="comparative")
    )
    deep_analysis: EvidenceReviewModePanel = field(
        default_factory=lambda: EvidenceReviewModePanel(mode="deep_analysis")
    )
    cross_mode_warnings: tuple[str, ...] = field(default_factory=tuple)
    provenance: tuple[str, ...] = field(default_factory=tuple)
    freshness: str = "unknown"
    internal_refs: tuple[str, ...] = field(default_factory=tuple)

