# Phase 7AA.6 Runtime Fallback / Rollback Layer

## 1. Purpose

Phase 7AA.6 defines the shared runtime fallback / rollback decision layer for controlled adaptive runtime integration. It evaluates scoring, recommendation, and parser adapter result records and produces one conservative runtime safety decision.

The fallback layer does not execute rollback.

## 2. Scope

This phase adds local deterministic decision records, adapter safety checks, rollback-reference checks, validation helpers, and serialization helpers. It remains in-memory and decision-only.

## 3. Non-Goals

This phase does not execute rollback, apply adaptive behavior, change files, mutate Phase 4I, modify runtime scoring, modify runtime recommendations, modify runtime parser behavior, change dashboard behavior, change CLI behavior, or modify `run_analysis.py`.

Phase 8 sizing/TCO is not implemented.

## 4. Fallback Is the Default Safe Posture

Deterministic fallback is default. If anything is missing, denied, invalid, unsafe, or uncertain, the final posture remains deterministic fallback.

## 5. Rollback Decision Is Not Rollback Execution

Rollback is represented as a decision requirement only. The layer can state whether rollback reference is present or missing, but rollback decision is not rollback execution.

## 6. Runtime Fallback Decision Flow

The decision flow:

1. Normalize adapter result records.
2. Check scoring, recommendation, and parser safety independently.
3. Detect runtime mutation or runtime influence flags.
4. Check Phase 4I preservation.
5. Check rollback, validation, and readiness references for adaptive consideration.
6. Emit one final posture.

Supported postures are `deterministic_fallback`, `adaptive_consideration_ready`, and `unsafe_requires_review`.

Adaptive_consideration_ready is not runtime active.

## 7. Scoring Adapter Safety

Scoring is safe only when runtime scoring was not applied, runtime mutation did not occur, runtime is not active, runtime influence was not granted, deterministic scoring remains authoritative, Phase 4I is preserved, and either deterministic fallback or gate consideration is recorded.

## 8. Recommendation Adapter Safety

Recommendation is safe only when runtime recommendation output was not applied, runtime mutation did not occur, runtime is not active, runtime influence was not granted, deterministic recommendations remain authoritative, Phase 4I is preserved, and either deterministic fallback or gate consideration is recorded.

## 9. Parser Adapter Safety

Parser is safe only when runtime parser output was not applied, runtime mutation did not occur, runtime is not active, runtime influence was not granted, current parser remains authoritative, Phase 4I is preserved, AWR regression is required, scoring regression is required, unknown signal safety is required, and either current parser fallback or gate consideration is recorded.

## 10. Rollback Reference Requirement

Rollback reference is required when any adaptive adapter result is allowed for consideration, when an adaptive source is selected, or when any gate result allows consideration. If rollback reference is missing, fallback is required and the final posture cannot be adaptive_consideration_ready.

## 11. Phase 4I Contract Boundary

Phase 4I contract preservation is mandatory. Any adapter result that fails Phase 4I preservation makes deterministic fallback required and makes the decision unsafe for review.

## 12. Deterministic Runtime Boundary

Deterministic runtime remains authoritative. Every valid decision preserves `deterministic_runtime_authoritative=true`.

## 13. Runtime Influence Boundary

Runtime mutation is not allowed. Runtime influence is not allowed. If any adapter record indicates runtime mutation or runtime influence, the final posture becomes `unsafe_requires_review` and fallback remains required.

The fallback layer does not apply adaptive behavior.

## 14. Relationship to 7AA.1 Runtime Gate

Phase 7AA.1 defines the opt-in runtime gate. Phase 7AA.6 consumes gate outcomes only as safety signals and cannot activate runtime behavior.

## 15. Relationship to 7AA.2 Runtime Context

Phase 7AA.2 defines the read-only adaptive runtime context. Phase 7AA.6 can validate that context before producing a unified posture.

## 16. Relationship to 7AA.3 Scoring Adapter

Phase 7AA.3 produces advisory scoring result records. Phase 7AA.6 checks those records for safety and fallback requirements.

## 17. Relationship to 7AA.4 Recommendation Adapter

Phase 7AA.4 produces advisory recommendation result records. Phase 7AA.6 checks those records for safety and fallback requirements.

## 18. Relationship to 7AA.5 Parser Adapter

Phase 7AA.5 produces parser backlog / integration consideration records. Phase 7AA.6 checks those records for safety and regression requirements.

## 19. Relationship to Future 7AA.7

Phase 7AA.7 may validate and certify the controlled integration path. Phase 7AA.6 does not certify, wire, execute, or activate runtime behavior.

## 20. Acceptance Criteria

- Runtime fallback / rollback decision layer exists.
- Fallback layer does not execute rollback.
- Fallback layer does not apply adaptive behavior.
- Deterministic fallback is default.
- Adaptive_consideration_ready is not runtime active.
- Runtime mutation is not allowed.
- `run_analysis.py` is not modified.
- run_analysis.py is not modified.
- Parser/scoring/recommendation modules are not modified.
- Runtime safety records are deterministic and serializable.
- Phase 8 sizing/TCO is not implemented.
