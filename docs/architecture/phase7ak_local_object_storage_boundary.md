# Phase 7AK Local / Object Storage Boundary

## 1. Purpose

Phase 7AK defines the local and object storage source boundary for future Screen 3 backend re-analysis.

The boundary ensures source metadata can be represented before future execution exists. Source validation does not execute analysis.

## 2. Local Source Boundary

Local paths are metadata only.

Local staged file identifiers, local paths, file names, expected file types, checksums, and existence hints are descriptive metadata. They do not prove a file exists and they do not authorize file loading.

Phase 7AK does not check filesystem existence, open files, read files, parse files, compute checksums, or validate local AWR contents.

## 3. Object Storage Boundary

Object storage values are metadata only.

Namespace, bucket, object name, region, compartment id, credential mode, URI, and configured hint describe intended source location only.

Object storage is not called. Phase 7AK does not import OCI SDK, validate real credentials, list buckets, download objects, inspect object metadata, or load object contents.

## 4. Existing Run Boundary

Existing run source references are metadata only.

Run id, AWR id, DBID, database name, and snapshot label can describe a future existing-run source. They do not trigger database access and they do not prove that a run record exists.

No DB lookup is made.

## 5. Future EM Extract Boundary

Future EM Extract metadata is placeholder only.

Phase 7AK may represent extract id, extract format, EM version, target name, and target type. It does not implement EM Extract parsing, collection, loading, conversion, or analysis.

EM Extract is not implemented.

## 6. Credential Boundary

Credentials are not validated.

`credential_mode` is metadata only and may describe `env`, `instance_principal`, `resource_principal`, `config_file`, or `unknown`. `configured_hint` is metadata only and cannot be treated as proof that object storage access is available.

## 7. Source Availability Boundary

Source availability is metadata-only in Phase 7AK.

`exists_hint` and `configured_hint` may help a future validator report likely source availability, but they are not authoritative. Phase 7AK does not verify availability.

## 8. Missing Source Handling

Missing source metadata is represented as validation status, denied reasons, warnings, and required next steps.

Missing local source metadata returns `NEEDS_LOCAL_SOURCE`. Missing object storage metadata or unconfirmed object storage configuration returns `NEEDS_OBJECT_STORAGE_CONFIG`. Missing existing run metadata returns `NEEDS_EXISTING_RUN_REFERENCE`. Future upload and future EM extract modes return `FUTURE_SOURCE_NOT_IMPLEMENTED`.

## 9. Source Validation Without Execution

Source validation does not execute analysis.

Source validation validates metadata shape only. It does not read local files, call object storage, query databases, call `run_analysis.py`, write artifacts, refresh dashboards, mutate Phase 4I, or change runtime truth.

In Phase 7AK, `can_execute=false in Phase 7AK` and `execution_blocked=true in Phase 7AK`.

## 10. Future Object Storage Execution Requirements

Future object storage execution must require explicit user action, actor identity, backend execution mode, governed write-path validation, source validation, credential validation, object reference validation, output lifecycle tracking, error artifact handling, and audit trail coverage.

Phase 7AK does not implement those execution requirements. It only defines metadata required by future validation.

## 11. Future EM Extract Requirements

Future EM Extract support must define source acquisition, extract format validation, target metadata validation, parser/source compatibility, evidence availability behavior, output lifecycle handling, audit trail, and Phase 8 governance where applicable.

EM Extract implementation belongs to Phase 8. Phase 8 sizing/TCO is not implemented.

## 12. Relationship to Screen 3

Screen 3 may later expose source mode controls for local, object storage, existing run, future upload, or future EM extract sources.

Phase 7AK does not add Screen 3 buttons, source controls, forms, JavaScript backend calls, dashboard writes, dashboard refresh, or dashboard behavior changes.

## 13. Relationship to Phase 8

Phase 8 sizing/TCO and what-if advisory are not implemented in Phase 7AK.

The `future_em_extract` source mode is placeholder metadata only and does not implement Phase 8 EM Extract behavior.

## 14. Acceptance Criteria

Phase 7AK local/object storage boundary is accepted when it clearly states:

- Local paths are metadata only.
- Object storage values are metadata only.
- Credentials are not validated.
- Object storage is not called.
- EM Extract is not implemented.
- Source validation does not execute analysis.
- No files are read.
- No DB lookup is made.
- `can_execute=false in Phase 7AK`.
- `execution_blocked=true in Phase 7AK`.
- No dashboard behavior is changed.
- No CLI behavior is changed.
- Phase 8 sizing/TCO is not implemented.
