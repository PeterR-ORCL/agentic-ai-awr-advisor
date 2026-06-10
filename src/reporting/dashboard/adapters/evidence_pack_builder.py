"""Deterministic evidence pack builder.

This adapter converts an explicit selected_review_scope_contract and
deterministic backend payload mappings into an evidence_pack_contract. It does
not call parsers, dashboard renderers, runtime services, generated artifacts, or
LLMs.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from src.reporting.dashboard.contracts.evidence_pack_contract import (
    CONTRACT_TYPE,
    CONTRACT_VERSION,
    AllowedVisualization,
    AnomalySummary,
    ComparativeEvidence,
    ConfidenceBasis,
    DeepAnalysisEvidence,
    DiagnosticEvidence,
    EvidenceAvailabilityStatus,
    EvidenceDomain,
    EvidenceFreshness,
    EvidenceIssue,
    EvidencePackContract,
    EvidencePackValidationStatus,
    EvidenceProvenance,
    EvidenceRow,
    EvidenceSeverity,
    HistoricalEvidence,
    LLMExplanationEligibility,
    LLMExplanationStatus,
    LearningGovernanceEvidence,
    MetricSummary,
    MissingEvidence,
    RecommendationActionEvidence,
    SimilarityContext,
    StaleEvidence,
    TrendSummary,
    UnavailableEvidence,
    VisualizationKind,
    compute_evidence_pack_id,
    detect_forbidden_authority_keys,
    validate_evidence_pack_contract,
)
from src.reporting.dashboard.contracts.selected_review_scope_contract import (
    ReviewMode,
    ScopeValidationStatus,
    SelectedReviewScopeContract,
    is_comparative_review_eligible,
    is_deep_analysis_eligible,
    is_diagnostic_snapshot_eligible,
    is_historical_review_eligible,
    unavailable_reasons_for,
    validate_selected_review_scope_contract,
)


DOMAIN_MODE = {
    EvidenceDomain.DIAGNOSTIC: ReviewMode.DIAGNOSTIC_SNAPSHOT,
    EvidenceDomain.HISTORICAL: ReviewMode.HISTORICAL_REVIEW,
    EvidenceDomain.COMPARATIVE: ReviewMode.COMPARATIVE_REVIEW,
    EvidenceDomain.DEEP_ANALYSIS: ReviewMode.DEEP_ANALYSIS,
    EvidenceDomain.RECOMMENDATION_ACTION: ReviewMode.RECOMMENDATION_ACTION,
    EvidenceDomain.LEARNING_GOVERNANCE: ReviewMode.LEARNING_GOVERNANCE,
}


def build_evidence_pack_contract(
    selected_scope_contract: SelectedReviewScopeContract | Mapping[str, Any],
    *,
    diagnostic_payload: Mapping[str, Any] | None = None,
    historical_payload: Mapping[str, Any] | None = None,
    comparative_payload: Mapping[str, Any] | None = None,
    deep_analysis_payload: Mapping[str, Any] | None = None,
    recommendation_action_payload: Mapping[str, Any] | None = None,
    learning_governance_payload: Mapping[str, Any] | None = None,
    provenance: EvidenceProvenance | Mapping[str, Any] | str | None = None,
) -> EvidencePackContract:
    """Build an evidence pack from selected scope and deterministic payloads."""

    if selected_scope_contract is None:
        raise ValueError("selected_scope_contract is required.")

    selected_scope = validate_selected_review_scope_contract(selected_scope_contract)
    pack_provenance = EvidenceProvenance.from_value(
        provenance
        or {
            "source_system": "deterministic_evidence_pack_builder",
            "builder_version": CONTRACT_VERSION,
            "deterministic_sources": ("selected_review_scope_contract",),
        }
    )

    errors: list[EvidenceIssue] = []
    warnings: list[EvidenceIssue] = []
    missing: list[MissingEvidence] = []
    unavailable: list[UnavailableEvidence] = []
    stale: list[StaleEvidence] = []
    visualizations: list[AllowedVisualization] = []
    llm_eligibility: list[LLMExplanationEligibility] = []
    rows: list[EvidenceRow] = []
    metrics: list[MetricSummary] = []
    trends: list[TrendSummary] = []
    anomalies: list[AnomalySummary] = []
    similarities: list[SimilarityContext] = []
    confidence: list[ConfidenceBasis] = []

    if selected_scope.validation_status in {ScopeValidationStatus.INVALID, ScopeValidationStatus.UNAVAILABLE}:
        for domain in EvidenceDomain:
            unavailable.append(
                UnavailableEvidence(
                    domain=domain,
                    reason_code="selected_scope_invalid",
                    message="Selected review scope is invalid or unavailable.",
                )
            )
        sections = {
            EvidenceDomain.DIAGNOSTIC: DiagnosticEvidence(
                availability_status=EvidenceAvailabilityStatus.UNAVAILABLE
            ),
            EvidenceDomain.HISTORICAL: HistoricalEvidence(
                availability_status=EvidenceAvailabilityStatus.UNAVAILABLE
            ),
            EvidenceDomain.COMPARATIVE: ComparativeEvidence(
                availability_status=EvidenceAvailabilityStatus.UNAVAILABLE
            ),
            EvidenceDomain.DEEP_ANALYSIS: DeepAnalysisEvidence(
                availability_status=EvidenceAvailabilityStatus.UNAVAILABLE
            ),
            EvidenceDomain.RECOMMENDATION_ACTION: RecommendationActionEvidence(
                availability_status=EvidenceAvailabilityStatus.UNAVAILABLE
            ),
            EvidenceDomain.LEARNING_GOVERNANCE: LearningGovernanceEvidence(
                availability_status=EvidenceAvailabilityStatus.UNAVAILABLE
            ),
        }
        errors.append(
            EvidenceIssue(
                code="selected_scope_invalid",
                message="Evidence pack cannot provide evidence for invalid selected scope.",
                severity=EvidenceSeverity.ERROR,
            )
        )
        return _assemble_contract(
            selected_scope=selected_scope,
            sections=sections,
            rows=(),
            metrics=(),
            trends=(),
            anomalies=(),
            similarities=(),
            confidence=(),
            missing=(),
            unavailable=tuple(unavailable),
            stale=(),
            visualizations=(),
            llm_eligibility=tuple(
                _blocked_llm(domain, "Selected review scope is invalid or unavailable.")
                for domain in EvidenceDomain
            ),
            provenance=pack_provenance,
            errors=tuple(errors),
            warnings=(),
        )

    domain_payloads = {
        EvidenceDomain.DIAGNOSTIC: diagnostic_payload,
        EvidenceDomain.HISTORICAL: historical_payload,
        EvidenceDomain.COMPARATIVE: comparative_payload,
        EvidenceDomain.DEEP_ANALYSIS: deep_analysis_payload,
        EvidenceDomain.RECOMMENDATION_ACTION: recommendation_action_payload,
        EvidenceDomain.LEARNING_GOVERNANCE: learning_governance_payload,
    }

    sections: dict[EvidenceDomain, Any] = {}
    for domain, payload in domain_payloads.items():
        eligible = _domain_eligible(selected_scope, domain)
        if not eligible:
            reason_message = _unavailable_message(selected_scope, domain)
            sections[domain] = _empty_section(domain, EvidenceAvailabilityStatus.UNAVAILABLE)
            unavailable.append(
                UnavailableEvidence(
                    domain=domain,
                    reason_code="mode_unavailable",
                    message=reason_message,
                )
            )
            llm_eligibility.append(_blocked_llm(domain, reason_message))
            continue

        if payload is None:
            reason = f"{domain.value} deterministic payload is missing."
            sections[domain] = _empty_section(domain, EvidenceAvailabilityStatus.MISSING)
            missing.append(
                MissingEvidence(
                    domain=domain,
                    reason_code="payload_missing",
                    message=reason,
                    required_for_modes=(DOMAIN_MODE[domain],),
                )
            )
            llm_eligibility.append(_blocked_llm(domain, reason))
            continue

        normalized = _normalize_payload(domain, payload, pack_provenance)
        errors.extend(normalized["errors"])
        warnings.extend(normalized["warnings"])
        if normalized["errors"]:
            reason = "Payload contains non-authoritative browser, generated HTML, UI, chart markup, or LLM evidence."
            sections[domain] = _empty_section(domain, EvidenceAvailabilityStatus.UNAVAILABLE)
            unavailable.append(
                UnavailableEvidence(
                    domain=domain,
                    reason_code="payload_rejected",
                    message=reason,
                )
            )
            llm_eligibility.append(_blocked_llm(domain, reason))
            continue

        section = normalized["section"]
        sections[domain] = section
        rows.extend(normalized["rows"])
        metrics.extend(normalized["metrics"])
        trends.extend(normalized["trends"])
        anomalies.extend(normalized["anomalies"])
        similarities.extend(normalized["similarities"])
        confidence.extend(normalized["confidence"])
        if section.availability_status == EvidenceAvailabilityStatus.STALE:
            stale.append(
                StaleEvidence(
                    domain=domain,
                    reason_code="payload_stale",
                    message=f"{domain.value} deterministic payload is stale.",
                    as_of=section.freshness.as_of,
                )
            )
            llm_eligibility.append(_blocked_llm(domain, "Stale evidence cannot be explained as current fact."))
            continue

        visualizations.extend(normalized["visualizations"])
        if section.availability_status == EvidenceAvailabilityStatus.PRESENT:
            llm_eligibility.append(
                LLMExplanationEligibility(
                    domain=domain,
                    status=LLMExplanationStatus.ALLOWED,
                    source_evidence_ids=section.evidence_ids,
                    reason="LLM may explain existing deterministic evidence only.",
                )
            )
        else:
            llm_eligibility.append(_blocked_llm(domain, "Evidence is not present."))

    return _assemble_contract(
        selected_scope=selected_scope,
        sections=sections,
        rows=tuple(rows),
        metrics=tuple(metrics),
        trends=tuple(trends),
        anomalies=tuple(anomalies),
        similarities=tuple(similarities),
        confidence=tuple(confidence),
        missing=tuple(missing),
        unavailable=tuple(unavailable),
        stale=tuple(stale),
        visualizations=tuple(visualizations),
        llm_eligibility=tuple(llm_eligibility),
        provenance=pack_provenance,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _domain_eligible(selected_scope: SelectedReviewScopeContract, domain: EvidenceDomain) -> bool:
    if domain == EvidenceDomain.DIAGNOSTIC:
        return is_diagnostic_snapshot_eligible(selected_scope)
    if domain == EvidenceDomain.HISTORICAL:
        return is_historical_review_eligible(selected_scope)
    if domain == EvidenceDomain.COMPARATIVE:
        return is_comparative_review_eligible(selected_scope)
    if domain == EvidenceDomain.DEEP_ANALYSIS:
        return is_deep_analysis_eligible(selected_scope)
    if domain in {EvidenceDomain.RECOMMENDATION_ACTION, EvidenceDomain.LEARNING_GOVERNANCE}:
        return is_diagnostic_snapshot_eligible(selected_scope)
    return False


def _normalize_payload(
    domain: EvidenceDomain,
    payload: Mapping[str, Any],
    default_provenance: EvidenceProvenance,
) -> dict[str, Any]:
    forbidden_categories = detect_forbidden_authority_keys(payload)
    errors = tuple(
        EvidenceIssue(
            code="non_authoritative_payload_rejected",
            message="Payload contains non-authoritative browser, generated HTML, UI, chart markup, or LLM evidence.",
            domain=domain,
            severity=EvidenceSeverity.ERROR,
        )
        for _category in forbidden_categories
    )
    if errors:
        return {
            "section": _empty_section(domain, EvidenceAvailabilityStatus.UNAVAILABLE),
            "rows": (),
            "metrics": (),
            "trends": (),
            "anomalies": (),
            "similarities": (),
            "confidence": (),
            "visualizations": (),
            "errors": errors,
            "warnings": (),
        }

    rows = tuple(EvidenceRow.from_value(row, domain) for row in _payload_sequence(payload.get("rows")))
    metrics = tuple(MetricSummary.from_value(item, domain) for item in _metric_sequence(payload.get("metrics")))
    trends = tuple(TrendSummary.from_value(item, domain) for item in _payload_sequence(payload.get("trends")))
    anomalies = tuple(AnomalySummary.from_value(item, domain) for item in _payload_sequence(payload.get("anomalies")))
    similarities = tuple(
        SimilarityContext.from_value(item, domain) for item in _payload_sequence(payload.get("similarity_context"))
    )
    confidence = tuple(
        ConfidenceBasis.from_value(item, domain) for item in _payload_sequence(payload.get("confidence_basis"))
    )

    evidence_ids = _evidence_ids_for_payload(domain, payload, rows, metrics, trends, anomalies)
    freshness = EvidenceFreshness.from_value(payload.get("freshness"))
    if str(payload.get("freshness_status") or "").lower() == "stale" or payload.get("stale") is True:
        freshness = EvidenceFreshness(
            status=EvidenceAvailabilityStatus.STALE,
            as_of=freshness.as_of,
            reason=freshness.reason or "Payload marked stale.",
        )
    has_deterministic_content = bool(
        evidence_ids or rows or metrics or trends or anomalies or similarities or confidence
    )
    status = EvidenceAvailabilityStatus.PRESENT if has_deterministic_content else EvidenceAvailabilityStatus.MISSING
    if freshness.status == EvidenceAvailabilityStatus.STALE:
        status = EvidenceAvailabilityStatus.STALE

    section = _section(
        domain=domain,
        status=status,
        evidence_ids=evidence_ids,
        rows=rows,
        summary=str(payload.get("summary")) if payload.get("summary") is not None else None,
        freshness=freshness,
        provenance=EvidenceProvenance.from_value(payload.get("provenance")) if payload.get("provenance") else default_provenance,
    )
    visualizations = ()
    if status == EvidenceAvailabilityStatus.PRESENT:
        visualizations = _visualizations_for_payload(domain, payload, section, rows, metrics, trends)

    return {
        "section": section,
        "rows": rows,
        "metrics": metrics,
        "trends": trends,
        "anomalies": anomalies,
        "similarities": similarities,
        "confidence": confidence,
        "visualizations": visualizations,
        "errors": (),
        "warnings": (),
    }


def _assemble_contract(
    *,
    selected_scope: SelectedReviewScopeContract,
    sections: Mapping[EvidenceDomain, Any],
    rows: Sequence[EvidenceRow],
    metrics: Sequence[MetricSummary],
    trends: Sequence[TrendSummary],
    anomalies: Sequence[AnomalySummary],
    similarities: Sequence[SimilarityContext],
    confidence: Sequence[ConfidenceBasis],
    missing: Sequence[MissingEvidence],
    unavailable: Sequence[UnavailableEvidence],
    stale: Sequence[StaleEvidence],
    visualizations: Sequence[AllowedVisualization],
    llm_eligibility: Sequence[LLMExplanationEligibility],
    provenance: EvidenceProvenance,
    errors: Sequence[EvidenceIssue],
    warnings: Sequence[EvidenceIssue],
) -> EvidencePackContract:
    diagnostic = sections.get(EvidenceDomain.DIAGNOSTIC) or DiagnosticEvidence()
    historical = sections.get(EvidenceDomain.HISTORICAL) or HistoricalEvidence()
    comparative = sections.get(EvidenceDomain.COMPARATIVE) or ComparativeEvidence()
    deep = sections.get(EvidenceDomain.DEEP_ANALYSIS) or DeepAnalysisEvidence()
    action = sections.get(EvidenceDomain.RECOMMENDATION_ACTION) or RecommendationActionEvidence()
    learning = sections.get(EvidenceDomain.LEARNING_GOVERNANCE) or LearningGovernanceEvidence()
    evidence_pack_id = compute_evidence_pack_id(
        selected_flow_id=selected_scope.selected_flow_id,
        source_selected_review_scope_id=selected_scope.selected_flow_id,
        selected_scope_validation_status=selected_scope.validation_status,
        diagnostic_evidence=diagnostic,
        historical_evidence=historical,
        comparative_evidence=comparative,
        deep_analysis_evidence=deep,
        recommendation_action_evidence=action,
        learning_governance_evidence=learning,
        evidence_rows=rows,
        metric_summaries=metrics,
        trend_summaries=trends,
        anomaly_summaries=anomalies,
        similarity_context=similarities,
        confidence_basis=confidence,
        missing_evidence=missing,
        unavailable_evidence=unavailable,
        stale_evidence=stale,
        allowed_visualizations=visualizations,
        llm_explanation_eligibility=llm_eligibility,
    )
    contract = EvidencePackContract(
        contract_type=CONTRACT_TYPE,
        contract_version=CONTRACT_VERSION,
        evidence_pack_id=evidence_pack_id,
        selected_flow_id=selected_scope.selected_flow_id,
        source_selected_review_scope_id=selected_scope.selected_flow_id,
        source_selected_review_scope_contract_type=selected_scope.contract_type,
        selected_scope_validation_status=selected_scope.validation_status,
        diagnostic_evidence=diagnostic,
        historical_evidence=historical,
        comparative_evidence=comparative,
        deep_analysis_evidence=deep,
        recommendation_action_evidence=action,
        learning_governance_evidence=learning,
        evidence_rows=tuple(rows),
        metric_summaries=tuple(metrics),
        trend_summaries=tuple(trends),
        anomaly_summaries=tuple(anomalies),
        similarity_context=tuple(similarities),
        confidence_basis=tuple(confidence),
        missing_evidence=tuple(missing),
        unavailable_evidence=tuple(unavailable),
        stale_evidence=tuple(stale),
        allowed_visualizations=tuple(visualizations),
        llm_explanation_eligibility=tuple(llm_eligibility),
        provenance=provenance,
        validation_status=EvidencePackValidationStatus.INVALID,
        validation_errors=tuple(errors),
        warnings=tuple(warnings),
    )
    return validate_evidence_pack_contract(contract)


def _section(
    *,
    domain: EvidenceDomain,
    status: EvidenceAvailabilityStatus,
    evidence_ids: Sequence[str] = (),
    rows: Sequence[EvidenceRow] = (),
    summary: str | None = None,
    freshness: EvidenceFreshness | None = None,
    provenance: EvidenceProvenance | None = None,
) -> Any:
    section_kwargs = {
        "availability_status": status,
        "evidence_ids": tuple(evidence_ids),
        "rows": tuple(rows),
        "summary": summary,
        "freshness": freshness or EvidenceFreshness(status=status),
        "provenance": provenance or EvidenceProvenance(),
    }
    if domain == EvidenceDomain.DIAGNOSTIC:
        return DiagnosticEvidence(**section_kwargs)
    if domain == EvidenceDomain.HISTORICAL:
        return HistoricalEvidence(**section_kwargs)
    if domain == EvidenceDomain.COMPARATIVE:
        return ComparativeEvidence(**section_kwargs)
    if domain == EvidenceDomain.DEEP_ANALYSIS:
        return DeepAnalysisEvidence(**section_kwargs)
    if domain == EvidenceDomain.RECOMMENDATION_ACTION:
        return RecommendationActionEvidence(**section_kwargs)
    return LearningGovernanceEvidence(**section_kwargs)


def _empty_section(domain: EvidenceDomain, status: EvidenceAvailabilityStatus) -> Any:
    return _section(domain=domain, status=status)


def _payload_sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str, Mapping)):
        return tuple(value)
    return (value,)


def _metric_sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Mapping):
        return tuple({"metric_name": key, "value": metric_value} for key, metric_value in sorted(value.items()))
    return _payload_sequence(value)


def _evidence_ids_for_payload(
    domain: EvidenceDomain,
    payload: Mapping[str, Any],
    rows: Sequence[EvidenceRow],
    metrics: Sequence[MetricSummary],
    trends: Sequence[TrendSummary],
    anomalies: Sequence[AnomalySummary],
) -> tuple[str, ...]:
    explicit = tuple(str(item) for item in _payload_sequence(payload.get("evidence_ids")) if item)
    if explicit:
        return explicit
    if rows:
        return tuple(row.row_id for row in rows)
    source_payload = {
        "domain": domain.value,
        "metrics": [metric.to_dict() for metric in metrics],
        "trends": [trend.to_dict() for trend in trends],
        "anomalies": [anomaly.to_dict() for anomaly in anomalies],
        "summary": payload.get("summary"),
    }
    if any(source_payload[key] for key in ("metrics", "trends", "anomalies", "summary")):
        return (f"{domain.value}:{_digest(source_payload)}",)
    return ()


def _visualizations_for_payload(
    domain: EvidenceDomain,
    payload: Mapping[str, Any],
    section: Any,
    rows: Sequence[EvidenceRow],
    metrics: Sequence[MetricSummary],
    trends: Sequence[TrendSummary],
) -> tuple[AllowedVisualization, ...]:
    requested = _payload_sequence(payload.get("visualizations"))
    visualizations: list[AllowedVisualization] = []
    if requested:
        for item in requested:
            if not isinstance(item, Mapping):
                continue
            sources = tuple(str(source) for source in item.get("source_evidence_ids", section.evidence_ids))
            if not sources or not set(sources).issubset(set(section.evidence_ids)):
                continue
            visualizations.append(
                AllowedVisualization(
                    visualization_id=str(item.get("visualization_id") or item.get("id") or _visual_id(domain, item)),
                    domain=domain,
                    kind=_visualization_kind(item.get("kind"), domain),
                    source_evidence_ids=sources,
                    title=str(item.get("title")) if item.get("title") else None,
                )
            )
        return tuple(visualizations)

    if rows:
        visualizations.append(
            AllowedVisualization(
                visualization_id=_visual_id(domain, {"kind": "table", "sources": section.evidence_ids}),
                domain=domain,
                kind=VisualizationKind.TABLE,
                source_evidence_ids=section.evidence_ids,
                title=f"{domain.value} evidence table",
            )
        )
    if metrics:
        visualizations.append(
            AllowedVisualization(
                visualization_id=_visual_id(domain, {"kind": "scalar", "sources": section.evidence_ids}),
                domain=domain,
                kind=VisualizationKind.COMPARISON_DELTA
                if domain == EvidenceDomain.COMPARATIVE
                else VisualizationKind.SCALAR,
                source_evidence_ids=section.evidence_ids,
                title=f"{domain.value} metric summary",
            )
        )
    if trends:
        visualizations.append(
            AllowedVisualization(
                visualization_id=_visual_id(domain, {"kind": "trend", "sources": section.evidence_ids}),
                domain=domain,
                kind=VisualizationKind.TREND,
                source_evidence_ids=section.evidence_ids,
                title=f"{domain.value} trend",
            )
        )
    return tuple(visualizations)


def _visualization_kind(value: Any, domain: EvidenceDomain) -> VisualizationKind:
    if isinstance(value, VisualizationKind):
        return value
    text = str(value or "").strip().lower()
    for item in VisualizationKind:
        if text in {item.value, item.name.lower()}:
            return item
    if domain == EvidenceDomain.COMPARATIVE:
        return VisualizationKind.COMPARISON_DELTA
    return VisualizationKind.TABLE


def _blocked_llm(domain: EvidenceDomain, reason: str) -> LLMExplanationEligibility:
    return LLMExplanationEligibility(
        domain=domain,
        status=LLMExplanationStatus.BLOCKED,
        source_evidence_ids=(),
        reason=reason,
    )


def _unavailable_message(selected_scope: SelectedReviewScopeContract, domain: EvidenceDomain) -> str:
    if domain in {EvidenceDomain.RECOMMENDATION_ACTION, EvidenceDomain.LEARNING_GOVERNANCE}:
        return "Selected scope is not eligible for downstream deterministic evidence."
    reasons = unavailable_reasons_for(selected_scope, DOMAIN_MODE[domain])
    if reasons:
        return "; ".join(reason.message for reason in reasons)
    return f"{domain.value} evidence is unavailable for selected scope."


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()[:16]


def _visual_id(domain: EvidenceDomain, payload: Any) -> str:
    return f"visual:{domain.value}:{_digest(payload)}"

