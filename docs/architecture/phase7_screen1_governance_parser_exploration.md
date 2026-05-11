# Phase 7H.6 Screen 1 Governance / Parser Exploration

## 1. Purpose

Phase 7H.6 makes Screen 1 explorable through read-only dashboard selector metadata. It helps reviewers inspect source, run, parser, unknown-signal, governance, knowledge request, and artifact context that is already shown or safely available to the static dashboard.

Screen 1 is read-only. Selections are exploratory only. They do not change loader behavior, parser output, parser diagnostics, unknown signal classification, governance state, knowledge requests, artifacts, diagnostic truth, historical truth, recommendation truth, or runtime behavior.

The boundary wording is explicit: Screen 1 does not change parser output, does not classify unknown signals, does not approve mappings, does not materialize artifacts, does not change governance state, does not change diagnostic truth, and does not change recommendation truth.

## 2. Scope

The scope is a browser-side Screen 1 exploration surface. It may render selectable cards, update URL hash or local browser state through the Phase 7H.1 foundation, visually mark selected items, and update a selected governance/parser summary.

No backend writes are added. No approval controls are added. No write controls are added. No runtime activation is added.

## 3. Non-Goals

Phase 7H.6 does not implement Screen 6 fleet/governance/semantic/learning exploration, full cross-screen propagation, Phase 7I CLI learning commands, parser mapping updates, knowledge request creation, artifact materialization, runtime learning, or any parser/scoring/decision/recommendation behavior change.

It does not approve mappings, reject mappings, materialize artifacts, activate artifacts, classify unknown signals, or change governance state.

## 4. Screen 1 Selector Categories

Screen 1 selector categories are source/run, parser section, parser diagnostic, unknown signal, governance item, knowledge request, and artifact selectors. Each category is optional and appears only when deterministic or governed display data is available.

When data is unavailable, the dashboard displays safe empty states such as "No parser section selector available in this static export" and "Parser and governance output remains unchanged."

## 5. Source / Run Selector

The source/run selector highlights current AWR, run, or source file context where available. It stores `selectedAwr` or `selectedRun` through the Phase 7H.1 state foundation.

Selections do not change loader behavior, ingestion behavior, source files, current diagnostic target, or parser output.

## 6. Parser Section Selector

The parser section selector highlights parser section visibility already represented in Screen 1 parse confidence data. It stores `selectedParserSection`.

Selections do not change parser output, section recognition, section ordering, parser coverage, or any deterministic parser result.

## 7. Parser Diagnostic Selector

The parser diagnostic selector highlights existing parse confidence and parser status context. It stores `selectedParserDiagnostic`.

Selections do not change parser diagnostics, parse completeness, warning counts, unknown counts, or alias/fallback behavior.

## 8. Unknown Signal Selector

The unknown signal selector highlights existing unknown-signal groups or records from parser review visibility. It stores `selectedUnknownSignal`.

Selections do not classify unknown signals, approve unknown signals, reject unknown signals, map unknown signals, or change unknown-signal status.

## 9. Governance Item Selector

The governance item selector highlights existing read-only governance rows. It stores `selectedGovernanceItem`.

Selections do not approve mappings, reject mappings, change approval status, change review status, or change governance state.

## 10. Knowledge Request Selector

The knowledge request selector highlights existing knowledge request context if present in the static export. It stores `selectedKnowledgeRequest`.

Selections do not create/update knowledge requests, submit requests, close requests, approve requests, or modify governed memory records.

## 11. Artifact Selector

The artifact selector highlights existing knowledge artifact context if present in the static export. It stores `selectedArtifact`.

Selections do not materialize artifacts, activate artifacts, update artifacts, validate artifacts, or convert artifacts into runtime behavior.

## 12. Selected Governance / Parser Summary

Screen 1 includes a selected governance/parser summary labeled "Read-only governance/parser exploration." The summary is exploratory only and browser-local.

The summary states that there are no backend writes, no approval controls, no runtime activation, no parser output changes, no unknown signal classification, no artifact materialization, no governance state changes, no diagnostic truth changes, and no recommendation truth changes.

## 13. Safe Empty State Behavior

If selector metadata is unavailable, Screen 1 renders empty states rather than inventing parser, governance, knowledge request, or artifact data.

Safe empty states state that selection is local and read-only and that parser and governance output remains unchanged.

## 14. URL Hash / Local State Behavior

Screen 1 uses the Phase 7H.1 foundation for URL hash and optional local storage state. Supported keys include `selectedAwr`, `selectedRun`, `selectedParserSection`, `selectedParserDiagnostic`, `selectedUnknownSignal`, `selectedGovernanceItem`, `selectedKnowledgeRequest`, and `selectedArtifact`.

Hash and local storage changes are browser-side only. They do not write to a backend, database, API, parser store, memory store, or artifact store.

## 15. Runtime Truth Boundary

Selections do not change runtime truth. Deterministic runtime remains authoritative.

No runtime learning was implemented. Phase 7H.6 does not alter parser/scoring/decision/recommendation behavior.

## 16. Loader Boundary

Selections do not change loader behavior. They do not load files, skip files, retry files, change file manifests, or change ingestion status.

## 17. Parser Output Boundary

Selections do not change parser output. They do not change parser sections, parser diagnostics, parse completeness, parser mappings, feature vectors, or Phase 4I output.

## 18. Parser Unknown Signal Boundary

Selections do not classify unknown signals. They do not approve mappings, reject mappings, implement mappings, validate mappings, close mappings, or update unknown-signal review state.

## 19. Governance State Boundary

Selections do not change governance state. Governance review remains read-only on the dashboard, and all governance transitions remain outside Screen 1 interactivity.

## 20. Knowledge Request Boundary

Selections do not create/update knowledge requests. They do not submit, approve, reject, revise, validate, close, or activate knowledge requests.

## 21. Artifact Materialization Boundary

Selections do not materialize artifacts. They do not activate artifacts, update artifact lifecycle state, or use artifacts as runtime truth.

## 22. Diagnostic Truth Boundary

Selections do not change diagnostic truth. Screen 1 governance/parser exploration does not become Screen 2 diagnostic evidence and does not alter primary issue, severity, confidence, scoring, trend, anomaly, or evidence values.

## 23. Recommendation Truth Boundary

Selections do not change recommendation truth. Screen 1 governance/parser exploration does not become Screen 5 recommendation evidence and does not alter recommendation text, priority, rank, rationale, or supporting evidence.

## 24. Learning / Semantic Boundary

Semantic/learning context is not parser evidence. Learning candidates remain proposal/review context only. Semantic context remains reviewer-assist only.

Screen 1 selections do not convert semantic recall, semantic candidate context, learning candidates, feedback, or recommendations into parser/governance truth.

## 25. Approval / Write-Control Boundary

Phase 7H.6 adds no approval controls and no write controls. It adds no approval buttons, reject buttons, implement buttons, validate buttons, close buttons, materialize buttons, activate buttons, apply controls, parser update controls, knowledge update controls, form posts, database calls, API write endpoints, network calls, OCI dependencies, ADB dependencies, Oracle Agent Memory live dependencies, semantic recall service dependencies, LLM calls, or CLI learning commands.

## 26. Cross-Screen Propagation Deferral

Full cross-screen propagation remains future 7H.8. Screen 1 may update browser-side selection state now, but other screens do not react authoritatively to Screen 1 selections in Phase 7H.6.

## 27. Relationship to Phase 7H.1 Foundation

Phase 7H.6 uses the Phase 7H.1 read-only foundation, including supported state keys, selector metadata hooks, URL hash state, optional local storage state, selected styling, and selected summary updates.

## 28. Relationship to Phase 7H.2 Screen 3 Control Center

Screen 3 remains a read-only control center. Phase 7H.6 does not make Screen 3 authoritative over Screen 1 and does not implement cross-screen propagation.

## 29. Relationship to Phase 7H.3 Screen 2 Diagnostic Exploration

Screen 2 remains deterministic diagnostic exploration only. Screen 1 selections do not become diagnostic evidence and do not change diagnostic truth.

## 30. Relationship to Phase 7H.4 Screen 4 Historical Review Exploration

Screen 4 remains deterministic historical context exploration only. Screen 1 selections do not change historical truth, trends, anomalies, baselines, or similarity results.

## 31. Relationship to Phase 7H.5 Screen 5 Recommendation / Action Exploration

Screen 5 remains deterministic/governed recommendation/action context exploration only. Screen 1 selections do not change recommendation truth or action/outcome/feedback records.

## 32. Relationship to Future 7H.7-7H.8 Work

Future Phase 7H.7 may add read-only Screen 6 fleet/governance/semantic/learning exploration. Full cross-screen propagation remains future 7H.8.

Phase 7H.6 does not implement Screen 6 fleet/governance/semantic/learning selector behavior or full cross-screen propagation.

## 33. Validation Requirements

Validation must prove import and compile safety, Screen 1 governance/parser exploration markers, selected governance/parser summary markers, selector metadata for parser/governance categories, required safety wording, absence of unsafe controls, absence of parser/governance mutation, absence of semantic/learning parser evidence, absence of Screen 2, Screen 4, and Screen 5 truth drift, absence of 7H.7+ behavior, existing 7H.1 through 7H.5 preservation, documentation coverage, Phase 7A-G preservation, and Phase 6 validation preservation when available.

Tests must be deterministic and local only. They must not require a database, OCI, ADB wallet, Oracle Agent Memory, environment variables, network, current date/time, or write access outside temporary directories.

## 34. Acceptance Criteria

Phase 7H.6 is accepted when Screen 1 Governance / Parser Exploration exists, Screen 1 has read-only governance/parser selector controls, Screen 1 uses Phase 7H.1 metadata hooks, Screen 1 includes selected governance/parser summary, source/run/parser/unknown/governance/knowledge/artifact selectors exist where safe deterministic or governed data is available, safe empty states appear when metadata is unavailable, and selections remain browser-side and read-only.

It is also accepted only if selections are exploratory only, no backend writes are added, no approval controls are added, no write controls are added, no runtime activation is added, loader behavior is unchanged, parser output is unchanged, unknown signals are not classified, governance state is unchanged, knowledge requests are not created/updated, artifacts are not materialized, diagnostic truth is unchanged, historical truth is unchanged, recommendation truth is unchanged, semantic/learning context is not parser evidence, learning candidates remain proposal/review context only, semantic context remains reviewer-assist only, full cross-screen propagation remains future 7H.8, no 7H.7+ screen-specific behavior is implemented, no runtime learning is implemented, deterministic runtime remains authoritative, and parser/scoring/decision/recommendation behavior is unchanged.
