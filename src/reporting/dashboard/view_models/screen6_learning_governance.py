"""Screen 6 Learning Governance product-safe view model contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .shared_product_shapes import EvidenceReviewSection


SCREEN6_GUARDRAILS: tuple[str, ...] = (
    "governed eligibility required for runtime eligibility",
    "memory or semantic recall cannot be diagnostic or recommendation evidence",
    "materialization state must be persisted/governed",
    "LLM cannot approve learning or runtime eligibility",
)


@dataclass(frozen=True)
class Screen6LearningGovernanceViewModel:
    screen_id: Literal["screen6_learning_governance"] = "screen6_learning_governance"
    contract_version: str = "7reset.product.v1"
    governance_summary: EvidenceReviewSection = field(default_factory=EvidenceReviewSection)
    candidate_queue: tuple[EvidenceReviewSection, ...] = field(default_factory=tuple)
    governance_status: str = "unavailable"
    materialization_gate: str = "blocked"
    runtime_eligibility: str = "unavailable"
    memory_policy: str = "not_authoritative"
    audit_timeline: tuple[EvidenceReviewSection, ...] = field(default_factory=tuple)
    secondary_sections: tuple[EvidenceReviewSection, ...] = field(default_factory=tuple)
    provenance: tuple[str, ...] = field(default_factory=tuple)
    freshness: str = "unknown"
    internal_refs: tuple[str, ...] = field(default_factory=tuple)

