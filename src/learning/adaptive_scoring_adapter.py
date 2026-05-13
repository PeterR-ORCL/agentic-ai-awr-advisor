"""Phase 7AA.3 controlled scoring integration adapter.

This module evaluates supplied adaptive scoring candidates against the 7AA.1
gate and 7AA.2 context, then returns an advisory result. It does not replace
runtime scoring, mutate Phase 4I scores, call the runtime scoring engine,
change parser output, change decisions, change recommendations, call services,
or write databases.
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


SCORING_INTEGRATION_SCORE_SOURCES = (
    "deterministic",
    "trend_aware",
    "shadow_ml",
    "proposed_scoring_config",
    "none",
)

SCORING_INTEGRATION_STATUSES = (
    "FALLBACK_TO_DETERMINISTIC",
    "ADVISORY_SELECTED",
    "DENIED",
)

SCORING_INTEGRATION_RESULT_FIELDS = (
    "result_id",
    "domain",
    "deterministic_score",
    "deterministic_score_authoritative",
    "trend_aware_score",
    "shadow_ml_score",
    "proposed_score",
    "selected_advisory_score",
    "selected_score_source",
    "score_delta_from_deterministic",
    "gate_allowed_for_consideration",
    "fallback_to_deterministic",
    "fallback_reason",
    "phase4i_contract_preserved",
    "runtime_score_applied",
    "runtime_mutation_performed",
    "runtime_active",
    "runtime_influence_granted",
    "validation_reference",
    "rollback_reference",
    "denied_reasons",
    "warnings",
    "rationale",
    "created_by",
    "notes",
)


class AdaptiveScoringAdapterError(ValueError):
    """Raised when Phase 7AA.3 scoring adapter rules are violated."""


@dataclass(frozen=True)
class ScoringIntegrationResult:
    """Advisory scoring integration result that never applies runtime scoring."""

    result_id: str
    domain: str
    deterministic_score: float
    deterministic_score_authoritative: bool
    trend_aware_score: float | None
    shadow_ml_score: float | None
    proposed_score: float | None
    selected_advisory_score: float
    selected_score_source: str
    score_delta_from_deterministic: float
    gate_allowed_for_consideration: bool
    fallback_to_deterministic: bool
    fallback_reason: str | None
    phase4i_contract_preserved: bool
    runtime_score_applied: bool
    runtime_mutation_performed: bool
    runtime_active: bool
    runtime_influence_granted: bool
    validation_reference: str | None
    rollback_reference: str | None
    denied_reasons: list[str]
    warnings: list[str]
    rationale: str
    created_by: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.result_id, "result_id")
        domain = _normalize_domain(self.domain)
        deterministic_score = normalize_score(
            self.deterministic_score,
            "deterministic_score",
        )
        trend_aware_score = _normalize_optional_score(
            self.trend_aware_score,
            "trend_aware_score",
        )
        shadow_ml_score = _normalize_optional_score(
            self.shadow_ml_score,
            "shadow_ml_score",
        )
        proposed_score = _normalize_optional_score(self.proposed_score, "proposed_score")
        selected_score = normalize_score(
            self.selected_advisory_score,
            "selected_advisory_score",
        )
        selected_source = _normalize_score_source(self.selected_score_source)
        expected_delta = _round_score(selected_score - deterministic_score)
        score_delta = _round_score(
            normalize_score(
                self.score_delta_from_deterministic + deterministic_score,
                "score_delta_from_deterministic_baseline_check",
            )
            - deterministic_score
        )
        if score_delta != expected_delta:
            raise AdaptiveScoringAdapterError(
                "score_delta_from_deterministic must equal selected_advisory_score "
                "minus deterministic_score."
            )
        _validate_bool(
            self.gate_allowed_for_consideration,
            "gate_allowed_for_consideration",
        )
        _validate_bool(self.fallback_to_deterministic, "fallback_to_deterministic")
        _require_true(
            self.deterministic_score_authoritative,
            "deterministic_score_authoritative",
        )
        _require_true(self.phase4i_contract_preserved, "phase4i_contract_preserved")
        _require_false(self.runtime_score_applied, "runtime_score_applied")
        _require_false(self.runtime_mutation_performed, "runtime_mutation_performed")
        _require_false(self.runtime_active, "runtime_active")
        _require_false(self.runtime_influence_granted, "runtime_influence_granted")
        _validate_optional_string(self.fallback_reason, "fallback_reason")
        _validate_optional_string(self.validation_reference, "validation_reference")
        _validate_optional_string(self.rollback_reference, "rollback_reference")
        denied_reasons = _normalize_string_list(self.denied_reasons, "denied_reasons")
        warnings = _normalize_string_list(self.warnings, "warnings")
        _require_non_empty_string(self.rationale, "rationale")
        _validate_optional_string(self.created_by, "created_by")
        _validate_optional_string(self.notes, "notes")
        if not self.gate_allowed_for_consideration and not self.fallback_to_deterministic:
            raise AdaptiveScoringAdapterError(
                "fallback_to_deterministic must be true when gate consideration is denied."
            )
        if self.fallback_to_deterministic and selected_source != "deterministic":
            raise AdaptiveScoringAdapterError(
                "fallback results must select deterministic score source."
            )
        if selected_source == "deterministic" and selected_score != deterministic_score:
            raise AdaptiveScoringAdapterError(
                "deterministic selected_advisory_score must equal deterministic_score."
            )

        object.__setattr__(self, "domain", domain)
        object.__setattr__(self, "deterministic_score", deterministic_score)
        object.__setattr__(self, "deterministic_score_authoritative", True)
        object.__setattr__(self, "trend_aware_score", trend_aware_score)
        object.__setattr__(self, "shadow_ml_score", shadow_ml_score)
        object.__setattr__(self, "proposed_score", proposed_score)
        object.__setattr__(self, "selected_advisory_score", selected_score)
        object.__setattr__(self, "selected_score_source", selected_source)
        object.__setattr__(
            self,
            "score_delta_from_deterministic",
            expected_delta,
        )
        object.__setattr__(self, "phase4i_contract_preserved", True)
        object.__setattr__(self, "runtime_score_applied", False)
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
        object.__setattr__(self, "denied_reasons", denied_reasons)
        object.__setattr__(self, "warnings", warnings)
        object.__setattr__(self, "rationale", self.rationale.strip())
        object.__setattr__(
            self,
            "created_by",
            _normalize_optional_string(self.created_by),
        )
        object.__setattr__(self, "notes", _normalize_optional_string(self.notes))


def create_scoring_integration_result_id(
    domain: str,
    score_source: str,
    deterministic_score: float,
) -> str:
    """Create a deterministic scoring integration result identifier."""

    normalized_domain = _normalize_domain(domain)
    normalized_source = _normalize_score_source(score_source)
    score = normalize_score(deterministic_score, "deterministic_score")
    return (
        f"ADAPTIVE-SCORING-RESULT-{_identifier_fragment(normalized_domain)}-"
        f"{_identifier_fragment(normalized_source)}-{_score_fragment(score)}"
    )


def evaluate_scoring_integration(
    *,
    domain: str,
    deterministic_score: Any,
    adaptive_runtime_context: AdaptiveRuntimeContext | Mapping[str, Any] | None = None,
    gate_result: AdaptiveRuntimeGateResult | Mapping[str, Any] | None = None,
    trend_aware_score_result: Any = None,
    shadow_ml_output: Any = None,
    proposed_scoring_config: Any = None,
    validation_reference: str | None = None,
    rollback_reference: str | None = None,
    created_by: str | None = None,
    notes: str | None = None,
) -> ScoringIntegrationResult:
    """Evaluate adaptive scoring candidates as advisory-only context."""

    normalized_domain = _normalize_domain(domain)
    baseline_score = normalize_score(deterministic_score, "deterministic_score")
    denied_reasons: list[str] = []
    warnings: list[str] = []

    context = None
    if adaptive_runtime_context is None:
        denied_reasons.append("adaptive_runtime_context_required")
    else:
        context = validate_adaptive_runtime_context(adaptive_runtime_context)
        if not context.deterministic_runtime_authoritative:
            denied_reasons.append("deterministic_runtime_authority_required")
        if not context.fallback_to_deterministic:
            denied_reasons.append("fallback_to_deterministic_required")
        if not context.phase4i_contract_preserved:
            denied_reasons.append("phase4i_contract_preservation_required")
        if context.runtime_influence_applied:
            denied_reasons.append("context_runtime_influence_already_applied")
        if context.runtime_mutation_performed:
            denied_reasons.append("context_runtime_mutation_performed")

    normalized_gate = None
    if gate_result is None:
        denied_reasons.append("scoring_gate_result_required")
    else:
        normalized_gate = validate_gate_result(gate_result)
        gate_dict = gate_result_to_dict(normalized_gate)
        if normalized_gate.component_type != "scoring":
            denied_reasons.append("scoring_gate_result_required")
        if not normalized_gate.allowed_for_consideration:
            denied_reasons.append("gate_denied_consideration")
        denied_reasons.extend(_string_items(gate_dict.get("denied_reasons", [])))
        warnings.extend(_string_items(gate_dict.get("warnings", [])))

    if not _has_text(validation_reference):
        denied_reasons.append("validation_reference_required")
    if not _has_text(rollback_reference):
        denied_reasons.append("rollback_reference_required")

    trend_score, trend_warnings = _extract_optional_score(
        trend_aware_score_result,
        ("trend_aware_score", "score", "selected_advisory_score"),
        "trend_aware_score",
    )
    shadow_score, shadow_warnings = _extract_optional_score(
        shadow_ml_output,
        ("shadow_ml_score", "score", "selected_advisory_score"),
        "shadow_ml_score",
    )
    proposed_score, proposed_warnings = _extract_optional_score(
        proposed_scoring_config,
        ("proposed_score", "score", "selected_advisory_score"),
        "proposed_score",
    )
    warnings.extend(trend_warnings)
    warnings.extend(shadow_warnings)
    warnings.extend(proposed_warnings)

    gate_allowed = (
        normalized_gate is not None
        and normalized_gate.allowed_for_consideration
        and normalized_gate.component_type == "scoring"
        and not denied_reasons
    )
    selected_score, selected_source, selection_warnings = choose_advisory_score(
        baseline_score,
        trend_aware_score=trend_score,
        shadow_ml_score=shadow_score,
        proposed_score=proposed_score,
        gate_allowed=gate_allowed,
    )
    warnings.extend(selection_warnings)
    fallback = selected_source == "deterministic" or not gate_allowed
    if fallback:
        selected_score = baseline_score
        selected_source = "deterministic"
    fallback_reason = _fallback_reason(denied_reasons, warnings, gate_allowed, selected_source)
    rationale = _integration_rationale(
        selected_source,
        fallback,
        gate_allowed,
        denied_reasons,
    )
    return ScoringIntegrationResult(
        result_id=create_scoring_integration_result_id(
            normalized_domain,
            selected_source,
            baseline_score,
        ),
        domain=normalized_domain,
        deterministic_score=baseline_score,
        deterministic_score_authoritative=True,
        trend_aware_score=trend_score,
        shadow_ml_score=shadow_score,
        proposed_score=proposed_score,
        selected_advisory_score=selected_score,
        selected_score_source=selected_source,
        score_delta_from_deterministic=_round_score(selected_score - baseline_score),
        gate_allowed_for_consideration=gate_allowed,
        fallback_to_deterministic=fallback,
        fallback_reason=fallback_reason,
        phase4i_contract_preserved=True,
        runtime_score_applied=False,
        runtime_mutation_performed=False,
        runtime_active=False,
        runtime_influence_granted=False,
        validation_reference=validation_reference,
        rollback_reference=rollback_reference,
        denied_reasons=_unique_strings(denied_reasons),
        warnings=_unique_strings(warnings),
        rationale=rationale,
        created_by=created_by,
        notes=notes,
    )


def validate_scoring_integration_result(
    result: ScoringIntegrationResult | Mapping[str, Any],
) -> ScoringIntegrationResult:
    """Validate and return a scoring integration result."""

    if isinstance(result, Mapping):
        return scoring_integration_result_from_dict(result)
    if not isinstance(result, ScoringIntegrationResult):
        raise AdaptiveScoringAdapterError("result must be ScoringIntegrationResult.")
    return ScoringIntegrationResult(**scoring_integration_result_to_dict(result))


def scoring_integration_result_to_dict(
    result: ScoringIntegrationResult,
) -> dict[str, Any]:
    """Serialize a scoring integration result to a deterministic dictionary."""

    if not isinstance(result, ScoringIntegrationResult):
        raise AdaptiveScoringAdapterError("result must be ScoringIntegrationResult.")
    return {
        "result_id": result.result_id,
        "domain": result.domain,
        "deterministic_score": result.deterministic_score,
        "deterministic_score_authoritative": result.deterministic_score_authoritative,
        "trend_aware_score": result.trend_aware_score,
        "shadow_ml_score": result.shadow_ml_score,
        "proposed_score": result.proposed_score,
        "selected_advisory_score": result.selected_advisory_score,
        "selected_score_source": result.selected_score_source,
        "score_delta_from_deterministic": result.score_delta_from_deterministic,
        "gate_allowed_for_consideration": result.gate_allowed_for_consideration,
        "fallback_to_deterministic": result.fallback_to_deterministic,
        "fallback_reason": result.fallback_reason,
        "phase4i_contract_preserved": result.phase4i_contract_preserved,
        "runtime_score_applied": result.runtime_score_applied,
        "runtime_mutation_performed": result.runtime_mutation_performed,
        "runtime_active": result.runtime_active,
        "runtime_influence_granted": result.runtime_influence_granted,
        "validation_reference": result.validation_reference,
        "rollback_reference": result.rollback_reference,
        "denied_reasons": deepcopy(result.denied_reasons),
        "warnings": deepcopy(result.warnings),
        "rationale": result.rationale,
        "created_by": result.created_by,
        "notes": result.notes,
    }


def scoring_integration_result_from_dict(
    data: Mapping[str, Any],
) -> ScoringIntegrationResult:
    """Reconstruct and validate a scoring integration result from dictionary data."""

    if not isinstance(data, Mapping):
        raise AdaptiveScoringAdapterError("scoring integration result data must be a mapping.")
    values = _values_from_mapping(
        data,
        SCORING_INTEGRATION_RESULT_FIELDS,
        optional_defaults={
            "deterministic_score_authoritative": True,
            "trend_aware_score": None,
            "shadow_ml_score": None,
            "proposed_score": None,
            "gate_allowed_for_consideration": False,
            "fallback_to_deterministic": True,
            "fallback_reason": None,
            "phase4i_contract_preserved": True,
            "runtime_score_applied": False,
            "runtime_mutation_performed": False,
            "runtime_active": False,
            "runtime_influence_granted": False,
            "validation_reference": None,
            "rollback_reference": None,
            "denied_reasons": [],
            "warnings": [],
            "created_by": None,
            "notes": None,
        },
    )
    return ScoringIntegrationResult(**values)


def normalize_score(value: Any, field_name: str = "score") -> float:
    """Normalize a score-like value on the 0.0 to 100.0 score scale."""

    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise AdaptiveScoringAdapterError(f"{field_name} must be numeric.")
    score = float(value)
    if score < 0.0 or score > 100.0:
        raise AdaptiveScoringAdapterError(f"{field_name} must be between 0.0 and 100.0.")
    return _round_score(score)


def choose_advisory_score(
    deterministic_score: Any,
    trend_aware_score: Any = None,
    shadow_ml_score: Any = None,
    proposed_score: Any = None,
    gate_allowed: bool = False,
) -> tuple[float, str, list[str]]:
    """Choose an advisory score deterministically without applying it."""

    baseline_score = normalize_score(deterministic_score, "deterministic_score")
    _validate_bool(gate_allowed, "gate_allowed")
    if not gate_allowed:
        return baseline_score, "deterministic", ["gate did not allow scoring consideration"]
    candidates = (
        ("proposed_scoring_config", proposed_score),
        ("shadow_ml", shadow_ml_score),
        ("trend_aware", trend_aware_score),
    )
    for source, value in candidates:
        if value is None:
            continue
        try:
            return normalize_score(value, source), source, []
        except AdaptiveScoringAdapterError:
            return (
                baseline_score,
                "deterministic",
                [f"{source} score was invalid; fell back to deterministic score"],
            )
    return baseline_score, "deterministic", ["no valid adaptive score was supplied"]


def fallback_scoring_result(
    domain: str,
    deterministic_score: Any,
    denied_reasons: Sequence[str] | None = None,
    warnings: Sequence[str] | None = None,
    created_by: str | None = None,
    notes: str | None = None,
) -> ScoringIntegrationResult:
    """Return an advisory result that falls back to deterministic scoring."""

    normalized_domain = _normalize_domain(domain)
    baseline_score = normalize_score(deterministic_score, "deterministic_score")
    reasons = list(denied_reasons or ["fallback_to_deterministic"])
    warning_list = list(warnings or [])
    return ScoringIntegrationResult(
        result_id=create_scoring_integration_result_id(
            normalized_domain,
            "deterministic",
            baseline_score,
        ),
        domain=normalized_domain,
        deterministic_score=baseline_score,
        deterministic_score_authoritative=True,
        trend_aware_score=None,
        shadow_ml_score=None,
        proposed_score=None,
        selected_advisory_score=baseline_score,
        selected_score_source="deterministic",
        score_delta_from_deterministic=0.0,
        gate_allowed_for_consideration=False,
        fallback_to_deterministic=True,
        fallback_reason="; ".join(_unique_strings(reasons)),
        phase4i_contract_preserved=True,
        runtime_score_applied=False,
        runtime_mutation_performed=False,
        runtime_active=False,
        runtime_influence_granted=False,
        validation_reference=None,
        rollback_reference=None,
        denied_reasons=_unique_strings(reasons),
        warnings=_unique_strings(warning_list),
        rationale=(
            "Deterministic score selected because adaptive scoring was not "
            "allowed for runtime consideration."
        ),
        created_by=created_by,
        notes=notes,
    )


def _extract_optional_score(
    value: Any,
    field_names: tuple[str, ...],
    field_name: str,
) -> tuple[float | None, list[str]]:
    if value is None:
        return None, []
    data = _object_to_mapping(value)
    for key in field_names:
        if key in data and data[key] is not None:
            try:
                return normalize_score(data[key], field_name), []
            except AdaptiveScoringAdapterError:
                return None, [f"{field_name} was invalid and ignored"]
    return None, [f"{field_name} input did not contain a score field"]


def _object_to_mapping(value: Any) -> dict[str, Any]:
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
    raise AdaptiveScoringAdapterError("scoring input must be a mapping or dataclass.")


def _normalize_optional_score(value: Any, field_name: str) -> float | None:
    return None if value is None else normalize_score(value, field_name)


def _normalize_score_source(value: Any) -> str:
    _require_non_empty_string(value, "selected_score_source")
    normalized = str(value).strip().lower().replace("-", "_")
    if normalized not in SCORING_INTEGRATION_SCORE_SOURCES:
        raise AdaptiveScoringAdapterError(f"Unsupported score source: {value}.")
    return normalized


def _normalize_domain(value: Any) -> str:
    _require_non_empty_string(value, "domain")
    return str(value).strip().upper()


def _fallback_reason(
    denied_reasons: list[str],
    warnings: list[str],
    gate_allowed: bool,
    selected_source: str,
) -> str | None:
    if selected_source != "deterministic" and gate_allowed and not denied_reasons:
        return None
    reasons = denied_reasons or warnings or ["fallback_to_deterministic"]
    return "; ".join(_unique_strings(reasons))


def _integration_rationale(
    selected_source: str,
    fallback: bool,
    gate_allowed: bool,
    denied_reasons: list[str],
) -> str:
    if fallback:
        reason = "; ".join(_unique_strings(denied_reasons)) or "deterministic fallback required"
        return (
            "Deterministic score remains authoritative; adaptive scoring was "
            f"not selected for advisory consideration because {reason}."
        )
    if gate_allowed:
        return (
            f"{selected_source} score selected for advisory consideration only; "
            "deterministic score remains authoritative and no runtime score was applied."
        )
    return "Deterministic score remains authoritative."


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
        raise AdaptiveScoringAdapterError(
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
        raise AdaptiveScoringAdapterError(f"{field_name} must be a list.")
    normalized = []
    for item in value:
        _require_non_empty_string(item, field_name)
        normalized.append(str(item).strip())
    return normalized


def _validate_bool(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise AdaptiveScoringAdapterError(f"{field_name} must be a boolean.")


def _require_true(value: Any, field_name: str) -> None:
    if value is not True:
        raise AdaptiveScoringAdapterError(
            f"Phase 7AA.3 scoring adapter requires {field_name}=true."
        )


def _require_false(value: Any, field_name: str) -> None:
    if value is not False:
        raise AdaptiveScoringAdapterError(
            f"Phase 7AA.3 scoring adapter requires {field_name}=false."
        )


def _require_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise AdaptiveScoringAdapterError(f"{field_name} must be a non-empty string.")


def _validate_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise AdaptiveScoringAdapterError(f"{field_name} must be None or a string.")
    if isinstance(value, str) and not value.strip():
        raise AdaptiveScoringAdapterError(f"{field_name} must not be blank.")


def _normalize_optional_string(value: str | None) -> str | None:
    return None if value is None else value.strip()


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _round_score(value: float) -> float:
    return round(float(value), 6)


def _score_fragment(value: float) -> str:
    return f"{value:.2f}".replace(".", "-")


def _identifier_fragment(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "UNSPECIFIED"
