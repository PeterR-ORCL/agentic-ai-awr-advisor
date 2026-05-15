# Phase 7AQ Diagnostic Review Object Model

## 1. Purpose

Phase 7AQ defines local, deterministic governed review object models for future Screen 2 diagnostic review workflows.

Diagnostic review records describe reviewer assessment. They do not change deterministic diagnosis.

## 2. Scope

The scope is local object modeling, deterministic identifiers, validation helpers, serialization/deserialization helpers, actor linkage metadata, target metadata, review decision metadata, review status metadata, candidate linkage metadata, and tests.

Phase 7AQ creates metadata objects only. It does not persist review records, invoke a governed write path, route to governance, add UI, or mutate runtime truth.

## 3. Non-Goals

Phase 7AQ does not add Screen 2 UI, approval buttons, dashboard buttons, dashboard forms, dashboard write controls, backend calls, CLI commands, database writes, governed write-path invocation, governance records, automatic learning candidates, parser candidates, scoring candidates, recommendation candidates, or Phase 8 sizing/TCO.

Review records do not mutate diagnostic truth. Review records do not change severity/confidence/score. Review records do not change parser output. Review records do not change recommendations. write_performed=false in 7AQ. runtime_influence=false. Phase 4I mutation is forbidden.

## 4. DiagnosticReviewRecord

`DiagnosticReviewRecord` is governed review metadata for a Screen 2 diagnostic target.

It captures review id, Screen 2 id, run and AWR references, target type and target id, domain, current value, review decision, review status, reviewer actor id, actor audit context, reviewer notes, optional candidate and parser/scoring/recommendation linkage ids, runtime influence posture, Phase 4I mutation posture, created-at metadata supplied by callers, and notes.

The record validates that `screen_id` is `screen_2`, the target type is supported, the target id is present, the review decision is supported, the review status is supported, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 5. EvidenceReviewRecord

`EvidenceReviewRecord` is review metadata for one evidence item.

It captures evidence review id, parent diagnostic review id, evidence type, evidence id, evidence name, domain, current value, evidence status, reliability status, missing reason, confidence impact, review decision, reviewer actor id, notes, parser/source/scoring/recommendation review recommendation flags, candidate creation posture, runtime influence posture, and Phase 4I mutation posture.

Evidence review records classify evidence for governance. They do not rewrite evidence values, change scoring, change confidence, change parser output, or change recommendation truth.

## 6. DiagnosticApprovalDecision

`DiagnosticApprovalDecision` is review decision metadata associated with a diagnostic review record.

It captures decision id, review id, decision type, decision status, actor id, actor audit context, decision summary, follow-up metadata, runtime influence posture, Phase 4I mutation posture, created-at metadata supplied by callers, and notes.

The actor id is required. The decision cannot request runtime influence or Phase 4I mutation.

## 7. DiagnosticReviewRequest

`DiagnosticReviewRequest` is request metadata for future Screen 2 workflow handling.

It captures request id, review target type, review target id, requested decision, actor id, actor audit context, payload, validation status, future governance routing eligibility, write posture, runtime influence posture, Phase 4I mutation posture, and notes.

`can_route_to_governance` is future eligibility only, not execution. write_performed=false in 7AQ.

## 8. Review Target Types

Supported target types are `primary_issue`, `secondary_issue`, `severity`, `confidence`, `domain_score`, `evidence_group`, `metric_group`, `wait_event_group`, `sql_signal_group`, `diagnostic_section`, `parser_derived_evidence`, `trend_reference`, `anomaly_reference`, `missing_metric`, `unavailable_evidence`, and `recommendation_context`.

These target types identify review references only. They are not mutable runtime targets.

## 9. Review Decisions

Supported review decisions are `confirm`, `dispute`, `insufficient_evidence`, `needs_parser_review`, `needs_scoring_review`, `needs_recommendation_review`, `needs_learning_candidate`, and `add_reviewer_note`.

Review decisions describe reviewer assessment. They do not directly change diagnosis, score, severity, confidence, parser output, recommendation truth, Phase 4I, or runtime behavior.

## 10. Review Statuses

Supported review statuses are `proposed`, `under_review`, `confirmed`, `disputed`, `insufficient_evidence`, `needs_revision`, `routed_to_governance`, and `closed`.

Statuses are governed review state, not runtime diagnosis state.

## 11. Actor / Audit Requirements

Review records and approval decisions link to actor metadata through actor ids and optional actor audit context mappings.

Future workflow handling must use Phase 7AE actor identity and audit requirements. Phase 7AQ does not implement authentication, authorization, sessions, reviewer assignment, or audit persistence.

## 12. Runtime Truth Boundary

Deterministic runtime remains authoritative.

Review records do not mutate diagnostic truth. Review records do not change severity/confidence/score. Review records do not change parser output. Review records do not change recommendations. Review records do not execute analysis and do not call backend runtime modules.

## 13. Phase 4I Boundary

Phase 4I mutation is forbidden.

All Phase 7AQ records require `phase4i_mutation_requested=false`. A review record can describe reviewer assessment of Phase 4I-derived content, but it cannot modify the Phase 4I payload or contract.

## 14. Parser Review Boundary

Parser review linkage metadata may identify that parser review should happen later.

Phase 7AQ does not change parser behavior, change parser output, create parser mappings, create parser candidates, or route parser review to governance.

## 15. Scoring Review Boundary

Scoring review linkage metadata may identify that scoring review should happen later.

Phase 7AQ does not change scores, severity, confidence, domain scores, scoring rules, trend scoring, anomaly scoring, or adaptive scoring behavior.

## 16. Recommendation Review Boundary

Recommendation review linkage metadata may identify that recommendation review should happen later.

Phase 7AQ does not change recommendations, recommendation ranking, recommendation rationale, action records, outcome records, or recommendation truth.

## 17. Candidate Linkage Boundary

Candidate linkage metadata is a reference field only.

No candidate is created automatically. Missing metric review candidates, parser candidates, scoring review candidates, recommendation review candidates, and learning candidates are future workflow links only until a later governed workflow creates or routes them.

## 18. Relationship to 7AP

Phase 7AP defined the Screen 2 review workflow boundary. Phase 7AQ implements local object models within that boundary.

Phase 7AQ preserves the 7AP guarantees: no Screen 2 UI, no review persistence, no governed write-path invocation, no diagnostic truth mutation, no Phase 4I mutation, and deterministic runtime remains authoritative.

## 19. Relationship to Future 7AR

Future 7AR may bridge Screen 2 review objects to governance.

Phase 7AQ does not implement the governance bridge, route review records, write governance records, or create candidates.

## 20. Relationship to Future 7AS

Future 7AS may add Screen 2 approval UI and review panel behavior.

Phase 7AQ does not add UI, buttons, forms, dashboard JavaScript workflow, disabled preview controls, or dashboard write controls.

## 21. Relationship to Future 7AT

Future 7AT may validate and certify the Screen 2 diagnostic review / approval workflow block.

Phase 7AQ adds object models and local tests only. It does not run final block readiness checks.

## 22. Acceptance Criteria

Phase 7AQ is accepted when diagnostic review records, evidence review records, diagnostic approval decision records, diagnostic review request records, deterministic id helpers, validation helpers, serialization/deserialization helpers, documentation, and tests exist.

Acceptance also requires that review records do not mutate diagnostic truth, review records do not change severity/confidence/score, review records do not change parser output, review records do not change recommendations, write_performed=false in 7AQ, runtime_influence=false, Phase 4I mutation is forbidden, no Screen 2 UI is added, no records are persisted, no candidate is created automatically, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
