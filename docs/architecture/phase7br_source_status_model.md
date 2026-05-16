# Phase 7BR Source Status Model

## 1. Purpose

The Phase 7BR source status model provides deterministic local metadata for index-level source readiness visibility. It is safe to import and does not perform source access.

## 2. SourceModeStatus Object Shape

`SourceModeStatus` contains `source_mode`, `display_name`, `status`, `status_label`, `readiness_level`, `configured_hint`, `available_hint`, `requires_configuration`, `requires_validation`, `execution_supported`, `handoff_supported`, `source_access_performed`, `file_read_performed`, `object_storage_call_performed`, `db_lookup_performed`, `run_analysis_called`, `future_phase`, and `notes`.

## 3. SourceModeStatusSummary Object Shape

`SourceModeStatusSummary` contains `summary_id`, `source_count`, `ready_count`, `needs_configuration_count`, `future_count`, `blocked_count`, `default_source_mode`, `statuses`, `object_storage_configured_hint`, `local_source_available_hint`, `future_em_extract_placeholder`, `execution_supported`, `handoff_supported`, `source_access_performed`, `warnings`, `required_next_steps`, and `notes`.

## 4. Source Statuses

Supported statuses are `preview_only`, `ready_metadata_only`, `needs_configuration`, `needs_validation`, `future_not_implemented`, `blocked`, and `unknown`.

## 5. Readiness Levels

Supported readiness levels are `ready_metadata_only`, `needs_configuration`, `needs_validation`, `future`, `blocked`, and `unknown`.

## 6. Source Mode Rules

`local_staged` defaults to `ready_metadata_only`. `local_file` defaults to `needs_validation`. `existing_run` defaults to `needs_validation`. `object_storage` defaults to `needs_configuration` unless a configured hint is explicitly provided, in which case it still requires validation. `future_upload` defaults to `future_not_implemented` with `future_phase="future workflow"`. `future_em_extract` defaults to `future_not_implemented` with `future_phase="Phase 8"`.

## 7. Preview Rules

Source status is preview-only in 7BR. Metadata hints may be displayed, but no source is loaded and no availability check performs real I/O.

## 8. Handoff Rules

`handoff_supported=false`. Validation rejects `handoff_supported=true`. No Screen 3 handoff is implemented, no handoff request is built, and no active source selection is submitted.

## 9. Execution Rules

`execution_supported=false`. Validation rejects `execution_supported=true`. `source_access_performed=false`, `file_read_performed=false`, `object_storage_call_performed=false`, `db_lookup_performed=false`, and `run_analysis_called=false`.

## 10. Serialization Rules

Serialization uses plain dictionaries with local metadata fields only. Deserialization rebuilds dataclass instances and re-applies validation. Serialization does not read files, call object storage, query DB, call run_analysis.py, execute source intake, or perform handoff.

## 11. Validation Rules

Validation requires supported source modes, supported statuses, supported readiness levels, non-empty display names and status labels, boolean flags, matching source counts, non-negative summary counts, `future_em_extract_placeholder=true`, `source_access_performed=false`, `file_read_performed=false`, `object_storage_call_performed=false`, `db_lookup_performed=false`, `run_analysis_called=false`, `execution_supported=false`, and `handoff_supported=false`.

## 12. Non-Goals

The model does not read files, check local file existence, open local paths, call object storage, import OCI, validate real credentials, list buckets, download objects, query DB, query existing runs, call run_analysis.py, execute analysis, execute source intake, create backend requests, create Screen 3 handoff, implement object storage configuration validation, implement EM Extract, mutate Phase 4I, change parser/scoring/decision/recommendation behavior, or implement Phase 8 sizing/TCO.

## 13. Acceptance Criteria

The model is accepted when all six source modes have deterministic statuses, local staged status is `ready_metadata_only`, object storage status is `needs_configuration` unless configured by metadata hint, future EM Extract is a Phase 8 placeholder, summary counts validate, serialization round trips, unsafe source-access flags are rejected, and no source access occurs.
