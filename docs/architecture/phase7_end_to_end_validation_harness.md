# Phase 7CH — End-to-End Validation Harness Consolidation

## Purpose

Phase 7CH adds a consolidated end-to-end validation harness for the final Phase 7 operational certification block. The harness orchestrates existing Phase 7 validation and readiness checks through an explicit allowlist, summarizes their results, and preserves the 7CG boundary that Phase 7 remains incomplete until 7CZ passes and `PHASE7_COMPLETE` is created.

The harness is validation orchestration only. It does not add operational behavior, does not create new workflow features, does not mutate runtime truth, and does not implement Phase 8.

## Safe Default Behavior

The default command is:

```bash
python scripts/run_phase7_end_to_end_validation.py
```

Default mode runs non-live, non-destructive checks only. It does not require DB connectivity, does not require OCI credentials, does not call live Object Storage, does not run live DB-backed tests, does not regenerate dashboard artifacts by default, does not execute governed workflow actions outside existing test-safe validation paths, and does not activate adaptive runtime influence.

## CLI Usage Examples

```bash
python scripts/run_phase7_end_to_end_validation.py
python scripts/run_phase7_end_to_end_validation.py --json
python scripts/run_phase7_end_to_end_validation.py --fast
python scripts/run_phase7_end_to_end_validation.py --fast --json
python scripts/run_phase7_end_to_end_validation.py --full --json
python scripts/run_phase7_end_to_end_validation.py --include-db
python scripts/run_phase7_end_to_end_validation.py --include-object-storage
python scripts/run_phase7_end_to_end_validation.py --include-phase6
python scripts/run_phase7_end_to_end_validation.py --include-db --include-object-storage --strict-live
python scripts/run_phase7_end_to_end_validation.py --list-checks
```

## Fast And Full Modes

Fast mode runs the smallest safe subset used for quick harness verification. It includes the 7CG boundary document check, invariant metadata, the Phase 7 learning foundation validation, controlled materialization validation, ML/adaptive scoring validation, controlled adaptive runtime integration validation, Screen 3 re-analysis validation, and active Screen 3 backend execution validation.

Default mode runs the safe non-live validation set across the represented Phase 7 blocks. It still skips DB-backed, live Object Storage, Phase 6, and broad readiness checks unless explicit flags or full mode are used.

Full mode adds a broader bounded set of existing readiness checks where available. It remains non-live unless `--include-db` or `--include-object-storage` is also provided. Full mode includes readiness checks for learning, materialization, ML, index/source mode, runtime materialization metadata, and active Screen 3 backend execution. Known slow global and screen-workflow readiness checks are represented in the registry and reported as skipped in 7CH so later 7CI and 7CK–7CY work can run or remediate them deliberately.

## DB Opt-In Behavior

DB-backed checks run only with:

```bash
python scripts/run_phase7_end_to_end_validation.py --include-db
```

The harness requires the existing opt-in DB flags before it runs DB-backed validation:

- `AWR_PHASE7CA_DB_TEST=1`
- `AWR_PHASE7CB_DB_TEST=1`
- `AWR_PHASE7CC_DB_TEST=1`
- `AWR_PHASE7CD_DB_TEST=1`
- `AWR_PHASE7CE_DB_TEST=1`

If these flags are missing, DB checks are skipped by default. With `--strict-live`, missing DB flags fail the harness. No DB secrets are hard-coded and the harness does not invent credentials. In 7CL, live evidence that exits zero but reports skipped live tests is treated as failed evidence for requested DB checks.

## Object Storage Opt-In Behavior

Object Storage live validation runs only with:

```bash
python scripts/run_phase7_end_to_end_validation.py --include-object-storage
```

The harness requires Object Storage metadata from environment/config before it enables the existing live 7CD validation path. Supported environment names include `OCI_NAMESPACE` or `OCI_OBJECT_STORAGE_NAMESPACE`, `OCI_BUCKET_NAME` or `OCI_OBJECT_STORAGE_BUCKET`, `OCI_OBJECT_NAME` or `OCI_OBJECT_STORAGE_OBJECT_NAME`, and `OCI_REGION`.

If these values are missing, Object Storage checks are skipped by default. With `--strict-live`, missing Object Storage metadata fails the harness. The harness does not hard-code OCI namespace, bucket, object name, region, credentials, or rclone remote values. In 7CL, live evidence that exits zero but reports skipped live tests is treated as failed evidence for requested Object Storage checks.

## Strict-Live Behavior

`--strict-live` changes missing requested live prerequisites from skipped to failed. It only applies to requested live categories such as `--include-db` and `--include-object-storage`.

Strict-live mode does not create credentials, does not assume DB availability, and does not assume Object Storage availability. It only enforces that explicitly requested live checks must have the required opt-in env/config.

## JSON Output Contract

`--json` emits valid JSON with these top-level fields:

- `phase`
- `subphase`
- `validation_name`
- `operational_certification_scope`
- `overall_status`
- `phase7_complete`
- `phase8_started`
- `checks`
- `skipped_checks`
- `invariants`
- `failures`

The required invariant values are `phase="Phase 7"`, `subphase="7CH"`, `phase7_complete=false`, and `phase8_started=false`.

Each check record includes its name, category, command, required flag, status, return code, reason, stdout tail, stderr tail, and description.

## Safety Boundaries

The harness uses explicit check allowlists. It uses argument-list subprocess calls with `shell=False`, runs from the repository root, captures output, and does not execute arbitrary discovered files.

For Screen 2, the harness uses targeted existing boundary, model, governance bridge, and diagnostic exploration tests. The broader Screen 2 review-panel validator is evaluated by the operational readiness gate and was remediated in 7CK.

The harness explicitly reports these invariant values:

- `phase7_complete=false`
- `phase8_started=false`
- `deterministic_runtime_authoritative=true`
- `phase4i_contract_protected=true`
- `uncontrolled_runtime_mutation_allowed=false`
- `adaptive_runtime_default_active=false`
- `phase8_behavior_implemented=false`

These are harness metadata assertions. Deeper proof remains tied to the selected underlying validation and readiness checks.

## What The Harness Does Not Do

The 7CH harness does not create or approve learning candidates, materialize learning into runtime, activate adaptive runtime scoring, change runtime gates, mutate parser/scoring/recommendation truth, mutate Phase 4I output contracts, regenerate dashboard artifacts by default, call `run_analysis.py` directly, invoke arbitrary shell commands, hard-code live OCI values, implement EM Extract runtime support, or implement sizing/TCO/what-if advisory.

## Expected Next Step

Next subphase:

7CI — Phase 7 Operational Readiness Check
