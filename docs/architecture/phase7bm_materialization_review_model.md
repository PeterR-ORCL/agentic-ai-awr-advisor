# Phase 7BM Materialization Review Model

## 1. Purpose

Phase 7BM defines local materialization review request/result metadata for the Screen 6 governance control plane.

The model supports disabled / preview-only materialization review UI. Request and result objects are local metadata only. They do not transition materialization state, persist review records, invoke governed write path, attach validation or rollback references, activate runtime, or mutate Phase 4I.

## 2. MaterializationReviewRequest Object Shape

`MaterializationReviewRequest` contains:

- `review_request_id`
- `materialization_id`
- `materialization_type`
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
- `materialization_status_changed`
- `validation_reference_attached`
- `rollback_reference_attached`
- `runtime_activation_requested`
- `runtime_influence`
- `phase4i_mutation_requested`
- `created_at`
- `notes`

The required safety values are `write_performed=false`, `materialization_status_changed=false`, `validation_reference_attached=false`, `rollback_reference_attached=false`, `runtime_activation_requested=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 3. MaterializationReviewResult Object Shape

`MaterializationReviewResult` contains:

- `review_result_id`
- `review_request_id`
- `materialization_id`
- `materialization_type`
- `requested_action`
- `result_status`
- `materialization_status_changed`
- `proposed_next_status`
- `governance_action_performed`
- `validation_reference_attached`
- `rollback_reference_attached`
- `write_performed`
- `denied_reasons`
- `warnings`
- `required_next_steps`
- `runtime_activation_requested`
- `runtime_influence`
- `phase4i_mutation_requested`
- `notes`

The required safety values are `materialization_status_changed=false`, `governance_action_performed=false`, `validation_reference_attached=false`, `rollback_reference_attached=false`, `write_performed=false`, `runtime_activation_requested=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 4. Supported Materialization Types

Supported materialization types are:

- `parser_mapping_artifact`
- `scoring_review_artifact`
- `recommendation_rule_artifact`
- `dashboard_wording_artifact`
- `dashboard_interaction_artifact`
- `governance_workflow_artifact`
- `semantic_summary_artifact`
- `documentation_artifact`
- `validation_artifact`
- `unknown`

Unsupported materialization types are rejected by validation.

## 5. Supported Review Actions

Supported review actions are:

- `mark_under_review`
- `approve_for_validation`
- `reject`
- `request_revision`
- `attach_validation_reference`
- `attach_rollback_reference`
- `mark_validated`
- `mark_implemented`
- `close_materialization`
- `add_materialization_note`

Unsupported actions are rejected by validation. Evaluation of an unsupported action returns `unsupported_action` and performs no write.

## 6. Result Statuses

Supported result statuses are:

- `preview_only`
- `valid_for_future_review`
- `needs_actor`
- `needs_materialization`
- `needs_validation_reference`
- `needs_rollback_reference`
- `unsupported_action`
- `write_not_allowed_in_this_phase`
- `blocked_by_runtime_safety`

Statuses describe local preview validation outcome only. They are not materialization lifecycle statuses and are not runtime active state.

## 7. Validation Rules

`MaterializationReviewRequest` validation requires `review_request_id`, `materialization_id`, supported `materialization_type`, supported `requested_action`, actor identity for all review actions, and a dictionary payload.

Request validation rejects `write_performed=true`, `materialization_status_changed=true`, `validation_reference_attached=true`, `rollback_reference_attached=true`, `runtime_activation_requested=true`, `runtime_influence=true`, `phase4i_mutation_requested=true`, unsupported materialization types, and unsupported actions.

`MaterializationReviewResult` validation requires `review_result_id`, `review_request_id`, `materialization_id`, supported `requested_action`, and supported `result_status`.

Result validation rejects `materialization_status_changed=true`, `governance_action_performed=true`, `validation_reference_attached=true`, `rollback_reference_attached=true`, `write_performed=true`, `runtime_activation_requested=true`, `runtime_influence=true`, `phase4i_mutation_requested=true`, unsupported actions, and unsupported statuses.

## 8. Serialization Rules

Request and result objects serialize to deterministic dictionaries with explicit safety flags.

Deserialization reconstructs the local metadata objects and re-applies safety validation. Serialization does not persist records, write files, write databases, invoke APIs, invoke CLI commands, or route to governed write path.

## 9. Deterministic ID Rules

Request IDs use deterministic local inputs:

`SCREEN6-MATERIALIZATION-REVIEW-REQUEST-<MATERIALIZATION_ID>-<REQUESTED_ACTION>`

Result IDs use deterministic local request IDs:

`SCREEN6-MATERIALIZATION-REVIEW-RESULT-<REVIEW_REQUEST_ID>`

IDs are local metadata identifiers only. They are not persisted governance records.

## 10. Runtime Safety Rules

Evaluation follows these rules:

- missing actor returns `needs_actor`
- missing materialization returns `needs_materialization`
- attach validation reference without `validation_reference` returns `needs_validation_reference`
- attach rollback reference without `rollback_reference` returns `needs_rollback_reference`
- unsupported action returns `unsupported_action`
- otherwise valid preview metadata returns `valid_for_future_review`
- evaluation never performs write
- evaluation never changes materialization status
- evaluation never attaches references for real
- evaluation never activates runtime

Deterministic runtime remains authoritative.

## 11. Non-Goals

Phase 7BM does not persist materialization review records, change materialization status, approve materialization for real, reject materialization for real, request revision for real, attach validation reference for real, attach rollback reference for real, mark implemented for real, mark validated for real, close materialization for real, create materialization artifacts, mutate materialization artifacts, invoke governed write path, activate runtime, mutate parser/scoring/decision/recommendation behavior, mutate Phase 4I, call `run_analysis.py`, add CLI commands, implement 7BN or later, or implement Phase 8 sizing/TCO.

## 12. Acceptance Criteria

Phase 7BM model acceptance requires local request/result models, supported constants, validation helpers, serialization/deserialization helpers, deterministic ID helpers, evaluation behavior, documentation, and tests.

Acceptance also requires these guarantees: no materialization status is changed, no governance action is performed, no validation reference is attached, no rollback reference is attached, no runtime activation is requested, no governed write path is invoked, no parser/scoring/decision/recommendation behavior changes occur, no Phase 4I mutation occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
