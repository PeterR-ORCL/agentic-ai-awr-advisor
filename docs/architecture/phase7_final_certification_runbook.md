# Phase 7CJ — Final Phase 7 Certification Runbook

## Purpose

This runbook defines the step-by-step 7CZ final certification sequence. It is created in 7CJ for later execution. Running this document in 7CJ is not allowed as final certification, and 7CJ must not create `PHASE7_COMPLETE`.

## Prerequisites

- Branch: `phase7-final-operational-certification`.
- Working tree: clean before 7CZ starts.
- Latest commit: the completed 7CJ documentation commit.
- Python: project virtual environment available as `.venv/bin/python` when live DB/Object Storage dependencies are needed.
- AWR input data: final deterministic runtime input files available in `data/input/`.
- DB configuration: ADB/dev-test schema available with 7CA workflow persistence schema applied.
- Object Storage configuration: namespace, bucket, object name, region, and credentials available through environment/config only.
- Secrets: no secrets, wallet contents, OCI credentials, or generated artifacts staged.

## Safe Local Checks

Run:

```bash
git status --short
python -m py_compile scripts/run_phase7_end_to_end_validation.py
python -m py_compile scripts/run_phase7_operational_readiness_check.py
python -m unittest tests/test_phase7_end_to_end_validation.py
python -m unittest tests/test_phase7_operational_readiness_check.py
python scripts/run_phase7_end_to_end_validation.py --json
python scripts/run_phase7_operational_readiness_check.py --json
```

Expected output: safe checks pass as scripts, DB/Object Storage may be skipped, `phase7_complete=false`, `phase8_started=false`, and Phase 7 is not marked complete.

## Final Certification Checks

Run the full final-certification readiness check with live categories included:

```bash
python scripts/run_phase7_operational_readiness_check.py --final-certification --include-db --include-object-storage --json
```

Expected output:

- DB persistence validation is satisfied.
- Object Storage live path validation is satisfied.
- Screen operational wiring checks are satisfied.
- `SCREEN2_BROAD_VALIDATOR_FAILURE` is absent.
- `phase7_complete=false`.
- `phase8_started=false`.
- `phase7_operational_ready=false` until the final 7CZ tag requirement is resolved.

## Live DB Checks

Run:

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

Expected output: 5 tests run, all pass, no skips.

## Live Object Storage Checks

Run:

```bash
AWR_PHASE7CD_OBJECT_STORAGE_TEST=1 \
.venv/bin/python -m unittest -v \
  tests.test_phase7cd_object_storage_load_execution.Phase7CDObjectStorageLoadExecutionTests.test_optional_live_object_storage_validation
```

Expected output: the live Object Storage test runs, passes, and reports no skips.

## Full run_analysis.py final validation

Run this in 7CZ, not 7CJ.

```bash
python scripts/run_analysis.py
```

The script does not define CLI arguments. It reads input AWR files from `data/input/`, loads the repository `.env` if present, resolves the configured AI provider, builds deterministic Phase 4 runtime output, generates the dashboard, and prints the resulting dashboard path.

Safety requirements:

- Use deterministic runtime configuration.
- Do not enable adaptive runtime influence by default.
- Do not use this command as governed workflow execution coupling.
- Do not wire it into governed Screen 3 execution.
- Do not bypass the injected Screen 3 execution architecture.
- Do not mutate Phase 4I outside the deterministic runtime output path.
- Do not implement or invoke Phase 8 behavior.

Evidence to capture:

- Command exit code.
- Console log showing AI provider resolution, executive summary, trend findings, decision posture, recommendations, derived metric availability, HTML dashboard path, and memory persistence status.
- Generated dashboard/report path, usually the resolved `index.html` returned by `generate_html_dashboard`.
- Confirmation that generated artifacts are not staged unless explicitly required by 7CZ.
- Confirmation that no Phase 8 sizing/TCO/what-if advisory or EM Extract runtime behavior appears.

Failure handling:

- If `data/input/` has no AWR files, the script raises `FileNotFoundError`; prepare deterministic input and rerun.
- If optional DB similarity or memory persistence fails, capture the failure text and determine whether it is acceptable for final deterministic runtime certification.
- If dashboard/report output is missing, do not tag.

## Final Readiness And Tag Gate

Run:

```bash
python scripts/run_phase7_operational_readiness_check.py --final-certification --include-db --include-object-storage --fail-on-not-ready
```

If any blocker remains other than the final 7CZ tag transition itself, do not tag.

After all checks pass and the final readiness policy for 7CZ is satisfied, create the final tag:

```bash
git tag PHASE7_COMPLETE
git status
git log --oneline -1
git tag --list PHASE7_COMPLETE
```

Only 7CZ may perform this tag creation.

## Evidence Capture

Capture:

- Safe local command outputs.
- Final-certification JSON output.
- Live DB command output.
- Live Object Storage command output.
- Full `scripts/run_analysis.py` command output.
- `git diff --check`.
- `git status --short`.
- `git log --oneline -1`.
- Final tag output after tag creation.

## Rollback / No-Tag Policy

If any required validation fails, do not create `PHASE7_COMPLETE`.

If the tag was accidentally created before all checks passed, treat the tag as invalid and stop for operator review. Do not claim Phase 7 completion until 7CZ is rerun cleanly and the final tag policy is satisfied.

## Phase Boundary

7CZ must preserve these boundaries:

- Phase 4 deterministic runtime remains authoritative.
- Phase 4I remains protected.
- Dashboard workflows do not mutate truth directly.
- DB/Object Storage live validation remains env/config driven.
- No secrets are committed.
- No uncontrolled subprocess execution is introduced.
- `scripts/run_analysis.py` remains a final deterministic runtime/demo validation path, not governed workflow execution coupling.
- Phase 8 remains not started.
