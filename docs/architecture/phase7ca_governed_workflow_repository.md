# Phase 7CA Governed Workflow Repository

## Purpose

`src/learning/governed_workflow_repository.py` is the DB-backed persistence adapter for governed workflow metadata. It supports Phase 7CA prerequisites for active backend execution without executing analysis or mutating runtime truth.

## Connection Boundary

The repository requires an injected connection object. It does not create DB connections on import, does not read environment variables, does not load `.env`, and does not import the project ADB connector directly. DB connectivity remains owned by existing project conventions outside the repository.

## Public Records

The repository defines durable metadata records:

- `PersistedWorkflowTransaction`
- `PersistedWorkflowRequest`
- `PersistedWorkflowValidation`
- `PersistedWorkflowAudit`
- `PersistedWorkflowOutputArtifact`
- `AnalysisExecutionRecord`
- `WorkflowPersistenceResult`

These records are workflow metadata only. Persisted records do not imply runtime activation, parser changes, scoring changes, recommendation changes, dashboard regeneration, Phase 4I mutation, or Phase 8 behavior.

## Public Methods

`GovernedWorkflowRepository` exposes:

- `persist_workflow_request`
- `persist_workflow_validation`
- `persist_workflow_audit`
- `persist_output_artifact`
- `get_workflow_request`
- `get_by_idempotency_key`
- `validate_idempotency_key`
- `create_workflow_transaction`
- `record_workflow_failure`
- `persist_workflow_bundle`
- `persist_analysis_execution_record`

## Parameterized SQL

All SQL uses bind parameters such as `:idempotency_key`, `:workflow_request_id`, and `:transaction_group_id`. The repository does not build SQL from user payload values.

## Idempotency

The repository checks `get_by_idempotency_key` before inserting a workflow request. If the same idempotency key already exists, `persist_workflow_bundle` returns the existing request with `duplicate=True` and status `DUPLICATE_REPLAY`.

## Transaction Handling

`persist_workflow_bundle` writes transaction, request, validation, audit, and output artifact metadata as one bundle. On success it updates the transaction status to `COMMITTED` and commits when `commit=True`.

## Audit Consistency

Successful bundle persistence writes an audit row with the request. The default audit row includes actor identity, action, summary, request reference, transaction reference, and payload hash.

## Failure Handling

`record_workflow_failure` records failure metadata by marking the transaction failed, marking an existing request failed when one exists, writing a failure audit row, and persisting an `error_artifact` reference. Failure metadata is recorded; the repository does not execute rollback.

## Output Artifact Persistence

Output artifact persistence stores references only. `AnalysisExecutionRecord` can create metadata references for analysis run records, Phase 4I payload references, dashboard artifact references, comparison artifacts, and source validation artifacts. It does not generate or refresh those artifacts.

## Import Safety

The repository does not import `scripts/run_analysis.py`, parser modules, scoring modules, decision modules, recommendation modules, dashboard modules, Object Storage clients, or Oracle driver modules. Importing it cannot open network connections or mutate runtime state.

## Boundary

Phase 7CA repository persistence is not runtime mutation. It creates governed workflow metadata only. No `run_analysis.py` execution occurs, no parser/scoring/recommendation behavior changes, no Phase 4I mutation occurs, and Phase 8 remains out of scope.
