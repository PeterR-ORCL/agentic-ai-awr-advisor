# Phase 7AF Dashboard Backend Execution Mode Boundary

## 1. Purpose

Phase 7AF defines the local dashboard backend execution mode boundary for future governed dashboard workflows.

Backend execution mode describes how a future workflow would execute. This phase does not execute backend actions.

## 2. Scope

The scope is supported backend execution modes, supported source modes, supported requested actions, execution request metadata, execution validation result metadata, execution safety boundaries, actor relationship, source mode relationship, runtime/adaptive request flags, deterministic identifiers, serialization/deserialization helpers, and validation rules.

The implementation is local, deterministic, standard-library-only except for allowed local actor identity metadata imports, and safe to import.

## 3. Non-Goals

Phase 7AF does not execute backend actions. It does not call run_analysis.py. It does not call parser, scoring, decision, recommendation, dashboard generation, object storage, network, OCI, ADB, Oracle Agent Memory, semantic recall, or LLM services.

Phase 7AF does not add API routes. It does not add dashboard buttons, dashboard forms, dashboard write controls, CLI commands, Screen 3 re-analysis behavior, source loading, governed write paths, output lifecycle behavior, database writes, file reads, file writes beyond requested source/docs/tests, or Phase 8 sizing/TCO.

No dashboard behavior is changed. No CLI behavior is changed. No parser/scoring/decision/recommendation behavior is changed. No Phase 4I contract change is made.

## 4. Why Backend Execution Modes Are Needed

Future Screen 3, Screen 1, Screen 2, Screen 5, Screen 6, and source-mode workflows need a shared execution boundary. Without it, each workflow could invent separate meanings for read-only exploration, manual command generation, local backend execution, future server execution, or object storage source handling.

Phase 7AF defines common execution semantics first and keeps all execution behavior future work.

## 5. Supported Execution Modes

Supported execution modes are:

- `static_read_only`
- `local_command_generation`
- `local_backend_execution`
- `future_api_server_execution`

`static_read_only` is the default. No mode executes anything in Phase 7AF.

## 6. Supported Source Modes

Supported source modes are:

- `none`
- `local_staged`
- `local_file`
- `existing_run`
- `object_storage`
- `future_upload`

`none` is valid for review-only workflows. `object_storage`, `local_file`, `local_staged`, and `future_upload` are metadata only in Phase 7AF.

## 7. Supported Requested Actions

Supported requested actions are:

- `read_only_view`
- `analyze_selection`
- `rerun_analysis`
- `build_comparison`
- `load_from_object_storage`
- `diagnostic_review`
- `parser_review`
- `recommendation_action`
- `outcome_capture`
- `governance_review`
- `materialization_review`
- `model_registry_review`
- `runtime_gate_review`

Actions are metadata only. No action executes in Phase 7AF.

## 8. Static Read-Only Mode

`static_read_only` represents current dashboard behavior. It supports read-only viewing and no backend execution.

Static read-only mode cannot request non-read-only execution behavior in Phase 7AF.

## 9. Local Command Generation Mode

`local_command_generation` describes a future mode where a dashboard workflow may generate a command for an operator to run manually.

Phase 7AF does not generate runnable commands and does not execute commands.

## 10. Local Backend Execution Mode

`local_backend_execution` is metadata only in Phase 7AF. local_backend_execution is metadata only. It describes a future local controller execution mode that may be considered after actor metadata, validation, audit, source validation, and future governed write-path controls exist.

Local backend execution is not implemented here.

## 11. Future API / Server Execution Mode

`future_api_server_execution` is metadata only in Phase 7AF. future_api_server_execution is metadata only. It describes a future server/API execution mode that may be considered after API routes, authorization, validation, audit, source validation, and future governed write-path controls exist.

Future API/server execution is not implemented here.

## 12. Object Storage Boundary

Object storage source mode is metadata only. This phase does not call object storage, does not call OCI, does not validate buckets, does not read objects, does not stage files, and does not load sources.

Object storage requests require future governed source validation before execution consideration.

## 13. Actor Requirement Boundary

Read-only view requests may omit actor metadata. Non-read-only actions require actor metadata through `actor_id` or actor audit context metadata.

Actor metadata comes from Phase 7AE. Actor metadata does not authorize execution by itself.

## 14. Audit Requirement Boundary

Non-read-only actions require audit metadata in future workflow paths. Phase 7AF records whether audit is required, but it does not create audit records and does not implement a write path.

## 15. Validation Boundary

Request validation is not execution. Validation can mark a request as valid for future execution consideration, invalid, needing actor metadata, needing source validation, unsupported, or read-only-only.

Validation never runs backend actions.

## 16. Runtime Truth Boundary

Deterministic runtime remains authoritative. Backend execution mode metadata does not modify parser output, scoring, decisions, recommendations, Phase 4I output, runtime gate state, generated dashboard HTML, or backend runtime behavior.

## 17. Phase 4I Boundary

Phase 7AF does not modify the Phase 4I output contract. Any future refreshed Phase 4I payload or regenerated dashboard artifact remains future 7AH or later work and must preserve or explicitly version the contract.

## 18. Relationship to 7AD

Phase 7AD defined that backend execution requires an explicit execution mode. Phase 7AF supplies the local metadata model for that boundary.

## 19. Relationship to 7AE

Phase 7AE supplies actor and actor audit context metadata. Phase 7AF can reference that metadata for non-read-only action requests, but actor metadata does not authorize execution by itself.

## 20. Relationship to Future 7AG

Future 7AG may define governed write-path and authorization behavior. Phase 7AF does not implement 7AG and does not authorize, persist, or execute requests.

## 21. Relationship to Future 7AH

Future 7AH may define output refresh and artifact lifecycle behavior. Phase 7AF does not create run records, refreshed Phase 4I payloads, regenerated dashboard artifacts, comparison artifacts, or error artifacts.

## 22. Relationship to Screen 3 Re-Analysis

Screen 3 re-analysis, analyze selection, build comparison, and load from object storage are future workflows. Phase 7AF only defines metadata to describe those requests.

## 23. Relationship to Phase 8

Phase 8 sizing/TCO is not implemented. Phase 7AF does not add sizing, TCO, what-if advisory, capacity planning, cost modeling, or sizing recommendation workflows.

## 24. Acceptance Criteria

Phase 7AF is accepted when backend execution mode metadata exists, backend execution request metadata exists, backend execution validation metadata exists, execution/source/action constants exist, deterministic id helpers exist, validation helpers exist, serialization/deserialization helpers exist, documentation exists, tests exist, this phase does not execute backend actions, this phase does not call run_analysis.py, this phase does not call object storage, this phase does not add API routes, this phase does not add dashboard buttons, local_backend_execution is metadata only, future_api_server_execution is metadata only, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
