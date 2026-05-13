# Phase 7O Adaptive Scoring Review

## Purpose

Phase 7O adds adaptive scoring review as a controlled, local, deterministic review model for proposed scoring changes derived from approved scoring materialization artifacts. Adaptive scoring review is proposal-only. It records a proposed versioned scoring configuration, expected before / after comparison, validation requirements, rollback planning, and source evidence for human review.

## Scope

Phase 7O may create and validate AdaptiveScoringReview records, serialize and deserialize those records, create inactive ProposedScoringConfig records, compare proposed review metadata, and enforce validation requirements. It may represent proposed changes for scoring weights, domain weights, domain thresholds, severity cutoffs, confidence thresholds, confidence rationale logic, trend sensitivity, anomaly sensitivity, recurring issue sensitivity, domain score normalization, and score interpretation labels.

## Non-Goals

Phase 7O does not modify runtime scoring behavior, scoring weights, scoring thresholds, confidence logic, trend logic, anomaly logic, decision logic, recommendation logic, parser behavior, parser output, Phase 4I output contracts, dashboard behavior, CLI behavior, database state, OCI state, Oracle Agent Memory, semantic recall services, LLM services, or network resources. No runtime scoring changes are applied. This is not ML and does not implement learned_model(x). Phase 7O does not implement Phase 7P recommendation rule evolution, Phase 7Q parser mapping evolution, or Phase 8 sizing/TCO.

## Source Materialization Artifact Requirement

An adaptive scoring review must originate from a scoring_review_artifact created from a scoring_weight_review_candidate. The source artifact must be runtime-sensitive, must have runtime_influence_granted=false, must be MATERIALIZED or VALIDATED, must carry required scoring validation requirements, and must not be REJECTED, ROLLED_BACK, or CLOSED. The source artifact is not mutated by review creation.

## Scoring Review Types

Supported review types are scoring_weight_review, domain_weight_review, threshold_review, severity_cutoff_review, confidence_logic_review, trend_sensitivity_review, anomaly_sensitivity_review, recurring_issue_sensitivity_review, score_normalization_review, and score_label_review. Unsupported review types fail validation.

## Adaptive Scoring Review Flow

The flow is scoring_weight_review_candidate approval, Phase 7N scoring_review_artifact materialization, Phase 7O AdaptiveScoringReview creation, proposal validation, and optional later human review. This flow produces review records only. It does not activate scoring changes, does not call a scoring engine, and does not write runtime configuration.

## Proposed Scoring Config Flow

A ProposedScoringConfig may be created from a validated AdaptiveScoringReview. The config receives a deterministic config_id, version, config_type, scoring proposal maps, status, source_review_id, runtime_active=false, and runtime_influence_granted=false. Proposed scoring configs are inactive. VALIDATED does not mean runtime active, and no ProposedScoringConfig is applied to runtime.

## Runtime Influence Boundary

runtime_influence_requested may document a request for future approval, but it is not runtime activation. runtime_influence_granted=false is enforced for every AdaptiveScoringReview and ProposedScoringConfig in Phase 7O. No Phase 7O status grants runtime influence.

## Versioning Requirements

Every adaptive scoring review must include proposed_config_version and a proposed_config payload. Review IDs are deterministic and use source materialization id, review type, and proposed config version. Proposed config IDs are deterministic and use config type, version, and source review id. IDs do not use random UUIDs, timestamps, database sequences, network services, or external systems.

## Before / After Comparison Requirements

Every review must include before_after_summary. The summary must describe the baseline scoring reference and the proposed scoring change as review context. The before / after comparison is evidence for review and validation planning only; it is not a recalculation of Phase 4I scores and it is not runtime scoring truth.

## Regression Validation Requirements

Every adaptive scoring review must require versioned scoring config validation, before/after comparison, scoring regression tests, Phase 4I scores contract validation, rollback plan validation, and confirmation that deterministic runtime remains authoritative. Review-type-specific validation also applies: threshold reviews require threshold regression tests, severity cutoff reviews require severity distribution comparison, confidence logic reviews require confidence calibration validation, trend sensitivity reviews require trend regression validation, anomaly sensitivity reviews require anomaly false positive/false negative review, and domain weight reviews require domain score distribution comparison.

## Rollback Requirements

Every adaptive scoring review must include rollback_plan. Runtime-sensitive scoring proposals require a clear way to discard or reverse the proposed scoring configuration before any later activation process can be considered. Rollback planning is audit and validation context only in Phase 7O.

## Semantic Context Boundary

Semantic context may support reviewer-assist context only. Semantic context is not scoring truth, not diagnostic evidence, not recommendation evidence, and not a source of automatic score changes. Semantic context cannot activate a proposed scoring config.

## Runtime Scoring Boundary

Existing runtime scoring remains deterministic and authoritative. Existing scoring engine remains authoritative. Phase 7O does not import scoring modules, does not change scoring formulas, does not change runtime weights, does not change runtime thresholds, and does not change confidence behavior.

## Phase 4I Scores Contract Boundary

Phase 4I scores contract preservation is mandatory. A Phase 7O review record may require Phase 4I scores contract validation for a future certified process, but Phase 7O itself does not change Phase 4I score values, score schema, dashboard truth, parser output, decisions, or recommendations.

## Relationship To Phase 7M

Phase 7M defined the learning materialization boundary and established that materialization is not activation. Phase 7O follows that boundary: scoring review is local, deterministic, proposal-only, and runtime_influence_granted=false remains enforced.

## Relationship To Phase 7N

Phase 7N introduced scoring_review_artifact records from approved scoring_weight_review_candidate records. Phase 7O uses only MATERIALIZED or VALIDATED scoring_review_artifact sources and converts them into inactive adaptive scoring review proposals. Phase 7N artifacts remain source materialization records and are not mutated.

## Relationship To Future Phase 7P

Phase 7P remains recommendation rule evolution. Phase 7O does not create, validate, activate, or modify recommendation rules and does not change recommendation behavior.

## Relationship To Future Phase 7Q

Phase 7Q remains parser mapping evolution. Phase 7O does not create parser mappings, classify unknown signals, alter parser output, or change parser behavior.

## Relationship To Future ML Phases

Future ML phases may define certified adaptive scoring intelligence, but Phase 7O is not ML. It does not implement learned_model(x), does not train a model, does not infer runtime scores, and does not create autonomous runtime changes.

## Acceptance Criteria

Phase 7O is accepted when adaptive scoring review records can be created only from valid scoring_review_artifact sources, unsupported source artifact types fail, unsupported review types fail, required validation requirements are enforced, review-type-specific validation is enforced, rollback plans are required, deterministic review and config IDs are generated, serialization is deterministic, proposed scoring configs are inactive, runtime_active=false, runtime_influence_granted=false, VALIDATED does not mean runtime active, no runtime scoring changes are applied, no scoring module is modified, no parser/decision/recommendation behavior is changed, no dashboard behavior is changed, no CLI behavior is changed, existing scoring engine remains authoritative, deterministic runtime remains authoritative, this is not ML, and learned_model(x) is not implemented.
