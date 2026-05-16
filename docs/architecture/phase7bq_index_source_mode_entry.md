# Phase 7BQ Index Source Mode Entry Point

## 1. Purpose

Phase 7BQ defines the dashboard index source mode entry boundary for the Agentic AI AWR Advisor. It makes the landing page aware that future workflows may begin from multiple source modes while keeping the current runtime deterministic and unchanged.

## 2. Scope

This phase adds local source mode entry metadata and optional preview-only index visibility. The supported entry options are local staged AWR, local file, existing run, object storage, future upload, and future EM Extract.

## 3. Non-Goals

Phase 7BQ does not perform source intake, validate real source configuration, execute analysis, navigate to Screen 3, submit a backend request, or implement Phase 8. Phase 8 sizing/TCO is not implemented.

## 4. Why Index Source Mode Entry Is Needed

The dashboard needs a clear entry point where users can see future source mode choices before later phases add readiness status, configuration validation, and handoff. This phase establishes the vocabulary and UI boundary without changing execution behavior.

## 5. Source Mode Entry Is Not Execution

Source mode entry is not execution. No files are read. No object storage calls are made. No DB lookup is made. No run_analysis.py call is made. No Screen 3 handoff is implemented. The index view is informational and preview-only.

## 6. Local Staged Source

Local staged AWR is displayed as the default source mode entry. Phase 7BQ does not inspect `data/input`, check file existence, read staged files, or invoke parser behavior.

## 7. Local File Source

Local file is displayed as a future-selectable source mode entry. Phase 7BQ does not open paths, read local files, validate file names, or load file content.

## 8. Existing Run Source

Existing run is displayed as a source mode entry for later workflow handoff. Phase 7BQ does not query persisted run history, inspect memory tables, or perform DB lookup.

## 9. Object Storage Source

Object storage is displayed as a source mode entry and may require configuration in later phases. Phase 7BQ does not import OCI, validate object storage configuration, list buckets, download objects, call network, or call object storage.

## 10. Future Upload Source

Future upload is a placeholder entry only. Upload handling is not implemented in Phase 7BQ and no upload control submits or transfers content.

## 11. Future EM Extract Source

future_em_extract is placeholder only. EM Extract implementation belongs to Phase 8. Phase 7BQ does not implement an EM Extract adapter, connect to Enterprise Manager, or ingest EM extract content.

## 12. Preview-Only Boundary

Every index source mode entry is preview-only in Phase 7BQ. Preview labels may be shown, but preview is not source validation, source intake, source loading, backend execution, or governed write-path execution.

## 13. Source Handoff Boundary

Handoff is not supported in Phase 7BQ. `handoff_supported=false` for all entries and summaries. No Screen 3 handoff is implemented, no selection handoff URL is generated, and no submit behavior is added.

## 14. Runtime Truth Boundary

Deterministic runtime remains authoritative. The index entry model cannot alter scoring, decision posture, recommendation generation, parser output, governance state, learning candidate state, or dashboard truth.

## 15. Phase 4I Boundary

Phase 7BQ does not mutate Phase 4I contracts. Phase 4I validated runtime output remains the source consumed by the dashboard and recommendation flow.

## 16. Relationship to 7AK

Phase 7AK defined Screen 3 source selection metadata for local, object storage, existing run, future upload, and future EM Extract concepts. Phase 7BQ reuses the same source mode vocabulary at the index boundary without executing 7AK selection or validation behavior.

## 17. Relationship to 7AV

Phase 7AV defined Screen 1 source intake control metadata. Phase 7BQ does not invoke source intake and does not create a source intake request. It only exposes preview metadata at the dashboard entry point.

## 18. Relationship to Future 7BR

Future 7BR may add a local and object storage source status panel. Phase 7BQ does not implement source status, does not inspect local staging, and does not determine object storage readiness.

## 19. Relationship to Future 7BS

Future 7BS may validate object storage configuration. Phase 7BQ does not validate namespace, bucket, region, credentials, object existence, or object access.

## 20. Relationship to Future 7BT

Future 7BT may implement index to Screen 3 selection handoff. Phase 7BQ does not implement handoff, does not add active source mode selection, and does not submit to Screen 3.

## 21. Relationship to Phase 8 EM Extract

EM Extract implementation belongs to Phase 8. future_em_extract remains placeholder-only in Phase 7BQ. Phase 8 sizing/TCO is not implemented.

## 22. Acceptance Criteria

Phase 7BQ is accepted when the index source mode entry metadata exists, all six source modes are represented, handoff and execution remain disabled, documentation states the execution boundaries, tests prove no execution functions exist, and related 7AK, 7AV, and 7AJ tests continue to pass.
