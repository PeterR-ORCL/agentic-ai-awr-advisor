# Phase 7 ML Validation Matrix

## Purpose

Phase 7Z provides the consolidated validation matrix for the Phase 7S-7Y ML / adaptive scoring block. It certifies that ML remains shadow/advisory, deterministic runtime remains authoritative, and no model is runtime active.

## Scope

The validation scope covers Phase 7S through Phase 7Y: ML boundary metadata, feature / label dataset records, trend-aware advisory scoring records, shadow ML interface records, training / backtesting evaluation records, explainability records, and model registry governance metadata. The matrix also covers import isolation, runtime safety, deterministic runtime boundaries, Phase 4I contract protection, materialization regression, Phase 7 foundation regression, and optional Phase 6 regression.

## Non-Goals

Phase 7Z does not add ML behavior, train models, implement learned_model(x), implement real model inference, deploy models, activate models, grant runtime eligibility, change scoring weights, change scoring thresholds, change severity cutoffs, change parser behavior, change decision behavior, change recommendation behavior, change dashboard behavior, change CLI behavior, or implement Phase 8. Phase 8 is not implemented.

## Validation Categories

The required validation categories are `ml_boundary`, `feature_label_dataset`, `trend_aware_scoring`, `shadow_ml_model_interface`, `ml_training_backtesting`, `ml_explainability`, `ml_model_registry`, `import_isolation`, `runtime_safety`, and `documentation`. Acceptance requires every category to pass with `runtime_active=false`, `runtime_influence=false`, `runtime_influence_granted=false`, and `runtime_eligibility_granted=false`.

## 7S ML Boundary Validation

The 7S validation confirms that the ML boundary exists, is explicit, and is enforced as shadow/advisory only. It confirms no learned model, no Score_ml(x), no Score(x, t) replacement, no training implementation, no runtime activation, and no runtime scoring changes are applied.

## 7T Feature / Label Dataset Validation

The 7T validation confirms that governed feature / label datasets are structured inputs only. The dataset is not a model, dataset validation is not training, dataset records keep `runtime_influence=false` and `runtime_active=false`, and datasets cannot replace deterministic scoring.

## 7U Trend-Aware Scoring Validation

The 7U validation confirms that trend-aware scoring remains advisory/shadow only. Trend-aware scoring may compare and explain local bounded scores, but it cannot change thresholds, severities, confidence, decisions, recommendations, parser output, or Phase 4I output.

## 7V Shadow ML Interface Validation

The 7V validation confirms that the shadow ML interface is non-authoritative. Shadow ML output can be compared with deterministic and trend-aware scores, but the shadow ML output cannot become runtime truth and cannot grant runtime influence.

## 7W Training / Backtesting Validation

The 7W validation confirms that training/backtesting is evaluation only. Training plans, split records, training results, backtest results, and metrics are offline evaluation records only, with no model deployment, no saved model activation, and no runtime scoring replacement.

## 7X Explainability Validation

The 7X validation confirms that explainability is not runtime truth. Explanations, feature contributions, score comparisons, and confidence explanations are explanatory only and do not change runtime scoring, decisions, recommendations, or parser output.

## 7Y Model Registry Validation

The 7Y validation confirms that the model registry is governance metadata only. Model approval does not activate runtime scoring, model registry records cannot deploy models, and `runtime_eligibility_granted=false`, `runtime_active=false`, and `runtime_influence_granted=false` remain enforced.

## Import Isolation Validation

Import isolation validation scans `scripts/run_analysis.py`, parser modules, scoring modules, decision modules, and recommendation modules. These runtime paths must not import `ml_boundary`, `feature_label_dataset`, `trend_aware_scoring`, `shadow_ml_model_interface`, `ml_training_backtesting`, `ml_explainability`, or `ml_model_registry`.

## Runtime Safety Validation

Runtime safety validation asserts that `runtime_active=true`, `runtime_influence=true`, `runtime_influence_granted=true`, and `runtime_eligibility_granted=true` are not accepted by ML/adaptive modules. It also checks that active runtime functions such as `deploy_model`, `activate_model`, `save_model`, `load_model`, `update_runtime_scoring`, `replace_scoring_engine`, `apply_ml_score`, `grant_runtime_eligibility`, `auto_apply`, and `autonomous_apply` are not exposed.

## Deterministic Runtime Boundary Validation

Deterministic runtime remains authoritative. Phase 7Z certification does not alter scoring weights, scoring thresholds, severity cutoffs, decision logic, recommendation logic, parser behavior, parser output, dashboard behavior, CLI behavior, database state, or generated dashboard output.

## Phase 4I Contract Boundary Validation

Phase 4I contract remains protected. ML/adaptive validation does not modify the output contract, does not add ML fields to deterministic runtime truth, and does not allow shadow/advisory records to become authoritative evidence.

## Materialization Regression Validation

Materialization regression validation confirms that Phase 7M-7R controlled materialization remains proposal-only and inactive. Candidate approval does not equal runtime activation, materialization is not activation, and no materialized artifact changes runtime scoring or parser/recommendation behavior.

## Phase 7 Foundation Regression Validation

Phase 7 foundation regression validation confirms that Phase 7A-7L learning governance remains candidate-based, human-governed, reviewer-assist only, local, deterministic, and non-runtime-mutating.

## Phase 6 Regression Validation

Phase 6 regression validation is optional in the 7Z validation script and required for release confidence when dependencies are available. It confirms governed memory and semantic recall remain non-authoritative and do not alter parser/scoring/decision/recommendation runtime truth.

## Acceptance Criteria

Phase 7Z is accepted only when all required ML validation groups pass, documentation is complete, import isolation passes, runtime safety passes, no model is runtime active, no runtime scoring changes are applied, deterministic runtime remains authoritative, Phase 4I contract remains protected, and Phase 8 is not implemented.
