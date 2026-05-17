# Phase 7BX Recommendation Runtime Rule Model

## Object Shapes

`RecommendationRuntimeRulePackage` includes `package_id`, `source_recommendation_evolution_id`, `source_materialization_id`, `recommendation_rule_version`, `affected_domains`, `affected_components`, `rule_type`, `proposed_rule_summary`, `wording_changes`, `priority_changes`, `evidence_mapping_changes`, `action_sequence_changes`, `risk_label_changes`, `suppression_rule_changes`, `escalation_rule_changes`, `before_after_reference`, `regression_reference`, `evidence_mapping_validation_reference`, `action_sequence_validation_reference`, `risk_label_validation_reference`, `phase4i_recommendation_contract_reference`, `rollback_reference`, `package_status`, `runtime_eligible`, `runtime_active`, `recommendation_rule_applied`, `recommendation_output_mutation_performed`, `phase4i_mutation_performed`, `created_by`, `created_at`, and `notes`.

`RecommendationActivationManifest` includes `manifest_id`, `package_id`, `manifest_version`, `activation_mode`, `explicit_activation_required`, `validation_reference`, `rollback_reference`, `runtime_gate_reference`, `deterministic_fallback_available`, `phase4i_recommendation_contract_preserved`, `runtime_activation_requested`, `runtime_activation_approved`, `runtime_active`, `recommendation_rule_applied`, `created_by`, `created_at`, and `notes`.

`RecommendationRuntimeEligibilityRecord` includes `eligibility_id`, `package_id`, `manifest_id`, `eligible`, `eligibility_status`, `required_validation_present`, `regression_reference_present`, `before_after_reference_present`, `evidence_mapping_validation_present`, `action_sequence_validation_present`, `risk_label_validation_present`, `phase4i_recommendation_contract_reference_present`, `rollback_reference_present`, `runtime_gate_reference_present`, `deterministic_fallback_available`, `runtime_active`, `recommendation_rule_applied`, `denied_reasons`, `warnings`, `required_next_steps`, and `notes`.

`RecommendationRollbackReference` includes `rollback_id`, `package_id`, `rollback_strategy`, `rollback_reference`, `rollback_validated`, `rollback_executed`, `recommendation_rule_reverted`, and `notes`.

`RecommendationRegressionEvidence` includes `regression_id`, `package_id`, `test_suite_reference`, `before_after_reference`, `evidence_mapping_validation_reference`, `action_sequence_validation_reference`, `risk_label_validation_reference`, `recommendation_contract_reference`, `regression_passed`, `evidence_mapping_valid`, `action_sequence_valid`, `risk_label_valid`, `phase4i_contract_preserved`, and `notes`.

## Package Statuses

The supported package statuses are `proposed`, `under_review`, `validation_required`, `regression_ready`, `eligible_for_runtime_review`, `rejected`, `superseded`, and `closed`. No status means active. Package status is governance metadata only.

## Eligibility Statuses

The supported eligibility statuses are `not_eligible`, `eligible_metadata_only`, `needs_regression_reference`, `needs_before_after_reference`, `needs_evidence_mapping_validation`, `needs_action_sequence_validation`, `needs_risk_label_validation`, `needs_phase4i_recommendation_contract`, `needs_rollback_reference`, `needs_runtime_gate`, and `blocked_by_safety`.

## Activation Modes

The supported activation modes are `disabled`, `manual_review_required`, `future_runtime_manifest`, and `emergency_disabled`. No activation mode activates recommendation rule in 7BX.

## Rule Types

The supported rule types are `wording`, `priority`, `domain_mapping`, `suppression`, `action_sequence`, `risk_label`, `evidence_mapping`, `category`, `confidence_wording`, `escalation`, and `unknown`.

## Validation Rules

Packages require a package id, source recommendation evolution id, source materialization id, recommendation rule version, list-shaped affected domains, list-shaped affected components, supported rule type, and proposed rule summary. `regression_ready` and `eligible_for_runtime_review` packages require a rollback reference. `runtime_eligible=true` can only be metadata eligibility and requires all validation references plus eligible status. `runtime_active=false`, `recommendation_rule_applied=false`, `recommendation_output_mutation_performed=false`, and `phase4i_mutation_performed=false` are mandatory.

Manifests require a manifest id, package id, manifest version, supported activation mode, `explicit_activation_required=true`, `deterministic_fallback_available=true`, and `phase4i_recommendation_contract_preserved=true`. `runtime_activation_requested=false`, `runtime_activation_approved=false`, `runtime_active=false`, and `recommendation_rule_applied=false` are mandatory.

Eligibility records require an eligibility id, package id, manifest id, supported eligibility status, and deterministic fallback. If `eligible=true`, then regression reference, before/after reference, evidence mapping validation reference, action sequence validation reference, risk label validation reference, Phase 4I recommendation contract reference, rollback reference, runtime gate reference, and manifest validation reference must all be present. eligible means metadata eligible, not active. `runtime_active=false` and `recommendation_rule_applied=false` are mandatory.

Rollback references require rollback id, package id, rollback strategy, and rollback reference. `rollback_executed=false` and `recommendation_rule_reverted=false` are mandatory.

Regression evidence requires regression id, package id, test suite reference, before/after reference, evidence mapping validation reference, action sequence validation reference, risk label validation reference, recommendation contract reference, `evidence_mapping_valid=true`, `action_sequence_valid=true`, `risk_label_valid=true`, and `phase4i_contract_preserved=true`. It records evidence metadata and does not run tests.

## Serialization Rules

Each object has explicit to/from dictionary helpers. Serialization preserves all safety flags and references. Deserialization re-runs dataclass validation, so serialized data cannot bypass `runtime_active=false`, `recommendation_rule_applied=false`, deterministic fallback, Phase 4I recommendation contract preservation, rollback execution, evidence mapping validation, action sequence validation, or risk label validation guards.

## Deterministic IDs

Recommendation package IDs follow `RECOMMENDATION-RUNTIME-PACKAGE-<EVOLUTION_ID>-<VERSION>`. Recommendation manifest IDs follow `RECOMMENDATION-RUNTIME-MANIFEST-<PACKAGE_ID>-<VERSION>`. Recommendation eligibility IDs follow `RECOMMENDATION-RUNTIME-ELIGIBILITY-<PACKAGE_ID>-<MANIFEST_ID>`. Recommendation rollback IDs follow `RECOMMENDATION-RUNTIME-ROLLBACK-<PACKAGE_ID>-<STRATEGY>`. Recommendation regression IDs follow `RECOMMENDATION-REGRESSION-<PACKAGE_ID>-<REFERENCE>`. IDs use no random UUID, timestamp, DB sequence, or external service.

## Runtime Safety

no recommendation modules are modified, no recommendation rule is applied, no recommendation output is changed, `runtime_active=false`, `recommendation_rule_applied=false`, deterministic fallback required, and phase 4i recommendation contract preserved. The model does not import recommendation, scoring, parser, decision, dashboard, CLI, database, network, or OCI runtime modules.

## Non-Goals

7BX does not edit recommendation modules, recommendation catalog, recommendation ranking, priority, wording, evidence mapping, action sequencing, risk labeling, scoring modules, parser modules, decision modules, dashboard modules, CLI modules, database schema, generated dashboard HTML, or Phase 4I. It does not call `run_analysis.py`, invoke recommendation runtime, persist recommendation rules, activate recommendation rules, implement 7BY, implement 7BZ, or implement Phase 8.
