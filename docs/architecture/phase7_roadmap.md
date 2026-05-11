# Phase 7 Roadmap

## Scope Statement

Only Phase 7A is in scope for this task. Phase 7B and later are future/deferred work.

Phase 7A is boundary-only. It documents learning constraints and validates that no runtime learning behavior, candidate generation, outcome mining, dashboard learning visibility, dashboard interactivity, CLI learning command, or runtime integration has been introduced.

## 1. Phase 7A - Learning Boundary Definition

Phase 7A defines the learning boundary, candidate lifecycle, and Phase 7 roadmap. It proves that learning is candidate-based, human-reviewed, non-authoritative until approved, governed, auditable, isolated from runtime diagnosis, and non-runtime-mutating.

Phase 7A deliverables are documentation, validation tests, and an optional inert src/learning package marker. It does not implement learning engines, outcome mining, dashboard interactivity, approval controls, activation, or materialization.

## 2. Phase 7B - Outcome Pattern Mining

Future/deferred. Phase 7B may analyze governed outcome history, feedback history, action history, recommendation history, and structured recall summaries to identify recurring patterns.

Outcome pattern mining must remain deterministic, auditable, and non-authoritative. Mined patterns may inform candidates but must not mutate runtime diagnosis, scoring, decisions, recommendations, parser logic, or dashboard truth.

## 3. Phase 7C - Learning Candidate Model

Future/deferred. Phase 7C may introduce a formal candidate model, persistence shape, validation rules, status transitions, and audit metadata.

The model must preserve requires_human_review=true and runtime_influence=false for proposed candidates. Candidate approval must not itself modify runtime behavior.

## 4. Phase 7D - Candidate Generation Engine

Future/deferred. Phase 7D may add deterministic candidate generation from structured outcome patterns, feedback, actions, recommendation history, unknown signals, knowledge artifacts, recall summaries, and dashboard interaction gaps.

The generation engine may propose candidates only. It must not apply candidates, activate candidates, update parser logic, update scoring logic, update recommendation logic, or change dashboard truth.

## 5. Phase 7E - Semantic Context for Candidate Explanation

Future/deferred. Phase 7E may attach optional semantic reviewer-assist context to candidate explanations.

Semantic context must remain non-authoritative. It may explain candidate rationale but cannot decide candidate status, approve candidates, reject candidates, set severity, score issues, select recommendations, or change runtime behavior.

## 6. Phase 7F - Governance Review for Learning Candidates

Future/deferred. Phase 7F may add governed review workflows for learning candidates, including status transitions, reviewer notes, rejection, revision, and approval for implementation.

Approval for implementation remains separate from materialization and runtime activation. Human governance remains required.

## 7. Phase 7G - Dashboard Learning Visibility

Future/deferred. Phase 7G may display learning candidates, candidate statuses, source evidence summaries, rationale, confidence, review state, semantic context, and audit metadata in the dashboard.

Dashboard learning visibility must remain downstream of deterministic and governed records. It must not mutate backend truth or activate candidates.

## 8. Phase 7H - Full Dashboard Interactive Selection Upgrade

Future/deferred. Phase 7H is the full dashboard interactive selection upgrade. By the end of Phase 7, all current static selection areas should become fully interactive and selectable across all relevant dashboard screens.

The Phase 7H dashboard goal is exploratory and read-only. Selected state must not mutate backend truth, deterministic output, parser output, scoring, decisions, recommendations, governed memory, semantic recall, learning candidates, or approval state.

Screen 1 expectations:

- selectable run/parser/governance/unknown/artifact items

Screen 2 expectations:

- selectable domain/evidence/metric/run items

Screen 3 expectations:

- fully interactive control center
- selectable AWR
- selectable DB/system
- selectable snapshot
- selectable comparison baseline
- selectable issue domain
- selectable severity/status
- selected state propagates across screens

Screen 4 expectations:

- selectable trend/domain/time window/anomaly/violin/similar-case items

Screen 5 expectations:

- selectable recommendation/action/outcome/feedback/learning-candidate items

Screen 6 expectations:

- selectable fleet group/system/run/governance/semantic/learning/outcome-pattern/candidate items

Cross-screen expectations:

- selected AWR/run/domain persists across navigation
- selected state is visible to the user
- selected state does not mutate backend truth
- selections are exploratory and read-only

Do not implement dashboard interactivity in Phase 7A. Phase 7A only documents this as future Phase 7H work.

## 9. Phase 7I - CLI Learning Commands

Future/deferred. Phase 7I may add CLI commands for listing candidates, showing candidate detail, reviewing candidates, recording review notes, and exporting candidate audit trails.

CLI commands must follow governed write-path discipline and must not activate runtime behavior as a side effect of listing, reviewing, or approving a candidate.

## 10. Phase 7J - Validation Harness

Future/deferred. Phase 7J may add validation harness coverage for candidate generation, candidate lifecycle transitions, governance review, semantic context boundaries, dashboard learning visibility, CLI learning commands, and runtime isolation.

Validation must prove that deterministic runtime remains authoritative and that learning candidates do not mutate runtime behavior.

## 11. Phase 7K - Documentation Finalization

Future/deferred. Phase 7K may finalize Phase 7 architecture, operational, governance, validation, CLI, dashboard, and readiness documentation.

Documentation must preserve the distinction between candidate proposal, human approval, implementation, validation, and runtime activation.

## 12. Phase 7L - Acceptance / Production Readiness

Future/deferred. Phase 7L may certify Phase 7 production readiness after all prior Phase 7 work is implemented, validated, documented, and governed.

Acceptance requires evidence that learning remains candidate-based, human-governed, auditable, deterministic where implemented, non-authoritative until approved, and isolated from runtime diagnosis unless explicitly implemented through controlled, validated, contract-preserving changes.
