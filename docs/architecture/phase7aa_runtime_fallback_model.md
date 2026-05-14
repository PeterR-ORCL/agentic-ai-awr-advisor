# Phase 7AA.6 Runtime Fallback Model

## 1. Purpose

This document defines the Phase 7AA.6 `RuntimeFallbackDecision` model. The model records the safe final runtime posture after evaluating scoring, recommendation, and parser adapter result records.

## 2. RuntimeFallbackDecision Object Shape

`RuntimeFallbackDecision` contains:

- `decision_id`
- `deterministic_runtime_authoritative`
- `final_runtime_posture`
- `fallback_to_deterministic`
- `fallback_required`
- `rollback_required`
- `rollback_available`
- `rollback_reference`
- `phase4i_contract_preserved`
- `runtime_mutation_detected`
- `runtime_influence_detected`
- `scoring_safe`
- `recommendation_safe`
- `parser_safe`
- `scoring_fallback_required`
- `recommendation_fallback_required`
- `parser_fallback_required`
- `denied_reasons`
- `warnings`
- `required_next_steps`
- `validation_reference`
- `readiness_reference`
- `created_by`
- `notes`

## 3. Final Runtime Postures

Supported postures are:

- `deterministic_fallback`
- `adaptive_consideration_ready`
- `unsafe_requires_review`

No posture means runtime active. Adaptive_consideration_ready is not runtime active.

## 4. Component Safety Rules

Scoring, recommendation, and parser adapter results are evaluated separately. Each component is safe only when its runtime mutation flags remain false, its deterministic authority flag remains true, Phase 4I is preserved, and either fallback or gate consideration is recorded.

Parser safety also requires AWR regression, scoring regression, and unknown signal safety requirements.

## 5. Rollback Rules

Rollback reference is required for adaptive consideration. Missing rollback reference requires deterministic fallback and prevents adaptive_consideration_ready.

Rollback decision is not rollback execution.

## 6. Validation Rules

Validation requires:

- Non-empty `decision_id`.
- Supported final runtime posture.
- `deterministic_runtime_authoritative=true`.
- `phase4i_contract_preserved=true`.
- List-shaped denied reasons, warnings, and required next steps.
- `deterministic_fallback` implies `fallback_to_deterministic=true`.
- `unsafe_requires_review` implies `fallback_required=true`.
- Runtime mutation and runtime influence detection are only valid under `unsafe_requires_review`.

## 7. Serialization Rules

Serialization uses deterministic dictionaries. Deserialization reconstructs and validates `RuntimeFallbackDecision` objects. No serialization helper executes rollback, reads files, calls services, or mutates runtime state.

## 8. Deterministic ID Rules

Runtime fallback decision IDs use stable input values:

`RUNTIME-FALLBACK-<VALIDATION_REFERENCE>-<READINESS_REFERENCE>`

IDs use no random UUID, no timestamp, no database sequence, and no external service.

## 9. Runtime Safety Rules

Every valid decision preserves:

- `deterministic_runtime_authoritative=true`
- `fallback_to_deterministic=true`
- `phase4i_contract_preserved=true`

Fallback_required=true when unsafe or uncertain. No runtime changes are applied.

## 10. Non-Goals

This model does not execute rollback, apply adaptive scoring, apply adaptive recommendations, apply parser changes, modify `run_analysis.py`, modify dashboard behavior, modify CLI behavior, or implement Phase 8 sizing/TCO.

## 11. Acceptance Criteria

- `RuntimeFallbackDecision` model exists.
- Deterministic fallback helper exists.
- Adapter safety evaluators exist.
- Rollback-reference checks exist.
- Serialization helpers exist.
- Deterministic fallback is default.
- Rollback decision is not rollback execution.
- No runtime changes are applied.
