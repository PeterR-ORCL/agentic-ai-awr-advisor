# Phase 7 Recommendation Rule Model

## Purpose

The Phase 7P recommendation rule model defines local proposal records for recommendation rule evolution. It represents proposed recommendation changes and inactive proposed recommendation rules without changing runtime recommendations. No recommendation module is modified, no Phase 4I contract is changed, and no rule is applied to runtime.

## RecommendationRuleEvolution Object Shape

RecommendationRuleEvolution contains evolution_id, source_materialization_id, source_candidate_id, evolution_type, affected_domain, affected_component, proposed_change_summary, proposed_rule_version, proposed_rule, baseline_reference, before_after_summary, validation_requirements, rollback_plan, runtime_influence_requested, runtime_influence_granted, status, actor, created_at, validation_reference, source_evidence, and semantic_context.

evolution_id is deterministic. source_materialization_id and source_candidate_id link the evolution back to the Phase 7N materialization artifact and original candidate. proposed_rule_version and proposed_rule are required. before_after_summary, validation_requirements, rollback_plan, and actor are required. created_at defaults to None and is not generated from current time.

## ProposedRecommendationRule Object Shape

ProposedRecommendationRule contains rule_id, version, rule_type, affected_domain, rule_payload, evidence_requirements, output_contract_requirements, status, runtime_active, runtime_influence_granted, and source_evolution_id.

runtime_active=false and runtime_influence_granted=false are enforced. Proposed recommendation rules are inactive. A ProposedRecommendationRule may be serialized, deserialized, validated, and compared as a proposal, but it is never applied to runtime recommendations in Phase 7P.

## Supported Evolution Types

Supported evolution types are recommendation_wording_review, recommendation_priority_review, recommendation_domain_mapping_review, recommendation_suppression_review, action_sequencing_review, risk_label_review, evidence_mapping_review, recommendation_category_review, recommendation_confidence_wording_review, and recommendation_escalation_review. These cover proposed changes to wording, priority, domain mapping, suppression behavior, action sequencing, risk labels, evidence mapping, categories, confidence wording, and escalation/de-escalation.

## Statuses

Supported statuses are PROPOSED, UNDER_REVIEW, APPROVED_FOR_VALIDATION, VALIDATED, REJECTED, ROLLED_BACK, and CLOSED. No status means runtime active. VALIDATED does not mean runtime active. APPROVED_FOR_VALIDATION does not mean runtime active. ROLLED_BACK and CLOSED do not imply runtime mutation. runtime_influence_granted=false remains enforced for every status.

## Source Artifact Requirements

RecommendationRuleEvolution creation requires a Phase 7N recommendation_rule_artifact source. The source must come from a recommendation_rule_candidate, must be runtime-sensitive, must have runtime_influence_granted=false, must be MATERIALIZED or VALIDATED, must include required recommendation validation requirements, and must not be REJECTED, ROLLED_BACK, or CLOSED. Parser mapping artifacts and scoring review artifacts cannot create recommendation rule evolutions.

## Validation Requirements

Every recommendation rule evolution must include validation requirements covering versioned recommendation rule/config, recommendation regression tests, evidence mapping validation, Phase 4I recommendations contract validation, rollback plan, and deterministic runtime remains authoritative. Missing required concepts fail validation. Deserialization also validates these concepts so invalid records cannot bypass construction.

## Evolution-Type-Specific Validation

recommendation_wording_review requires wording regression validation. recommendation_priority_review requires priority/order regression validation. recommendation_domain_mapping_review requires domain mapping validation. recommendation_suppression_review requires suppression false positive/false negative review. action_sequencing_review requires action sequencing validation. risk_label_review requires risk label consistency validation. evidence_mapping_review requires evidence linkage validation. recommendation_category_review requires category consistency validation. recommendation_confidence_wording_review requires confidence wording calibration validation. recommendation_escalation_review requires escalation/de-escalation validation.

## Runtime Influence Fields

runtime_influence_requested is request-only and may be true as future review context. It does not activate runtime. runtime_influence_granted=false is mandatory and validation rejects any record that attempts to grant runtime influence. ProposedRecommendationRule also requires runtime_active=false and runtime_influence_granted=false.

## Deterministic ID Rules

RecommendationRuleEvolution IDs use RECO-EVO, evolution type, source materialization id, and proposed rule version after identifier normalization. ProposedRecommendationRule IDs use RECO-RULE, rule type, version, and source evolution id after identifier normalization. IDs do not use random UUIDs, timestamps, database sequences, DB writes, network calls, or external services.

## Serialization Rules

RecommendationRuleEvolution and ProposedRecommendationRule serialize to deterministic dictionaries with fixed field order. Deserialization validates supported evolution types, supported statuses, required strings, proposed rule shape, validation requirements, rollback requirements, runtime_active=false, runtime_influence_granted=false, source evidence shape, and semantic context shape. Serialization does not import runtime recommendation modules and does not mutate source artifacts.

## Versioning Rules

Every recommendation evolution requires proposed_rule_version. Every proposed recommendation rule requires version. Versioned rule records are proposals only. A versioned proposed rule can be reviewed and validated, but Phase 7P does not promote it to active recommendation truth.

## Evidence Mapping Rules

Evidence mapping validation is required for every evolution. ProposedRecommendationRule records carry evidence_requirements that preserve evidence mapping or evidence linkage validation. Semantic context is not recommendation truth, is not source evidence, and cannot replace deterministic evidence linkage.

## Phase 4I Recommendations Contract Rules

Phase 4I recommendations contract validation is required for every evolution and every proposed recommendation rule. Phase 7P does not change the Phase 4I recommendations contract, does not change runtime recommendation text, does not change recommendation rank or priority, and does not change recommendation evidence payloads.

## Rollback Rules

Every recommendation rule evolution requires rollback_plan. Rollback references describe how a proposed recommendation rule would be discarded or reversed by a later certified process. Rollback is not runtime activation and does not modify recommendation behavior in Phase 7P.

## Non-Goals

The model does not apply recommendation rules, activate recommendation rules, update runtime recommendations, update recommendation rules, change recommendation generation, change recommendation ranking, change recommendation priority, change recommendation wording, change evidence mapping, change action sequencing, change risk labels, change scoring behavior, change decision behavior, change trend or anomaly behavior, change parser behavior, change parser output, change dashboard behavior, change CLI behavior, write to a database, call OCI, call Oracle Agent Memory, call a semantic recall service, call an LLM, make network calls, implement Phase 7Q, implement Phase 7R, implement ML, implement learned_model(x), or implement Phase 8 sizing/TCO.

## Acceptance Criteria

The model is accepted when it creates proposal-only recommendation rule evolutions from valid recommendation_rule_artifact sources, rejects parser and scoring artifacts, rejects inactive source status misuse, rejects runtime influence grants, requires actor, proposed_rule_version, proposed_rule, before_after_summary, validation_requirements, and rollback_plan, enforces base and evolution-type-specific validation requirements, creates inactive proposed recommendation rules, preserves runtime_active=false, preserves runtime_influence_granted=false, serializes deterministically, keeps proposed recommendation rules inactive, applies no rule to runtime, modifies no recommendation module, changes no Phase 4I contract, keeps existing recommendation engine authoritative, and keeps deterministic runtime authoritative.
