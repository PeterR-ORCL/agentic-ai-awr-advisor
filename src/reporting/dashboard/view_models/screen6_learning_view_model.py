"""Screen 6 learning/governance view model.

This module exposes deterministic governed learning evidence from an
evidence_pack_contract. It does not activate learning, bypass governance, call
LLMs, infer state from UI, render HTML, or mutate source contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.reporting.dashboard.contracts.evidence_pack_contract import (
    EvidenceDomain,
    EvidencePackContract,
    get_allowed_visualizations_by_domain,
    get_llm_explanation_eligibility_by_domain,
    get_missing_evidence_by_domain,
    validate_evidence_pack_contract,
)


@dataclass(frozen=True)
class Screen6LearningViewModel:
    screen_id: str
    selected_flow_id: str
    evidence_pack_id: str
    availability_status: str
    summary: str | None
    governance_rows: tuple[dict[str, Any], ...]
    learning_candidates: tuple[dict[str, Any], ...]
    governance_status: tuple[dict[str, Any], ...]
    memory_policy: tuple[dict[str, Any], ...]
    approval_boundaries: tuple[dict[str, Any], ...]
    confidence_basis: tuple[dict[str, Any], ...]
    missing_evidence: tuple[dict[str, Any], ...]
    unavailable_evidence: tuple[dict[str, Any], ...]
    stale_evidence: tuple[dict[str, Any], ...]
    allowed_visualizations: tuple[dict[str, Any], ...]
    llm_explanation_eligibility: tuple[dict[str, Any], ...]
    provenance: dict[str, Any]
    evidence_provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "screen_id": self.screen_id,
            "selected_flow_id": self.selected_flow_id,
            "evidence_pack_id": self.evidence_pack_id,
            "availability_status": self.availability_status,
            "summary": self.summary,
            "governance_rows": list(self.governance_rows),
            "learning_candidates": list(self.learning_candidates),
            "governance_status": list(self.governance_status),
            "memory_policy": list(self.memory_policy),
            "approval_boundaries": list(self.approval_boundaries),
            "confidence_basis": list(self.confidence_basis),
            "missing_evidence": list(self.missing_evidence),
            "unavailable_evidence": list(self.unavailable_evidence),
            "stale_evidence": list(self.stale_evidence),
            "allowed_visualizations": list(self.allowed_visualizations),
            "llm_explanation_eligibility": list(self.llm_explanation_eligibility),
            "provenance": self.provenance,
            "evidence_provenance": self.evidence_provenance,
        }


def build_screen6_learning_view_model(evidence_pack: EvidencePackContract) -> Screen6LearningViewModel:
    """Build Screen 6 learning/governance view model from governed evidence."""

    pack = validate_evidence_pack_contract(evidence_pack)
    domain = EvidenceDomain.LEARNING_GOVERNANCE
    section = pack.learning_governance_evidence
    rows = tuple(row.to_dict() for row in section.rows)
    return Screen6LearningViewModel(
        screen_id="screen6_learning_governance",
        selected_flow_id=pack.selected_flow_id,
        evidence_pack_id=pack.evidence_pack_id,
        availability_status=section.availability_status.value,
        summary=section.summary,
        governance_rows=rows,
        learning_candidates=_fields_matching(rows, ("candidate", "learning")),
        governance_status=_fields_matching(rows, ("governance", "status")),
        memory_policy=_fields_matching(rows, ("memory", "policy")),
        approval_boundaries=_fields_matching(rows, ("approval", "materialization", "activation")),
        confidence_basis=tuple(basis.to_dict() for basis in pack.confidence_basis if basis.domain == domain),
        missing_evidence=tuple(item.to_dict() for item in get_missing_evidence_by_domain(pack, domain)),
        unavailable_evidence=tuple(item.to_dict() for item in pack.unavailable_evidence if item.domain == domain),
        stale_evidence=tuple(item.to_dict() for item in pack.stale_evidence if item.domain == domain),
        allowed_visualizations=tuple(
            item.to_dict() for item in get_allowed_visualizations_by_domain(pack, domain)
        ),
        llm_explanation_eligibility=tuple(
            item.to_dict() for item in get_llm_explanation_eligibility_by_domain(pack, domain)
        ),
        provenance=pack.provenance.to_dict(),
        evidence_provenance=section.provenance.to_dict(),
    )


def _fields_matching(
    rows: tuple[dict[str, Any], ...],
    field_names: tuple[str, ...],
) -> tuple[dict[str, Any], ...]:
    matches: list[dict[str, Any]] = []
    for row in rows:
        values = row.get("values")
        if not isinstance(values, dict):
            continue
        matched = {
            key: value
            for key, value in values.items()
            if any(name in key.lower() for name in field_names)
        }
        if matched:
            matches.append({"row_id": row.get("row_id"), "values": matched})
    return tuple(matches)

