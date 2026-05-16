# Phase 7BL Learning Candidate Review Model

## 1. Purpose

Phase 7BL defines local learning candidate review request/result metadata for the Screen 6 governance control plane.

The model supports disabled / preview-only candidate review UI. Request and result objects are local metadata only. They do not transition candidate state, persist review records, invoke governed write path, attach materialization references, activate runtime, or mutate Phase 4I.

## 2. LearningCandidateReviewRequest Object Shape

`LearningCandidateReviewRequest` contains:

- `review_request_id`
- `candidate_id`
- `candidate_type`
- `requested_action`
- `actor_id`
- `actor_audit_context`
- `governance_note`
- `materialization_reference`
- `payload`
- `validation_status`
- `can_route_to_write_path`
- `write_performed`
- `candidate_status_changed`
- `materialization_reference_attached`
- `runtime_influence`
- `runtime_activation_requested`
- `phase4i_mutation_requested`
- `created_at`
- `notes`

The required safety values are `write_performed=false`, `candidate_status_changed=false`, `materialization_reference_attached=false`, `runtime_influence=false`, `runtime_activation_requested=false`, and `phase4i_mutation_requested=false`.

## 3. LearningCandidateReviewResult Object Shape

`LearningCandidateReviewResult` contains:

- `review_result_id`
- `review_request_id`
- `candidate_id`
- `requested_action`
- `result_status`
- `candidate_status_changed`
- `proposed_next_status`
- `governance_action_performed`
- `materialization_reference_attached`
- `write_performed`
- `denied_reasons`
- `warnings`
- `required_next_steps`
- `runtime_influence`
- `runtime_activation_requested`
- `phase4i_mutation_requested`
- `notes`

The required safety values are `candidate_status_changed=false`, `governance_action_performed=false`, `materialization_reference_attached=false`, `write_performed=false`, `runtime_influence=false`, `runtime_activation_requested=false`, and `phase4i_mutation_requested=false`.

## 4. Supported Candidate Types

Supported candidate types match the existing learning candidate model:

- `parser_mapping_candidate`
- `recommendation_rule_candidate`
- `scoring_weight_review_candidate`
- `dashboard_wording_candidate`
- `dashboard_interaction_candidate`
- `governance_workflow_candidate`
- `semantic_summary_candidate`
- `documentation_candidate`
- `validation_candidate`

Unsupported candidate types are rejected by validation.

## 5. Supported Review Actions

Supported review actions are:

- `mark_under_review`
- `approve_for_implementation`
- `reject`
- `request_revision`
- `close_candidate`
- `add_governance_note`
- `attach_materialization_reference`

Unsupported actions are rejected by validation. Evaluation of an unsupported action returns `unsupported_action` and performs no write.

## 6. Result Statuses

Supported result statuses are:

- `preview_only`
- `valid_for_future_review`
- `needs_actor`
- `needs_candidate`
- `unsupported_action`
- `write_not_allowed_in_this_phase`
- `blocked_by_runtime_safety`

Statuses describe local preview validation outcome only. They are not candidate lifecycle statuses and are not runtime active state.

## 7. Validation Rules

`LearningCandidateReviewRequest` validation requires `review_request_id`, `candidate_id`, supported `candidate_type`, supported `requested_action`, actor identity for all review actions, and a dictionary payload.

Request validation rejects `write_performed=true`, `candidate_status_changed=true`, `materialization_reference_attached=true`, `runtime_influence=true`, `runtime_activation_requested=true`, `phase4i_mutation_requested=true`, unsupported candidate types, and unsupported actions.

`LearningCandidateReviewResult` validation requires `review_result_id`, `review_request_id`, `candidate_id`, supported `requested_action`, and supported `result_status`.

Result validation rejects `candidate_status_changed=true`, `governance_action_performed=true`, `materialization_reference_attached=true`, `write_performed=true`, `runtime_influence=true`, `runtime_activation_requested=true`, `phase4i_mutation_requested=true`, unsupported actions, and unsupported statuses.

## 8. Serialization Rules

Request and result objects serialize to deterministic dictionaries with explicit safety flags.

Deserialization reconstructs the local metadata objects and re-applies safety validation. Serialization does not persist records, write files, write databases, invoke APIs, invoke CLI commands, or route to governed write path.

## 9. Deterministic ID Rules

Request IDs use deterministic local inputs:

`SCREEN6-CANDIDATE-REVIEW-REQUEST-<CANDIDATE_ID>-<REQUESTED_ACTION>`

Result IDs use deterministic local request IDs:

`SCREEN6-CANDIDATE-REVIEW-RESULT-<REVIEW_REQUEST_ID>`

IDs are local metadata identifiers only. They are not persisted governance records.

## 10. Runtime Safety Rules

Evaluation follows these rules:

- missing actor returns `needs_actor`
- missing candidate returns `needs_candidate`
- unsupported action returns `unsupported_action`
- otherwise valid preview metadata returns `valid_for_future_review`
- evaluation never performs write
- evaluation never changes candidate status
- evaluation never attaches materialization reference
- evaluation never activates runtime

Deterministic runtime remains authoritative.

## 11. Non-Goals

Phase 7BL does not persist candidate review records, change candidate status, approve candidates for real, reject candidates for real, request revision for real, close candidates for real, attach materialization references for real, create materialization artifacts, create learning candidates, invoke governed write path, mutate parser/scoring/decision/recommendation behavior, activate runtime, mutate Phase 4I, call `run_analysis.py`, add CLI commands, implement 7BM or later, or implement Phase 8 sizing/TCO.

## 12. Acceptance Criteria

Phase 7BL model acceptance requires local request/result models, supported constants, validation helpers, serialization/deserialization helpers, deterministic ID helpers, evaluation behavior, documentation, and tests.

Acceptance also requires these guarantees: no candidate status is changed, no governance action is performed, no materialization reference is attached, no runtime activation occurs, no governed write path is invoked, no parser/scoring/decision/recommendation behavior changes occur, no Phase 4I mutation occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
