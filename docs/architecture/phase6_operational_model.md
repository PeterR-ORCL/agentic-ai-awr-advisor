# Phase 6 Operational Model

This document describes how Phase 6 functions in practice. It is operational guidance for deterministic runtime analysis, governed memory, governance workflows, semantic recall, CLI usage, dashboard visibility, and validation.

## 1. Runtime Analysis Flow

The runtime flow remains deterministic:

1. Loader discovers and stages AWR sources.
2. Parser extracts AWR sections and metrics.
3. Feature model builds structured diagnostic signals.
4. Scoring engines compute deterministic scores.
5. Decision engine determines posture and issue prioritization.
6. Recommendation engine produces deterministic action guidance.
7. Dashboard renderer displays deterministic evidence and read-only memory visibility.
8. Governed memory records runtime output downstream.

Oracle Agent Memory is not required for this flow.

## 2. Memory Persistence Flow

Memory persistence records deterministic runtime output and downstream review artifacts. It persists run memory, recommendation memory, unknown parser signals, actions, outcomes, feedback, governance requests, and knowledge artifacts.

Persistence is append-oriented where auditability matters. Review and governance updates are explicit and bounded to review or approval metadata.

## 3. Governance Review Flow

Unknown parser signals may be reviewed by humans. Review captures status, classification, reviewer, timestamp, notes, and metadata. The dashboard shows these records as read-only visibility.

Review does not modify parser logic. Review does not change scoring or recommendations.

## 4. Knowledge Request Lifecycle

Knowledge update requests are created from reviewed signals, feedback, or outcomes. A request begins as `PENDING`. A human reviewer may update approval status to `APPROVED`, `REJECTED`, or another governed state.

Approval marks eligibility for future materialization. It does not change runtime behavior.

## 5. Artifact Lifecycle

Approved requests may be materialized into knowledge artifacts. Artifacts are versioned, auditable, and created with `ACTIVATION_STATUS = INACTIVE`.

Artifacts do not influence runtime analysis in Phase 6. Activation is deferred to a future controlled phase.

## 6. Structured Recall Operations

Structured recall APIs query governed memory tables. They support filtering, bounded limits, and deterministic ordering with `newest` or `oldest`.

Structured recall returns stable shapes with fields such as `enabled`, `success`, `records`, `count`, and `order`.

Structured recall is read-only.

## 7. Semantic Recall Operations

Semantic recall uses curated Oracle Agent Memory context only when explicitly requested through semantic APIs or CLI commands. It returns non-authoritative context for analyst assistance.

If semantic recall is disabled, commands return a structured skipped response. Normal runtime analysis and dashboard generation do not depend on live Oracle Agent Memory connectivity.

## 8. Governance Semantic Assistance

Governance semantic assistance builds reviewer-oriented context for:

- unknown signal review
- parser governance review
- knowledge request review
- artifact review

It may surface prior semantic themes, matched DB names, issue types, postures, and observations. It does not approve, reject, classify, materialize, activate, recommend, or instruct parser behavior.

## 9. Dashboard Visibility Behavior

Dashboard visibility is read-only. Screen 1 exposes intake, parser review, and parser governance visibility. Screen 6 exposes fleet, governance, knowledge readiness, and semantic recall visibility.

Semantic recall appears only as system-level visibility. It is labeled as reviewer-assist context and not diagnostic evidence.

## 10. CLI Operations

The unified CLI entrypoint is:

```bash
PYTHONPATH=. .venv/bin/python scripts/awr_memory_cli.py
```

Command groups are:

- `status`
- `recall`
- `review`
- `governance`
- `artifact`
- `semantic`

The CLI delegates to existing APIs. It does not shell out to older scripts, and existing individual scripts remain available.

## 11. Validation Workflow

Run consolidated Phase 6 validation with:

```bash
PYTHONPATH=. .venv/bin/python scripts/run_phase6_validation.py
```

The validation suite checks runtime isolation, semantic isolation, governance safety, dashboard truth preservation, CLI operational safety, memory persistence integrity, recall correctness, semantic non-authoritativeness, import isolation, and write discipline.

## 12. Operational Safety Rules

Operational safety rules:

- deterministic runtime remains authoritative
- semantic recall remains non-authoritative
- governed memory is auditable
- governance remains human-controlled
- CLI writes require an actor
- semantic commands remain read-only
- dashboard visibility does not mutate state
- artifacts remain inactive in Phase 6

## 13. Read-only vs Write Operations

Read-only operations:

- all structured recall commands
- semantic recall commands
- semantic assist commands
- status commands
- dashboard visibility
- artifact listing

Explicit write operations:

- unknown signal review
- knowledge request creation
- approval status update
- knowledge artifact materialization
- action tracking
- outcome tracking
- feedback capture

Write operations are explicit and should include actor attribution where exposed through CLI operations.

## 14. Failure Isolation Behavior

Failure isolation rules:

- memory disabled returns structured skipped output
- semantic recall disabled returns structured skipped output
- Oracle Agent Memory unavailability does not block runtime analysis
- DB recall errors return structured errors in CLI/API paths
- dashboard generation tolerates unavailable governance or semantic visibility data
- semantic failures do not affect parser, scoring, decision, recommendation, or dashboard truth
