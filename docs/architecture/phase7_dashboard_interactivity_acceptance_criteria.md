# Phase 7H Dashboard Interactivity Acceptance Criteria

## 1. Acceptance Purpose

This document defines the final acceptance criteria for Phase 7H Dashboard Interactivity. Phase 7H is accepted only when interactivity is read-only, browser-side only, exploratory only, static-dashboard-compatible, free of backend writes, free of approval/write controls, free of runtime truth mutation, and separated from semantic reviewer-assist context and learning candidate activation.

## 2. Required Completed Subtasks

Phase 7H requires completed Phase 7H.1 Dashboard Interactivity Foundation, Phase 7H.2 Screen 3 Control Center, Phase 7H.3 Screen 2 Diagnostic Exploration, Phase 7H.4 Screen 4 Historical Review Exploration, Phase 7H.5 Screen 5 Recommendation / Action Exploration, Phase 7H.6 Screen 1 Governance / Parser Exploration, Phase 7H.7 Screen 6 Fleet / Governance / Semantic / Learning Exploration, and Phase 7H.8 Cross-Screen Selection Propagation.

## 3. Required Documentation

Required documentation includes the foundation doc, each screen-specific exploration doc, the cross-screen propagation doc, this acceptance criteria doc, the consolidated Phase 7H architecture doc, and the Phase 7H validation matrix.

## 4. Required Tests

Required tests include all Phase 7H.1 through Phase 7H.8 unittest modules and the consolidated `tests/test_dashboard_interactivity_phase7h_acceptance.py` module.

## 5. Required Validation Commands

Required validation commands include py_compile for the acceptance test, py_compile for any modified reporting module, the consolidated acceptance unittest, all Phase 7H.1 through Phase 7H.8 unittests, Phase 7A through Phase 7G unittests, the optional Phase 7H validation script when present, and Phase 6 validation when the environment supports it.

## 6. Required Runtime Isolation Evidence

Acceptance requires evidence that no parser/scoring/decision/recommendation/runtime files are modified for Phase 7H.9, parser/scoring/decision/recommendation paths do not import `src.learning` due to dashboard interactivity, and runtime paths do not import dashboard interactivity helpers.

## 7. Required Dashboard Safety Evidence

Acceptance requires evidence that dashboard interactivity remains read-only, selections are exploratory only, selection state is browser-side only, URL hash/localStorage state is not authoritative truth, no backend writes exist, no API calls exist, no approval controls exist, no write controls exist, and no runtime activation exists.

## 8. Required Semantic/Learning Boundary Evidence

Acceptance requires evidence that semantic context remains reviewer-assist only, learning candidates remain proposal/review context only, `runtime_influence=false` remains visible, `requires_human_review=true` remains visible, semantic context is not diagnostic evidence, semantic context is not recommendation truth, learning candidates are not diagnostic evidence, and learning candidates are not recommendation truth.

## 9. Required Cross-Screen Propagation Evidence

Acceptance requires evidence that cross-screen propagation is browser-side only, read-only, exploratory only, static-dashboard-compatible, hash/localStorage based, selected-summary based, visually selected-state based, and not authoritative truth.

## 10. Required Non-Goals Confirmation

Acceptance requires confirmation that Phase 7H.9 added validation/docs only; no new UI behavior was added; no new selectors were added; no backend writes were added; no API calls were added; no approval controls were added; no write controls were added; no runtime activation was added; no Phase 7I CLI learning commands were implemented; no runtime learning was implemented; and parser/scoring/decision/recommendation behavior is unchanged.

## 11. Required Git State

Before commit, the working tree should contain only expected Phase 7H.9 documentation, test, optional local validation script, and README changes. Parser, scoring, decision, recommendation, database schema, generated dashboard HTML, and runtime command files must remain unchanged.

## 12. Phase 7H Acceptance Statement

Phase 7H is accepted only if all 7H.1 through 7H.8 tests pass, the consolidated 7H acceptance test passes, Phase 7A-G tests pass, Phase 6 validation passes when run, no parser/scoring/decision/recommendation/runtime files are modified, no backend write paths exist, no approval controls exist, no runtime truth changes exist, and dashboard interactivity remains read-only and browser-side only. Parser output is unchanged, diagnostic truth is unchanged, historical truth is unchanged, recommendation truth is unchanged, governance state is unchanged, candidate status is unchanged, semantic context remains reviewer-assist only, learning candidates remain proposal/review context only, deterministic runtime remains authoritative, and Phase 7H does not implement Phase 7I CLI learning commands.
