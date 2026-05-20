# Phase 7CO Screen 2 Diagnostic Review Runtime Workflow

Screen 2 is the current diagnostic snapshot and high-level analysis workspace. It presents the deterministic diagnosis, the reasoning behind the posture, and the evidence drivers that support the current outcome.

The operator can focus a diagnostic domain, evidence group, metric group, wait event group, SQL signal, or diagnostic section. That focus is browser-side review context only; it does not change diagnosis, scoring, recommendation truth, parser output, runtime execution, materialization, or runtime eligibility.

## Diagnostic Meaning Rule

LLM-assisted wording may explain diagnostic meaning, but it must not replace deterministic diagnostic truth or governed service behavior. The deterministic engine decides; LLM-style wording explains the already-decided, screen-appropriate meaning. If explanatory wording conflicts with deterministic diagnosis, primary domain, score, severity, confidence, decision posture, recommendation, evidence values, thresholds, validation rules, service behavior, or runtime behavior, the deterministic value wins and the wording must be corrected or removed.

For 7CO, this rule is applied only to index/source intake, Screen 1 ingestion/parser governance, and Screen 2 diagnostic review. It is not generalized to Screens 3-6.

## Screen 2 Interaction Contract

Screen 2 interaction changes the browser-side evidence focus and explanatory reporting context only. The operator can select a diagnostic domain, evidence group, metric group, wait event group, SQL signal, or diagnostic section to focus the explanation.

Screen 2 does not submit review dispositions, reviewer notes, audit requests, ML feedback, outcomes, parser governance actions, scoring overrides, recommendation actions, learning candidate updates, materialization changes, or runtime eligibility changes.

## Safety Boundary

Screen 2 diagnostic review is non-mutating and non-submitting. It must not mutate Phase 4I output, diagnostic truth, domain scores, severity/confidence truth, recommendations, parser output, runtime execution, learning candidates, materialization state, runtime eligibility, governed service behavior, or Phase 8 behavior. It also must not create review, audit, ML feedback, outcome, materialization, or runtime eligibility records.

## Validation

Use:

```bash
.venv/bin/python scripts/run_phase7_screen2_diagnostic_review_workflow_validation.py --json
```

Readiness remains false until later screen workflows and final certification are complete.
