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
BOUNDARY_DOC = DOCS / "phase7be_screen5_recommendation_action_workflow_boundary.md"
LIFECYCLE_DOC = DOCS / "phase7be_screen5_action_outcome_lifecycle.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "screen5_action_workflow_boundary.py"

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

SCREEN5_WORKFLOW_ALLOWED_BEHAVIOR_FILE = "src/reporting/html_dashboard.py"
SCREEN5_PREVIEW_ARTIFACT_FILES = {
    "docs/architecture/phase7bg_screen5_action_tracking_panel.md",
    "docs/architecture/phase7bg_action_tracking_preview_model.md",
    "src/learning/screen5_action_tracking.py",
    "tests/test_dashboard_screen5_action_tracking_panel.py",
    "docs/architecture/phase7bh_screen5_outcome_capture_panel.md",
    "docs/architecture/phase7bh_outcome_capture_preview_model.md",
    "src/learning/screen5_outcome_capture.py",
    "tests/test_dashboard_screen5_outcome_capture_panel.py",
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
            files.extend(sorted(child for child in path.rglob("*.py") if child.is_file()))
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


def disallowed_behavior_changes(changed: set[str], all_changed: set[str]) -> set[str]:
    disallowed = set(changed)
    if (
        SCREEN5_WORKFLOW_ALLOWED_BEHAVIOR_FILE in disallowed
        and SCREEN5_PREVIEW_ARTIFACT_FILES.intersection(all_changed)
    ):
        disallowed.remove(SCREEN5_WORKFLOW_ALLOWED_BEHAVIOR_FILE)
    return disallowed


class Phase7BEScreen5RecommendationActionBoundaryTests(unittest.TestCase):
    def test_required_docs_exist(self) -> None:
        self.assertTrue(BOUNDARY_DOC.is_file(), BOUNDARY_DOC)
        self.assertTrue(LIFECYCLE_DOC.is_file(), LIFECYCLE_DOC)

    def test_boundary_doc_contains_required_sections(self) -> None:
        text = read_text(BOUNDARY_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Scope",
            "## 3. Non-Goals",
            "## 4. Why Screen 5 Needs Recommendation / Action / Outcome Workflow",
            "## 5. Existing Screen 5 Recommendation Boundary",
            "## 6. Workflow Is Not Recommendation Mutation",
            "## 7. Recommendation Decision Boundary",
            "## 8. Action Tracking Boundary",
            "## 9. Outcome Capture Boundary",
            "## 10. Feedback Boundary",
            "## 11. Actor Requirement",
            "## 12. Governed Write-Path Requirement",
            "## 13. Audit Requirement",
            "## 14. Phase 4I Recommendation Contract Boundary",
            "## 15. Recommendation Rule Evolution Boundary",
            "## 16. Learning Candidate Boundary",
            "## 17. Future Workflow Target Types",
            "## 18. Future Workflow Actions",
            "## 19. Future Workflow Statuses",
            "## 20. Relationship to 7AD-7AI",
            "## 21. Relationship to Future 7BF",
            "## 22. Relationship to Future 7BG",
            "## 23. Relationship to Future 7BH",
            "## 24. Relationship to Future 7BI",
            "## 25. Relationship to Future 7BJ",
            "## 26. Relationship to Phase 8",
            "## 27. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, text)

    def test_lifecycle_doc_contains_required_sections(self) -> None:
        text = read_text(LIFECYCLE_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Lifecycle Overview",
            "## 3. Read-Only Recommendation Stage",
            "## 4. Recommendation Decision Stage",
            "## 5. Actor Identification Stage",
            "## 6. Action Assignment Stage",
            "## 7. Action Tracking Stage",
            "## 8. Outcome Capture Stage",
            "## 9. Feedback Capture Stage",
            "## 10. Learning Candidate Routing Stage",
            "## 11. Governed Write-Path Stage",
            "## 12. Audit Trail Stage",
            "## 13. Closure Stage",
            "## 14. Forbidden Shortcuts",
            "## 15. Required Validation Evidence",
            "## 16. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, text)

    def test_boundary_doc_contains_required_phrases(self) -> None:
        text = lower_text(BOUNDARY_DOC)
        for phrase in (
            "boundary-only",
            "no screen 5 action ui is added",
            "no recommendation decision records are created",
            "no action records are created",
            "no outcome records are created",
            "no feedback records are created",
            "no backend write path is invoked",
            "no recommendation truth is changed",
            "no recommendation ranking is changed",
            "no recommendation evidence mapping is changed",
            "no recommendation text is changed",
            "no scoring/decision/parser behavior is changed",
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
            "no lifecycle stage is implemented in 7be",
            "recommendation decision is not runtime mutation",
            "action assignment does not change recommendation truth",
            "outcome capture does not immediately change scoring",
            "feedback routing does not automatically create candidates",
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
            "recommendation",
            "recommendation_domain",
            "recommendation_category",
            "recommendation_evidence",
            "recommendation_action",
            "assigned_action",
            "action_status",
            "implementation_date",
            "outcome",
            "feedback",
            "recommendation_effectiveness",
            "recommendation_rule_candidate",
            "learning_candidate_intent",
        ):
            with self.subTest(target_type=target_type):
                self.assertIn(target_type, text)

    def test_future_workflow_actions_are_documented(self) -> None:
        text = lower_text(BOUNDARY_DOC) + "\n" + lower_text(LIFECYCLE_DOC)
        for action in (
            "accept_recommendation",
            "reject_recommendation",
            "defer_recommendation",
            "mark_not_applicable",
            "assign_owner",
            "create_action_item",
            "update_action_status",
            "record_implementation_date",
            "capture_outcome",
            "mark_effective",
            "mark_ineffective",
            "add_feedback",
            "request_recommendation_review",
            "request_learning_candidate",
        ):
            with self.subTest(action=action):
                self.assertIn(action, text)

    def test_future_workflow_statuses_are_documented(self) -> None:
        text = lower_text(BOUNDARY_DOC) + "\n" + lower_text(LIFECYCLE_DOC)
        for status in (
            "proposed",
            "accepted",
            "rejected",
            "deferred",
            "not_applicable",
            "under_review",
            "closed",
            "assigned",
            "in_progress",
            "implemented",
            "blocked",
            "cancelled",
            "pending",
            "improved",
            "worsened",
            "no_change",
            "issue_recurred",
            "inconclusive",
            "reviewed",
            "routed_to_learning",
        ):
            with self.subTest(status=status):
                self.assertIn(status, text)

    def test_optional_module_safety_and_boundary_summary(self) -> None:
        self.assertTrue(MODULE_PATH.is_file(), MODULE_PATH)
        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.screen5_action_workflow_boundary")
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

        summary = module.screen5_action_workflow_boundary_summary()
        self.assertTrue(summary["boundary_only"])
        self.assertEqual(
            summary["target_types"],
            list(module.SCREEN5_WORKFLOW_TARGET_TYPES),
        )
        self.assertEqual(summary["actions"], list(module.SCREEN5_WORKFLOW_ACTIONS))
        self.assertEqual(
            summary["recommendation_decision_statuses"],
            list(module.RECOMMENDATION_DECISION_STATUSES),
        )
        self.assertEqual(summary["action_statuses"], list(module.ACTION_STATUSES))
        self.assertEqual(summary["outcome_statuses"], list(module.OUTCOME_STATUSES))
        self.assertEqual(summary["feedback_statuses"], list(module.FEEDBACK_STATUSES))
        self.assertEqual(
            summary["required_gates"],
            list(module.SCREEN5_WORKFLOW_REQUIRED_GATES),
        )
        self.assertFalse(summary["workflow_implemented"])
        self.assertFalse(summary["screen5_action_ui_added"])
        self.assertFalse(summary["recommendation_decision_records_created"])
        self.assertFalse(summary["action_records_created"])
        self.assertFalse(summary["outcome_records_created"])
        self.assertFalse(summary["feedback_records_created"])
        self.assertFalse(summary["learning_candidate_intents_created"])
        self.assertFalse(summary["learning_candidates_created"])
        self.assertFalse(summary["recommendation_rule_candidates_created"])
        self.assertFalse(summary["backend_write_path_invoked"])
        self.assertFalse(summary["backend_calls_added"])
        self.assertFalse(summary["run_analysis_wiring_added"])
        self.assertFalse(summary["recommendation_truth_changed"])
        self.assertFalse(summary["recommendation_ranking_changed"])
        self.assertFalse(summary["recommendation_evidence_mapping_changed"])
        self.assertFalse(summary["recommendation_text_changed"])
        self.assertFalse(summary["recommendation_action_sequencing_changed"])
        self.assertFalse(summary["score_changed"])
        self.assertFalse(summary["decision_changed"])
        self.assertFalse(summary["parser_behavior_changed"])
        self.assertFalse(summary["phase4i_mutation_added"])
        self.assertTrue(summary["deterministic_runtime_authoritative"])
        self.assertEqual(summary["feedback_to_learning_future_phase"], "7BI")
        self.assertFalse(summary["phase8_sizing_tco_implemented"])
        self.assertIn("no Screen 5 action workflow is implemented", summary["summary"])

        boundary = module.validate_screen5_action_workflow_boundary()
        self.assertIn("recommendation", boundary["target_types"])
        self.assertIn("accept_recommendation", boundary["actions"])
        self.assertIn("proposed", boundary["recommendation_decision_statuses"])
        self.assertIn("actor identity", boundary["required_gates"])
        self.assertIn("governed write path", boundary["required_gates"])
        self.assertIn("audit trail", boundary["required_gates"])

        with self.assertRaises(module.Screen5ActionWorkflowBoundaryError):
            module.validate_screen5_action_workflow_boundary(mode="execution")

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        for module_name in (
            "src.learning.screen5_action_workflow_boundary",
            "learning.screen5_action_workflow_boundary",
            "screen5_action_workflow_boundary",
        ):
            with self.subTest(module_name=module_name):
                self.assertNotIn(module_name, run_analysis_imports)

        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            source = read_text(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.screen5_action_workflow_boundary", imports)
                self.assertNotIn("learning.screen5_action_workflow_boundary", imports)
                self.assertNotIn("screen5_action_workflow_boundary", imports)
                self.assertNotIn("screen5_action_workflow_boundary", source)

    def test_behavior_files_are_not_modified_by_phase7be(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git not available")
        if not (ROOT / ".git").exists():
            self.skipTest("not a git checkout")

        try:
            all_changed = git_changed_paths()
            changed = git_changed_paths(FORBIDDEN_BEHAVIOR_FILES)
        except RuntimeError as exc:
            self.skipTest(str(exc))

        disallowed = disallowed_behavior_changes(changed, all_changed)
        self.assertFalse(disallowed, f"behavior files modified: {sorted(disallowed)}")

    def test_readme_links_new_docs(self) -> None:
        text = read_text(README)
        for title, filename in (
            (
                "Phase 7BE Screen 5 Recommendation Action Workflow Boundary",
                "phase7be_screen5_recommendation_action_workflow_boundary.md",
            ),
            (
                "Phase 7BE Screen 5 Action Outcome Lifecycle",
                "phase7be_screen5_action_outcome_lifecycle.md",
            ),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)


if __name__ == "__main__":
    unittest.main()
