# Phase 7BY ML Runtime Manifest Model

## Object Shapes

`MLRuntimeEligibilityPackage` includes `package_id`, `model_id`, `model_family`, `model_version`, `registry_entry_id`, `training_reference`, `backtest_reference`, `explainability_reference`, `validation_reference`, `dataset_reference`, `feature_schema_version`, `label_schema_version`, `deterministic_comparison_reference`, `drift_review_reference`, `rollback_reference`, `monitoring_reference`, `eligibility_status`, `runtime_eligible`, `runtime_active`, `runtime_influence_granted`, `runtime_eligibility_granted`, `model_deployed`, `model_loaded`, `model_saved`, `runtime_scoring_replaced`, `phase4i_mutation_performed`, `created_by`, `created_at`, and `notes`.

`MLRuntimeActivationManifest` includes `manifest_id`, `package_id`, `manifest_version`, `activation_mode`, `explicit_activation_required`, `validation_reference`, `rollback_reference`, `runtime_gate_reference`, `monitoring_reference`, `deterministic_fallback_available`, `phase4i_contract_preserved`, `runtime_activation_requested`, `runtime_activation_approved`, `runtime_active`, `model_deployed`, `runtime_scoring_replaced`, `created_by`, `created_at`, and `notes`.

`MLRuntimeEligibilityRecord` includes `eligibility_id`, `package_id`, `manifest_id`, `eligible`, `eligibility_status`, registry/training/backtest/explainability/validation/deterministic-comparison/drift/rollback/monitoring/runtime-gate presence flags, deterministic fallback and Phase 4I flags, runtime safety flags, denied reasons, warnings, required next steps, and notes.

`MLRuntimeFallbackPlan` includes `fallback_id`, `package_id`, `fallback_strategy`, `deterministic_scoring_fallback`, `disable_model_fallback`, `rollback_reference`, `fallback_validated`, `fallback_executed`, `model_disabled`, `runtime_scoring_reverted`, and `notes`.

`MLRuntimeMonitoringPlan` includes `monitoring_id`, `package_id`, `monitoring_strategy`, `drift_monitoring_required`, `performance_monitoring_required`, `confidence_monitoring_required`, `fallback_trigger_defined`, `monitoring_active`, `runtime_active`, and `notes`.

`MLRuntimeRegressionEvidence` includes `regression_id`, `package_id`, `backtest_reference`, `explainability_reference`, `deterministic_comparison_reference`, `validation_reference`, `regression_passed`, `backtesting_passed`, `explainability_present`, `deterministic_comparison_acceptable`, `phase4i_contract_preserved`, and `notes`.

## Statuses

Supported eligibility statuses are `not_eligible`, `eligible_metadata_only`, `needs_registry_reference`, `needs_training_reference`, `needs_backtest_reference`, `needs_explainability_reference`, `needs_validation_reference`, `needs_deterministic_comparison`, `needs_drift_review`, `needs_rollback_reference`, `needs_monitoring_reference`, `needs_runtime_gate`, and `blocked_by_safety`.

## Activation Modes

Supported activation modes are `disabled`, `shadow_only`, `manual_review_required`, `future_runtime_manifest`, and `emergency_disabled`. No activation mode activates ML runtime in 7BY.

## Model Families

Supported model families are `tree`, `neural_net`, `hybrid_rule_ml`, `linear`, `baseline_mock`, `baseline_majority`, `baseline_numeric_mean`, `shadow_placeholder`, `external_placeholder`, and `unknown`.

## Validation Rules

Package validation requires a package ID, model ID, supported model family, model version, supported eligibility status, and safety flags that keep `runtime_active=false`, `runtime_eligibility_granted=false`, `runtime_influence_granted=false`, `model_deployed=false`, `model_loaded=false`, `model_saved=false`, `runtime_scoring_replaced=false`, and `phase4i_mutation_performed=false`. If `runtime_eligible=true`, all package references must be present and status must be `eligible_metadata_only`.

Manifest validation requires a manifest ID, package ID, manifest version, supported activation mode, `explicit_activation_required=true`, `deterministic_fallback_available=true`, `phase4i_contract_preserved=true`, `runtime_activation_requested=false`, `runtime_activation_approved=false`, `runtime_active=false`, `model_deployed=false`, and `runtime_scoring_replaced=false`.

Eligibility validation requires supported eligibility status, deterministic fallback, Phase 4I contract preservation, and all runtime flags false. If `eligible=true`, every required reference presence flag must be true. eligible means metadata eligible, not active.

Fallback validation requires deterministic scoring fallback and disable-model fallback. It rejects fallback execution, model disablement, and runtime scoring reversion in 7BY.

Monitoring validation requires boolean monitoring requirement flags and rejects active monitoring or runtime activation in 7BY.

Regression evidence validation requires Phase 4I contract preservation. If regression metadata is marked passed, backtesting, explainability, and deterministic comparison evidence must be present.

## Serialization Rules

Each object has a deterministic dictionary serializer and deserializer. Serialization records metadata only; it does not persist files, write DB rows, deploy models, load models, save models, or run inference.

## Deterministic IDs

IDs are stable for the same inputs:

- `ML-RUNTIME-PACKAGE-<MODEL_ID>-<VERSION>`
- `ML-RUNTIME-MANIFEST-<PACKAGE_ID>-<VERSION>`
- `ML-RUNTIME-ELIGIBILITY-<PACKAGE_ID>-<MANIFEST_ID>`
- `ML-RUNTIME-FALLBACK-<PACKAGE_ID>-<STRATEGY>`
- `ML-RUNTIME-MONITORING-<PACKAGE_ID>-<STRATEGY>`
- `ML-RUNTIME-REGRESSION-<PACKAGE_ID>-<REFERENCE>`

The ID helpers use no random UUID, no timestamp, no DB sequence, and no external service.

## Runtime Safety

no model is deployed. no model is loaded/saved. no runtime scoring is replaced. `runtime_active=false`, `runtime_eligibility_granted=false`, `runtime_influence_granted=false`, and `runtime_scoring_replaced=false` are required. deterministic fallback required and Phase 4I preserved are mandatory.

## Non-Goals

7BY does not train, deploy, load, save, or run ML models. It does not replace scoring, change decisions, change recommendations, change parser behavior, mutate Phase 4I, call `run_analysis.py`, write DB records, create migrations, grant runtime eligibility, grant runtime influence, activate monitoring, execute fallback, or implement Phase 8.
