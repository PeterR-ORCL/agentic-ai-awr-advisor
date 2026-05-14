# Phase 7AH Output Artifact Model

## 1. Purpose

This document defines the Phase 7AH local output artifact and refresh
instruction object model. The model is deterministic, local-only, and metadata
only.

No file writes occur in Phase 7AH.

## 2. DashboardOutputArtifact Object Shape

`DashboardOutputArtifact` contains:

- `artifact_id`
- `artifact_type`
- `source_request_id`
- `source_validation_id`
- `source_audit_id`
- `run_id`
- `phase4i_reference`
- `dashboard_reference`
- `comparison_reference`
- `artifact_uri`
- `artifact_summary`
- `lifecycle_status`
- `validation_status`
- `error_summary`
- `created_by`
- `created_at`
- `output_written`
- `dashboard_regenerated`
- `phase4i_mutated`
- `runtime_mutation_performed`
- `notes`

The object describes an artifact reference. It does not create the artifact.

## 3. DashboardOutputRefreshInstruction Object Shape

`DashboardOutputRefreshInstruction` contains:

- `refresh_id`
- `artifact_id`
- `refresh_mode`
- `message`
- `link_target`
- `run_id`
- `dashboard_reference`
- `safe_to_display`
- `requires_manual_action`
- `refresh_performed`
- `notes`

The object describes a future display or link instruction. It does not execute
refresh.

## 4. Artifact Types

Supported artifact types are:

- `validation_response`
- `analysis_run_record`
- `phase4i_payload_reference`
- `dashboard_artifact_reference`
- `comparison_artifact`
- `error_artifact`
- `source_validation_artifact`
- `object_storage_load_artifact`
- `workflow_audit_artifact`
- `governance_review_artifact`
- `outcome_capture_artifact`

## 5. Refresh Modes

Supported refresh modes are:

- `no_refresh`
- `show_message`
- `link_to_artifact`
- `link_to_run`
- `regenerate_dashboard_requested`
- `future_live_refresh`

Refresh instructions are metadata only. `refresh_performed=false` is required.

## 6. Lifecycle Statuses

Supported lifecycle statuses are:

- `PROPOSED`
- `VALIDATED`
- `AVAILABLE`
- `FAILED`
- `SUPERSEDED`
- `CLOSED`

Lifecycle status is descriptive. It does not mean a file was written by 7AH.

## 7. Validation Rules

Artifact validation requires:

- `artifact_id` is present.
- `artifact_type` is supported.
- `artifact_summary` is present.
- `lifecycle_status` is supported.
- `output_written=false`.
- `dashboard_regenerated=false`.
- `phase4i_mutated=false`.
- `runtime_mutation_performed=false`.
- `error_artifact` includes `error_summary`.
- `phase4i_payload_reference` includes `phase4i_reference`.
- `dashboard_artifact_reference` includes `dashboard_reference`.
- `comparison_artifact` includes `comparison_reference`.
- `analysis_run_record` includes `run_id`.

Refresh instruction validation requires:

- `refresh_id` is present.
- `artifact_id` is present.
- `refresh_mode` is supported.
- `message` is present.
- `refresh_performed=false`.
- `link_to_run` includes `run_id`.
- `link_to_artifact` includes a link target or artifact id.
- `future_live_refresh` requires manual action.

## 8. Serialization Rules

Serialization converts dataclass metadata to dictionaries without side effects.
Deserialization rebuilds dataclass metadata and runs the same validation rules.
Round trips must remain deterministic.

## 9. Deterministic ID Rules

Artifact ids use:

`DASHBOARD-OUTPUT-<TYPE>-<REQUEST_OR_RUN>`

Refresh ids use:

`DASHBOARD-REFRESH-<ARTIFACT_ID>-<MODE>`

No random UUID, timestamp, DB sequence, or external service is used.

## 10. Safety Flags

The following flags must remain false:

- `output_written=false`
- `dashboard_regenerated=false`
- `phase4i_mutated=false`
- `runtime_mutation_performed=false`
- `refresh_performed=false`

Any true value is rejected in Phase 7AH.

## 11. Non-Goals

Phase 7AH does not write artifacts, does not regenerate dashboards, does not
mutate Phase 4I, does not execute refresh, does not call object storage, does
not execute backend requests, does not add dashboard UI, does not add CLI
behavior, and does not implement Phase 8.

## 12. Acceptance Criteria

- Output artifact model exists.
- Refresh instruction model exists.
- Artifact types are supported.
- Refresh modes are supported.
- Lifecycle statuses are supported.
- Safety flags remain false.
- Serialization helpers round trip deterministically.
- No file writes occur.
- Deterministic runtime remains authoritative.
