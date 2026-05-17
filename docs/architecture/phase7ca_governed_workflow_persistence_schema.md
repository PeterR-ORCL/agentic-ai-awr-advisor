# Phase 7CA Governed Workflow Persistence Schema

## Purpose

Phase 7CA introduces DB persistence for governed workflow metadata. The schema supports active execution prerequisites without running analysis, regenerating dashboards, changing parser/scoring/recommendation behavior, mutating Phase 4I, or implementing Phase 8.

## Schema File

The schema lives in `dbschema/phase7ca_governed_workflow_persistence.sql`. It uses guarded Oracle DDL blocks that check `USER_TABLES` and `USER_INDEXES` before creating tables and indexes, so it is safe to run more than once.

## JSON And CLOB Choice

Workflow payloads and validation lists are stored as CLOBs with `IS JSON` checks where appropriate. This keeps the schema compatible with environments where native JSON type support varies while still constraining JSON-shaped metadata.

## AWR_WORKFLOW_TRANSACTION

`AWR_WORKFLOW_TRANSACTION` stores the transaction envelope. Its primary key is `TRANSACTION_GROUP_ID`. Required columns include `IDEMPOTENCY_KEY`, `TRANSACTION_SCOPE`, `STATUS`, `ROLLBACK_REFERENCE`, `CREATED_AT`, `UPDATED_AT`, and `NOTES`.

The table has `UK_AWR_WF_TX_IDEMP` on `IDEMPOTENCY_KEY` and `CK_AWR_WF_TX_STATUS` for allowed statuses: `PENDING`, `IN_PROGRESS`, `COMMITTED`, `FAILED`, `DUPLICATE_REPLAY`, and `ROLLED_BACK`.

## AWR_WORKFLOW_REQUEST

`AWR_WORKFLOW_REQUEST` stores the workflow request. Its primary key is `WORKFLOW_REQUEST_ID`. Required columns include `TRANSACTION_GROUP_ID`, `IDEMPOTENCY_KEY`, `SOURCE_SCREEN`, `WORKFLOW_TYPE`, `REQUESTED_ACTION`, `ACTOR_ID`, `PAYLOAD_CLOB`, `STATUS`, `CREATED_AT`, `UPDATED_AT`, `ERROR_CLOB`, `WARNING_CLOB`, and `NOTES`.

The table has `UK_AWR_WF_REQ_IDEMP` on `IDEMPOTENCY_KEY`, a foreign key to `AWR_WORKFLOW_TRANSACTION`, a JSON check on `PAYLOAD_CLOB`, and a status check for request lifecycle values.

## AWR_WORKFLOW_VALIDATION

`AWR_WORKFLOW_VALIDATION` stores validation metadata for a request. Its primary key is `WORKFLOW_VALIDATION_ID`. Required columns include `WORKFLOW_REQUEST_ID`, `VALIDATION_STATUS`, `VALID_FLAG`, `DENIED_REASONS_CLOB`, `WARNINGS_CLOB`, `REQUIRED_NEXT_STEPS_CLOB`, `CREATED_AT`, and `NOTES`.

The table has a foreign key to `AWR_WORKFLOW_REQUEST`, a `Y/N` check on `VALID_FLAG`, and JSON checks for denied reasons, warnings, and next steps.

## AWR_WORKFLOW_AUDIT

`AWR_WORKFLOW_AUDIT` stores audit rows. Its primary key is `WORKFLOW_AUDIT_ID`. Required columns include `WORKFLOW_REQUEST_ID`, `TRANSACTION_GROUP_ID`, `ACTOR_ID`, `ACTION`, `AUDIT_SUMMARY`, `PAYLOAD_HASH`, `CREATED_AT`, and `NOTES`.

The table has foreign keys to both request and transaction tables. This enforces that audit records are tied to the workflow request and transaction group they describe.

## AWR_WORKFLOW_OUTPUT_ARTIFACT

`AWR_WORKFLOW_OUTPUT_ARTIFACT` stores output artifact references only. Its primary key is `WORKFLOW_OUTPUT_ID`. Required columns include `WORKFLOW_REQUEST_ID`, `ARTIFACT_TYPE`, `ARTIFACT_REFERENCE`, `ARTIFACT_SUMMARY`, `ARTIFACT_METADATA_CLOB`, `STATUS`, `CREATED_AT`, and `NOTES`.

Allowed artifact types are `validation_response`, `analysis_run_record`, `phase4i_payload_reference`, `dashboard_artifact_reference`, `comparison_artifact`, `error_artifact`, `source_validation_artifact`, `object_storage_load_artifact`, and `workflow_audit_artifact`.

## Indexes

The schema creates lookup indexes for transaction, status, validation, audit, and output artifact access:

- `IX_AWR_WF_REQ_TX`
- `IX_AWR_WF_REQ_STATUS`
- `IX_AWR_WF_VAL_REQ`
- `IX_AWR_WF_AUD_REQ`
- `IX_AWR_WF_AUD_TX`
- `IX_AWR_WF_OUT_REQ`
- `IX_AWR_WF_OUT_TYPE`

## Boundary

The schema stores governed workflow metadata. It does not store generated dashboards, execute `run_analysis.py`, parse AWR files, score workloads, generate recommendations, mutate Phase 4I, activate adaptive runtime behavior, or implement Phase 8.
