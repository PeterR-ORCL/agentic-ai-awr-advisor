"""Screen 3 Diagnostic Snapshot view model.

This module maps an evidence_pack_contract into display-ready diagnostic data.
It does not render HTML, compute evidence, execute comparisons, call LLMs, read
browser state, or inspect generated dashboard artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.reporting.dashboard.contracts.evidence_pack_contract import (
    EvidenceDomain,
    EvidencePackContract,
    LLMExplanationEligibility,
    get_llm_explanation_eligibility_by_domain,
    get_missing_evidence_by_domain,
    validate_evidence_pack_contract,
)


@dataclass(frozen=True)
class Screen3DiagnosticViewModel:
    screen_id: str
    selected_flow_id: str
    evidence_pack_id: str
    availability_status: str
    summary: str | None
    evidence_rows: tuple[dict[str, Any], ...]
    metric_summaries: tuple[dict[str, Any], ...]
    trend_summaries: tuple[dict[str, Any], ...]
    anomaly_summaries: tuple[dict[str, Any], ...]
    similarity_context: tuple[dict[str, Any], ...]
    confidence_basis: tuple[dict[str, Any], ...]
    missing_evidence: tuple[dict[str, Any], ...]
    unavailable_evidence: tuple[dict[str, Any], ...]
    stale_evidence: tuple[dict[str, Any], ...]
    provenance: dict[str, Any]
    evidence_provenance: dict[str, Any]
    llm_explanation_eligibility: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "screen_id": self.screen_id,
            "selected_flow_id": self.selected_flow_id,
            "evidence_pack_id": self.evidence_pack_id,
            "availability_status": self.availability_status,
            "summary": self.summary,
            "evidence_rows": list(self.evidence_rows),
            "metric_summaries": list(self.metric_summaries),
            "trend_summaries": list(self.trend_summaries),
            "anomaly_summaries": list(self.anomaly_summaries),
            "similarity_context": list(self.similarity_context),
            "confidence_basis": list(self.confidence_basis),
            "missing_evidence": list(self.missing_evidence),
            "unavailable_evidence": list(self.unavailable_evidence),
            "stale_evidence": list(self.stale_evidence),
            "provenance": self.provenance,
            "evidence_provenance": self.evidence_provenance,
            "llm_explanation_eligibility": list(self.llm_explanation_eligibility),
        }


def build_screen3_diagnostic_view_model(
    evidence_pack: EvidencePackContract,
) -> Screen3DiagnosticViewModel:
    """Build the Screen 3 diagnostic-only view model from an evidence pack."""

    pack = validate_evidence_pack_contract(evidence_pack)
    domain = EvidenceDomain.DIAGNOSTIC
    diagnostic = pack.diagnostic_evidence
    return Screen3DiagnosticViewModel(
        screen_id="screen3_diagnostic_snapshot",
        selected_flow_id=pack.selected_flow_id,
        evidence_pack_id=pack.evidence_pack_id,
        availability_status=diagnostic.availability_status.value,
        summary=diagnostic.summary,
        evidence_rows=tuple(row.to_dict() for row in diagnostic.rows),
        metric_summaries=tuple(summary.to_dict() for summary in pack.metric_summaries if summary.domain == domain),
        trend_summaries=tuple(summary.to_dict() for summary in pack.trend_summaries if summary.domain == domain),
        anomaly_summaries=tuple(summary.to_dict() for summary in pack.anomaly_summaries if summary.domain == domain),
        similarity_context=tuple(context.to_dict() for context in pack.similarity_context if context.domain == domain),
        confidence_basis=tuple(basis.to_dict() for basis in pack.confidence_basis if basis.domain == domain),
        missing_evidence=tuple(item.to_dict() for item in get_missing_evidence_by_domain(pack, domain)),
        unavailable_evidence=tuple(
            item.to_dict() for item in pack.unavailable_evidence if item.domain == domain
        ),
        stale_evidence=tuple(item.to_dict() for item in pack.stale_evidence if item.domain == domain),
        provenance=pack.provenance.to_dict(),
        evidence_provenance=diagnostic.provenance.to_dict(),
        llm_explanation_eligibility=tuple(
            item.to_dict()
            for item in _diagnostic_llm_eligibility(pack, domain)
        ),
    )


def _diagnostic_llm_eligibility(
    pack: EvidencePackContract,
    domain: EvidenceDomain,
) -> tuple[LLMExplanationEligibility, ...]:
    return get_llm_explanation_eligibility_by_domain(pack, domain)

