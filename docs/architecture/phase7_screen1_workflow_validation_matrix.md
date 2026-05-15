# Phase 7 Screen 1 Workflow Validation Matrix

## 1. Purpose

This document defines the consolidated validation matrix for Phase 7AU-7AY, the Screen 1 Ingestion / Parser Governance Workflow block. It certifies that the Screen 1 workflow is governed, local, deterministic, and bounded to metadata models plus disabled preview panels.

## 2. Scope

The validation scope covers 7AU boundary documentation and inert boundary metadata, 7AV source intake request and validation metadata, 7AW parser unknown review models and preview panel, 7AX knowledge artifact review models and preview panel, and the 7AY validation and readiness scripts.

## 3. Non-Goals

This matrix does not certify source intake execution, local file loading, object storage access, DB lookup, parser invocation, parser mutation, parser mapping creation, parser candidate creation, parser backlog creation, artifact approval/rejection execution, artifact materialization, Phase 4I mutation, Phase 8 EM Extract, or Phase 8 sizing/TCO.

## 4. Validation Categories

The validation script groups checks into workflow_boundary, source_intake, parser_unknown_review, parser_unknown_review_panel, knowledge_artifact_review, knowledge_artifact_review_panel, screen1_governance_exploration_regression, import_isolation, runtime_safety, and documentation.

## 5. 7AU Boundary Validation

7AU validation proves the Screen 1 workflow boundary exists, future workflow target types are documented, future workflow actions are documented, future workflow statuses are documented, and runtime paths do not import the boundary module. It also preserves the rule that no source intake occurs and no parser output changes occur.

## 6. 7AV Source Intake Validation

7AV validation proves source intake records are local metadata only. Source selection and source validation are not source loading. The model keeps `can_intake=false`, `intake_blocked=true`, and all execution flags false. No local files are read, no object storage calls are made, no DB lookup is made, parser is not invoked, and `run_analysis.py` is not called.

## 7. 7AW Parser Unknown Review Validation

7AW validation proves parser unknown review records, requests, mapping intents, backlog intents, and validation metadata remain local models/intents only. No parser unknown classification is persisted, no parser mapping is created, no parser candidate is created automatically, no parser backlog item is created, and no parser output changes occur.

## 8. 7AW Parser Unknown Review Panel Validation

The parser unknown review panel validation proves Screen 1 parser unknown controls are disabled and preview-only. The panel does not submit forms, issue fetch/XMLHttpRequest calls, invoke a backend, invoke the governed write path, classify parser unknowns, create mappings, create candidates, create backlog items, or mutate Phase 4I.

## 9. 7AX Knowledge Artifact Review Validation

7AX validation proves knowledge artifact review records, review requests, artifact decisions, candidate link intents, materialization link intents, and validation metadata remain local models/intents only. No artifact approval/rejection is executed, no artifact revision request is persisted, no candidate is created automatically, and no materialization occurs.

## 10. 7AX Knowledge Artifact Review Panel Validation

The knowledge artifact review panel validation proves Screen 1 artifact controls are disabled and preview-only. The panel does not submit forms, issue fetch/XMLHttpRequest calls, invoke a backend, invoke the governed write path, approve or reject artifacts, request revision for real, create candidates, create materialization artifacts, or mutate Phase 4I.

## 11. Screen 1 Exploration Regression

The Screen 1 governance/parser exploration regression confirms the existing read-only Screen 1 exploration remains available after adding preview panels. The validation confirms parser/source/artifact panels are preview-only and Screen 1 exploration remains non-authoritative.

## 12. Import Isolation Validation

Import isolation validation scans `run_analysis.py` and parser/scoring/decision/recommendation paths to confirm they do not import `screen1_parser_governance_boundary`, `screen1_source_intake`, `screen1_parser_unknown_review`, or `screen1_knowledge_artifact_review`.

## 13. Runtime Safety Validation

Runtime safety validation scans Screen 1 workflow modules and dashboard source for forbidden mutation functions and unsafe UI snippets. It confirms no source intake occurs, no parser unknown classification is persisted, no parser mapping/candidate/backlog item is created, no artifact approval/rejection is executed, no materialization occurs, and no parser output changes occur.

## 14. Phase 4I Boundary Validation

Phase 4I boundary validation requires all Screen 1 workflow metadata to remain non-authoritative and non-mutating. No parser/scoring/decision/recommendation behavior changes occur, and no Phase 4I payload mutation is introduced.

## 15. Phase 8 EM Extract Exclusion

Phase 8 EM Extract was not implemented. `future_em_extract` remains a placeholder source mode and has no execution adapter, no source loader, and no ingestion runtime.

## 16. Phase 8 Sizing/TCO Exclusion

Phase 8 sizing/TCO was not implemented. The Screen 1 workflow block adds no sizing calculations, no TCO model, no what-if advisory behavior, and no Phase 8 UI.

## 17. Documentation Validation

Documentation validation requires all 7AU-7AY architecture documents to exist and contain the required boundary language. The documentation set must state that Screen 1 workflow is governed, parser/source/artifact panels are preview-only, and deterministic runtime remains authoritative.

## 18. Phase 7 Regression

Broader Phase 7 regression is optional for this block-level check. It may be run by `run_phase7_screen1_workflow_readiness_check.py --include-phase7` when a broader release context is needed.

## 19. Phase 6 Regression

Phase 6 regression is optional for this block-level check. It may be run by `run_phase7_screen1_workflow_readiness_check.py --include-phase6` when a broader memory/governance regression context is needed.

## 20. Acceptance Criteria

Acceptance requires the validation script to pass, `screen1_workflow_ready=true`, source/parser/artifact UI to remain preview-only, no source intake to occur, no parser unknown classification to be persisted, no parser mapping/candidate/backlog item to be created, no artifact approval/rejection to be executed, no materialization artifact to be created, no parser output changes to occur, no Phase 4I mutation to occur, deterministic runtime to remain authoritative, Phase 8 EM Extract to remain unimplemented, and Phase 8 sizing/TCO to remain unimplemented.
