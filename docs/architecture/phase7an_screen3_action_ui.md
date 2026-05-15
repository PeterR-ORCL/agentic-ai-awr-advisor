# Phase 7AN Screen 3 Action UI

## 1. Purpose

Phase 7AN adds visible Screen 3 controls for future backend re-analysis actions while keeping the dashboard non-executing. The controls explain the future path for Analyze Selection, Re-run Analysis, Build Comparison, and Load From Object Storage.

## 2. Scope

The scope is dashboard presentation only: disabled/preview-only action cards, read-only request context, source-mode display, blocked status, and safety labels.

## 3. Non-Goals

Phase 7AN does not implement backend execution, backend validation, object storage access, local file loading, DB lookup, dashboard regeneration, Phase 4I mutation, CLI commands, missing metric handling, or Phase 8 sizing/TCO.

## 4. Action UI Is Not Execution

Action UI is not execution. All action controls are disabled/preview-only. There is no backend execution, no run_analysis.py call, no object storage call, no local file read, no DB lookup, and no Phase 4I mutation.

## 5. Analyze Selection Control

Analyze Selection is shown as a disabled/preview-only control. It can describe a future request, but it does not submit, execute, validate, or call backend code.

## 6. Re-run Analysis Control

Re-run Analysis is shown as a disabled/preview-only control. It does not call run_analysis.py and does not regenerate dashboard output.

## 7. Build Comparison Control

Build Comparison is shown as a disabled/preview-only control. Comparison is not triggered from the dashboard in Phase 7AN; the in-memory comparison engine remains the 7AM.1 model only.

## 8. Load From Object Storage Control

Load From Object Storage is shown as a disabled/preview-only control. It does not call object storage, validate credentials, list buckets, or download objects.

## 9. Disabled / Preview-Only Behavior

Controls are represented as inert UI cards with disabled/preview-only labels. There is no active submit behavior, no form POST, no fetch or XMLHttpRequest, and no API route.

## 10. Source Mode Display

Screen 3 displays future source modes: Local staged, Local file, Existing run, Object Storage, and Future EM Extract. Source selection is metadata only in this phase.

## 11. Request Preview

The request preview is read-only and shows selected AWR/run, database/system, snapshot, comparison baseline, issue domain, severity/status, source mode, execution mode, requested action placeholder, and blocked status. It does not claim execution occurred.

## 12. Runtime Truth Boundary

Deterministic runtime remains authoritative. Screen 3 action UI does not change parser, scoring, decision, recommendation, Screen 2 diagnostic truth, or Screen 5 recommendation truth.

## 13. Phase 4I Boundary

No Phase 4I mutation occurs in Phase 7AN. Any future refreshed payload must preserve or explicitly version the Phase 4I contract before it can be used.

## 14. Object Storage Boundary

Object Storage values are displayed as future metadata only. There is no object storage call, no credential validation, no bucket listing, and no object download.

## 15. Local File Boundary

Local staged and local file modes are display-only. There is no local file read, no open operation, no path validation, and no file content validation.

## 16. AWR / Report Comparison Boundary

AWR/report comparison is future 7AM.1 engine only and not triggered here. Phase 7AN does not build comparison artifacts or compare dashboard data.

## 17. Missing Metric / Evidence Boundary

Missing metric/evidence handling remains future 7AO.1 / 7AQ.1. Phase 7AN may mention this future requirement but does not implement it.

## 18. Relationship to 7AJ

7AJ defined the boundary that selection is not execution. 7AN exposes that boundary visibly in Screen 3.

## 19. Relationship to 7AK

7AK defined source selection metadata. 7AN displays source modes but does not implement source selection behavior.

## 20. Relationship to 7AL

7AL defined request metadata. 7AN shows a request preview but does not create an executable backend request.

## 21. Relationship to 7AM

7AM defined controller and comparison models. 7AN does not invoke the controller, does not execute analysis, and does not trigger comparison.

## 22. Relationship to Future 7AO

Future 7AO will validate/readiness-check the re-analysis control plane. Phase 7AN does not implement 7AO validation/readiness.

## 23. Relationship to Phase 8

Future EM Extract and sizing/TCO comparison belong to Phase 8. Phase 8 sizing/TCO is not implemented.

## 24. Acceptance Criteria

- Screen 3 shows Analyze Selection, Re-run Analysis, Build Comparison, and Load From Object Storage controls.
- All action controls are disabled/preview-only.
- No backend execution is added.
- No run_analysis.py call is added.
- No object storage call is added.
- No local file read is added.
- No DB lookup is added.
- No Phase 4I mutation occurs.
- Comparison is not triggered.
- EM Extract is placeholder only.
- Phase 8 sizing/TCO is not implemented.
