# Phase 7CE Dashboard Output Refresh Model

## Object Shapes

`DashboardRefreshRequestEnvelope` contains the refresh execution id, source execution id, source execution type, optional workflow request id, idempotency key, transaction group id, actor id, actor audit context, Phase 4I reference, dashboard reference, comparison reference, Object Storage reference, refresh mode, renderer requested flag, dry-run flag, validation reference, rollback reference, creation timestamp, and notes.

`DashboardRefreshValidation` contains the validation id, refresh execution id, validity flag, validation status, source execution presence, Phase 4I reference presence, renderer presence, refresh capability, blocked state, denied reasons, warnings, required next steps, dashboard regeneration flag, output write flag, safety flags, and notes.

`RegeneratedDashboardArtifactReference` contains the dashboard artifact id, refresh execution id, artifact type, artifact reference, summary, optional output path, renderer name, renderer version, dashboard generation flag, output write flag, overwrite flag, generated timestamp, and notes.

`Phase4IPayloadReference` contains the Phase 4I reference id, source execution id, payload reference, payload summary, payload version, Phase 4I contract preserved flag, Phase 4I mutation flag, and notes.

`DashboardRefreshResult` contains refresh status, validation metadata, optional Phase 4I payload reference, optional dashboard artifact reference, output artifact persistence flags, workflow persistence flags, idempotent replay flag, dashboard regeneration and output write flags, safety flags, denied reasons, warnings, required next steps, and notes.

## Refresh Statuses

Supported refresh statuses are `dry_run_only`, `blocked_no_renderer`, `blocked_missing_phase4i_reference`, `metadata_persisted`, `linked_existing_dashboard`, `regenerated_with_injected_renderer`, `validation_response_persisted`, `error_artifact_persisted`, `idempotent_replay`, and `failed_safely`.

## Refresh Modes

Supported refresh modes are `metadata_only`, `link_existing_dashboard`, `regenerate_with_renderer`, `validation_response_only`, and `error_artifact_only`. `metadata_only` persists references. `link_existing_dashboard` links an existing dashboard reference. `regenerate_with_renderer` requires an injected renderer. `validation_response_only` records validation metadata. `error_artifact_only` records safe error metadata.

## Renderer Contract

The renderer is injected. It may expose `validate_render_input(payload_reference)` and must expose `render_dashboard(payload_reference, output_reference)` for regeneration mode. Renderer output is a dictionary that may include `artifact_reference`, `dashboard_reference`, `artifact_summary`, `output_path`, `renderer_name`, `renderer_version`, `dashboard_generated`, `output_written`, `overwrite_performed`, and `generated_at`. Renderer output is rejected if it reports run_analysis.py, parser, scoring, recommendation, Object Storage, subprocess, or Phase 4I mutation.

## Repository Behavior

The governed workflow repository persists transaction, request, validation, audit, `phase4i_payload_reference`, `dashboard_artifact_reference`, `comparison_artifact`, `object_storage_load_artifact`, `validation_response`, and `error_artifact` metadata as applicable. Repeated idempotency keys return `idempotent_replay` and skip renderer calls.

## Safety Flags

Results enforce `phase4i_mutated=false`, `run_analysis_called=false`, `parser_invoked=false`, `scoring_invoked=false`, `recommendation_invoked=false`, and `object_storage_called=false`. Dashboard regeneration and output written flags may be true only when an injected renderer reports successful controlled generation.

## Idempotency

Idempotency is evaluated before renderer invocation. A replay does not call the renderer, does not write output, and does not create duplicate workflow records.

## Deterministic IDs

`create_dashboard_refresh_execution_id(source_execution_id, idempotency_key)` creates stable refresh ids. `create_dashboard_refresh_validation_id`, `create_phase4i_payload_reference_id`, and `create_dashboard_artifact_reference_id` create stable validation, Phase 4I reference, and dashboard artifact reference ids.

## Non-Goals

Phase 7CE does not call run_analysis.py, import dashboard rendering modules at import time, call parser/scoring/decision/recommendation modules, call Object Storage, read AWR files, read Object Storage contents, query DB report content, mutate Phase 4I, overwrite dashboards silently, regenerate dashboards by default, commit generated dashboard HTML, activate Screen 3 UI buttons, implement EM Extract, or implement Phase 8.
