"""Phase 7BX recommendation runtime rule activation metadata.

This module defines local-only recommendation runtime rule package, activation
manifest, eligibility, rollback, and regression evidence metadata. It validates
future recommendation activation envelopes without importing runtime
recommendation modules, changing recommendation code or catalog, applying
rules, mutating recommendation output, activating runtime recommendations, or
mutating Phase 4I.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


RECOMMENDATION_RUNTIME_PACKAGE_STATUSES = (
    "proposed",
    "under_review",
    "validation_required",
    "regression_ready",
    "eligible_for_runtime_review",
    "rejected",
    "superseded",
    "closed",
)

RECOMMENDATION_RUNTIME_ELIGIBILITY_STATUSES = (
    "not_eligible",
    "eligible_metadata_only",
    "needs_regression_reference",
    "needs_before_after_reference",
    "needs_evidence_mapping_validation",
    "needs_action_sequence_validation",
    "needs_risk_label_validation",
    "needs_phase4i_recommendation_contract",
    "needs_rollback_reference",
    "needs_runtime_gate",
    "blocked_by_safety",
)

RECOMMENDATION_RUNTIME_ACTIVATION_MODES = (
    "disabled",
    "manual_review_required",
    "future_runtime_manifest",
    "emergency_disabled",
)

RECOMMENDATION_RULE_TYPES = (
    "wording",
    "priority",
    "domain_mapping",
    "suppression",
    "action_sequence",
    "risk_label",
    "evidence_mapping",
    "category",
    "confidence_wording",
    "escalation",
    "unknown",
)

ELIGIBILITY_PACKAGE_STATUS = "eligible_for_runtime_review"
DEFAULT_ACTIVATION_MODE = "manual_review_required"


class RecommendationRuntimeActivationError(ValueError):
    """Raised when Phase 7BX recommendation activation metadata is invalid."""


@dataclass(frozen=True)
class RecommendationRuntimeRulePackage:
    """Local metadata package for future recommendation runtime rule eligibility."""

    package_id: str
    source_recommendation_evolution_id: str
    source_materialization_id: str
    recommendation_rule_version: str
    affected_domains: list[str] = field(default_factory=list)
    affected_components: list[str] = field(default_factory=list)
    rule_type: str = "unknown"
    proposed_rule_summary: str = ""
    wording_changes: dict[str, Any] = field(default_factory=dict)
    priority_changes: dict[str, Any] = field(default_factory=dict)
    evidence_mapping_changes: dict[str, Any] = field(default_factory=dict)
    action_sequence_changes: dict[str, Any] = field(default_factory=dict)
    risk_label_changes: dict[str, Any] = field(default_factory=dict)
    suppression_rule_changes: dict[str, Any] = field(default_factory=dict)
    escalation_rule_changes: dict[str, Any] = field(default_factory=dict)
    before_after_reference: str | None = None
    regression_reference: str | None = None
    evidence_mapping_validation_reference: str | None = None
    action_sequence_validation_reference: str | None = None
    risk_label_validation_reference: str | None = None
    phase4i_recommendation_contract_reference: str | None = None
    rollback_reference: str | None = None
    package_status: str = "proposed"
    runtime_eligible: bool = False
    runtime_active: bool = False
    recommendation_rule_applied: bool = False
    recommendation_output_mutation_performed: bool = False
    phase4i_mutation_performed: bool = False
    created_by: str | None = None
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.package_id, "package_id")
        _require_nonempty_string(
            self.source_recommendation_evolution_id,
            "source_recommendation_evolution_id",
        )
        _require_nonempty_string(
            self.source_materialization_id,
            "source_materialization_id",
        )
        _require_nonempty_string(
            self.recommendation_rule_version,
            "recommendation_rule_version",
        )
        _require_list_of_strings(self.affected_domains, "affected_domains")
        _require_list_of_strings(self.affected_components, "affected_components")
        _require_supported(self.rule_type, RECOMMENDATION_RULE_TYPES, "rule_type")
        _require_nonempty_string(self.proposed_rule_summary, "proposed_rule_summary")
        _require_mapping(self.wording_changes, "wording_changes")
        _require_mapping(self.priority_changes, "priority_changes")
        _require_mapping(self.evidence_mapping_changes, "evidence_mapping_changes")
        _require_mapping(self.action_sequence_changes, "action_sequence_changes")
        _require_mapping(self.risk_label_changes, "risk_label_changes")
        _require_mapping(self.suppression_rule_changes, "suppression_rule_changes")
        _require_mapping(self.escalation_rule_changes, "escalation_rule_changes")
        _require_optional_string(self.before_after_reference, "before_after_reference")
        _require_optional_string(self.regression_reference, "regression_reference")
        _require_optional_string(
            self.evidence_mapping_validation_reference,
            "evidence_mapping_validation_reference",
        )
        _require_optional_string(
            self.action_sequence_validation_reference,
            "action_sequence_validation_reference",
        )
        _require_optional_string(
            self.risk_label_validation_reference,
            "risk_label_validation_reference",
        )
        _require_optional_string(
            self.phase4i_recommendation_contract_reference,
            "phase4i_recommendation_contract_reference",
        )
        _require_optional_string(self.rollback_reference, "rollback_reference")
        _require_supported(
            self.package_status,
            RECOMMENDATION_RUNTIME_PACKAGE_STATUSES,
            "package_status",
        )
        _require_boolean(self.runtime_eligible, "runtime_eligible")
        _require_false(self.runtime_active, "runtime_active")
        _require_false(
            self.recommendation_rule_applied,
            "recommendation_rule_applied",
        )
        _require_false(
            self.recommendation_output_mutation_performed,
            "recommendation_output_mutation_performed",
        )
        _require_false(
            self.phase4i_mutation_performed,
            "phase4i_mutation_performed",
        )
        _require_optional_string(self.created_by, "created_by")
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")
        if self.package_status in ("regression_ready", "eligible_for_runtime_review"):
            _require_nonempty_string(self.rollback_reference, "rollback_reference")
        if self.runtime_eligible and not _package_has_all_eligibility_metadata(self):
            raise RecommendationRuntimeActivationError(
                "runtime_eligible metadata requires all validation references, "
                "rollback reference, and eligible status."
            )


@dataclass(frozen=True)
class RecommendationActivationManifest:
    """Local manifest metadata for future recommendation rule activation review."""

    manifest_id: str
    package_id: str
    manifest_version: str
    activation_mode: str = DEFAULT_ACTIVATION_MODE
    explicit_activation_required: bool = True
    validation_reference: str | None = None
    rollback_reference: str | None = None
    runtime_gate_reference: str | None = None
    deterministic_fallback_available: bool = True
    phase4i_recommendation_contract_preserved: bool = True
    runtime_activation_requested: bool = False
    runtime_activation_approved: bool = False
    runtime_active: bool = False
    recommendation_rule_applied: bool = False
    created_by: str | None = None
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.manifest_id, "manifest_id")
        _require_nonempty_string(self.package_id, "package_id")
        _require_nonempty_string(self.manifest_version, "manifest_version")
        _require_supported(
            self.activation_mode,
            RECOMMENDATION_RUNTIME_ACTIVATION_MODES,
            "activation_mode",
        )
        _require_true(
            self.explicit_activation_required,
            "explicit_activation_required",
        )
        _require_optional_string(self.validation_reference, "validation_reference")
        _require_optional_string(self.rollback_reference, "rollback_reference")
        _require_optional_string(self.runtime_gate_reference, "runtime_gate_reference")
        _require_true(
            self.deterministic_fallback_available,
            "deterministic_fallback_available",
        )
        _require_true(
            self.phase4i_recommendation_contract_preserved,
            "phase4i_recommendation_contract_preserved",
        )
        _require_false(
            self.runtime_activation_requested,
            "runtime_activation_requested",
        )
        _require_false(
            self.runtime_activation_approved,
            "runtime_activation_approved",
        )
        _require_false(self.runtime_active, "runtime_active")
        _require_false(
            self.recommendation_rule_applied,
            "recommendation_rule_applied",
        )
        _require_optional_string(self.created_by, "created_by")
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class RecommendationRuntimeEligibilityRecord:
    """Local eligibility result for a recommendation runtime rule package."""

    eligibility_id: str
    package_id: str
    manifest_id: str
    eligible: bool
    eligibility_status: str
    required_validation_present: bool
    regression_reference_present: bool
    before_after_reference_present: bool
    evidence_mapping_validation_present: bool
    action_sequence_validation_present: bool
    risk_label_validation_present: bool
    phase4i_recommendation_contract_reference_present: bool
    rollback_reference_present: bool
    runtime_gate_reference_present: bool
    deterministic_fallback_available: bool
    runtime_active: bool = False
    recommendation_rule_applied: bool = False
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
            RECOMMENDATION_RUNTIME_ELIGIBILITY_STATUSES,
            "eligibility_status",
        )
        _require_boolean(
            self.required_validation_present,
            "required_validation_present",
        )
        _require_boolean(
            self.regression_reference_present,
            "regression_reference_present",
        )
        _require_boolean(
            self.before_after_reference_present,
            "before_after_reference_present",
        )
        _require_boolean(
            self.evidence_mapping_validation_present,
            "evidence_mapping_validation_present",
        )
        _require_boolean(
            self.action_sequence_validation_present,
            "action_sequence_validation_present",
        )
        _require_boolean(
            self.risk_label_validation_present,
            "risk_label_validation_present",
        )
        _require_boolean(
            self.phase4i_recommendation_contract_reference_present,
            "phase4i_recommendation_contract_reference_present",
        )
        _require_boolean(
            self.rollback_reference_present,
            "rollback_reference_present",
        )
        _require_boolean(
            self.runtime_gate_reference_present,
            "runtime_gate_reference_present",
        )
        _require_true(
            self.deterministic_fallback_available,
            "deterministic_fallback_available",
        )
        _require_false(self.runtime_active, "runtime_active")
        _require_false(
            self.recommendation_rule_applied,
            "recommendation_rule_applied",
        )
        _require_list_of_strings(self.denied_reasons, "denied_reasons")
        _require_list_of_strings(self.warnings, "warnings")
        _require_list_of_strings(self.required_next_steps, "required_next_steps")
        _require_optional_string(self.notes, "notes")
        if self.eligible:
            if self.eligibility_status != "eligible_metadata_only":
                raise RecommendationRuntimeActivationError(
                    "eligible metadata must use eligible_metadata_only status."
                )
            missing = [
                not self.required_validation_present,
                not self.regression_reference_present,
                not self.before_after_reference_present,
                not self.evidence_mapping_validation_present,
                not self.action_sequence_validation_present,
                not self.risk_label_validation_present,
                not self.phase4i_recommendation_contract_reference_present,
                not self.rollback_reference_present,
                not self.runtime_gate_reference_present,
            ]
            if any(missing):
                raise RecommendationRuntimeActivationError(
                    "eligible metadata requires all validation references."
                )


@dataclass(frozen=True)
class RecommendationRollbackReference:
    """Local rollback metadata for a future recommendation runtime rule update."""

    rollback_id: str
    package_id: str
    rollback_strategy: str
    rollback_reference: str
    rollback_validated: bool = False
    rollback_executed: bool = False
    recommendation_rule_reverted: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.rollback_id, "rollback_id")
        _require_nonempty_string(self.package_id, "package_id")
        _require_nonempty_string(self.rollback_strategy, "rollback_strategy")
        _require_nonempty_string(self.rollback_reference, "rollback_reference")
        _require_boolean(self.rollback_validated, "rollback_validated")
        _require_false(self.rollback_executed, "rollback_executed")
        _require_false(
            self.recommendation_rule_reverted,
            "recommendation_rule_reverted",
        )
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class RecommendationRegressionEvidence:
    """Local regression evidence metadata for future recommendation rule review."""

    regression_id: str
    package_id: str
    test_suite_reference: str
    before_after_reference: str
    evidence_mapping_validation_reference: str
    action_sequence_validation_reference: str
    risk_label_validation_reference: str
    recommendation_contract_reference: str
    regression_passed: bool
    evidence_mapping_valid: bool
    action_sequence_valid: bool
    risk_label_valid: bool
    phase4i_contract_preserved: bool
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.regression_id, "regression_id")
        _require_nonempty_string(self.package_id, "package_id")
        _require_nonempty_string(self.test_suite_reference, "test_suite_reference")
        _require_nonempty_string(self.before_after_reference, "before_after_reference")
        _require_nonempty_string(
            self.evidence_mapping_validation_reference,
            "evidence_mapping_validation_reference",
        )
        _require_nonempty_string(
            self.action_sequence_validation_reference,
            "action_sequence_validation_reference",
        )
        _require_nonempty_string(
            self.risk_label_validation_reference,
            "risk_label_validation_reference",
        )
        _require_nonempty_string(
            self.recommendation_contract_reference,
            "recommendation_contract_reference",
        )
        _require_boolean(self.regression_passed, "regression_passed")
        _require_true(self.evidence_mapping_valid, "evidence_mapping_valid")
        _require_true(self.action_sequence_valid, "action_sequence_valid")
        _require_true(self.risk_label_valid, "risk_label_valid")
        _require_true(
            self.phase4i_contract_preserved,
            "phase4i_contract_preserved",
        )
        _require_optional_string(self.notes, "notes")


def create_recommendation_runtime_package_id(
    source_recommendation_evolution_id: str,
    recommendation_rule_version: str,
) -> str:
    """Create a deterministic recommendation runtime package id."""

    _require_nonempty_string(
        source_recommendation_evolution_id,
        "source_recommendation_evolution_id",
    )
    _require_nonempty_string(
        recommendation_rule_version,
        "recommendation_rule_version",
    )
    return (
        "RECOMMENDATION-RUNTIME-PACKAGE-"
        f"{_normalize_token(source_recommendation_evolution_id)}-"
        f"{_normalize_token(recommendation_rule_version)}"
    )


def create_recommendation_activation_manifest_id(
    package_id: str,
    manifest_version: str,
) -> str:
    """Create a deterministic recommendation activation manifest id."""

    _require_nonempty_string(package_id, "package_id")
    _require_nonempty_string(manifest_version, "manifest_version")
    return (
        "RECOMMENDATION-RUNTIME-MANIFEST-"
        f"{_normalize_token(package_id)}-"
        f"{_normalize_token(manifest_version)}"
    )


def create_recommendation_runtime_eligibility_id(
    package_id: str,
    manifest_id: str,
) -> str:
    """Create a deterministic recommendation runtime eligibility id."""

    _require_nonempty_string(package_id, "package_id")
    _require_nonempty_string(manifest_id, "manifest_id")
    return (
        "RECOMMENDATION-RUNTIME-ELIGIBILITY-"
        f"{_normalize_token(package_id)}-"
        f"{_normalize_token(manifest_id)}"
    )


def create_recommendation_rollback_id(
    package_id: str,
    rollback_strategy: str,
) -> str:
    """Create a deterministic recommendation rollback id."""

    _require_nonempty_string(package_id, "package_id")
    _require_nonempty_string(rollback_strategy, "rollback_strategy")
    return (
        "RECOMMENDATION-RUNTIME-ROLLBACK-"
        f"{_normalize_token(package_id)}-"
        f"{_normalize_token(rollback_strategy)}"
    )


def create_recommendation_regression_id(package_id: str, reference: str) -> str:
    """Create a deterministic recommendation regression evidence id."""

    _require_nonempty_string(package_id, "package_id")
    _require_nonempty_string(reference, "reference")
    return (
        "RECOMMENDATION-REGRESSION-"
        f"{_normalize_token(package_id)}-"
        f"{_normalize_token(reference)}"
    )


def validate_recommendation_runtime_rule_package(
    package: RecommendationRuntimeRulePackage,
) -> RecommendationRuntimeRulePackage:
    """Validate recommendation runtime rule package metadata without applying it."""

    if not isinstance(package, RecommendationRuntimeRulePackage):
        raise RecommendationRuntimeActivationError(
            "package must be a RecommendationRuntimeRulePackage instance."
        )
    package.__post_init__()
    return package


def validate_recommendation_activation_manifest(
    manifest: RecommendationActivationManifest,
) -> RecommendationActivationManifest:
    """Validate recommendation activation manifest metadata without activation."""

    if not isinstance(manifest, RecommendationActivationManifest):
        raise RecommendationRuntimeActivationError(
            "manifest must be a RecommendationActivationManifest instance."
        )
    manifest.__post_init__()
    return manifest


def validate_recommendation_runtime_eligibility_record(
    record: RecommendationRuntimeEligibilityRecord,
) -> RecommendationRuntimeEligibilityRecord:
    """Validate recommendation runtime eligibility metadata without activation."""

    if not isinstance(record, RecommendationRuntimeEligibilityRecord):
        raise RecommendationRuntimeActivationError(
            "record must be a RecommendationRuntimeEligibilityRecord instance."
        )
    record.__post_init__()
    return record


def validate_recommendation_rollback_reference(
    rollback: RecommendationRollbackReference,
) -> RecommendationRollbackReference:
    """Validate recommendation rollback metadata without executing rollback."""

    if not isinstance(rollback, RecommendationRollbackReference):
        raise RecommendationRuntimeActivationError(
            "rollback must be a RecommendationRollbackReference instance."
        )
    rollback.__post_init__()
    return rollback


def validate_recommendation_regression_evidence(
    evidence: RecommendationRegressionEvidence,
) -> RecommendationRegressionEvidence:
    """Validate recommendation regression evidence metadata without running tests."""

    if not isinstance(evidence, RecommendationRegressionEvidence):
        raise RecommendationRuntimeActivationError(
            "evidence must be a RecommendationRegressionEvidence instance."
        )
    evidence.__post_init__()
    return evidence


def evaluate_recommendation_runtime_eligibility(
    package: RecommendationRuntimeRulePackage,
    manifest: RecommendationActivationManifest,
) -> RecommendationRuntimeEligibilityRecord:
    """Evaluate recommendation package eligibility as metadata only."""

    package = validate_recommendation_runtime_rule_package(package)
    manifest = validate_recommendation_activation_manifest(manifest)

    denied_reasons: list[str] = []
    warnings = [
        "Phase 7BX eligibility is metadata only; recommendation_rule_applied=false.",
        "Runtime recommendations remain inactive; runtime_active=false.",
        "Deterministic recommendation fallback remains required.",
    ]
    required_next_steps: list[str] = []

    regression_reference_present = bool(_optional_text(package.regression_reference))
    before_after_reference_present = bool(_optional_text(package.before_after_reference))
    evidence_mapping_validation_present = bool(
        _optional_text(package.evidence_mapping_validation_reference)
    )
    action_sequence_validation_present = bool(
        _optional_text(package.action_sequence_validation_reference)
    )
    risk_label_validation_present = bool(
        _optional_text(package.risk_label_validation_reference)
    )
    phase4i_recommendation_contract_reference_present = bool(
        _optional_text(package.phase4i_recommendation_contract_reference)
    )
    rollback_reference_present = bool(
        _optional_text(package.rollback_reference)
        and _optional_text(manifest.rollback_reference)
    )
    runtime_gate_reference_present = bool(
        _optional_text(manifest.runtime_gate_reference)
    )
    required_validation_present = bool(_optional_text(manifest.validation_reference))

    eligibility_status = "eligible_metadata_only"
    if package.package_status != ELIGIBILITY_PACKAGE_STATUS:
        eligibility_status = "not_eligible"
        denied_reasons.append(
            "package_status must be eligible_for_runtime_review for metadata eligibility"
        )
        required_next_steps.append("advance package metadata through governance review")
    elif not regression_reference_present:
        eligibility_status = "needs_regression_reference"
        denied_reasons.append("regression_reference is required")
        required_next_steps.append("attach recommendation regression evidence reference")
    elif not before_after_reference_present:
        eligibility_status = "needs_before_after_reference"
        denied_reasons.append("before_after_reference is required")
        required_next_steps.append("attach before/after comparison reference")
    elif not evidence_mapping_validation_present:
        eligibility_status = "needs_evidence_mapping_validation"
        denied_reasons.append("evidence_mapping_validation_reference is required")
        required_next_steps.append("attach evidence mapping validation reference")
    elif not action_sequence_validation_present:
        eligibility_status = "needs_action_sequence_validation"
        denied_reasons.append("action_sequence_validation_reference is required")
        required_next_steps.append("attach action sequence validation reference")
    elif not risk_label_validation_present:
        eligibility_status = "needs_risk_label_validation"
        denied_reasons.append("risk_label_validation_reference is required")
        required_next_steps.append("attach risk label validation reference")
    elif not phase4i_recommendation_contract_reference_present:
        eligibility_status = "needs_phase4i_recommendation_contract"
        denied_reasons.append("phase4i_recommendation_contract_reference is required")
        required_next_steps.append("attach Phase 4I recommendation contract evidence")
    elif not rollback_reference_present:
        eligibility_status = "needs_rollback_reference"
        denied_reasons.append("rollback_reference is required on package and manifest")
        required_next_steps.append("attach rollback reference metadata")
    elif not runtime_gate_reference_present:
        eligibility_status = "needs_runtime_gate"
        denied_reasons.append("runtime_gate_reference is required")
        required_next_steps.append("attach runtime gate review reference")
    elif not required_validation_present:
        eligibility_status = "needs_phase4i_recommendation_contract"
        denied_reasons.append("manifest validation_reference is required")
        required_next_steps.append("attach manifest validation reference")
    else:
        required_next_steps.append("future runtime review may consider this package")
        required_next_steps.append("explicit activation remains required in a future phase")

    eligible = eligibility_status == "eligible_metadata_only"
    return validate_recommendation_runtime_eligibility_record(
        RecommendationRuntimeEligibilityRecord(
            eligibility_id=create_recommendation_runtime_eligibility_id(
                package.package_id,
                manifest.manifest_id,
            ),
            package_id=package.package_id,
            manifest_id=manifest.manifest_id,
            eligible=eligible,
            eligibility_status=eligibility_status,
            required_validation_present=required_validation_present,
            regression_reference_present=regression_reference_present,
            before_after_reference_present=before_after_reference_present,
            evidence_mapping_validation_present=evidence_mapping_validation_present,
            action_sequence_validation_present=action_sequence_validation_present,
            risk_label_validation_present=risk_label_validation_present,
            phase4i_recommendation_contract_reference_present=(
                phase4i_recommendation_contract_reference_present
            ),
            rollback_reference_present=rollback_reference_present,
            runtime_gate_reference_present=runtime_gate_reference_present,
            deterministic_fallback_available=True,
            runtime_active=False,
            recommendation_rule_applied=False,
            denied_reasons=denied_reasons,
            warnings=warnings,
            required_next_steps=required_next_steps,
            notes=package.notes,
        )
    )


def recommendation_runtime_rule_package_to_dict(
    package: RecommendationRuntimeRulePackage,
) -> dict[str, Any]:
    """Serialize recommendation runtime rule package metadata."""

    package.__post_init__()
    return {
        "package_id": package.package_id,
        "source_recommendation_evolution_id": (
            package.source_recommendation_evolution_id
        ),
        "source_materialization_id": package.source_materialization_id,
        "recommendation_rule_version": package.recommendation_rule_version,
        "affected_domains": list(package.affected_domains),
        "affected_components": list(package.affected_components),
        "rule_type": package.rule_type,
        "proposed_rule_summary": package.proposed_rule_summary,
        "wording_changes": dict(package.wording_changes),
        "priority_changes": dict(package.priority_changes),
        "evidence_mapping_changes": dict(package.evidence_mapping_changes),
        "action_sequence_changes": dict(package.action_sequence_changes),
        "risk_label_changes": dict(package.risk_label_changes),
        "suppression_rule_changes": dict(package.suppression_rule_changes),
        "escalation_rule_changes": dict(package.escalation_rule_changes),
        "before_after_reference": package.before_after_reference,
        "regression_reference": package.regression_reference,
        "evidence_mapping_validation_reference": (
            package.evidence_mapping_validation_reference
        ),
        "action_sequence_validation_reference": (
            package.action_sequence_validation_reference
        ),
        "risk_label_validation_reference": package.risk_label_validation_reference,
        "phase4i_recommendation_contract_reference": (
            package.phase4i_recommendation_contract_reference
        ),
        "rollback_reference": package.rollback_reference,
        "package_status": package.package_status,
        "runtime_eligible": package.runtime_eligible,
        "runtime_active": package.runtime_active,
        "recommendation_rule_applied": package.recommendation_rule_applied,
        "recommendation_output_mutation_performed": (
            package.recommendation_output_mutation_performed
        ),
        "phase4i_mutation_performed": package.phase4i_mutation_performed,
        "created_by": package.created_by,
        "created_at": package.created_at,
        "notes": package.notes,
    }


def recommendation_runtime_rule_package_from_dict(
    data: dict[str, Any],
) -> RecommendationRuntimeRulePackage:
    """Deserialize recommendation runtime rule package metadata."""

    _require_mapping(data, "data")
    return RecommendationRuntimeRulePackage(
        package_id=str(data["package_id"]),
        source_recommendation_evolution_id=str(
            data["source_recommendation_evolution_id"]
        ),
        source_materialization_id=str(data["source_materialization_id"]),
        recommendation_rule_version=str(data["recommendation_rule_version"]),
        affected_domains=list(data.get("affected_domains") or []),
        affected_components=list(data.get("affected_components") or []),
        rule_type=str(data.get("rule_type", "unknown")),
        proposed_rule_summary=str(data["proposed_rule_summary"]),
        wording_changes=dict(data.get("wording_changes") or {}),
        priority_changes=dict(data.get("priority_changes") or {}),
        evidence_mapping_changes=dict(data.get("evidence_mapping_changes") or {}),
        action_sequence_changes=dict(data.get("action_sequence_changes") or {}),
        risk_label_changes=dict(data.get("risk_label_changes") or {}),
        suppression_rule_changes=dict(data.get("suppression_rule_changes") or {}),
        escalation_rule_changes=dict(data.get("escalation_rule_changes") or {}),
        before_after_reference=_optional_text(data.get("before_after_reference")),
        regression_reference=_optional_text(data.get("regression_reference")),
        evidence_mapping_validation_reference=_optional_text(
            data.get("evidence_mapping_validation_reference")
        ),
        action_sequence_validation_reference=_optional_text(
            data.get("action_sequence_validation_reference")
        ),
        risk_label_validation_reference=_optional_text(
            data.get("risk_label_validation_reference")
        ),
        phase4i_recommendation_contract_reference=_optional_text(
            data.get("phase4i_recommendation_contract_reference")
        ),
        rollback_reference=_optional_text(data.get("rollback_reference")),
        package_status=str(data.get("package_status", "proposed")),
        runtime_eligible=_bool_from_mapping(data, "runtime_eligible", False),
        runtime_active=_bool_from_mapping(data, "runtime_active", False),
        recommendation_rule_applied=_bool_from_mapping(
            data,
            "recommendation_rule_applied",
            False,
        ),
        recommendation_output_mutation_performed=_bool_from_mapping(
            data,
            "recommendation_output_mutation_performed",
            False,
        ),
        phase4i_mutation_performed=_bool_from_mapping(
            data,
            "phase4i_mutation_performed",
            False,
        ),
        created_by=_optional_text(data.get("created_by")),
        created_at=_optional_text(data.get("created_at")),
        notes=_optional_text(data.get("notes")),
    )


def recommendation_activation_manifest_to_dict(
    manifest: RecommendationActivationManifest,
) -> dict[str, Any]:
    """Serialize recommendation activation manifest metadata."""

    manifest.__post_init__()
    return {
        "manifest_id": manifest.manifest_id,
        "package_id": manifest.package_id,
        "manifest_version": manifest.manifest_version,
        "activation_mode": manifest.activation_mode,
        "explicit_activation_required": manifest.explicit_activation_required,
        "validation_reference": manifest.validation_reference,
        "rollback_reference": manifest.rollback_reference,
        "runtime_gate_reference": manifest.runtime_gate_reference,
        "deterministic_fallback_available": (
            manifest.deterministic_fallback_available
        ),
        "phase4i_recommendation_contract_preserved": (
            manifest.phase4i_recommendation_contract_preserved
        ),
        "runtime_activation_requested": manifest.runtime_activation_requested,
        "runtime_activation_approved": manifest.runtime_activation_approved,
        "runtime_active": manifest.runtime_active,
        "recommendation_rule_applied": manifest.recommendation_rule_applied,
        "created_by": manifest.created_by,
        "created_at": manifest.created_at,
        "notes": manifest.notes,
    }


def recommendation_activation_manifest_from_dict(
    data: dict[str, Any],
) -> RecommendationActivationManifest:
    """Deserialize recommendation activation manifest metadata."""

    _require_mapping(data, "data")
    return RecommendationActivationManifest(
        manifest_id=str(data["manifest_id"]),
        package_id=str(data["package_id"]),
        manifest_version=str(data["manifest_version"]),
        activation_mode=str(data.get("activation_mode", DEFAULT_ACTIVATION_MODE)),
        explicit_activation_required=_bool_from_mapping(
            data,
            "explicit_activation_required",
            True,
        ),
        validation_reference=_optional_text(data.get("validation_reference")),
        rollback_reference=_optional_text(data.get("rollback_reference")),
        runtime_gate_reference=_optional_text(data.get("runtime_gate_reference")),
        deterministic_fallback_available=_bool_from_mapping(
            data,
            "deterministic_fallback_available",
            True,
        ),
        phase4i_recommendation_contract_preserved=_bool_from_mapping(
            data,
            "phase4i_recommendation_contract_preserved",
            True,
        ),
        runtime_activation_requested=_bool_from_mapping(
            data,
            "runtime_activation_requested",
            False,
        ),
        runtime_activation_approved=_bool_from_mapping(
            data,
            "runtime_activation_approved",
            False,
        ),
        runtime_active=_bool_from_mapping(data, "runtime_active", False),
        recommendation_rule_applied=_bool_from_mapping(
            data,
            "recommendation_rule_applied",
            False,
        ),
        created_by=_optional_text(data.get("created_by")),
        created_at=_optional_text(data.get("created_at")),
        notes=_optional_text(data.get("notes")),
    )


def recommendation_runtime_eligibility_record_to_dict(
    record: RecommendationRuntimeEligibilityRecord,
) -> dict[str, Any]:
    """Serialize recommendation runtime eligibility metadata."""

    record.__post_init__()
    return {
        "eligibility_id": record.eligibility_id,
        "package_id": record.package_id,
        "manifest_id": record.manifest_id,
        "eligible": record.eligible,
        "eligibility_status": record.eligibility_status,
        "required_validation_present": record.required_validation_present,
        "regression_reference_present": record.regression_reference_present,
        "before_after_reference_present": record.before_after_reference_present,
        "evidence_mapping_validation_present": (
            record.evidence_mapping_validation_present
        ),
        "action_sequence_validation_present": (
            record.action_sequence_validation_present
        ),
        "risk_label_validation_present": record.risk_label_validation_present,
        "phase4i_recommendation_contract_reference_present": (
            record.phase4i_recommendation_contract_reference_present
        ),
        "rollback_reference_present": record.rollback_reference_present,
        "runtime_gate_reference_present": record.runtime_gate_reference_present,
        "deterministic_fallback_available": record.deterministic_fallback_available,
        "runtime_active": record.runtime_active,
        "recommendation_rule_applied": record.recommendation_rule_applied,
        "denied_reasons": list(record.denied_reasons),
        "warnings": list(record.warnings),
        "required_next_steps": list(record.required_next_steps),
        "notes": record.notes,
    }


def recommendation_runtime_eligibility_record_from_dict(
    data: dict[str, Any],
) -> RecommendationRuntimeEligibilityRecord:
    """Deserialize recommendation runtime eligibility metadata."""

    _require_mapping(data, "data")
    return RecommendationRuntimeEligibilityRecord(
        eligibility_id=str(data["eligibility_id"]),
        package_id=str(data["package_id"]),
        manifest_id=str(data["manifest_id"]),
        eligible=_bool_from_mapping(data, "eligible", False),
        eligibility_status=str(data["eligibility_status"]),
        required_validation_present=_bool_from_mapping(
            data,
            "required_validation_present",
            False,
        ),
        regression_reference_present=_bool_from_mapping(
            data,
            "regression_reference_present",
            False,
        ),
        before_after_reference_present=_bool_from_mapping(
            data,
            "before_after_reference_present",
            False,
        ),
        evidence_mapping_validation_present=_bool_from_mapping(
            data,
            "evidence_mapping_validation_present",
            False,
        ),
        action_sequence_validation_present=_bool_from_mapping(
            data,
            "action_sequence_validation_present",
            False,
        ),
        risk_label_validation_present=_bool_from_mapping(
            data,
            "risk_label_validation_present",
            False,
        ),
        phase4i_recommendation_contract_reference_present=_bool_from_mapping(
            data,
            "phase4i_recommendation_contract_reference_present",
            False,
        ),
        rollback_reference_present=_bool_from_mapping(
            data,
            "rollback_reference_present",
            False,
        ),
        runtime_gate_reference_present=_bool_from_mapping(
            data,
            "runtime_gate_reference_present",
            False,
        ),
        deterministic_fallback_available=_bool_from_mapping(
            data,
            "deterministic_fallback_available",
            True,
        ),
        runtime_active=_bool_from_mapping(data, "runtime_active", False),
        recommendation_rule_applied=_bool_from_mapping(
            data,
            "recommendation_rule_applied",
            False,
        ),
        denied_reasons=list(data.get("denied_reasons") or []),
        warnings=list(data.get("warnings") or []),
        required_next_steps=list(data.get("required_next_steps") or []),
        notes=_optional_text(data.get("notes")),
    )


def recommendation_rollback_reference_to_dict(
    rollback: RecommendationRollbackReference,
) -> dict[str, Any]:
    """Serialize recommendation rollback metadata."""

    rollback.__post_init__()
    return {
        "rollback_id": rollback.rollback_id,
        "package_id": rollback.package_id,
        "rollback_strategy": rollback.rollback_strategy,
        "rollback_reference": rollback.rollback_reference,
        "rollback_validated": rollback.rollback_validated,
        "rollback_executed": rollback.rollback_executed,
        "recommendation_rule_reverted": rollback.recommendation_rule_reverted,
        "notes": rollback.notes,
    }


def recommendation_rollback_reference_from_dict(
    data: dict[str, Any],
) -> RecommendationRollbackReference:
    """Deserialize recommendation rollback metadata."""

    _require_mapping(data, "data")
    return RecommendationRollbackReference(
        rollback_id=str(data["rollback_id"]),
        package_id=str(data["package_id"]),
        rollback_strategy=str(data["rollback_strategy"]),
        rollback_reference=str(data["rollback_reference"]),
        rollback_validated=_bool_from_mapping(data, "rollback_validated", False),
        rollback_executed=_bool_from_mapping(data, "rollback_executed", False),
        recommendation_rule_reverted=_bool_from_mapping(
            data,
            "recommendation_rule_reverted",
            False,
        ),
        notes=_optional_text(data.get("notes")),
    )


def recommendation_regression_evidence_to_dict(
    evidence: RecommendationRegressionEvidence,
) -> dict[str, Any]:
    """Serialize recommendation regression evidence metadata."""

    evidence.__post_init__()
    return {
        "regression_id": evidence.regression_id,
        "package_id": evidence.package_id,
        "test_suite_reference": evidence.test_suite_reference,
        "before_after_reference": evidence.before_after_reference,
        "evidence_mapping_validation_reference": (
            evidence.evidence_mapping_validation_reference
        ),
        "action_sequence_validation_reference": (
            evidence.action_sequence_validation_reference
        ),
        "risk_label_validation_reference": evidence.risk_label_validation_reference,
        "recommendation_contract_reference": (
            evidence.recommendation_contract_reference
        ),
        "regression_passed": evidence.regression_passed,
        "evidence_mapping_valid": evidence.evidence_mapping_valid,
        "action_sequence_valid": evidence.action_sequence_valid,
        "risk_label_valid": evidence.risk_label_valid,
        "phase4i_contract_preserved": evidence.phase4i_contract_preserved,
        "notes": evidence.notes,
    }


def recommendation_regression_evidence_from_dict(
    data: dict[str, Any],
) -> RecommendationRegressionEvidence:
    """Deserialize recommendation regression evidence metadata."""

    _require_mapping(data, "data")
    return RecommendationRegressionEvidence(
        regression_id=str(data["regression_id"]),
        package_id=str(data["package_id"]),
        test_suite_reference=str(data["test_suite_reference"]),
        before_after_reference=str(data["before_after_reference"]),
        evidence_mapping_validation_reference=str(
            data["evidence_mapping_validation_reference"]
        ),
        action_sequence_validation_reference=str(
            data["action_sequence_validation_reference"]
        ),
        risk_label_validation_reference=str(data["risk_label_validation_reference"]),
        recommendation_contract_reference=str(
            data["recommendation_contract_reference"]
        ),
        regression_passed=_bool_from_mapping(data, "regression_passed", False),
        evidence_mapping_valid=_bool_from_mapping(
            data,
            "evidence_mapping_valid",
            True,
        ),
        action_sequence_valid=_bool_from_mapping(
            data,
            "action_sequence_valid",
            True,
        ),
        risk_label_valid=_bool_from_mapping(data, "risk_label_valid", True),
        phase4i_contract_preserved=_bool_from_mapping(
            data,
            "phase4i_contract_preserved",
            True,
        ),
        notes=_optional_text(data.get("notes")),
    )


def _package_has_all_eligibility_metadata(
    package: RecommendationRuntimeRulePackage,
) -> bool:
    return (
        package.package_status == ELIGIBILITY_PACKAGE_STATUS
        and bool(_optional_text(package.regression_reference))
        and bool(_optional_text(package.before_after_reference))
        and bool(_optional_text(package.evidence_mapping_validation_reference))
        and bool(_optional_text(package.action_sequence_validation_reference))
        and bool(_optional_text(package.risk_label_validation_reference))
        and bool(_optional_text(package.phase4i_recommendation_contract_reference))
        and bool(_optional_text(package.rollback_reference))
    )


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _bool_from_mapping(data: dict[str, Any], field_name: str, default: bool) -> bool:
    value = data.get(field_name, default)
    if isinstance(value, bool):
        return value
    raise RecommendationRuntimeActivationError(f"{field_name} must be a boolean.")


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise RecommendationRuntimeActivationError(f"{field_name} must be a mapping.")


def _require_nonempty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise RecommendationRuntimeActivationError(
            f"{field_name} must be a non-empty string."
        )


def _require_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise RecommendationRuntimeActivationError(
            f"{field_name} must be a string or None."
        )


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        raise RecommendationRuntimeActivationError(
            f"{field_name} must be one of: {', '.join(supported)}."
        )


def _require_boolean(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise RecommendationRuntimeActivationError(f"{field_name} must be a boolean.")


def _require_true(value: Any, field_name: str) -> None:
    _require_boolean(value, field_name)
    if not value:
        raise RecommendationRuntimeActivationError(
            f"{field_name} must remain true in Phase 7BX."
        )


def _require_false(value: Any, field_name: str) -> None:
    _require_boolean(value, field_name)
    if value:
        raise RecommendationRuntimeActivationError(
            f"{field_name} must remain false in Phase 7BX."
        )


def _require_list_of_strings(value: Any, field_name: str) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise RecommendationRuntimeActivationError(
            f"{field_name} must be a list of strings."
        )


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text).strip("-")
    return text or "NONE"
