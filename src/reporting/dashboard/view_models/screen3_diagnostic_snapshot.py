"""Screen 3 Diagnostic Snapshot product-safe view model contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .shared_product_shapes import (
    EvidenceDisplayRow,
    EvidenceReviewSection,
    ExplanationBlock,
    ProductScopeSummary,
)
from .visual_contracts import (
    ComparisonDeltaVisual,
    DistributionVisual,
    TimeSeriesVisual,
    ViolinVisual,
)


SCREEN3_GUARDRAILS: tuple[str, ...] = (
    "internal_refs is allowed but not first-fold content",
    "selected_flow_id may exist only under internal_refs, provenance, or debug_metadata",
    "evidence_pack_id may exist only under internal_refs, provenance, or debug_metadata",
    "llm_explanation prohibited_as_evidence True",
    "missing evidence must be explicit",
    "Screen 3 cannot accept raw dict/list-only product rows as first-fold or primary-card content",
    "single_awr diagnostic truth cannot be polluted by historical_multi_snapshot context",
)


@dataclass(frozen=True)
class DiagnosticFirstFold:
    status_label: str = ""
    primary_issue_label: str = ""
    severity_score: float | None = None
    confidence_score: float | None = None
    top_driver_labels: tuple[str, ...] = field(default_factory=tuple)
    missing_evidence_summary: str = ""


ProductVisual = TimeSeriesVisual | DistributionVisual | ViolinVisual | ComparisonDeltaVisual


@dataclass(frozen=True)
class Screen3DiagnosticSnapshotViewModel:
    screen_id: Literal["screen3_diagnostic_snapshot"] = "screen3_diagnostic_snapshot"
    contract_version: str = "7reset.product.v1"
    scope_summary: ProductScopeSummary = field(default_factory=ProductScopeSummary)
    first_fold: DiagnosticFirstFold = field(default_factory=DiagnosticFirstFold)
    primary_cards: tuple[EvidenceReviewSection, ...] = field(default_factory=tuple)
    secondary_sections: tuple[EvidenceReviewSection, ...] = field(default_factory=tuple)
    visuals: tuple[ProductVisual, ...] = field(default_factory=tuple)
    evidence_table: tuple[EvidenceDisplayRow, ...] = field(default_factory=tuple)
    missing_evidence: tuple[str, ...] = field(default_factory=tuple)
    llm_explanation: ExplanationBlock = field(default_factory=ExplanationBlock)
    provenance: tuple[str, ...] = field(default_factory=tuple)
    freshness: str = "unknown"
    internal_refs: tuple[str, ...] = field(default_factory=tuple)

