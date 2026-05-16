# Phase 7BR Local / Object Storage Source Status Panel

## 1. Purpose

Phase 7BR adds index-level source status visibility for the Agentic AI AWR Advisor. It shows readiness metadata for local staged AWR, local file, existing run, object storage, future upload, and future EM Extract without performing source access.

## 2. Scope

This phase adds a local deterministic source status model, source status summary model, validation helpers, serialization helpers, documentation, tests, and a preview-only landing-page Source Status panel.

## 3. Non-Goals

Phase 7BR does not validate real object storage configuration, read local files, check local file existence, query DB, query existing runs, call run_analysis.py, execute analysis, execute source intake, create a backend request, create Screen 3 handoff, implement EM Extract, or implement Phase 8 sizing/TCO.

## 4. Source Status Is Not Source Access

Source status is not source access. No files are read. No object storage calls are made. No DB lookup is made. No run_analysis.py call is made. The status panel is preview-only and reports metadata hints only.

## 5. Local Staged Status

Local staged AWR is the default operational source mode and is shown as `ready_metadata_only`. Phase 7BR does not inspect `data/input`, check local file existence, open files, read staged files, or invoke parser behavior.

## 6. Local File Status

Local file is shown as `needs_validation`. Phase 7BR does not open local paths, read local files, validate file existence, or parse file content.

## 7. Existing Run Status

Existing run is shown as `needs_validation`. Phase 7BR does not query DB, query existing runs, inspect persisted memory, or validate a run identifier.

## 8. Object Storage Status

Object storage is shown as `needs_configuration` unless metadata explicitly provides a configured hint. Phase 7BR does not import OCI, validate credentials, list buckets, download objects, call network, or make object storage calls. Real object storage validation belongs to future 7BS.

## 9. Future Upload Status

Future upload is shown as `future_not_implemented`. Phase 7BR does not upload files, stage files, read files, or submit content.

## 10. Future EM Extract Status

future_em_extract is Phase 8 placeholder. EM Extract implementation belongs to Phase 8. Phase 7BR does not implement an EM Extract adapter, connect to Enterprise Manager, or ingest EM extract content.

## 11. Preview-Only Status Panel

The Source Status panel is preview-only. It may show status, readiness, configuration requirements, validation requirements, and disabled execution/handoff indicators, but it cannot submit, fetch, call APIs, or change runtime behavior.

## 12. Source Access Boundary

`source_access_performed=false` in 7BR. `file_read_performed=false`, `object_storage_call_performed=false`, `db_lookup_performed=false`, and `run_analysis_called=false` in 7BR.

## 13. Object Storage Boundary

Object storage status is metadata only. A configured hint is not validation. No object storage calls are made, no credentials are checked, no bucket is listed, and no object is downloaded.

## 14. Local File Boundary

Local file status is metadata only. No files are read, no local paths are opened, and no file existence check is performed.

## 15. Existing Run Boundary

Existing run status is metadata only. No DB lookup is made, no run history is queried, and no persisted run is loaded.

## 16. Handoff Boundary

`handoff_supported=false in 7BR`. No Screen 3 handoff is implemented, no handoff payload is generated, and no active source selection is submitted.

## 17. Relationship to 7BQ

Phase 7BQ established the source mode entry point and preview-only entry cards. Phase 7BR adds read-only source status metadata for those same source modes without changing the 7BQ execution boundary.

## 18. Relationship to Future 7BS

Future 7BS may validate object storage configuration. Phase 7BR only displays metadata hints and does not validate namespace, bucket, region, credentials, object existence, or object access.

## 19. Relationship to Future 7BT

Future 7BT may implement index to Screen 3 selection handoff. Phase 7BR does not implement handoff, does not add submit behavior, and keeps `handoff_supported=false in 7BR`.

## 20. Relationship to Phase 8 EM Extract

Future EM Extract belongs to Phase 8. future_em_extract remains a Phase 8 placeholder in Phase 7BR. Phase 8 sizing/TCO is not implemented.

## 21. Acceptance Criteria

Phase 7BR is accepted when source status metadata exists for all six source modes, the Source Status panel renders preview-only status cards, object storage remains metadata-only, no source access occurs, `execution_supported=false in 7BR`, `handoff_supported=false in 7BR`, future EM Extract remains Phase 8 placeholder, and related 7BQ, 7AK, and 7AV tests continue to pass.
