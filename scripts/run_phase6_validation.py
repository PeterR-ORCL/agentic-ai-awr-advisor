#!/usr/bin/env python3
"""Run the Phase 6 validation suite and emit summary JSON."""

from __future__ import annotations

import json
import sys
import unittest

TEST_MODULES = [
    "tests.test_phase6_validation",
    "tests.test_awr_memory_cli",
    "tests.test_governance_semantic_assist",
    "tests.test_semantic_recall_service",
    "tests.test_oracle_agent_memory",
    "tests.test_memory_recall",
]

CATEGORIES = {
    "runtime_isolation": True,
    "semantic_isolation": True,
    "governance_safety": True,
    "dashboard_truth_preservation": True,
    "cli_operational_safety": True,
    "memory_persistence_integrity": True,
    "recall_correctness": True,
    "semantic_non_authoritativeness": True,
    "import_isolation": True,
    "write_discipline": True,
}


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromNames(TEST_MODULES)
    runner = unittest.TextTestRunner(stream=sys.stderr, verbosity=1)
    result = runner.run(suite)
    success = result.wasSuccessful()
    summary = {
        "phase": "6P",
        "success": success,
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "categories": {key: success and value for key, value in CATEGORIES.items()},
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
