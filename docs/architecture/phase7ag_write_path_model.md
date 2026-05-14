# Phase 7AG Write-Path Model

## 1. Purpose

This document defines the object model, validation rules, audit metadata, serialization rules, and deterministic id rules for the Phase 7AG governed write-path framework.

Validation is not execution.

## 2. GovernedWriteRequest Object Shape

`GovernedWriteRequest` has these fields:

- `request_id`: required deterministic string
- `target_type`: supported target type
- `target_id`: required string
- `write_intent`: supported write intent
- `actor_id`: optional actor id
- `actor_audit_context`: optional actor audit context dictionary
- `backend_execution_request`: optional backend execution request dictionary
- `payload`: dictionary
- `dry_run`: boolean, required to be `true`
- `requires_actor`: boolean
- `requires_audit`: boolean, required to be `true`
- `requires_backend_validation`: boolean
- `runtime_mutation_requested`: boolean, required to be `false`
- `phase4i_mutation_requested`: boolean, required to be `false`
- `created_at`: optional string
- `notes`: optional string

## 3. GovernedWriteValidation Object Shape

`GovernedWriteValidation` has these fields:

- `validation_id`: required deterministic string
- `request_id`: required string
- `valid`: boolean
- `validation_status`: supported validation status
- `write_allowed_for_future_handling`: boolean
- `write_performed`: boolean, required to be `false`
- `dry_run`: boolean, required to be `true`
- `actor_required`: boolean
- `actor_present`: boolean
- `audit_required`: boolean
- `backend_validation_required`: boolean
- `backend_validation_present`: boolean
- `runtime_mutation_requested`: boolean, required to be `false`
- `phase4i_mutation_requested`: boolean, required to be `false`
- `denied_reasons`: list of strings
- `warnings`: list of strings
- `required_next_steps`: list of strings

write_performed=false is required.

## 4. GovernedWriteAuditRecord Object Shape

`GovernedWriteAuditRecord` has these fields:

- `audit_id`: required deterministic string
- `request_id`: required string
- `validation_id`: required string
- `actor_id`: optional actor id
- `target_type`: supported target type
- `target_id`: required string
- `write_intent`: supported write intent
- `dry_run`: boolean, required to be `true`
- `write_performed`: boolean, required to be `false`
- `validation_status`: supported validation status
- `audit_summary`: required string
- `runtime_mutation_performed`: boolean, required to be `false`
- `phase4i_mutation_performed`: boolean, required to be `false`
- `created_at`: optional string
- `notes`: optional string

The audit record is not backend write metadata being persisted by Phase 7AG.

## 5. Target Types

Supported target types are `diagnostic_evidence`, `recommendation`, `action`, `outcome`, `parser_unknown`, `learning_candidate`, `materialization_artifact`, `model_registry_entry`, `runtime_gate`, `backend_execution_request`, `source_selection`, `historical_baseline`, `trend_anomaly_review`, and `governance_item`.

## 6. Write Intents

Supported write intents are `read_only`, `review`, `approve`, `reject`, `request_revision`, `defer`, `assign`, `execute`, `capture_outcome`, `create_candidate`, `link_artifact`, `validate`, and `close`.

The `read_only` intent may omit actor metadata. All other intents require actor metadata.

## 7. Validation Statuses

Supported validation statuses are:

- `VALID`
- `INVALID`
- `NEEDS_ACTOR`
- `NEEDS_PERMISSION_SCOPE`
- `NEEDS_TARGET`
- `NEEDS_BACKEND_EXECUTION_MODE`
- `READ_ONLY_ONLY`
- `UNSUPPORTED_ACTION`

VALID means valid for future workflow handling, not that a write occurred.

## 8. Dry-Run Rules

dry_run=true is required. dry_run=false is rejected.

Dry-run validation may produce validation metadata and audit metadata only.

## 9. Actor Rules

Non-read-only actions require actor metadata. Actor metadata may be supplied as actor id or actor audit context.

Actor metadata does not authorize writes by itself.

## 10. Backend Execution Rules

The `execute` intent requires backend execution validation metadata from the Phase 7AF boundary.

Phase 7AG does not execute backend actions.

## 11. Audit Rules

All governed write requests require audit metadata. Audit record generation creates local metadata only.

Audit record is not backend write behavior and does not persist state.

## 12. Serialization Rules

Request, validation, and audit record serialization use deterministic dictionaries with stable field names.

Serialization does not write files, write databases, call services, call networks, or mutate runtime state.

## 13. Deterministic ID Rules

Request ids use normalized target type, target id, and intent:

- `GOVERNED-WRITE-REQUEST-<TARGET_TYPE>-<TARGET_ID>-<INTENT>`

Validation ids use normalized request id:

- `GOVERNED-WRITE-VALIDATION-<REQUEST_ID>`

Audit ids use normalized request id and validation id:

- `GOVERNED-WRITE-AUDIT-<REQUEST_ID>-<VALIDATION_ID>`

Rules:

- no random UUID
- no timestamp
- no DB sequence
- no external service
- stable for same input

## 14. Non-Goals

Phase 7AG does not perform writes, execute backend actions, call run_analysis.py, mutate Phase 4I, mutate parser/scoring/decision/recommendation behavior, mutate dashboard output, write database records, add dashboard buttons, add CLI commands, implement screen workflows, implement output lifecycle behavior, or implement Phase 8 sizing/TCO.

No runtime mutation occurs.

## 15. Acceptance Criteria

Acceptance requires governed write request metadata, governed write validation metadata, governed write audit metadata, supported target types, supported write intents, supported validation statuses, dry-run enforcement, actor requirement validation, backend execution requirement validation, serialization helpers, deterministic id helpers, documentation, and tests.

Acceptance also requires dry_run=true, write_performed=false, validation is not execution, audit record is not backend write, no runtime mutation occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
