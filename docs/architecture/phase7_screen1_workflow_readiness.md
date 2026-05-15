# Phase 7 Screen 1 Workflow Readiness

## 1. Purpose

This document defines readiness criteria for Phase 7AU-7AY, the Screen 1 Ingestion / Parser Governance Workflow block.

## 2. Readiness Scope

Readiness covers the Screen 1 workflow boundary, source intake metadata, parser unknown review metadata and preview panel, knowledge artifact review metadata and preview panel, import isolation, runtime safety, documentation completeness, and optional broader Phase 7 or Phase 6 regression.

## 3. Completed Subphases

The completed subphases are 7AU Screen 1 Ingestion / Parser Governance Workflow Boundary, 7AV Source Intake Control Model, 7AW Parser Unknown Review UI / Workflow, 7AX Knowledge Artifact Review Workflow, and 7AY Screen 1 Workflow Validation / Certification.

## 4. Readiness Categories

Readiness categories are workflow_boundary, source_intake, parser_unknown_review, parser_unknown_review_panel, knowledge_artifact_review, knowledge_artifact_review_panel, screen1_governance_exploration_regression, runtime_isolation, documentation_complete, phase7_regression, and phase6_regression.

## 5. Boundary Readiness

Boundary readiness requires the 7AU boundary and lifecycle documents to remain present, the inert boundary module to remain local-only, and runtime parser behavior to remain authoritative.

## 6. Source Intake Readiness

Source intake readiness requires 7AV request, validation, and preview metadata to remain deterministic and non-executing. Source intake is not performed. No local files are read, no object storage calls are made, no DB lookup is made, parser is not invoked, and `run_analysis.py` is not called.

## 7. Parser Unknown Review Readiness

Parser unknown review readiness requires 7AW review records, review requests, parser mapping intents, parser backlog intents, and validation objects to remain local models/intents only. No parser unknown classification is persisted and no parser mapping/candidate/backlog item is created.

## 8. Knowledge Artifact Review Readiness

Knowledge artifact review readiness requires 7AX review records, review requests, artifact decisions, candidate link intents, materialization link intents, and validation objects to remain local models/intents only. No artifact approval/rejection is executed, no revision request is persisted, no candidate is created automatically, and no materialization artifact is created.

## 9. Screen 1 Preview Panel Readiness

Screen 1 workflow is governed and preview-only at the UI layer. Parser/source/artifact panels are preview-only, controls are disabled, and no form POST, fetch, XMLHttpRequest, API call, backend execution, or governed write-path execution is added.

## 10. Runtime Isolation Readiness

Runtime isolation readiness requires `run_analysis.py` and parser/scoring/decision/recommendation paths to avoid importing Screen 1 workflow modules. Parser runtime remains authoritative, deterministic runtime remains authoritative, and no Phase 4I mutation occurs.

## 11. Documentation Readiness

Documentation readiness requires the validation matrix, readiness document, release certification, operational checklist, and architecture README links to exist and match the certified boundary.

## 12. Required Commands

Run `python3 scripts/run_phase7_screen1_workflow_validation.py` for the consolidated block validation. Run `python3 scripts/run_phase7_screen1_workflow_readiness_check.py` for readiness. JSON forms are available with `--json`.

## 13. Readiness Criteria

screen1_workflow_ready=true only when checks pass. The ready state requires no source intake, no local file read, no object storage call, no DB lookup, no parser invocation, no `run_analysis.py` call, no parser unknown classification persistence, no parser mapping/candidate/backlog item creation, no artifact approval/rejection execution, no materialization creation, no parser output change, no Phase 4I mutation, deterministic runtime authority, no Phase 8 EM Extract, and no Phase 8 sizing/TCO.

## 14. Screen 1 Workflow Ready Statement

When all required checks pass, Screen 1 workflow readiness is certified as `screen1_workflow_ready=true`. The Screen 1 workflow is governed and preview-only at the UI layer, source intake remains metadata only, parser unknown review remains intent-only, knowledge artifact review remains intent-only, parser runtime remains authoritative, and Phase 8 remains out of scope.
