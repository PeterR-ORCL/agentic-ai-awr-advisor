from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class DecisionInput:
    awr_id: int
    canonical_domain_scores: dict[str, float]
    severity_input: float | None = None
    confidence_input: float | None = None
    completeness: float | None = None
    primary_signal_domain: str | None = None
    score_evidence: dict[str, Any] | None = None
    feature_evidence: dict[str, Any] | None = None
    trend_rows: list[dict[str, Any]] | None = None
    anomaly_signals: list[dict[str, Any]] | None = None


@dataclass(slots=True)
class AwrDecision:
    awr_id: int
    overall_status: str
    primary_issue: str | None
    secondary_issues: list[str]
    severity_score: float
    confidence: float
    evidence: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
