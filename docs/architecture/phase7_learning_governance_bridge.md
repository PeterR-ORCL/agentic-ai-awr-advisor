# Phase 7F Learning Governance Bridge

## 1. Purpose

Phase 7F adds a local, deterministic, auditable governance bridge for Phase 7 `LearningCandidate` records. The bridge lets a human actor record review transitions, review notes, approval-for-implementation decisions, materialization references, implementation state, validation state, and closure.

The governance bridge is local and deterministic. It is not runtime integration, not persistence, not an approval UI, not a dashboard control path, and not a mutation path for parser, scoring, decision, recommendation, or dashboard truth.

## 2. Scope

Phase 7F operates only on in-memory Phase 7C learning candidates supplied by the caller. It returns a copied candidate record and a `GovernanceDecision` audit record for each supported action.

The bridge supports actor-required review transitions while preserving `runtime_influence=false` and `requires_human_review=true`. It uses Python standard library behavior and local Phase 7 learning modules only.

## 3. Non-Goals

Phase 7F does not change parser behavior, parser output, scoring logic, scoring weights, trend or anomaly logic, decision logic, recommendation logic, Phase 4I output contracts, `run_analysis.py`, dashboard diagnostic truth, Screen 2 diagnostic evidence, or Screen 5 recommendation truth.

Phase 7F does not implement dashboard learning visibility, dashboard interactivity, CLI learning commands, database writes, OCI dependencies, ADB dependencies, Oracle Agent Memory live dependencies, semantic recall service dependencies, LLM calls, automatic activation, automatic parser updates, automatic scoring updates, automatic recommendation updates, or runtime learning.

## 4. Governance Decision Shape

`GovernanceDecision` contains `decision_id`, `candidate_id`, `from_status`, `to_status`, `actor`, `decision_type`, `review_notes`, `materialization_reference`, `runtime_influence`, `approved_for_implementation_only`, `created_at`, and `audit_records`.

Decision ids are deterministic and use local inputs only. They do not use random UUIDs, current timestamps, database sequences, network calls, external services, or environment-dependent values.

Each audit record includes the candidate id, action, from status, to status, actor, optional review notes, optional materialization reference, `runtime_influence=false`, `requires_human_review=true`, and approval-only metadata when applicable. No audit record may imply runtime activation.

## 5. Governance Actions

The bridge supports `mark_under_review`, `reject_candidate`, `request_revision`, `approve_for_implementation`, `attach_materialization`, `mark_implemented`, `mark_validated`, and `close_candidate`.

These actions record governance state only. They do not activate runtime behavior, do not materialize implementation work by themselves, and do not update runtime contracts.

## 6. Allowed Status Transitions

The allowed transitions are `PROPOSED -> UNDER_REVIEW`, `PROPOSED -> REJECTED`, `PROPOSED -> NEEDS_REVISION`, `UNDER_REVIEW -> APPROVED_FOR_IMPLEMENTATION`, `UNDER_REVIEW -> REJECTED`, `UNDER_REVIEW -> NEEDS_REVISION`, `APPROVED_FOR_IMPLEMENTATION -> IMPLEMENTED`, `APPROVED_FOR_IMPLEMENTATION -> NEEDS_REVISION`, `APPROVED_FOR_IMPLEMENTATION -> CLOSED`, `IMPLEMENTED -> VALIDATED`, `VALIDATED -> CLOSED`, `NEEDS_REVISION -> UNDER_REVIEW`, `NEEDS_REVISION -> CLOSED`, and `REJECTED -> CLOSED`.

Invalid transitions are rejected with a clear governance exception. `CLOSED` is terminal for review transitions.

## 7. Actor Requirement

Every governance action requires a non-empty actor. Missing actor identity fails validation before a candidate copy or decision record is returned.

The actor is audit metadata. It does not confer runtime authority, does not approve runtime activation, and does not override deterministic runtime truth.

## 8. Approval Boundary

`approve_for_implementation` moves a candidate to `APPROVED_FOR_IMPLEMENTATION`. Approval means approved for implementation only.

Approval does not activate runtime behavior. Approval does not modify parser logic, scoring logic, decision logic, recommendation logic, dashboard truth, generated files, persisted memory, or runtime contracts. Approval preserves `runtime_influence=false` and `requires_human_review=true`.

An approval decision sets `approved_for_implementation_only=true`. It does not set `materialization_reference` unless a later explicit materialization action records one.

## 9. Materialization Reference Boundary

`attach_materialization` records an implementation reference for audit traceability. The materialization reference does not activate runtime behavior.

Attaching a materialization reference does not change status, does not set `runtime_influence=true`, does not implement code by itself, does not validate implementation work, and does not make the candidate runtime influencing.

## 10. Implementation Boundary

`mark_implemented` can move a candidate from `APPROVED_FOR_IMPLEMENTATION` to `IMPLEMENTED` only when a materialization reference exists or is supplied. `IMPLEMENTED` means an implementation reference exists or has been recorded.

`IMPLEMENTED` does not set `runtime_influence=true`. It does not mean the bridge has changed parser, scoring, decision, recommendation, dashboard, or Phase 4I behavior.

## 11. Validation Boundary

`mark_validated` can move a candidate from `IMPLEMENTED` to `VALIDATED`. Validation records review state only.

`VALIDATED` does not set `runtime_influence=true`. It does not activate a candidate, does not update runtime contracts, and does not replace separate controlled implementation tests and contract-preservation validation outside Phase 7F.

## 12. Runtime Isolation Boundary

The governance bridge is not runtime integration. Runtime parser, scoring, trend, anomaly, decision, recommendation, dashboard truth, and `run_analysis.py` paths must not import `src.learning`.

Deterministic runtime remains authoritative. Phase 7F does not alter parser/scoring/decision/recommendation behavior and does not change runtime analysis outputs.

## 13. Semantic Recall Boundary

Semantic context can remain attached but cannot decide. Phase 7F may preserve a candidate's existing `semantic_context`, but semantic recall is reviewer-assist only and non-authoritative.

Semantic recall is not used as evidence. Phase 7F does not call a live semantic recall service, Oracle Agent Memory, embeddings, LLMs, databases, or network services.

## 14. Source Evidence Boundary

Governance does not change source_evidence. The bridge preserves the candidate's existing `source_evidence` and `structured_sources` when it records a status transition or audit metadata.

Governance audit metadata is not diagnostic evidence, not parser evidence, not Phase 4I output evidence, and not a replacement for outcome pattern source records.

## 15. Confidence Boundary

Governance does not change confidence. Review status, approval, materialization reference attachment, implementation marking, validation marking, and closure must not raise, lower, clamp, rank, or otherwise change the candidate confidence field.

Confidence remains a candidate-model field generated before governance review. Governance cannot turn semantic context or audit notes into confidence evidence.

## 16. Dashboard Boundary

Phase 7F does not change dashboard diagnostic truth, generated dashboard files, Screen 2 diagnostic evidence, Screen 5 recommendation truth, dashboard controls, dashboard filters, dashboard links, or dashboard runtime behavior.

Dashboard learning visibility remains future Phase 7G. Dashboard interactivity remains future Phase 7H.

## 17. CLI Boundary

Phase 7F does not add CLI learning commands, CLI approval controls, CLI rejection commands, CLI persistence commands, or CLI runtime activation commands.

CLI learning commands remain future Phase 7I.

## 18. Relationship to Phase 7C Candidate Model

Phase 7C defines the `LearningCandidate` model, supported candidate types, supported statuses, serialization behavior, deterministic candidate ids, `runtime_influence=false`, and `requires_human_review=true`.

Phase 7F consumes Phase 7C candidate records and returns validated candidate copies. It does not loosen Phase 7C validation and does not add any candidate state that can influence runtime behavior.

## 19. Relationship to Phase 7D Candidate Generation

Phase 7D creates deterministic proposal-only learning candidates from governed outcome patterns. Phase 7F does not generate candidates and does not mine outcome patterns.

Phase 7F reviews candidate records that already exist. It does not alter Phase 7D candidate generation rules, source evidence rules, confidence rules, deterministic ordering, or candidate identity rules.

## 20. Relationship to Phase 7E Semantic Candidate Context

Phase 7E attaches optional reviewer-assist semantic context to candidates. Phase 7F preserves semantic context when candidates move through governance transitions.

Semantic context can explain but cannot decide. Phase 7F does not use semantic context as source evidence, does not change confidence based on semantic context, and does not call semantic recall services.

## 21. Relationship to Future Phase 7G Dashboard Learning Visibility

Dashboard learning visibility remains future Phase 7G. Phase 7F does not add dashboard panels, learning candidate tables, governance badges, materialization links, validation indicators, or learning summaries.

Any future dashboard learning visibility must consume governed records without mutating backend truth or activating runtime behavior.

## 22. Relationship to Future Phase 7H Dashboard Interactivity

Dashboard interactivity remains future Phase 7H. Phase 7F does not add reviewer controls, candidate action controls, approval controls, rejection controls, implementation controls, validation controls, or dashboard mutation behavior.

Any future interactive dashboard behavior must remain explicitly governed and must not change deterministic runtime truth.

## 23. Relationship to Future Phase 7I CLI Learning Commands

CLI learning commands remain future Phase 7I. Phase 7F does not expose command-line candidate review, approval, rejection, revision, materialization, implementation, validation, or closure commands.

Any future CLI learning command must preserve actor requirements, auditability, runtime isolation, and deterministic runtime authority.

## 24. Validation Requirements

Validation must prove import safety, governance decision serialization, actor requirements, allowed transitions, invalid transition rejection, approval boundary behavior, materialization boundary behavior, candidate immutability and safety, deterministic decision ids, audit record content, helper action dispatch, absence of autonomous runtime-update function names, runtime import isolation, and documentation boundary coverage.

Validation must also preserve Phase 7A learning boundary tests, Phase 7B outcome pattern mining tests, Phase 7C learning candidate model tests, Phase 7D candidate generation tests, Phase 7E semantic candidate context tests, and Phase 6 validation when the local environment supports it.

## 25. Acceptance Criteria

Phase 7F is accepted when the learning governance bridge exists; governance decisions are serializable; status transitions are validated; every review or write action requires an actor; approval means approved for implementation only; approval does not activate runtime behavior; materialization reference does not activate runtime behavior; `IMPLEMENTED` does not set `runtime_influence=true`; `VALIDATED` does not set `runtime_influence=true`; all governed candidates preserve `runtime_influence=false` and `requires_human_review=true`; governance does not change confidence; governance does not change source_evidence; semantic context can remain attached but cannot decide; no dashboard learning visibility is implemented; no dashboard interactivity is implemented; no CLI learning commands are implemented; no runtime learning is implemented; and deterministic runtime remains authoritative.

Phase 7F must not alter parser/scoring/decision/recommendation behavior, dashboard truth, Phase 4I contracts, generated dashboard files, governed memory persistence, or `run_analysis.py` behavior.
