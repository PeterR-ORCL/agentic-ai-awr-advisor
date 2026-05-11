# Phase 7H.2 Screen 3 Control Center

## 1. Purpose

Phase 7H.2 turns Screen 3 into the first read-only dashboard control center. It uses the Phase 7H.1 browser-side interactivity foundation to let users make exploratory selections in a static dashboard export.

Screen 3 is read-only. Selections are exploratory only. They do not change diagnostic truth, recommendation truth, primary issue, severity, parser output, scoring, decisions, recommendations, Phase 4I output, governed memory state, semantic context, or learning candidate state.

## 2. Scope

The scope is Screen 3 selector rendering only. Screen 3 may render selectable cards for current AWR/run context, database/system context, snapshot context, issue domain, severity/status, comparison baseline, and available fleet/comparison context.

Selections may update browser-side selection state, URL hash state, optional local storage state, selected styling, and selected-state summary text through the Phase 7H.1 foundation.

## 3. Non-Goals

Phase 7H.2 does not implement Screen 2 diagnostic exploration, Screen 4 historical exploration, Screen 5 recommendation/action exploration, Screen 1 governance/parser exploration, Screen 6 fleet/governance/semantic/learning exploration, full cross-screen propagation, or CLI learning commands.

It adds no backend writes, no approval controls, no write controls, no runtime activation, no parser changes, no scoring changes, no trend/anomaly changes, no decision changes, no recommendation changes, no Phase 4I contract changes, no external frontend dependencies, no API calls, no database calls, no OCI dependency, no ADB dependency, no Oracle Agent Memory live dependency, no semantic recall service dependency, and no LLM calls.

## 4. Screen 3 Selector Categories

Screen 3 selector categories are AWR/run, database/system, snapshot, issue domain, severity/status, comparison baseline, and fleet/comparison context where safe metadata is available.

If a category lacks export metadata, Screen 3 shows a safe empty state such as no additional AWR choices available in this static export or no comparison baseline data is available in this static export. It does not fabricate specific AWR IDs, run IDs, snapshots, severity, or diagnostic truth.

## 5. AWR / Run Selector

The AWR / Run selector stores browser-side state in `selectedAwr` or `selectedRun` when current export metadata includes a safe AWR or run identifier.

The selector is read-only. It does not load another AWR, re-run analysis, write to memory, or change backend truth.

## 6. Database / System Selector

The Database / System selector stores browser-side state in `selectedDb` or `selectedSystem` using available DB name, DBID, host, and instance metadata.

Selection does not change parser output, scoring, topology detection, platform detection, selected scope, or deterministic diagnosis.

## 7. Snapshot Selector

The Snapshot selector stores browser-side state in `selectedSnapshot` using available snapshot labels or current latest/worst/window summary metadata.

Selection does not change selected-scope evidence. It does not re-window the deterministic analysis.

## 8. Issue Domain Selector

The Issue Domain selector includes CPU, IO, MEMORY, COMMIT, RAC, and ADG as fixed authoritative domain choices for exploratory selection state.

Selection does not change primary issue. It does not recalculate evidence, alter domain scores, change the dominant issue, or promote contextual domains into diagnostic truth.

## 9. Severity / Status Selector

The Severity / Status selector stores browser-side state in `selectedSeverity` when current status, display severity, or severity score metadata exists.

Selection does not change severity. It does not change risk state, health state, severity score, decision posture, or recommendation urgency.

## 10. Comparison Baseline Selector

The Comparison Baseline selector stores browser-side state in `selectedComparisonBaseline` using available comparison window, latest interval, worst interval, latest-vs-prior, or comparison mode metadata.

If no baseline data exists, Screen 3 shows a safe empty state. Baseline selection does not change historical proof or deterministic comparison conclusions.

## 11. Selected State Summary

Screen 3 includes a visible selected-state summary labeled Read-only selection state. The summary is exploratory only and may be updated by browser-side JavaScript.

The summary must clearly state no backend writes, does not change diagnostic truth, does not change recommendation truth, selection does not change primary issue, selection does not change severity, no approval controls, no write controls, and no runtime activation.

## 12. URL Hash / Local State Behavior

Screen 3 uses Phase 7H.1 metadata hooks such as `data-dashboard-selectable`, `data-dashboard-select-type`, `data-dashboard-select-key`, `data-dashboard-select-id`, `data-dashboard-select-domain`, `data-dashboard-filter-key`, and `data-dashboard-filter-value`.

The Phase 7H.1 foundation may update URL hash state and optional local storage state. That browser-side state is not backend state and does not mutate embedded diagnostic data.

## 13. Runtime Truth Boundary

Screen 3 selections do not change runtime truth. Parser output, feature vectors, scoring, trends, anomalies, decisions, recommendations, Phase 4I output, and deterministic dashboard truth remain authoritative and unchanged.

No runtime learning is implemented.

## 14. Diagnostic Evidence Boundary

Selections do not change diagnostic truth. Screen 3 selections do not convert selected domains, semantic context, learning candidates, fleet context, historical comparison context, or browser-local state into diagnostic evidence.

Screen 2 diagnostic evidence remains downstream of deterministic runtime analysis only.

## 15. Recommendation Truth Boundary

Selections do not change recommendation truth. Screen 3 selections do not convert selected domains, severity markers, semantic context, learning candidates, fleet context, or browser-local state into recommendation truth.

Screen 5 recommendation truth remains downstream of deterministic recommendations only.

## 16. Learning / Semantic Boundary

Learning candidates remain proposal/review context only. Screen 3 does not approve, reject, implement, validate, close, activate, apply, materialize, or rank learning candidates for runtime use.

Semantic context remains reviewer-assist only. Screen 3 does not display semantic recall as diagnostic evidence and does not convert semantic context into recommendation truth.

## 17. Approval / Write-Control Boundary

Phase 7H.2 adds no approval controls and no write controls. It adds no approval buttons, reject buttons, implement buttons, validate buttons, close buttons, activate buttons, apply buttons, form posts, API write endpoints, database writes, network writes, CLI learning commands, OCI writes, ADB writes, or Oracle Agent Memory writes.

No backend writes are added.

## 18. Cross-Screen Propagation Deferral

Cross-screen propagation remains future Phase 7H.8. Screen 3 may update browser-side URL hash/local state now, but full behavior across screens remains future 7H.8.

Phase 7H.2 does not make Screen 2, Screen 4, Screen 5, Screen 1, or Screen 6 react to Screen 3 selections.

## 19. Relationship to Phase 7H.1 Foundation

Phase 7H.1 provided the read-only dashboard interactivity foundation. Phase 7H.2 is the first screen-specific use of that foundation.

Screen 3 uses the foundation metadata hooks and selected-state summary conventions without introducing backend writes, runtime activation, or authoritative truth mutation.

## 20. Relationship to Future 7H.3-7H.8 Work

Future Phase 7H.3 through Phase 7H.7 may add screen-specific exploratory behavior for other screens. Full cross-screen propagation remains future 7H.8.

Phase 7H.2 does not implement 7H.3+ screen behavior.

## 21. Validation Requirements

Validation must prove import and compile safety, Screen 3 Control Center markers, selected-state summary markers, selector metadata hooks, authoritative domain choices, safety labels, absence of unsafe controls, absence of Screen 2 and Screen 5 truth drift, absence of 7H.3+ implementation, and documentation boundary phrases.

Tests must be deterministic and local only. They must not require a database, OCI, ADB wallet, Oracle Agent Memory, environment variables, network, current date/time, or writes outside temporary directories.

## 22. Acceptance Criteria

Phase 7H.2 is accepted when Screen 3 has read-only selector controls, uses Phase 7H.1 metadata hooks, includes a visible selected-state summary, includes CPU, IO, MEMORY, COMMIT, RAC, and ADG domain controls, includes safe AWR/run/system/snapshot/status/baseline selectors where metadata exists or empty states where metadata is unavailable, and preserves all runtime truth boundaries.

It is accepted only if selections are exploratory only, no backend writes are added, no approval controls are added, no write controls are added, no runtime activation is added, diagnostic truth is unchanged, recommendation truth is unchanged, primary issue is unchanged, severity is unchanged, learning candidates remain proposal/review context only, semantic context remains reviewer-assist only, full cross-screen propagation remains future 7H.8, no 7H.3+ screen behavior is implemented, deterministic runtime remains authoritative, and parser/scoring/decision/recommendation behavior is unchanged.
