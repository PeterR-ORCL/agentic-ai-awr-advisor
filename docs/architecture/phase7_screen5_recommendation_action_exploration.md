# Phase 7H.5 Screen 5 Recommendation / Action Exploration

## 1. Purpose

Phase 7H.5 makes Screen 5 recommendation and action content explorable through read-only browser-side selectors. The selectors help a user highlight deterministic recommendation/action context already rendered on Screen 5 without changing recommendation truth.

Screen 5 is read-only. Selections are exploratory only. They do not change recommendation truth, recommendation priority, recommendation rank, recommendation rationale, supporting evidence, diagnostic truth, historical truth, action status, outcome status, feedback status, parser output, scoring, decisions, recommendations, Phase 4I output, semantic context, or learning candidate state. Screen 5 selection does not change recommendation truth, does not change recommendation priority, does not change recommendation rationale, does not change supporting evidence, and does not change diagnostic truth.

## 2. Scope

The scope is Screen 5 recommendation/action exploration only. Screen 5 may render read-only selectors for recommendations, recommendation domains, recommendation categories, deterministic supporting evidence groups, action context, outcome context, feedback context, and related learning candidate review context when deterministic or governed display data is available.

Selections may update browser-side selected state, selected styling, selected recommendation/action summary text, URL hash state, and optional local storage state through the Phase 7H.1 foundation.

## 3. Non-Goals

Phase 7H.5 does not implement Screen 1 governance/parser exploration, Screen 6 fleet/governance/semantic/learning exploration, full cross-screen propagation, or Phase 7I CLI learning commands.

It adds no backend writes, no approval controls, no write controls, no runtime activation, no parser changes, no scoring changes, no trend/anomaly changes, no decision changes, no recommendation generation changes, no recommendation ranking changes, no recommendation rationale changes, no Phase 4I contract changes, no API calls, no database calls, no network calls, no external frontend dependencies, no OCI dependency, no ADB dependency, no Oracle Agent Memory live dependency, no semantic recall service dependency, and no LLM calls.

## 4. Screen 5 Selector Categories

Screen 5 selector categories are recommendation, recommendation domain, recommendation category, supporting evidence link, action context, outcome context, feedback context, and related learning context.

If deterministic or governed display metadata is unavailable, Screen 5 shows a safe empty state. It does not invent recommendations, actions, outcomes, feedback records, candidate relationships, or evidence.

## 5. Recommendation Selector

The Recommendation Selector uses deterministic recommendation objects already available to Screen 5. It stores read-only browser-side state in `selectedRecommendation`.

Recommendation selection does not change recommendation truth, recommendation priority, recommendation rank, recommendation rationale, supporting evidence, action posture, or recommendation text.

## 6. Recommendation Domain Selector

The Recommendation Domain Selector includes CPU, IO, MEMORY, COMMIT, RAC, and ADG. It stores read-only browser-side state in `selectedDomain`.

Domain selection is read-only. It does not filter in a way that changes recommendation truth, does not alter evidence, and does not promote a domain into recommendation truth.

## 7. Recommendation Category Selector

The Recommendation Category Selector uses recommendation group titles or recommendation category metadata when present. It stores browser-side state in `selectedRecommendationCategory`.

Category selection is read-only. It does not change recommendation ranking, priority, rationale, category assignment, or recommendation truth.

## 8. Supporting Evidence Link Selector

The Supporting Evidence Link Selector uses deterministic evidence tie-back and validation focus groups already available to Screen 5. It stores browser-side state in `selectedRecommendationEvidence`.

Evidence selection is read-only. It does not change supporting evidence, evidence values, diagnostic truth, historical truth, recommendation truth, or recommendation rationale.

## 9. Action Context Selector

The Action Context Selector uses action context, action history, or already rendered posture guidance when present. It stores browser-side state in `selectedActionContext`.

Action context selection is read-only. It does not write action tracking records, mutate action status, or execute action workflows.

## 10. Outcome Context Selector

The Outcome Context Selector uses governed outcome context when present. It stores browser-side state in `selectedOutcomeContext`.

Outcome context selection is read-only. It does not write outcome records, mutate outcome status, or affect future learning candidates.

## 11. Feedback Context Selector

The Feedback Context Selector uses governed feedback context when present. It stores browser-side state in `selectedFeedbackContext`.

Feedback context selection is read-only. It does not write feedback records, mutate feedback status, or use feedback as recommendation evidence.

## 12. Related Learning Context Selector

The Related Learning Context Selector may show related learning candidate review context only when Screen 5 receives that governed display data. It stores browser-side state in `selectedLearningCandidate`.

Related learning context is review/proposal context only, not recommendation evidence, not automatically applied, and `runtime_influence=false`. It adds no approval, reject, implement, validate, close, activate, or apply controls.

## 13. Selected Recommendation / Action Summary

Screen 5 includes a visible selected recommendation/action summary labeled Read-only recommendation/action exploration. The summary is exploratory only and may be updated by browser-side JavaScript.

The summary states that selections do not change recommendation truth, do not change recommendation priority, do not change recommendation rationale, do not change supporting evidence, do not change diagnostic truth, and do not write backend records.

## 14. Safe Empty State Behavior

When a selector category has no deterministic or governed display data, Screen 5 renders safe wording such as no additional recommendation categories available in this static export, no action context available in this static export, no outcome context available in this static export, no feedback context available in this static export, selection is local and read-only, and recommendation output remains unchanged.

Safe empty states do not imply missing data is evidence. They do not fabricate recommendations, actions, outcomes, feedback, learning candidates, candidate relationships, or recommendation evidence.

## 15. URL Hash / Local State Behavior

Screen 5 uses Phase 7H.1 metadata hooks such as `data-dashboard-selectable`, `data-dashboard-select-type`, `data-dashboard-select-key`, `data-dashboard-select-id`, `data-dashboard-select-domain`, `data-dashboard-filter-key`, and `data-dashboard-filter-value`.

The foundation supports `selectedRecommendation`, `selectedDomain`, `selectedRecommendationCategory`, `selectedRecommendationEvidence`, `selectedActionContext`, `selectedOutcomeContext`, `selectedFeedbackContext`, and `selectedLearningCandidate` for Screen 5 exploration. URL hash and local storage state are browser-local only.

## 16. Runtime Truth Boundary

Screen 5 selections do not change runtime truth. Parser output, feature vectors, scoring, trends, anomalies, decisions, recommendations, Phase 4I output, and deterministic dashboard truth remain authoritative and unchanged.

No runtime learning is implemented.

## 17. Recommendation Truth Boundary

Screen 5 selections do not change recommendation truth. Browser-local selected state is not a recommendation source, recommendation rule, recommendation result, or recommendation update.

Recommendation text, recommendation objects, action posture, and recommendation conclusions remain deterministic output.

## 18. Recommendation Priority / Rationale Boundary

Screen 5 selections do not change recommendation priority and do not change recommendation rationale. They do not alter rank, category, confidence, rationale text, action text, next-step text, or ordering.

Selection only highlights existing recommendation/action context.

## 19. Supporting Evidence Boundary

Screen 5 selections do not change supporting evidence. They do not alter evidence values, evidence group labels, validation focus areas, diagnostic evidence, historical evidence, or evidence tie-back.

Learning candidates are not recommendation evidence. Semantic context is not recommendation evidence.

## 20. Diagnostic Truth Boundary

Screen 5 selections do not change diagnostic truth. They do not change primary issue, secondary issues, severity, confidence, evidence values, scoring, or Screen 2 diagnosis.

Diagnostic truth remains downstream of deterministic analysis only.

## 21. Learning Candidate Boundary

Learning candidates remain proposal/review context only. Screen 5 selectors do not approve, reject, implement, validate, close, activate, apply, materialize, rank for runtime use, or convert learning candidates into recommendation evidence.

Learning candidates are not recommendation evidence and are not automatically applied.

## 22. Semantic Context Boundary

Semantic context remains reviewer-assist only. Screen 5 selectors do not turn semantic recall, semantic candidate context, or semantic memory into recommendation evidence, recommendation truth, scoring input, diagnostic evidence, or runtime truth.

Semantic context is not recommendation evidence and cannot change confidence, status, diagnosis, recommendation, or governance state.

## 23. Action / Outcome / Feedback Write Boundary

Action/outcome/feedback selectors do not write or mutate records. They do not write action tracking records, do not write outcome tracking records, do not write feedback records, and do not mutate action, outcome, or feedback status.

Action, outcome, and feedback context remains governed display context only.

## 24. Approval / Write-Control Boundary

Phase 7H.5 adds no approval controls and no write controls. It adds no approval buttons, reject buttons, implement buttons, validate buttons, close buttons, activate buttons, apply buttons, form posts, database calls, network calls, API write endpoints, CLI learning commands, OCI writes, ADB writes, or Oracle Agent Memory writes.

No backend writes are added.

## 25. Cross-Screen Propagation Deferral

Full cross-screen propagation remains future 7H.8. Screen 5 may update URL hash and local browser state through the Phase 7H.1 foundation, but Screen 2, Screen 3, Screen 4, Screen 1, and Screen 6 do not react authoritatively to Screen 5 selections in Phase 7H.5.

## 26. Relationship to Phase 7H.1 Foundation

Phase 7H.5 uses the Phase 7H.1 read-only dashboard interactivity foundation. It uses browser-side state keys, selectable metadata hooks, selected styling, selected summary updates, URL hash state, and optional local storage state.

The foundation remains static-dashboard-compatible, dependency-free, read-only, and exploratory only.

## 27. Relationship to Phase 7H.2 Screen 3 Control Center

Phase 7H.2 Screen 3 Control Center remains read-only and exploratory. Phase 7H.5 does not make Screen 3 selections authoritative and does not implement cross-screen propagation from Screen 3 into Screen 5.

Both screens can store browser-local state through the same foundation, but deterministic runtime truth remains unchanged.

## 28. Relationship to Phase 7H.3 Screen 2 Diagnostic Exploration

Phase 7H.3 Screen 2 Diagnostic Exploration remains read-only and deterministic evidence-only. Phase 7H.5 does not alter Screen 2 diagnostic truth, primary issue, severity, confidence, or diagnostic evidence.

Recommendation/action exploration on Screen 5 does not convert Screen 5 state into Screen 2 diagnostic evidence.

## 29. Relationship to Phase 7H.4 Screen 4 Historical Review Exploration

Phase 7H.4 Screen 4 Historical Review Exploration remains read-only and deterministic historical-context-only. Phase 7H.5 does not alter Screen 4 historical truth, trend values, anomaly classifications, baseline values, or similarity results.

Recommendation/action exploration on Screen 5 does not convert Screen 5 state into Screen 4 historical evidence.

## 30. Relationship to Future 7H.6-7H.8 Work

Future Phase 7H.6 and Phase 7H.7 work may add additional read-only screen-specific selectors. Full cross-screen propagation remains future 7H.8.

Phase 7H.5 does not implement Screen 1 governance/parser exploration, Screen 6 fleet/governance/semantic/learning exploration, or full cross-screen propagation.

## 31. Validation Requirements

Validation must prove import and compile safety, Screen 5 recommendation/action exploration markers, selected recommendation/action summary markers, selector metadata for recommendation and recommendation/action categories, authoritative domain controls, required safety wording, absence of unsafe controls, absence of learning/semantic/governance recommendation evidence, absence of action/outcome/feedback mutation controls, absence of Screen 2 and Screen 4 truth drift, absence of 7H.6+ behavior, existing 7H.1 through 7H.4 preservation, documentation coverage, Phase 7A-G preservation, and Phase 6 validation preservation when available.

Tests must be deterministic and local only. They must not require a database, OCI, ADB wallet, Oracle Agent Memory, environment variables, network, current date/time, or write access outside temporary directories.

## 32. Acceptance Criteria

Phase 7H.5 is accepted when Screen 5 Recommendation/Action Exploration exists, Screen 5 has read-only recommendation/action selector controls, Screen 5 uses Phase 7H.1 foundation metadata hooks, Screen 5 includes selected recommendation/action summary, domain selectors include CPU, IO, MEMORY, COMMIT, RAC, and ADG, and recommendation/category/evidence/action/outcome/feedback/related-learning selectors exist where safe deterministic or governed display data is available or safe empty states are shown.

It is also accepted only if selections are browser-side and read-only, selections are exploratory only, no backend writes are added, no approval controls are added, no write controls are added, no runtime activation is added, recommendation truth is unchanged, recommendation priority and rank are unchanged, recommendation rationale is unchanged, supporting evidence is unchanged, diagnostic truth is unchanged, historical truth is unchanged, learning candidates are not recommendation evidence, semantic context is not recommendation evidence, action/outcome/feedback records are not mutated, learning candidates remain proposal/review context only, semantic context remains reviewer-assist only, full cross-screen propagation remains future 7H.8, no 7H.6+ screen-specific behavior is implemented, no runtime learning is implemented, deterministic runtime remains authoritative, and parser/scoring/decision/recommendation behavior is unchanged.
