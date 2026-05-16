# Phase 7BT Index to Screen 3 Handoff Model

## 1. Purpose

The Phase 7BT handoff model provides deterministic local metadata for a future index-to-Screen-3 source selection handoff. It describes a possible handoff without performing it.

## 2. IndexToScreen3Handoff Object Shape

`IndexToScreen3Handoff` contains `handoff_id`, `source_mode`, `source_mode_entry_id`, `source_status_id`, `object_storage_config_id`, `target_screen`, `target_state_key`, `selected_source_mode`, `handoff_label`, `handoff_summary`, `handoff_supported`, `handoff_performed`, `screen3_state_updated`, `backend_request_created`, `source_access_performed`, `run_analysis_called`, `object_storage_called`, `local_file_read_performed`, `db_lookup_performed`, and `notes`.

## 3. IndexToScreen3HandoffValidation Object Shape

`IndexToScreen3HandoffValidation` contains `validation_id`, `handoff_id`, `valid`, `validation_status`, `source_mode`, `target_screen`, `source_status_ready`, `object_storage_metadata_valid`, `future_em_extract_placeholder`, `can_handoff`, `handoff_blocked`, `handoff_performed`, `screen3_state_updated`, `backend_request_created`, `denied_reasons`, `warnings`, `required_next_steps`, and `notes`.

## 4. IndexSourceEntryReadiness Object Shape

`IndexSourceEntryReadiness` contains `readiness_id`, `source_mode_entry_ready`, `source_status_ready`, `object_storage_config_metadata_ready`, `handoff_metadata_ready`, `handoff_performed`, `execution_performed`, `object_storage_called`, `local_file_read_performed`, `db_lookup_performed`, `run_analysis_called`, `future_em_extract_placeholder`, `phase8_implemented`, `denied_reasons`, `warnings`, `required_next_steps`, and `notes`.

## 5. Handoff Statuses

Supported statuses are `VALID_METADATA_ONLY`, `INVALID`, `NEEDS_SOURCE_MODE`, `NEEDS_SOURCE_STATUS`, `NEEDS_OBJECT_STORAGE_METADATA`, `FUTURE_EM_EXTRACT_PLACEHOLDER`, and `HANDOFF_NOT_ALLOWED_IN_THIS_PHASE`.

## 6. Validation Rules

Validation requires supported source modes, `target_screen=screen_3`, matching selected source mode, and boolean safety flags. Validation rejects `handoff_performed=true`, `screen3_state_updated=true`, `backend_request_created=true`, `source_access_performed=true`, `run_analysis_called=true`, `object_storage_called=true`, `local_file_read_performed=true`, `db_lookup_performed=true`, `can_handoff=true`, `handoff_blocked=false`, and `phase8_implemented=true`.

## 7. Serialization Rules

Serialization uses plain dictionaries with local metadata only. Deserialization rebuilds dataclass instances and re-applies validation. Serialization does not update Screen 3 state, call backend, call object storage, read files, query DB, or call run_analysis.py.

## 8. Deterministic ID Rules

Handoff IDs are deterministic from source mode and target screen. Validation IDs are deterministic from handoff IDs. Readiness IDs are deterministic from a context label.

## 9. Runtime Safety Rules

Phase 7BT never performs active handoff, browser state mutation, backend request creation, source access, object storage calls, file reads, DB lookup, run_analysis.py calls, execution, EM Extract, or Phase 8 sizing/TCO.

## 10. Non-Goals

The model does not perform active handoff, update browser URL/hash/localStorage state, modify Screen 3 selected state at runtime, add form submit behavior, call fetch/XMLHttpRequest, call backend, call run_analysis.py, call object storage, read files, query DB, execute source intake, create backend requests, execute analysis, implement object storage access, implement EM Extract, mutate Phase 4I, change parser/scoring/decision/recommendation behavior, or implement Phase 8 sizing/TCO.

## 11. Acceptance Criteria

The model is accepted when all supported source modes validate as metadata-only, future EM Extract returns `FUTURE_EM_EXTRACT_PLACEHOLDER`, object storage requires configuration metadata, `can_handoff=false`, `handoff_blocked=true`, Screen 3 state update remains false, backend request creation remains false, serialization round trips, deterministic IDs are stable, unsafe flags are rejected, future EM Extract remains Phase 8, and Phase 8 sizing/TCO is not implemented.
