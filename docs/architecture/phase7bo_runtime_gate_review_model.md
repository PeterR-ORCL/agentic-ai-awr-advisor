# Phase 7BO Runtime Gate Review Model

## 1. Purpose

Phase 7BO defines local runtime gate review request/result metadata for the Screen 6 governance control plane.

The model supports disabled / preview-only runtime gate review UI. Request and result objects are local metadata only. They do not transition runtime gate state, persist review records, invoke governed write path, enable adaptive runtime, grant runtime influence, grant runtime eligibility, execute rollback, activate runtime, or mutate Phase 4I.

## 2. RuntimeGateReviewRequest Object Shape

`RuntimeGateReviewRequest` contains:

- `review_request_id`
- `gate_id`
- `gate_type`
- `requested_action`
- `actor_id`
- `actor_audit_context`
- `governance_note`
- `validation_reference`
- `rollback_reference`
- `payload`
- `validation_status`
- `can_route_to_write_path`
- `write_performed`
- `gate_state_changed`
- `adaptive_runtime_enabled_changed`
- `runtime_influence_allowed_changed`
- `runtime_review_requested`
- `rollback_review_requested`
- `runtime_influence_granted`
- `runtime_eligibility_granted`
- `runtime_active`
- `validation_reference_attached`
- `rollback_reference_attached`
- `phase4i_mutation_requested`
- `created_at`
- `notes`

The required safety values are `write_performed=false`, `gate_state_changed=false`, `adaptive_runtime_enabled_changed=false`, `runtime_influence_allowed_changed=false`, `runtime_review_requested=false`, `rollback_review_requested=false`, `runtime_influence_granted=false`, `runtime_eligibility_granted=false`, `runtime_active=false`, `validation_reference_attached=false`, `rollback_reference_attached=false`, and `phase4i_mutation_requested=false`.

## 3. RuntimeGateReviewResult Object Shape

`RuntimeGateReviewResult` contains:

- `review_result_id`
- `review_request_id`
- `gate_id`
- `requested_action`
- `result_status`
- `proposed_next_status`
- `gate_state_changed`
- `adaptive_runtime_enabled_changed`
- `runtime_influence_allowed_changed`
- `runtime_review_requested`
- `rollback_review_requested`
- `runtime_influence_granted`
- `runtime_eligibility_granted`
- `runtime_active`
- `governance_action_performed`
- `validation_reference_attached`
- `rollback_reference_attached`
- `write_performed`
- `denied_reasons`
- `warnings`
- `required_next_steps`
- `phase4i_mutation_requested`
- `notes`

The required safety values are `gate_state_changed=false`, `adaptive_runtime_enabled_changed=false`, `runtime_influence_allowed_changed=false`, `runtime_review_requested=false`, `rollback_review_requested=false`, `runtime_influence_granted=false`, `runtime_eligibility_granted=false`, `runtime_active=false`, `governance_action_performed=false`, `validation_reference_attached=false`, `rollback_reference_attached=false`, `write_performed=false`, and `phase4i_mutation_requested=false`.

## 4. Supported Gate Types

Supported gate types are:

- `adaptive_runtime_gate`
- `adaptive_runtime_context`
- `scoring_integration_result`
- `recommendation_integration_result`
- `parser_integration_result`
- `runtime_fallback_decision`
- `runtime_readiness_record`
- `unknown`

Unsupported gate types are rejected by validation.

## 5. Supported Review Actions

Supported review actions are:

- `mark_gate_under_review`
- `review_adaptive_runtime_context`
- `review_scoring_integration`
- `review_recommendation_integration`
- `review_parser_integration`
- `review_fallback_posture`
- `request_runtime_review`
- `request_rollback_review`
- `request_gate_revision`
- `close_gate_review`
- `add_runtime_gate_note`

Unsupported actions are rejected by validation. Evaluation of an unsupported action returns `unsupported_action` and performs no write, except the reserved future validation-reference action can return `needs_validation_reference` when no validation reference is provided.

## 6. Result Statuses

Supported result statuses are:

- `preview_only`
- `valid_for_future_review`
- `needs_actor`
- `needs_gate`
- `needs_validation_reference`
- `needs_rollback_reference`
- `unsupported_action`
- `write_not_allowed_in_this_phase`
- `blocked_by_runtime_safety`

Statuses describe local preview validation outcome only. They are not runtime gate lifecycle statuses and are not runtime active state.

## 7. Validation Rules

`RuntimeGateReviewRequest` validation requires `review_request_id`, `gate_id`, supported `requested_action`, supported `gate_type`, actor identity for all review actions, and a dictionary payload.

Request validation rejects `write_performed=true`, `gate_state_changed=true`, `adaptive_runtime_enabled_changed=true`, `runtime_influence_allowed_changed=true`, `runtime_review_requested=true`, `rollback_review_requested=true`, `runtime_influence_granted=true`, `runtime_eligibility_granted=true`, `runtime_active=true`, `validation_reference_attached=true`, `rollback_reference_attached=true`, `phase4i_mutation_requested=true`, unsupported gate types, and unsupported actions.

`RuntimeGateReviewResult` validation requires `review_result_id`, `review_request_id`, `gate_id`, supported `requested_action`, and supported `result_status`.

Result validation rejects `gate_state_changed=true`, `adaptive_runtime_enabled_changed=true`, `runtime_influence_allowed_changed=true`, `runtime_review_requested=true`, `rollback_review_requested=true`, `runtime_influence_granted=true`, `runtime_eligibility_granted=true`, `runtime_active=true`, `governance_action_performed=true`, `validation_reference_attached=true`, `rollback_reference_attached=true`, `write_performed=true`, `phase4i_mutation_requested=true`, unsupported actions, and unsupported statuses.

## 8. Serialization Rules

Request and result objects serialize to deterministic dictionaries with explicit safety flags.

Deserialization reconstructs the local metadata objects and re-applies safety validation. Serialization does not persist records, write files, write databases, invoke APIs, invoke CLI commands, route to governed write path, enable adaptive runtime, execute rollback, or activate runtime.

## 9. Deterministic ID Rules

Request IDs use deterministic local inputs:

`SCREEN6-RUNTIME-GATE-REVIEW-REQUEST-<GATE_ID>-<REQUESTED_ACTION>`

Result IDs use deterministic local request IDs:

`SCREEN6-RUNTIME-GATE-REVIEW-RESULT-<REVIEW_REQUEST_ID>`

IDs are local metadata identifiers only. They are not persisted governance records.

## 10. Runtime Safety Rules

Evaluation follows these rules:

- missing actor returns `needs_actor`
- missing gate returns `needs_gate`
- attach validation reference action without `validation_reference` returns `needs_validation_reference`
- rollback review action without `rollback_reference` returns `needs_rollback_reference`
- request runtime review returns `valid_for_future_review` but keeps `runtime_eligibility_granted=false` and `runtime_active=false`
- unsupported action returns `unsupported_action`
- otherwise valid preview metadata returns `valid_for_future_review`
- evaluation never performs write
- evaluation never changes runtime gate state
- evaluation never grants runtime influence
- evaluation never grants runtime eligibility
- evaluation never activates runtime
- evaluation never executes rollback

Deterministic runtime remains authoritative.

## 11. Non-Goals

Phase 7BO does not persist runtime gate review records, change runtime gate state, enable adaptive runtime, set `adaptive_runtime_enabled=true`, set `runtime_influence_allowed=true`, set `runtime_influence_granted=true`, set `runtime_eligibility_granted=true`, set `runtime_active=true`, approve runtime gate for real, request runtime review for real, execute rollback, invoke governed write path, activate runtime, mutate parser/scoring/recommendation/decision behavior, mutate Phase 4I, call `run_analysis.py`, add CLI commands, implement 7BP or later, or implement Phase 8 sizing/TCO.

## 12. Acceptance Criteria

Phase 7BO model acceptance requires local request/result models, supported constants, validation helpers, serialization/deserialization helpers, deterministic ID helpers, evaluation behavior, documentation, and tests.

Acceptance also requires these guarantees: no runtime gate state is changed, adaptive runtime remains disabled, runtime influence is not granted, runtime eligibility is not granted, `runtime_active=false`, no rollback execution occurs, no governed write path is invoked, no parser/scoring/recommendation/decision behavior changes occur, no Phase 4I mutation occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
