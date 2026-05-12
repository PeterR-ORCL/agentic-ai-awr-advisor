# Phase 7H Dashboard Interactivity Architecture

## 1. Purpose

Phase 7H defines static dashboard interactivity for the Agentic AI AWR Advisor. Dashboard interactivity is read-only, selections are exploratory only, selection state is browser-side only, and deterministic runtime truth remains authoritative.

## 2. Scope

Phase 7H covers browser-side dashboard state, selectable metadata, read-only exploration on Screens 1 through 6, and Cross-Screen Selection Propagation. It does not change parser output, diagnostic truth, historical truth, recommendation truth, governance state, candidate status, or any backend runtime behavior.

## 3. Completed Phase 7H Subtasks

Phase 7H.1 added the Dashboard Interactivity Foundation. Phase 7H.2 added Screen 3 Control Center. Phase 7H.3 added Screen 2 Diagnostic Exploration. Phase 7H.4 added Screen 4 Historical Review Exploration. Phase 7H.5 added Screen 5 Recommendation / Action Exploration. Phase 7H.6 added Screen 1 Governance / Parser Exploration. Phase 7H.7 added Screen 6 Fleet / Governance / Semantic / Learning Exploration. Phase 7H.8 added Cross-Screen Selection Propagation. Phase 7H.9 adds validation and documentation only.

## 4. Static Dashboard Compatibility

The dashboard remains static HTML. It requires no server, no backend session, no API service, no database connection, no network call, no React, no Vue, no npm package, and no bundler for interactivity. Static dashboard works without JavaScript because JavaScript is progressive enhancement only.

## 5. Browser-Side State Model

Selection state is browser-side only and consists of bounded string identifiers such as selected run, domain, recommendation, parser section, semantic item, learning candidate, or fleet group. URL hash/localStorage state is not authoritative truth.

## 6. URL Hash State

URL hash state allows static dashboard pages to carry selected values such as `selectedDomain=CPU`. Hash parsing accepts only supported keys, sanitizes selector values, ignores unknown keys, and never executes dynamic content.

## 7. Optional Local Storage State

Optional localStorage preserves the same supported state keys under a dashboard-specific key. It stores selector values only, not raw report content, diagnostic evidence, recommendations, semantic records, learning records, or backend truth.

## 8. Cross-Screen Selection Propagation

Cross-Screen Selection Propagation restores browser-side state on page load, updates selected summaries, marks matching controls with selected visual state, and preserves selected state across static dashboard navigation. It adds no backend writes, no API calls, no approval controls, no write controls, and no runtime activation.

## 9. Screen 1 Governance / Parser Exploration

Screen 1 selectors highlight existing source, parser, unknown signal, governance, knowledge request, and artifact context. They do not change loader behavior, parser output, parser diagnostics, unknown signal classification, governance state, knowledge requests, or artifact lifecycle state.

## 10. Screen 2 Diagnostic Exploration

Screen 2 selectors highlight deterministic diagnostic evidence already rendered on the page. They do not change diagnostic truth, primary issue, secondary issues, severity, confidence, evidence values, or recommendation truth.

## 11. Screen 3 Control Center

Screen 3 provides the primary read-only control center for AWR/run, database/system, snapshot, domain, severity, and baseline context. It does not switch backend output, recalculate diagnosis, change primary issue, change severity, or make selected state authoritative.

## 12. Screen 4 Historical Review Exploration

Screen 4 selectors highlight historical windows, trend metrics, anomalies, distributions, baselines, and similar-case context already rendered on the page. They do not change historical truth, recalculate trends, reclassify anomalies, change baselines, or recompute similarity results.

## 13. Screen 5 Recommendation / Action Exploration

Screen 5 selectors highlight existing recommendation, category, evidence, action, outcome, feedback, and related learning review context. They do not change recommendation truth, recommendation priority, recommendation rank, recommendation rationale, supporting evidence, action records, outcome records, feedback records, or candidate status.

## 14. Screen 6 Fleet / Governance / Semantic / Learning Exploration

Screen 6 selectors highlight existing fleet, governance, semantic reviewer-assist, learning candidate, outcome pattern, and action effectiveness context. They do not change fleet posture, governance state, semantic authority, learning candidate status, diagnostic truth, or recommendation truth.

## 15. Runtime Truth Boundary

Phase 7H does not change runtime truth. Parser output, feature vectors, scoring, trends, anomalies, decisions, recommendations, Phase 4I output, and deterministic dashboard truth remain authoritative.

## 16. Parser / Loader Boundary

Phase 7H does not change loader behavior, parser behavior, parser output, parser diagnostics, parser mappings, or unknown signal classification. It adds no parser update controls.

## 17. Diagnostic Truth Boundary

Phase 7H does not change diagnostic truth. Semantic context remains outside diagnostic evidence, learning candidates remain outside diagnostic evidence, governance status remains outside diagnostic evidence, and browser-side selected state is not diagnostic evidence.

## 18. Historical Truth Boundary

Phase 7H does not change historical truth. It does not recalculate trends, reclassify anomalies, change baselines, recompute similarity results, or convert semantic/learning context into historical evidence.

## 19. Recommendation Truth Boundary

Phase 7H does not change recommendation truth. It does not change recommendation text, priority, rank, rationale, supporting evidence, action state, outcome state, feedback state, or recommendation generation.

## 20. Governance State Boundary

Phase 7H does not change governance state. It does not approve, reject, revise, implement, validate, close, materialize, activate, or mutate governance records.

## 21. Semantic Context Boundary

Semantic context remains reviewer-assist only and non-authoritative. It is not diagnostic evidence, not historical evidence, not recommendation truth, and not runtime truth.

## 22. Learning Candidate Boundary

Learning candidates remain proposal/review context only. They are not diagnostic evidence, not recommendation truth, not runtime activated, and not automatically applied. Candidate status is unchanged, and Phase 7H does not change candidate status.

## 23. Approval / Write-Control Boundary

Phase 7H adds no approval controls, no write controls, no approval buttons, no reject buttons, no implement buttons, no validate buttons, no close buttons, no materialize buttons, no activate controls, and no apply controls.

## 24. Backend Persistence Boundary

Phase 7H adds no backend writes, no API calls, no database writes, no network calls, no backend persistence, no server-side session state, and no Phase 7I CLI learning commands.

## 25. Accessibility / Progressive Enhancement

Selectable elements expose selected visual state and selected metadata while keeping page content visible. JavaScript is progressive enhancement only; the core diagnostic, historical, recommendation, governance, semantic, and learning information remains visible in static HTML.

## 26. Non-Goals

Phase 7H does not implement runtime learning, autonomous adaptation, parser changes, scoring changes, decision changes, recommendation changes, governance transitions, candidate activation, semantic recall service calls, Oracle Agent Memory calls, backend persistence, write APIs, or Phase 7I CLI learning commands.

## 27. Operational Notes

Operators may use selected state to explore rendered dashboard context. The selected state is local, read-only, exploratory only, and not authoritative. Clearing URL hash/localStorage removes browser-side convenience state without changing any generated artifact or runtime record.

## 28. Acceptance Summary

Phase 7H is accepted when all Phase 7H.1 through Phase 7H.8 tests pass, the consolidated Phase 7H acceptance test passes, Phase 7A through Phase 7G tests pass, Phase 6 validation passes, no parser/scoring/decision/recommendation/runtime files are modified, no backend write paths exist, no approval controls exist, no runtime truth changes exist, and dashboard interactivity remains read-only and browser-side only.
