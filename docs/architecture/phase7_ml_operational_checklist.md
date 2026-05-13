# Phase 7 ML Operational Checklist

## Purpose

This checklist defines the local operational procedure for Phase 7Z ML Validation / Certification. It is used to certify the Phase 7S-7Y ML / adaptive scoring block as shadow/advisory only.

## Pre-Run Checklist

- Confirm the branch is `phase7-ml-validation-certification`.
- Confirm the working tree is clean before making release certification claims.
- Confirm no parser, scoring, decision, recommendation, dashboard behavior, CLI behavior, `scripts/run_analysis.py`, database schema, or generated dashboard HTML files are modified.
- Use `.venv/bin/python` if system Python lacks project dependencies such as dotenv.
- Do not certify if validation fails.
- Do not bypass runtime isolation boundaries.

## Validation Checklist

- Run `python3 scripts/run_phase7_ml_validation.py`.
- Run `python3 scripts/run_phase7_ml_validation.py --json`.
- Confirm the text output says `Phase 7 ML validation passed.`
- Confirm JSON reports `success=true`, `runtime_active=false`, `runtime_influence=false`, `runtime_influence_granted=false`, and `runtime_eligibility_granted=false`.

## ML Boundary Checklist

- Confirm the 7S boundary is shadow/advisory only.
- Confirm no learned_model(x), runtime Score_ml(x), model deployment, model activation, or runtime scoring replacement is certified.
- Confirm deterministic runtime remains authoritative.

## Dataset Checklist

- Confirm feature / label datasets are governed inputs only.
- Confirm dataset is not a model.
- Confirm dataset validation is not training.
- Confirm dataset records keep `runtime_influence=false` and `runtime_active=false`.

## Trend-Aware Scoring Checklist

- Confirm trend-aware scoring is advisory/shadow only.
- Confirm no runtime scoring changes are applied.
- Confirm no scoring thresholds, scoring weights, severity cutoffs, confidence, decisions, recommendations, parser output, or Phase 4I output are changed.

## Shadow ML Checklist

- Confirm shadow ML output is non-authoritative.
- Confirm shadow ML scores are comparison records only.
- Confirm `runtime_influence=false`, `runtime_active=false`, and `runtime_influence_granted=false`.

## Training / Backtesting Checklist

- Confirm training/backtesting is evaluation only.
- Confirm no real model deployment is performed.
- Confirm no saved model is loaded into runtime.
- Confirm training and backtesting records keep runtime activation fields false.

## Explainability Checklist

- Confirm explainability is not runtime truth.
- Confirm feature contributions, score comparisons, and confidence explanations do not alter deterministic scoring, decisions, recommendations, parser output, or Phase 4I output.

## Model Registry Checklist

- Confirm model registry is governance metadata only.
- Confirm model registry does not deploy models.
- Confirm model approval does not activate runtime scoring.
- Confirm `runtime_eligibility_granted=false`, `runtime_active=false`, and `runtime_influence_granted=false`.

## Runtime Isolation Checklist

- Confirm `scripts/run_analysis.py` does not import Phase 7S-7Y ML/adaptive modules.
- Confirm parser modules do not import Phase 7S-7Y ML/adaptive modules.
- Confirm scoring modules do not import Phase 7S-7Y ML/adaptive modules.
- Confirm decision modules do not import Phase 7S-7Y ML/adaptive modules.
- Confirm recommendation modules do not import Phase 7S-7Y ML/adaptive modules.

## Documentation Checklist

- Confirm `docs/architecture/phase7_ml_validation_matrix.md` exists.
- Confirm `docs/architecture/phase7_ml_readiness.md` exists.
- Confirm `docs/architecture/phase7_ml_release_certification.md` exists.
- Confirm `docs/architecture/phase7_ml_operational_checklist.md` exists.
- Confirm README links the new ML validation, readiness, release certification, and operational checklist documents.

## Failure Handling

- Stop certification if any validation command fails.
- Review the failed group or failed readiness category before rerunning.
- Do not set `runtime_active=true`.
- Do not set `runtime_influence=true`.
- Do not set `runtime_influence_granted=true`.
- Do not set `runtime_eligibility_granted=true`.
- Do not bypass runtime isolation boundaries.

## Acceptance Checklist

- Run `python3 scripts/run_phase7_ml_readiness_check.py`.
- Run `python3 scripts/run_phase7_ml_readiness_check.py --json`.
- Confirm the text output says `Phase 7 ML readiness passed.` and `ml_ready=true`.
- Run `python3 scripts/run_phase7_materialization_validation.py`.
- Run `python3 scripts/run_phase7_materialization_readiness_check.py`.
- Run `python3 scripts/run_phase7_validation.py` or `.venv/bin/python scripts/run_phase7_validation.py` if dependencies require it.
- Run `.venv/bin/python scripts/run_phase7_readiness_check.py`.
- Run `python3 scripts/run_phase7h_dashboard_validation.py`.
- Run `.venv/bin/python scripts/awr_memory_cli.py learning validate --json`.
- Run `PYTHONPATH=. .venv/bin/python scripts/run_phase6_validation.py`.
- Confirm deterministic runtime remains authoritative and Phase 8 is not implemented.
