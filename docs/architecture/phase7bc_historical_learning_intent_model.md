# Phase 7BC Historical Learning Intent Model

## 1. Purpose

Phase 7BC defines the concrete local intent model for bridging Screen 4 historical review metadata to future learning workflows.

The model is deterministic and local-only. It creates intent metadata only.

## 2. HistoricalLearningCandidateIntent Shape

`HistoricalLearningCandidateIntent` has this metadata shape:

- `intent_id`
- `source_review_id`
- `source_trend_review_id`
- `source_anomaly_review_id`
- `source_baseline_candidate_id`
- `candidate_type`
- `affected_domain`
- `affected_component`
- `rationale`
- `source_evidence`
- `confidence`
- `requires_human_review`
- `candidate_created`
- `runtime_influence`
- `phase4i_mutation_requested`
- `notes`

Candidate intents are not candidates. `candidate_created=false`, `requires_human_review=true`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 3. HistoricalLearningSignalIntent Shape

`HistoricalLearningSignalIntent` has this metadata shape:

- `signal_intent_id`
- `signal_type`
- `label_name`
- `label_value`
- `source_review_id`
- `source_trend_review_id`
- `source_anomaly_review_id`
- `affected_domain`
- `confidence`
- `dataset_label_created`
- `requires_human_review`
- `runtime_influence`
- `notes`

Learning signal intents are not dataset labels. `dataset_label_created=false`, `requires_human_review=true`, and `runtime_influence=false`.

## 4. HistoricalGovernanceRoute Shape

`HistoricalGovernanceRoute` has this metadata shape:

- `route_id`
- `route_type`
- `route_target`
- `source_review_id`
- `affected_domain`
- `recommended_action`
- `governance_workflow`
- `route_status`
- `governance_action_performed`
- `candidate_created`
- `runtime_influence`
- `phase4i_mutation_requested`
- `notes`

No governance action is executed. `governance_action_performed=false`, `candidate_created=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 5. HistoricalReviewLearningBridgeResult Shape

`HistoricalReviewLearningBridgeResult` has this metadata shape:

- `bridge_result_id`
- `source_review_count`
- `candidate_intent_count`
- `learning_signal_intent_count`
- `governance_route_count`
- `candidate_intents`
- `learning_signal_intents`
- `governance_routes`
- `bridge_status`
- `candidates_created`
- `dataset_labels_created`
- `governance_actions_performed`
- `runtime_influence`
- `phase4i_mutation_requested`
- `denied_reasons`
- `warnings`
- `required_next_steps`
- `notes`

Bridge results are summaries only. `candidates_created=false`, `dataset_labels_created=false`, `governance_actions_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 6. Candidate Types

Supported candidate intent types are:

- `scoring_weight_review_candidate`
- `recommendation_rule_candidate`
- `validation_candidate`
- `documentation_candidate`
- `parser_mapping_candidate`

No actual candidate object is created in Phase 7BC.

## 7. Signal Types

Supported signal types are:

- `trend_review_signal`
- `anomaly_review_signal`
- `recurrence_signal`
- `false_positive_signal`
- `evidence_quality_signal`
- `baseline_quality_signal`
- `scoring_review_signal`

## 8. Label Names

Supported label names are:

- `issue_recurred`
- `false_positive`
- `false_negative`
- `no_change`
- `risk_confirmed`
- `unknown_outcome`

No dataset labels are created.

## 9. Governance Route Types

Supported governance route types are scoring review, recommendation review, evidence validation, human review, learning candidate request, and documentation review.

Supported route targets are scoring governance, recommendation governance, evidence quality, human review queue, learning candidate queue, and documentation queue.

## 10. Validation Rules

Candidate intent validation requires supported candidate type, non-empty rationale, list-valued source evidence, confidence between 0.0 and 0.95, `requires_human_review=true`, `candidate_created=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

Signal intent validation requires supported signal type, supported label name, confidence between 0.0 and 0.95, `dataset_label_created=false`, `requires_human_review=true`, and `runtime_influence=false`.

Governance route validation requires supported route type, supported route target, non-empty recommended action, `governance_action_performed=false`, `candidate_created=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

Bridge result validation requires list-valued intent collections, supported bridge status, `candidates_created=false`, `dataset_labels_created=false`, `governance_actions_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 11. Serialization Rules

All object types serialize to deterministic dictionaries with explicit fields.

Deserialization reconstructs frozen dataclass objects and reruns validation. Round trips must be stable for the same input.

Serialization is not persistence. It does not write files, write database rows, call services, execute governance, create candidates, create labels, or mutate runtime truth.

## 12. Deterministic ID Rules

IDs are deterministic and based only on supplied metadata:

- `SCREEN4-HIST-CANDIDATE-INTENT-<SOURCE_REVIEW>-<CANDIDATE_TYPE>`
- `SCREEN4-HIST-SIGNAL-INTENT-<SOURCE_REVIEW>-<SIGNAL_TYPE>-<LABEL_NAME>`
- `SCREEN4-HIST-GOVERNANCE-ROUTE-<SOURCE_REVIEW>-<ROUTE_TYPE>-<ROUTE_TARGET>`
- `SCREEN4-HIST-BRIDGE-RESULT-<SOURCE_REVIEW_COUNT>`

IDs use no random UUID, no timestamp, no database sequence, and no external service. The same input creates the same ID.

## 13. Runtime Safety Rules

Runtime safety requires `candidate_created=false`, `dataset_label_created=false`, `candidates_created=false`, `dataset_labels_created=false`, `governance_actions_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

No historical truth, trend truth, anomaly truth, scoring behavior, recommendation behavior, parser output, dashboard behavior, or Phase 4I output is changed.

## 14. Non-Goals

Phase 7BC does not create learning candidates, create labels, persist intents, persist review records, persist baseline selections, execute governance, invoke governed write path, add active controls, call backend code, mutate runtime truth, implement Phase 7BD, or implement Phase 8 sizing/TCO.

## 15. Acceptance Criteria

Acceptance requires deterministic dataclasses, supported constants, validation helpers, deterministic IDs, mapping helpers, bridge helpers, serialization/deserialization helpers, documentation, and tests.

Acceptance also requires these guarantees: candidate intents are not candidates, learning signal intents are not dataset labels, no candidates are created automatically, no dataset labels are created, no trend/anomaly truth is changed, no scoring behavior is changed, no Phase 4I mutation occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
