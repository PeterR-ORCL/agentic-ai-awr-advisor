# Phase 7AZ Screen 4 Historical Review Workflow Boundary

## 1. Purpose

Phase 7AZ defines the architecture boundary for future Screen 4 historical review workflows in the Agentic AI AWR Advisor project.

This phase is boundary-only. It documents how future Screen 4 workflow actions may create governed historical review state without changing historical truth, trend truth, anomaly truth, scoring behavior, recommendation truth, runtime behavior, or the Phase 4I contract.

Screen 4 remains the historical review and proof screen. Historical evidence remains authoritative as deterministic output; review workflow state is separate.

## 2. Scope

The scope is documentation, lifecycle definition, inert local boundary metadata, validation tests, and architecture index updates for future Screen 4 historical review workflow boundaries.

Phase 7AZ defines:

- the Screen 4 historical review workflow boundary
- future workflow target types
- future workflow actions
- future historical review statuses
- actor, governed write-path, audit, and output artifact lifecycle requirements
- why historical review state is separate from historical truth
- why trend and anomaly review do not directly mutate scoring or runtime behavior
- what shortcuts are forbidden before future workflow phases exist

No Screen 4 workflow is implemented in Phase 7AZ.

## 3. Non-Goals

Phase 7AZ adds no Screen 4 workflow UI. No Screen 4 workflow UI is added.

Phase 7AZ adds no select official baseline, trend approval, trend dispute, insufficient evidence, anomaly approval, anomaly false positive, anomaly insufficient evidence, scoring review, sensitivity review, threshold review, learning candidate request, note, or governance routing controls.

Phase 7AZ creates no baseline selection records. No baseline selection records are created.

Phase 7AZ creates no trend/anomaly review records. No trend/anomaly review records are created.

Phase 7AZ creates no learning candidate intents and no learning candidates. No learning candidates are created.

Phase 7AZ invokes no backend write path. No backend write path is invoked.

Phase 7AZ changes no historical truth. No historical truth is changed. No trend/anomaly truth is changed. No scoring behavior is changed. No recommendation truth is changed. No Phase 4I mutation is added.

Phase 7AZ does not call `scripts/run_analysis.py`, wire into backend execution, write database records, write governance records, create learning candidates, create candidate intents, create baseline selection records, create trend review records, create anomaly review records, create audit records, or create output artifacts.

Phase 7AZ does not implement future 7BA baseline selection model, future 7BB trend/anomaly review object model, future 7BC historical review to learning candidate bridge, future 7BD validation/certification, or Phase 8 sizing/TCO.

Phase 8 sizing/TCO is not implemented.

## 4. Why Screen 4 Needs Historical Review Workflow

Screen 4 is the historical review and proof screen. It presents historical evidence, trend visibility, anomaly visibility, baseline and comparison context, distributions, similar cases, recurrence context, and read-only historical exploration.

Future reviewers need governed actions to decide whether a trend is valid, whether a baseline should become official, whether an anomaly is real or a false positive, whether missing trend evidence should limit confidence, whether recurring behavior should request a learning candidate intent, and whether trend/anomaly behavior should route to scoring review.

Those actions are sensitive because they may influence future interpretation, confidence, recommendation review, materialization posture, and before/after comparison posture. Therefore future Screen 4 workflow must first be separated from runtime truth.

## 5. Existing Screen 4 Read-Only Boundary

Existing Screen 4 behavior is read-only historical exploration.

Screen 4 may help a reviewer inspect historical windows, trend summaries, trend metrics, anomaly groups, anomaly events, distribution views, similar cases, recurrence patterns, historical confidence, missing historical evidence, and trend-aware scoring references. That exploration does not create records, write governance state, execute analysis, change baselines, recalculate trends, reclassify anomalies, change score, change recommendation truth, change parser output, or mutate Phase 4I.

Screen 4 historical review remains read-only until workflow phases explicitly add controls.

## 6. Historical Review Is Not Historical Truth Mutation

Historical review is not historical truth mutation.

Future Screen 4 review actions create governed review state, not direct changes to trend/anomaly truth. A future official baseline selection, trend approval, trend dispute, insufficient evidence mark, anomaly approval, anomaly false positive mark, scoring review request, learning candidate request, reviewer note, or governance route is workflow metadata and audit context only until a later governed path explicitly handles it.

No future Screen 4 workflow action may directly mutate historical truth, trend truth, anomaly truth, score, trend-aware scoring, confidence, recommendation truth, parser output, dashboard truth, runtime state, or Phase 4I.

## 7. Baseline Selection Boundary

Baseline selection is governed.

Future baseline selection may identify an official comparison baseline or comparison baseline candidate for a target historical review context. Selecting an official baseline must be validated and audited.

Baseline selection is governed review state. It is not historical truth mutation, not trend recalculation, not anomaly reclassification, not scoring change, not recommendation change, not parser output change, not dashboard truth change, and not Phase 4I mutation.

Phase 7AZ creates no baseline selection records and adds no baseline selection UI.

## 8. Trend Review Boundary

Trend review is governed.

Future trend review may approve a trend, dispute a trend, mark a trend as insufficient evidence, request trend-aware scoring review, request scoring threshold review, add reviewer notes, or route a finding to governance. Those actions create review state and possible future candidate intents. They do not directly change trend interpretation, trend-aware scoring, confidence, score, recommendation truth, runtime behavior, or Phase 4I.

Approving a trend does not prove the scoring engine should change. Disputing a trend does not remove deterministic trend output. Marking insufficient evidence does not rewrite historical evidence.

Phase 7AZ creates no trend review records and changes no trend logic.

## 9. Anomaly Review Boundary

Anomaly review is governed.

Future anomaly review may approve an anomaly, mark an anomaly false positive, mark an anomaly insufficient evidence, request anomaly sensitivity review, add reviewer notes, or route an anomaly group to governance.

Marking anomaly false positive creates review state, not immediate anomaly logic changes. Approving an anomaly does not alter scoring. Marking anomaly insufficient evidence does not delete anomaly output. Anomaly sensitivity changes must route to future governed scoring or materialization paths.

Phase 7AZ creates no anomaly review records and changes no anomaly logic.

## 10. Similar Case / Recurrence Boundary

Similar case and recurrence review is governed context.

Future workflows may review similar cases, recurrence patterns, repeated trend behavior, repeated anomaly behavior, and historical confidence context. Those references may support a future request for governance routing or a learning candidate intent.

Similar cases and recurrence patterns are not historical truth mutation, not scoring mutation, not recommendation mutation, and not candidate creation in Phase 7AZ.

## 11. Missing Historical Evidence Boundary

Missing historical evidence is a review constraint, not runtime mutation.

Future workflows may mark missing historical evidence, insufficient trend evidence, unavailable comparison context, weak distribution coverage, or incomplete recurrence support. Those marks may limit workflow confidence or route to governance later.

Missing historical evidence review does not change historical truth, trend truth, anomaly truth, score, recommendation truth, parser output, runtime state, or Phase 4I.

## 12. Actor Requirement

Future workflow actions require actor identity.

Future workflow actions require actor identity through the Phase 7AE actor/reviewer identity model before any non-read-only Screen 4 workflow action can be accepted. Browser state, URL hash state, selected historical state, dashboard local state, semantic context, learning metadata, or anonymous metadata cannot stand in for a human actor.

Future workflow actions require actor identity.

Phase 7AZ does not implement actor identity and does not wire actor identity into Screen 4.

## 13. Governed Write-Path Requirement

Future workflow actions require governed write path.

Any future non-read-only Screen 4 historical review workflow action must use the Phase 7AG governed write-path framework. The future write path must validate request shape, actor identity, authorization posture, target reference, action type, status transition, audit fields, baseline/trend/anomaly truth protection, Phase 4I protection, failure behavior, and closure state before review state can be created.

Future workflow actions require governed write path.

Phase 7AZ does not implement a governed write path and does not invoke one.

## 14. Audit Requirement

Future workflow actions require audit trail.

Future audit records must identify the actor, target type, target reference, workflow action, requested status transition, source historical payload reference, validation result, authorization result, governed write-path result, timestamp or sequence marker supplied by the future audit layer, notes when present, routed governance references when present, candidate intent references when present, and closure state.

Reviewer notes, baseline notes, trend notes, anomaly notes, governance routing notes, and learning candidate requests are audit records. Future notes require actor/audit.

Future workflow actions require audit trail.

Phase 7AZ does not create audit records.

## 15. Output Artifact Lifecycle Requirement

Future Screen 4 historical review outputs must use 7AH output artifact lifecycle.

Any future historical review output, export, refreshed artifact, governance packet, baseline review packet, trend review packet, anomaly review packet, or candidate-intent packet must follow the Phase 7AH output artifact lifecycle. Output lifecycle requirements do not permit runtime mutation and do not allow dashboard regeneration from an uncontrolled workflow action.

Phase 7AZ creates no output artifacts and writes no generated dashboard HTML.

## 16. Trend-Aware Scoring Review Boundary

Trend-aware scoring changes are separate.

Future requests for trend-aware scoring review, anomaly sensitivity review, or scoring threshold review route to scoring review and materialization paths. They do not mutate runtime, do not apply trend-aware scoring, do not change deterministic scoring, do not change confidence, and do not alter recommendation truth.

Phase 7AZ changes no trend-aware scoring behavior and creates no scoring review records.

## 17. Learning Candidate Boundary

Learning candidate creation is governed.

Recurring trend/anomaly behavior may request a learning candidate intent later. A future request_learning_candidate action may create a candidate intent only after actor, validation, governed write path, and audit requirements are satisfied in a later phase.

A learning candidate intent is not a learning candidate, not approval, not materialization, and not runtime activation. No candidates are created in 7AZ.

Phase 7AZ creates no learning candidate intents and creates no learning candidates.

## 18. Runtime Truth Boundary

Runtime truth remains protected.

Historical review state is governed workflow state. It is not runtime historical truth, not runtime trend truth, not runtime anomaly truth, not runtime score, not runtime confidence, not runtime recommendation truth, not runtime parser output, and not Phase 4I.

Future Screen 4 workflow actions cannot directly mutate runtime. Deterministic runtime remains authoritative.

## 19. Phase 4I Contract Boundary

Phase 4I contract remains protected.

No Screen 4 workflow action can directly change Phase 4I. Phase 7AZ adds no Phase 4I mutation and no Phase 4I contract change.

Any future workflow that proposes a Phase 4I-affecting correction must use a separately versioned, validated, governed backend contract. Workflow state alone cannot update Phase 4I, parser output, scoring output, decision output, recommendation output, historical output, dashboard payload shape, or generated dashboard artifacts.

## 20. Future Workflow Target Types

Future Screen 4 workflow target types are boundary concepts only in Phase 7AZ:

- `historical_baseline`
- `comparison_baseline`
- `trend_summary`
- `trend_metric`
- `anomaly_group`
- `anomaly_event`
- `distribution_view`
- `similar_case`
- `recurrence_pattern`
- `historical_confidence`
- `missing_historical_evidence`
- `trend_aware_scoring_reference`
- `learning_candidate_intent`

These target types are references for future governed review state. They are not mutable runtime artifacts in Phase 7AZ.

## 21. Future Workflow Actions

Future Screen 4 workflow actions are boundary concepts only in Phase 7AZ:

- `select_official_baseline`
- `approve_trend`
- `dispute_trend`
- `mark_trend_insufficient`
- `approve_anomaly`
- `mark_anomaly_false_positive`
- `mark_anomaly_insufficient`
- `request_trend_aware_scoring_review`
- `request_anomaly_sensitivity_review`
- `request_scoring_threshold_review`
- `request_learning_candidate`
- `add_historical_review_note`

All future actions require actor. All future actions require audit. All future actions require governed write path. None directly mutate trend/anomaly/scoring truth. None directly mutate runtime. None directly create candidates.

## 22. Future Workflow Statuses

Future Screen 4 workflow statuses are boundary concepts only in Phase 7AZ:

- `proposed`
- `under_review`
- `approved`
- `disputed`
- `insufficient_evidence`
- `false_positive`
- `routed_to_governance`
- `linked_to_candidate`
- `closed`

Statuses are governed review state. Statuses are not runtime trend/anomaly state.

## 23. Relationship to 7AD-7AI

Phase 7AZ depends on the Screen workflow infrastructure boundary from 7AD-7AI.

Future Screen 4 actions require 7AE actor identity, 7AG governed write-path behavior, 7AH output artifact lifecycle, and 7AI validation/certification posture before any implemented workflow can create state.

Phase 7AZ does not implement 7AD-7AI behavior. It documents that future Screen 4 workflow must use those frameworks.

## 24. Relationship to Future 7BA

Future 7BA may define the historical baseline selection model.

Phase 7AZ does not implement 7BA, create baseline selection records, select official baselines, validate baseline selection requests, add baseline UI, or change historical truth.

## 25. Relationship to Future 7BB

Future 7BB may define trend/anomaly review object models.

Phase 7AZ does not implement 7BB, create trend review records, create anomaly review records, approve or dispute trends, mark anomalies false positive, validate review transitions, or change trend/anomaly logic.

## 26. Relationship to Future 7BC

Future 7BC may define the historical review to learning candidate bridge.

Phase 7AZ does not implement 7BC, create candidate intents, create learning candidates, route recurring trend/anomaly findings to learning, approve candidates, materialize candidates, or activate runtime behavior.

## 27. Relationship to Future 7BD

Future 7BD may define Screen 4 workflow validation, readiness, release certification, and operational documentation.

Phase 7AZ does not implement 7BD. This phase provides only boundary docs, lifecycle docs, inert metadata, and local tests for the boundary.

## 28. Relationship to Phase 8

Phase 8 sizing/TCO is out of scope.

Screen 4 historical review may later support evidence that informs advisory sizing or TCO workflows, but Phase 7AZ does not implement Phase 8 sizing/TCO, EM extract, capacity planning, cost modeling, what-if advisory, or any Phase 8 runtime.

Phase 8 sizing/TCO is not implemented.

## 29. Acceptance Criteria

Phase 7AZ acceptance requires this boundary document, the historical review lifecycle document, inert local boundary metadata, validation tests, and architecture index links.

Acceptance also requires these guarantees: this phase is boundary-only, no Screen 4 workflow UI is added, no baseline selection records are created, no trend/anomaly review records are created, no learning candidates are created, no backend write path is invoked, no historical truth is changed, no trend/anomaly truth is changed, no scoring behavior is changed, no recommendation truth is changed, no Phase 4I mutation is added, future workflow actions require actor identity, future workflow actions require governed write path, future workflow actions require audit trail, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
