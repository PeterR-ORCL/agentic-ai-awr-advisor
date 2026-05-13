# Phase 7Y ML Governance / Model Registry

## 1. Purpose

Phase 7Y defines a local deterministic ML governance and model registry layer for the Agentic AI AWR Advisor. The registry records model metadata, version metadata, dataset references, training references, backtesting references, explainability references, validation metrics, governance status, eligibility state, rollback references, retirement state, and audit notes.

The registry is governance metadata only. Deterministic scoring remains authoritative.

## 2. Scope

Phase 7Y creates registry records, governance decision records, eligibility records, validation rules, deterministic ID helpers, and deterministic serialization helpers. These records support reviewer visibility and auditability for future ML governance.

All records are local. No database writes, OCI calls, Oracle Agent Memory calls, LLM calls, or network calls are part of this phase.

## 3. Non-Goals

Phase 7Y does not train models, deploy models, load model files, save model files, activate models, change scoring weights, change thresholds, change severity cutoffs, change confidence logic, change parser behavior, change decisions, change recommendations, add dashboard controls, add CLI commands, implement final ML certification, or implement Phase 8.

Phase 8 sizing/TCO is not implemented.

## 4. Model Registry Is Not Runtime Deployment

The model registry does not deploy models. A registry record is an auditable governance object, not a model artifact store, runtime loader, or deployment system.

Model approval does not activate runtime scoring. APPROVED_FOR_RUNTIME_REVIEW is not runtime active.

## 5. Model Registry Entry

`MLModelRegistryEntry` records `model_id`, `model_family`, `model_version`, `model_name`, feature and label schema versions, training dataset reference, training reference, backtest reference, explainability reference, validation metrics, governance status, shadow eligibility, runtime eligibility request state, runtime eligibility grant state, runtime active state, runtime influence grant state, rollback reference, retirement state, creator, reviewer, and notes.

`runtime_eligibility_granted=false`, `runtime_active=false`, and `runtime_influence_granted=false` are required.

## 6. Model Governance Decision

`MLModelGovernanceDecision` records an auditable transition from one governance status to another. It includes a deterministic decision ID, model ID, source status, target status, decision type, actor, review notes, validation reference, runtime eligibility request state, runtime eligibility grant state, runtime active state, and optional created-at text.

Governance decisions can request runtime review, but they cannot grant runtime eligibility and cannot activate runtime scoring.

## 7. Model Eligibility Record

`MLModelEligibilityRecord` records whether a model is eligible for shadow review or has a runtime review request state. In Phase 7Y, `runtime_eligible=false`, `runtime_active=false`, and `runtime_influence_granted=false` are required.

Eligibility records do not deploy models and do not change runtime behavior.

## 8. Supported Model Families

Supported model families are `tree`, `neural_net`, `hybrid_rule_ml`, `linear`, `baseline_mock`, `baseline_majority`, `baseline_numeric_mean`, `shadow_placeholder`, and `external_placeholder`.

These values are metadata only. They do not identify real model implementations in Phase 7Y.

## 9. Governance Statuses

Supported governance statuses are `PROPOSED`, `REGISTERED`, `TRAINED`, `BACKTESTED`, `EXPLAINED`, `APPROVED_FOR_SHADOW`, `APPROVED_FOR_RUNTIME_REVIEW`, `REJECTED`, `RETIRED`, and `CLOSED`.

No status means runtime active. APPROVED_FOR_RUNTIME_REVIEW is not runtime active.

## 10. Decision Types

Supported decision types are `register`, `mark-trained`, `mark-backtested`, `attach-explainability`, `approve-for-shadow`, `request-runtime-review`, `reject`, `retire`, and `close`.

Each decision type maps deterministically to a governance status. None of the decision types grants runtime eligibility or activates runtime scoring.

## 11. Eligibility Types

Supported eligibility types are `shadow` and `runtime_review`.

Shadow eligibility can be recorded for shadow review. Runtime review can be requested for governance review, but runtime eligibility is not granted in Phase 7Y.

## 12. Shadow Eligibility

Shadow eligibility may be true only when the registry entry status is `APPROVED_FOR_SHADOW` or `APPROVED_FOR_RUNTIME_REVIEW`. Shadow eligibility is still non-runtime-active and cannot replace deterministic scoring.

## 13. Runtime Eligibility Boundary

Runtime eligibility may be requested as governance state. Runtime eligibility may not be granted in Phase 7Y.

`runtime_eligibility_granted=false` is enforced for registry entries and governance decisions. `runtime_eligible=false` is enforced for eligibility records.

## 14. Runtime Influence Boundary

Runtime influence is not granted in Phase 7Y. `runtime_influence_granted=false` is enforced for registry entries and eligibility records.

No model registry record can update scoring weights, thresholds, severity cutoffs, confidence logic, decision logic, recommendation ranking, parser output, dashboard behavior, CLI behavior, or runtime configuration.

## 15. Deterministic Runtime Boundary

Deterministic scoring remains authoritative. No model registry record changes Phase 4I, decisions, recommendations, parser behavior, scoring behavior, dashboard behavior, or CLI behavior.

`runtime_active=false` is enforced for all records that contain runtime active state.

## 16. Relationship to Phase 7S

Phase 7S established the ML and adaptive scoring boundary. Phase 7Y respects that boundary by recording registry metadata only and by keeping all runtime influence fields false.

## 17. Relationship to Phase 7T

Phase 7T introduced governed feature and label dataset records. Phase 7Y may reference a training dataset ID, feature schema version, and label schema version, but it does not train a model or alter dataset behavior.

## 18. Relationship to Phase 7U

Phase 7U introduced deterministic trend-aware advisory scoring. Phase 7Y may track validation metrics that compare advisory outputs, but it does not change Score(x, t) or deterministic runtime scoring.

## 19. Relationship to Phase 7V

Phase 7V introduced a shadow ML model interface. Phase 7Y may record model families compatible with shadow metadata, but it does not load real models, persist model files, or make Score_ml(x) runtime active.

## 20. Relationship to Phase 7W

Phase 7W introduced local training and backtesting evaluation records. Phase 7Y may reference training and backtesting outputs, but it does not perform new training or backtesting behavior.

## 21. Relationship to Phase 7X

Phase 7X introduced explanation records. Phase 7Y may reference explainability records, but explanation remains advisory only and does not become runtime truth.

## 22. Relationship to Future Phase 7Z

Phase 7Z is the future ML validation and certification phase. Phase 7Y prepares governance and registry records only. It does not certify a model for runtime use.

## 23. Relationship to Phase 8

Phase 8 sizing/TCO is not implemented. Phase 7Y does not add sizing, capacity planning, cost modeling, TCO modeling, or what-if advisory behavior.

## 24. Acceptance Criteria

Phase 7Y is accepted when model registry entries, governance decisions, and eligibility records validate and serialize deterministically; supported model families, statuses, decision types, and eligibility types are enforced; shadow eligibility is bounded to approved shadow statuses; runtime_eligibility_granted=false, runtime_active=false, and runtime_influence_granted=false are enforced; registry is governance metadata only; model registry does not deploy models; model approval does not activate runtime scoring; APPROVED_FOR_RUNTIME_REVIEW is not runtime active; deterministic scoring remains authoritative; no model registry record changes Phase 4I; no model registry record changes decisions or recommendations; no dashboard behavior changes; no CLI behavior changes; and Phase 8 sizing/TCO is not implemented.
