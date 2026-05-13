# Phase 7AA.3 Scoring Integration Adapter

## 1. Purpose

Phase 7AA.3 defines a controlled scoring integration adapter for the Agentic AI AWR Advisor project. The adapter evaluates supplied deterministic, trend-aware, shadow ML, and proposed scoring config inputs under the 7AA.1 runtime gate and 7AA.2 runtime context, then returns an advisory result.

## 2. Scope

The adapter may produce a local deterministic scoring integration result with the deterministic baseline score, optional trend-aware score, optional shadow ML score, optional proposed scoring config score, selected advisory score, score delta, gate status, fallback decision, Phase 4I preservation flag, denied reasons, warnings, and rationale.

## 3. Non-Goals

The adapter does not replace runtime scoring, modify scoring weights, change thresholds, alter severity cutoffs, modify confidence logic, change trend or anomaly runtime behavior, mutate Phase 4I scores, change decisions, change recommendations, change parser output, write databases, call OCI, call Oracle Agent Memory, call semantic recall, call LLMs, call network services, add dashboard controls, add CLI commands, or implement Phase 8 sizing/TCO.

## 4. Scoring Adapter Is Not Runtime Scoring

The scoring adapter is not runtime scoring. It evaluates in-memory inputs and returns an advisory result only. No scoring module is modified, no scoring engine is called, no runtime scoring behavior is changed, and no run_analysis.py integration is added.

## 5. Required Gate Input

The adapter requires a 7AA.1 gate result that is allowed for consideration and scoped to `scoring` before it can select an adaptive advisory score. If the gate is missing, denied, or for another component type, the adapter falls back to deterministic scoring.

## 6. Required Runtime Context Input

The adapter requires a 7AA.2 adaptive runtime context or compatible dictionary. The context must validate with deterministic runtime authority, deterministic fallback, Phase 4I preservation, no runtime influence applied, and no runtime mutation performed.

## 7. Deterministic Score Authority

Deterministic scoring remains authoritative. The result always preserves `deterministic_score_authoritative=true`, even when an adaptive advisory score is selected for consideration.

## 8. Advisory Score Selection

The selected advisory score is not runtime score. When all required gates pass, selection is deterministic: proposed scoring config score first, shadow ML score second, trend-aware score third, and deterministic fallback last.

## 9. Fallback Behavior

Fallback to deterministic is required. If the gate denies consideration, context is missing or invalid, references are missing, or adaptive scores are invalid, the result selects the deterministic score, records denied reasons or warnings, and sets `fallback_to_deterministic=true`.

## 10. Phase 4I Contract Boundary

Phase 4I remains protected. The adapter can carry a Phase 4I reference through validation and rationale, but it does not mutate Phase 4I output or replace Phase 4I scores.

## 11. Runtime Influence Boundary

The result preserves `runtime_score_applied=false`, `runtime_mutation_performed=false`, `runtime_active=false`, and `runtime_influence_granted=false`. The adapter does not grant runtime influence and does not make adaptive scores runtime truth.

## 12. Score Scale Boundary

All score-like values use the 0.0 to 100.0 score scale. Confidence is not score and must not be mixed with score values. Confidence-like values remain on the 0.0 to 1.0 scale in their source layers.

## 13. Relationship to 7AA.1 Runtime Gate

The 7AA.1 runtime gate determines whether scoring may be considered. The adapter consumes the gate result and respects gate denial. It does not override gate decisions.

## 14. Relationship to 7AA.2 Runtime Context

The 7AA.2 runtime context provides the read-only envelope for future adapters. The scoring adapter consumes and validates that context, but it does not mutate the context or apply it to runtime.

## 15. Relationship to Trend-Aware Scoring

Trend-aware scoring remains advisory. The adapter may select a trend-aware score for advisory consideration only when higher-priority advisory sources are absent and the gate allows consideration.

## 16. Relationship to Shadow ML

Shadow ML remains non-authoritative. The adapter may select a shadow ML score for advisory consideration only when a proposed scoring config score is absent and the gate allows consideration.

## 17. Relationship to Future 7AA.4

Future 7AA.4 may implement a controlled recommendation adapter. Recommendation adapters are future work and are not implemented by this scoring adapter.

## 18. Relationship to Future 7AA.5

Future 7AA.5 may implement a controlled parser adapter or backlog gate. Parser adapters are future work and are not implemented by this scoring adapter.

## 19. Relationship to Future 7AA.6

Future 7AA.6 may implement fallback or rollback execution. Phase 7AA.3 records fallback decisions and rollback references only; it does not execute rollback.

## 20. Acceptance Criteria

Phase 7AA.3 is accepted when the controlled scoring integration adapter exists, the scoring integration result model exists, fallback scoring result exists, advisory score selection exists, gate and context validation are used, deterministic scoring remains authoritative, selected advisory score is not runtime score, fallback to deterministic is required, `runtime_score_applied=false`, `runtime_mutation_performed=false`, `runtime_active=false`, no run_analysis.py integration is added, no scoring module is modified, recommendation/parser adapters are future work, and Phase 8 sizing/TCO is not implemented.
