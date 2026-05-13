# Phase 7W ML Backtesting Model

## 1. Purpose

This document defines the serializable object model for Phase 7W ML training / backtesting harness records. The model exists for local evaluation, auditability, and future governance evidence only.

Training/backtesting artifacts are evaluation records only. They are not runtime model artifacts.

## 2. DatasetSplit Object Shape

`DatasetSplit` contains `split_id`, `dataset_id`, `split_strategy`, `train_record_ids`, `test_record_ids`, `validation_record_ids`, `split_seed`, and `notes`.

`dataset_id` and `split_strategy` are required. Train, test, and validation IDs must be lists of strings. Train and test IDs must not overlap. Dataset split objects do not contain runtime influence or runtime activation fields.

## 3. MLTrainingPlan Object Shape

`MLTrainingPlan` contains `training_plan_id`, `dataset_id`, `dataset_name`, `model_family`, `feature_schema_version`, `label_schema_version`, `target_label_name`, `split_strategy`, `required_metrics`, `created_by`, `notes`, `runtime_influence`, and `runtime_active`.

`runtime_influence=false` and `runtime_active=false` are required. A training plan describes evaluation intent only.

## 4. MLTrainingResult Object Shape

`MLTrainingResult` contains `training_id`, `training_plan_id`, `dataset_id`, `model_family`, `target_label_name`, `split_id`, `metrics`, `training_status`, `insufficient_label_count`, `excluded_label_count`, `validation_notes`, `runtime_active`, `runtime_influence_granted`, and `deterministic_runtime_remains_authoritative`.

`runtime_active=false`, `runtime_influence_granted=false`, and `deterministic_runtime_remains_authoritative=true` are required. A training result is not model approval.

## 5. MLBacktestResult Object Shape

`MLBacktestResult` contains `backtest_id`, `training_id`, `dataset_id`, `split_id`, `test_record_count`, `metrics`, `baseline_comparison`, `disagreement_count`, `backtest_status`, `validation_notes`, `runtime_active`, `runtime_influence_granted`, and `deterministic_runtime_remains_authoritative`.

`runtime_active=false`, `runtime_influence_granted=false`, and `deterministic_runtime_remains_authoritative=true` are required. A backtest result is not runtime activation.

## 6. Supported Model Families

Supported model families are `baseline_majority`, `baseline_numeric_mean`, `shadow_placeholder`, `tree`, `neural_net`, `hybrid_rule_ml`, and `linear`.

Only `baseline_majority`, `baseline_numeric_mean`, and `shadow_placeholder` are executable by the local deterministic helpers. Other families are planned metadata values only and do not trigger real ML training.

## 7. Split Strategies

Supported split strategies are `deterministic_holdout`, `chronological_holdout`, `full_backtest`, and `no_split`.

Split records are deterministic. No UUID, timestamp, database sequence, network service, or external scheduler is used to form split IDs or split membership.

## 8. Metric Rules

Supported metrics are `accuracy`, `precision`, `recall`, `mean_absolute_error`, `baseline_accuracy`, `disagreement_rate`, `insufficient_label_count`, and `excluded_label_count`.

Metric values must be numeric. Non-negative metrics are required. Rate metrics must be between 0.0 and 1.0. Classification baselines can compute majority-label accuracy. Binary labels can compute precision and recall. Numeric labels can compute mean absolute error.

## 9. Statuses

Training statuses are `PLANNED`, `TRAINED`, `VALIDATED`, `REJECTED`, and `INSUFFICIENT_DATA`.

Backtest statuses are `BACKTESTED`, `VALIDATED`, `REJECTED`, and `INSUFFICIENT_DATA`.

No status means runtime active. Status values are evidence workflow states only.

## 10. Serialization Rules

Every object has deterministic to-dictionary and from-dictionary helpers. Deserialization reruns validation and rejects records that attempt `runtime_influence=true`, `runtime_active=true`, or `runtime_influence_granted=true`.

Serialization does not write databases, model files, dashboard state, CLI state, registry state, or runtime configuration.

## 11. Deterministic ID Rules

IDs are derived from stable input fields:

```text
SPLIT-<DATASET_ID>-<STRATEGY>-<SEED>
TRAINING-PLAN-<DATASET_ID>-<MODEL_FAMILY>-<TARGET_LABEL>
TRAINING-RESULT-<PLAN_ID>-<SPLIT_ID>
BACKTEST-<TRAINING_ID>-<SPLIT_ID>
```

IDs do not use UUIDs, timestamps, database sequences, current time, network calls, or external services.

## 12. Runtime Boundary

No model is runtime active. `runtime_active=false` and `runtime_influence_granted=false` are required on training and backtesting results. Deterministic scoring remains authoritative.

Training result is not model approval. Backtest result is not runtime activation. No model registry is implemented. No runtime scoring is changed.

## 13. Non-Goals

Phase 7W does not implement real ML framework training, learned_model(x), runtime inference, model deployment, model activation, model registry approval, Phase 7X explainability, Phase 7Y model registry, Phase 7Z certification, or Phase 8 sizing/TCO.

Phase 7W does not change parser behavior, scoring behavior, decision behavior, recommendation behavior, dashboard behavior, CLI behavior, database schema, or generated dashboard HTML.

## 14. Acceptance Criteria

The model is accepted when dataset split, training plan, training result, and backtest result objects validate and serialize deterministically; supported model families, split strategies, statuses, metrics, and ID rules are enforced; baseline training and backtesting helpers remain local and deterministic; training/backtesting artifacts are evaluation records only; `runtime_active=false`; `runtime_influence_granted=false`; training result is not model approval; backtest result is not runtime activation; no model registry is implemented; no runtime scoring is changed; and deterministic runtime remains authoritative.
