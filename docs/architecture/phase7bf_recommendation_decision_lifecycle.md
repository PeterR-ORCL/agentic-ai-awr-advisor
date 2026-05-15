# Phase 7BF Recommendation Decision Lifecycle

## 1. Purpose

Phase 7BF defines the lifecycle boundary for future Screen 5 recommendation decision handling before action assignment, outcome capture, feedback routing, persistence, governed write-path invocation, or learning behavior is implemented.

No lifecycle stage writes records in 7BF.

## 2. Lifecycle Overview

Future recommendation decision workflows must move through controlled lifecycle stages:

1. Read-only recommendation stage
2. Recommendation decision request stage
3. Actor identification stage
4. Decision validation stage
5. Follow-up classification stage
6. Future write-path stage
7. Future action / outcome / feedback stage
8. Future learning bridge stage
9. Audit trail stage

No lifecycle stage writes records in 7BF. The lifecycle defines required metadata and validation boundaries only.

## 3. Read-Only Recommendation Stage

The lifecycle begins with the existing read-only Screen 5 recommendation stage. Screen 5 displays deterministic recommendations, recommendation rationale, evidence references, categories, domains, and action guidance for exploration.

Read-only recommendation exploration is not decision state, not persistence, not governed write-path execution, not backend truth mutation, and not runtime mutation.

## 4. Recommendation Decision Request Stage

A future recommendation decision request may express intent to accept a recommendation, reject it, defer it, mark it not applicable, request recommendation review, or request learning candidate review.

The request is metadata only. It does not create a decision record, action record, outcome record, feedback record, learning candidate, recommendation rule candidate, or runtime change.

## 5. Actor Identification Stage

Future workflows cannot skip actor.

A valid recommendation decision requires actor identity. Actor identity must come from the future governed dashboard workflow path and must be auditable. Anonymous browser state, URL hash state, selected card state, semantic context, or local dashboard state cannot replace actor identity.

Phase 7BF validates actor presence as metadata only.

## 6. Decision Validation Stage

Decision validation checks request metadata, recommendation reference presence, actor presence, supported decision type, supported validation status, write flags, runtime influence flags, and Phase 4I mutation flags.

Decision validation is not persistence. A valid validation result means the metadata is eligible for a future governed workflow, not that any record was written.

## 7. Follow-Up Classification Stage

Follow-up classification maps decision type to a metadata-only follow-up type:

- accepted recommendations require future action handling
- rejected and not-applicable recommendations require future feedback handling
- deferred recommendations require future human review
- recommendation review requests require future recommendation review handling
- learning candidate requests require future learning candidate review handling

Follow-up classification is metadata only. It does not create action, outcome, feedback, recommendation review, learning candidate intent, or learning candidate records.

## 8. Future Write-Path Stage

Future workflows cannot skip governed write path.

Any future non-read-only Screen 5 recommendation decision must enter the Phase 7AG governed write-path framework before a decision record can be persisted, routed, linked, audited, or closed. `can_route_to_write_path` in 7BF is eligibility metadata only, not execution.

Phase 7BF does not invoke the governed write path.

## 9. Future Action / Outcome / Feedback Stage

Action, outcome, and feedback handling are future phases.

7BG may later handle action assignment and tracking. 7BH may later handle outcome capture. 7BI may later handle recommendation feedback to learning. Phase 7BF does not create action records, outcome records, feedback records, or UI controls.

## 10. Future Learning Bridge Stage

A future request for learning candidate review may route to a governed learning bridge in 7BI. That route is not automatic candidate creation.

Phase 7BF does not create learning candidates, candidate intents, recommendation rule candidates, governance records, or materialized runtime changes.

## 11. Audit Trail Stage

Future recommendation decision workflows require audit trail. Audit must capture actor, recommendation reference, requested decision, validation result, follow-up classification, governed write-path result, future linked action/outcome/feedback/candidate references when present, and closure state.

Phase 7BF carries actor/audit metadata fields but does not create audit records.

## 12. Forbidden Shortcuts

Forbidden shortcuts include writing records during decision validation, treating validation as persistence, treating follow-up classification as record creation, skipping actor, skipping governed write path, creating decision records directly from a dashboard click, creating action/outcome/feedback records, creating learning candidates, changing recommendation truth, changing recommendation ranking, changing recommendation text, changing recommendation evidence mapping, changing recommendation action sequencing, changing parser behavior, changing scoring behavior, changing decision behavior, changing recommendation runtime behavior, mutating Phase 4I, adding Screen 5 UI, adding CLI behavior, and implementing Phase 8 sizing/TCO.

Decisions cannot mutate recommendation truth.

## 13. Acceptance Criteria

Phase 7BF lifecycle acceptance requires this lifecycle document, explicit stage boundaries, forbidden shortcut language, and tests proving the lifecycle remains local and metadata-only.

Acceptance also requires these guarantees: no lifecycle stage writes records in 7BF, decision validation is not persistence, follow-up classification is metadata only, future workflows cannot skip actor, future workflows cannot skip governed write path, decisions cannot mutate recommendation truth, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
