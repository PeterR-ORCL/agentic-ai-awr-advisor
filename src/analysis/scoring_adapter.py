from __future__ import annotations

import json
from typing import Any

from src.models.decision import DecisionInput

DOMAIN_ORDER = ("CPU", "IO", "MEMORY", "COMMIT", "RAC", "ADG")
SCORE_DOMAIN_MAP = {
    "CPU": "CPU",
    "CAPACITY": "CPU",
    "LOAD": "CPU",
    "SQL": "CPU",
    "IO": "IO",
    "EXADATA": "IO",
    # In the current AWR_WEIGHTED_CORE seed model, WAIT is emitted only by
    # LOG_FILE_SYNC_MS, so Phase 4G can safely treat it as COMMIT-scoped.
    "WAIT": "COMMIT",
    "MEMORY": "MEMORY",
    "COMMIT": "COMMIT",
    "CLUSTER": "RAC",
    "RAC": "RAC",
    "DG": "ADG",
    "DATAGUARD": "ADG",
    "ADG": "ADG",
}


def build_decision_input_from_score_result(
    awr_id: int,
    score_result: dict[str, Any] | None,
    trend_rows: list[dict[str, Any]] | None = None,
    anomaly_signals: list[dict[str, Any]] | None = None,
    feature_evidence: dict[str, Any] | None = None,
) -> DecisionInput:
    score_payload = _normalize_score_result(score_result)
    canonical_domain_scores, score_evidence = _build_authoritative_score_evidence(
        score_payload
    )
    all_anomalies = list(trend_rows or [])
    if anomaly_signals:
        all_anomalies.extend(anomaly_signals)
    return DecisionInput(
        awr_id=awr_id,
        canonical_domain_scores=canonical_domain_scores,
        severity_input=_coerce_severity(score_payload),
        confidence_input=_coerce_confidence(score_payload),
        completeness=_coerce_completeness(score_payload),
        primary_signal_domain=_normalize_domain_key(
            score_payload.get("primary_signal_domain")
        ),
        score_evidence=score_evidence,
        feature_evidence=feature_evidence or {},
        trend_rows=list(trend_rows or []),
        anomaly_signals=all_anomalies,
    )


def _build_authoritative_score_evidence(
    score_payload: dict[str, Any],
) -> tuple[dict[str, float], dict[str, Any]]:
    canonical_scores = _coerce_canonical_scores(
        score_payload.get("canonical_domain_scores")
        or score_payload.get("domain_scores")
    )
    if canonical_scores is not None:
        return canonical_scores, {
            "canonical_domain_scores": {
                domain: round(canonical_scores.get(domain, 0.0), 4)
                for domain in DOMAIN_ORDER
            },
            "raw_domain_totals": {},
            "canonical_domain_totals": {
                domain: round(canonical_scores.get(domain, 0.0), 4)
                for domain in DOMAIN_ORDER
            },
            "score_result": _score_result_metadata(score_payload),
        }

    raw_domain_totals = score_payload.get("domain_totals", {})
    canonical_totals = {domain: 0.0 for domain in DOMAIN_ORDER}
    raw_components: dict[str, float] = {}
    if isinstance(raw_domain_totals, dict):
        for source_domain, raw_value in raw_domain_totals.items():
            numeric_value = _safe_float(raw_value)
            if numeric_value is None:
                continue
            raw_components[str(source_domain)] = round(numeric_value, 4)
            mapped_domain = SCORE_DOMAIN_MAP.get(str(source_domain).upper())
            if mapped_domain is None:
                continue
            canonical_totals[mapped_domain] += numeric_value

    score_scale_max = _coerce_score_scale_max(score_payload)
    if score_scale_max is not None and score_scale_max > 0.0:
        canonical_scores_from_totals = {
            domain: round(canonical_totals[domain] / score_scale_max, 4)
            for domain in DOMAIN_ORDER
        }
    else:
        canonical_scores_from_totals = {
            domain: round(canonical_totals[domain], 4) for domain in DOMAIN_ORDER
        }

    return canonical_scores_from_totals, {
        "raw_domain_totals": raw_components,
        "canonical_domain_totals": {
            domain: round(canonical_totals[domain], 4) for domain in DOMAIN_ORDER
        },
        "score_scale_max": score_scale_max,
        "score_result": _score_result_metadata(score_payload),
    }


def _coerce_canonical_scores(raw_scores: Any) -> dict[str, float] | None:
    if not isinstance(raw_scores, dict):
        return None
    canonical_scores = {domain: 0.0 for domain in DOMAIN_ORDER}
    seen_numeric = False
    for domain in DOMAIN_ORDER:
        numeric_value = _safe_float(raw_scores.get(domain))
        if numeric_value is None:
            continue
        canonical_scores[domain] = round(numeric_value, 4)
        seen_numeric = True
    if not seen_numeric:
        return None
    return canonical_scores


def _normalize_score_result(score_result: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(score_result, dict):
        return {}
    normalized = dict(score_result)
    scorecard_json = _load_json(score_result.get("scorecard_json"))
    if isinstance(scorecard_json, dict):
        normalized.update(scorecard_json)
    contribution_json = _load_json(score_result.get("contribution_json"))
    if isinstance(contribution_json, dict):
        normalized["contribution_json"] = contribution_json
    explanation_json = _load_json(score_result.get("explanation_json"))
    if isinstance(explanation_json, dict):
        normalized["explanation_json"] = explanation_json
    return normalized


def _score_result_metadata(score_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in score_payload.items()
        if key
        in {
            "severity_score",
            "confidence_score",
            "confidence",
            "total_score",
            "risk_level",
            "coverage_ratio",
            "primary_signal_domain",
            "model_code",
            "model_version",
            "decision_domain",
            "score_max",
        }
    }


def _coerce_score_scale_max(score_payload: dict[str, Any]) -> float | None:
    for key in ("score_max",):
        numeric_value = _safe_float(score_payload.get(key))
        if numeric_value is not None and numeric_value > 0.0:
            return numeric_value
    model_config = score_payload.get("model_config_json")
    if isinstance(model_config, dict):
        for key in ("score_max", "domain_score_max"):
            numeric_value = _safe_float(model_config.get(key))
            if numeric_value is not None and numeric_value > 0.0:
                return numeric_value
    return None


def _normalize_domain_key(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().upper()
    return SCORE_DOMAIN_MAP.get(normalized)


def _coerce_confidence(score_payload: dict[str, Any]) -> float | None:
    direct_confidence = _safe_float(score_payload.get("confidence"))
    if direct_confidence is not None:
        return _clamp(direct_confidence, 0.0, 1.0)
    percent_confidence = _safe_float(score_payload.get("confidence_score"))
    if percent_confidence is not None:
        return _clamp(percent_confidence / 100.0, 0.0, 1.0)
    return None


def _coerce_severity(score_payload: dict[str, Any]) -> float | None:
    for key in ("severity_score", "total_score"):
        numeric_value = _safe_float(score_payload.get(key))
        if numeric_value is not None:
            return numeric_value
    return None


def _coerce_completeness(score_payload: dict[str, Any]) -> float | None:
    numeric_value = _safe_float(score_payload.get("coverage_ratio"))
    if numeric_value is None:
        return None
    return _clamp(numeric_value, 0.0, 1.0)


def _load_json(value: Any) -> Any:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
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
