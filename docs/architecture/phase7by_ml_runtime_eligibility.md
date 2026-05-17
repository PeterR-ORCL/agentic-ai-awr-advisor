# Phase 7BY ML Runtime Eligibility / Shadow-to-Runtime Path

## 1. Purpose

Phase 7BY defines the local, deterministic metadata path that describes when a shadow or advisory ML model has enough evidence for future runtime review. It bridges model registry records, backtesting, explainability, deterministic comparison, fallback, monitoring, and runtime gate metadata without activating ML runtime behavior.

## 2. Scope

The scope is metadata only: ML runtime eligibility packages, activation manifests, eligibility records, fallback plans, monitoring plans, regression evidence, deterministic IDs, validation helpers, and serialization helpers.

## 3. Non-Goals

7BY does not deploy models, load model files, save model files, run inference, train models, replace deterministic scoring, mutate decisions, mutate recommendations, mutate parser behavior, write DB records, call `run_analysis.py`, or implement Phase 8.

## 4. ML Runtime Eligibility Is Not Model Deployment

ML runtime eligibility is a review envelope. no model is deployed in 7BY. no model is loaded/saved in 7BY. no runtime scoring is replaced in 7BY. eligible means metadata eligible, not active.

## 5. MLRuntimeEligibilityPackage

`MLRuntimeEligibilityPackage` records the model identity, model family, registry entry, training evidence, backtest evidence, explainability evidence, validation evidence, dataset and schema references, deterministic comparison evidence, drift review, rollback reference, monitoring reference, and safety flags. `runtime_active=false`, `runtime_eligibility_granted=false`, `runtime_influence_granted=false`, `model_deployed=false`, `model_loaded=false`, `model_saved=false`, `runtime_scoring_replaced=false`, and `phase4i_mutation_performed=false`.

## 6. MLRuntimeActivationManifest

`MLRuntimeActivationManifest` describes a future activation review envelope. It requires explicit activation, deterministic fallback, Phase 4I contract preservation, rollback metadata, runtime gate metadata, and monitoring metadata. It keeps `runtime_activation_requested=false`, `runtime_activation_approved=false`, `runtime_active=false`, `model_deployed=false`, and `runtime_scoring_replaced=false`.

## 7. MLRuntimeEligibilityRecord

`MLRuntimeEligibilityRecord` is a local validation result. `eligible=true` means eligible metadata only. It does not grant runtime eligibility, runtime influence, model deployment, runtime scoring replacement, or runtime activation.

## 8. MLRuntimeFallbackPlan

`MLRuntimeFallbackPlan` records the deterministic fallback strategy. deterministic fallback required means deterministic scoring remains available and authoritative. Fallback execution is not performed in 7BY.

## 9. MLRuntimeMonitoringPlan

`MLRuntimeMonitoringPlan` records future drift, performance, confidence, and fallback trigger monitoring metadata. Monitoring is not active in 7BY, so `monitoring_active=false` and `runtime_active=false`.

## 10. MLRuntimeRegressionEvidence

`MLRuntimeRegressionEvidence` records backtesting, explainability, deterministic comparison, validation, and Phase 4I contract evidence references. It does not run tests or inference.

## 11. Registry Reference Requirement

A model registry entry reference is required before metadata eligibility can be true.

## 12. Training / Backtesting Requirement

Training and backtesting references are required before metadata eligibility can be true. 7BY does not train models or run backtests.

## 13. Explainability Requirement

Explainability evidence is required before metadata eligibility can be true. 7BY does not compute explanations.

## 14. Deterministic Comparison Requirement

The model must have deterministic comparison metadata before future runtime review. Deterministic runtime remains authoritative.

## 15. Drift Review Requirement

Drift review metadata is required so future runtime review can identify when fallback or rejection is required.

## 16. Rollback Requirement

Rollback metadata is required on the package and manifest before metadata eligibility can be true. Rollback is not executed in 7BY.

## 17. Monitoring Requirement

Monitoring metadata is required on the package and manifest before metadata eligibility can be true. Monitoring is not active in 7BY.

## 18. Runtime Gate Requirement

A runtime gate reference is required before metadata eligibility can be true. The runtime gate reference is not a grant of runtime eligibility or runtime influence.

## 19. Deterministic Fallback Requirement

deterministic fallback required is a hard boundary. Future review must preserve deterministic scoring fallback and must not replace deterministic scoring by default.

## 20. Phase 4I Contract Requirement

Phase 4I preserved means ML metadata cannot change the Phase 4I contract, scores, decisions, recommendations, parser outputs, or runtime truth in 7BY.

## 21. Relationship to 7BU

7BU created governed persistence and status transition metadata boundaries. 7BY uses the same boundary philosophy: local metadata, deterministic IDs, validation helpers, serialization helpers, no DB persistence, no status transition, and no runtime activation.

## 22. Relationship to 7S-7Z / 7BN

7S-7Z created the ML/adaptive scoring foundation, shadow interface, training/backtesting metadata, explainability metadata, model registry metadata, and validation. 7BN created model registry review preview metadata. 7BY does not change any of those records; it defines the next metadata envelope for future runtime review.

## 23. Relationship to Future 7BZ

7BZ may validate the complete controlled runtime materialization execution path. 7BY does not perform that certification and does not activate any runtime ML path.

## 24. Acceptance Criteria

7BY is accepted when local ML runtime eligibility package, activation manifest, eligibility record, fallback plan, monitoring plan, and regression evidence models exist; validation rejects runtime-active and deployment flags; deterministic IDs and serialization helpers exist; no model is deployed; no model is loaded/saved; no runtime scoring is replaced; runtime_eligibility_granted=false; runtime_influence_granted=false; runtime_active=false; deterministic fallback required; Phase 4I preserved; and Phase 8 is not implemented.
