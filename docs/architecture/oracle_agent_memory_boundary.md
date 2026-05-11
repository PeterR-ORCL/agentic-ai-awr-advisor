# Oracle Agent Memory Boundary

Oracle Agent Memory in Phase 6N.1 is a prototype-only semantic recall layer for curated experimentation.

It is observational, optional, isolated, curated, and non-authoritative.

Deterministic runtime truth remains owned by the parser, feature model, scoring engine, decision engine, recommendation engine, governed Phase 6 memory tables, and dashboard evidence generated from those deterministic sources.

Oracle Agent Memory must never influence deterministic runtime diagnosis, scoring, recommendations, or dashboard truth in Phase 6.

The Phase 6N.1 adapter may connect to Oracle Agent Memory, create or retrieve a DB-scoped semantic thread, write a curated non-authoritative memory summary, and search that semantic memory back for analyst experimentation. It must not mutate parser output, scoring inputs, recommendation logic, governance approval state, deterministic memory tables, or Phase 4I output contracts.

Any future use for phrasing enrichment, analyst assistance, learning bridges, or control-plane workflows must remain explicitly gated by later phases. Approval does not equal activation, and semantic recall does not equal deterministic truth.

## Phase 6N.2 Live Semantic Validation

Phase 6N.2 validates the isolated Oracle Agent Memory prototype against a real enabled environment. The purpose is to prove that the adapter can initialize Oracle Agent Memory, create or retrieve a DB-scoped thread, write one curated non-authoritative memory summary, and search it back by database name, issue type, posture, and operational context.

Required or supported environment variables are:

- `ORACLE_AGENT_MEMORY_ENABLED=true`
- `ORACLE_AGENT_MEMORY_COMPARTMENT_ID`
- `ORACLE_AGENT_MEMORY_AGENT_ENDPOINT`
- `ORACLE_AGENT_MEMORY_WALLET_DIR`
- `ORACLE_AGENT_MEMORY_WALLET_PASSWORD`
- `ORACLE_AGENT_MEMORY_USER`
- `ORACLE_AGENT_MEMORY_PASSWORD`
- `ORACLE_AGENT_MEMORY_DSN` or `ADB_DSN`
- `ORACLE_AGENT_MEMORY_THREAD_PREFIX=awr-advisor`

Run validation with:

```bash
PYTHONPATH=. .venv/bin/python scripts/test_oracle_agent_memory.py
```

When enabled and configured, expected output includes:

```json
{
  "enabled": true,
  "success": true,
  "thread_id": "awr-advisor:db:SPRTRN",
  "thread_key": "awr-advisor:db:SPRTRN",
  "write": {
    "success": true,
    "memory_id": "..."
  },
  "searches": [
    {
      "query": "SPRTRN",
      "success": true,
      "count": 1,
      "top_result": {}
    }
  ],
  "isolation": {
    "authoritative": false,
    "runtime_influence": false,
    "deterministic_tables_modified": false
  },
  "isolation_verified": true
}
```

Oracle Agent Memory remains non-authoritative in Phase 6N.2. Its semantic recall output is not consumed by parser extraction, feature engineering, scoring engines, decision engines, recommendation engines, dashboard truth, governed approval state, or deterministic Phase 6 memory persistence.

## Phase 6N.3 Curated Semantic Recall APIs

Phase 6N.3 adds a reusable curated semantic recall service on top of the isolated Oracle Agent Memory adapter. The service is intended for analyst assistance and future phrasing enrichment experiments only. It provides read-only APIs for recall by database name, issue type, posture, and related context, plus a deterministic summary builder that aggregates retrieved semantic memory themes.

The public service module is:

```text
src/memory/semantic_recall_service.py
```

The supported APIs are:

- `recall_by_db_name(db_name, limit=5)`
- `recall_by_issue_type(issue_type, limit=5)`
- `recall_by_posture(posture, limit=5)`
- `recall_related_context(query, limit=5)`
- `build_curated_semantic_summary(query, limit=5)`

All service responses are explicitly marked:

```json
{
  "authoritative": false,
  "runtime_influence": false,
  "semantic_only": true
}
```

The service may rank retrieved semantic records deterministically for display by preferring exact database, posture, or issue matches before preserving Oracle Agent Memory semantic relevance order. This ranking is not scoring, not recommendation generation, and not runtime decision logic.

Curated summaries must use observational language such as "semantic recall suggests," "retrieved memory context indicates," or "historical semantic entries referenced." They must not state root cause, determine severity, generate recommendations, approve governance records, activate artifacts, or override deterministic evidence.

Oracle Agent Memory remains non-authoritative in Phase 6N.3. Semantic recall must not be imported into parser extraction, feature engineering, scoring engines, decision engines, recommendation engines, dashboard truth rendering, governed approval state, or deterministic Phase 6 memory persistence.

## Phase 6N.4 Governance-Assisted Semantic Recall

Phase 6N.4 adds optional semantic assistance for human governance and review workflows. The service can retrieve curated semantic context for unknown signal review, parser governance review, knowledge request review, and artifact review. It is intended to help reviewers see related historical semantic context without making or changing any governance decision.

The public service module is:

```text
src/memory/governance_semantic_assist.py
```

The supported reviewer-assist APIs are:

- `assist_unknown_signal_review(unknown_signal, limit=5)`
- `assist_knowledge_request_review(request, limit=5)`
- `assist_artifact_review(artifact, limit=5)`
- `assist_parser_governance_review(parser_context, limit=5)`

All governance-assist responses are explicitly marked:

```json
{
  "authoritative": false,
  "runtime_influence": false,
  "semantic_only": true,
  "reviewer_assist_only": true
}
```

Governance semantic assistance is non-authoritative reviewer context only. It must never determine governance outcomes, approval status, parser classification, runtime diagnosis, scoring, recommendations, or dashboard truth.

Reviewer-assist observations must use language such as "semantic recall suggests," "prior semantic entries referenced," "retrieved governance context indicates," or "historical reviewer context included." They must never approve, reject, classify, materialize, recommend, or instruct parser behavior.

Human reviewers remain authoritative. Phase 6N.4 does not add autonomous governance decisions, automatic parser classification, automatic approval, automatic artifact materialization, learning loops, or runtime truth influence.
