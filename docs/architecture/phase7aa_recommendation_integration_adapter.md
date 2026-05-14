# Phase 7AA.4 Recommendation Integration Adapter

## 1. Purpose

Phase 7AA.4 defines the controlled recommendation integration adapter for the Agentic AI AWR Advisor project. The adapter evaluates supplied adaptive recommendation candidates under the Phase 7AA.1 runtime gate and Phase 7AA.2 read-only context, then returns an advisory recommendation integration result.

The adapter does not replace runtime recommendations.

## 2. Scope

This phase adds a local deterministic adapter result layer only. It may compare deterministic recommendation output with a proposed rule or recommendation evolution record, but it only produces an advisory result envelope.

## 3. Non-Goals

This phase does not modify recommendation generation, recommendation ranking, recommendation wording used by runtime, evidence mapping used by runtime, parser output, scoring, decisions, dashboard behavior, CLI behavior, or `run_analysis.py`.

Phase 8 sizing/TCO is not implemented.

## 4. Recommendation Adapter Is Not Runtime Recommendation Logic

The adapter is not runtime recommendation logic. It does not call the runtime recommendation engine, does not rewrite Phase 4I recommendations, and does not apply advisory output to any runtime path.

Adapter evaluation is local, in-memory, and deterministic.

## 5. Required Gate Input

A Phase 7AA.1 recommendation gate result is required before an adaptive recommendation can be considered. The gate must be for component type `recommendation` and must allow consideration.

Allowed by the gate means allowed for consideration only, not runtime activation.

## 6. Required Runtime Context Input

A Phase 7AA.2 adaptive runtime context, or compatible dictionary, is required. The context must validate with deterministic authority, fallback, Phase 4I preservation, and no runtime mutation.

## 7. Deterministic Recommendation Authority

Deterministic recommendations remain authoritative. The adapter result always preserves `deterministic_recommendation_authoritative=true`.

## 8. Advisory Recommendation Selection

The adapter may select an advisory recommendation only when the gate allows consideration, the runtime context validates, a deterministic recommendation is present, validation and rollback references exist, and the candidate recommendation is valid.

Selection order is deterministic:

1. Proposed recommendation rule.
2. Recommendation rule evolution.
3. Deterministic recommendation.

The selected advisory recommendation is not runtime recommendation.

## 9. Fallback Behavior

Fallback to deterministic recommendation is required whenever the gate denies consideration, the context is missing, validation or rollback references are missing, or adaptive candidates are invalid.

The result records `fallback_to_deterministic=true` for fallback outcomes.

## 10. Evidence Mapping Requirements

Recommendation integration preserves evidence boundaries through an `evidence_mapping_summary`. An evidence reference is recorded when supplied.

If an adaptive recommendation is considered without an evidence reference, the adapter emits a warning. If the proposed recommendation lacks evidence mapping, the adapter emits a warning. Evidence does not make an advisory recommendation authoritative in Phase 7AA.4.

## 11. Phase 4I Contract Boundary

Phase 4I recommendation output is protected. The adapter records `phase4i_contract_preserved=true` and does not mutate Phase 4I recommendations or contracts.

## 12. Runtime Influence Boundary

The adapter is advisory only:

- `runtime_recommendation_applied=false`
- `runtime_mutation_performed=false`
- `runtime_active=false`
- `runtime_influence_granted=false`

No adaptive recommendation is activated by this phase.

## 13. Relationship to 7AA.1 Runtime Gate

Phase 7AA.1 defines the opt-in gate and denial-first policy. Phase 7AA.4 consumes gate results, but it cannot bypass the gate and cannot activate runtime behavior.

## 14. Relationship to 7AA.2 Runtime Context

Phase 7AA.2 defines the read-only context envelope. Phase 7AA.4 consumes that context to confirm deterministic authority, fallback, and no runtime mutation.

## 15. Relationship to Recommendation Rule Evolution

Recommendation rule evolution records remain proposal-only inputs. They can be summarized as advisory candidates but do not replace deterministic recommendations.

## 16. Relationship to Future 7AA.5

Parser adapter remains future work. Phase 7AA.4 does not implement parser integration or parser backlog gating.

## 17. Relationship to Future 7AA.6

Fallback and rollback execution remain future work. Phase 7AA.4 records rollback references for consideration, but it does not execute rollback.

## 18. Acceptance Criteria

- Controlled recommendation integration adapter exists.
- Recommendation integration result model exists.
- Adapter does not replace runtime recommendations.
- Deterministic recommendations remain authoritative.
- Selected advisory recommendation is not runtime recommendation.
- Fallback to deterministic recommendation is required.
- `runtime_recommendation_applied=false`.
- `runtime_mutation_performed=false`.
- `runtime_active=false`.
- No `run_analysis.py` integration is added.
- No run_analysis.py integration is added.
- No recommendation module is modified.
- No scoring, parser, decision, dashboard, or CLI behavior is changed.
- Phase 8 sizing/TCO is not implemented.
