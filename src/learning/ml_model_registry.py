"""Phase 7Y local ML governance / model registry records.

This module records deterministic model governance metadata only. It does not
deploy models, load model files, save model files, train models, activate
runtime scoring, alter deterministic scoring, change decisions, change
recommendations, call services, or write databases.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence


MODEL_GOVERNANCE_STATUSES = (
    "PROPOSED",
    "REGISTERED",
    "TRAINED",
    "BACKTESTED",
    "EXPLAINED",
    "APPROVED_FOR_SHADOW",
    "APPROVED_FOR_RUNTIME_REVIEW",
    "REJECTED",
    "RETIRED",
    "CLOSED",
)

MODEL_DECISION_TYPES = (
    "register",
    "mark-trained",
    "mark-backtested",
    "attach-explainability",
    "approve-for-shadow",
    "request-runtime-review",
    "reject",
    "retire",
    "close",
)

MODEL_ELIGIBILITY_TYPES = (
    "shadow",
    "runtime_review",
)

MODEL_REGISTRY_FAMILIES = (
    "tree",
    "neural_net",
    "hybrid_rule_ml",
    "linear",
    "baseline_mock",
    "baseline_majority",
    "baseline_numeric_mean",
    "shadow_placeholder",
    "external_placeholder",
)

MODEL_REGISTRY_ENTRY_FIELDS = (
    "model_id",
    "model_family",
    "model_version",
    "model_name",
    "feature_schema_version",
    "label_schema_version",
    "training_dataset_id",
    "training_reference",
    "backtest_reference",
    "explainability_reference",
    "validation_metrics",
    "governance_status",
    "shadow_eligible",
    "runtime_eligibility_requested",
    "runtime_eligibility_granted",
    "runtime_active",
    "runtime_influence_granted",
    "rollback_reference",
    "retired",
    "created_by",
    "reviewed_by",
    "notes",
)

MODEL_GOVERNANCE_DECISION_FIELDS = (
    "decision_id",
    "model_id",
    "from_status",
    "to_status",
    "decision_type",
    "actor",
    "review_notes",
    "validation_reference",
    "runtime_eligibility_requested",
    "runtime_eligibility_granted",
    "runtime_active",
    "created_at",
)

MODEL_ELIGIBILITY_RECORD_FIELDS = (
    "eligibility_id",
    "model_id",
    "eligibility_type",
    "shadow_eligible",
    "runtime_eligible",
    "runtime_active",
    "runtime_influence_granted",
    "validation_reference",
    "rollback_reference",
    "notes",
)

_DECISION_STATUS_TRANSITIONS = {
    "register": "REGISTERED",
    "mark-trained": "TRAINED",
    "mark-backtested": "BACKTESTED",
    "attach-explainability": "EXPLAINED",
    "approve-for-shadow": "APPROVED_FOR_SHADOW",
    "request-runtime-review": "APPROVED_FOR_RUNTIME_REVIEW",
    "reject": "REJECTED",
    "retire": "RETIRED",
    "close": "CLOSED",
}

_SHADOW_ELIGIBLE_STATUSES = (
    "APPROVED_FOR_SHADOW",
    "APPROVED_FOR_RUNTIME_REVIEW",
)

_RETIRED_STATUSES = (
    "RETIRED",
    "CLOSED",
)


class MLModelRegistryError(ValueError):
    """Raised when Phase 7Y model registry governance rules are violated."""


@dataclass(frozen=True)
class MLModelRegistryEntry:
    """Serializable local model registry entry for governance state only."""

    model_id: str
    model_family: str
    model_version: str
    model_name: str
    feature_schema_version: str | None
    label_schema_version: str | None
    training_dataset_id: str | None
    training_reference: str | None
    backtest_reference: str | None
    explainability_reference: str | None
    validation_metrics: dict[str, float]
    governance_status: str
    shadow_eligible: bool
    runtime_eligibility_requested: bool
    runtime_eligibility_granted: bool
    runtime_active: bool
    runtime_influence_granted: bool
    rollback_reference: str | None
    retired: bool
    created_by: str | None
    reviewed_by: str | None
    notes: str | None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.model_id, "model_id")
        model_family = _normalize_model_family(self.model_family)
        _require_non_empty_string(self.model_version, "model_version")
        _require_non_empty_string(self.model_name, "model_name")
        _validate_optional_string(self.feature_schema_version, "feature_schema_version")
        _validate_optional_string(self.label_schema_version, "label_schema_version")
        _validate_optional_string(self.training_dataset_id, "training_dataset_id")
        _validate_optional_string(self.training_reference, "training_reference")
        _validate_optional_string(self.backtest_reference, "backtest_reference")
        _validate_optional_string(
            self.explainability_reference,
            "explainability_reference",
        )
        validation_metrics = _normalize_validation_metrics(self.validation_metrics)
        governance_status = _normalize_governance_status(self.governance_status)
        _validate_bool(self.shadow_eligible, "shadow_eligible")
        _validate_bool(
            self.runtime_eligibility_requested,
            "runtime_eligibility_requested",
        )
        _require_false(
            self.runtime_eligibility_granted,
            "runtime_eligibility_granted",
        )
        _require_false(self.runtime_active, "runtime_active")
        _require_false(self.runtime_influence_granted, "runtime_influence_granted")
        _validate_optional_string(self.rollback_reference, "rollback_reference")
        _validate_bool(self.retired, "retired")
        _validate_optional_string(self.created_by, "created_by")
        _validate_optional_string(self.reviewed_by, "reviewed_by")
        _validate_optional_string(self.notes, "notes")
        if self.shadow_eligible and governance_status not in _SHADOW_ELIGIBLE_STATUSES:
            raise MLModelRegistryError(
                "shadow_eligible=true requires APPROVED_FOR_SHADOW or "
                "APPROVED_FOR_RUNTIME_REVIEW governance status."
            )
        if self.retired and governance_status not in _RETIRED_STATUSES:
            raise MLModelRegistryError(
                "retired=true requires RETIRED or CLOSED governance status."
            )

        object.__setattr__(self, "model_id", self.model_id.strip())
        object.__setattr__(self, "model_family", model_family)
        object.__setattr__(self, "model_version", self.model_version.strip())
        object.__setattr__(self, "model_name", self.model_name.strip())
        object.__setattr__(
            self,
            "feature_schema_version",
            _normalize_optional_string(self.feature_schema_version),
        )
        object.__setattr__(
            self,
            "label_schema_version",
            _normalize_optional_string(self.label_schema_version),
        )
        object.__setattr__(
            self,
            "training_dataset_id",
            _normalize_optional_string(self.training_dataset_id),
        )
        object.__setattr__(
            self,
            "training_reference",
            _normalize_optional_string(self.training_reference),
        )
        object.__setattr__(
            self,
            "backtest_reference",
            _normalize_optional_string(self.backtest_reference),
        )
        object.__setattr__(
            self,
            "explainability_reference",
            _normalize_optional_string(self.explainability_reference),
        )
        object.__setattr__(self, "validation_metrics", validation_metrics)
        object.__setattr__(self, "governance_status", governance_status)
        object.__setattr__(self, "shadow_eligible", bool(self.shadow_eligible))
        object.__setattr__(
            self,
            "runtime_eligibility_requested",
            bool(self.runtime_eligibility_requested),
        )
        object.__setattr__(self, "runtime_eligibility_granted", False)
        object.__setattr__(self, "runtime_active", False)
        object.__setattr__(self, "runtime_influence_granted", False)
        object.__setattr__(
            self,
            "rollback_reference",
            _normalize_optional_string(self.rollback_reference),
        )
        object.__setattr__(self, "retired", bool(self.retired))
        object.__setattr__(
            self,
            "created_by",
            _normalize_optional_string(self.created_by),
        )
        object.__setattr__(
            self,
            "reviewed_by",
            _normalize_optional_string(self.reviewed_by),
        )
        object.__setattr__(self, "notes", _normalize_optional_string(self.notes))


@dataclass(frozen=True)
class MLModelGovernanceDecision:
    """Auditable model governance transition record."""

    decision_id: str
    model_id: str
    from_status: str
    to_status: str
    decision_type: str
    actor: str
    review_notes: str | None
    validation_reference: str | None
    runtime_eligibility_requested: bool
    runtime_eligibility_granted: bool
    runtime_active: bool
    created_at: str | None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.decision_id, "decision_id")
        _require_non_empty_string(self.model_id, "model_id")
        from_status = _normalize_governance_status(self.from_status)
        to_status = _normalize_governance_status(self.to_status)
        decision_type = _normalize_decision_type(self.decision_type)
        _require_non_empty_string(self.actor, "actor")
        _validate_optional_string(self.review_notes, "review_notes")
        _validate_optional_string(self.validation_reference, "validation_reference")
        _validate_bool(
            self.runtime_eligibility_requested,
            "runtime_eligibility_requested",
        )
        _require_false(
            self.runtime_eligibility_granted,
            "runtime_eligibility_granted",
        )
        _require_false(self.runtime_active, "runtime_active")
        _validate_optional_string(self.created_at, "created_at")
        expected_to_status = _DECISION_STATUS_TRANSITIONS[decision_type]
        if to_status != expected_to_status:
            raise MLModelRegistryError(
                "to_status must match the deterministic decision type transition."
            )
        expected_decision_id = create_governance_decision_id(
            self.model_id,
            decision_type,
            from_status,
            to_status,
        )
        if self.decision_id.strip() != expected_decision_id:
            raise MLModelRegistryError(
                "decision_id must match deterministic governance decision ID."
            )

        object.__setattr__(self, "decision_id", expected_decision_id)
        object.__setattr__(self, "model_id", self.model_id.strip())
        object.__setattr__(self, "from_status", from_status)
        object.__setattr__(self, "to_status", to_status)
        object.__setattr__(self, "decision_type", decision_type)
        object.__setattr__(self, "actor", self.actor.strip())
        object.__setattr__(
            self,
            "review_notes",
            _normalize_optional_string(self.review_notes),
        )
        object.__setattr__(
            self,
            "validation_reference",
            _normalize_optional_string(self.validation_reference),
        )
        object.__setattr__(
            self,
            "runtime_eligibility_requested",
            bool(self.runtime_eligibility_requested),
        )
        object.__setattr__(self, "runtime_eligibility_granted", False)
        object.__setattr__(self, "runtime_active", False)
        object.__setattr__(
            self,
            "created_at",
            _normalize_optional_string(self.created_at),
        )


@dataclass(frozen=True)
class MLModelEligibilityRecord:
    """Serializable eligibility record that never grants runtime activation."""

    eligibility_id: str
    model_id: str
    eligibility_type: str
    shadow_eligible: bool
    runtime_eligible: bool
    runtime_active: bool
    runtime_influence_granted: bool
    validation_reference: str | None
    rollback_reference: str | None
    notes: str | None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.eligibility_id, "eligibility_id")
        _require_non_empty_string(self.model_id, "model_id")
        eligibility_type = _normalize_eligibility_type(self.eligibility_type)
        _validate_bool(self.shadow_eligible, "shadow_eligible")
        _require_false(self.runtime_eligible, "runtime_eligible")
        _require_false(self.runtime_active, "runtime_active")
        _require_false(self.runtime_influence_granted, "runtime_influence_granted")
        _validate_optional_string(self.validation_reference, "validation_reference")
        _validate_optional_string(self.rollback_reference, "rollback_reference")
        _validate_optional_string(self.notes, "notes")
        expected_eligibility_id = create_eligibility_id(
            self.model_id,
            eligibility_type,
        )
        if self.eligibility_id.strip() != expected_eligibility_id:
            raise MLModelRegistryError(
                "eligibility_id must match deterministic eligibility ID."
            )

        object.__setattr__(self, "eligibility_id", expected_eligibility_id)
        object.__setattr__(self, "model_id", self.model_id.strip())
        object.__setattr__(self, "eligibility_type", eligibility_type)
        object.__setattr__(self, "shadow_eligible", bool(self.shadow_eligible))
        object.__setattr__(self, "runtime_eligible", False)
        object.__setattr__(self, "runtime_active", False)
        object.__setattr__(self, "runtime_influence_granted", False)
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
        object.__setattr__(self, "notes", _normalize_optional_string(self.notes))


def create_model_id(
    model_family: str,
    model_version: str,
    model_name: str | None = None,
) -> str:
    """Create a deterministic model registry identifier."""

    normalized_family = _normalize_model_family(model_family)
    _require_non_empty_string(model_version, "model_version")
    if model_name is not None:
        _validate_optional_string(model_name, "model_name")
    name_fragment = model_name if _has_text(model_name) else "unnamed-model"
    return (
        f"ML-MODEL-{_identifier_fragment(normalized_family)}-"
        f"{_identifier_fragment(model_version)}-"
        f"{_identifier_fragment(name_fragment)}"
    )


def create_model_registry_entry(
    model_family: str,
    model_version: str,
    model_name: str,
    feature_schema_version: str | None = None,
    label_schema_version: str | None = None,
    training_dataset_id: str | None = None,
    training_reference: str | None = None,
    backtest_reference: str | None = None,
    explainability_reference: str | None = None,
    validation_metrics: Mapping[str, Any] | None = None,
    created_by: str | None = None,
    notes: str | None = None,
) -> MLModelRegistryEntry:
    """Create a proposed local model registry entry."""

    model_id = create_model_id(model_family, model_version, model_name)
    return MLModelRegistryEntry(
        model_id=model_id,
        model_family=model_family,
        model_version=model_version,
        model_name=model_name,
        feature_schema_version=feature_schema_version,
        label_schema_version=label_schema_version,
        training_dataset_id=training_dataset_id,
        training_reference=training_reference,
        backtest_reference=backtest_reference,
        explainability_reference=explainability_reference,
        validation_metrics={} if validation_metrics is None else dict(validation_metrics),
        governance_status="PROPOSED",
        shadow_eligible=False,
        runtime_eligibility_requested=False,
        runtime_eligibility_granted=False,
        runtime_active=False,
        runtime_influence_granted=False,
        rollback_reference=None,
        retired=False,
        created_by=created_by,
        reviewed_by=None,
        notes=notes,
    )


def validate_model_registry_entry(
    entry: MLModelRegistryEntry | Mapping[str, Any],
) -> MLModelRegistryEntry:
    """Validate and return a registry entry."""

    if isinstance(entry, Mapping):
        return model_registry_entry_from_dict(entry)
    if not isinstance(entry, MLModelRegistryEntry):
        raise MLModelRegistryError("entry must be MLModelRegistryEntry.")
    return MLModelRegistryEntry(**model_registry_entry_to_dict(entry))


def create_governance_decision(
    entry: MLModelRegistryEntry | Mapping[str, Any],
    decision_type: str,
    actor: str,
    review_notes: str | None = None,
    validation_reference: str | None = None,
) -> tuple[MLModelRegistryEntry, MLModelGovernanceDecision]:
    """Create a governance transition without runtime activation."""

    current_entry = validate_model_registry_entry(entry)
    normalized_decision_type = _normalize_decision_type(decision_type)
    to_status = _DECISION_STATUS_TRANSITIONS[normalized_decision_type]
    from_status = current_entry.governance_status
    decision_id = create_governance_decision_id(
        current_entry.model_id,
        normalized_decision_type,
        from_status,
        to_status,
    )
    runtime_eligibility_requested = (
        current_entry.runtime_eligibility_requested
        or normalized_decision_type == "request-runtime-review"
    )
    decision = MLModelGovernanceDecision(
        decision_id=decision_id,
        model_id=current_entry.model_id,
        from_status=from_status,
        to_status=to_status,
        decision_type=normalized_decision_type,
        actor=actor,
        review_notes=review_notes,
        validation_reference=validation_reference,
        runtime_eligibility_requested=runtime_eligibility_requested,
        runtime_eligibility_granted=False,
        runtime_active=False,
        created_at=None,
    )
    updated_entry = MLModelRegistryEntry(
        model_id=current_entry.model_id,
        model_family=current_entry.model_family,
        model_version=current_entry.model_version,
        model_name=current_entry.model_name,
        feature_schema_version=current_entry.feature_schema_version,
        label_schema_version=current_entry.label_schema_version,
        training_dataset_id=current_entry.training_dataset_id,
        training_reference=current_entry.training_reference,
        backtest_reference=current_entry.backtest_reference,
        explainability_reference=current_entry.explainability_reference,
        validation_metrics=current_entry.validation_metrics,
        governance_status=to_status,
        shadow_eligible=to_status in _SHADOW_ELIGIBLE_STATUSES,
        runtime_eligibility_requested=runtime_eligibility_requested,
        runtime_eligibility_granted=False,
        runtime_active=False,
        runtime_influence_granted=False,
        rollback_reference=current_entry.rollback_reference,
        retired=to_status in _RETIRED_STATUSES,
        created_by=current_entry.created_by,
        reviewed_by=actor,
        notes=current_entry.notes,
    )
    return updated_entry, decision


def validate_governance_decision(
    decision: MLModelGovernanceDecision | Mapping[str, Any],
) -> MLModelGovernanceDecision:
    """Validate and return a governance decision."""

    if isinstance(decision, Mapping):
        return model_governance_decision_from_dict(decision)
    if not isinstance(decision, MLModelGovernanceDecision):
        raise MLModelRegistryError("decision must be MLModelGovernanceDecision.")
    return MLModelGovernanceDecision(**model_governance_decision_to_dict(decision))


def create_model_eligibility_record(
    entry: MLModelRegistryEntry | Mapping[str, Any],
    eligibility_type: str,
    validation_reference: str | None = None,
    rollback_reference: str | None = None,
    notes: str | None = None,
) -> MLModelEligibilityRecord:
    """Create a model eligibility record that never grants runtime eligibility."""

    current_entry = validate_model_registry_entry(entry)
    normalized_eligibility_type = _normalize_eligibility_type(eligibility_type)
    eligibility_id = create_eligibility_id(
        current_entry.model_id,
        normalized_eligibility_type,
    )
    shadow_eligible = (
        current_entry.shadow_eligible
        and current_entry.governance_status in _SHADOW_ELIGIBLE_STATUSES
    )
    return MLModelEligibilityRecord(
        eligibility_id=eligibility_id,
        model_id=current_entry.model_id,
        eligibility_type=normalized_eligibility_type,
        shadow_eligible=shadow_eligible,
        runtime_eligible=False,
        runtime_active=False,
        runtime_influence_granted=False,
        validation_reference=validation_reference,
        rollback_reference=rollback_reference,
        notes=notes,
    )


def validate_model_eligibility_record(
    record: MLModelEligibilityRecord | Mapping[str, Any],
) -> MLModelEligibilityRecord:
    """Validate and return an eligibility record."""

    if isinstance(record, Mapping):
        return model_eligibility_record_from_dict(record)
    if not isinstance(record, MLModelEligibilityRecord):
        raise MLModelRegistryError("record must be MLModelEligibilityRecord.")
    return MLModelEligibilityRecord(**model_eligibility_record_to_dict(record))


def model_registry_entry_to_dict(entry: MLModelRegistryEntry) -> dict[str, Any]:
    """Serialize a registry entry to a deterministic dictionary."""

    if not isinstance(entry, MLModelRegistryEntry):
        raise MLModelRegistryError("entry must be MLModelRegistryEntry.")
    return {
        "model_id": entry.model_id,
        "model_family": entry.model_family,
        "model_version": entry.model_version,
        "model_name": entry.model_name,
        "feature_schema_version": entry.feature_schema_version,
        "label_schema_version": entry.label_schema_version,
        "training_dataset_id": entry.training_dataset_id,
        "training_reference": entry.training_reference,
        "backtest_reference": entry.backtest_reference,
        "explainability_reference": entry.explainability_reference,
        "validation_metrics": deepcopy(entry.validation_metrics),
        "governance_status": entry.governance_status,
        "shadow_eligible": entry.shadow_eligible,
        "runtime_eligibility_requested": entry.runtime_eligibility_requested,
        "runtime_eligibility_granted": entry.runtime_eligibility_granted,
        "runtime_active": entry.runtime_active,
        "runtime_influence_granted": entry.runtime_influence_granted,
        "rollback_reference": entry.rollback_reference,
        "retired": entry.retired,
        "created_by": entry.created_by,
        "reviewed_by": entry.reviewed_by,
        "notes": entry.notes,
    }


def model_registry_entry_from_dict(data: Mapping[str, Any]) -> MLModelRegistryEntry:
    """Reconstruct and validate a registry entry from dictionary data."""

    if not isinstance(data, Mapping):
        raise MLModelRegistryError("registry entry data must be a mapping.")
    _reject_runtime_activation_fields(data)
    values = _values_from_mapping(
        data,
        MODEL_REGISTRY_ENTRY_FIELDS,
        optional_defaults={
            "feature_schema_version": None,
            "label_schema_version": None,
            "training_dataset_id": None,
            "training_reference": None,
            "backtest_reference": None,
            "explainability_reference": None,
            "validation_metrics": {},
            "governance_status": "PROPOSED",
            "shadow_eligible": False,
            "runtime_eligibility_requested": False,
            "runtime_eligibility_granted": False,
            "runtime_active": False,
            "runtime_influence_granted": False,
            "rollback_reference": None,
            "retired": False,
            "created_by": None,
            "reviewed_by": None,
            "notes": None,
        },
    )
    return MLModelRegistryEntry(**values)


def model_governance_decision_to_dict(
    decision: MLModelGovernanceDecision,
) -> dict[str, Any]:
    """Serialize a governance decision to a deterministic dictionary."""

    if not isinstance(decision, MLModelGovernanceDecision):
        raise MLModelRegistryError("decision must be MLModelGovernanceDecision.")
    return {
        "decision_id": decision.decision_id,
        "model_id": decision.model_id,
        "from_status": decision.from_status,
        "to_status": decision.to_status,
        "decision_type": decision.decision_type,
        "actor": decision.actor,
        "review_notes": decision.review_notes,
        "validation_reference": decision.validation_reference,
        "runtime_eligibility_requested": decision.runtime_eligibility_requested,
        "runtime_eligibility_granted": decision.runtime_eligibility_granted,
        "runtime_active": decision.runtime_active,
        "created_at": decision.created_at,
    }


def model_governance_decision_from_dict(
    data: Mapping[str, Any],
) -> MLModelGovernanceDecision:
    """Reconstruct and validate a governance decision from dictionary data."""

    if not isinstance(data, Mapping):
        raise MLModelRegistryError("governance decision data must be a mapping.")
    _reject_runtime_activation_fields(data)
    values = _values_from_mapping(
        data,
        MODEL_GOVERNANCE_DECISION_FIELDS,
        optional_defaults={
            "review_notes": None,
            "validation_reference": None,
            "runtime_eligibility_requested": False,
            "runtime_eligibility_granted": False,
            "runtime_active": False,
            "created_at": None,
        },
    )
    return MLModelGovernanceDecision(**values)


def model_eligibility_record_to_dict(
    record: MLModelEligibilityRecord,
) -> dict[str, Any]:
    """Serialize an eligibility record to a deterministic dictionary."""

    if not isinstance(record, MLModelEligibilityRecord):
        raise MLModelRegistryError("record must be MLModelEligibilityRecord.")
    return {
        "eligibility_id": record.eligibility_id,
        "model_id": record.model_id,
        "eligibility_type": record.eligibility_type,
        "shadow_eligible": record.shadow_eligible,
        "runtime_eligible": record.runtime_eligible,
        "runtime_active": record.runtime_active,
        "runtime_influence_granted": record.runtime_influence_granted,
        "validation_reference": record.validation_reference,
        "rollback_reference": record.rollback_reference,
        "notes": record.notes,
    }


def model_eligibility_record_from_dict(
    data: Mapping[str, Any],
) -> MLModelEligibilityRecord:
    """Reconstruct and validate an eligibility record from dictionary data."""

    if not isinstance(data, Mapping):
        raise MLModelRegistryError("eligibility record data must be a mapping.")
    _reject_runtime_activation_fields(data)
    values = _values_from_mapping(
        data,
        MODEL_ELIGIBILITY_RECORD_FIELDS,
        optional_defaults={
            "shadow_eligible": False,
            "runtime_eligible": False,
            "runtime_active": False,
            "runtime_influence_granted": False,
            "validation_reference": None,
            "rollback_reference": None,
            "notes": None,
        },
    )
    return MLModelEligibilityRecord(**values)


def create_governance_decision_id(
    model_id: str,
    decision_type: str,
    from_status: str,
    to_status: str,
) -> str:
    """Create a deterministic governance decision identifier."""

    _require_non_empty_string(model_id, "model_id")
    decision_type = _normalize_decision_type(decision_type)
    from_status = _normalize_governance_status(from_status)
    to_status = _normalize_governance_status(to_status)
    return (
        f"ML-GOVDEC-{_identifier_fragment(model_id)}-"
        f"{_identifier_fragment(decision_type)}-"
        f"{_identifier_fragment(from_status)}-"
        f"{_identifier_fragment(to_status)}"
    )


def create_eligibility_id(model_id: str, eligibility_type: str) -> str:
    """Create a deterministic model eligibility identifier."""

    _require_non_empty_string(model_id, "model_id")
    eligibility_type = _normalize_eligibility_type(eligibility_type)
    return (
        f"ML-ELIGIBILITY-{_identifier_fragment(model_id)}-"
        f"{_identifier_fragment(eligibility_type)}"
    )


def _normalize_model_family(value: Any) -> str:
    _require_non_empty_string(value, "model_family")
    normalized = str(value).strip().lower()
    if normalized not in MODEL_REGISTRY_FAMILIES:
        raise MLModelRegistryError(f"Unsupported model_family: {value}.")
    return normalized


def _normalize_governance_status(value: Any) -> str:
    _require_non_empty_string(value, "governance_status")
    normalized = str(value).strip().upper().replace("-", "_")
    if normalized not in MODEL_GOVERNANCE_STATUSES:
        raise MLModelRegistryError(f"Unsupported governance_status: {value}.")
    return normalized


def _normalize_decision_type(value: Any) -> str:
    _require_non_empty_string(value, "decision_type")
    normalized = str(value).strip().lower().replace("_", "-")
    if normalized not in MODEL_DECISION_TYPES:
        raise MLModelRegistryError(f"Unsupported decision_type: {value}.")
    return normalized


def _normalize_eligibility_type(value: Any) -> str:
    _require_non_empty_string(value, "eligibility_type")
    normalized = str(value).strip().lower().replace("-", "_")
    if normalized not in MODEL_ELIGIBILITY_TYPES:
        raise MLModelRegistryError(f"Unsupported eligibility_type: {value}.")
    return normalized


def _normalize_validation_metrics(value: Any) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise MLModelRegistryError("validation_metrics must be a mapping.")
    normalized: dict[str, float] = {}
    for metric_name, metric_value in sorted(value.items(), key=lambda item: str(item[0])):
        if not isinstance(metric_name, str) or not metric_name.strip():
            raise MLModelRegistryError(
                "validation_metrics keys must be non-empty strings."
            )
        if not _is_number(metric_value):
            raise MLModelRegistryError("validation_metrics values must be numeric.")
        normalized[metric_name.strip()] = float(metric_value)
    return normalized


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
        raise MLModelRegistryError(
            "Missing required fields: " + ", ".join(missing) + "."
        )
    return {
        field_name: deepcopy(data[field_name])
        if field_name in data
        else deepcopy(optional_defaults[field_name])
        for field_name in fields
    }


def _reject_runtime_activation_fields(data: Mapping[str, Any]) -> None:
    for field_name in (
        "runtime_eligible",
        "runtime_eligibility_granted",
        "runtime_active",
        "runtime_influence_granted",
    ):
        if data.get(field_name) is True:
            raise MLModelRegistryError(
                f"{field_name} cannot be true on Phase 7Y model registry records."
            )


def _require_false(value: Any, field_name: str) -> None:
    if value is not False:
        raise MLModelRegistryError(
            f"Phase 7Y model registry records must keep {field_name}=false."
        )


def _validate_bool(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise MLModelRegistryError(f"{field_name} must be a boolean.")


def _require_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise MLModelRegistryError(f"{field_name} must be a non-empty string.")


def _validate_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise MLModelRegistryError(f"{field_name} must be None or a string.")
    if isinstance(value, str) and not value.strip():
        raise MLModelRegistryError(f"{field_name} must not be blank.")


def _normalize_optional_string(value: str | None) -> str | None:
    return None if value is None else value.strip()


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _identifier_fragment(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "UNSPECIFIED"
