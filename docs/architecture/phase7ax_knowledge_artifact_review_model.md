# Phase 7AX Knowledge Artifact Review Model

## 1. Purpose

Phase 7AX defines local deterministic object shapes and validation rules for Screen 1 knowledge artifact review workflow metadata.

The model supports future artifact review, decision, candidate linkage intent, and materialization linkage intent without persistence or runtime mutation.

## 2. KnowledgeArtifactReviewRecord Object Shape

`KnowledgeArtifactReviewRecord` contains:

- `artifact_review_id`
- `artifact_id`
- `artifact_type`
- `artifact_title`
- `source_request_id`
- `review_decision`
- `review_status`
- `reviewer_actor_id`
- `actor_audit_context`
- `review_notes`
- `linked_candidate_intent_id`
- `linked_materialization_intent_id`
- `linked_parser_review_id`
- `linked_scoring_review_id`
- `linked_recommendation_review_id`
- `write_performed`
- `artifact_approved`
- `artifact_rejected`
- `artifact_revision_requested`
- `materialization_created`
- `candidate_created`
- `runtime_influence`
- `phase4i_mutation_requested`
- `created_at`
- `notes`

It is local metadata only. No artifact review is persisted.

## 3. KnowledgeArtifactReviewRequest Object Shape

`KnowledgeArtifactReviewRequest` contains:

- `artifact_review_request_id`
- `artifact_id`
- `requested_decision`
- `actor_id`
- `actor_audit_context`
- `payload`
- `validation_status`
- `can_route_to_write_path`
- `write_performed`
- `artifact_approved`
- `artifact_rejected`
- `artifact_revision_requested`
- `materialization_created`
- `candidate_created`
- `runtime_influence`
- `phase4i_mutation_requested`
- `notes`

`can_route_to_write_path` is future eligibility only and does not invoke a write path.

## 4. KnowledgeArtifactDecision Object Shape

`KnowledgeArtifactDecision` contains:

- `artifact_decision_id`
- `artifact_review_id`
- `decision_type`
- `decision_status`
- `actor_id`
- `actor_audit_context`
- `decision_summary`
- `requires_followup`
- `followup_type`
- `write_performed`
- `materialization_created`
- `candidate_created`
- `runtime_influence`
- `phase4i_mutation_requested`
- `created_at`
- `notes`

The decision object is not approval, rejection, revision persistence, candidate creation, or materialization.

## 5. ArtifactCandidateLinkIntent Object Shape

`ArtifactCandidateLinkIntent` contains:

- `link_intent_id`
- `artifact_id`
- `candidate_type`
- `affected_component`
- `affected_domain`
- `rationale`
- `source_evidence`
- `candidate_created`
- `requires_human_review`
- `runtime_influence`
- `notes`

The candidate link intent is not a candidate. No candidate is created automatically.

## 6. ArtifactMaterializationLinkIntent Object Shape

`ArtifactMaterializationLinkIntent` contains:

- `materialization_intent_id`
- `artifact_id`
- `materialization_type`
- `affected_component`
- `affected_domain`
- `rationale`
- `materialization_created`
- `runtime_influence`
- `phase4i_mutation_requested`
- `notes`

The materialization link intent is not a materialization artifact. No materialization artifact is created.

## 7. KnowledgeArtifactReviewValidation Object Shape

`KnowledgeArtifactReviewValidation` contains:

- `validation_id`
- `artifact_review_request_id`
- `valid`
- `validation_status`
- `requested_decision`
- `actor_present`
- `artifact_present`
- `can_route_to_write_path`
- `write_performed`
- `artifact_approved`
- `artifact_rejected`
- `artifact_revision_requested`
- `materialization_created`
- `candidate_created`
- `denied_reasons`
- `warnings`
- `required_next_steps`
- `runtime_influence`
- `phase4i_mutation_requested`
- `notes`

Validation is metadata only. No artifact review is persisted.

## 8. Artifact Types

Supported artifact types are:

- `parser_mapping_guidance`
- `scoring_review_guidance`
- `recommendation_rule_guidance`
- `semantic_summary`
- `documentation`
- `validation`
- `materialization_reference`
- `governance_workflow`
- `unknown`

Unsupported artifact types fail validation.

## 9. Review Decisions

Supported review decisions are:

- `approve_for_review`
- `reject_artifact`
- `request_revision`
- `link_to_candidate`
- `link_to_materialization`
- `link_to_parser_review`
- `link_to_scoring_review`
- `link_to_recommendation_review`
- `mark_superseded`
- `add_review_note`

Unsupported review decisions fail validation.

## 10. Review Statuses

Supported review statuses are:

- `proposed`
- `under_review`
- `approved_for_review`
- `rejected`
- `needs_revision`
- `linked_to_candidate`
- `linked_to_materialization`
- `superseded`
- `closed`

Unsupported statuses fail validation.

## 11. Follow-Up Types

Supported follow-up types are:

- `none`
- `candidate_review_required`
- `materialization_review_required`
- `parser_review_required`
- `scoring_review_required`
- `recommendation_review_required`
- `artifact_revision_required`
- `human_review_required`

Unsupported follow-up types fail validation.

## 12. Candidate Type Mapping

Candidate type mapping is:

- `parser_mapping_guidance` -> `parser_mapping_candidate`
- `scoring_review_guidance` -> `scoring_weight_review_candidate`
- `recommendation_rule_guidance` -> `recommendation_rule_candidate`
- `semantic_summary` -> `semantic_summary_candidate`
- `documentation` -> `documentation_candidate`
- `validation` -> `validation_candidate`
- `governance_workflow` -> `governance_workflow_candidate`
- `materialization_reference` -> `validation_candidate`

These are link intents only. No real candidates are created.

## 13. Materialization Type Mapping

Materialization type mapping is:

- `parser_mapping_guidance` -> `parser_mapping_artifact`
- `scoring_review_guidance` -> `scoring_review_artifact`
- `recommendation_rule_guidance` -> `recommendation_rule_artifact`
- `semantic_summary` -> `semantic_summary_artifact`
- `documentation` -> `documentation_artifact`
- `validation` -> `validation_artifact`
- `governance_workflow` -> `governance_workflow_artifact`
- `materialization_reference` -> `validation_artifact`

These are materialization link intents only. No materialization artifacts are created.

## 14. Validation Rules

Review records require artifact review id, artifact id, supported artifact type, supported review decision, supported review status, list-based review notes, and runtime safety flags set to false.

Review requests require request id, supported requested decision, payload dictionary, and actor metadata for workflow validation.

Artifact decisions require decision id, artifact review id, supported decision type, supported decision status, actor metadata, supported follow-up type, and runtime safety flags set to false.

Candidate link intents require candidate type, `candidate_created=false`, `requires_human_review=true`, and `runtime_influence=false`.

Materialization link intents require materialization type, `materialization_created=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

Validation results require supported validation status, supported requested decision, list-based denied reasons, list-based warnings, list-based required next steps, and all write/action/materialization/candidate flags false.

## 15. Serialization Rules

All object models serialize to plain dictionaries and deserialize back to equivalent deterministic dataclass records.

Serialization does not persist records. Deserialization validates metadata shape only.

## 16. Deterministic ID Rules

IDs are deterministic and use normalized request metadata. They do not use random UUIDs, timestamps, database sequences, or external services.

Identifier shapes include:

- `SCREEN1-KNOWLEDGE-ARTIFACT-REVIEW-<ARTIFACT>-<DECISION>`
- `SCREEN1-KNOWLEDGE-ARTIFACT-REQUEST-<ARTIFACT>-<DECISION>`
- `SCREEN1-KNOWLEDGE-ARTIFACT-DECISION-<REVIEW>-<DECISION>`
- `SCREEN1-ARTIFACT-CANDIDATE-LINK-INTENT-<ARTIFACT>-<CANDIDATE_TYPE>`
- `SCREEN1-ARTIFACT-MATERIALIZATION-LINK-INTENT-<ARTIFACT>-<MATERIALIZATION_TYPE>`
- `SCREEN1-KNOWLEDGE-ARTIFACT-VALIDATION-<REQUEST_ID>`

## 17. Runtime Safety Rules

Runtime safety flags must remain false:

- `write_performed=false`
- `artifact_approved=false`
- `artifact_rejected=false`
- `artifact_revision_requested=false`
- `materialization_created=false`
- `candidate_created=false`
- `runtime_influence=false`
- `phase4i_mutation_requested=false`

No artifact approval/rejection is executed. No artifact revision request is persisted. No parser/scoring/recommendation behavior changes occur. No Phase 4I mutation occurs. Deterministic runtime remains authoritative.

## 18. Non-Goals

Phase 7AX does not persist artifact review records, approve artifacts at runtime, reject artifacts at runtime, request artifact revision at runtime, create materialization artifacts, create candidates automatically, create parser/scoring/recommendation records, invoke governed write path, call backend services, call `run_analysis.py`, modify parser/scoring/recommendation behavior, mutate Phase 4I, add active dashboard submit behavior, add CLI commands, implement source intake execution, implement parser unknown classification, or implement Phase 8 sizing/TCO.

## 19. Acceptance Criteria

Phase 7AX model work is accepted when all object shapes exist, supported artifact types/review decisions/review statuses/follow-up types validate, unsupported values fail, deterministic IDs are stable, serialization round trips are deterministic, candidate type mappings create link intents only, materialization type mappings create link intents only, no artifact review is persisted, no artifact approval/rejection is executed, no artifact revision request is persisted, no candidate is created automatically, no materialization artifact is created, no parser/scoring/recommendation behavior changes occur, no Phase 4I mutation occurs, deterministic runtime remains authoritative, and Phase 8 sizing/TCO is not implemented.
