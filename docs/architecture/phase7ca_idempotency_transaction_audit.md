# Phase 7CA Idempotency, Transaction, And Audit

## Purpose

Phase 7CA makes governed workflow persistence retry-safe before Screen 3 backend execution becomes active. It introduces idempotency keys, transaction grouping, audit consistency, failure metadata, rollback references, and output artifact references.

## Idempotency

Every workflow request requires an `idempotency_key`. The database enforces unique idempotency keys in both `AWR_WORKFLOW_TRANSACTION` and `AWR_WORKFLOW_REQUEST`. The repository checks for an existing request before insert and returns the existing request for duplicate replay.

Duplicate replay does not create another workflow request row. It also does not write another audit row or output artifact row through `persist_workflow_bundle`.

## Transaction Grouping

Every workflow request requires a `transaction_group_id`. The transaction group owns the request, validation, audit, failure, and artifact reference metadata for one governed workflow attempt.

The transaction record includes scope, status, rollback reference, timestamps, and notes. The repository updates the transaction status to `COMMITTED` when bundle persistence succeeds and to `FAILED` when failure metadata is recorded.

## Audit Consistency

Audit persistence is required with successful request bundle persistence. The audit row references both `WORKFLOW_REQUEST_ID` and `TRANSACTION_GROUP_ID`, records the actor, records the action, stores an audit summary, and stores a payload hash.

Audit records are metadata. They do not approve runtime activation, change deterministic outputs, or make Screen 3 buttons active.

## Failure Modes

Failures are represented as metadata. `record_workflow_failure` can mark a transaction failed, mark an existing request failed, write a failure audit row, and add an `error_artifact` reference. The error is preserved instead of being swallowed.

If the DB itself is unavailable, DB-backed validation must be reported as blocked or skipped honestly. Tests must not fabricate success or weaken persistence assertions.

## Rollback References

A rollback reference is required for bundle persistence. Phase 7CA records rollback metadata only. It does not execute rollback, restore runtime state, revert Phase 4I, or alter deterministic runtime truth.

## Output Artifact References

Output artifact records reference future artifacts. Supported metadata includes validation responses, analysis run records, Phase 4I payload references, dashboard artifact references, comparison artifacts, error artifacts, source validation artifacts, Object Storage load artifacts, and workflow audit artifacts.

Phase 7CA does not generate dashboards, write generated dashboard HTML, load Object Storage, call `run_analysis.py`, parse AWR files, or create comparison artifacts.

## Runtime Safety

Persistence is not runtime mutation. Persisted workflow state does not mutate parser/scoring/recommendation behavior, does not mutate Phase 4I, does not activate adaptive runtime, and does not implement Phase 8 sizing/TCO.

## Relationship To Future Execution

Future 7CB-7CF phases may consume the persisted metadata to perform active execution under governance. Phase 7CA only creates the durable prerequisite envelope and validates that retries, audit, transaction grouping, and failure recording are available.
