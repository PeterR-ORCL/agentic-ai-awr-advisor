# Phase 7R Controlled Learning Materialization Validation Matrix

## Purpose

Phase 7R certifies the controlled materialization block delivered in Phase 7M through Phase 7Q. It is a validation and certification layer only. It does not add new materialization behavior, scoring review behavior, recommendation evolution behavior, parser evolution behavior, dashboard behavior, CLI behavior, machine learning, or Phase 8 sizing/TCO functionality.

The central certification statement is that candidate approval does not equal runtime activation, candidate approval is not activation, materialization is separate from approval, and materialization is not activation.

## Scope

The scope is the completed Phase 7M through Phase 7Q materialization block:

- Phase 7M learning materialization boundary.
- Phase 7N approved candidate materialization artifacts.
- Phase 7O adaptive scoring review proposals and inactive proposed scoring configs.
- Phase 7P recommendation rule evolution proposals and inactive proposed recommendation rules.
- Phase 7Q parser mapping evolution proposals and inactive parser backlog items.

Phase 7R validates that `runtime_influence_granted=false`, `runtime_active=false`, parser/scoring/recommendation changes are proposal-only, parser evolution is first-class and protected, and deterministic runtime remains authoritative.

## Non-Goals

Phase 7R does not apply parser mappings, activate scoring configs, activate recommendation rules, mutate parser logic, mutate scoring logic, mutate recommendation logic, change Phase 4I output contracts, add dashboard mutation paths, add CLI materialization commands, add DB writes, add network calls, add Oracle Agent Memory dependency, implement ML, implement learned_model(x), or implement Phase 8.

## Validation Categories

The validation harness groups are `materialization_boundary`, `approved_candidate_materialization`, `adaptive_scoring_review`, `recommendation_rule_evolution`, `parser_mapping_evolution`, `import_isolation`, `runtime_safety`, and `documentation`.

Each category must pass before the materialization block can be certified. The checks are local-only, deterministic, standard-library only, safe for CI, and do not require database, OCI, Oracle Agent Memory, semantic recall service, network, or environment variable dependencies.

## 7M Boundary Validation

Phase 7M validation confirms that learning materialization boundaries are defined and inert. It validates that materializable candidate types are classified without creating artifacts, transitioning candidate status, writing records, calling services, or activating runtime behavior.

The boundary validation must state that candidate approval does not equal runtime activation, materialization is separate from approval, materialization is not activation, `runtime_influence_granted=false`, semantic context is not implementation truth, dashboard and CLI are not mutation paths, and Phase 4I contract remains protected.

## 7N Approved Candidate Materialization Validation

Phase 7N validation confirms that approved candidates can become local controlled materialization artifacts. This is a work-item model only: approved candidate materialization records can be created and validated locally, but materialization is not activation.

The validation confirms that `runtime_influence_granted=false` is enforced and that materialized or validated artifacts are not runtime active by themselves.

## 7O Adaptive Scoring Review Validation

Phase 7O validation confirms that adaptive scoring review is proposal-only. Proposed scoring configs are inactive, `runtime_active=false`, and `runtime_influence_granted=false`.

No runtime scoring changes are applied. Existing scoring logic, scoring weights, thresholds, trend sensitivity, anomaly sensitivity, severity logic, and scoring output contract remain authoritative.

## 7P Recommendation Rule Evolution Validation

Phase 7P validation confirms that recommendation rule evolution is proposal-only. Proposed recommendation rules are inactive, `runtime_active=false`, and `runtime_influence_granted=false`.

No runtime recommendation changes are applied. Existing recommendation generation, ranking, rationale, evidence mapping, and recommendation output contract remain authoritative.

## 7Q Parser Mapping Evolution Validation

Phase 7Q validation confirms that parser evolution is first-class and protected. Parser mapping evolution records and parser backlog items are proposal-only, inactive, and guarded by parser tests, AWR regression validation, Phase 4I contract validation, unknown signal safety, scoring regression validation, and rollback planning.

No runtime parser changes are applied. No automatic parser mutation exists. Parser backlog items are not runtime active and cannot grant runtime influence.

## Import Isolation Validation

Import isolation validation uses AST import scanning to confirm that runtime paths do not import materialization/evolution modules.

The required isolation checks include:

- `scripts/run_analysis.py` does not import `materialization_artifact`, `adaptive_scoring_review`, `recommendation_rule_evolution`, or `parser_mapping_evolution`.
- Parser runtime modules do not import `parser_mapping_evolution`, `materialization_artifact`, `adaptive_scoring_review`, or `recommendation_rule_evolution`.
- Scoring runtime modules do not import `adaptive_scoring_review`, `materialization_artifact`, `recommendation_rule_evolution`, or `parser_mapping_evolution`.
- Recommendation runtime modules do not import `recommendation_rule_evolution`, `materialization_artifact`, `adaptive_scoring_review`, or `parser_mapping_evolution`.

## Runtime Safety Validation

Runtime safety validation confirms that no materialization/evolution module accepts `runtime_influence_granted=true` and no proposed scoring config, proposed recommendation rule, or parser backlog item accepts `runtime_active=true`.

The validation also confirms the absence of active mutation functions such as `apply_parser_mapping`, `activate_parser_mapping`, `mutate_parser`, `update_runtime_parser`, `update_parser_regex`, `apply_scoring_config`, `activate_scoring`, `mutate_scoring`, `update_runtime_scoring`, `update_scoring_weights`, `apply_recommendation_rule`, `activate_recommendation_rule`, `mutate_recommendations`, `update_runtime_recommendations`, `update_recommendation_rules`, `auto_apply`, and `autonomous_apply`.

## Parser-Specific Safety Validation

Parser-specific safety validation confirms that parser evolution remains first-class and protected. Parser proposals require Phase 4I contract validation, AWR regression validation, unknown signal safety, scoring regression validation, and rollback planning.

No automatic parser mutation is allowed. Semantic context is not parser truth. Dashboard and CLI are not parser mutation paths.

## Scoring-Specific Safety Validation

Scoring-specific safety validation confirms that scoring review records and proposed scoring configs remain inactive. `runtime_active=false`, `runtime_influence_granted=false`, and no automatic scoring mutation is allowed.

The deterministic scoring runtime remains authoritative, and no scoring weights or scoring logic are changed by Phase 7R.

## Recommendation-Specific Safety Validation

Recommendation-specific safety validation confirms that recommendation rule evolution records and proposed recommendation rules remain inactive. `runtime_active=false`, `runtime_influence_granted=false`, and no automatic recommendation mutation is allowed.

The deterministic recommendation runtime remains authoritative, and no recommendation ranking, rationale, evidence mapping, or rule logic is changed by Phase 7R.

## Semantic Boundary Validation

Semantic boundary validation confirms that semantic context is reviewer-assist only. Semantic context is not implementation truth, is not parser truth, is not scoring truth, is not recommendation truth, and does not activate or materialize runtime behavior.

## Dashboard / CLI Boundary Validation

Dashboard and CLI boundary validation confirms that dashboard and CLI are not mutation paths. Dashboard behavior remains read-only, CLI behavior remains local and actor-gated, and neither surface can activate parser, scoring, or recommendation changes.

## Phase 4I Contract Boundary Validation

Phase 4I contract boundary validation confirms that parser/scoring/recommendation changes are proposal-only and cannot alter the validated output contract. The Phase 4I contract remains protected, and deterministic runtime remains authoritative.

## Phase 7 Foundation Regression Validation

Phase 7 foundation regression validation can be run with `scripts/run_phase7_validation.py`. It confirms that the governed learning foundation remains local, deterministic, candidate-based, reviewer-assist only where semantic context is present, and non-runtime-mutating.

## Phase 6 Regression Validation

Phase 6 regression validation can be run with `PYTHONPATH=. .venv/bin/python scripts/run_phase6_validation.py`. It confirms that governed memory, semantic recall, and reviewer-assist context remain non-authoritative and do not alter parser/scoring/decision/recommendation runtime truth.

## Acceptance Criteria

Phase 7R is accepted only when all validation groups pass, `runtime_influence_granted=false`, `runtime_active=false`, candidate approval is not activation, materialization is not activation, parser/scoring/recommendation changes are proposal-only, parser evolution is first-class and protected, no automatic parser mutation exists, no automatic scoring mutation exists, no automatic recommendation mutation exists, dashboard and CLI are not mutation paths, Phase 4I contract remains protected, and deterministic runtime remains authoritative.
