# Phase 7BL Learning Candidate Review UI

## 1. Purpose

Phase 7BL adds disabled / preview-only Screen 6 learning candidate review controls for the Agentic AI AWR Advisor project.

The purpose is to make the future candidate governance workflow visible without executing candidate governance actions. Controls are disabled/preview-only, no candidate status is changed, no governance action is performed, no materialization reference is attached, no runtime activation occurs, and deterministic runtime remains authoritative.

## 2. Scope

The scope is a Screen 6 learning candidate review preview panel, local candidate review request/result models, validation helpers, serialization helpers, documentation, and tests.

The preview panel may show future controls for mark under review, approve for implementation, reject, request revision, close candidate, add governance note, and attach materialization reference. It may show read-only request fields and safety labels.

Phase 7BL does not execute those controls.

## 3. Non-Goals

Phase 7BL adds no active submit behavior, no form POST, no fetch/XMLHttpRequest, no API calls, no CLI commands, no governed write-path invocation, no review record persistence, no candidate status mutation, no real candidate approval, no real candidate rejection, no real revision request, no real candidate closure, no real materialization reference attachment, no materialization artifact creation, no learning candidate creation, no runtime activation, no parser/scoring/decision/recommendation behavior mutation, no Phase 4I mutation, and no Phase 8 sizing/TCO.

No candidate status is changed. No governance action is performed. No materialization reference is attached. No runtime activation occurs.

## 4. Learning Candidate Review Is Not Candidate Mutation

Learning candidate review is not candidate mutation in Phase 7BL.

The preview controls describe future governed actions only. Marking under review, approving for implementation, rejecting, requesting revision, closing a candidate, adding a governance note, or attaching a materialization reference requires a future actor-identified, audited, governed write-path workflow before any state can be created.

Phase 7BL does not transition a candidate from proposed to under review, approved, rejected, needs revision, or closed.

## 5. Candidate Review Request

`LearningCandidateReviewRequest` is a local metadata object for a future request to review a learning candidate.

It includes `review_request_id`, `candidate_id`, `candidate_type`, `requested_action`, `actor_id`, `actor_audit_context`, `governance_note`, `materialization_reference`, `payload`, `validation_status`, `can_route_to_write_path`, `write_performed`, `candidate_status_changed`, `materialization_reference_attached`, `runtime_influence`, `runtime_activation_requested`, `phase4i_mutation_requested`, `created_at`, and `notes`.

The request object is local metadata only. It does not persist review records, route to the governed write path, or mutate candidate state.

## 6. Candidate Review Result

`LearningCandidateReviewResult` is a local preview object for a candidate review request.

It includes `review_result_id`, `review_request_id`, `candidate_id`, `requested_action`, `result_status`, `candidate_status_changed`, `proposed_next_status`, `governance_action_performed`, `materialization_reference_attached`, `write_performed`, `denied_reasons`, `warnings`, `required_next_steps`, `runtime_influence`, `runtime_activation_requested`, `phase4i_mutation_requested`, and `notes`.

The result object records preview validation outcome only. It does not perform governance action, attach materialization, write data, activate runtime, or mutate Phase 4I.

## 7. Preview Controls

The Screen 6 Learning Candidate Review Preview panel shows disabled controls for:

- Mark Under Review
- Approve for Implementation
- Reject
- Request Revision
- Close Candidate
- Add Governance Note
- Attach Materialization Reference

The controls are future workflow affordances only. They are visible so reviewers can understand the intended control plane, but they are disabled in Phase 7BL.

## 8. Disabled / Preview-Only Behavior

Controls are disabled/preview-only. They do not submit, fetch, route, post, invoke backend code, call `run_analysis.py`, call a governed write path, create review records, update candidate records, attach materialization references, create artifacts, or activate runtime.

The panel renders safety labels: Preview only, Candidate review disabled in this phase, No candidate status changed, No governance action performed, No materialization reference attached, No runtime activation, No governed write path invoked, No Phase 4I mutation, and Deterministic runtime remains authoritative.

## 9. Runtime Truth Boundary

Candidate review preview state is not runtime truth.

Future candidate review state may inform later governance workflows, but it cannot directly influence parser behavior, scoring behavior, decision behavior, recommendation behavior, ML behavior, adaptive runtime posture, or runtime activation.

Deterministic runtime remains authoritative.

## 10. Materialization Boundary

Attach Materialization Reference is preview-only in Phase 7BL.

No materialization reference is attached. No materialization artifact is created. No materialization status is changed. Future materialization review UI remains Phase 7BM and must follow governed write-path, audit, validation, and output lifecycle requirements.

## 11. Phase 4I Boundary

Phase 4I remains protected.

Candidate review preview objects and disabled controls cannot mutate Phase 4I, parser output, scoring output, decision output, recommendation output, dashboard payload shape, or generated dashboard artifacts.

No Phase 4I mutation occurs.

## 12. Relationship to 7BK

Phase 7BK defined the Screen 6 governance control boundary. Phase 7BL implements the first preview-only UI and local model inside that boundary.

7BL does not weaken 7BK. The controls remain disabled/preview-only and do not create governed state.

## 13. Relationship to Future 7BM

Future 7BM may add Materialization Review UI.

Phase 7BL does not implement materialization review UI, does not attach materialization references for real, and does not create materialization artifacts.

## 14. Relationship to Future 7BN

Future 7BN may add ML Model Registry Review UI.

Phase 7BL does not review model registry entries, approve models for shadow, deploy models, or grant model runtime eligibility.

## 15. Relationship to Future 7BO

Future 7BO may add Runtime Gate Review UI.

Phase 7BL does not review runtime gates, request runtime activation, change runtime gate state, or activate adaptive runtime.

## 16. Relationship to Future 7BP

Future 7BP may validate and certify the Screen 6 governance workflow block.

Phase 7BL adds only preview UI and local model validation. It does not certify active governance controls because no active controls are implemented.

## 17. Acceptance Criteria

Phase 7BL is accepted when the local candidate review request/result models exist, the Screen 6 Learning Candidate Review Preview panel exists, all candidate review controls are disabled/preview-only, safety labels are rendered, documentation and tests exist, and subphase validation passes.

Acceptance also requires these guarantees: no candidate status is changed, no governance action is performed, no materialization reference is attached, no runtime activation occurs, no governed write path is invoked, no parser/scoring/decision/recommendation behavior changes occur, no Phase 4I mutation occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
