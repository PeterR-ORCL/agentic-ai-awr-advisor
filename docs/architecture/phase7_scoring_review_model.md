# Phase 7 Scoring Review Model

## Purpose

The Phase 7O scoring review model defines local proposal records for adaptive scoring review. It represents proposed scoring changes and inactive proposed scoring configurations without changing runtime scoring. No scoring module is modified, no Phase 4I contract is changed, and no config is applied to runtime.

## AdaptiveScoringReview Object Shape

AdaptiveScoringReview contains review_id, source_materialization_id, source_candidate_id, review_type, affected_domain, affected_component, proposed_change_summary, proposed_config_version, proposed_config, baseline_reference, before_after_summary, validation_requirements, rollback_plan, runtime_influence_requested, runtime_influence_granted, status, actor, created_at, validation_reference, and source_evidence.

review_id is deterministic. source_materialization_id and source_candidate_id link the review back to the Phase 7N materialization artifact and original candidate. proposed_config_version and proposed_config are required. before_after_summary, validation_requirements, rollback_plan, and actor are required. created_at defaults to None and is not generated from current time.

## ProposedScoringConfig Object Shape

ProposedScoringConfig contains config_id, version, config_type, domain_weights, thresholds, severity_cutoffs, confidence_rules, trend_sensitivity, anomaly_sensitivity, status, runtime_active, runtime_influence_granted, and source_review_id.

runtime_active=false and runtime_influence_granted=false are enforced. Proposed scoring configs are inactive. A ProposedScoringConfig may be serialized, deserialized, validated, and compared as a proposal, but it is never applied to runtime scoring in Phase 7O.

## Supported Review Types

Supported review types are scoring_weight_review, domain_weight_review, threshold_review, severity_cutoff_review, confidence_logic_review, trend_sensitivity_review, anomaly_sensitivity_review, recurring_issue_sensitivity_review, score_normalization_review, and score_label_review. These cover proposed changes to scoring weights, domain weights, thresholds, severity cutoffs, confidence thresholds and rationale logic, trend sensitivity, anomaly sensitivity, recurring issue sensitivity, domain score normalization, and score interpretation labels.

## Statuses

Supported statuses are PROPOSED, UNDER_REVIEW, APPROVED_FOR_VALIDATION, VALIDATED, REJECTED, ROLLED_BACK, and CLOSED. No status means runtime active. VALIDATED does not mean runtime active. APPROVED_FOR_VALIDATION does not mean runtime active. ROLLED_BACK and CLOSED do not imply runtime mutation. runtime_influence_granted=false remains enforced for every status.

## Source Artifact Requirements

AdaptiveScoringReview creation requires a Phase 7N scoring_review_artifact source. The source must come from a scoring_weight_review_candidate, must be runtime-sensitive, must have runtime_influence_granted=false, must be MATERIALIZED or VALIDATED, must include required scoring validation requirements, and must not be REJECTED, ROLLED_BACK, or CLOSED. Parser mapping artifacts and recommendation rule artifacts cannot create adaptive scoring reviews.

## Validation Requirements

Every adaptive scoring review must include validation requirements covering versioned scoring config, before/after comparison, scoring regression tests, Phase 4I scores contract validation, rollback plan, and deterministic runtime remains authoritative. Missing required concepts fail validation. Deserialization also validates these concepts so invalid records cannot bypass construction.

## Review-Type-Specific Validation

threshold_review requires threshold regression tests. severity_cutoff_review requires severity distribution comparison. confidence_logic_review requires confidence calibration validation. trend_sensitivity_review requires trend regression validation. anomaly_sensitivity_review requires anomaly false positive/false negative review. domain_weight_review requires domain score distribution comparison.

## Runtime Influence Fields

runtime_influence_requested is request-only and may be true as future review context. It does not activate runtime. runtime_influence_granted=false is mandatory and validation rejects any record that attempts to grant runtime influence. ProposedScoringConfig also requires runtime_active=false and runtime_influence_granted=false.

## Deterministic ID Rules

AdaptiveScoringReview IDs use SCORING-REVIEW, review type, source materialization id, and proposed config version after identifier normalization. ProposedScoringConfig IDs use SCORING-CONFIG, config type, version, and source review id after identifier normalization. IDs do not use random UUIDs, timestamps, database sequences, DB writes, network calls, or external services.

## Serialization Rules

AdaptiveScoringReview and ProposedScoringConfig serialize to deterministic dictionaries with fixed field order. Deserialization validates supported review types, supported statuses, required strings, proposed config shape, validation requirements, rollback requirements, runtime_active=false, runtime_influence_granted=false, and source evidence shape. Serialization does not import runtime scoring modules and does not mutate source artifacts.

## Versioning Rules

Every scoring review requires proposed_config_version. Every proposed scoring config requires version. Versioned config records are proposals only. A versioned proposed config can be reviewed and validated, but Phase 7O does not promote it to active scoring truth.

## Rollback Rules

Every adaptive scoring review requires rollback_plan. Rollback references describe how a proposed scoring config would be discarded or reversed by a later certified process. Rollback is not runtime activation and does not modify scoring behavior in Phase 7O.

## Non-Goals

The model does not apply scoring changes, activate scoring configs, update runtime scoring, update scoring weights, change thresholds, change confidence logic, change trend or anomaly runtime logic, change decision logic, change recommendation logic, change parser behavior, change parser output, change dashboard behavior, change CLI behavior, write to a database, call OCI, call Oracle Agent Memory, call a semantic recall service, call an LLM, make network calls, implement Phase 7P, implement Phase 7Q, implement ML, implement learned_model(x), or implement Phase 8 sizing/TCO.

## Acceptance Criteria

The model is accepted when it creates proposal-only scoring reviews from valid scoring_review_artifact sources, rejects parser and recommendation artifacts, rejects inactive source status misuse, rejects runtime influence grants, requires actor, proposed_config_version, proposed_config, before_after_summary, validation_requirements, and rollback_plan, enforces base and review-type-specific validation requirements, creates inactive proposed scoring configs, preserves runtime_active=false, preserves runtime_influence_granted=false, serializes deterministically, keeps proposed scoring configs inactive, applies no config to runtime, modifies no scoring module, changes no Phase 4I contract, keeps existing scoring engine authoritative, and keeps deterministic runtime authoritative.
