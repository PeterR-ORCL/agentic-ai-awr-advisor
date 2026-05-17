# Phase 7CE Dashboard Output Refresh

## 1. Purpose

Phase 7CE introduces controlled dashboard output refresh and regenerated artifact handling for active Screen 3 execution results. It records metadata references for refreshed dashboard outputs without changing deterministic runtime truth.

## 2. Scope

The scope is limited to consuming 7CB deterministic execution metadata, 7CC comparison metadata, and 7CD Object Storage load metadata; creating dashboard refresh request and validation metadata; recording Phase 4I payload references; recording regenerated or linked dashboard artifact references; and persisting output artifact metadata through the Phase 7CA governed workflow repository.

## 3. Non-Goals

Phase 7CE does not execute analysis, does not call run_analysis.py, does not invoke parser/scoring/recommendation modules, does not call Object Storage, does not read AWR files, does not query report content from the DB, does not mutate Phase 4I, does not regenerate dashboard files by default, does not overwrite dashboard files silently, does not activate Screen 3 UI buttons, does not implement EM Extract, and does not implement Phase 8.

## 4. Dashboard Refresh Is Not Analysis Execution

Dashboard refresh metadata is presentation-layer workflow state. It is not parser output, scoring output, recommendation output, analysis execution, Object Storage load execution, or deterministic backend truth mutation.

## 5. DashboardRefreshRequestEnvelope

`DashboardRefreshRequestEnvelope` captures the refresh execution id, source execution id and type, optional source workflow request id, actor/audit metadata, idempotency key, transaction group id, Phase 4I reference, dashboard reference, comparison reference, Object Storage reference, refresh mode, renderer intent, dry-run flag, validation reference, rollback reference, creation timestamp, and notes.

## 6. DashboardRefreshValidation

`DashboardRefreshValidation` records whether the source execution and Phase 4I reference are present, whether an injected renderer is present, whether the request can refresh, whether it is blocked, denied reasons, warnings, required next steps, and safety flags. Safety flags remain false for Phase 4I mutation, run_analysis.py, parser, scoring, recommendation, and Object Storage calls.

## 7. RegeneratedDashboardArtifactReference

`RegeneratedDashboardArtifactReference` records dashboard artifact metadata such as artifact id, artifact type, artifact reference, summary, optional output path, renderer name/version, generation flag, output write flag, overwrite flag, generated timestamp, and notes. Dashboard generation only through injected renderer is the Phase 7CE rule.

## 8. Phase4IPayloadReference

`Phase4IPayloadReference` records the Phase 4I payload reference consumed by a dashboard refresh. It preserves the Phase 4I contract and records `phase4i_mutated=false`.

## 9. DashboardRefreshResult

`DashboardRefreshResult` records the refresh status, validation metadata, optional Phase 4I payload reference, optional dashboard artifact reference, workflow persistence flags, idempotent replay flag, dashboard regeneration and output write flags, safety flags, denied reasons, warnings, required next steps, and notes.

## 10. Refresh Modes

Supported refresh modes are `metadata_only`, `link_existing_dashboard`, `regenerate_with_renderer`, `validation_response_only`, and `error_artifact_only`. The default path is metadata-only.

## 11. Renderer Injection Boundary

No renderer is constructed on import. No dashboard rendering source is imported. `regenerate_with_renderer` requires an injected renderer. The injected renderer may validate input and return dashboard artifact metadata, but 7CE validates that it does not report run_analysis.py, parser, scoring, recommendation, Object Storage, or Phase 4I mutation.

## 12. Repository Persistence

Phase 7CE uses the governed workflow repository to persist transaction, request, validation, audit, and output artifact metadata. It records references only; it does not create generated dashboard HTML by default.

## 13. Idempotency

An idempotency key is required. Existing workflow metadata returns `idempotent_replay` before the renderer is called, preventing duplicate dashboard generation attempts or duplicate output artifact records.

## 14. Output Artifact Metadata

Phase 7CE may persist `phase4i_payload_reference`, `dashboard_artifact_reference`, `comparison_artifact`, `object_storage_load_artifact`, `validation_response`, and `error_artifact` metadata. Persisted references do not imply artifact file generation or runtime truth mutation.

## 15. Phase 4I Boundary

Phase 7CE does not mutate Phase 4I. A Phase 4I payload reference is a pointer to a preserved contract, not a rewritten payload.

## 16. Runtime Truth Boundary

Deterministic runtime remains authoritative. Dashboard output refresh metadata is a governed presentation artifact layer and cannot change parser/scoring/recommendation decisions.

## 17. Relationship to 7CA

Phase 7CA provides the repository, idempotency, transaction, audit, validation, and output artifact tables used by Phase 7CE.

## 18. Relationship to 7CB

Phase 7CB produces deterministic execution metadata and output references. Phase 7CE consumes those references and does not redo deterministic execution.

## 19. Relationship to 7CC

Phase 7CC produces in-memory comparison metadata and comparison artifact references. Phase 7CE can link those references but does not rebuild comparisons.

## 20. Relationship to 7CD

Phase 7CD produces Object Storage load metadata. Phase 7CE can reference that metadata but makes no Object Storage call and does not read loaded object contents.

## 21. Relationship to Future 7CF

Phase 7CF will certify the active Screen 3 execution path. Phase 7CE does not enable active Screen 3 UI buttons.

## 22. Acceptance Criteria

Phase 7CE is accepted when dashboard refresh request, validation, result, Phase 4I payload reference, and dashboard artifact reference models exist; metadata-only refresh works; fake renderer refresh works only through injection; idempotent replay avoids renderer calls; repository persistence records output artifact metadata; no run_analysis.py call occurs; no parser/scoring/recommendation invocation occurs; no Object Storage call occurs; no Phase 4I mutation occurs; default behavior performs no dashboard regeneration; no generated dashboard HTML is committed; deterministic runtime remains authoritative; and Phase 8 is not implemented.
