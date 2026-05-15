# Phase 7AZ Historical Review Lifecycle

## 1. Purpose

Phase 7AZ defines the lifecycle boundary that future Screen 4 historical review workflows must follow before any governed Screen 4 write behavior can be implemented.

This lifecycle is documentation-only. No lifecycle stage is implemented in 7AZ.

## 2. Lifecycle Overview

Future Screen 4 historical review workflows must move through controlled lifecycle stages:

1. Read-only historical review stage
2. Review target selection stage
3. Actor identification stage
4. Historical review decision stage
5. Baseline selection stage
6. Trend / anomaly review stage
7. Governance routing stage
8. Learning candidate intent stage
9. Governed write-path stage
10. Audit trail stage
11. Output artifact stage
12. Closure stage

No lifecycle stage is implemented in 7AZ. The lifecycle defines required boundaries before future Screen 4 historical review workflows can exist.

## 3. Read-Only Historical Review Stage

The lifecycle begins with the existing read-only historical review stage. Screen 4 displays historical evidence, comparison context, baseline context, trend summaries, trend metrics, anomaly groups, anomaly events, distributions, similar cases, recurrence patterns, historical confidence, missing historical evidence, and trend-aware scoring references for exploration.

Read-only historical review is not baseline selection state, not trend review state, not anomaly review state, not governance state, not learning candidate intent state, not backend truth mutation, and not runtime mutation. It cannot create records, write records, execute analysis, change historical truth, recalculate trends, reclassify anomalies, change score, change recommendation truth, modify Phase 4I, or bypass runtime gates.

## 4. Review Target Selection Stage

Future review target selection may identify a supported target type such as `historical_baseline`, `comparison_baseline`, `trend_summary`, `trend_metric`, `anomaly_group`, `anomaly_event`, `distribution_view`, `similar_case`, `recurrence_pattern`, `historical_confidence`, `missing_historical_evidence`, `trend_aware_scoring_reference`, or `learning_candidate_intent`.

Target selection is not mutation. It does not create baseline selection records, trend review records, anomaly review records, governance records, candidate intents, learning candidates, output artifacts, or runtime changes.

Phase 7AZ does not implement target selection.

## 5. Actor Identification Stage

Future workflows cannot skip actor.

Before any future Screen 4 workflow action can be accepted, a human actor identity from Phase 7AE must be present. Browser state, URL hash state, selected historical state, dashboard local state, semantic context, learning metadata, or anonymous metadata cannot replace actor identity.

Phase 7AZ does not implement actor identification.

## 6. Historical Review Decision Stage

Future historical review decision may record proposed, under review, approved, disputed, insufficient evidence, false positive, routed to governance, linked to candidate, or closed workflow state.

Historical review decision is governed workflow state. It is not historical truth mutation, not trend truth mutation, not anomaly truth mutation, not scoring mutation, not recommendation mutation, not runtime mutation, and not Phase 4I mutation.

Phase 7AZ does not implement historical review decisions.

## 7. Baseline Selection Stage

Future baseline selection may select an official comparison baseline or comparison baseline candidate after actor, target validation, action validation, governed write-path, and audit requirements are satisfied.

Baseline selection is not mutation. Selecting an official baseline creates governed review state later. It does not rewrite historical evidence, recalculate trends, reclassify anomalies, change score, change confidence, change recommendations, change parser output, change runtime behavior, or mutate Phase 4I.

Phase 7AZ does not implement baseline selection.

## 8. Trend / Anomaly Review Stage

Future trend review may approve a trend, dispute a trend, mark a trend insufficient evidence, request trend-aware scoring review, request scoring threshold review, add reviewer notes, or route trend context to governance.

Trend review is not scoring mutation. It does not directly change trend interpretation, trend-aware scoring, deterministic score, confidence, recommendation truth, runtime behavior, or Phase 4I.

Future anomaly review may approve an anomaly, mark an anomaly false positive, mark an anomaly insufficient evidence, request anomaly sensitivity review, add reviewer notes, or route anomaly context to governance.

Anomaly review is not anomaly logic mutation. It does not directly change anomaly interpretation, anomaly detection, anomaly sensitivity, deterministic score, recommendation truth, runtime behavior, or Phase 4I.

Phase 7AZ does not implement trend review or anomaly review.

## 9. Governance Routing Stage

Future governance routing may route historical findings, disputed trends, false positive anomaly claims, insufficient historical evidence, baseline concerns, scoring review requests, anomaly sensitivity review requests, scoring threshold review requests, or recurring trend/anomaly patterns to governance.

Governance routing is governed review state. It is not runtime mutation, not candidate creation, not materialization, and not Phase 4I mutation.

Phase 7AZ does not implement governance routing.

## 10. Learning Candidate Intent Stage

Future learning candidate intent may request that recurring trend/anomaly behavior be considered for later learning candidate creation.

Learning candidate intent is not candidate creation. A learning candidate intent is not a learning candidate, not approval, not materialization, and not runtime activation. Candidate creation, candidate governance, materialization, and runtime integration remain separate governed phases.

Phase 7AZ does not implement learning candidate intents and creates no learning candidates.

## 11. Governed Write-Path Stage

Future workflows cannot bypass governed write path.

Any future non-read-only Screen 4 workflow action must enter the Phase 7AG governed write-path framework before baseline selection state, trend review state, anomaly review state, governance routing state, learning candidate intent state, reviewer note state, or closure state can be created.

Future workflows cannot skip validation. Validation must prove that the target type is supported, target reference is present, actor identity is present, action type is supported, requested status transition is legal, audit fields are available, governed write-path requirements are satisfied, historical truth is protected, trend/anomaly truth is protected, scoring truth is protected, recommendation truth is protected, Phase 4I is protected, and failure behavior is safe.

Phase 7AZ does not perform governed writes and does not invoke the write path.

## 12. Audit Trail Stage

Future workflows cannot skip audit.

The audit trail must identify actor, target type, target reference, workflow action, requested status, validation result, governed write-path result, governance routing result when applicable, candidate intent reference when applicable, review note when applicable, historical payload reference, and closure state.

Baseline notes, trend notes, anomaly notes, missing evidence notes, governance routing notes, and learning candidate requests are audit records and require actor/audit.

Phase 7AZ does not create audit records.

## 13. Output Artifact Stage

Future historical review outputs must use the Phase 7AH output artifact lifecycle.

Output artifacts may later include governed historical review packets, baseline review packets, trend review packets, anomaly review packets, governance packets, or candidate-intent packets. Output artifact handling cannot skip validation, cannot skip audit, cannot bypass governed write path, cannot regenerate dashboards as a side effect of a review click, and cannot mutate runtime truth.

Phase 7AZ does not create output artifacts.

## 14. Closure Stage

Closure records the final state of a future Screen 4 workflow action, such as rejected before validation, rejected by governed write-path validation, proposed, under review, approved, disputed, insufficient evidence, false positive, routed to governance, linked to candidate, or closed.

Closure state is governed review state. Closure state is not runtime trend/anomaly state.

Phase 7AZ does not implement closure.

## 15. Forbidden Shortcuts

Forbidden shortcuts include skipping actor, skipping validation, skipping audit, bypassing governed write path, creating baseline selection records directly from a dashboard click, creating trend/anomaly review records directly from a dashboard click, treating baseline selection as historical truth mutation, treating trend review as scoring mutation, treating anomaly review as anomaly logic mutation, treating learning candidate intent as candidate creation, directly mutating historical truth, directly mutating trend/anomaly truth, directly mutating scoring, directly mutating recommendation truth, mutating parser output from workflow state, mutating Phase 4I from workflow state, creating learning candidates without governance, calling `run_analysis.py`, executing backend code, adding Screen 4 workflow UI, and implementing Phase 8 sizing/TCO inside Phase 7AZ.

Future workflows cannot skip actor. Future workflows cannot skip validation. Future workflows cannot skip audit. Future workflows cannot bypass governed write path.

## 16. Required Validation Evidence

Future validation evidence must include supported target type validation, target reference validation, actor presence validation, workflow action validation, status transition validation, governed write-path validation, audit field validation, historical truth protection validation, trend truth protection validation, anomaly truth protection validation, scoring truth protection validation, recommendation truth protection validation, Phase 4I contract protection validation, parser/scoring/decision/recommendation runtime isolation validation, learning candidate intent separation validation, output artifact lifecycle validation, safe failure validation, and forbidden shortcut rejection.

Future workflows cannot skip validation.

## 17. Acceptance Criteria

Phase 7AZ lifecycle acceptance requires this lifecycle document, explicit stage boundaries, forbidden shortcut language, required validation evidence, and tests proving the lifecycle remains boundary-only.

Acceptance also requires these guarantees: no lifecycle stage is implemented in 7AZ, baseline selection is not mutation, trend review is not scoring mutation, anomaly review is not anomaly logic mutation, learning candidate intent is not candidate creation, future workflows cannot skip actor, future workflows cannot skip validation, future workflows cannot skip audit, future workflows cannot bypass governed write path, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
