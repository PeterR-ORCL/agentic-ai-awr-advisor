"""Phase 7AA.2 read-only adaptive runtime context builder.

This module gathers already-existing Phase 7 records into a deterministic
context envelope for future adapters. It does not apply adaptive behavior,
mutate runtime scoring, alter parser output, change decisions, change
recommendations, call services, or write databases.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field, is_dataclass
import re
from typing import Any, Mapping, Sequence

from src.learning.adaptive_runtime_gate import (
    ADAPTIVE_RUNTIME_MODES,
    adaptive_runtime_config_to_dict,
    component_eligibility_to_dict,
    default_deterministic_runtime_config,
    gate_result_to_dict,
    validate_adaptive_runtime_config,
    validate_component_eligibility,
    validate_gate_result,
)


ADAPTIVE_RUNTIME_CONTEXT_FIELDS = (
    "context_id",
    "runtime_mode",
    "deterministic_runtime_authoritative",
    "fallback_to_deterministic",
    "phase4i_contract_preserved",
    "runtime_influence_applied",
    "runtime_mutation_performed",
    "adaptive_runtime_config",
    "gate_results",
    "scoring_context",
    "recommendation_context",
    "parser_context",
    "trend_context",
    "shadow_ml_context",
    "model_registry_context",
    "explainability_context",
    "materialization_context",
    "validation_context",
    "readiness_context",
    "denied_reasons",
    "warnings",
    "required_next_steps",
    "created_by",
    "notes",
)

ADAPTIVE_RUNTIME_SECTION_FIELDS = (
    "section_name",
    "available",
    "item_count",
    "eligible_count",
    "allowed_for_consideration_count",
    "runtime_active_count",
    "summaries",
    "warnings",
)

ADAPTIVE_PARSER_RUNTIME_SECTION_FIELDS = (
    "section_name",
    "available",
    "parser_evolution_count",
    "parser_backlog_count",
    "runtime_active_count",
    "phase4i_contract_required",
    "awr_regression_required",
    "scoring_regression_required",
    "summaries",
    "warnings",
)

_SECTION_COMPONENT_TYPES = {
    "scoring": "scoring",
    "recommendation": "recommendation",
    "parser": "parser",
    "trend": "trend_aware_scoring",
    "shadow_ml": "shadow_ml",
    "model_registry": "model_registry",
    "materialization": "materialization_artifact",
}

_DEFAULT_REQUIRED_NEXT_STEPS = (
    "Future adapters must re-evaluate the 7AA.1 runtime gate before use.",
    "Future scoring/recommendation/parser adapters must treat context as read-only.",
)


class AdaptiveRuntimeContextError(ValueError):
    """Raised when Phase 7AA.2 runtime context rules are violated."""


@dataclass(frozen=True)
class AdaptiveRuntimeSection:
    """Read-only normalized context section for adaptive materials."""

    section_name: str
    available: bool
    item_count: int
    eligible_count: int
    allowed_for_consideration_count: int
    runtime_active_count: int
    summaries: list[dict[str, object]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def review_count(self) -> int:
        """Return item_count for scoring/recommendation review sections."""

        return self.item_count

    @property
    def result_count(self) -> int:
        """Return item_count for trend-aware result sections."""

        return self.item_count

    @property
    def output_count(self) -> int:
        """Return item_count for shadow ML output sections."""

        return self.item_count

    @property
    def model_count(self) -> int:
        """Return the number of distinct model references in summaries."""

        return _distinct_summary_value_count(self.summaries, ("model_id", "model_name"))

    @property
    def registered_model_count(self) -> int:
        """Return item_count for model registry sections."""

        return self.item_count

    @property
    def shadow_eligible_count(self) -> int:
        """Return summaries marked shadow eligible."""

        return _count_true_summary_field(self.summaries, "shadow_eligible")

    @property
    def runtime_eligible_count(self) -> int:
        """Return summaries marked runtime eligible."""

        return _count_true_summary_field(self.summaries, "runtime_eligible")

    @property
    def artifact_count(self) -> int:
        """Return item_count for materialization sections."""

        return self.item_count

    @property
    def runtime_sensitive_count(self) -> int:
        """Return summaries marked runtime sensitive."""

        return _count_true_summary_field(self.summaries, "runtime_sensitive")

    @property
    def domains(self) -> list[str]:
        """Return deterministic domain names from section summaries."""

        domains = {
            str(summary["domain"]).strip()
            for summary in self.summaries
            if isinstance(summary.get("domain"), str) and str(summary["domain"]).strip()
        }
        return sorted(domains)

    def __post_init__(self) -> None:
        _require_non_empty_string(self.section_name, "section_name")
        _validate_bool(self.available, "available")
        for field_name in (
            "item_count",
            "eligible_count",
            "allowed_for_consideration_count",
            "runtime_active_count",
        ):
            _validate_nonnegative_int(getattr(self, field_name), field_name)
        _require_zero(self.runtime_active_count, "runtime_active_count")
        summaries = _normalize_summaries(self.summaries)
        warnings = _normalize_string_list(self.warnings, "warnings")
        if self.item_count != len(summaries):
            raise AdaptiveRuntimeContextError(
                "item_count must match the number of section summaries."
            )
        object.__setattr__(self, "section_name", self.section_name.strip())
        object.__setattr__(self, "available", bool(self.available))
        object.__setattr__(self, "item_count", int(self.item_count))
        object.__setattr__(self, "eligible_count", int(self.eligible_count))
        object.__setattr__(
            self,
            "allowed_for_consideration_count",
            int(self.allowed_for_consideration_count),
        )
        object.__setattr__(self, "runtime_active_count", 0)
        object.__setattr__(self, "summaries", summaries)
        object.__setattr__(self, "warnings", warnings)


@dataclass(frozen=True)
class AdaptiveParserRuntimeSection:
    """Read-only normalized parser context with parser-specific guardrails."""

    section_name: str
    available: bool
    parser_evolution_count: int
    parser_backlog_count: int
    runtime_active_count: int
    phase4i_contract_required: bool
    awr_regression_required: bool
    scoring_regression_required: bool
    summaries: list[dict[str, object]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_non_empty_string(self.section_name, "section_name")
        _validate_bool(self.available, "available")
        for field_name in (
            "parser_evolution_count",
            "parser_backlog_count",
            "runtime_active_count",
        ):
            _validate_nonnegative_int(getattr(self, field_name), field_name)
        _require_zero(self.runtime_active_count, "runtime_active_count")
        _require_true(self.phase4i_contract_required, "phase4i_contract_required")
        _require_true(self.awr_regression_required, "awr_regression_required")
        _require_true(self.scoring_regression_required, "scoring_regression_required")
        summaries = _normalize_summaries(self.summaries)
        warnings = _normalize_string_list(self.warnings, "warnings")
        if self.parser_evolution_count + self.parser_backlog_count != len(summaries):
            raise AdaptiveRuntimeContextError(
                "parser_evolution_count plus parser_backlog_count must match summaries."
            )
        object.__setattr__(self, "section_name", self.section_name.strip())
        object.__setattr__(self, "available", bool(self.available))
        object.__setattr__(
            self,
            "parser_evolution_count",
            int(self.parser_evolution_count),
        )
        object.__setattr__(self, "parser_backlog_count", int(self.parser_backlog_count))
        object.__setattr__(self, "runtime_active_count", 0)
        object.__setattr__(self, "phase4i_contract_required", True)
        object.__setattr__(self, "awr_regression_required", True)
        object.__setattr__(self, "scoring_regression_required", True)
        object.__setattr__(self, "summaries", summaries)
        object.__setattr__(self, "warnings", warnings)


@dataclass(frozen=True)
class AdaptiveRuntimeContext:
    """Read-only adaptive runtime context envelope for future adapters."""

    context_id: str
    runtime_mode: str
    deterministic_runtime_authoritative: bool
    fallback_to_deterministic: bool
    phase4i_contract_preserved: bool
    runtime_influence_applied: bool
    runtime_mutation_performed: bool
    adaptive_runtime_config: dict[str, object]
    gate_results: list[dict[str, object]]
    scoring_context: AdaptiveRuntimeSection
    recommendation_context: AdaptiveRuntimeSection
    parser_context: AdaptiveParserRuntimeSection
    trend_context: AdaptiveRuntimeSection
    shadow_ml_context: AdaptiveRuntimeSection
    model_registry_context: AdaptiveRuntimeSection
    explainability_context: AdaptiveRuntimeSection
    materialization_context: AdaptiveRuntimeSection
    validation_context: dict[str, object]
    readiness_context: dict[str, object]
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    created_by: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.context_id, "context_id")
        runtime_mode = _normalize_runtime_mode(self.runtime_mode)
        _require_true(
            self.deterministic_runtime_authoritative,
            "deterministic_runtime_authoritative",
        )
        _require_true(self.fallback_to_deterministic, "fallback_to_deterministic")
        _require_true(self.phase4i_contract_preserved, "phase4i_contract_preserved")
        _require_false(self.runtime_influence_applied, "runtime_influence_applied")
        _require_false(self.runtime_mutation_performed, "runtime_mutation_performed")
        config = _normalize_mapping(
            self.adaptive_runtime_config,
            "adaptive_runtime_config",
        )
        gate_results = _normalize_gate_result_dicts(self.gate_results)
        _validate_no_active_gate_results(gate_results)
        scoring_context = _section_from_any(self.scoring_context)
        recommendation_context = _section_from_any(self.recommendation_context)
        parser_context = _parser_section_from_any(self.parser_context)
        trend_context = _section_from_any(self.trend_context)
        shadow_ml_context = _section_from_any(self.shadow_ml_context)
        model_registry_context = _section_from_any(self.model_registry_context)
        explainability_context = _section_from_any(self.explainability_context)
        materialization_context = _section_from_any(self.materialization_context)
        sections = (
            scoring_context,
            recommendation_context,
            parser_context,
            trend_context,
            shadow_ml_context,
            model_registry_context,
            explainability_context,
            materialization_context,
        )
        for section in sections:
            _validate_section_runtime_inactive(section)
        validation_context = _normalize_mapping(
            self.validation_context,
            "validation_context",
        )
        readiness_context = _normalize_mapping(
            self.readiness_context,
            "readiness_context",
        )
        denied_reasons = _normalize_string_list(self.denied_reasons, "denied_reasons")
        warnings = _normalize_string_list(self.warnings, "warnings")
        required_next_steps = _normalize_string_list(
            self.required_next_steps,
            "required_next_steps",
        )
        _validate_optional_string(self.created_by, "created_by")
        _validate_optional_string(self.notes, "notes")

        object.__setattr__(self, "context_id", self.context_id.strip())
        object.__setattr__(self, "runtime_mode", runtime_mode)
        object.__setattr__(self, "deterministic_runtime_authoritative", True)
        object.__setattr__(self, "fallback_to_deterministic", True)
        object.__setattr__(self, "phase4i_contract_preserved", True)
        object.__setattr__(self, "runtime_influence_applied", False)
        object.__setattr__(self, "runtime_mutation_performed", False)
        object.__setattr__(self, "adaptive_runtime_config", config)
        object.__setattr__(self, "gate_results", gate_results)
        object.__setattr__(self, "scoring_context", scoring_context)
        object.__setattr__(self, "recommendation_context", recommendation_context)
        object.__setattr__(self, "parser_context", parser_context)
        object.__setattr__(self, "trend_context", trend_context)
        object.__setattr__(self, "shadow_ml_context", shadow_ml_context)
        object.__setattr__(self, "model_registry_context", model_registry_context)
        object.__setattr__(self, "explainability_context", explainability_context)
        object.__setattr__(self, "materialization_context", materialization_context)
        object.__setattr__(self, "validation_context", validation_context)
        object.__setattr__(self, "readiness_context", readiness_context)
        object.__setattr__(self, "denied_reasons", denied_reasons)
        object.__setattr__(self, "warnings", warnings)
        object.__setattr__(self, "required_next_steps", required_next_steps)
        object.__setattr__(
            self,
            "created_by",
            _normalize_optional_string(self.created_by),
        )
        object.__setattr__(self, "notes", _normalize_optional_string(self.notes))


def create_adaptive_runtime_context_id(
    runtime_mode: str,
    phase4i_reference: str | None = None,
) -> str:
    """Create a deterministic adaptive runtime context identifier."""

    mode = _normalize_runtime_mode(runtime_mode)
    _validate_optional_string(phase4i_reference, "phase4i_reference")
    reference = phase4i_reference if _has_text(phase4i_reference) else "no-phase4i-reference"
    return (
        f"ADAPTIVE-RUNTIME-CONTEXT-{_identifier_fragment(mode)}-"
        f"{_identifier_fragment(reference)}"
    )


def build_adaptive_runtime_context(
    *,
    report_metadata: Any = None,
    phase4i_output_summary: Any = None,
    adaptive_runtime_config: Any = None,
    component_eligibilities: Any = None,
    gate_results: Any = None,
    materialization_artifacts: Any = None,
    adaptive_scoring_reviews: Any = None,
    recommendation_rule_evolutions: Any = None,
    parser_mapping_evolutions: Any = None,
    trend_aware_scores: Any = None,
    shadow_ml_outputs: Any = None,
    ml_explanations: Any = None,
    model_registry_entries: Any = None,
    validation_references: Any = None,
    readiness_references: Any = None,
    created_by: str | None = None,
    notes: str | None = None,
) -> AdaptiveRuntimeContext:
    """Build a read-only adaptive runtime context from in-memory inputs."""

    config_dict = _normalize_config(adaptive_runtime_config)
    runtime_mode = _normalize_runtime_mode(config_dict.get("mode", "deterministic_only"))
    eligibility_dicts = _normalize_eligibility_dicts(component_eligibilities)
    gate_result_dicts = _normalize_gate_result_dicts(gate_results)
    phase4i_reference = _phase4i_reference(phase4i_output_summary, report_metadata)
    context_id = create_adaptive_runtime_context_id(runtime_mode, phase4i_reference)

    denied_reasons = _collect_gate_strings(gate_result_dicts, "denied_reasons")
    warnings = _collect_gate_strings(gate_result_dicts, "warnings")
    required_next_steps = list(_DEFAULT_REQUIRED_NEXT_STEPS)
    required_next_steps.extend(
        _collect_gate_strings(gate_result_dicts, "required_next_steps")
    )

    scoring_context = _build_runtime_section(
        section_name="scoring",
        items=adaptive_scoring_reviews,
        item_type="adaptive_scoring_review",
        component_type="scoring",
        eligibility_dicts=eligibility_dicts,
        gate_result_dicts=gate_result_dicts,
    )
    recommendation_context = _build_runtime_section(
        section_name="recommendation",
        items=recommendation_rule_evolutions,
        item_type="recommendation_rule_evolution",
        component_type="recommendation",
        eligibility_dicts=eligibility_dicts,
        gate_result_dicts=gate_result_dicts,
    )
    parser_context = _build_parser_section(parser_mapping_evolutions)
    trend_context = _build_runtime_section(
        section_name="trend",
        items=trend_aware_scores,
        item_type="trend_aware_score",
        component_type="trend_aware_scoring",
        eligibility_dicts=eligibility_dicts,
        gate_result_dicts=gate_result_dicts,
    )
    shadow_ml_context = _build_runtime_section(
        section_name="shadow_ml",
        items=shadow_ml_outputs,
        item_type="shadow_ml_output",
        component_type="shadow_ml",
        eligibility_dicts=eligibility_dicts,
        gate_result_dicts=gate_result_dicts,
    )
    model_registry_context = _build_runtime_section(
        section_name="model_registry",
        items=model_registry_entries,
        item_type="model_registry_entry",
        component_type="model_registry",
        eligibility_dicts=eligibility_dicts,
        gate_result_dicts=gate_result_dicts,
    )
    explainability_context = _build_runtime_section(
        section_name="explainability",
        items=ml_explanations,
        item_type="ml_explanation",
        component_type=None,
        eligibility_dicts=eligibility_dicts,
        gate_result_dicts=gate_result_dicts,
    )
    materialization_context = _build_runtime_section(
        section_name="materialization",
        items=materialization_artifacts,
        item_type="materialization_artifact",
        component_type="materialization_artifact",
        eligibility_dicts=eligibility_dicts,
        gate_result_dicts=gate_result_dicts,
    )

    for section in (
        scoring_context,
        recommendation_context,
        parser_context,
        trend_context,
        shadow_ml_context,
        model_registry_context,
        explainability_context,
        materialization_context,
    ):
        warnings.extend(getattr(section, "warnings"))

    validation_context = _reference_context("validation", validation_references)
    readiness_context = _reference_context("readiness", readiness_references)

    return AdaptiveRuntimeContext(
        context_id=context_id,
        runtime_mode=runtime_mode,
        deterministic_runtime_authoritative=True,
        fallback_to_deterministic=True,
        phase4i_contract_preserved=True,
        runtime_influence_applied=False,
        runtime_mutation_performed=False,
        adaptive_runtime_config=config_dict,
        gate_results=gate_result_dicts,
        scoring_context=scoring_context,
        recommendation_context=recommendation_context,
        parser_context=parser_context,
        trend_context=trend_context,
        shadow_ml_context=shadow_ml_context,
        model_registry_context=model_registry_context,
        explainability_context=explainability_context,
        materialization_context=materialization_context,
        validation_context=validation_context,
        readiness_context=readiness_context,
        denied_reasons=_unique_strings(denied_reasons),
        warnings=_unique_strings(warnings),
        required_next_steps=_unique_strings(required_next_steps),
        created_by=created_by,
        notes=notes,
    )


def validate_adaptive_runtime_context(
    context: AdaptiveRuntimeContext | Mapping[str, Any],
) -> AdaptiveRuntimeContext:
    """Validate and return an adaptive runtime context."""

    if isinstance(context, Mapping):
        return adaptive_runtime_context_from_dict(context)
    if not isinstance(context, AdaptiveRuntimeContext):
        raise AdaptiveRuntimeContextError("context must be AdaptiveRuntimeContext.")
    return AdaptiveRuntimeContext(**adaptive_runtime_context_to_dict(context))


def adaptive_runtime_context_to_dict(
    context: AdaptiveRuntimeContext,
) -> dict[str, Any]:
    """Serialize an adaptive runtime context to a deterministic dictionary."""

    if not isinstance(context, AdaptiveRuntimeContext):
        raise AdaptiveRuntimeContextError("context must be AdaptiveRuntimeContext.")
    return {
        "context_id": context.context_id,
        "runtime_mode": context.runtime_mode,
        "deterministic_runtime_authoritative": (
            context.deterministic_runtime_authoritative
        ),
        "fallback_to_deterministic": context.fallback_to_deterministic,
        "phase4i_contract_preserved": context.phase4i_contract_preserved,
        "runtime_influence_applied": context.runtime_influence_applied,
        "runtime_mutation_performed": context.runtime_mutation_performed,
        "adaptive_runtime_config": deepcopy(context.adaptive_runtime_config),
        "gate_results": deepcopy(context.gate_results),
        "scoring_context": adaptive_runtime_section_to_dict(context.scoring_context),
        "recommendation_context": adaptive_runtime_section_to_dict(
            context.recommendation_context
        ),
        "parser_context": adaptive_parser_runtime_section_to_dict(
            context.parser_context
        ),
        "trend_context": adaptive_runtime_section_to_dict(context.trend_context),
        "shadow_ml_context": adaptive_runtime_section_to_dict(
            context.shadow_ml_context
        ),
        "model_registry_context": adaptive_runtime_section_to_dict(
            context.model_registry_context
        ),
        "explainability_context": adaptive_runtime_section_to_dict(
            context.explainability_context
        ),
        "materialization_context": adaptive_runtime_section_to_dict(
            context.materialization_context
        ),
        "validation_context": deepcopy(context.validation_context),
        "readiness_context": deepcopy(context.readiness_context),
        "denied_reasons": deepcopy(context.denied_reasons),
        "warnings": deepcopy(context.warnings),
        "required_next_steps": deepcopy(context.required_next_steps),
        "created_by": context.created_by,
        "notes": context.notes,
    }


def adaptive_runtime_context_from_dict(
    data: Mapping[str, Any],
) -> AdaptiveRuntimeContext:
    """Reconstruct and validate an adaptive runtime context from dictionary data."""

    if not isinstance(data, Mapping):
        raise AdaptiveRuntimeContextError("adaptive runtime context data must be a mapping.")
    values = _values_from_mapping(
        data,
        ADAPTIVE_RUNTIME_CONTEXT_FIELDS,
        optional_defaults={
            "deterministic_runtime_authoritative": True,
            "fallback_to_deterministic": True,
            "phase4i_contract_preserved": True,
            "runtime_influence_applied": False,
            "runtime_mutation_performed": False,
            "adaptive_runtime_config": adaptive_runtime_config_to_dict(
                default_deterministic_runtime_config()
            ),
            "gate_results": [],
            "scoring_context": _empty_section("scoring"),
            "recommendation_context": _empty_section("recommendation"),
            "parser_context": _empty_parser_section(),
            "trend_context": _empty_section("trend"),
            "shadow_ml_context": _empty_section("shadow_ml"),
            "model_registry_context": _empty_section("model_registry"),
            "explainability_context": _empty_section("explainability"),
            "materialization_context": _empty_section("materialization"),
            "validation_context": _reference_context("validation", None),
            "readiness_context": _reference_context("readiness", None),
            "denied_reasons": [],
            "warnings": [],
            "required_next_steps": list(_DEFAULT_REQUIRED_NEXT_STEPS),
            "created_by": None,
            "notes": None,
        },
    )
    values["scoring_context"] = _section_from_any(values["scoring_context"])
    values["recommendation_context"] = _section_from_any(
        values["recommendation_context"]
    )
    values["parser_context"] = _parser_section_from_any(values["parser_context"])
    values["trend_context"] = _section_from_any(values["trend_context"])
    values["shadow_ml_context"] = _section_from_any(values["shadow_ml_context"])
    values["model_registry_context"] = _section_from_any(values["model_registry_context"])
    values["explainability_context"] = _section_from_any(values["explainability_context"])
    values["materialization_context"] = _section_from_any(
        values["materialization_context"]
    )
    return AdaptiveRuntimeContext(**values)


def adaptive_runtime_section_to_dict(
    section: AdaptiveRuntimeSection,
) -> dict[str, Any]:
    """Serialize an adaptive runtime section to a deterministic dictionary."""

    if not isinstance(section, AdaptiveRuntimeSection):
        raise AdaptiveRuntimeContextError("section must be AdaptiveRuntimeSection.")
    return {
        "section_name": section.section_name,
        "available": section.available,
        "item_count": section.item_count,
        "eligible_count": section.eligible_count,
        "allowed_for_consideration_count": (
            section.allowed_for_consideration_count
        ),
        "runtime_active_count": section.runtime_active_count,
        "summaries": deepcopy(section.summaries),
        "warnings": deepcopy(section.warnings),
    }


def adaptive_runtime_section_from_dict(
    data: Mapping[str, Any],
) -> AdaptiveRuntimeSection:
    """Reconstruct and validate an adaptive runtime section from dictionary data."""

    if not isinstance(data, Mapping):
        raise AdaptiveRuntimeContextError("adaptive runtime section data must be a mapping.")
    values = _values_from_mapping(
        data,
        ADAPTIVE_RUNTIME_SECTION_FIELDS,
        optional_defaults={
            "available": False,
            "item_count": 0,
            "eligible_count": 0,
            "allowed_for_consideration_count": 0,
            "runtime_active_count": 0,
            "summaries": [],
            "warnings": [],
        },
    )
    return AdaptiveRuntimeSection(**values)


def adaptive_parser_runtime_section_to_dict(
    section: AdaptiveParserRuntimeSection,
) -> dict[str, Any]:
    """Serialize a parser runtime section to a deterministic dictionary."""

    if not isinstance(section, AdaptiveParserRuntimeSection):
        raise AdaptiveRuntimeContextError(
            "section must be AdaptiveParserRuntimeSection."
        )
    return {
        "section_name": section.section_name,
        "available": section.available,
        "parser_evolution_count": section.parser_evolution_count,
        "parser_backlog_count": section.parser_backlog_count,
        "runtime_active_count": section.runtime_active_count,
        "phase4i_contract_required": section.phase4i_contract_required,
        "awr_regression_required": section.awr_regression_required,
        "scoring_regression_required": section.scoring_regression_required,
        "summaries": deepcopy(section.summaries),
        "warnings": deepcopy(section.warnings),
    }


def adaptive_parser_runtime_section_from_dict(
    data: Mapping[str, Any],
) -> AdaptiveParserRuntimeSection:
    """Reconstruct and validate a parser runtime section from dictionary data."""

    if not isinstance(data, Mapping):
        raise AdaptiveRuntimeContextError("parser runtime section data must be a mapping.")
    values = _values_from_mapping(
        data,
        ADAPTIVE_PARSER_RUNTIME_SECTION_FIELDS,
        optional_defaults={
            "available": False,
            "parser_evolution_count": 0,
            "parser_backlog_count": 0,
            "runtime_active_count": 0,
            "phase4i_contract_required": True,
            "awr_regression_required": True,
            "scoring_regression_required": True,
            "summaries": [],
            "warnings": [],
        },
    )
    return AdaptiveParserRuntimeSection(**values)


def summarize_context_items(items: Any, item_type: str) -> list[dict[str, object]]:
    """Return deterministic summaries for in-memory dict or dataclass items."""

    _require_non_empty_string(item_type, "item_type")
    summaries = []
    for item in _normalize_items(items):
        summary = _summary_from_item(item, item_type)
        summaries.append(summary)
    return sorted(summaries, key=_summary_sort_key)


def empty_adaptive_runtime_context(
    created_by: str | None = None,
    notes: str | None = None,
) -> AdaptiveRuntimeContext:
    """Return a safe empty context with deterministic runtime fallback."""

    return build_adaptive_runtime_context(created_by=created_by, notes=notes)


def _build_runtime_section(
    *,
    section_name: str,
    items: Any,
    item_type: str,
    component_type: str | None,
    eligibility_dicts: list[dict[str, object]],
    gate_result_dicts: list[dict[str, object]],
) -> AdaptiveRuntimeSection:
    summaries = summarize_context_items(items, item_type)
    runtime_active_count = _runtime_active_count(summaries)
    warnings = _runtime_active_warnings(section_name, summaries)
    eligible_count = _eligible_count(component_type, eligibility_dicts)
    allowed_count = _allowed_for_consideration_count(component_type, gate_result_dicts)
    return AdaptiveRuntimeSection(
        section_name=section_name,
        available=bool(summaries),
        item_count=len(summaries),
        eligible_count=eligible_count,
        allowed_for_consideration_count=allowed_count,
        runtime_active_count=runtime_active_count,
        summaries=summaries,
        warnings=warnings,
    )


def _build_parser_section(items: Any) -> AdaptiveParserRuntimeSection:
    summaries = summarize_context_items(items, "parser_mapping_evolution")
    runtime_active_count = _runtime_active_count(summaries)
    parser_backlog_count = sum(1 for summary in summaries if _is_parser_backlog(summary))
    parser_evolution_count = len(summaries) - parser_backlog_count
    warnings = _runtime_active_warnings("parser", summaries)
    return AdaptiveParserRuntimeSection(
        section_name="parser",
        available=bool(summaries),
        parser_evolution_count=parser_evolution_count,
        parser_backlog_count=parser_backlog_count,
        runtime_active_count=runtime_active_count,
        phase4i_contract_required=True,
        awr_regression_required=True,
        scoring_regression_required=True,
        summaries=summaries,
        warnings=warnings,
    )


def _empty_section(section_name: str) -> AdaptiveRuntimeSection:
    return AdaptiveRuntimeSection(
        section_name=section_name,
        available=False,
        item_count=0,
        eligible_count=0,
        allowed_for_consideration_count=0,
        runtime_active_count=0,
        summaries=[],
        warnings=[],
    )


def _empty_parser_section() -> AdaptiveParserRuntimeSection:
    return AdaptiveParserRuntimeSection(
        section_name="parser",
        available=False,
        parser_evolution_count=0,
        parser_backlog_count=0,
        runtime_active_count=0,
        phase4i_contract_required=True,
        awr_regression_required=True,
        scoring_regression_required=True,
        summaries=[],
        warnings=[],
    )


def _normalize_config(config: Any) -> dict[str, object]:
    if config is None:
        return adaptive_runtime_config_to_dict(default_deterministic_runtime_config())
    return adaptive_runtime_config_to_dict(validate_adaptive_runtime_config(config))


def _normalize_eligibility_dicts(items: Any) -> list[dict[str, object]]:
    normalized = []
    for item in _normalize_items(items):
        normalized.append(
            component_eligibility_to_dict(validate_component_eligibility(item))
        )
    return sorted(normalized, key=_summary_sort_key)


def _normalize_gate_result_dicts(items: Any) -> list[dict[str, object]]:
    normalized = []
    for item in _normalize_items(items):
        normalized.append(gate_result_to_dict(validate_gate_result(item)))
    return sorted(normalized, key=_summary_sort_key)


def _section_from_any(value: Any) -> AdaptiveRuntimeSection:
    if isinstance(value, AdaptiveRuntimeSection):
        return value
    if isinstance(value, Mapping):
        return adaptive_runtime_section_from_dict(value)
    raise AdaptiveRuntimeContextError("section data must be an adaptive runtime section.")


def _parser_section_from_any(value: Any) -> AdaptiveParserRuntimeSection:
    if isinstance(value, AdaptiveParserRuntimeSection):
        return value
    if isinstance(value, Mapping):
        return adaptive_parser_runtime_section_from_dict(value)
    raise AdaptiveRuntimeContextError("parser section data must be a parser section.")


def _reference_context(name: str, references: Any) -> dict[str, object]:
    summaries = summarize_context_items(references, f"{name}_reference")
    return {
        "section_name": name,
        "available": bool(summaries),
        "reference_count": len(summaries),
        "references": summaries,
    }


def _phase4i_reference(phase4i_output_summary: Any, report_metadata: Any) -> str | None:
    for source in (phase4i_output_summary, report_metadata):
        if source is None:
            continue
        summary = _summary_from_item(source, "phase4i_reference_source")
        for key in (
            "phase4i_reference",
            "phase4i_output_reference",
            "output_reference",
            "contract_reference",
            "report_id",
            "run_id",
            "awr_id",
        ):
            value = summary.get(key)
            if _has_text(value):
                return str(value).strip()
    return None


def _collect_gate_strings(
    gate_results: list[dict[str, object]],
    field_name: str,
) -> list[str]:
    values: list[str] = []
    for result in gate_results:
        raw_items = result.get(field_name, [])
        if isinstance(raw_items, list):
            for item in raw_items:
                if _has_text(item):
                    values.append(str(item).strip())
    return values


def _eligible_count(
    component_type: str | None,
    eligibility_dicts: list[dict[str, object]],
) -> int:
    if component_type is None:
        return 0
    return sum(
        1
        for eligibility in eligibility_dicts
        if eligibility.get("component_type") == component_type
        and eligibility.get("runtime_eligible") is True
    )


def _allowed_for_consideration_count(
    component_type: str | None,
    gate_result_dicts: list[dict[str, object]],
) -> int:
    if component_type is None:
        return 0
    return sum(
        1
        for result in gate_result_dicts
        if result.get("component_type") == component_type
        and result.get("allowed") is True
        and result.get("runtime_active") is False
    )


def _normalize_items(items: Any) -> list[Any]:
    if items is None:
        return []
    if isinstance(items, (str, bytes)):
        raise AdaptiveRuntimeContextError("context items must not be strings.")
    if isinstance(items, Mapping):
        return [items]
    if is_dataclass(items) and not isinstance(items, type):
        return [items]
    if hasattr(items, "to_dict") and callable(items.to_dict):
        return [items]
    if isinstance(items, Sequence):
        return list(items)
    return [items]


def _summary_from_item(item: Any, item_type: str) -> dict[str, object]:
    if isinstance(item, Mapping):
        data = deepcopy(dict(item))
    elif is_dataclass(item) and not isinstance(item, type):
        data = asdict(item)
    elif hasattr(item, "to_dict") and callable(item.to_dict):
        data = deepcopy(item.to_dict())
    elif hasattr(item, "__dict__"):
        data = {
            key: deepcopy(value)
            for key, value in vars(item).items()
            if not key.startswith("_") and not callable(value)
        }
    else:
        raise AdaptiveRuntimeContextError(
            f"Unsupported context item type for {item_type}."
        )
    summary = _normalize_summary_mapping(data)
    summary["item_type"] = item_type
    return dict(sorted(summary.items(), key=lambda item_pair: item_pair[0]))


def _normalize_summary_mapping(data: Mapping[str, Any]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in data.items():
        if not isinstance(key, str) or not key.strip():
            raise AdaptiveRuntimeContextError("summary keys must be non-empty strings.")
        normalized[key.strip()] = _normalize_summary_value(value)
    return normalized


def _normalize_summary_value(value: Any) -> object:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_summary_value(child)
            for key, child in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_normalize_summary_value(child) for child in value]
    if is_dataclass(value) and not isinstance(value, type):
        return _normalize_summary_value(asdict(value))
    return str(value)


def _normalize_summaries(value: Any) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise AdaptiveRuntimeContextError("summaries must be a list.")
    summaries = []
    for item in value:
        if not isinstance(item, Mapping):
            raise AdaptiveRuntimeContextError("summary entries must be mappings.")
        summaries.append(_normalize_summary_mapping(item))
    return sorted(summaries, key=_summary_sort_key)


def _normalize_mapping(value: Any, field_name: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise AdaptiveRuntimeContextError(f"{field_name} must be a mapping.")
    return _normalize_summary_mapping(value)


def _runtime_active_count(summaries: list[dict[str, object]]) -> int:
    return sum(1 for summary in summaries if summary.get("runtime_active") is True)


def _runtime_active_warnings(
    section_name: str,
    summaries: list[dict[str, object]],
) -> list[str]:
    warnings = []
    for summary in summaries:
        if summary.get("runtime_active") is True:
            identifier = _summary_identifier(summary)
            warnings.append(
                f"{section_name} item {identifier} claimed runtime_active=true."
            )
    return warnings


def _is_parser_backlog(summary: Mapping[str, object]) -> bool:
    if _has_text(summary.get("backlog_id")):
        return True
    status = summary.get("status")
    return isinstance(status, str) and status.strip().upper() == "BACKLOG_CREATED"


def _validate_no_active_gate_results(gate_results: list[dict[str, object]]) -> None:
    for result in gate_results:
        if result.get("runtime_active") is True:
            raise AdaptiveRuntimeContextError(
                "gate results must not indicate runtime_active=true."
            )


def _validate_section_runtime_inactive(section: Any) -> None:
    if getattr(section, "runtime_active_count") != 0:
        raise AdaptiveRuntimeContextError(
            f"{getattr(section, 'section_name', 'section')} runtime_active_count must be 0."
        )


def _distinct_summary_value_count(
    summaries: list[dict[str, object]],
    field_names: tuple[str, ...],
) -> int:
    values = set()
    for summary in summaries:
        for field_name in field_names:
            value = summary.get(field_name)
            if _has_text(value):
                values.add(str(value).strip())
                break
    return len(values)


def _count_true_summary_field(
    summaries: list[dict[str, object]],
    field_name: str,
) -> int:
    return sum(1 for summary in summaries if summary.get(field_name) is True)


def _summary_sort_key(summary: Mapping[str, object]) -> str:
    return "|".join(
        str(summary.get(field_name, ""))
        for field_name in (
            "component_type",
            "item_type",
            "gate_id",
            "component_id",
            "review_id",
            "evolution_id",
            "backlog_id",
            "result_id",
            "output_id",
            "model_id",
            "materialization_id",
            "explanation_id",
            "reference",
            "name",
        )
    )


def _summary_identifier(summary: Mapping[str, object]) -> str:
    for field_name in (
        "gate_id",
        "component_id",
        "review_id",
        "evolution_id",
        "backlog_id",
        "result_id",
        "output_id",
        "model_id",
        "materialization_id",
        "explanation_id",
        "reference",
        "item_type",
    ):
        value = summary.get(field_name)
        if _has_text(value):
            return str(value).strip()
    return "unspecified"


def _unique_strings(values: Sequence[str]) -> list[str]:
    seen = set()
    unique: list[str] = []
    for value in values:
        if not _has_text(value):
            continue
        text = str(value).strip()
        if text not in seen:
            unique.append(text)
            seen.add(text)
    return unique


def _values_from_mapping(
    data: Mapping[str, Any],
    fields: Sequence[str],
    optional_defaults: Mapping[str, Any],
) -> dict[str, Any]:
    missing = [
        field_name
        for field_name in fields
        if field_name not in data and field_name not in optional_defaults
    ]
    if missing:
        raise AdaptiveRuntimeContextError(
            "Missing required fields: " + ", ".join(missing) + "."
        )
    return {
        field_name: deepcopy(data[field_name])
        if field_name in data
        else deepcopy(optional_defaults[field_name])
        for field_name in fields
    }


def _normalize_runtime_mode(value: Any) -> str:
    _require_non_empty_string(value, "runtime_mode")
    normalized = str(value).strip().lower().replace("-", "_")
    if normalized not in ADAPTIVE_RUNTIME_MODES:
        raise AdaptiveRuntimeContextError(f"Unsupported runtime_mode: {value}.")
    return normalized


def _normalize_string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise AdaptiveRuntimeContextError(f"{field_name} must be a list.")
    normalized = []
    for item in value:
        _require_non_empty_string(item, field_name)
        normalized.append(str(item).strip())
    return normalized


def _require_true(value: Any, field_name: str) -> None:
    if value is not True:
        raise AdaptiveRuntimeContextError(
            f"Phase 7AA.2 runtime context requires {field_name}=true."
        )


def _require_false(value: Any, field_name: str) -> None:
    if value is not False:
        raise AdaptiveRuntimeContextError(
            f"Phase 7AA.2 runtime context requires {field_name}=false."
        )


def _require_zero(value: Any, field_name: str) -> None:
    if value != 0:
        raise AdaptiveRuntimeContextError(
            f"Phase 7AA.2 runtime context requires {field_name}=0."
        )


def _validate_bool(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise AdaptiveRuntimeContextError(f"{field_name} must be a boolean.")


def _validate_nonnegative_int(value: Any, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise AdaptiveRuntimeContextError(f"{field_name} must be a non-negative int.")


def _require_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise AdaptiveRuntimeContextError(f"{field_name} must be a non-empty string.")


def _validate_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise AdaptiveRuntimeContextError(f"{field_name} must be None or a string.")
    if isinstance(value, str) and not value.strip():
        raise AdaptiveRuntimeContextError(f"{field_name} must not be blank.")


def _normalize_optional_string(value: str | None) -> str | None:
    return None if value is None else value.strip()


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _identifier_fragment(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "UNSPECIFIED"
