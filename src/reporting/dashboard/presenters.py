"""Deterministic product presenters for 7RESET dashboard view models.

This layer translates already-decided backend contracts into product-safe
view models. It does not decide new diagnoses, scores, recommendations,
comparisons, learning state, materialization state, runtime eligibility, or
runtime behavior.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.reporting.dashboard.contracts.evidence_pack_contract import EvidencePackContract
from src.reporting.dashboard.contracts.selected_review_scope_contract import SelectedReviewScopeContract
from src.reporting.dashboard.view_models.screen3_diagnostic_snapshot import (
    DiagnosticFirstFold,
    Screen3DiagnosticSnapshotViewModel,
)
from src.reporting.dashboard.view_models.screen4_evidence_review import (
    EvidenceReviewModePanel,
    Screen4EvidenceReviewViewModel,
)
from src.reporting.dashboard.view_models.screen5_recommendation_action import (
    Screen5RecommendationActionViewModel,
)
from src.reporting.dashboard.view_models.screen6_learning_governance import (
    Screen6LearningGovernanceViewModel,
)
from src.reporting.dashboard.view_models.shared_product_shapes import (
    EvidenceDisplayRow,
    EvidenceReviewSection,
    ExplanationBlock,
    ProductScopeSummary,
    ScopeClassification,
    UnavailableVisualState,
)
from src.reporting.dashboard.view_models.visual_contracts import (
    ComparisonDeltaVisual,
    DistributionVisual,
    TimeSeriesVisual,
    ViolinVisual,
)


SUPPORTED_FLOW_KINDS: tuple[str, ...] = (
    "single_awr",
    "selected_report",
    "runtime_scope",
    "timeframe",
    "historical_multi_snapshot",
    "multi_awr_set",
    "comparison",
    "multi_target_comparison",
    "fleet",
    "cohort",
    "healthcheck",
    "predictive_sizing",
    "comparative_sizing",
    "unavailable",
)
SINGLE_SCOPE_FLOW_KINDS = ("single_awr", "selected_report", "runtime_scope")
TEMPORAL_FLOW_KINDS = ("timeframe", "historical_multi_snapshot")
SET_FLOW_KINDS = ("multi_awr_set",)
COMPARISON_FLOW_KINDS = ("comparison", "multi_target_comparison")
FLEET_FLOW_KINDS = ("fleet", "cohort")
SIZING_FLOW_KINDS = ("predictive_sizing", "comparative_sizing")

EVIDENCE_CHANNELS: tuple[str, ...] = (
    "selected_diagnostic_evidence",
    "selected_set_evidence",
    "member_diagnostic_evidence",
    "aggregate_evidence",
    "temporal_evidence",
    "supporting_historical_context",
    "comparison_evidence",
    "deep_analysis_evidence",
    "fleet_or_cohort_evidence",
    "recommendation_evidence",
    "governance_evidence",
    "visualization_evidence",
    "missing_evidence",
    "unavailable_states",
)

VISUAL_CONTRACT_TYPES = (
    TimeSeriesVisual,
    DistributionVisual,
    ViolinVisual,
    ComparisonDeltaVisual,
    UnavailableVisualState,
)

PRESENTER_PRODUCT_RULES: tuple[str, ...] = (
    "selected_scope_analysis_set",
    "analysis_set_not_comparison",
    "multi_awr_set does not require target_a",
    "multi_target_comparison supports two or more targets",
    "deep analysis ready if detail evidence exists",
    "historical context is supporting",
    "supporting_historical_context_not_selected_truth",
    "comparison requires deterministic comparison contract",
    "comparison_contract_required",
    "allowed_visualizations is not product content",
    "allowed_visualizations metadata only",
    "chart metadata is not evidence",
    "chart_metadata_not_evidence",
    "fake static svg is not evidence",
    "static svg not evidence",
    "missing visual evidence must produce UnavailableVisualState",
    "governed eligibility",
)

SELECTED_SCOPE_MAPPING_AUTHORITY_FIELDS = (
    "contract_type",
    "contract_version",
    "flow_kind",
    "validation_status",
    "source_of_truth",
    "provenance",
)
PRODUCT_VIEW_MODEL_VERSION = "7reset.product.presenter.v1"


def build_screen3_diagnostic_snapshot_view_model(
    selected_scope_contract: SelectedReviewScopeContract | Mapping[str, Any],
    evidence_pack_contract: EvidencePackContract | Mapping[str, Any],
) -> Screen3DiagnosticSnapshotViewModel:
    """Build Screen 3 Diagnostic Snapshot from deterministic contract evidence."""

    _assert_selected_scope_contract_authority(selected_scope_contract)
    evidence_channels = _evidence_channels(evidence_pack_contract)
    flow_kind = _flow_kind(selected_scope_contract)
    scope_summary = _scope_summary(selected_scope_contract, flow_kind)
    internal_refs = _internal_refs(selected_scope_contract, evidence_pack_contract)
    missing_evidence = _missing_evidence_messages(evidence_channels)
    unavailable = _unavailable_for_flow(flow_kind, evidence_channels)

    first_fold = DiagnosticFirstFold(
        status_label=_screen3_status_label(flow_kind, evidence_channels),
        primary_issue_label=_primary_issue_label(flow_kind, evidence_channels),
        severity_score=_number_from_evidence(evidence_channels["selected_diagnostic_evidence"], "severity_score"),
        confidence_score=_number_from_evidence(evidence_channels["selected_diagnostic_evidence"], "confidence_score"),
        top_driver_labels=_driver_labels(flow_kind, evidence_channels),
        missing_evidence_summary="; ".join(missing_evidence),
    )

    primary_cards = (
        _screen3_scope_projection_section(flow_kind, evidence_channels),
        _evidence_section(
            "screen3-selected-diagnostic-evidence",
            "Selected diagnostic evidence",
            "current_scope",
            evidence_channels["selected_diagnostic_evidence"],
        ),
    )
    secondary_sections = tuple(
        section
        for section in (
            _evidence_section(
                "screen3-temporal-evidence",
                "Temporal evidence",
                "historical_supporting_context",
                evidence_channels["temporal_evidence"],
            ),
            _evidence_section(
                "screen3-comparison-evidence",
                "Comparison evidence",
                "comparative_output",
                evidence_channels["comparison_evidence"],
            ),
            _unavailable_section("screen3-unavailable-states", unavailable),
        )
        if section.rows or section.limitations
    )

    return Screen3DiagnosticSnapshotViewModel(
        screen_id="screen3_diagnostic_snapshot",
        contract_version=PRODUCT_VIEW_MODEL_VERSION,
        scope_summary=scope_summary,
        first_fold=first_fold,
        primary_cards=primary_cards,
        secondary_sections=secondary_sections,
        visuals=_visual_contracts(evidence_channels, "current_scope"),
        evidence_table=_display_rows(evidence_channels["selected_diagnostic_evidence"], "current_scope"),
        missing_evidence=missing_evidence,
        llm_explanation=_llm_explanation_boundary(evidence_pack_contract),
        provenance=_provenance_labels(selected_scope_contract, evidence_pack_contract),
        freshness=_freshness_label(evidence_pack_contract),
        internal_refs=internal_refs,
    )


def build_screen4_evidence_review_view_model(
    selected_scope_contract: SelectedReviewScopeContract | Mapping[str, Any],
    evidence_pack_contract: EvidencePackContract | Mapping[str, Any],
) -> Screen4EvidenceReviewViewModel:
    """Build Screen 4 Evidence Review with dynamic mode availability."""

    _assert_selected_scope_contract_authority(selected_scope_contract)
    evidence_channels = _evidence_channels(evidence_pack_contract)
    flow_kind = _flow_kind(selected_scope_contract)
    scope_summary = _scope_summary(selected_scope_contract, flow_kind)

    historical = _historical_mode_panel(flow_kind, evidence_channels, evidence_pack_contract)
    comparative = _comparative_mode_panel(selected_scope_contract, flow_kind, evidence_channels, evidence_pack_contract)
    deep_analysis = _deep_analysis_mode_panel(flow_kind, evidence_channels, evidence_pack_contract)
    active_mode = _active_screen4_mode(flow_kind, historical, comparative, deep_analysis)

    return Screen4EvidenceReviewViewModel(
        screen_id="screen4_evidence_review",
        contract_version=PRODUCT_VIEW_MODEL_VERSION,
        scope_summary=scope_summary,
        active_mode=active_mode,
        mode_tabs=("historical", "comparative", "deep_analysis"),
        historical=historical,
        comparative=comparative,
        deep_analysis=deep_analysis,
        cross_mode_warnings=_screen4_cross_mode_warnings(flow_kind, evidence_channels),
        provenance=_provenance_labels(selected_scope_contract, evidence_pack_contract),
        freshness=_freshness_label(evidence_pack_contract),
        internal_refs=_internal_refs(selected_scope_contract, evidence_pack_contract),
    )


def build_screen5_recommendation_action_view_model(
    selected_scope_contract: SelectedReviewScopeContract | Mapping[str, Any],
    evidence_pack_contract: EvidencePackContract | Mapping[str, Any],
) -> Screen5RecommendationActionViewModel:
    """Build Screen 5 Recommendation Action from recommendation_evidence only."""

    _assert_selected_scope_contract_authority(selected_scope_contract)
    evidence_channels = _evidence_channels(evidence_pack_contract)
    flow_kind = _flow_kind(selected_scope_contract)
    recommendation_evidence = evidence_channels["recommendation_evidence"]
    recommendation_ready = _has_evidence(recommendation_evidence)
    unavailable = ()
    if not recommendation_ready:
        unavailable = (
            _unavailable_state(
                "screen5-recommendation-evidence-unavailable",
                "recommendation_evidence_missing",
                "Recommendation evidence unavailable",
                "Screen 5 requires deterministic recommendation_evidence for the selected scope.",
                "recommendation_evidence",
                ("recommendation_evidence",),
                "current_scope",
            ),
        )

    first_fold = _evidence_section(
        "screen5-first-fold",
        _screen5_title(flow_kind),
        "current_scope",
        recommendation_evidence,
        fallback_rows=(
            EvidenceDisplayRow(
                label="unavailable_recommendation_state",
                value="unavailable" if not recommendation_ready else "ready",
                unit="",
                interpretation="LLM text cannot create recommendation evidence.",
                evidence_ref_label="recommendation_evidence",
                freshness_status=_freshness_label(evidence_pack_contract),
            ),
        ),
    )

    return Screen5RecommendationActionViewModel(
        screen_id="screen5_recommendation_action",
        contract_version=PRODUCT_VIEW_MODEL_VERSION,
        scope_summary=_scope_summary(selected_scope_contract, flow_kind),
        first_fold=first_fold,
        recommendation_decision=_summary_text(recommendation_evidence) if recommendation_ready else "unavailable",
        action_plan=(_evidence_section("screen5-action-plan", "Action plan", "current_scope", recommendation_evidence),),
        validation_checklist=(_unavailable_section("screen5-unavailable", unavailable),),
        risk_impact=(_evidence_section("screen5-risk-impact", "Risk and impact", "current_scope", recommendation_evidence),),
        owner_status="deterministic_evidence_required" if not recommendation_ready else "ready_for_owner_review",
        outcome_capture=(),
        secondary_sections=_screen5_secondary_sections(flow_kind, evidence_channels, unavailable),
        llm_explanation=_llm_explanation_boundary(evidence_pack_contract),
        provenance=_provenance_labels(selected_scope_contract, evidence_pack_contract),
        freshness=_freshness_label(evidence_pack_contract),
        internal_refs=_internal_refs(selected_scope_contract, evidence_pack_contract),
    )


def build_screen6_learning_governance_view_model(
    selected_scope_contract: SelectedReviewScopeContract | Mapping[str, Any],
    evidence_pack_contract: EvidencePackContract | Mapping[str, Any],
) -> Screen6LearningGovernanceViewModel:
    """Build Screen 6 Learning Governance from governed deterministic evidence."""

    _assert_selected_scope_contract_authority(selected_scope_contract)
    evidence_channels = _evidence_channels(evidence_pack_contract)
    flow_kind = _flow_kind(selected_scope_contract)
    governance_evidence = evidence_channels["governance_evidence"]
    governance_ready = _has_evidence(governance_evidence)
    runtime_eligibility = "governed eligibility" if governance_ready and flow_kind in FLEET_FLOW_KINDS else "unavailable"
    unavailable = ()
    if not governance_ready:
        unavailable = (
            _unavailable_state(
                "screen6-governance-evidence-unavailable",
                "governance_evidence_missing",
                "Governance evidence unavailable",
                "Screen 6 requires governed deterministic governance_evidence before runtime eligibility.",
                "governance_evidence",
                ("governance_evidence",),
                "governance_persisted",
            ),
        )

    return Screen6LearningGovernanceViewModel(
        screen_id="screen6_learning_governance",
        contract_version=PRODUCT_VIEW_MODEL_VERSION,
        governance_summary=_evidence_section(
            "screen6-governance-summary",
            _screen6_title(flow_kind),
            "governance_persisted",
            governance_evidence,
        ),
        candidate_queue=_screen6_candidate_queue(flow_kind, evidence_channels),
        governance_status="ready" if governance_ready else "unavailable",
        materialization_gate="persisted_governance_required",
        runtime_eligibility=runtime_eligibility,
        memory_policy="semantic_recall_not_product_evidence",
        audit_timeline=(_evidence_section("screen6-audit-timeline", "Audit timeline", "governance_persisted", governance_evidence),),
        secondary_sections=(_unavailable_section("screen6-unavailable", unavailable),),
        provenance=_provenance_labels(selected_scope_contract, evidence_pack_contract),
        freshness=_freshness_label(evidence_pack_contract),
        internal_refs=_internal_refs(selected_scope_contract, evidence_pack_contract),
    )


PRODUCT_PRESENTERS = {
    "build_screen3_diagnostic_snapshot_view_model": build_screen3_diagnostic_snapshot_view_model,
    "build_screen4_evidence_review_view_model": build_screen4_evidence_review_view_model,
    "build_screen5_recommendation_action_view_model": build_screen5_recommendation_action_view_model,
    "build_screen6_learning_governance_view_model": build_screen6_learning_governance_view_model,
}
PRODUCT_PRESENTER_BUILDERS = PRODUCT_PRESENTERS
PRESENTER_BUILDERS = PRODUCT_PRESENTERS


def _assert_selected_scope_contract_authority(
    selected_scope_contract: SelectedReviewScopeContract | Mapping[str, Any],
) -> None:
    if isinstance(selected_scope_contract, SelectedReviewScopeContract):
        return
    if not isinstance(selected_scope_contract, Mapping):
        raise TypeError("selected_scope_contract must be a SelectedReviewScopeContract or deterministic mapping.")
    missing = [
        field_name
        for field_name in SELECTED_SCOPE_MAPPING_AUTHORITY_FIELDS
        if field_name not in selected_scope_contract
    ]
    if missing:
        raise ValueError(
            "selected_scope_contract mapping must carry deterministic authority fields: "
            + ", ".join(missing)
        )


def _value(source: Any, field_name: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, Mapping):
        return source.get(field_name, default)
    return getattr(source, field_name, default)


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    enum_value = getattr(value, "value", None)
    if enum_value is not None:
        return str(enum_value)
    text = str(value).strip()
    return text or default


def _flow_kind(selected_scope_contract: SelectedReviewScopeContract | Mapping[str, Any]) -> str:
    flow_kind = _text(_value(selected_scope_contract, "flow_kind"), "unavailable")
    return flow_kind if flow_kind in SUPPORTED_FLOW_KINDS else "unavailable"


def _scope_summary(
    selected_scope_contract: SelectedReviewScopeContract | Mapping[str, Any],
    flow_kind: str,
) -> ProductScopeSummary:
    runtime_scope = _value(selected_scope_contract, "runtime_scope")
    selected_report = _value(selected_scope_contract, "selected_report")
    selected_window = _value(selected_scope_contract, "selected_window") or _value(
        selected_scope_contract,
        "selected_snapshot",
    )
    selected_database = _value(selected_scope_contract, "selected_database")

    label = _first_text(
        _value(runtime_scope, "label"),
        _value(selected_report, "label"),
        _value(selected_scope_contract, "label"),
        flow_kind,
    )
    return ProductScopeSummary(
        label=label,
        database_label=_first_text(_value(selected_database, "database_name"), _value(runtime_scope, "database_id")),
        instance_label=_first_text(_value(selected_database, "instance_name"), _value(runtime_scope, "workload_id")),
        snapshot_window_label=_first_text(_value(selected_window, "window_id"), _value(runtime_scope, "snapshot_window_id")),
        flow_kind=flow_kind,
        validation_status=_text(_value(selected_scope_contract, "validation_status"), "unavailable"),
    )


def _first_text(*values: Any) -> str:
    for value in values:
        text = _text(value)
        if text:
            return text
    return ""


def _evidence_channels(evidence_pack_contract: EvidencePackContract | Mapping[str, Any]) -> dict[str, Any]:
    return {
        "selected_diagnostic_evidence": _channel(
            evidence_pack_contract,
            "selected_diagnostic_evidence",
            "diagnostic_evidence",
        ),
        "selected_set_evidence": _channel(evidence_pack_contract, "selected_set_evidence"),
        "member_diagnostic_evidence": _channel(evidence_pack_contract, "member_diagnostic_evidence"),
        "aggregate_evidence": _channel(evidence_pack_contract, "aggregate_evidence"),
        "temporal_evidence": _channel(evidence_pack_contract, "temporal_evidence", "historical_evidence"),
        "supporting_historical_context": _channel(evidence_pack_contract, "supporting_historical_context"),
        "comparison_evidence": _channel(evidence_pack_contract, "comparison_evidence", "comparative_evidence"),
        "deep_analysis_evidence": _channel(evidence_pack_contract, "deep_analysis_evidence"),
        "fleet_or_cohort_evidence": _channel(evidence_pack_contract, "fleet_or_cohort_evidence"),
        "recommendation_evidence": _channel(
            evidence_pack_contract,
            "recommendation_evidence",
            "recommendation_action_evidence",
        ),
        "governance_evidence": _channel(
            evidence_pack_contract,
            "governance_evidence",
            "learning_governance_evidence",
        ),
        "visualization_evidence": _channel(evidence_pack_contract, "visualization_evidence"),
        "missing_evidence": _channel(evidence_pack_contract, "missing_evidence"),
        "unavailable_states": _channel(evidence_pack_contract, "unavailable_states", "unavailable_evidence"),
    }


def _channel(source: Any, primary_name: str, legacy_name: str | None = None) -> Any:
    primary = _value(source, primary_name)
    if _has_evidence(primary):
        return primary
    if legacy_name:
        legacy = _value(source, legacy_name)
        if _has_evidence(legacy):
            return legacy
    return primary if primary is not None else ()


def _has_evidence(evidence: Any) -> bool:
    if evidence is None:
        return False
    if isinstance(evidence, Mapping):
        return any(value not in (None, "", (), [], {}) for value in evidence.values())
    if isinstance(evidence, Sequence) and not isinstance(evidence, (str, bytes, bytearray)):
        return len(evidence) > 0
    for field_name in ("evidence_ids", "rows", "metrics", "summary", "values"):
        value = _value(evidence, field_name)
        if value not in (None, "", (), [], {}):
            return True
    status = _text(_value(evidence, "availability_status"))
    return status in {"present", "ready", "partial"}


def _display_rows(evidence: Any, scope_classification: ScopeClassification) -> tuple[EvidenceDisplayRow, ...]:
    rows = _extract_rows(evidence)
    if not rows and _has_evidence(evidence):
        rows = (_mapping_from_evidence(evidence),)
    display_rows = []
    for index, row in enumerate(rows):
        values = _value(row, "values", row if isinstance(row, Mapping) else {})
        display_rows.append(
            EvidenceDisplayRow(
                label=_first_text(_value(row, "label"), _value(row, "metric"), _value(row, "row_id"), f"evidence-{index + 1}"),
                value=_first_value(values, "value", "summary", "status", "recommendation"),
                unit=_text(_value(values, "unit")),
                interpretation=_first_text(_value(values, "interpretation"), _value(row, "summary"), _summary_text(evidence)),
                evidence_ref_label=_first_text(_value(row, "row_id"), _value(row, "source"), _value(row, "evidence_ref_label")),
                freshness_status=_freshness_from_evidence(evidence),
                scope_classification=scope_classification,
            )
        )
    return tuple(display_rows)


def _extract_rows(evidence: Any) -> tuple[Any, ...]:
    if evidence is None:
        return ()
    rows = _value(evidence, "rows")
    if rows:
        return tuple(rows)
    if isinstance(evidence, Sequence) and not isinstance(evidence, (str, bytes, bytearray)):
        return tuple(evidence)
    return ()


def _mapping_from_evidence(evidence: Any) -> Mapping[str, Any]:
    if isinstance(evidence, Mapping):
        return evidence
    return {
        "row_id": _first_text(_value(evidence, "domain"), _value(evidence, "availability_status"), "evidence"),
        "values": {
            "summary": _summary_text(evidence),
            "status": _text(_value(evidence, "availability_status"), "present"),
        },
    }


def _first_value(mapping: Any, *keys: str) -> str | int | float | None:
    if not isinstance(mapping, Mapping):
        return None
    for key in keys:
        value = mapping.get(key)
        if value not in (None, "", (), [], {}):
            if isinstance(value, (str, int, float)):
                return value
            return str(value)
    return None


def _summary_text(evidence: Any) -> str:
    return _first_text(
        _value(evidence, "summary"),
        _value(evidence, "description"),
        _value(evidence, "message"),
        _value(evidence, "availability_status"),
    )


def _freshness_from_evidence(evidence: Any) -> str:
    freshness = _value(evidence, "freshness")
    return _first_text(_value(freshness, "freshness_status"), _value(freshness, "status"), "unknown")


def _freshness_label(evidence_pack_contract: EvidencePackContract | Mapping[str, Any]) -> str:
    for field_name in ("freshness", "stale_evidence"):
        value = _value(evidence_pack_contract, field_name)
        if _has_evidence(value):
            return _text(value, "available")
    return "unknown"


def _evidence_section(
    section_id: str,
    title: str,
    scope_classification: ScopeClassification,
    evidence: Any,
    fallback_rows: tuple[EvidenceDisplayRow, ...] = (),
) -> EvidenceReviewSection:
    rows = _display_rows(evidence, scope_classification)
    return EvidenceReviewSection(
        section_id=section_id,
        title=title,
        scope_classification=scope_classification,
        rows=rows or fallback_rows,
        limitations=() if _has_evidence(evidence) else ("deterministic evidence unavailable",),
    )


def _unavailable_state(
    state_id: str,
    reason_code: str,
    title: str,
    message: str,
    required_contract: str,
    missing_fields: tuple[str, ...],
    scope_classification: ScopeClassification,
) -> UnavailableVisualState:
    return UnavailableVisualState(
        state_id=state_id,
        reason_code=reason_code,
        title=title,
        message=message,
        required_contract=required_contract,
        missing_fields=missing_fields,
        scope_classification=scope_classification,
        prohibited_substitutes=("allowed_visualizations", "chart_metadata", "fake_static_svg", "llm_text"),
        next_deterministic_step=f"Provide {required_contract} from backend deterministic contracts.",
    )


def _unavailable_section(
    section_id: str,
    unavailable_states: tuple[UnavailableVisualState, ...],
) -> EvidenceReviewSection:
    return EvidenceReviewSection(
        section_id=section_id,
        title="Unavailable states",
        scope_classification="current_scope",
        rows=tuple(
            EvidenceDisplayRow(
                label=state.reason_code,
                value=state.title,
                unit="",
                interpretation=state.message,
                evidence_ref_label=state.required_contract,
                freshness_status="unavailable",
                scope_classification=state.scope_classification,
            )
            for state in unavailable_states
        ),
        limitations=tuple(state.next_deterministic_step for state in unavailable_states),
    )


def _unavailable_for_flow(flow_kind: str, evidence_channels: Mapping[str, Any]) -> tuple[UnavailableVisualState, ...]:
    if flow_kind in SIZING_FLOW_KINDS and not _has_evidence(_channel(evidence_channels, "sizing_evidence")):
        return (
            _unavailable_state(
                f"{flow_kind}-sizing-evidence-unavailable",
                "sizing_evidence_missing",
                "Sizing evidence unavailable",
                "predictive_sizing and comparative_sizing require real sizing evidence contracts.",
                "sizing_evidence",
                ("sizing_evidence",),
                "current_scope",
            ),
        )
    if flow_kind in COMPARISON_FLOW_KINDS and not _has_evidence(evidence_channels["comparison_evidence"]):
        return (
            _unavailable_state(
                f"{flow_kind}-comparison-evidence-unavailable",
                "comparison_evidence_missing",
                "Comparison evidence unavailable",
                "comparison requires deterministic comparison contract.",
                "comparison_evidence",
                ("comparison_evidence",),
                "comparative_output",
            ),
        )
    return ()


def _screen3_status_label(flow_kind: str, evidence_channels: Mapping[str, Any]) -> str:
    if flow_kind in TEMPORAL_FLOW_KINDS:
        return "window-level diagnostic posture" if _has_evidence(evidence_channels["temporal_evidence"]) else "unavailable"
    if flow_kind in SET_FLOW_KINDS:
        return "set-level diagnostic posture" if _has_evidence(evidence_channels["aggregate_evidence"]) else "unavailable"
    if flow_kind in COMPARISON_FLOW_KINDS:
        return "comparative diagnostic posture" if _has_evidence(evidence_channels["comparison_evidence"]) else "unavailable"
    if flow_kind in FLEET_FLOW_KINDS:
        return "fleet/cohort diagnostic posture" if _has_evidence(evidence_channels["fleet_or_cohort_evidence"]) else "unavailable"
    if flow_kind in SIZING_FLOW_KINDS:
        return "unavailable"
    return "point-in-time diagnostic snapshot" if _has_evidence(evidence_channels["selected_diagnostic_evidence"]) else "unavailable"


def _primary_issue_label(flow_kind: str, evidence_channels: Mapping[str, Any]) -> str:
    if flow_kind in TEMPORAL_FLOW_KINDS:
        return _summary_text(evidence_channels["temporal_evidence"])
    if flow_kind in SET_FLOW_KINDS:
        return _summary_text(evidence_channels["aggregate_evidence"])
    if flow_kind in COMPARISON_FLOW_KINDS:
        return _summary_text(evidence_channels["comparison_evidence"])
    if flow_kind in FLEET_FLOW_KINDS:
        return _summary_text(evidence_channels["fleet_or_cohort_evidence"])
    return _summary_text(evidence_channels["selected_diagnostic_evidence"])


def _number_from_evidence(evidence: Any, field_name: str) -> float | None:
    value = _value(evidence, field_name)
    if value is None and isinstance(evidence, Mapping):
        value = _value(_value(evidence, "metrics", {}), field_name)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _driver_labels(flow_kind: str, evidence_channels: Mapping[str, Any]) -> tuple[str, ...]:
    if flow_kind in SET_FLOW_KINDS:
        return _tuple_texts(_value(evidence_channels["aggregate_evidence"], "repeated_drivers"))
    if flow_kind in COMPARISON_FLOW_KINDS:
        return _tuple_texts(_value(evidence_channels["comparison_evidence"], "delta_drivers"))
    if flow_kind in FLEET_FLOW_KINDS:
        return _tuple_texts(_value(evidence_channels["fleet_or_cohort_evidence"], "outlier_members"))
    return _tuple_texts(_value(evidence_channels["selected_diagnostic_evidence"], "top_driver_labels"))


def _tuple_texts(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return tuple(_text(item) for item in value if _text(item))
    return (_text(value),)


def _screen3_scope_projection_section(
    flow_kind: str,
    evidence_channels: Mapping[str, Any],
) -> EvidenceReviewSection:
    rows = (
        EvidenceDisplayRow(
            label="selected_count",
            value=_first_value(evidence_channels["selected_set_evidence"], "selected_count") or "deterministic evidence required",
            unit="reports",
            interpretation="multi_awr_set selected-scope analysis set, not comparison",
            evidence_ref_label="selected_set_evidence",
            freshness_status="unknown",
        ),
        EvidenceDisplayRow(
            label="aggregate_posture",
            value=_summary_text(evidence_channels["aggregate_evidence"]) or "unavailable",
            unit="",
            interpretation="aggregate posture only from aggregate_evidence",
            evidence_ref_label="aggregate_evidence",
            freshness_status="unknown",
        ),
        EvidenceDisplayRow(
            label="repeated_drivers",
            value=", ".join(_tuple_texts(_value(evidence_channels["aggregate_evidence"], "repeated_drivers"))) or "unavailable",
            unit="",
            interpretation="repeated drivers only from deterministic aggregate evidence",
            evidence_ref_label="aggregate_evidence",
            freshness_status="unknown",
        ),
        EvidenceDisplayRow(
            label="outlier_members",
            value=", ".join(_tuple_texts(_value(evidence_channels["fleet_or_cohort_evidence"], "outlier_members"))) or "unavailable",
            unit="",
            interpretation="outlier members only from fleet_or_cohort_evidence",
            evidence_ref_label="fleet_or_cohort_evidence",
            freshness_status="unknown",
        ),
        EvidenceDisplayRow(
            label="delta_drivers",
            value=", ".join(_tuple_texts(_value(evidence_channels["comparison_evidence"], "delta_drivers"))) or "unavailable",
            unit="",
            interpretation="delta drivers only from deterministic comparison evidence",
            evidence_ref_label="comparison_evidence",
            freshness_status="unknown",
            scope_classification="comparative_output",
        ),
    )
    return EvidenceReviewSection(
        section_id="screen3-dynamic-scope-projection",
        title=f"Dynamic projection for {flow_kind}",
        scope_classification="current_scope",
        rows=rows,
        limitations=() if flow_kind in SUPPORTED_FLOW_KINDS else ("unsupported flow_kind",),
    )


def _missing_evidence_messages(evidence_channels: Mapping[str, Any]) -> tuple[str, ...]:
    missing = evidence_channels["missing_evidence"]
    if not _has_evidence(missing):
        return ()
    return tuple(
        _first_text(_value(item, "message"), _value(item, "reason_code"), _text(item))
        for item in _as_sequence(missing)
    )


def _as_sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return (value,)


def _historical_mode_panel(
    flow_kind: str,
    evidence_channels: Mapping[str, Any],
    evidence_pack_contract: EvidencePackContract | Mapping[str, Any],
) -> EvidenceReviewModePanel:
    temporal_evidence = evidence_channels["temporal_evidence"]
    supporting_historical_context = evidence_channels["supporting_historical_context"]
    ready = _has_evidence(temporal_evidence) and flow_kind in TEMPORAL_FLOW_KINDS
    availability = "ready" if ready else ("partial" if _has_evidence(supporting_historical_context) else "unavailable")
    visuals = _visual_contracts(evidence_channels, "historical_supporting_context")
    unavailable_states = () if availability != "unavailable" else (
        _unavailable_state(
            "screen4-historical-unavailable",
            "temporal_evidence_missing",
            "Historical Review unavailable",
            "Historical context is supporting and cannot become selected-scope truth.",
            "temporal_evidence",
            ("temporal_evidence",),
            "historical_supporting_context",
        ),
    )
    unavailable_states = unavailable_states + _visual_contract_unavailable_states(
        mode="historical",
        availability=availability,
        visuals=visuals,
        scope_classification="historical_supporting_context",
    )
    return EvidenceReviewModePanel(
        mode="historical",
        availability=availability,
        first_fold_summary=_summary_text(temporal_evidence) or "historical context is supporting",
        primary_cards=(
            _evidence_section("screen4-temporal-evidence", "Temporal evidence", "historical_supporting_context", temporal_evidence),
        ),
        secondary_sections=(
            _evidence_section(
                "screen4-supporting-historical-context",
                "Supporting historical context",
                "historical_supporting_context",
                supporting_historical_context,
            ),
        ),
        visuals=visuals,
        evidence_table=_display_rows(temporal_evidence, "historical_supporting_context"),
        unavailable_states=unavailable_states,
        llm_explanation=_llm_explanation_boundary(evidence_pack_contract),
    )


def _comparative_mode_panel(
    selected_scope_contract: SelectedReviewScopeContract | Mapping[str, Any],
    flow_kind: str,
    evidence_channels: Mapping[str, Any],
    evidence_pack_contract: EvidencePackContract | Mapping[str, Any],
) -> EvidenceReviewModePanel:
    comparison_evidence = evidence_channels["comparison_evidence"]
    deterministic_comparison_ready = _comparison_contract_ready(selected_scope_contract, flow_kind, comparison_evidence)
    availability = "ready" if deterministic_comparison_ready else "unavailable"
    visuals = _visual_contracts(evidence_channels, "comparative_output")
    unavailable_states = () if deterministic_comparison_ready else (
        _unavailable_state(
            "screen4-comparative-unavailable",
            "comparison_contract_required",
            "Comparative Review unavailable",
            "comparison requires deterministic comparison contract; multi target comparison supports n_way targets.",
            "comparison_evidence",
            ("comparison_evidence", "target_a", "target_b"),
            "comparative_output",
        ),
    )
    unavailable_states = unavailable_states + _visual_contract_unavailable_states(
        mode="comparative",
        availability=availability,
        visuals=visuals,
        scope_classification="comparative_output",
    )
    return EvidenceReviewModePanel(
        mode="comparative",
        availability=availability,
        first_fold_summary=_summary_text(comparison_evidence) or "deterministic comparison contract required",
        primary_cards=(
            _evidence_section("screen4-comparison-evidence", "Comparison evidence", "comparative_output", comparison_evidence),
        ),
        secondary_sections=(
            _evidence_section("screen4-n-way-comparison", "N-way multi target comparison", "comparative_output", comparison_evidence),
        ),
        visuals=visuals,
        evidence_table=_display_rows(comparison_evidence, "comparative_output"),
        unavailable_states=unavailable_states,
        llm_explanation=_llm_explanation_boundary(evidence_pack_contract),
    )


def _deep_analysis_mode_panel(
    flow_kind: str,
    evidence_channels: Mapping[str, Any],
    evidence_pack_contract: EvidencePackContract | Mapping[str, Any],
) -> EvidenceReviewModePanel:
    deep_analysis_detail_evidence = evidence_channels["deep_analysis_evidence"]
    ready = _has_evidence(deep_analysis_detail_evidence)
    availability = "ready" if ready else ("partial" if flow_kind in SINGLE_SCOPE_FLOW_KINDS else "unavailable")
    visuals = _visual_contracts(evidence_channels, "deep_analysis_current_scope")
    unavailable_states = () if ready else (
        _unavailable_state(
            "screen4-deep-analysis-unavailable",
            "deep_analysis_detail_evidence_missing",
            "Deep Analysis unavailable",
            "Deep Analysis is ready if detail evidence exists.",
            "deep_analysis_evidence",
            ("deep_analysis_evidence",),
            "deep_analysis_current_scope",
        ),
    )
    unavailable_states = unavailable_states + _visual_contract_unavailable_states(
        mode="deep_analysis",
        availability=availability,
        visuals=visuals,
        scope_classification="deep_analysis_current_scope",
    )
    return EvidenceReviewModePanel(
        mode="deep_analysis",
        availability=availability,
        first_fold_summary=_summary_text(deep_analysis_detail_evidence) or "detail evidence exists requirement",
        primary_cards=(
            _evidence_section(
                "screen4-deep-analysis-evidence",
                "Deep Analysis evidence",
                "deep_analysis_current_scope",
                deep_analysis_detail_evidence,
            ),
        ),
        secondary_sections=(),
        visuals=visuals,
        evidence_table=_display_rows(deep_analysis_detail_evidence, "deep_analysis_current_scope"),
        unavailable_states=unavailable_states,
        llm_explanation=_llm_explanation_boundary(evidence_pack_contract),
    )


def _comparison_contract_ready(
    selected_scope_contract: SelectedReviewScopeContract | Mapping[str, Any],
    flow_kind: str,
    comparison_evidence: Any,
) -> bool:
    if not _has_evidence(comparison_evidence):
        return False
    if flow_kind == "multi_target_comparison":
        return _target_count(selected_scope_contract, comparison_evidence) >= 2
    if flow_kind == "comparison":
        return bool(_value(selected_scope_contract, "target_a") and _value(selected_scope_contract, "target_b"))
    return False


def _target_count(selected_scope_contract: Any, comparison_evidence: Any) -> int:
    targets = _value(comparison_evidence, "targets")
    if targets:
        return len(tuple(targets))
    target_a = _value(selected_scope_contract, "target_a")
    target_b = _value(selected_scope_contract, "target_b")
    return len(tuple(target for target in (target_a, target_b) if target))


def _active_screen4_mode(
    flow_kind: str,
    historical: EvidenceReviewModePanel,
    comparative: EvidenceReviewModePanel,
    deep_analysis: EvidenceReviewModePanel,
) -> str:
    if flow_kind in COMPARISON_FLOW_KINDS and comparative.availability == "ready":
        return "comparative"
    if flow_kind in TEMPORAL_FLOW_KINDS and historical.availability in {"ready", "partial"}:
        return "historical"
    if deep_analysis.availability == "ready":
        return "deep_analysis"
    return "historical"


def _screen4_cross_mode_warnings(flow_kind: str, evidence_channels: Mapping[str, Any]) -> tuple[str, ...]:
    warnings = []
    if flow_kind == "multi_awr_set":
        warnings.append("multi_awr_set is a selected_scope_analysis_set and analysis_set_not_comparison.")
    if _has_evidence(evidence_channels["supporting_historical_context"]):
        warnings.append("supporting_historical_context_not_selected_truth.")
    return tuple(warnings)


def _screen5_title(flow_kind: str) -> str:
    if flow_kind in TEMPORAL_FLOW_KINDS:
        return "Timeframe recommendation posture"
    if flow_kind in SET_FLOW_KINDS:
        return "Set-level and member-level recommendation backlog"
    if flow_kind in COMPARISON_FLOW_KINDS:
        return "Delta-based recommendation"
    if flow_kind in FLEET_FLOW_KINDS:
        return "Fleet action backlog"
    return "Selected diagnostic recommendation"


def _screen5_secondary_sections(
    flow_kind: str,
    evidence_channels: Mapping[str, Any],
    unavailable: tuple[UnavailableVisualState, ...],
) -> tuple[EvidenceReviewSection, ...]:
    sections = [
        _evidence_section("screen5-temporal-recommendations", "Recurring/degrading/improving evidence", "historical_supporting_context", evidence_channels["temporal_evidence"]),
        _evidence_section("screen5-set-backlog", "Set-level and member-level backlog", "current_scope", evidence_channels["selected_set_evidence"]),
        _evidence_section("screen5-delta-recommendations", "Delta-based recommendation evidence", "comparative_output", evidence_channels["comparison_evidence"]),
        _evidence_section("screen5-fleet-backlog", "Fleet recommendation themes", "governance_persisted", evidence_channels["fleet_or_cohort_evidence"]),
        _unavailable_section("screen5-unavailable-recommendation-state", unavailable),
    ]
    if flow_kind in SINGLE_SCOPE_FLOW_KINDS:
        return tuple(sections[:1] + sections[-1:])
    return tuple(section for section in sections if section.rows or section.limitations)


def _screen6_title(flow_kind: str) -> str:
    if flow_kind in TEMPORAL_FLOW_KINDS:
        return "Recurrence, trend, anomaly, and outcome governance candidates"
    if flow_kind in SET_FLOW_KINDS:
        return "Repeated-pattern governance candidates across selected set"
    if flow_kind in COMPARISON_FLOW_KINDS:
        return "Comparison-derived learning candidates"
    if flow_kind in FLEET_FLOW_KINDS:
        return "Fleet-level candidate queues and governed runtime eligibility"
    return "Governance candidates linked to selected report/run"


def _screen6_candidate_queue(
    flow_kind: str,
    evidence_channels: Mapping[str, Any],
) -> tuple[EvidenceReviewSection, ...]:
    scope = "governance_persisted"
    if flow_kind in COMPARISON_FLOW_KINDS:
        scope = "comparative_output"
    return (
        _evidence_section("screen6-governance-candidates", _screen6_title(flow_kind), scope, evidence_channels["governance_evidence"]),
        _evidence_section("screen6-repeated-patterns", "Repeated-pattern governance candidates", "governance_persisted", evidence_channels["aggregate_evidence"]),
    )


def _visual_contracts(
    evidence_channels: Mapping[str, Any],
    scope_classification: ScopeClassification,
) -> tuple[TimeSeriesVisual | DistributionVisual | ViolinVisual | ComparisonDeltaVisual, ...]:
    visualization_evidence = evidence_channels["visualization_evidence"]
    if not _has_evidence(visualization_evidence):
        return ()
    visuals = []
    for item in _as_sequence(visualization_evidence):
        visual_kind = _text(_value(item, "visual_kind") or _value(item, "kind"))
        title = _first_text(_value(item, "title"), visual_kind, "Evidence visual")
        if visual_kind == "time_series":
            visuals.append(
                TimeSeriesVisual(
                    visual_id=_first_text(_value(item, "visual_id"), "time-series"),
                    title=title,
                    scope_classification=scope_classification,
                    provenance=_tuple_texts(_value(item, "provenance") or _value(item, "source_evidence_ids")),
                    unavailable_state=_visual_unavailable_state(item, "TimeSeriesVisual", scope_classification),
                )
            )
        elif visual_kind == "distribution":
            visuals.append(
                DistributionVisual(
                    visual_id=_first_text(_value(item, "visual_id"), "distribution"),
                    title=title,
                    scope_classification=scope_classification,
                    metric_name=_text(_value(item, "metric_name")),
                    provenance=_tuple_texts(_value(item, "provenance") or _value(item, "source_evidence_ids")),
                    unavailable_state=_visual_unavailable_state(item, "DistributionVisual", scope_classification),
                )
            )
        elif visual_kind == "violin":
            visuals.append(
                ViolinVisual(
                    visual_id=_first_text(_value(item, "visual_id"), "violin"),
                    distribution=DistributionVisual(
                        visual_id=_first_text(_value(item, "visual_id"), "violin-distribution"),
                        visual_kind="distribution",
                        title=title,
                        scope_classification=scope_classification,
                        metric_name=_text(_value(item, "metric_name")),
                        provenance=_tuple_texts(_value(item, "provenance") or _value(item, "source_evidence_ids")),
                        unavailable_state=_visual_unavailable_state(item, "ViolinVisual", scope_classification),
                    ),
                    density_method=_text(_value(item, "density_method")),
                )
            )
        elif visual_kind == "comparison_delta":
            visuals.append(
                ComparisonDeltaVisual(
                    visual_id=_first_text(_value(item, "visual_id"), "comparison-delta"),
                    title=title,
                    scope_classification="comparative_output",
                    target_a=_text(_value(item, "target_a")),
                    target_b=_text(_value(item, "target_b")),
                    provenance=_tuple_texts(_value(item, "provenance") or _value(item, "source_evidence_ids")),
                    unavailable_state=_visual_unavailable_state(item, "ComparisonDeltaVisual", "comparative_output"),
                )
            )
    return tuple(visuals)


def _visual_contract_unavailable_states(
    *,
    mode: str,
    availability: str,
    visuals: tuple[TimeSeriesVisual | DistributionVisual | ViolinVisual | ComparisonDeltaVisual, ...],
    scope_classification: ScopeClassification,
) -> tuple[UnavailableVisualState, ...]:
    if availability not in {"ready", "partial"} or visuals:
        return ()
    return (
        UnavailableVisualState(
            state_id=f"screen4-{mode}-visual-evidence-unavailable",
            reason_code="visual_evidence_unavailable",
            title="Visual evidence unavailable",
            message=(
                "Evidence exists for this mode, but no explicit visualization_evidence "
                "contract was supplied."
            ),
            required_contract="visualization_evidence",
            missing_fields=("visualization_evidence",),
            scope_classification=scope_classification,
            prohibited_substitutes=(
                "generated_html",
                "browser_cache",
                "llm_text",
                "static_fake_visual",
                "allowed_visualizations",
            ),
            next_deterministic_step=(
                "Produce a deterministic visualization_evidence contract before rendering a visual."
            ),
        ),
    )


def _visual_unavailable_state(
    item: Any,
    required_contract: str,
    scope_classification: ScopeClassification,
) -> UnavailableVisualState | None:
    if _has_evidence(_value(item, "source_evidence_ids")) or _has_evidence(_value(item, "provenance")):
        return None
    return _unavailable_state(
        f"{required_contract}-source-evidence-missing",
        "missing_visual_evidence",
        "Visual evidence unavailable",
        "missing visual evidence must produce UnavailableVisualState.",
        required_contract,
        ("source_evidence_ids", "provenance"),
        scope_classification,
    )


def _llm_explanation_boundary(evidence_pack_contract: EvidencePackContract | Mapping[str, Any]) -> ExplanationBlock:
    eligibility = _value(evidence_pack_contract, "llm_explanation_eligibility")
    return ExplanationBlock(
        eligibility="eligible_to_explain_decided_truth" if _has_evidence(eligibility) else "unavailable",
        explanation_text="",
        explains_refs=_tuple_texts(_value(eligibility, "source_evidence_ids")),
        prohibited_as_evidence=True,
    )


def _provenance_labels(
    selected_scope_contract: SelectedReviewScopeContract | Mapping[str, Any],
    evidence_pack_contract: EvidencePackContract | Mapping[str, Any],
) -> tuple[str, ...]:
    return tuple(
        label
        for label in (
            _first_text(_value(_value(selected_scope_contract, "provenance"), "source_system"), "selected_scope_contract"),
            _first_text(_value(_value(evidence_pack_contract, "provenance"), "source_system"), "evidence_pack_contract"),
        )
        if label
    )


def _internal_refs(
    selected_scope_contract: SelectedReviewScopeContract | Mapping[str, Any],
    evidence_pack_contract: EvidencePackContract | Mapping[str, Any],
) -> tuple[str, ...]:
    return tuple(
        ref
        for ref in (
            _text(_value(selected_scope_contract, "selected_flow_id")),
            _text(_value(evidence_pack_contract, "evidence_pack_id")),
        )
        if ref
    )
