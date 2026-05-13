# Phase 7V Shadow ML Output Model

## 1. Purpose

This document defines the serializable output model for the Phase 7V shadow ML interface. Score_ml(x) exists only as a shadow interface/result contract. No output replaces deterministic score.

## 2. ShadowModelMetadata Object Shape

`ShadowModelMetadata` contains `model_id`, `model_family`, `model_version`, `feature_schema_version`, `label_schema_version`, `training_reference`, `validation_reference`, `runtime_active`, `runtime_influence_granted`, and `notes`.

`runtime_active=false` and `runtime_influence_granted=false` are required. No real ML model is implemented by this metadata.

## 3. ShadowMLInput Object Shape

`ShadowMLInput` contains `input_id`, `run_id`, `awr_id`, `feature_reference`, `dataset_reference`, `deterministic_score`, `trend_aware_score`, `feature_values`, `model_id`, `score_version`, `runtime_influence`, and `runtime_active`.

At least one of `run_id` or `awr_id` is required. `feature_values` must be a dictionary. `runtime_influence=false` and `runtime_active=false` are required.

## 4. ShadowMLOutput Object Shape

`ShadowMLOutput` contains `output_id`, `input_id`, `model_id`, `model_family`, `deterministic_score`, `trend_aware_score`, `shadow_ml_score`, `ml_delta_from_deterministic`, `ml_delta_from_trend_aware`, `confidence`, `advisory_status`, `disagreement_summary`, `boundary_summary`, `runtime_influence`, `runtime_active`, `runtime_influence_granted`, and `deterministic_runtime_remains_authoritative`.

Every output requires `runtime_influence=false`, `runtime_active=false`, `runtime_influence_granted=false`, and `deterministic_runtime_remains_authoritative=true`. No output changes Phase 4I. No output changes decisions or recommendations.

## 5. Supported Model Families

Supported model families are `tree`, `neural_net`, `hybrid_rule_ml`, `linear`, `baseline_mock`, and `external_placeholder`.

These values are metadata only. They do not activate tree models, neural networks, hybrid models, linear models, external inference, training, backtesting, or runtime model loading.

## 6. Advisory Statuses

Supported advisory statuses are `SHADOW_ONLY`, `ADVISORY_ONLY`, `INSUFFICIENT_MODEL_CONTEXT`, and `INVALID_INPUT`.

`SHADOW_ONLY` is not runtime active. `ADVISORY_ONLY` is not runtime active. `INSUFFICIENT_MODEL_CONTEXT` is not runtime active. `INVALID_INPUT` is not runtime active. There is no runtime-active status.

## 7. Placeholder Scoring Rules

The placeholder helper starts from the deterministic score, optionally applies a bounded blend toward a supplied trend-aware score, optionally applies a bounded adjustment from numeric risk-style feature values, and clamps the result to 0.0 through 100.0.

This helper is deterministic. It does not train, fit, backtest, call external services, load persisted models, save model artifacts, or update runtime scoring.

## 8. Validation Rules

Metadata validation requires `model_id`, supported model family, `model_version`, `runtime_active=false`, and `runtime_influence_granted=false`.

Input validation requires `input_id`, at least one of `run_id` or `awr_id`, deterministic score between 0.0 and 100.0, optional trend-aware score between 0.0 and 100.0, dictionary feature values, `model_id`, `score_version`, `runtime_influence=false`, and `runtime_active=false`.

Output validation requires scores between 0.0 and 100.0, confidence between 0.0 and 0.95, supported advisory status, correct deltas, `runtime_influence=false`, `runtime_active=false`, `runtime_influence_granted=false`, and `deterministic_runtime_remains_authoritative=true`.

## 9. Serialization Rules

Each object has deterministic dictionary serialization and deserialization helpers. Deserialization re-runs validation and rejects records that attempt to set runtime influence, runtime activation, or runtime influence grant flags to true.

Serialization does not write databases, files, model artifacts, registries, dashboards, or CLI state.

## 10. Deterministic ID Rules

IDs are derived from stable input fields:

```text
SHADOW-MODEL-<FAMILY>-<VERSION>-<FEATURE_SCHEMA>-<LABEL_SCHEMA>
SHADOW-INPUT-<RUN_OR_AWR>-<MODEL_ID>-<SCORE_VERSION>
SHADOW-OUTPUT-<INPUT_ID>-<MODEL_ID>
```

IDs do not use UUIDs, timestamps, database sequences, current time, network calls, or external services.

## 11. Runtime Boundary

Shadow ML is non-authoritative. Deterministic scoring remains authoritative. Shadow output does not change runtime scoring.

No output replaces deterministic score. No output changes Phase 4I. No output changes decisions or recommendations. No output changes parser behavior, scoring behavior, decision behavior, recommendation behavior, dashboard behavior, or CLI behavior.

## 12. Non-Goals

No real ML model is implemented. No training is implemented. No learned_model(x) is implemented. No model registry is implemented. No Phase 7W training/backtesting, Phase 7X full explainability, Phase 7Y model registry, Phase 7Z certification, or Phase 8 sizing/TCO is implemented.

## 13. Acceptance Criteria

The model is accepted when shadow metadata, input, and output records validate and serialize deterministically; supported model families and advisory statuses are enforced; placeholder scoring is bounded and deterministic; `runtime_influence=false`; `runtime_active=false`; `runtime_influence_granted=false`; deterministic runtime remains authoritative; no output replaces deterministic score; no output changes Phase 4I; no output changes decisions or recommendations; and shadow ML remains a non-authoritative interface only.
