# Phase 7CJ — Final Phase 7 Operational Checklist

## Purpose

This checklist is the human-run operational checklist for 7CZ final certification. It is prepared in 7CJ, but it must not be executed as final certification until 7CZ.

## Pre-Run Checks

- Confirm the branch is `phase7-final-operational-certification`.
- Confirm the working tree is clean with `git status`.
- Confirm the latest commit is the expected 7CJ commit when 7CZ begins.
- Confirm no `PHASE7_COMPLETE` tag exists before final certification unless the run is explicitly verifying a completed 7CZ state.
- Confirm `.venv/bin/python` is available for project dependencies when system Python is insufficient.
- Confirm required input AWR files are present under `data/input/` for the full `scripts/run_analysis.py` validation.
- Confirm DB opt-in flags and wallet/config are prepared for final live DB validation.
- Confirm Object Storage env/config is prepared for final live Object Storage validation.
- Confirm no secrets, wallet contents, OCI credentials, generated dashboard artifacts, or unrelated files are staged.

## Safe Local Checks

Run these before live checks:

```bash
git status --short
python -m py_compile scripts/run_phase7_end_to_end_validation.py
python -m py_compile scripts/run_phase7_operational_readiness_check.py
python -m unittest tests/test_phase7_end_to_end_validation.py
python -m unittest tests/test_phase7_operational_readiness_check.py
python -m unittest tests/test_phase7_dashboard_runtime_interaction_wiring.py
python scripts/run_phase7_end_to_end_validation.py --json
python scripts/run_phase7_dashboard_runtime_interaction_validation.py --json
python scripts/run_phase7_operational_readiness_check.py --json
```

Safe local checks are non-live and non-destructive. They may skip DB and Object Storage and must not mark Phase 7 complete.

## Final Certification Checks

Run final certification readiness with live evidence:

```bash
python scripts/run_phase7_operational_readiness_check.py --final-certification --include-db --include-object-storage --json
```

The output must show DB persistence validation satisfied, Object Storage live path validation satisfied, `SCREEN2_BROAD_VALIDATOR_FAILURE` absent, `DASHBOARD_RUNTIME_INTERACTION_NOT_WIRED` absent, `phase7_complete=false`, `phase8_started=false`, and `phase7_operational_ready=false` until the 7CZ tag step is complete.

## Required Live DB Check

Use the exact DB-backed 7CA-7CE method set:

```bash
AWR_PHASE7CA_DB_TEST=1 \
AWR_PHASE7CB_DB_TEST=1 \
AWR_PHASE7CC_DB_TEST=1 \
AWR_PHASE7CD_DB_TEST=1 \
AWR_PHASE7CE_DB_TEST=1 \
.venv/bin/python -m unittest -v \
  tests.test_phase7ca_governed_workflow_repository.Phase7CAGovernedWorkflowRepositoryTests.test_optional_db_backed_insert_read_idempotency \
  tests.test_phase7cb_deterministic_execution.Phase7CBDeterministicExecutionTests.test_optional_db_backed_deterministic_execution \
  tests.test_phase7cc_comparison_execution.Phase7CCComparisonExecutionTests.test_optional_db_backed_comparison_execution \
  tests.test_phase7cd_object_storage_load_execution.Phase7CDObjectStorageLoadExecutionTests.test_optional_db_backed_object_storage_load \
  tests.test_phase7ce_dashboard_output_refresh.Phase7CEDashboardOutputRefreshTests.test_optional_db_backed_dashboard_refresh
```

Pass criteria: all 5 tests run and pass with no skips.

## Required Live Object Storage Check

Use the existing 7CD live validation path:

```bash
AWR_PHASE7CD_OBJECT_STORAGE_TEST=1 \
.venv/bin/python -m unittest -v \
  tests.test_phase7cd_object_storage_load_execution.Phase7CDObjectStorageLoadExecutionTests.test_optional_live_object_storage_validation
```

Pass criteria: the live test runs and passes with no skips. Namespace, bucket, object name, region, credentials, and rclone convenience values must come from environment/config and must not be committed.

## Screen 2 Broad Validator Check

Run:

```bash
python scripts/run_phase7_screen2_review_validation.py --json
```

Pass criteria: the broad Screen 2 validator passes and `SCREEN2_BROAD_VALIDATOR_FAILURE` remains absent from readiness output.

## Dashboard Runtime Interaction Wiring Check

Run:

```bash
python scripts/run_phase7_dashboard_runtime_interaction_validation.py --json
```

Pass criteria:

- `index_source_selection_ready=true`.
- `picker_support_ready=true`.
- `service_validation_ready=true`.
- Index-scope `blocker_active=false`.
- Screens 1–6 and cross-screen integration remain explicitly pending for 7CN–7CT.
- Index source-selection controls submit governed, validated payloads through the 7CM action contract/service bridge outside `html_dashboard.py`.
- Existing Run uses service-side lookup with selectable run options; Object Storage uses service-side validation before handoff.
- No direct `scripts/run_analysis.py` button coupling exists.
- No diagnostic truth, recommendation truth, Phase 4I, adaptive runtime default activation, or Phase 8 path is exposed.

## Full run_analysis.py Final Deterministic Demo/Runtime Check

Run this only in 7CZ, not 7CJ:

```bash
python scripts/run_analysis.py
```

The script has no CLI arguments. It reads AWR input files from `data/input/`, loads the repository `.env` when present, resolves the configured AI provider, builds deterministic analysis output, attempts DB-backed similarity and Phase 6 memory persistence when configured, and generates the dashboard via `src.reporting.html_dashboard.generate_html_dashboard`.

Pass criteria:

- The command exits zero.
- Console output includes the executive summary, trend findings, decision posture, recommendations, derived metric availability, AI narrative layer, HTML dashboard path, and memory persistence section.
- The reported dashboard path resolves to the generated dashboard `index.html`.
- The regenerated dashboard contains 7CM governed action controls and passes `python scripts/run_phase7_dashboard_runtime_interaction_validation.py --json`.
- Any generated artifacts are reviewed and either intentionally ignored or removed before commit unless 7CZ explicitly requires an artifact.
- Phase 4I is not mutated outside the deterministic runtime output path.
- Adaptive runtime influence is not enabled by default.
- No Phase 8 sizing/TCO/what-if advisory or EM Extract runtime behavior appears.

## Final Readiness Gate

Run:

```bash
python scripts/run_phase7_operational_readiness_check.py --final-certification --include-db --include-object-storage --fail-on-not-ready
```

Before the final tag step, a non-zero exit can be expected if the only remaining blocker is the 7CZ tag requirement. Do not suppress any other blocker.

## Diff And Staging Checks

Run:

```bash
git diff --check
git status --short
```

Confirm:

- No generated or unwanted artifacts are staged.
- No secrets are staged.
- No Phase 8 files or behavior are staged.
- No direct governed workflow coupling to `scripts/run_analysis.py` has been added.
- No uncontrolled subprocess behavior has been added.

## Tag Policy

Create `PHASE7_COMPLETE` only in 7CZ after every required check passes, final readiness is acceptable for tag creation, the working tree is clean, and all evidence is captured.

Do not create `PHASE7_COMPLETE` in 7CJ.

## Failure Handling

If any required check fails, do not tag. Record the failure, leave Phase 7 incomplete, and use the reserved 7CK-7CY range only for scoped remediation that preserves Phase 7 boundaries and does not become Phase 8.
