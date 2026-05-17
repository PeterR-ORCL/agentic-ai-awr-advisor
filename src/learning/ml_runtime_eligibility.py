"""Phase 7BY ML runtime eligibility metadata.

This module defines local-only ML runtime eligibility package, activation
manifest, fallback, monitoring, and regression evidence metadata. It validates
future shadow-to-runtime review envelopes without importing ML frameworks,
deploying models, loading or saving model files, replacing deterministic
scoring, granting runtime influence, activating runtime ML, or mutating
Phase 4I.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any


ML_RUNTIME_ELIGIBILITY_STATUSES = (
    "not_eligible",
    "eligible_metadata_only",
    "needs_registry_reference",
    "needs_training_reference",
    "needs_backtest_reference",
    "needs_explainability_reference",
    "needs_validation_reference",
    "needs_deterministic_comparison",
    "needs_drift_review",
    "needs_rollback_reference",
    "needs_monitoring_reference",
    "needs_runtime_gate",
    "blocked_by_safety",
)

ML_RUNTIME_ACTIVATION_MODES = (
    "disabled",
    "shadow_only",
    "manual_review_required",
    "future_runtime_manifest",
    "emergency_disabled",
)

ML_RUNTIME_MODEL_FAMILIES = (
    "tree",
    "neural_net",
    "hybrid_rule_ml",
    "linear",
    "baseline_mock",
    "baseline_majority",
    "baseline_numeric_mean",
    "shadow_placeholder",
    "external_placeholder",
    "unknown",
)

ELIGIBLE_METADATA_STATUS = "eligible_metadata_only"
DEFAULT_ACTIVATION_MODE = "manual_review_required"


class MLRuntimeEligibilityError(ValueError):
    """Raised when Phase 7BY ML runtime eligibility metadata is invalid."""


@dataclass(frozen=True)
class MLRuntimeEligibilityPackage:
    """Local metadata package for future ML runtime eligibility review."""

    package_id: str
    model_id: str
    model_family: str
    model_version: str
    registry_entry_id: str | None = None
    training_reference: str | None = None
    backtest_reference: str | None = None
    explainability_reference: str | None = None
    validation_reference: str | None = None
    dataset_reference: str | None = None
    feature_schema_version: str | None = None
    label_schema_version: str | None = None
    deterministic_comparison_reference: str | None = None
    drift_review_reference: str | None = None
    rollback_reference: str | None = None
    monitoring_reference: str | None = None
    eligibility_status: str = "not_eligible"
    runtime_eligible: bool = False
    runtime_active: bool = False
    runtime_influence_granted: bool = False
    runtime_eligibility_granted: bool = False
    model_deployed: bool = False
    model_loaded: bool = False
    model_saved: bool = False
    runtime_scoring_replaced: bool = False
    phase4i_mutation_performed: bool = False
    created_by: str | None = None
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.package_id, "package_id")
        _require_nonempty_string(self.model_id, "model_id")
        _require_supported(
            self.model_family,
            ML_RUNTIME_MODEL_FAMILIES,
            "model_family",
        )
        _require_nonempty_string(self.model_version, "model_version")
        _require_optional_string(self.registry_entry_id, "registry_entry_id")
        _require_optional_string(self.training_reference, "training_reference")
        _require_optional_string(self.backtest_reference, "backtest_reference")
        _require_optional_string(
            self.explainability_reference,
            "explainability_reference",
        )
        _require_optional_string(self.validation_reference, "validation_reference")
        _require_optional_string(self.dataset_reference, "dataset_reference")
        _require_optional_string(
            self.feature_schema_version,
            "feature_schema_version",
        )
        _require_optional_string(self.label_schema_version, "label_schema_version")
        _require_optional_string(
            self.deterministic_comparison_reference,
            "deterministic_comparison_reference",
        )
        _require_optional_string(self.drift_review_reference, "drift_review_reference")
        _require_optional_string(self.rollback_reference, "rollback_reference")
        _require_optional_string(self.monitoring_reference, "monitoring_reference")
        _require_supported(
            self.eligibility_status,
            ML_RUNTIME_ELIGIBILITY_STATUSES,
            "eligibility_status",
        )
        _require_boolean(self.runtime_eligible, "runtime_eligible")
        _require_false(self.runtime_active, "runtime_active")
        _require_false(self.runtime_influence_granted, "runtime_influence_granted")
        _require_false(self.runtime_eligibility_granted, "runtime_eligibility_granted")
        _require_false(self.model_deployed, "model_deployed")
        _require_false(self.model_loaded, "model_loaded")
        _require_false(self.model_saved, "model_saved")
        _require_false(self.runtime_scoring_replaced, "runtime_scoring_replaced")
        _require_false(
            self.phase4i_mutation_performed,
            "phase4i_mutation_performed",
        )
        _require_optional_string(self.created_by, "created_by")
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")
        if self.runtime_eligible and not _package_has_all_eligibility_metadata(self):
            raise MLRuntimeEligibilityError(
                "runtime_eligible metadata requires all ML runtime eligibility "
                "references and eligible_metadata_only status."
            )


@dataclass(frozen=True)
class MLRuntimeActivationManifest:
    """Local manifest metadata for future ML runtime activation review."""

    manifest_id: str
    package_id: str
    manifest_version: str
    activation_mode: str = DEFAULT_ACTIVATION_MODE
    explicit_activation_required: bool = True
    validation_reference: str | None = None
    rollback_reference: str | None = None
    runtime_gate_reference: str | None = None
    monitoring_reference: str | None = None
    deterministic_fallback_available: bool = True
    phase4i_contract_preserved: bool = True
    runtime_activation_requested: bool = False
    runtime_activation_approved: bool = False
    runtime_active: bool = False
    model_deployed: bool = False
    runtime_scoring_replaced: bool = False
    created_by: str | None = None
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.manifest_id, "manifest_id")
        _require_nonempty_string(self.package_id, "package_id")
        _require_nonempty_string(self.manifest_version, "manifest_version")
        _require_supported(
            self.activation_mode,
            ML_RUNTIME_ACTIVATION_MODES,
            "activation_mode",
        )
        _require_true(self.explicit_activation_required, "explicit_activation_required")
        _require_optional_string(self.validation_reference, "validation_reference")
        _require_optional_string(self.rollback_reference, "rollback_reference")
        _require_optional_string(self.runtime_gate_reference, "runtime_gate_reference")
        _require_optional_string(self.monitoring_reference, "monitoring_reference")
        _require_true(
            self.deterministic_fallback_available,
            "deterministic_fallback_available",
        )
        _require_true(self.phase4i_contract_preserved, "phase4i_contract_preserved")
        _require_false(
            self.runtime_activation_requested,
            "runtime_activation_requested",
        )
        _require_false(
            self.runtime_activation_approved,
            "runtime_activation_approved",
        )
        _require_false(self.runtime_active, "runtime_active")
        _require_false(self.model_deployed, "model_deployed")
        _require_false(self.runtime_scoring_replaced, "runtime_scoring_replaced")
        _require_optional_string(self.created_by, "created_by")
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class MLRuntimeEligibilityRecord:
    """Local eligibility result for an ML runtime eligibility package."""

    eligibility_id: str
    package_id: str
    manifest_id: str
    eligible: bool
    eligibility_status: str
    registry_reference_present: bool
    training_reference_present: bool
    backtest_reference_present: bool
    explainability_reference_present: bool
    validation_reference_present: bool
    deterministic_comparison_reference_present: bool
    drift_review_reference_present: bool
    rollback_reference_present: bool
    monitoring_reference_present: bool
    runtime_gate_reference_present: bool
    deterministic_fallback_available: bool
    phase4i_contract_preserved: bool
    runtime_active: bool = False
    runtime_eligibility_granted: bool = False
    runtime_influence_granted: bool = False
    model_deployed: bool = False
    runtime_scoring_replaced: bool = False
    denied_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.eligibility_id, "eligibility_id")
        _require_nonempty_string(self.package_id, "package_id")
        _require_nonempty_string(self.manifest_id, "manifest_id")
        _require_boolean(self.eligible, "eligible")
        _require_supported(
            self.eligibility_status,
            ML_RUNTIME_ELIGIBILITY_STATUSES,
            "eligibility_status",
        )
        _require_boolean(
            self.registry_reference_present,
            "registry_reference_present",
        )
        _require_boolean(
            self.training_reference_present,
            "training_reference_present",
        )
        _require_boolean(
            self.backtest_reference_present,
            "backtest_reference_present",
        )
        _require_boolean(
            self.explainability_reference_present,
            "explainability_reference_present",
        )
        _require_boolean(
            self.validation_reference_present,
            "validation_reference_present",
        )
        _require_boolean(
            self.deterministic_comparison_reference_present,
            "deterministic_comparison_reference_present",
        )
        _require_boolean(
            self.drift_review_reference_present,
            "drift_review_reference_present",
        )
        _require_boolean(
            self.rollback_reference_present,
            "rollback_reference_present",
        )
        _require_boolean(
            self.monitoring_reference_present,
            "monitoring_reference_present",
        )
        _require_boolean(
            self.runtime_gate_reference_present,
            "runtime_gate_reference_present",
        )
        _require_true(
            self.deterministic_fallback_available,
            "deterministic_fallback_available",
        )
        _require_true(self.phase4i_contract_preserved, "phase4i_contract_preserved")
        _require_false(self.runtime_active, "runtime_active")
        _require_false(
            self.runtime_eligibility_granted,
            "runtime_eligibility_granted",
        )
        _require_false(self.runtime_influence_granted, "runtime_influence_granted")
        _require_false(self.model_deployed, "model_deployed")
        _require_false(self.runtime_scoring_replaced, "runtime_scoring_replaced")
        _require_list_of_strings(self.denied_reasons, "denied_reasons")
        _require_list_of_strings(self.warnings, "warnings")
        _require_list_of_strings(self.required_next_steps, "required_next_steps")
        _require_optional_string(self.notes, "notes")
        if self.eligible:
            if self.eligibility_status != ELIGIBLE_METADATA_STATUS:
                raise MLRuntimeEligibilityError(
                    "eligible metadata must use eligible_metadata_only status."
                )
            if not all(
                (
                    self.registry_reference_present,
                    self.training_reference_present,
                    self.backtest_reference_present,
                    self.explainability_reference_present,
                    self.validation_reference_present,
                    self.deterministic_comparison_reference_present,
                    self.drift_review_reference_present,
                    self.rollback_reference_present,
                    self.monitoring_reference_present,
                    self.runtime_gate_reference_present,
                )
            ):
                raise MLRuntimeEligibilityError(
                    "eligible metadata requires all ML validation references."
                )


@dataclass(frozen=True)
class MLRuntimeFallbackPlan:
    """Local fallback metadata for future ML runtime review."""

    fallback_id: str
    package_id: str
    fallback_strategy: str
    deterministic_scoring_fallback: bool = True
    disable_model_fallback: bool = True
    rollback_reference: str | None = None
    fallback_validated: bool = False
    fallback_executed: bool = False
    model_disabled: bool = False
    runtime_scoring_reverted: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.fallback_id, "fallback_id")
        _require_nonempty_string(self.package_id, "package_id")
        _require_nonempty_string(self.fallback_strategy, "fallback_strategy")
        _require_true(
            self.deterministic_scoring_fallback,
            "deterministic_scoring_fallback",
        )
        _require_true(self.disable_model_fallback, "disable_model_fallback")
        _require_optional_string(self.rollback_reference, "rollback_reference")
        _require_boolean(self.fallback_validated, "fallback_validated")
        _require_false(self.fallback_executed, "fallback_executed")
        _require_false(self.model_disabled, "model_disabled")
        _require_false(self.runtime_scoring_reverted, "runtime_scoring_reverted")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class MLRuntimeMonitoringPlan:
    """Local monitoring metadata for future ML runtime review."""

    monitoring_id: str
    package_id: str
    monitoring_strategy: str
    drift_monitoring_required: bool
    performance_monitoring_required: bool
    confidence_monitoring_required: bool
    fallback_trigger_defined: bool
    monitoring_active: bool = False
    runtime_active: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.monitoring_id, "monitoring_id")
        _require_nonempty_string(self.package_id, "package_id")
        _require_nonempty_string(self.monitoring_strategy, "monitoring_strategy")
        _require_boolean(
            self.drift_monitoring_required,
            "drift_monitoring_required",
        )
        _require_boolean(
            self.performance_monitoring_required,
            "performance_monitoring_required",
        )
        _require_boolean(
            self.confidence_monitoring_required,
            "confidence_monitoring_required",
        )
        _require_boolean(self.fallback_trigger_defined, "fallback_trigger_defined")
        _require_false(self.monitoring_active, "monitoring_active")
        _require_false(self.runtime_active, "runtime_active")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class MLRuntimeRegressionEvidence:
    """Local regression evidence metadata for future ML runtime review."""

    regression_id: str
    package_id: str
    backtest_reference: str
    explainability_reference: str
    deterministic_comparison_reference: str
    validation_reference: str
    regression_passed: bool
    backtesting_passed: bool
    explainability_present: bool
    deterministic_comparison_acceptable: bool
    phase4i_contract_preserved: bool
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.regression_id, "regression_id")
        _require_nonempty_string(self.package_id, "package_id")
        _require_nonempty_string(self.backtest_reference, "backtest_reference")
        _require_nonempty_string(
            self.explainability_reference,
            "explainability_reference",
        )
        _require_nonempty_string(
            self.deterministic_comparison_reference,
            "deterministic_comparison_reference",
        )
        _require_nonempty_string(self.validation_reference, "validation_reference")
        _require_boolean(self.regression_passed, "regression_passed")
        _require_boolean(self.backtesting_passed, "backtesting_passed")
        _require_boolean(self.explainability_present, "explainability_present")
        _require_boolean(
            self.deterministic_comparison_acceptable,
            "deterministic_comparison_acceptable",
        )
        _require_true(self.phase4i_contract_preserved, "phase4i_contract_preserved")
        _require_optional_string(self.notes, "notes")
        if self.regression_passed and not all(
            (
                self.backtesting_passed,
                self.explainability_present,
                self.deterministic_comparison_acceptable,
            )
        ):
            raise MLRuntimeEligibilityError(
                "regression_passed metadata requires backtesting, explainability, "
                "and deterministic comparison evidence."
            )


def create_ml_runtime_package_id(model_id: str, model_version: str) -> str:
    """Create a deterministic ML runtime package id."""

    _require_nonempty_string(model_id, "model_id")
    _require_nonempty_string(model_version, "model_version")
    return (
        "ML-RUNTIME-PACKAGE-"
        f"{_normalize_token(model_id)}-"
        f"{_normalize_token(model_version)}"
    )


def create_ml_runtime_manifest_id(package_id: str, manifest_version: str) -> str:
    """Create a deterministic ML runtime manifest id."""

    _require_nonempty_string(package_id, "package_id")
    _require_nonempty_string(manifest_version, "manifest_version")
    return (
        "ML-RUNTIME-MANIFEST-"
        f"{_normalize_token(package_id)}-"
        f"{_normalize_token(manifest_version)}"
    )


def create_ml_runtime_eligibility_id(package_id: str, manifest_id: str) -> str:
    """Create a deterministic ML runtime eligibility id."""

    _require_nonempty_string(package_id, "package_id")
    _require_nonempty_string(manifest_id, "manifest_id")
    return (
        "ML-RUNTIME-ELIGIBILITY-"
        f"{_normalize_token(package_id)}-"
        f"{_normalize_token(manifest_id)}"
    )


def create_ml_runtime_fallback_id(package_id: str, fallback_strategy: str) -> str:
    """Create a deterministic ML runtime fallback id."""

    _require_nonempty_string(package_id, "package_id")
    _require_nonempty_string(fallback_strategy, "fallback_strategy")
    return (
        "ML-RUNTIME-FALLBACK-"
        f"{_normalize_token(package_id)}-"
        f"{_normalize_token(fallback_strategy)}"
    )


def create_ml_runtime_monitoring_id(package_id: str, monitoring_strategy: str) -> str:
    """Create a deterministic ML runtime monitoring id."""

    _require_nonempty_string(package_id, "package_id")
    _require_nonempty_string(monitoring_strategy, "monitoring_strategy")
    return (
        "ML-RUNTIME-MONITORING-"
        f"{_normalize_token(package_id)}-"
        f"{_normalize_token(monitoring_strategy)}"
    )


def create_ml_runtime_regression_id(package_id: str, reference: str) -> str:
    """Create a deterministic ML runtime regression evidence id."""

    _require_nonempty_string(package_id, "package_id")
    _require_nonempty_string(reference, "reference")
    return (
        "ML-RUNTIME-REGRESSION-"
        f"{_normalize_token(package_id)}-"
        f"{_normalize_token(reference)}"
    )


def validate_ml_runtime_eligibility_package(
    package: MLRuntimeEligibilityPackage,
) -> MLRuntimeEligibilityPackage:
    """Validate ML runtime eligibility package metadata without activation."""

    if not isinstance(package, MLRuntimeEligibilityPackage):
        raise MLRuntimeEligibilityError(
            "package must be an MLRuntimeEligibilityPackage instance."
        )
    package.__post_init__()
    return package


def validate_ml_runtime_activation_manifest(
    manifest: MLRuntimeActivationManifest,
) -> MLRuntimeActivationManifest:
    """Validate ML runtime activation manifest metadata without activation."""

    if not isinstance(manifest, MLRuntimeActivationManifest):
        raise MLRuntimeEligibilityError(
            "manifest must be an MLRuntimeActivationManifest instance."
        )
    manifest.__post_init__()
    return manifest


def validate_ml_runtime_eligibility_record(
    record: MLRuntimeEligibilityRecord,
) -> MLRuntimeEligibilityRecord:
    """Validate ML runtime eligibility result metadata."""

    if not isinstance(record, MLRuntimeEligibilityRecord):
        raise MLRuntimeEligibilityError(
            "record must be an MLRuntimeEligibilityRecord instance."
        )
    record.__post_init__()
    return record


def validate_ml_runtime_fallback_plan(
    fallback: MLRuntimeFallbackPlan,
) -> MLRuntimeFallbackPlan:
    """Validate ML runtime fallback metadata without executing fallback."""

    if not isinstance(fallback, MLRuntimeFallbackPlan):
        raise MLRuntimeEligibilityError(
            "fallback must be an MLRuntimeFallbackPlan instance."
        )
    fallback.__post_init__()
    return fallback


def validate_ml_runtime_monitoring_plan(
    monitoring: MLRuntimeMonitoringPlan,
) -> MLRuntimeMonitoringPlan:
    """Validate ML runtime monitoring metadata without activating monitoring."""

    if not isinstance(monitoring, MLRuntimeMonitoringPlan):
        raise MLRuntimeEligibilityError(
            "monitoring must be an MLRuntimeMonitoringPlan instance."
        )
    monitoring.__post_init__()
    return monitoring


def validate_ml_runtime_regression_evidence(
    evidence: MLRuntimeRegressionEvidence,
) -> MLRuntimeRegressionEvidence:
    """Validate ML runtime regression metadata without running tests."""

    if not isinstance(evidence, MLRuntimeRegressionEvidence):
        raise MLRuntimeEligibilityError(
            "evidence must be an MLRuntimeRegressionEvidence instance."
        )
    evidence.__post_init__()
    return evidence


def evaluate_ml_runtime_eligibility(
    package: MLRuntimeEligibilityPackage,
    manifest: MLRuntimeActivationManifest,
) -> MLRuntimeEligibilityRecord:
    """Evaluate ML runtime eligibility as metadata only."""

    package = validate_ml_runtime_eligibility_package(package)
    manifest = validate_ml_runtime_activation_manifest(manifest)

    denied_reasons: list[str] = []
    warnings = [
        "Phase 7BY ML eligibility is metadata only; runtime_active=false.",
        "Runtime eligibility and influence are not granted in Phase 7BY.",
        "Deterministic scoring fallback remains required and authoritative.",
    ]
    required_next_steps: list[str] = []

    registry_reference_present = bool(_optional_text(package.registry_entry_id))
    training_reference_present = bool(_optional_text(package.training_reference))
    backtest_reference_present = bool(_optional_text(package.backtest_reference))
    explainability_reference_present = bool(
        _optional_text(package.explainability_reference)
    )
    validation_reference_present = bool(
        _optional_text(package.validation_reference)
        and _optional_text(manifest.validation_reference)
    )
    deterministic_comparison_reference_present = bool(
        _optional_text(package.deterministic_comparison_reference)
    )
    drift_review_reference_present = bool(
        _optional_text(package.drift_review_reference)
    )
    rollback_reference_present = bool(
        _optional_text(package.rollback_reference)
        and _optional_text(manifest.rollback_reference)
    )
    monitoring_reference_present = bool(
        _optional_text(package.monitoring_reference)
        and _optional_text(manifest.monitoring_reference)
    )
    runtime_gate_reference_present = bool(_optional_text(manifest.runtime_gate_reference))

    eligibility_status = ELIGIBLE_METADATA_STATUS
    if package.eligibility_status != ELIGIBLE_METADATA_STATUS:
        eligibility_status = "not_eligible"
        denied_reasons.append(
            "eligibility_status must be eligible_metadata_only for metadata review"
        )
        required_next_steps.append("advance package metadata through governance review")
    elif not registry_reference_present:
        eligibility_status = "needs_registry_reference"
        denied_reasons.append("registry_entry_id is required")
        required_next_steps.append("attach model registry reference")
    elif not training_reference_present:
        eligibility_status = "needs_training_reference"
        denied_reasons.append("training_reference is required")
        required_next_steps.append("attach training evidence reference")
    elif not backtest_reference_present:
        eligibility_status = "needs_backtest_reference"
        denied_reasons.append("backtest_reference is required")
        required_next_steps.append("attach backtesting evidence reference")
    elif not explainability_reference_present:
        eligibility_status = "needs_explainability_reference"
        denied_reasons.append("explainability_reference is required")
        required_next_steps.append("attach explainability evidence reference")
    elif not validation_reference_present:
        eligibility_status = "needs_validation_reference"
        denied_reasons.append("package and manifest validation references are required")
        required_next_steps.append("attach ML validation reference metadata")
    elif not deterministic_comparison_reference_present:
        eligibility_status = "needs_deterministic_comparison"
        denied_reasons.append("deterministic_comparison_reference is required")
        required_next_steps.append("attach deterministic comparison evidence")
    elif not drift_review_reference_present:
        eligibility_status = "needs_drift_review"
        denied_reasons.append("drift_review_reference is required")
        required_next_steps.append("attach drift review reference")
    elif not rollback_reference_present:
        eligibility_status = "needs_rollback_reference"
        denied_reasons.append("rollback_reference is required on package and manifest")
        required_next_steps.append("attach rollback reference metadata")
    elif not monitoring_reference_present:
        eligibility_status = "needs_monitoring_reference"
        denied_reasons.append("monitoring_reference is required on package and manifest")
        required_next_steps.append("attach monitoring plan reference")
    elif not runtime_gate_reference_present:
        eligibility_status = "needs_runtime_gate"
        denied_reasons.append("runtime_gate_reference is required")
        required_next_steps.append("attach runtime gate review reference")
    elif not _package_has_all_eligibility_metadata(package):
        eligibility_status = "blocked_by_safety"
        denied_reasons.append(
            "dataset, feature schema, label schema, or validation metadata is missing"
        )
        required_next_steps.append("complete package metadata before runtime review")
    else:
        required_next_steps.append("future runtime review may consider this package")
        required_next_steps.append("explicit activation remains required in a future phase")

    eligible = eligibility_status == ELIGIBLE_METADATA_STATUS
    return validate_ml_runtime_eligibility_record(
        MLRuntimeEligibilityRecord(
            eligibility_id=create_ml_runtime_eligibility_id(
                package.package_id,
                manifest.manifest_id,
            ),
            package_id=package.package_id,
            manifest_id=manifest.manifest_id,
            eligible=eligible,
            eligibility_status=eligibility_status,
            registry_reference_present=registry_reference_present,
            training_reference_present=training_reference_present,
            backtest_reference_present=backtest_reference_present,
            explainability_reference_present=explainability_reference_present,
            validation_reference_present=validation_reference_present,
            deterministic_comparison_reference_present=(
                deterministic_comparison_reference_present
            ),
            drift_review_reference_present=drift_review_reference_present,
            rollback_reference_present=rollback_reference_present,
            monitoring_reference_present=monitoring_reference_present,
            runtime_gate_reference_present=runtime_gate_reference_present,
            deterministic_fallback_available=True,
            phase4i_contract_preserved=True,
            runtime_active=False,
            runtime_eligibility_granted=False,
            runtime_influence_granted=False,
            model_deployed=False,
            runtime_scoring_replaced=False,
            denied_reasons=denied_reasons,
            warnings=warnings,
            required_next_steps=required_next_steps,
            notes=package.notes,
        )
    )


def ml_runtime_eligibility_package_to_dict(
    package: MLRuntimeEligibilityPackage,
) -> dict[str, Any]:
    """Serialize ML runtime eligibility package metadata."""

    return _to_dict(validate_ml_runtime_eligibility_package(package))


def ml_runtime_eligibility_package_from_dict(
    data: dict[str, Any],
) -> MLRuntimeEligibilityPackage:
    """Deserialize ML runtime eligibility package metadata."""

    _require_mapping(data, "data")
    return MLRuntimeEligibilityPackage(**dict(data))


def ml_runtime_activation_manifest_to_dict(
    manifest: MLRuntimeActivationManifest,
) -> dict[str, Any]:
    """Serialize ML runtime activation manifest metadata."""

    return _to_dict(validate_ml_runtime_activation_manifest(manifest))


def ml_runtime_activation_manifest_from_dict(
    data: dict[str, Any],
) -> MLRuntimeActivationManifest:
    """Deserialize ML runtime activation manifest metadata."""

    _require_mapping(data, "data")
    return MLRuntimeActivationManifest(**dict(data))


def ml_runtime_eligibility_record_to_dict(
    record: MLRuntimeEligibilityRecord,
) -> dict[str, Any]:
    """Serialize ML runtime eligibility record metadata."""

    return _to_dict(validate_ml_runtime_eligibility_record(record))


def ml_runtime_eligibility_record_from_dict(
    data: dict[str, Any],
) -> MLRuntimeEligibilityRecord:
    """Deserialize ML runtime eligibility record metadata."""

    _require_mapping(data, "data")
    return MLRuntimeEligibilityRecord(**dict(data))


def ml_runtime_fallback_plan_to_dict(
    fallback: MLRuntimeFallbackPlan,
) -> dict[str, Any]:
    """Serialize ML runtime fallback plan metadata."""

    return _to_dict(validate_ml_runtime_fallback_plan(fallback))


def ml_runtime_fallback_plan_from_dict(
    data: dict[str, Any],
) -> MLRuntimeFallbackPlan:
    """Deserialize ML runtime fallback plan metadata."""

    _require_mapping(data, "data")
    return MLRuntimeFallbackPlan(**dict(data))


def ml_runtime_monitoring_plan_to_dict(
    monitoring: MLRuntimeMonitoringPlan,
) -> dict[str, Any]:
    """Serialize ML runtime monitoring plan metadata."""

    return _to_dict(validate_ml_runtime_monitoring_plan(monitoring))


def ml_runtime_monitoring_plan_from_dict(
    data: dict[str, Any],
) -> MLRuntimeMonitoringPlan:
    """Deserialize ML runtime monitoring plan metadata."""

    _require_mapping(data, "data")
    return MLRuntimeMonitoringPlan(**dict(data))


def ml_runtime_regression_evidence_to_dict(
    evidence: MLRuntimeRegressionEvidence,
) -> dict[str, Any]:
    """Serialize ML runtime regression evidence metadata."""

    return _to_dict(validate_ml_runtime_regression_evidence(evidence))


def ml_runtime_regression_evidence_from_dict(
    data: dict[str, Any],
) -> MLRuntimeRegressionEvidence:
    """Deserialize ML runtime regression evidence metadata."""

    _require_mapping(data, "data")
    return MLRuntimeRegressionEvidence(**dict(data))


def _package_has_all_eligibility_metadata(
    package: MLRuntimeEligibilityPackage,
) -> bool:
    return all(
        (
            package.eligibility_status == ELIGIBLE_METADATA_STATUS,
            _optional_text(package.registry_entry_id),
            _optional_text(package.training_reference),
            _optional_text(package.backtest_reference),
            _optional_text(package.explainability_reference),
            _optional_text(package.validation_reference),
            _optional_text(package.dataset_reference),
            _optional_text(package.feature_schema_version),
            _optional_text(package.label_schema_version),
            _optional_text(package.deterministic_comparison_reference),
            _optional_text(package.drift_review_reference),
            _optional_text(package.rollback_reference),
            _optional_text(package.monitoring_reference),
        )
    )


def _to_dict(value: Any) -> dict[str, Any]:
    return dict(asdict(value))


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise MLRuntimeEligibilityError(f"{field_name} must be a dictionary.")


def _require_nonempty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise MLRuntimeEligibilityError(f"{field_name} must be a non-empty string.")


def _require_optional_string(value: Any, field_name: str) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise MLRuntimeEligibilityError(
            f"{field_name} must be a non-empty string when provided."
        )


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        supported_values = ", ".join(supported)
        raise MLRuntimeEligibilityError(
            f"{field_name} must be one of: {supported_values}."
        )


def _require_boolean(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise MLRuntimeEligibilityError(f"{field_name} must be a boolean.")


def _require_true(value: Any, field_name: str) -> None:
    _require_boolean(value, field_name)
    if value is not True:
        raise MLRuntimeEligibilityError(f"{field_name}=true is required.")


def _require_false(value: Any, field_name: str) -> None:
    _require_boolean(value, field_name)
    if value is not False:
        raise MLRuntimeEligibilityError(
            f"{field_name}=true is not allowed in Phase 7BY."
        )


def _require_list_of_strings(value: Any, field_name: str) -> None:
    if not isinstance(value, list):
        raise MLRuntimeEligibilityError(f"{field_name} must be a list.")
    for item in value:
        _require_nonempty_string(item, field_name)


def _normalize_token(value: Any) -> str:
    _require_nonempty_string(value, "id component")
    token = re.sub(r"[^A-Za-z0-9]+", "-", str(value).strip().upper()).strip("-")
    if not token:
        raise MLRuntimeEligibilityError("id component must contain a stable token.")
    return token
