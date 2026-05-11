# Phase 7G Dashboard Learning Visibility

## 1. Purpose

Phase 7G adds dashboard learning visibility for governed Phase 7 records. The dashboard may display learning candidates, review state, semantic reviewer-assist presence, and governance bridge metadata so reviewers can understand candidate status without changing runtime truth.

Dashboard learning visibility is read-only. Learning candidates are not diagnostic evidence. Learning candidates are not recommendation truth. The dashboard remains downstream of deterministic output and governed learning records.

## 2. Scope

Phase 7G may display candidate counts, candidate statuses, candidate types, affected components, affected domains, confidence values, `runtime_influence=false`, `requires_human_review=true`, semantic context presence, governance review state, review notes, reviewer identity, and materialization references.

All displayed learning state is proposal or review context only. It is not automatically applied and cannot change parser, scoring, trend, anomaly, decision, recommendation, or dashboard diagnostic truth.

## 3. Non-Goals

Phase 7G does not add approval controls, reject controls, implementation controls, validation controls, close controls, write controls, CLI learning commands, database writes, Oracle Agent Memory live dependencies, semantic recall service dependencies, OCI dependencies, ADB dependencies, or LLM calls.

Phase 7G does not implement runtime learning, runtime activation, autonomous adaptation, full dashboard interactivity, dashboard selections, or Phase 7H dashboard interactivity.

## 4. Screen Scope

The primary display surface is Screen 6, the Fleet Overview / Governance / Semantic / Learning visibility screen. Phase 7G does not add learning candidate evidence to Screen 2 and does not add learning candidate recommendation truth to Screen 5.

If future screens show related context, it must be labeled as review context only, not recommendation evidence, and not automatically applied.

## 5. Learning Visibility Data Shape

The dashboard consumes optional in-memory data. Candidate records may include `candidate_id`, `candidate_type`, `status`, `affected_component`, `affected_domain`, `confidence`, `requires_human_review`, `runtime_influence`, `title`, `source_evidence`, `semantic_context`, `reviewed_by`, `review_notes`, and `materialization_reference`.

Governance records may include `status`, `from_status`, `to_status`, `actor`, `reviewed_by`, `review_notes`, `materialization_reference`, `approved_for_implementation_only`, and `runtime_influence`.

Missing learning data must produce a safe empty state.

## 6. Candidate Display Rules

Candidates are displayed as proposed / review-state records. Candidate display must show safety labels including read-only, Human review required, `runtime_influence=false`, `requires_human_review=true`, Not diagnostic evidence, Not recommendation truth, and Not automatically applied.

Candidate display may summarize counts by status, type, affected component, and affected domain. Candidate rows may show source evidence count, but semantic context is not source_evidence and must not be rendered as diagnostic evidence.

## 7. Governance Display Rules

Governance bridge state is review state only. `APPROVED_FOR_IMPLEMENTATION` means Approved for implementation only, not runtime activation. Governance approval is not runtime activation.

Displayed governance fields may include status, reviewed_by, review_notes, materialization_reference, approved_for_implementation_only, and `runtime_influence=false`. Materialization references are reference only and do not activate runtime behavior.

## 8. Semantic Context Display Rules

Semantic context is reviewer-assist only. Semantic context is optional, non-authoritative, not source_evidence, not diagnostic evidence, not recommendation truth, and not automatically applied.

The dashboard may display semantic_context presence and reviewer-assist labels. It must not treat semantic recall or semantic candidate context as source evidence for diagnosis or recommendation truth.

## 9. Empty State Behavior

When no learning candidates exist, Screen 6 must display a safe empty state:

- No learning candidates available
- Learning visibility is read-only
- No runtime influence

The empty state must preserve `runtime_influence=false`, `requires_human_review=true`, no approval controls, no write controls, and no runtime activation.

## 10. Runtime Truth Boundary

Dashboard learning visibility must not change parser output, feature vectors, scoring, trends, anomalies, decision posture, recommendations, Phase 4I output, or deterministic dashboard truth.

Deterministic runtime remains authoritative. Phase 7G does not implement runtime learning.

## 11. Diagnostic Evidence Boundary

Learning candidates are not diagnostic evidence. Semantic context is not diagnostic evidence. Governance review state is not diagnostic evidence.

Screen 2 diagnostic evidence remains downstream of deterministic runtime analysis only.

## 12. Recommendation Truth Boundary

Learning candidates are not recommendation truth. Semantic context is not recommendation truth. Governance bridge state is not recommendation truth.

Screen 5 recommendation truth remains downstream of deterministic recommendations only.

## 13. Approval / Write-Control Boundary

Phase 7G adds no approval controls and no write controls. The dashboard must not approve, reject, implement, validate, close, activate, apply, or auto apply learning candidates.

The dashboard may show review status, but it cannot change review status.

## 14. Dashboard Interactivity Boundary

Phase 7G is static/read-only visibility. Full dashboard interactivity remains future Phase 7H. Dashboard selections remain future Phase 7H.

No full cross-screen selector, candidate state engine, write action, or activation workflow is introduced in Phase 7G.

## 15. Relationship to Phase 7C Candidate Model

Phase 7C defines learning candidates as serializable proposal-only records with `runtime_influence=false` and `requires_human_review=true`. Phase 7G displays those records without creating candidate truth or changing candidate lifecycle state.

## 16. Relationship to Phase 7D Candidate Generation

Phase 7D converts deterministic outcome patterns into proposal-only learning candidates. Phase 7G may display generated candidate records, but it does not generate, rank for activation, approve, implement, or apply them.

## 17. Relationship to Phase 7E Semantic Candidate Context

Phase 7E attaches optional semantic candidate context as reviewer-assist only. Phase 7G may display semantic context presence and the label Semantic context is reviewer-assist only, but semantic context is not source_evidence and cannot change confidence, status, diagnosis, or recommendation truth.

## 18. Relationship to Phase 7F Governance Bridge

Phase 7F provides deterministic local governance transitions. Phase 7G may display governance bridge review state, including Approved for implementation only, not runtime activation, reviewed_by, review_notes, and materialization_reference as reference only.

Phase 7G does not invoke governance actions and does not add dashboard controls for governance transitions.

## 19. Relationship to Future Phase 7H Dashboard Interactivity

Full dashboard interactivity remains future Phase 7H. Candidate selection, review workflows, dashboard write actions, and governed control-plane interactions are outside Phase 7G.

Phase 7G deliberately keeps learning visibility downstream, read-only, and non-authoritative.

## 20. Validation Requirements

Validation must prove import safety, empty state safety, deterministic candidate summaries, safety labels, semantic context reviewer-assist labeling, governance approval labeling, absence of write controls, absence of runtime import drift, Screen 2 and Screen 5 boundaries, no Phase 7H full interactivity, and documentation boundary phrases.

Tests must be deterministic and local only. They must not require a database, OCI, ADB wallet, Oracle Agent Memory, environment variables, network, or current date/time.

## 21. Acceptance Criteria

Phase 7G is accepted when Screen 6 displays Learning Visibility as read-only, shows candidate summary data when optional records are provided, shows a safe empty state when no records exist, labels `runtime_influence=false`, labels `requires_human_review=true`, labels Human review required, labels learning candidates as Not diagnostic evidence and Not recommendation truth, labels semantic context as reviewer-assist only, labels governance approval as Approved for implementation only, not runtime activation, and provides no approval controls, no write controls, no runtime activation, no full dashboard interactivity, and no runtime learning.

The parser, scoring, trend, anomaly, decision, recommendation, Phase 4I output contract, Screen 2 diagnostic evidence, and Screen 5 recommendation truth must remain unchanged.
