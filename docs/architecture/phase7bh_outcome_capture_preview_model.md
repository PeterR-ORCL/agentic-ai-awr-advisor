# Phase 7BH Outcome Capture Preview Model

## 1. Purpose

Phase 7BH defines local deterministic preview metadata for the Screen 5 outcome capture panel.

The preview model supports disabled dashboard presentation only. No backend write occurs.

## 2. OutcomeCapturePreview Shape

`OutcomeCapturePreview` describes future outcome capture metadata before outcome records exist.

Fields are `outcome_preview_id`, `recommendation_id`, `linked_action_id`, `outcome_status`, `outcome_effectiveness`, `issue_recurred`, `followup_awr`, `followup_run`, `implementation_date`, `outcome_notes`, `actor_id`, `actor_audit_context`, `write_performed`, `outcome_created`, `feedback_created`, `label_created`, `candidate_created`, `scoring_mutation_requested`, `runtime_influence`, `phase4i_mutation_requested`, and `notes`.

Required safety defaults are `write_performed=false`, `outcome_created=false`, `feedback_created=false`, `label_created=false`, `candidate_created=false`, `scoring_mutation_requested=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 3. OutcomeCaptureValidation Shape

`OutcomeCaptureValidation` describes local validation metadata for an outcome preview.

Fields are `validation_id`, `outcome_preview_id`, `valid`, `validation_status`, `actor_present`, `recommendation_present`, `action_present`, `write_performed`, `outcome_created`, `feedback_created`, `label_created`, `candidate_created`, `denied_reasons`, `warnings`, and `required_next_steps`.

Validation metadata does not create outcome records, feedback records, labels, candidates, or write-path routes.

## 4. Supported Outcome Statuses

Supported outcome statuses are:

- `pending`
- `improved`
- `worsened`
- `no_change`
- `issue_recurred`
- `inconclusive`
- `closed`

All statuses are preview/status metadata only in Phase 7BH. No outcome status is persisted.

## 5. Supported Outcome Effectiveness Values

Supported outcome effectiveness values are:

- `effective`
- `ineffective`
- `partially_effective`
- `not_applicable`
- `unknown`

All effectiveness values are preview metadata only in Phase 7BH.

## 6. Validation Rules

Validation requires deterministic preview identifiers, supported outcome status, supported outcome effectiveness, mapping actor audit context when present, boolean safety flags, string-list validation fields, and required false safety flags.

Validation rejects `write_performed=true`, `outcome_created=true`, `feedback_created=true`, `label_created=true`, `candidate_created=true`, `scoring_mutation_requested=true`, `runtime_influence=true`, `phase4i_mutation_requested=true`, unsupported outcome status, and unsupported outcome effectiveness.

Missing actor, missing recommendation, and missing action produce validation metadata for future workflow gating; they do not write records.

## 7. Serialization Rules

Preview records and validation records serialize to plain dictionaries and deserialize back to equivalent local metadata.

Serialization is deterministic, uses no random UUID, no timestamp, no database sequence, and no external service.

## 8. Runtime Safety Rules

`write_performed=false`, `outcome_created=false`, `feedback_created=false`, `label_created=false`, `candidate_created=false`, `scoring_mutation_requested=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false` are mandatory in Phase 7BH.

No backend write occurs. No governed write path is invoked. No outcome record is persisted. No feedback is created. No learning label is created. No candidate is created automatically. No scoring is changed. No recommendation truth is changed. Deterministic runtime remains authoritative.

## 9. Non-Goals

Phase 7BH does not persist outcome records, update action records, create feedback, create labels, create candidates, invoke governed write path, call backend APIs, change recommendation truth, change recommendation ranking, change recommendation evidence, change recommendation text, change scoring, mutate Phase 4I, modify parser/scoring/decision/recommendation behavior, add CLI commands, implement feedback-to-learning bridge, or implement Phase 8 sizing/TCO.

## 10. Acceptance Criteria

The preview model is accepted when supported statuses and effectiveness values are defined, deterministic IDs are stable, preview validation rejects unsafe write/outcome/feedback/label/candidate/scoring/runtime flags, serialization round trips deterministically, no backend write occurs, no outcome record is persisted, no feedback is created, no learning label is created, no candidate is created automatically, no scoring is changed, no Phase 4I mutation occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
