# Phase 7 Dashboard Workflow Infrastructure Operational Checklist

## 1. Purpose

This checklist defines local operator steps for validating and certifying the
Phase 7AD-7AI dashboard workflow infrastructure block.

Do not treat infrastructure readiness as workflow activation.

## 2. Pre-Run Checklist

- Confirm the repository is on `phase7-dashboard-workflow-infrastructure`.
- Confirm the working tree contains only expected validation/certification files.
- Confirm no dashboard files, CLI behavior files, parser modules, scoring
  modules, decision modules, recommendation modules, or generated dashboard HTML
  were modified.
- Use `.venv/bin/python` if system Python lacks dotenv.

## 3. Validation Checklist

Run:

- `python3 scripts/run_phase7_dashboard_workflow_validation.py`
- `python3 scripts/run_phase7_dashboard_workflow_validation.py --json`
- `python3 scripts/run_phase7_dashboard_workflow_readiness_check.py`
- `python3 scripts/run_phase7_dashboard_workflow_readiness_check.py --json`
- `python3 scripts/run_phase7_final_readiness_check.py`
- `python3 scripts/run_phase7aa_runtime_integration_readiness_check.py`
- `python3 scripts/run_phase7_validation.py`
- `PYTHONPATH=. .venv/bin/python scripts/run_phase6_validation.py`

If system Python lacks dependencies such as dotenv, use `.venv/bin/python` for
the Phase 7 commands.

## 4. Workflow Boundary Checklist

- Confirm 7AD boundary documentation exists.
- Confirm lifecycle documentation exists.
- Confirm no dashboard workflow is activated yet.

## 5. Actor Identity Checklist

- Confirm actor identity metadata tests pass.
- Confirm actor identity remains metadata only.
- Confirm no authentication or authorization service is implemented.

## 6. Backend Execution Mode Checklist

- Confirm backend execution mode tests pass.
- Confirm backend execution mode remains metadata only.
- Confirm no backend execution occurs yet.

## 7. Governed Write-Path Checklist

- Confirm governed write-path tests pass.
- Confirm `dry_run=true`.
- Confirm `write_performed=false`.
- Confirm no write is performed.

## 8. Output Lifecycle Checklist

- Confirm output lifecycle tests pass.
- Confirm `output_written=false`.
- Confirm `dashboard_regenerated=false`.
- Confirm `phase4i_mutated=false`.
- Confirm `runtime_mutation_performed=false`.
- Confirm `refresh_performed=false`.

## 9. Runtime Isolation Checklist

- Confirm `run_analysis.py` does not import workflow infrastructure modules.
- Confirm parser/scoring/decision/recommendation paths do not import workflow
  infrastructure modules.
- Confirm deterministic runtime remains authoritative.

## 10. Documentation Checklist

- Confirm the validation matrix exists.
- Confirm readiness documentation exists.
- Confirm release certification exists.
- Confirm this operational checklist exists.
- Confirm architecture README links the new documents.

## 11. Failure Handling

- Do not certify if validation fails.
- Do not bypass runtime isolation boundaries.
- Do not treat readiness output as permission to add dashboard buttons or writes.
- Fix the failing validation category before rerunning readiness.

## 12. Acceptance Checklist

- Dashboard workflow validation passes.
- Dashboard workflow readiness passes.
- Phase 7 final readiness passes.
- Phase 7AA runtime integration readiness passes.
- Phase 7 validation passes.
- Phase 6 validation passes when run.
- No backend execution is added.
- No write is performed.
- No output artifact is written.
- No dashboard is regenerated.
- No Phase 4I mutation occurs.
- Phase 8 sizing/TCO is not implemented.
