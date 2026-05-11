# Phase 6 CLI Operations

This document defines the unified Phase 6 operational CLI surface for memory, governance, recall, artifacts, and semantic assistance.

## Entrypoint

Use:

```bash
PYTHONPATH=. .venv/bin/python scripts/awr_memory_cli.py <command>
```

The CLI prints JSON by default. Use `--compact` before the command for compact JSON output.

## Command Groups

The unified command groups are:

- `status`
- `recall`
- `review`
- `governance`
- `artifact`
- `semantic`

## Read-Only Commands

These commands are read-only:

- `status`
- `recall summary`
- `recall runs`
- `recall recommendations`
- `recall actions`
- `recall outcomes`
- `recall feedback`
- `recall unknown-signals`
- `recall knowledge-requests`
- `recall knowledge-artifacts`
- `artifact list`
- `semantic status`
- `semantic recall`
- `semantic assist-unknown-signal`
- `semantic assist-knowledge-request`
- `semantic assist-artifact`
- `semantic assist-parser-governance`

Examples:

```bash
PYTHONPATH=. .venv/bin/python scripts/awr_memory_cli.py status

PYTHONPATH=. .venv/bin/python scripts/awr_memory_cli.py recall unknown-signals \
  --status NEW \
  --limit 5 \
  --order newest

PYTHONPATH=. .venv/bin/python scripts/awr_memory_cli.py semantic recall \
  --query "SPRTRN io pressure" \
  --limit 5
```

## Explicit Write Commands

These commands perform explicit governance or review writes and require `--actor`:

- `review unknown-signal`
- `governance create-request`
- `governance approve-request`
- `artifact materialize`

Examples:

```bash
PYTHONPATH=. .venv/bin/python scripts/awr_memory_cli.py review unknown-signal \
  --unknown-signal-id 1 \
  --review-status CLASSIFIED \
  --review-classification IO \
  --review-notes "Validated from CLI integration" \
  --actor probev

PYTHONPATH=. .venv/bin/python scripts/awr_memory_cli.py governance create-request \
  --source-type UNKNOWN_SIGNAL \
  --source-id 1 \
  --classification IO \
  --summary "Unknown IO section consistently detected" \
  --details "Observed across repeated AWR parser gaps" \
  --actor probev

PYTHONPATH=. .venv/bin/python scripts/awr_memory_cli.py governance approve-request \
  --request-id 1 \
  --approval-status APPROVED \
  --actor senior_dba \
  --notes "Confirmed valid mapping"

PYTHONPATH=. .venv/bin/python scripts/awr_memory_cli.py artifact materialize \
  --request-id 1 \
  --artifact-type SIGNAL_CLASSIFICATION \
  --classification IO \
  --summary "Approved IO classification for unknown signal" \
  --details "Derived from approved governance request" \
  --actor probev
```

## Safety Boundaries

The unified CLI delegates to existing Phase 6 APIs and does not shell out to older scripts. Existing individual scripts remain available.

Semantic recall remains non-authoritative and reviewer-assist only. It does not approve, reject, classify, materialize, activate artifacts, alter parser behavior, change scoring, change recommendations, change Phase 4I output, or influence runtime dashboard truth.

Write commands do not call semantic recall implicitly. Semantic assistance must be requested explicitly through the `semantic` command group.
