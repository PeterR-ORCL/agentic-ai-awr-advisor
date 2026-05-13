# Phase 7P Recommendation Rule Evolution

## Purpose

Phase 7P adds recommendation rule evolution as a controlled, local, deterministic proposal model for recommendation changes derived from approved recommendation materialization artifacts. Recommendation rule evolution is proposal-only. It records proposed recommendation wording, priority, evidence, category, sequencing, suppression, risk, confidence wording, and escalation changes for human review without changing runtime recommendations.

## Scope

Phase 7P may create and validate RecommendationRuleEvolution records, serialize and deserialize those records, create inactive ProposedRecommendationRule records, preserve source evidence and semantic reviewer-assist context, and enforce deterministic validation requirements. It supports recommendation wording review, recommendation priority review, recommendation domain mapping review, recommendation suppression review, action sequencing review, risk label review, evidence mapping review, recommendation category review, recommendation confidence wording review, and recommendation escalation/de-escalation review.

## Non-Goals

Phase 7P does not modify runtime recommendation behavior, recommendation generation logic, recommendation ranking, recommendation priority order, recommendation wording used by runtime, recommendation evidence mapping used by runtime, action sequencing used by runtime, risk labels used by runtime, scoring logic, decision logic, trend or anomaly logic, parser behavior, parser output, Phase 4I output contracts, dashboard behavior, CLI behavior, database state, OCI state, Oracle Agent Memory, semantic recall services, LLM services, or network resources. No runtime recommendation changes are applied. This is not ML and does not implement learned_model(x). Phase 7P does not implement Phase 7Q parser mapping evolution, Phase 7R certification, or Phase 8 sizing/TCO.

## Source Materialization Artifact Requirement

A recommendation rule evolution must originate from a recommendation_rule_artifact created from a recommendation_rule_candidate. The source artifact must be runtime-sensitive, must have runtime_influence_granted=false, must be MATERIALIZED or VALIDATED, must include recommendation validation requirements, and must not be REJECTED, ROLLED_BACK, or CLOSED. The source artifact is never mutated by evolution creation.

## Recommendation Evolution Types

Supported evolution types are recommendation_wording_review, recommendation_priority_review, recommendation_domain_mapping_review, recommendation_suppression_review, action_sequencing_review, risk_label_review, evidence_mapping_review, recommendation_category_review, recommendation_confidence_wording_review, and recommendation_escalation_review. Unsupported evolution types fail validation.

## Recommendation Rule Evolution Flow

The flow is recommendation_rule_candidate approval, Phase 7N recommendation_rule_artifact materialization, Phase 7P RecommendationRuleEvolution creation, deterministic proposal validation, and optional later human review. This flow produces proposal records only. It does not activate recommendation rules, call the recommendation engine, rewrite recommendation catalogs, or write runtime configuration.

## Proposed Recommendation Rule Flow

A ProposedRecommendationRule may be created from a validated RecommendationRuleEvolution. The rule receives a deterministic rule_id, version, rule_type, affected_domain, rule_payload, evidence requirements, output contract requirements, status, source_evolution_id, runtime_active=false, and runtime_influence_granted=false. Proposed recommendation rules are inactive. VALIDATED does not mean runtime active, and no ProposedRecommendationRule is applied to runtime.

## Runtime Influence Boundary

runtime_influence_requested may document a request for future approval, but it is not runtime activation. runtime_influence_granted=false is enforced for every RecommendationRuleEvolution and ProposedRecommendationRule in Phase 7P. No Phase 7P status grants runtime influence.

## Versioning Requirements

Every recommendation rule evolution must include proposed_rule_version and a proposed_rule payload. Evolution IDs are deterministic and use source materialization id, evolution type, and proposed rule version. Proposed rule IDs are deterministic and use rule type, version, and source evolution id. IDs do not use random UUIDs, timestamps, database sequences, network services, or external systems.

## Before / After Comparison Requirements

Every evolution must include before_after_summary. The summary must describe the baseline recommendation rule reference and the proposed recommendation change as review context. The before / after comparison is validation planning context only; it is not a recalculation of Phase 4I recommendations and it is not runtime recommendation truth.

## Regression Validation Requirements

Every recommendation rule evolution must require versioned recommendation rule/config validation, recommendation regression tests, evidence mapping validation, Phase 4I recommendations contract validation, rollback plan validation, and confirmation that deterministic runtime remains authoritative. Evolution-type-specific validation also applies: wording review requires wording regression validation, priority review requires priority/order regression validation, domain mapping review requires domain mapping validation, suppression review requires suppression false positive/false negative review, action sequencing review requires action sequencing validation, risk label review requires risk label consistency validation, evidence mapping review requires evidence linkage validation, category review requires category consistency validation, confidence wording review requires confidence wording calibration validation, and escalation review requires escalation/de-escalation validation.

## Evidence Mapping Boundary

Evidence mapping validation is mandatory. Recommendation evolution may preserve and reference source_evidence from the materialization artifact, and may require evidence linkage validation for a future certified process. It cannot rewrite runtime evidence mapping, cannot treat semantic context as evidence, and cannot alter the recommendation evidence used by runtime.

## Phase 4I Recommendations Contract Boundary

Phase 4I recommendations contract preservation is mandatory. A Phase 7P record may require Phase 4I recommendations contract validation, but Phase 7P itself does not change recommendation schema, recommendation text, recommendation order, recommendation risk labels, action sequence payloads, dashboard truth, parser output, scores, or decisions.

## Recommendation Runtime Boundary

Existing runtime recommendation behavior remains deterministic and authoritative. Existing recommendation engine remains authoritative. Phase 7P does not import recommendation runtime modules, does not change recommendation catalogs, does not change generation logic, does not change ranking, does not change priority, and does not change runtime recommendation wording.

## Semantic Context Boundary

Semantic context may support reviewer-assist context only. Semantic context is not recommendation truth, not diagnostic evidence, not source evidence, and not a source of automatic recommendation changes. Semantic context cannot activate a proposed recommendation rule.

## Dashboard / CLI Boundary

Dashboard and CLI surfaces are not recommendation mutation paths. Phase 7P adds no dashboard controls, no CLI controls, no approval buttons, no write controls, and no commands that rewrite recommendation logic. Existing dashboard behavior and CLI behavior remain unchanged.

## Rollback Requirements

Every recommendation rule evolution must include rollback_plan. Runtime-sensitive recommendation proposals require a clear way to discard or reverse the proposed recommendation rule before any later activation process can be considered. Rollback planning is audit and validation context only in Phase 7P.

## Relationship to Phase 7M

Phase 7M defined the learning materialization boundary and established that materialization is not activation. Phase 7P follows that boundary: recommendation rule evolution is local, deterministic, proposal-only, and runtime_influence_granted=false remains enforced.

## Relationship to Phase 7N

Phase 7N introduced recommendation_rule_artifact records from approved recommendation_rule_candidate records. Phase 7P uses only MATERIALIZED or VALIDATED recommendation_rule_artifact sources and converts them into inactive recommendation evolution proposals. Phase 7N artifacts remain source materialization records and are not mutated.

## Relationship to Phase 7O

Phase 7O added proposal-only scoring review artifacts and inactive proposed scoring configs. Phase 7P mirrors that controlled materialization pattern for recommendation rules while keeping scoring behavior unchanged.

## Relationship to Future Phase 7Q

Phase 7Q remains parser mapping evolution. Phase 7P does not create parser mappings, classify unknown signals, alter parser output, or change parser behavior.

## Relationship to Future ML Phases

Future ML phases may define certified adaptive intelligence, but Phase 7P is not ML. It does not implement learned_model(x), does not train a model, does not infer runtime recommendations, and does not create autonomous runtime changes.

## Acceptance Criteria

Phase 7P is accepted when recommendation rule evolution records can be created only from valid recommendation_rule_artifact sources, unsupported source artifact types fail, unsupported evolution types fail, required validation requirements are enforced, evolution-type-specific validation is enforced, rollback plans are required, deterministic evolution and rule IDs are generated, serialization is deterministic, proposed recommendation rules are inactive, runtime_active=false, runtime_influence_granted=false, VALIDATED does not mean runtime active, no runtime recommendation changes are applied, no recommendation module is modified, no parser/scoring/decision behavior is changed, no dashboard behavior is changed, no CLI behavior is changed, existing recommendation engine remains authoritative, deterministic runtime remains authoritative, this is not ML, and learned_model(x) is not implemented.
