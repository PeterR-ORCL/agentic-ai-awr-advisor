"""Production adapter for contract-backed dashboard screen rendering.

This module normalizes deterministic production report data into the explicit
contract spine. It does not read generated dashboard artifacts, browser state,
cache state, or LLM output as evidence.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from src.reporting.dashboard.adapters.dashboard_screen_adapter import (
    DashboardScreenRenderBundle,
    build_dashboard_screen_render_bundle,
)
from src.reporting.dashboard.contracts.selected_review_scope_contract import (
    ReviewMode,
    SourceMode,
    build_selected_review_scope_contract,
)


AUTHORITATIVE_SELECTION_FIELDS = {
    "metadata",
    "ingestion_context",
    "analysis_context",
    "comparison_context",
    "snapshot_labels",
}

DETERMINISTIC_EVIDENCE_FIELDS = {
    "scores",
    "trends",
    "anomalies",
    "decision",
    "recommendations",
    "grouped_deterministic_findings",
    "analysis_output",
    "top_sql",
    "summary_key_signals",
    "derived_pressure_metrics",
    "derived_scalar_metrics",
    "time_series",
    "db_scope_metrics",
    "anomaly_windows",
    "multi_snapshot_summary",
    "latest_snapshot_summary",
    "decision_posture",
    "confidence",
    "memory_runtime",
}

INSUFFICIENTLY_NORMALIZED_FIELDS = {
    "time_series_charts",
    "violin_panel",
}

TRANSITIONAL_DISPLAY_FIELDS = {
    "title",
    "generated_at",
    "dashboard_generated_session_id",
    "product",
    "executive_summary",
    "screen_models",
}

LLM_FIELDS = {
    "llm_explanation",
    "ai_generated_narrative",
    "ai_provider",
    "ai_model",
}

LEGACY_FALLBACK_FIELDS = {
    "compatibility",
    "issues",
    "agentic_decision",
    "oci_guidance",
}


@dataclass(frozen=True)
class RejectedProductionField:
    field_path: str
    category: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {
            "field_path": self.field_path,
            "category": self.category,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ProductionContractBundleReadiness:
    is_ready: bool
    selected_scope_ready: bool
    evidence_payloads_ready: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    authoritative_fields: tuple[str, ...]
    deterministic_evidence_fields: tuple[str, ...]
    rejected_fields: tuple[RejectedProductionField, ...]
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_ready": self.is_ready,
            "selected_scope_ready": self.selected_scope_ready,
            "evidence_payloads_ready": self.evidence_payloads_ready,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "authoritative_fields": list(self.authoritative_fields),
            "deterministic_evidence_fields": list(self.deterministic_evidence_fields),
            "rejected_fields": [field.to_dict() for field in self.rejected_fields],
            "recommendation": self.recommendation,
        }


def inspect_production_contract_bundle_readiness(
    report_data: Mapping[str, Any],
) -> ProductionContractBundleReadiness:
    """Inspect whether production report data can build a real render bundle."""

    if not isinstance(report_data, Mapping):
        raise TypeError("report_data must be a mapping.")

    selected_scope_ready = _can_normalize_selected_scope(report_data)
    evidence_payloads_ready = bool(_build_diagnostic_payload(report_data))
    authoritative_fields = tuple(
        key
        for key in sorted(report_data)
        if _classify_top_level_field(key) == "authoritative deterministic selection input"
    )
    deterministic_evidence_fields = tuple(
        key
        for key in sorted(report_data)
        if _classify_top_level_field(key) == "deterministic evidence input"
    )
    rejected_fields = tuple(_rejected_fields(report_data))

    blockers: list[str] = []
    warnings: list[str] = []
    if not selected_scope_ready:
        blockers.append(
            "Production report_data does not contain enough deterministic run, report, "
            "database, and snapshot identity to normalize selected_review_scope_contract."
        )
    if not evidence_payloads_ready:
        blockers.append(
            "Production report_data does not contain enough deterministic diagnostic "
            "evidence to build Screen 3 payloads."
        )
    if not _comparison_targets_available(report_data):
        warnings.append(
            "Target A/B comparison selections are not present; comparative review will "
            "remain explicitly unavailable."
        )
    if not _deep_analysis_available(report_data):
        warnings.append(
            "Deep-analysis payloads are not present; deep analysis will remain explicitly unavailable."
        )

    is_ready = selected_scope_ready and evidence_payloads_ready and not blockers
    recommendation = (
        "Production contract-backed regeneration may proceed for the current "
        "runtime/report scope; comparative/deep modes remain gated by explicit inputs."
        if is_ready
        else "Do not regenerate production dashboard artifacts until authoritative "
        "selection identity and deterministic diagnostic evidence are supplied."
    )

    return ProductionContractBundleReadiness(
        is_ready=is_ready,
        selected_scope_ready=selected_scope_ready,
        evidence_payloads_ready=evidence_payloads_ready,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        authoritative_fields=authoritative_fields,
        deterministic_evidence_fields=deterministic_evidence_fields,
        rejected_fields=rejected_fields,
        recommendation=recommendation,
    )


def build_production_selected_review_scope_contract(report_data: Mapping[str, Any]):
    """Normalize production run/report/window identity into selected scope."""

    if not _can_normalize_selected_scope(report_data):
        raise ValueError("Production report_data cannot be normalized into selected scope.")

    metadata = _mapping(report_data.get("metadata"))
    analysis_context = _mapping(report_data.get("analysis_context"))
    ingestion_context = _mapping(report_data.get("ingestion_context"))
    snapshot_labels = _strings(report_data.get("snapshot_labels"))
    db_id = _first_text(metadata, "dbid", "db_id", "database_id")
    db_name = _first_text(metadata, "db_name", "database_name")
    instance_name = _first_text(metadata, "instance_name")
    file_name = _first_text(metadata, "file_name")
    awr_id = _first_text(metadata, "awr_id", "report_id") or file_name
    begin_time = _first_text(metadata, "snapshot_begin", "begin_time")
    end_time = _first_text(metadata, "snapshot_end", "end_time")
    source_database = _first_text(analysis_context, "source_database")
    window_label = (
        _first_text(analysis_context, "latest_snapshot_interval")
        or _first_text(analysis_context, "time_window")
        or "current production analysis window"
    )
    source_mode = _first_text(ingestion_context, "source_mode") or "LOCAL"
    database_id = db_id or db_name or source_database
    snapshot_window_id = _stable_id(
        "window",
        {
            "begin_time": begin_time,
            "end_time": end_time,
            "snapshot_labels": snapshot_labels,
        },
    )
    runtime_scope = {
        "scope_id": _stable_id(
            "runtime_scope",
            {
                "database_id": database_id,
                "file_name": file_name,
                "begin_time": begin_time,
                "end_time": end_time,
                "snapshot_labels": snapshot_labels,
            },
        ),
        "label": source_database or db_name or file_name or "Production runtime scope",
        "report_id": awr_id,
        "database_id": database_id,
        "snapshot_window_id": snapshot_window_id,
        "alignment_key": database_id,
    }
    report_identity = {
        "report_id": awr_id or runtime_scope["scope_id"],
        "label": file_name or window_label,
        "source_path": file_name,
    }
    database_identity = {
        "database_id": database_id,
        "database_name": db_name,
        "instance_name": instance_name,
    }
    selected_window = {
        "window_id": snapshot_window_id,
        "begin_time": begin_time,
        "end_time": end_time,
        "label": window_label,
    }
    historical_available = bool(len(snapshot_labels) > 1 or report_data.get("time_series"))
    requested_modes = [ReviewMode.DIAGNOSTIC_SNAPSHOT]
    if historical_available:
        requested_modes.append(ReviewMode.HISTORICAL_REVIEW)

    return build_selected_review_scope_contract(
        source_mode=SourceMode.NEW_SOURCE if source_mode.upper() == "LOCAL" else SourceMode.EXISTING_EVIDENCE,
        runtime_scope=runtime_scope,
        selected_report=report_identity,
        selected_database=database_identity,
        selected_window=selected_window,
        review_mode_intent={
            "requested_modes": requested_modes,
            "historical_evidence_available": historical_available,
            "deep_analysis_requested": False,
            "deep_analysis_available": False,
        },
        provenance={
            "source_system": "scripts.run_analysis.report_data",
            "operator_action_id": "production-runtime-input-scope",
            "created_at": _first_text(report_data, "generated_at"),
        },
    )


def build_production_dashboard_screen_render_bundle(
    report_data: Mapping[str, Any],
) -> DashboardScreenRenderBundle:
    """Build a production contract-backed Screen 3/4/5/6 render bundle."""

    readiness = inspect_production_contract_bundle_readiness(report_data)
    if not readiness.is_ready:
        raise RuntimeError(readiness.recommendation)

    selected_scope = build_production_selected_review_scope_contract(report_data)
    return build_dashboard_screen_render_bundle(
        selected_scope,
        diagnostic_payload=_build_diagnostic_payload(report_data),
        historical_payload=_build_historical_payload(report_data),
        comparative_payload=None,
        deep_analysis_payload=None,
        recommendation_action_payload=_build_recommendation_action_payload(report_data),
        learning_governance_payload=_build_learning_governance_payload(report_data),
        provenance={
            "source_system": "scripts.run_analysis.report_data",
            "builder_version": "production_contract_bundle_adapter.v1",
            "generated_at": _first_text(report_data, "generated_at"),
            "deterministic_sources": (
                "metadata",
                "scores",
                "trends",
                "anomalies",
                "decision",
                "recommendations",
                "time_series",
                "db_scope_metrics",
                "memory_runtime",
            ),
        },
    )


def require_production_contract_bundle_ready(
    report_data: Mapping[str, Any],
) -> ProductionContractBundleReadiness:
    """Fail closed when production report data cannot build a real bundle."""

    readiness = inspect_production_contract_bundle_readiness(report_data)
    if not readiness.is_ready:
        raise RuntimeError(readiness.recommendation)
    return readiness


def _can_normalize_selected_scope(report_data: Mapping[str, Any]) -> bool:
    metadata = _mapping(report_data.get("metadata"))
    analysis_context = _mapping(report_data.get("analysis_context"))
    has_database_identity = bool(
        _first_text(metadata, "dbid", "db_id", "database_id", "db_name", "database_name")
        or _first_text(analysis_context, "source_database")
    )
    has_report_identity = bool(
        _first_text(metadata, "awr_id", "report_id", "file_name")
        or _strings(report_data.get("snapshot_labels"))
    )
    has_window_identity = bool(
        _first_text(metadata, "snapshot_begin", "begin_time")
        or _first_text(metadata, "snapshot_end", "end_time")
        or _first_text(analysis_context, "time_window", "latest_snapshot_interval")
    )
    return has_database_identity and has_report_identity and has_window_identity


def _comparison_targets_available(report_data: Mapping[str, Any]) -> bool:
    return isinstance(report_data.get("target_a"), Mapping) and isinstance(report_data.get("target_b"), Mapping)


def _deep_analysis_available(report_data: Mapping[str, Any]) -> bool:
    return isinstance(report_data.get("deep_analysis_payload"), Mapping)


def _build_diagnostic_payload(report_data: Mapping[str, Any]) -> dict[str, Any]:
    metrics = _domain_score_metrics(report_data)
    metrics.extend(_derived_scalar_metrics(report_data))
    trends = _trend_summaries(report_data)
    anomalies = _anomaly_summaries(report_data)
    confidence = _confidence_basis(report_data, "diagnostic-confidence")
    rows = _evidence_rows(report_data)
    if not any((metrics, trends, anomalies, confidence, rows)):
        return {}
    return {
        "evidence_ids": ("production:diagnostic",),
        "rows": rows,
        "metrics": metrics,
        "trends": trends,
        "anomalies": anomalies,
        "confidence_basis": confidence,
        "summary": _first_text(report_data, "latest_snapshot_summary"),
        "provenance": {"source_system": "scripts.run_analysis.report_data"},
    }


def _build_historical_payload(report_data: Mapping[str, Any]) -> dict[str, Any] | None:
    trends = _time_series_trends(report_data)
    anomalies = _anomaly_summaries(report_data)
    confidence = _confidence_basis(report_data, "historical-confidence")
    if not any((trends, anomalies, confidence)):
        return None
    return {
        "evidence_ids": ("production:historical",),
        "trends": trends,
        "anomalies": anomalies,
        "confidence_basis": confidence,
        "summary": _first_text(report_data, "multi_snapshot_summary"),
        "provenance": {"source_system": "scripts.run_analysis.report_data"},
    }


def _build_recommendation_action_payload(report_data: Mapping[str, Any]) -> dict[str, Any] | None:
    recommendations = _sequence(report_data.get("recommendations"))
    if not recommendations:
        return None
    rows = []
    for index, item in enumerate(recommendations):
        if not isinstance(item, Mapping):
            continue
        rows.append(
            {
                "row_id": f"recommendation:{index}",
                "values": {
                    "action": item.get("action"),
                    "impact": item.get("impact"),
                    "confidence": item.get("confidence"),
                    "category": item.get("category"),
                },
                "source": "analysis_output.recommendations",
            }
        )
    return {
        "evidence_ids": ("production:recommendation_action",),
        "rows": rows,
        "confidence_basis": _confidence_basis(report_data, "action-confidence"),
        "summary": "Deterministic recommendation/action payload from analysis output.",
        "provenance": {"source_system": "scripts.run_analysis.report_data"},
    }


def _build_learning_governance_payload(report_data: Mapping[str, Any]) -> dict[str, Any] | None:
    memory_runtime = _mapping(report_data.get("memory_runtime"))
    if not memory_runtime:
        return None
    return {
        "evidence_ids": ("production:learning_governance",),
        "rows": (
            {
                "row_id": "memory_runtime",
                "values": {
                    "enabled": memory_runtime.get("enabled"),
                    "success": memory_runtime.get("success"),
                    "state": memory_runtime.get("state"),
                },
                "source": "memory_runtime",
            },
        ),
        "summary": "Governed memory runtime status from deterministic run output.",
        "provenance": {"source_system": "scripts.run_analysis.report_data"},
    }


def _domain_score_metrics(report_data: Mapping[str, Any]) -> list[dict[str, Any]]:
    scores = _mapping(report_data.get("scores"))
    domain_scores = _mapping(scores.get("domain_scores"))
    return [
        {
            "metric_name": f"domain_score_{key}",
            "value": value,
            "source_evidence_ids": ("production:diagnostic",),
        }
        for key, value in sorted(domain_scores.items())
    ]


def _derived_scalar_metrics(report_data: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "metric_name": key,
            "value": value,
            "source_evidence_ids": ("production:diagnostic",),
        }
        for key, value in sorted(_mapping(report_data.get("derived_scalar_metrics")).items())
    ]


def _trend_summaries(report_data: Mapping[str, Any]) -> list[dict[str, Any]]:
    trends = _mapping(report_data.get("trends"))
    findings = _sequence(trends.get("findings"))
    return [
        {
            "trend_name": f"finding_{index}",
            "direction": str(finding),
        }
        for index, finding in enumerate(findings)
    ]


def _time_series_trends(report_data: Mapping[str, Any]) -> list[dict[str, Any]]:
    time_series = _mapping(report_data.get("time_series"))
    trends = []
    for name, values in sorted(time_series.items()):
        points = [
            {"index": index, "value": value}
            for index, value in enumerate(_sequence(values))
        ]
        if points:
            trends.append({"trend_name": str(name), "points": points})
    return trends


def _anomaly_summaries(report_data: Mapping[str, Any]) -> list[dict[str, Any]]:
    anomalies = _sequence(report_data.get("anomaly_windows"))
    if not anomalies:
        anomalies = _sequence(_mapping(report_data.get("anomalies")).get("windows"))
    summaries = []
    for index, item in enumerate(anomalies):
        if isinstance(item, Mapping):
            summaries.append(
                {
                    "anomaly_name": str(item.get("metric") or item.get("name") or f"anomaly_{index}"),
                    "severity": str(item.get("severity") or "info").lower(),
                    "description": str(item.get("reason") or item.get("description") or ""),
                }
            )
        else:
            summaries.append({"anomaly_name": f"anomaly_{index}", "description": str(item)})
    return summaries


def _confidence_basis(report_data: Mapping[str, Any], basis_id: str) -> list[dict[str, Any]]:
    confidence = _mapping(report_data.get("confidence"))
    if not confidence:
        decision = _mapping(report_data.get("decision"))
        confidence_value = decision.get("confidence")
        return (
            [{"basis_id": basis_id, "confidence": str(confidence_value)}]
            if confidence_value is not None
            else []
        )
    return [
        {
            "basis_id": basis_id,
            "confidence": _first_text(confidence, "level") or _first_text(confidence, "confidence"),
            "factors": tuple(str(item) for item in _sequence(confidence.get("reasons") or confidence.get("factors"))),
        }
    ]


def _evidence_rows(report_data: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, signal in enumerate(_sequence(report_data.get("summary_key_signals"))):
        rows.append(
            {
                "row_id": f"summary_signal:{index}",
                "values": {"signal": signal},
                "source": "summary_key_signals",
            }
        )
    decision = _mapping(report_data.get("decision"))
    if decision:
        rows.append(
            {
                "row_id": "decision",
                "values": {
                    key: decision.get(key)
                    for key in ("primary_domain", "risk_level", "confidence")
                    if key in decision
                },
                "source": "analysis_output.decision",
            }
        )
    return rows


def _classify_top_level_field(field_name: str) -> str:
    if field_name in AUTHORITATIVE_SELECTION_FIELDS:
        return "authoritative deterministic selection input"
    if field_name in DETERMINISTIC_EVIDENCE_FIELDS:
        return "deterministic evidence input"
    if field_name in INSUFFICIENTLY_NORMALIZED_FIELDS:
        return "possibly usable but insufficiently normalized"
    if field_name in TRANSITIONAL_DISPLAY_FIELDS:
        return "transitional compatibility/display field"
    if field_name in LLM_FIELDS:
        return "LLM explanation"
    if field_name in LEGACY_FALLBACK_FIELDS:
        return "legacy fallback copy"
    if field_name in {"browser_state", "hash_state", "localStorage", "local_storage"}:
        return "browser/cache/UI state"
    if field_name in {"generated_html", "generated_html_path", "dashboard_artifact_path"}:
        return "generated HTML/output"
    return "unknown / unsafe"


def _rejected_fields(report_data: Mapping[str, Any]) -> tuple[RejectedProductionField, ...]:
    rejected = []
    for key in sorted(report_data):
        category = _classify_top_level_field(key)
        if category not in {
            "authoritative deterministic selection input",
            "deterministic evidence input",
        }:
            rejected.append(
                RejectedProductionField(
                    field_path=key,
                    category=category,
                    reason="Field is not authoritative contract input for production bundle construction.",
                )
            )
    rejected.extend(_scan_for_forbidden_authority(report_data))
    return _dedupe_rejected_fields(rejected)


def _scan_for_forbidden_authority(value: Any, path: str = "") -> list[RejectedProductionField]:
    rejected: list[RejectedProductionField] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            category = _forbidden_key_category(str(key), child)
            if category:
                rejected.append(
                    RejectedProductionField(
                        field_path=child_path,
                        category=category,
                        reason="Nested field cannot be used as production evidence authority.",
                    )
                )
            rejected.extend(_scan_for_forbidden_authority(child, child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            rejected.extend(_scan_for_forbidden_authority(child, f"{path}[{index}]"))
    return rejected


def _forbidden_key_category(key: str, value: Any) -> str | None:
    normalized = key.lower()
    if normalized in {"localstorage", "local_storage", "browser_state", "hash_state"}:
        return "browser/cache/UI state"
    if normalized in {"selector_state", "runtime_selector", "cache_continuity"}:
        return "browser/cache/UI state"
    if normalized in {"generated_html", "rendered_html", "chart_markup", "html"}:
        return "generated HTML/output"
    if normalized in {"dashboard_artifact_path", "generated_html_path"}:
        return "generated HTML/output"
    if isinstance(value, str) and "awr_dashboard/" in value:
        return "generated HTML/output"
    if "llm" in normalized or normalized in {"ai_generated_narrative", "ai_provider", "ai_model"}:
        return "LLM explanation"
    if normalized in LEGACY_FALLBACK_FIELDS or "fallback" in normalized:
        return "legacy fallback copy"
    return None


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return (value,)


def _strings(value: Any) -> tuple[str, ...]:
    return tuple(str(item) for item in _sequence(value) if str(item or "").strip())


def _first_text(source: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = source.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _stable_id(prefix: str, payload: Any) -> str:
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _dedupe_rejected_fields(
    rejected: Sequence[RejectedProductionField],
) -> tuple[RejectedProductionField, ...]:
    seen: set[tuple[str, str]] = set()
    deduped: list[RejectedProductionField] = []
    for item in rejected:
        key = (item.field_path, item.category)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return tuple(deduped)
