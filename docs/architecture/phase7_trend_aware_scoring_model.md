# Phase 7U Trend-Aware Scoring Model

## 1. Purpose

This document defines the local deterministic object model for Phase 7U trend-aware advisory scoring. Score(x, t) is implemented as advisory/shadow only deterministic scoring. It does not replace runtime score truth.

## 2. TrendContext Object Shape

`TrendContext` contains `trend_id`, `domain`, `trend_direction`, `trend_strength`, `trend_window`, `trend_confidence`, `trend_signal_count`, `evidence_reference`, and `notes`.

The record represents explicit local trend context. It does not call a live trend engine and does not recalculate runtime trends.

## 3. AnomalyContext Object Shape

`AnomalyContext` contains `anomaly_id`, `domain`, `anomaly_count`, `anomaly_severity`, `anomaly_confidence`, `anomaly_pattern`, `recurrence_count`, `evidence_reference`, and `notes`.

The record represents explicit local anomaly context. It does not call a live anomaly engine and does not change runtime anomaly behavior.

## 4. TrendAwareScoringInput Object Shape

`TrendAwareScoringInput` contains `input_id`, `run_id`, `awr_id`, `domain`, `baseline_score`, `trend_context`, `anomaly_context`, `feature_reference`, `score_version`, `runtime_influence`, and `runtime_active`.

At least one of `run_id` or `awr_id` is required. `baseline_score` must be between 0.0 and 100.0. `runtime_influence=false` and `runtime_active=false` are required.

## 5. TrendAwareScoreResult Object Shape

`TrendAwareScoreResult` contains `result_id`, `input_id`, `domain`, `baseline_score`, `trend_aware_score`, `score_delta`, `trend_influence`, `anomaly_influence`, `advisory_status`, `explanation`, `confidence`, `runtime_influence`, `runtime_active`, and `deterministic_runtime_remains_authoritative`.

Every result requires `runtime_influence=false`, `runtime_active=false`, and `deterministic_runtime_remains_authoritative=true`. No trend-aware result replaces runtime score.

## 6. Supported Domains

Supported domains are `CPU`, `IO`, `MEMORY`, `COMMIT`, `RAC`, and `ADG`. Common `I/O` variants may normalize to `IO`; new domains are not invented.

## 7. Supported Trend Directions

Supported trend directions are `improving`, `stable`, `degrading`, `volatile`, and `insufficient_data`.

## 8. Supported Anomaly Patterns

Supported anomaly patterns are `none`, `isolated`, `recurring`, `severe`, `noisy`, and `insufficient_data`.

## 9. Advisory Statuses

Supported statuses are `SHADOW_ONLY`, `ADVISORY_ONLY`, and `INSUFFICIENT_CONTEXT`. There is no runtime-active status.

## 10. Scoring Rules

The Phase 7U scoring helper computes:

```text
trend_aware_score = clamp(baseline_score + trend_influence + anomaly_influence, 0.0, 100.0)
score_delta = trend_aware_score - baseline_score
```

Trend influence is bounded. Improving trends apply a negative advisory adjustment, stable trends apply no adjustment, degrading trends apply a positive advisory adjustment, volatile trends apply a positive caution adjustment, and insufficient data applies no trend adjustment.

Anomaly influence is bounded. No anomaly applies no adjustment, isolated anomalies apply a small positive adjustment, recurring anomalies apply a moderate positive adjustment, severe anomalies apply a larger positive adjustment, noisy anomalies apply a small caution adjustment, and insufficient data applies no anomaly adjustment.

## 11. Confidence Rules

Confidence is deterministic, never exceeds 0.95, and never implies runtime authority. Missing or insufficient context lowers confidence. Confidence is an advisory reliability indicator only.

## 12. Validation Rules

Trend context validation requires supported domain, supported trend direction, trend strength between 0.0 and 1.0, trend confidence between 0.0 and 1.0, and non-negative signal count.

Anomaly context validation requires supported domain, non-negative anomaly count, anomaly severity between 0.0 and 1.0, anomaly confidence between 0.0 and 1.0, supported anomaly pattern, and non-negative recurrence count.

Input validation requires supported domain, baseline score between 0.0 and 100.0, at least one of `run_id` or `awr_id`, score version, `runtime_influence=false`, and `runtime_active=false`.

Result validation requires baseline and trend-aware scores between 0.0 and 100.0, confidence between 0.0 and 0.95, supported advisory status, `runtime_influence=false`, `runtime_active=false`, and `deterministic_runtime_remains_authoritative=true`.

## 13. Serialization Rules

Each record has deterministic to/from dictionary helpers. Deserialization re-runs validation and rejects runtime activation flags set to true. IDs are deterministic from stable input values and do not use UUIDs, timestamps, current time, network calls, or database calls.

## 14. Runtime Boundary

No trend-aware result replaces runtime score. No Phase 4I contract is changed. No runtime scoring changes are applied. Deterministic scoring remains authoritative.

Phase 7U does not import parser, scoring, decision, recommendation, dashboard, CLI, database, OCI, Oracle Agent Memory, semantic recall, LLM, or network dependencies.

## 15. Non-Goals

Phase 7U does not implement learned_model(x), Score_ml(x), model training, model backtesting, model registry behavior, certification, Phase 8 sizing/TCO, dashboard controls, CLI controls, parser changes, scoring engine changes, decision changes, or recommendation changes.

## 16. Acceptance Criteria

The model is accepted when TrendContext, AnomalyContext, TrendAwareScoringInput, and TrendAwareScoreResult validate and serialize deterministically; Score(x, t) returns only advisory/shadow results; `runtime_influence=false`; `runtime_active=false`; `deterministic_runtime_remains_authoritative=true`; deterministic scoring remains authoritative; no trend-aware result replaces runtime score; no Phase 4I contract is changed; learned_model(x) is not implemented; Score_ml(x) is not implemented; no model training is implemented; and no Phase 8 sizing/TCO is implemented.
