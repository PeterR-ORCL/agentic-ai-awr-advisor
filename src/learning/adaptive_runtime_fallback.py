"""Phase 7AA.6 runtime fallback / rollback decision layer.

This module evaluates existing Phase 7AA adapter result records and returns a
unified runtime safety decision. It does not execute rollback, apply adaptive
behavior, mutate Phase 4I, call runtime engines, call services, or write
databases.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
import re
from typing import Any, Mapping, Sequence

from src.learning.adaptive_parser_adapter import (
    ParserIntegrationResult,
    parser_integration_result_to_dict,
)
from src.learning.adaptive_recommendation_adapter import (
    RecommendationIntegrationResult,
    recommendation_integration_result_to_dict,
)
from src.learning.adaptive_runtime_context import (
    AdaptiveRuntimeContext,
    validate_adaptive_runtime_context,
)
from src.learning.adaptive_runtime_gate import (
    AdaptiveRuntimeConfig,
    AdaptiveRuntimeGateResult,
    adaptive_runtime_config_to_dict,
    gate_result_to_dict,
    validate_adaptive_runtime_config,
    validate_gate_result,
)
from src.learning.adaptive_scoring_adapter import (
    ScoringIntegrationResult,
    scoring_integration_result_to_dict,
)


FINAL_RUNTIME_POSTURES = (
    "deterministic_fallback",
    "adaptive_consideration_ready",
    "unsafe_requires_review",
)

FALLBACK_COMPONENTS = (
    "scoring",
    "recommendation",
    "parser",
)

RUNTIME_FALLBACK_DECISION_FIELDS = (
    "decision_id",
    "deterministic_runtime_authoritative",
    "final_runtime_posture",
    "fallback_to_deterministic",
    "fallback_required",
    "rollback_required",
    "rollback_available",
    "rollback_reference",
    "phase4i_contract_preserved",
    "runtime_mutation_detected",
    "runtime_influence_detected",
    "scoring_safe",
    "recommendation_safe",
    "parser_safe",
    "scoring_fallback_required",
    "recommendation_fallback_required",
    "parser_fallback_required",
    "denied_reasons",
    "warnings",
    "required_next_steps",
    "validation_reference",
    "readiness_reference",
    "created_by",
    "notes",
)


class AdaptiveRuntimeFallbackError(ValueError):
    """Raised when Phase 7AA.6 fallback decision rules are violated."""


@dataclass(frozen=True)
class RuntimeFallbackDecision:
    """Unified runtime safety decision that never executes fallback or rollback."""

    decision_id: str
    deterministic_runtime_authoritative: bool
    final_runtime_posture: str
    fallback_to_deterministic: bool
    fallback_required: bool
    rollback_required: bool
    rollback_available: bool
    rollback_reference: str | None
    phase4i_contract_preserved: bool
    runtime_mutation_detected: bool
    runtime_influence_detected: bool
    scoring_safe: bool
    recommendation_safe: bool
    parser_safe: bool
    scoring_fallback_required: bool
    recommendation_fallback_required: bool
    parser_fallback_required: bool
    denied_reasons: list[str]
    warnings: list[str]
    required_next_steps: list[str]
    validation_reference: str | None
    readiness_reference: str | None
    created_by: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.decision_id, "decision_id")
        posture = _normalize_posture(self.final_runtime_posture)
        for field_name in (
            "deterministic_runtime_authoritative",
            "fallback_to_deterministic",
            "fallback_required",
            "rollback_required",
            "rollback_available",
            "phase4i_contract_preserved",
            "runtime_mutation_detected",
            "runtime_influence_detected",
            "scoring_safe",
            "recommendation_safe",
            "parser_safe",
            "scoring_fallback_required",
            "recommendation_fallback_required",
            "parser_fallback_required",
        ):
            _validate_bool(getattr(self, field_name), field_name)
        _require_true(
            self.deterministic_runtime_authoritative,
            "deterministic_runtime_authoritative",
        )
        _require_true(self.phase4i_contract_preserved, "phase4i_contract_preserved")
        _validate_optional_string(self.rollback_reference, "rollback_reference")
        _validate_optional_string(self.validation_reference, "validation_reference")
        _validate_optional_string(self.readiness_reference, "readiness_reference")
        denied_reasons = _normalize_string_list(self.denied_reasons, "denied_reasons")
        warnings = _normalize_string_list(self.warnings, "warnings")
        required_next_steps = _normalize_string_list(
            self.required_next_steps,
            "required_next_steps",
        )
        _validate_optional_string(self.created_by, "created_by")
        _validate_optional_string(self.notes, "notes")

        if self.rollback_required and not self.rollback_available and not self.fallback_required:
            raise AdaptiveRuntimeFallbackError(
                "rollback_required=true and rollback_available=false require "
                "fallback_required=true."
            )
        if posture == "unsafe_requires_review" and not self.fallback_required:
            raise AdaptiveRuntimeFallbackError(
                "unsafe_requires_review requires fallback_required=true."
            )
        if posture == "deterministic_fallback" and not self.fallback_to_deterministic:
            raise AdaptiveRuntimeFallbackError(
                "deterministic_fallback requires fallback_to_deterministic=true."
            )
        if posture != "unsafe_requires_review" and self.runtime_mutation_detected:
            raise AdaptiveRuntimeFallbackError(
                "runtime_mutation_detected=true is only valid for unsafe_requires_review."
            )
        if posture != "unsafe_requires_review" and self.runtime_influence_detected:
            raise AdaptiveRuntimeFallbackError(
                "runtime_influence_detected=true is only valid for unsafe_requires_review."
            )
        if posture == "adaptive_consideration_ready" and self.fallback_required:
            raise AdaptiveRuntimeFallbackError(
                "adaptive_consideration_ready must not require immediate fallback."
            )

        object.__setattr__(self, "final_runtime_posture", posture)
        object.__setattr__(self, "deterministic_runtime_authoritative", True)
        object.__setattr__(
            self,
            "rollback_reference",
            _normalize_optional_string(self.rollback_reference),
        )
        object.__setattr__(self, "phase4i_contract_preserved", True)
        object.__setattr__(self, "denied_reasons", denied_reasons)
        object.__setattr__(self, "warnings", warnings)
        object.__setattr__(self, "required_next_steps", required_next_steps)
        object.__setattr__(
            self,
            "validation_reference",
            _normalize_optional_string(self.validation_reference),
        )
        object.__setattr__(
            self,
            "readiness_reference",
            _normalize_optional_string(self.readiness_reference),
        )
        object.__setattr__(
            self,
            "created_by",
            _normalize_optional_string(self.created_by),
        )
        object.__setattr__(self, "notes", _normalize_optional_string(self.notes))


def create_runtime_fallback_decision_id(
    validation_reference: str | None = None,
    readiness_reference: str | None = None,
) -> str:
    """Create a deterministic runtime fallback decision identifier."""

    return (
        "RUNTIME-FALLBACK-"
        f"{_identifier_fragment(validation_reference or 'NO-VALIDATION')}-"
        f"{_identifier_fragment(readiness_reference or 'NO-READINESS')}"
    )


def evaluate_runtime_fallback(
    *,
    scoring_integration_result: ScoringIntegrationResult | Mapping[str, Any] | None = None,
    recommendation_integration_result: (
        RecommendationIntegrationResult | Mapping[str, Any] | None
    ) = None,
    parser_integration_result: ParserIntegrationResult | Mapping[str, Any] | None = None,
    adaptive_runtime_context: AdaptiveRuntimeContext | Mapping[str, Any] | None = None,
    adaptive_runtime_config: AdaptiveRuntimeConfig | Mapping[str, Any] | None = None,
    gate_results: Sequence[AdaptiveRuntimeGateResult | Mapping[str, Any]] | None = None,
    rollback_reference: str | None = None,
    validation_reference: str | None = None,
    readiness_reference: str | None = None,
    created_by: str | None = None,
    notes: str | None = None,
) -> RuntimeFallbackDecision:
    """Evaluate adapter result safety and return a decision-only runtime posture."""

    denied_reasons: list[str] = []
    warnings: list[str] = []

    if adaptive_runtime_context is not None:
        try:
            context = validate_adaptive_runtime_context(adaptive_runtime_context)
            if not context.deterministic_runtime_authoritative:
                denied_reasons.append("context_deterministic_runtime_authority_required")
            if not context.fallback_to_deterministic:
                denied_reasons.append("context_fallback_to_deterministic_required")
            if not context.phase4i_contract_preserved:
                denied_reasons.append("context_phase4i_contract_preservation_required")
            if context.runtime_influence_applied:
                denied_reasons.append("context_runtime_influence_already_applied")
            if context.runtime_mutation_performed:
                denied_reasons.append("context_runtime_mutation_performed")
        except Exception as exc:
            denied_reasons.append("adaptive_runtime_context_invalid")
            warnings.append(str(exc))

    if adaptive_runtime_config is not None:
        try:
            config = validate_adaptive_runtime_config(adaptive_runtime_config)
            config_data = adaptive_runtime_config_to_dict(config)
            if not config_data.get("deterministic_runtime_authoritative", False):
                denied_reasons.append("config_deterministic_runtime_authority_required")
            if not config_data.get("fallback_to_deterministic", False):
                denied_reasons.append("config_fallback_to_deterministic_required")
        except Exception as exc:
            denied_reasons.append("adaptive_runtime_config_invalid")
            warnings.append(str(exc))

    gate_allowed = _any_gate_allowed(gate_results, denied_reasons, warnings)
    scoring_safe, scoring_denied, scoring_warnings = (
        evaluate_scoring_result_safety(scoring_integration_result)
        if scoring_integration_result is not None
        else (True, [], [])
    )
    recommendation_safe, recommendation_denied, recommendation_warnings = (
        evaluate_recommendation_result_safety(recommendation_integration_result)
        if recommendation_integration_result is not None
        else (True, [], [])
    )
    parser_safe, parser_denied, parser_warnings = (
        evaluate_parser_result_safety(parser_integration_result)
        if parser_integration_result is not None
        else (True, [], [])
    )
    denied_reasons.extend(scoring_denied)
    denied_reasons.extend(recommendation_denied)
    denied_reasons.extend(parser_denied)
    warnings.extend(scoring_warnings)
    warnings.extend(recommendation_warnings)
    warnings.extend(parser_warnings)

    scoring_data = _adapter_mapping(scoring_integration_result, "scoring")
    recommendation_data = _adapter_mapping(
        recommendation_integration_result,
        "recommendation",
    )
    parser_data = _adapter_mapping(parser_integration_result, "parser")
    all_adapter_data = [scoring_data, recommendation_data, parser_data]

    mutation_detected = any(_runtime_mutation_present(data) for data in all_adapter_data)
    influence_detected = any(_runtime_influence_present(data) for data in all_adapter_data)
    if mutation_detected:
        denied_reasons.append("runtime_mutation_detected")
    if influence_detected:
        denied_reasons.append("runtime_influence_detected")

    scoring_fallback_required = _component_fallback_required(
        scoring_data,
        "fallback_to_deterministic",
        scoring_safe,
    )
    recommendation_fallback_required = _component_fallback_required(
        recommendation_data,
        "fallback_to_deterministic",
        recommendation_safe,
    )
    parser_fallback_required = _component_fallback_required(
        parser_data,
        "fallback_to_current_parser",
        parser_safe,
    )
    adaptive_consideration = (
        gate_allowed
        or _scoring_adaptive_considered(scoring_data)
        or _recommendation_adaptive_considered(recommendation_data)
        or _parser_adaptive_considered(parser_data)
    )

    effective_rollback = _first_text(rollback_reference)
    rollback_available = _has_text(effective_rollback)
    rollback_required = adaptive_consideration and not rollback_available
    if rollback_required:
        denied_reasons.append("rollback_reference_required")

    effective_validation = _first_text(
        validation_reference,
        _mapping_text(scoring_data, "validation_reference"),
        _mapping_text(recommendation_data, "validation_reference"),
        _mapping_text(parser_data, "validation_reference"),
    )
    if adaptive_consideration and not _has_text(effective_validation):
        denied_reasons.append("validation_reference_required")
    if adaptive_consideration and not _has_text(readiness_reference):
        denied_reasons.append("readiness_reference_required")

    unsafe = (
        mutation_detected
        or influence_detected
        or not scoring_safe
        or not recommendation_safe
        or not parser_safe
    )
    component_fallback_required = (
        scoring_fallback_required
        or recommendation_fallback_required
        or parser_fallback_required
    )
    if unsafe:
        posture = "unsafe_requires_review"
        fallback_required = True
    elif (
        adaptive_consideration
        and rollback_available
        and _has_text(effective_validation)
        and _has_text(readiness_reference)
        and not component_fallback_required
        and not denied_reasons
    ):
        posture = "adaptive_consideration_ready"
        fallback_required = False
    else:
        posture = "deterministic_fallback"
        fallback_required = True

    next_steps = _required_next_steps(
        posture,
        rollback_required,
        adaptive_consideration,
        effective_validation,
        readiness_reference,
        denied_reasons,
    )
    return RuntimeFallbackDecision(
        decision_id=create_runtime_fallback_decision_id(
            effective_validation,
            readiness_reference,
        ),
        deterministic_runtime_authoritative=True,
        final_runtime_posture=posture,
        fallback_to_deterministic=True,
        fallback_required=fallback_required,
        rollback_required=rollback_required,
        rollback_available=rollback_available,
        rollback_reference=effective_rollback,
        phase4i_contract_preserved=True,
        runtime_mutation_detected=mutation_detected,
        runtime_influence_detected=influence_detected,
        scoring_safe=scoring_safe,
        recommendation_safe=recommendation_safe,
        parser_safe=parser_safe,
        scoring_fallback_required=scoring_fallback_required,
        recommendation_fallback_required=recommendation_fallback_required,
        parser_fallback_required=parser_fallback_required,
        denied_reasons=_unique_strings(denied_reasons),
        warnings=_unique_strings(warnings),
        required_next_steps=next_steps,
        validation_reference=effective_validation,
        readiness_reference=readiness_reference,
        created_by=created_by,
        notes=notes,
    )


def validate_runtime_fallback_decision(
    decision: RuntimeFallbackDecision | Mapping[str, Any],
) -> RuntimeFallbackDecision:
    """Validate and return a runtime fallback decision."""

    if isinstance(decision, Mapping):
        return runtime_fallback_decision_from_dict(decision)
    if not isinstance(decision, RuntimeFallbackDecision):
        raise AdaptiveRuntimeFallbackError("decision must be RuntimeFallbackDecision.")
    return RuntimeFallbackDecision(**runtime_fallback_decision_to_dict(decision))


def runtime_fallback_decision_to_dict(decision: RuntimeFallbackDecision) -> dict[str, Any]:
    """Serialize a runtime fallback decision to a deterministic dictionary."""

    if not isinstance(decision, RuntimeFallbackDecision):
        raise AdaptiveRuntimeFallbackError("decision must be RuntimeFallbackDecision.")
    return {
        "decision_id": decision.decision_id,
        "deterministic_runtime_authoritative": (
            decision.deterministic_runtime_authoritative
        ),
        "final_runtime_posture": decision.final_runtime_posture,
        "fallback_to_deterministic": decision.fallback_to_deterministic,
        "fallback_required": decision.fallback_required,
        "rollback_required": decision.rollback_required,
        "rollback_available": decision.rollback_available,
        "rollback_reference": decision.rollback_reference,
        "phase4i_contract_preserved": decision.phase4i_contract_preserved,
        "runtime_mutation_detected": decision.runtime_mutation_detected,
        "runtime_influence_detected": decision.runtime_influence_detected,
        "scoring_safe": decision.scoring_safe,
        "recommendation_safe": decision.recommendation_safe,
        "parser_safe": decision.parser_safe,
        "scoring_fallback_required": decision.scoring_fallback_required,
        "recommendation_fallback_required": decision.recommendation_fallback_required,
        "parser_fallback_required": decision.parser_fallback_required,
        "denied_reasons": deepcopy(decision.denied_reasons),
        "warnings": deepcopy(decision.warnings),
        "required_next_steps": deepcopy(decision.required_next_steps),
        "validation_reference": decision.validation_reference,
        "readiness_reference": decision.readiness_reference,
        "created_by": decision.created_by,
        "notes": decision.notes,
    }


def runtime_fallback_decision_from_dict(
    data: Mapping[str, Any],
) -> RuntimeFallbackDecision:
    """Reconstruct and validate a runtime fallback decision from dictionary data."""

    if not isinstance(data, Mapping):
        raise AdaptiveRuntimeFallbackError(
            "runtime fallback decision data must be a mapping."
        )
    values = _values_from_mapping(
        data,
        RUNTIME_FALLBACK_DECISION_FIELDS,
        optional_defaults={
            "deterministic_runtime_authoritative": True,
            "final_runtime_posture": "deterministic_fallback",
            "fallback_to_deterministic": True,
            "fallback_required": True,
            "rollback_required": False,
            "rollback_available": False,
            "rollback_reference": None,
            "phase4i_contract_preserved": True,
            "runtime_mutation_detected": False,
            "runtime_influence_detected": False,
            "scoring_safe": True,
            "recommendation_safe": True,
            "parser_safe": True,
            "scoring_fallback_required": True,
            "recommendation_fallback_required": True,
            "parser_fallback_required": True,
            "denied_reasons": [],
            "warnings": [],
            "required_next_steps": [],
            "validation_reference": None,
            "readiness_reference": None,
            "created_by": None,
            "notes": None,
        },
    )
    return RuntimeFallbackDecision(**values)


def evaluate_scoring_result_safety(result: Any) -> tuple[bool, list[str], list[str]]:
    """Return safety status for one scoring integration result record."""

    data = _adapter_mapping(result, "scoring")
    if not data:
        return False, ["scoring_result_missing"], []
    checks = (
        ("runtime_score_applied", False),
        ("runtime_mutation_performed", False),
        ("runtime_active", False),
        ("runtime_influence_granted", False),
        ("deterministic_score_authoritative", True),
        ("phase4i_contract_preserved", True),
    )
    denied = _failed_boolean_checks(data, checks, "scoring")
    if not (
        _bool_value(data, "fallback_to_deterministic")
        or _bool_value(data, "gate_allowed_for_consideration")
    ):
        denied.append("scoring_requires_fallback_or_gate_consideration")
    return not denied, denied, _adapter_warnings(data)


def evaluate_recommendation_result_safety(result: Any) -> tuple[bool, list[str], list[str]]:
    """Return safety status for one recommendation integration result record."""

    data = _adapter_mapping(result, "recommendation")
    if not data:
        return False, ["recommendation_result_missing"], []
    checks = (
        ("runtime_recommendation_applied", False),
        ("runtime_mutation_performed", False),
        ("runtime_active", False),
        ("runtime_influence_granted", False),
        ("deterministic_recommendation_authoritative", True),
        ("phase4i_contract_preserved", True),
    )
    denied = _failed_boolean_checks(data, checks, "recommendation")
    if not (
        _bool_value(data, "fallback_to_deterministic")
        or _bool_value(data, "gate_allowed_for_consideration")
    ):
        denied.append("recommendation_requires_fallback_or_gate_consideration")
    return not denied, denied, _adapter_warnings(data)


def evaluate_parser_result_safety(result: Any) -> tuple[bool, list[str], list[str]]:
    """Return safety status for one parser integration result record."""

    data = _adapter_mapping(result, "parser")
    if not data:
        return False, ["parser_result_missing"], []
    checks = (
        ("runtime_parser_applied", False),
        ("runtime_mutation_performed", False),
        ("runtime_active", False),
        ("runtime_influence_granted", False),
        ("parser_runtime_authoritative", True),
        ("phase4i_contract_preserved", True),
        ("awr_regression_required", True),
        ("scoring_regression_required", True),
        ("unknown_signal_safety_required", True),
    )
    denied = _failed_boolean_checks(data, checks, "parser")
    if not (
        _bool_value(data, "fallback_to_current_parser")
        or _bool_value(data, "gate_allowed_for_consideration")
    ):
        denied.append("parser_requires_fallback_or_gate_consideration")
    return not denied, denied, _adapter_warnings(data)


def deterministic_fallback_decision(
    reason: str,
    created_by: str | None = None,
    notes: str | None = None,
) -> RuntimeFallbackDecision:
    """Return the default deterministic fallback decision record."""

    _require_non_empty_string(reason, "reason")
    return RuntimeFallbackDecision(
        decision_id=create_runtime_fallback_decision_id(),
        deterministic_runtime_authoritative=True,
        final_runtime_posture="deterministic_fallback",
        fallback_to_deterministic=True,
        fallback_required=True,
        rollback_required=False,
        rollback_available=False,
        rollback_reference=None,
        phase4i_contract_preserved=True,
        runtime_mutation_detected=False,
        runtime_influence_detected=False,
        scoring_safe=True,
        recommendation_safe=True,
        parser_safe=True,
        scoring_fallback_required=True,
        recommendation_fallback_required=True,
        parser_fallback_required=True,
        denied_reasons=[reason],
        warnings=[],
        required_next_steps=["keep deterministic runtime authoritative"],
        validation_reference=None,
        readiness_reference=None,
        created_by=created_by,
        notes=notes,
    )


def _adapter_mapping(value: Any, component: str) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, ScoringIntegrationResult):
        return scoring_integration_result_to_dict(value)
    if isinstance(value, RecommendationIntegrationResult):
        return recommendation_integration_result_to_dict(value)
    if isinstance(value, ParserIntegrationResult):
        return parser_integration_result_to_dict(value)
    if isinstance(value, Mapping):
        return deepcopy(dict(value))
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return deepcopy(value.to_dict())
    if hasattr(value, "__dict__"):
        return {
            key: deepcopy(child)
            for key, child in vars(value).items()
            if not key.startswith("_") and not callable(child)
        }
    raise AdaptiveRuntimeFallbackError(f"{component} result must be mapping or dataclass.")


def _failed_boolean_checks(
    data: Mapping[str, Any],
    checks: Sequence[tuple[str, bool]],
    component: str,
) -> list[str]:
    denied: list[str] = []
    for field_name, expected in checks:
        if data.get(field_name) is not expected:
            denied.append(f"{component}_{field_name}_unsafe")
    return denied


def _adapter_warnings(data: Mapping[str, Any]) -> list[str]:
    return _string_items(data.get("warnings", []))


def _component_fallback_required(
    data: Mapping[str, Any],
    fallback_field: str,
    safe: bool,
) -> bool:
    if not data:
        return True
    return (not safe) or _bool_value(data, fallback_field)


def _scoring_adaptive_considered(data: Mapping[str, Any]) -> bool:
    if not data:
        return False
    return bool(data.get("gate_allowed_for_consideration")) or (
        data.get("selected_score_source") not in (None, "deterministic")
    )


def _recommendation_adaptive_considered(data: Mapping[str, Any]) -> bool:
    if not data:
        return False
    return bool(data.get("gate_allowed_for_consideration")) or (
        data.get("selected_recommendation_source") not in (None, "deterministic")
    )


def _parser_adaptive_considered(data: Mapping[str, Any]) -> bool:
    if not data:
        return False
    return bool(data.get("gate_allowed_for_consideration")) or (
        data.get("selected_parser_source") not in (None, "current_parser")
    ) or (data.get("selected_parser_action") not in (None, "keep_current_parser"))


def _runtime_mutation_present(data: Mapping[str, Any]) -> bool:
    return any(
        data.get(field_name) is True
        for field_name in (
            "runtime_mutation_performed",
            "runtime_score_applied",
            "runtime_recommendation_applied",
            "runtime_parser_applied",
            "runtime_active",
        )
    )


def _runtime_influence_present(data: Mapping[str, Any]) -> bool:
    return data.get("runtime_influence_granted") is True


def _any_gate_allowed(
    gate_results: Sequence[AdaptiveRuntimeGateResult | Mapping[str, Any]] | None,
    denied_reasons: list[str],
    warnings: list[str],
) -> bool:
    if gate_results is None:
        return False
    allowed = False
    if not isinstance(gate_results, Sequence) or isinstance(gate_results, (str, bytes)):
        denied_reasons.append("gate_results_must_be_sequence")
        return False
    for gate_result in gate_results:
        try:
            gate = validate_gate_result(gate_result)
            gate_data = gate_result_to_dict(gate)
            if gate.allowed_for_consideration:
                allowed = True
            denied_reasons.extend(_string_items(gate_data.get("denied_reasons", [])))
            warnings.extend(_string_items(gate_data.get("warnings", [])))
        except Exception as exc:
            denied_reasons.append("gate_result_invalid")
            warnings.append(str(exc))
    return allowed


def _required_next_steps(
    posture: str,
    rollback_required: bool,
    adaptive_consideration: bool,
    validation_reference: str | None,
    readiness_reference: str | None,
    denied_reasons: Sequence[str],
) -> list[str]:
    steps: list[str] = []
    if posture == "deterministic_fallback":
        steps.append("keep deterministic runtime authoritative")
    if posture == "unsafe_requires_review":
        steps.append("review unsafe adapter result before runtime certification")
    if rollback_required:
        steps.append("provide rollback reference before adaptive consideration")
    if adaptive_consideration and not _has_text(validation_reference):
        steps.append("provide validation reference before adaptive consideration")
    if adaptive_consideration and not _has_text(readiness_reference):
        steps.append("provide readiness reference before adaptive consideration")
    if posture == "adaptive_consideration_ready":
        steps.append("certify adaptive consideration in Phase 7AA.7 before runtime use")
    if denied_reasons and not steps:
        steps.append("resolve denied fallback decision reasons")
    return _unique_strings(steps)


def _bool_value(data: Mapping[str, Any], field_name: str) -> bool:
    return data.get(field_name) is True


def _mapping_text(data: Mapping[str, Any], field_name: str) -> str | None:
    value = data.get(field_name)
    return str(value).strip() if _has_text(value) else None


def _first_text(*values: Any) -> str | None:
    for value in values:
        if _has_text(value):
            return str(value).strip()
    return None


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
        raise AdaptiveRuntimeFallbackError(
            "Missing required fields: " + ", ".join(missing) + "."
        )
    return {
        field_name: deepcopy(data[field_name])
        if field_name in data
        else deepcopy(optional_defaults[field_name])
        for field_name in fields
    }


def _normalize_posture(value: Any) -> str:
    _require_non_empty_string(value, "final_runtime_posture")
    normalized = str(value).strip().lower().replace("-", "_")
    if normalized not in FINAL_RUNTIME_POSTURES:
        raise AdaptiveRuntimeFallbackError(f"Unsupported final runtime posture: {value}.")
    return normalized


def _string_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if _has_text(item)]


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


def _normalize_string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise AdaptiveRuntimeFallbackError(f"{field_name} must be a list.")
    normalized = []
    for item in value:
        _require_non_empty_string(item, field_name)
        normalized.append(str(item).strip())
    return normalized


def _validate_bool(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise AdaptiveRuntimeFallbackError(f"{field_name} must be a boolean.")


def _require_true(value: Any, field_name: str) -> None:
    if value is not True:
        raise AdaptiveRuntimeFallbackError(
            f"Phase 7AA.6 fallback layer requires {field_name}=true."
        )


def _require_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise AdaptiveRuntimeFallbackError(f"{field_name} must be a non-empty string.")


def _validate_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise AdaptiveRuntimeFallbackError(f"{field_name} must be None or a string.")
    if isinstance(value, str) and not value.strip():
        raise AdaptiveRuntimeFallbackError(f"{field_name} must not be blank.")


def _normalize_optional_string(value: str | None) -> str | None:
    return None if value is None else value.strip()


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _identifier_fragment(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "UNSPECIFIED"
