# Architecture Documentation

This directory contains architecture, governance, validation, and operational documentation for the Agentic AI AWR Advisor project.

## Phase 6 Core Documents

- [Phase 6 Memory Architecture](phase6_memory_architecture.md)
- [Phase 6 Operational Model](phase6_operational_model.md)
- [Phase 6 Acceptance Criteria](phase6_acceptance_criteria.md)
- [Phase 6 Validation Matrix](phase6_validation_matrix.md)
- [Phase 6 CLI Operations](phase6_cli_operations.md)
- [Phase 6 Production Readiness](phase6_production_readiness.md)
- [Phase 6 Release Certification](phase6_release_certification.md)
- [Phase 6 Operational Checklist](phase6_operational_checklist.md)

## Semantic Memory and Governance

- [Oracle Agent Memory Boundary](oracle_agent_memory_boundary.md)

These documents define the non-authoritative semantic recall boundary, reviewer-assist model, and Oracle Agent Memory isolation rules.

## Repository Governance

- [Repository Structure and Naming Policy](repository_structure_and_naming.md)

This document defines architectural naming semantics, generated artifact policy, data pack policy, schema organization, adapter naming, and rename/refactor guardrails.

## Phase Boundary Summary

Phase 6 is governed, deterministic, explicit, and validated.

- Deterministic runtime remains authoritative.
- Semantic recall remains non-authoritative.
- Governance remains human-controlled.
- Dashboard truth remains deterministic.
- No autonomous learning behavior exists in Phase 6.
- Future adaptive or activation behavior belongs to later phases only.
