# Phase 7T Feature / Label Dataset Model

## 1. Purpose

Phase 7T defines the governed local dataset foundation for future ML and adaptive scoring work in the Agentic AI AWR Advisor project.

The dataset model represents `(X, y)`: X = feature vectors and y = observed outcomes. A Phase 7T dataset is not a model. Dataset validation is not training. Deterministic runtime remains authoritative.

## 2. Scope

Phase 7T covers local deterministic feature records, label records, feature schema metadata, label schema metadata, dataset records, validation helpers, join helpers, summary helpers, and serialization/deserialization helpers.

The dataset is governed input for future phases. It may collect deterministic AWR-derived feature values and audited observed outcomes, but it does not train, score, infer, activate, or modify any runtime behavior.

## 3. Non-Goals

Phase 7T does not implement model training, learned_model(x), Score_ml(x), Score(x, t), model inference, trend-aware scoring, shadow ML scoring, backtesting, explainability, model registry behavior, model certification, dashboard ML controls, CLI ML commands, or Phase 8 sizing/TCO.

Phase 7T does not modify parser behavior, parser output, scoring logic, scoring weights, scoring thresholds, decision logic, recommendation logic, recommendation ranking, trend/anomaly runtime behavior, the Phase 4I output contract, `run_analysis.py`, dashboard behavior, CLI behavior, database schema, generated dashboard HTML, or runtime paths.

## 4. X = Feature Vectors

X = feature vectors. Feature records represent deterministic local values that may originate from AWR-derived domains such as domain scores, wait class metrics, SQL signal metrics, trend features, anomaly features, workload shape, memory pressure, IO pressure, commit behavior, RAC indicators, ADG indicators, topology, platform indicators, AWR metadata, and derived feature values.

No live AWR parsing is performed by Phase 7T. No runtime feature extraction changes are introduced. Feature values are accepted only when their declared feature type is supported and locally valid.

## 5. y = Observed Outcomes

y = observed outcomes. Label records represent governed outcomes such as tuning success, performance improvement, performance worsening, accepted recommendations, rejected recommendations, recurrence, risk confirmation, false positives, false negatives, effective actions, ineffective actions, no change, and unknown outcomes.

Labels must be auditable. Supervised labels require a source outcome, source record, or evidence reference where available. unknown_outcome is allowed, but it is excluded from supervised labels by default and must not be treated as supervised truth.

## 6. Feature Record Model

A feature record includes `feature_id`, `run_id`, `awr_id`, `feature_name`, `feature_domain`, `feature_value`, `feature_type`, `source_component`, `source_metric`, `feature_schema_version`, `evidence_reference`, `created_at`, and `notes`.

Feature records require a stable identifier, at least one of `run_id` or `awr_id`, a feature name, an explicit schema version, and a supported feature type. Supported values are constrained to numeric, categorical, boolean, text, derived numeric, derived categorical, or missing feature types.

## 7. Label Record Model

A label record includes `label_id`, `run_id`, `awr_id`, `label_name`, `label_value`, `label_type`, `outcome_source`, `source_record_id`, `label_schema_version`, `confidence`, `evidence_reference`, `reviewed_by`, `created_at`, and `notes`.

Label records require a stable identifier, at least one of `run_id` or `awr_id`, a supported label name, an explicit schema version, a supported label type, and confidence between 0.0 and 1.0. Label validation does not change candidates, runtime scoring, or runtime decisions.

## 8. Feature / Label Dataset Model

A dataset record includes `dataset_id`, `dataset_name`, `feature_schema_version`, `label_schema_version`, `features`, `labels`, `source_records`, `dataset_purpose`, `created_by`, `created_at`, `validation_status`, `validation_notes`, `train_split_reference`, `test_split_reference`, `runtime_influence`, and `runtime_active`.

The dataset model is a governed collection of X feature vectors and y observed outcomes. It is not a model. It contains no learned parameters, no scoring function, no inference path, and no runtime activation path.

## 9. Dataset Lineage

Dataset lineage must identify the feature schema version, label schema version, source records, creation actor, dataset purpose, and validation notes.

Source records are local metadata references. They do not trigger database writes, OCI calls, Oracle Agent Memory calls, semantic recall calls, LLM calls, network calls, parser execution, scoring execution, or dashboard behavior.

## 10. Dataset Validation

Dataset validation checks required fields, supported feature and label types, supported label names, confidence bounds, schema version consistency, runtime flags, and joinability between feature and label records.

Dataset validation is not training. Validation may report unmatched features and unmatched labels in `validation_notes`. Validation does not fit a model, evaluate a model, backtest a model, calculate Score_ml(x), calculate Score(x, t), or alter deterministic Score(x).

## 11. Runtime Influence Boundary

Phase 7T requires `runtime_influence=false` and `runtime_active=false`. Validation rejects `runtime_influence=true` and rejects `runtime_active=true`.

No dataset may be marked runtime active in Phase 7T. Dataset creation and validation do not grant runtime influence.

## 12. Deterministic Runtime Boundary

Deterministic runtime remains authoritative. Existing deterministic parser, feature engineering, scoring, trend/anomaly, decision, recommendation, and Phase 4I contract behavior remain the runtime source of truth.

Phase 7T adds no runtime scoring changes and no runtime decision changes. Dataset records may be inspected by future governed phases, but they do not affect runtime output.

## 13. Materialization Boundary

Phase 7T does not bypass Phase 7M-7R materialization. Dataset records are governed input, not materialized runtime changes.

Any future parser, scoring, recommendation, model, or runtime behavior change must still pass through controlled materialization, validation, rollback, and certification gates defined by the Phase 7 model.

## 14. ML Boundary

learned_model(x) is not implemented. Score_ml(x) is not implemented. Score(x, t) is not implemented.

Phase 7T does not train ML models, infer with ML models, create a model registry, activate a model, or change scoring. Future ML phases may use governed datasets only after their own scope, validation, and runtime boundaries are defined.

## 15. Semantic Context Boundary

Semantic context remains reviewer-assist only and non-authoritative. Phase 7T adds no Oracle Agent Memory dependency, no semantic recall service dependency, no LLM calls, and no semantic context runtime dependency.

Semantic summaries are not automatically labels, source evidence, parser truth, scoring truth, recommendation truth, or runtime evidence.

## 16. Parser / Scoring / Recommendation Boundary

Phase 7T does not import parser modules, scoring modules, decision modules, recommendation modules, dashboard modules, CLI modules, database clients, OCI clients, or network clients.

No parser/scoring/recommendation behavior changes are introduced. No parser output changes are introduced. No scoring weights, thresholds, severities, confidence rules, decision rules, recommendation rankings, or recommendation rationale are changed.

## 17. Relationship to Phase 7S

Phase 7S established the ML / adaptive scoring boundary: ML starts in shadow mode, deterministic scoring remains authoritative, ML is non-authoritative by default, learned_model(x) is not implemented, Score_ml(x) is not implemented, Score(x, t) is not implemented, training is not implemented, and runtime activation is not allowed.

Phase 7T implements the future dataset concept referenced by Phase 7S, but only as a governed local dataset model for X = feature vectors and y = observed outcomes. It does not change the Phase 7S ML boundary.

## 18. Relationship to Future Phase 7U

Future Phase 7U may define trend-aware scoring concepts. Phase 7T does not implement trend-aware scoring, does not implement Score(x, t), and does not change trend/anomaly runtime behavior.

## 19. Relationship to Future Phase 7V

Future Phase 7V may define a shadow ML model interface. Phase 7T does not implement learned_model(x), Score_ml(x), ML inference, model loading, model activation, or model runtime eligibility.

## 20. Relationship to Future Phase 7W

Future Phase 7W may define training and backtesting. Phase 7T does not train models, backtest models, fit parameters, calculate evaluation metrics, or compare model output to deterministic runtime scores.

## 21. Relationship to Future Phase 8

Phase 8 sizing/TCO is not implemented. Phase 7T does not implement sizing, TCO, what-if advisory, capacity planning, cost modeling, or advisory runtime changes.

Future Phase 8 may consume validated intelligence only after the necessary governed boundaries exist.

## 22. Acceptance Criteria

Phase 7T is accepted when the feature record model, label record model, feature schema model, label schema model, dataset model, deterministic ID helpers, validation helpers, serialization helpers, dataset join helper, dataset summary helper, architecture documentation, schema documentation, and local tests exist.

Acceptance also requires that dataset is not a model, dataset validation is not training, learned_model(x) is not implemented, Score_ml(x) is not implemented, Score(x, t) is not implemented, `runtime_influence=false`, `runtime_active=false`, deterministic runtime remains authoritative, no parser/scoring/recommendation behavior changes are made, no dashboard behavior is changed, no CLI behavior is changed, and Phase 8 sizing/TCO is not implemented.
