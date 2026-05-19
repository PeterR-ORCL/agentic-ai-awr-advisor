# Phase 7CN Screen 1 Parser Governance Runtime Workflow

## Objective

7CN turns Screen 1 parser governance from preview-only visibility into a governed request workflow. The dashboard can select a parser unknown, parser governance item, or knowledge artifact context, show evidence and safety state, submit a review request through the governed dashboard workflow service, and display the resulting request/audit state.

This workflow is intentionally request-record-only. It does not mutate parser output, Phase 4I, diagnostic truth, scoring truth, recommendation truth, approvals, or dashboard truth.

## Index Functional Lock Decision

For the 7CN WIP, `awr_dashboard/index.html` is functionally locked, not byte locked. The regenerated index artifact is acceptable for generated dashboard bundle consistency because the source-selection visible DOM and source-selection behavior are unchanged. The byte diff is caused by shared embedded CSS/JS growth from `src/reporting/html_dashboard.py`; source-selection handlers and source-selection data markers remain unchanged. The shared `buildDashboardActionRequest` function changed only to add Screen 1 governed action branches.

## Screen 1 User Workflow

1. Open Screen 1.
2. Review the Parser Governance panel.
3. Select a parser unknown signal, parser governance item, or knowledge artifact target.
4. Confirm the active target, target type, evidence/context summary, governance status, and safety/influence status.
5. Choose a governed action such as parser unknown review, parser unknown classification intent, parser unknown routing, parser mapping approval intent, or knowledge artifact review.
6. Submit the governed request through the dashboard workflow service.
7. Review the accepted/rejected status, request ID, and audit record path.

Historical preview panels may remain below the primary workflow for evidence and debug context, but they are not the operational workflow.

## Governed Action Contract

Screen 1 governed requests use the shared dashboard action contract with:

- `screen_id=screen_1`
- a valid parser governance `action_type`
- a valid target type for that action
- a selected target ID or signal/artifact ID
- reviewer/actor identity
- governance intent and governance status
- safety fields proving no direct mutation or runtime activation
- future-run influence metadata explicitly gated and inactive by default

Supported action types include:

- `parser_unknown_review`
- `parser_unknown_classify`
- `parser_unknown_route`
- `parser_unknown_approve`
- `parser_unknown_reject`
- `parser_mapping_approval_intent`
- `knowledge_artifact_review`
- `knowledge_artifact_approve`
- `knowledge_artifact_reject`

The contract rejects missing targets, unsupported target/action combinations, unsafe mutation requests, direct runtime activation, Phase 4I mutation, Phase 8 behavior, EM Extract attempts, browser-side DB/Object Storage/file reads, browser-side AWR parsing, and direct `run_analysis.py` coupling.

## Request And Audit Behavior

Accepted Screen 1 requests are queued as governed dashboard action records by `scripts/dashboard_workflow_service.py` through `src/learning/dashboard_runtime_interaction.py`. The response includes request status, request ID, audit reference, source summary, and safety flags.

Rejected requests return a clear reason and do not write accepted request/audit evidence.

## Safety Boundaries

Screen 1 parser governance requests do not:

- mutate parser output
- create parser mappings directly
- persist unknown-signal classifications directly
- create parser candidates or backlog items directly
- approve, reject, revise, or materialize artifacts directly
- mutate Phase 4I
- mutate diagnostic/scoring/recommendation truth
- activate adaptive runtime
- grant runtime influence by default
- start Phase 8 behavior
- run EM Extract
- call `run_analysis.py` from browser actions

Future-run influence remains gated, auditable, and denied by default. Separate governed materialization and runtime eligibility checks are required before any future parser behavior can change.

## Validation Commands

Run the focused Screen 1 validator:

```bash
.venv/bin/python scripts/run_phase7_screen1_parser_governance_workflow_validation.py --json
```

Run the broader readiness check:

```bash
.venv/bin/python scripts/run_phase7_operational_readiness_check.py --json
```

Expected readiness remains `phase7_operational_ready=false` because 7CO through 7CT and final certification remain pending.
