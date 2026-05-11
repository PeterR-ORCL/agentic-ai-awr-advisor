# Phase 6 Validation Matrix

This matrix defines Phase 6 validation coverage for deterministic runtime isolation, governed memory, governance safety, semantic recall boundaries, CLI operations, and dashboard truth preservation.

| Category | Purpose | Validation Method | Expected Result | Safety Boundary Verified |
| --- | --- | --- | --- | --- |
| Runtime Isolation | Ensure deterministic runtime does not depend on semantic memory. | Static source checks and import graph assertions for `scripts.run_analysis`, parser, analysis, recommendation, and reporting runtime paths. | Runtime modules do not import Oracle Agent Memory, semantic recall, or governance semantic assist modules. | Parser, scoring, decision, recommendation, and dashboard truth remain deterministic. |
| Semantic Isolation | Ensure semantic recall is observational only. | Mock semantic adapter calls and response shape assertions. | Semantic responses contain `authoritative=false`, `runtime_influence=false`, and `semantic_only=true`. | Semantic memory does not modify deterministic tables, approvals, artifacts, or runtime conclusions. |
| Governance Safety | Ensure reviewer-assist context does not become autonomous governance. | Governance assist tests scan returned context for forbidden approve/reject/recommend/materialize/parser-instruction wording. | Returned context includes `reviewer_assist_only=true` and no autonomous decision language. | Human reviewers remain authoritative. |
| Dashboard Truth Preservation | Ensure semantic visibility is isolated from diagnostic and recommendation truth. | Generated HTML checks for semantic visibility only on Screen 6 and absent from Screen 2 and Screen 5. | Screen 6 shows semantic boundary wording; Screen 2 and Screen 5 do not show semantic recall sections. | Dashboard diagnosis and recommendation truth remain deterministic. |
| CLI Operational Safety | Ensure unified CLI separates read-only and write operations. | Argparse validation and mocked service delegation tests. | Write commands require `--actor`; read commands return JSON and do not call write APIs. | CLI operations are explicit and auditable. |
| Memory Persistence Integrity | Ensure structured recall APIs preserve stable read-only shapes. | Fake connection tests assert `enabled`, `success`, `count`, `records`, ordering, limits, and no commit/rollback. | Recall APIs issue SELECT-only queries and do not mutate memory. | Governed memory recall remains read-only. |
| Recall Correctness | Ensure filters and ordering are passed correctly. | Unit tests for unknown-signal filters, knowledge artifact filters, limit enforcement, and newest/oldest order. | Filters, limits, and ordering appear in generated query behavior and returned shape. | Recall is deterministic and bounded. |
| Semantic Non-Authoritativeness | Ensure semantic recall cannot alter deterministic truth. | Response flag assertions plus dashboard wording checks. | Semantic context is labeled non-authoritative and reviewer-assist only. | Semantic recall cannot change decision posture, scoring, recommendations, or dashboard truth. |
| Import Isolation | Ensure semantic modules are lazily loaded only when explicitly used. | Runtime import assertions after importing `scripts.run_analysis`. | `oracle_agent_memory_adapter`, `semantic_recall_service`, and `governance_semantic_assist` are absent from `sys.modules`. | Semantic memory stays outside runtime truth paths. |
| Write Discipline | Ensure no hidden secondary writes or implicit semantic calls. | CLI write command tests with mocked semantic recall. | Write operations do not call semantic recall unless explicitly requested through the semantic group. | No hidden autonomous side effects. |

## Required Guarantees

- Deterministic runtime remains authoritative.
- Semantic recall remains non-authoritative.
- Governance remains human-controlled.
- Dashboard truth remains deterministic.
- CLI writes are explicit and require an actor.
- Semantic recall does not approve, reject, classify, recommend, materialize, activate artifacts, or learn.
- No Oracle Agent Memory path influences parser extraction, scoring, decision posture, recommendations, Phase 4I output, governed memory persistence, or dashboard truth.

## Validation Command

Run:

```bash
python3 -m unittest \
  tests/test_phase6_validation.py \
  tests/test_awr_memory_cli.py \
  tests/test_governance_semantic_assist.py \
  tests/test_semantic_recall_service.py \
  tests/test_oracle_agent_memory.py \
  tests/test_memory_recall.py
```

Optional consolidated runner:

```bash
PYTHONPATH=. .venv/bin/python scripts/run_phase6_validation.py
```
