# Phase 7N Approved Candidate Materialization

## Purpose

Phase 7N adds a controlled, local, deterministic artifact model for learning candidates that have already been approved for implementation consideration. The artifact is a governed work item that describes a proposed implementation reference, validation requirements, rollback planning, source evidence, and reviewer-assist semantic context when available.

## Scope

Phase 7N may convert one approved learning candidate into one local materialization artifact, validate artifact structure, serialize and deserialize artifacts, classify artifact type by candidate type, enforce validation requirements, enforce rollback requirements, enforce human actor requirements, and preserve runtime_influence_granted=false. The artifact remains a proposal and review vehicle only.

## Non-Goals

Phase 7N does not modify parser behavior, parser output, parser configuration, scoring logic, scoring weights, decision logic, recommendation logic, recommendation rules, Phase 4I output, dashboard behavior, CLI behavior, database state, OCI state, Oracle Agent Memory, semantic recall services, or network resources. Phase 7N does not implement Phase 7O adaptive scoring review, Phase 7P recommendation rule evolution, Phase 7Q parser mapping evolution, ML, adaptive runtime scoring, or Phase 8 sizing/TCO.

## Candidate Approval Requirement

A candidate must be APPROVED_FOR_IMPLEMENTATION before materialization artifact creation. Candidate approval does not equal materialization. Rejected, closed, proposed, or otherwise non-approved candidates cannot create artifacts. The candidate must still have runtime_influence=false and requires_human_review=true.

## Candidate To Artifact Flow

The flow is candidate review, candidate status APPROVED_FOR_IMPLEMENTATION, explicit local artifact creation by a human actor, artifact validation, and optional future review in later phases. This flow does not transition the candidate, mutate the candidate, or attach runtime behavior.

## Materialization Is Not Activation

Materialization does not equal runtime activation. A materialization artifact describes controlled work that could be implemented, validated, and rolled back, but the artifact itself does not change runtime truth. MATERIALIZED is not runtime active. VALIDATED is not runtime active by itself. CLOSED is not runtime active, and ROLLED_BACK is not runtime active.

## Runtime Influence Boundary

runtime_influence_granted=false for Phase 7N artifacts. runtime_influence_requested may document a future review request, but it is advisory only and does not grant influence. No Phase 7N status grants runtime influence. Deterministic runtime remains authoritative until a later certified process explicitly changes that boundary.

## Parser Artifact Boundary

Parser materialization artifacts are runtime-sensitive. A parser_mapping_candidate maps to parser_mapping_artifact. Parser artifacts must require parser tests, AWR regression validation, Phase 4I contract validation, unknown signal safety, and a scoring regression check. Parser evolution remains future 7Q. Phase 7N adds no automatic parser mutation and no automatic parser mapping evolution.

## Scoring Artifact Boundary

Scoring materialization artifacts are runtime-sensitive. A scoring_weight_review_candidate maps to scoring_review_artifact. Scoring artifacts must require a versioned scoring config, before/after comparison, scoring regression tests, Phase 4I scores contract validation, and a rollback plan. Scoring evolution remains future 7O. Phase 7N adds no automatic scoring mutation and no scoring weight change.

## Recommendation Artifact Boundary

Recommendation materialization artifacts are runtime-sensitive. A recommendation_rule_candidate maps to recommendation_rule_artifact. Recommendation artifacts must require versioned recommendation rule/config references, recommendation regression tests, evidence mapping validation, Phase 4I recommendations contract validation, and a rollback plan. Recommendation evolution remains future 7P. Phase 7N adds no automatic recommendation mutation and no recommendation rule change.

## Dashboard / Governance / Semantic / Documentation Artifact Boundary

Dashboard wording, dashboard interaction, governance workflow, semantic summary, documentation, and validation artifacts are non-runtime or indirect artifact types in Phase 7N. They describe proposed work only and do not directly mutate dashboard files, CLI behavior, documentation, governance state, parser logic, scoring logic, decision logic, or recommendation logic. Semantic context is reviewer-assist only and not implementation truth, not source evidence, and not diagnostic authority.

## Validation Requirements

Every artifact must carry validation_requirements. Parser artifacts require parser tests, AWR regression validation, Phase 4I contract validation, unknown signal safety, and scoring regression checks. Scoring artifacts require versioned scoring config review, before/after comparison, scoring regression tests, and Phase 4I scores contract validation. Recommendation artifacts require versioned recommendation rules/config, recommendation regression tests, evidence mapping validation, and Phase 4I recommendations contract validation. Dashboard artifacts require dashboard rendering validation, safety label preservation when applicable, and read-only behavior preservation when applicable. Governance artifacts require actor requirement validation, approval boundary validation, and audit trail validation. Semantic artifacts require reviewer-assist only validation, non-authoritative validation, and not source evidence validation. Documentation artifacts require doc review and boundary language preservation. Validation artifacts require validation command update and regression test coverage.

## Rollback Requirements

Runtime-sensitive parser, scoring, and recommendation artifacts require an explicit rollback plan. Non-runtime artifacts may use a lower rollback burden, but they still support rollback_plan as a controlled field. Rollback planning does not activate runtime behavior.

## Human Actor Requirement

Artifact creation requires a non-empty actor. Phase 7N does not allow dashboard controls, CLI shortcuts, or automatic processes to create an artifact without an actor field.

## Audit Requirements

Artifacts preserve source_candidate_id, candidate_type, affected component and domain, proposed change summary, proposed artifact type, implementation reference, validation requirements, rollback plan, runtime influence request state, runtime influence grant state, status, actor, approval reference, review references, source evidence, and semantic context. created_at defaults to None and is not generated from current time.

## Relationship To Phase 7M

Phase 7M defined the learning materialization boundary and lifecycle. Phase 7N uses that boundary to create actual local artifact records while keeping the same controls: candidate approval does not equal runtime activation, materialization is separate from approval, materialization does not equal runtime activation, and runtime_influence_granted=false.

## Relationship To Future Phase 7O

Phase 7O remains the future adaptive scoring review phase. Phase 7N may create scoring_review_artifact records, but it does not change scoring configuration, scoring weights, scoring formulas, or Phase 4I scores.

## Relationship To Future Phase 7P

Phase 7P remains the future recommendation rule evolution phase. Phase 7N may create recommendation_rule_artifact records, but it does not change recommendation rules, recommendation configuration, recommendation evidence mapping, or Phase 4I recommendations.

## Relationship To Future Phase 7Q

Phase 7Q remains the future parser mapping evolution phase. Phase 7N may create parser_mapping_artifact records, but it does not change parser mappings, parser code, parser configuration, unknown signal classification, parser output, or Phase 4I contracts.

## Acceptance Criteria

Phase 7N is accepted when approved candidates can create deterministic local artifacts, non-approved candidates cannot create artifacts, candidate-to-artifact mapping is enforced, runtime-sensitive parser/scoring/recommendation requirements are enforced, runtime-sensitive rollback plans are required, actor identity is required, serialization round trips are deterministic, runtime_influence_granted=false is enforced, no artifact activates runtime, no automatic parser mutation is added, no automatic scoring mutation is added, no automatic recommendation mutation is added, no dashboard behavior is changed, no CLI behavior is changed, no parser/scoring/decision/recommendation behavior is changed, and deterministic runtime remains authoritative.
