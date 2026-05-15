# Phase 7BI Feedback Learning Intent Model

## 1. Purpose

This document defines the local deterministic intent models used by the Phase 7BI Screen 5 recommendation feedback-to-learning bridge.

## 2. RecommendationFeedbackIntent Shape

`RecommendationFeedbackIntent` contains `feedback_intent_id`, `recommendation_id`, `decision_id`, `action_preview_id`, `outcome_preview_id`, `feedback_type`, `feedback_status`, `feedback_summary`, `actor_id`, `actor_audit_context`, `source_payload`, `feedback_created`, `write_performed`, `runtime_influence`, `phase4i_mutation_requested`, and `notes`.

## 3. LearningSignalIntent Shape

`LearningSignalIntent` contains `signal_intent_id`, `recommendation_id`, `outcome_status`, `outcome_effectiveness`, `signal_type`, `label_name`, `label_value`, `supervised_label_eligible`, `dataset_label_created`, `source_feedback_intent_id`, `source_evidence`, `confidence`, `requires_human_review`, `runtime_influence`, and `notes`.

## 4. RecommendationCandidateIntent Shape

`RecommendationCandidateIntent` contains `candidate_intent_id`, `source_feedback_intent_id`, `candidate_type`, `affected_domain`, `affected_component`, `rationale`, `source_evidence`, `candidate_created`, `requires_human_review`, `runtime_influence`, and `notes`.

## 5. RecommendationFeedbackBridgeResult Shape

`RecommendationFeedbackBridgeResult` contains `bridge_result_id`, `recommendation_id`, `feedback_intents`, `learning_signal_intents`, `candidate_intents`, `feedback_created`, `dataset_labels_created`, `candidates_created`, `write_performed`, `runtime_influence`, `phase4i_mutation_requested`, `bridge_status`, `denied_reasons`, `warnings`, `required_next_steps`, and `notes`.

## 6. Feedback Types

Supported feedback types are `accepted`, `rejected`, `deferred`, `not_applicable`, `effective`, `ineffective`, `partially_effective`, `improved`, `worsened`, `no_change`, `issue_recurred`, `inconclusive`, `false_positive`, `false_negative`, and `needs_review`.

## 7. Learning Signal Types

Supported learning signal types are `recommendation_outcome`, `action_effectiveness`, `performance_result`, `recurrence_signal`, `false_positive_signal`, `false_negative_signal`, `validation_signal`, and `review_signal`.

## 8. Label Names

Supported label names are `recommendation_accepted`, `recommendation_rejected`, `action_effective`, `action_ineffective`, `performance_improved`, `performance_worsened`, `no_change`, `issue_recurred`, `false_positive`, `false_negative`, and `unknown_outcome`. Learning signal intents are not dataset labels.

## 9. Candidate Type Mapping

Supported candidate intent types are `recommendation_rule_candidate`, `validation_candidate`, `scoring_weight_review_candidate`, and `documentation_candidate`. Candidate intents are not candidates, and no candidate is created automatically.

## 10. Validation Rules

Validation requires supported feedback types, signal types, label names, candidate types, and bridge statuses. It rejects `feedback_created=true`, `dataset_label_created=true`, `candidate_created=true`, `write_performed=true`, `runtime_influence=true`, and `phase4i_mutation_requested=true`. It also rejects `dataset_labels_created=true`, `candidates_created=true`, confidence values outside `0.0` through `0.95`, and `requires_human_review=false` for signal and candidate intents.

## 11. Serialization Rules

Serialization helpers convert each intent and bridge result to and from dictionaries. Round trips are deterministic and preserve false safety flags. Serialization is not persistence.

## 12. Deterministic ID Rules

IDs are deterministic and derived from stable inputs. Feedback intent IDs follow `SCREEN5-FEEDBACK-INTENT-<RECOMMENDATION_ID>-<FEEDBACK_TYPE>`. Learning signal intent IDs follow `SCREEN5-LEARNING-SIGNAL-<RECOMMENDATION_ID>-<SIGNAL_TYPE>-<LABEL>`. Candidate intent IDs follow `SCREEN5-CANDIDATE-INTENT-<RECOMMENDATION_ID>-<CANDIDATE_TYPE>`. Bridge result IDs follow `SCREEN5-FEEDBACK-BRIDGE-<RECOMMENDATION_ID>`.

## 13. Runtime Safety Rules

`feedback_created=false`, `dataset_label_created=false`, `candidate_created=false`, `write_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false` are mandatory. Bridge result aggregates also require `dataset_labels_created=false` and `candidates_created=false`.

## 14. Non-Goals

Phase 7BI does not persist feedback, create feedback records, create dataset labels, create learning candidates, update action records, update outcome records, invoke governed write path, mutate recommendation truth, mutate scoring, mutate parser behavior, mutate decision behavior, mutate Phase 4I, add UI, add CLI commands, or implement Phase 8 sizing/TCO.

## 15. Acceptance Criteria

The intent model is accepted when all object shapes are defined, feedback-to-label mapping is deterministic, feedback-to-candidate-intent mapping is deterministic, validation rejects unsafe flags and unsupported values, serialization round trips deterministically, feedback intents are not feedback records, learning signal intents are not dataset labels, candidate intents are not candidates, no feedback is persisted, no label is created, no candidate is created automatically, no recommendation truth is changed, no scoring is changed, no Phase 4I mutation occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
