# Phase 7D Candidate Generation Engine

## 1. Purpose

Phase 7D adds a deterministic candidate generation engine for the Agentic AI AWR Advisor project. The engine converts already-mined Phase 7B `OutcomePattern` records into Phase 7C `LearningCandidate` proposal records.

Candidate generation is proposal-only. It may propose a learning candidate for review, but generated candidates are not approved, generated candidates are not implemented, and generated candidates are not activated.

## 2. Scope

The Phase 7D engine is local, deterministic, read-only, and safe to import. It accepts caller-provided outcome patterns or caller-provided in-memory records that are explicitly passed to the memory input helper.

Generated candidates keep `status=PROPOSED`, `runtime_influence=false`, and `requires_human_review=true`. The engine performs no persistence, no approval, no materialization, and no runtime activation.

## 3. Non-Goals

Phase 7D does not mine outcomes except when the explicit memory input helper is called. It does not persist candidates to a database, approve candidates, review candidates, materialize candidates, activate candidates, modify runtime analysis, alter parser behavior, alter scoring logic, alter trend or anomaly logic, alter decision logic, alter recommendation logic, or change Phase 4I output contracts.

Phase 7D does not change dashboard diagnostic truth, Screen 2 diagnostic evidence, Screen 5 recommendation truth, dashboard learning visibility, dashboard interactivity, CLI learning commands, governance bridge behavior, semantic candidate context, Oracle Agent Memory behavior, OCI behavior, ADB behavior, environment-variable requirements, network behavior, or LLM behavior.

## 4. Inputs

The primary input is a sequence of Phase 7B outcome pattern records. Records may be `OutcomePattern` objects or plain mappings with equivalent fields.

The explicit memory helper input is an in-memory mapping of record categories to record sequences. This helper may call the Phase 7B `OutcomePatternMiner` locally before generating candidates.

## 5. Outputs

The engine outputs Phase 7C `LearningCandidate` records. Convenience functions may return serialized dictionaries, but no files are written and no records are persisted.

Every generated candidate remains a proposal with `status=PROPOSED`, `runtime_influence=false`, `requires_human_review=true`, `semantic_context=None`, no reviewer, no review notes, no created timestamp, and no materialization reference.

## 6. Pattern-to-Candidate Mapping

`repeated_rejected_recommendation` maps to `recommendation_rule_candidate`.

`poor_outcome_after_action` maps to `recommendation_rule_candidate`.

`recurring_issue_after_action` maps to `recommendation_rule_candidate`.

`repeated_unknown_signal` maps to `parser_mapping_candidate`.

`repeated_feedback_theme` maps to `dashboard_wording_candidate` by default. It maps to `recommendation_rule_candidate` only when the theme clearly relates to recommendation usefulness, actionability, relevance, or helpfulness.

`recurring_domain_issue` maps to `scoring_weight_review_candidate` by default. It maps to `recommendation_rule_candidate` only when the rationale clearly points to recurring action or recommendation behavior.

If an outcome pattern supplies a supported `suggested_candidate_type`, the engine honors that suggestion. If the suggestion is missing or unsupported, the deterministic mapping above is used.

## 7. Candidate Field Population Rules

`candidate_id` is deterministic. It is based on candidate type and `pattern_id` when a pattern id is available. If no pattern id is available, it is based on deterministic candidate content and source evidence.

`candidate_type` comes from the supported suggestion or deterministic pattern mapping. `title` is human-readable and includes the pattern type plus the affected component or domain when available. `description` explains the repeated pattern and states that the candidate is a proposal for human review only.

`source_evidence` is copied from `pattern.source_records`. `structured_sources` includes outcome pattern metadata such as `pattern_id`, `pattern_type`, `recurrence_count`, observed effect, affected component, affected domain, suggested candidate type, and source record count.

`semantic_context remains None in Phase 7D`. Semantic candidate context is future Phase 7E work.

`affected_component` is copied from the pattern when present. Otherwise it is inferred as `parser` for repeated unknown signals, `recommendation` for rejected, poor-outcome, or recurring action patterns, `dashboard` for feedback wording or usability themes, and `scoring` for recurring domain issues by default.

`affected_domain` is copied from the pattern when present. `confidence` is copied from the pattern and clamped to the Phase 7C model range. Confidence is never `1.0`. `rationale` includes the pattern rationale and states that human review is required. `created_at` remains `None`, and `created_by` is `phase7_candidate_generation_engine`.

## 8. Deterministic Generation Rules

Generation uses stable sorting and deterministic candidate identifiers. It does not use random UUIDs, current timestamps, database sequences, semantic search, LLM output, environment variables, network calls, file writes, or external service calls.

The same input produces the same output order and values. Input patterns and memory records are not modified.

## 9. Deduplication Rules

Candidate IDs are deduplicated deterministically. If multiple patterns produce the same candidate id, the engine keeps one candidate, merges source evidence deterministically, merges structured source metadata deterministically, preserves `status=PROPOSED`, preserves `runtime_influence=false`, preserves `requires_human_review=true`, and uses the maximum duplicate confidence while still honoring the Phase 7C confidence ceiling.

Ordering remains stable after deduplication.

## 10. Memory Input Helper Boundary

`generate_candidates_from_memory` may call the Phase 7B outcome pattern miner when the caller explicitly provides in-memory records. This boundary is local and read-only. It does not require a database, OCI, ADB, Oracle Agent Memory, environment variables, network access, or file writes.

The helper exists for caller convenience only. It does not integrate with `run_analysis.py` and does not modify runtime analysis.

## 11. Runtime Isolation Boundary

Phase 7D is isolated from deterministic runtime behavior. Runtime parser, scoring, trend, anomaly, decision, recommendation, dashboard truth, and `run_analysis.py` paths must not import `src.learning`.

No runtime parser/scoring/decision/recommendation behavior changes are made. Deterministic runtime remains authoritative.

## 12. Semantic Recall Boundary

Semantic recall remains non-authoritative. Semantic recall is not used as evidence. Phase 7D does not call semantic search, Oracle Agent Memory, embedding services, LLM services, or semantic recall services.

`semantic_context remains None in Phase 7D`; future reviewer-assist semantic candidate context remains Phase 7E work.

## 13. Governance Boundary

Generated candidates require human review. Generated candidates are not approved, generated candidates are not implemented, and generated candidates are not activated by the generation engine.

The governance bridge remains future Phase 7F. Phase 7D does not implement candidate approval workflow, review workflow, governance bridge persistence, materialization, activation, or runtime learning.

## 14. Dashboard Boundary

Phase 7D does not change dashboard diagnostic truth, Screen 2 diagnostic evidence, Screen 5 recommendation truth, dashboard files, or dashboard runtime behavior.

Dashboard learning visibility remains future Phase 7G. Dashboard interactivity remains future Phase 7H. Phase 7D does not regenerate dashboard HTML and does not add dashboard controls for learning candidates.

## 15. Relationship to Phase 7B Outcome Pattern Mining

Phase 7B mines observational `OutcomePattern` records from governed memory-shaped inputs. Phase 7D consumes those pattern records and converts them into proposal-only `LearningCandidate` records.

Phase 7D does not replace Phase 7B mining and does not mine beyond the explicit local memory helper boundary.

## 16. Relationship to Phase 7C Candidate Model

Phase 7C defines the learning candidate object model, supported types, supported statuses, serialization behavior, deterministic id helpers, and validation rules.

Phase 7D uses the Phase 7C model and validates every generated candidate. The engine does not loosen Phase 7C validation. Generated candidates keep `runtime_influence=false` and `requires_human_review=true`.

## 17. Relationship to Future Phase 7E Semantic Candidate Context

Phase 7E remains future work for optional reviewer-assist semantic candidate context. Phase 7D does not implement semantic candidate context and does not use semantic recall as evidence.

All Phase 7D candidates keep `semantic_context=None`.

## 18. Relationship to Future Phase 7F Governance Bridge

Phase 7F remains future work for a governed bridge between reviewed candidates and controlled implementation workflows. Phase 7D does not implement the governance bridge.

Generated candidates are proposals only and cannot approve, implement, materialize, activate, or modify runtime behavior.

## 19. Validation Requirements

Validation must prove import safety, empty input behavior, pattern-to-candidate mappings, supported suggested candidate type handling, unsupported suggestion fallback, candidate safety defaults, Phase 7C candidate validation, deterministic output, stable ordering, deduplication, memory helper behavior, input non-mutation, source evidence population, structured source metadata, created field defaults, absence of forbidden autonomous function names, runtime import isolation, and documentation boundary coverage.

Validation must also preserve Phase 7A learning boundary tests, Phase 7B outcome pattern mining tests, Phase 7C learning candidate model tests, and Phase 6 validation when the environment supports it.

## 20. Acceptance Criteria

Phase 7D is accepted when a deterministic candidate generation engine exists, candidate generation is proposal-only, generated candidates are not approved, generated candidates are not implemented, generated candidates are not activated, generated candidates keep `runtime_influence=false`, generated candidates keep `requires_human_review=true`, generated candidates remain `status=PROPOSED`, `semantic_context remains None in Phase 7D`, semantic recall remains non-authoritative, semantic recall is not used as evidence, no governance bridge was implemented, governance bridge remains future Phase 7F, no dashboard learning visibility was implemented, dashboard learning visibility remains future Phase 7G, no dashboard interactivity was implemented, dashboard interactivity remains future Phase 7H, no runtime learning was implemented, and deterministic runtime remains authoritative.

Phase 7D must not alter parser/scoring/decision/recommendation behavior, dashboard truth, Phase 4I contracts, generated dashboard files, governed memory persistence, or `run_analysis.py` behavior.
