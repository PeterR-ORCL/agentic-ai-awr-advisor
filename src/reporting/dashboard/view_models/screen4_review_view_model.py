"""Screen 4 review view model.

Screen 4 organizes historical, comparative, and deep-analysis evidence from an
evidence_pack_contract. It does not render HTML, infer evidence from UI state,
compute comparisons, call LLMs, or inspect generated dashboard artifacts.
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
class Screen4ReviewModeViewModel:
    mode_id: str
    domain: str
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
    allowed_visualizations: tuple[dict[str, Any], ...]
    llm_explanation_eligibility: tuple[dict[str, Any], ...]
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode_id": self.mode_id,
            "domain": self.domain,
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
            "allowed_visualizations": list(self.allowed_visualizations),
            "llm_explanation_eligibility": list(self.llm_explanation_eligibility),
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class Screen4ReviewViewModel:
    screen_id: str
    selected_flow_id: str
    evidence_pack_id: str
    historical_review: Screen4ReviewModeViewModel
    comparative_review: Screen4ReviewModeViewModel
    deep_analysis: Screen4ReviewModeViewModel
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "screen_id": self.screen_id,
            "selected_flow_id": self.selected_flow_id,
            "evidence_pack_id": self.evidence_pack_id,
            "historical_review": self.historical_review.to_dict(),
            "comparative_review": self.comparative_review.to_dict(),
            "deep_analysis": self.deep_analysis.to_dict(),
            "provenance": self.provenance,
        }


def build_screen4_review_view_model(evidence_pack: EvidencePackContract) -> Screen4ReviewViewModel:
    """Build Screen 4 review mode view models from an evidence pack."""

    pack = validate_evidence_pack_contract(evidence_pack)
    return Screen4ReviewViewModel(
        screen_id="screen4_review",
        selected_flow_id=pack.selected_flow_id,
        evidence_pack_id=pack.evidence_pack_id,
        historical_review=_mode_view_model(pack, EvidenceDomain.HISTORICAL, "historical_review"),
        comparative_review=_mode_view_model(pack, EvidenceDomain.COMPARATIVE, "comparative_review"),
        deep_analysis=_mode_view_model(pack, EvidenceDomain.DEEP_ANALYSIS, "deep_analysis"),
        provenance=pack.provenance.to_dict(),
    )


def _mode_view_model(
    pack: EvidencePackContract,
    domain: EvidenceDomain,
    mode_id: str,
) -> Screen4ReviewModeViewModel:
    section = {
        EvidenceDomain.HISTORICAL: pack.historical_evidence,
        EvidenceDomain.COMPARATIVE: pack.comparative_evidence,
        EvidenceDomain.DEEP_ANALYSIS: pack.deep_analysis_evidence,
    }[domain]
    return Screen4ReviewModeViewModel(
        mode_id=mode_id,
        domain=domain.value,
        availability_status=section.availability_status.value,
        summary=section.summary,
        evidence_rows=tuple(row.to_dict() for row in section.rows),
        metric_summaries=tuple(summary.to_dict() for summary in pack.metric_summaries if summary.domain == domain),
        trend_summaries=tuple(summary.to_dict() for summary in pack.trend_summaries if summary.domain == domain),
        anomaly_summaries=tuple(summary.to_dict() for summary in pack.anomaly_summaries if summary.domain == domain),
        similarity_context=tuple(context.to_dict() for context in pack.similarity_context if context.domain == domain),
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
        provenance=section.provenance.to_dict(),
    )

