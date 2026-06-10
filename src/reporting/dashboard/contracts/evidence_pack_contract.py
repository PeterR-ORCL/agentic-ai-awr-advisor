"""Evidence pack contract for selected dashboard review flows.

The evidence pack is the deterministic evidence authority downstream of
``selected_review_scope_contract``. It validates evidence payload shape and
provenance only. It does not render HTML, inspect browser state, read generated
dashboard artifacts, call LLMs, compute comparisons in the browser, or mutate
the selected review scope.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any

from src.reporting.dashboard.contracts.selected_review_scope_contract import (
    ReviewMode,
    ScopeValidationStatus,
    SelectedReviewScopeContract,
    validate_selected_review_scope_contract,
)


CONTRACT_TYPE = "evidence_pack_contract"
CONTRACT_VERSION = "7reset.evidence_pack.v1"


class EvidencePackValidationStatus(str, Enum):
    VALID = "valid"
    PARTIAL = "partial"
    INVALID = "invalid"
    UNAVAILABLE = "unavailable"


class EvidenceAvailabilityStatus(str, Enum):
    PRESENT = "present"
    MISSING = "missing"
    UNAVAILABLE = "unavailable"
    STALE = "stale"


class EvidenceDomain(str, Enum):
    DIAGNOSTIC = "diagnostic"
    HISTORICAL = "historical"
    COMPARATIVE = "comparative"
    DEEP_ANALYSIS = "deep_analysis"
    RECOMMENDATION_ACTION = "recommendation_action"
    LEARNING_GOVERNANCE = "learning_governance"


class EvidenceSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class VisualizationKind(str, Enum):
    TABLE = "table"
    SCALAR = "scalar"
    TREND = "trend"
    BAR = "bar"
    LINE = "line"
    COMPARISON_DELTA = "comparison_delta"
    DISTRIBUTION = "distribution"
    NONE = "none"


class LLMExplanationStatus(str, Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    NOT_APPLICABLE = "not_applicable"


FORBIDDEN_AUTHORITY_KEYS = {
    "browser_hash",
    "browser_state",
    "chart_markup",
    "css_class",
    "dashboard_hash",
    "generated_artifact_path",
    "generated_html",
    "generated_html_path",
    "hash_state",
    "html",
    "html_path",
    "llm_decision",
    "llm_facts",
    "llm_generated_evidence",
    "llm_recommendation",
    "llm_text",
    "local_storage",
    "localStorage",
    "rendered_html",
    "selector_label",
    "selector_state",
    "ui_flags",
    "ui_selector_label",
}


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _enum_value(enum_type: type[Enum], value: Any, default: Enum) -> Enum:
    if isinstance(value, enum_type):
        return value
    if value is None:
        return default
    text = _clean_string(value)
    if not text:
        return default
    normalized = text.lower()
    for item in enum_type:
        if normalized in {item.value.lower(), item.name.lower()}:
            return item
    return default


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _tuple_of_strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return tuple(str(item) for item in value if _clean_string(item))
    return (str(value),)


def _json_safe_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    safe: dict[str, Any] = {}
    for key, raw in value.items():
        if raw is None:
            continue
        if isinstance(raw, (str, int, float, bool)):
            safe[str(key)] = raw
        elif isinstance(raw, Mapping):
            safe[str(key)] = _json_safe_mapping(raw)
        elif isinstance(raw, Sequence) and not isinstance(raw, (bytes, bytearray, str)):
            safe[str(key)] = [
                _json_safe_mapping(item) if isinstance(item, Mapping) else item
                for item in raw
                if item is not None
            ]
        else:
            safe[str(key)] = str(raw)
    return safe


def _contains_generated_html(value: Any) -> bool:
    if isinstance(value, str):
        normalized = value.replace("\\", "/").lower()
        return normalized.endswith(".html") and (
            normalized.startswith("awr_dashboard/") or "/awr_dashboard/" in normalized
        )
    if isinstance(value, Mapping):
        return any(_contains_generated_html(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return any(_contains_generated_html(item) for item in value)
    return False


def detect_forbidden_authority_keys(value: Any) -> tuple[str, ...]:
    """Return forbidden payload key categories without preserving raw evidence."""

    detected: set[str] = set()

    def visit(item: Any) -> None:
        if isinstance(item, Mapping):
            for key, raw in item.items():
                key_text = str(key)
                if key_text in FORBIDDEN_AUTHORITY_KEYS:
                    if key_text in {"generated_html", "generated_html_path", "html", "html_path", "rendered_html"}:
                        detected.add("generated_html")
                    elif key_text.startswith("llm_") or key_text in {"llm_text", "llm_facts"}:
                        detected.add("llm_generated_evidence")
                    elif key_text in {"chart_markup"}:
                        detected.add("chart_markup")
                    elif key_text in {"localStorage", "local_storage", "browser_state", "hash_state", "browser_hash"}:
                        detected.add("browser_state")
                    else:
                        detected.add("ui_state")
                visit(raw)
        elif isinstance(item, Sequence) and not isinstance(item, (bytes, bytearray, str)):
            for child in item:
                visit(child)
        elif _contains_generated_html(item):
            detected.add("generated_html")

    visit(value)
    return tuple(sorted(detected))


@dataclass(frozen=True)
class EvidencePackIdentity:
    evidence_pack_id: str
    selected_flow_id: str
    source_selected_review_scope_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "evidence_pack_id": self.evidence_pack_id,
            "selected_flow_id": self.selected_flow_id,
            "source_selected_review_scope_id": self.source_selected_review_scope_id,
        }


@dataclass(frozen=True)
class EvidenceProvenance:
    source_system: str | None = None
    builder_version: str | None = None
    generated_at: str | None = None
    deterministic_sources: tuple[str, ...] = ()

    def is_present(self) -> bool:
        return bool(_clean_string(self.source_system))

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_system": self.source_system,
            "builder_version": self.builder_version,
            "generated_at": self.generated_at,
            "deterministic_sources": list(self.deterministic_sources),
        }

    @classmethod
    def from_value(cls, value: Any) -> "EvidenceProvenance":
        if value is None:
            return cls()
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls(source_system=_clean_string(value))
        if not isinstance(value, Mapping):
            return cls(source_system=str(value))
        return cls(
            source_system=_clean_string(value.get("source_system") or value.get("source")),
            builder_version=_clean_string(value.get("builder_version")),
            generated_at=_clean_string(value.get("generated_at") or value.get("created_at")),
            deterministic_sources=_tuple_of_strings(value.get("deterministic_sources")),
        )


@dataclass(frozen=True)
class EvidenceFreshness:
    status: EvidenceAvailabilityStatus = EvidenceAvailabilityStatus.PRESENT
    as_of: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "status": self.status.value,
            "as_of": self.as_of,
            "reason": self.reason,
        }

    @classmethod
    def from_value(cls, value: Any) -> "EvidenceFreshness":
        if value is None:
            return cls()
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls(status=_enum_value(EvidenceAvailabilityStatus, value, EvidenceAvailabilityStatus.PRESENT))
        if not isinstance(value, Mapping):
            return cls(reason=str(value))
        return cls(
            status=_enum_value(
                EvidenceAvailabilityStatus,
                value.get("status"),
                EvidenceAvailabilityStatus.PRESENT,
            ),
            as_of=_clean_string(value.get("as_of")),
            reason=_clean_string(value.get("reason")),
        )


@dataclass(frozen=True)
class EvidenceIssue:
    code: str
    message: str
    domain: EvidenceDomain | None = None
    severity: EvidenceSeverity = EvidenceSeverity.ERROR
    field: str | None = None

    def to_dict(self) -> dict[str, str]:
        payload = {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
        }
        if self.domain:
            payload["domain"] = self.domain.value
        if self.field:
            payload["field"] = self.field
        return payload

    @classmethod
    def from_value(cls, value: Any) -> "EvidenceIssue":
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            return cls(code="issue", message=str(value))
        return cls(
            code=str(value.get("code") or "issue"),
            message=str(value.get("message") or value.get("reason") or "Evidence issue."),
            domain=_enum_value(EvidenceDomain, value.get("domain"), None),  # type: ignore[arg-type]
            severity=_enum_value(EvidenceSeverity, value.get("severity"), EvidenceSeverity.ERROR),
            field=_clean_string(value.get("field")),
        )


@dataclass(frozen=True)
class MissingEvidence:
    domain: EvidenceDomain
    reason_code: str
    message: str
    required_for_modes: tuple[ReviewMode, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain.value,
            "reason_code": self.reason_code,
            "message": self.message,
            "required_for_modes": [mode.value for mode in self.required_for_modes],
        }

    @classmethod
    def from_value(cls, value: Any) -> "MissingEvidence":
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            return cls(EvidenceDomain.DIAGNOSTIC, "missing_evidence", str(value))
        return cls(
            domain=_enum_value(EvidenceDomain, value.get("domain"), EvidenceDomain.DIAGNOSTIC),
            reason_code=str(value.get("reason_code") or "missing_evidence"),
            message=str(value.get("message") or "Evidence is missing."),
            required_for_modes=tuple(
                _enum_value(ReviewMode, mode, ReviewMode.DIAGNOSTIC_SNAPSHOT)
                for mode in value.get("required_for_modes", ())
            ),
        )


@dataclass(frozen=True)
class UnavailableEvidence:
    domain: EvidenceDomain
    reason_code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "domain": self.domain.value,
            "reason_code": self.reason_code,
            "message": self.message,
        }

    @classmethod
    def from_value(cls, value: Any) -> "UnavailableEvidence":
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            return cls(EvidenceDomain.DIAGNOSTIC, "unavailable_evidence", str(value))
        return cls(
            domain=_enum_value(EvidenceDomain, value.get("domain"), EvidenceDomain.DIAGNOSTIC),
            reason_code=str(value.get("reason_code") or "unavailable_evidence"),
            message=str(value.get("message") or "Evidence is unavailable."),
        )


@dataclass(frozen=True)
class StaleEvidence:
    domain: EvidenceDomain
    reason_code: str
    message: str
    as_of: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "domain": self.domain.value,
            "reason_code": self.reason_code,
            "message": self.message,
            "as_of": self.as_of,
        }

    @classmethod
    def from_value(cls, value: Any) -> "StaleEvidence":
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            return cls(EvidenceDomain.DIAGNOSTIC, "stale_evidence", str(value))
        return cls(
            domain=_enum_value(EvidenceDomain, value.get("domain"), EvidenceDomain.DIAGNOSTIC),
            reason_code=str(value.get("reason_code") or "stale_evidence"),
            message=str(value.get("message") or "Evidence is stale."),
            as_of=_clean_string(value.get("as_of")),
        )


@dataclass(frozen=True)
class EvidenceRow:
    row_id: str
    domain: EvidenceDomain
    values: Mapping[str, Any]
    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_id": self.row_id,
            "domain": self.domain.value,
            "values": _json_safe_mapping(self.values),
            "source": self.source,
        }

    @classmethod
    def from_value(cls, value: Any, domain: EvidenceDomain) -> "EvidenceRow":
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            return cls(row_id=_stable_id(domain.value, {"value": value}), domain=domain, values={"value": value})
        values = _json_safe_mapping(value.get("values") if isinstance(value.get("values"), Mapping) else value)
        return cls(
            row_id=str(value.get("row_id") or value.get("id") or _stable_id(domain.value, values)),
            domain=_enum_value(EvidenceDomain, value.get("domain"), domain),
            values=values,
            source=_clean_string(value.get("source")),
        )


@dataclass(frozen=True)
class MetricSummary:
    metric_name: str
    domain: EvidenceDomain
    value: Any
    unit: str | None = None
    source_evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "domain": self.domain.value,
            "value": self.value,
            "unit": self.unit,
            "source_evidence_ids": list(self.source_evidence_ids),
        }

    @classmethod
    def from_value(cls, value: Any, domain: EvidenceDomain) -> "MetricSummary":
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            return cls(
                metric_name=str(value.get("metric_name") or value.get("name") or value.get("key") or "metric"),
                domain=_enum_value(EvidenceDomain, value.get("domain"), domain),
                value=value.get("value"),
                unit=_clean_string(value.get("unit")),
                source_evidence_ids=_tuple_of_strings(value.get("source_evidence_ids")),
            )
        return cls(metric_name="metric", domain=domain, value=value)


@dataclass(frozen=True)
class TrendSummary:
    trend_name: str
    domain: EvidenceDomain
    direction: str | None = None
    points: tuple[Mapping[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "trend_name": self.trend_name,
            "domain": self.domain.value,
            "direction": self.direction,
            "points": [_json_safe_mapping(point) for point in self.points],
        }

    @classmethod
    def from_value(cls, value: Any, domain: EvidenceDomain) -> "TrendSummary":
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            return cls(trend_name="trend", domain=domain, direction=str(value))
        return cls(
            trend_name=str(value.get("trend_name") or value.get("name") or "trend"),
            domain=_enum_value(EvidenceDomain, value.get("domain"), domain),
            direction=_clean_string(value.get("direction")),
            points=tuple(
                _json_safe_mapping(point)
                for point in value.get("points", ())
                if isinstance(point, Mapping)
            ),
        )


@dataclass(frozen=True)
class AnomalySummary:
    anomaly_name: str
    domain: EvidenceDomain
    severity: EvidenceSeverity = EvidenceSeverity.INFO
    description: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "anomaly_name": self.anomaly_name,
            "domain": self.domain.value,
            "severity": self.severity.value,
            "description": self.description,
        }

    @classmethod
    def from_value(cls, value: Any, domain: EvidenceDomain) -> "AnomalySummary":
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            return cls(anomaly_name="anomaly", domain=domain, description=str(value))
        return cls(
            anomaly_name=str(value.get("anomaly_name") or value.get("name") or "anomaly"),
            domain=_enum_value(EvidenceDomain, value.get("domain"), domain),
            severity=_enum_value(EvidenceSeverity, value.get("severity"), EvidenceSeverity.INFO),
            description=_clean_string(value.get("description")),
        )


@dataclass(frozen=True)
class SimilarityContext:
    context_id: str
    domain: EvidenceDomain
    similar_case_ids: tuple[str, ...] = ()
    basis: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "domain": self.domain.value,
            "similar_case_ids": list(self.similar_case_ids),
            "basis": self.basis,
        }

    @classmethod
    def from_value(cls, value: Any, domain: EvidenceDomain) -> "SimilarityContext":
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            return cls(context_id=_stable_id(domain.value, {"similarity": value}), domain=domain, basis=str(value))
        return cls(
            context_id=str(value.get("context_id") or value.get("id") or _stable_id(domain.value, value)),
            domain=_enum_value(EvidenceDomain, value.get("domain"), domain),
            similar_case_ids=_tuple_of_strings(value.get("similar_case_ids")),
            basis=_clean_string(value.get("basis")),
        )


@dataclass(frozen=True)
class ConfidenceBasis:
    basis_id: str
    domain: EvidenceDomain
    confidence: str | None = None
    factors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "basis_id": self.basis_id,
            "domain": self.domain.value,
            "confidence": self.confidence,
            "factors": list(self.factors),
        }

    @classmethod
    def from_value(cls, value: Any, domain: EvidenceDomain) -> "ConfidenceBasis":
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            return cls(basis_id=_stable_id(domain.value, {"confidence": value}), domain=domain, confidence=str(value))
        return cls(
            basis_id=str(value.get("basis_id") or value.get("id") or _stable_id(domain.value, value)),
            domain=_enum_value(EvidenceDomain, value.get("domain"), domain),
            confidence=_clean_string(value.get("confidence")),
            factors=_tuple_of_strings(value.get("factors")),
        )


@dataclass(frozen=True)
class _EvidenceSection:
    availability_status: EvidenceAvailabilityStatus = EvidenceAvailabilityStatus.MISSING
    evidence_ids: tuple[str, ...] = ()
    rows: tuple[EvidenceRow, ...] = ()
    summary: str | None = None
    freshness: EvidenceFreshness = field(default_factory=EvidenceFreshness)
    provenance: EvidenceProvenance = field(default_factory=EvidenceProvenance)

    @property
    def domain(self) -> EvidenceDomain:
        raise NotImplementedError

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain.value,
            "availability_status": self.availability_status.value,
            "evidence_ids": list(self.evidence_ids),
            "rows": [row.to_dict() for row in self.rows],
            "summary": self.summary,
            "freshness": self.freshness.to_dict(),
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True)
class DiagnosticEvidence(_EvidenceSection):
    @property
    def domain(self) -> EvidenceDomain:
        return EvidenceDomain.DIAGNOSTIC


@dataclass(frozen=True)
class HistoricalEvidence(_EvidenceSection):
    @property
    def domain(self) -> EvidenceDomain:
        return EvidenceDomain.HISTORICAL


@dataclass(frozen=True)
class ComparativeEvidence(_EvidenceSection):
    @property
    def domain(self) -> EvidenceDomain:
        return EvidenceDomain.COMPARATIVE


@dataclass(frozen=True)
class DeepAnalysisEvidence(_EvidenceSection):
    @property
    def domain(self) -> EvidenceDomain:
        return EvidenceDomain.DEEP_ANALYSIS


@dataclass(frozen=True)
class RecommendationActionEvidence(_EvidenceSection):
    @property
    def domain(self) -> EvidenceDomain:
        return EvidenceDomain.RECOMMENDATION_ACTION


@dataclass(frozen=True)
class LearningGovernanceEvidence(_EvidenceSection):
    @property
    def domain(self) -> EvidenceDomain:
        return EvidenceDomain.LEARNING_GOVERNANCE


SECTION_TYPES = {
    EvidenceDomain.DIAGNOSTIC: DiagnosticEvidence,
    EvidenceDomain.HISTORICAL: HistoricalEvidence,
    EvidenceDomain.COMPARATIVE: ComparativeEvidence,
    EvidenceDomain.DEEP_ANALYSIS: DeepAnalysisEvidence,
    EvidenceDomain.RECOMMENDATION_ACTION: RecommendationActionEvidence,
    EvidenceDomain.LEARNING_GOVERNANCE: LearningGovernanceEvidence,
}


@dataclass(frozen=True)
class AllowedVisualization:
    visualization_id: str
    domain: EvidenceDomain
    kind: VisualizationKind
    source_evidence_ids: tuple[str, ...]
    title: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "visualization_id": self.visualization_id,
            "domain": self.domain.value,
            "kind": self.kind.value,
            "source_evidence_ids": list(self.source_evidence_ids),
            "title": self.title,
        }

    @classmethod
    def from_value(cls, value: Any) -> "AllowedVisualization":
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            return cls(
                visualization_id=_stable_id("visualization", {"value": value}),
                domain=EvidenceDomain.DIAGNOSTIC,
                kind=VisualizationKind.NONE,
                source_evidence_ids=(),
                title=str(value),
            )
        return cls(
            visualization_id=str(value.get("visualization_id") or value.get("id") or _stable_id("visualization", value)),
            domain=_enum_value(EvidenceDomain, value.get("domain"), EvidenceDomain.DIAGNOSTIC),
            kind=_enum_value(VisualizationKind, value.get("kind"), VisualizationKind.NONE),
            source_evidence_ids=_tuple_of_strings(value.get("source_evidence_ids")),
            title=_clean_string(value.get("title")),
        )


@dataclass(frozen=True)
class LLMExplanationEligibility:
    domain: EvidenceDomain
    status: LLMExplanationStatus
    source_evidence_ids: tuple[str, ...] = ()
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain.value,
            "status": self.status.value,
            "source_evidence_ids": list(self.source_evidence_ids),
            "reason": self.reason,
        }

    @classmethod
    def from_value(cls, value: Any) -> "LLMExplanationEligibility":
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            return cls(EvidenceDomain.DIAGNOSTIC, LLMExplanationStatus.BLOCKED, reason=str(value))
        return cls(
            domain=_enum_value(EvidenceDomain, value.get("domain"), EvidenceDomain.DIAGNOSTIC),
            status=_enum_value(LLMExplanationStatus, value.get("status"), LLMExplanationStatus.BLOCKED),
            source_evidence_ids=_tuple_of_strings(value.get("source_evidence_ids")),
            reason=_clean_string(value.get("reason")),
        )


@dataclass(frozen=True)
class EvidencePackContract:
    contract_type: str
    contract_version: str
    evidence_pack_id: str
    selected_flow_id: str
    source_selected_review_scope_id: str
    source_selected_review_scope_contract_type: str
    selected_scope_validation_status: ScopeValidationStatus
    diagnostic_evidence: DiagnosticEvidence
    historical_evidence: HistoricalEvidence
    comparative_evidence: ComparativeEvidence
    deep_analysis_evidence: DeepAnalysisEvidence
    recommendation_action_evidence: RecommendationActionEvidence
    learning_governance_evidence: LearningGovernanceEvidence
    evidence_rows: tuple[EvidenceRow, ...]
    metric_summaries: tuple[MetricSummary, ...]
    trend_summaries: tuple[TrendSummary, ...]
    anomaly_summaries: tuple[AnomalySummary, ...]
    similarity_context: tuple[SimilarityContext, ...]
    confidence_basis: tuple[ConfidenceBasis, ...]
    missing_evidence: tuple[MissingEvidence, ...]
    unavailable_evidence: tuple[UnavailableEvidence, ...]
    stale_evidence: tuple[StaleEvidence, ...]
    allowed_visualizations: tuple[AllowedVisualization, ...]
    llm_explanation_eligibility: tuple[LLMExplanationEligibility, ...]
    provenance: EvidenceProvenance
    validation_status: EvidencePackValidationStatus
    validation_errors: tuple[EvidenceIssue, ...] = ()
    warnings: tuple[EvidenceIssue, ...] = ()

    def identity(self) -> EvidencePackIdentity:
        return EvidencePackIdentity(
            evidence_pack_id=self.evidence_pack_id,
            selected_flow_id=self.selected_flow_id,
            source_selected_review_scope_id=self.source_selected_review_scope_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return evidence_pack_to_dict(self)


def compute_evidence_pack_id(
    *,
    selected_flow_id: str,
    source_selected_review_scope_id: str,
    selected_scope_validation_status: ScopeValidationStatus | str,
    diagnostic_evidence: DiagnosticEvidence,
    historical_evidence: HistoricalEvidence,
    comparative_evidence: ComparativeEvidence,
    deep_analysis_evidence: DeepAnalysisEvidence,
    recommendation_action_evidence: RecommendationActionEvidence,
    learning_governance_evidence: LearningGovernanceEvidence,
    evidence_rows: Sequence[EvidenceRow] = (),
    metric_summaries: Sequence[MetricSummary] = (),
    trend_summaries: Sequence[TrendSummary] = (),
    anomaly_summaries: Sequence[AnomalySummary] = (),
    similarity_context: Sequence[SimilarityContext] = (),
    confidence_basis: Sequence[ConfidenceBasis] = (),
    missing_evidence: Sequence[MissingEvidence] = (),
    unavailable_evidence: Sequence[UnavailableEvidence] = (),
    stale_evidence: Sequence[StaleEvidence] = (),
    allowed_visualizations: Sequence[AllowedVisualization] = (),
    llm_explanation_eligibility: Sequence[LLMExplanationEligibility] = (),
) -> str:
    """Return deterministic evidence-pack id from selected flow and evidence content."""

    payload = {
        "contract_type": CONTRACT_TYPE,
        "contract_version": CONTRACT_VERSION,
        "selected_flow_id": selected_flow_id,
        "source_selected_review_scope_id": source_selected_review_scope_id,
        "selected_scope_validation_status": _enum_value(
            ScopeValidationStatus,
            selected_scope_validation_status,
            ScopeValidationStatus.INVALID,
        ).value,
        "diagnostic_evidence": diagnostic_evidence.to_dict(),
        "historical_evidence": historical_evidence.to_dict(),
        "comparative_evidence": comparative_evidence.to_dict(),
        "deep_analysis_evidence": deep_analysis_evidence.to_dict(),
        "recommendation_action_evidence": recommendation_action_evidence.to_dict(),
        "learning_governance_evidence": learning_governance_evidence.to_dict(),
        "evidence_rows": [row.to_dict() for row in evidence_rows],
        "metric_summaries": [summary.to_dict() for summary in metric_summaries],
        "trend_summaries": [summary.to_dict() for summary in trend_summaries],
        "anomaly_summaries": [summary.to_dict() for summary in anomaly_summaries],
        "similarity_context": [context.to_dict() for context in similarity_context],
        "confidence_basis": [basis.to_dict() for basis in confidence_basis],
        "missing_evidence": [missing.to_dict() for missing in missing_evidence],
        "unavailable_evidence": [unavailable.to_dict() for unavailable in unavailable_evidence],
        "stale_evidence": [stale.to_dict() for stale in stale_evidence],
        "allowed_visualizations": [visual.to_dict() for visual in allowed_visualizations],
        "llm_explanation_eligibility": [
            eligibility.to_dict() for eligibility in llm_explanation_eligibility
        ],
    }
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"evidence-pack:{digest[:24]}"


def validate_evidence_pack_contract(
    contract: EvidencePackContract | Mapping[str, Any],
) -> EvidencePackContract:
    if isinstance(contract, Mapping):
        contract = evidence_pack_from_dict(contract)
    if not isinstance(contract, EvidencePackContract):
        raise TypeError("contract must be EvidencePackContract or mapping.")

    errors = list(contract.validation_errors)
    warnings = list(contract.warnings)
    if contract.contract_type != CONTRACT_TYPE:
        errors.append(
            EvidenceIssue("contract_type_invalid", "Evidence pack contract_type is invalid.")
        )
    if contract.contract_version != CONTRACT_VERSION:
        errors.append(
            EvidenceIssue("contract_version_invalid", "Evidence pack contract_version is invalid.")
        )
    if contract.selected_flow_id != contract.source_selected_review_scope_id:
        errors.append(
            EvidenceIssue(
                "selected_scope_linkage_mismatch",
                "selected_flow_id must match source_selected_review_scope_id.",
            )
        )
    if not contract.provenance.is_present():
        errors.append(EvidenceIssue("provenance_required", "Evidence pack provenance is required."))

    expected_pack_id = compute_evidence_pack_id(
        selected_flow_id=contract.selected_flow_id,
        source_selected_review_scope_id=contract.source_selected_review_scope_id,
        selected_scope_validation_status=contract.selected_scope_validation_status,
        diagnostic_evidence=contract.diagnostic_evidence,
        historical_evidence=contract.historical_evidence,
        comparative_evidence=contract.comparative_evidence,
        deep_analysis_evidence=contract.deep_analysis_evidence,
        recommendation_action_evidence=contract.recommendation_action_evidence,
        learning_governance_evidence=contract.learning_governance_evidence,
        evidence_rows=contract.evidence_rows,
        metric_summaries=contract.metric_summaries,
        trend_summaries=contract.trend_summaries,
        anomaly_summaries=contract.anomaly_summaries,
        similarity_context=contract.similarity_context,
        confidence_basis=contract.confidence_basis,
        missing_evidence=contract.missing_evidence,
        unavailable_evidence=contract.unavailable_evidence,
        stale_evidence=contract.stale_evidence,
        allowed_visualizations=contract.allowed_visualizations,
        llm_explanation_eligibility=contract.llm_explanation_eligibility,
    )
    if contract.evidence_pack_id != expected_pack_id:
        errors.append(
            EvidenceIssue("evidence_pack_id_mismatch", "evidence_pack_id is not deterministic for content.")
        )

    status = _determine_validation_status(
        selected_scope_validation_status=contract.selected_scope_validation_status,
        errors=errors,
        warnings=warnings,
        missing=contract.missing_evidence,
        unavailable=contract.unavailable_evidence,
        stale=contract.stale_evidence,
    )
    return replace(
        contract,
        evidence_pack_id=expected_pack_id,
        validation_status=status,
        validation_errors=tuple(_dedupe_issues(errors)),
        warnings=tuple(_dedupe_issues(warnings)),
    )


def evidence_pack_to_dict(contract: EvidencePackContract) -> dict[str, Any]:
    return {
        "contract_type": contract.contract_type,
        "contract_version": contract.contract_version,
        "evidence_pack_id": contract.evidence_pack_id,
        "selected_flow_id": contract.selected_flow_id,
        "source_selected_review_scope_id": contract.source_selected_review_scope_id,
        "source_selected_review_scope_contract_type": contract.source_selected_review_scope_contract_type,
        "selected_scope_validation_status": contract.selected_scope_validation_status.value,
        "diagnostic_evidence": contract.diagnostic_evidence.to_dict(),
        "historical_evidence": contract.historical_evidence.to_dict(),
        "comparative_evidence": contract.comparative_evidence.to_dict(),
        "deep_analysis_evidence": contract.deep_analysis_evidence.to_dict(),
        "recommendation_action_evidence": contract.recommendation_action_evidence.to_dict(),
        "learning_governance_evidence": contract.learning_governance_evidence.to_dict(),
        "evidence_rows": [row.to_dict() for row in contract.evidence_rows],
        "metric_summaries": [summary.to_dict() for summary in contract.metric_summaries],
        "trend_summaries": [summary.to_dict() for summary in contract.trend_summaries],
        "anomaly_summaries": [summary.to_dict() for summary in contract.anomaly_summaries],
        "similarity_context": [context.to_dict() for context in contract.similarity_context],
        "confidence_basis": [basis.to_dict() for basis in contract.confidence_basis],
        "missing_evidence": [missing.to_dict() for missing in contract.missing_evidence],
        "unavailable_evidence": [unavailable.to_dict() for unavailable in contract.unavailable_evidence],
        "stale_evidence": [stale.to_dict() for stale in contract.stale_evidence],
        "allowed_visualizations": [visual.to_dict() for visual in contract.allowed_visualizations],
        "llm_explanation_eligibility": [
            eligibility.to_dict() for eligibility in contract.llm_explanation_eligibility
        ],
        "provenance": contract.provenance.to_dict(),
        "validation_status": contract.validation_status.value,
        "validation_errors": [issue.to_dict() for issue in contract.validation_errors],
        "warnings": [issue.to_dict() for issue in contract.warnings],
    }


def evidence_pack_from_dict(data: Mapping[str, Any]) -> EvidencePackContract:
    contract = EvidencePackContract(
        contract_type=str(data.get("contract_type") or CONTRACT_TYPE),
        contract_version=str(data.get("contract_version") or CONTRACT_VERSION),
        evidence_pack_id=str(data.get("evidence_pack_id") or "evidence-pack:none"),
        selected_flow_id=str(data.get("selected_flow_id") or ""),
        source_selected_review_scope_id=str(data.get("source_selected_review_scope_id") or ""),
        source_selected_review_scope_contract_type=str(
            data.get("source_selected_review_scope_contract_type")
            or "selected_review_scope_contract"
        ),
        selected_scope_validation_status=_enum_value(
            ScopeValidationStatus,
            data.get("selected_scope_validation_status"),
            ScopeValidationStatus.INVALID,
        ),
        diagnostic_evidence=_section_from_value(data.get("diagnostic_evidence"), EvidenceDomain.DIAGNOSTIC),
        historical_evidence=_section_from_value(data.get("historical_evidence"), EvidenceDomain.HISTORICAL),
        comparative_evidence=_section_from_value(data.get("comparative_evidence"), EvidenceDomain.COMPARATIVE),
        deep_analysis_evidence=_section_from_value(data.get("deep_analysis_evidence"), EvidenceDomain.DEEP_ANALYSIS),
        recommendation_action_evidence=_section_from_value(
            data.get("recommendation_action_evidence"),
            EvidenceDomain.RECOMMENDATION_ACTION,
        ),
        learning_governance_evidence=_section_from_value(
            data.get("learning_governance_evidence"),
            EvidenceDomain.LEARNING_GOVERNANCE,
        ),
        evidence_rows=tuple(
            EvidenceRow.from_value(row, _enum_value(EvidenceDomain, row.get("domain") if isinstance(row, Mapping) else None, EvidenceDomain.DIAGNOSTIC))
            for row in data.get("evidence_rows", ())
        ),
        metric_summaries=tuple(
            MetricSummary.from_value(summary, EvidenceDomain.DIAGNOSTIC)
            for summary in data.get("metric_summaries", ())
        ),
        trend_summaries=tuple(
            TrendSummary.from_value(summary, EvidenceDomain.DIAGNOSTIC)
            for summary in data.get("trend_summaries", ())
        ),
        anomaly_summaries=tuple(
            AnomalySummary.from_value(summary, EvidenceDomain.DIAGNOSTIC)
            for summary in data.get("anomaly_summaries", ())
        ),
        similarity_context=tuple(
            SimilarityContext.from_value(context, EvidenceDomain.DIAGNOSTIC)
            for context in data.get("similarity_context", ())
        ),
        confidence_basis=tuple(
            ConfidenceBasis.from_value(basis, EvidenceDomain.DIAGNOSTIC)
            for basis in data.get("confidence_basis", ())
        ),
        missing_evidence=tuple(MissingEvidence.from_value(item) for item in data.get("missing_evidence", ())),
        unavailable_evidence=tuple(
            UnavailableEvidence.from_value(item) for item in data.get("unavailable_evidence", ())
        ),
        stale_evidence=tuple(StaleEvidence.from_value(item) for item in data.get("stale_evidence", ())),
        allowed_visualizations=tuple(
            AllowedVisualization.from_value(item) for item in data.get("allowed_visualizations", ())
        ),
        llm_explanation_eligibility=tuple(
            LLMExplanationEligibility.from_value(item)
            for item in data.get("llm_explanation_eligibility", ())
        ),
        provenance=EvidenceProvenance.from_value(data.get("provenance")),
        validation_status=_enum_value(
            EvidencePackValidationStatus,
            data.get("validation_status"),
            EvidencePackValidationStatus.INVALID,
        ),
        validation_errors=tuple(
            EvidenceIssue.from_value(item) for item in data.get("validation_errors", ())
        ),
        warnings=tuple(EvidenceIssue.from_value(item) for item in data.get("warnings", ())),
    )
    return validate_evidence_pack_contract(contract)


def is_evidence_pack_valid(contract: EvidencePackContract | Mapping[str, Any]) -> bool:
    return validate_evidence_pack_contract(contract).validation_status == EvidencePackValidationStatus.VALID


def get_missing_evidence_by_domain(
    contract: EvidencePackContract,
    domain: EvidenceDomain | str,
) -> tuple[MissingEvidence, ...]:
    normalized_domain = _enum_value(EvidenceDomain, domain, EvidenceDomain.DIAGNOSTIC)
    return tuple(item for item in contract.missing_evidence if item.domain == normalized_domain)


def get_allowed_visualizations_by_domain(
    contract: EvidencePackContract,
    domain: EvidenceDomain | str,
) -> tuple[AllowedVisualization, ...]:
    normalized_domain = _enum_value(EvidenceDomain, domain, EvidenceDomain.DIAGNOSTIC)
    return tuple(item for item in contract.allowed_visualizations if item.domain == normalized_domain)


def get_llm_explanation_eligibility_by_domain(
    contract: EvidencePackContract,
    domain: EvidenceDomain | str,
) -> tuple[LLMExplanationEligibility, ...]:
    normalized_domain = _enum_value(EvidenceDomain, domain, EvidenceDomain.DIAGNOSTIC)
    return tuple(item for item in contract.llm_explanation_eligibility if item.domain == normalized_domain)


def make_empty_evidence_pack(
    selected_scope_contract: SelectedReviewScopeContract | Mapping[str, Any],
    *,
    provenance: EvidenceProvenance | Mapping[str, Any] | str | None = None,
    validation_errors: Sequence[EvidenceIssue] = (),
    warnings: Sequence[EvidenceIssue] = (),
) -> EvidencePackContract:
    """Create an empty pack linked to a selected scope contract."""

    selected_scope = validate_selected_review_scope_contract(selected_scope_contract)
    pack_provenance = EvidenceProvenance.from_value(provenance)
    diagnostic = DiagnosticEvidence()
    historical = HistoricalEvidence()
    comparative = ComparativeEvidence()
    deep = DeepAnalysisEvidence()
    action = RecommendationActionEvidence()
    learning = LearningGovernanceEvidence()
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
        evidence_rows=(),
        metric_summaries=(),
        trend_summaries=(),
        anomaly_summaries=(),
        similarity_context=(),
        confidence_basis=(),
        missing_evidence=(),
        unavailable_evidence=(),
        stale_evidence=(),
        allowed_visualizations=(),
        llm_explanation_eligibility=(),
        provenance=pack_provenance,
        validation_status=EvidencePackValidationStatus.INVALID,
        validation_errors=tuple(validation_errors),
        warnings=tuple(warnings),
    )
    return validate_evidence_pack_contract(contract)


def _determine_validation_status(
    *,
    selected_scope_validation_status: ScopeValidationStatus,
    errors: Sequence[EvidenceIssue],
    warnings: Sequence[EvidenceIssue],
    missing: Sequence[MissingEvidence],
    unavailable: Sequence[UnavailableEvidence],
    stale: Sequence[StaleEvidence],
) -> EvidencePackValidationStatus:
    if selected_scope_validation_status == ScopeValidationStatus.UNAVAILABLE:
        return EvidencePackValidationStatus.UNAVAILABLE
    if selected_scope_validation_status == ScopeValidationStatus.INVALID:
        return EvidencePackValidationStatus.INVALID
    if errors:
        return EvidencePackValidationStatus.INVALID
    if (
        selected_scope_validation_status == ScopeValidationStatus.PARTIAL
        or missing
        or unavailable
        or stale
        or warnings
    ):
        return EvidencePackValidationStatus.PARTIAL
    return EvidencePackValidationStatus.VALID


def _section_from_value(value: Any, domain: EvidenceDomain) -> _EvidenceSection:
    section_type = SECTION_TYPES[domain]
    if isinstance(value, _EvidenceSection):
        return value
    if not isinstance(value, Mapping):
        return section_type()
    return section_type(
        availability_status=_enum_value(
            EvidenceAvailabilityStatus,
            value.get("availability_status"),
            EvidenceAvailabilityStatus.MISSING,
        ),
        evidence_ids=_tuple_of_strings(value.get("evidence_ids")),
        rows=tuple(EvidenceRow.from_value(row, domain) for row in value.get("rows", ())),
        summary=_clean_string(value.get("summary")),
        freshness=EvidenceFreshness.from_value(value.get("freshness")),
        provenance=EvidenceProvenance.from_value(value.get("provenance")),
    )


def _stable_id(prefix: str, payload: Any) -> str:
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{prefix}:{digest[:16]}"


def _dedupe_issues(issues: Sequence[EvidenceIssue]) -> tuple[EvidenceIssue, ...]:
    seen: set[tuple[str, EvidenceDomain | None, str | None]] = set()
    deduped: list[EvidenceIssue] = []
    for issue in issues:
        key = (issue.code, issue.domain, issue.field)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    return tuple(deduped)

