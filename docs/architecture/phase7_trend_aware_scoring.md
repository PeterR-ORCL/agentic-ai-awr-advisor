# Phase 7U Trend-Aware Scoring

## 1. Purpose

Phase 7U implements Score(x, t) as deterministic advisory scoring. It compares a baseline deterministic score, `score_x`, with explicit local trend and anomaly context, `t`, and returns a shadow-only advisory score, `score_x_t`. The result helps reviewers understand directional risk without changing runtime truth.

Trend-aware scoring is advisory/shadow only. Deterministic scoring remains authoritative.

## 2. Scope

Phase 7U adds local records for trend context, anomaly context, trend-aware scoring input, and trend-aware score result. It also adds deterministic helper functions for validation, scoring, explanations, IDs, and serialization.

All inputs are explicit records supplied to the helper functions. Phase 7U does not call the live trend engine, parser, runtime scoring engine, decision engine, recommendation engine, dashboard, CLI, database, OCI service, Oracle Agent Memory, semantic recall service, LLM, or network.

## 3. Non-Goals

Phase 7U does not replace runtime scoring, modify runtime scoring weights, modify runtime scoring thresholds, modify severity cutoffs, modify confidence logic, modify trend/anomaly runtime behavior, modify decisions, modify recommendations, modify parser behavior, modify Phase 4I output, add dashboard controls, add CLI controls, write to a database, or add service dependencies.

learned_model(x) is not implemented. Score_ml(x) is not implemented. No model training is implemented. No backtesting, explainability beyond deterministic contribution summaries, model registry behavior, certification, or Phase 8 sizing/TCO is implemented.

## 4. Score(x, t) Concept

Score(x, t) is the Phase 7U deterministic advisory function:

```text
Score(x, t) = f(x, trends, anomalies)
```

Here, `x` is represented by a baseline deterministic score and optional feature reference. `t` is represented by explicit trend and anomaly context records. The function computes trend and anomaly influences, adds those bounded influences to the baseline score, clamps the result to 0-100, and returns an advisory result.

Score(x, t) is not ML. It is deterministic and local.

## 5. Baseline Deterministic Score

The baseline deterministic score is `score_x`. It is the existing deterministic score for a domain or component and remains the runtime source of truth. Phase 7U reads this value as input and never mutates it.

## 6. Trend Context

Trend context records describe the observed direction and reliability of a trend signal. Supported directions are `improving`, `stable`, `degrading`, `volatile`, and `insufficient_data`.

Trend context includes a supported domain, strength between 0.0 and 1.0, optional window, confidence between 0.0 and 1.0, signal count, optional evidence reference, and optional notes.

## 7. Anomaly Context

Anomaly context records describe anomaly volume, severity, confidence, pattern, and recurrence. Supported anomaly patterns are `none`, `isolated`, `recurring`, `severe`, `noisy`, and `insufficient_data`.

Anomaly context includes a supported domain, non-negative anomaly count, severity between 0.0 and 1.0, confidence between 0.0 and 1.0, recurrence count, optional evidence reference, and optional notes.

## 8. Trend-Aware Score Result

The trend-aware score result contains the baseline score, advisory trend-aware score, score delta, trend influence, anomaly influence, advisory status, explanation, confidence, and runtime safety flags.

Every result keeps `runtime_influence=false`, `runtime_active=false`, and `deterministic_runtime_remains_authoritative=true`.

## 9. Advisory / Shadow Boundary

Trend-aware scoring is advisory/shadow only. It may compute an advisory score, compare against deterministic score, and explain the deterministic trend/anomaly influence. It may not apply the advisory score to runtime scoring.

Advisory statuses are `SHADOW_ONLY`, `ADVISORY_ONLY`, and `INSUFFICIENT_CONTEXT`. There is no runtime-active status.

## 10. Runtime Influence Boundary

Phase 7U enforces `runtime_influence=false` and `runtime_active=false` on trend-aware inputs and results. No runtime scoring changes are applied.

Trend-aware output is not eligible to change runtime weights, thresholds, severity, confidence, decisions, recommendations, or parser output.

## 11. Deterministic Runtime Boundary

Deterministic scoring remains authoritative. Existing deterministic score values remain the runtime source of truth. A trend-aware score can be stored or displayed later only as advisory evidence if a future phase explicitly adds such behavior under governance.

## 12. Decision / Recommendation Boundary

Phase 7U does not change decision logic, recommendation logic, recommendation priority, recommendation ranking, recommendation rationale, or recommendation evidence. No decision/recommendation changes are applied.

## 13. Parser Boundary

Phase 7U does not modify parser behavior, parser mappings, parser unknown handling, parser output, or the Phase 4I output contract. No Phase 4I contract is changed.

## 14. Materialization Boundary

Phase 7U does not bypass Phase 7M-7R controlled materialization. Trend-aware scoring does not create runtime materialized scoring changes and does not grant runtime influence.

## 15. ML Boundary

Score(x, t) is deterministic advisory scoring, not a learned model. learned_model(x) is not implemented. Score_ml(x) is not implemented. No model training is implemented. No model backtesting, registry behavior, or certification is implemented.

## 16. Relationship to Phase 7S

Phase 7S defined the ML/adaptive scoring boundary and explicitly kept ML in shadow mode. Phase 7U implements the deterministic Score(x, t) concept that Phase 7S reserved for future work, while preserving Phase 7S boundaries: deterministic runtime remains authoritative, runtime influence remains false, and learned scoring is not implemented.

## 17. Relationship to Phase 7T

Phase 7T defined governed feature/label dataset records for future learning. Phase 7U may reference the deterministic feature state by ID, but it does not train on Phase 7T datasets, validate model readiness, or change dataset runtime flags. Dataset validation is still not training.

## 18. Relationship to Future Phase 7V

Future Phase 7V may define a shadow ML model interface. Phase 7U does not implement that interface, does not implement Score_ml(x), and does not implement learned_model(x).

## 19. Relationship to Future Phase 7W

Future Phase 7W may address training and backtesting. Phase 7U does not train a model, does not backtest a model, and does not add model evaluation pipelines.

## 20. Relationship to Future Phase 8

Phase 8 sizing/TCO is not implemented here. Phase 7U does not implement sizing, capacity planning, cost modeling, TCO, or what-if advisory behavior.

## 21. Acceptance Criteria

Phase 7U is accepted when local deterministic trend-aware scoring records and helpers exist, Score(x, t) computes advisory/shadow scores only, trend and anomaly influence summaries are explainable, inputs and results serialize deterministically, validation enforces supported domains and safe runtime flags, deterministic scoring remains authoritative, no runtime scoring changes are applied, learned_model(x) is not implemented, Score_ml(x) is not implemented, no model training is implemented, no Phase 8 sizing/TCO is implemented, and parser/scoring/decision/recommendation/dashboard/CLI behavior remains unchanged.
