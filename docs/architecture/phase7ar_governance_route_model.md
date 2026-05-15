# Phase 7AR Governance Route Model

## 1. Purpose

Phase 7AR defines local route, candidate intent, and bridge result object shapes for Screen 2 governance routing recommendations.

The model is preview-only and local-only.

## 2. Screen2GovernanceRoute Object Shape

`Screen2GovernanceRoute` captures route id, source review id, optional source evidence review id, optional source decision id, route type, route target, domain, reason, recommended action, candidate type, governance workflow, actor id, actor audit context, source payload, route status, route eligibility, safety flags, and notes.

Validation requires `governance_action_performed=false`, `candidate_created=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 3. Screen2CandidateRequestIntent Object Shape

`Screen2CandidateRequestIntent` captures intent id, source route id, candidate type, affected component, affected domain, rationale, source evidence references, human review requirement, runtime influence posture, candidate creation posture, and notes.

Candidate intents are not candidates. `requires_human_review=true`, `runtime_influence=false`, and `candidate_created=false` are required.

## 4. Screen2GovernanceBridgeResult Object Shape

`Screen2GovernanceBridgeResult` summarizes route and candidate intent recommendations.

It captures bridge result id, source review id, route count, candidate intent count, route list, candidate intent list, bridge status, safety flags, denied reasons, warnings, required next steps, and notes.

Validation requires `governance_actions_performed=false`, `candidates_created=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 5. Route Types

Supported route types are `no_action`, `close_review`, `human_review`, `parser_review`, `scoring_review`, `recommendation_review`, `evidence_validation`, `source_review`, and `learning_candidate_request`.

## 6. Route Targets

Supported route targets are `parser_governance`, `scoring_governance`, `recommendation_governance`, `evidence_quality`, `source_quality`, `learning_candidate_queue`, `human_review_queue`, and `review_closure`.

## 7. Governance Workflows

Supported governance workflows are `parser_mapping_review`, `scoring_review`, `recommendation_rule_review`, `evidence_availability_review`, `source_validation_review`, `learning_candidate_review`, `human_review`, and `closure`.

## 8. Candidate Type Mapping

Supported candidate intent types are `parser_mapping_candidate`, `scoring_weight_review_candidate`, `recommendation_rule_candidate`, and `validation_candidate`.

Parser routes map to parser mapping candidate intent. Scoring routes map to scoring weight review candidate intent. Recommendation routes map to recommendation rule candidate intent. Evidence validation, source review, and general learning candidate request routes map to validation candidate intent unless recommendation context requires recommendation rule candidate intent.

## 9. Validation Rules

Validation rejects unsupported route types, route targets, workflows, bridge statuses, and candidate types.

Validation also rejects `governance_action_performed=true`, `candidate_created=true`, `candidates_created=true`, `governance_actions_performed=true`, `runtime_influence=true`, and `phase4i_mutation_requested=true`.

## 10. Serialization Rules

Every model has to/from dictionary helpers.

Serialization is deterministic and local. No writes occur. Deserialization validates the same safety flags as direct construction.

## 11. Deterministic ID Rules

Route ids use `SCREEN2-GOV-ROUTE-<REVIEW_ID>-<ROUTE_TYPE>-<TARGET>`.

Candidate intent ids use `SCREEN2-CANDIDATE-INTENT-<ROUTE_ID>-<CANDIDATE_TYPE>`.

Bridge result ids use `SCREEN2-GOV-BRIDGE-<REVIEW_ID>`.

No random UUID, timestamp, database sequence, or external service is used.

## 12. Non-Goals

The model does not execute governance actions, persist governance records, create candidates automatically, call governance services, invoke governed write paths, add UI, call `run_analysis.py`, mutate Phase 4I, change diagnostic truth, or change parser/scoring/recommendation behavior.

## 13. Acceptance Criteria

Phase 7AR route model acceptance requires supported route types, targets, workflows, candidate type mappings, deterministic ids, validation helpers, serialization helpers, routing helpers, and tests.

Acceptance also requires `governance_action_performed=false`, `candidate_created=false`, `candidates_created=false`, `runtime_influence=false`, `phase4i_mutation_requested=false`, no writes occur, no candidates are created automatically, candidate intents are not candidates, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
