# Phase 7I Learning CLI Operations

## 1. Purpose

Phase 7I adds safe CLI learning commands to the existing unified memory CLI at `scripts/awr_memory_cli.py learning ...`. The commands provide local operational visibility and governed review workflow support for Phase 7 learning records.

The commands are local and deterministic. They inspect local JSON input, call existing Phase 7 learning modules, and print JSON or human-readable output. They do not activate runtime behavior.

## 2. Scope

Phase 7I covers the `learning` command group only. It exposes local status, local outcome pattern mining, proposal-only learning candidate generation, local candidate detail display, local reviewer-assist semantic context attachment, local governance review transitions, local export normalization, and local validation wrappers.

Every learning command keeps `runtime_influence=false`. Candidate-producing and review commands keep `requires_human_review=true`.

## 3. Non-Goals

Phase 7I does not implement runtime learning. It does not implement Phase 7J validation harness work beyond CLI-specific local validation, Phase 7K documentation finalization, or Phase 7L readiness certification.

It does not modify parser logic, scoring logic, decision logic, recommendation logic, Phase 4I output, dashboard truth, generated dashboards, database schema, runtime configuration, or repository files unless the user explicitly supplies a local export output path.

## 4. CLI Command Group

The command namespace is:

```bash
python3 scripts/awr_memory_cli.py learning ...
```

The command group is an operational wrapper over existing Phase 7 modules:

- `src.learning.outcome_pattern_miner`
- `src.learning.learning_candidate_model`
- `src.learning.learning_candidate_engine`
- `src.learning.semantic_candidate_context`
- `src.learning.learning_governance_bridge`

## 5. Command Summary

The Phase 7I commands are:

- `learning status`
- `learning patterns`
- `learning candidates`
- `learning candidate-detail`
- `learning semantic-context`
- `learning review`
- `learning export`
- `learning validate`

All commands are local and deterministic. No command writes to Oracle DB, requires OCI or ADB, requires Oracle Agent Memory, uses a semantic recall service, makes a network call, or activates candidates.

## 6. learning status

`learning status` reports whether the Phase 7 learning modules are available. It reports the outcome pattern miner, candidate model, candidate engine, semantic candidate context module, and governance bridge.

The status output states `runtime_influence=false`, that deterministic runtime remains authoritative, and that there is no runtime activation.

## 7. learning patterns

`learning patterns` mines observational outcome patterns from local JSON memory records:

```bash
python3 scripts/awr_memory_cli.py learning patterns --input memory.json --json
```

If no input is supplied, the command uses empty memory records and returns a safe empty pattern list. It is read-only, does not write database state, and does not generate candidates. Pattern records are not learning candidates.

## 8. learning candidates

`learning candidates` generates proposal-only learning candidates from local pattern JSON or, with `--from-memory`, from locally mined memory records:

```bash
python3 scripts/awr_memory_cli.py learning candidates --input patterns.json --json
python3 scripts/awr_memory_cli.py learning candidates --from-memory --input memory.json --json
```

Generated candidates have `status=PROPOSED`, `runtime_influence=false`, and `requires_human_review=true`. The command does not approve, implement, materialize, persist, or activate candidates.

## 9. learning candidate-detail

`learning candidate-detail` shows one candidate from a local JSON candidate file:

```bash
python3 scripts/awr_memory_cli.py learning candidate-detail --input candidates.json --candidate-id CANDIDATE-ID --json
```

The command is read-only. It does not mutate the candidate, does not persist state, and does not activate runtime behavior.

## 10. learning semantic-context

`learning semantic-context` attaches optional reviewer-assist semantic context from local JSON semantic records:

```bash
python3 scripts/awr_memory_cli.py learning semantic-context \
  --candidate-input candidate.json \
  --semantic-input semantic_records.json \
  --json
```

Semantic context is reviewer-assist only, optional, non-authoritative, and not source evidence. Semantic context is not evidence and is not `source_evidence`. It must not change confidence, status, candidate type, source evidence, structured sources, or runtime influence.

This command does not call live semantic services. It has no Oracle Agent Memory dependency, no semantic recall service dependency, and no network dependency.

## 11. learning review

`learning review` applies local governed status transitions through the Phase 7F governance bridge:

```bash
python3 scripts/awr_memory_cli.py learning review \
  --input candidate.json \
  --action approve-for-implementation \
  --actor reviewer@example.com \
  --json
```

Allowed actions are `under-review`, `reject`, `needs-revision`, `approve-for-implementation`, `attach-materialization`, `implemented`, `validated`, and `close`.

Actor required: every review action requires `--actor`. Approval means approved for implementation only, not runtime activation. Review output preserves `runtime_influence=false` and `requires_human_review=true`.

## 12. learning export

`learning export` normalizes local learning records to JSON:

```bash
python3 scripts/awr_memory_cli.py learning export --input candidates.json --kind candidates
python3 scripts/awr_memory_cli.py learning export --input patterns.json --kind patterns --output normalized.json
```

By default, output is written to stdout only. Optional `--output` writes a user-provided local JSON file only when explicitly requested. Existing files are not overwritten unless `--force` is supplied. This is local file output only and is not runtime persistence.

## 13. learning validate

`learning validate` runs the local Phase 7 learning validation subset:

```bash
python3 scripts/awr_memory_cli.py learning validate --json
```

The command runs deterministic unittest modules for Phase 7B through Phase 7F learning modules when available. It does not require DB, OCI, ADB wallet, Oracle Agent Memory, a semantic recall service, environment variables, or network access.

## 14. Local JSON Input Shapes

Memory input may be:

```json
{
  "runs": [],
  "recommendations": [],
  "actions": [],
  "outcomes": [],
  "feedback": [],
  "unknown_signals": [],
  "knowledge_requests": [],
  "knowledge_artifacts": []
}
```

Pattern input may be `{ "patterns": [] }`, a list of pattern objects, or one pattern object.

Candidate input may be `{ "candidates": [] }`, a list of candidate objects, `{ "candidate": { ... } }`, or one candidate object.

Semantic input may be `{ "semantic_records": [] }`, a list of semantic records, or one local semantic record object.

Validation errors are explicit and local. They do not trigger database, network, OCI, ADB, Oracle Agent Memory, or semantic recall activity.

## 15. Output Modes

Read-oriented commands support human-readable output by default and JSON output with `--json`. `learning export` emits JSON by default.

JSON output is deterministic: keys are sorted, generated IDs come from existing deterministic Phase 7 modules, and no timestamps are introduced unless already present in input.

Human-readable output includes safety labels such as `runtime_influence=false`, `requires_human_review=true`, proposal-only where applicable, read-only where applicable, no runtime activation, and deterministic runtime remains authoritative.

## 16. Actor Requirement

Actor required for review/write actions. `learning review` requires `--actor` for every action, including approval, rejection, revision, materialization attachment, implemented, validated, and close transitions.

Read-only commands do not require actor: `learning status`, `learning patterns`, `learning candidates`, `learning candidate-detail`, and `learning validate`.

## 17. Review / Write Boundary

Review transitions are local governance records only. They do not write to a database, do not update Phase 6 memory tables, do not update generated dashboards, and do not activate learning candidates.

Approval means approved for implementation only. It is not runtime activation, not runtime integration, and not permission for uncontrolled autonomous learning.

## 18. Runtime Truth Boundary

Deterministic runtime remains authoritative. CLI learning commands may inspect and review learning state but may not activate runtime behavior.

No Phase 7I command sets runtime influence. All candidate and governance outputs preserve `runtime_influence=false`.

## 19. Parser / Scoring / Decision / Recommendation Boundary

Phase 7I does not modify parser behavior, parser output, loader behavior, scoring logic, scoring weights, trend or anomaly logic, decision logic, recommendation logic, recommendation ranking, or the Phase 4I output contract.

Runtime parser, scoring, decision, and recommendation paths must not import CLI learning code.

## 20. Semantic Context Boundary

Semantic context is reviewer-assist only. It is optional, non-authoritative, and not evidence. It is not `source_evidence`.

The semantic context command uses local JSON records only. It does not call Oracle Agent Memory, does not call a semantic recall service, does not call an LLM, and has no network dependency.

## 21. Governance Boundary

The governance bridge is local and deterministic. It records explicit human-governed transitions and audit-shaped decision output.

All review transitions preserve `requires_human_review=true` and `runtime_influence=false`. Approval is approved for implementation only, not runtime activation.

## 22. Persistence Boundary

No DB writes are performed. No Oracle DB writes, Phase 6 memory table writes, dashboard file writes, parser code writes, scoring config writes, recommendation writes, or runtime logic writes are performed.

Optional `--output` writes are local JSON file output only, user-specified, explicit, and protected from accidental overwrite unless `--force` is supplied.

## 23. Dashboard Boundary

Dashboard interactivity remains separate and read-only. Phase 7I does not add dashboard approval controls, dashboard write controls, dashboard truth changes, generated dashboard updates, semantic boundary label changes, or browser-side interactivity changes.

## 24. Validation Requirements

Phase 7I validation must run locally and deterministically. Required local validation includes:

- `tests.test_outcome_pattern_miner`
- `tests.test_learning_candidate_model`
- `tests.test_learning_candidate_engine`
- `tests.test_semantic_candidate_context`
- `tests.test_learning_governance_bridge`
- `tests.test_learning_cli_commands`

Existing Phase 7A through Phase 7H validations should continue to pass. Phase 6 validation should continue to pass when the environment supports it.

## 25. Acceptance Criteria

Phase 7I is accepted when the unified CLI exposes the `learning` command group with status, patterns, candidates, candidate-detail, semantic-context, review, export, and validate commands.

The accepted implementation must be local and deterministic; must add no DB writes; must add no network dependency; must add no Oracle Agent Memory dependency; must add no semantic recall service dependency; must keep approval approved for implementation only; must add no runtime activation; must keep `runtime_influence=false`; must keep `requires_human_review=true`; must keep semantic context reviewer-assist only; must keep dashboard interactivity separate and read-only; must not modify parser, scoring, decision, or recommendation behavior; and must not implement runtime learning.
