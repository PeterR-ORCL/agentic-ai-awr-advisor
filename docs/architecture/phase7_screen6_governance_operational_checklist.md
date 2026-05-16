# Phase 7 Screen 6 Governance Operational Checklist

## Purpose

This checklist gives operators the local validation steps for the Phase 7BK-7BP Screen 6 Governance Control Plane block.

## Pre-Run Checklist

- Confirm the branch is `phase7-screen6-governance-control-plane`.
- Confirm the working tree is clean before certification work starts.
- Confirm no new Screen 6 behavior was added for 7BP.
- Confirm generated dashboard HTML is not part of this certification task.

## Validation Checklist

- Run `python3 scripts/run_phase7_screen6_governance_validation.py`.
- Run `python3 scripts/run_phase7_screen6_governance_validation.py --json`.
- Confirm `Phase 7 Screen 6 governance validation passed.`
- Confirm `screen6_governance_ready=true`.

## Candidate Review Checklist

- Run `python3 -m unittest tests/test_dashboard_screen6_candidate_review_panel.py`.
- Confirm candidate review controls are disabled and preview-only.
- Confirm no candidate status is changed.
- Confirm no governance action is performed.

## Materialization Review Checklist

- Run `python3 -m unittest tests/test_dashboard_screen6_materialization_review_panel.py`.
- Confirm materialization review controls are disabled and preview-only.
- Confirm no materialization status is changed.
- Confirm no validation or rollback reference is attached.

## Model Registry Review Checklist

- Run `python3 -m unittest tests/test_dashboard_screen6_model_registry_review_panel.py`.
- Confirm model registry review controls are disabled and preview-only.
- Confirm no model status is changed.
- Confirm no runtime eligibility is granted.

## Runtime Gate Review Checklist

- Run `python3 -m unittest tests/test_dashboard_screen6_runtime_gate_review_panel.py`.
- Confirm runtime gate review controls are disabled and preview-only.
- Confirm no runtime gate state is changed.
- Confirm no rollback execution occurs.

## Runtime Isolation Checklist

- Confirm `scripts/run_analysis.py` does not import Screen 6 governance preview modules.
- Confirm parser/scoring/decision/recommendation paths do not import Screen 6 governance preview modules.
- Confirm no governed write path is invoked.
- Confirm no runtime activation occurs.
- Confirm no Phase 4I mutation occurs.

## Documentation Checklist

- Confirm the validation matrix, readiness guide, release certification, and operational checklist are linked from `docs/architecture/README.md`.
- Confirm Screen 6 governance controls are preview-only.
- Confirm active governance persistence is future work.
- Confirm deterministic runtime remains authoritative.

## Failure Handling

- Stop on any validation failure.
- Do not modify runtime behavior to satisfy validation.
- Fix only the failing 7BK-7BP documentation, scripts, tests, or preview-only guardrails.
- Re-run the exact failing command, then re-run the full Screen 6 governance validation and readiness commands.

## Acceptance Checklist

- Run `python3 scripts/run_phase7_screen6_governance_readiness_check.py`.
- Run `python3 scripts/run_phase7_screen6_governance_readiness_check.py --json`.
- Confirm `Phase 7 Screen 6 governance readiness passed.`
- Confirm `screen6_governance_ready=true`.
- Confirm no governance action is performed.
- Confirm no status transition occurs.
- Confirm no runtime eligibility is granted.
- Confirm no runtime activation occurs.
- Confirm no Phase 4I mutation occurs.
- Confirm Phase 8 sizing/TCO is not implemented.
