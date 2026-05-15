# Phase 7BF Recommendation Decision Object Model

## 1. Purpose

Phase 7BF defines local, deterministic object models for future Screen 5 recommendation decisions in the Agentic AI AWR Advisor project.

Recommendation decisions are governed workflow state only. They do not directly change deterministic recommendation truth.

## 2. Scope

The scope is local recommendation decision metadata, request metadata, validation metadata, decision status metadata, actor/audit linkage, recommendation reference metadata, decision rationale metadata, serialization/deserialization helpers, validation helpers, documentation, and tests.

Phase 7BF defines the model that future UI and persistence phases may use after governed workflow gates exist. It does not create a workflow surface and does not write records.

## 3. Non-Goals

Phase 7BF adds no Screen 5 UI, buttons, forms, backend calls, CLI commands, persistence, database schema, governed write-path invocation, action records, outcome records, feedback records, learning candidates, recommendation runtime calls, Phase 4I mutation, recommendation truth changes, recommendation ranking changes, recommendation wording changes, recommendation evidence mapping changes, recommendation action sequencing changes, scoring changes, decision changes, parser behavior changes, dashboard behavior changes, CLI behavior changes, 7BG behavior, 7BH behavior, 7BI behavior, 7BJ certification, or Phase 8 sizing/TCO.

Action/outcome/feedback records are future phases.

## 4. RecommendationDecisionRecord

`RecommendationDecisionRecord` is a governed decision record shape for a Screen 5 recommendation. It is local metadata only in Phase 7BF.

The record fields are `decision_id`, `recommendation_id`, `run_id`, `awr_id`, `domain`, `recommendation_title`, `decision_type`, `decision_status`, `actor_id`, `actor_audit_context`, `decision_rationale`, `decision_notes`, `linked_action_id`, `linked_outcome_id`, `linked_feedback_id`, `linked_candidate_intent_id`, `requires_followup`, `followup_type`, `write_performed`, `runtime_influence`, `phase4i_mutation_requested`, `created_at`, and `notes`.

Validation requires `decision_id`, `recommendation_id`, supported `decision_type`, supported `decision_status`, `actor_id`, supported `followup_type`, boolean `requires_followup`, `write_performed=false in 7BF`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 5. RecommendationDecisionRequest

`RecommendationDecisionRequest` is a future request object for recommendation decision workflows. It is not execution and not persistence.

The request fields are `request_id`, `recommendation_id`, `requested_decision`, `actor_id`, `actor_audit_context`, `payload`, `validation_status`, `can_route_to_write_path`, `write_performed`, `runtime_influence`, `phase4i_mutation_requested`, and `notes`.

Validation requires `request_id`, `recommendation_id`, supported `requested_decision`, `actor_id` for non-read-only decisions, mapping `payload`, `write_performed=false in 7BF`, `runtime_influence=false`, and `phase4i_mutation_requested=false`. `can_route_to_write_path` is future eligibility metadata only, not execution.

## 6. RecommendationDecisionValidation

`RecommendationDecisionValidation` records the local validation result for a decision request. Decision validation is not persistence.

The validation fields are `validation_id`, `request_id`, `valid`, `validation_status`, `requested_decision`, `actor_present`, `recommendation_present`, `can_route_to_write_path`, `write_performed`, `denied_reasons`, `warnings`, `required_next_steps`, `runtime_influence`, `phase4i_mutation_requested`, and `notes`.

Validation requires `validation_id`, `request_id`, supported `requested_decision`, supported `validation_status`, list-shaped `denied_reasons`, list-shaped `warnings`, list-shaped `required_next_steps`, `write_performed=false in 7BF`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 7. Decision Types

Supported decision types are:

- `accept_recommendation`
- `reject_recommendation`
- `defer_recommendation`
- `mark_not_applicable`
- `request_recommendation_review`
- `request_learning_candidate`

Unsupported decision types are rejected.

## 8. Decision Statuses

Supported decision statuses are:

- `proposed`
- `accepted`
- `rejected`
- `deferred`
- `not_applicable`
- `under_review`
- `routed_to_governance`
- `closed`

Unsupported decision statuses are rejected.

## 9. Follow-Up Types

Supported follow-up types are:

- `none`
- `action_required`
- `outcome_required`
- `feedback_required`
- `recommendation_review_required`
- `learning_candidate_review_required`
- `human_review_required`

Unsupported follow-up types are rejected.

## 10. Decision to Status Mapping

The metadata-only decision to status mapping is:

- `accept_recommendation` maps to `accepted`
- `reject_recommendation` maps to `rejected`
- `defer_recommendation` maps to `deferred`
- `mark_not_applicable` maps to `not_applicable`
- `request_recommendation_review` maps to `under_review`
- `request_learning_candidate` maps to `routed_to_governance`

This mapping does not mutate recommendation truth.

## 11. Follow-Up Rules

The metadata-only follow-up rules are:

- `accept_recommendation` maps to `action_required`
- `reject_recommendation` maps to `feedback_required`
- `defer_recommendation` maps to `human_review_required`
- `mark_not_applicable` maps to `feedback_required`
- `request_recommendation_review` maps to `recommendation_review_required`
- `request_learning_candidate` maps to `learning_candidate_review_required`

Follow-up classification is metadata only. Action/outcome/feedback records are future phases.

## 12. Actor / Audit Requirements

Recommendation decisions require actor identity and audit linkage. `actor_id` is required for valid decision records and valid non-read-only decision requests. `actor_audit_context` may carry Phase 7AE actor/audit metadata for future governed workflows.

Phase 7BF does not authenticate actors, authorize actors, create audit records, or invoke a governed write path.

## 13. Runtime Truth Boundary

Recommendation decisions do not change recommendation truth.

Recommendation decisions do not change recommendation ranking.

Recommendation decisions do not change recommendation text/evidence/action sequencing.

`write_performed=false in 7BF`, `runtime_influence=false`, deterministic runtime remains authoritative, and no local object in this phase can alter parser, scoring, decision, recommendation, dashboard, CLI, or runtime behavior.

## 14. Phase 4I Recommendation Boundary

Phase 4I mutation is forbidden.

Decision records, requests, validation results, decision status mapping, and follow-up classification cannot mutate Phase 4I recommendations, Phase 4I payloads, generated dashboard artifacts, parser output, scoring output, decision output, recommendation output, recommendation text, recommendation evidence, or recommendation ranking.

## 15. Recommendation Engine Boundary

The recommendation engine remains authoritative for deterministic recommendations. Phase 7BF does not call the recommendation runtime, import recommendation runtime modules, update recommendation rules, activate recommendation rules, alter recommendation ranking, rewrite recommendation text, or change recommendation evidence mapping.

Recommendation decisions are workflow metadata, not recommendation engine inputs in this phase.

## 16. Action / Outcome / Feedback Boundary

Action/outcome/feedback records are future phases.

Phase 7BF may classify follow-up needs such as `action_required` or `feedback_required`, but that classification does not create action records, outcome records, feedback records, learning candidates, or candidate intents.

7BG may later handle action assignment/tracking UI. 7BH may later handle outcome capture UI. 7BI may later handle recommendation feedback to learning bridge.

## 17. Relationship to 7BE

Phase 7BE established the Screen 5 recommendation/action/outcome workflow boundary. Phase 7BF uses that boundary to define local decision metadata only.

7BF narrows the first workflow object model to recommendation decisions and keeps all 7BE protections intact: no Screen 5 action UI, no backend write path invocation, no recommendation truth mutation, no Phase 4I mutation, and deterministic runtime remains authoritative.

## 18. Relationship to Future 7BG

Future 7BG may add action assignment and tracking UI. Phase 7BF does not add UI, action assignment controls, action tracking controls, action records, owner assignment records, implementation date records, dashboard JavaScript workflows, or dashboard write controls.

## 19. Relationship to Future 7BH

Future 7BH may add outcome capture UI. Phase 7BF does not add outcome forms, outcome records, effectiveness controls, implementation outcome capture, outcome persistence, or outcome-based scoring changes.

## 20. Relationship to Future 7BI

Future 7BI may bridge recommendation feedback to learning. Phase 7BF does not create feedback records, create learning candidates, create learning candidate intents, create recommendation rule candidates, route governance actions, or activate learning.

## 21. Relationship to Future 7BJ

Future 7BJ may validate and certify the Screen 5 recommendation/action/outcome workflow block. Phase 7BF only adds local model documentation, local deterministic model code, validation tests, and architecture index links.

## 22. Acceptance Criteria

Phase 7BF is accepted when recommendation decision record, request, and validation models exist; supported decision types, statuses, follow-up types, decision-to-status mapping, and follow-up classification exist; deterministic ID helpers exist; serialization/deserialization helpers round trip deterministically; validation rejects writes, runtime influence, Phase 4I mutation, unsupported decisions, unsupported statuses, and unsupported follow-up types; no recommendation decision records are persisted; no action/outcome/feedback records are created; no recommendation truth is changed; no recommendation ranking/text/evidence/action sequencing is changed; no Phase 4I mutation occurs; deterministic runtime remains authoritative; and Phase 8 sizing/TCO is not implemented.
