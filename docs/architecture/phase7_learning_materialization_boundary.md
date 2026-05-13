# Phase 7 Learning Materialization Boundary

## 1. Purpose

Phase 7M defines the learning materialization boundary for the Agentic AI AWR Advisor project. It explains how approved learning candidates may later become controlled implementation artifacts without allowing approval, semantic context, dashboard actions, or CLI actions to directly mutate runtime behavior.

The central rule is: candidate approval does not equal runtime activation.

## 2. Scope

This document covers the boundary between candidate approval, materialization artifact creation, controlled implementation, validation, and explicit runtime activation. It applies to all existing Phase 7 candidate types and establishes guardrails for future Phase 7N through Phase 7Q work.

Phase 7M is boundary, documentation, and validation only. It does not implement actual materialization behavior.

## 3. Non-Goals

Phase 7M does not implement materialization artifacts, materialization persistence, parser evolution, scoring review, recommendation evolution, dashboard changes, CLI materialization commands, database writes, network calls, LLM calls, Oracle Agent Memory integration, semantic recall service integration, or runtime activation.

Phase 7M does not change parser behavior, parser output, loader behavior, scoring logic, scoring weights, trend/anomaly logic, decision logic, recommendation logic, recommendation ranking, Phase 4I output contracts, `run_analysis.py`, dashboard behavior, CLI behavior, candidate generation, candidate approval behavior, or governance transition behavior.

## 4. Candidate Approval vs Materialization vs Activation

Candidate approval is governance state only. Approval means "approved for implementation consideration." Candidate approval does not equal runtime activation.

Materialization is separate from approval. Materialization creates a controlled implementation artifact, work item, code/config proposal, rule proposal, validation plan, or documentation change record for later human implementation work.

Materialization is not activation. A materialized artifact may describe a proposed code/config/model/rule update, but it does not automatically run.

Runtime eligibility is a separate later decision. `runtime_influence remains false` in Phase 7M, and `runtime_influence_granted=false` remains the default for any future materialization artifact shape.

## 5. Materialization Principles

Phase 7M establishes these principles:

- Candidate approval is governance state only.
- Materialization is separate from approval.
- Materialization is not activation.
- Runtime influence is separately granted.
- Parser/scoring/recommendation paths are separate.
- Parser evolution is first-class.
- Semantic context is not implementation truth.
- Dashboard and CLI are not runtime mutation paths.
- Phase 4I contract must be preserved.
- No automatic parser mutation is allowed.
- No automatic scoring mutation is allowed.
- No automatic recommendation mutation is allowed.

## 6. Candidate Types Covered

| Candidate type | Can be materialized later | Materialization artifact | Can ever influence runtime | Validation required | Approval required | Rollback required | Explicitly forbidden |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `parser_mapping_candidate` | Yes, in future Phase 7Q. | Parser materialization artifact for a controlled code/config mapping change. | Only after future explicit runtime eligibility. | Parser tests, AWR regression validation, Phase 4I contract validation, scoring regression checks. | Human approval for implementation plus parser-owner review. | Parser mapping rollback and regression re-run. | Unknown signal auto-classification, semantic rewrite, dashboard rewrite, CLI rewrite, automatic parser mutation. |
| `recommendation_rule_candidate` | Yes, in future Phase 7P. | Versioned recommendation rule/config proposal. | Only after future explicit runtime eligibility. | Recommendation regression tests, evidence mapping checks, Phase 4I recommendations contract validation. | Human approval for implementation plus recommendation-owner review. | Rule/config rollback and recommendation regression re-run. | Automatic recommendation rule mutation or semantic context directly changing recommendations. |
| `scoring_weight_review_candidate` | Yes, in future Phase 7O. | Versioned scoring config or threshold review proposal. | Only after future explicit runtime eligibility. | Before/after comparison, scoring regression tests, Phase 4I scores contract validation. | Human approval for implementation plus scoring-owner review. | Versioned scoring config rollback and regression re-run. | Automatic scoring mutation or approval directly changing scoring. |
| `dashboard_wording_candidate` | Yes, as a non-runtime UI copy artifact. | Dashboard wording change proposal or documentation issue. | No runtime diagnostic influence. | UI copy review and dashboard snapshot/regression checks where applicable. | Human approval for implementation. | Wording rollback. | Changing diagnostic truth, recommendation truth, parser output, or runtime state. |
| `dashboard_interaction_candidate` | Yes, as a non-runtime dashboard design/work item. | Dashboard interaction proposal. | No runtime diagnostic influence. | Dashboard interactivity tests and read-only behavior validation. | Human approval for implementation. | Interaction rollback. | Backend writes, approval controls, write controls, API calls, or runtime mutation. |
| `governance_workflow_candidate` | Yes, as a governance process/workflow proposal. | Governance workflow artifact or process change record. | No direct runtime influence. | Governance safety tests and actor-gating validation. | Human governance approval. | Workflow rollback or process reversal. | Automatic approval, automatic activation, or hidden state transition. |
| `semantic_summary_candidate` | Yes, as reviewer-assist content only. | Semantic summary improvement proposal. | No runtime influence. | Non-authoritative semantic boundary validation. | Human approval for implementation. | Summary/content rollback. | Semantic context becoming implementation truth or runtime evidence. |
| `documentation_candidate` | Yes, as documentation work. | Documentation change proposal. | No runtime influence. | Documentation review and link validation. | Human approval for implementation. | Documentation rollback. | Claiming runtime behavior that does not exist. |
| `validation_candidate` | Yes, as validation/test work. | Validation plan or test proposal. | No runtime influence by itself. | Test review and deterministic local validation. | Human approval for implementation. | Test change rollback. | Treating tests as runtime activation or bypassing validation. |

All candidate types remain proposal/review context in Phase 7M.

## 7. Parser Materialization Boundary

Parser must not be treated generically. Parser evolution is first-class and protected because parser output feeds deterministic feature engineering, scoring, trend/anomaly review, decision logic, recommendations, dashboard truth, and the Phase 4I contract.

The protected parser flow is:

```text
Unknown signal
-> parser_mapping_candidate
-> human review
-> approved for implementation
-> parser materialization artifact
-> controlled parser code/config change
-> parser tests
-> AWR regression validation
-> Phase 4I contract validation
-> explicit runtime eligibility decision
```

Hard parser rules:

- No automatic parser mutation.
- No semantic recall directly changing parser behavior.
- No dashboard approval rewriting parser logic.
- No CLI approval rewriting parser logic.
- No unknown signal auto-classification into parser output.
- No parser behavior change without code/config implementation.
- No parser runtime eligibility without tests.
- No parser evolution that breaks Phase 4I output contract.
- No parser change that causes scoring regression without validation.

Parser validation requirements include old AWRs still parse, known sections still work, new mapping works, unknown signal handling remains safe, Phase 4I contract is preserved, and scoring does not regress because of bad parse output.

## 8. Scoring Materialization Boundary

Scoring materialization remains future Phase 7O work. Phase 7M only defines the boundary for `scoring_weight_review_candidate`, threshold review, confidence logic review, trend/anomaly sensitivity review, and domain score weighting review.

Scoring changes require a versioned scoring config or equivalent controlled implementation reference. They require before/after comparison, regression tests, score contract checks, and explicit human review.

Hard scoring rules:

- No automatic scoring mutation.
- No approval directly changing scoring.
- No runtime score change without versioned scoring config.
- No scoring config eligibility without regression tests.
- No learned/semantic context directly modifying score.
- No score threshold change without before/after comparison.
- No breaking Phase 4I scores contract.

## 9. Recommendation Materialization Boundary

Recommendation materialization remains future Phase 7P work. Phase 7M only defines the boundary for `recommendation_rule_candidate`, recommendation wording, recommendation priority, evidence mapping, action sequencing, and risk labeling.

Recommendation changes require versioned recommendation rules or equivalent controlled implementation reference. They require recommendation regression tests, evidence mapping review, priority/ranking comparison where applicable, and Phase 4I recommendations contract preservation.

Hard recommendation rules:

- No automatic recommendation mutation.
- No approval directly changing recommendations.
- No semantic context directly changing recommendations.
- No runtime recommendation change without versioned recommendation rules or config.
- No recommendation rule eligibility without regression tests.
- No breaking Phase 4I recommendations contract.

## 10. Dashboard / Documentation / Validation Candidate Boundary

Dashboard wording, dashboard interaction, documentation, and validation candidates may create non-runtime work items in future materialization work. These artifacts can improve presentation, documentation, or validation coverage, but they cannot alter deterministic backend truth.

Dashboard artifacts must remain read-only unless a later phase explicitly implements reviewed dashboard behavior. Documentation artifacts cannot claim unsupported runtime behavior. Validation artifacts can add tests, but passing tests is not runtime activation.

## 11. Governance Workflow Candidate Boundary

Governance workflow candidates may become process or workflow change proposals. They do not directly update candidate state, materialization state, runtime state, parser logic, scoring logic, recommendation logic, dashboard truth, or CLI behavior.

Governance approval remains human-governed and actor-gated. Approval for implementation consideration is not runtime activation.

## 12. Semantic Summary Candidate Boundary

Semantic summary candidates may become reviewer-assist content proposals. Semantic context is not implementation truth.

Semantic context may help explain why a materialization should be reviewed, but semantic context cannot itself become code, config, parser mapping, scoring threshold, recommendation rule, validation result, approval evidence, or runtime evidence.

## 13. Runtime Influence Boundary

`runtime_influence remains false` for candidates and Phase 7M boundary records. Future materialization artifact shapes must keep `runtime_influence_granted=false` by default.

Runtime influence may be considered only by a later certified process that has explicit implementation reference, validation evidence, rollback plan, human approval, and runtime eligibility decision.

## 14. Human Approval Requirements

Human approval is required before implementation consideration. Separate owner review is required for parser, scoring, recommendation, governance, dashboard, documentation, and validation work.

Approval does not create artifacts automatically, does not implement code/config automatically, does not validate changes automatically, and does not activate runtime behavior.

## 15. Versioning Requirements

Runtime-sensitive materialization must use versioned implementation references. Parser mappings, scoring configs, recommendation rules, evidence mappings, thresholds, and action sequencing changes must be identifiable, reviewable, and reversible.

Versioning must preserve provenance from source candidate to approval reference to implementation reference to validation reference to runtime eligibility decision.

## 16. Validation Requirements

Validation requirements are component-specific:

- Parser: parser tests, old AWR coverage, known section coverage, unknown signal safety, AWR regression validation, Phase 4I contract validation, scoring regression checks.
- Scoring: versioned scoring config review, before/after comparison, regression tests, Phase 4I scores contract validation.
- Recommendation: versioned recommendation rules, evidence mapping tests, priority/ranking comparison where applicable, regression tests, Phase 4I recommendations contract validation.
- Dashboard: read-only behavior validation and dashboard tests.
- Governance: actor-gating and no hidden state transition validation.
- Semantic summary: non-authoritative reviewer-assist validation.
- Documentation and validation: documentation tests and deterministic local validation.

## 17. Rollback Requirements

Every runtime-sensitive materialization path requires a rollback plan before runtime eligibility can be considered. Rollback must identify the versioned implementation reference, affected component, validation evidence to rerun, and operator responsible for reversal.

Non-runtime documentation, dashboard, governance, semantic summary, and validation artifacts also require a rollback or reversal note appropriate to their artifact type.

## 18. Runtime Truth Boundary

Deterministic runtime remains authoritative. Parser output, feature engineering, scoring, trend/anomaly logic, decision logic, recommendation logic, and Phase 4I output contracts remain the runtime truth path.

Phase 7M does not place candidate approval, materialization boundary records, semantic context, dashboard actions, CLI actions, or documentation in the runtime truth path.

## 19. Semantic Context Boundary

Semantic context remains reviewer-assist only. It is not source evidence, deterministic evidence, approval evidence, implementation truth, validation evidence, or runtime truth.

Semantic context cannot directly change parser behavior, scoring behavior, recommendation behavior, dashboard truth, governance state, candidate status, or runtime eligibility.

## 20. Dashboard Boundary

Dashboard and CLI are not runtime mutation paths. Dashboard displays may later expose materialization review context, but dashboard approval must not rewrite parser logic, scoring logic, recommendation rules, governance state, candidate status, or runtime state.

Phase 7M introduces no dashboard selectors, no dashboard controls, no generated dashboard HTML changes, no backend writes, and no API calls.

## 21. CLI Boundary

The CLI may later display or request review for materialization workflows, but Phase 7M adds no CLI materialization commands and changes no CLI behavior.

CLI approval must not rewrite parser logic, scoring logic, recommendation rules, governance state, candidate status, runtime state, or backend storage.

## 22. Relationship to Phase 7A-7L Foundation

Phase 7A through Phase 7L established governed learning foundations: boundary definition, outcome pattern mining, candidate modeling, candidate generation, semantic reviewer-assist context, governance bridge, dashboard visibility and interactivity, CLI learning operations, validation harness, documentation finalization, and readiness certification.

Phase 7M builds on those foundations by defining the next boundary. It does not revise completed Phase 7A through Phase 7L behavior.

## 23. Relationship to Future Phase 7N

Future 7N implements actual materialization artifacts. Phase 7M does not create materialization artifacts, persist materialization artifacts, or implement artifact lifecycle transitions.

## 24. Relationship to Future Phase 7O

Future 7O implements scoring review. Phase 7M only defines scoring materialization boundaries and confirms no automatic scoring mutation.

## 25. Relationship to Future Phase 7P

Future 7P implements recommendation evolution. Phase 7M only defines recommendation materialization boundaries and confirms no automatic recommendation mutation.

## 26. Relationship to Future Phase 7Q

Future 7Q implements parser mapping evolution. Phase 7M only defines parser materialization boundaries and confirms no automatic parser mutation.

## 27. Acceptance Criteria

Phase 7M is accepted when materialization boundary documentation exists, materialization lifecycle documentation exists, tests prove the required boundary language is present, all existing candidate types are covered, parser/scoring/recommendation boundaries are explicit, optional scaffolding remains inert and local-only if present, runtime paths do not import materialization boundary code, `runtime_influence remains false`, `runtime_influence_granted=false` remains the default, and existing Phase 7 and Phase 6 validation remains green.
