"""Screen 4 Deep Analysis dynamic visualization selection.

This module inspects validated Deep Analysis contract sections and rows to
select future visualization candidates. It is non-rendering and non-mutating:
it does not render HTML/SVG, use browser APIs, call services, invoke LLMs,
execute parsers or comparisons, or depend on generated dashboard artifacts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from numbers import Real
import re
from typing import Any

from src.reporting.dashboard.screen4.deep_analysis_contract import (
    DeepAnalysisState,
    DeepAnalysisValidationResult,
    ScopeClassification,
    validate_deep_analysis_contract,
)


MIN_TIME_SERIES_POINTS = 2
MIN_DISTRIBUTION_SAMPLES = 3


class VisualizationStatus(str, Enum):
    ELIGIBLE = "eligible"
    BLOCKED = "blocked"
    OMITTED = "omitted"
    NOT_REQUESTED = "not_requested"
    NOT_SUPPORTED = "not_supported"


class VisualizationFamily(str, Enum):
    CONTRIBUTION = "contribution"
    RANKED_CONTRIBUTION = "ranked_contribution"
    TIME_SERIES = "time_series"
    ALIGNED_OVERLAY = "aligned_overlay"
    DISTRIBUTION_EVIDENCE = "distribution_evidence"
    ANOMALY_TIMELINE = "anomaly_timeline"
    PRESSURE_BAND = "pressure_band"
    TOPOLOGY_FACT_MAP = "topology_fact_map"
    SIMILARITY_NEIGHBORHOOD = "similarity_neighborhood"
    FLEET_POPULATION = "fleet_population"
    TABLE_ONLY = "table_only"


class EvidenceShape(str, Enum):
    CATEGORICAL_CONTRIBUTION = "categorical_contribution"
    RANKED_ROWS = "ranked_rows"
    TIME_INDEXED_SERIES = "time_indexed_series"
    ALIGNED_MULTI_SERIES = "aligned_multi_series"
    NUMERIC_SAMPLES = "numeric_samples"
    INTERVAL_EVENTS = "interval_events"
    SCALAR_THRESHOLD = "scalar_threshold"
    TOPOLOGY_FACTS = "topology_facts"
    IDENTITY_ROWS = "identity_rows"
    SCORE_VECTOR = "score_vector"
    SIMILARITY_CASES = "similarity_cases"
    POPULATION_SAMPLES = "population_samples"


@dataclass(frozen=True)
class DeepAnalysisVisualizationCandidate:
    candidate_id: str
    status: VisualizationStatus
    visualization_family: VisualizationFamily
    suggested_title: str
    scope_classification: str
    evidence_shape: EvidenceShape
    section_id: str
    row_ids: tuple[str, ...]
    required_data_shape: str
    observed_data_shape: str
    minimum_requirements: tuple[str, ...]
    blocked_reason: str = ""
    omitted_reason: str = ""
    provenance_summary: str = ""
    freshness_summary: str = ""
    rendering_boundary: str = "selection_only_no_rendering"
    recommended_renderer: str = ""
    label_guidance: str = ""
    is_supporting_context: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "status": self.status.value,
            "visualization_family": self.visualization_family.value,
            "suggested_title": self.suggested_title,
            "scope_classification": self.scope_classification,
            "evidence_shape": self.evidence_shape.value,
            "section_id": self.section_id,
            "row_ids": list(self.row_ids),
            "required_data_shape": self.required_data_shape,
            "observed_data_shape": self.observed_data_shape,
            "minimum_requirements": list(self.minimum_requirements),
            "blocked_reason": self.blocked_reason,
            "omitted_reason": self.omitted_reason,
            "provenance_summary": self.provenance_summary,
            "freshness_summary": self.freshness_summary,
            "rendering_boundary": self.rendering_boundary,
            "recommended_renderer": self.recommended_renderer,
            "label_guidance": self.label_guidance,
            "is_supporting_context": self.is_supporting_context,
        }


@dataclass(frozen=True)
class DeepAnalysisVisualizationSelectionResult:
    candidates: tuple[DeepAnalysisVisualizationCandidate, ...]
    messages: tuple[str, ...] = ()

    @property
    def eligible_candidates(self) -> tuple[DeepAnalysisVisualizationCandidate, ...]:
        return tuple(
            candidate
            for candidate in self.candidates
            if candidate.status == VisualizationStatus.ELIGIBLE
            and candidate.visualization_family != VisualizationFamily.TABLE_ONLY
        )

    @property
    def blocked_candidates(self) -> tuple[DeepAnalysisVisualizationCandidate, ...]:
        return tuple(
            candidate
            for candidate in self.candidates
            if candidate.status
            in {VisualizationStatus.BLOCKED, VisualizationStatus.NOT_SUPPORTED}
        )

    @property
    def omitted_candidates(self) -> tuple[DeepAnalysisVisualizationCandidate, ...]:
        return tuple(
            candidate
            for candidate in self.candidates
            if candidate.status
            in {VisualizationStatus.OMITTED, VisualizationStatus.NOT_REQUESTED}
        )

    @property
    def table_only_sections(self) -> tuple[str, ...]:
        return tuple(
            candidate.section_id
            for candidate in self.candidates
            if candidate.visualization_family == VisualizationFamily.TABLE_ONLY
        )

    @property
    def has_eligible_visuals(self) -> bool:
        return bool(self.eligible_candidates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "eligible_candidates": [
                candidate.to_dict() for candidate in self.eligible_candidates
            ],
            "blocked_candidates": [
                candidate.to_dict() for candidate in self.blocked_candidates
            ],
            "omitted_candidates": [
                candidate.to_dict() for candidate in self.omitted_candidates
            ],
            "table_only_sections": list(self.table_only_sections),
            "messages": list(self.messages),
            "has_eligible_visuals": self.has_eligible_visuals,
        }


def select_deep_analysis_visualizations(
    contract: Any,
    validation_result: DeepAnalysisValidationResult | Mapping[str, Any] | None = None,
) -> DeepAnalysisVisualizationSelectionResult:
    """Select future Deep Analysis visualization candidates without rendering."""

    if not isinstance(contract, Mapping) or not contract:
        return DeepAnalysisVisualizationSelectionResult(
            candidates=(),
            messages=("contract_missing_or_invalid",),
        )

    validation = validation_result or validate_deep_analysis_contract(contract)
    validation_state = _validation_state(validation)
    validation_ready = _validation_ready(validation)
    allowed_section_ids = _validation_ids(validation, "allowed_section_ids")
    supporting_section_ids = _validation_ids(validation, "supporting_section_ids")
    current_visuals_allowed = validation_ready
    supporting_visuals_allowed = validation_state in {
        DeepAnalysisState.READY.value,
        DeepAnalysisState.HISTORICAL_SUPPORTING_CONTEXT.value,
    }

    sections = _sections_by_id(contract)
    rows_by_section = _rows_by_section(contract)
    candidates: list[DeepAnalysisVisualizationCandidate] = []
    messages: list[str] = []

    for section_id, rows in rows_by_section.items():
        section = sections.get(section_id, {})
        scope = _section_scope(section, rows)
        if scope == ScopeClassification.CURRENT_SCOPE.value:
            if not (current_visuals_allowed and section_id in allowed_section_ids):
                candidates.append(
                    _blocked_section_candidate(
                        section,
                        rows,
                        "current_scope_contract_not_ready",
                    )
                )
                continue
            candidates.extend(_candidates_for_allowed_section(section, rows))
            continue
        if scope == ScopeClassification.HISTORICAL_SUPPORTING_CONTEXT.value:
            if not (supporting_visuals_allowed and section_id in supporting_section_ids):
                candidates.append(
                    _blocked_section_candidate(
                        section,
                        rows,
                        "historical_supporting_context_not_validated",
                    )
                )
                continue
            candidates.extend(
                _candidates_for_allowed_section(section, rows, supporting=True)
            )
            continue
        candidates.append(_blocked_scope_candidate(section, rows, scope))

    candidates.extend(_chart_eligibility_candidates(contract.get("chart_eligibility")))
    if not candidates:
        messages.append("no_visual_candidates_from_validated_evidence_shapes")

    return DeepAnalysisVisualizationSelectionResult(
        candidates=tuple(candidates),
        messages=tuple(messages),
    )


def _candidates_for_allowed_section(
    section: Mapping[str, Any],
    rows: list[Mapping[str, Any]],
    *,
    supporting: bool = False,
) -> list[DeepAnalysisVisualizationCandidate]:
    renderable_rows = [row for row in rows if _row_is_shape_eligible(row)]
    if not renderable_rows:
        return [
            _table_only_candidate(
                section,
                rows,
                "rows_do_not_contain_visual_shape",
                supporting=supporting,
            )
        ]

    shape_result = _detect_evidence_shape(section, renderable_rows)
    if shape_result["status"] == VisualizationStatus.BLOCKED:
        return [
            _candidate(
                section,
                renderable_rows,
                status=VisualizationStatus.BLOCKED,
                family=shape_result["family"],
                shape=shape_result["shape"],
                required_data_shape=shape_result["required"],
                observed_data_shape=shape_result["observed"],
                minimum_requirements=shape_result["minimum"],
                blocked_reason=shape_result["reason"],
                supporting=supporting,
            )
        ]
    if shape_result["family"] == VisualizationFamily.TABLE_ONLY:
        return [
            _table_only_candidate(
                section,
                rows,
                "valid_evidence_without_visual_shape",
                supporting=supporting,
            )
        ]
    return [
        _candidate(
            section,
            renderable_rows,
            status=VisualizationStatus.ELIGIBLE,
            family=shape_result["family"],
            shape=shape_result["shape"],
            required_data_shape=shape_result["required"],
            observed_data_shape=shape_result["observed"],
            minimum_requirements=shape_result["minimum"],
            supporting=supporting,
        )
    ]


def _detect_evidence_shape(
    section: Mapping[str, Any],
    rows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    explicit = _first_text(
        section.get("evidence_shape"),
        section.get("required_evidence_shape"),
        *[
            _first_text(row.get("evidence_shape"), row.get("visual_evidence_shape"))
            for row in rows
        ],
    )
    if explicit:
        explicit_result = _shape_from_name(explicit)
        if explicit_result:
            verified = _verify_explicit_shape(explicit_result, rows)
            if verified:
                return verified
            return explicit_result

    if _has_aligned_multi_series(rows):
        return _shape(
            VisualizationFamily.ALIGNED_OVERLAY,
            EvidenceShape.ALIGNED_MULTI_SERIES,
            "aligned rows with shared time/index axis and at least two series",
            f"{len(rows)} aligned rows",
            ("at least two series", "at least two aligned points"),
        )

    time_points = _time_indexed_point_count(rows)
    if time_points:
        if time_points < MIN_TIME_SERIES_POINTS:
            return _blocked_shape(
                VisualizationFamily.TIME_SERIES,
                EvidenceShape.TIME_INDEXED_SERIES,
                "time-indexed rows with at least two points",
                f"{time_points} point",
                ("at least two time-indexed points",),
                "time_series_points_below_minimum",
            )
        return _shape(
            VisualizationFamily.TIME_SERIES,
            EvidenceShape.TIME_INDEXED_SERIES,
            "time-indexed rows with at least two points",
            f"{time_points} points",
            ("at least two time-indexed points",),
        )

    sample_count = _numeric_sample_count(rows)
    if sample_count:
        if sample_count < MIN_DISTRIBUTION_SAMPLES:
            return _blocked_shape(
                VisualizationFamily.DISTRIBUTION_EVIDENCE,
                EvidenceShape.NUMERIC_SAMPLES,
                "real numeric sample arrays",
                f"{sample_count} sample",
                ("at least three numeric samples", "no synthetic samples"),
                "numeric_samples_below_minimum",
            )
        return _shape(
            VisualizationFamily.DISTRIBUTION_EVIDENCE,
            EvidenceShape.NUMERIC_SAMPLES,
            "real numeric sample arrays",
            f"{sample_count} samples",
            ("at least three numeric samples", "no synthetic samples"),
        )

    evidence_type = _normalized_text(section.get("evidence_type"))
    if evidence_type in {"rac_adg_topology_detail", "topology_fact", "topology_facts"}:
        return _shape(
            VisualizationFamily.TOPOLOGY_FACT_MAP,
            EvidenceShape.TOPOLOGY_FACTS,
            "topology/RAC/ADG identity or relationship facts",
            f"{len(rows)} topology rows",
            ("at least one topology fact row",),
        )
    if evidence_type in {"anomaly_supporting_context", "anomaly_event"}:
        return _shape(
            VisualizationFamily.ANOMALY_TIMELINE,
            EvidenceShape.INTERVAL_EVENTS,
            "time-bounded anomaly or interval events",
            f"{len(rows)} event rows",
            ("at least one event row",),
        )
    if evidence_type in {"similarity_supporting_context", "similarity_case"}:
        return _shape(
            VisualizationFamily.SIMILARITY_NEIGHBORHOOD,
            EvidenceShape.SIMILARITY_CASES,
            "similarity case rows",
            f"{len(rows)} similarity rows",
            ("at least one similarity row",),
        )
    if _has_scalar_threshold(rows):
        return _shape(
            VisualizationFamily.PRESSURE_BAND,
            EvidenceShape.SCALAR_THRESHOLD,
            "scalar value with threshold or comparator reference",
            f"{len(rows)} scalar threshold rows",
            ("at least one numeric scalar", "threshold or comparator reference"),
        )
    if _has_ranked_rows(rows):
        return _shape(
            VisualizationFamily.RANKED_CONTRIBUTION,
            EvidenceShape.RANKED_ROWS,
            "ranked rows with deterministic values",
            f"{len(rows)} ranked rows",
            ("at least one ranked deterministic row",),
        )
    if _has_score_vector(rows):
        return _shape(
            VisualizationFamily.CONTRIBUTION,
            EvidenceShape.SCORE_VECTOR,
            "score vector rows",
            f"{len(rows)} score rows",
            ("at least one score vector row",),
        )
    if _has_categorical_contribution(rows, evidence_type):
        return _shape(
            VisualizationFamily.CONTRIBUTION,
            EvidenceShape.CATEGORICAL_CONTRIBUTION,
            "categorical deterministic contribution rows",
            f"{len(rows)} contribution rows",
            ("at least one numeric deterministic value",),
        )
    return _shape(
        VisualizationFamily.TABLE_ONLY,
        EvidenceShape.IDENTITY_ROWS,
        "validated evidence rows without visual shape",
        f"{len(rows)} table rows",
        ("validated deterministic rows",),
    )


def _shape(
    family: VisualizationFamily,
    shape: EvidenceShape,
    required: str,
    observed: str,
    minimum: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "status": VisualizationStatus.ELIGIBLE,
        "family": family,
        "shape": shape,
        "required": required,
        "observed": observed,
        "minimum": minimum,
        "reason": "",
    }


def _blocked_shape(
    family: VisualizationFamily,
    shape: EvidenceShape,
    required: str,
    observed: str,
    minimum: tuple[str, ...],
    reason: str,
) -> dict[str, Any]:
    return {
        "status": VisualizationStatus.BLOCKED,
        "family": family,
        "shape": shape,
        "required": required,
        "observed": observed,
        "minimum": minimum,
        "reason": reason,
    }


def _shape_from_name(value: str) -> dict[str, Any] | None:
    normalized = _normalized_text(value)
    mapping = {
        EvidenceShape.CATEGORICAL_CONTRIBUTION.value: (
            VisualizationFamily.CONTRIBUTION,
            EvidenceShape.CATEGORICAL_CONTRIBUTION,
        ),
        EvidenceShape.RANKED_ROWS.value: (
            VisualizationFamily.RANKED_CONTRIBUTION,
            EvidenceShape.RANKED_ROWS,
        ),
        EvidenceShape.TIME_INDEXED_SERIES.value: (
            VisualizationFamily.TIME_SERIES,
            EvidenceShape.TIME_INDEXED_SERIES,
        ),
        EvidenceShape.ALIGNED_MULTI_SERIES.value: (
            VisualizationFamily.ALIGNED_OVERLAY,
            EvidenceShape.ALIGNED_MULTI_SERIES,
        ),
        EvidenceShape.NUMERIC_SAMPLES.value: (
            VisualizationFamily.DISTRIBUTION_EVIDENCE,
            EvidenceShape.NUMERIC_SAMPLES,
        ),
        EvidenceShape.INTERVAL_EVENTS.value: (
            VisualizationFamily.ANOMALY_TIMELINE,
            EvidenceShape.INTERVAL_EVENTS,
        ),
        EvidenceShape.SCALAR_THRESHOLD.value: (
            VisualizationFamily.PRESSURE_BAND,
            EvidenceShape.SCALAR_THRESHOLD,
        ),
        EvidenceShape.TOPOLOGY_FACTS.value: (
            VisualizationFamily.TOPOLOGY_FACT_MAP,
            EvidenceShape.TOPOLOGY_FACTS,
        ),
        EvidenceShape.SIMILARITY_CASES.value: (
            VisualizationFamily.SIMILARITY_NEIGHBORHOOD,
            EvidenceShape.SIMILARITY_CASES,
        ),
        EvidenceShape.POPULATION_SAMPLES.value: (
            VisualizationFamily.FLEET_POPULATION,
            EvidenceShape.POPULATION_SAMPLES,
        ),
    }
    if normalized not in mapping:
        return None
    family, shape = mapping[normalized]
    return _shape(
        family,
        shape,
        f"validated {shape.value} evidence shape",
        f"explicit {shape.value}",
        ("explicit validated evidence shape",),
    )


def _verify_explicit_shape(
    shape_result: dict[str, Any],
    rows: list[Mapping[str, Any]],
) -> dict[str, Any] | None:
    shape = shape_result["shape"]
    if shape == EvidenceShape.NUMERIC_SAMPLES:
        sample_count = _numeric_sample_count(rows)
        if sample_count < MIN_DISTRIBUTION_SAMPLES:
            return _blocked_shape(
                VisualizationFamily.DISTRIBUTION_EVIDENCE,
                EvidenceShape.NUMERIC_SAMPLES,
                "real numeric sample arrays",
                f"{sample_count} sample",
                ("at least three numeric samples", "no synthetic samples"),
                "numeric_samples_below_minimum",
            )
        shape_result["observed"] = f"{sample_count} samples"
    elif shape == EvidenceShape.TIME_INDEXED_SERIES:
        point_count = _time_indexed_point_count(rows)
        if point_count < MIN_TIME_SERIES_POINTS:
            return _blocked_shape(
                VisualizationFamily.TIME_SERIES,
                EvidenceShape.TIME_INDEXED_SERIES,
                "time-indexed rows with at least two points",
                f"{point_count} point",
                ("at least two time-indexed points",),
                "time_series_points_below_minimum",
            )
        shape_result["observed"] = f"{point_count} points"
    elif shape == EvidenceShape.ALIGNED_MULTI_SERIES and not _has_aligned_multi_series(rows):
        return _blocked_shape(
            VisualizationFamily.ALIGNED_OVERLAY,
            EvidenceShape.ALIGNED_MULTI_SERIES,
            "aligned rows with shared time/index axis and at least two series",
            "aligned multi-series shape missing",
            ("at least two series", "at least two aligned points"),
            "aligned_multi_series_shape_missing",
        )
    return shape_result


def _candidate(
    section: Mapping[str, Any],
    rows: list[Mapping[str, Any]],
    *,
    status: VisualizationStatus,
    family: VisualizationFamily,
    shape: EvidenceShape,
    required_data_shape: str,
    observed_data_shape: str,
    minimum_requirements: tuple[str, ...],
    blocked_reason: str = "",
    omitted_reason: str = "",
    supporting: bool = False,
) -> DeepAnalysisVisualizationCandidate:
    section_id = _section_id(section, rows)
    return DeepAnalysisVisualizationCandidate(
        candidate_id=f"{family.value}:{_slug(section_id)}:{shape.value}",
        status=status,
        visualization_family=family,
        suggested_title=_suggested_title(section, family, supporting=supporting),
        scope_classification=_section_scope(section, rows),
        evidence_shape=shape,
        section_id=section_id,
        row_ids=tuple(_row_id(row) for row in rows if _row_id(row)),
        required_data_shape=required_data_shape,
        observed_data_shape=observed_data_shape,
        minimum_requirements=minimum_requirements,
        blocked_reason=blocked_reason,
        omitted_reason=omitted_reason,
        provenance_summary=_provenance_summary(section, rows),
        freshness_summary=_freshness_summary(section, rows),
        recommended_renderer=f"future_deep_analysis_{family.value}_renderer",
        label_guidance=_label_guidance(family, supporting=supporting),
        is_supporting_context=supporting,
    )


def _table_only_candidate(
    section: Mapping[str, Any],
    rows: list[Mapping[str, Any]],
    reason: str,
    *,
    supporting: bool = False,
) -> DeepAnalysisVisualizationCandidate:
    return _candidate(
        section,
        rows,
        status=VisualizationStatus.OMITTED,
        family=VisualizationFamily.TABLE_ONLY,
        shape=EvidenceShape.IDENTITY_ROWS,
        required_data_shape="validated rows without chart-ready shape",
        observed_data_shape=f"{len(rows)} validated rows",
        minimum_requirements=("render as table/text only",),
        omitted_reason=reason,
        supporting=supporting,
    )


def _blocked_section_candidate(
    section: Mapping[str, Any],
    rows: list[Mapping[str, Any]],
    reason: str,
) -> DeepAnalysisVisualizationCandidate:
    return _candidate(
        section,
        rows,
        status=VisualizationStatus.BLOCKED,
        family=VisualizationFamily.TABLE_ONLY,
        shape=EvidenceShape.IDENTITY_ROWS,
        required_data_shape="ready Deep Analysis contract and validator-allowed section",
        observed_data_shape=f"{len(rows)} rows before visual selection",
        minimum_requirements=("validated contract readiness", "allowed/supporting section id"),
        blocked_reason=reason,
        supporting=_section_scope(section, rows)
        == ScopeClassification.HISTORICAL_SUPPORTING_CONTEXT.value,
    )


def _blocked_scope_candidate(
    section: Mapping[str, Any],
    rows: list[Mapping[str, Any]],
    scope: str,
) -> DeepAnalysisVisualizationCandidate:
    family = (
        VisualizationFamily.FLEET_POPULATION
        if scope == ScopeClassification.FLEET_POPULATION.value
        else VisualizationFamily.TABLE_ONLY
    )
    status = (
        VisualizationStatus.NOT_SUPPORTED
        if scope == ScopeClassification.FLEET_POPULATION.value
        else VisualizationStatus.BLOCKED
    )
    return _candidate(
        section,
        rows,
        status=status,
        family=family,
        shape=(
            EvidenceShape.POPULATION_SAMPLES
            if scope == ScopeClassification.FLEET_POPULATION.value
            else EvidenceShape.IDENTITY_ROWS
        ),
        required_data_shape="current_scope or historical_supporting_context validated evidence",
        observed_data_shape=f"{scope or 'unknown'} scope",
        minimum_requirements=("Deep Analysis supported scope",),
        blocked_reason=f"{scope or 'unknown'}_scope_not_deep_analysis_visual_evidence",
    )


def _chart_eligibility_candidates(charts: Any) -> list[DeepAnalysisVisualizationCandidate]:
    if not isinstance(charts, list):
        return []
    candidates: list[DeepAnalysisVisualizationCandidate] = []
    for index, chart in enumerate(charts):
        if not isinstance(chart, Mapping):
            continue
        unsafe_flags = [
            flag
            for flag in (
                "browser_computation_allowed",
                "synthetic_data_allowed",
                "empty_chart_allowed",
            )
            if chart.get(flag) is True
        ]
        if unsafe_flags:
            candidates.append(
                DeepAnalysisVisualizationCandidate(
                    candidate_id=f"chart-eligibility:{index}",
                    status=VisualizationStatus.BLOCKED,
                    visualization_family=VisualizationFamily.TABLE_ONLY,
                    suggested_title="Chart Eligibility Signal Blocked",
                    scope_classification=_first_text(
                        chart.get("scope_classification"),
                        "unknown_or_mixed",
                    ),
                    evidence_shape=EvidenceShape.IDENTITY_ROWS,
                    section_id=_first_text(chart.get("section_id"), "chart_eligibility"),
                    row_ids=(),
                    required_data_shape="chart eligibility plus validated evidence rows",
                    observed_data_shape="chart eligibility signal without evidence rows",
                    minimum_requirements=(
                        "browser_computation_allowed=false",
                        "synthetic_data_allowed=false",
                        "empty_chart_allowed=false",
                    ),
                    blocked_reason="unsafe_chart_eligibility_flags:" + ",".join(unsafe_flags),
                    provenance_summary="chart_eligibility",
                    freshness_summary="chart_eligibility",
                    recommended_renderer="none",
                    label_guidance="Chart eligibility is an input signal only and does not create evidence.",
                )
            )
    return candidates


def _sections_by_id(contract: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    sections: dict[str, Mapping[str, Any]] = {}
    for section in contract.get("evidence_sections") or []:
        if not isinstance(section, Mapping):
            continue
        section_id = _first_text(section.get("section_id"))
        if section_id:
            sections[section_id] = section
    return sections


def _rows_by_section(contract: Mapping[str, Any]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in contract.get("evidence_rows") or []:
        if not isinstance(row, Mapping):
            continue
        section_id = _first_text(row.get("section_id"))
        if not section_id:
            continue
        grouped.setdefault(section_id, []).append(row)
    return grouped


def _row_is_shape_eligible(row: Mapping[str, Any]) -> bool:
    if _freshness(row) in {"stale", "cache_only", "cached_continuity_only"}:
        return False
    if row.get("llm_generated") is True:
        return False
    if "llm" in _normalized_text(row.get("generated_by")):
        return False
    for flag in (
        "synthetic",
        "synthetic_row",
        "demo",
        "demo_row",
        "placeholder",
        "placeholder_row",
        "hard_coded",
        "hardcoded",
        "example",
    ):
        if row.get(flag) is True:
            return False
    if _scope(row) == ScopeClassification.CURRENT_SCOPE.value and not isinstance(
        row.get("supports_existing_truth_ref"),
        Mapping,
    ):
        return False
    return True


def _has_aligned_multi_series(rows: list[Mapping[str, Any]]) -> bool:
    series_keys: set[str] = set()
    time_points = 0
    for row in rows:
        value = row.get("deterministic_value")
        if isinstance(value, Mapping) and isinstance(value.get("series"), Mapping):
            series_keys.update(str(key) for key in value.get("series", {}).keys())
            if _has_time_index(row) or _has_text(value.get("timestamp")):
                time_points += 1
            continue
        series = _first_text(row.get("series_id"), row.get("series_key"), row.get("target"))
        if series:
            series_keys.add(series)
        if _has_time_index(row):
            time_points += 1
    return len(series_keys) >= 2 and time_points >= MIN_TIME_SERIES_POINTS


def _time_indexed_point_count(rows: list[Mapping[str, Any]]) -> int:
    count = 0
    for row in rows:
        value = row.get("deterministic_value")
        if isinstance(value, Mapping):
            points = value.get("points") or value.get("time_series")
            if isinstance(points, list):
                return len([
                    point
                    for point in points
                    if isinstance(point, Mapping)
                    and _has_text(point.get("timestamp") or point.get("time_index"))
                    and _has_numeric_value(point)
                ])
        if _has_time_index(row) and _has_numeric_value(row):
            count += 1
    return count


def _numeric_sample_count(rows: list[Mapping[str, Any]]) -> int:
    total = 0
    saw_summary_only = False
    for row in rows:
        value = row.get("deterministic_value")
        samples = _numeric_samples(value)
        if not samples and isinstance(row.get("samples"), list):
            samples = _numeric_samples(row.get("samples"))
        if samples:
            total += len(samples)
            continue
        if isinstance(value, Mapping) and any(
            key in value for key in ("min", "max", "sample_count", "p50", "p95")
        ):
            saw_summary_only = True
    return total if total else (1 if saw_summary_only else 0)


def _numeric_samples(value: Any) -> list[float]:
    if isinstance(value, Mapping):
        for key in ("samples", "numeric_samples", "sample_values", "values"):
            samples = _numeric_samples(value.get(key))
            if samples:
                return samples
        return []
    if not isinstance(value, (list, tuple)):
        return []
    samples: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, Real):
            continue
        samples.append(float(item))
    return samples


def _has_scalar_threshold(rows: list[Mapping[str, Any]]) -> bool:
    for row in rows:
        value = row.get("deterministic_value")
        if _is_number(value) and (
            row.get("comparator_or_threshold_ref")
            or row.get("threshold_ref")
            or row.get("threshold")
        ):
            return True
        if isinstance(value, Mapping) and _is_number(
            value.get("value") or value.get("current_value")
        ) and (
            "threshold" in value
            or "threshold_ref" in value
            or "comparator" in value
        ):
            return True
    return False


def _has_ranked_rows(rows: list[Mapping[str, Any]]) -> bool:
    for row in rows:
        if any(key in row for key in ("rank", "position", "ordinal", "sort_order")):
            return True
        if _normalized_text(row.get("evidence_type")) in {
            "top_sql_detail",
            "wait_event_detail",
            "ranked_contribution",
        }:
            return True
    return False


def _has_score_vector(rows: list[Mapping[str, Any]]) -> bool:
    return any(
        _normalized_text(row.get("evidence_type"))
        in {"domain_score_detail", "score_vector", "metric_breakdown"}
        and _is_number(row.get("deterministic_value"))
        for row in rows
    )


def _has_categorical_contribution(
    rows: list[Mapping[str, Any]],
    evidence_type: str,
) -> bool:
    if evidence_type in {
        "diagnostic_driver",
        "metric_breakdown",
        "db_time_breakdown",
        "domain_score_detail",
        "scalar_metric_detail",
        "wait_event_detail",
    }:
        return any(_is_number(row.get("deterministic_value")) for row in rows)
    return any(
        _is_number(row.get("deterministic_value"))
        and _has_text(row.get("metric_name") or row.get("evidence_name"))
        for row in rows
    )


def _has_time_index(row: Mapping[str, Any]) -> bool:
    if _has_text(row.get("timestamp") or row.get("time_index") or row.get("snapshot")):
        return True
    value = row.get("deterministic_value")
    return isinstance(value, Mapping) and _has_text(
        value.get("timestamp") or value.get("time_index") or value.get("snapshot")
    )


def _has_numeric_value(row: Mapping[str, Any]) -> bool:
    if any(_is_number(row.get(key)) for key in ("value", "current_value", "metric_value", "y")):
        return True
    value = row.get("deterministic_value")
    if _is_number(value):
        return True
    if isinstance(value, Mapping):
        return any(
            _is_number(value.get(key))
            for key in ("value", "current_value", "metric_value", "y")
        )
    return False


def _is_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, Real)


def _validation_ready(validation: Any) -> bool:
    if isinstance(validation, Mapping):
        return bool(validation.get("is_ready"))
    return bool(getattr(validation, "is_ready", False))


def _validation_state(validation: Any) -> str:
    value = validation.get("state") if isinstance(validation, Mapping) else getattr(validation, "state", "")
    return str(getattr(value, "value", value) or "")


def _validation_ids(validation: Any, field: str) -> set[str]:
    if isinstance(validation, Mapping):
        values = validation.get(field) or ()
    else:
        values = getattr(validation, field, ()) or ()
    return {str(value) for value in values if _has_text(value)}


def _section_scope(section: Mapping[str, Any], rows: list[Mapping[str, Any]]) -> str:
    return _first_text(
        section.get("scope_classification"),
        *[row.get("scope_classification") for row in rows],
    )


def _section_id(section: Mapping[str, Any], rows: list[Mapping[str, Any]]) -> str:
    return _first_text(section.get("section_id"), *[row.get("section_id") for row in rows], "unknown-section")


def _row_id(row: Mapping[str, Any]) -> str:
    return _first_text(row.get("row_id"), row.get("id"))


def _scope(row: Mapping[str, Any]) -> str:
    return _first_text(row.get("scope_classification"))


def _freshness(row: Mapping[str, Any]) -> str:
    return _normalized_text(row.get("freshness_status") or row.get("freshness"))


def _suggested_title(
    section: Mapping[str, Any],
    family: VisualizationFamily,
    *,
    supporting: bool,
) -> str:
    title = _first_text(section.get("title"), family.value.replace("_", " ").title())
    if family == VisualizationFamily.DISTRIBUTION_EVIDENCE:
        title = f"{title} Distribution Evidence"
    elif family == VisualizationFamily.TABLE_ONLY:
        title = f"{title} Table Detail"
    if supporting and "Supporting" not in title:
        title = f"{title} Supporting Context"
    return title


def _label_guidance(family: VisualizationFamily, *, supporting: bool) -> str:
    prefix = "Label as supporting context. " if supporting else ""
    if family == VisualizationFamily.DISTRIBUTION_EVIDENCE:
        return prefix + "Use Distribution Evidence unless density semantics are explicitly validated; do not claim true violin from samples alone."
    if family == VisualizationFamily.FLEET_POPULATION:
        return prefix + "Requires a future fleet/population evidence contract."
    if family == VisualizationFamily.TABLE_ONLY:
        return prefix + "Render as table/text only; do not create a chart shell."
    return prefix + "Render only after a future renderer consumes this selected candidate."


def _provenance_summary(
    section: Mapping[str, Any],
    rows: list[Mapping[str, Any]],
) -> str:
    provenance = section.get("provenance")
    if isinstance(provenance, Mapping):
        summary = _first_text(
            provenance.get("source_contract_ref"),
            provenance.get("source_path"),
            provenance.get("deterministic_engine_version"),
        )
        if summary:
            return summary
    for row in rows:
        row_provenance = row.get("provenance")
        if isinstance(row_provenance, Mapping):
            summary = _first_text(
                row_provenance.get("source_contract_ref"),
                row_provenance.get("source_path"),
                row_provenance.get("deterministic_engine_version"),
            )
            if summary:
                return summary
    return "provenance_required"


def _freshness_summary(
    section: Mapping[str, Any],
    rows: list[Mapping[str, Any]],
) -> str:
    summary = _first_text(section.get("freshness_status"))
    if summary:
        return summary
    for row in rows:
        summary = _first_text(row.get("freshness_status"))
        if summary:
            return summary
    return "freshness_required"


def _first_text(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _has_text(value: Any) -> bool:
    return _first_text(value) != ""


def _normalized_text(value: Any) -> str:
    return _first_text(value).lower().replace("-", "_").replace(" ", "_")


def _slug(value: Any) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", _first_text(value).lower()).strip("-")
    return slug or "value"
