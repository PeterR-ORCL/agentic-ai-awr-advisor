# Phase 7CC Comparison Execution Model

## Object Shapes

`ComparisonExecutionRequestEnvelope` contains the deterministic comparison execution id, `BackendReAnalysisRequest`, actor id, actor audit context, idempotency key, transaction group id, comparison name, supplied comparison inputs, baseline reference, requested action, source mode, deterministic flags, dry-run flag, validation reference, rollback reference, created timestamp, and notes.

`ComparisonExecutionResult` contains the execution status, comparison artifact, persistence flags, idempotent replay flag, safety flags, output references, denied reasons, warnings, required next steps, and notes.

`ComparisonOutputReference` contains the output reference id, comparison id, artifact type, artifact reference, artifact summary, persistence flag, output-written flag, dashboard flag, Phase 4I flag, and notes.

## Statuses

Supported statuses are `blocked_invalid_request`, `blocked_insufficient_inputs`, `comparison_built_in_memory`, `comparison_persisted_metadata`, `idempotent_replay`, and `failed_safely`.

Comparison input readiness statuses are `comparison_ready`, `already_loaded`, `staged_needs_load`, `needs_reanalysis`, `missing_structured_payload`, and `invalid`.

## Validation Rules

The envelope requires actor id, actor audit context, idempotency key, transaction group id, rollback reference, requested action `build_comparison`, matching Screen 3 source mode, deterministic default enabled, adaptive runtime disabled, and at least two supplied in-memory comparison input dictionaries.

Each comparison input must be `comparison_ready` or `already_loaded` and must contain a structured comparison-ready payload. Staged-only, raw-file-only, `staged_needs_load`, `needs_reanalysis`, `missing_structured_payload`, and `invalid` inputs return a blocked comparison result before the comparison engine is called.

The result rejects any true value for `run_analysis_called`, `subprocess_called`, `object_storage_called`, `local_file_read_performed`, `parser_called`, `db_lookup_performed`, `dashboard_regenerated`, `phase4i_mutated`, `adaptive_runtime_used`, or `phase8_sizing_tco_used`.

The output reference requires artifact type `comparison_artifact` and rejects output writes, dashboard regeneration, and Phase 4I mutation.

## Persistence Behavior

When no repository is supplied, Phase 7CC may build the comparison in memory and returns persistence flags as false. When a `GovernedWorkflowRepository` is supplied, the service writes transaction, request, validation, audit, and comparison output artifact metadata. This phase introduces active comparison workflow persistence, not runtime mutation.

## Idempotency

The service checks the repository by idempotency key before building a comparison. Existing workflow metadata returns `idempotent_replay`, does not rebuild the comparison, and does not write duplicate request rows.

## Deterministic IDs

`create_comparison_execution_id(request_id, idempotency_key)` produces a stable id for the comparison execution envelope. Workflow request and output artifact ids continue to use the Phase 7CA repository id helpers.

## In-Memory Comparison Inputs

Comparison inputs are dictionaries supplied by the caller. They may include run identifiers, AWR identifiers, scores, wait events, SQL concentration, trends, anomalies, topology, platform target, source options, data availability, and missing metrics. Missing values remain missing and become limitations where the 7AM engine can identify them.

An already-loaded structured payload can be provided at the top level or inside `structured_payload`, `comparison_ready_payload`, or `comparison_payload`. A staged-only input blocks comparison with the denied reason "Selected AWR is staged but not loaded; run deterministic load/re-analysis before comparison." A missing structured payload blocks comparison with a deterministic load/re-analysis next step.

## Boundary Phrases

The comparison uses supplied in-memory payloads only. No AWR files are read. No parser is called. No DB report lookup occurs. No object storage call occurs. No run_analysis.py call occurs. No dashboard regeneration occurs. No Phase 4I mutation occurs. Phase 8 sizing/TCO comparison remains future. Do not implement Load-and-Compare in Phase 7CC.

## Non-Goals

Phase 7CC does not parse reports, read files, load Object Storage data, query report bodies from the DB, regenerate dashboard HTML, mutate parser/scoring/recommendation behavior, activate adaptive runtime, mutate Phase 4I, implement Load-and-Compare, or implement Phase 8 sizing/TCO comparison.
