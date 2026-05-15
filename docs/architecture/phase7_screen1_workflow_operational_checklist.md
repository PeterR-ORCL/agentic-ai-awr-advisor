# Phase 7 Screen 1 Workflow Operational Checklist

## 1. Purpose

This checklist defines operator validation steps for Phase 7AU-7AY Screen 1 Ingestion / Parser Governance Workflow certification.

## 2. Pre-Run Checklist

- Confirm the working branch is `phase7-screen1-parser-governance-workflow`.
- Confirm the working tree is clean before starting certification edits.
- Confirm no generated dashboard HTML is being modified.
- Confirm no parser, scoring, decision, recommendation, CLI, DB schema, or runtime files are in scope.

## 3. Validation Checklist

- Run `python3 scripts/run_phase7_screen1_workflow_validation.py`.
- Run `python3 scripts/run_phase7_screen1_workflow_validation.py --json`.
- Confirm the text output says `Phase 7 Screen 1 workflow validation passed.`
- Confirm JSON reports `screen1_workflow_ready=true`.

## 4. Source Intake Checklist

- Confirm source intake metadata tests pass.
- Confirm `source_intake_performed=false`.
- Confirm `local_file_read_performed=false`.
- Confirm `object_storage_called=false`.
- Confirm `db_lookup_performed=false`.
- Confirm `parser_invoked=false`.
- Confirm `run_analysis_called=false`.

## 5. Parser Unknown Review Checklist

- Run `python3 -m unittest tests/test_phase7aw_parser_unknown_review.py`.
- Confirm parser unknown review metadata remains local-only.
- Confirm `parser_unknown_classification_persisted=false`.
- Confirm `parser_mapping_created=false`.
- Confirm `parser_candidate_created=false`.
- Confirm `parser_backlog_item_created=false`.

## 6. Knowledge Artifact Review Checklist

- Run `python3 -m unittest tests/test_phase7ax_knowledge_artifact_review.py`.
- Confirm knowledge artifact review metadata remains local-only.
- Confirm `artifact_approval_executed=false`.
- Confirm `artifact_rejection_executed=false`.
- Confirm `materialization_created=false`.

## 7. Preview Panel Checklist

- Run `python3 -m unittest tests/test_dashboard_screen1_knowledge_artifact_review_panel.py`.
- Run parser unknown preview panel tests when validating the full block.
- Confirm parser/source/artifact panels are preview-only.
- Confirm controls are disabled.
- Confirm no form POST, fetch, XMLHttpRequest, API call, backend execution, or governed write-path execution exists.

## 8. Runtime Isolation Checklist

- Confirm `run_analysis.py` does not import Screen 1 workflow modules.
- Confirm parser/scoring/decision/recommendation paths do not import Screen 1 workflow modules.
- Confirm no active mutation functions exist.
- Confirm no parser output changes occur.
- Confirm no Phase 4I mutation occurs.

## 9. Documentation Checklist

- Confirm the validation matrix exists.
- Confirm the readiness document exists.
- Confirm release certification exists.
- Confirm this operational checklist exists.
- Confirm README links the Screen 1 workflow validation/readiness/certification/checklist documents.

## 10. Failure Handling

If validation fails, do not certify readiness. Inspect the failing validation group, fix only the scoped documentation/test/script issue, rerun the validation script, and rerun the readiness script. Do not use a failure as permission to add source intake, parser mutation, artifact approval, materialization, backend calls, or Phase 8 behavior.

## 11. Acceptance Checklist

- `python3 scripts/run_phase7_screen1_workflow_readiness_check.py` passes.
- `python3 scripts/run_phase7_screen1_workflow_readiness_check.py --json` passes.
- `screen1_workflow_ready=true`.
- `python3 -m unittest tests/test_phase7aw_parser_unknown_review.py` passes.
- `python3 -m unittest tests/test_phase7ax_knowledge_artifact_review.py` passes.
- `python3 -m unittest tests/test_dashboard_screen1_knowledge_artifact_review_panel.py` passes.
- Source intake was not performed.
- Parser unknown classification was not persisted.
- Parser mapping/candidate/backlog item was not created.
- Artifact approval/rejection was not executed.
- Materialization artifact was not created.
- Parser output was not changed.
- Phase 4I was not mutated.
- Deterministic runtime remains authoritative.
- Phase 8 EM Extract was not implemented.
- Phase 8 sizing/TCO was not implemented.
