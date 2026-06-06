"""Screen 4 Deep Analysis deterministic contract builder.

This module assembles plain mapping payloads for the 7CY Deep Analysis
contract validator. It is intentionally non-rendering and non-mutating: it does
not read files, call services, invoke LLMs, query databases, execute parsers,
run comparisons, or depend on generated dashboard artifacts.
"""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from src.reporting.dashboard.screen4.deep_analysis_contract import (
    CONTRACT_TYPE,
    MUTATION_BOUNDARY_FLAGS,
    SUPPORTED_CONTRACT_VERSION,
    DeepAnalysisValidationResult,
    ScopeClassification,
    validate_deep_analysis_contract,
)


DEEP_ANALYSIS_BUILDER_VERSION = "7cy-deep-analysis-builder-v1"
DETERMINISTIC_ENGINE_VERSION = "phase7cy-deep-analysis-v1"
DEFAULT_GENERATED_BY = "deterministic_backend"
CURRENT_SOURCE_SCOPE = "current_selected_diagnostic_scope"

_COMPARATIVE_KEYS = {
    "comparative_review_state",
    "comparison_state",
    "comparison_review_state",
    "deterministic_comparison_output",
    "metric_deltas",
    "domain_deltas",
    "allowed_visualizations",
    "visual_eligibility",
}
_PREPARED_KEYS = {
    "comparison_prepared_context",
    "prepared_target_context",
    "prepared_targets",
    "target_a",
    "target_b",
    "selectedComparisonTargetA",
    "selectedComparisonTargetB",
}
_CACHE_KEYS = {
    "browser_cache_state",
    "localStorage",
    "local_storage",
    "hash_state",
    "route_state",
}
_LLM_KEYS = {
    "llm_explanation",
    "llm_vocalization",
    "technical_explanation",
    "executive_explanation",
    "action_explanation",
}


def build_deep_analysis_contract(
    *,
    report_data: Mapping[str, Any],
    selected_scope: Mapping[str, Any],
    screen_model: Mapping[str, Any] | None = None,
    chart_payload: Mapping[str, Any] | None = None,
    generation_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a conservative Screen 4 Deep Analysis contract mapping.

    The returned contract may be invalid if required provenance, freshness, or
    selected-scope identifiers are absent. Readiness is owned only by
    ``validate_deep_analysis_contract``.
    """

    report = _mapping(report_data)
    selected = _mapping(selected_scope)
    screen = _mapping(screen_model)
    charts = _mapping(chart_payload)
    context = _mapping(generation_context)

    provenance = _resolve_mapping(
        context.get("provenance"),
        report.get("provenance"),
        selected.get("provenance"),
        screen.get("provenance"),
    )
    freshness = _resolve_mapping(
        context.get("freshness"),
        report.get("freshness"),
        selected.get("freshness"),
        screen.get("freshness"),
    )
    if not freshness and _selected_scope_is_cache_only(selected):
        freshness = {"freshness_status": "cache_only", "source_path": "selected_scope.cache_status"}

    selected_run_id = _first_text(
        selected.get("selected_run_id"),
        selected.get("run_id"),
        _nested_get(report, ("metadata", "selected_run_id")),
        _nested_get(report, ("metadata", "run_id")),
        report.get("analysis_run_id"),
        _nested_get(screen, ("header", "analysis_run_id")),
        _nested_get(screen, ("header", "run_id")),
    )
    selected_source_identifier = _selected_source_identifier(report, selected, screen)
    selected_snapshot_identifier = _selected_snapshot_identifier(report, selected, screen)
    current_ref = _current_diagnostic_output_ref(report, selected, screen, selected_run_id)
    immutable_truth_refs = _resolve_mapping(
        context.get("immutable_truth_refs"),
        selected.get("immutable_truth_refs"),
        report.get("immutable_truth_refs"),
        screen.get("immutable_truth_refs"),
    )
    if not immutable_truth_refs:
        immutable_truth_refs = _immutable_truth_refs(report, screen)

    evidence_sections: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    missing_evidence: list[dict[str, Any]] = []
    limitations: list[dict[str, Any]] = []

    _append_current_diagnostic_rows(
        evidence_sections=evidence_sections,
        evidence_rows=evidence_rows,
        missing_evidence=missing_evidence,
        report=report,
        screen=screen,
        provenance=provenance,
        freshness=freshness,
    )
    _append_current_top_sql_rows(
        evidence_sections=evidence_sections,
        evidence_rows=evidence_rows,
        missing_evidence=missing_evidence,
        report=report,
        provenance=provenance,
        freshness=freshness,
    )
    _append_current_chart_rows(
        evidence_sections=evidence_sections,
        evidence_rows=evidence_rows,
        charts=charts,
        provenance=provenance,
        freshness=freshness,
    )
    _append_historical_support_rows(
        evidence_sections=evidence_sections,
        evidence_rows=evidence_rows,
        report=report,
        screen=screen,
        charts=charts,
        provenance=provenance,
        freshness=freshness,
    )

    _append_input_boundary_limitations(
        limitations=limitations,
        report=report,
        selected=selected,
        screen=screen,
        charts=charts,
    )
    if not any(row.get("scope_classification") == ScopeClassification.CURRENT_SCOPE.value for row in evidence_rows):
        missing_evidence.append(
            {
                "type": "current_scope_evidence_missing",
                "field": "report_data.decision/report_data.scores/report_data.issues/report_data.top_sql",
                "reason": "No deterministic current-scope Deep Analysis evidence rows were available in supplied inputs.",
            }
        )
    if not evidence_sections:
        evidence_sections.append(
            _section(
                section_id="missing-current-scope-evidence",
                title="Missing Evidence",
                scope=ScopeClassification.CURRENT_SCOPE,
                evidence_type="missing_evidence",
                source_path="report_data",
                provenance=provenance,
                freshness=freshness,
                rows_present=False,
                allowed_rendering="blocked_state",
                display_priority=90,
            )
        )

    contract = {
        "contract_type": CONTRACT_TYPE,
        "contract_version": SUPPORTED_CONTRACT_VERSION,
        "generated_by": DEFAULT_GENERATED_BY,
        "generated_at": _generated_at(context, report, screen),
        "deterministic_engine_version": _first_text(
            context.get("deterministic_engine_version"),
            report.get("deterministic_engine_version"),
            screen.get("deterministic_engine_version"),
            DETERMINISTIC_ENGINE_VERSION,
        ),
        "source_scope": _source_scope(selected),
        "selected_run_id": selected_run_id,
        "selected_source_identifier": selected_source_identifier or None,
        "selected_snapshot_identifier": selected_snapshot_identifier or None,
        "generation_context": _generation_context(context, report, selected, screen),
        "freshness": freshness,
        "provenance": provenance,
        "current_diagnostic_output_ref": current_ref,
        "immutable_truth_refs": dict(immutable_truth_refs),
        "evidence_sections": evidence_sections,
        "evidence_rows": evidence_rows,
        "chart_eligibility": _chart_eligibility(context),
        "limitations": limitations,
        "missing_evidence": missing_evidence,
        "validation_messages": [],
        "llm_explanation_boundary": {
            "llm_may_explain_validated_contract": True,
            "llm_can_create_evidence": False,
            "llm_can_classify_scope": False,
            "llm_can_decide_truth": False,
            "llm_can_choose_chart_eligibility": False,
        },
        "mutation_boundaries": {flag: False for flag in MUTATION_BOUNDARY_FLAGS},
    }
    return contract


def build_and_validate_deep_analysis_contract(
    *,
    report_data: Mapping[str, Any],
    selected_scope: Mapping[str, Any],
    screen_model: Mapping[str, Any] | None = None,
    chart_payload: Mapping[str, Any] | None = None,
    generation_context: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], DeepAnalysisValidationResult]:
    """Build a contract and validate it with the 7CY-C validator."""

    contract = build_deep_analysis_contract(
        report_data=report_data,
        selected_scope=selected_scope,
        screen_model=screen_model,
        chart_payload=chart_payload,
        generation_context=generation_context,
    )
    return contract, validate_deep_analysis_contract(contract)


def _append_current_diagnostic_rows(
    *,
    evidence_sections: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    missing_evidence: list[dict[str, Any]],
    report: Mapping[str, Any],
    screen: Mapping[str, Any],
    provenance: Mapping[str, Any],
    freshness: Mapping[str, Any],
) -> None:
    rows_before = len(evidence_rows)
    decision = _decision(report, screen)
    scores = _scores(report, screen)

    decision_fields = (
        ("primary_issue", "Primary Issue", "primary_domain_ref"),
        ("primary_domain", "Primary Domain", "primary_domain_ref"),
        ("overall_status", "Overall Status", "severity_ref"),
        ("risk_level", "Risk Level", "severity_ref"),
        ("display_severity_label", "Severity Label", "severity_ref"),
        ("severity_score", "Severity Score", "severity_ref"),
        ("confidence", "Confidence", "confidence_ref"),
        ("decision_posture", "Posture", "posture_ref"),
        ("posture", "Posture", "posture_ref"),
        ("recommendation", "Recommendation", "recommendation_ref"),
    )
    for key, label, truth_ref in decision_fields:
        value = decision.get(key)
        if not _has_value(value):
            continue
        evidence_rows.append(
            _row(
                row_id=f"diagnostic-{_slug(key)}",
                section_id="current-diagnostic-truth",
                scope=ScopeClassification.CURRENT_SCOPE,
                evidence_type="diagnostic_driver",
                evidence_name=label,
                deterministic_value=value,
                source_path=f"{_decision_source_path(report, screen)}.{key}",
                provenance=provenance,
                freshness=freshness,
                supports_existing_truth_ref={"ref": f"immutable_truth_refs.{truth_ref}"},
                render_as="evidence_row",
                display_label=label,
            )
        )

    domain_scores = _mapping(scores.get("domain_scores"))
    if domain_scores:
        for domain, score in sorted(domain_scores.items(), key=lambda item: str(item[0])):
            if not _has_value(score):
                continue
            metric_name = f"domain_score.{domain}"
            evidence_rows.append(
                _row(
                    row_id=f"domain-score-{_slug(domain)}",
                    section_id="current-diagnostic-truth",
                    scope=ScopeClassification.CURRENT_SCOPE,
                    evidence_type="metric_breakdown",
                    metric_name=metric_name,
                    deterministic_value=score,
                    source_path=f"{_scores_source_path(report, screen)}.domain_scores.{domain}",
                    provenance=provenance,
                    freshness=freshness,
                    supports_existing_truth_ref={"ref": "immutable_truth_refs.score_ref"},
                    render_as="metric_row",
                    display_label=f"{domain} score",
                )
            )

    for index, issue in enumerate(_mapping_list(report.get("issues"))):
        value = _first_value(
            issue.get("deterministic_value"),
            issue.get("score"),
            _nested_get(issue, ("evidence", "pct_db_time")),
            _nested_get(issue, ("evidence", "value")),
            issue.get("severity"),
            issue.get("finding"),
            issue.get("summary"),
        )
        if not _has_value(value):
            continue
        name = _first_text(
            issue.get("issue_type"),
            issue.get("domain"),
            issue.get("metric"),
            issue.get("name"),
            f"issue-{index + 1}",
        )
        evidence_rows.append(
            _row(
                row_id=f"issue-{index + 1}-{_slug(name)}",
                section_id="current-diagnostic-truth",
                scope=ScopeClassification.CURRENT_SCOPE,
                evidence_type="diagnostic_driver",
                evidence_name=name,
                deterministic_value=value,
                source_path=f"report_data.issues[{index}]",
                provenance=provenance,
                freshness=freshness,
                supports_existing_truth_ref={"ref": "immutable_truth_refs.diagnostic_driver_refs"},
                render_as="evidence_row",
                display_label=name,
            )
        )

    if len(evidence_rows) > rows_before:
        evidence_sections.append(
            _section(
                section_id="current-diagnostic-truth",
                title="Current Diagnostic Evidence",
                scope=ScopeClassification.CURRENT_SCOPE,
                evidence_type="diagnostic_driver",
                source_path="report_data.decision/report_data.scores/report_data.issues",
                provenance=provenance,
                freshness=freshness,
                rows_present=True,
                allowed_rendering="evidence_table",
                display_priority=10,
            )
        )
    else:
        missing_evidence.append(
            {
                "type": "diagnostic_driver_missing",
                "field": "report_data.decision/report_data.scores/report_data.issues",
                "reason": "No deterministic diagnostic driver values were available.",
            }
        )


def _append_current_top_sql_rows(
    *,
    evidence_sections: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    missing_evidence: list[dict[str, Any]],
    report: Mapping[str, Any],
    provenance: Mapping[str, Any],
    freshness: Mapping[str, Any],
) -> None:
    top_sql = _mapping_list(report.get("top_sql"))
    rows_before = len(evidence_rows)
    for index, sql_record in enumerate(top_sql[:10]):
        sql_id = _first_text(sql_record.get("sql_id"), sql_record.get("sql_identifier"))
        value = _first_value(
            sql_record.get("pct_total"),
            sql_record.get("elapsed_time_seconds"),
            sql_record.get("db_time_seconds"),
            sql_record.get("executions"),
            sql_record.get("buffer_gets"),
        )
        if not sql_id or not _has_value(value):
            continue
        evidence_rows.append(
            _row(
                row_id=f"top-sql-{index + 1}-{_slug(sql_id)}",
                section_id="current-top-sql-detail",
                scope=ScopeClassification.CURRENT_SCOPE,
                evidence_type="top_sql_detail",
                evidence_name=sql_id,
                deterministic_value=value,
                unit=_first_text(
                    sql_record.get("unit"),
                    "pct_total" if _has_value(sql_record.get("pct_total")) else "",
                ),
                source_path=f"report_data.top_sql[{index}]",
                provenance=provenance,
                freshness=freshness,
                supports_existing_truth_ref={"ref": "immutable_truth_refs.diagnostic_driver_refs"},
                render_as="table_row",
                display_label=f"SQL {sql_id}",
            )
        )

    if len(evidence_rows) > rows_before:
        evidence_sections.append(
            _section(
                section_id="current-top-sql-detail",
                title="Top SQL Detail",
                scope=ScopeClassification.CURRENT_SCOPE,
                evidence_type="top_sql_detail",
                source_path="report_data.top_sql",
                provenance=provenance,
                freshness=freshness,
                rows_present=True,
                allowed_rendering="evidence_table",
                display_priority=20,
            )
        )
    else:
        missing_evidence.append(
            {
                "type": "top_sql_missing",
                "field": "report_data.top_sql",
                "reason": "No deterministic Top SQL rows were available.",
            }
        )


def _append_current_chart_rows(
    *,
    evidence_sections: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    charts: Mapping[str, Any],
    provenance: Mapping[str, Any],
    freshness: Mapping[str, Any],
) -> None:
    if not _is_current_scope_payload(charts):
        return
    db_time = _mapping(charts.get("db_time_breakdown"))
    labels = _list(db_time.get("labels"))
    values = _list(db_time.get("values"))
    rows_before = len(evidence_rows)
    for index, label in enumerate(labels):
        if index >= len(values) or not _has_value(values[index]):
            continue
        evidence_rows.append(
            _row(
                row_id=f"db-time-{index + 1}-{_slug(label)}",
                section_id="current-db-time-breakdown",
                scope=ScopeClassification.CURRENT_SCOPE,
                evidence_type="db_time_breakdown",
                metric_name=str(label),
                deterministic_value=values[index],
                unit=_first_text(db_time.get("unit"), "percent"),
                source_path=f"chart_payload.db_time_breakdown.values[{index}]",
                provenance=provenance,
                freshness=freshness,
                supports_existing_truth_ref={"ref": "immutable_truth_refs.diagnostic_driver_refs"},
                render_as="metric_row",
                display_label=str(label),
            )
        )
    if len(evidence_rows) > rows_before:
        evidence_sections.append(
            _section(
                section_id="current-db-time-breakdown",
                title="DB Time Breakdown",
                scope=ScopeClassification.CURRENT_SCOPE,
                evidence_type="db_time_breakdown",
                source_path="chart_payload.db_time_breakdown",
                provenance=provenance,
                freshness=freshness,
                rows_present=True,
                allowed_rendering="evidence_table",
                display_priority=30,
            )
        )


def _append_historical_support_rows(
    *,
    evidence_sections: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    report: Mapping[str, Any],
    screen: Mapping[str, Any],
    charts: Mapping[str, Any],
    provenance: Mapping[str, Any],
    freshness: Mapping[str, Any],
) -> None:
    time_series_sources = (
        ("report_data.time_series_charts", _mapping(report.get("time_series_charts"))),
        ("chart_payload.time_series_charts", _mapping(charts.get("time_series_charts"))),
    )
    time_series_rows: list[dict[str, Any]] = []
    for source_path, payload in time_series_sources:
        for key, values in sorted(payload.items(), key=lambda item: str(item[0])):
            if key == "snapshot_labels":
                continue
            samples = _numeric_values(values)
            if not samples:
                continue
            time_series_rows.append(
                _row(
                    row_id=f"historical-time-series-{_slug(key)}",
                    section_id="historical-time-series-support",
                    scope=ScopeClassification.HISTORICAL_SUPPORTING_CONTEXT,
                    evidence_type="time_series_supporting_context",
                    metric_name=str(key),
                    deterministic_value={"sample_count": len(samples)},
                    source_path=f"{source_path}.{key}",
                    provenance=provenance,
                    freshness=freshness,
                    supports_existing_truth_ref={},
                    render_as="supporting_context_row",
                    display_label=str(key),
                )
            )
    if time_series_rows:
        evidence_rows.extend(time_series_rows)
        evidence_sections.append(
            _section(
                section_id="historical-time-series-support",
                title="Historical Supporting Context",
                scope=ScopeClassification.HISTORICAL_SUPPORTING_CONTEXT,
                evidence_type="time_series_supporting_context",
                source_path="report_data.time_series_charts/chart_payload.time_series_charts",
                provenance=provenance,
                freshness=freshness,
                rows_present=True,
                allowed_rendering="supporting_context",
                display_priority=60,
            )
        )

    distribution_sources = (
        ("report_data.violin_panel", _mapping(report.get("violin_panel"))),
        ("report_data.metric_samples", _mapping(report.get("metric_samples"))),
        ("chart_payload.violin_panel", _mapping(charts.get("violin_panel"))),
    )
    distribution_rows: list[dict[str, Any]] = []
    for source_path, payload in distribution_sources:
        for key, values in _flatten_numeric_series(payload):
            distribution_rows.append(
                _row(
                    row_id=f"historical-distribution-{_slug(source_path)}-{_slug(key)}",
                    section_id="historical-distribution-support",
                    scope=ScopeClassification.HISTORICAL_SUPPORTING_CONTEXT,
                    evidence_type="distribution_supporting_context",
                    metric_name=str(key),
                    deterministic_value={"sample_count": len(values)},
                    source_path=f"{source_path}.{key}",
                    provenance=provenance,
                    freshness=freshness,
                    supports_existing_truth_ref={},
                    render_as="supporting_context_row",
                    display_label=str(key),
                )
            )
    if distribution_rows:
        evidence_rows.extend(distribution_rows)
        evidence_sections.append(
            _section(
                section_id="historical-distribution-support",
                title="Distribution Supporting Context",
                scope=ScopeClassification.HISTORICAL_SUPPORTING_CONTEXT,
                evidence_type="distribution_supporting_context",
                source_path="report_data.violin_panel/report_data.metric_samples/chart_payload.violin_panel",
                provenance=provenance,
                freshness=freshness,
                rows_present=True,
                allowed_rendering="supporting_context",
                display_priority=70,
            )
        )

    visual_analysis = _mapping(screen.get("visual_analysis"))
    if visual_analysis and not (time_series_rows or distribution_rows):
        summary = _first_value(visual_analysis.get("summary"), visual_analysis.get("story"))
        if _has_value(summary):
            evidence_rows.append(
                _row(
                    row_id="historical-visual-analysis-summary",
                    section_id="historical-visual-analysis-support",
                    scope=ScopeClassification.HISTORICAL_SUPPORTING_CONTEXT,
                    evidence_type="engineering_detail",
                    evidence_name="Historical visual analysis summary",
                    deterministic_value=summary,
                    source_path="screen_model.visual_analysis",
                    provenance=provenance,
                    freshness=freshness,
                    supports_existing_truth_ref={},
                    render_as="supporting_context_row",
                    display_label="Historical visual analysis summary",
                )
            )
            evidence_sections.append(
                _section(
                    section_id="historical-visual-analysis-support",
                    title="Historical Supporting Context",
                    scope=ScopeClassification.HISTORICAL_SUPPORTING_CONTEXT,
                    evidence_type="engineering_detail",
                    source_path="screen_model.visual_analysis",
                    provenance=provenance,
                    freshness=freshness,
                    rows_present=True,
                    allowed_rendering="supporting_context",
                    display_priority=80,
                )
            )


def _section(
    *,
    section_id: str,
    title: str,
    scope: ScopeClassification,
    evidence_type: str,
    source_path: str,
    provenance: Mapping[str, Any],
    freshness: Mapping[str, Any],
    rows_present: bool,
    allowed_rendering: str,
    display_priority: int,
) -> dict[str, Any]:
    section = {
        "section_id": section_id,
        "title": title,
        "scope_classification": scope.value,
        "evidence_type": evidence_type,
        "source_path": source_path,
        "provenance": _provenance_for_source(provenance, source_path),
        "rows_present": rows_present,
        "allowed_rendering": allowed_rendering,
        "limitations": [],
        "missing_evidence": [],
        "llm_explainable": True,
        "display_priority": display_priority,
    }
    freshness_status = _freshness_status(freshness)
    if freshness_status:
        section["freshness_status"] = freshness_status
    return section


def _row(
    *,
    row_id: str,
    section_id: str,
    scope: ScopeClassification,
    evidence_type: str,
    source_path: str,
    provenance: Mapping[str, Any],
    freshness: Mapping[str, Any],
    supports_existing_truth_ref: Mapping[str, Any],
    render_as: str,
    deterministic_value: Any,
    evidence_name: Any = None,
    metric_name: Any = None,
    unit: Any = None,
    display_label: Any = None,
) -> dict[str, Any]:
    row = {
        "row_id": row_id,
        "section_id": section_id,
        "scope_classification": scope.value,
        "evidence_type": evidence_type,
        "deterministic_value": deterministic_value,
        "source_path": source_path,
        "provenance": _provenance_for_source(provenance, source_path),
        "supports_existing_truth_ref": dict(supports_existing_truth_ref),
        "limitation_flags": [],
        "render_as": render_as,
    }
    freshness_status = _freshness_status(freshness)
    if freshness_status:
        row["freshness_status"] = freshness_status
    if _has_value(evidence_name):
        row["evidence_name"] = str(evidence_name)
    if _has_value(metric_name):
        row["metric_name"] = str(metric_name)
    if _has_value(unit):
        row["unit"] = unit
    if _has_value(display_label):
        row["display_label"] = str(display_label)
    return row


def _immutable_truth_refs(
    report: Mapping[str, Any],
    screen: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    decision = _decision(report, screen)
    scores = _scores(report, screen)
    refs: dict[str, dict[str, Any]] = {}
    _add_truth_ref(
        refs,
        "primary_domain_ref",
        _first_value(decision.get("primary_domain"), decision.get("primary_issue")),
        f"{_decision_source_path(report, screen)}.primary_issue",
    )
    _add_truth_ref(
        refs,
        "score_ref",
        _first_value(scores.get("domain_scores"), scores.get("severity_score"), decision.get("severity_score")),
        _scores_source_path(report, screen),
    )
    _add_truth_ref(
        refs,
        "severity_ref",
        _first_value(decision.get("display_severity_label"), decision.get("risk_level"), decision.get("overall_status"), decision.get("severity_score")),
        _decision_source_path(report, screen),
    )
    _add_truth_ref(
        refs,
        "confidence_ref",
        decision.get("confidence"),
        f"{_decision_source_path(report, screen)}.confidence",
    )
    _add_truth_ref(
        refs,
        "posture_ref",
        _first_value(decision.get("decision_posture"), decision.get("posture")),
        _decision_source_path(report, screen),
    )
    _add_truth_ref(
        refs,
        "recommendation_ref",
        _first_value(decision.get("recommendation"), _first_value(*_list(report.get("recommendations")))),
        "report_data.recommendations",
    )
    _add_truth_ref(
        refs,
        "threshold_refs",
        _first_value(report.get("thresholds"), decision.get("thresholds")),
        "report_data.thresholds",
    )
    if _mapping_list(report.get("issues")):
        refs["diagnostic_driver_refs"] = {
            "ref": "report_data.issues",
            "read_only": True,
            "value": "current diagnostic issue rows",
        }
    elif decision:
        refs["diagnostic_driver_refs"] = {
            "ref": _decision_source_path(report, screen),
            "read_only": True,
            "value": "current diagnostic decision",
        }
    return refs


def _add_truth_ref(
    refs: dict[str, dict[str, Any]],
    key: str,
    value: Any,
    source_path: str,
) -> None:
    if not _has_value(value):
        return
    refs[key] = {
        "ref": source_path,
        "read_only": True,
        "value": value,
    }


def _selected_source_identifier(
    report: Mapping[str, Any],
    selected: Mapping[str, Any],
    screen: Mapping[str, Any],
) -> dict[str, Any]:
    explicit = _mapping(selected.get("selected_source_identifier") or selected.get("source_identifier"))
    if explicit:
        return dict(explicit)
    metadata = _mapping(report.get("metadata"))
    header = _mapping(screen.get("header"))
    fields = {
        "source_artifact_id": _first_text(
            selected.get("source_artifact_id"),
            metadata.get("source_artifact_id"),
            report.get("source_artifact_id"),
            report.get("artifact_id"),
        ),
        "source_type": _first_text(selected.get("source_type"), metadata.get("source_type")),
        "db_name": _first_text(selected.get("db_name"), metadata.get("db_name"), header.get("db_name")),
        "dbid": _first_text(selected.get("dbid"), metadata.get("dbid"), header.get("dbid")),
        "instance_name": _first_text(selected.get("instance_name"), metadata.get("instance_name"), header.get("instance_name")),
        "host_name": _first_text(selected.get("host_name"), metadata.get("host_name"), header.get("host_name")),
    }
    return {key: value for key, value in fields.items() if value}


def _selected_snapshot_identifier(
    report: Mapping[str, Any],
    selected: Mapping[str, Any],
    screen: Mapping[str, Any],
) -> dict[str, Any]:
    explicit = _mapping(selected.get("selected_snapshot_identifier") or selected.get("snapshot_identifier"))
    if explicit:
        return dict(explicit)
    metadata = _mapping(report.get("metadata"))
    header = _mapping(screen.get("header"))
    fields = {
        "awr_id": _first_text(selected.get("awr_id"), metadata.get("awr_id"), report.get("awr_id")),
        "snapshot_begin": _first_text(selected.get("snapshot_begin"), metadata.get("snapshot_begin"), header.get("snapshot_begin")),
        "snapshot_end": _first_text(selected.get("snapshot_end"), metadata.get("snapshot_end"), header.get("snapshot_end")),
        "snapshot": _first_text(selected.get("snapshot"), selected.get("snapshot_label"), metadata.get("snapshot")),
        "window": _first_text(selected.get("window"), selected.get("time_window"), header.get("comparison_window")),
    }
    return {key: value for key, value in fields.items() if value}


def _current_diagnostic_output_ref(
    report: Mapping[str, Any],
    selected: Mapping[str, Any],
    screen: Mapping[str, Any],
    selected_run_id: str,
) -> dict[str, Any]:
    explicit = _mapping(
        selected.get("current_diagnostic_output_ref")
        or report.get("current_diagnostic_output_ref")
        or screen.get("current_diagnostic_output_ref")
    )
    if explicit:
        return dict(explicit)
    decision = _decision(report, screen)
    ref = {
        "run_id": selected_run_id,
        "diagnostic_output_id": _first_text(
            selected.get("diagnostic_output_id"),
            report.get("diagnostic_output_id"),
            _nested_get(report, ("metadata", "diagnostic_output_id")),
        ),
        "source_path": _decision_source_path(report, screen) if decision else "",
    }
    primary_issue = _first_value(decision.get("primary_domain"), decision.get("primary_issue"))
    if _has_value(primary_issue):
        ref["primary_issue"] = primary_issue
    return {key: value for key, value in ref.items() if _has_value(value)}


def _generation_context(
    context: Mapping[str, Any],
    report: Mapping[str, Any],
    selected: Mapping[str, Any],
    screen: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(context)
    payload.setdefault("builder_version", DEEP_ANALYSIS_BUILDER_VERSION)
    dashboard_generation_id = _first_text(
        context.get("dashboard_generation_id"),
        report.get("dashboard_generated_session_id"),
        report.get("dashboard_generation_id"),
        screen.get("dashboard_generation_id"),
    )
    if dashboard_generation_id:
        payload.setdefault("dashboard_generation_id", dashboard_generation_id)
    selected_scope_label = _first_text(
        selected.get("scope_label"),
        _nested_get(screen, ("header", "scope_label")),
    )
    if selected_scope_label:
        payload.setdefault("selected_scope_label", selected_scope_label)
    return payload


def _chart_eligibility(context: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = context.get("chart_eligibility")
    if not isinstance(raw, list):
        return []
    eligibility: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        chart = dict(item)
        chart.setdefault("browser_computation_allowed", False)
        chart.setdefault("synthetic_data_allowed", False)
        chart.setdefault("empty_chart_allowed", False)
        chart.setdefault("eligibility_status", "not_requested")
        eligibility.append(chart)
    return eligibility


def _append_input_boundary_limitations(
    *,
    limitations: list[dict[str, Any]],
    report: Mapping[str, Any],
    selected: Mapping[str, Any],
    screen: Mapping[str, Any],
    charts: Mapping[str, Any],
) -> None:
    inputs = (
        ("report_data", report),
        ("selected_scope", selected),
        ("screen_model", screen),
        ("chart_payload", charts),
    )
    for source_name, payload in inputs:
        _append_limitations_for_keys(limitations, source_name, payload, _COMPARATIVE_KEYS, "comparative_output_blocked")
        _append_limitations_for_keys(limitations, source_name, payload, _PREPARED_KEYS, "prepared_only_blocked")
        _append_limitations_for_keys(limitations, source_name, payload, _CACHE_KEYS, "cache_only_blocked")
        _append_limitations_for_keys(limitations, source_name, payload, _LLM_KEYS, "llm_text_not_evidence")


def _append_limitations_for_keys(
    limitations: list[dict[str, Any]],
    source_name: str,
    payload: Mapping[str, Any],
    keys: set[str],
    limitation_type: str,
) -> None:
    for key in sorted(keys):
        if key in payload:
            limitations.append(
                {
                    "type": limitation_type,
                    "field": f"{source_name}.{key}",
                    "reason": "Input was ignored as Deep Analysis evidence by contract-builder boundary.",
                }
            )


def _source_scope(selected: Mapping[str, Any]) -> str:
    if _selected_scope_is_cache_only(selected):
        return ScopeClassification.CACHE_ONLY.value
    if _selected_scope_is_prepared_only(selected):
        return ScopeClassification.PREPARED_ONLY.value
    explicit = _normalized_text(
        selected.get("source_scope")
        or selected.get("scope_classification")
        or selected.get("scope")
    )
    if explicit in {
        ScopeClassification.CACHE_ONLY.value,
        ScopeClassification.PREPARED_ONLY.value,
        ScopeClassification.COMPARATIVE_OUTPUT.value,
        ScopeClassification.FLEET_POPULATION.value,
        ScopeClassification.LLM_EXPLANATION_ONLY.value,
        ScopeClassification.UNKNOWN_OR_MIXED.value,
    }:
        return explicit
    return CURRENT_SOURCE_SCOPE


def _selected_scope_is_cache_only(selected: Mapping[str, Any]) -> bool:
    values = (
        selected.get("scope_classification"),
        selected.get("source_scope"),
        selected.get("cache_status"),
        selected.get("truth_source"),
        selected.get("context_mode"),
    )
    text = " ".join(_normalized_text(value) for value in values if value is not None)
    return any(token in text for token in ("cache_only", "cached_continuity_only", "browser_cache", "localstorage"))


def _selected_scope_is_prepared_only(selected: Mapping[str, Any]) -> bool:
    values = (
        selected.get("scope_classification"),
        selected.get("source_scope"),
        selected.get("context_mode"),
        selected.get("comparison_status"),
    )
    text = " ".join(_normalized_text(value) for value in values if value is not None)
    if "prepared_only" in text:
        return True
    return selected.get("prepared_only") is True


def _decision(report: Mapping[str, Any], screen: Mapping[str, Any]) -> Mapping[str, Any]:
    return _resolve_mapping(
        report.get("decision"),
        screen.get("normalized_decision"),
        screen.get("decision_summary"),
    )


def _scores(report: Mapping[str, Any], screen: Mapping[str, Any]) -> Mapping[str, Any]:
    screen_scores = _mapping(screen.get("scores_panel"))
    diagnostic_scores = _mapping(_mapping(screen.get("diagnostic_snapshot")).get("domain_scores"))
    if diagnostic_scores and "domain_scores" not in screen_scores:
        screen_scores = {**screen_scores, "domain_scores": diagnostic_scores}
    return _resolve_mapping(report.get("scores"), screen_scores)


def _decision_source_path(report: Mapping[str, Any], screen: Mapping[str, Any]) -> str:
    if isinstance(report.get("decision"), Mapping):
        return "report_data.decision"
    if isinstance(screen.get("normalized_decision"), Mapping):
        return "screen_model.normalized_decision"
    return "screen_model.decision_summary"


def _scores_source_path(report: Mapping[str, Any], screen: Mapping[str, Any]) -> str:
    if isinstance(report.get("scores"), Mapping):
        return "report_data.scores"
    if isinstance(screen.get("scores_panel"), Mapping):
        return "screen_model.scores_panel"
    return "screen_model.diagnostic_snapshot.domain_scores"


def _generated_at(
    context: Mapping[str, Any],
    report: Mapping[str, Any],
    screen: Mapping[str, Any],
) -> str:
    return _first_text(
        context.get("generated_at"),
        _nested_get(context, ("freshness", "generated_at")),
        report.get("generated_at"),
        _nested_get(report, ("metadata", "generated_at")),
        screen.get("generated_at"),
    )


def _provenance_for_source(provenance: Mapping[str, Any], source_path: str) -> dict[str, Any]:
    if not provenance:
        return {}
    payload = dict(provenance)
    payload.setdefault("source_path", source_path)
    return payload


def _freshness_status(freshness: Mapping[str, Any]) -> str:
    return _first_text(
        freshness.get("freshness_status") if isinstance(freshness, Mapping) else None,
        freshness.get("status") if isinstance(freshness, Mapping) else None,
    )


def _is_current_scope_payload(payload: Mapping[str, Any]) -> bool:
    return _normalized_text(payload.get("scope_classification") or payload.get("source_scope")) in {
        ScopeClassification.CURRENT_SCOPE.value,
        CURRENT_SOURCE_SCOPE,
        "selected_diagnostic_scope",
        "current_selected_scope",
    }


def _resolve_mapping(*values: Any) -> Mapping[str, Any]:
    for value in values:
        if isinstance(value, Mapping) and value:
            return value
    return {}


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _mapping_list(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _flatten_numeric_series(value: Any, prefix: str = "") -> list[tuple[str, list[float]]]:
    if isinstance(value, Mapping):
        rows: list[tuple[str, list[float]]] = []
        for key, item in sorted(value.items(), key=lambda pair: str(pair[0])):
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(_flatten_numeric_series(item, next_prefix))
        return rows
    numeric_values = _numeric_values(value)
    return [(prefix, numeric_values)] if prefix and numeric_values else []


def _numeric_values(value: Any) -> list[float]:
    if not isinstance(value, (list, tuple)):
        return []
    values: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            continue
        values.append(float(item))
    return values


def _nested_get(payload: Any, path: tuple[str, ...]) -> Any:
    current = payload
    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _first_value(*values: Any) -> Any:
    for value in values:
        if _has_value(value):
            return value
    return None


def _first_text(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _normalized_text(value: Any) -> str:
    return _first_text(value).lower().replace("-", "_").replace(" ", "_")


def _slug(value: Any) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", _first_text(value).lower()).strip("-")
    return slug or "value"
