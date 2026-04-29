from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Protocol, Sequence

from src.models.decision import AwrDecision

OUTPUT_VERSION = "4I_v1"
OUTPUT_SOURCE = "AWR_ANALYSIS"
CLI_DIVIDER = "=" * 48
CANONICAL_DECISION_KEYS = (
    "workload_class",
    "topology_class",
    "platform_class",
    "event_class",
)


class OutputRecommendation(Protocol):
    """Recommendation interface consumed by the output layer."""

    priority: Any
    action: str

    def to_dict(self) -> dict[str, Any]: ...


def build_analysis_output(
    *,
    decision: AwrDecision,
    scores: dict[str, Any],
    trends: dict[str, Any],
    similarity_intelligence: dict[str, Any],
    recommendations: list[Any] | None,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Build the stable presentation contract for analysis results."""

    decision_dict = decision.to_dict()
    classification = _extract_classification(decision)
    domain_scores = dict(scores.get("domain_scores", scores)) if isinstance(scores, dict) else {}
    normalized_recommendations = _normalize_recommendations(recommendations)
    normalized_similarity = (
        dict(similarity_intelligence)
        if isinstance(similarity_intelligence, dict)
        else {"enabled": False}
    )
    if "enabled" not in normalized_similarity:
        normalized_similarity["enabled"] = False

    return {
        "metadata": {
            "awr_id": _safe_int(metadata.get("awr_id")),
            "db_name": _safe_str(metadata.get("db_name")),
            "snapshot_begin": _safe_value(metadata.get("snapshot_begin")),
            "snapshot_end": _safe_value(metadata.get("snapshot_end")),
            "generated_at": _format_timestamp(datetime.now(timezone.utc)),
            "output_version": OUTPUT_VERSION,
            "source": OUTPUT_SOURCE,
        },
        "decision": {
            "primary_domain": decision_dict.get("primary_issue"),
            "secondary_domains": list(decision_dict.get("secondary_issues") or []),
            "risk_level": decision_dict.get("overall_status"),
            "confidence": float(decision_dict.get("confidence") or 0.0),
            "classification": classification,
        },
        "scores": {
            "domain_scores": domain_scores,
        },
        "trends": dict(trends) if isinstance(trends, dict) else {"findings": [], "time_series": {}},
        "similarity_intelligence": normalized_similarity,
        "recommendations": normalized_recommendations,
    }


def render_analysis_json(
    decision: AwrDecision,
    recommendations: Sequence[OutputRecommendation],
    generated_at: datetime | None = None,
    output_version: str = OUTPUT_VERSION,
    source: str = OUTPUT_SOURCE,
) -> str:
    """Render the final analysis payload as formatted JSON."""

    del generated_at, output_version, source
    payload = build_analysis_output(
        decision=decision,
        scores=_default_scores_from_decision(decision),
        trends={"findings": [], "time_series": {}},
        similarity_intelligence={"enabled": False},
        recommendations=list(recommendations),
        metadata={"awr_id": decision.awr_id},
    )
    return json.dumps(payload, indent=2, sort_keys=False)


def render_analysis_cli(
    decision: AwrDecision,
    recommendations: Sequence[OutputRecommendation],
) -> str:
    """Render the final deterministic analysis in a human-readable CLI format."""

    lines = [
        CLI_DIVIDER,
        "AWR ANALYSIS RESULT",
        CLI_DIVIDER,
        f"AWR ID: {decision.awr_id}",
        "",
        f"STATUS: {decision.overall_status}",
        f"PRIMARY ISSUE: {decision.primary_issue}",
    ]
    if decision.secondary_issues:
        lines.append(
            "SECONDARY ISSUES: " + ", ".join(decision.secondary_issues)
        )
    lines.extend(
        [
            f"SEVERITY SCORE: {decision.severity_score:.2f}",
            f"CONFIDENCE: {decision.confidence:.2f}",
            "",
            "TOP RECOMMENDATIONS:",
        ]
    )
    for recommendation in recommendations:
        lines.append(f"{recommendation.priority}. {recommendation.action}")
    lines.append("")
    lines.append(CLI_DIVIDER)
    return "\n".join(lines)


def _extract_classification(decision: AwrDecision) -> dict[str, str | None]:
    evidence = decision.evidence or {}
    feature_evidence = evidence.get("feature_evidence")
    score_evidence = evidence.get("score_evidence")
    classification: dict[str, str | None] = {}
    for key in CANONICAL_DECISION_KEYS:
        classification[key] = (
            _lookup_classification_value(key, feature_evidence)
            or _lookup_classification_value(key, score_evidence)
        )
    return classification


def _lookup_classification_value(
    key: str,
    source: Any,
) -> str | None:
    if not isinstance(source, dict):
        return None
    candidates = (
        key,
        key.upper(),
        key.lower(),
        key.replace("_class", "").upper() + "_CLASS",
    )
    for candidate in candidates:
        value = source.get(candidate)
        if value is None:
            continue
        return str(value)
    return None


def _normalize_recommendations(
    recommendations: list[Any] | None,
) -> list[Any]:
    if not recommendations:
        return []
    normalized: list[Any] = []
    for recommendation in recommendations:
        if hasattr(recommendation, "to_dict"):
            normalized.append(recommendation.to_dict())
        else:
            normalized.append(recommendation)
    return normalized


def _default_scores_from_decision(decision: AwrDecision) -> dict[str, Any]:
    evidence = decision.evidence or {}
    domain_scores = evidence.get("domain_scores", {})
    return {"domain_scores": domain_scores if isinstance(domain_scores, dict) else {}}


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value_utc = value.astimezone(timezone.utc)
    return value_utc.isoformat(timespec="seconds").replace("+00:00", "Z")


def _safe_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _safe_value(value: Any) -> Any:
    return None if value is None else value
