# Phase 7BQ Source Mode Entry Model

## 1. Purpose

The Phase 7BQ source mode entry model provides deterministic local metadata for dashboard index source choices. It is safe to import and does not load sources.

## 2. IndexSourceModeEntry Object Shape

`IndexSourceModeEntry` contains `source_mode`, `display_name`, `description`, `enabled_for_preview`, `implemented`, `requires_configuration`, `requires_validation`, `target_screen`, `handoff_supported`, `execution_supported`, `status_label`, and `notes`.

## 3. IndexSourceModeEntrySummary Object Shape

`IndexSourceModeEntrySummary` contains `summary_id`, `entries`, `default_source_mode`, `source_mode_count`, `implemented_count`, `preview_only_count`, `handoff_supported`, `execution_supported`, `object_storage_available_hint`, `future_em_extract_available_hint`, and `notes`.

## 4. Supported Source Modes

Supported source modes are `local_staged`, `local_file`, `existing_run`, `object_storage`, `future_upload`, and `future_em_extract`.

## 5. Display Names

Display names are Local Staged AWR, Local File, Existing Run, Object Storage, Future Upload, and Future EM Extract.

## 6. Preview Rules

Source modes are preview-only. `enabled_for_preview` may be true so the index can show the entry options, but preview is not source loading, source validation, source intake, backend request creation, or execution.

## 7. Handoff Rules

`handoff_supported=false` in 7BQ for every entry and summary. Validation rejects `handoff_supported=true`. No Screen 3 handoff is implemented and no handoff payload is generated.

## 8. Execution Rules

`execution_supported=false` in 7BQ for every entry and summary. Validation rejects `execution_supported=true`. Source mode entry is not execution. No files are read, no object storage calls are made, no DB lookup is made, and no run_analysis.py call is made.

## 9. Serialization Rules

Serialization uses plain dictionaries with only local metadata fields. Deserialization rebuilds dataclass instances and re-applies validation. Serialization does not execute source lookup, object storage access, DB lookup, file reading, or handoff.

## 10. Validation Rules

Validation requires a supported `source_mode`, non-empty `display_name`, non-empty `description`, boolean preview and implementation flags, boolean configuration and validation flags, `handoff_supported=false`, `execution_supported=false`, matching source mode counts, and matching summary counts. `future_em_extract_available_hint` defaults to false.

## 11. Non-Goals

The model does not call object storage, import OCI, call network, read local files, check file existence, query DB, call run_analysis.py, execute source intake, create backend requests, implement Screen 3 handoff, implement EM Extract, mutate Phase 4I, or implement Phase 8 sizing/TCO. future_em_extract is placeholder only and EM Extract implementation belongs to Phase 8.

## 12. Acceptance Criteria

The model is accepted when all supported source modes can be created, the default summary uses `local_staged`, counts validate, unsupported source modes are rejected, handoff and execution flags are rejected when true, serialization round trips, source modes remain preview-only, and no source is loaded.
