# Phase 7 Runtime Materialization Operational Checklist

## 1. Purpose

This checklist guides local operation of the Phase 7BZ validation and readiness scripts for the Phase 7BU-7BY Controlled Runtime Materialization Execution metadata block.

## 2. Pre-Run Checklist

Confirm the branch is `phase7-runtime-materialization-execution`, confirm the working tree is clean before beginning a new task, and confirm no DB, ADB, OCI, Object Storage, Oracle Agent Memory, semantic recall, or network service is required.

## 3. Validation Checklist

Run `python3 scripts/run_phase7_runtime_materialization_validation.py` and verify the text output says `Phase 7 runtime materialization validation passed.`. Run `python3 scripts/run_phase7_runtime_materialization_validation.py --json` and verify JSON reports `runtime_materialization_ready=true`.

## 4. Persistence / Audit Checklist

Confirm 7BU governed workflow persistence, audit, transaction, idempotency, rollback, and write safety metadata tests pass. Confirm no db persistence occurs.

## 5. Status Transition Checklist

Confirm 7BU status transition execution metadata tests pass. Confirm no status transition occurs.

## 6. Parser Runtime Update Checklist

Confirm 7BV parser runtime update path tests pass. Confirm no parser update is applied and parser output remains unchanged.

## 7. Scoring Runtime Activation Checklist

Confirm 7BW scoring runtime activation tests pass. Confirm no scoring config is applied and deterministic scoring remains authoritative.

## 8. Recommendation Runtime Activation Checklist

Confirm 7BX recommendation runtime activation tests pass. Confirm no recommendation rule is applied and recommendation output remains unchanged.

## 9. ML Runtime Eligibility Checklist

Confirm 7BY ML runtime eligibility tests pass. Confirm no model is deployed, no model is loaded/saved, no runtime scoring is replaced, and no runtime eligibility or influence is granted.

## 10. Runtime Isolation Checklist

Confirm `run_analysis.py` and parser/scoring/decision/recommendation runtime paths do not import 7BU-7BY metadata modules. Confirm no active mutation functions exist for DB persistence, status transition, parser update, scoring config, recommendation rule, model deployment, runtime activation, autonomous application, or Phase 4I mutation.

## 11. Failure Handling

If a check fails, inspect the named validation group and fix only the metadata, validation, or documentation issue in scope. Do not start a DB service, do not fabricate DB validation, do not activate runtime, do not change parser/scoring/recommendation runtime behavior, and do not implement Phase 8.

## 12. Acceptance Checklist

Run `python3 scripts/run_phase7_runtime_materialization_readiness_check.py` and verify the text output says `Phase 7 runtime materialization readiness passed.` and `runtime_materialization_ready=true`. Run `python3 scripts/run_phase7_runtime_materialization_readiness_check.py --json` and verify readiness categories are true for governed workflow persistence, status transition execution, parser runtime update, scoring runtime activation, recommendation runtime activation, ML runtime eligibility, runtime isolation, and documentation completeness.
