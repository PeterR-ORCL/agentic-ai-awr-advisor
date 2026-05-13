# Phase 7W ML Training / Backtesting Harness

## 1. Purpose

Phase 7W defines a local, deterministic ML training / backtesting harness for governed Phase 7T feature / label datasets. The harness creates auditable evaluation records: dataset splits, training plans, deterministic baseline/mock training results, and backtest results.

Training/backtesting artifacts are evaluation records only. They are not runtime models, registry entries, approval records, or activation records.

## 2. Scope

Phase 7W adds local object models, validation helpers, deterministic ID helpers, serialization helpers, baseline/mock training helpers, and backtesting helpers. The implementation uses Python standard library behavior and governed local dataset records.

No real ML framework is required. The local helpers may evaluate `baseline_majority`, `baseline_numeric_mean`, and `shadow_placeholder` behavior, but they do not train a learned model.

## 3. Non-Goals

Phase 7W does not activate any model, implement model runtime approval, implement a model registry, persist runtime model assets, perform runtime inference, add dashboard controls, add CLI controls, write databases, call OCI, call Oracle Agent Memory, call LLMs, or call network services.

Phase 7W does not modify parser behavior, parser output, runtime scoring weights, runtime scoring thresholds, severity cutoffs, confidence logic, trend/anomaly runtime behavior, decision logic, recommendation logic, recommendation ranking, Phase 4I output, dashboard behavior, CLI behavior, database schema, or generated dashboard HTML.

Phase 7X explainability, Phase 7Y model registry, Phase 7Z certification, and Phase 8 sizing/TCO are not implemented. Phase 8 sizing/TCO is not implemented.

## 4. Training / Backtesting Is Not Runtime Activation

Training/backtesting artifacts are evaluation records only. Training/backtesting does not equal model approval. Backtesting success is not runtime activation.

No model is runtime active. No learned_model(x) runtime implementation is activated. No model registry is implemented. No runtime scoring changes are applied.

## 5. Dataset Inputs

The input foundation is the Phase 7T `FeatureLabelDataset`. Datasets are governed inputs, not models. Labels are observed outcomes, not runtime truth. Dataset validation is not training.

Training and backtesting helpers reference dataset IDs, feature schema versions, label schema versions, label names, and record IDs for auditability.

## 6. Dataset Split Model

`DatasetSplit` records define `split_id`, `dataset_id`, `split_strategy`, `train_record_ids`, `test_record_ids`, optional `validation_record_ids`, optional `split_seed`, and notes.

Split IDs are deterministic. Train, test, and validation record IDs are local lists. Train and test IDs must not overlap. Dataset split records have no runtime influence fields.

## 7. Training Plan Model

`MLTrainingPlan` records define the dataset, dataset name, model family, feature schema version, label schema version, target label name, split strategy, required metrics, creator metadata, notes, and runtime boundary flags.

Every plan requires `runtime_influence=false` and `runtime_active=false`. A training plan is planning metadata only and does not approve, train, save, or activate a model.

## 8. Training Result Model

`MLTrainingResult` records define `training_id`, `training_plan_id`, `dataset_id`, model family, target label name, split ID, metric values, training status, label counts, validation notes, and runtime boundary flags.

Every result requires `runtime_active=false`, `runtime_influence_granted=false`, and `deterministic_runtime_remains_authoritative=true`. A training result is not a model registry entry and is not runtime eligible.

## 9. Backtest Result Model

`MLBacktestResult` records define `backtest_id`, `training_id`, `dataset_id`, split ID, test record count, metric values, baseline comparison summary, disagreement count, backtest status, validation notes, and runtime boundary flags.

Every result requires `runtime_active=false`, `runtime_influence_granted=false`, and `deterministic_runtime_remains_authoritative=true`. A backtest result is evidence only. Backtesting success is not runtime activation.

## 10. Supported Model Families

Supported model families are `baseline_majority`, `baseline_numeric_mean`, `shadow_placeholder`, `tree`, `neural_net`, `hybrid_rule_ml`, and `linear`.

Only `baseline_majority`, `baseline_numeric_mean`, and `shadow_placeholder` are executable by the deterministic local helpers. `tree`, `neural_net`, `hybrid_rule_ml`, and `linear` are metadata-only planned families in Phase 7W and do not trigger real training.

## 11. Supported Split Strategies

Supported split strategies are `deterministic_holdout`, `chronological_holdout`, `full_backtest`, and `no_split`.

All split behavior is deterministic. No random split is used unless an explicit seed is provided and recorded. Even seeded behavior is local and deterministic.

## 12. Metrics

Supported metrics are `accuracy`, `precision`, `recall`, `mean_absolute_error`, `baseline_accuracy`, `disagreement_rate`, `insufficient_label_count`, and `excluded_label_count`.

Classification baselines can compute majority-label accuracy. Binary labels can also compute precision and recall. Numeric baselines can compute mean absolute error. Backtesting records can include baseline comparison summaries and disagreement counts.

## 13. Runtime Influence Boundary

Phase 7W validation rejects `runtime_influence=true`, `runtime_active=true`, and `runtime_influence_granted=true`. No record may be marked runtime active in Phase 7W.

Training and backtesting artifacts do not change runtime scoring, severity, confidence, decisions, recommendations, parser output, Phase 4I output, dashboard behavior, or CLI behavior.

## 14. Deterministic Runtime Boundary

Deterministic scoring remains authoritative. Phase 7W may compare baseline/mock training or backtesting evidence against available deterministic score, trend-aware score, or shadow ML score references, but those comparisons are advisory evidence only.

No runtime scoring changes are applied. No parser/scoring/decision/recommendation behavior changes are applied.

## 15. Relationship to Phase 7S

Phase 7S established the ML / adaptive scoring boundary, including shadow mode, non-authoritative ML behavior, no training, no learned_model(x), and no runtime activation. Phase 7W adds local training/backtesting evaluation records while preserving that boundary.

## 16. Relationship to Phase 7T

Phase 7T defines governed feature / label datasets. Phase 7W consumes those datasets as local governed inputs and records dataset references, schema versions, split references, and label counts.

Datasets remain inputs. A dataset is not a model, and dataset validation is not training.

## 17. Relationship to Phase 7U

Phase 7U trend-aware scoring remains advisory. Phase 7W may compare against available trend-aware score references where present, but trend-aware score remains non-authoritative and does not become runtime truth.

## 18. Relationship to Phase 7V

Phase 7V shadow ML output remains non-authoritative. Phase 7W may compare against available shadow ML score references where present, but shadow ML output does not change runtime scoring and does not become runtime truth.

## 19. Relationship to Future Phase 7X

Future Phase 7X may add explainability. Phase 7W includes only basic metric summaries, validation notes, baseline comparison summaries, and runtime boundary statements. It does not implement a full explainability layer.

## 20. Relationship to Future Phase 7Y

Future Phase 7Y may define a governed model registry. Phase 7W does not implement model registry behavior. A training result is not model approval, and a backtest result is not runtime activation.

## 21. Relationship to Future Phase 7Z

Future Phase 7Z may define certification. Phase 7W does not certify runtime eligibility. Backtesting evidence can support later governance, but it cannot activate a model.

## 22. Relationship to Phase 8

Phase 8 sizing/TCO is not implemented. Phase 7W does not implement sizing, capacity planning, cost modeling, TCO, or what-if advisory behavior.

## 23. Acceptance Criteria

Phase 7W is accepted when the local training/backtesting harness exists; dataset split, training plan, training result, and backtest result models exist; deterministic ID, validation, serialization, baseline/mock training, and backtesting helpers exist; no real ML framework is required; no model is runtime active; no learned_model(x) runtime implementation is activated; no model registry is implemented; backtesting success is not runtime activation; deterministic scoring remains authoritative; no runtime scoring changes are applied; no parser/scoring/decision/recommendation behavior changes are applied; no dashboard behavior is changed; no CLI behavior is changed; and Phase 8 sizing/TCO is not implemented.
