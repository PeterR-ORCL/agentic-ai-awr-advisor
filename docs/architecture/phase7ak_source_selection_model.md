# Phase 7AK Source Selection Model

## 1. Purpose

Phase 7AK defines the local deterministic source selection model for future Screen 3 backend re-analysis.

The model lets future Screen 3 requests describe where analysis input should come from without loading, executing, or mutating anything.

Source selection is not execution.

## 2. Scope

The scope is source selection metadata, source reference metadata, source availability metadata, deterministic identifiers, serialization helpers, and metadata-only validation.

Phase 7AK covers:

- `SourceSelection`
- `LocalSourceReference`
- `ObjectStorageSourceReference`
- `ExistingRunSourceReference`
- `FutureEMExtractSourceReference`
- `SourceValidationResult`
- source modes
- source validation statuses
- deterministic ID rules
- serialization and deserialization rules

## 3. Non-Goals

Phase 7AK does not read files. No files are read.

Phase 7AK does not open local AWR files, load local files, parse local files, validate file contents, call Object Storage, validate real Object Storage credentials, list buckets, download objects, call OCI SDK, call network services, query databases, call `run_analysis.py`, execute backend analysis, create Screen 3 buttons, modify dashboard behavior, modify CLI behavior, implement an EM Extract adapter, implement AWR/report comparison, implement missing metric handling, or implement Phase 8 sizing/TCO.

No object storage calls are made.

No DB lookup is made.

## 4. Source Selection Is Not Execution

Source selection is not execution.

A source selection record describes source intent only. It may identify no source, a local staged source, a local path, an existing run, object storage metadata, a future upload placeholder, or a future EM extract placeholder.

In Phase 7AK, `can_execute=false in Phase 7AK` and `execution_blocked=true in Phase 7AK`. A valid source selection means metadata-valid only, not executable.

## 5. Source Modes

Supported source modes are:

- `none`
- `local_staged`
- `local_file`
- `existing_run`
- `object_storage`
- `future_upload`
- `future_em_extract`

`none` is valid for no source selected or placeholder state. `local_staged` and `local_file` are metadata-only. `existing_run` is metadata-only and performs no database lookup. `object_storage` is metadata-only and performs no OCI call. `future_upload` is placeholder metadata only. `future_em_extract` is placeholder metadata only.

## 6. Local Source Reference

`LocalSourceReference` describes local source metadata:

- `local_source_id`
- `staged_file_id`
- `local_path`
- `file_name`
- `expected_file_type`
- `checksum`
- `exists_hint`
- `notes`

At least one of `staged_file_id`, `local_path`, or `file_name` is required for meaningful local source metadata. `expected_file_type` must be one of the supported expected source file types when provided.

`exists_hint` is metadata only. No filesystem existence check is performed. No files are read.

## 7. Object Storage Source Reference

`ObjectStorageSourceReference` describes object storage metadata:

- `object_source_id`
- `namespace`
- `bucket`
- `object_name`
- `region`
- `compartment_id`
- `credential_mode`
- `uri`
- `configured_hint`
- `notes`

`namespace`, `bucket`, `object_name`, and `region` are required for meaningful object storage source metadata. `credential_mode` may be `env`, `instance_principal`, `resource_principal`, `config_file`, or `unknown`.

`configured_hint` is metadata only. Credentials are not validated. No object storage calls are made.

## 8. Existing Run Source Reference

`ExistingRunSourceReference` describes existing run metadata:

- `run_source_id`
- `run_id`
- `awr_id`
- `dbid`
- `database_name`
- `snapshot_label`
- `notes`

At least one of `run_id` or `awr_id` is required for meaningful existing-run metadata.

No DB lookup is made. No run history is queried.

## 9. Future EM Extract Source Reference

`FutureEMExtractSourceReference` describes placeholder future Enterprise Manager extract metadata:

- `em_source_id`
- `extract_id`
- `extract_format`
- `em_version`
- `target_name`
- `target_type`
- `notes`

`future_em_extract is placeholder only`. Metadata can validate as a placeholder, but evaluation returns `FUTURE_SOURCE_NOT_IMPLEMENTED`.

EM Extract implementation belongs to Phase 8. Phase 7AK does not implement an EM Extract adapter.

## 10. Source Validation Result

`SourceValidationResult` records metadata-only validation:

- `validation_id`
- `source_selection_id`
- `valid`
- `validation_status`
- `source_mode`
- `denied_reasons`
- `warnings`
- `required_next_steps`
- `can_execute`
- `execution_blocked`
- `object_storage_call_performed`
- `local_file_read_performed`
- `db_lookup_performed`
- `created_at`
- `notes`

The required Phase 7AK flags are:

- `can_execute=false in Phase 7AK`
- `execution_blocked=true in Phase 7AK`
- `object_storage_call_performed=false`
- `local_file_read_performed=false`
- `db_lookup_performed=false`

## 11. Source Validation Statuses

Supported validation statuses are:

- `VALID_METADATA_ONLY`
- `INVALID`
- `NO_SOURCE_SELECTED`
- `NEEDS_LOCAL_SOURCE`
- `NEEDS_OBJECT_STORAGE_CONFIG`
- `NEEDS_EXISTING_RUN_REFERENCE`
- `FUTURE_SOURCE_NOT_IMPLEMENTED`
- `EXECUTION_NOT_ALLOWED_IN_THIS_PHASE`

`VALID_METADATA_ONLY` means the source metadata shape is valid. It does not mean the source can execute.

## 12. Deterministic ID Rules

IDs are deterministic. They use normalized source metadata and do not use random UUIDs, timestamps, database sequences, or external services.

Identifier shapes include:

- `SCREEN3-SOURCE-SELECTION-<MODE>-<LABEL>`
- `LOCAL-SOURCE-<FILE_OR_PATH_OR_STAGED_ID>`
- `OBJECT-SOURCE-<NAMESPACE>-<BUCKET>-<OBJECT>-<REGION>`
- `EXISTING-RUN-SOURCE-<RUN_OR_AWR_OR_DBID>`
- `FUTURE-EM-EXTRACT-SOURCE-<EXTRACT_OR_TARGET>`
- `SOURCE-VALIDATION-<SOURCE_SELECTION_ID>`

## 13. Serialization Rules

Source reference records, source selection records, and source validation result records must serialize to plain dictionaries and deserialize back to equivalent deterministic dataclass records.

Serialization does not perform source access. Deserialization validates metadata shape only.

## 14. Runtime Truth Boundary

Source selection metadata is not runtime truth.

Source selection does not change parser output, scoring, decisions, recommendations, trend/anomaly behavior, Phase 4I payloads, dashboard artifacts, CLI behavior, database state, memory state, or generated dashboard HTML.

Deterministic runtime remains authoritative.

## 15. Object Storage Boundary

Object storage metadata describes intended source location only.

Phase 7AK does not import OCI SDK, call Object Storage, validate credentials, list buckets, download objects, inspect objects, or create object storage load artifacts.

No object storage calls are made.

## 16. Local File Boundary

Local paths and staged file identifiers are metadata only.

Phase 7AK does not check filesystem existence, open files, read files, parse files, compute checksums, or validate local AWR contents.

No files are read.

## 17. Existing Run Boundary

Existing run references are metadata only.

Phase 7AK does not query databases, inspect run history, load prior Phase 4I payloads, or validate prior dashboard artifacts.

No DB lookup is made.

## 18. Future EM Extract Boundary

Future EM extract support is placeholder metadata only in Phase 7AK.

`future_em_extract is placeholder only`. EM Extract implementation belongs to Phase 8. Phase 8 sizing/TCO is not implemented.

## 19. Relationship to 7AJ

Phase 7AJ defined the Screen 3 backend re-analysis boundary and stated that source mode must be validated before execution.

Phase 7AK adds the metadata model used to describe that future source intent. It preserves the 7AJ rule that source selection is not execution.

## 20. Relationship to Future 7AL

Future 7AL may define the backend re-analysis request model.

Phase 7AK source selection records may become inputs to that future request model, but Phase 7AK does not implement request submission, action payloads, API contracts, command payloads, or execution requests.

## 21. Relationship to Future 7AM

Future 7AM may implement the backend re-analysis execution controller.

Phase 7AK does not execute analysis, call `run_analysis.py`, read selected sources, call object storage, query existing runs, write artifacts, regenerate dashboards, or create run records.

## 22. Relationship to Future 7AO.1

Future 7AO.1 may handle missing metric and evidence availability behavior.

Phase 7AK does not inspect source contents, detect missing metrics, adjust confidence, or create parser/source review candidates.

## 23. Relationship to Phase 8 EM Extract

Phase 8 may later define EM Extract support, sizing/TCO, and what-if advisory features.

Phase 7AK includes `future_em_extract` as placeholder metadata only so future source intent can be represented without implementing Phase 8.

EM Extract implementation belongs to Phase 8. Phase 8 sizing/TCO is not implemented.

## 24. Acceptance Criteria

Phase 7AK is accepted when source selection metadata, local source metadata, object storage source metadata, existing run source metadata, future EM extract placeholder metadata, validation result metadata, deterministic IDs, serialization helpers, documentation, and focused tests exist.

Acceptance requires:

- Source selection is not execution.
- No files are read.
- No object storage calls are made.
- No DB lookup is made.
- `can_execute=false in Phase 7AK`.
- `execution_blocked=true in Phase 7AK`.
- `future_em_extract is placeholder only`.
- EM Extract implementation belongs to Phase 8.
- No dashboard behavior is changed.
- No CLI behavior is changed.
- No `run_analysis.py` wiring is added.
- Deterministic runtime remains authoritative.
- Phase 8 sizing/TCO is not implemented.
