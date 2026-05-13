# Phase 7AA.3 Scoring Integration Model

## 1. Purpose

The Phase 7AA.3 scoring integration model defines the local deterministic result object and helper rules for advisory scoring integration. It evaluates candidate adaptive scores without applying runtime scoring changes.

## 2. ScoringIntegrationResult Object Shape

`ScoringIntegrationResult` contains `result_id`, `domain`, `deterministic_score`, `deterministic_score_authoritative`, `trend_aware_score`, `shadow_ml_score`, `proposed_score`, `selected_advisory_score`, `selected_score_source`, `score_delta_from_deterministic`, `gate_allowed_for_consideration`, `fallback_to_deterministic`, `fallback_reason`, `phase4i_contract_preserved`, `runtime_score_applied`, `runtime_mutation_performed`, `runtime_active`, `runtime_influence_granted`, validation and rollback references, denied reasons, warnings, rationale, creator, and notes.

The result requires `deterministic_score_authoritative=true`, `phase4i_contract_preserved=true`, `runtime_score_applied=false`, `runtime_mutation_performed=false`, `runtime_active=false`, and `runtime_influence_granted=false`.

## 3. Supported Score Sources

Supported score sources are `deterministic`, `trend_aware`, `shadow_ml`, `proposed_scoring_config`, and `none`. The deterministic source is the fallback/default. Trend-aware, shadow ML, and proposed scoring config sources are advisory only.

## 4. Selection Rules

The adapter may select an advisory score only when gate consideration is allowed, the runtime context validates, fallback remains available, Phase 4I is preserved, deterministic score is valid, the selected adaptive score is valid, rollback reference exists, and validation reference exists. Deterministic selection order is proposed scoring config score, then shadow ML score, then trend-aware score, then deterministic fallback.

## 5. Fallback Rules

Fallback to deterministic is required when gate consideration is denied, context is missing, context is invalid, validation reference is missing, rollback reference is missing, adaptive scores are invalid, or no adaptive score exists. Fallback selects `selected_score_source=deterministic` and `selected_advisory_score=deterministic_score`.

## 6. Score Scale Rules

Scores are 0.0-100.0. Confidence is not score and must not be mixed with score values. Confidence-like values remain 0.0-1.0 in their source layers and are not interpreted as score by this adapter.

## 7. Validation Rules

Validation rejects missing result IDs, missing domains, invalid score scales, unsupported score sources, `deterministic_score_authoritative=false`, `phase4i_contract_preserved=false`, `runtime_score_applied=true`, `runtime_mutation_performed=true`, `runtime_active=true`, `runtime_influence_granted=true`, non-list denied reasons, non-list warnings, and missing rationale.

## 8. Serialization Rules

Serialization uses deterministic dictionaries with explicit field names. Round trips through `scoring_integration_result_to_dict` and `scoring_integration_result_from_dict` preserve advisory decisions and runtime safety flags without calling runtime scoring, parser, decision, recommendation, dashboard, CLI, database, network, or `run_analysis.py`.

## 9. Deterministic ID Rules

Result IDs follow `ADAPTIVE-SCORING-RESULT-<DOMAIN>-<SOURCE>-<SCORE>`. IDs use no UUID, timestamp, database sequence, or external service and remain stable for the same domain, score source, and deterministic score.

## 10. Runtime Safety Rules

No runtime scoring changes are applied. The result is advisory only and must keep `runtime_score_applied=false`, `runtime_mutation_performed=false`, `runtime_active=false`, `runtime_influence_granted=false`, and `deterministic_score_authoritative=true`.

## 11. Non-Goals

Phase 7AA.3 does not replace deterministic scoring, update Phase 4I scores, change scoring modules, change parser behavior, change decisions, change recommendations, add dashboard controls, add CLI commands, execute rollback, implement recommendation adapters, implement parser adapters, or implement Phase 8 sizing/TCO.

## 12. Acceptance Criteria

The scoring integration model is accepted when the result object exists, score sources are explicit, selection rules are deterministic, fallback rules are safe, scores are 0.0-100.0, confidence is not score, validation rejects unsafe runtime flags, serialization is deterministic, deterministic score remains authoritative, no runtime scoring changes are applied, and Phase 8 sizing/TCO is not implemented.
