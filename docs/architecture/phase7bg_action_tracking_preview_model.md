# Phase 7BG Action Tracking Preview Model

## 1. Purpose

Phase 7BG defines local deterministic preview metadata for the Screen 5 action assignment / tracking panel.

The preview model supports disabled dashboard presentation only. No backend write occurs.

## 2. ActionAssignmentPreview Shape

`ActionAssignmentPreview` describes future action assignment metadata before action records exist.

Fields are `action_preview_id`, `recommendation_id`, `action_title`, `assigned_owner`, `owner_role`, `due_date`, `action_status`, `actor_id`, `actor_audit_context`, `write_performed`, `outcome_created`, `feedback_created`, `runtime_influence`, `phase4i_mutation_requested`, and `notes`.

Required safety defaults are `write_performed=false`, `outcome_created=false`, `feedback_created=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 3. ActionTrackingValidation Shape

`ActionTrackingValidation` describes local validation metadata for an action preview.

Fields are `validation_id`, `action_preview_id`, `valid`, `validation_status`, `actor_present`, `recommendation_present`, `write_performed`, `outcome_created`, `feedback_created`, `denied_reasons`, `warnings`, and `required_next_steps`.

Validation metadata does not create action records and does not route to a write path.

## 4. Supported Action Statuses

Supported action statuses are:

- `proposed`
- `assigned`
- `in_progress`
- `implemented`
- `blocked`
- `cancelled`
- `closed`

All statuses are preview/status metadata only in Phase 7BG. No status update is persisted.

## 5. Validation Rules

Validation requires deterministic preview identifiers, supported action status, mapping actor audit context when present, boolean safety flags, string-list validation fields, and the required false safety flags.

Validation rejects `write_performed=true`, `outcome_created=true`, `feedback_created=true`, `runtime_influence=true`, `phase4i_mutation_requested=true`, and unsupported action status.

Missing actor and missing recommendation produce validation metadata for future workflow gating; they do not write records.

## 6. Serialization Rules

Preview records and validation records serialize to plain dictionaries and deserialize back to equivalent local metadata.

Serialization is deterministic, uses no random UUID, no timestamp, no database sequence, and no external service.

## 7. Runtime Safety Rules

`write_performed=false`, `outcome_created=false`, `feedback_created=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false` are mandatory in Phase 7BG.

No backend write occurs. No governed write path is invoked. No action status is persisted. No outcome is captured. No feedback is created. No recommendation truth is changed. Deterministic runtime remains authoritative.

## 8. Non-Goals

Phase 7BG does not persist action records, update action state, assign real owners, create outcomes, create feedback, invoke governed write path, call backend APIs, change recommendation truth, change recommendation ranking, change recommendation evidence, change recommendation text, mutate Phase 4I, modify parser/scoring/decision/recommendation behavior, add CLI commands, implement outcome capture UI, implement feedback-to-learning bridge, or implement Phase 8 sizing/TCO.

## 9. Acceptance Criteria

The preview model is accepted when supported statuses are defined, deterministic IDs are stable, preview validation rejects unsafe write/runtime flags, serialization round trips deterministically, no backend write occurs, no action record is persisted, no outcome is captured, no feedback is created, no Phase 4I mutation occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
