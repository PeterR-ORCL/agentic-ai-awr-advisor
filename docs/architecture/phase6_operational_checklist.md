# Phase 6 Operational Checklist

This checklist supports deployment and demo readiness for Phase 6. Checked items represent the certified Phase 6 baseline. Open items are operator-specific steps to verify in the target environment.

## 1. Environment Validation

- [x] Python modules compile for Phase 6 validation and readiness tooling.
- [x] Runtime analysis does not require Oracle Agent Memory.
- [x] Semantic recall remains disabled-safe when environment variables are absent.
- [ ] Confirm target environment variables for database connectivity.
- [ ] Confirm target environment variables for OCI narrative generation if AI narrative output is required.

## 2. Database Connectivity

- [x] Governed memory code paths are isolated from semantic memory code paths.
- [x] Structured recall handles unavailable database access with structured output.
- [ ] Confirm production or demo database connectivity.
- [ ] Confirm governed memory schema is deployed where persistence is required.

## 3. OCI Provider Validation

- [x] Provider/model display is deterministic and does not use LLM-generated identity values.
- [x] Runtime diagnostics may show raw operational identifiers.
- [x] Dashboard presentation uses friendly provider/model display.
- [ ] Confirm OCI provider credentials in the target environment.
- [ ] Confirm `AI_PROVIDER=oci` when OCI execution is intended.

## 4. Memory Persistence Validation

- [x] Governed memory persists structured run, recommendation, action, outcome, feedback, unknown signal, governance, and artifact records.
- [x] Semantic memory does not write deterministic Phase 6 memory tables.
- [ ] Confirm memory persistence succeeds in the target database.

## 5. Dashboard Generation Validation

- [x] Dashboard generation completes in the validated baseline.
- [x] Dashboard truth remains deterministic.
- [x] Semantic recall visibility is informational and appears as system-level context.
- [ ] Regenerate dashboard in the target environment.
- [ ] Review generated Screen 1, Screen 2, Screen 5, Screen 6, and index pages before demo or release.

## 6. Structured Recall Validation

- [x] Structured recall APIs return stable `enabled`, `success`, `count`, and `records` shapes.
- [x] Structured recall supports bounded limits and `newest` or `oldest` ordering.
- [x] Structured recall is read-only.
- [ ] Run `scripts/awr_memory_cli.py recall summary` in the target environment.

## 7. Semantic Recall Validation

- [x] Semantic recall returns `authoritative=false`, `runtime_influence=false`, and `semantic_only=true`.
- [x] Semantic recall is optional and disabled-safe.
- [x] Oracle Agent Memory connectivity is not required for runtime analysis.
- [ ] If semantic recall is enabled, run the Oracle Agent Memory validation script in the target environment.

## 8. Governance Workflow Validation

- [x] Governance remains human-controlled.
- [x] Unknown signal review, knowledge request approval, and artifact materialization require explicit commands.
- [x] No autonomous approval or activation behavior exists.
- [ ] Confirm authorized operators understand write-command actor requirements.

## 9. CLI Validation

- [x] Unified CLI command groups exist for `recall`, `review`, `governance`, `artifact`, `semantic`, and `status`.
- [x] Write commands require `--actor`.
- [x] Semantic commands are read-only.
- [ ] Run `scripts/awr_memory_cli.py status` in the target environment.

## 10. Validation Harness Execution

- [x] Phase 6 validation harness exists.
- [x] Phase 6 readiness check exists.
- [ ] Run `PYTHONPATH=. .venv/bin/python scripts/run_phase6_validation.py`.
- [ ] Run `PYTHONPATH=. .venv/bin/python scripts/run_phase6_readiness_check.py`.

## 11. Isolation Verification

- [x] Runtime analysis remains isolated from Oracle Agent Memory.
- [x] Semantic recall cannot influence parser output, scoring, decisions, recommendations, governance approvals, artifact activation, or dashboard truth.
- [x] Dashboard truth remains deterministic.

## 12. Operational Failure Checks

- [x] Disabled semantic memory returns structured skipped output.
- [x] Missing semantic configuration does not break runtime analysis.
- [x] Semantic memory failure does not break deterministic runtime analysis.
- [ ] Confirm operational logs are reviewed after target-environment validation.

## 13. Safe Disabled-State Checks

- [x] Oracle Agent Memory disabled state is a supported operating mode.
- [x] Structured memory recall remains available independently of semantic recall.
- [x] Dashboard can render semantic recall as disabled without requiring live connectivity.

## 14. Deployment Checklist

- [ ] Validation harness passed in the target environment.
- [ ] Readiness check passed in the target environment.
- [ ] Dashboard regenerated and reviewed.
- [ ] CLI status reviewed.
- [ ] Governed memory connectivity confirmed.
- [ ] Semantic recall either validated or intentionally disabled.

## 15. Demo Readiness Checklist

- [ ] Dashboard index opens and shows governed memory status.
- [ ] Screen 1 shows intake, parser review, and governance visibility.
- [ ] Screen 2 shows deterministic diagnostic truth without unsupported claims.
- [ ] Screen 5 shows deterministic recommendation posture.
- [ ] Screen 6 shows governance, artifacts, and semantic recall visibility.
- [ ] CLI recall summary command returns structured JSON.
- [ ] No autonomous learning, autonomous approval, or semantic runtime influence is presented as active.
