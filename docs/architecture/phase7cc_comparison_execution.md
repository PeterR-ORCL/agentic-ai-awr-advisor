# Phase 7CC Comparison Execution

## 1. Purpose

Phase 7CC introduces the controlled active AWR/report comparison execution path for Screen 3. It builds comparison metadata from supplied in-memory payloads and records governed workflow metadata through the Phase 7CA repository when a repository is supplied.

## 2. Scope

The scope is limited to validating comparison execution envelopes, reusing the Phase 7AM in-memory comparison engine, returning a comparison execution result, and persisting workflow request, validation, audit, transaction, and comparison output artifact metadata.

## 3. Non-Goals

This phase does not parse AWR files, read local files, query report content from the DB, call Object Storage, call run_analysis.py, regenerate dashboards, mutate Phase 4I, modify parser/scoring/recommendation behavior, activate adaptive runtime, or implement Phase 8. Do not implement Load-and-Compare in Phase 7CC.

## 4. Active Comparison Execution Is Not Phase 8 Sizing/TCO

Phase 7CC compares supplied AWR/report/run summary payloads for Screen 3 workflow execution. It is not target platform sizing, TCO modeling, ExaDB-D versus ADB-D advisory, EM Extract comparison, or what-if cost modeling. Phase 8 sizing/TCO comparison remains future.

## 5. ComparisonExecutionRequestEnvelope

The request envelope carries the comparison execution id, Screen 3 re-analysis request, actor id, actor audit context, idempotency key, transaction group id, comparison name, supplied comparison inputs, baseline reference, requested action, source mode, deterministic/default flags, validation reference, rollback reference, created timestamp, and notes.

## 6. ComparisonExecutionResult

The result records whether the comparison was built, whether governed metadata was persisted, whether the request was an idempotent replay, and the safety flags proving that no file, object store, DB report lookup, dashboard, adaptive runtime, Phase 4I, or Phase 8 path was used.

## 7. ComparisonOutputReference

The output reference records metadata for the comparison artifact only. The artifact type is `comparison_artifact`; the reference is metadata, not a generated file. No dashboard regeneration occurs and no Phase 4I mutation occurs.

## 8. In-Memory Comparison Engine Reuse

Phase 7CC reuses the existing Phase 7AM comparison engine in `screen3_reanalysis_controller.py`. The comparison uses supplied in-memory payloads only. No AWR files are read, no parser is called, no DB report lookup occurs, no object storage call occurs, and no run_analysis.py call occurs.

## 8A. Comparison Input Readiness

Comparison input readiness must be validated before the comparison engine is called. Supported readiness states are `comparison_ready`, `already_loaded`, `staged_needs_load`, `needs_reanalysis`, `missing_structured_payload`, and `invalid`.

Only `comparison_ready` or `already_loaded` inputs with structured comparison-ready payloads may be compared. If an input is staged-only, raw-file-only, or missing a structured payload, Phase 7CC returns a blocked result. A staged input uses the denied reason: "Selected AWR is staged but not loaded; run deterministic load/re-analysis before comparison." A missing structured payload uses a denied reason telling the caller to run deterministic load/re-analysis before comparison.

This readiness gate does not read staged files, does not call a parser, does not call run_analysis.py, does not implement Load-and-Compare, and does not implement Object Storage loading.

## 9. Governed Repository Persistence

When a `GovernedWorkflowRepository` is supplied, Phase 7CC persists workflow transaction, request, validation, audit, and comparison output artifact metadata. Persistence is workflow metadata only and is not deterministic runtime truth mutation.

## 10. Idempotency

An idempotency key is required. A repeated key returns `idempotent_replay`, avoids duplicate workflow rows, and does not rebuild the comparison.

## 11. Output Artifact Metadata

The comparison output artifact is stored as a reference with summary and serialized comparison metadata. The phase does not write dashboard files or generated comparison files.

## 12. Data Availability / Missing Value Limitations

Missing values are surfaced as comparison limitations and data availability differences. The comparison engine must not fabricate values to make absent data appear present.

## 13. Runtime Safety Boundary

The safety boundary requires `run_analysis_called=false`, `subprocess_called=false`, `object_storage_called=false`, `local_file_read_performed=false`, `parser_called=false`, `db_lookup_performed=false`, `dashboard_regenerated=false`, `adaptive_runtime_used=false`, and `phase8_sizing_tco_used=false`.

## 14. Phase 4I Boundary

Phase 7CC may reference comparison metadata, but it does not write Phase 4I payloads. No Phase 4I mutation occurs.

## 15. Relationship to 7AM.1

Phase 7AM.1 provides the comparison engine and artifact model. Phase 7CC adds active governed execution metadata around that in-memory engine.

## 16. Relationship to 7CA

Phase 7CA provides the governed workflow repository, idempotency, transaction, validation, audit, and output artifact persistence primitives consumed by Phase 7CC.

## 17. Relationship to 7CB

Phase 7CB established the deterministic execution envelope/result pattern. Phase 7CC follows the same controlled execution style while performing comparison work rather than deterministic re-analysis.

## 18. Relationship to Future 7CD

Object Storage loading remains future 7CD work. Phase 7CC does not call Object Storage and does not load report content from Object Storage.

## 19. Relationship to Future 7CE

Dashboard output refresh and regenerated artifact handling remain future 7CE work. No dashboard regeneration occurs in Phase 7CC.

## 20. Relationship to Phase 8

Phase 8 remains separate and future. Phase 7CC does not implement sizing, TCO, target-platform what-if, or cost comparison logic.

## 21. Acceptance Criteria

Phase 7CC is accepted when comparison execution validates actor, audit, idempotency, transaction, comparison input readiness, and input metadata; builds comparisons from supplied already-loaded structured in-memory payloads only; blocks staged-only and missing-structured-payload inputs; persists governed workflow metadata when a repository is supplied; supports idempotent replay; records comparison output references; and keeps all runtime mutation, file access, parser call, Object Storage, DB report lookup, dashboard regeneration, Phase 4I, adaptive runtime, and Phase 8 flags false.
