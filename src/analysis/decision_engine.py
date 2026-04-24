from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models.decision import AwrDecision, DecisionInput

DOMAIN_ORDER = ("CPU", "IO", "MEMORY", "COMMIT", "RAC", "ADG")
PRIMARY_QUALIFICATION_THRESHOLD = 11.0
SECONDARY_QUALIFICATION_THRESHOLD = 6.1
SECONDARY_RELATIVE_THRESHOLD = 0.25
SECONDARY_RELATIVE_CEILING = 0.50
SECONDARY_ONLY_THRESHOLD = 3.5
PRIMARY_MIN_SEVERITY_THRESHOLD = 21.55
PRIMARY_DOMINANCE_MARGIN = 4.5
PRIMARY_TIE_TOLERANCE = 0.5
PRIMARY_TERTIARY_SUPPRESSION_THRESHOLD = 5.0
OK_STATUS_THRESHOLD = 25.0
WARNING_STATUS_THRESHOLD = 75.0
ANOMALY_SEVERITY_WEIGHT = {
    "LOW": 0.03,
    "MEDIUM": 0.06,
    "HIGH": 0.10,
}

ANOMALY_DOMAIN_MAP = {
    "DB_CPU_PCT_DB_TIME": "CPU",
    "CPU_UTIL_P95": "CPU",
    "DB_CPU_PER_SEC": "CPU",
    "TOP_SQL_LOAD_CONCENTRATION": "CPU",
    "READ_LATENCY_MS": "IO",
    "WRITE_LATENCY_MS": "IO",
    "TEMP_WRITE_LATENCY_MS": "IO",
    "CELL_SINGLE_BLOCK_LATENCY_MS": "IO",
    "CELL_MULTIBLOCK_LATENCY_MS": "IO",
    "USER_IO_PRESSURE": "IO",
    "TEMP_IO_PRESSURE": "IO",
    "PGA_SPILL_PRESSURE": "MEMORY",
    "PGA_CACHE_HIT_PCT": "MEMORY",
    "TEMP_SPILL_PCT": "MEMORY",
    "SORTS_DISK_PCT": "MEMORY",
    "WORKAREA_ONEPASS_PCT": "MEMORY",
    "WORKAREA_MULTIPASS_PCT": "MEMORY",
    "HARD_PARSE_PCT": "MEMORY",
    "HARD_PARSES_PER_SEC": "MEMORY",
    "LOG_FILE_SYNC_MS": "COMMIT",
    "LOG_WRITE_LATENCY_MS": "COMMIT",
    "COMMIT_PRESSURE": "COMMIT",
    "CLUSTER_WAIT_PCT_DB_TIME": "RAC",
    "GC_CR_WAIT_PCT_DB_TIME": "RAC",
    "GC_CURRENT_WAIT_PCT_DB_TIME": "RAC",
    "GC_BUFFER_BUSY_PCT_DB_TIME": "RAC",
    "INTERCONNECT_STRESS_FLAG": "RAC",
    "RAC_CONTENTION_FLAG": "RAC",
    "TRANSPORT_LAG_SEC": "ADG",
    "APPLY_LAG_SEC": "ADG",
    "REDO_TRANSPORT_ISSUE_FLAG": "ADG",
    "POST_FAILOVER_RECOVERY_FLAG": "ADG",
    "ROLE_TRANSITION_FLAG": "ADG",
    "FAILOVER_EVENT_FLAG": "ADG",
}


@dataclass(slots=True)
class DomainEvidence:
    score: float = 0.0
    score_components: dict[str, float] = field(default_factory=dict)
    anomalies: list[dict[str, Any]] = field(default_factory=list)
    anomaly_score_total: float = 0.0
    reasons: list[str] = field(default_factory=list)


def build_decision(
    decision_input: DecisionInput,
    include_diagnostics: bool = False,
) -> AwrDecision:
    domain_evidence = _build_domain_evidence(decision_input)
    ranked_domains, ordered_candidates = _rank_domains(domain_evidence)
    primary_issue = _select_primary_issue(
        decision_input,
        domain_evidence,
        ranked_domains,
    )
    secondary_issues = _select_secondary_issues(
        domain_evidence=domain_evidence,
        ranked_domains=ranked_domains,
        primary_issue=primary_issue,
        decision_input=decision_input,
    )
    tie_break_applied, tie_break_reason = _compute_meaningful_tie_break(
        ordered_candidates=ordered_candidates,
        primary_issue=primary_issue,
        secondary_issues=secondary_issues,
    )
    severity_score = _derive_severity_score(
        decision_input=decision_input,
        domain_evidence=domain_evidence,
        primary_issue=primary_issue,
        secondary_issues=secondary_issues,
    )
    overall_status = _status_from_severity(severity_score)
    confidence = _derive_confidence(
        decision_input=decision_input,
        domain_evidence=domain_evidence,
        ranked_domains=ranked_domains,
        primary_issue=primary_issue,
    )

    evidence: dict[str, Any] = {
        "domain_scores": {
            domain: round(domain_evidence[domain].score, 4) for domain in DOMAIN_ORDER
        },
        "primary_reasons": list(domain_evidence[primary_issue].reasons)
        if primary_issue
        else [],
        "feature_evidence": decision_input.feature_evidence or {},
        "trend_rows": list(decision_input.trend_rows or []),
        "anomaly_signals": list(decision_input.anomaly_signals or []),
        "anomaly_evidence": {
            domain: list(domain_evidence[domain].anomalies)
            for domain in DOMAIN_ORDER
            if domain_evidence[domain].anomalies
        },
        "score_evidence": decision_input.score_evidence or {},
    }
    if include_diagnostics:
        evidence["decision_diagnostics"] = _build_decision_diagnostics(
            domain_evidence=domain_evidence,
            decision_input=decision_input,
            ranked_domains=ranked_domains,
            ordered_candidates=ordered_candidates,
            primary_issue=primary_issue,
            secondary_issues=secondary_issues,
            tie_break_applied=tie_break_applied,
            tie_break_reason=tie_break_reason,
        )

    return AwrDecision(
        awr_id=decision_input.awr_id,
        overall_status=overall_status,
        primary_issue=primary_issue,
        secondary_issues=secondary_issues,
        severity_score=severity_score,
        confidence=confidence,
        evidence=evidence,
    )


def _build_domain_evidence(decision_input: DecisionInput) -> dict[str, DomainEvidence]:
    evidence = {domain: DomainEvidence() for domain in DOMAIN_ORDER}
    for domain in DOMAIN_ORDER:
        score = max(_safe_float(decision_input.canonical_domain_scores.get(domain)) or 0.0, 0.0)
        evidence[domain].score = round(score, 4)
        if score > 0.0:
            evidence[domain].score_components["upstream_score"] = round(score, 4)
            evidence[domain].reasons.append(
                f"Authoritative upstream scoring contributed {score:.4f}."
            )
    _apply_anomalies(evidence, decision_input.anomaly_signals or [])
    return evidence


def _apply_anomalies(
    evidence: dict[str, DomainEvidence],
    anomalies: list[dict[str, Any]],
) -> None:
    for anomaly in anomalies:
        if str(anomaly.get("anomaly_flag") or "").upper() != "Y":
            continue
        metric_name = str(anomaly.get("metric_name") or "").strip()
        domain = _resolve_anomaly_domain(anomaly, metric_name)
        if domain is None:
            continue
        anomaly_score = str(anomaly.get("anomaly_score") or "LOW").upper()
        score_delta = _coerce_anomaly_score_delta(anomaly)
        anomaly_record = {
            "metric_name": metric_name,
            "anomaly_type": anomaly.get("anomaly_type"),
            "anomaly_score": anomaly_score,
            "metric_value_num": _safe_float(anomaly.get("metric_value_num")),
            "score_delta": round(score_delta, 4) if score_delta else 0.0,
        }
        evidence[domain].anomalies.append(anomaly_record)
        if score_delta is None:
            evidence[domain].reasons.append(
                f"Trend/anomaly evidence was recorded for {metric_name}."
            )
            continue
        applied_delta = max(score_delta, 0.0)
        evidence[domain].score += applied_delta
        evidence[domain].anomaly_score_total += applied_delta
        evidence[domain].score_components["anomaly_support"] = round(
            evidence[domain].anomaly_score_total,
            4,
        )
        evidence[domain].reasons.append(
            f"Trend/anomaly delta contributed {applied_delta:.4f} from {metric_name}."
        )


def _resolve_anomaly_domain(
    anomaly: dict[str, Any],
    metric_name: str,
) -> str | None:
    explicit_domain = _normalize_domain_key(
        anomaly.get("canonical_domain") or anomaly.get("domain")
    )
    if explicit_domain is not None:
        return explicit_domain
    return ANOMALY_DOMAIN_MAP.get(metric_name)


def _coerce_anomaly_score_delta(anomaly: dict[str, Any]) -> float | None:
    for key in ("domain_score_delta", "decision_score_delta"):
        numeric_value = _safe_float(anomaly.get(key))
        if numeric_value is not None:
            return numeric_value
    anomaly_score = str(anomaly.get("anomaly_score") or "").upper()
    if anomaly_score and anomaly.get("domain_score_delta") is None and anomaly.get("decision_score_delta") is None:
        return None
    return None


def _rank_domains(
    domain_evidence: dict[str, DomainEvidence],
) -> tuple[list[str], list[dict[str, Any]]]:
    domain_scores = {
        domain: round(domain_evidence[domain].score, 4) for domain in DOMAIN_ORDER
    }
    grouped_candidates: list[dict[str, Any]] = []
    seen_scores: list[float] = []
    for domain in DOMAIN_ORDER:
        score = domain_scores[domain]
        if score in seen_scores:
            continue
        seen_scores.append(score)
        grouped_candidates.append(
            {
                "score": score,
                "domains": [
                    candidate_domain
                    for candidate_domain in DOMAIN_ORDER
                    if domain_scores[candidate_domain] == score
                ],
            }
        )
    grouped_candidates.sort(key=lambda item: item["score"], reverse=True)
    ranked_domains = sorted(
        DOMAIN_ORDER,
        key=lambda domain: (-domain_scores[domain], DOMAIN_ORDER.index(domain)),
    )
    return ranked_domains, grouped_candidates


def _select_primary_issue(
    decision_input: DecisionInput,
    domain_evidence: dict[str, DomainEvidence],
    ranked_domains: list[str],
) -> str | None:
    qualifying_domains = [
        domain
        for domain in ranked_domains
        if _qualified_for_primary(domain_evidence[domain], decision_input)
    ]
    if not qualifying_domains:
        return None

    top_domain = qualifying_domains[0]
    top_score = domain_evidence[top_domain].score
    runner_up_score = (
        domain_evidence[ranked_domains[1]].score
        if len(ranked_domains) > 1
        else 0.0
    )
    tertiary_score = (
        domain_evidence[ranked_domains[2]].score
        if len(ranked_domains) > 2
        else 0.0
    )
    gap = top_score - runner_up_score

    if gap <= PRIMARY_TIE_TOLERANCE:
        if tertiary_score > PRIMARY_TERTIARY_SUPPRESSION_THRESHOLD:
            return None
        tied_domains = [
            domain
            for domain in qualifying_domains
            if (top_score - domain_evidence[domain].score) <= PRIMARY_TIE_TOLERANCE
        ]
        return sorted(tied_domains, key=DOMAIN_ORDER.index)[0]

    if gap < PRIMARY_DOMINANCE_MARGIN:
        return None
    return top_domain


def _select_secondary_issues(
    domain_evidence: dict[str, DomainEvidence],
    ranked_domains: list[str],
    primary_issue: str | None,
    decision_input: DecisionInput,
) -> list[str]:
    secondary_issues: list[str] = []
    primary_score = domain_evidence[primary_issue].score if primary_issue else None
    if primary_issue is None:
        ambiguous_secondaries = _select_ambiguous_no_primary_secondaries(
            decision_input=decision_input,
            domain_evidence=domain_evidence,
            ranked_domains=ranked_domains,
        )
        if ambiguous_secondaries is not None:
            return ambiguous_secondaries
        for domain in DOMAIN_ORDER:
            if not _qualified_for_secondary_only(domain_evidence[domain]):
                continue
            secondary_issues.append(domain)
        return secondary_issues

    for domain in DOMAIN_ORDER:
        if domain == primary_issue:
            continue
        if not _qualified_for_secondary(domain_evidence[domain], primary_score):
            continue
        secondary_issues.append(domain)
    return secondary_issues


def _select_ambiguous_no_primary_secondaries(
    decision_input: DecisionInput,
    domain_evidence: dict[str, DomainEvidence],
    ranked_domains: list[str],
) -> list[str] | None:
    qualifying_domains = [
        domain
        for domain in ranked_domains
        if _qualified_for_primary(domain_evidence[domain], decision_input)
    ]
    if not qualifying_domains:
        top_domain = ranked_domains[0]
        top_score = domain_evidence[top_domain].score
        runner_up_score = (
            domain_evidence[ranked_domains[1]].score if len(ranked_domains) > 1 else 0.0
        )
        if top_score >= PRIMARY_QUALIFICATION_THRESHOLD and (
            top_score - runner_up_score
        ) < PRIMARY_DOMINANCE_MARGIN:
            return [top_domain]
        return None

    top_domain = qualifying_domains[0]
    top_score = domain_evidence[top_domain].score
    runner_up_score = (
        domain_evidence[ranked_domains[1]].score if len(ranked_domains) > 1 else 0.0
    )
    gap = top_score - runner_up_score
    if gap <= PRIMARY_TIE_TOLERANCE:
        tied_domains = [
            domain
            for domain in ranked_domains
            if (top_score - domain_evidence[domain].score) <= PRIMARY_TIE_TOLERANCE
            and _qualified_for_primary(domain_evidence[domain], decision_input)
        ]
        if tied_domains:
            return [sorted(tied_domains, key=DOMAIN_ORDER.index)[0]]
    if gap < PRIMARY_DOMINANCE_MARGIN:
        return [top_domain]
    return None


def _qualified_for_primary(
    domain_evidence: DomainEvidence,
    decision_input: DecisionInput,
) -> bool:
    if domain_evidence.score < PRIMARY_QUALIFICATION_THRESHOLD:
        return False
    if (decision_input.severity_input or 0.0) < PRIMARY_MIN_SEVERITY_THRESHOLD:
        return False
    return _support_count(domain_evidence) >= 1


def _qualified_for_secondary(
    domain_evidence: DomainEvidence,
    primary_score: float | None,
) -> bool:
    if domain_evidence.score < SECONDARY_QUALIFICATION_THRESHOLD:
        return False
    if primary_score is not None and domain_evidence.score < (primary_score * SECONDARY_RELATIVE_THRESHOLD):
        return False
    if primary_score is not None and domain_evidence.score > (primary_score * SECONDARY_RELATIVE_CEILING):
        return False
    return _support_count(domain_evidence) >= 1


def _qualified_for_secondary_only(domain_evidence: DomainEvidence) -> bool:
    if domain_evidence.score < SECONDARY_ONLY_THRESHOLD:
        return False
    return _support_count(domain_evidence) >= 1


def _support_count(domain_evidence: DomainEvidence) -> int:
    return int(bool(domain_evidence.score_components.get("upstream_score"))) + int(
        bool(domain_evidence.anomalies)
    )


def _compute_meaningful_tie_break(
    ordered_candidates: list[dict[str, Any]],
    primary_issue: str | None,
    secondary_issues: list[str],
) -> tuple[bool, str | None]:
    meaningful_domains = set(secondary_issues)
    if primary_issue is not None:
        meaningful_domains.add(primary_issue)
    for group in ordered_candidates:
        tied_meaningful = [domain for domain in group["domains"] if domain in meaningful_domains]
        if len(tied_meaningful) >= 2:
            return (
                True,
                "Equal qualifying adjusted scores were resolved using locked domain order: "
                + " > ".join(DOMAIN_ORDER),
            )
    return False, None


def _build_decision_diagnostics(
    domain_evidence: dict[str, DomainEvidence],
    decision_input: DecisionInput,
    ranked_domains: list[str],
    ordered_candidates: list[dict[str, Any]],
    primary_issue: str | None,
    secondary_issues: list[str],
    tie_break_applied: bool,
    tie_break_reason: str | None,
) -> dict[str, Any]:
    domain_scores = {
        domain: round(domain_evidence[domain].score, 4) for domain in DOMAIN_ORDER
    }
    primary_score = domain_evidence[primary_issue].score if primary_issue else None
    return {
        "domain_diagnostics": {
            domain: {
                "score": domain_scores[domain],
                "qualified_for_primary": _qualified_for_primary(
                    domain_evidence[domain],
                    decision_input,
                ),
                "qualified_for_secondary": _qualified_for_secondary(
                    domain_evidence[domain],
                    primary_score,
                ),
            }
            for domain in DOMAIN_ORDER
        },
        "ordered_candidates_pre_tiebreak": ordered_candidates,
        "final_ranked_domains": list(ranked_domains),
        "tie_break_applied": tie_break_applied,
        "tie_break_reason": tie_break_reason,
    }


def _derive_severity_score(
    decision_input: DecisionInput,
    domain_evidence: dict[str, DomainEvidence],
    primary_issue: str | None,
    secondary_issues: list[str],
) -> float:
    del domain_evidence, primary_issue, secondary_issues
    return round(max(min(decision_input.severity_input or 0.0, 100.0), 0.0), 2)


def _status_from_severity(severity_score: float) -> str:
    if severity_score >= WARNING_STATUS_THRESHOLD:
        return "CRITICAL"
    if severity_score >= OK_STATUS_THRESHOLD:
        return "WARNING"
    return "OK"


def _derive_confidence(
    decision_input: DecisionInput,
    domain_evidence: dict[str, DomainEvidence],
    ranked_domains: list[str],
    primary_issue: str | None,
) -> float:
    top_domain = ranked_domains[0]
    top_score = domain_evidence[top_domain].score
    runner_up_score = (
        domain_evidence[ranked_domains[1]].score if len(ranked_domains) > 1 else 0.0
    )
    margin = max(top_score - runner_up_score, 0.0)
    consistency_bonus = 0.0
    if primary_issue is not None and decision_input.primary_signal_domain == primary_issue:
        consistency_bonus = 0.10
    elif primary_issue is None and decision_input.primary_signal_domain is None:
        consistency_bonus = 0.06
    base_confidence = decision_input.confidence_input
    if base_confidence is None:
        base_confidence = 0.35
    completeness = decision_input.completeness or 0.0
    top_strength = _clamp(top_score / 25.0, 0.0, 1.0)
    margin_strength = _clamp(margin / PRIMARY_DOMINANCE_MARGIN, 0.0, 1.0)
    support_strength = _clamp(
        sum(_support_count(domain_evidence[domain]) for domain in DOMAIN_ORDER) / 6.0,
        0.0,
        1.0,
    )
    derived_confidence = (
        (0.45 * _clamp(base_confidence, 0.0, 1.0))
        + (0.20 * top_strength)
        + (0.10 * margin_strength)
        + (0.10 * _clamp(completeness, 0.0, 1.0))
        + (0.05 * support_strength)
        + consistency_bonus
    )
    return round(_clamp(derived_confidence, 0.0, 1.0), 4)


def _normalize_domain_key(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().upper()
    if normalized in DOMAIN_ORDER:
        return normalized
    return None


def _safe_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").strip())
        except ValueError:
            return None
    return None


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
