# Phase 7AS Screen 2 Review Request Preview

## 1. Purpose

Phase 7AS defines the Screen 2 review request preview shown in the disabled diagnostic review panel.

The preview is not review execution. It only displays the future governed request shape.

## 2. Review Request Preview Shape

The preview displays target type, review decision, actor required, audit required, governed write path required, governance bridge required, candidate intent possible, `write_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

Preview is not review execution.

## 3. Review Target Summary

The review target summary is read-only.

It may display selected diagnostic/evidence context and a safe empty state. It does not claim review was submitted and does not create a request object.

## 4. Future Actor Requirement

Future review execution requires actor identity.

The preview states actor required but does not authenticate, authorize, or create actor audit state.

## 5. Future Audit Requirement

Future review execution requires audit.

The preview states audit required but does not create audit records.

## 6. Future Governed Write Path Requirement

Future review writes require the governed write path.

The preview does not call backend, does not write, and does not invoke governed write path.

## 7. Future Governance Bridge Requirement

Future routed review decisions require the Screen 2 governance bridge.

The preview does not execute governance routing and does not create governance routes.

## 8. Candidate Intent Preview

Candidate intent possible means a future governed workflow may create a candidate intent.

The preview does not create candidates. No candidate is created automatically.

## 9. Runtime Safety Flags

The preview displays `write_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

These flags express that the preview does not mutate runtime, does not write, and does not mutate Phase 4I.

## 10. Non-Goals

Phase 7AS does not add active submit behavior, form POST, fetch/XMLHttpRequest, backend API calls, governed write path invocation, review record creation, persistence, governance execution, candidate creation, diagnostic truth mutation, parser output mutation, scoring mutation, recommendation truth mutation, `run_analysis.py` calls, 7AT validation/certification, or Phase 8 sizing/TCO.

## 11. Acceptance Criteria

Phase 7AS request preview is accepted when it shows future target type, review decision, actor required, audit required, governed write path required, governance bridge required, candidate intent possible, `write_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`, while proving that preview is not review execution, preview does not call backend, preview does not write, preview does not create candidates, preview does not mutate runtime, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
