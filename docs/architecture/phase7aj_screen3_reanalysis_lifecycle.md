# Phase 7AJ Screen 3 Backend Re-Analysis Lifecycle

## 1. Purpose

Phase 7AJ defines the future lifecycle boundary for Screen 3 backend re-analysis.

This lifecycle is documentation-only. No lifecycle stage is implemented in 7AJ. The lifecycle describes the stages that future 7AK-7AO work must satisfy before Screen 3 can safely move from read-only selection to a governed backend re-analysis control plane.

## 2. Lifecycle Overview

Future Screen 3 backend re-analysis must move through controlled lifecycle stages:

1. Read-only selection
2. User action
3. Actor identification
4. Backend execution mode declaration
5. Governed write-path validation
6. Request validation
7. Source validation
8. Deterministic execution
9. Controlled adaptive execution when explicitly gated
10. Output artifact handling
11. Dashboard refresh handling
12. Error or failure handling
13. Audit trail recording
14. Closure

No lifecycle stage is implemented in 7AJ.

## 3. Read-Only Selection Stage

The lifecycle begins with existing Screen 3 read-only selection state. A reviewer may select AWR/run context, database/system context, snapshot context, comparison baseline, issue domain, severity/status, source mode context where displayed, and execution mode context in a future UI.

Read-only selection is not execution. It does not call backend code, load sources, write records, refresh artifacts, mutate Phase 4I, change dashboard behavior, or change deterministic runtime truth.

## 4. User Action Stage

Future execution requires explicit user action. A future action may be `analyze_selection`, `rerun_analysis`, `build_comparison`, or `load_from_object_storage`.

Selection alone cannot trigger this stage. A future button or action control must be deliberate, visible, and governed, but no buttons or action controls are added in 7AJ.

## 5. Actor Identification Stage

Future execution cannot skip actor.

The actor identification stage must bind the request to Phase 7AE actor/reviewer identity metadata before execution validation proceeds. Browser state, URL state, local storage state, selected card state, and source metadata cannot substitute for actor identity.

Phase 7AJ does not implement actor identification.

## 6. Backend Execution Mode Stage

Future execution must declare backend execution mode before validation.

A future request must identify whether the action is static/read-only, local command generation, local backend execution, or future API/server execution using Phase 7AF execution mode metadata.

Phase 7AJ does not add execution mode UI, execution mode handling, command generation, API routes, or backend execution.

## 7. Governed Write-Path Stage

Future execution must pass governed write-path validation from Phase 7AG before creating run records, validation artifacts, refreshed payload references, dashboard artifact references, comparison artifacts, error artifacts, or audit outputs.

Future execution cannot skip validation. Future execution cannot skip output artifact tracking. Future writes cannot be performed directly from a dashboard click.

Phase 7AJ does not perform governed writes.

## 8. Request Validation Stage

The request validation stage must validate future selected state, requested action, actor identity, execution mode, source mode, required fields, target artifact class, Phase 4I preservation, deterministic fallback, Phase 7AA gate posture when adaptive execution is requested, and failure behavior.

Future execution cannot skip validation. Invalid requests must fail safely and must not alter parser/scoring/decision/recommendation behavior, Phase 4I payloads, dashboard artifacts, or runtime state.

Phase 7AJ does not implement a request model or request validator.

## 9. Source Validation Stage

The source validation stage must validate existing-run, local source, and object storage source references before execution.

Object storage cannot be loaded without explicit validation. Local source references cannot be trusted without validation. Comparison cannot be built without validated sources.

Phase 7AJ does not implement source selection, source validation, local file loading, object storage loading, OCI calls, network calls, or object storage calls.

## 10. Deterministic Execution Stage

Deterministic execution is the default future execution posture.

Future deterministic execution may call backend analysis only after explicit action, actor identity, execution mode declaration, governed write-path validation, request validation, source validation, and output lifecycle planning.

Phase 7AJ does not execute deterministic analysis, call `run_analysis.py`, create run records, refresh Phase 4I, regenerate dashboards, or modify deterministic runtime behavior.

## 11. Controlled Adaptive Execution Stage

Controlled adaptive execution is optional future behavior and requires explicit gate validation.

Future adaptive execution cannot bypass 7AA gate. Future adaptive execution must preserve deterministic fallback, declare adaptive intent, validate actor and request metadata, pass governed write-path validation, record output artifacts, and keep Phase 4I contract protection intact.

Phase 7AJ does not activate adaptive runtime, apply adaptive scores, apply adaptive recommendations, modify parser behavior, or grant runtime influence.

## 12. Output Artifact Stage

Future execution must create traceable output metadata through the Phase 7AH output lifecycle.

Future outputs may include validation response, analysis run record, refreshed Phase 4I payload reference, regenerated dashboard artifact reference, comparison artifact, source validation artifact, object storage load artifact, or error artifact.

Future execution cannot skip output artifact tracking. Phase 7AJ does not write artifacts, regenerate dashboards, refresh payloads, or create comparison artifacts.

## 13. Dashboard Refresh Stage

Future dashboard refresh must be driven by validated output artifact metadata and must not silently replace dashboard truth.

Dashboard refresh may later show a message, link to a run record, link to an artifact, request a regenerated dashboard, or use a future live refresh mode only after governed execution has completed.

Phase 7AJ does not change dashboard behavior and does not refresh any dashboard.

## 14. Error / Failure Stage

Invalid, incomplete, unauthorized, unsupported, unavailable, failed, or unsafe requests must fail safely.

Future failures must not mutate parser/scoring/decision/recommendation behavior, Phase 4I, dashboard artifacts, CLI behavior, database records, or runtime truth. Future failures should produce validation/error artifact metadata after a request enters a governed path.

Missing metrics must affect validation/confidence later. Missing metric handling is not implemented in 7AJ.

## 15. Audit Trail Stage

Future Screen 3 backend actions require audit trail coverage.

Audit trail metadata must identify actor, action, selected state reference, source mode, source references, execution mode, validation status, governed write-path result, output artifact references, error artifact references where applicable, deterministic fallback posture, Phase 7AA gate posture when adaptive execution is requested, and closure state.

Phase 7AJ does not create audit records.

## 16. Forbidden Shortcuts

Forbidden shortcuts include:

- executing from selection alone
- skipping explicit user action
- skipping actor identity
- skipping backend execution mode declaration
- skipping governed write-path validation
- skipping request validation
- skipping source validation
- loading object storage without validation
- building comparison without validated sources
- bypassing Phase 7AA gate for adaptive execution
- silently mutating Phase 4I
- silently regenerating dashboards
- writing directly from Screen 3 state
- calling `run_analysis.py` from dashboard state
- modifying parser/scoring/decision/recommendation behavior
- implementing Phase 8 sizing/TCO inside Screen 3 re-analysis

## 17. Required Validation Evidence

Future validation evidence must prove actor identity is present, execution mode is declared, requested action is supported, selected state is complete, source mode is supported, source references are validated, governed write-path checks pass, output lifecycle tracking is planned, deterministic fallback remains available, Phase 4I contract is preserved or explicitly versioned, Phase 7AA gate is satisfied for controlled adaptive execution, object storage validation is complete before load, comparison sources are validated before comparison, and missing metrics affect validation/confidence later.

Phase 7AJ only validates that these lifecycle requirements are documented and that no execution behavior is introduced.

## 18. Acceptance Criteria

Phase 7AJ lifecycle acceptance requires this lifecycle document, explicit lifecycle stages, forbidden shortcut language, required validation evidence, boundary tests, optional inert local metadata if present, and README links.

Acceptance also requires:

- No lifecycle stage is implemented in 7AJ.
- Future execution cannot skip actor.
- Future execution cannot skip validation.
- Future execution cannot skip output artifact tracking.
- Future adaptive execution cannot bypass 7AA gate.
- Object storage cannot be loaded without explicit validation.
- Comparison cannot be built without validated sources.
- Missing metrics must affect validation/confidence later.
- No backend execution is added.
- No source selection implementation is added.
- No object storage calls are added.
- No run_analysis.py wiring is added.
- No Phase 4I mutation is added.
- No dashboard behavior is changed.
- No CLI behavior is changed.
- Deterministic runtime remains authoritative.
- Phase 8 sizing/TCO is not implemented.
