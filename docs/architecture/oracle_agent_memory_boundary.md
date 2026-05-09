# Oracle Agent Memory Boundary

Oracle Agent Memory in Phase 6N.1 is a prototype-only semantic recall layer for curated experimentation.

It is observational, optional, isolated, curated, and non-authoritative.

Deterministic runtime truth remains owned by the parser, feature model, scoring engine, decision engine, recommendation engine, governed Phase 6 memory tables, and dashboard evidence generated from those deterministic sources.

Oracle Agent Memory must never influence deterministic runtime diagnosis, scoring, recommendations, or dashboard truth in Phase 6.

The Phase 6N.1 adapter may connect to Oracle Agent Memory, create or retrieve a DB-scoped semantic thread, write a curated non-authoritative memory summary, and search that semantic memory back for analyst experimentation. It must not mutate parser output, scoring inputs, recommendation logic, governance approval state, deterministic memory tables, or Phase 4I output contracts.

Any future use for phrasing enrichment, analyst assistance, learning bridges, or control-plane workflows must remain explicitly gated by later phases. Approval does not equal activation, and semantic recall does not equal deterministic truth.
