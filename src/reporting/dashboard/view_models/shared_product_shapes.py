"""Product-safe shared shapes for the 7RESET dashboard recut.

These dataclasses are passive contracts only. They do not read generated
artifacts, browser continuity state, cache, localStorage, or LLM text as
authority.
"""

from __future__ import annotations

from dataclasses import field, dataclass
from typing import Literal


ScopeClassification = Literal[
    "current_scope",
    "historical_supporting_context",
    "comparative_output",
    "deep_analysis_current_scope",
    "governance_persisted",
]


SCOPE_CLASSIFICATIONS: tuple[str, ...] = (
    "current_scope",
    "historical_supporting_context",
    "comparative_output",
    "deep_analysis_current_scope",
    "governance_persisted",
)


@dataclass(frozen=True)
class ProductScopeSummary:
    label: str = ""
    database_label: str = ""
    instance_label: str = ""
    snapshot_window_label: str = ""
    flow_kind: str = "single_awr"
    validation_status: str = "unavailable"


@dataclass(frozen=True)
class EvidenceDisplayRow:
    label: str = ""
    value: str | int | float | None = None
    unit: str = ""
    interpretation: str = ""
    evidence_ref_label: str = ""
    freshness_status: str = "unknown"
    scope_classification: ScopeClassification = "current_scope"


@dataclass(frozen=True)
class EvidenceReviewSection:
    section_id: str = ""
    title: str = ""
    scope_classification: ScopeClassification = "current_scope"
    rows: tuple[EvidenceDisplayRow, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ExplanationBlock:
    eligibility: str = "unavailable"
    explanation_text: str = ""
    explains_refs: tuple[str, ...] = field(default_factory=tuple)
    prohibited_as_evidence: Literal[True] = True


@dataclass(frozen=True)
class UnavailableVisualState:
    state_id: str = ""
    reason_code: str = ""
    title: str = ""
    message: str = ""
    required_contract: str = ""
    missing_fields: tuple[str, ...] = field(default_factory=tuple)
    scope_classification: ScopeClassification = "current_scope"
    prohibited_substitutes: tuple[str, ...] = field(default_factory=tuple)
    next_deterministic_step: str = ""

