# Phase 7R Controlled Learning Materialization Readiness

## Purpose

This document defines readiness for Phase 7M through Phase 7R controlled learning materialization. Readiness means the materialization block is validated, documented, operationally checkable, and certified as proposal-only and inactive.

`materialization_ready=true only when all checks pass`.

## Readiness Scope

The readiness scope is validation and certification for the 7M-7Q controlled materialization block. It includes local validation scripts, documentation, operational checklist coverage, import isolation, runtime safety checks, and regression checks.

It does not introduce runtime activation, parser changes, scoring changes, recommendation changes, dashboard changes, CLI changes, DB writes, OCI calls, Oracle Agent Memory dependency, semantic recall service dependency, ML, learned_model(x), or Phase 8 sizing/TCO behavior.

## Completed Materialization Subphases

Phase 7M defines the learning materialization boundary. Phase 7N defines approved candidate materialization artifacts. Phase 7O defines adaptive scoring review proposals and inactive proposed scoring configs. Phase 7P defines recommendation rule evolution proposals and inactive proposed recommendation rules. Phase 7Q defines parser mapping evolution proposals and inactive parser backlog items.

7M-7Q are proposal-only / inactive.

## Readiness Categories

The readiness checker reports `materialization_boundary`, `approved_candidate_materialization`, `adaptive_scoring_review`, `recommendation_rule_evolution`, `parser_mapping_evolution`, `runtime_isolation`, `documentation_complete`, `phase7_regression`, and `phase6_regression`.

The `phase6_regression` category is `null` unless Phase 6 validation is explicitly included.

## Boundary Readiness

Boundary readiness confirms that candidate approval does not equal runtime activation, materialization is separate from approval, materialization is not activation, and `runtime_influence_granted=false` remains enforced across the controlled materialization block.

## Artifact Readiness

Artifact readiness confirms that approved candidates can become local controlled materialization artifacts only. These artifacts are implementation work items and validation envelopes; they are not active runtime configuration.

## Scoring Review Readiness

Scoring review readiness confirms that adaptive scoring review records are proposal-only and that proposed scoring configs are inactive. `runtime_active=false`, `runtime_influence_granted=false`, and no runtime scoring changes are applied.

## Recommendation Evolution Readiness

Recommendation evolution readiness confirms that recommendation rule evolution records are proposal-only and proposed recommendation rules are inactive. `runtime_active=false`, `runtime_influence_granted=false`, and no runtime recommendation changes are applied.

## Parser Evolution Readiness

Parser evolution readiness confirms that parser evolution is first-class and protected. Parser backlog items are inactive, `runtime_active=false`, `runtime_influence_granted=false`, and no runtime parser changes are applied.

## Runtime Isolation Readiness

Runtime isolation readiness confirms that `scripts/run_analysis.py`, parser runtime paths, scoring runtime paths, decision runtime paths, and recommendation runtime paths do not import materialization/evolution modules.

Parser/scoring/recommendation runtime paths remain authoritative.

## Documentation Readiness

Documentation readiness confirms that the validation matrix, readiness document, release certification, operational checklist, and architecture README links are present and contain the required boundary language.

## Operational Readiness

Operational readiness confirms that operators have local commands for validation and readiness checks, including JSON output for CI consumption.

Use `.venv/bin/python` if system Python lacks project dependencies such as dotenv.

## Required Commands

The required commands are:

- `python3 scripts/run_phase7_materialization_validation.py`
- `python3 scripts/run_phase7_materialization_validation.py --json`
- `python3 scripts/run_phase7_materialization_readiness_check.py`
- `python3 scripts/run_phase7_materialization_readiness_check.py --json`
- `python3 scripts/run_phase7_validation.py`
- `python3 scripts/run_phase7_readiness_check.py`
- `python3 scripts/run_phase7h_dashboard_validation.py`
- `.venv/bin/python scripts/awr_memory_cli.py learning validate --json`
- `PYTHONPATH=. .venv/bin/python scripts/run_phase6_validation.py`

## Readiness Criteria

Readiness requires all required materialization validation groups to pass, Phase 7 regression to pass, documentation to be complete, runtime isolation to pass, `runtime_influence_granted=false`, `runtime_active=false`, no runtime changes are applied, and deterministic runtime remains authoritative.

## Materialization Ready Statement

Phase 7R reports `materialization_ready=true` only when all checks pass. The readiness statement certifies the controlled materialization block as proposal-only and inactive; parser/scoring/recommendation runtime paths remain authoritative and no runtime changes are applied.
