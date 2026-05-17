# Phase 7CB Deterministic Re-Analysis Execution

## Purpose

Phase 7CB introduces the controlled deterministic execution service for Screen 3 Analyze Selection and Re-run Analysis requests. It uses the Phase 7CA governed workflow repository to persist request, validation, audit, transaction, and output reference metadata before active Screen 3 execution expands further.

## Scope

The scope is the service-layer execution boundary in `src/learning/screen3_deterministic_execution.py`. The service validates a Screen 3 re-analysis envelope, requires actor metadata, requires idempotency metadata, persists governed workflow metadata, optionally invokes an injected deterministic runner, and records output references.

## Non-Goals

Phase 7CB does not implement 7CC comparison execution, 7CD Object Storage load execution, 7CE dashboard output refresh, or 7CF certification. It does not modify `scripts/run_analysis.py`, dashboard UI files, parser modules, scoring modules, decision modules, recommendation modules, generated dashboard HTML, or DB schema. Phase 8 is not implemented.

## Deterministic Execution Is Not Adaptive Runtime

Deterministic execution here means an explicitly supplied service-layer runner can be invoked under a governed envelope. It does not mean adaptive runtime is enabled. `adaptive_runtime_requested` must remain false, `adaptive_runtime_used` remains false, and deterministic runtime remains authoritative.

## Execution Envelope

The `DeterministicExecutionRequestEnvelope` contains execution id, Screen 3 re-analysis request metadata, actor id, actor audit context, idempotency key, transaction group id, source mode, requested action, deterministic default flag, adaptive runtime flag, dry-run flag, validation reference, rollback reference, timestamps, and notes.

The envelope requires actor identity, idempotency key, transaction group id, deterministic default true, adaptive runtime false, and rollback reference metadata.

## Runner Interface

The runner is an injected callable. The service never imports `run_analysis.py` and makes no direct run_analysis.py call. A runner receives the envelope and returns a dictionary containing metadata such as `analysis_run_reference`, `phase4i_reference`, `dashboard_reference`, `artifact_summary`, and `warnings`.

## Repository Persistence

The service uses `GovernedWorkflowRepository` from Phase 7CA. It persists a workflow transaction, workflow request, workflow validation, workflow audit, and output artifact references. It uses repository methods only and does not issue direct SQL.

## Idempotency

The service checks idempotency before invoking a runner. If the idempotency key already exists, it returns `idempotent_replay` and does not invoke the runner again.

## Audit

Successful persistence includes an audit record tied to the workflow request and transaction group. The audit records that Phase 7CB deterministic execution metadata was recorded and that runtime truth was not mutated.

## Output References

Output references are metadata only. Supported references include analysis run record, Phase 4I payload reference, dashboard artifact reference, validation response, source validation artifact, and error artifact. No output files are written in Phase 7CB.

## Dry Run / No Runner Behavior

If `dry_run=true`, the service records governed metadata and returns `dry_run_only` without invoking a runner. If `dry_run=false` and no runner is supplied, it records governed metadata and returns `blocked_no_runner`.

## Runtime Safety Boundary

There is no subprocess, no direct run_analysis.py call, no Object Storage call, no adaptive runtime, no dashboard regeneration, no parser/scoring/recommendation behavior change, and no runtime semantic mutation.

## Phase 4I Boundary

Phase 4I is not mutated. The service can record a `phase4i_payload_reference` returned by an injected runner, but that reference does not replace deterministic truth.

## Relationship To 7CA

Phase 7CA supplied DB-backed governed workflow persistence. Phase 7CB consumes that repository to persist deterministic execution workflow metadata and enforce idempotency, transaction grouping, audit, and output reference behavior.

## Relationship To Future 7CC

7CC will own active AWR/report comparison execution. Phase 7CB does not build comparison artifacts beyond recording metadata references returned by an injected deterministic runner.

## Relationship To Future 7CD

7CD will own Object Storage load execution. Phase 7CB rejects Object Storage execution and records `object_storage_called=false`.

## Relationship To Future 7CE

7CE will own dashboard output refresh and regenerated artifact handling. Phase 7CB records dashboard references only and performs no dashboard regeneration.

## Acceptance Criteria

Phase 7CB is accepted when the deterministic execution service exists, the runner interface is injected, no-runner and dry-run paths block safely, fake runner execution works, repository persistence is integrated, idempotent replay prevents duplicate execution, DB-backed validation runs when ADB is available, no subprocess occurs, no direct run_analysis.py call occurs, no Object Storage call occurs, no adaptive runtime occurs, no dashboard regeneration occurs, Phase 4I is not mutated, deterministic runtime remains authoritative, and Phase 8 is not implemented.
