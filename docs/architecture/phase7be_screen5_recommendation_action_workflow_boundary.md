# Phase 7BE Screen 5 Recommendation Action Workflow Boundary

## 1. Purpose

Phase 7BE defines the architecture boundary for future Screen 5 recommendation decision, action tracking, outcome capture, and feedback-to-learning workflows in the Agentic AI AWR Advisor project.

This phase is boundary-only. It documents how future Screen 5 workflow actions may create governed recommendation/action/outcome state without changing deterministic recommendation truth, recommendation ranking, recommendation evidence mapping, recommendation text, backend runtime truth, or the Phase 4I contract.

Screen 5 deterministic recommendations remain authoritative. Workflow actions do not overwrite recommendations.

## 2. Scope

The scope is documentation, lifecycle definition, optional inert local boundary metadata, validation tests, and architecture index updates for future Screen 5 recommendation/action/outcome workflow boundaries.

Phase 7BE defines:

- the Screen 5 recommendation workflow boundary
- future workflow target types
- future workflow actions
- future recommendation decision, action, outcome, and feedback statuses
- actor, governed write-path, and audit requirements
- why recommendation decision state is separate from deterministic recommendation truth
- why outcome capture is evidence for future learning, not immediate runtime mutation
- what shortcuts are forbidden before future workflow phases exist

No Screen 5 action workflow is implemented in Phase 7BE.

## 3. Non-Goals

Phase 7BE adds no Screen 5 action UI. No Screen 5 action UI is added.

Phase 7BE adds no accept, reject, defer, not-applicable, owner assignment, action item, status tracking, implementation date, outcome capture, effectiveness, feedback, recommendation review, or learning candidate controls.

Phase 7BE creates no recommendation decision records. No recommendation decision records are created.

Phase 7BE creates no action records. No action records are created.

Phase 7BE creates no outcome records. No outcome records are created.

Phase 7BE creates no feedback records. No feedback records are created.

Phase 7BE invokes no backend write path. No backend write path is invoked.

Phase 7BE does not call `scripts/run_analysis.py`, wire into backend execution, write database records, write governance records, create learning candidates, create recommendation rule candidates, create action tracking records, or create outcome records.

Phase 7BE changes no recommendation truth. No recommendation truth is changed. No recommendation ranking is changed. No recommendation evidence mapping is changed. No recommendation text is changed. No recommendation action sequencing is changed. No scoring/decision/parser behavior is changed. No Phase 4I mutation is added.

Phase 7BE does not implement the future 7BF recommendation decision object model, future 7BG action assignment/tracking UI, future 7BH outcome capture UI, future 7BI feedback-to-learning bridge, future 7BJ validation/certification, or Phase 8 sizing/TCO.

Phase 8 sizing/TCO is not implemented.

## 4. Why Screen 5 Needs Recommendation / Action / Outcome Workflow

Screen 5 is the "what to do" screen. It presents deterministic recommendations, recommendation rationale, action context, and read-only recommendation/action exploration that operators use to decide what operational work may follow.

Outcome-based learning requires captured actions and outcomes. The system cannot learn whether a recommendation was useful unless a governed workflow later records whether the recommendation was accepted or rejected, whether action was taken, whether the action improved the issue, whether the issue recurred, whether the recommendation was effective, and whether the recommendation was misleading, not applicable, or incomplete.

Those future records must be governed workflow state. A click must not directly mutate recommendation truth, recommendation ranking, recommendation evidence, Phase 4I output, scoring, parser output, or decisions.

## 5. Existing Screen 5 Recommendation Boundary

Existing Screen 5 behavior provides deterministic recommendation/action visibility and read-only recommendation/action exploration.

Screen 5 may help a reviewer inspect recommendation domains, categories, rationale, supporting evidence, action guidance, and related read-only dashboard selections. That exploration does not create records, write governance state, execute analysis, change recommendation truth, change ranking, change evidence mapping, change recommendation text, change action sequencing, change score, change decision, change parser output, or mutate Phase 4I.

Phase 7BE preserves the existing read-only Screen 5 recommendation boundary.

## 6. Workflow Is Not Recommendation Mutation

Workflow is not recommendation mutation.

Future Screen 5 workflow creates governed recommendation/action/outcome state later, not runtime changes. A future accept, reject, defer, not-applicable mark, owner assignment, action item, status update, implementation date, outcome capture, effectiveness mark, feedback note, recommendation review request, or learning candidate request is workflow metadata and audit context only until a later governed path explicitly handles it.

No future Screen 5 workflow action may directly mutate recommendation truth, recommendation ranking, recommendation evidence mapping, recommendation text, recommendation action sequencing, scoring output, decision output, parser output, dashboard truth, runtime state, or Phase 4I.

## 7. Recommendation Decision Boundary

Recommendation decision is not mutation.

Future recommendation decisions may record that a human actor accepted, rejected, deferred, marked not applicable, placed under review, or closed a recommendation workflow item. That decision state is governed workflow state, not deterministic recommendation truth.

Accepting a recommendation does not prove the recommendation engine was correct. Rejecting a recommendation does not remove it from the deterministic output. Deferring a recommendation does not lower ranking. Marking a recommendation not applicable does not rewrite evidence. Review and closure state do not alter Phase 4I recommendations.

## 8. Action Tracking Boundary

Action tracking is separate from recommendation generation.

Future Screen 5 workflows may assign an owner, create an action item, update action status, and record implementation date. Those actions describe operational follow-through. They do not change the recommendation engine, recommendation ranking, recommendation evidence, recommendation text, score, decision, parser output, runtime state, or Phase 4I.

Phase 7BE does not create action tracking records, action assignment records, action status records, implementation date records, action UI, dashboard write controls, backend routes, or CLI commands.

## 9. Outcome Capture Boundary

Outcome capture is evidence for future learning.

Future outcome records may capture whether a recommendation/action improved an issue, worsened it, produced no change, recurred, remained inconclusive, or closed. Outcome capture provides governed evidence for later review and learning workflows. It does not immediately change scoring, recommendation ranking, recommendation text, parser output, decision output, or runtime behavior.

Phase 7BE creates no outcome records and adds no outcome capture UI.

## 10. Feedback Boundary

Feedback is governed workflow state.

Future Screen 5 feedback may explain why a recommendation was useful, misleading, not applicable, incomplete, too risky, too costly, not actionable, or needs rule review. Feedback may create learning candidate intents in future 7BI, but 7BE does not create feedback records, learning candidates, governance records, or recommendation rule candidates.

Feedback-to-learning is future 7BI, not 7BE.

## 11. Actor Requirement

Future workflow actions require actor identity.

Future workflow actions require actor identity through the Phase 7AE actor/reviewer identity model before any non-read-only Screen 5 workflow action can be accepted. Browser state, URL hash state, selected recommendation state, dashboard local state, semantic context, learning metadata, or anonymous metadata cannot stand in for a human actor.

Future workflow actions require actor identity.

Phase 7BE does not implement actor identity and does not wire actor identity into Screen 5.

## 12. Governed Write-Path Requirement

Future workflow actions require governed write path.

Any future non-read-only Screen 5 recommendation/action/outcome workflow action must use the Phase 7AG governed write-path framework. The future write path must validate request shape, actor identity, authorization posture, target reference, action type, status transition, audit fields, recommendation truth protection, Phase 4I protection, failure behavior, and closure state before workflow state can be created.

Future workflow actions require governed write path.

Phase 7BE does not implement a governed write path and does not invoke one.

## 13. Audit Requirement

Future workflow actions require audit trail.

Future audit records must identify the actor, target type, target reference, workflow action, requested status transition, source recommendation payload reference, validation result, authorization result, governed write-path result, timestamp or sequence marker supplied by the future audit layer, notes when present, routed governance references when present, and closure state.

Reviewer feedback and action notes are audit records. Future notes require actor/audit.

Future workflow actions require audit trail.

Phase 7BE does not create audit records.

## 14. Phase 4I Recommendation Contract Boundary

Phase 4I contract is protected.

No Screen 5 action can directly change Phase 4I recommendations. Phase 7BE adds no Phase 4I mutation and no Phase 4I contract change.

Any future workflow that proposes a Phase 4I-affecting correction must use a separately versioned, validated, governed backend contract. Workflow state alone cannot update Phase 4I, parser output, scoring output, decision output, recommendation output, dashboard payload shape, or generated dashboard artifacts.

## 15. Recommendation Rule Evolution Boundary

Recommendation rule evolution is governed.

Future feedback may route to `recommendation_rule_candidate` or recommendation rule evolution review, but it must not mutate recommendation runtime directly. Rule evolution remains proposal-only until a future governed materialization and runtime integration path explicitly validates and activates it.

Phase 7BE creates no recommendation rule candidates, activates no rules, modifies no recommendation engine code, and changes no recommendation runtime behavior.

## 16. Learning Candidate Boundary

Feedback may create learning candidate intents in future 7BI.

A future Screen 5 feedback action may request a learning candidate intent, but an intent is not a learning candidate, not approval, not materialization, and not runtime mutation. Candidate creation, governance, and learning feedback routing remain future work.

Phase 7BE does not create learning candidate intents and does not create learning candidates.

## 17. Future Workflow Target Types

Future Screen 5 workflow target types are boundary concepts only in Phase 7BE:

- `recommendation`
- `recommendation_domain`
- `recommendation_category`
- `recommendation_evidence`
- `recommendation_action`
- `assigned_action`
- `action_status`
- `implementation_date`
- `outcome`
- `feedback`
- `recommendation_effectiveness`
- `recommendation_rule_candidate`
- `learning_candidate_intent`

These target types are references for future governed workflow state. They are not mutable runtime artifacts in Phase 7BE.

## 18. Future Workflow Actions

Future Screen 5 workflow actions are boundary concepts only in Phase 7BE:

- `accept_recommendation`
- `reject_recommendation`
- `defer_recommendation`
- `mark_not_applicable`
- `assign_owner`
- `create_action_item`
- `update_action_status`
- `record_implementation_date`
- `capture_outcome`
- `mark_effective`
- `mark_ineffective`
- `add_feedback`
- `request_recommendation_review`
- `request_learning_candidate`

All future actions require actor. All future actions require audit. All future actions require governed write path. None directly mutate recommendation truth. None directly mutate runtime.

## 19. Future Workflow Statuses

Future recommendation decision statuses are boundary concepts only in Phase 7BE:

- `proposed`
- `accepted`
- `rejected`
- `deferred`
- `not_applicable`
- `under_review`
- `closed`

Future action statuses are boundary concepts only in Phase 7BE:

- `proposed`
- `assigned`
- `in_progress`
- `implemented`
- `blocked`
- `cancelled`
- `closed`

Future outcome statuses are boundary concepts only in Phase 7BE:

- `pending`
- `improved`
- `worsened`
- `no_change`
- `issue_recurred`
- `inconclusive`
- `closed`

Future feedback statuses are boundary concepts only in Phase 7BE:

- `proposed`
- `reviewed`
- `routed_to_learning`
- `closed`

Statuses are governed workflow state. Statuses are not runtime recommendation state.

## 20. Relationship to 7AD-7AI

Phase 7AD-7AI established dashboard workflow infrastructure:

- 7AD defined workflow boundaries.
- 7AE defined actor/reviewer identity metadata.
- 7AF defined backend execution mode metadata.
- 7AG defined governed write-path metadata.
- 7AH defined output artifact lifecycle metadata.
- 7AI validated the workflow infrastructure block.

Phase 7BE depends on those boundaries for future Screen 5 recommendation/action/outcome workflows. It does not replace them and does not activate a workflow.

## 21. Relationship to Future 7BF

Future 7BF may define the recommendation decision object model.

Phase 7BE only defines target types, actions, statuses, and required gates as boundary concepts. It does not create recommendation decision records, schemas, serialization contracts, request models, persistence models, or decision object records.

## 22. Relationship to Future 7BG

Future 7BG may define action assignment/tracking UI.

Phase 7BE adds no Screen 5 action UI, no action assignment UI, no action tracking UI, no forms, no buttons, no dashboard JavaScript workflow, and no dashboard write controls.

## 23. Relationship to Future 7BH

Future 7BH may define outcome capture UI.

Phase 7BE adds no outcome capture UI, no outcome forms, no effectiveness controls, no implementation date controls, and no outcome records.

## 24. Relationship to Future 7BI

Future 7BI may define recommendation feedback to learning bridge.

Phase 7BE does not bridge feedback to learning, does not write feedback records, does not route recommendation feedback, does not create learning candidates, and does not create recommendation rule candidates.

## 25. Relationship to Future 7BJ

Future 7BJ may validate and certify the Screen 5 recommendation/action/outcome workflow block.

Phase 7BE only introduces boundary documentation, lifecycle documentation, architecture index links, inert local metadata when present, and boundary tests for the first subtask in the block. It does not run full readiness checks.

## 26. Relationship to Phase 8

Phase 8 sizing/TCO is not implemented.

Phase 7BE does not add sizing, TCO, what-if advisory, capacity planning, cost modeling, EM Extract implementation, or sizing recommendation workflows. Recommendation/action/outcome workflow in this boundary is governed operational recommendation workflow only, not Phase 8 advisory.

## 27. Acceptance Criteria

Phase 7BE is accepted when Screen 5 recommendation/action workflow boundary documentation exists, Screen 5 action/outcome lifecycle documentation exists, optional inert local boundary metadata is boundary-only when present, boundary validation tests exist, architecture index links exist when the README is updated, future workflow target types are documented, future workflow actions are documented, future workflow statuses are documented, future workflow actions require actor identity, future workflow actions require governed write path, future workflow actions require audit trail, deterministic Screen 5 recommendations remain authoritative, workflow is not recommendation mutation, no Screen 5 action UI is added, no recommendation decision records are created, no action records are created, no outcome records are created, no feedback records are created, no backend write path is invoked, no recommendation truth is changed, no recommendation ranking is changed, no recommendation evidence mapping is changed, no recommendation text is changed, no scoring/decision/parser behavior is changed, no Phase 4I mutation is added, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
