# Phase 7R Controlled Learning Materialization Operational Checklist

## Purpose

This checklist gives operators the local commands and pass/fail criteria for Phase 7R controlled learning materialization validation and readiness certification.

## Pre-Run Checklist

- Confirm the branch is `phase7-materialization-certification`.
- Confirm the working tree is clean before certification.
- Use `.venv/bin/python` if system Python lacks project dependencies such as dotenv.
- Confirm no database, OCI, Oracle Agent Memory, semantic recall service, or network access is required.

## Validation Checklist

- Run `python3 scripts/run_phase7_materialization_validation.py`.
- Run `python3 scripts/run_phase7_materialization_validation.py --json`.
- Confirm the text output says `Phase 7 materialization validation passed.`
- Confirm the JSON output reports `success=true`.

## Materialization Boundary Checklist

- Confirm candidate approval does not equal runtime activation.
- Confirm materialization is separate from approval.
- Confirm materialization is not activation.
- Confirm `runtime_influence_granted=false`.

## Artifact Checklist

- Confirm approved candidates become local controlled artifacts only.
- Confirm materialized artifacts are not runtime active.
- Confirm validated artifacts are not runtime active by themselves.

## Scoring Review Checklist

- Confirm adaptive scoring review remains proposal-only.
- Confirm proposed scoring configs report `runtime_active=false`.
- Confirm proposed scoring configs report `runtime_influence_granted=false`.
- Confirm no automatic scoring mutation exists.

## Recommendation Evolution Checklist

- Confirm recommendation rule evolution remains proposal-only.
- Confirm proposed recommendation rules report `runtime_active=false`.
- Confirm proposed recommendation rules report `runtime_influence_granted=false`.
- Confirm no automatic recommendation mutation exists.

## Parser Evolution Checklist

- Confirm parser evolution is first-class and protected.
- Confirm parser backlog items report `runtime_active=false`.
- Confirm parser backlog items report `runtime_influence_granted=false`.
- Confirm no automatic parser mutation exists.
- Do not bypass parser regression boundaries.

## Runtime Isolation Checklist

- Confirm `scripts/run_analysis.py` does not import materialization/evolution modules.
- Confirm parser runtime paths do not import materialization/evolution modules.
- Confirm scoring runtime paths do not import materialization/evolution modules.
- Confirm recommendation runtime paths do not import materialization/evolution modules.
- Confirm parser/scoring/recommendation runtime paths remain authoritative.

## Documentation Checklist

- Confirm `docs/architecture/phase7_materialization_validation_matrix.md` exists.
- Confirm `docs/architecture/phase7_materialization_readiness.md` exists.
- Confirm `docs/architecture/phase7_materialization_release_certification.md` exists.
- Confirm `docs/architecture/phase7_materialization_operational_checklist.md` exists.
- Confirm `docs/architecture/README.md` links the readiness and certification docs.

## Failure Handling

Do not certify if validation fails. Do not bypass parser regression boundaries. Do not mark `materialization_ready=true` manually. Fix the failing local validation, rerun the commands, and preserve `runtime_influence_granted=false` and `runtime_active=false`.

## Acceptance Checklist

- Run `python3 scripts/run_phase7_materialization_readiness_check.py`.
- Run `python3 scripts/run_phase7_materialization_readiness_check.py --json`.
- Run `python3 scripts/run_phase7_validation.py`.
- Run `python3 scripts/run_phase7_readiness_check.py`.
- Run `python3 scripts/run_phase7h_dashboard_validation.py`.
- Run `.venv/bin/python scripts/awr_memory_cli.py learning validate --json`.
- Run `PYTHONPATH=. .venv/bin/python scripts/run_phase6_validation.py`.
- Confirm readiness output says `Phase 7 controlled materialization readiness passed.`
- Confirm readiness output says `materialization_ready=true`.
- Confirm no parser behavior, scoring behavior, recommendation behavior, dashboard behavior, or CLI behavior changed.
