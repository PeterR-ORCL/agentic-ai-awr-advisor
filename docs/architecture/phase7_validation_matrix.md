# Phase 7 Validation Matrix

## Purpose

Phase 7J provides the consolidated Phase 7 validation harness for the Agentic AI AWR Advisor project. The matrix defines how local validation proves that Phase 7A through Phase 7I remain bounded, deterministic, candidate-based, human-governed, and non-runtime-mutating.

Validation is local and deterministic. It does not require DB, OCI, ADB wallet, Oracle Agent Memory, semantic recall service, environment variables, network, or LLM calls.

## Scope

The Phase 7 validation harness covers Phase 7A Learning Boundary Definition, Phase 7B Outcome Pattern Mining, Phase 7C Learning Candidate Model, Phase 7D Candidate Generation Engine, Phase 7E Semantic Candidate Context, Phase 7F Learning Governance Bridge, Phase 7G Dashboard Learning Visibility, Phase 7H Dashboard Interactivity, and Phase 7I Learning CLI Operations.

The harness also validates import isolation, runtime safety markers, semantic boundaries, dashboard boundaries, CLI boundaries, optional Phase 6 regression execution, and validation documentation.

## Non-Goals

Phase 7J does not add learning behavior. It does not add dashboard behavior. It does not change CLI learning command behavior. It does not change parser behavior, parser output, loader behavior, scoring logic, trend or anomaly logic, decision logic, recommendation logic, recommendation ranking, or the Phase 4I output contract.

Phase 7J does not add DB writes, API calls, network calls, OCI calls, Oracle Agent Memory live calls, semantic recall service live calls, LLM calls, approval controls, write controls, runtime activation, or autonomous learning behavior.

## Validation Groups

The consolidated harness runs these named validation groups:

- `phase7_boundary`
- `outcome_pattern_mining`
- `candidate_model`
- `candidate_generation`
- `semantic_candidate_context`
- `learning_governance_bridge`
- `dashboard_learning_visibility`
- `dashboard_interactivity`
- `learning_cli`
- `import_isolation`
- `runtime_safety`
- `documentation`

The harness may also run `static_compile` and the optional `phase6_regression` group when requested with `--include-phase6`.

## Phase 7A Boundary Validation

The `phase7_boundary` group runs `tests/test_phase7_learning_boundary.py`. It proves that Phase 7 is candidate-based and human-reviewed, that deterministic runtime remains authoritative, that semantic recall remains reviewer-assist only, that dashboard selections do not mutate backend truth, and that no parser, scoring, decision, or recommendation runtime path imports `src.learning`.

This group confirms no runtime activation and no parser/scoring/decision/recommendation behavior change.

## Phase 7B Outcome Pattern Mining Validation

The `outcome_pattern_mining` group runs `tests/test_outcome_pattern_miner.py`. It proves outcome mining is observational only, uses caller-provided local records, keeps `runtime_influence=false`, keeps `requires_human_review=true`, does not generate approved candidates, and does not treat semantic recall as evidence.

Outcome pattern records remain observations. They are not diagnostic truth, recommendation truth, or runtime activation.

## Phase 7C Candidate Model Validation

The `candidate_model` group runs `tests/test_learning_candidate_model.py`. It proves learning candidates are serializable proposal-only records with required source evidence, bounded confidence, `runtime_influence=false`, and `requires_human_review=true`.

Learning candidates remain proposal/review context only. Candidate status alone does not activate runtime behavior.

## Phase 7D Candidate Generation Validation

The `candidate_generation` group runs `tests/test_learning_candidate_engine.py`. It proves candidate generation is deterministic, local, proposal-only, and derived from governed outcome pattern records or explicitly supplied local memory records.

Generated candidates remain `status=PROPOSED`, `runtime_influence=false`, and `requires_human_review=true`. The generator does not approve, implement, materialize, persist, or activate candidates.

## Phase 7E Semantic Candidate Context Validation

The `semantic_candidate_context` group runs `tests/test_semantic_candidate_context.py`. It proves semantic context remains reviewer-assist only, optional, non-authoritative, and not source evidence.

Semantic context remains reviewer-assist only. It cannot change confidence, status, diagnosis, recommendation truth, parser behavior, scoring behavior, decision behavior, or runtime behavior.

## Phase 7F Governance Bridge Validation

The `learning_governance_bridge` group runs `tests/test_learning_governance_bridge.py`. It proves governance transitions are local, deterministic, actor-gated, and non-runtime-mutating.

Approval remains approved for implementation only. Governance approval is not runtime activation, does not set `runtime_influence=true`, and does not modify parser, scoring, decision, or recommendation truth.

## Phase 7G Dashboard Learning Visibility Validation

The `dashboard_learning_visibility` group runs `tests/test_dashboard_learning_visibility.py`. It proves dashboard learning visibility remains read-only, downstream, and non-authoritative.

Dashboard learning visibility shows safety labels such as `runtime_influence=false`, `requires_human_review=true`, not diagnostic evidence, not recommendation truth, human review required, and read-only. It adds no approval controls, write controls, backend writes, API calls, or runtime activation.

## Phase 7H Dashboard Interactivity Validation

The `dashboard_interactivity` group invokes `scripts/run_phase7h_dashboard_validation.py` when that script exists. If the script is absent, the harness can fall back to the Phase 7H unittest modules.

Dashboard interactivity remains read-only. It is browser-side only, exploratory only, static-dashboard-compatible, and non-authoritative. URL hash and localStorage selection state do not change parser output, diagnostic truth, historical truth, recommendation truth, governance state, candidate status, semantic context, or learning candidates.

## Phase 7I Learning CLI Validation

The `learning_cli` group runs `tests/test_learning_cli_commands.py` and `tests/test_awr_memory_cli.py`. It proves CLI learning commands are local and actor-gated for review transitions.

CLI learning commands are local and deterministic. They do not require DB, OCI, ADB wallet, Oracle Agent Memory, semantic recall service, environment variables, network, or LLM calls. The CLI learning commands do not add runtime activation and do not change parser/scoring/decision/recommendation behavior.

## Import Isolation Validation

The `import_isolation` group recursively scans existing runtime paths with Python `ast` import parsing. It inspects `scripts/run_analysis.py`, `src/parser`, `src/parsing`, `src/scoring`, `src/decision`, `src/recommendation`, `src/recommendations`, and `src/analysis` where those paths exist.

The group proves runtime parser, parsing, scoring, decision, recommendation, and analysis modules do not import `src.learning` and do not import `scripts.awr_memory_cli`. It also proves parser/scoring/decision/recommendation paths do not import dashboard interactivity helpers.

## Runtime Safety Validation

The `runtime_safety` group validates source markers and boundary phrases. It proves `runtime_influence=false`, `requires_human_review=true`, no runtime activation, deterministic runtime remains authoritative, semantic context remains reviewer-assist only, learning candidates remain proposal/review context only, dashboard interactivity is read-only, and CLI learning commands are local and deterministic.

The group uses AST checks to detect actual `runtime_influence=True` assignments, dict values, or keyword arguments in Phase 7 learning and dashboard learning visibility paths. It avoids failing on explanatory text that says the system must not set `runtime_influence=true`.

## Semantic Boundary Validation

Semantic recall and semantic candidate context are not diagnostic evidence and are not recommendation truth. They remain reviewer-assist only, optional, non-authoritative, and marked with `runtime_influence=false`.

The validation proves semantic context remains reviewer-assist only and does not become evidence for outcome pattern mining, diagnosis, recommendations, governance decisions, or runtime activation.

## Dashboard Boundary Validation

The dashboard remains downstream of deterministic runtime output and governed records. Phase 7 dashboard learning visibility and dashboard interactivity remain read-only, exploratory, and non-authoritative.

Dashboard validation proves no backend writes, API calls, approval controls, write controls, runtime activation, parser output changes, diagnostic truth changes, historical truth changes, recommendation truth changes, governance state changes, or candidate status changes.

## CLI Boundary Validation

The learning CLI remains a local validation, visibility, export, and actor-gated review wrapper. It does not introduce live DB, network, OCI, Oracle Agent Memory, semantic recall service, or LLM dependencies for learning commands.

CLI validation proves learning commands preserve `runtime_influence=false`, `requires_human_review=true`, no runtime activation, deterministic runtime remains authoritative, and no parser/scoring/decision/recommendation behavior change.

## Phase 6 Regression Validation

Phase 6 validation is documented as a separate regression command by default. The Phase 7 harness may run it only when explicitly requested with `--include-phase6`.

The expected separate command is:

```bash
PYTHONPATH=. .venv/bin/python scripts/run_phase6_validation.py
```

If `.venv` is unavailable, developers should run the standard Python validation that their local environment supports and report any dependency limitation honestly.

## Validation Commands

The primary Phase 7J commands are:

```bash
python3 scripts/run_phase7_validation.py
python3 scripts/run_phase7_validation.py --json
python3 scripts/run_phase7_validation.py --include-phase6
```

Additional focused commands include:

```bash
python3 scripts/run_phase7h_dashboard_validation.py
python3 scripts/awr_memory_cli.py learning validate --json
python3 -m unittest tests/test_learning_cli_commands.py
python3 -m unittest tests/test_awr_memory_cli.py
python3 -m unittest tests/test_learning_governance_bridge.py
python3 -m unittest tests/test_semantic_candidate_context.py
python3 -m unittest tests/test_learning_candidate_engine.py
python3 -m unittest tests/test_learning_candidate_model.py
python3 -m unittest tests/test_outcome_pattern_miner.py
python3 -m unittest tests/test_phase7_learning_boundary.py
```

## Acceptance Criteria

Phase 7J is accepted when `scripts/run_phase7_validation.py` exists, supports normal output and `--json`, runs all required Phase 7 validation groups, returns exit code 0 on success, returns nonzero on failure, and emits deterministic JSON.

Acceptance also requires the harness to prove local and deterministic validation, no DB dependency, no network dependency, no Oracle Agent Memory dependency, no runtime activation, deterministic runtime remains authoritative, semantic context remains reviewer-assist only, learning candidates remain proposal/review context only, dashboard interactivity remains read-only, CLI learning commands are local and actor-gated, and no parser/scoring/decision/recommendation behavior change.

Phase 7J must not change parser output, diagnostic truth, historical truth, recommendation truth, governance state, candidate status, dashboard behavior, CLI learning behavior, backend write behavior, API behavior, or runtime activation state.
