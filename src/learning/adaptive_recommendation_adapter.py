"""Phase 7AA.4 controlled recommendation integration adapter.

This module evaluates supplied adaptive recommendation candidates against the
7AA.1 gate and 7AA.2 context, then returns an advisory result. It does not
replace runtime recommendations, mutate Phase 4I recommendations, call the
runtime recommendation engine, change scoring, change parser output, call
services, or write databases.
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


RECOMMENDATION_INTEGRATION_SOURCES = (
    "deterministic",
    "proposed_rule",
    "recommendation_evolution",
    "none",
)

RECOMMENDATION_INTEGRATION_STATUSES = (
    "FALLBACK_TO_DETERMINISTIC",
    "ADVISORY_SELECTED",
    "DENIED",
)

RECOMMENDATION_INTEGRATION_RESULT_FIELDS = (
    "result_id",
    "domain",
    "recommendation_id",
    "deterministic_recommendation",
    "deterministic_recommendation_authoritative",
    "proposed_recommendation",
    "proposed_rule_reference",
    "selected_advisory_recommendation",
    "selected_recommendation_source",
    "recommendation_change_summary",
    "evidence_mapping_summary",
    "gate_allowed_for_consideration",
    "fallback_to_deterministic",
    "fallback_reason",
    "phase4i_contract_preserved",
    "runtime_recommendation_applied",
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

_EVIDENCE_KEYS = (
    "evidence",
    "evidence_mapping",
    "evidence_mapping_summary",
    "evidence_reference",
    "evidence_references",
    "evidence_requirements",
    "evidence_refs",
    "source_evidence",
)


class AdaptiveRecommendationAdapterError(ValueError):
    """Raised when Phase 7AA.4 recommendation adapter rules are violated."""


@dataclass(frozen=True)
class RecommendationIntegrationResult:
    """Advisory recommendation integration result that never applies runtime output."""

    result_id: str
    domain: str | None
    recommendation_id: str | None
    deterministic_recommendation: dict[str, object]
    deterministic_recommendation_authoritative: bool
    proposed_recommendation: dict[str, object] | None
    proposed_rule_reference: str | None
    selected_advisory_recommendation: dict[str, object]
    selected_recommendation_source: str
    recommendation_change_summary: str
    evidence_mapping_summary: str
    gate_allowed_for_consideration: bool
    fallback_to_deterministic: bool
    fallback_reason: str | None
    phase4i_contract_preserved: bool
    runtime_recommendation_applied: bool
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
        domain = _normalize_optional_string_value(self.domain, "domain")
        recommendation_id = _normalize_optional_string_value(
            self.recommendation_id,
            "recommendation_id",
        )
        deterministic_recommendation = normalize_recommendation_payload(
            self.deterministic_recommendation,
            "deterministic_recommendation",
        )
        proposed_recommendation = (
            None
            if self.proposed_recommendation is None
            else normalize_recommendation_payload(
                self.proposed_recommendation,
                "proposed_recommendation",
            )
        )
        selected_recommendation = normalize_recommendation_payload(
            self.selected_advisory_recommendation,
            "selected_advisory_recommendation",
        )
        selected_source = _normalize_recommendation_source(
            self.selected_recommendation_source
        )
        _require_non_empty_string(
            self.recommendation_change_summary,
            "recommendation_change_summary",
        )
        _require_non_empty_string(self.evidence_mapping_summary, "evidence_mapping_summary")
        _validate_bool(
            self.gate_allowed_for_consideration,
            "gate_allowed_for_consideration",
        )
        _validate_bool(self.fallback_to_deterministic, "fallback_to_deterministic")
        _require_true(
            self.deterministic_recommendation_authoritative,
            "deterministic_recommendation_authoritative",
        )
        _require_true(self.phase4i_contract_preserved, "phase4i_contract_preserved")
        _require_false(
            self.runtime_recommendation_applied,
            "runtime_recommendation_applied",
        )
        _require_false(self.runtime_mutation_performed, "runtime_mutation_performed")
        _require_false(self.runtime_active, "runtime_active")
        _require_false(self.runtime_influence_granted, "runtime_influence_granted")
        _validate_optional_string(self.proposed_rule_reference, "proposed_rule_reference")
        _validate_optional_string(self.fallback_reason, "fallback_reason")
        _validate_optional_string(self.validation_reference, "validation_reference")
        _validate_optional_string(self.rollback_reference, "rollback_reference")
        denied_reasons = _normalize_string_list(self.denied_reasons, "denied_reasons")
        warnings = _normalize_string_list(self.warnings, "warnings")
        _require_non_empty_string(self.rationale, "rationale")
        _validate_optional_string(self.created_by, "created_by")
        _validate_optional_string(self.notes, "notes")

        if (
            not self.gate_allowed_for_consideration
            and not self.fallback_to_deterministic
        ):
            raise AdaptiveRecommendationAdapterError(
                "fallback_to_deterministic must be true when gate consideration is denied."
            )
        if self.fallback_to_deterministic and selected_source != "deterministic":
            raise AdaptiveRecommendationAdapterError(
                "fallback results must select deterministic recommendation source."
            )
        if selected_source == "deterministic" and (
            selected_recommendation != deterministic_recommendation
        ):
            raise AdaptiveRecommendationAdapterError(
                "deterministic selected_advisory_recommendation must equal "
                "deterministic_recommendation."
            )
        if selected_source != "deterministic" and proposed_recommendation is None:
            raise AdaptiveRecommendationAdapterError(
                "adaptive advisory selections require proposed_recommendation."
            )

        object.__setattr__(self, "domain", domain)
        object.__setattr__(self, "recommendation_id", recommendation_id)
        object.__setattr__(
            self,
            "deterministic_recommendation",
            deterministic_recommendation,
        )
        object.__setattr__(self, "deterministic_recommendation_authoritative", True)
        object.__setattr__(
            self,
            "proposed_recommendation",
            proposed_recommendation,
        )
        object.__setattr__(
            self,
            "proposed_rule_reference",
            _normalize_optional_string(self.proposed_rule_reference),
        )
        object.__setattr__(
            self,
            "selected_advisory_recommendation",
            selected_recommendation,
        )
        object.__setattr__(self, "selected_recommendation_source", selected_source)
        object.__setattr__(
            self,
            "recommendation_change_summary",
            self.recommendation_change_summary.strip(),
        )
        object.__setattr__(
            self,
            "evidence_mapping_summary",
            self.evidence_mapping_summary.strip(),
        )
        object.__setattr__(self, "phase4i_contract_preserved", True)
        object.__setattr__(self, "runtime_recommendation_applied", False)
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


def create_recommendation_integration_result_id(
    domain: str | None,
    recommendation_id: str | None,
    source: str,
) -> str:
    """Create a deterministic recommendation integration result identifier."""

    normalized_source = _normalize_recommendation_source(source)
    return (
        "ADAPTIVE-RECOMMENDATION-RESULT-"
        f"{_identifier_fragment(domain or 'NO-DOMAIN')}-"
        f"{_identifier_fragment(recommendation_id or 'NO-RECOMMENDATION')}-"
        f"{_identifier_fragment(normalized_source)}"
    )


def evaluate_recommendation_integration(
    *,
    deterministic_recommendation: Any,
    recommendation_id: str | None = None,
    domain: str | None = None,
    adaptive_runtime_context: AdaptiveRuntimeContext | Mapping[str, Any] | None = None,
    gate_result: AdaptiveRuntimeGateResult | Mapping[str, Any] | None = None,
    recommendation_rule_evolution: Any = None,
    proposed_recommendation_rule: Any = None,
    evidence_reference: str | None = None,
    validation_reference: str | None = None,
    rollback_reference: str | None = None,
    created_by: str | None = None,
    notes: str | None = None,
) -> RecommendationIntegrationResult:
    """Evaluate adaptive recommendation candidates as advisory-only context."""

    baseline_recommendation = normalize_recommendation_payload(
        deterministic_recommendation,
        "deterministic_recommendation",
    )
    normalized_domain = _normalize_optional_string_value(domain, "domain")
    normalized_recommendation_id = _normalize_optional_string_value(
        recommendation_id,
        "recommendation_id",
    )
    denied_reasons: list[str] = []
    warnings: list[str] = []

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
        denied_reasons.append("recommendation_gate_result_required")
    else:
        normalized_gate = validate_gate_result(gate_result)
        gate_dict = gate_result_to_dict(normalized_gate)
        if normalized_gate.component_type != "recommendation":
            denied_reasons.append("recommendation_gate_result_required")
        if not normalized_gate.allowed_for_consideration:
            denied_reasons.append("gate_denied_consideration")
        denied_reasons.extend(_string_items(gate_dict.get("denied_reasons", [])))
        warnings.extend(_string_items(gate_dict.get("warnings", [])))

    if not _has_text(validation_reference):
        denied_reasons.append("validation_reference_required")
    if not _has_text(rollback_reference):
        denied_reasons.append("rollback_reference_required")

    proposed_payload, proposed_reference, proposed_warnings = _extract_advisory_payload(
        proposed_recommendation_rule,
        "proposed_recommendation_rule",
    )
    evolution_payload, evolution_reference, evolution_warnings = _extract_advisory_payload(
        recommendation_rule_evolution,
        "recommendation_rule_evolution",
    )
    warnings.extend(proposed_warnings)
    warnings.extend(evolution_warnings)

    gate_allowed = (
        normalized_gate is not None
        and normalized_gate.allowed_for_consideration
        and normalized_gate.component_type == "recommendation"
        and not denied_reasons
    )
    selected_recommendation, selected_source, selection_warnings = (
        choose_advisory_recommendation(
            baseline_recommendation,
            proposed_rule=proposed_payload,
            recommendation_evolution=evolution_payload,
            gate_allowed=gate_allowed,
        )
    )
    warnings.extend(selection_warnings)
    fallback = selected_source == "deterministic" or not gate_allowed
    if fallback:
        selected_recommendation = baseline_recommendation
        selected_source = "deterministic"

    source_payload = (
        proposed_recommendation_rule
        if selected_source == "proposed_rule"
        else recommendation_rule_evolution
        if selected_source == "recommendation_evolution"
        else None
    )
    if selected_source != "deterministic":
        if not _has_any_evidence_mapping(source_payload, selected_recommendation):
            warnings.append("proposed recommendation lacks evidence mapping")
        if not _has_text(evidence_reference):
            warnings.append(
                "evidence reference missing for adaptive recommendation consideration"
            )

    proposed_recommendation = (
        deepcopy(selected_recommendation) if selected_source != "deterministic" else None
    )
    proposed_rule_reference = (
        proposed_reference
        if selected_source == "proposed_rule"
        else evolution_reference
        if selected_source == "recommendation_evolution"
        else None
    )
    fallback_reason = _fallback_reason(
        denied_reasons,
        warnings,
        gate_allowed,
        selected_source,
    )
    rationale = _integration_rationale(
        selected_source,
        fallback,
        gate_allowed,
        denied_reasons,
    )
    return RecommendationIntegrationResult(
        result_id=create_recommendation_integration_result_id(
            normalized_domain,
            normalized_recommendation_id,
            selected_source,
        ),
        domain=normalized_domain,
        recommendation_id=normalized_recommendation_id,
        deterministic_recommendation=baseline_recommendation,
        deterministic_recommendation_authoritative=True,
        proposed_recommendation=proposed_recommendation,
        proposed_rule_reference=proposed_rule_reference,
        selected_advisory_recommendation=selected_recommendation,
        selected_recommendation_source=selected_source,
        recommendation_change_summary=_change_summary(selected_source, fallback),
        evidence_mapping_summary=_evidence_mapping_summary(
            source_payload,
            selected_recommendation,
            evidence_reference,
        ),
        gate_allowed_for_consideration=gate_allowed,
        fallback_to_deterministic=fallback,
        fallback_reason=fallback_reason,
        phase4i_contract_preserved=True,
        runtime_recommendation_applied=False,
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


def validate_recommendation_integration_result(
    result: RecommendationIntegrationResult | Mapping[str, Any],
) -> RecommendationIntegrationResult:
    """Validate and return a recommendation integration result."""

    if isinstance(result, Mapping):
        return recommendation_integration_result_from_dict(result)
    if not isinstance(result, RecommendationIntegrationResult):
        raise AdaptiveRecommendationAdapterError(
            "result must be RecommendationIntegrationResult."
        )
    return RecommendationIntegrationResult(**recommendation_integration_result_to_dict(result))


def recommendation_integration_result_to_dict(
    result: RecommendationIntegrationResult,
) -> dict[str, Any]:
    """Serialize a recommendation integration result to a deterministic dictionary."""

    if not isinstance(result, RecommendationIntegrationResult):
        raise AdaptiveRecommendationAdapterError(
            "result must be RecommendationIntegrationResult."
        )
    return {
        "result_id": result.result_id,
        "domain": result.domain,
        "recommendation_id": result.recommendation_id,
        "deterministic_recommendation": deepcopy(result.deterministic_recommendation),
        "deterministic_recommendation_authoritative": (
            result.deterministic_recommendation_authoritative
        ),
        "proposed_recommendation": deepcopy(result.proposed_recommendation),
        "proposed_rule_reference": result.proposed_rule_reference,
        "selected_advisory_recommendation": deepcopy(
            result.selected_advisory_recommendation
        ),
        "selected_recommendation_source": result.selected_recommendation_source,
        "recommendation_change_summary": result.recommendation_change_summary,
        "evidence_mapping_summary": result.evidence_mapping_summary,
        "gate_allowed_for_consideration": result.gate_allowed_for_consideration,
        "fallback_to_deterministic": result.fallback_to_deterministic,
        "fallback_reason": result.fallback_reason,
        "phase4i_contract_preserved": result.phase4i_contract_preserved,
        "runtime_recommendation_applied": result.runtime_recommendation_applied,
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


def recommendation_integration_result_from_dict(
    data: Mapping[str, Any],
) -> RecommendationIntegrationResult:
    """Reconstruct and validate a recommendation result from dictionary data."""

    if not isinstance(data, Mapping):
        raise AdaptiveRecommendationAdapterError(
            "recommendation integration result data must be a mapping."
        )
    values = _values_from_mapping(
        data,
        RECOMMENDATION_INTEGRATION_RESULT_FIELDS,
        optional_defaults={
            "domain": None,
            "recommendation_id": None,
            "deterministic_recommendation_authoritative": True,
            "proposed_recommendation": None,
            "proposed_rule_reference": None,
            "gate_allowed_for_consideration": False,
            "fallback_to_deterministic": True,
            "fallback_reason": None,
            "phase4i_contract_preserved": True,
            "runtime_recommendation_applied": False,
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
    return RecommendationIntegrationResult(**values)


def choose_advisory_recommendation(
    deterministic_recommendation: Any,
    proposed_rule: Any = None,
    recommendation_evolution: Any = None,
    gate_allowed: bool = False,
) -> tuple[dict[str, object], str, list[str]]:
    """Choose an advisory recommendation deterministically without applying it."""

    baseline = normalize_recommendation_payload(
        deterministic_recommendation,
        "deterministic_recommendation",
    )
    _validate_bool(gate_allowed, "gate_allowed")
    if not gate_allowed:
        return baseline, "deterministic", [
            "gate did not allow recommendation consideration"
        ]

    candidates = (
        ("proposed_rule", proposed_rule),
        ("recommendation_evolution", recommendation_evolution),
    )
    for source, value in candidates:
        if value is None:
            continue
        try:
            return normalize_recommendation_payload(value, source), source, []
        except AdaptiveRecommendationAdapterError:
            return (
                baseline,
                "deterministic",
                [
                    f"{source} recommendation was invalid; "
                    "fell back to deterministic recommendation"
                ],
            )
    return baseline, "deterministic", ["no valid adaptive recommendation was supplied"]


def fallback_recommendation_result(
    domain: str | None,
    recommendation_id: str | None,
    deterministic_recommendation: Any,
    denied_reasons: Sequence[str] | None = None,
    warnings: Sequence[str] | None = None,
    created_by: str | None = None,
    notes: str | None = None,
) -> RecommendationIntegrationResult:
    """Return an advisory result that falls back to deterministic recommendations."""

    baseline = normalize_recommendation_payload(
        deterministic_recommendation,
        "deterministic_recommendation",
    )
    normalized_domain = _normalize_optional_string_value(domain, "domain")
    normalized_recommendation_id = _normalize_optional_string_value(
        recommendation_id,
        "recommendation_id",
    )
    reasons = list(denied_reasons or ["fallback_to_deterministic"])
    warning_list = list(warnings or [])
    return RecommendationIntegrationResult(
        result_id=create_recommendation_integration_result_id(
            normalized_domain,
            normalized_recommendation_id,
            "deterministic",
        ),
        domain=normalized_domain,
        recommendation_id=normalized_recommendation_id,
        deterministic_recommendation=baseline,
        deterministic_recommendation_authoritative=True,
        proposed_recommendation=None,
        proposed_rule_reference=None,
        selected_advisory_recommendation=baseline,
        selected_recommendation_source="deterministic",
        recommendation_change_summary=(
            "No adaptive recommendation selected; deterministic recommendation retained."
        ),
        evidence_mapping_summary=(
            "Deterministic recommendation retained; adaptive evidence mapping "
            "was not applied."
        ),
        gate_allowed_for_consideration=False,
        fallback_to_deterministic=True,
        fallback_reason="; ".join(_unique_strings(reasons)),
        phase4i_contract_preserved=True,
        runtime_recommendation_applied=False,
        runtime_mutation_performed=False,
        runtime_active=False,
        runtime_influence_granted=False,
        validation_reference=None,
        rollback_reference=None,
        denied_reasons=_unique_strings(reasons),
        warnings=_unique_strings(warning_list),
        rationale=(
            "Deterministic recommendation selected because adaptive recommendations "
            "were not allowed for runtime consideration."
        ),
        created_by=created_by,
        notes=notes,
    )


def normalize_recommendation_payload(
    value: Any,
    field_name: str = "recommendation",
) -> dict[str, object]:
    """Normalize a recommendation-like payload into a deterministic dictionary."""

    data = _object_to_mapping(value, field_name)
    if not data:
        raise AdaptiveRecommendationAdapterError(f"{field_name} must be non-empty.")
    normalized: dict[str, object] = {}
    for key, child in sorted(data.items(), key=lambda item: str(item[0])):
        if not isinstance(key, str) or not key.strip():
            raise AdaptiveRecommendationAdapterError(
                f"{field_name} keys must be non-empty strings."
            )
        normalized[key.strip()] = _normalize_payload_value(child)
    if not normalized:
        raise AdaptiveRecommendationAdapterError(f"{field_name} must be non-empty.")
    return normalized


def _extract_advisory_payload(
    value: Any,
    field_name: str,
) -> tuple[dict[str, object] | None, str | None, list[str]]:
    if value is None:
        return None, None, []
    try:
        data = normalize_recommendation_payload(value, field_name)
        payload = _payload_from_advisory_data(data)
        reference = _reference_from_advisory_data(data)
        return payload, reference, []
    except AdaptiveRecommendationAdapterError:
        return None, None, [f"{field_name} was invalid and ignored"]


def _payload_from_advisory_data(data: Mapping[str, Any]) -> dict[str, object]:
    for key in (
        "selected_advisory_recommendation",
        "proposed_recommendation",
        "recommendation",
        "rule_payload",
        "proposed_rule",
    ):
        child = data.get(key)
        if isinstance(child, Mapping) and child:
            return normalize_recommendation_payload(child, key)
    return normalize_recommendation_payload(data, "advisory_recommendation")


def _reference_from_advisory_data(data: Mapping[str, Any]) -> str | None:
    for key in (
        "proposed_rule_reference",
        "rule_id",
        "source_evolution_id",
        "evolution_id",
        "recommendation_id",
        "id",
    ):
        value = data.get(key)
        if _has_text(value):
            return str(value).strip()
    return None


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
    raise AdaptiveRecommendationAdapterError(
        f"{field_name} must be a mapping or dataclass."
    )


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


def _normalize_recommendation_source(value: Any) -> str:
    _require_non_empty_string(value, "selected_recommendation_source")
    normalized = str(value).strip().lower().replace("-", "_")
    if normalized not in RECOMMENDATION_INTEGRATION_SOURCES:
        raise AdaptiveRecommendationAdapterError(
            f"Unsupported recommendation source: {value}."
        )
    return normalized


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
        reason = "; ".join(_unique_strings(denied_reasons))
        reason = reason or "deterministic recommendation fallback required"
        return (
            "Deterministic recommendations remain authoritative; adaptive "
            "recommendations were not selected for advisory consideration "
            f"because {reason}."
        )
    if gate_allowed:
        return (
            f"{selected_source} recommendation selected for advisory consideration "
            "only; deterministic recommendations remain authoritative and no "
            "runtime recommendation was applied."
        )
    return "Deterministic recommendations remain authoritative."


def _change_summary(selected_source: str, fallback: bool) -> str:
    if fallback:
        return "No adaptive recommendation selected; deterministic recommendation retained."
    return (
        f"{selected_source} selected as advisory recommendation only; deterministic "
        "recommendation output remains authoritative."
    )


def _evidence_mapping_summary(
    source_payload: Any,
    selected_recommendation: Mapping[str, Any],
    evidence_reference: str | None,
) -> str:
    details: list[str] = []
    if _has_text(evidence_reference):
        details.append(f"evidence_reference={str(evidence_reference).strip()}")
    evidence_keys = _evidence_keys(source_payload)
    evidence_keys.extend(_evidence_keys(selected_recommendation))
    if evidence_keys:
        details.append("evidence_mapping_keys=" + ",".join(_unique_strings(evidence_keys)))
    if details:
        return "; ".join(details)
    return "No evidence mapping supplied; deterministic recommendation remains authoritative."


def _has_any_evidence_mapping(source_payload: Any, selected_recommendation: Any) -> bool:
    return bool(_evidence_keys(source_payload) or _evidence_keys(selected_recommendation))


def _evidence_keys(value: Any) -> list[str]:
    try:
        data = _object_to_mapping(value, "evidence_payload")
    except AdaptiveRecommendationAdapterError:
        return []
    keys: list[str] = []
    for key, child in data.items():
        key_text = str(key).strip()
        if key_text in _EVIDENCE_KEYS and _has_evidence_value(child):
            keys.append(key_text)
        if isinstance(child, Mapping):
            keys.extend(_evidence_keys(child))
        elif isinstance(child, list):
            for item in child:
                keys.extend(_evidence_keys(item))
    return _unique_strings(keys)


def _has_evidence_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, Mapping)):
        return bool(value)
    return True


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
        raise AdaptiveRecommendationAdapterError(
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
        raise AdaptiveRecommendationAdapterError(f"{field_name} must be a list.")
    normalized = []
    for item in value:
        _require_non_empty_string(item, field_name)
        normalized.append(str(item).strip())
    return normalized


def _validate_bool(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise AdaptiveRecommendationAdapterError(f"{field_name} must be a boolean.")


def _require_true(value: Any, field_name: str) -> None:
    if value is not True:
        raise AdaptiveRecommendationAdapterError(
            f"Phase 7AA.4 recommendation adapter requires {field_name}=true."
        )


def _require_false(value: Any, field_name: str) -> None:
    if value is not False:
        raise AdaptiveRecommendationAdapterError(
            f"Phase 7AA.4 recommendation adapter requires {field_name}=false."
        )


def _require_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise AdaptiveRecommendationAdapterError(
            f"{field_name} must be a non-empty string."
        )


def _validate_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise AdaptiveRecommendationAdapterError(f"{field_name} must be None or a string.")
    if isinstance(value, str) and not value.strip():
        raise AdaptiveRecommendationAdapterError(f"{field_name} must not be blank.")


def _normalize_optional_string(value: str | None) -> str | None:
    return None if value is None else value.strip()


def _normalize_optional_string_value(value: Any, field_name: str) -> str | None:
    _validate_optional_string(value, field_name)
    return None if value is None else str(value).strip()


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _identifier_fragment(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "UNSPECIFIED"
