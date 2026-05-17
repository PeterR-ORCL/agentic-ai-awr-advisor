# Phase 7BV Parser Runtime Update Model

## Object Shapes

`ParserRuntimeUpdatePackage` includes `package_id`, `source_parser_evolution_id`, `source_materialization_id`, `parser_section`, `signal_name`, `update_type`, `proposed_change_summary`, `affected_files`, `affected_patterns`, `validation_requirements`, `parser_tests_reference`, `awr_regression_reference`, `phase4i_validation_reference`, `scoring_regression_reference`, `rollback_reference`, `package_status`, `runtime_eligible`, `runtime_active`, `parser_update_applied`, `parser_output_mutation_performed`, `phase4i_mutation_performed`, `created_by`, `created_at`, and `notes`.

`ParserRuntimeUpdateManifest` includes `manifest_id`, `package_id`, `manifest_version`, `activation_mode`, `explicit_activation_required`, `validation_reference`, `rollback_reference`, `runtime_gate_reference`, `deterministic_fallback_available`, `phase4i_contract_preserved`, `runtime_activation_requested`, `runtime_activation_approved`, `runtime_active`, `parser_update_applied`, `created_by`, `created_at`, and `notes`.

`ParserRuntimeEligibilityRecord` includes `eligibility_id`, `package_id`, `manifest_id`, `eligible`, `eligibility_status`, `required_validation_present`, `parser_tests_present`, `awr_regression_present`, `phase4i_validation_present`, `scoring_regression_present`, `rollback_reference_present`, `runtime_gate_reference_present`, `deterministic_fallback_available`, `runtime_active`, `parser_update_applied`, `denied_reasons`, `warnings`, `required_next_steps`, and `notes`.

`ParserRuntimeRollbackReference` includes `rollback_id`, `package_id`, `rollback_strategy`, `rollback_reference`, `rollback_validated`, `rollback_executed`, `parser_update_reverted`, and `notes`.

## Update Types

The supported update types are `new_section_mapping`, `section_mapping_refinement`, `unknown_signal_mapping`, `regex_pattern_review`, `normalization_rule_review`, `field_extraction_review`, `unit_conversion_review`, `parser_confidence_metadata_review`, `section_registry_review`, and `parser_regression_test_addition`.

## Package Statuses

The supported package statuses are `proposed`, `under_review`, `validation_required`, `validation_ready`, `eligible_for_runtime_review`, `rejected`, `superseded`, and `closed`. No status means active. Package status is governance metadata only.

## Eligibility Statuses

The supported eligibility statuses are `not_eligible`, `eligible_metadata_only`, `needs_parser_tests`, `needs_awr_regression`, `needs_phase4i_validation`, `needs_scoring_regression`, `needs_rollback_reference`, `needs_runtime_gate`, and `blocked_by_safety`.

## Activation Modes

The supported activation modes are `disabled`, `manual_review_required`, `future_runtime_manifest`, and `emergency_disabled`. No activation mode activates a parser update in 7BV.

## Validation Rules

Packages require a package id, source parser evolution id, source materialization id, parser section, signal name, supported update type, proposed change summary, list-shaped affected files, list-shaped affected patterns, and list-shaped validation requirements. `validation_ready` and `eligible_for_runtime_review` packages require a rollback reference. `runtime_eligible=true` can only be metadata eligibility and requires all validation references plus `eligible_for_runtime_review`. `runtime_active=false`, `parser_update_applied=false`, `parser_output_mutation_performed=false`, and `phase4i_mutation_performed=false` are mandatory.

Manifests require a manifest id, package id, manifest version, supported activation mode, `explicit_activation_required=true`, `deterministic_fallback_available=true`, and `phase4i_contract_preserved=true`. `runtime_activation_requested=false`, `runtime_activation_approved=false`, `runtime_active=false`, and `parser_update_applied=false` are mandatory.

Eligibility records require an eligibility id, package id, manifest id, supported eligibility status, and deterministic fallback. If `eligible=true`, then parser test, AWR regression, Phase 4I validation, scoring regression, rollback reference, runtime gate reference, and manifest validation reference must all be present. eligible means metadata eligible, not active. `runtime_active=false` and `parser_update_applied=false` are mandatory.

Rollback references require rollback id, package id, rollback strategy, and rollback reference. `rollback_executed=false` and `parser_update_reverted=false` are mandatory.

## Serialization Rules

Each object has explicit to/from dictionary helpers. Serialization preserves all safety flags and references. Deserialization re-runs dataclass validation, so serialized data cannot bypass `runtime_active=false`, `parser_update_applied=false`, deterministic fallback, Phase 4I preservation, or rollback execution guards.

## Deterministic IDs

Parser package IDs follow `PARSER-RUNTIME-PACKAGE-<EVOLUTION_ID>-<SECTION>-<SIGNAL>`. Parser manifest IDs follow `PARSER-RUNTIME-MANIFEST-<PACKAGE_ID>-<VERSION>`. Parser eligibility IDs follow `PARSER-RUNTIME-ELIGIBILITY-<PACKAGE_ID>-<MANIFEST_ID>`. Parser rollback IDs follow `PARSER-RUNTIME-ROLLBACK-<PACKAGE_ID>-<STRATEGY>`. IDs use no random UUID, timestamp, DB sequence, or external service.

## Runtime Safety

no parser files are modified, no parser update is applied, no parser output is changed, `runtime_active=false`, `parser_update_applied=false`, deterministic fallback required, and phase 4i preserved. The model does not import parser, scoring, decision, recommendation, dashboard, CLI, database, network, or OCI runtime modules.

## Non-Goals

7BV does not edit parser modules, parser regexes, parser section registry, parser config, parser output, parser mapping records, parser candidates, parser backlog items, scoring modules, recommendation modules, decision modules, dashboard modules, CLI modules, database schema, generated dashboard HTML, or Phase 4I. It does not call `run_analysis.py`, invoke parser runtime, persist parser updates, activate parser updates, implement 7BW, implement 7BX, implement 7BY, implement 7BZ, or implement Phase 8.
