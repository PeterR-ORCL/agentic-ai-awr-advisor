# Phase 7BN ML Model Registry Review Model

## 1. Purpose

Phase 7BN defines local model registry review request/result metadata for the Screen 6 governance control plane.

The model supports disabled / preview-only model registry review UI. Request and result objects are local metadata only. They do not transition model registry state, persist review records, invoke governed write path, change shadow eligibility, request runtime review for real, grant runtime eligibility, deploy models, activate runtime, or mutate Phase 4I.

## 2. ModelRegistryReviewRequest Object Shape

`ModelRegistryReviewRequest` contains:

- `review_request_id`
- `model_id`
- `model_family`
- `model_version`
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
- `model_status_changed`
- `shadow_eligibility_changed`
- `runtime_review_requested`
- `runtime_eligibility_granted`
- `runtime_active`
- `validation_reference_attached`
- `rollback_reference_attached`
- `runtime_influence`
- `phase4i_mutation_requested`
- `created_at`
- `notes`

The required safety values are `write_performed=false`, `model_status_changed=false`, `shadow_eligibility_changed=false`, `runtime_review_requested=false`, `runtime_eligibility_granted=false`, `runtime_active=false`, `validation_reference_attached=false`, `rollback_reference_attached=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 3. ModelRegistryReviewResult Object Shape

`ModelRegistryReviewResult` contains:

- `review_result_id`
- `review_request_id`
- `model_id`
- `requested_action`
- `result_status`
- `proposed_next_status`
- `model_status_changed`
- `shadow_eligibility_changed`
- `runtime_review_requested`
- `runtime_eligibility_granted`
- `runtime_active`
- `governance_action_performed`
- `validation_reference_attached`
- `rollback_reference_attached`
- `write_performed`
- `denied_reasons`
- `warnings`
- `required_next_steps`
- `runtime_influence`
- `phase4i_mutation_requested`
- `notes`

The required safety values are `model_status_changed=false`, `shadow_eligibility_changed=false`, `runtime_review_requested=false`, `runtime_eligibility_granted=false`, `runtime_active=false`, `governance_action_performed=false`, `validation_reference_attached=false`, `rollback_reference_attached=false`, `write_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 4. Supported Model Families

Supported model families are:

- `tree`
- `neural_net`
- `hybrid_rule_ml`
- `linear`
- `baseline_mock`
- `baseline_majority`
- `baseline_numeric_mean`
- `shadow_placeholder`
- `external_placeholder`
- `unknown`

Unsupported model families are rejected by validation.

## 5. Supported Review Actions

Supported review actions are:

- `mark_under_review`
- `approve_for_shadow`
- `request_runtime_review`
- `reject_model`
- `retire_model`
- `attach_validation_reference`
- `attach_rollback_reference`
- `add_model_governance_note`
- `close_model_review`

Unsupported actions are rejected by validation. Evaluation of an unsupported action returns `unsupported_action` and performs no write.

## 6. Result Statuses

Supported result statuses are:

- `preview_only`
- `valid_for_future_review`
- `needs_actor`
- `needs_model`
- `needs_validation_reference`
- `needs_rollback_reference`
- `unsupported_action`
- `write_not_allowed_in_this_phase`
- `blocked_by_runtime_safety`

Statuses describe local preview validation outcome only. They are not model registry lifecycle statuses and are not runtime active state.

## 7. Validation Rules

`ModelRegistryReviewRequest` validation requires `review_request_id`, `model_id`, supported `requested_action`, supported `model_family`, actor identity for all review actions, and a dictionary payload.

Request validation rejects `write_performed=true`, `model_status_changed=true`, `shadow_eligibility_changed=true`, `runtime_review_requested=true`, `runtime_eligibility_granted=true`, `runtime_active=true`, `validation_reference_attached=true`, `rollback_reference_attached=true`, `runtime_influence=true`, `phase4i_mutation_requested=true`, unsupported model families, and unsupported actions.

`ModelRegistryReviewResult` validation requires `review_result_id`, `review_request_id`, `model_id`, supported `requested_action`, and supported `result_status`.

Result validation rejects `model_status_changed=true`, `shadow_eligibility_changed=true`, `runtime_review_requested=true`, `runtime_eligibility_granted=true`, `runtime_active=true`, `governance_action_performed=true`, `validation_reference_attached=true`, `rollback_reference_attached=true`, `write_performed=true`, `runtime_influence=true`, `phase4i_mutation_requested=true`, unsupported actions, and unsupported statuses.

## 8. Serialization Rules

Request and result objects serialize to deterministic dictionaries with explicit safety flags.

Deserialization reconstructs the local metadata objects and re-applies safety validation. Serialization does not persist records, write files, write databases, invoke APIs, invoke CLI commands, route to governed write path, load model files, save model files, deploy models, or activate runtime.

## 9. Deterministic ID Rules

Request IDs use deterministic local inputs:

`SCREEN6-MODEL-REGISTRY-REVIEW-REQUEST-<MODEL_ID>-<REQUESTED_ACTION>`

Result IDs use deterministic local request IDs:

`SCREEN6-MODEL-REGISTRY-REVIEW-RESULT-<REVIEW_REQUEST_ID>`

IDs are local metadata identifiers only. They are not persisted governance records.

## 10. Runtime Safety Rules

Evaluation follows these rules:

- missing actor returns `needs_actor`
- missing model returns `needs_model`
- attach validation reference without `validation_reference` returns `needs_validation_reference`
- attach rollback reference without `rollback_reference` returns `needs_rollback_reference`
- unsupported action returns `unsupported_action`
- request runtime review returns `valid_for_future_review` but keeps `runtime_eligibility_granted=false` and `runtime_active=false`
- otherwise valid preview metadata returns `valid_for_future_review`
- evaluation never performs write
- evaluation never changes model status
- evaluation never changes shadow eligibility
- evaluation never requests runtime review for real
- evaluation never grants runtime eligibility
- evaluation never activates model
- evaluation never deploys model

Deterministic runtime remains authoritative.

## 11. Non-Goals

Phase 7BN does not persist model registry review records, change model registry status, approve model for shadow for real, request runtime review for real, grant runtime eligibility, set `runtime_eligibility_granted=true`, set `runtime_active=true`, deploy models, load model files, save model files, invoke governed write path, activate runtime, mutate scoring/recommendation/parser/decision behavior, mutate Phase 4I, call `run_analysis.py`, add CLI commands, implement 7BO or later, or implement Phase 8 sizing/TCO.

## 12. Acceptance Criteria

Phase 7BN model acceptance requires local request/result models, supported constants, validation helpers, serialization/deserialization helpers, deterministic ID helpers, evaluation behavior, documentation, and tests.

Acceptance also requires these guarantees: no model status is changed, no shadow eligibility is changed, no runtime review is requested, no runtime eligibility is granted, no model is deployed, no runtime activation occurs, no governed write path is invoked, no scoring/recommendation/parser/decision behavior changes occur, no Phase 4I mutation occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
