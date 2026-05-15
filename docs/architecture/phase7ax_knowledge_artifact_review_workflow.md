# Phase 7AX Knowledge Artifact Review Workflow

## 1. Purpose

Phase 7AX defines the local knowledge artifact review workflow and intention model for future Screen 1 ingestion and parser governance workflows.

Knowledge artifact review creates local review and intention models only. It does not approve, reject, materialize, or activate artifacts.

## 2. Scope

The scope is local knowledge artifact review records, artifact review request records, artifact decision records, artifact-to-candidate link intents, artifact-to-materialization link intents, artifact review validation metadata, deterministic mappings, validation helpers, serialization helpers, deserialization helpers, a disabled Screen 1 preview panel, tests, and architecture documentation.

Phase 7AX supports future review of knowledge artifacts such as parser mapping guidance, scoring review guidance, recommendation rule guidance, semantic summary artifacts, documentation artifacts, validation artifacts, materialization references, and governance workflow artifacts.

## 3. Non-Goals

Phase 7AX does not persist artifact review records. No artifact review is persisted.

Phase 7AX does not approve artifacts at runtime, reject artifacts at runtime, request artifact revision at runtime, materialize artifacts, create materialization records, create candidates automatically, create parser mapping records, create scoring review records, create recommendation rule records, invoke governed write path, call backend services, call `run_analysis.py`, mutate parser behavior, mutate parser output, mutate scoring behavior, mutate recommendation behavior, mutate decision behavior, mutate Phase 4I, add active dashboard submit behavior, add active backend calls, add CLI commands, implement source intake execution, implement parser unknown classification, or implement Phase 8 sizing/TCO.

No artifact approval/rejection is executed. No artifact revision request is persisted. No candidate is created automatically. No materialization artifact is created. No parser/scoring/recommendation behavior changes occur. No Phase 4I mutation occurs.

## 4. Knowledge Artifact Review Is Not Materialization

Knowledge artifact review is governed review metadata.

A review record, request, decision, candidate link intent, materialization link intent, validation result, or dashboard preview does not materialize an artifact, activate an artifact, grant runtime influence, or make an artifact parser/scoring/recommendation truth.

Deterministic runtime remains authoritative.

## 5. KnowledgeArtifactReviewRecord

`KnowledgeArtifactReviewRecord` is a local review record for a knowledge artifact.

Fields are:

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

The required safety flags are `write_performed=false`, `artifact_approved=false`, `artifact_rejected=false`, `artifact_revision_requested=false`, `materialization_created=false`, `candidate_created=false`, `runtime_influence=false`, and `phase4i_mutation_requested=false`.

## 6. KnowledgeArtifactReviewRequest

`KnowledgeArtifactReviewRequest` is a future request object for artifact review workflow.

Fields are:

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

`can_route_to_write_path` is future eligibility only. It does not invoke the governed write path and does not persist review state.

## 7. KnowledgeArtifactDecision

`KnowledgeArtifactDecision` is a local decision object.

Fields are:

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

The decision object is metadata only. It does not execute approval, rejection, revision, candidate creation, or materialization.

## 8. ArtifactCandidateLinkIntent

`ArtifactCandidateLinkIntent` is a local intent to link an artifact to a future candidate.

Fields are:

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

Candidate link intent is not candidate creation. No candidate is created automatically.

## 9. ArtifactMaterializationLinkIntent

`ArtifactMaterializationLinkIntent` is a local intent to link an artifact to future materialization.

Fields are:

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

Materialization link intent is not materialization. No materialization artifact is created.

## 10. KnowledgeArtifactReviewValidation

`KnowledgeArtifactReviewValidation` is a validation object.

Fields are:

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

Validation is metadata only. It does not persist review state or execute artifact actions.

## 11. Artifact Types

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

## 12. Review Decisions

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

These decisions are local review intent. They are not runtime approval, rejection, revision, linkage, or materialization.

## 13. Review Statuses

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

Statuses are local review state. They are not artifact runtime state.

## 14. Follow-Up Types

Supported follow-up types are:

- `none`
- `candidate_review_required`
- `materialization_review_required`
- `parser_review_required`
- `scoring_review_required`
- `recommendation_review_required`
- `artifact_revision_required`
- `human_review_required`

Follow-up type is routing metadata only.

## 15. Candidate Type Mapping

Artifact types map to candidate link intent types:

- `parser_mapping_guidance` -> `parser_mapping_candidate`
- `scoring_review_guidance` -> `scoring_weight_review_candidate`
- `recommendation_rule_guidance` -> `recommendation_rule_candidate`
- `semantic_summary` -> `semantic_summary_candidate`
- `documentation` -> `documentation_candidate`
- `validation` -> `validation_candidate`
- `governance_workflow` -> `governance_workflow_candidate`
- `materialization_reference` -> `validation_candidate`

These are candidate link intents only. No real candidates are created.

## 16. Materialization Type Mapping

Artifact types map to materialization link intent types:

- `parser_mapping_guidance` -> `parser_mapping_artifact`
- `scoring_review_guidance` -> `scoring_review_artifact`
- `recommendation_rule_guidance` -> `recommendation_rule_artifact`
- `semantic_summary` -> `semantic_summary_artifact`
- `documentation` -> `documentation_artifact`
- `validation` -> `validation_artifact`
- `governance_workflow` -> `governance_workflow_artifact`
- `materialization_reference` -> `validation_artifact`

These are materialization link intents only. No materialization artifacts are created.

## 17. Runtime Truth Boundary

Knowledge artifact review metadata is not runtime truth.

Phase 7AX does not change parser behavior, parser output, scoring behavior, recommendation behavior, decision behavior, materialization state, runtime gate state, dashboard truth, generated dashboard artifacts, CLI behavior, database state, memory state, or adaptive runtime state.

Deterministic runtime remains authoritative.

## 18. Phase 4I Boundary

Phase 4I remains protected.

Knowledge artifact review state cannot update Phase 4I, parser output, scoring output, decision output, recommendation output, dashboard payload shape, or generated dashboard artifacts.

No Phase 4I mutation occurs.

## 19. Candidate Creation Boundary

Artifact candidate link intent may identify a candidate type for future review.

The intent is not a candidate. No candidate is created automatically.

## 20. Materialization Boundary

Artifact materialization link intent may identify a materialization type for future review.

The intent is not a materialization artifact. No materialization artifact is created.

## 21. Relationship to 7AU

Phase 7AU defined the Screen 1 ingestion/parser governance workflow boundary.

Phase 7AX implements the local knowledge artifact review and intention model allowed by that boundary. It preserves the 7AU rule that artifact review is governed and does not materialize artifacts or mutate runtime behavior.

## 22. Relationship to 7AV

Phase 7AV defined source intake request, validation, and preview models.

Phase 7AX may reference source request ids, but it does not perform source intake, read files, call object storage, query databases, or execute backend analysis.

## 23. Relationship to 7AW

Phase 7AW defined parser unknown review workflow and parser mapping/backlog intents.

Phase 7AX may link an artifact to future parser review metadata, but it does not classify parser unknowns, create parser mappings, create parser candidates, create backlog items, or change parser output.

## 24. Relationship to Future 7AY

Future 7AY may validate and certify the Screen 1 workflow block.

Phase 7AX adds only local artifact review/intention models, preview UI, tests, and documentation. It does not implement final block readiness or certification.

## 25. Relationship to Phase 8

Phase 8 sizing/TCO and what-if advisory are not implemented.

Phase 7AX does not implement EM Extract, capacity planning, cost modeling, sizing recommendations, or what-if advisory.

## 26. Acceptance Criteria

Phase 7AX is accepted when knowledge artifact review records, artifact review request records, artifact decision records, artifact candidate link intents, artifact materialization link intents, review validation metadata, validation helpers, serialization helpers, deserialization helpers, preview-only Screen 1 UI, documentation, and tests exist; no artifact review is persisted; no artifact approval/rejection is executed; no artifact revision request is persisted; no candidate is created automatically; no materialization artifact is created; no parser/scoring/recommendation behavior changes occur; no Phase 4I mutation occurs; deterministic runtime remains authoritative; and Phase 8 sizing/TCO is not implemented.
