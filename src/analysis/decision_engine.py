from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models.decision import AwrDecision, DecisionInput

DOMAIN_ORDER = ("CPU", "IO", "MEMORY", "COMMIT", "RAC", "ADG")
PRIMARY_QUALIFICATION_THRESHOLD = 7.0
SECONDARY_QUALIFICATION_THRESHOLD = 5.0
SECONDARY_RELATIVE_THRESHOLD = 0.25
SECONDARY_RELATIVE_CEILING = 0.70
MATERIAL_RUNNER_UP_SECONDARY_RATIO = 0.70
SECONDARY_ONLY_THRESHOLD = 3.5
TOPOLOGY_EVIDENCE_SECONDARY_SCORE_FLOOR = 0.5
NO_PRIMARY_MAX_SECONDARIES = 2
NO_PRIMARY_EXCLUDED_TOP_RELATIVE_THRESHOLD = 0.5
PRIMARY_MIN_SEVERITY_THRESHOLD = 13.0
PRIMARY_DOMINANCE_MARGIN = 5.0
PRIMARY_TIE_TOLERANCE = 0.3
PRIMARY_TERTIARY_SUPPRESSION_THRESHOLD = 5.0
PRIMARY_MATERIALITY_FLOOR = 17.0
LOW_SEVERITY_PRIMARY_THRESHOLD = 18.0
LOW_SEVERITY_PRIMARY_MIN_SCORE_SHARE = 0.87
LOW_ACTIVITY_PRIMARY_MAX_DB_TIME_PER_SEC = 1.0
ACTIVITY_SUPPORTED_PRIMARY_MIN_DB_TIME_PER_SEC = 3.1
ACTIVITY_SUPPORTED_PRIMARY_MIN_DB_TIME_PER_TXN = 0.02
ACTIVITY_SUPPORTED_PRIMARY_MAX_BREADTH = 3
ACTIVITY_SUPPORTED_PRIMARY_MIN_GAP = 0.25
LOW_ACTIVITY_NO_PRIMARY_MAX_DB_TIME_PER_SEC = 1.0
LOW_ACTIVITY_NO_PRIMARY_EXCLUSION_MAX_GAP = 1.5
LOW_ACTIVITY_DIFFUSE_MAX_DB_TIME_PER_SEC = 3.0
LOW_ACTIVITY_DIFFUSE_MIN_TOP_SCORE = 7.0
LOW_ACTIVITY_DIFFUSE_MIN_RUNNER_UP_SCORE = 4.0
LOW_PRIMARY_SECONDARY_SCORE_THRESHOLD = 10.0
LOW_PRIMARY_SECONDARY_GAP_ALLOWANCE = 4.0
CLOSE_SECONDARY_GAP_ALLOWANCE = 1.0
CPU_BASELINE_SECONDARY_MIN_PCT = 35.0
CPU_BASELINE_SECONDARY_MIN_AAS_PER_CPU = 1.0
PRIMARY_MIN_SHARE = 0.65
PRIMARY_HIGH_SCORE_SHARE_THRESHOLD = 20.0
PRIMARY_HIGH_SCORE_MIN_SHARE = 0.54
SECONDARY_ONLY_DOMINANCE_MARGIN = 2.5
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
        top_domain = ranked_domains[0] if ranked_domains else None
        if top_domain and _activity_supported_primary_override(
            top_domain,
            decision_input,
            domain_evidence,
            ranked_domains,
        ):
            return top_domain
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
        del tertiary_score
        return None

    if gap < PRIMARY_DOMINANCE_MARGIN:
        if _activity_supported_primary_override(
            top_domain,
            decision_input,
            domain_evidence,
            ranked_domains,
        ):
            return top_domain
        return None

    if _top_score_share(domain_evidence, ranked_domains) < _primary_min_share(top_score):
        if _activity_supported_primary_override(
            top_domain,
            decision_input,
            domain_evidence,
            ranked_domains,
        ):
            return top_domain
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
        excluded_top_domain = _excluded_low_activity_top_domain(
            decision_input=decision_input,
            domain_evidence=domain_evidence,
            ranked_domains=ranked_domains,
        )
        secondary_only_candidates = [
            domain
            for domain in ranked_domains
            if domain != excluded_top_domain
            and _qualified_for_secondary_only(domain_evidence[domain])
        ]
        secondary_only_candidates = _filter_evidence_backed_secondary_candidates(
            secondary_only_candidates,
            domain_evidence=domain_evidence,
            decision_input=decision_input,
            top_domain=(ranked_domains[0] if ranked_domains else None),
            no_primary_context=True,
        )
        if _uses_single_follow_on_secondary(
            decision_input=decision_input,
            domain_evidence=domain_evidence,
            ranked_domains=ranked_domains,
            excluded_top_domain=excluded_top_domain,
        ):
            return secondary_only_candidates[:1]
        return _limit_no_primary_secondaries(
            secondary_only_candidates,
            domain_evidence,
        )

    material_runner_up_domain = _material_runner_up_secondary_candidate(
        primary_issue=primary_issue,
        ranked_domains=ranked_domains,
        domain_evidence=domain_evidence,
    )

    for domain in DOMAIN_ORDER:
        if domain == primary_issue:
            continue
        if not _qualified_for_secondary(
            domain_evidence[domain],
            primary_score,
            (primary_score - domain_evidence[domain].score) if primary_score is not None else None,
            allow_material_runner_up=(domain == material_runner_up_domain),
        ):
            continue
        if not _has_domain_pressure_evidence(
            domain,
            decision_input,
        ):
            continue
        secondary_issues.append(domain)
    return secondary_issues


def _select_ambiguous_no_primary_secondaries(
    decision_input: DecisionInput,
    domain_evidence: dict[str, DomainEvidence],
    ranked_domains: list[str],
) -> list[str] | None:
    excluded_top_domain = _excluded_low_activity_top_domain(
        decision_input=decision_input,
        domain_evidence=domain_evidence,
        ranked_domains=ranked_domains,
    )
    qualifying_domains = [
        domain
        for domain in ranked_domains
        if _qualified_for_primary(domain_evidence[domain], decision_input)
    ]
    if not qualifying_domains:
        top_domain = ranked_domains[0]
        if top_domain == excluded_top_domain:
            return None
        top_score = domain_evidence[top_domain].score
        runner_up_score = (
            domain_evidence[ranked_domains[1]].score if len(ranked_domains) > 1 else 0.0
        )
        if top_score >= PRIMARY_QUALIFICATION_THRESHOLD and (
            top_score - runner_up_score
        ) < PRIMARY_DOMINANCE_MARGIN:
            return [top_domain]
        if (
            top_score >= SECONDARY_QUALIFICATION_THRESHOLD
            and (top_score - runner_up_score) >= SECONDARY_ONLY_DOMINANCE_MARGIN
        ):
            return [top_domain]
        return None

    top_domain = qualifying_domains[0]
    if top_domain == excluded_top_domain:
        return None
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
    if _top_score_share(domain_evidence, ranked_domains) < _primary_min_share(top_score):
        fallback_candidates = [
            domain
            for domain in ranked_domains
            if domain != top_domain and _qualified_for_secondary_only(domain_evidence[domain])
        ]
        fallback_candidates = _filter_evidence_backed_secondary_candidates(
            fallback_candidates,
            domain_evidence,
            decision_input,
            top_domain=top_domain,
            no_primary_context=True,
        ) or [top_domain]
        anchored_candidates = _topology_anchor_secondaries(
            top_domain=top_domain,
            domain_evidence=domain_evidence,
            decision_input=decision_input,
        )
        return _limit_no_primary_secondaries(
            _merge_secondary_candidates(anchored_candidates, fallback_candidates),
            domain_evidence,
        )
    return None


def _qualified_for_primary(
    domain_evidence: DomainEvidence,
    decision_input: DecisionInput,
) -> bool:
    if domain_evidence.score < PRIMARY_QUALIFICATION_THRESHOLD:
        return False
    severity_input = decision_input.severity_input or 0.0
    if severity_input < PRIMARY_MIN_SEVERITY_THRESHOLD:
        return False
    if _total_supported_score(decision_input) < PRIMARY_MATERIALITY_FLOOR:
        return False
    db_time_per_sec = _feature_metric(decision_input, "db_time_per_sec")
    if (
        severity_input < LOW_SEVERITY_PRIMARY_THRESHOLD
        and db_time_per_sec is not None
        and db_time_per_sec < LOW_ACTIVITY_PRIMARY_MAX_DB_TIME_PER_SEC
    ):
        return False
    if (
        severity_input < LOW_SEVERITY_PRIMARY_THRESHOLD
        and severity_input > 0.0
        and (domain_evidence.score / severity_input) < LOW_SEVERITY_PRIMARY_MIN_SCORE_SHARE
    ):
        return False
    return _support_count(domain_evidence) >= 1


def _qualified_for_secondary(
    domain_evidence: DomainEvidence,
    primary_score: float | None,
    score_gap: float | None = None,
    *,
    allow_material_runner_up: bool = False,
) -> bool:
    if domain_evidence.score < SECONDARY_QUALIFICATION_THRESHOLD:
        return False
    if primary_score is None:
        return False
    if (
        allow_material_runner_up
        and primary_score > 0.0
        and domain_evidence.score >= (primary_score * MATERIAL_RUNNER_UP_SECONDARY_RATIO)
    ):
        return _support_count(domain_evidence) >= 1
    if score_gap is not None and score_gap <= CLOSE_SECONDARY_GAP_ALLOWANCE:
        return _support_count(domain_evidence) >= 1
    if primary_score < LOW_PRIMARY_SECONDARY_SCORE_THRESHOLD:
        return (
            score_gap is not None
            and score_gap <= LOW_PRIMARY_SECONDARY_GAP_ALLOWANCE
            and _support_count(domain_evidence) >= 1
        )
    if domain_evidence.score < (primary_score * SECONDARY_RELATIVE_THRESHOLD):
        return False
    if domain_evidence.score > (primary_score * SECONDARY_RELATIVE_CEILING):
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


def _material_runner_up_secondary_candidate(
    primary_issue: str | None,
    ranked_domains: list[str],
    domain_evidence: dict[str, DomainEvidence],
) -> str | None:
    if primary_issue is None:
        return None
    primary_score = domain_evidence[primary_issue].score
    if primary_score <= 0.0:
        return None
    runner_up_domain = next(
        (domain for domain in ranked_domains if domain != primary_issue),
        None,
    )
    if runner_up_domain is None:
        return None
    runner_up_score = domain_evidence[runner_up_domain].score
    if runner_up_score < SECONDARY_QUALIFICATION_THRESHOLD:
        return None
    if runner_up_score < (primary_score * MATERIAL_RUNNER_UP_SECONDARY_RATIO):
        return None
    if _support_count(domain_evidence[runner_up_domain]) < 1:
        return None
    return runner_up_domain


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
    material_runner_up_domain = _material_runner_up_secondary_candidate(
        primary_issue=primary_issue,
        ranked_domains=ranked_domains,
        domain_evidence=domain_evidence,
    )
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
                    allow_material_runner_up=(domain == material_runner_up_domain),
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


def _total_supported_score(decision_input: DecisionInput) -> float:
    return sum(
        max(_safe_float(decision_input.canonical_domain_scores.get(domain)) or 0.0, 0.0)
        for domain in DOMAIN_ORDER
    )


def _top_score_share(
    domain_evidence: dict[str, DomainEvidence],
    ranked_domains: list[str],
) -> float:
    if not ranked_domains:
        return 0.0
    total_score = sum(
        max(domain_evidence[domain].score, 0.0) for domain in ranked_domains
    )
    if total_score <= 0.0:
        return 0.0
    return domain_evidence[ranked_domains[0]].score / total_score


def _primary_min_share(top_score: float) -> float:
    if top_score >= PRIMARY_HIGH_SCORE_SHARE_THRESHOLD:
        return PRIMARY_HIGH_SCORE_MIN_SHARE
    return PRIMARY_MIN_SHARE


def _activity_supported_primary_override(
    top_domain: str,
    decision_input: DecisionInput,
    domain_evidence: dict[str, DomainEvidence],
    ranked_domains: list[str],
) -> bool:
    if top_domain != decision_input.primary_signal_domain:
        return False
    top_score = domain_evidence[top_domain].score
    if top_score < PRIMARY_QUALIFICATION_THRESHOLD:
        return False
    db_time_per_sec = _feature_metric(decision_input, "db_time_per_sec")
    db_time_per_txn = _feature_metric(decision_input, "db_time_per_txn")
    if (
        db_time_per_sec is None
        or db_time_per_sec < ACTIVITY_SUPPORTED_PRIMARY_MIN_DB_TIME_PER_SEC
    ):
        return False
    if (
        db_time_per_txn is None
        or db_time_per_txn < ACTIVITY_SUPPORTED_PRIMARY_MIN_DB_TIME_PER_TXN
    ):
        return False
    meaningful_domain_count = sum(
        1
        for domain in DOMAIN_ORDER
        if domain_evidence[domain].score >= SECONDARY_QUALIFICATION_THRESHOLD
    )
    if meaningful_domain_count > ACTIVITY_SUPPORTED_PRIMARY_MAX_BREADTH:
        return False
    runner_up_score = (
        domain_evidence[ranked_domains[1]].score if len(ranked_domains) > 1 else 0.0
    )
    return (top_score - runner_up_score) >= ACTIVITY_SUPPORTED_PRIMARY_MIN_GAP


def _limit_no_primary_secondaries(
    secondary_candidates: list[str],
    domain_evidence: dict[str, DomainEvidence],
) -> list[str]:
    if not secondary_candidates:
        return []
    if len(secondary_candidates) <= NO_PRIMARY_MAX_SECONDARIES:
        return list(secondary_candidates)
    top_score = domain_evidence[secondary_candidates[0]].score
    minimum_score = max(
        SECONDARY_ONLY_THRESHOLD,
        top_score * NO_PRIMARY_EXCLUDED_TOP_RELATIVE_THRESHOLD,
    )
    filtered_candidates = [
        domain
        for domain in secondary_candidates
        if domain_evidence[domain].score >= minimum_score
    ]
    return filtered_candidates[:NO_PRIMARY_MAX_SECONDARIES]


def _merge_secondary_candidates(
    leading_candidates: list[str],
    trailing_candidates: list[str],
) -> list[str]:
    merged: list[str] = []
    for domain in [*leading_candidates, *trailing_candidates]:
        if domain not in merged:
            merged.append(domain)
    return merged


def _filter_evidence_backed_secondary_candidates(
    candidates: list[str],
    domain_evidence: dict[str, DomainEvidence],
    decision_input: DecisionInput,
    *,
    top_domain: str | None,
    no_primary_context: bool,
) -> list[str]:
    return [
        domain
        for domain in candidates
        if _has_domain_pressure_evidence(
            domain,
            decision_input,
            no_primary_context=no_primary_context,
            topology_top_domain=top_domain,
        )
        and _meets_topology_secondary_floor(
            domain,
            domain_evidence[domain].score,
        )
    ]


def _topology_anchor_secondaries(
    top_domain: str,
    domain_evidence: dict[str, DomainEvidence],
    decision_input: DecisionInput,
) -> list[str]:
    if top_domain not in {"RAC", "ADG"}:
        return []
    if not _has_domain_pressure_evidence(
        top_domain,
        decision_input,
        no_primary_context=True,
        topology_top_domain=top_domain,
    ):
        return []
    if not _meets_topology_secondary_floor(
        top_domain,
        domain_evidence[top_domain].score,
    ):
        return []
    return [top_domain]


def _meets_topology_secondary_floor(domain: str, score: float) -> bool:
    if domain in {"RAC", "ADG"}:
        return score >= TOPOLOGY_EVIDENCE_SECONDARY_SCORE_FLOOR
    return True


def _excluded_low_activity_top_domain(
    decision_input: DecisionInput,
    domain_evidence: dict[str, DomainEvidence],
    ranked_domains: list[str],
) -> str | None:
    if len(ranked_domains) < 2:
        return None
    db_time_per_sec = _feature_metric(decision_input, "db_time_per_sec")
    if db_time_per_sec is None:
        return None
    top_domain = ranked_domains[0]
    top_score = domain_evidence[top_domain].score
    runner_up_score = domain_evidence[ranked_domains[1]].score
    gap = top_score - runner_up_score
    if (
        db_time_per_sec < LOW_ACTIVITY_NO_PRIMARY_MAX_DB_TIME_PER_SEC
        and top_score >= SECONDARY_QUALIFICATION_THRESHOLD
        and gap <= LOW_ACTIVITY_NO_PRIMARY_EXCLUSION_MAX_GAP
    ):
        return top_domain
    if (
        db_time_per_sec < LOW_ACTIVITY_DIFFUSE_MAX_DB_TIME_PER_SEC
        and top_score >= LOW_ACTIVITY_DIFFUSE_MIN_TOP_SCORE
        and runner_up_score >= LOW_ACTIVITY_DIFFUSE_MIN_RUNNER_UP_SCORE
        and gap < PRIMARY_DOMINANCE_MARGIN
    ):
        return top_domain
    return None


def _uses_single_follow_on_secondary(
    decision_input: DecisionInput,
    domain_evidence: dict[str, DomainEvidence],
    ranked_domains: list[str],
    excluded_top_domain: str | None,
) -> bool:
    if excluded_top_domain is None or len(ranked_domains) < 2:
        return False
    db_time_per_sec = _feature_metric(decision_input, "db_time_per_sec")
    if db_time_per_sec is None:
        return False
    top_score = domain_evidence[ranked_domains[0]].score
    runner_up_score = domain_evidence[ranked_domains[1]].score
    return (
        db_time_per_sec >= LOW_ACTIVITY_NO_PRIMARY_MAX_DB_TIME_PER_SEC
        and db_time_per_sec < LOW_ACTIVITY_DIFFUSE_MAX_DB_TIME_PER_SEC
        and top_score >= LOW_ACTIVITY_DIFFUSE_MIN_TOP_SCORE
        and runner_up_score >= LOW_ACTIVITY_DIFFUSE_MIN_RUNNER_UP_SCORE
        and (top_score - runner_up_score) < PRIMARY_DOMINANCE_MARGIN
    )


def _feature_metric(decision_input: DecisionInput, metric_name: str) -> float | None:
    feature_evidence = decision_input.feature_evidence or {}
    for key in (metric_name, metric_name.upper()):
        numeric_value = _safe_float(feature_evidence.get(key))
        if numeric_value is not None:
            return numeric_value
    return None


def _has_domain_pressure_evidence(
    domain: str,
    decision_input: DecisionInput,
    *,
    no_primary_context: bool = False,
    topology_top_domain: str | None = None,
) -> bool:
    feature_evidence = decision_input.feature_evidence or {}
    if not feature_evidence:
        return True
    if domain == "RAC":
        return _has_any_metric(
            decision_input,
            "cluster_wait_pct_db_time",
            "gc_current_wait_pct_db_time",
            "gc_cr_wait_pct_db_time",
            "gc_buffer_busy_pct_db_time",
            "rac_buffer_busy_pressure",
            threshold=0.01,
        ) or _has_any_flag(
            decision_input,
            "interconnect_stress_flag",
            "rac_contention_flag",
        )
    if domain == "ADG":
        return _has_any_metric(
            decision_input,
            "apply_lag_sec",
            "transport_lag_sec",
            threshold=0.01,
        ) or _has_any_flag(
            decision_input,
            "redo_transport_issue_flag",
            "failover_event_flag",
            "role_transition_flag",
            "post_failover_recovery_flag",
        )
    if domain == "IO":
        return True
    if domain == "COMMIT":
        return True
    if domain == "MEMORY":
        return True
    if domain == "CPU":
        if (
            no_primary_context
            and topology_top_domain in {"RAC", "ADG"}
        ):
            cpu_pct = max(
                _feature_metric(decision_input, "cpu_util_p95") or 0.0,
                _feature_metric(decision_input, "db_cpu_pct_db_time") or 0.0,
            )
            aas_per_cpu = _feature_metric(decision_input, "aas_per_cpu") or 0.0
            return (
                cpu_pct >= CPU_BASELINE_SECONDARY_MIN_PCT
                or aas_per_cpu >= CPU_BASELINE_SECONDARY_MIN_AAS_PER_CPU
            )
        return True
    return False


def _has_any_metric(
    decision_input: DecisionInput,
    *metric_names: str,
    threshold: float,
) -> bool:
    return any(
        (_feature_metric(decision_input, metric_name) or 0.0) > threshold
        for metric_name in metric_names
    )


def _has_any_flag(
    decision_input: DecisionInput,
    *metric_names: str,
) -> bool:
    return any(
        (_feature_metric(decision_input, metric_name) or 0.0) >= 0.5
        for metric_name in metric_names
    )
