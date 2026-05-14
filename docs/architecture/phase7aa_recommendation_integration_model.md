# Phase 7AA.4 Recommendation Integration Model

## 1. Purpose

This document defines the Phase 7AA.4 recommendation integration result model. The model records advisory recommendation consideration only and preserves deterministic runtime authority.

## 2. RecommendationIntegrationResult Object Shape

`RecommendationIntegrationResult` contains:

- `result_id`
- `domain`
- `recommendation_id`
- `deterministic_recommendation`
- `deterministic_recommendation_authoritative`
- `proposed_recommendation`
- `proposed_rule_reference`
- `selected_advisory_recommendation`
- `selected_recommendation_source`
- `recommendation_change_summary`
- `evidence_mapping_summary`
- `gate_allowed_for_consideration`
- `fallback_to_deterministic`
- `fallback_reason`
- `phase4i_contract_preserved`
- `runtime_recommendation_applied`
- `runtime_mutation_performed`
- `runtime_active`
- `runtime_influence_granted`
- `validation_reference`
- `rollback_reference`
- `denied_reasons`
- `warnings`
- `rationale`
- `created_by`
- `notes`

## 3. Supported Recommendation Sources

Supported sources are:

- `deterministic`
- `proposed_rule`
- `recommendation_evolution`
- `none`

`deterministic` is the fallback and default source.

## 4. Selection Rules

Adaptive recommendation selection is advisory only. The adapter may select an advisory recommendation only when the gate allows consideration, the runtime context validates, deterministic recommendation output is present, validation reference exists, rollback reference exists, and the candidate recommendation is valid.

The deterministic selection order is:

1. `proposed_rule`
2. `recommendation_evolution`
3. `deterministic`

Selected advisory recommendation is not runtime recommendation.

## 5. Fallback Rules

Fallback to deterministic recommendation is required if any required gate, context, validation, rollback, or candidate condition fails.

Fallback results use `selected_recommendation_source=deterministic`, keep the selected advisory recommendation equal to the deterministic recommendation, and record a fallback reason.

## 6. Evidence Mapping Rules

Evidence mapping is represented with `evidence_mapping_summary`. Evidence references and evidence-bearing fields can be summarized, but no evidence mapping makes an adaptive recommendation authoritative.

An adaptive candidate without an evidence reference generates a warning. A proposed recommendation that lacks evidence mapping generates a warning.

## 7. Validation Rules

Validation requires:

- Non-empty `result_id`.
- Non-empty deterministic recommendation.
- Non-empty selected advisory recommendation.
- Supported selected recommendation source.
- Non-empty recommendation change summary.
- Non-empty evidence mapping summary.
- Non-empty rationale.
- List-shaped denied reasons and warnings.
- `deterministic_recommendation_authoritative=true`.
- `phase4i_contract_preserved=true`.
- `runtime_recommendation_applied=false`.
- `runtime_mutation_performed=false`.
- `runtime_active=false`.
- `runtime_influence_granted=false`.

Unsafe runtime flags are rejected.

## 8. Serialization Rules

Serialization uses deterministic dictionaries. Deserialization reconstructs and validates `RecommendationIntegrationResult` objects. No serialization helper reads files, calls services, or mutates runtime state.

## 9. Deterministic ID Rules

Recommendation integration result IDs use stable input values:

`ADAPTIVE-RECOMMENDATION-RESULT-<DOMAIN>-<RECOMMENDATION_ID>-<SOURCE>`

IDs use no random UUID, no timestamp, no database sequence, and no external service.

## 10. Runtime Safety Rules

The model never applies changes:

- `runtime_recommendation_applied=false`
- `runtime_mutation_performed=false`
- `runtime_active=false`
- `runtime_influence_granted=false`
- `deterministic_recommendation_authoritative=true`

No runtime recommendation changes are applied.

## 11. Non-Goals

This model does not implement runtime recommendation generation, ranking, wording changes, evidence mapping changes, dashboard controls, CLI commands, parser integration, scoring changes, rollback execution, or `run_analysis.py` integration.

Phase 8 sizing/TCO is not implemented.

## 12. Acceptance Criteria

- Recommendation integration result model exists.
- Supported recommendation sources are explicit.
- Selection is advisory only.
- Fallback to deterministic recommendation is required.
- Evidence mapping summary exists.
- Runtime flags remain false.
- Deterministic recommendations remain authoritative.
- No runtime recommendation changes are applied.
