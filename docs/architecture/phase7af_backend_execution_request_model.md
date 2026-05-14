# Phase 7AF Backend Execution Request Model

## 1. Purpose

This document defines the request and validation object model for Phase 7AF dashboard backend execution mode metadata.

The model describes future execution intent only. Request validation is not execution.

## 2. DashboardBackendExecutionRequest Object Shape

`DashboardBackendExecutionRequest` has these fields:

- `request_id`: required deterministic string
- `execution_mode`: supported execution mode
- `requested_action`: supported requested action
- `source_mode`: supported source mode
- `actor_id`: optional actor id
- `actor_audit_context`: optional actor audit context dictionary
- `target_screen`: optional string
- `selected_state`: dictionary
- `execution_payload`: dictionary
- `adaptive_runtime_requested`: boolean metadata
- `deterministic_default`: boolean, required to be `true`
- `requires_validation`: boolean, required to be `true`
- `requires_actor`: boolean
- `requires_audit`: boolean
- `created_at`: optional string, defaulting to `None`
- `notes`: optional string

`created_at` does not use the current timestamp.

## 3. DashboardBackendExecutionValidation Object Shape

`DashboardBackendExecutionValidation` has these fields:

- `validation_id`: required deterministic string
- `request_id`: required string
- `valid`: boolean
- `execution_allowed`: boolean meaning valid for future execution consideration
- `execution_performed`: boolean, always `false` in 7AF
- `denied_reasons`: list of strings
- `warnings`: list of strings
- `required_next_steps`: list of strings
- `deterministic_default`: boolean, required to be `true`
- `adaptive_runtime_requested`: boolean metadata
- `backend_execution_mode`: supported execution mode
- `source_mode`: supported source mode
- `requested_action`: supported requested action
- `actor_required`: boolean
- `actor_present`: boolean
- `audit_required`: boolean
- `validation_status`: supported validation status

execution_performed=false in 7AF.

## 4. Execution Modes

Supported execution modes are `static_read_only`, `local_command_generation`, `local_backend_execution`, and `future_api_server_execution`.

No execution mode executes backend actions in Phase 7AF.

## 5. Source Modes

Supported source modes are `none`, `local_staged`, `local_file`, `existing_run`, `object_storage`, and `future_upload`.

Source modes are metadata only in Phase 7AF. No local files are read and no object storage calls occur.

## 6. Requested Actions

Supported requested actions are `read_only_view`, `analyze_selection`, `rerun_analysis`, `build_comparison`, `load_from_object_storage`, `diagnostic_review`, `parser_review`, `recommendation_action`, `outcome_capture`, `governance_review`, `materialization_review`, `model_registry_review`, and `runtime_gate_review`.

Actions are metadata only and do not execute.

## 7. Validation Statuses

Supported validation statuses are:

- `VALID`
- `INVALID`
- `NEEDS_ACTOR`
- `NEEDS_SOURCE_VALIDATION`
- `UNSUPPORTED_MODE`
- `READ_ONLY_ONLY`

Validation status describes request posture only.

## 8. Actor Requirements

Read-only view requests may omit actor metadata. Non-read-only actions require actor metadata through `actor_id` or actor audit context.

Non-read-only actions require actor metadata. Actor metadata does not authorize execution by itself.

## 9. Audit Requirements

Read-only view requests do not require audit metadata in Phase 7AF. Non-read-only actions require future audit metadata before execution consideration.

Phase 7AF records audit requirement metadata only and does not write audit records.

## 10. Deterministic ID Rules

Request ids use normalized execution mode, requested action, source mode, and target screen:

- `DASHBOARD-BACKEND-REQUEST-<MODE>-<ACTION>-<SOURCE>-<SCREEN>`

Validation ids use the normalized request id:

- `DASHBOARD-BACKEND-VALIDATION-<REQUEST_ID>`

Rules:

- no random UUID
- no timestamp
- no DB sequence
- no external service
- stable for same input

## 11. Serialization Rules

Request and validation serialization use dictionaries with deterministic field names. Deserialization validates supported modes, sources, actions, booleans, list fields, deterministic default posture, and execution-performed posture.

Serialization does not write files, write databases, call services, call networks, or mutate runtime state.

## 12. Validation Rules

Request validation requires a request id, supported execution mode, supported requested action, supported source mode, dictionary selected state, dictionary execution payload, deterministic default set to `true`, validation required set to `true`, actor metadata for non-read-only actions, and audit requirement metadata for non-read-only actions.

Object storage source mode requires future source validation. `local_backend_execution` and `future_api_server_execution` are metadata only in 7AF.

Validation result metadata requires a validation id, request id, supported backend execution mode, supported source mode, supported requested action, `execution_performed=false`, `deterministic_default=true`, boolean validity flags, list fields, and supported validation status.

## 13. Non-Goals

Phase 7AF does not execute backend actions, does not call run_analysis.py, does not call parser/scoring/decision/recommendation runtime, does not call object storage, does not call OCI, does not call network services, does not write database records, does not create API routes, does not add dashboard buttons, does not add CLI commands, does not implement source loading, does not implement Screen 3 submit behavior, does not implement governed write paths, does not implement output lifecycle behavior, and does not implement Phase 8 sizing/TCO.

No backend write occurs.

## 14. Acceptance Criteria

Acceptance requires the backend execution mode constants, source mode constants, requested action constants, validation status constants, `DashboardBackendExecutionRequest` object shape, `DashboardBackendExecutionValidation` object shape, deterministic id helpers, request validation helpers, validation result helpers, serialization helpers, documentation, and tests.

Acceptance also requires `execution_performed=false` in 7AF, non-read-only actions require actor metadata, request validation is not execution, no backend write occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
