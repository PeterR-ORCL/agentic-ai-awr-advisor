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
