# Phase 7AJ Screen 3 Backend Re-Analysis Boundary

## 1. Purpose

Phase 7AJ defines the architecture boundary for future Screen 3 backend re-analysis in the Agentic AI AWR Advisor project.

This phase is boundary-only. It documents how Screen 3 may later become a governed backend re-analysis control plane without changing current dashboard behavior, backend runtime truth, or Phase 4I contracts.

Selection is not execution. A selected AWR, run, database, snapshot, baseline, issue domain, severity/status filter, source mode, or execution mode cannot run analysis by itself.

## 2. Scope

The scope is documentation, lifecycle definition, validation tests, and optional inert local boundary metadata for future Screen 3 backend re-analysis.

Phase 7AJ defines:

- what Screen 3 backend re-analysis means
- what selected state can be submitted later
- what future actions may exist
- what future source modes will be supported
- what validation must happen before execution
- how execution mode is governed
- how deterministic and controlled adaptive execution modes are separated
- how future output artifacts must be handled
- what shortcuts are forbidden

No dashboard behavior is changed.

## 3. Non-Goals

Phase 7AJ adds no Screen 3 buttons. No Screen 3 buttons are added.

Phase 7AJ adds no Analyze Selection button, Re-run Analysis button, Build Comparison button, Load From Object Storage button, dashboard forms, JavaScript backend calls, dashboard write controls, or dashboard submission behavior.

Phase 7AJ adds no backend execution. No backend execution is added.

Phase 7AJ adds no source selection implementation. No source selection implementation is added.

Phase 7AJ adds no object storage access, OCI SDK dependency, Object Storage SDK dependency, source fetch, local file loading, source upload, or network call. No object storage calls are added.

Phase 7AJ adds no `scripts/run_analysis.py` wiring. No run_analysis.py wiring is added.

Phase 7AJ adds no Phase 4I payload mutation. No Phase 4I mutation is added.

Phase 7AJ does not modify parser behavior, parser output, scoring behavior, decision behavior, recommendation behavior, database schema, generated dashboard HTML, dashboard reporting modules, CLI commands, or runtime entrypoints.

Phase 8 sizing/TCO is not implemented.

## 4. Why Screen 3 Needs Backend Re-Analysis

Screen 3 is the control center for selecting analysis context. It already exposes read-only selection concepts for AWR/run context, database/system context, snapshot context, comparison baseline, issue domain, severity/status, and source context where displayed.

Future Screen 3 backend re-analysis will let a reviewer intentionally submit a selected context to a governed backend path. That future path may analyze a selected run, rerun an existing analysis, build a comparison artifact, or load a source from object storage after validation.

This boundary exists so future Screen 3 selection can be useful without becoming an accidental execution path. Selection is browser-side context until an explicit action, actor identity, execution mode, source validation, governed write-path validation, and output lifecycle are present.

## 5. Existing Screen 3 Read-Only Boundary

Existing Screen 3 behavior remains read-only. It may track selected AWR/run, selected database/system, selected snapshot, selected comparison baseline, selected issue domain, selected severity/status, and displayed source context in browser-side state.

Existing Screen 3 selection does not load another AWR, rerun analysis, call backend code, write records, regenerate dashboards, modify deterministic diagnosis, change recommendation truth, update Phase 4I, or change runtime state.

Phase 7AJ preserves the existing read-only boundary.

## 6. Selection Is Not Execution

Selection is not execution.

Selected values are future request inputs only. They are not commands, approvals, writes, backend truth, diagnostic truth, recommendation truth, output artifacts, or runtime state.

Future execution requires explicit user action. Selecting values alone cannot call `run_analysis.py`, start backend execution, load local files, load object storage sources, build comparisons, refresh Phase 4I payloads, regenerate dashboards, or create run records.

## 7. Future Selected State

Future Screen 3 re-analysis may submit selected state fields such as:

- `selected_awr`
- `selected_run`
- `selected_database`
- `selected_system`
- `selected_snapshot`
- `selected_comparison_baseline`
- `selected_issue_domain`
- `selected_severity_status`
- `selected_source_mode`
- `selected_object_storage_reference`
- `selected_local_source_reference`
- `selected_execution_mode`

These fields are boundary concepts only in 7AJ. They are not implemented as a request model in this phase.

## 8. Future Actions

Future Screen 3 actions may include:

- `analyze_selection`
- `rerun_analysis`
- `build_comparison`
- `load_from_object_storage`

All are future actions. All require validation. All require actor identity before execution. All require backend execution mode declaration. None are implemented in 7AJ.

No Screen 3 buttons are added for these actions in Phase 7AJ.

## 9. Actor Requirement

Future backend actions require actor/reviewer identity from Phase 7AE.

A future Screen 3 backend re-analysis request cannot execute with only browser state, URL hash state, local storage state, selected card state, or anonymous metadata. Actor identity is required before a future action can enter validation for execution.

Phase 7AJ does not implement actor identity.

## 10. Backend Execution Mode Requirement

Future Screen 3 backend actions require a declared backend execution mode from Phase 7AF.

The future request must distinguish static/read-only intent, local command generation, local backend execution, and future API/server execution. Execution mode metadata must exist before validation can decide whether an action is allowed.

Phase 7AJ does not execute backend actions and does not add execution mode selection UI.

## 11. Governed Write-Path Requirement

Future Screen 3 backend actions require the governed write-path framework from Phase 7AG.

The future write path must validate request shape, actor identity, execution mode, source references, target artifact class, audit fields, output lifecycle, failure behavior, and Phase 4I protection before any write or execution output is accepted.

Phase 7AJ does not write files, write database records, update dashboard state, create audit records, or perform governed writes.

## 12. Output Lifecycle Requirement

Future Screen 3 backend actions require the output artifact lifecycle from Phase 7AH.

Future execution outputs may include validation response, new analysis run record, refreshed Phase 4I payload reference, regenerated dashboard artifact reference, comparison artifact, source validation artifact, object storage load artifact, or error artifact.

Phase 7AJ does not create output artifacts, write output files, regenerate dashboards, refresh payloads, or update dashboard artifacts.

## 13. Source Mode Boundary

Future source modes must be explicitly selected and validated before execution.

The expected future source modes include existing-run context, local source context, and object storage source context. Source mode is not a shortcut to execution. The selected source mode must be compatible with selected state, actor identity, execution mode, governed write path, and output lifecycle.

Phase 7AJ defines source mode boundaries only. It does not implement source selection.

## 14. Local Source Boundary

Future local source handling may allow a validated local reference to be analyzed or compared.

Local source references must not be trusted solely because they appear in Screen 3 state. A future local source path must validate the reference, supported file type, provenance, permissions, request shape, execution mode, actor, and output expectations before execution.

Phase 7AJ does not add local file loading, path selection, upload handling, file parsing, or analysis execution.

## 15. Object Storage Boundary

Future object storage handling may allow a validated object storage reference to be loaded.

Object storage cannot be loaded without explicit validation. A future object storage path must validate object reference shape, tenancy or namespace context where applicable, bucket/object identity, permissions, actor, execution mode, source compatibility, output lifecycle, and failure behavior before execution.

Phase 7AJ does not add object storage calls, OCI calls, Object Storage SDK dependencies, network access, credential handling, or object loading.

## 16. Deterministic Execution Boundary

Deterministic execution is default.

Future Screen 3 backend re-analysis must preserve deterministic runtime as authoritative unless a later certified path explicitly allows controlled adaptive consideration. Deterministic execution must remain available as the fallback and baseline for future validation, comparison, and dashboard refresh.

Phase 7AJ does not change deterministic parser, scoring, decision, recommendation, trend, anomaly, or output behavior.

## 17. Controlled Adaptive Execution Boundary

Controlled adaptive execution requires gate.

Future controlled adaptive execution requires explicit execution mode, actor identity, request validation, governed write-path validation, output lifecycle tracking, deterministic fallback, and Phase 7AA gate validation.

Phase 7AJ does not activate adaptive runtime, apply adaptive scoring, apply adaptive recommendation behavior, modify parser output, bypass Phase 7AA, or grant runtime influence.

## 18. Phase 4I Contract Boundary

The Phase 4I output contract must be preserved.

Any future refreshed payload must preserve the existing Phase 4I contract or use an explicitly versioned and validated contract. Screen 3 selected state cannot silently mutate Phase 4I, parser output, scoring output, decisions, recommendations, dashboard payload shape, or generated artifacts.

No Phase 4I mutation is added in Phase 7AJ.

## 19. AWR / Report Comparison Future Requirement

AWR/report comparison is future 7AM.1.

Future Phase 7AM.1 must define an AWR / Report Comparison Engine that can compare:

- two or more AWR reports
- selected run contexts
- before/after performance posture
- score changes
- waits
- SQL concentration
- trends
- anomalies
- data difference versus option, target, or platform difference
- output comparison artifact

Phase 7AJ does not implement the comparison engine and does not build comparison artifacts.

## 20. Missing Metric / Evidence Availability Future Requirement

Missing metric handling is future 7AO.1 / 7AQ.1.

Future missing metric and evidence availability handling must cover:

- metric unavailable
- metric absent from AWR
- metric unsupported by topology or platform
- parser did not extract it
- value present but not reliable
- missing metric affects confidence
- missing metric creates candidate for parser/source review

Phase 7AJ does not implement missing metric handling, evidence availability scoring, confidence adjustment, parser review creation, or source review creation.

## 21. Runtime Truth Boundary

Deterministic runtime remains authoritative.

Screen 3 re-analysis boundary metadata is not runtime truth. Future selected state, future requested actions, source mode metadata, validation metadata, comparison plans, and output references do not change parser, scoring, decision, recommendation, trend, anomaly, Phase 4I, dashboard, or memory truth by themselves.

No autonomous runtime changes are introduced.

## 22. Relationship to 7AD-7AI

Phase 7AD-7AI established the dashboard workflow infrastructure:

- 7AD defined workflow boundaries.
- 7AE defined actor/reviewer identity metadata.
- 7AF defined backend execution mode metadata.
- 7AG defined governed write-path metadata.
- 7AH defined output artifact lifecycle metadata.
- 7AI validated the workflow infrastructure block.

Phase 7AJ uses those boundaries as prerequisites for future Screen 3 backend re-analysis. It does not replace them and does not activate a workflow.

## 23. Relationship to Future 7AK

Future 7AK may define the source selection model for local and object storage modes.

Phase 7AJ only states that source mode must be selected and validated later. It does not implement source selection, local file references, object storage references, source loading, or object storage access.

## 24. Relationship to Future 7AL

Future 7AL may define the backend re-analysis request model.

Phase 7AJ only lists future selected state fields and future actions as boundary concepts. It does not implement a request model, serialization contract, API payload, command payload, or request validation engine.

## 25. Relationship to Future 7AM

Future 7AM may define the backend re-analysis execution controller.

Phase 7AJ does not execute analysis, call `run_analysis.py`, call backend adapters, create run records, refresh Phase 4I, regenerate dashboards, write artifacts, or dispatch execution.

## 26. Relationship to Future 7AM.1

Future 7AM.1 may define the AWR / Report Comparison Engine.

Phase 7AJ documents comparison as a first-class future action only. It does not compare AWR reports, compare runs, compute before/after posture, calculate score changes, compare waits, compare SQL concentration, compare trends or anomalies, or produce comparison artifacts.

## 27. Relationship to Future 7AN

Future 7AN may add Screen 3 submit/action UI.

Phase 7AJ adds no UI buttons, no forms, no JavaScript backend calls, no dashboard action handlers, no submission controls, and no dashboard write controls.

## 28. Relationship to Future 7AO

Future 7AO may add re-analysis validation and readiness for the 7AJ-7AO block.

Phase 7AJ adds focused boundary tests only. It does not add block readiness, full execution validation, source validation, comparison validation, or dashboard refresh validation.

## 29. Relationship to Future 7AO.1 / 7AQ.1

Future 7AO.1 and 7AQ.1 may define missing metric, evidence availability, and missing metric review behavior.

Phase 7AJ documents that missing metrics must later affect validation and confidence. It does not implement missing metric handling, evidence availability modeling, confidence adjustment, parser/source review candidates, or review workflow behavior.

## 30. Relationship to Phase 8

Phase 8 sizing/TCO is not implemented.

Screen 3 backend re-analysis is not a sizing engine, TCO workflow, what-if advisory workflow, capacity model, cost model, or Phase 8 feature. Future re-analysis outputs must not be treated as Phase 8 sizing or TCO advice unless Phase 8 explicitly defines and validates those contracts later.

## 31. Acceptance Criteria

Phase 7AJ is accepted when Screen 3 re-analysis boundary documentation exists, Screen 3 re-analysis lifecycle documentation exists, boundary validation tests exist, optional local boundary metadata is inert if present, README links are updated, and existing related workflow infrastructure tests still pass.

Acceptance requires:

- Phase 7AJ is boundary-only.
- No Screen 3 buttons are added.
- No backend execution is added.
- No source selection implementation is added.
- No object storage calls are added.
- No run_analysis.py wiring is added.
- No Phase 4I mutation is added.
- No dashboard behavior is changed.
- No CLI behavior is changed.
- Selection is not execution.
- Deterministic execution is default.
- Controlled adaptive execution requires gate.
- Deterministic runtime remains authoritative.
- AWR/report comparison is future 7AM.1.
- Missing metric handling is future 7AO.1 / 7AQ.1.
- Phase 8 sizing/TCO is not implemented.
