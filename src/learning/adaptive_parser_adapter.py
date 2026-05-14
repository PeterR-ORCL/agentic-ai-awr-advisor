"""Phase 7AA.5 controlled parser integration adapter / backlog gate.

This module evaluates supplied parser evolution and backlog candidates against
the 7AA.1 gate and 7AA.2 context, then returns a consideration-only result. It
does not modify runtime parser behavior, mutate Phase 4I, call parser modules,
change scoring, change recommendations, call services, or write databases.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
import re
from typing import Any, Mapping, Sequence

from src.learning.adaptive_runtime_context import (
    AdaptiveRuntimeContext,
    validate_adaptive_runtime_context,
)
from src.learning.adaptive_runtime_gate import (
    AdaptiveRuntimeGateResult,
    gate_result_to_dict,
    validate_gate_result,
)


PARSER_INTEGRATION_SOURCES = (
    "current_parser",
    "parser_evolution",
    "parser_backlog",
    "none",
)

PARSER_INTEGRATION_ACTIONS = (
    "keep_current_parser",
    "consider_parser_backlog",
    "consider_parser_evolution",
    "deny_parser_integration",
)

REQUIRED_PARSER_INTEGRATION_GATES = (
    "adaptive_runtime_context",
    "parser_gate_result",
    "phase4i_contract_preserved",
    "validation_reference",
    "rollback_reference",
    "awr_regression_reference",
    "scoring_regression_reference",
    "unknown_signal_safety_required",
)

PARSER_INTEGRATION_RESULT_FIELDS = (
    "result_id",
    "parser_section",
    "signal_name",
    "parser_evolution_id",
    "parser_backlog_id",
    "proposed_parser_change_type",
    "parser_runtime_authoritative",
    "selected_parser_action",
    "selected_parser_source",
    "parser_change_summary",
    "gate_allowed_for_consideration",
    "fallback_to_current_parser",
    "fallback_reason",
    "phase4i_contract_preserved",
    "awr_regression_required",
    "scoring_regression_required",
    "unknown_signal_safety_required",
    "runtime_parser_applied",
    "runtime_mutation_performed",
    "runtime_active",
    "runtime_influence_granted",
    "validation_reference",
    "rollback_reference",
    "awr_regression_reference",
    "scoring_regression_reference",
    "denied_reasons",
    "warnings",
    "rationale",
    "created_by",
    "notes",
)


class AdaptiveParserAdapterError(ValueError):
    """Raised when Phase 7AA.5 parser adapter rules are violated."""


@dataclass(frozen=True)
class ParserIntegrationResult:
    """Parser backlog/integration consideration result that never applies runtime changes."""

    result_id: str
    parser_section: str | None
    signal_name: str | None
    parser_evolution_id: str | None
    parser_backlog_id: str | None
    proposed_parser_change_type: str | None
    parser_runtime_authoritative: bool
    selected_parser_action: str
    selected_parser_source: str
    parser_change_summary: str
    gate_allowed_for_consideration: bool
    fallback_to_current_parser: bool
    fallback_reason: str | None
    phase4i_contract_preserved: bool
    awr_regression_required: bool
    scoring_regression_required: bool
    unknown_signal_safety_required: bool
    runtime_parser_applied: bool
    runtime_mutation_performed: bool
    runtime_active: bool
    runtime_influence_granted: bool
    validation_reference: str | None
    rollback_reference: str | None
    awr_regression_reference: str | None
    scoring_regression_reference: str | None
    denied_reasons: list[str]
    warnings: list[str]
    rationale: str
    created_by: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.result_id, "result_id")
        parser_section = _normalize_optional_string_value(
            self.parser_section,
            "parser_section",
        )
        signal_name = _normalize_optional_string_value(self.signal_name, "signal_name")
        parser_evolution_id = _normalize_optional_string_value(
            self.parser_evolution_id,
            "parser_evolution_id",
        )
        parser_backlog_id = _normalize_optional_string_value(
            self.parser_backlog_id,
            "parser_backlog_id",
        )
        proposed_change_type = _normalize_optional_string_value(
            self.proposed_parser_change_type,
            "proposed_parser_change_type",
        )
        selected_action = _normalize_parser_action(self.selected_parser_action)
        selected_source = _normalize_parser_source(self.selected_parser_source)
        _require_non_empty_string(self.parser_change_summary, "parser_change_summary")
        _validate_bool(
            self.gate_allowed_for_consideration,
            "gate_allowed_for_consideration",
        )
        _validate_bool(self.fallback_to_current_parser, "fallback_to_current_parser")
        _require_true(self.parser_runtime_authoritative, "parser_runtime_authoritative")
        _require_true(self.phase4i_contract_preserved, "phase4i_contract_preserved")
        _require_true(self.awr_regression_required, "awr_regression_required")
        _require_true(self.scoring_regression_required, "scoring_regression_required")
        _require_true(
            self.unknown_signal_safety_required,
            "unknown_signal_safety_required",
        )
        _require_false(self.runtime_parser_applied, "runtime_parser_applied")
        _require_false(self.runtime_mutation_performed, "runtime_mutation_performed")
        _require_false(self.runtime_active, "runtime_active")
        _require_false(self.runtime_influence_granted, "runtime_influence_granted")
        _validate_optional_string(self.fallback_reason, "fallback_reason")
        _validate_optional_string(self.validation_reference, "validation_reference")
        _validate_optional_string(self.rollback_reference, "rollback_reference")
        _validate_optional_string(
            self.awr_regression_reference,
            "awr_regression_reference",
        )
        _validate_optional_string(
            self.scoring_regression_reference,
            "scoring_regression_reference",
        )
        denied_reasons = _normalize_string_list(self.denied_reasons, "denied_reasons")
        warnings = _normalize_string_list(self.warnings, "warnings")
        _require_non_empty_string(self.rationale, "rationale")
        _validate_optional_string(self.created_by, "created_by")
        _validate_optional_string(self.notes, "notes")

        if (
            not self.gate_allowed_for_consideration
            and not self.fallback_to_current_parser
        ):
            raise AdaptiveParserAdapterError(
                "fallback_to_current_parser must be true when gate consideration is denied."
            )
        if self.fallback_to_current_parser and selected_source != "current_parser":
            raise AdaptiveParserAdapterError(
                "fallback results must select current_parser source."
            )
        if self.fallback_to_current_parser and selected_action != "keep_current_parser":
            raise AdaptiveParserAdapterError(
                "fallback results must keep_current_parser."
            )
        if selected_source == "current_parser" and selected_action != "keep_current_parser":
            raise AdaptiveParserAdapterError(
                "current_parser source must use keep_current_parser action."
            )
        if selected_source == "parser_backlog" and selected_action != "consider_parser_backlog":
            raise AdaptiveParserAdapterError(
                "parser_backlog source must use consider_parser_backlog action."
            )
        if (
            selected_source == "parser_evolution"
            and selected_action != "consider_parser_evolution"
        ):
            raise AdaptiveParserAdapterError(
                "parser_evolution source must use consider_parser_evolution action."
            )

        object.__setattr__(self, "parser_section", parser_section)
        object.__setattr__(self, "signal_name", signal_name)
        object.__setattr__(self, "parser_evolution_id", parser_evolution_id)
        object.__setattr__(self, "parser_backlog_id", parser_backlog_id)
        object.__setattr__(
            self,
            "proposed_parser_change_type",
            proposed_change_type,
        )
        object.__setattr__(self, "parser_runtime_authoritative", True)
        object.__setattr__(self, "selected_parser_action", selected_action)
        object.__setattr__(self, "selected_parser_source", selected_source)
        object.__setattr__(
            self,
            "parser_change_summary",
            self.parser_change_summary.strip(),
        )
        object.__setattr__(self, "phase4i_contract_preserved", True)
        object.__setattr__(self, "awr_regression_required", True)
        object.__setattr__(self, "scoring_regression_required", True)
        object.__setattr__(self, "unknown_signal_safety_required", True)
        object.__setattr__(self, "runtime_parser_applied", False)
        object.__setattr__(self, "runtime_mutation_performed", False)
        object.__setattr__(self, "runtime_active", False)
        object.__setattr__(self, "runtime_influence_granted", False)
        object.__setattr__(
            self,
            "fallback_reason",
            _normalize_optional_string(self.fallback_reason),
        )
        object.__setattr__(
            self,
            "validation_reference",
            _normalize_optional_string(self.validation_reference),
        )
        object.__setattr__(
            self,
            "rollback_reference",
            _normalize_optional_string(self.rollback_reference),
        )
        object.__setattr__(
            self,
            "awr_regression_reference",
            _normalize_optional_string(self.awr_regression_reference),
        )
        object.__setattr__(
            self,
            "scoring_regression_reference",
            _normalize_optional_string(self.scoring_regression_reference),
        )
        object.__setattr__(self, "denied_reasons", denied_reasons)
        object.__setattr__(self, "warnings", warnings)
        object.__setattr__(self, "rationale", self.rationale.strip())
        object.__setattr__(
            self,
            "created_by",
            _normalize_optional_string(self.created_by),
        )
        object.__setattr__(self, "notes", _normalize_optional_string(self.notes))


def create_parser_integration_result_id(
    parser_section: str | None,
    signal_name: str | None,
    source: str,
) -> str:
    """Create a deterministic parser integration result identifier."""

    normalized_source = _normalize_parser_source(source)
    return (
        "ADAPTIVE-PARSER-RESULT-"
        f"{_identifier_fragment(parser_section or 'NO-SECTION')}-"
        f"{_identifier_fragment(signal_name or 'NO-SIGNAL')}-"
        f"{_identifier_fragment(normalized_source)}"
    )


def evaluate_parser_integration(
    *,
    parser_mapping_evolution: Any = None,
    parser_backlog_item: Any = None,
    parser_section: str | None = None,
    signal_name: str | None = None,
    adaptive_runtime_context: AdaptiveRuntimeContext | Mapping[str, Any] | None = None,
    gate_result: AdaptiveRuntimeGateResult | Mapping[str, Any] | None = None,
    validation_reference: str | None = None,
    rollback_reference: str | None = None,
    awr_regression_reference: str | None = None,
    scoring_regression_reference: str | None = None,
    phase4i_reference: str | None = None,
    created_by: str | None = None,
    notes: str | None = None,
) -> ParserIntegrationResult:
    """Evaluate parser evolution/backlog candidates as consideration-only context."""

    normalized_section = _normalize_optional_string_value(
        parser_section,
        "parser_section",
    )
    normalized_signal = _normalize_optional_string_value(signal_name, "signal_name")
    denied_reasons: list[str] = []
    warnings: list[str] = []

    if adaptive_runtime_context is None:
        denied_reasons.append("adaptive_runtime_context_required")
    else:
        context = validate_adaptive_runtime_context(adaptive_runtime_context)
        if not context.deterministic_runtime_authoritative:
            denied_reasons.append("deterministic_runtime_authority_required")
        if not context.fallback_to_deterministic:
            denied_reasons.append("fallback_to_current_parser_required")
        if not context.phase4i_contract_preserved:
            denied_reasons.append("phase4i_contract_preservation_required")
        if context.runtime_influence_applied:
            denied_reasons.append("context_runtime_influence_already_applied")
        if context.runtime_mutation_performed:
            denied_reasons.append("context_runtime_mutation_performed")

    normalized_gate = None
    if gate_result is None:
        denied_reasons.append("parser_gate_result_required")
    else:
        normalized_gate = validate_gate_result(gate_result)
        gate_dict = gate_result_to_dict(normalized_gate)
        if normalized_gate.component_type != "parser":
            denied_reasons.append("parser_gate_result_required")
        if not normalized_gate.allowed_for_consideration:
            denied_reasons.append("gate_denied_consideration")
        denied_reasons.extend(_string_items(gate_dict.get("denied_reasons", [])))
        warnings.extend(_string_items(gate_dict.get("warnings", [])))

    for reference_value, denied_reason in (
        (phase4i_reference, "phase4i_reference_required"),
        (validation_reference, "validation_reference_required"),
        (rollback_reference, "rollback_reference_required"),
        (awr_regression_reference, "awr_regression_reference_required"),
        (scoring_regression_reference, "scoring_regression_reference_required"),
    ):
        if not _has_text(reference_value):
            denied_reasons.append(denied_reason)

    backlog_payload, backlog_meta, backlog_warnings, backlog_invalid = _extract_parser_candidate(
        parser_backlog_item,
        "parser_backlog_item",
    )
    evolution_payload, evolution_meta, evolution_warnings, evolution_invalid = (
        _extract_parser_candidate(
            parser_mapping_evolution,
            "parser_mapping_evolution",
        )
    )
    warnings.extend(backlog_warnings)
    warnings.extend(evolution_warnings)
    if backlog_invalid or evolution_invalid:
        denied_reasons.append("parser_input_invalid")
    if parser_backlog_item is None and parser_mapping_evolution is None:
        denied_reasons.append("parser_candidate_required")

    gate_allowed = (
        normalized_gate is not None
        and normalized_gate.allowed_for_consideration
        and normalized_gate.component_type == "parser"
        and not denied_reasons
    )
    selected_action, selected_source, selection_warnings = choose_parser_consideration(
        parser_mapping_evolution=evolution_payload,
        parser_backlog_item=backlog_payload,
        gate_allowed=gate_allowed,
    )
    warnings.extend(selection_warnings)
    fallback = selected_source == "current_parser" or not gate_allowed
    if fallback:
        selected_action = "keep_current_parser"
        selected_source = "current_parser"

    selected_meta = backlog_meta if selected_source == "parser_backlog" else evolution_meta
    result_section = normalized_section or selected_meta.get("parser_section")
    result_signal = normalized_signal or selected_meta.get("signal_name")
    parser_evolution_id = (
        selected_meta.get("source_evolution_id")
        if selected_source == "parser_backlog"
        else selected_meta.get("evolution_id")
    )
    if parser_evolution_id is None and evolution_meta:
        parser_evolution_id = evolution_meta.get("evolution_id")
    parser_backlog_id = backlog_meta.get("backlog_id")
    proposed_change_type = (
        selected_meta.get("proposed_parser_change_type")
        or backlog_meta.get("proposed_parser_change_type")
        or evolution_meta.get("proposed_parser_change_type")
    )
    fallback_reason = _fallback_reason(
        denied_reasons,
        warnings,
        gate_allowed,
        selected_source,
    )
    return ParserIntegrationResult(
        result_id=create_parser_integration_result_id(
            result_section,
            result_signal,
            selected_source,
        ),
        parser_section=result_section,
        signal_name=result_signal,
        parser_evolution_id=parser_evolution_id,
        parser_backlog_id=parser_backlog_id,
        proposed_parser_change_type=proposed_change_type,
        parser_runtime_authoritative=True,
        selected_parser_action=selected_action,
        selected_parser_source=selected_source,
        parser_change_summary=_change_summary(selected_source, fallback),
        gate_allowed_for_consideration=gate_allowed,
        fallback_to_current_parser=fallback,
        fallback_reason=fallback_reason,
        phase4i_contract_preserved=True,
        awr_regression_required=True,
        scoring_regression_required=True,
        unknown_signal_safety_required=True,
        runtime_parser_applied=False,
        runtime_mutation_performed=False,
        runtime_active=False,
        runtime_influence_granted=False,
        validation_reference=validation_reference,
        rollback_reference=rollback_reference,
        awr_regression_reference=awr_regression_reference,
        scoring_regression_reference=scoring_regression_reference,
        denied_reasons=_unique_strings(denied_reasons),
        warnings=_unique_strings(warnings),
        rationale=_integration_rationale(
            selected_source,
            fallback,
            gate_allowed,
            denied_reasons,
        ),
        created_by=created_by,
        notes=notes,
    )


def validate_parser_integration_result(
    result: ParserIntegrationResult | Mapping[str, Any],
) -> ParserIntegrationResult:
    """Validate and return a parser integration result."""

    if isinstance(result, Mapping):
        return parser_integration_result_from_dict(result)
    if not isinstance(result, ParserIntegrationResult):
        raise AdaptiveParserAdapterError("result must be ParserIntegrationResult.")
    return ParserIntegrationResult(**parser_integration_result_to_dict(result))


def parser_integration_result_to_dict(result: ParserIntegrationResult) -> dict[str, Any]:
    """Serialize a parser integration result to a deterministic dictionary."""

    if not isinstance(result, ParserIntegrationResult):
        raise AdaptiveParserAdapterError("result must be ParserIntegrationResult.")
    return {
        "result_id": result.result_id,
        "parser_section": result.parser_section,
        "signal_name": result.signal_name,
        "parser_evolution_id": result.parser_evolution_id,
        "parser_backlog_id": result.parser_backlog_id,
        "proposed_parser_change_type": result.proposed_parser_change_type,
        "parser_runtime_authoritative": result.parser_runtime_authoritative,
        "selected_parser_action": result.selected_parser_action,
        "selected_parser_source": result.selected_parser_source,
        "parser_change_summary": result.parser_change_summary,
        "gate_allowed_for_consideration": result.gate_allowed_for_consideration,
        "fallback_to_current_parser": result.fallback_to_current_parser,
        "fallback_reason": result.fallback_reason,
        "phase4i_contract_preserved": result.phase4i_contract_preserved,
        "awr_regression_required": result.awr_regression_required,
        "scoring_regression_required": result.scoring_regression_required,
        "unknown_signal_safety_required": result.unknown_signal_safety_required,
        "runtime_parser_applied": result.runtime_parser_applied,
        "runtime_mutation_performed": result.runtime_mutation_performed,
        "runtime_active": result.runtime_active,
        "runtime_influence_granted": result.runtime_influence_granted,
        "validation_reference": result.validation_reference,
        "rollback_reference": result.rollback_reference,
        "awr_regression_reference": result.awr_regression_reference,
        "scoring_regression_reference": result.scoring_regression_reference,
        "denied_reasons": deepcopy(result.denied_reasons),
        "warnings": deepcopy(result.warnings),
        "rationale": result.rationale,
        "created_by": result.created_by,
        "notes": result.notes,
    }


def parser_integration_result_from_dict(data: Mapping[str, Any]) -> ParserIntegrationResult:
    """Reconstruct and validate a parser integration result from dictionary data."""

    if not isinstance(data, Mapping):
        raise AdaptiveParserAdapterError(
            "parser integration result data must be a mapping."
        )
    values = _values_from_mapping(
        data,
        PARSER_INTEGRATION_RESULT_FIELDS,
        optional_defaults={
            "parser_section": None,
            "signal_name": None,
            "parser_evolution_id": None,
            "parser_backlog_id": None,
            "proposed_parser_change_type": None,
            "parser_runtime_authoritative": True,
            "gate_allowed_for_consideration": False,
            "fallback_to_current_parser": True,
            "fallback_reason": None,
            "phase4i_contract_preserved": True,
            "awr_regression_required": True,
            "scoring_regression_required": True,
            "unknown_signal_safety_required": True,
            "runtime_parser_applied": False,
            "runtime_mutation_performed": False,
            "runtime_active": False,
            "runtime_influence_granted": False,
            "validation_reference": None,
            "rollback_reference": None,
            "awr_regression_reference": None,
            "scoring_regression_reference": None,
            "denied_reasons": [],
            "warnings": [],
            "created_by": None,
            "notes": None,
        },
    )
    return ParserIntegrationResult(**values)


def choose_parser_consideration(
    parser_mapping_evolution: Any = None,
    parser_backlog_item: Any = None,
    gate_allowed: bool = False,
) -> tuple[str, str, list[str]]:
    """Choose a parser consideration action deterministically without applying it."""

    _validate_bool(gate_allowed, "gate_allowed")
    if not gate_allowed:
        return (
            "keep_current_parser",
            "current_parser",
            ["gate did not allow parser consideration"],
        )

    candidates = (
        ("consider_parser_backlog", "parser_backlog", parser_backlog_item),
        ("consider_parser_evolution", "parser_evolution", parser_mapping_evolution),
    )
    for action, source, value in candidates:
        if value is None:
            continue
        try:
            normalize_parser_payload(value, source)
            return action, source, []
        except AdaptiveParserAdapterError:
            return (
                "keep_current_parser",
                "current_parser",
                [f"{source} input was invalid; fell back to current parser"],
            )
    return (
        "keep_current_parser",
        "current_parser",
        ["no valid parser backlog or parser evolution was supplied"],
    )


def fallback_parser_result(
    parser_section: str | None = None,
    signal_name: str | None = None,
    denied_reasons: Sequence[str] | None = None,
    warnings: Sequence[str] | None = None,
    created_by: str | None = None,
    notes: str | None = None,
) -> ParserIntegrationResult:
    """Return a consideration result that falls back to current parser behavior."""

    normalized_section = _normalize_optional_string_value(
        parser_section,
        "parser_section",
    )
    normalized_signal = _normalize_optional_string_value(signal_name, "signal_name")
    reasons = list(denied_reasons or ["fallback_to_current_parser"])
    warning_list = list(warnings or [])
    return ParserIntegrationResult(
        result_id=create_parser_integration_result_id(
            normalized_section,
            normalized_signal,
            "current_parser",
        ),
        parser_section=normalized_section,
        signal_name=normalized_signal,
        parser_evolution_id=None,
        parser_backlog_id=None,
        proposed_parser_change_type=None,
        parser_runtime_authoritative=True,
        selected_parser_action="keep_current_parser",
        selected_parser_source="current_parser",
        parser_change_summary=(
            "No parser backlog or evolution selected; current parser retained."
        ),
        gate_allowed_for_consideration=False,
        fallback_to_current_parser=True,
        fallback_reason="; ".join(_unique_strings(reasons)),
        phase4i_contract_preserved=True,
        awr_regression_required=True,
        scoring_regression_required=True,
        unknown_signal_safety_required=True,
        runtime_parser_applied=False,
        runtime_mutation_performed=False,
        runtime_active=False,
        runtime_influence_granted=False,
        validation_reference=None,
        rollback_reference=None,
        awr_regression_reference=None,
        scoring_regression_reference=None,
        denied_reasons=_unique_strings(reasons),
        warnings=_unique_strings(warning_list),
        rationale=(
            "Current parser selected because adaptive parser integration was not "
            "allowed for runtime consideration."
        ),
        created_by=created_by,
        notes=notes,
    )


def normalize_parser_payload(
    value: Any,
    field_name: str = "parser_payload",
) -> dict[str, object]:
    """Normalize a parser evolution/backlog payload into a deterministic dictionary."""

    data = _object_to_mapping(value, field_name)
    if not data:
        raise AdaptiveParserAdapterError(f"{field_name} must be non-empty.")
    normalized: dict[str, object] = {}
    for key, child in sorted(data.items(), key=lambda item: str(item[0])):
        if not isinstance(key, str) or not key.strip():
            raise AdaptiveParserAdapterError(
                f"{field_name} keys must be non-empty strings."
            )
        normalized[key.strip()] = _normalize_payload_value(child)
    if not normalized:
        raise AdaptiveParserAdapterError(f"{field_name} must be non-empty.")
    return normalized


def _extract_parser_candidate(
    value: Any,
    field_name: str,
) -> tuple[dict[str, object] | None, dict[str, str | None], list[str], bool]:
    if value is None:
        return None, {}, [], False
    try:
        payload = normalize_parser_payload(value, field_name)
        invalid_reasons = _unsafe_parser_payload_reasons(payload, field_name)
        if invalid_reasons:
            return None, {}, invalid_reasons, True
        return payload, _parser_candidate_meta(payload), [], False
    except AdaptiveParserAdapterError:
        return None, {}, [f"{field_name} was invalid and ignored"], True


def _parser_candidate_meta(payload: Mapping[str, Any]) -> dict[str, str | None]:
    return {
        "backlog_id": _optional_text(payload.get("backlog_id")),
        "evolution_id": _optional_text(payload.get("evolution_id")),
        "source_evolution_id": _optional_text(payload.get("source_evolution_id")),
        "parser_section": _optional_text(payload.get("parser_section")),
        "signal_name": _optional_text(payload.get("signal_name")),
        "proposed_parser_change_type": _optional_text(
            payload.get("proposed_parser_change_type")
            or payload.get("parser_change_type")
            or payload.get("evolution_type")
        ),
    }


def _unsafe_parser_payload_reasons(
    payload: Mapping[str, Any],
    field_name: str,
) -> list[str]:
    reasons: list[str] = []
    if payload.get("runtime_active") is True:
        reasons.append(f"{field_name} cannot be runtime active")
    if payload.get("runtime_influence_granted") is True:
        reasons.append(f"{field_name} cannot grant runtime influence")
    for key in (
        "phase4i_contract_required",
        "awr_regression_required",
        "scoring_regression_required",
    ):
        if key in payload and payload[key] is not True:
            reasons.append(f"{field_name} must preserve {key}=true")
    return reasons


def _object_to_mapping(value: Any, field_name: str) -> dict[str, Any]:
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
    raise AdaptiveParserAdapterError(f"{field_name} must be a mapping or dataclass.")


def _normalize_payload_value(value: Any) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {
            str(key).strip(): _normalize_payload_value(child)
            for key, child in sorted(value.items(), key=lambda item: str(item[0]))
            if str(key).strip()
        }
    if isinstance(value, (list, tuple)):
        return [_normalize_payload_value(child) for child in value]
    if is_dataclass(value) and not isinstance(value, type):
        return _normalize_payload_value(asdict(value))
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _normalize_payload_value(value.to_dict())
    return str(value)


def _normalize_parser_source(value: Any) -> str:
    _require_non_empty_string(value, "selected_parser_source")
    normalized = str(value).strip().lower().replace("-", "_")
    if normalized not in PARSER_INTEGRATION_SOURCES:
        raise AdaptiveParserAdapterError(f"Unsupported parser source: {value}.")
    return normalized


def _normalize_parser_action(value: Any) -> str:
    _require_non_empty_string(value, "selected_parser_action")
    normalized = str(value).strip().lower().replace("-", "_")
    if normalized not in PARSER_INTEGRATION_ACTIONS:
        raise AdaptiveParserAdapterError(f"Unsupported parser action: {value}.")
    return normalized


def _fallback_reason(
    denied_reasons: list[str],
    warnings: list[str],
    gate_allowed: bool,
    selected_source: str,
) -> str | None:
    if selected_source != "current_parser" and gate_allowed and not denied_reasons:
        return None
    reasons = denied_reasons or warnings or ["fallback_to_current_parser"]
    return "; ".join(_unique_strings(reasons))


def _integration_rationale(
    selected_source: str,
    fallback: bool,
    gate_allowed: bool,
    denied_reasons: list[str],
) -> str:
    if fallback:
        reason = "; ".join(_unique_strings(denied_reasons))
        reason = reason or "current parser fallback required"
        return (
            "Current parser remains authoritative; adaptive parser changes were "
            f"not selected for consideration because {reason}."
        )
    if gate_allowed:
        return (
            f"{selected_source} selected for consideration only; current parser "
            "remains authoritative and no runtime parser change was applied."
        )
    return "Current parser remains authoritative."


def _change_summary(selected_source: str, fallback: bool) -> str:
    if fallback:
        return "No parser backlog or evolution selected; current parser retained."
    return (
        f"{selected_source} selected for parser consideration only; current parser "
        "behavior remains authoritative."
    )


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
        raise AdaptiveParserAdapterError(
            "Missing required fields: " + ", ".join(missing) + "."
        )
    return {
        field_name: deepcopy(data[field_name])
        if field_name in data
        else deepcopy(optional_defaults[field_name])
        for field_name in fields
    }


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
        raise AdaptiveParserAdapterError(f"{field_name} must be a list.")
    normalized = []
    for item in value:
        _require_non_empty_string(item, field_name)
        normalized.append(str(item).strip())
    return normalized


def _validate_bool(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise AdaptiveParserAdapterError(f"{field_name} must be a boolean.")


def _require_true(value: Any, field_name: str) -> None:
    if value is not True:
        raise AdaptiveParserAdapterError(
            f"Phase 7AA.5 parser adapter requires {field_name}=true."
        )


def _require_false(value: Any, field_name: str) -> None:
    if value is not False:
        raise AdaptiveParserAdapterError(
            f"Phase 7AA.5 parser adapter requires {field_name}=false."
        )


def _require_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise AdaptiveParserAdapterError(f"{field_name} must be a non-empty string.")


def _validate_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise AdaptiveParserAdapterError(f"{field_name} must be None or a string.")
    if isinstance(value, str) and not value.strip():
        raise AdaptiveParserAdapterError(f"{field_name} must not be blank.")


def _normalize_optional_string(value: str | None) -> str | None:
    return None if value is None else value.strip()


def _normalize_optional_string_value(value: Any, field_name: str) -> str | None:
    _validate_optional_string(value, field_name)
    return None if value is None else str(value).strip()


def _optional_text(value: Any) -> str | None:
    return str(value).strip() if _has_text(value) else None


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _identifier_fragment(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "UNSPECIFIED"
