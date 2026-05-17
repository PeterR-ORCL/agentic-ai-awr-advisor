"""Phase 7BV parser runtime update path metadata.

This module defines local-only parser runtime update package, manifest,
eligibility, and rollback metadata. It validates future parser update envelopes
without importing parser runtime modules, changing parser code or config,
mutating parser output, invoking runtime parsing, activating runtime, or
mutating Phase 4I.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


PARSER_RUNTIME_UPDATE_TYPES = (
    "new_section_mapping",
    "section_mapping_refinement",
    "unknown_signal_mapping",
    "regex_pattern_review",
    "normalization_rule_review",
    "field_extraction_review",
    "unit_conversion_review",
    "parser_confidence_metadata_review",
    "section_registry_review",
    "parser_regression_test_addition",
)

PARSER_RUNTIME_PACKAGE_STATUSES = (
    "proposed",
    "under_review",
    "validation_required",
    "validation_ready",
    "eligible_for_runtime_review",
    "rejected",
    "superseded",
    "closed",
)

PARSER_RUNTIME_ELIGIBILITY_STATUSES = (
    "not_eligible",
    "eligible_metadata_only",
    "needs_parser_tests",
    "needs_awr_regression",
    "needs_phase4i_validation",
    "needs_scoring_regression",
    "needs_rollback_reference",
    "needs_runtime_gate",
    "blocked_by_safety",
)

PARSER_RUNTIME_ACTIVATION_MODES = (
    "disabled",
    "manual_review_required",
    "future_runtime_manifest",
    "emergency_disabled",
)

ELIGIBILITY_PACKAGE_STATUS = "eligible_for_runtime_review"
DEFAULT_ACTIVATION_MODE = "manual_review_required"


class ParserRuntimeUpdatePathError(ValueError):
    """Raised when Phase 7BV parser update metadata is invalid."""


@dataclass(frozen=True)
class ParserRuntimeUpdatePackage:
    """Local metadata package for future parser runtime update eligibility."""

    package_id: str
    source_parser_evolution_id: str
    source_materialization_id: str
    parser_section: str
    signal_name: str
    update_type: str
    proposed_change_summary: str
    affected_files: list[str] = field(default_factory=list)
    affected_patterns: list[str] = field(default_factory=list)
    validation_requirements: list[str] = field(default_factory=list)
    parser_tests_reference: str | None = None
    awr_regression_reference: str | None = None
    phase4i_validation_reference: str | None = None
    scoring_regression_reference: str | None = None
    rollback_reference: str | None = None
    package_status: str = "proposed"
    runtime_eligible: bool = False
    runtime_active: bool = False
    parser_update_applied: bool = False
    parser_output_mutation_performed: bool = False
    phase4i_mutation_performed: bool = False
    created_by: str | None = None
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.package_id, "package_id")
        _require_nonempty_string(
            self.source_parser_evolution_id,
            "source_parser_evolution_id",
        )
        _require_nonempty_string(
            self.source_materialization_id,
            "source_materialization_id",
        )
        _require_nonempty_string(self.parser_section, "parser_section")
        _require_nonempty_string(self.signal_name, "signal_name")
        _require_supported(self.update_type, PARSER_RUNTIME_UPDATE_TYPES, "update_type")
        _require_nonempty_string(
            self.proposed_change_summary,
            "proposed_change_summary",
        )
        _require_list_of_strings(self.affected_files, "affected_files")
        _require_list_of_strings(self.affected_patterns, "affected_patterns")
        _require_list_of_strings(
            self.validation_requirements,
            "validation_requirements",
        )
        _require_optional_string(self.parser_tests_reference, "parser_tests_reference")
        _require_optional_string(
            self.awr_regression_reference,
            "awr_regression_reference",
        )
        _require_optional_string(
            self.phase4i_validation_reference,
            "phase4i_validation_reference",
        )
        _require_optional_string(
            self.scoring_regression_reference,
            "scoring_regression_reference",
        )
        _require_optional_string(self.rollback_reference, "rollback_reference")
        _require_supported(
            self.package_status,
            PARSER_RUNTIME_PACKAGE_STATUSES,
            "package_status",
        )
        _require_boolean(self.runtime_eligible, "runtime_eligible")
        _require_false(self.runtime_active, "runtime_active")
        _require_false(self.parser_update_applied, "parser_update_applied")
        _require_false(
            self.parser_output_mutation_performed,
            "parser_output_mutation_performed",
        )
        _require_false(
            self.phase4i_mutation_performed,
            "phase4i_mutation_performed",
        )
        _require_optional_string(self.created_by, "created_by")
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")
        if self.package_status in (
            "validation_ready",
            "eligible_for_runtime_review",
        ):
            _require_nonempty_string(self.rollback_reference, "rollback_reference")
        if self.runtime_eligible and not _package_has_all_eligibility_metadata(self):
            raise ParserRuntimeUpdatePathError(
                "runtime_eligible metadata requires all validation references, "
                "rollback reference, and eligible_for_runtime_review status."
            )


@dataclass(frozen=True)
class ParserRuntimeUpdateManifest:
    """Local manifest metadata for future parser update activation review."""

    manifest_id: str
    package_id: str
    manifest_version: str
    activation_mode: str = DEFAULT_ACTIVATION_MODE
    explicit_activation_required: bool = True
    validation_reference: str | None = None
    rollback_reference: str | None = None
    runtime_gate_reference: str | None = None
    deterministic_fallback_available: bool = True
    phase4i_contract_preserved: bool = True
    runtime_activation_requested: bool = False
    runtime_activation_approved: bool = False
    runtime_active: bool = False
    parser_update_applied: bool = False
    created_by: str | None = None
    created_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.manifest_id, "manifest_id")
        _require_nonempty_string(self.package_id, "package_id")
        _require_nonempty_string(self.manifest_version, "manifest_version")
        _require_supported(
            self.activation_mode,
            PARSER_RUNTIME_ACTIVATION_MODES,
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
        _require_false(self.parser_update_applied, "parser_update_applied")
        _require_optional_string(self.created_by, "created_by")
        _require_optional_string(self.created_at, "created_at")
        _require_optional_string(self.notes, "notes")


@dataclass(frozen=True)
class ParserRuntimeEligibilityRecord:
    """Local eligibility result for a parser runtime update package."""

    eligibility_id: str
    package_id: str
    manifest_id: str
    eligible: bool
    eligibility_status: str
    required_validation_present: bool
    parser_tests_present: bool
    awr_regression_present: bool
    phase4i_validation_present: bool
    scoring_regression_present: bool
    rollback_reference_present: bool
    runtime_gate_reference_present: bool
    deterministic_fallback_available: bool
    runtime_active: bool = False
    parser_update_applied: bool = False
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
            PARSER_RUNTIME_ELIGIBILITY_STATUSES,
            "eligibility_status",
        )
        _require_boolean(
            self.required_validation_present,
            "required_validation_present",
        )
        _require_boolean(self.parser_tests_present, "parser_tests_present")
        _require_boolean(self.awr_regression_present, "awr_regression_present")
        _require_boolean(
            self.phase4i_validation_present,
            "phase4i_validation_present",
        )
        _require_boolean(
            self.scoring_regression_present,
            "scoring_regression_present",
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
        _require_false(self.parser_update_applied, "parser_update_applied")
        _require_list_of_strings(self.denied_reasons, "denied_reasons")
        _require_list_of_strings(self.warnings, "warnings")
        _require_list_of_strings(self.required_next_steps, "required_next_steps")
        _require_optional_string(self.notes, "notes")
        if self.eligible:
            if self.eligibility_status != "eligible_metadata_only":
                raise ParserRuntimeUpdatePathError(
                    "eligible metadata must use eligible_metadata_only status."
                )
            missing = [
                not self.required_validation_present,
                not self.parser_tests_present,
                not self.awr_regression_present,
                not self.phase4i_validation_present,
                not self.scoring_regression_present,
                not self.rollback_reference_present,
                not self.runtime_gate_reference_present,
            ]
            if any(missing):
                raise ParserRuntimeUpdatePathError(
                    "eligible metadata requires all validation references."
                )


@dataclass(frozen=True)
class ParserRuntimeRollbackReference:
    """Local rollback metadata for a future parser runtime update."""

    rollback_id: str
    package_id: str
    rollback_strategy: str
    rollback_reference: str
    rollback_validated: bool = False
    rollback_executed: bool = False
    parser_update_reverted: bool = False
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.rollback_id, "rollback_id")
        _require_nonempty_string(self.package_id, "package_id")
        _require_nonempty_string(self.rollback_strategy, "rollback_strategy")
        _require_nonempty_string(self.rollback_reference, "rollback_reference")
        _require_boolean(self.rollback_validated, "rollback_validated")
        _require_false(self.rollback_executed, "rollback_executed")
        _require_false(self.parser_update_reverted, "parser_update_reverted")
        _require_optional_string(self.notes, "notes")


def create_parser_runtime_package_id(
    source_parser_evolution_id: str,
    parser_section: str,
    signal_name: str,
) -> str:
    """Create a deterministic parser runtime package id."""

    _require_nonempty_string(
        source_parser_evolution_id,
        "source_parser_evolution_id",
    )
    _require_nonempty_string(parser_section, "parser_section")
    _require_nonempty_string(signal_name, "signal_name")
    return (
        "PARSER-RUNTIME-PACKAGE-"
        f"{_normalize_token(source_parser_evolution_id)}-"
        f"{_normalize_token(parser_section)}-"
        f"{_normalize_token(signal_name)}"
    )


def create_parser_runtime_manifest_id(
    package_id: str,
    manifest_version: str,
) -> str:
    """Create a deterministic parser runtime manifest id."""

    _require_nonempty_string(package_id, "package_id")
    _require_nonempty_string(manifest_version, "manifest_version")
    return (
        "PARSER-RUNTIME-MANIFEST-"
        f"{_normalize_token(package_id)}-"
        f"{_normalize_token(manifest_version)}"
    )


def create_parser_runtime_eligibility_id(
    package_id: str,
    manifest_id: str,
) -> str:
    """Create a deterministic parser runtime eligibility id."""

    _require_nonempty_string(package_id, "package_id")
    _require_nonempty_string(manifest_id, "manifest_id")
    return (
        "PARSER-RUNTIME-ELIGIBILITY-"
        f"{_normalize_token(package_id)}-"
        f"{_normalize_token(manifest_id)}"
    )


def create_parser_runtime_rollback_id(
    package_id: str,
    rollback_strategy: str,
) -> str:
    """Create a deterministic parser runtime rollback id."""

    _require_nonempty_string(package_id, "package_id")
    _require_nonempty_string(rollback_strategy, "rollback_strategy")
    return (
        "PARSER-RUNTIME-ROLLBACK-"
        f"{_normalize_token(package_id)}-"
        f"{_normalize_token(rollback_strategy)}"
    )


def validate_parser_runtime_update_package(
    package: ParserRuntimeUpdatePackage,
) -> ParserRuntimeUpdatePackage:
    """Validate parser runtime update package metadata without applying it."""

    if not isinstance(package, ParserRuntimeUpdatePackage):
        raise ParserRuntimeUpdatePathError(
            "package must be a ParserRuntimeUpdatePackage instance."
        )
    package.__post_init__()
    return package


def validate_parser_runtime_update_manifest(
    manifest: ParserRuntimeUpdateManifest,
) -> ParserRuntimeUpdateManifest:
    """Validate parser runtime update manifest metadata without activation."""

    if not isinstance(manifest, ParserRuntimeUpdateManifest):
        raise ParserRuntimeUpdatePathError(
            "manifest must be a ParserRuntimeUpdateManifest instance."
        )
    manifest.__post_init__()
    return manifest


def validate_parser_runtime_eligibility_record(
    record: ParserRuntimeEligibilityRecord,
) -> ParserRuntimeEligibilityRecord:
    """Validate parser runtime eligibility metadata without activation."""

    if not isinstance(record, ParserRuntimeEligibilityRecord):
        raise ParserRuntimeUpdatePathError(
            "record must be a ParserRuntimeEligibilityRecord instance."
        )
    record.__post_init__()
    return record


def validate_parser_runtime_rollback_reference(
    rollback: ParserRuntimeRollbackReference,
) -> ParserRuntimeRollbackReference:
    """Validate parser runtime rollback metadata without executing rollback."""

    if not isinstance(rollback, ParserRuntimeRollbackReference):
        raise ParserRuntimeUpdatePathError(
            "rollback must be a ParserRuntimeRollbackReference instance."
        )
    rollback.__post_init__()
    return rollback


def evaluate_parser_runtime_eligibility(
    package: ParserRuntimeUpdatePackage,
    manifest: ParserRuntimeUpdateManifest,
) -> ParserRuntimeEligibilityRecord:
    """Evaluate parser package eligibility as metadata only."""

    package = validate_parser_runtime_update_package(package)
    manifest = validate_parser_runtime_update_manifest(manifest)

    denied_reasons: list[str] = []
    warnings = [
        "Phase 7BV eligibility is metadata only; parser_update_applied=false.",
        "Parser runtime remains inactive; runtime_active=false.",
        "Deterministic parser fallback remains required.",
    ]
    required_next_steps: list[str] = []

    parser_tests_present = bool(_optional_text(package.parser_tests_reference))
    awr_regression_present = bool(_optional_text(package.awr_regression_reference))
    phase4i_validation_present = bool(
        _optional_text(package.phase4i_validation_reference)
    )
    scoring_regression_present = bool(
        _optional_text(package.scoring_regression_reference)
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
    elif not parser_tests_present:
        eligibility_status = "needs_parser_tests"
        denied_reasons.append("parser_tests_reference is required")
        required_next_steps.append("attach parser test evidence reference")
    elif not awr_regression_present:
        eligibility_status = "needs_awr_regression"
        denied_reasons.append("awr_regression_reference is required")
        required_next_steps.append("attach AWR regression evidence reference")
    elif not phase4i_validation_present:
        eligibility_status = "needs_phase4i_validation"
        denied_reasons.append("phase4i_validation_reference is required")
        required_next_steps.append("attach Phase 4I validation evidence reference")
    elif not scoring_regression_present:
        eligibility_status = "needs_scoring_regression"
        denied_reasons.append("scoring_regression_reference is required")
        required_next_steps.append("attach scoring regression evidence reference")
    elif not rollback_reference_present:
        eligibility_status = "needs_rollback_reference"
        denied_reasons.append("rollback_reference is required on package and manifest")
        required_next_steps.append("attach rollback reference metadata")
    elif not runtime_gate_reference_present:
        eligibility_status = "needs_runtime_gate"
        denied_reasons.append("runtime_gate_reference is required")
        required_next_steps.append("attach runtime gate review reference")
    elif not required_validation_present:
        eligibility_status = "needs_phase4i_validation"
        denied_reasons.append("manifest validation_reference is required")
        required_next_steps.append("attach manifest validation reference")
    else:
        required_next_steps.append("future runtime review may consider this package")
        required_next_steps.append("explicit activation remains required in a future phase")

    eligible = eligibility_status == "eligible_metadata_only"
    return validate_parser_runtime_eligibility_record(
        ParserRuntimeEligibilityRecord(
            eligibility_id=create_parser_runtime_eligibility_id(
                package.package_id,
                manifest.manifest_id,
            ),
            package_id=package.package_id,
            manifest_id=manifest.manifest_id,
            eligible=eligible,
            eligibility_status=eligibility_status,
            required_validation_present=required_validation_present,
            parser_tests_present=parser_tests_present,
            awr_regression_present=awr_regression_present,
            phase4i_validation_present=phase4i_validation_present,
            scoring_regression_present=scoring_regression_present,
            rollback_reference_present=rollback_reference_present,
            runtime_gate_reference_present=runtime_gate_reference_present,
            deterministic_fallback_available=True,
            runtime_active=False,
            parser_update_applied=False,
            denied_reasons=denied_reasons,
            warnings=warnings,
            required_next_steps=required_next_steps,
            notes=package.notes,
        )
    )


def parser_runtime_update_package_to_dict(
    package: ParserRuntimeUpdatePackage,
) -> dict[str, Any]:
    """Serialize parser runtime update package metadata."""

    package.__post_init__()
    return {
        "package_id": package.package_id,
        "source_parser_evolution_id": package.source_parser_evolution_id,
        "source_materialization_id": package.source_materialization_id,
        "parser_section": package.parser_section,
        "signal_name": package.signal_name,
        "update_type": package.update_type,
        "proposed_change_summary": package.proposed_change_summary,
        "affected_files": list(package.affected_files),
        "affected_patterns": list(package.affected_patterns),
        "validation_requirements": list(package.validation_requirements),
        "parser_tests_reference": package.parser_tests_reference,
        "awr_regression_reference": package.awr_regression_reference,
        "phase4i_validation_reference": package.phase4i_validation_reference,
        "scoring_regression_reference": package.scoring_regression_reference,
        "rollback_reference": package.rollback_reference,
        "package_status": package.package_status,
        "runtime_eligible": package.runtime_eligible,
        "runtime_active": package.runtime_active,
        "parser_update_applied": package.parser_update_applied,
        "parser_output_mutation_performed": package.parser_output_mutation_performed,
        "phase4i_mutation_performed": package.phase4i_mutation_performed,
        "created_by": package.created_by,
        "created_at": package.created_at,
        "notes": package.notes,
    }


def parser_runtime_update_package_from_dict(
    data: dict[str, Any],
) -> ParserRuntimeUpdatePackage:
    """Deserialize parser runtime update package metadata."""

    _require_mapping(data, "data")
    return ParserRuntimeUpdatePackage(
        package_id=str(data["package_id"]),
        source_parser_evolution_id=str(data["source_parser_evolution_id"]),
        source_materialization_id=str(data["source_materialization_id"]),
        parser_section=str(data["parser_section"]),
        signal_name=str(data["signal_name"]),
        update_type=str(data["update_type"]),
        proposed_change_summary=str(data["proposed_change_summary"]),
        affected_files=list(data.get("affected_files") or []),
        affected_patterns=list(data.get("affected_patterns") or []),
        validation_requirements=list(data.get("validation_requirements") or []),
        parser_tests_reference=_optional_text(data.get("parser_tests_reference")),
        awr_regression_reference=_optional_text(data.get("awr_regression_reference")),
        phase4i_validation_reference=_optional_text(
            data.get("phase4i_validation_reference")
        ),
        scoring_regression_reference=_optional_text(
            data.get("scoring_regression_reference")
        ),
        rollback_reference=_optional_text(data.get("rollback_reference")),
        package_status=str(data.get("package_status", "proposed")),
        runtime_eligible=_bool_from_mapping(data, "runtime_eligible", False),
        runtime_active=_bool_from_mapping(data, "runtime_active", False),
        parser_update_applied=_bool_from_mapping(
            data,
            "parser_update_applied",
            False,
        ),
        parser_output_mutation_performed=_bool_from_mapping(
            data,
            "parser_output_mutation_performed",
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


def parser_runtime_update_manifest_to_dict(
    manifest: ParserRuntimeUpdateManifest,
) -> dict[str, Any]:
    """Serialize parser runtime update manifest metadata."""

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
        "phase4i_contract_preserved": manifest.phase4i_contract_preserved,
        "runtime_activation_requested": manifest.runtime_activation_requested,
        "runtime_activation_approved": manifest.runtime_activation_approved,
        "runtime_active": manifest.runtime_active,
        "parser_update_applied": manifest.parser_update_applied,
        "created_by": manifest.created_by,
        "created_at": manifest.created_at,
        "notes": manifest.notes,
    }


def parser_runtime_update_manifest_from_dict(
    data: dict[str, Any],
) -> ParserRuntimeUpdateManifest:
    """Deserialize parser runtime update manifest metadata."""

    _require_mapping(data, "data")
    return ParserRuntimeUpdateManifest(
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
        phase4i_contract_preserved=_bool_from_mapping(
            data,
            "phase4i_contract_preserved",
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
        parser_update_applied=_bool_from_mapping(
            data,
            "parser_update_applied",
            False,
        ),
        created_by=_optional_text(data.get("created_by")),
        created_at=_optional_text(data.get("created_at")),
        notes=_optional_text(data.get("notes")),
    )


def parser_runtime_eligibility_record_to_dict(
    record: ParserRuntimeEligibilityRecord,
) -> dict[str, Any]:
    """Serialize parser runtime eligibility metadata."""

    record.__post_init__()
    return {
        "eligibility_id": record.eligibility_id,
        "package_id": record.package_id,
        "manifest_id": record.manifest_id,
        "eligible": record.eligible,
        "eligibility_status": record.eligibility_status,
        "required_validation_present": record.required_validation_present,
        "parser_tests_present": record.parser_tests_present,
        "awr_regression_present": record.awr_regression_present,
        "phase4i_validation_present": record.phase4i_validation_present,
        "scoring_regression_present": record.scoring_regression_present,
        "rollback_reference_present": record.rollback_reference_present,
        "runtime_gate_reference_present": record.runtime_gate_reference_present,
        "deterministic_fallback_available": record.deterministic_fallback_available,
        "runtime_active": record.runtime_active,
        "parser_update_applied": record.parser_update_applied,
        "denied_reasons": list(record.denied_reasons),
        "warnings": list(record.warnings),
        "required_next_steps": list(record.required_next_steps),
        "notes": record.notes,
    }


def parser_runtime_eligibility_record_from_dict(
    data: dict[str, Any],
) -> ParserRuntimeEligibilityRecord:
    """Deserialize parser runtime eligibility metadata."""

    _require_mapping(data, "data")
    return ParserRuntimeEligibilityRecord(
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
        parser_tests_present=_bool_from_mapping(data, "parser_tests_present", False),
        awr_regression_present=_bool_from_mapping(
            data,
            "awr_regression_present",
            False,
        ),
        phase4i_validation_present=_bool_from_mapping(
            data,
            "phase4i_validation_present",
            False,
        ),
        scoring_regression_present=_bool_from_mapping(
            data,
            "scoring_regression_present",
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
        parser_update_applied=_bool_from_mapping(
            data,
            "parser_update_applied",
            False,
        ),
        denied_reasons=list(data.get("denied_reasons") or []),
        warnings=list(data.get("warnings") or []),
        required_next_steps=list(data.get("required_next_steps") or []),
        notes=_optional_text(data.get("notes")),
    )


def parser_runtime_rollback_reference_to_dict(
    rollback: ParserRuntimeRollbackReference,
) -> dict[str, Any]:
    """Serialize parser runtime rollback metadata."""

    rollback.__post_init__()
    return {
        "rollback_id": rollback.rollback_id,
        "package_id": rollback.package_id,
        "rollback_strategy": rollback.rollback_strategy,
        "rollback_reference": rollback.rollback_reference,
        "rollback_validated": rollback.rollback_validated,
        "rollback_executed": rollback.rollback_executed,
        "parser_update_reverted": rollback.parser_update_reverted,
        "notes": rollback.notes,
    }


def parser_runtime_rollback_reference_from_dict(
    data: dict[str, Any],
) -> ParserRuntimeRollbackReference:
    """Deserialize parser runtime rollback metadata."""

    _require_mapping(data, "data")
    return ParserRuntimeRollbackReference(
        rollback_id=str(data["rollback_id"]),
        package_id=str(data["package_id"]),
        rollback_strategy=str(data["rollback_strategy"]),
        rollback_reference=str(data["rollback_reference"]),
        rollback_validated=_bool_from_mapping(data, "rollback_validated", False),
        rollback_executed=_bool_from_mapping(data, "rollback_executed", False),
        parser_update_reverted=_bool_from_mapping(
            data,
            "parser_update_reverted",
            False,
        ),
        notes=_optional_text(data.get("notes")),
    )


def _package_has_all_eligibility_metadata(
    package: ParserRuntimeUpdatePackage,
) -> bool:
    return (
        package.package_status == ELIGIBILITY_PACKAGE_STATUS
        and bool(_optional_text(package.parser_tests_reference))
        and bool(_optional_text(package.awr_regression_reference))
        and bool(_optional_text(package.phase4i_validation_reference))
        and bool(_optional_text(package.scoring_regression_reference))
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
    raise ParserRuntimeUpdatePathError(f"{field_name} must be a boolean.")


def _require_mapping(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise ParserRuntimeUpdatePathError(f"{field_name} must be a mapping.")


def _require_nonempty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ParserRuntimeUpdatePathError(
            f"{field_name} must be a non-empty string."
        )


def _require_optional_string(value: Any, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise ParserRuntimeUpdatePathError(f"{field_name} must be a string or None.")


def _require_supported(value: Any, supported: tuple[str, ...], field_name: str) -> None:
    if value not in supported:
        raise ParserRuntimeUpdatePathError(
            f"{field_name} must be one of: {', '.join(supported)}."
        )


def _require_boolean(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise ParserRuntimeUpdatePathError(f"{field_name} must be a boolean.")


def _require_true(value: Any, field_name: str) -> None:
    _require_boolean(value, field_name)
    if not value:
        raise ParserRuntimeUpdatePathError(
            f"{field_name} must remain true in Phase 7BV."
        )


def _require_false(value: Any, field_name: str) -> None:
    _require_boolean(value, field_name)
    if value:
        raise ParserRuntimeUpdatePathError(
            f"{field_name} must remain false in Phase 7BV."
        )


def _require_list_of_strings(value: Any, field_name: str) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise ParserRuntimeUpdatePathError(
            f"{field_name} must be a list of strings."
        )


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text).strip("-")
    return text or "NONE"
