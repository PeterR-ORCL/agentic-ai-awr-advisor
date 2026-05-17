# Phase 7CB Deterministic Execution Model

## Purpose

This document defines the Phase 7CB deterministic execution object model. The model enables governed Screen 3 deterministic re-analysis execution with an injected runner and Phase 7CA repository persistence.

## Object Shapes

`DeterministicExecutionRequestEnvelope` carries the execution id, `BackendReAnalysisRequest`, actor id, actor audit context, idempotency key, transaction group id, source mode, requested action, deterministic default flag, adaptive runtime request flag, dry-run flag, validation reference, rollback reference, created timestamp, and notes.

`DeterministicExecutionResult` records execution id, request id, idempotency key, transaction group id, execution status, deterministic execution flag, runner invocation flag, safety flags, persistence flags, output references, denied reasons, warnings, next steps, and notes.

`DeterministicExecutionOutputReference` records output reference id, artifact type, artifact reference, summary, optional Phase 4I reference, optional dashboard reference, optional comparison reference, optional error reference, persistence flag, output write flag, dashboard regeneration flag, Phase 4I mutation flag, and notes.

## Statuses

Supported statuses are `dry_run_only`, `blocked_no_runner`, `invalid_request`, `persisted_metadata_only`, `deterministic_runner_completed`, `idempotent_replay`, and `failed_safely`. No status enables adaptive runtime.

## Runner Contract

The runner is a callable supplied by the caller. It receives a `DeterministicExecutionRequestEnvelope` and returns a dictionary. Common keys are `analysis_run_reference`, `phase4i_reference`, `dashboard_reference`, `artifact_summary`, and `warnings`.

The service validates runner safety flags. The runner must not report `run_analysis_called=true`, `subprocess_called=true`, `adaptive_runtime_used=true`, `object_storage_called=true`, `dashboard_regenerated=true`, or `phase4i_mutated=true`.

## Repository Integration

The service integrates with `GovernedWorkflowRepository`. It persists `PersistedWorkflowTransaction`, `PersistedWorkflowRequest`, `PersistedWorkflowValidation`, `PersistedWorkflowAudit`, and `PersistedWorkflowOutputArtifact` records.

The service does not issue direct SQL. It relies on Phase 7CA repository methods and therefore inherits parameterized SQL, idempotency handling, transaction grouping, audit consistency, and output reference persistence.

## Safety Flags

The result always records `run_analysis_called=false`, `subprocess_called=false`, `adaptive_runtime_used=false`, `object_storage_called=false`, `dashboard_regenerated=false`, and `phase4i_mutated=false`.

## Validation Rules

The envelope requires actor id, actor audit context with actor id, idempotency key, transaction group id, source mode, requested action, deterministic default true, adaptive runtime requested false, and rollback reference.

Only `analyze_selection` and `rerun_analysis` are deterministic 7CB actions. `build_comparison` belongs to future 7CC. Object Storage execution belongs to future 7CD.

## Idempotency

Before invoking a runner, the service looks up the idempotency key in the governed workflow repository. If a request already exists, it returns `idempotent_replay` and does not invoke the runner.

## Output References

The service persists metadata references only. Output references do not write files, regenerate dashboards, mutate Phase 4I, or alter deterministic runtime truth.

## Non-Goals

Phase 7CB has no subprocess, no direct run_analysis.py call, no adaptive runtime, no Object Storage, no dashboard regeneration, no parser/scoring/recommendation behavior changes, no Phase 4I mutation, and no Phase 8 implementation.

## Runtime Authority

Deterministic runtime remains authoritative. Phase 7CB stores governed workflow metadata and output references; it does not replace deterministic backend truth or activate adaptive runtime.
