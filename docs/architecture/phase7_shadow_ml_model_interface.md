# Phase 7V Shadow ML Model Interface

## 1. Purpose

Phase 7V defines a local shadow ML model interface for representing `Score_ml(x)`-style output records. Score_ml(x) exists only as a shadow interface/result contract. It is a record and comparison shape, not a runtime scoring path.

Shadow ML is non-authoritative. Deterministic scoring remains authoritative.

## 2. Scope

Phase 7V adds local deterministic object models for shadow model metadata, shadow ML input, and shadow ML output. It also adds validation, deterministic ID helpers, serialization helpers, comparison helpers, and a placeholder shadow score helper.

All behavior is local and deterministic. Phase 7V does not call parser, scoring, decision, recommendation, dashboard, CLI, database, OCI, Oracle Agent Memory, semantic recall, LLM, or network dependencies.

## 3. Non-Goals

No real ML model is implemented. No training is implemented. No learned_model(x) is implemented. No model registry is implemented. No persisted model files are loaded or saved.

Phase 7V does not modify runtime scoring weights, thresholds, decisions, recommendations, parser behavior, parser output, Phase 4I output, dashboard behavior, CLI behavior, database schema, generated dashboard HTML, or materialized runtime artifacts. Phase 8 sizing/TCO is not implemented.

## 4. Score_ml(x) Shadow Interface Concept

`Score_ml(x)` is represented as a shadow interface/result contract only. The interface accepts explicit local inputs and emits a shadow output record with score, confidence, deltas, disagreement summary, boundary summary, and runtime safety flags.

The placeholder helper is deterministic and simple. It exists to exercise the interface shape, not to act as a learned model. Shadow output does not change runtime scoring.

## 5. Shadow Model Metadata

Shadow model metadata identifies `model_id`, `model_family`, `model_version`, optional feature and label schema versions, optional training and validation references, and notes.

Supported model families are `tree`, `neural_net`, `hybrid_rule_ml`, `linear`, `baseline_mock`, and `external_placeholder`. These values are metadata only in Phase 7V. They do not imply trained trees, neural networks, linear models, or external inference.

Every metadata record requires `runtime_active=false` and `runtime_influence_granted=false`.

## 6. Shadow ML Input

Shadow ML input records identify `input_id`, `run_id` or `awr_id`, optional feature and dataset references, deterministic score, optional trend-aware score, feature values, `model_id`, and score version.

Every input requires `runtime_influence=false` and `runtime_active=false`. At least one of `run_id` or `awr_id` is required. Scores must remain between 0.0 and 100.0.

## 7. Shadow ML Output

Shadow ML output records identify `output_id`, `input_id`, `model_id`, model family, deterministic score, optional trend-aware score, shadow ML score, deltas, confidence, advisory status, disagreement summary, boundary summary, and runtime safety flags.

Every output requires `runtime_influence=false`, `runtime_active=false`, `runtime_influence_granted=false`, and `deterministic_runtime_remains_authoritative=true`.

## 8. Placeholder Shadow Score

The placeholder shadow score starts from the deterministic score. If a trend-aware score is supplied, the helper may apply a small bounded deterministic blend. If feature values contain numeric risk-style fields, the helper may apply a small bounded deterministic adjustment. The result is clamped to 0.0 through 100.0.

Confidence never exceeds 0.95 and is lower when little context is present. Advisory status is `SHADOW_ONLY` or `INSUFFICIENT_MODEL_CONTEXT`. The helper performs no training, fitting, backtesting, persisted model loading, external service call, or runtime update.

## 9. Deterministic Runtime Boundary

Deterministic scoring remains authoritative. Phase 7V accepts deterministic score as input and may compare against it, but it never replaces it.

No shadow ML output becomes runtime truth. No output changes deterministic severity, confidence, decisions, recommendations, parser output, or Phase 4I output.

## 10. Runtime Influence Boundary

Phase 7V enforces `runtime_influence=false`, `runtime_active=false`, and `runtime_influence_granted=false`. Records marked with true runtime flags are invalid.

There is no runtime-active advisory status. `SHADOW_ONLY`, `ADVISORY_ONLY`, `INSUFFICIENT_MODEL_CONTEXT`, and `INVALID_INPUT` are not runtime activation states.

## 11. Relationship to Deterministic Score

The deterministic score is the authoritative baseline. Shadow ML may calculate `ml_delta_from_deterministic` and summarize disagreement for later review. The delta is evidence for review only and has no runtime force.

## 12. Relationship to Trend-Aware Score

Phase 7U trend-aware scoring remains advisory/shadow only. Phase 7V may accept a trend-aware score as an optional comparison point and calculate `ml_delta_from_trend_aware`.

Neither trend-aware score nor shadow ML score changes runtime scoring.

## 13. Relationship to Feature / Label Dataset

Phase 7T defines governed feature vectors and observed outcomes. Phase 7V may reference feature schema, label schema, dataset ID, or explicit feature values, but it does not train on those records.

Dataset validation is not training. A dataset is not a model.

## 14. Relationship to Phase 7S Boundary

Phase 7S established that ML starts in shadow mode and that learned_model(x) and Score_ml(x) were not implemented there. Phase 7V advances only the shadow result contract for Score_ml(x). It preserves the Phase 7S rule that ML may compare, explain minimally, and propose later, but cannot bypass Phase 7M-7R materialization.

## 15. Relationship to Future Phase 7W Training / Backtesting

Future Phase 7W may define governed training and backtesting. Phase 7V does not train a model, backtest a model, evaluate model readiness, or certify runtime eligibility.

## 16. Relationship to Future Phase 7X Explainability

Future Phase 7X may define a fuller explainability layer. Phase 7V includes only minimal output fields such as deltas, confidence, disagreement summary, and boundary summary.

## 17. Relationship to Future Phase 7Y Model Registry

Future Phase 7Y may define model registry metadata, approval, rollback, and eligibility workflows. Phase 7V does not create a model registry and does not persist model artifacts.

## 18. Relationship to Future Phase 8

Phase 8 sizing/TCO is not implemented. Phase 7V does not implement sizing, capacity planning, cost modeling, TCO, or what-if advisory behavior.

## 19. Acceptance Criteria

Phase 7V is accepted when shadow model metadata, shadow ML input, and shadow ML output records exist; deterministic ID helpers, validation helpers, serialization helpers, comparison helpers, and a placeholder shadow score helper exist; Score_ml(x) exists only as a shadow interface/result contract; no real ML model is implemented; no training is implemented; no learned_model(x) is implemented; no model registry is implemented; shadow ML is non-authoritative; deterministic scoring remains authoritative; shadow output does not change runtime scoring; `runtime_influence=false`; `runtime_active=false`; `runtime_influence_granted=false`; no dashboard behavior is changed; no CLI behavior is changed; and parser/scoring/decision/recommendation behavior remains unchanged.
