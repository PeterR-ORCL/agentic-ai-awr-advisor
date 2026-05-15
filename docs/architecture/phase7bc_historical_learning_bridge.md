# Phase 7BC Historical Review to Learning Candidate Bridge

## 1. Purpose

Phase 7BC defines a local, deterministic bridge from Screen 4 historical review metadata to future learning candidate intents, learning signal intents, and governance route intents.

The bridge lets recurring historical behavior, disputed trends, false positive anomaly claims, missing evidence, baseline concerns, and scoring review requests become safe intent metadata.

## 2. Scope

Phase 7BC adds local intent models, deterministic routing helpers, bridge helpers, serialization/deserialization helpers, documentation, tests, architecture index links, and a disabled/preview-only Screen 4 historical review panel.

The scope is intent generation only. Candidate intents are not candidates. Learning signal intents are not dataset labels.

## 3. Non-Goals

Phase 7BC does not create actual learning candidates, create dataset labels, persist candidate intents, persist review records, persist baseline selections, invoke governed write path, execute backend code, mutate historical truth, mutate trend truth, mutate anomaly truth, change scoring behavior, change recommendations, change parser output, mutate Phase 4I, implement Phase 7BD validation/certification, or implement Phase 8 sizing/TCO.

No candidates are created automatically. No dataset labels are created. No trend/anomaly truth is changed. No scoring behavior is changed. No Phase 4I mutation occurs. Deterministic runtime remains authoritative. Phase 8 sizing/TCO is not implemented.

## 4. Historical Review to Learning Bridge Is Not Candidate Creation

Historical review can create candidate intents only.

Candidate intents are not candidates. They are local metadata that a future governed workflow may inspect. A candidate intent does not imply approval, persistence, materialization, runtime influence, or Phase 4I mutation.

## 5. HistoricalLearningCandidateIntent

`HistoricalLearningCandidateIntent` represents a local intent for a future learning candidate derived from historical review.

Fields include `intent_id`, `source_review_id`, `source_trend_review_id`, `source_anomaly_review_id`, `source_baseline_candidate_id`, `candidate_type`, `affected_domain`, `affected_component`, `rationale`, `source_evidence`, `confidence`, `requires_human_review`, `candidate_created`, `runtime_influence`, `phase4i_mutation_requested`, and `notes`.

Rules require supported candidate type, rationale, list-valued source evidence, confidence between 0.0 and 0.95, `requires_human_review=true`, `candidate_created=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 6. HistoricalLearningSignalIntent

`HistoricalLearningSignalIntent` represents a local learning signal intent derived from historical review.

Fields include `signal_intent_id`, `signal_type`, `label_name`, `label_value`, source review references, affected domain, confidence, `dataset_label_created`, `requires_human_review`, `runtime_influence`, and notes.

Learning signal intents are not dataset labels. They require `dataset_label_created=false`, `requires_human_review=true`, and `runtime_influence=false`.

## 7. HistoricalGovernanceRoute

`HistoricalGovernanceRoute` represents a local governance route intent.

Fields include `route_id`, `route_type`, `route_target`, `source_review_id`, `affected_domain`, `recommended_action`, `governance_workflow`, `route_status`, `governance_action_performed`, `candidate_created`, `runtime_influence`, `phase4i_mutation_requested`, and `notes`.

No governance actions are executed. Routes require `governance_action_performed=false`, `candidate_created=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 8. HistoricalReviewLearningBridgeResult

`HistoricalReviewLearningBridgeResult` summarizes the local bridge output.

It counts source reviews, candidate intents, learning signal intents, and governance routes. It also carries the emitted intent lists, bridge status, warnings, denied reasons, next steps, and hard safety flags.

Rules require `candidates_created=false`, `dataset_labels_created=false`, `governance_actions_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 9. Candidate Type Mapping

Candidate type mappings include:

- `request_trend_aware_scoring_review` -> `scoring_weight_review_candidate`
- `request_anomaly_sensitivity_review` -> `scoring_weight_review_candidate`
- `request_scoring_threshold_review` -> `scoring_weight_review_candidate`
- `request_learning_candidate` -> `validation_candidate` by default
- `mark_anomaly_false_positive` -> `validation_candidate`
- `dispute_trend` -> `validation_candidate`
- insufficient evidence decisions -> `validation_candidate`
- recurring pattern context -> `scoring_weight_review_candidate` or `recommendation_rule_candidate` depending supplied context

These mappings produce intent metadata only. No real candidates are created.

## 10. Learning Signal Mapping

Learning signal mappings include trend review signal, anomaly review signal, recurrence signal, false positive signal, evidence quality signal, baseline quality signal, and scoring review signal.

Label names include `issue_recurred`, `false_positive`, `false_negative`, `no_change`, `risk_confirmed`, and `unknown_outcome`.

No dataset labels are created.

## 11. Governance Route Mapping

Governance route mappings include scoring review, recommendation review, evidence validation, human review, learning candidate request, and documentation review.

Route targets include scoring governance, recommendation governance, evidence quality, human review queue, learning candidate queue, and documentation queue.

No governance actions are executed.

## 12. Runtime Truth Boundary

The bridge emits local intent metadata only. It does not mutate historical truth, dashboard truth, parser output, recommendation truth, or runtime behavior.

Deterministic runtime remains authoritative.

## 13. Trend / Anomaly Truth Boundary

No trend/anomaly truth is changed.

Historical review decisions such as disputed trend, insufficient trend evidence, false positive anomaly, or anomaly sensitivity review request remain reviewer assessment and intent metadata only.

## 14. Scoring Boundary

No scoring behavior is changed.

Scoring-related review requests map to scoring review candidate intents or governance route intents. They do not create scoring review records, change deterministic score, change trend-aware scoring, change confidence, or alter runtime scoring.

## 15. Dataset Label Boundary

Learning signal intents are not dataset labels.

They do not write training rows, feature/label records, outcome labels, model labels, or backtesting labels. Dataset label creation remains a future governed workflow.

## 16. Candidate Creation Boundary

Candidate intents are not candidates.

No candidate is created automatically. Candidate creation, candidate governance, materialization, and runtime integration remain separate governed phases.

## 17. Relationship to 7AZ

Phase 7AZ established the Screen 4 historical review workflow boundary. Phase 7BC stays inside that boundary by emitting intent metadata and disabled preview UI only.

## 18. Relationship to 7BA

Phase 7BA defined baseline candidate and comparison context metadata. Phase 7BC may reference baseline ids and comparison context ids as source evidence, but it does not make baselines official or persist baseline records.

## 19. Relationship to 7BB

Phase 7BB defined trend/anomaly review records, requests, validations, and routing intent metadata. Phase 7BC consumes those local review records to produce intent metadata only.

## 20. Relationship to Future 7BD

Future 7BD may define Screen 4 workflow validation, readiness, certification, and operational documentation.

Phase 7BC does not implement 7BD and does not certify the full Screen 4 workflow block.

## 21. Relationship to Phase 8

Phase 8 sizing/TCO is out of scope.

Historical intent metadata may later inform sizing or what-if workflows, but Phase 7BC does not implement capacity planning, cost modeling, EM extract, sizing, TCO, or what-if advisory.

Phase 8 sizing/TCO is not implemented.

## 22. Acceptance Criteria

Phase 7BC acceptance requires local bridge models, deterministic IDs, mapping helpers, validation helpers, serialization/deserialization helpers, documentation, disabled Screen 4 preview UI, and tests.

Acceptance also requires these guarantees: candidate intents are not candidates, learning signal intents are not dataset labels, no candidates are created automatically, no dataset labels are created, no trend/anomaly truth is changed, no scoring behavior is changed, no Phase 4I mutation occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
