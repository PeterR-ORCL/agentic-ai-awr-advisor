# Phase 7 Materialization Artifact Model

## Purpose

The Phase 7N materialization artifact model represents a local controlled work item created from one approved learning candidate. Artifacts are deterministic records for implementation review, validation planning, rollback planning, and audit. No artifact activates runtime.

## Artifact Object Shape

The artifact object contains materialization_id, source_candidate_id, candidate_type, affected_component, affected_domain, proposed_change_summary, proposed_artifact_type, implementation_reference, validation_requirements, rollback_plan, runtime_influence_requested, runtime_influence_granted, status, actor, approval_reference, created_at, reviewed_by, validation_reference, source_evidence, and semantic_context.

## Artifact Types

Supported artifact types are parser_mapping_artifact, scoring_review_artifact, recommendation_rule_artifact, dashboard_wording_artifact, dashboard_interaction_artifact, governance_workflow_artifact, semantic_summary_artifact, documentation_artifact, and validation_artifact.

## Candidate Type Mapping

parser_mapping_candidate maps to parser_mapping_artifact. scoring_weight_review_candidate maps to scoring_review_artifact. recommendation_rule_candidate maps to recommendation_rule_artifact. dashboard_wording_candidate maps to dashboard_wording_artifact. dashboard_interaction_candidate maps to dashboard_interaction_artifact. governance_workflow_candidate maps to governance_workflow_artifact. semantic_summary_candidate maps to semantic_summary_artifact. documentation_candidate maps to documentation_artifact. validation_candidate maps to validation_artifact.

## Runtime-Sensitive Artifact Types

Runtime-sensitive artifact types are parser_mapping_artifact, scoring_review_artifact, and recommendation_rule_artifact. They can describe future work that may require runtime-sensitive code or configuration changes in later phases, but Phase 7N does not perform those changes.

## Non-Runtime Artifact Types

Non-runtime or indirect artifact types are dashboard_wording_artifact, dashboard_interaction_artifact, governance_workflow_artifact, semantic_summary_artifact, documentation_artifact, and validation_artifact. They describe proposed changes only. They do not directly mutate dashboard files, CLI behavior, documentation, workflow state, parser behavior, scoring behavior, decision behavior, or recommendation behavior during Phase 7N.

## Required Fields

source_candidate_id, candidate_type, proposed_change_summary, proposed_artifact_type, validation_requirements, status, actor, runtime_influence_requested, runtime_influence_granted, and source_evidence are required model fields. runtime-sensitive artifacts also require rollback_plan. created_at defaults to None and the model does not generate current timestamps.

## Validation Requirements

Each artifact must include validation_requirements that cover the required concepts for its artifact type. Missing artifact type requirements fail validation. Runtime-sensitive artifacts require stronger validation because they may describe parser, scoring, or recommendation work for future phases.

## Statuses

Supported statuses are PROPOSED, APPROVED_FOR_MATERIALIZATION, MATERIALIZED, VALIDATED, REJECTED, ROLLED_BACK, and CLOSED. The default status is non-active. MATERIALIZED is not runtime active. VALIDATED is not runtime active by itself. CLOSED and ROLLED_BACK are not runtime active. No status changes runtime influence in Phase 7N.

## Runtime Influence Fields

runtime_influence_granted=false by default and is enforced by validation. runtime_influence_requested is advisory/request only and may document a future review request. It does not activate runtime and does not grant runtime influence. Deserialization rejects artifacts that claim granted runtime influence.

## Deterministic ID Rules

Materialization IDs are deterministic and use stable inputs: source candidate id, artifact type, and affected component. The format is MAT-ARTIFACT-TYPE-SOURCE-CANDIDATE-ID-AFFECTED-COMPONENT after identifier normalization. IDs do not use random UUIDs, timestamps, database sequences, network services, or external systems.

## Serialization Rules

Artifacts serialize to deterministic dictionaries with a fixed field order. Deserialization validates the same artifact structure, supported statuses, supported artifact types, candidate-to-artifact mapping, validation requirements, rollback requirements, actor requirements, source evidence shape, and runtime influence boundary. Serialization performs no DB writes and no runtime imports.

## Parser Validation Requirements

Parser artifacts must include parser tests, AWR regression validation, Phase 4I contract validation, unknown signal safety, and scoring regression check. Parser artifacts are local controlled work items only. There is no automatic parser mutation and no automatic materialization into parser code.

## Scoring Validation Requirements

Scoring artifacts must include versioned scoring config, before/after comparison, scoring regression tests, Phase 4I scores contract validation, and rollback plan. Scoring artifacts are local controlled work items only. There is no automatic scoring mutation and no automatic materialization into scoring configuration.

## Recommendation Validation Requirements

Recommendation artifacts must include versioned recommendation rule/config, recommendation regression tests, evidence mapping validation, Phase 4I recommendations contract validation, and rollback plan. Recommendation artifacts are local controlled work items only. There is no automatic recommendation mutation and no automatic materialization into recommendation rules.

## Rollback Requirements

Runtime-sensitive artifacts require rollback_plan. Non-runtime artifacts can carry an empty or lower-burden rollback plan when the proposed work is indirect, but the field remains part of the artifact shape. Rollback planning is audit context only and does not activate runtime.

## Non-Goals

The model does not write to a database, call OCI, call Oracle Agent Memory, call a semantic recall service, call an LLM, use a network dependency, import runtime parser/scoring/decision/recommendation modules, import dashboard modules, import CLI modules, change Phase 4I output, alter dashboard behavior, or alter CLI behavior.

## Acceptance Criteria

The model is accepted when it can create artifacts only from APPROVED_FOR_IMPLEMENTATION candidates, rejects non-approved candidates, maps every supported candidate type to exactly one artifact type, enforces runtime-sensitive validation and rollback requirements, requires an actor, preserves source evidence and reviewer-assist semantic context, serializes and deserializes deterministically, keeps runtime_influence_granted=false, treats runtime_influence_requested as request-only, performs no automatic parser mutation, performs no automatic scoring mutation, performs no automatic recommendation mutation, keeps artifacts as local controlled work items, and keeps deterministic runtime authoritative.
