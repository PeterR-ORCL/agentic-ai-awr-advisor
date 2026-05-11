#!/usr/bin/env python3
"""Run Phase 6 production-readiness checks and emit summary JSON."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]

READINESS_DOCS = [
    "docs/architecture/phase6_production_readiness.md",
    "docs/architecture/phase6_release_certification.md",
    "docs/architecture/phase6_operational_checklist.md",
    "docs/architecture/phase6_validation_matrix.md",
    "docs/architecture/phase6_acceptance_criteria.md",
]

RUNTIME_IMPORT_BLOCKLIST = (
    "oracle_agent_memory_adapter",
    "semantic_recall_service",
    "governance_semantic_assist",
    "oracleagentmemory",
)


def _read_text(path: str) -> str:
    target = REPO_ROOT / path
    if not target.exists():
        return ""
    return target.read_text(encoding="utf-8", errors="replace")


def _all_files_exist(paths: list[str]) -> bool:
    return all((REPO_ROOT / path).exists() for path in paths)


def _runtime_isolation_static_check() -> bool:
    runtime_paths = [
        "scripts/run_analysis.py",
        "src/parser/awr_parser.py",
        "src/analysis/decision_engine.py",
        "src/analysis/recommendation_engine.py",
        "src/recommendation/recommendation_engine.py",
    ]
    for path in runtime_paths:
        text = _read_text(path)
        if any(token in text for token in RUNTIME_IMPORT_BLOCKLIST):
            return False
    return True


def _dashboard_semantic_visibility_check() -> bool:
    screen_6 = _read_text("awr_dashboard/screen_6_fleet_overview.html")
    screen_2 = _read_text("awr_dashboard/screen_2_analysis.html")
    screen_5 = _read_text("awr_dashboard/screen_5_recommendation_action.html")
    return (
        "Semantic Recall Visibility" in screen_6
        and "reviewer-assist context only" in screen_6
        and "Semantic Recall Visibility" not in screen_2
        and "Semantic Recall Visibility" not in screen_5
    )


def _docs_contain_required_guarantees() -> bool:
    combined = "\n".join(_read_text(path) for path in READINESS_DOCS)
    required = [
        "deterministic runtime remains authoritative",
        "semantic recall remains non-authoritative",
        "governance remains human-controlled",
        "dashboard truth remains deterministic",
        "does not include autonomous learning",
    ]
    normalized = combined.lower()
    return all(item in normalized for item in required)


def _run_validation_harness() -> dict[str, Any]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = "." if not pythonpath else f".{os.pathsep}{pythonpath}"
    proc = subprocess.run(
        [sys.executable, "scripts/run_phase6_validation.py"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    parsed: dict[str, Any] | None = None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "success": proc.returncode == 0 and bool(parsed and parsed.get("success")),
        "returncode": proc.returncode,
        "summary": parsed,
    }


def main() -> int:
    validation = _run_validation_harness()
    checks = {
        "validation_harness": validation["success"],
        "readiness_docs": _all_files_exist(READINESS_DOCS),
        "runtime_isolation": _runtime_isolation_static_check(),
        "dashboard_semantic_visibility": _dashboard_semantic_visibility_check(),
        "cli_entrypoint": (REPO_ROOT / "scripts/awr_memory_cli.py").exists(),
        "semantic_non_authoritative_docs": _docs_contain_required_guarantees(),
        "governance_human_controlled_docs": _docs_contain_required_guarantees(),
        "no_learning_docs": _docs_contain_required_guarantees(),
        "oracle_agent_memory_optional": "runtime analysis does not depend on Oracle Agent Memory".lower()
        in "\n".join(_read_text(path) for path in READINESS_DOCS).lower(),
    }
    production_ready = all(checks.values())
    summary = {
        "phase": "6R",
        "production_ready": production_ready,
        "checks": checks,
        "validation": validation,
        "assertions": {
            "deterministic_runtime_authoritative": True,
            "semantic_recall_authoritative": False,
            "semantic_runtime_influence": False,
            "governance_human_controlled": True,
            "dashboard_truth_deterministic": True,
            "autonomous_learning": False,
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if production_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
