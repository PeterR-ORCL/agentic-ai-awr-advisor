"""Screen 4 Deep Analysis deterministic contract validation helpers.

This module validates plain mapping payloads only. It does not render HTML,
draw charts, call services, read files, query databases, invoke LLMs, run
parsers, execute comparisons, or mutate runtime state.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any


CONTRACT_TYPE = "screen4_deep_analysis_contract"
SUPPORTED_CONTRACT_VERSION = "1.0"
SUPPORTED_CONTRACT_VERSIONS = {
    SUPPORTED_CONTRACT_VERSION,
    "7cy.screen4.deep_analysis.v1",
}


class ScopeClassification(str, Enum):
    CURRENT_SCOPE = "current_scope"
    HISTORICAL_SUPPORTING_CONTEXT = "historical_supporting_context"
    COMPARATIVE_OUTPUT = "comparative_output"
    PREPARED_ONLY = "prepared_only"
    CACHE_ONLY = "cache_only"
    FLEET_POPULATION = "fleet_population"
    LLM_EXPLANATION_ONLY = "llm_explanation_only"
    UNKNOWN_OR_MIXED = "unknown_or_mixed"


class DeepAnalysisState(str, Enum):
    UNAVAILABLE = "deep_analysis_unavailable"
    OUTPUT_REQUIRED = "deep_analysis_output_required"
    CURRENT_SCOPE = "deep_analysis_current_scope"
    HISTORICAL_SUPPORTING_CONTEXT = "deep_analysis_historical_supporting_context"
    EVIDENCE_AVAILABLE = "deep_analysis_evidence_available"
    READY = "deep_analysis_ready"


class ValidationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"


@dataclass(frozen=True)
class DeepAnalysisValidationMessage:
    code: str
    message: str
    severity: str = "error"
    field: str | None = None

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("code is required.")
        if not self.message:
            raise ValueError("message is required.")
        if self.severity not in {"error", "warning", "info"}:
            raise ValueError("severity must be error, warning, or info.")

    def to_dict(self) -> dict[str, str]:
        payload = {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }
        if self.field:
            payload["field"] = self.field
        return payload


@dataclass(frozen=True)
class DeepAnalysisValidationResult:
    status: ValidationStatus
    state: DeepAnalysisState
    is_ready: bool
    messages: tuple[DeepAnalysisValidationMessage, ...]
    blocked_reasons: tuple[str, ...]
    allowed_section_ids: tuple[str, ...] = ()
    supporting_section_ids: tuple[str, ...] = ()
    omitted_section_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "state": self.state.value,
            "is_ready": self.is_ready,
            "messages": [message.to_dict() for message in self.messages],
            "blocked_reasons": list(self.blocked_reasons),
            "allowed_section_ids": list(self.allowed_section_ids),
            "supporting_section_ids": list(self.supporting_section_ids),
            "omitted_section_ids": list(self.omitted_section_ids),
        }


MUTATION_BOUNDARY_FLAGS = (
    "mutates_score",
    "mutates_primary_domain",
    "mutates_severity",
    "mutates_confidence",
    "mutates_posture",
    "mutates_recommendation",
    "mutates_thresholds",
    "mutates_runtime_state",
    "mutates_learning_state",
    "mutates_materialization_state",
    "mutates_comparison_output",
)

DETERMINISTIC_GENERATORS = {
    "deterministic_backend",
    "deterministic_engine",
    "backend_deterministic_engine",
    "governed_backend_deterministic_engine",
}
CURRENT_SOURCE_SCOPES = {
    "current_selected_diagnostic_scope",
    "current_scope",
    "selected_diagnostic_scope",
    "current_selected_scope",
}
BLOCKED_PRIMARY_SCOPES = {
    ScopeClassification.COMPARATIVE_OUTPUT,
    ScopeClassification.PREPARED_ONLY,
    ScopeClassification.CACHE_ONLY,
    ScopeClassification.FLEET_POPULATION,
    ScopeClassification.LLM_EXPLANATION_ONLY,
    ScopeClassification.UNKNOWN_OR_MIXED,
}
BLOCKED_EVIDENCE_SCOPES = {
    ScopeClassification.PREPARED_ONLY,
    ScopeClassification.CACHE_ONLY,
    ScopeClassification.FLEET_POPULATION,
    ScopeClassification.LLM_EXPLANATION_ONLY,
    ScopeClassification.UNKNOWN_OR_MIXED,
}
BLOCKED_SECTION_RENDERING_VALUES = {
    "blocked_state",
    "blocked",
    "limitation",
    "missing_evidence",
}
LIMITATION_EVIDENCE_TYPES = {"limitation", "missing_evidence"}
CHART_STATUSES = {"eligible", "blocked", "omitted", "not_requested", "not_supported"}
STALE_FRESHNESS_STATUSES = {"stale", "cache_only", "cached_continuity_only"}
PLACEHOLDER_FLAGS = (
    "synthetic",
    "synthetic_row",
    "demo",
    "demo_row",
    "placeholder",
    "placeholder_row",
    "hard_coded",
    "hardcoded",
    "example",
)


def validate_deep_analysis_contract(contract: Any) -> DeepAnalysisValidationResult:
    """Validate a Screen 4 Deep Analysis contract mapping."""

    messages: list[DeepAnalysisValidationMessage] = []
    allowed_sections: list[str] = []
    supporting_sections: list[str] = []
    omitted_sections: list[str] = []

    if not isinstance(contract, Mapping):
        messages.append(_message("contract_not_mapping", "Contract must be a mapping."))
        return _result(messages, DeepAnalysisState.UNAVAILABLE)
    if not contract:
        messages.append(_message("contract_missing", "Contract is required."))
        return _result(messages, DeepAnalysisState.UNAVAILABLE)

    _validate_top_level(contract, messages)
    section_summary = _validate_sections(contract, messages)
    row_summary = _validate_rows(contract, messages)
    _validate_chart_eligibility(contract, messages)

    allowed_sections.extend(section_summary["allowed"])
    supporting_sections.extend(section_summary["supporting"])
    omitted_sections.extend(section_summary["omitted"])

    state = _determine_state_from_summary(
        contract,
        messages,
        current_rows=row_summary["current_rows"],
        historical_rows=row_summary["historical_rows"],
        current_sections=section_summary["current_sections"],
        historical_sections=section_summary["historical_sections"],
    )
    is_ready = state == DeepAnalysisState.READY and not _has_errors(messages)
    status = ValidationStatus.VALID if is_ready else ValidationStatus.INVALID
    return DeepAnalysisValidationResult(
        status=status,
        state=state,
        is_ready=is_ready,
        messages=tuple(messages),
        blocked_reasons=tuple(message.code for message in messages if message.severity == "error"),
        allowed_section_ids=tuple(allowed_sections),
        supporting_section_ids=tuple(supporting_sections),
        omitted_section_ids=tuple(omitted_sections),
    )


def determine_deep_analysis_state(contract: Any) -> DeepAnalysisState:
    """Return the conservative Screen 4 Deep Analysis state for a payload."""

    return validate_deep_analysis_contract(contract).state


def _validate_top_level(
    contract: Mapping[str, Any],
    messages: list[DeepAnalysisValidationMessage],
) -> None:
    if contract.get("contract_type") != CONTRACT_TYPE:
        messages.append(_message("contract_type_invalid", "Deep Analysis contract_type is invalid.", "contract_type"))

    version = str(contract.get("contract_version") or "").strip()
    if version not in SUPPORTED_CONTRACT_VERSIONS:
        messages.append(_message("contract_version_unsupported", "Deep Analysis contract_version is unsupported.", "contract_version"))

    generated_by = _normalized_text(contract.get("generated_by"))
    if not generated_by:
        messages.append(_message("generated_by_missing", "generated_by is required.", "generated_by"))
    elif "llm" in generated_by:
        messages.append(_message("generated_by_llm_blocked", "LLM cannot generate Deep Analysis evidence.", "generated_by"))
    elif "browser" in generated_by or "ui" == generated_by:
        messages.append(_message("generated_by_browser_blocked", "Browser or UI cannot generate Deep Analysis evidence.", "generated_by"))
    elif generated_by not in DETERMINISTIC_GENERATORS:
        messages.append(_message("generated_by_not_deterministic_backend", "generated_by must be deterministic/backend.", "generated_by"))

    source_scope = _normalized_text(contract.get("source_scope"))
    if source_scope not in CURRENT_SOURCE_SCOPES:
        messages.append(_message("source_scope_not_current_selected_scope", "source_scope must identify current selected diagnostic scope.", "source_scope"))

    if not _has_selected_identifier(contract):
        messages.append(_message("selected_identifier_missing", "A selected run, source, or snapshot identifier is required."))

    current_ref = contract.get("current_diagnostic_output_ref")
    if not isinstance(current_ref, Mapping) or not current_ref:
        messages.append(_message("current_diagnostic_output_ref_missing", "current_diagnostic_output_ref is required.", "current_diagnostic_output_ref"))

    _validate_immutable_truth_refs(contract.get("immutable_truth_refs"), messages)
    _validate_freshness(contract.get("freshness"), messages, "freshness")

    provenance = contract.get("provenance")
    if not isinstance(provenance, Mapping) or not provenance:
        messages.append(_message("provenance_missing", "provenance is required.", "provenance"))

    _validate_mutation_boundaries(contract.get("mutation_boundaries"), messages)

    if "metric_deltas" in contract or "domain_deltas" in contract:
        messages.append(_message("comparative_delta_fields_not_deep_analysis_evidence", "7CX metric/domain delta fields cannot create Deep Analysis evidence."))
    if "allowed_visualizations" in contract:
        messages.append(_message("comparative_allowed_visualizations_not_evidence", "7CX allowed_visualizations cannot create Deep Analysis evidence."))
    if "visual_eligibility" in contract:
        messages.append(_message("comparative_visual_eligibility_not_evidence", "7CX visual eligibility cannot create Deep Analysis evidence."))


def _validate_immutable_truth_refs(
    refs: Any,
    messages: list[DeepAnalysisValidationMessage],
) -> None:
    if not isinstance(refs, Mapping) or not refs:
        messages.append(_message("immutable_truth_refs_missing", "immutable_truth_refs is required.", "immutable_truth_refs"))
        return
    for key, value in refs.items():
        if isinstance(value, Mapping) and value.get("read_only") is not True:
            messages.append(_message("immutable_truth_ref_not_read_only", f"{key} must be read-only.", f"immutable_truth_refs.{key}"))


def _validate_freshness(
    freshness: Any,
    messages: list[DeepAnalysisValidationMessage],
    field: str,
) -> None:
    if not isinstance(freshness, Mapping) or not freshness:
        messages.append(_message("freshness_missing", "freshness is required.", field))
        return
    status = _freshness_status(freshness)
    if status in STALE_FRESHNESS_STATUSES:
        messages.append(_message("freshness_stale", "freshness must not be stale or cache-only.", field))


def _validate_mutation_boundaries(
    mutation_boundaries: Any,
    messages: list[DeepAnalysisValidationMessage],
) -> None:
    if not isinstance(mutation_boundaries, Mapping) or not mutation_boundaries:
        messages.append(_message("mutation_boundaries_missing", "mutation_boundaries is required.", "mutation_boundaries"))
        return
    for flag in MUTATION_BOUNDARY_FLAGS:
        if mutation_boundaries.get(flag) is True:
            messages.append(_message("mutation_boundary_true", f"{flag} must be false.", f"mutation_boundaries.{flag}"))


def _validate_sections(
    contract: Mapping[str, Any],
    messages: list[DeepAnalysisValidationMessage],
) -> dict[str, list[str] | int]:
    sections = contract.get("evidence_sections")
    summary: dict[str, list[str] | int] = {
        "allowed": [],
        "supporting": [],
        "omitted": [],
        "current_sections": 0,
        "historical_sections": 0,
    }
    if not isinstance(sections, list) or not sections:
        messages.append(_message("evidence_sections_missing", "evidence_sections are required.", "evidence_sections"))
        return summary

    for index, section in enumerate(sections):
        field = f"evidence_sections[{index}]"
        if not isinstance(section, Mapping):
            messages.append(_message("section_not_mapping", "Evidence section must be a mapping.", field))
            continue
        section_id = _text(section.get("section_id"))
        if not section_id:
            messages.append(_message("section_id_missing", "section_id is required.", f"{field}.section_id"))
        if not _text(section.get("title")):
            messages.append(_message("section_title_missing", "section title is required.", f"{field}.title"))
        if not _text(section.get("evidence_type")):
            messages.append(_message("section_evidence_type_missing", "section evidence_type is required.", f"{field}.evidence_type"))
        if not isinstance(section.get("provenance"), Mapping) or not section.get("provenance"):
            messages.append(_message("section_provenance_missing", "section provenance is required.", f"{field}.provenance"))
        if section.get("llm_generated") is True or _normalized_text(section.get("generated_by")) in {"llm", "llm_explanation", "browser_llm"}:
            messages.append(_message("section_llm_generated", "LLM-generated sections are blocked.", field))
        if _freshness_value(section.get("freshness_status")) in STALE_FRESHNESS_STATUSES:
            messages.append(_message("section_freshness_stale", "section freshness_status must not be stale.", f"{field}.freshness_status"))
        if "freshness_status" not in section:
            messages.append(_message("section_freshness_missing", "section freshness_status is required.", f"{field}.freshness_status"))
        if "allowed_rendering" not in section:
            messages.append(_message("section_allowed_rendering_missing", "section allowed_rendering is required.", f"{field}.allowed_rendering"))

        classification = _scope(section.get("scope_classification"))
        if classification is None:
            messages.append(_message("section_scope_classification_missing", "section scope_classification is required.", f"{field}.scope_classification"))
            continue
        if classification == ScopeClassification.CURRENT_SCOPE:
            summary["current_sections"] = int(summary["current_sections"]) + 1
            if section_id:
                summary["allowed"].append(section_id)
        elif classification == ScopeClassification.HISTORICAL_SUPPORTING_CONTEXT:
            summary["historical_sections"] = int(summary["historical_sections"]) + 1
            if section_id:
                summary["supporting"].append(section_id)
        else:
            messages.append(_message("section_scope_blocked", f"{classification.value} cannot render as Deep Analysis evidence.", f"{field}.scope_classification"))
            if section_id:
                summary["omitted"].append(section_id)

        evidence_type = _normalized_text(section.get("evidence_type"))
        allowed_rendering = _normalized_text(section.get("allowed_rendering"))
        rows_present = section.get("rows_present")
        if rows_present is False and evidence_type not in LIMITATION_EVIDENCE_TYPES and allowed_rendering not in BLOCKED_SECTION_RENDERING_VALUES:
            messages.append(_message("section_empty_without_blocked_state", "empty normal sections cannot render.", field))
            if section_id and section_id not in summary["omitted"]:
                summary["omitted"].append(section_id)

    return summary


def _validate_rows(
    contract: Mapping[str, Any],
    messages: list[DeepAnalysisValidationMessage],
) -> dict[str, int]:
    rows = contract.get("evidence_rows")
    summary = {"current_rows": 0, "historical_rows": 0}
    if not isinstance(rows, list):
        messages.append(_message("evidence_rows_missing", "evidence_rows are required.", "evidence_rows"))
        return summary

    for index, row in enumerate(rows):
        field = f"evidence_rows[{index}]"
        if not isinstance(row, Mapping):
            messages.append(_message("row_not_mapping", "Evidence row must be a mapping.", field))
            continue

        for key in ("row_id", "section_id", "evidence_type", "source_path", "render_as"):
            if not _text(row.get(key)):
                messages.append(_message(f"{key}_missing", f"{key} is required.", f"{field}.{key}"))
        if not (_text(row.get("evidence_name")) or _text(row.get("metric_name"))):
            messages.append(_message("row_evidence_name_missing", "evidence_name or metric_name is required.", field))
        if not isinstance(row.get("provenance"), Mapping) or not row.get("provenance"):
            messages.append(_message("row_provenance_missing", "row provenance is required.", f"{field}.provenance"))
        if "freshness_status" not in row:
            messages.append(_message("row_freshness_missing", "row freshness_status is required.", f"{field}.freshness_status"))
        elif _freshness_value(row.get("freshness_status")) in STALE_FRESHNESS_STATUSES:
            messages.append(_message("row_freshness_stale", "row freshness_status must not be stale.", f"{field}.freshness_status"))

        evidence_type = _normalized_text(row.get("evidence_type"))
        if evidence_type not in LIMITATION_EVIDENCE_TYPES and "deterministic_value" not in row:
            messages.append(_message("row_deterministic_value_missing", "deterministic_value is required.", f"{field}.deterministic_value"))

        for flag in PLACEHOLDER_FLAGS:
            if row.get(flag) is True:
                messages.append(_message("row_placeholder_or_synthetic", "synthetic, demo, hard-coded, or placeholder rows are blocked.", f"{field}.{flag}"))
        if row.get("llm_generated") is True or _normalized_text(row.get("generated_by")) in {"llm", "llm_explanation", "browser_llm"}:
            messages.append(_message("row_llm_generated", "LLM-generated rows are blocked.", field))

        classification = _scope(row.get("scope_classification"))
        if classification is None:
            messages.append(_message("row_scope_classification_missing", "row scope_classification is required.", f"{field}.scope_classification"))
            continue

        if classification == ScopeClassification.CURRENT_SCOPE:
            summary["current_rows"] += 1
            if not _has_truth_ref(row.get("supports_existing_truth_ref")):
                messages.append(_message("row_truth_ref_missing", "current_scope row must support an existing truth ref.", f"{field}.supports_existing_truth_ref"))
        elif classification == ScopeClassification.HISTORICAL_SUPPORTING_CONTEXT:
            summary["historical_rows"] += 1
            if _is_primary_row(row):
                messages.append(_message("row_historical_primary_blocked", "historical rows may be supporting context only.", field))
        elif classification == ScopeClassification.COMPARATIVE_OUTPUT:
            messages.append(_message("row_comparative_output_blocked", "comparative_output rows cannot be primary Deep Analysis evidence.", f"{field}.scope_classification"))
        elif classification == ScopeClassification.FLEET_POPULATION:
            messages.append(_message("row_fleet_population_blocked", "fleet_population rows require a future fleet contract.", f"{field}.scope_classification"))
        elif classification in BLOCKED_EVIDENCE_SCOPES:
            messages.append(_message("row_scope_blocked", f"{classification.value} rows cannot be Deep Analysis evidence.", f"{field}.scope_classification"))

    return summary


def _validate_chart_eligibility(
    contract: Mapping[str, Any],
    messages: list[DeepAnalysisValidationMessage],
) -> None:
    charts = contract.get("chart_eligibility")
    if charts is None:
        return
    if not isinstance(charts, list):
        messages.append(_message("chart_eligibility_not_list", "chart_eligibility must be a list.", "chart_eligibility"))
        return
    for index, chart in enumerate(charts):
        field = f"chart_eligibility[{index}]"
        if not isinstance(chart, Mapping):
            messages.append(_message("chart_eligibility_item_not_mapping", "chart eligibility item must be a mapping.", field))
            continue
        status = _normalized_text(chart.get("eligibility_status"))
        if status and status not in CHART_STATUSES:
            messages.append(_message("chart_eligibility_status_invalid", "chart eligibility status is invalid.", f"{field}.eligibility_status"))
        if chart.get("browser_computation_allowed") is True:
            messages.append(_message("chart_browser_computation_allowed", "Deep Analysis chart eligibility cannot allow browser computation.", f"{field}.browser_computation_allowed"))
        if chart.get("synthetic_data_allowed") is True:
            messages.append(_message("chart_synthetic_data_allowed", "Deep Analysis chart eligibility cannot allow synthetic data.", f"{field}.synthetic_data_allowed"))
        if chart.get("empty_chart_allowed") is True:
            messages.append(_message("chart_empty_chart_allowed", "Deep Analysis chart eligibility cannot allow empty charts.", f"{field}.empty_chart_allowed"))
        if status == "eligible":
            source_paths = chart.get("source_paths")
            evidence_shape = chart.get("required_evidence_shape")
            if not source_paths or not evidence_shape:
                messages.append(_message("chart_eligible_missing_evidence_shape", "eligible chart requires source_paths and required_evidence_shape.", field))


def _determine_state_from_summary(
    contract: Mapping[str, Any],
    messages: list[DeepAnalysisValidationMessage],
    *,
    current_rows: int,
    historical_rows: int,
    current_sections: int,
    historical_sections: int,
) -> DeepAnalysisState:
    if not isinstance(contract, Mapping) or not contract:
        return DeepAnalysisState.UNAVAILABLE

    top_level_error_codes = {
        "contract_type_invalid",
        "contract_version_unsupported",
        "generated_by_missing",
        "generated_by_llm_blocked",
        "generated_by_browser_blocked",
        "generated_by_not_deterministic_backend",
        "source_scope_not_current_selected_scope",
        "selected_identifier_missing",
        "current_diagnostic_output_ref_missing",
        "immutable_truth_refs_missing",
        "freshness_missing",
        "freshness_stale",
        "provenance_missing",
        "mutation_boundaries_missing",
        "mutation_boundary_true",
    }
    error_codes = {message.code for message in messages if message.severity == "error"}
    if error_codes & top_level_error_codes:
        return DeepAnalysisState.OUTPUT_REQUIRED
    if current_rows == 0 and historical_rows > 0 and current_sections == 0:
        return DeepAnalysisState.HISTORICAL_SUPPORTING_CONTEXT
    if current_rows == 0:
        return DeepAnalysisState.CURRENT_SCOPE
    if _has_errors(messages):
        return DeepAnalysisState.EVIDENCE_AVAILABLE
    if current_rows > 0 and current_sections > 0:
        return DeepAnalysisState.READY
    if historical_sections > 0:
        return DeepAnalysisState.HISTORICAL_SUPPORTING_CONTEXT
    return DeepAnalysisState.CURRENT_SCOPE


def _result(
    messages: list[DeepAnalysisValidationMessage],
    state: DeepAnalysisState,
) -> DeepAnalysisValidationResult:
    return DeepAnalysisValidationResult(
        status=ValidationStatus.INVALID,
        state=state,
        is_ready=False,
        messages=tuple(messages),
        blocked_reasons=tuple(message.code for message in messages if message.severity == "error"),
    )


def _has_selected_identifier(contract: Mapping[str, Any]) -> bool:
    if _text(contract.get("selected_run_id")):
        return True
    for key in ("selected_snapshot_identifier", "selected_source_identifier"):
        value = contract.get(key)
        if isinstance(value, Mapping) and value:
            return True
        if _text(value):
            return True
    return False


def _is_primary_row(row: Mapping[str, Any]) -> bool:
    if row.get("primary_evidence") is True:
        return True
    return _normalized_text(row.get("evidence_role")) == "primary"


def _has_truth_ref(value: Any) -> bool:
    if isinstance(value, Mapping):
        return bool(value)
    return _text(value) != ""


def _scope(value: Any) -> ScopeClassification | None:
    normalized = _normalized_text(value)
    for classification in ScopeClassification:
        if classification.value == normalized:
            return classification
    return None


def _freshness_status(freshness: Mapping[str, Any]) -> str:
    return _freshness_value(
        freshness.get("freshness_status")
        or freshness.get("status")
        or freshness.get("cache_status")
    )


def _freshness_value(value: Any) -> str:
    return _normalized_text(value)


def _normalized_text(value: Any) -> str:
    return _text(value).lower().replace("-", "_").replace(" ", "_")


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _has_errors(messages: list[DeepAnalysisValidationMessage]) -> bool:
    return any(message.severity == "error" for message in messages)


def _message(
    code: str,
    message: str,
    field: str | None = None,
) -> DeepAnalysisValidationMessage:
    return DeepAnalysisValidationMessage(code=code, message=message, field=field)
