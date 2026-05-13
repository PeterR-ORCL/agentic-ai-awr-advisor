# Phase 7 Materialization Lifecycle

## 1. Purpose

This document defines the future materialization lifecycle boundary for Phase 7M. It describes how a governed learning candidate may later move from approval for implementation consideration into a controlled implementation artifact, validation evidence, runtime eligibility review, and rollback planning.

The lifecycle is documentation and validation only in Phase 7M. No automatic activation is introduced.

## 2. Lifecycle Overview

The controlled lifecycle is:

```text
candidate proposed
-> human review
-> APPROVED_FOR_IMPLEMENTATION
-> materialization request
-> APPROVED_FOR_MATERIALIZATION
-> implementation reference
-> MATERIALIZED
-> validation evidence
-> VALIDATED
-> explicit runtime eligibility decision in a later certified process
```

APPROVED_FOR_IMPLEMENTATION is not runtime active. APPROVED_FOR_MATERIALIZATION is not runtime active. MATERIALIZED is not runtime active. VALIDATED is not runtime active unless a later explicit runtime eligibility decision exists.

## 3. Candidate States

Existing candidate states remain proposal/review lifecycle states. `PROPOSED`, `UNDER_REVIEW`, `APPROVED_FOR_IMPLEMENTATION`, `REJECTED`, `NEEDS_REVISION`, `IMPLEMENTED`, `VALIDATED`, and `CLOSED` do not grant runtime influence by themselves.

`APPROVED_FOR_IMPLEMENTATION` means a human has approved implementation consideration. It is not a parser change, scoring change, recommendation change, materialization artifact, validation result, runtime eligibility decision, or runtime activation.

## 4. Materialization Artifact States

Future materialization artifact states are:

- `PROPOSED`
- `APPROVED_FOR_MATERIALIZATION`
- `MATERIALIZED`
- `VALIDATED`
- `REJECTED`
- `ROLLED_BACK`
- `CLOSED`

These states describe artifact handling only. They do not make runtime behavior active in Phase 7M.

## 5. Approval Stage

The approval stage confirms that a candidate is approved for implementation consideration. It requires human review, actor attribution, candidate context, source evidence review, and explicit acknowledgement that candidate approval does not equal runtime activation.

Approval does not create an artifact automatically and does not mutate runtime logic.

## 6. Materialization Request Stage

The materialization request stage is separate from approval. It requests creation of a controlled implementation artifact or work item for a candidate.

`APPROVED_FOR_MATERIALIZATION` is not runtime active. It means a future materialization process may produce or track an implementation reference. It does not change parser behavior, scoring behavior, recommendation behavior, dashboard behavior, CLI behavior, or backend state in Phase 7M.

## 7. Implementation Reference Stage

The implementation reference stage links a materialization artifact to a proposed code/config/model/rule/docs/test change. An implementation reference may point to a branch, patch, config version, rule version, work item, document change, or test plan in a future phase.

`MATERIALIZED` is not runtime active. It means an implementation artifact exists for review. It does not run automatically.

## 8. Validation Stage

The validation stage attaches validation evidence to the implementation reference. Required evidence depends on candidate type and affected component.

`VALIDATED` is not runtime active unless a later explicit runtime eligibility decision exists. Validation proves a proposed implementation passed required checks; it does not grant runtime influence by itself.

## 9. Runtime Eligibility Stage

Runtime eligibility is a later certified decision outside Phase 7M. It requires implementation reference, validation evidence, rollback plan, accountable human actors, component-owner review, and explicit runtime eligibility approval.

`runtime_influence_granted=false by default` for all future artifact shapes. Runtime influence cannot be inferred from candidate approval, materialization request approval, artifact existence, semantic context, dashboard interaction, CLI action, or validation success alone.

## 10. Activation Boundary

Activation is not implemented in Phase 7M. No materialization artifact activates runtime behavior in this phase.

Activation must be explicit, separately certified, reversible, and validation-backed. Parser/scoring/recommendation changes require separate validation before any runtime eligibility decision.

## 11. Rollback Stage

A rollback plan is required for runtime-eligible changes. The rollback plan must describe the versioned implementation reference to reverse, affected component, owner, validation evidence to rerun, and operator steps required to restore prior behavior.

Rollback is required before runtime eligibility can be considered for parser, scoring, recommendation, or any runtime-sensitive materialization path.

## 12. Parser Lifecycle Flow

The parser lifecycle is:

```text
Unknown signal
-> parser_mapping_candidate
-> human review
-> APPROVED_FOR_IMPLEMENTATION
-> parser materialization artifact
-> controlled parser code/config change
-> parser tests
-> AWR regression validation
-> Phase 4I contract validation
-> explicit runtime eligibility decision
```

Parser lifecycle validation requires old AWRs still parse, known sections still work, new mapping works, unknown signal handling remains safe, Phase 4I contract is preserved, and scoring does not regress because of bad parse output.

No automatic parser mutation is allowed.

## 13. Scoring Lifecycle Flow

The scoring lifecycle is:

```text
scoring_weight_review_candidate
-> human review
-> APPROVED_FOR_IMPLEMENTATION
-> scoring materialization artifact
-> versioned scoring config
-> before/after comparison
-> regression tests
-> Phase 4I scores contract validation
-> explicit runtime eligibility decision
```

Scoring lifecycle coverage includes scoring weight review, threshold review, confidence logic review, trend/anomaly sensitivity review, and domain score weighting review.

No automatic scoring mutation is allowed.

## 14. Recommendation Lifecycle Flow

The recommendation lifecycle is:

```text
recommendation_rule_candidate
-> human review
-> APPROVED_FOR_IMPLEMENTATION
-> recommendation materialization artifact
-> versioned recommendation rules
-> evidence mapping validation
-> output contract preservation
-> regression tests
-> explicit runtime eligibility decision
```

Recommendation lifecycle coverage includes recommendation wording, recommendation priority, evidence mapping, action sequencing, and risk labeling.

No automatic recommendation mutation is allowed.

## 15. Documentation / Dashboard / Validation Lifecycle Flow

Documentation, dashboard wording, dashboard interaction, semantic summary, governance workflow, and validation candidates may later become non-runtime work items. They still require human approval, implementation reference, validation evidence, and rollback or reversal notes.

Dashboard and CLI are not runtime mutation paths. Dashboard changes must not alter diagnostic truth, recommendation truth, parser output, scoring output, or runtime state.

## 16. Required Audit Fields

A future materialization artifact shape should include:

- `materialization_id`
- `source_candidate_id`
- `candidate_type`
- `affected_component`
- `affected_domain`
- `proposed_change_summary`
- `proposed_artifact_type`
- `implementation_reference`
- `validation_requirements`
- `rollback_plan`
- `runtime_influence_requested`
- `runtime_influence_granted`
- `status`
- `actor`
- `approval_reference`
- `created_at`
- `reviewed_by`
- `validation_reference`

All future defaults must keep `runtime_influence_granted=false`.

## 17. Required Validation Evidence

Required validation evidence depends on affected component:

- Parser changes require parser tests, AWR regression validation, Phase 4I contract validation, unknown signal safety validation, and scoring regression checks.
- Scoring changes require versioned scoring config review, before/after comparison, regression tests, and Phase 4I scores contract validation.
- Recommendation changes require versioned recommendation rules, evidence mapping checks, output contract preservation, and regression tests.
- Dashboard changes require read-only behavior validation and dashboard tests.
- Governance workflow changes require actor-gating and no hidden transition validation.
- Documentation and validation changes require deterministic local validation and documentation review.

## 18. Required Human Actors

Required human actors include candidate reviewer, materialization requester, component owner, implementation owner, validation reviewer, rollback owner, and runtime eligibility approver in a later certified process.

One person may hold multiple roles only when project governance allows it, but the lifecycle must preserve explicit actor attribution.

## 19. Forbidden Shortcuts

Forbidden shortcuts include:

- Treating candidate approval as runtime activation.
- Treating APPROVED_FOR_MATERIALIZATION as runtime activation.
- Treating MATERIALIZED as runtime activation.
- Treating VALIDATED as runtime activation without a later explicit runtime eligibility decision.
- Letting semantic context become implementation truth.
- Letting dashboard actions rewrite runtime logic.
- Letting CLI actions rewrite runtime logic.
- Automatically changing parser mappings.
- Automatically changing scoring weights, thresholds, confidence logic, trend/anomaly sensitivity, or domain score weighting.
- Automatically changing recommendation rules, wording, priority, evidence mapping, action sequencing, or risk labels.
- Bypassing validation.
- Activating without rollback.

## 20. Acceptance Criteria

The lifecycle boundary is accepted when documentation and tests prove APPROVED_FOR_IMPLEMENTATION is not runtime active, APPROVED_FOR_MATERIALIZATION is not runtime active, MATERIALIZED is not runtime active, VALIDATED is not runtime active without a later explicit runtime eligibility decision, `runtime_influence_granted=false by default`, parser/scoring/recommendation changes require separate validation, rollback plan is required for runtime-eligible changes, and no automatic activation exists.
