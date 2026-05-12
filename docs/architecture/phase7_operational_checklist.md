# Phase 7 Operational Checklist

## 1. Purpose

This checklist defines the local operator workflow for Phase 7L readiness and release certification. It is documentation-only and validation-only. It does not add runtime behavior, learning behavior, dashboard behavior, CLI behavior, backend writes, API calls, database dependencies, Oracle Agent Memory dependencies, semantic recall service dependencies, LLM calls, or runtime activation.

## 2. Pre-Run Checklist

- Confirm the branch is `phase7-readiness-certification`.
- Confirm `git status` is clean before making certification changes.
- Confirm no parser, scoring, decision, recommendation, dashboard behavior, CLI behavior, learning behavior, database schema, generated dashboard HTML, or `scripts/run_analysis.py` files are part of the readiness change.
- Use `.venv/bin/python` if system Python lacks project dependencies such as dotenv.
- Do not use readiness failures as a reason to bypass validation.
- Do not certify if validation fails.

## 3. Validation Checklist

Run the Phase 7L readiness checker:

```bash
python3 scripts/run_phase7_readiness_check.py
```

Run the deterministic JSON readiness checker:

```bash
python3 scripts/run_phase7_readiness_check.py --json
```

Run the consolidated Phase 7 validation harness:

```bash
python3 scripts/run_phase7_validation.py
```

Run the deterministic JSON Phase 7 validation harness:

```bash
python3 scripts/run_phase7_validation.py --json
```

Run Phase 7H dashboard validation:

```bash
python3 scripts/run_phase7h_dashboard_validation.py
```

Run Phase 7I CLI validation:

```bash
python3 scripts/awr_memory_cli.py learning validate --json
```

Run Phase 6 validation where the environment supports it:

```bash
PYTHONPATH=. .venv/bin/python scripts/run_phase6_validation.py
```

## 4. CLI Checklist

- Confirm CLI learning commands are local and actor-gated.
- Confirm read-only CLI learning commands do not write backend state.
- Confirm review commands require actor attribution.
- Confirm CLI validation reports `runtime_influence=false`.
- Confirm CLI validation reports no network dependency, no database dependency, and no Oracle Agent Memory dependency.

## 5. Dashboard Checklist

- Confirm dashboard interactivity remains read-only.
- Confirm browser-side selection state is non-authoritative.
- Confirm dashboard controls do not approve candidates.
- Confirm dashboard controls do not mutate candidate status.
- Confirm dashboard controls do not mutate governance state.
- Confirm dashboard controls do not change parser output, diagnostic truth, historical truth, or recommendation truth.

## 6. Governance Checklist

- Confirm Phase 7 remains human-governed.
- Confirm candidate review transitions are actor-gated.
- Confirm approval means approved for implementation only.
- Confirm approval is not runtime activation.
- Confirm governance state is unchanged by Phase 7L.
- Confirm no backend writes were added.

## 7. Semantic Boundary Checklist

- Confirm semantic context remains reviewer-assist only.
- Confirm semantic context is non-authoritative.
- Confirm semantic context is not source evidence, deterministic evidence, approval evidence, or runtime evidence.
- Confirm semantic context does not change candidate confidence, candidate status, candidate type, runtime influence, parser output, diagnostic truth, historical truth, recommendation truth, or governance state.

## 8. Runtime Isolation Checklist

- Confirm deterministic runtime remains authoritative.
- Confirm no runtime activation exists.
- Confirm learning remains candidate-based and proposal-only.
- Confirm no autonomous parser/scoring/recommendation changes exist.
- Confirm no parser/scoring/decision/recommendation behavior change exists.
- Confirm parser output is unchanged.
- Confirm diagnostic truth is unchanged.
- Confirm historical truth is unchanged.
- Confirm recommendation truth is unchanged.

## 9. Documentation Checklist

- Confirm Phase 7 Production Readiness exists.
- Confirm Phase 7 Release Certification exists.
- Confirm Phase 7 Operational Checklist exists.
- Confirm architecture README links readiness documentation.
- Confirm required safety language is present: deterministic runtime remains authoritative; no runtime activation; candidate-based; human-governed; semantic context remains reviewer-assist only; dashboard interactivity remains read-only; CLI learning commands are local and actor-gated; no parser/scoring/decision/recommendation behavior change.

## 10. Release Checklist

- Run `python3 -m py_compile scripts/run_phase7_readiness_check.py`.
- Run `python3 -m py_compile tests/test_phase7_readiness_check.py`.
- Run `python3 -m unittest tests/test_phase7_readiness_check.py`.
- Run `python3 scripts/run_phase7_readiness_check.py`.
- Run `python3 scripts/run_phase7_readiness_check.py --json`.
- Run `python3 scripts/run_phase7_validation.py`.
- Run `python3 scripts/run_phase7_validation.py --json`.
- Run `python3 scripts/run_phase7h_dashboard_validation.py`.
- Run `python3 scripts/awr_memory_cli.py learning validate --json`.
- Run `python3 -m unittest tests/test_phase7_documentation_finalization.py`.
- Run `PYTHONPATH=. .venv/bin/python scripts/run_phase6_validation.py` where supported.
- Run `git diff --check`.

## 11. Failure Handling

If any readiness or validation command fails, stop certification and inspect the failing command output. Do not use readiness failures as a reason to bypass validation. Do not certify if validation fails.

Common failure causes include missing documentation, missing readiness links, changed safety language, missing validation scripts, unsafe imports, recursive readiness test execution, project dependency mismatch in system Python, or unintended runtime behavior changes.

If system Python lacks dependencies such as dotenv, rerun project-dependent validation with `.venv/bin/python` and report the interpreter used.

## 12. Acceptance Checklist

Phase 7L is accepted only when:

- `production_ready=true`.
- The readiness checker passes in text mode.
- The readiness checker passes in JSON mode.
- Phase 7 validation passes.
- Phase 7H validation passes.
- Phase 7I validation passes.
- Phase 7K documentation tests pass.
- Phase 6 validation passes where run.
- Deterministic runtime remains authoritative.
- Semantic context remains reviewer-assist only.
- Learning candidates remain proposal/review context only.
- Dashboard interactivity remains read-only.
- CLI learning commands are local and actor-gated.
- No parser/scoring/decision/recommendation behavior change exists.
