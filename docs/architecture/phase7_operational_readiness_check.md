# Phase 7CI — Phase 7 Operational Readiness Check

## Purpose

7CI defines the strict operational readiness gate for final Phase 7 certification. It evaluates whether Phase 7 is ready to proceed toward final certification, while preserving the 7CG boundary that Phase 7 remains incomplete until 7CZ passes and `PHASE7_COMPLETE` is created.

The readiness checker is a gate, not new runtime behavior. It does not create learning candidates, does not materialize learning into runtime, does not activate adaptive scoring, does not mutate parser/scoring/recommendation truth, does not mutate Phase 4I, does not call `run_analysis.py` directly, and does not implement Phase 8.

## Safe Local Mode And Final Certification Mode

Safe local mode is the default:

```bash
python scripts/run_phase7_operational_readiness_check.py
```

Safe local mode performs a non-live readiness evaluation. It can run the 7CH safe harness and direct documentation checks, but it does not require DB connectivity, does not require OCI configuration, does not call live Object Storage, and does not run live DB-backed validation. Safe local mode can complete successfully as a script while reporting `phase7_operational_ready=false`.

Final certification mode is stricter:

```bash
python scripts/run_phase7_operational_readiness_check.py --final-certification
```

Final certification mode treats DB persistence validation, Object Storage live path validation, and screen-level operational wiring validation as required. If any required live check is skipped, any required screen validation is skipped or blocked, any known blocker remains unresolved, or later 7CJ/7CZ certification steps are still pending, the checker reports `phase7_operational_ready=false`.

## DB And Object Storage Requirements

DB and Object Storage checks are not run by default because they require explicit live configuration. This keeps local readiness evaluation non-destructive and avoids assuming credentials or environment availability.

For final certification, DB validation is required. The checker uses the existing opt-in DB flags and does not hard-code secrets:

```bash
AWR_PHASE7CA_DB_TEST=1
AWR_PHASE7CB_DB_TEST=1
AWR_PHASE7CC_DB_TEST=1
AWR_PHASE7CD_DB_TEST=1
AWR_PHASE7CE_DB_TEST=1
python scripts/run_phase7_operational_readiness_check.py --final-certification --include-db
```

For final certification, Object Storage live path validation is also required. OCI namespace, bucket, object name, and region must come from env/config, and the rclone remote name must not be treated as the OCI namespace:

```bash
OCI_NAMESPACE=<namespace>
OCI_BUCKET_NAME=<bucket>
OCI_OBJECT_NAME=<object-name>
OCI_REGION=<region>
python scripts/run_phase7_operational_readiness_check.py --final-certification --include-object-storage
```

If DB or Object Storage prerequisites are missing in safe local mode, the relevant requirement is skipped. If they are missing in final certification mode, readiness is blocked.

## Known Screen 2 Blocker

The checker records this blocker explicitly:

`SCREEN2_BROAD_VALIDATOR_FAILURE`

The broader Screen 2 validation script previously failed due to a dashboard/button wiring issue involving `<button` in the broader dashboard source. 7CH used targeted passing Screen 2 boundary, model, bridge, and diagnostic tests, but final Phase 7 certification requires broader Screen 2 operational wiring validation to pass.

Impact: `phase7_operational_ready=false` until resolved.

Expected remediation: use the reserved 7CK–7CY fix range if the blocker is not resolved by 7CI validation work.

The blocker must not be hidden, downgraded to an informational warning, or bypassed by targeted Screen 2 tests.

7CK remediates this blocker only when the broad Screen 2 validator passes. The readiness checker evaluates the broad validator directly; the blocker remains active if that validation fails and is absent from active blockers when the broad validator succeeds.

## Screen Operational Wiring Policy

By final Phase 7 certification, all Phase 7 dashboard workflow screens must be interactive and properly wired within their governed Phase 7 scope. This does not permit uncontrolled backend mutation.

Screen 1 parser governance controls must be wired to governed source intake, parser unknown review, and knowledge artifact review paths where Phase 7 allows them.

Screen 2 diagnostic review controls must be wired to governed diagnostic review, evidence, and governance bridge paths without mutating diagnostic truth, severity, confidence, scores, recommendations, parser output, or Phase 4I.

Screen 3 backend re-analysis submit workflow must be wired through governed persistence and injected deterministic execution, comparison, Object Storage, and dashboard refresh paths.

Screen 4 historical review controls must be wired to governed baseline, trend, anomaly, and candidate-intent paths without directly mutating historical truth, trend truth, anomaly truth, scoring, recommendations, or Phase 4I.

Screen 5 recommendation/action/outcome controls must be wired to governed recommendation decision, action, outcome, and feedback paths without silently changing recommendation truth or Phase 4I.

Screen 6 governance controls must be wired to governed candidate, materialization, model, and runtime-gate review paths without uncontrolled activation or runtime influence.

Index/source mode source selection handoff must be wired into the supported Phase 7 source-selection path.

Final readiness must not mark a screen ready when broad validation is skipped, known validation failure exists, wiring is preview-only where active governed wiring is required, wiring bypasses governance, wiring mutates backend truth directly, wiring mutates Phase 4I, or wiring activates runtime influence by default.

## Readiness Status Semantics

Each requirement is reported with:

- `id`
- `name`
- `category`
- `required_for_final_certification`
- `status`
- `evidence`
- `reason`
- `remediation_subphase`

Allowed statuses are:

- `satisfied`: the requirement has evidence for the current readiness mode.
- `blocked`: the requirement is required and cannot currently be accepted.
- `skipped`: the requirement was not run in the current safe or optional mode.
- `pending`: the requirement belongs to a later 7CJ or 7CZ step.

`phase7_operational_ready=true` is allowed only when final certification mode is active, all final certification requirements are satisfied, DB validation passed, Object Storage live validation passed, all screen operational wiring validations passed, no known blockers exist, Phase 4I protection is satisfied, no Phase 8 behavior is present, and final 7CJ/7CZ documentation and tag requirements are complete.

For 7CI, `phase7_operational_ready=false` is expected while blockers, skipped final checks, or later certification steps remain.

## CLI Usage

```bash
python scripts/run_phase7_operational_readiness_check.py
python scripts/run_phase7_operational_readiness_check.py --json
python scripts/run_phase7_operational_readiness_check.py --final-certification
python scripts/run_phase7_operational_readiness_check.py --final-certification --json
python scripts/run_phase7_operational_readiness_check.py --final-certification --fail-on-not-ready
python scripts/run_phase7_operational_readiness_check.py --include-db
python scripts/run_phase7_operational_readiness_check.py --include-object-storage
python scripts/run_phase7_operational_readiness_check.py --include-phase6
python scripts/run_phase7_operational_readiness_check.py --list-requirements
```

`--fail-on-not-ready` exits non-zero when `phase7_operational_ready=false`. This is intended for later CI/release gating and is expected to fail while blockers remain.

## JSON Output Contract

`--json` emits valid JSON with at least:

- `phase`
- `subphase`
- `readiness_name`
- `phase7_operational_ready`
- `phase7_complete`
- `phase8_started`
- `final_certification_mode`
- `safe_local_mode`
- `required_final_certification_checks`
- `satisfied_checks`
- `blocked_checks`
- `skipped_checks`
- `known_blockers`
- `invariants`
- `next_subphase`

Required invariant values include `phase="Phase 7"`, `subphase="7CI"`, `phase7_complete=false`, `phase8_started=false`, `phase8_behavior_implemented=false`, `deterministic_runtime_authoritative=true`, `phase4i_contract_protected=true`, `runtime_influence_denied_by_default=true`, `screen_wiring_required_for_final_certification=true`, `db_validation_required_for_final_certification=true`, and `object_storage_validation_required_for_final_certification=true`.

## Final Certification Requirements

The checker models these final certification requirements:

- 7CG final operational certification boundary exists and is referenced.
- 7CH end-to-end validation harness exists and passes safe validation.
- Phase 7 learning foundation is represented and not runtime-active by default.
- Controlled learning materialization is represented and not runtime-active by default.
- ML/adaptive scoring foundation is represented and shadow/advisory only.
- Controlled adaptive runtime integration is represented and denied by default.
- Dashboard workflow infrastructure is represented.
- Screen 1 parser governance workflow operational wiring is validated.
- Screen 2 diagnostic review workflow operational wiring is validated.
- Screen 3 active backend execution operational wiring is validated.
- Screen 4 historical review workflow operational wiring is validated.
- Screen 5 recommendation/action/outcome workflow operational wiring is validated.
- Screen 6 governance control plane operational wiring is validated.
- Index/source mode entry and Screen 3 handoff are validated.
- Runtime materialization metadata is validated without activation.
- DB persistence validation passed.
- Object Storage live path validation passed.
- Deterministic fallback/rollback behavior is validated.
- Phase 4I output contract is protected.
- No uncontrolled runtime mutation exists.
- No direct uncontrolled subprocess execution exists.
- No direct governed workflow coupling to `run_analysis.py` exists.
- No adaptive runtime activation occurs by default.
- No Phase 8 implementation exists.
- Known blockers are resolved.
- Final release documentation remains pending until 7CJ.
- Final certification and the `PHASE7_COMPLETE` tag remain pending until 7CZ.

## Phase Boundary

Phase 7 remains incomplete after 7CI.

Phase 8 remains not started.

7CI does not create `PHASE7_COMPLETE`. The final tag is only allowed after 7CZ final certification passes.

## Next Step

The next subphase depends on readiness gaps. Proceed to 7CJ only if release certification documentation is the remaining planned work. Use the reserved 7CK–7CY range for fixes discovered during certification, including the known Screen 2 broad validator blocker if it remains unresolved.
