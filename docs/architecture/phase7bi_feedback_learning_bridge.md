# Phase 7BI Feedback Learning Bridge

## 1. Purpose

Phase 7BI defines the Screen 5 recommendation feedback-to-learning bridge. The bridge converts recommendation decision metadata, action tracking preview metadata, and outcome capture preview metadata into future feedback, learning signal, and candidate intent records.

## 2. Scope

The scope is local deterministic intent modeling only. Phase 7BI defines recommendation feedback intents, learning signal intents, recommendation candidate intents, bridge result summaries, mapping rules, validation helpers, serialization helpers, and documentation.

## 3. Non-Goals

Phase 7BI does not add UI, add CLI commands, persist feedback records, create dataset labels, create learning candidates, update action records, update outcome records, invoke a governed write path, call backend execution, mutate recommendation truth, mutate scoring, mutate parser behavior, or mutate Phase 4I.

## 4. Feedback-to-Learning Bridge Is Not Persistence

Feedback-to-learning bridge intent is not persistence. Feedback intents are not feedback records, learning signal intents are not dataset labels, and candidate intents are not candidates. The bridge produces reviewable metadata only.

## 5. Recommendation Feedback Intent

`RecommendationFeedbackIntent` records future feedback intent metadata derived from Screen 5 workflow context. It references recommendation, decision, action preview, outcome preview, actor/audit context, feedback type, feedback status, and source payload metadata. `feedback_created=false`, `write_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false` are mandatory.

## 6. Learning Signal Intent

`LearningSignalIntent` records a future learning signal or label intent. It captures recommendation id, outcome status, effectiveness, signal type, label name, label value, confidence, source feedback intent, and source evidence. Learning signal intents are not dataset labels, `dataset_label_created=false`, `requires_human_review=true`, and `runtime_influence=false`.

## 7. Candidate Intent

`RecommendationCandidateIntent` records a future candidate request intent. Candidate intents are not candidates. They preserve source feedback linkage, candidate type, affected domain/component, rationale, and source evidence while enforcing `candidate_created=false`, `requires_human_review=true`, and `runtime_influence=false`.

## 8. Bridge Result

`RecommendationFeedbackBridgeResult` summarizes feedback intents, learning signal intents, and candidate intents for a recommendation. It enforces `feedback_created=false`, `dataset_labels_created=false`, `candidates_created=false`, `write_performed=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 9. Feedback Types

Supported feedback types are `accepted`, `rejected`, `deferred`, `not_applicable`, `effective`, `ineffective`, `partially_effective`, `improved`, `worsened`, `no_change`, `issue_recurred`, `inconclusive`, `false_positive`, `false_negative`, and `needs_review`.

## 10. Learning Signal Types

Supported learning signal types are `recommendation_outcome`, `action_effectiveness`, `performance_result`, `recurrence_signal`, `false_positive_signal`, `false_negative_signal`, `validation_signal`, and `review_signal`.

## 11. Label Mapping

Decision and outcome metadata may map to label intents such as `recommendation_accepted`, `recommendation_rejected`, `action_effective`, `action_ineffective`, `performance_improved`, `performance_worsened`, `no_change`, `issue_recurred`, `false_positive`, `false_negative`, and `unknown_outcome`. No label is created in Phase 7BI.

## 12. Candidate Intent Mapping

Rejected and not applicable feedback maps to `recommendation_rule_candidate` intent. Ineffective action feedback maps to `recommendation_rule_candidate` intent. False positive and false negative feedback maps to `validation_candidate` intent. Issue recurrence maps to `scoring_weight_review_candidate` or `recommendation_rule_candidate` according to supplied context. Improved and effective feedback maps to `documentation_candidate` or validation review context. These mappings create candidate intents only, and no candidate is created automatically.

## 13. Confidence Rules

Confidence is deterministic, local, and bounded from `0.0` to `0.95`. Inconclusive and unknown outcomes receive lower confidence. No Phase 7BI confidence value is `1.0`, and confidence never grants runtime authority.

## 14. Runtime Truth Boundary

Deterministic runtime remains authoritative. Feedback intents, learning signal intents, candidate intents, and bridge results do not alter runtime behavior.

## 15. Phase 4I Boundary

No Phase 4I mutation occurs. Phase 7BI does not alter Phase 4I recommendations, scoring, diagnostics, evidence, or output contract semantics.

## 16. Recommendation Truth Boundary

No recommendation truth is changed. No recommendation ranking, text, evidence, action sequencing, or recommendation rule runtime state is changed.

## 17. Dataset Label Boundary

Learning signal intents are not dataset labels. Phase 7BI does not update the feature/label dataset and no label is created.

## 18. Candidate Creation Boundary

Candidate intents are not candidates. Phase 7BI does not create learning candidates, validation candidates, scoring review candidates, documentation candidates, or recommendation rule candidates.

## 19. Relationship to 7BE

Phase 7BE established the Screen 5 recommendation/action/outcome workflow boundary. Phase 7BI uses that boundary by producing intents only and preserving actor, audit, governed write path, and runtime-truth constraints.

## 20. Relationship to 7BF

Phase 7BF defined local recommendation decision metadata. Phase 7BI can map those decision objects into feedback intent and label intent metadata without persisting recommendation decision records.

## 21. Relationship to 7BG

Phase 7BG defined action tracking preview metadata. Phase 7BI can include action preview identifiers and status metadata as source context only. It does not update action records.

## 22. Relationship to 7BH

Phase 7BH defined outcome capture preview metadata. Phase 7BI can map outcome statuses and effectiveness metadata into learning signal intents only. It does not persist outcome records or create labels.

## 23. Relationship to Future 7BJ

Future 7BJ may validate and certify the full Screen 5 recommendation/action/outcome workflow block. Phase 7BI only supplies the bridge intent model and local tests.

## 24. Relationship to Phase 8

Phase 8 sizing/TCO is not implemented. Phase 7BI does not perform sizing, TCO, what-if advisory, capacity planning, or cost modeling.

## 25. Acceptance Criteria

Phase 7BI is accepted when the local bridge model exists, feedback intent model exists, learning signal intent model exists, candidate intent model exists, bridge result model exists, feedback-to-label mapping exists, feedback-to-candidate-intent mapping exists, validation rejects unsafe write/runtime flags, serialization round trips deterministically, no feedback is persisted, no label is created, no candidate is created automatically, no recommendation truth is changed, no scoring is changed, no Phase 4I mutation occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
