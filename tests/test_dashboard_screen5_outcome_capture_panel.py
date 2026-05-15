from __future__ import annotations

import ast
import importlib
import os
import py_compile
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
HTML_DASHBOARD_PATH = ROOT / "src" / "reporting" / "html_dashboard.py"
MODULE_PATH = ROOT / "src" / "learning" / "screen5_outcome_capture.py"
PANEL_DOC = DOCS / "phase7bh_screen5_outcome_capture_panel.md"
MODEL_DOC = DOCS / "phase7bh_outcome_capture_preview_model.md"

FORBIDDEN_IMPORT_PREFIXES = (
    "subprocess",
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

FORBIDDEN_MODEL_FUNCTION_NAMES = (
    "persist_outcome_record",
    "update_action_record",
    "create_feedback_record",
    "create_learning_label",
    "create_learning_candidate",
    "invoke_governed_write_path",
    "call_backend",
    "auto_apply",
    "autonomous_apply",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def lower_text(path: Path) -> str:
    return read_text(path).lower()


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def function_names(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


def dashboard_module():
    return importlib.import_module("src.reporting.html_dashboard")


class DashboardScreen5OutcomeCapturePanelTests(unittest.TestCase):
    @staticmethod
    def model_module():
        return importlib.import_module("src.learning.screen5_outcome_capture")

    def render_screen5(self) -> str:
        return dashboard_module()._render_screen_5_page(
            self.sample_screen5_model(),
            ai_sections={},
            agentic_decision={},
            report_data={"run_history_id": "RUN-1"},
        )

    @staticmethod
    def sample_screen5_model() -> dict[str, object]:
        return {
            "header": {
                "decision_posture": "TUNE FIRST",
                "display_severity_label": "High",
                "confidence": 0.82,
                "primary_issue": "CPU",
            },
            "normalized_decision": {
                "primary_issue": "CPU",
                "overall_status": "WARNING",
                "display_severity_label": "High",
                "confidence": 0.82,
            },
            "canonical_recommendation_count": 1,
            "recommendation_list": [
                {
                    "recommendation_id": "RECO-CPU-001",
                    "action_id": "ACTION-CPU-001",
                    "issue": "CPU",
                    "action": "Tune top SQL before scaling",
                    "priority": "HIGH",
                    "category": "tuning",
                    "rationale": "CPU evidence supports SQL tuning first.",
                }
            ],
            "posture_guidance": [
                "Validate top SQL elapsed time before scaling.",
            ],
        }

    def make_preview(self, **overrides):
        module = self.model_module()
        values = {
            "outcome_preview_id": module.build_outcome_preview_id(
                "RECO-CPU-001",
                "ACTION-CPU-001",
            ),
            "recommendation_id": "RECO-CPU-001",
            "linked_action_id": "ACTION-CPU-001",
            "outcome_status": "pending",
            "outcome_effectiveness": "unknown",
            "issue_recurred": None,
            "followup_awr": "not linked",
            "followup_run": "not linked",
            "implementation_date": "not set",
            "outcome_notes": "not captured",
            "actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-JANE-REVIEWER"},
        }
        values.update(overrides)
        return module.OutcomeCapturePreview(**values)

    def test_dashboard_source_compiles(self) -> None:
        py_compile.compile(str(HTML_DASHBOARD_PATH), doraise=True)

    def test_outcome_capture_panel_exists(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen5()
        for phrase in (
            "Screen 5 Outcome Capture Preview",
            "Capture Outcome",
            "Mark Improved",
            "Mark Worsened",
            "Mark No Change",
            "Mark Issue Recurred",
            "Mark Inconclusive",
            "Link Follow-up AWR / Run",
            "View Feedback / Learning Next Step",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)
                self.assertIn(phrase, rendered)

    def test_controls_are_disabled_preview_only(self) -> None:
        source = read_text(HTML_DASHBOARD_PATH)
        rendered = self.render_screen5()
        for phrase in (
            "aria-disabled",
            "preview-only",
            "Outcome capture disabled in this phase",
            "Preview only",
            "Outcome capture is not execution",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)
                self.assertIn(phrase, rendered)

    def test_safety_labels_exist(self) -> None:
        rendered = self.render_screen5()
        for phrase in (
            "No backend write",
            "No governed write path invoked",
            "No outcome record persisted",
            "No feedback created",
            "No learning label created",
            "No candidate created automatically",
            "Does not change recommendation truth",
            "Does not change scoring",
            "Does not mutate Phase 4I",
            "Deterministic runtime remains authoritative",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_no_unsafe_backend_calls(self) -> None:
        source = lower_text(HTML_DASHBOARD_PATH)
        for phrase in (
            "fetch(",
            "xmlhttprequest",
            "method=\"post\"",
            "action=\"/",
            "create_outcome",
            "capture_outcome",
            "create_feedback",
            "create_label",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, source)

    def test_preview_fields_exist(self) -> None:
        rendered = self.render_screen5()
        for phrase in (
            "recommendation_id",
            "linked_action_id",
            "outcome_status",
            "outcome_effectiveness",
            "issue_recurred",
            "followup_awr",
            "followup_run",
            "write_performed=false",
            "outcome_created=false",
            "feedback_created=false",
            "label_created=false",
            "candidate_created=false",
            "scoring_mutation_requested=false",
            "phase4i_mutation_requested=false",
            "runtime_influence=false",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, rendered)

    def test_docs_exist_and_contain_required_phrases(self) -> None:
        self.assertTrue(PANEL_DOC.is_file(), PANEL_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)
        text = lower_text(PANEL_DOC) + "\n" + lower_text(MODEL_DOC)
        for phrase in (
            "no outcome capture is performed",
            "no outcome record is persisted",
            "no feedback is created",
            "no learning label is created",
            "no candidate is created automatically",
            "no scoring is changed",
            "no recommendation truth is changed",
            "all controls are disabled/preview-only",
            "phase 8 sizing/tco is not implemented",
            "write_performed=false",
            "outcome_created=false",
            "feedback_created=false",
            "label_created=false",
            "candidate_created=false",
            "scoring_mutation_requested=false",
            "runtime_influence=false",
            "phase4i_mutation_requested=false",
            "no backend write occurs",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_optional_model_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = self.model_module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "OutcomeCapturePreview"))
        self.assertTrue(hasattr(module, "OutcomeCaptureValidation"))

        imports = imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )

    def test_optional_model_validation_and_serialization(self) -> None:
        module = self.model_module()
        preview = self.make_preview()
        self.assertIs(module.validate_outcome_capture_preview(preview), preview)
        validation = module.evaluate_outcome_capture_preview(preview)
        self.assertTrue(validation.valid)
        self.assertFalse(validation.write_performed)
        self.assertFalse(validation.outcome_created)
        self.assertFalse(validation.feedback_created)
        self.assertFalse(validation.label_created)
        self.assertFalse(validation.candidate_created)

        for overrides in (
            {"outcome_status": "runtime_applied"},
            {"outcome_effectiveness": "auto_learned"},
            {"write_performed": True},
            {"outcome_created": True},
            {"feedback_created": True},
            {"label_created": True},
            {"candidate_created": True},
            {"scoring_mutation_requested": True},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen5OutcomeCaptureError):
                    self.make_preview(**overrides)

        serialized_preview = module.outcome_capture_preview_to_dict(preview)
        serialized_validation = module.outcome_capture_validation_to_dict(validation)
        self.assertEqual(
            serialized_preview,
            module.outcome_capture_preview_to_dict(
                module.outcome_capture_preview_from_dict(serialized_preview)
            ),
        )
        self.assertEqual(
            serialized_validation,
            module.outcome_capture_validation_to_dict(
                module.outcome_capture_validation_from_dict(serialized_validation)
            ),
        )

    def test_supported_statuses_effectiveness_and_deterministic_ids(self) -> None:
        module = self.model_module()
        self.assertEqual(
            module.OUTCOME_CAPTURE_STATUSES,
            (
                "pending",
                "improved",
                "worsened",
                "no_change",
                "issue_recurred",
                "inconclusive",
                "closed",
            ),
        )
        self.assertEqual(
            module.OUTCOME_EFFECTIVENESS_VALUES,
            (
                "effective",
                "ineffective",
                "partially_effective",
                "not_applicable",
                "unknown",
            ),
        )
        first = module.build_outcome_preview_id("RECO-CPU-001", "ACTION-CPU-001")
        second = module.build_outcome_preview_id("RECO-CPU-001", "ACTION-CPU-001")
        self.assertEqual(first, second)
        self.assertFalse(
            re.search(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                first.lower(),
            )
        )

    def test_optional_model_no_persistence_or_mutation_functions(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_MODEL_FUNCTION_NAMES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, names)


if __name__ == "__main__":
    unittest.main()
