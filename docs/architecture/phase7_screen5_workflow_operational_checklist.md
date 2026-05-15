# Phase 7 Screen 5 Workflow Operational Checklist

## 1. Purpose

This checklist guides local validation and release operation for the Phase 7BE-7BJ Screen 5 Recommendation / Action / Outcome Workflow block.

## 2. Pre-Run Checklist

- Confirm the branch is `phase7-screen5-action-outcome-workflow`.
- Confirm the working tree is clean before certification.
- Confirm no Phase 8 sizing/TCO work is included.
- Confirm Screen 5 workflow is governed.

## 3. Validation Checklist

- Run `python3 scripts/run_phase7_screen5_workflow_validation.py`.
- Run `python3 scripts/run_phase7_screen5_workflow_validation.py --json`.
- Confirm validation output says `Phase 7 Screen 5 workflow validation passed.`
- Confirm `screen5_workflow_ready=true`.

## 4. Recommendation Decision Checklist

- Run `python3 -m unittest tests/test_phase7bf_recommendation_decision_model.py`.
- Confirm no recommendation decision records are persisted.
- Confirm recommendation decision models do not mutate recommendation truth.

## 5. Action Tracking Checklist

- Run `python3 -m unittest tests/test_dashboard_screen5_action_tracking_panel.py`.
- Confirm action tracking UI remains disabled and preview-only.
- Confirm no action record is persisted and no action status is updated.

## 6. Outcome Capture Checklist

- Run `python3 -m unittest tests/test_dashboard_screen5_outcome_capture_panel.py`.
- Confirm outcome capture UI remains disabled and preview-only.
- Confirm no outcome record is persisted, no feedback is created, and no learning label is created.

## 7. Feedback Bridge Checklist

- Run `python3 -m unittest tests/test_phase7bi_feedback_learning_bridge.py`.
- Confirm feedback bridge creates intents only.
- Confirm feedback intents are not feedback records, learning signal intents are not dataset labels, and candidate intents are not candidates.

## 8. Runtime Isolation Checklist

- Confirm `scripts/run_analysis.py` does not import Screen 5 workflow modules.
- Confirm parser/scoring/decision/recommendation paths do not import Screen 5 workflow modules.
- Confirm no governed write path is invoked.
- Confirm no recommendation truth mutation occurs.

## 9. Documentation Checklist

- Confirm validation matrix, readiness, release certification, and operational checklist documents exist.
- Confirm architecture README links the Screen 5 workflow certification documents.
- Confirm documentation states no persistence occurs and no candidate is created automatically.

## 10. Failure Handling

- If validation fails, inspect the failing validation group.
- Do not modify parser, scoring, decision, recommendation, dashboard behavior, CLI behavior, database schema, generated dashboard HTML, or Phase 8 work to satisfy Screen 5 workflow certification.
- Fix only the local validation/certification artifact or the scoped Screen 5 workflow model that failed.

## 11. Acceptance Checklist

- Run `python3 scripts/run_phase7_screen5_workflow_readiness_check.py`.
- Run `python3 scripts/run_phase7_screen5_workflow_readiness_check.py --json`.
- Confirm text output says `Phase 7 Screen 5 workflow readiness passed.`
- Confirm JSON output has `screen5_workflow_ready=true`.
- Confirm no recommendation decision records, action records, outcome records, feedback records, labels, or candidates are created.
- Confirm deterministic runtime remains authoritative and Phase 8 sizing/TCO is not implemented.
