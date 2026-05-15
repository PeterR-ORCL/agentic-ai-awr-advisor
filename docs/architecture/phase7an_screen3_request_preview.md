# Phase 7AN Screen 3 Request Preview

## 1. Purpose

The Phase 7AN request preview makes the future Screen 3 backend re-analysis request shape visible without executing, validating, writing, or calling backend services.

## 2. Request Preview Shape

The preview may show selected context, selected source mode, selected execution mode, requested action placeholder, and validation/blocked status. Request preview is not execution.

## 3. Selected State Display

Selected state display is read-only. It may include selected AWR/run, database/system, snapshot, comparison baseline, issue domain, and severity/status.

## 4. Source Mode Display

Source mode display may show Local staged, Local file, Existing run, Object Storage, and Future EM Extract. These values are presentation metadata only.

## 5. Execution Mode Display

Execution mode display is read-only and blocked in this phase. The default display remains static_read_only / execution disabled in this phase.

## 6. Action Preview Display

Action preview display may list Analyze Selection, Re-run Analysis, Build Comparison, and Load From Object Storage. It does not activate any action.

## 7. Validation / Blocked Status

The preview displays blocked status such as execution_blocked=true and can_execute=false. Request preview is not backend validation.

## 8. Safety Labels

Safety labels must state no backend execution, no run_analysis.py call, no object storage call, no local file read, no DB lookup, no Phase 4I mutation, deterministic runtime remains authoritative, controlled adaptive execution requires future validation/gate, AWR/report comparison is future 7AM.1 engine only and not triggered here, and missing metric/evidence handling remains future 7AO.1 / 7AQ.1.

## 9. Non-Goals

The request preview does not call backend, does not write, does not mutate runtime, does not call object storage, does not read files, does not query DB, does not regenerate dashboards, and does not implement Phase 8 sizing/TCO.

## 10. Acceptance Criteria

- Request preview is visible on Screen 3.
- Request preview is not execution.
- Request preview is not backend validation.
- Request preview does not call backend.
- Request preview does not write.
- Request preview does not mutate runtime.
- Invalid or empty selected state remains safely displayed as preview-only context.
