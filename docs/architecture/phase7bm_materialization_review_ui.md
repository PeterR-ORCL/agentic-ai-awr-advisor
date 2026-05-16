# Phase 7BM Materialization Review UI

## 1. Purpose

Phase 7BM adds disabled / preview-only Screen 6 materialization review controls for the Agentic AI AWR Advisor project.

The purpose is to make future materialization governance visible without executing materialization review actions. Controls are disabled/preview-only, no materialization status is changed, no validation reference is attached, no rollback reference is attached, no runtime activation is requested, no governed write path is invoked, and deterministic runtime remains authoritative.

## 2. Scope

The scope is a Screen 6 materialization review preview panel, local materialization review request/result models, validation helpers, serialization helpers, documentation, and tests.

The preview panel may show future controls for mark under review, approve for validation, reject materialization, request revision, attach validation reference, attach rollback reference, mark validated, mark implemented, close materialization, and add materialization note.

Phase 7BM does not execute those controls.

## 3. Non-Goals

Phase 7BM adds no active submit behavior, no form POST, no fetch/XMLHttpRequest, no API calls, no CLI commands, no governed write-path invocation, no materialization review record persistence, no materialization status mutation, no real materialization approval, no real materialization rejection, no real revision request, no real validation reference attachment, no real rollback reference attachment, no real implemented mark, no real validated mark, no real materialization closure, no materialization artifact creation, no materialization artifact mutation, no runtime activation, no parser/scoring/decision/recommendation behavior mutation, no Phase 4I mutation, and no Phase 8 sizing/TCO.

No materialization status is changed. No validation reference is attached. No rollback reference is attached. No runtime activation is requested. No governed write path is invoked.

## 4. Materialization Review Is Not Materialization Mutation

Materialization review is not materialization mutation in Phase 7BM.

The preview controls describe future governed actions only. Marking under review, approving for validation, rejecting, requesting revision, attaching validation or rollback references, marking validated, marking implemented, closing materialization, or adding a materialization note requires a future actor-identified, audited, governed write-path workflow before any state can be created.

Phase 7BM does not transition materialization state and does not activate artifacts.

## 5. Materialization Review Request

`MaterializationReviewRequest` is a local metadata object for a future request to review a materialization artifact.

It includes `review_request_id`, `materialization_id`, `materialization_type`, `requested_action`, `actor_id`, `actor_audit_context`, `governance_note`, `validation_reference`, `rollback_reference`, `payload`, `validation_status`, `can_route_to_write_path`, `write_performed`, `materialization_status_changed`, `validation_reference_attached`, `rollback_reference_attached`, `runtime_activation_requested`, `runtime_influence`, `phase4i_mutation_requested`, `created_at`, and `notes`.

The request object is local metadata only. It does not persist review records, route to the governed write path, mutate materialization state, attach references for real, or activate runtime.

## 6. Materialization Review Result

`MaterializationReviewResult` is a local preview object for a materialization review request.

It includes `review_result_id`, `review_request_id`, `materialization_id`, `materialization_type`, `requested_action`, `result_status`, `materialization_status_changed`, `proposed_next_status`, `governance_action_performed`, `validation_reference_attached`, `rollback_reference_attached`, `write_performed`, `denied_reasons`, `warnings`, `required_next_steps`, `runtime_activation_requested`, `runtime_influence`, `phase4i_mutation_requested`, and `notes`.

The result object records preview validation outcome only. It does not perform governance action, attach validation or rollback references, write data, activate runtime, or mutate Phase 4I.

## 7. Preview Controls

The Screen 6 Materialization Review Preview panel shows disabled controls for:

- Mark Under Review
- Approve for Validation
- Reject Materialization
- Request Revision
- Attach Validation Reference
- Attach Rollback Reference
- Mark Validated
- Mark Implemented
- Close Materialization
- Add Materialization Note

The controls are future workflow affordances only. They are visible so reviewers can understand the intended materialization control plane, but they are disabled in Phase 7BM.

## 8. Disabled / Preview-Only Behavior

Controls are disabled/preview-only. They do not submit, fetch, route, post, invoke backend code, call `run_analysis.py`, call a governed write path, create review records, update materialization records, attach validation references, attach rollback references, create artifacts, mutate artifacts, or activate runtime.

The panel renders safety labels: Preview only, Materialization review disabled in this phase, No materialization status changed, No governance action performed, No validation reference attached, No rollback reference attached, No runtime activation requested, No governed write path invoked, No Phase 4I mutation, and Deterministic runtime remains authoritative.

## 9. Validation Reference Boundary

Attach Validation Reference is preview-only in Phase 7BM.

No validation reference is attached. Future validation reference attachment requires actor identity, validation, governed write path, audit trail, and output artifact lifecycle discipline.

## 10. Rollback Reference Boundary

Attach Rollback Reference is preview-only in Phase 7BM.

No rollback reference is attached. Future rollback reference attachment requires actor identity, validation, governed write path, audit trail, and explicit runtime safety separation.

## 11. Runtime Activation Boundary

Materialization review is not runtime activation.

Future materialization review state may inform later governance workflows, but it cannot directly activate parser packages, scoring configs, recommendation rules, ML eligibility, adaptive runtime, or any runtime path.

No runtime activation is requested. Deterministic runtime remains authoritative.

## 12. Phase 4I Boundary

Phase 4I remains protected.

Materialization review preview objects and disabled controls cannot mutate Phase 4I, parser output, scoring output, decision output, recommendation output, dashboard payload shape, or generated dashboard artifacts.

No Phase 4I mutation occurs.

## 13. Relationship to 7BK

Phase 7BK defined the Screen 6 governance control boundary. Phase 7BM implements a preview-only materialization review UI and local model inside that boundary.

7BM does not weaken 7BK. The controls remain disabled/preview-only and do not create governed state.

## 14. Relationship to 7BL

Phase 7BL added preview-only learning candidate review. Phase 7BM extends Screen 6 preview coverage to materialization artifacts.

Candidate review and materialization review remain separate. Candidate review does not create materialization artifacts, and materialization review does not change candidate status.

## 15. Relationship to Future 7BN

Future 7BN may add ML Model Registry Review UI.

Phase 7BM does not review model registry entries, approve models for shadow, deploy models, or grant model runtime eligibility.

## 16. Relationship to Future 7BO

Future 7BO may add Runtime Gate Review UI.

Phase 7BM does not review runtime gates, request runtime activation, change runtime gate state, or activate adaptive runtime.

## 17. Relationship to Future 7BP

Future 7BP may validate and certify the Screen 6 governance workflow block.

Phase 7BM adds only preview UI and local model validation. It does not certify active governance controls because no active controls are implemented.

## 18. Acceptance Criteria

Phase 7BM is accepted when the local materialization review request/result models exist, the Screen 6 Materialization Review Preview panel exists, all materialization review controls are disabled/preview-only, safety labels are rendered, documentation and tests exist, and subphase validation passes.

Acceptance also requires these guarantees: no materialization status is changed, no validation reference is attached, no rollback reference is attached, no runtime activation is requested, no governed write path is invoked, no parser/scoring/decision/recommendation behavior changes occur, no Phase 4I mutation occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
