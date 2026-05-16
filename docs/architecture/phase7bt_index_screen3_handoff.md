# Phase 7BT Index to Screen 3 Selection Handoff

## 1. Purpose

Phase 7BT defines a metadata-only handoff model from the dashboard index/source mode entry point to future Screen 3 source selection state. It completes the Phase 7BQ-7BT Index / Source Mode Entry Point block.

## 2. Scope

This phase adds local deterministic handoff metadata, handoff validation metadata, block readiness metadata, optional preview-only index handoff visibility, validation/readiness scripts, tests, and documentation.

## 3. Non-Goals

Phase 7BT does not perform active handoff, update browser URL/hash/localStorage state, update Screen 3 selected state, create backend requests, call backend, call run_analysis.py, call object storage, read files, query DB, execute source intake, execute analysis, implement object storage access, implement EM Extract, or implement Phase 8 sizing/TCO.

## 4. Handoff Is Not Execution

Handoff is not execution. No handoff is performed. No Screen 3 state is updated. No backend request is created. No source access occurs. No object storage call occurs. No file read occurs. No DB lookup occurs. No run_analysis.py call occurs.

## 5. IndexToScreen3Handoff

`IndexToScreen3Handoff` records the source mode, source entry metadata reference, source status reference, optional object storage config reference, target screen, target state key, selected source mode, labels, and safety flags for a future handoff. All active behavior flags remain false in Phase 7BT.

## 6. IndexToScreen3HandoffValidation

`IndexToScreen3HandoffValidation` records metadata validity, validation status, source status readiness, object storage metadata readiness, future EM Extract placeholder state, denied reasons, warnings, and required next steps. `can_handoff=false` and `handoff_blocked=true` in Phase 7BT.

## 7. IndexSourceEntryReadiness

`IndexSourceEntryReadiness` certifies the 7BQ-7BT block as metadata-only. It records that source mode entry, source status, object storage configuration metadata, and handoff metadata are present while handoff, execution, object storage calls, file reads, DB lookup, and run_analysis.py calls are not performed.

## 8. Supported Source Modes

Supported source modes are `local_staged`, `local_file`, `existing_run`, `object_storage`, `future_upload`, and `future_em_extract`.

## 9. Handoff Statuses

Supported handoff statuses are `VALID_METADATA_ONLY`, `INVALID`, `NEEDS_SOURCE_MODE`, `NEEDS_SOURCE_STATUS`, `NEEDS_OBJECT_STORAGE_METADATA`, `FUTURE_EM_EXTRACT_PLACEHOLDER`, and `HANDOFF_NOT_ALLOWED_IN_THIS_PHASE`.

## 10. Screen 3 Target Boundary

The only valid target screen is `screen_3`. Phase 7BT records a future target but does not navigate to Screen 3, update Screen 3 selectors, update browser selection state, or create a backend Screen 3 request.

## 11. Source Access Boundary

No source access occurs. The model records `source_access_performed=false`, `local_file_read_performed=false`, `db_lookup_performed=false`, and `run_analysis_called=false`.

## 12. Object Storage Boundary

Object storage handoff metadata may reference object storage configuration metadata, but no object storage call occurs, no bucket is listed, no object is downloaded, and no credential validation is performed.

## 13. Future EM Extract Boundary

future_em_extract is a placeholder only. Future EM Extract belongs to Phase 8. Phase 7BT does not implement EM Extract or Phase 8 sizing/TCO.

## 14. Relationship to 7BQ

Phase 7BQ defined the index source mode entry point. Phase 7BT consumes that vocabulary as metadata only and does not change the 7BQ preview-only boundary.

## 15. Relationship to 7BR

Phase 7BR defined source status metadata. Phase 7BT may reference source status metadata readiness but does not perform source status checks or source access.

## 16. Relationship to 7BS

Phase 7BS defined object storage configuration metadata validation. Phase 7BT may require object storage config metadata for object_storage handoff metadata, but it does not call object storage.

## 17. Relationship to Future Screen 3 Active Execution

Future Screen 3 active execution may use actor identity, backend execution mode, governed write path, output lifecycle, source validation, and controlled request generation. Phase 7BT implements none of that active behavior.

## 18. Relationship to Phase 8

EM Extract belongs to Phase 8. Phase 8 sizing/TCO is not implemented.

## 19. Acceptance Criteria

Phase 7BT is accepted when handoff metadata, handoff validation metadata, and block readiness metadata exist; no handoff is performed; no Screen 3 state is updated; no backend request is created; no source access occurs; no object storage call occurs; no file read occurs; no DB lookup occurs; no run_analysis.py call occurs; future EM Extract remains Phase 8; Phase 8 sizing/TCO is not implemented; and 7BQ-7BT validation/readiness passes.
