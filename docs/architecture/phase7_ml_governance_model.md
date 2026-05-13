# Phase 7Y ML Governance Model

## 1. Purpose

This document defines the serializable object model for Phase 7Y ML governance and model registry records. The model is local, deterministic, and non-runtime-active.

The registry is governance metadata only. Deterministic scoring remains authoritative.

## 2. MLModelRegistryEntry Object Shape

`MLModelRegistryEntry` contains `model_id`, `model_family`, `model_version`, `model_name`, `feature_schema_version`, `label_schema_version`, `training_dataset_id`, `training_reference`, `backtest_reference`, `explainability_reference`, `validation_metrics`, `governance_status`, `shadow_eligible`, `runtime_eligibility_requested`, `runtime_eligibility_granted`, `runtime_active`, `runtime_influence_granted`, `rollback_reference`, `retired`, `created_by`, `reviewed_by`, and `notes`.

`runtime_eligibility_granted=false`, `runtime_active=false`, and `runtime_influence_granted=false` are required. Registry entries do not deploy models and do not change runtime scoring.

## 3. MLModelGovernanceDecision Object Shape

`MLModelGovernanceDecision` contains `decision_id`, `model_id`, `from_status`, `to_status`, `decision_type`, `actor`, `review_notes`, `validation_reference`, `runtime_eligibility_requested`, `runtime_eligibility_granted`, `runtime_active`, and `created_at`.

The actor is required. Runtime review can be requested as governance state, but `runtime_eligibility_granted=false` and `runtime_active=false` are required.

## 4. MLModelEligibilityRecord Object Shape

`MLModelEligibilityRecord` contains `eligibility_id`, `model_id`, `eligibility_type`, `shadow_eligible`, `runtime_eligible`, `runtime_active`, `runtime_influence_granted`, `validation_reference`, `rollback_reference`, and `notes`.

In Phase 7Y, `runtime_eligible=false`, `runtime_active=false`, and `runtime_influence_granted=false` are required.

## 5. Model Families

Supported model families are `tree`, `neural_net`, `hybrid_rule_ml`, `linear`, `baseline_mock`, `baseline_majority`, `baseline_numeric_mean`, `shadow_placeholder`, and `external_placeholder`.

The model family is metadata only and does not select a runtime model implementation.

## 6. Governance Statuses

Supported governance statuses are `PROPOSED`, `REGISTERED`, `TRAINED`, `BACKTESTED`, `EXPLAINED`, `APPROVED_FOR_SHADOW`, `APPROVED_FOR_RUNTIME_REVIEW`, `REJECTED`, `RETIRED`, and `CLOSED`.

No status means runtime active. APPROVED_FOR_RUNTIME_REVIEW is not runtime active.

## 7. Decision Types

Supported decision types are `register`, `mark-trained`, `mark-backtested`, `attach-explainability`, `approve-for-shadow`, `request-runtime-review`, `reject`, `retire`, and `close`.

The transition mapping is deterministic: `register` to `REGISTERED`, `mark-trained` to `TRAINED`, `mark-backtested` to `BACKTESTED`, `attach-explainability` to `EXPLAINED`, `approve-for-shadow` to `APPROVED_FOR_SHADOW`, `request-runtime-review` to `APPROVED_FOR_RUNTIME_REVIEW`, `reject` to `REJECTED`, `retire` to `RETIRED`, and `close` to `CLOSED`.

Model approval does not activate runtime scoring.

## 8. Eligibility Types

Supported eligibility types are `shadow` and `runtime_review`.

Shadow eligibility can be true for `APPROVED_FOR_SHADOW` and `APPROVED_FOR_RUNTIME_REVIEW` entries. Runtime review eligibility may be requested, but no model is deployed and no runtime eligibility is granted.

## 9. Validation Rules

Registry entry validation requires non-empty model ID, supported model family, non-empty model version, non-empty model name, supported governance status, numeric validation metric values, `runtime_active=false`, `runtime_influence_granted=false`, and `runtime_eligibility_granted=false`.

If `shadow_eligible=true`, the governance status must be `APPROVED_FOR_SHADOW` or `APPROVED_FOR_RUNTIME_REVIEW`. If `retired=true`, the governance status must be `RETIRED` or `CLOSED`.

Governance decision validation requires non-empty decision ID, non-empty model ID, supported from and to statuses, supported decision type, required actor, `runtime_active=false`, and `runtime_eligibility_granted=false`.

Eligibility record validation requires non-empty eligibility ID, non-empty model ID, supported eligibility type, `runtime_eligible=false`, `runtime_active=false`, and `runtime_influence_granted=false`.

## 10. Serialization Rules

Every object has deterministic to-dictionary and from-dictionary helpers. Deserialization reruns validation and rejects runtime activation state.

Serialization does not write databases, files, dashboard state, CLI state, runtime configuration, model files, model stores, or Phase 4I output.

## 11. Deterministic ID Rules

Model IDs use stable input fields:

```text
ML-MODEL-<FAMILY>-<VERSION>-<MODEL_NAME>
```

Governance decision IDs use stable transition fields:

```text
ML-GOVDEC-<MODEL_ID>-<DECISION_TYPE>-<FROM>-<TO>
```

Eligibility IDs use stable model and eligibility fields:

```text
ML-ELIGIBILITY-<MODEL_ID>-<ELIGIBILITY_TYPE>
```

IDs do not use UUIDs, timestamps, database sequences, current time, network calls, or external services.

## 12. Runtime Boundary

The model registry does not deploy models. Model approval does not activate runtime scoring. APPROVED_FOR_RUNTIME_REVIEW is not runtime active.

`runtime_eligibility_granted=false`, `runtime_active=false`, and `runtime_influence_granted=false` are enforced. No runtime scoring is changed. No Phase 4I contract is changed. No parser, scoring, decision, recommendation, dashboard, or CLI behavior is changed.

## 13. Non-Goals

Phase 7Y does not implement model deployment, model file storage, model file loading, real ML frameworks, runtime activation, final ML certification, dashboard registry controls, CLI registry commands, database writes, OCI integration, Oracle Agent Memory integration, semantic recall integration, LLM calls, network calls, or Phase 8 sizing/TCO.

Phase 8 sizing/TCO is not implemented.

## 14. Acceptance Criteria

The governance model is accepted when registry entries, governance decisions, and eligibility records validate and serialize deterministically; deterministic IDs are stable; unsupported families, statuses, decision types, and eligibility types are rejected; runtime_active=false, runtime_influence_granted=false, runtime_eligibility_granted=false, and runtime_eligible=false are enforced where applicable; registry is governance metadata only; no model is deployed; no runtime scoring is changed; no Phase 4I contract is changed; deterministic scoring remains authoritative; and Phase 8 sizing/TCO is not implemented.
