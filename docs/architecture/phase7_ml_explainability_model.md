# Phase 7X ML Explainability Model

## 1. Purpose

This document defines the serializable object model for Phase 7X ML explainability records. The model exists to explain advisory/shadow ML artifacts locally and deterministically.

Explainability is not runtime truth. Explanations do not change runtime scoring. Deterministic scoring remains authoritative.

## 2. FeatureContribution Object Shape

`FeatureContribution` contains `feature_name`, `feature_domain`, `contribution_direction`, `contribution_strength`, `contribution_weight`, `evidence_reference`, and `explanation_text`.

`feature_name` and `explanation_text` are required. `feature_domain` and `evidence_reference` are optional strings. `contribution_strength` is bounded from 0.0 to 1.0. `contribution_weight` is bounded from -1.0 to 1.0.

Feature contributions are explanatory only. Contribution weights do not become model weights or runtime scoring weights.

## 3. ScoreComparisonExplanation Object Shape

`ScoreComparisonExplanation` contains `deterministic_score`, optional `trend_aware_score`, optional `shadow_ml_score`, optional `trend_delta`, optional `shadow_delta`, `disagreement_level`, and `disagreement_summary`.

Scores are bounded from 0.0 to 100.0 where present. `trend_delta` is `trend_aware_score - deterministic_score` when trend-aware score is present. `shadow_delta` is `shadow_ml_score - deterministic_score` when shadow ML score is present.

## 4. ConfidenceExplanation Object Shape

`ConfidenceExplanation` contains `confidence`, `uncertainty_reason`, `confidence_factors`, and `insufficient_context_flags`.

`confidence` is bounded from 0.0 to 0.95. Confidence is not score. Confidence factors and insufficient context flags explain uncertainty only and do not modify runtime confidence logic.

## 5. MLExplanationRecord Object Shape

`MLExplanationRecord` contains `explanation_id`, `source_output_id`, `model_id`, `domain`, `feature_contributions`, `score_comparison`, `confidence_explanation`, `top_positive_features`, `top_negative_features`, `boundary_summary`, `evidence_references`, `advisory_status`, `runtime_influence`, `runtime_active`, `runtime_influence_granted`, and `deterministic_runtime_remains_authoritative`.

`runtime_influence=false`, `runtime_active=false`, `runtime_influence_granted=false`, and `deterministic_runtime_remains_authoritative=true` are required.

## 6. Contribution Directions

Supported contribution directions are `increases_risk`, `decreases_risk`, `neutral`, and `insufficient_context`.

No contribution direction means runtime influence. Directions describe only the explanatory placeholder interpretation of supplied feature values.

## 7. Disagreement Levels

Supported disagreement levels are `none`, `low`, `moderate`, `high`, and `insufficient_context`.

When no trend-aware or shadow ML score is available for comparison, the disagreement level is `insufficient_context`. A zero delta is `none`, a nonzero delta below 5 is `low`, a delta from 5 through less than 15 is `moderate`, and a delta of 15 or more is `high`.

## 8. Explainability Statuses

Supported explainability statuses are `EXPLANATION_ONLY`, `SHADOW_EXPLANATION`, and `INSUFFICIENT_CONTEXT`.

No runtime-active status exists. No status means approved, certified, deployed, or runtime eligible.

## 9. Feature Contribution Rules

Feature values are interpreted deterministically. Numeric values above zero increase risk only when the feature name contains risk-oriented terms such as risk, pressure, wait, load, latency, or contention. Numeric values below or equal to zero are neutral.

Boolean true values are neutral unless the feature name suggests risk or decreased risk. Text and categorical values produce neutral contributions unless context is missing. Contributions are sorted deterministically by absolute contribution strength descending and then by feature name.

This is not ML feature importance. It is a deterministic explanation placeholder for the shadow layer.

## 10. Validation Rules

Validation requires non-empty identifiers and explanation text, supported contribution directions, supported disagreement levels, supported explainability statuses, score values between 0.0 and 100.0, confidence values between 0.0 and 0.95, contribution strengths between 0.0 and 1.0, and contribution weights between -1.0 and 1.0.

Validation rejects `runtime_influence=true`, `runtime_active=true`, `runtime_influence_granted=true`, and `deterministic_runtime_remains_authoritative=false`.

## 11. Serialization Rules

Every object has deterministic to-dictionary and from-dictionary helpers. Deserialization reruns validation and preserves the same runtime boundary rules.

Serialization does not write databases, files, dashboards, CLI state, model registry state, or runtime configuration. Serialization does not change Phase 4I.

## 12. Deterministic ID Rules

Explanation IDs use stable input fields:

```text
ML-EXPLAIN-<SOURCE_OUTPUT_ID>-<MODEL_ID>-<DOMAIN>
```

When model ID or domain is absent, stable placeholders are used. IDs do not use UUIDs, timestamps, database sequences, current time, network calls, or external services.

## 13. Runtime Boundary

Explanation records require `runtime_influence=false`, `runtime_active=false`, `runtime_influence_granted=false`, and `deterministic_runtime_remains_authoritative=true`.

No explanation changes Phase 4I. No explanation changes decisions or recommendations. No explanation changes parser output, scoring behavior, dashboard behavior, CLI behavior, database state, model registry state, or runtime configuration.

## 14. Non-Goals

Phase 7X does not implement model training, learned_model(x), Score_ml(x) activation, model registry, model approval, model deployment, model certification, dashboard explainability controls, CLI explainability commands, DB writes, OCI calls, Oracle Agent Memory calls, LLM calls, network calls, or Phase 8 sizing/TCO.

No model registry is implemented. No runtime activation is implemented. Phase 8 sizing/TCO is not implemented. Semantic context is not ML explanation.

## 15. Acceptance Criteria

The model is accepted when feature contribution, score comparison explanation, confidence explanation, and ML explanation record objects validate and serialize deterministically; deterministic IDs are stable; explanations are not runtime truth; feature contributions are explanatory only; confidence is not score; runtime influence fields are false; deterministic runtime remains authoritative; no explanation changes Phase 4I; no explanation changes decisions or recommendations; no model registry is implemented; no runtime activation is implemented; and Phase 8 sizing/TCO is not implemented.
