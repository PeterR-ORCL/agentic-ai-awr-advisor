# Phase 7CA Active Backend Execution Boundary

## Purpose

Phase 7CA introduces the persistence foundation required before Screen 3 backend execution can become active. It creates DB-backed governed workflow metadata for requests, validations, transactions, audits, and output artifact references.

## Scope

This phase adds the schema in `dbschema/phase7ca_governed_workflow_persistence.sql` and the injected-connection repository in `src/learning/governed_workflow_repository.py`. It supports workflow metadata for Screen 3 and future Screen 1, 2, 4, 5, and 6 workflows.

## Non-Goals

Phase 7CA does not call `scripts/run_analysis.py`, execute analysis, load Object Storage, regenerate dashboards, activate Screen 3 buttons, mutate parser/scoring/recommendation behavior, mutate Phase 4I, or implement Phase 8 sizing/TCO.

## Why Persistence Is Required Before Active Execution

Active backend execution needs a durable boundary before a user action can trigger work. The repository records who requested the workflow, what action was requested, what validation occurred, which idempotency key guards retry, which transaction group owns the write, and what audit/artifact metadata was produced.

## Active Execution Boundary

Phase 7CA is a prerequisite boundary only. It records metadata that future 7CB-7CF execution steps may consume, but it does not start deterministic re-analysis, comparison, Object Storage loading, dashboard refresh, or certification.

## DB Persistence Boundary

DB persistence is limited to governed workflow state. The schema stores request payload CLOBs, validation CLOBs, audit hashes, transaction metadata, rollback references, and artifact references. It does not store generated dashboards, AWR file contents, external auth material, or local private paths.

## Workflow Persistence Is Not Runtime Mutation

Persisted workflow records are operational metadata. A persisted request, validation, approval-shaped payload, or output artifact reference does not change deterministic runtime truth and does not activate adaptive runtime behavior.

## Idempotency Requirement

Every persisted workflow request requires an `idempotency_key`. The transaction and request tables enforce uniqueness so replay of the same key returns the existing workflow request instead of creating duplicate records.

## Transaction Requirement

Every workflow request requires a `transaction_group_id`. The transaction row groups request, validation, audit, failure, and output artifact metadata into one governed write envelope.

## Audit Requirement

When `persist_workflow_bundle` succeeds, an audit row is written with the workflow request. The audit row references both request and transaction, includes actor identity, action, audit summary, and a payload hash.

## Output Artifact Requirement

Phase 7CA persists output artifact references only. Supported types include validation responses, analysis run records, Phase 4I payload references, dashboard artifact references, comparison artifacts, error artifacts, source validation artifacts, Object Storage load artifacts, and workflow audit artifacts.

## Rollback Reference Requirement

A rollback reference is required for bundle persistence. Phase 7CA records rollback metadata so future execution phases can reason about fallback, but it does not execute rollback.

## Phase 4I Boundary

Phase 4I remains deterministic output truth. Phase 7CA may persist a `phase4i_payload_reference` artifact record, but it never mutates, regenerates, or replaces a Phase 4I payload.

## Runtime Truth Boundary

Parser output, scoring, decision, recommendation, and dashboard truth remain owned by their existing deterministic layers. Workflow persistence does not grant runtime eligibility, apply parser mappings, activate scoring config, apply recommendation rules, or deploy ML models.

## Relationship To 7AJ-7AO

Phases 7AJ-7AO defined Screen 3 re-analysis request and readiness metadata without active backend execution. Phase 7CA adds durable persistence for the governed workflow records that future active execution will require.

## Relationship To 7BU-7BZ

Phases 7BU-7BZ defined runtime materialization metadata and explicitly did not persist to DB. Phase 7CA is the first governed workflow persistence phase and turns the metadata envelope into durable workflow state without activating runtime materialization.

## Relationship To Future 7CB-7CF

Future phases may use Phase 7CA records as prerequisites. 7CB may execute deterministic re-analysis, 7CC may compare reports, 7CD may load Object Storage, 7CE may refresh output artifacts, and 7CF may certify active execution. None of those actions are implemented in 7CA.

## Acceptance Criteria

Phase 7CA is accepted when the schema exists, repository persistence works with injected connections, idempotency prevents duplicate workflow requests, transaction metadata is required, audit rows are written with successful request persistence, output artifact references can be recorded, failure metadata can be recorded, local tests pass, and DB-backed validation runs if ADB connectivity is available.
