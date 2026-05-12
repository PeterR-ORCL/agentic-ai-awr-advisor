# Phase 7H Dashboard Interactivity Validation Matrix

## 1. Static Dashboard Compatibility

Validation purpose: prove the dashboard remains usable as static HTML. Validation method: inspect the embedded interactivity script and run dashboard generation smoke tests. Expected result: no server, router, React, Vue, npm, bundler, or external interactivity dependency is required. Related test or command: `tests/test_dashboard_interactivity_phase7h_acceptance.py`, `tests/test_dashboard_cross_screen_selection_propagation.py`, and a temp-dir dashboard generation smoke test.

## 2. Browser-Side State Only

Validation purpose: prove selection state is browser-side only. Validation method: inspect state helpers and boundary wording. Expected result: selection state uses URL hash/localStorage only and URL hash/localStorage state is not authoritative truth. Related test or command: `tests/test_dashboard_interactivity_phase7h_acceptance.py` and `tests/test_dashboard_cross_screen_selection_propagation.py`.

## 3. URL Hash Safety

Validation purpose: prove URL hash handling is bounded and safe. Validation method: inspect `parseHashState`, `updateHashState`, allowed state keys, value sanitization, and dynamic execution bans. Expected result: unknown keys are ignored, values are sanitized, and no eval or dynamic execution exists. Related test or command: `tests/test_dashboard_cross_screen_selection_propagation.py`.

## 4. Local Storage Safety

Validation purpose: prove localStorage is optional and bounded to selector values. Validation method: inspect namespaced storage key, try/catch guards, and persisted payload. Expected result: localStorage failure is safe and raw report content is not stored. Related test or command: `tests/test_dashboard_cross_screen_selection_propagation.py`.

## 5. No Backend/API Writes

Validation purpose: prove interactivity adds no backend writes. Validation method: scan dashboard source and embedded script for fetch, XMLHttpRequest, write endpoints, form posts, and backend persistence markers. Expected result: no backend writes, no API calls, no database writes, and no network calls. Related test or command: `tests/test_dashboard_interactivity_phase7h_acceptance.py`.

## 6. No Approval/Write Controls

Validation purpose: prove no write controls are present. Validation method: scan rendered/source markers for approval-control, write-control, data-learning-action, candidate status mutation controls, governance status mutation controls, parser update controls, knowledge update controls, materialize controls, activate controls, and apply controls. Expected result: no approval controls and no write controls. Related test or command: `tests/test_dashboard_interactivity_phase7h_acceptance.py`.

## 7. No Runtime Truth Mutation

Validation purpose: prove runtime truth remains authoritative and unchanged. Validation method: inspect boundary wording and runtime imports. Expected result: parser output, scoring, trend/anomaly, decision, recommendation, and Phase 4I output behavior are unchanged. Related test or command: `tests/test_dashboard_interactivity_phase7h_acceptance.py`, `tests/test_phase7_learning_boundary.py`, and `scripts/run_phase6_validation.py`.

## 8. Screen 1 Parser/Governance Boundary

Validation purpose: prove Screen 1 exploration is read-only. Validation method: inspect Screen 1 markers and guardrails. Expected result: no loader changes, parser output changes, unknown signal classification, governance state mutation, knowledge request mutation, or artifact materialization. Related test or command: `tests/test_dashboard_screen1_governance_parser_exploration.py`.

## 9. Screen 2 Diagnostic Truth Boundary

Validation purpose: prove Screen 2 exploration does not alter deterministic diagnosis. Validation method: inspect Screen 2 selectors and labels. Expected result: no diagnostic truth, primary issue, secondary issue, severity, confidence, evidence, or recommendation truth changes. Related test or command: `tests/test_dashboard_screen2_diagnostic_exploration.py`.

## 10. Screen 3 Control Center Boundary

Validation purpose: prove Screen 3 remains a read-only control center. Validation method: inspect selector metadata and summary labels. Expected result: selected state is exploratory only and does not change primary issue, severity, diagnostic truth, or recommendation truth. Related test or command: `tests/test_dashboard_screen3_control_center.py`.

## 11. Screen 4 Historical Truth Boundary

Validation purpose: prove Screen 4 exploration does not alter history. Validation method: inspect Screen 4 selectors and labels. Expected result: no historical truth changes, trend recalculation, anomaly reclassification, baseline mutation, or similarity recomputation. Related test or command: `tests/test_dashboard_screen4_historical_review_exploration.py`.

## 12. Screen 5 Recommendation Truth Boundary

Validation purpose: prove Screen 5 exploration does not alter recommendation truth. Validation method: inspect Screen 5 selectors and labels. Expected result: no recommendation truth, priority, rank, rationale, supporting evidence, action, outcome, feedback, or candidate status changes. Related test or command: `tests/test_dashboard_screen5_recommendation_action_exploration.py`.

## 13. Screen 6 Fleet/Governance/Semantic/Learning Boundary

Validation purpose: prove Screen 6 exploration remains non-mutating. Validation method: inspect Screen 6 selectors and labels. Expected result: no fleet posture, governance state, semantic authority, candidate status, diagnostic truth, recommendation truth, or artifact state changes. Related test or command: `tests/test_dashboard_screen6_fleet_governance_learning_exploration.py`.

## 14. Semantic Reviewer-Assist Boundary

Validation purpose: prove semantic context remains non-authoritative. Validation method: inspect labels and tests for semantic context boundaries. Expected result: semantic context remains reviewer-assist only, not diagnostic evidence, not historical evidence, not recommendation truth, and not runtime truth. Related test or command: `tests/test_semantic_candidate_context.py`, `tests/test_dashboard_learning_visibility.py`, and `tests/test_dashboard_interactivity_phase7h_acceptance.py`.

## 15. Learning Candidate Proposal/Review Boundary

Validation purpose: prove learning candidates are not activated. Validation method: inspect labels and learning tests. Expected result: learning candidates remain proposal/review context only, `runtime_influence=false`, `requires_human_review=true`, not diagnostic evidence, not recommendation truth, and candidate status is unchanged. Related test or command: `tests/test_learning_candidate_model.py`, `tests/test_learning_candidate_engine.py`, `tests/test_learning_governance_bridge.py`, and `tests/test_dashboard_interactivity_phase7h_acceptance.py`.

## 16. Cross-Screen Propagation Boundary

Validation purpose: prove propagation is browser-side only. Validation method: inspect URL hash/localStorage helpers, navigation state propagation, summary updates, selected state classes, and no backend calls. Expected result: propagation is read-only, exploratory only, browser-side only, and not authoritative truth. Related test or command: `tests/test_dashboard_cross_screen_selection_propagation.py`.

## 17. Runtime Import Isolation

Validation purpose: prove runtime paths do not import learning or dashboard interactivity due to Phase 7H. Validation method: inspect `run_analysis.py`, parser modules, scoring modules, decision engine, and recommendation engine imports. Expected result: parser/scoring/decision/recommendation paths do not import `src.learning` or dashboard interactivity helpers. Related test or command: `tests/test_dashboard_interactivity_phase7h_acceptance.py`.

## 18. Phase 7A-G Regression Preservation

Validation purpose: prove prior Phase 7 learning behavior remains intact. Validation method: run Phase 7A through Phase 7G unittest modules. Expected result: all Phase 7A-G tests pass. Related test or command: `tests/test_phase7_learning_boundary.py`, `tests/test_outcome_pattern_miner.py`, `tests/test_learning_candidate_model.py`, `tests/test_learning_candidate_engine.py`, `tests/test_semantic_candidate_context.py`, `tests/test_learning_governance_bridge.py`, and `tests/test_dashboard_learning_visibility.py`.

## 19. Phase 6 Regression Preservation

Validation purpose: prove Phase 6 memory and semantic boundaries remain intact. Validation method: run the Phase 6 validation script when the environment supports it. Expected result: Phase 6 validation passes with runtime isolation, semantic isolation, governance safety, and write discipline intact. Related test or command: `PYTHONPATH=. .venv/bin/python scripts/run_phase6_validation.py`.

## 20. Acceptance Criteria

Validation purpose: prove Phase 7H is complete. Validation method: run consolidated Phase 7H acceptance tests and the Phase 7H local validation script. Expected result: all required docs exist, all required tests exist, all safety boundaries are documented, all dashboard interactivity remains read-only and browser-side only, and no runtime truth mutation exists. Related test or command: `tests/test_dashboard_interactivity_phase7h_acceptance.py` and `python3 scripts/run_phase7h_dashboard_validation.py`.
