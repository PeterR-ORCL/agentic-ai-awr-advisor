# Phase 7AR Screen 2 Governance Bridge

## 1. Purpose

Phase 7AR defines the local Screen 2 workflow bridge to governance for the Agentic AI AWR Advisor project.

The Screen 2 workflow bridge produces governance routing recommendations only. It does not perform governance actions.

## 2. Scope

The scope is local deterministic bridge metadata, diagnostic review routing, evidence review routing, candidate request intent metadata, governance action preview metadata, validation helpers, serialization/deserialization helpers, documentation, and tests.

Phase 7AR maps Screen 2 diagnostic and evidence review decisions to proposed future governance routes such as parser review, scoring review, recommendation review, evidence validation, source review, learning candidate request, human review, or closure.

## 3. Non-Goals

Phase 7AR does not add Screen 2 approval UI, dashboard buttons, dashboard forms, backend calls, CLI commands, governed write-path invocation, governance persistence, real learning candidates, real parser candidates, real scoring review records, real recommendation review records, governance state transitions, `run_analysis.py` calls, Phase 4I mutation, parser/scoring/recommendation behavior changes, diagnostic truth changes, dashboard behavior changes, CLI behavior changes, or Phase 8 sizing/TCO.

The bridge does not execute governance actions. The bridge does not persist governance records. The bridge does not create candidates automatically. Candidate intents are not candidates.

## 4. Governance Bridge Is Not Governance Execution

Governance bridge records are previews and routing recommendations.

They can explain where a future workflow should send a review, but they cannot write governance records, transition governance state, invoke the governed write path, create candidates, call services, or change runtime behavior.

## 5. Diagnostic Review Routing

Diagnostic review routing maps `DiagnosticReviewRecord` decisions to proposed route types.

`confirm` routes to `close_review`, `dispute` routes to `human_review`, `insufficient_evidence` routes to `evidence_validation`, `needs_parser_review` routes to `parser_review`, `needs_scoring_review` routes to `scoring_review`, `needs_recommendation_review` routes to `recommendation_review`, and `needs_learning_candidate` routes to `learning_candidate_request`.

`add_reviewer_note` routes to `human_review` when review notes exist and `no_action` when there is no review context.

## 6. Evidence Review Routing

Evidence review routing maps `EvidenceReviewRecord` recommendation flags and evidence posture to proposed route types.

`parser_review_recommended` creates a parser route. `scoring_review_recommended` creates a scoring route. `recommendation_review_recommended` creates a recommendation route. `source_review_recommended` creates a source route. Missing, unavailable, unsupported, or unreliable evidence can create evidence validation routing.

Multiple flags create routes in deterministic order: parser review, scoring review, recommendation review, source review, evidence validation, human review, learning candidate request, and close review.

## 7. Candidate Request Intent

Candidate request intents describe that a future governed workflow may create a candidate.

Candidate intents are not candidates. They do not create records, candidate ids in the learning candidate model, parser mappings, scoring records, recommendation rules, or governance transitions.

## 8. Route Types

Supported route types are `no_action`, `close_review`, `human_review`, `parser_review`, `scoring_review`, `recommendation_review`, `evidence_validation`, `source_review`, and `learning_candidate_request`.

## 9. Route Targets

Supported route targets are `parser_governance`, `scoring_governance`, `recommendation_governance`, `evidence_quality`, `source_quality`, `learning_candidate_queue`, `human_review_queue`, and `review_closure`.

## 10. Governance Workflows

Supported governance workflows are `parser_mapping_review`, `scoring_review`, `recommendation_rule_review`, `evidence_availability_review`, `source_validation_review`, `learning_candidate_review`, `human_review`, and `closure`.

## 11. Candidate Type Mapping

`needs_parser_review` and `parser_gap` map to `parser_mapping_candidate` intent.

`needs_scoring_review` and missing `domain_score` evidence map to `scoring_weight_review_candidate` intent.

`needs_recommendation_review` and `recommendation_context` issues map to `recommendation_rule_candidate` intent.

`needs_learning_candidate`, `insufficient_evidence`, `source_not_collected`, and `source_misconfigured` map to `validation_candidate` intent unless recommendation context requires recommendation rule review.

This creates candidate request intents only. It does not create actual candidates.

## 12. Deterministic Routing Rules

Routes and intents use deterministic ids derived from review ids, route types, route targets, and candidate types.

The bridge uses no random UUIDs, timestamps, database sequences, network calls, or external services for identifiers.

## 13. Runtime Truth Boundary

No diagnostic truth is changed.

Routes, candidate intents, and bridge results are governance preview metadata. They do not change primary issue, secondary issue, severity, confidence, score, evidence values, parser output, scoring behavior, recommendation behavior, or deterministic runtime truth.

## 14. Phase 4I Boundary

No Phase 4I mutation occurs.

All route and bridge result records require `phase4i_mutation_requested=false`. The bridge cannot modify the Phase 4I payload or contract.

## 15. Parser Review Boundary

Parser review routes are recommendations only.

No parser/scoring/recommendation behavior changes occur. Parser routes do not create parser candidates, update parser mappings, alter parser output, or call parser modules.

## 16. Scoring Review Boundary

Scoring review routes are recommendations only.

Scoring routes do not change scoring weights, severity, confidence, domain scores, adaptive scoring behavior, or runtime scoring.

## 17. Recommendation Review Boundary

Recommendation review routes are recommendations only.

Recommendation routes do not create recommendation rules, change recommendations, change recommendation ranking, or mutate recommendation truth.

## 18. Source / Evidence Review Boundary

Source and evidence review routes are recommendations only.

They do not read files, call Object Storage, query databases, validate credentials, or change evidence values.

## 19. Relationship to 7AP

Phase 7AP defined the Screen 2 review workflow boundary.

Phase 7AR stays inside that boundary by adding local bridge preview metadata only and preserving the rule that review does not mutate diagnostic truth.

## 20. Relationship to 7AQ

Phase 7AQ defined local diagnostic review and evidence review object models.

Phase 7AR consumes those local records and produces proposed route metadata. It does not mutate 7AQ records and does not persist them.

## 21. Relationship to Future 7AS

Future 7AS may add Screen 2 approval UI and review panel behavior.

Phase 7AR does not add UI, buttons, forms, dashboard write controls, or dashboard behavior.

## 22. Relationship to Future 7AT

Future 7AT may validate and certify the Screen 2 diagnostic review workflow block.

Phase 7AR adds bridge models and local tests only. It does not run final block readiness checks.

## 23. Acceptance Criteria

Phase 7AR is accepted when the Screen 2 governance bridge model exists, governance route model exists, candidate request intent model exists, bridge result model exists, diagnostic review routing works, evidence review routing works, candidate intents are created as intents only, validation rejects unsafe fields, serialization round trips, no governance action is executed, no governance record is persisted, no candidate is created automatically, candidate intents are not candidates, no diagnostic truth is changed, no Phase 4I mutation occurs, no parser/scoring/recommendation behavior changes occur, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
