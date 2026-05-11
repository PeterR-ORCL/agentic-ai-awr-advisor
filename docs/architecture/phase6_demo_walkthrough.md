# Phase 6 Demo Walkthrough

This document guides a Phase 6 demo for architecture review, OCI presentation, operational onboarding, executive walkthrough, and engineering continuation.

## 1. Demo Objectives

Show that Phase 6 adds governed deterministic memory, structured recall, governance visibility, semantic reviewer-assist context, CLI operations, and validation without changing deterministic runtime truth.

Do not claim that the system learns autonomously, changes recommendations based on semantic memory, approves governance records automatically, or activates artifacts automatically.

## 2. Runtime Analysis Walkthrough

What to show:

- Run `AI_PROVIDER=oci PYTHONPATH=. .venv/bin/python scripts/run_analysis.py`.
- Point out the deterministic runtime flow: loader, parser, feature model, scoring, decision, recommendation, governed memory, dashboard rendering.
- Show runtime diagnostics and provider/model display.

What not to claim:

- Do not claim Oracle Agent Memory is required for runtime analysis.
- Do not claim semantic recall changes parser, scoring, decision, or recommendation outputs.

Key message:

Deterministic runtime truth remains authoritative.

## 3. Dashboard Walkthrough

What to show:

- Open `awr_dashboard/index.html`.
- Show the AI Explanation Layer and pipeline.
- Show Screen 1 intake, parser review, and parser governance visibility.
- Show Screen 2 diagnostic truth and evidence-gated narrative wording.
- Show Screen 5 recommendation posture.
- Show Screen 6 governance, artifact, and semantic recall visibility.

What not to claim:

- Do not present semantic recall as diagnostic evidence.
- Do not imply dashboard controls can approve, classify, or activate governance records.

Key message:

Dashboard truth is deterministic. Governance and semantic sections are read-only visibility.

## 4. Governance Walkthrough

What to show:

- Explain unknown signal review records.
- Explain knowledge request and approval status tracking.
- Explain artifact materialization as an explicit human-controlled operation.
- Show CLI examples from `docs/architecture/phase6_cli_operations.md`.

What not to claim:

- Do not claim governance records approve themselves.
- Do not claim artifacts influence runtime decisions in Phase 6.

Key message:

Governance remains human-controlled and does not alter runtime truth.

## 5. Structured Recall Walkthrough

What to show:

```text
PYTHONPATH=. .venv/bin/python scripts/awr_memory_cli.py recall summary
PYTHONPATH=. .venv/bin/python scripts/awr_memory_cli.py recall unknown-signals --status NEW --limit 5 --order newest
```

Explain that structured recall is read-only, bounded, filterable, and deterministic.

What not to claim:

- Do not claim structured recall modifies memory.
- Do not claim recall changes diagnosis or recommendation posture.

Key message:

Structured recall makes governed memory inspectable without changing runtime behavior.

## 6. Semantic Recall Walkthrough

What to show:

```text
PYTHONPATH=. .venv/bin/python scripts/awr_memory_cli.py semantic status
PYTHONPATH=. .venv/bin/python scripts/awr_memory_cli.py semantic recall --query "SPRTRN io pressure" --limit 5
```

If Oracle Agent Memory is disabled, show the structured skipped output and explain that disabled state is safe and expected.

What not to claim:

- Do not claim semantic recall is authoritative.
- Do not claim semantic recall determines root cause, severity, posture, or recommendations.

Key message:

Semantic recall is optional reviewer-assist context only.

## 7. CLI Walkthrough

What to show:

- `status` for operational overview.
- `recall` for read-only governed memory inspection.
- `semantic` for non-authoritative reviewer-assist context.
- `review`, `governance`, and `artifact` examples as explicit actor-attributed write operations.

What not to claim:

- Do not present write commands as hidden automation.
- Do not imply semantic commands approve or materialize anything.

Key message:

The CLI separates read-only inspection from explicit write operations.

## 8. Validation Walkthrough

What to show:

```text
PYTHONPATH=. .venv/bin/python scripts/run_phase6_validation.py
PYTHONPATH=. .venv/bin/python scripts/run_phase6_readiness_check.py
```

Show validation categories and readiness checks.

What not to claim:

- Do not claim live Oracle Agent Memory is required for validation.

Key message:

Phase 6 has explicit validation for runtime isolation, semantic isolation, governance safety, dashboard truth, CLI safety, recall correctness, and write discipline.

## 9. Safety and Isolation Talking Points

- Parser extraction remains deterministic.
- Scoring remains deterministic.
- Decision posture remains deterministic.
- Recommendation generation remains deterministic.
- Governed memory is structured and reviewable.
- Semantic recall is non-authoritative.
- Governance remains human-controlled.
- Dashboard truth remains deterministic.
- Oracle Agent Memory is optional and isolated.
- No autonomous learning behavior exists in Phase 6.

## 10. Key Architecture Messaging

Use this concise architecture message:

Phase 6 adds governed memory and recall around the deterministic AWR Advisor runtime. It makes history, governance, artifacts, and semantic context visible and inspectable while preserving parser, scoring, decision, recommendation, and dashboard truth boundaries.

Use this semantic boundary message:

Semantic recall is reviewer-assist context only. It does not change deterministic diagnosis, scoring, recommendations, governance approvals, artifact activation, or dashboard truth.

## 11. Phase 7 Transition Talking Points

Phase 7 can explore interactive control-plane workflows and separately governed activation models. Any future adaptive behavior must be explicitly designed, validated, and governed.

Do not present deferred Phase 7 work as active Phase 6 capability.
