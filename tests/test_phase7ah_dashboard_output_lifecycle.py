"""Phase 7AH tests for dashboard output lifecycle metadata."""

from __future__ import annotations

import ast
import importlib
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "learning" / "dashboard_output_lifecycle.py"
RUN_ANALYSIS_PATH = ROOT / "scripts" / "run_analysis.py"
DOCS = ROOT / "docs" / "architecture"
ARCHITECTURE_DOC = DOCS / "phase7ah_dashboard_output_lifecycle.md"
MODEL_DOC = DOCS / "phase7ah_output_artifact_model.md"

FORBIDDEN_IMPORT_PREFIXES = (
    "subprocess",
    "requests",
    "httpx",
    "urllib",
    "socket",
    "http.client",
    "oci",
    "oracledb",
    "cx_Oracle",
    "sqlite3",
    "src.reporting",
    "src.parser",
    "src.parsers",
    "src.scoring",
    "src.decision",
    "src.recommendation",
    "src.recommendations",
    "scripts.run_analysis",
    "scripts.awr_memory_cli",
)

FORBIDDEN_FUNCTION_TERMS = (
    "write_artifact",
    "regenerate_dashboard",
    "mutate_phase4i",
    "execute_refresh",
    "call_backend",
    "run_analysis",
    "subprocess",
    "auto_apply",
    "autonomous_apply",
)

RUNTIME_ISOLATION_PATHS = (
    ROOT / "src" / "parser",
    ROOT / "src" / "scoring",
    ROOT / "src" / "decision",
    ROOT / "src" / "recommendation",
)


class Phase7AHDashboardOutputLifecycleTests(unittest.TestCase):
    """Validate the 7AH output lifecycle remains metadata-only."""

    @staticmethod
    def _module():
        return importlib.import_module("src.learning.dashboard_output_lifecycle")

    @staticmethod
    def _read(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _lower(path: Path) -> str:
        return Phase7AHDashboardOutputLifecycleTests._read(path).lower()

    @staticmethod
    def _imported_modules(path: Path) -> set[str]:
        tree = ast.parse(Phase7AHDashboardOutputLifecycleTests._read(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        return imports

    @staticmethod
    def _function_names(path: Path) -> set[str]:
        tree = ast.parse(Phase7AHDashboardOutputLifecycleTests._read(path))
        return {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

    @staticmethod
    def _python_files(path: Path) -> list[Path]:
        if not path.exists():
            return []
        if path.is_file() and path.suffix == ".py":
            return [path]
        return list(path.rglob("*.py"))

    def _make_artifact(self, **overrides: object):
        module = self._module()
        values: dict[str, object] = {
            "artifact_id": module.create_output_artifact_id(
                "validation_response",
                source_request_id="REQ-1",
            ),
            "artifact_type": "validation_response",
            "source_request_id": "REQ-1",
            "source_validation_id": "VAL-1",
            "source_audit_id": "AUD-1",
            "run_id": None,
            "phase4i_reference": None,
            "dashboard_reference": None,
            "comparison_reference": None,
            "artifact_uri": None,
            "artifact_summary": "Validation response metadata",
            "lifecycle_status": "VALIDATED",
            "validation_status": "VALID",
            "error_summary": None,
            "created_by": "ACTOR-LOCAL-JANE-REVIEWER",
            "created_at": None,
            "output_written": False,
            "dashboard_regenerated": False,
            "phase4i_mutated": False,
            "runtime_mutation_performed": False,
            "notes": "unit-test artifact",
        }
        values.update(overrides)
        return module.DashboardOutputArtifact(**values)

    def _make_refresh_instruction(self, **overrides: object):
        module = self._module()
        values: dict[str, object] = {
            "refresh_id": module.create_output_refresh_id(
                "DASHBOARD-OUTPUT-VALIDATION-RESPONSE-REQ-1",
                "show_message",
            ),
            "artifact_id": "DASHBOARD-OUTPUT-VALIDATION-RESPONSE-REQ-1",
            "refresh_mode": "show_message",
            "message": "Validation response metadata",
            "link_target": None,
            "run_id": None,
            "dashboard_reference": None,
            "safe_to_display": True,
            "requires_manual_action": False,
            "refresh_performed": False,
            "notes": "unit-test refresh",
        }
        values.update(overrides)
        return module.DashboardOutputRefreshInstruction(**values)

    def test_module_import_safety(self):
        module = self._module()
        self.assertTrue(hasattr(module, "DashboardOutputArtifact"))

        imports = self._imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            self.assertFalse(
                any(
                    imported == forbidden or imported.startswith(f"{forbidden}.")
                    for imported in imports
                ),
                f"Forbidden import found in 7AH module: {forbidden}",
            )

    def test_docs_exist(self):
        self.assertTrue(ARCHITECTURE_DOC.exists())
        self.assertTrue(MODEL_DOC.exists())

    def test_docs_contain_required_boundary_phrases(self):
        combined = f"{self._lower(ARCHITECTURE_DOC)}\n{self._lower(MODEL_DOC)}"
        required_phrases = (
            "does not write artifacts",
            "does not regenerate dashboards",
            "does not mutate phase 4i",
            "does not execute refresh",
            "output records are metadata only",
            "refresh instructions are metadata only",
            "deterministic runtime remains authoritative",
        )
        for phrase in required_phrases:
            self.assertIn(phrase, combined)

    def test_supported_artifact_types(self):
        module = self._module()
        expected_types = {
            "validation_response",
            "analysis_run_record",
            "phase4i_payload_reference",
            "dashboard_artifact_reference",
            "comparison_artifact",
            "error_artifact",
            "source_validation_artifact",
            "object_storage_load_artifact",
            "workflow_audit_artifact",
            "governance_review_artifact",
            "outcome_capture_artifact",
        }
        self.assertEqual(expected_types, set(module.OUTPUT_ARTIFACT_TYPES))

        required_fields: dict[str, dict[str, object]] = {
            "analysis_run_record": {"run_id": "RUN-1"},
            "phase4i_payload_reference": {"phase4i_reference": "phase4i.json"},
            "dashboard_artifact_reference": {
                "dashboard_reference": "dashboard.html",
            },
            "comparison_artifact": {"comparison_reference": "comparison.json"},
            "error_artifact": {"error_summary": "failure metadata"},
        }
        for artifact_type in expected_types:
            source_request_id = f"REQ-{artifact_type}"
            artifact = self._make_artifact(
                artifact_id=module.create_output_artifact_id(
                    artifact_type,
                    source_request_id=source_request_id,
                ),
                artifact_type=artifact_type,
                source_request_id=source_request_id,
                artifact_summary=f"{artifact_type} metadata",
                **required_fields.get(artifact_type, {}),
            )
            self.assertEqual(artifact_type, artifact.artifact_type)

        with self.assertRaises(module.DashboardOutputLifecycleError):
            self._make_artifact(artifact_type="written_dashboard_file")

    def test_supported_refresh_modes(self):
        module = self._module()
        expected_modes = {
            "no_refresh",
            "show_message",
            "link_to_artifact",
            "link_to_run",
            "regenerate_dashboard_requested",
            "future_live_refresh",
        }
        self.assertEqual(expected_modes, set(module.OUTPUT_REFRESH_MODES))

        for refresh_mode in expected_modes:
            overrides: dict[str, object] = {
                "refresh_id": module.create_output_refresh_id("ART-1", refresh_mode),
                "artifact_id": "ART-1",
                "refresh_mode": refresh_mode,
                "requires_manual_action": refresh_mode
                not in ("no_refresh", "show_message"),
            }
            if refresh_mode == "link_to_run":
                overrides["run_id"] = "RUN-1"
            if refresh_mode == "link_to_artifact":
                overrides["link_target"] = "artifact.json"
            instruction = self._make_refresh_instruction(**overrides)
            self.assertEqual(refresh_mode, instruction.refresh_mode)

        with self.assertRaises(module.DashboardOutputLifecycleError):
            self._make_refresh_instruction(refresh_mode="live_auto_refresh")

    def test_output_artifact_validation_rules(self):
        module = self._module()
        artifact = module.create_validation_response_artifact(
            "REQ-VALID",
            "Validation succeeded",
            "VALID",
            created_by="ACTOR-LOCAL-JANE-REVIEWER",
        )
        self.assertIs(module.validate_dashboard_output_artifact(artifact), artifact)

        with self.assertRaises(module.DashboardOutputLifecycleError):
            self._make_artifact(
                artifact_type="error_artifact",
                artifact_summary="error metadata",
                lifecycle_status="FAILED",
                error_summary=None,
            )
        with self.assertRaises(module.DashboardOutputLifecycleError):
            self._make_artifact(
                artifact_type="phase4i_payload_reference",
                artifact_summary="Phase 4I metadata",
                phase4i_reference=None,
            )
        with self.assertRaises(module.DashboardOutputLifecycleError):
            self._make_artifact(
                artifact_type="dashboard_artifact_reference",
                artifact_summary="Dashboard metadata",
                dashboard_reference=None,
            )
        with self.assertRaises(module.DashboardOutputLifecycleError):
            self._make_artifact(
                artifact_type="comparison_artifact",
                artifact_summary="Comparison metadata",
                comparison_reference=None,
            )
        with self.assertRaises(module.DashboardOutputLifecycleError):
            self._make_artifact(
                artifact_type="analysis_run_record",
                artifact_summary="Run metadata",
                run_id=None,
            )

    def test_safety_flags_must_remain_false(self):
        module = self._module()
        for field_name in (
            "output_written",
            "dashboard_regenerated",
            "phase4i_mutated",
            "runtime_mutation_performed",
        ):
            with self.assertRaises(module.DashboardOutputLifecycleError):
                self._make_artifact(**{field_name: True})

    def test_refresh_instruction_validation_rules(self):
        module = self._module()
        show_message = self._make_refresh_instruction()
        self.assertIs(
            module.validate_dashboard_output_refresh_instruction(show_message),
            show_message,
        )

        with self.assertRaises(module.DashboardOutputLifecycleError):
            self._make_refresh_instruction(
                refresh_id=module.create_output_refresh_id("ART-1", "link_to_run"),
                refresh_mode="link_to_run",
                run_id=None,
                requires_manual_action=True,
            )

        link_instruction = self._make_refresh_instruction(
            refresh_id=module.create_output_refresh_id("ART-1", "link_to_artifact"),
            artifact_id="ART-1",
            refresh_mode="link_to_artifact",
            link_target=None,
            requires_manual_action=True,
        )
        self.assertFalse(link_instruction.refresh_performed)

        future_instruction = self._make_refresh_instruction(
            refresh_id=module.create_output_refresh_id("ART-1", "future_live_refresh"),
            artifact_id="ART-1",
            refresh_mode="future_live_refresh",
            requires_manual_action=True,
        )
        self.assertTrue(future_instruction.requires_manual_action)
        self.assertFalse(future_instruction.refresh_performed)

        with self.assertRaises(module.DashboardOutputLifecycleError):
            self._make_refresh_instruction(
                refresh_id=module.create_output_refresh_id("ART-1", "future_live_refresh"),
                refresh_mode="future_live_refresh",
                requires_manual_action=False,
            )
        with self.assertRaises(module.DashboardOutputLifecycleError):
            self._make_refresh_instruction(refresh_performed=True)

    def test_helper_constructors(self):
        module = self._module()
        validation_artifact = module.create_validation_response_artifact(
            "REQ-1",
            "Validation response ready",
            "VALID",
            created_by="ACTOR-LOCAL-JANE-REVIEWER",
        )
        error_artifact = module.create_error_artifact(
            "REQ-2",
            "Validation failed",
            created_by="ACTOR-LOCAL-JANE-REVIEWER",
        )
        refresh = module.create_refresh_instruction_for_artifact(validation_artifact)

        for artifact in (validation_artifact, error_artifact):
            self.assertFalse(artifact.output_written)
            self.assertFalse(artifact.dashboard_regenerated)
            self.assertFalse(artifact.phase4i_mutated)
            self.assertFalse(artifact.runtime_mutation_performed)
        self.assertEqual("show_message", refresh.refresh_mode)
        self.assertFalse(refresh.requires_manual_action)
        self.assertFalse(refresh.refresh_performed)

    def test_serialization_round_trips(self):
        module = self._module()
        artifact = self._make_artifact()
        artifact_round_trip = module.dashboard_output_artifact_from_dict(
            module.dashboard_output_artifact_to_dict(artifact)
        )
        self.assertEqual(artifact, artifact_round_trip)

        instruction = self._make_refresh_instruction()
        instruction_round_trip = module.dashboard_output_refresh_instruction_from_dict(
            module.dashboard_output_refresh_instruction_to_dict(instruction)
        )
        self.assertEqual(instruction, instruction_round_trip)

    def test_deterministic_ids(self):
        module = self._module()
        first_artifact_id = module.create_output_artifact_id(
            "validation_response",
            source_request_id=" Request 1 ",
        )
        second_artifact_id = module.create_output_artifact_id(
            "validation_response",
            source_request_id="Request 1",
        )
        self.assertEqual(first_artifact_id, second_artifact_id)
        self.assertEqual(
            "DASHBOARD-OUTPUT-VALIDATION-RESPONSE-REQUEST-1",
            first_artifact_id,
        )

        run_artifact_id = module.create_output_artifact_id(
            "analysis_run_record",
            run_id=" Run 1 ",
        )
        self.assertEqual(
            "DASHBOARD-OUTPUT-ANALYSIS-RUN-RECORD-RUN-1",
            run_artifact_id,
        )
        refresh_id = module.create_output_refresh_id(
            first_artifact_id,
            "show_message",
        )
        self.assertEqual(
            "DASHBOARD-REFRESH-DASHBOARD-OUTPUT-VALIDATION-RESPONSE-REQUEST-1-SHOW-MESSAGE",
            refresh_id,
        )

    def test_no_write_or_refresh_functions(self):
        source = self._lower(MODULE_PATH)
        functions = self._function_names(MODULE_PATH)
        for term in FORBIDDEN_FUNCTION_TERMS:
            self.assertNotIn(term, functions)
            if term == "regenerate_dashboard":
                self.assertIn("regenerate_dashboard_requested", source)
                self.assertNotIn("def regenerate_dashboard", source)
            else:
                self.assertNotIn(term, source)

    def test_runtime_import_isolation(self):
        self.assertNotIn("dashboard_output_lifecycle", self._read(RUN_ANALYSIS_PATH))
        for path in RUNTIME_ISOLATION_PATHS:
            for python_file in self._python_files(path):
                self.assertNotIn(
                    "dashboard_output_lifecycle",
                    self._read(python_file),
                    f"{python_file} must not import 7AH output lifecycle code.",
                )

    def test_behavior_files_not_modified_by_7ah_diff(self):
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            self.skipTest(f"git diff unavailable: {result.stderr.strip()}")
        changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
        forbidden_changed = {
            "src/reporting/html_dashboard.py",
            "src/reporting/ai_display_metadata.py",
            "scripts/awr_memory_cli.py",
            "scripts/run_analysis.py",
        }
        self.assertFalse(changed & forbidden_changed)


if __name__ == "__main__":
    unittest.main()
