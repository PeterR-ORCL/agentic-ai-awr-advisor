# Phase 6 Memory Architecture

This document is the authoritative architectural overview for Phase 6 memory, governance, recall, semantic context, CLI operations, dashboard visibility, and validation.

## 1. Phase 6 Objectives

Phase 6 adds governed downstream memory around deterministic AWR analysis. Its objectives are to persist auditable run context, record actions and outcomes, capture feedback, review unknown parser signals, govern candidate knowledge updates, expose structured recall, and provide optional semantic reviewer assistance.

Phase 6 does not change deterministic analysis. It preserves the Phase 4I output contract and keeps parser extraction, scoring, decision posture, recommendations, and dashboard truth deterministic.

## 2. Deterministic Runtime Truth

Runtime truth is produced by:

- loader utilities
- parser utilities
- feature model construction
- scoring engines
- decision engines
- recommendation engines
- deterministic dashboard rendering

These components remain authoritative for the runtime diagnostic result. Memory, governance, recall, and semantic context are downstream or observational layers.

## 3. Governed Memory Layer

The governed memory layer is deterministic, structured, auditable, and reviewable. It persists:

- run history
- recommendation history
- unknown signal history
- action history
- outcome history
- feedback history
- knowledge update requests
- knowledge artifacts

Governed memory is not semantic learning. It records what happened, what humans reviewed, and what governance state exists.

## 4. Structured Recall Layer

Structured recall APIs provide read-only access to governed memory tables. They support bounded filtering, deterministic ordering, and stable JSON-like response shapes.

Structured recall is observational and read-only. It does not influence parser behavior, scoring, recommendations, or runtime decisions.

## 5. Governance Workflow Layer

Governance provides manual, auditable control for candidate knowledge updates. Unknown signal review, feedback, and outcomes can inform candidate requests. Requests may be approved or rejected by humans. Approved requests may be materialized as inactive knowledge artifacts.

Approval does not equal activation. Materialization does not equal runtime use.

## 6. Semantic Recall Layer

Semantic recall is optional, curated, read-only, and non-authoritative. It retrieves contextual memory for analyst assistance and reviewer support.

Semantic recall may help a human understand prior semantic context. It must never determine root cause, severity, posture, recommendation, parser classification, approval status, artifact activation, or dashboard truth.

## 7. Oracle Agent Memory Prototype

Oracle Agent Memory is isolated behind `src/memory/oracle_agent_memory_adapter.py`. It can be enabled through environment variables for prototype semantic recall validation. It is not imported by runtime truth paths.

Oracle Agent Memory in Phase 6 is:

- observational
- optional
- isolated
- curated
- non-authoritative

It does not write to deterministic Phase 6 memory tables.

## 8. Dashboard Visibility Model

The dashboard exposes governed memory, parser review, governance readiness, knowledge artifact visibility, and semantic recall status as read-only visibility.

Semantic recall visibility appears in Screen 6 as system-level memory context. It does not appear as Screen 2 diagnostic truth or Screen 5 recommendation truth.

Dashboard visibility does not equal control-plane authority.

## 9. CLI Operational Layer

The unified CLI entrypoint is:

```bash
PYTHONPATH=. .venv/bin/python scripts/awr_memory_cli.py
```

It provides:

- structured recall commands
- explicit review commands
- explicit governance commands
- explicit artifact commands
- read-only semantic commands
- overall Phase 6 status

Write commands require an actor. Semantic commands are read-only and reviewer-assist only.

## 10. Isolation Boundaries

Phase 6 enforces these boundaries:

- runtime analysis does not import semantic memory modules
- semantic memory does not modify deterministic tables
- governance assist does not make governance decisions
- artifacts are inactive unless a future controlled activation phase uses them
- CLI writes are explicit and actor-attributed
- dashboard visibility does not mutate memory or activate workflows

## 11. Non-Authoritative Semantic Guarantees

Semantic recall responses are explicitly marked with:

```json
{
  "authoritative": false,
  "runtime_influence": false,
  "semantic_only": true
}
```

Governance semantic assist responses also include:

```json
{
  "reviewer_assist_only": true
}
```

Semantic recall is non-authoritative. Runtime truth remains deterministic. Governance remains human-controlled. No autonomous learning exists in Phase 6.

## 12. Runtime Truth Preservation

Phase 6 does not change:

- parser extraction
- scoring formulas
- decision posture
- recommendation generation
- Phase 4I contract
- dashboard diagnostic truth
- provider routing

The deterministic runtime remains the source of truth.

## 13. Future Phase 7 Relationship

Phase 6 prepares governed memory, recall, and semantic context that may support future Phase 7 work. Future work may explore controlled learning, activation, or adaptive workflows only if explicitly designed, approved, validated, and isolated.

Phase 6 does not include adaptive runtime recommendations, automatic parser evolution, semantic runtime influence, self-modifying governance, or automatic artifact activation.

## 14. Explicit Non-Goals

Phase 6 does not implement:

- autonomous learning
- adaptive runtime recommendations
- automatic parser evolution
- semantic runtime influence
- self-modifying governance
- automatic artifact activation
- AI-driven approvals
- semantic override of deterministic evidence
- dashboard write controls
- hidden recommendation changes
