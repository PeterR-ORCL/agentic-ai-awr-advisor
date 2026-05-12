# Phase 7 Validation Harness

## Purpose

The Phase 7 validation harness provides one repeatable local entry point for validating Phase 7A through Phase 7I. It is validation-only and exists to prove that learning remains candidate-based, human-governed, proposal-only, and non-runtime-mutating.

The harness is local and deterministic. It requires no DB, OCI, ADB wallet, Oracle Agent Memory, semantic recall service, environment variables, network, or LLM calls.

## Script Usage

Run the default local Phase 7 suite with:

```bash
python3 scripts/run_phase7_validation.py
```

Emit deterministic JSON with:

```bash
python3 scripts/run_phase7_validation.py --json
```

Optionally include Phase 6 regression validation with:

```bash
python3 scripts/run_phase7_validation.py --include-phase6
```

Phase 6 validation is not required by default because Phase 7J is focused on the local Phase 7 validation harness.

## JSON Output

The JSON output includes these top-level fields:

- `phase`
- `command`
- `success`
- `validation_groups`
- `tests_run`
- `checks_run`
- `failures`
- `errors`
- `skipped`
- `runtime_influence`
- `deterministic_runtime_remains_authoritative`
- `semantic_context_non_authoritative`
- `learning_candidates_proposal_only`
- `dashboard_interactivity_read_only`
- `cli_learning_local_only`
- `network_dependency`
- `database_dependency`
- `oracle_agent_memory_dependency`
- `phase6_validation_included`

The expected safety markers are `runtime_influence=false`, deterministic runtime remains authoritative, semantic context remains reviewer-assist only, learning candidates remain proposal/review context only, dashboard interactivity is read-only, and CLI learning commands are local and deterministic.

## Validation Groups

The harness runs the required groups `phase7_boundary`, `outcome_pattern_mining`, `candidate_model`, `candidate_generation`, `semantic_candidate_context`, `learning_governance_bridge`, `dashboard_learning_visibility`, `dashboard_interactivity`, `learning_cli`, `import_isolation`, `runtime_safety`, and `documentation`.

It also performs static compile checks for Phase 7 modules and can optionally run Phase 6 regression validation.

## Expected Success Output

Successful text output begins with:

```text
Phase 7 validation passed.
```

It then reports test counts, check counts, failure counts, error counts, skipped counts, and the boundary confirmations:

```text
runtime_influence=false
requires_human_review=true
no runtime activation
deterministic runtime remains authoritative
semantic context remains reviewer-assist only
learning candidates remain proposal/review context only
dashboard interactivity is read-only
CLI learning commands are local and deterministic
```

## Failure Behavior

The script returns a nonzero exit code when any required validation group fails. JSON output sets `success=false`, and the failing group includes details for the failed tests or checks.

The harness does not fabricate success. Missing required Phase 7 tests, missing validation documentation, import isolation violations, unsafe runtime markers, or failed unit tests fail the run.

## CI Usage

CI can run:

```bash
python3 scripts/run_phase7_validation.py --json
```

The command is safe for CI because it uses the Python standard library, avoids `shell=True`, captures subprocess output for JSON mode, does not require network, does not require DB access, does not require OCI credentials, does not require Oracle Agent Memory, and does not modify the repository.

## Local Developer Usage

Developers should run:

```bash
python3 scripts/run_phase7_validation.py
```

For focused follow-up, developers may run the Phase 7H dashboard validation script, the learning CLI validation command, or individual Phase 7 unittest modules listed in the validation matrix.

## Non-Goals

The harness does not add learning behavior, dashboard behavior, CLI learning behavior, backend writes, API calls, approval controls, write controls, runtime activation, parser changes, scoring changes, decision changes, recommendation changes, or Phase 4I output contract changes.

It does not implement Phase 7K documentation finalization or Phase 7L production readiness certification.

## Acceptance Criteria

The harness is accepted when it runs the complete local Phase 7 validation set, emits deterministic JSON with the required safety fields, proves no runtime activation, proves deterministic runtime remains authoritative, proves semantic context remains reviewer-assist only, proves dashboard interactivity remains read-only, proves CLI learning commands are local and actor-gated, proves learning candidates remain proposal/review context only, and proves no parser/scoring/decision/recommendation behavior change.
