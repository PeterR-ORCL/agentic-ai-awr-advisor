from __future__ import annotations

import ast
import importlib
import os
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
BOUNDARY_DOC = DOCS / "phase7az_screen4_historical_review_workflow_boundary.md"
LIFECYCLE_DOC = DOCS / "phase7az_historical_review_lifecycle.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "screen4_historical_review_boundary.py"

RUNTIME_IMPORT_PATHS = (
    "scripts/run_analysis.py",
    "src/parser",
    "src/parsing",
    "src/scoring",
    "src/decision",
    "src/recommendation",
    "src/recommendations",
    "src/analysis/decision_engine.py",
    "src/analysis/recommendation_engine.py",
    "src/analysis/scoring_adapter.py",
)

FORBIDDEN_BEHAVIOR_FILES = (
    "src/reporting/html_dashboard.py",
    "src/reporting/ai_display_metadata.py",
    "scripts/awr_memory_cli.py",
    "scripts/run_analysis.py",
)

PHASE7BC_ALLOWED_DASHBOARD_PREVIEW_FILE = "src/reporting/html_dashboard.py"
PHASE7BC_REQUIRED_PREVIEW_ARTIFACTS = {
    "src/learning/screen4_historical_learning_bridge.py",
    "tests/test_phase7bc_historical_learning_bridge.py",
    "tests/test_dashboard_screen4_historical_review_panel.py",
    "docs/architecture/phase7bc_historical_learning_bridge.md",
    "docs/architecture/phase7bc_historical_learning_intent_model.md",
    "docs/architecture/phase7bc_screen4_historical_review_panel.md",
}

FORBIDDEN_MODULE_IMPORT_PREFIXES = (
    "oracledb",
    "cx_Oracle",
    "sqlite3",
    "oci",
    "requests",
    "socket",
    "urllib",
    "http.client",
    "httpx",
    "boto3",
    "botocore",
    "src.reporting",
    "src.parser",
    "src.parsing",
    "src.scoring",
    "src.decision",
    "src.recommendation",
    "src.recommendations",
    "src.analysis",
    "src.memory",
    "scripts.awr_memory_cli",
    "scripts.run_analysis",
    "oracle_agent_memory",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def lower_text(path: Path) -> str:
    return read_text(path).lower()


def python_files(paths: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for relative_path in paths:
        path = ROOT / relative_path
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            files.extend(
                sorted(child for child in path.rglob("*.py") if child.is_file())
            )
    return files


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def git_changed_paths(pathspecs: tuple[str, ...] = ()) -> set[str]:
    changed: set[str] = set()
    git_commands = (
        ("git", "diff", "--name-only"),
        ("git", "diff", "--cached", "--name-only"),
        ("git", "ls-files", "--others", "--exclude-standard"),
    )
    for base_command in git_commands:
        command = base_command + (("--",) + pathspecs if pathspecs else ())
        completed = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "git change scan unavailable")
        changed.update(
            line.strip()
            for line in completed.stdout.splitlines()
            if line.strip()
        )
    return changed


def disallowed_behavior_changes_for_phase7bc(
    changed: set[str],
    all_changed: set[str],
) -> set[str]:
    if (
        PHASE7BC_ALLOWED_DASHBOARD_PREVIEW_FILE in changed
        and PHASE7BC_REQUIRED_PREVIEW_ARTIFACTS.issubset(all_changed)
    ):
        return changed - {PHASE7BC_ALLOWED_DASHBOARD_PREVIEW_FILE}
    return changed


class Phase7AZScreen4HistoricalReviewBoundaryTests(unittest.TestCase):
    def test_required_docs_exist(self) -> None:
        self.assertTrue(BOUNDARY_DOC.is_file(), BOUNDARY_DOC)
        self.assertTrue(LIFECYCLE_DOC.is_file(), LIFECYCLE_DOC)

    def test_boundary_doc_contains_required_sections(self) -> None:
        text = read_text(BOUNDARY_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Scope",
            "## 3. Non-Goals",
            "## 4. Why Screen 4 Needs Historical Review Workflow",
            "## 5. Existing Screen 4 Read-Only Boundary",
            "## 6. Historical Review Is Not Historical Truth Mutation",
            "## 7. Baseline Selection Boundary",
            "## 8. Trend Review Boundary",
            "## 9. Anomaly Review Boundary",
            "## 10. Similar Case / Recurrence Boundary",
            "## 11. Missing Historical Evidence Boundary",
            "## 12. Actor Requirement",
            "## 13. Governed Write-Path Requirement",
            "## 14. Audit Requirement",
            "## 15. Output Artifact Lifecycle Requirement",
            "## 16. Trend-Aware Scoring Review Boundary",
            "## 17. Learning Candidate Boundary",
            "## 18. Runtime Truth Boundary",
            "## 19. Phase 4I Contract Boundary",
            "## 20. Future Workflow Target Types",
            "## 21. Future Workflow Actions",
            "## 22. Future Workflow Statuses",
            "## 23. Relationship to 7AD-7AI",
            "## 24. Relationship to Future 7BA",
            "## 25. Relationship to Future 7BB",
            "## 26. Relationship to Future 7BC",
            "## 27. Relationship to Future 7BD",
            "## 28. Relationship to Phase 8",
            "## 29. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, text)

    def test_lifecycle_doc_contains_required_sections(self) -> None:
        text = read_text(LIFECYCLE_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Lifecycle Overview",
            "## 3. Read-Only Historical Review Stage",
            "## 4. Review Target Selection Stage",
            "## 5. Actor Identification Stage",
            "## 6. Historical Review Decision Stage",
            "## 7. Baseline Selection Stage",
            "## 8. Trend / Anomaly Review Stage",
            "## 9. Governance Routing Stage",
            "## 10. Learning Candidate Intent Stage",
            "## 11. Governed Write-Path Stage",
            "## 12. Audit Trail Stage",
            "## 13. Output Artifact Stage",
            "## 14. Closure Stage",
            "## 15. Forbidden Shortcuts",
            "## 16. Required Validation Evidence",
            "## 17. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, text)

    def test_boundary_doc_contains_required_phrases(self) -> None:
        text = lower_text(BOUNDARY_DOC)
        for phrase in (
            "boundary-only",
            "no screen 4 workflow ui is added",
            "no baseline selection records are created",
            "no trend/anomaly review records are created",
            "no learning candidates are created",
            "no backend write path is invoked",
            "no historical truth is changed",
            "no trend/anomaly truth is changed",
            "no scoring behavior is changed",
            "no recommendation truth is changed",
            "no phase 4i mutation is added",
            "future workflow actions require actor identity",
            "future workflow actions require governed write path",
            "future workflow actions require audit trail",
            "phase 8 sizing/tco is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_lifecycle_doc_contains_required_phrases(self) -> None:
        text = lower_text(LIFECYCLE_DOC)
        for phrase in (
            "no lifecycle stage is implemented in 7az",
            "baseline selection is not mutation",
            "trend review is not scoring mutation",
            "anomaly review is not anomaly logic mutation",
            "learning candidate intent is not candidate creation",
            "future workflows cannot skip actor",
            "future workflows cannot skip validation",
            "future workflows cannot skip audit",
            "future workflows cannot bypass governed write path",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_future_workflow_targets_are_documented(self) -> None:
        text = lower_text(BOUNDARY_DOC) + "\n" + lower_text(LIFECYCLE_DOC)
        for target_type in (
            "historical_baseline",
            "comparison_baseline",
            "trend_summary",
            "trend_metric",
            "anomaly_group",
            "anomaly_event",
            "distribution_view",
            "similar_case",
            "recurrence_pattern",
            "historical_confidence",
            "missing_historical_evidence",
            "trend_aware_scoring_reference",
            "learning_candidate_intent",
        ):
            with self.subTest(target_type=target_type):
                self.assertIn(target_type, text)

    def test_future_workflow_actions_are_documented(self) -> None:
        text = lower_text(BOUNDARY_DOC) + "\n" + lower_text(LIFECYCLE_DOC)
        for action in (
            "select_official_baseline",
            "approve_trend",
            "dispute_trend",
            "mark_trend_insufficient",
            "approve_anomaly",
            "mark_anomaly_false_positive",
            "mark_anomaly_insufficient",
            "request_trend_aware_scoring_review",
            "request_anomaly_sensitivity_review",
            "request_scoring_threshold_review",
            "request_learning_candidate",
            "add_historical_review_note",
        ):
            with self.subTest(action=action):
                self.assertIn(action, text)

    def test_future_workflow_statuses_are_documented(self) -> None:
        text = lower_text(BOUNDARY_DOC) + "\n" + lower_text(LIFECYCLE_DOC)
        for status in (
            "proposed",
            "under_review",
            "approved",
            "disputed",
            "insufficient_evidence",
            "false_positive",
            "routed_to_governance",
            "linked_to_candidate",
            "closed",
        ):
            with self.subTest(status=status):
                self.assertIn(status, text)

    def test_optional_module_safety_and_boundary_summary(self) -> None:
        self.assertTrue(MODULE_PATH.is_file(), MODULE_PATH)
        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.screen4_historical_review_boundary")
        self.assertEqual(before_environment, dict(os.environ))

        imports = imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_MODULE_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )

        summary = module.screen4_historical_review_boundary_summary()
        self.assertTrue(summary["boundary_only"])
        self.assertEqual(
            summary["target_types"],
            list(module.SCREEN4_WORKFLOW_TARGET_TYPES),
        )
        self.assertEqual(summary["actions"], list(module.SCREEN4_WORKFLOW_ACTIONS))
        self.assertEqual(summary["statuses"], list(module.SCREEN4_WORKFLOW_STATUSES))
        self.assertEqual(
            summary["required_gates"],
            list(module.SCREEN4_WORKFLOW_REQUIRED_GATES),
        )
        self.assertFalse(summary["workflow_implemented"])
        self.assertFalse(summary["screen4_workflow_ui_added"])
        self.assertFalse(summary["baseline_selection_records_created"])
        self.assertFalse(summary["trend_review_records_created"])
        self.assertFalse(summary["anomaly_review_records_created"])
        self.assertFalse(summary["trend_anomaly_review_records_created"])
        self.assertFalse(summary["learning_candidate_intents_created"])
        self.assertFalse(summary["learning_candidates_created"])
        self.assertFalse(summary["backend_write_path_invoked"])
        self.assertFalse(summary["backend_calls_added"])
        self.assertFalse(summary["run_analysis_wiring_added"])
        self.assertFalse(summary["historical_truth_changed"])
        self.assertFalse(summary["trend_truth_changed"])
        self.assertFalse(summary["anomaly_truth_changed"])
        self.assertFalse(summary["trend_anomaly_truth_changed"])
        self.assertFalse(summary["scoring_behavior_changed"])
        self.assertFalse(summary["trend_aware_scoring_changed"])
        self.assertFalse(summary["confidence_changed"])
        self.assertFalse(summary["recommendation_truth_changed"])
        self.assertFalse(summary["parser_behavior_changed"])
        self.assertFalse(summary["parser_output_changed"])
        self.assertFalse(summary["phase4i_mutation_added"])
        self.assertTrue(summary["deterministic_runtime_authoritative"])
        self.assertEqual(summary["future_baseline_selection_phase"], "7BA")
        self.assertEqual(summary["future_trend_anomaly_review_phase"], "7BB")
        self.assertEqual(summary["future_historical_learning_bridge_phase"], "7BC")
        self.assertEqual(summary["future_validation_certification_phase"], "7BD")
        self.assertFalse(summary["phase8_sizing_tco_implemented"])
        self.assertIn("no Screen 4 historical review workflow is implemented", summary["summary"])

        boundary = module.validate_screen4_historical_review_boundary()
        self.assertIn("historical_baseline", boundary["target_types"])
        self.assertIn("approve_trend", boundary["actions"])
        self.assertIn("proposed", boundary["statuses"])
        self.assertIn("actor identity", boundary["required_gates"])
        self.assertIn("governed write path", boundary["required_gates"])
        self.assertIn("audit trail", boundary["required_gates"])

        with self.assertRaises(module.Screen4HistoricalReviewBoundaryError):
            module.validate_screen4_historical_review_boundary(mode="execution")

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        for module_name in (
            "src.learning.screen4_historical_review_boundary",
            "learning.screen4_historical_review_boundary",
            "screen4_historical_review_boundary",
        ):
            with self.subTest(module_name=module_name):
                self.assertNotIn(module_name, run_analysis_imports)

        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            source = read_text(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.screen4_historical_review_boundary", imports)
                self.assertNotIn("learning.screen4_historical_review_boundary", imports)
                self.assertNotIn("screen4_historical_review_boundary", imports)
                self.assertNotIn("screen4_historical_review_boundary", source)

    def test_behavior_files_are_not_modified_by_phase7az(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git not available")
        if not (ROOT / ".git").exists():
            self.skipTest("not a git checkout")

        try:
            changed = git_changed_paths(FORBIDDEN_BEHAVIOR_FILES)
            all_changed = git_changed_paths()
        except RuntimeError as exc:
            self.skipTest(str(exc))

        changed = disallowed_behavior_changes_for_phase7bc(changed, all_changed)
        self.assertFalse(changed, f"behavior files modified: {sorted(changed)}")

    def test_readme_links_new_docs(self) -> None:
        text = read_text(README)
        for title, filename in (
            (
                "Phase 7AZ Screen 4 Historical Review Workflow Boundary",
                "phase7az_screen4_historical_review_workflow_boundary.md",
            ),
            (
                "Phase 7AZ Historical Review Lifecycle",
                "phase7az_historical_review_lifecycle.md",
            ),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)


if __name__ == "__main__":
    unittest.main()
