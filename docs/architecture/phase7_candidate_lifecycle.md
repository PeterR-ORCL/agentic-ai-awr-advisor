# Phase 7 Candidate Lifecycle

## 1. Purpose

This document defines the lifecycle for future Phase 7 learning candidates. A learning candidate is a governed proposal for possible improvement. It is candidate-based, human-reviewed, non-authoritative until approved, and unable to modify runtime behavior by itself.

Phase 7A documents this lifecycle only. It does not implement candidate generation, mining, approval controls, materialization, activation, or runtime learning.

## 2. Candidate Sources

Future candidates may be proposed from structured and auditable sources, including:

- outcome history
- feedback history
- action history
- recommendation history
- parser unknown signal history
- knowledge requests
- knowledge artifacts
- structured recall summaries
- semantic reviewer-assist summaries
- dashboard interaction gaps

Source evidence must be structured and auditable. Semantic reviewer-assist summaries may add context, but they are optional and non-authoritative.

## 3. Candidate Types

Future candidate types include:

- parser_mapping_candidate
- recommendation_rule_candidate
- scoring_weight_review_candidate
- dashboard_wording_candidate
- dashboard_interaction_candidate
- governance_workflow_candidate
- semantic_summary_candidate
- documentation_candidate
- validation_candidate

Each type proposes a reviewable improvement. None of these candidate types directly updates parser logic, scoring logic, recommendation logic, dashboard truth, governance state, or runtime contracts.

## 4. Candidate Object Shape

A future candidate object should include at least:

```json
{
  "candidate_id": "string",
  "candidate_type": "parser_mapping_candidate",
  "title": "string",
  "description": "string",
  "source_evidence": [],
  "structured_sources": [],
  "semantic_context": null,
  "affected_component": "string",
  "affected_domain": "string",
  "confidence": 0.0,
  "rationale": "string",
  "requires_human_review": true,
  "runtime_influence": false,
  "status": "PROPOSED",
  "created_at": "timestamp",
  "created_by": "string",
  "reviewed_by": null,
  "review_notes": null,
  "materialization_reference": null
}
```

The runtime_influence field must remain false until controlled implementation occurs. Candidate approval does not itself modify runtime logic.

## 5. Candidate Statuses

Future candidate statuses are:

- PROPOSED
- UNDER_REVIEW
- APPROVED_FOR_IMPLEMENTATION
- REJECTED
- NEEDS_REVISION
- IMPLEMENTED
- VALIDATED
- CLOSED

Status changes must be auditable and must not trigger automatic runtime mutation.

## 6. Evidence Requirements

Candidate source_evidence must be structured and auditable. Evidence should reference concrete run records, recommendation records, action records, outcome records, feedback records, parser unknown signals, knowledge requests, knowledge artifacts, structured recall summaries, or dashboard interaction observations.

Evidence must identify enough source material for a reviewer to reproduce why the candidate exists. Evidence does not approve anything by itself.

## 7. Confidence and Rationale Requirements

Candidate confidence is advisory and does not approve anything. Confidence may help prioritize review, but it does not change status, runtime logic, parser behavior, scoring, decisions, recommendations, dashboard truth, or governance outcomes.

Candidate rationale must explain why the candidate exists, what source evidence supports it, what component could be affected, and what risk or validation would be required before implementation.

## 8. Human Review Requirements

Every candidate must have requires_human_review=true. Human review is required before a candidate can move beyond PROPOSED or UNDER_REVIEW.

Reviewers must evaluate source evidence, structured sources, optional semantic_context, confidence, rationale, affected component, affected domain, risk, validation needs, and contract implications.

## 9. Approval Requirements

Approval means a human reviewer agrees that a candidate may proceed to controlled implementation. Approval does not itself modify runtime logic.

An APPROVED_FOR_IMPLEMENTATION candidate remains non-runtime-mutating. It must not alter parser logic, scoring logic, decision logic, recommendation logic, dashboard truth, governed memory, semantic memory, or Phase 4I contracts.

## 10. Rejection and Revision Flow

A candidate may move to REJECTED when evidence is insufficient, risk is unacceptable, the proposal conflicts with runtime boundaries, or the proposal is not useful.

A candidate may move to NEEDS_REVISION when the idea may be useful but requires more evidence, narrower scope, clearer rationale, revised affected component, revised candidate type, or stronger validation plan. Revised candidates remain non-authoritative.

## 11. Materialization Flow

Materialization requires a separate implementation step. A candidate may reference an implementation through materialization_reference only after the implementation exists.

Implementation requires tests and validation. Final activation requires preserved runtime contracts, reviewed code or configuration, reproducible validation results, and explicit confirmation that deterministic runtime truth remains authoritative.

## 12. Runtime Activation Boundary

runtime_influence must remain false until a controlled implementation occurs. Candidate status alone must never activate runtime behavior.

Final activation is not a candidate lifecycle side effect. It requires normal engineering controls, code/config review, test execution, validation evidence, and preservation of parser, scoring, decision, recommendation, dashboard, and output contracts.

## 13. Dashboard Interaction Candidate Boundary

A dashboard_interaction_candidate may propose UI interactivity improvements but cannot alter diagnostic truth. It may describe selectable controls, state propagation, evidence exploration, or usability gaps.

Dashboard selection state must remain exploratory/read-only unless a governed write path is explicitly implemented later. Dashboard selections cannot mutate backend truth, parser output, scoring, decisions, recommendations, outcome records, feedback records, learning candidate status, or governance approval state.

## 14. Audit Trail Requirements

Each candidate must have an audit trail that records candidate_id, candidate_type, source_evidence, structured_sources, semantic_context when present, confidence, rationale, status history, reviewer, review notes, decision timestamps, implementation reference, validation reference, and closure reason.

The audit trail must distinguish proposal, review, approval, implementation, validation, activation, rejection, revision, and closure.

## 15. Relationship to Phase 6 Governance

Phase 6 governance remains the controlled boundary for unknown signal review, knowledge requests, artifact review, materialization, and semantic reviewer assistance. Phase 7 candidates may reference Phase 6 governance records as evidence.

Phase 7 candidates do not bypass Phase 6 governance. Human-controlled governance remains authoritative for approvals and materialization workflows.

## 16. Relationship to Semantic Recall

semantic_context is optional and non-authoritative. Semantic recall is reviewer-assist only and must remain marked with runtime_influence=false.

Semantic context can explain why a candidate may be worth reviewing, but it cannot decide candidate status, approve a candidate, reject a candidate, select runtime behavior, classify parser output, determine severity, score an issue, or recommend an action.

## 17. Non-Goals

This lifecycle does not implement candidate storage, candidate generation, outcome mining, semantic candidate explanation, approval controls, materialization logic, runtime activation, dashboard interactivity, or CLI learning commands.

It does not allow automatic parser evolution, automatic scoring evolution, automatic recommendation evolution, automatic dashboard truth changes, automatic candidate approval, automatic materialization, or self-modifying runtime behavior.

## 18. Acceptance Criteria

The candidate lifecycle is accepted for Phase 7A when candidate sources, types, object shape, statuses, evidence requirements, confidence requirements, human review, approval, rejection, revision, materialization, runtime activation, dashboard interaction, audit trail, Phase 6 governance relationship, semantic recall relationship, non-goals, and acceptance criteria are documented.

It is also accepted only if validation confirms that candidates are not implemented as active runtime logic in Phase 7A.
