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
BOUNDARY_DOC = DOCS / "phase7af_dashboard_backend_execution_mode.md"
MODEL_DOC = DOCS / "phase7af_backend_execution_request_model.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "dashboard_backend_execution_mode.py"

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

FORBIDDEN_IMPORT_PREFIXES = (
    "subprocess",
    "oracledb",
    "sqlite3",
    "oci",
    "requests",
    "socket",
    "urllib",
    "http.client",
    "httpx",
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
)

FORBIDDEN_SOURCE_TERMS = (
    "execute_request",
    "run_analysis.py",
    "call_object_storage",
    "call_api",
    "subprocess",
    "requests",
    "write_database",
    "auto_execute",
    "autonomous_execute",
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


def function_names(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


def execution_module():
    return importlib.import_module("src.learning.dashboard_backend_execution_mode")


def actor_context_payload() -> dict[str, object]:
    actor_module = importlib.import_module("src.learning.dashboard_actor_identity")
    actor = actor_module.DashboardActorIdentity(
        actor_id="ACTOR-LOCAL-JANE-REVIEWER",
        display_name="Jane Reviewer",
        role="reviewer",
        actor_source="local",
        permission_scope="review",
        authenticated=False,
    )
    context = actor_module.create_actor_audit_context(
        actor,
        action_scope="analyze_selection",
    )
    return actor_module.actor_audit_context_to_dict(context)


def make_request(**overrides):
    module = execution_module()
    values = {
        "request_id": module.create_backend_execution_request_id(
            "local_backend_execution",
            "analyze_selection",
            "none",
            target_screen="Screen 3",
        ),
        "execution_mode": "local_backend_execution",
        "requested_action": "analyze_selection",
        "source_mode": "none",
        "actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
        "actor_audit_context": None,
        "target_screen": "Screen 3",
        "selected_state": {"sql_id": "abc123"},
        "execution_payload": {"scope": "sql"},
        "adaptive_runtime_requested": False,
        "deterministic_default": True,
        "requires_validation": True,
        "requires_actor": True,
        "requires_audit": True,
        "created_at": None,
        "notes": "unit test",
    }
    values.update(overrides)
    return module.DashboardBackendExecutionRequest(**values)


class Phase7AFDashboardBackendExecutionModeTests(unittest.TestCase):
    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = execution_module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "DashboardBackendExecutionRequest"))
        self.assertTrue(hasattr(module, "DashboardBackendExecutionValidation"))

        imports = imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )

    def test_docs_exist(self) -> None:
        self.assertTrue(BOUNDARY_DOC.is_file(), BOUNDARY_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        text = lower_text(BOUNDARY_DOC) + "\n" + lower_text(MODEL_DOC)
        for phrase in (
            "does not execute backend actions",
            "does not call run_analysis.py",
            "does not call object storage",
            "does not add api routes",
            "does not add dashboard buttons",
            "local_backend_execution is metadata only",
            "future_api_server_execution is metadata only",
            "deterministic runtime remains authoritative",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_docs_contain_required_sections(self) -> None:
        boundary_text = read_text(BOUNDARY_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Scope",
            "## 3. Non-Goals",
            "## 4. Why Backend Execution Modes Are Needed",
            "## 5. Supported Execution Modes",
            "## 6. Supported Source Modes",
            "## 7. Supported Requested Actions",
            "## 8. Static Read-Only Mode",
            "## 9. Local Command Generation Mode",
            "## 10. Local Backend Execution Mode",
            "## 11. Future API / Server Execution Mode",
            "## 12. Object Storage Boundary",
            "## 13. Actor Requirement Boundary",
            "## 14. Audit Requirement Boundary",
            "## 15. Validation Boundary",
            "## 16. Runtime Truth Boundary",
            "## 17. Phase 4I Boundary",
            "## 18. Relationship to 7AD",
            "## 19. Relationship to 7AE",
            "## 20. Relationship to Future 7AG",
            "## 21. Relationship to Future 7AH",
            "## 22. Relationship to Screen 3 Re-Analysis",
            "## 23. Relationship to Phase 8",
            "## 24. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, boundary_text)

        model_text = read_text(MODEL_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. DashboardBackendExecutionRequest Object Shape",
            "## 3. DashboardBackendExecutionValidation Object Shape",
            "## 4. Execution Modes",
            "## 5. Source Modes",
            "## 6. Requested Actions",
            "## 7. Validation Statuses",
            "## 8. Actor Requirements",
            "## 9. Audit Requirements",
            "## 10. Deterministic ID Rules",
            "## 11. Serialization Rules",
            "## 12. Validation Rules",
            "## 13. Non-Goals",
            "## 14. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, model_text)

    def test_supported_execution_modes(self) -> None:
        module = execution_module()
        self.assertEqual(
            module.BACKEND_EXECUTION_MODES,
            (
                "static_read_only",
                "local_command_generation",
                "local_backend_execution",
                "future_api_server_execution",
            ),
        )
        for mode in module.BACKEND_EXECUTION_MODES:
            with self.subTest(mode=mode):
                request = make_request(execution_mode=mode)
                self.assertEqual(request.execution_mode, mode)
        with self.assertRaises(module.DashboardBackendExecutionModeError):
            make_request(execution_mode="remote_shell")

    def test_supported_source_modes(self) -> None:
        module = execution_module()
        self.assertEqual(
            module.SOURCE_MODES,
            (
                "none",
                "local_staged",
                "local_file",
                "existing_run",
                "object_storage",
                "future_upload",
            ),
        )
        for source_mode in module.SOURCE_MODES:
            with self.subTest(source_mode=source_mode):
                request = make_request(source_mode=source_mode)
                self.assertEqual(request.source_mode, source_mode)
        with self.assertRaises(module.DashboardBackendExecutionModeError):
            make_request(source_mode="bucket_direct")

    def test_supported_requested_actions(self) -> None:
        module = execution_module()
        self.assertEqual(
            module.REQUESTED_ACTIONS,
            (
                "read_only_view",
                "analyze_selection",
                "rerun_analysis",
                "build_comparison",
                "load_from_object_storage",
                "diagnostic_review",
                "parser_review",
                "recommendation_action",
                "outcome_capture",
                "governance_review",
                "materialization_review",
                "model_registry_review",
                "runtime_gate_review",
            ),
        )
        for action in module.REQUESTED_ACTIONS:
            with self.subTest(action=action):
                if action == "read_only_view":
                    request = module.default_static_read_only_request()
                else:
                    request = make_request(requested_action=action)
                self.assertEqual(request.requested_action, action)
        with self.assertRaises(module.DashboardBackendExecutionModeError):
            make_request(requested_action="apply_change")

    def test_default_static_read_only_request(self) -> None:
        module = execution_module()
        request = module.default_static_read_only_request(
            target_screen="Screen 3",
            notes="view only",
        )
        self.assertEqual(request.execution_mode, "static_read_only")
        self.assertEqual(request.requested_action, "read_only_view")
        self.assertEqual(request.source_mode, "none")
        self.assertTrue(request.deterministic_default)
        self.assertTrue(request.requires_validation)
        self.assertFalse(request.requires_actor)
        self.assertFalse(request.requires_audit)
        self.assertFalse(request.adaptive_runtime_requested)
        self.assertIs(module.validate_backend_execution_request(request), request)

        validation = module.evaluate_backend_execution_request(request)
        self.assertTrue(validation.valid)
        self.assertTrue(validation.execution_allowed)
        self.assertFalse(validation.execution_performed)
        self.assertTrue(validation.deterministic_default)
        self.assertEqual(validation.validation_status, "VALID")

    def test_non_read_only_actions_require_actor(self) -> None:
        module = execution_module()
        without_actor = make_request(actor_id=None, actor_audit_context=None)
        with self.assertRaises(module.DashboardBackendExecutionModeError):
            module.validate_backend_execution_request(without_actor)

        denied = module.evaluate_backend_execution_request(without_actor)
        self.assertFalse(denied.valid)
        self.assertFalse(denied.execution_allowed)
        self.assertFalse(denied.execution_performed)
        self.assertEqual(denied.validation_status, "NEEDS_ACTOR")
        self.assertIn("actor metadata is required", " ".join(denied.denied_reasons))

        with_actor = make_request(actor_id="ACTOR-LOCAL-JANE-REVIEWER")
        self.assertIs(module.validate_backend_execution_request(with_actor), with_actor)
        allowed = module.evaluate_backend_execution_request(with_actor)
        self.assertTrue(allowed.valid)
        self.assertTrue(allowed.execution_allowed)
        self.assertFalse(allowed.execution_performed)
        self.assertEqual(allowed.validation_status, "VALID")

        with_context = make_request(actor_id=None, actor_audit_context=actor_context_payload())
        self.assertIs(module.validate_backend_execution_request(with_context), with_context)

    def test_object_storage_boundary(self) -> None:
        module = execution_module()
        request = make_request(
            requested_action="load_from_object_storage",
            source_mode="object_storage",
            actor_id="ACTOR-LOCAL-JANE-REVIEWER",
            execution_payload={"object_ref": "metadata-only"},
        )
        self.assertIs(module.validate_backend_execution_request(request), request)
        validation = module.evaluate_backend_execution_request(request)
        self.assertFalse(validation.valid)
        self.assertFalse(validation.execution_allowed)
        self.assertFalse(validation.execution_performed)
        self.assertTrue(validation.deterministic_default)
        self.assertEqual(validation.validation_status, "NEEDS_SOURCE_VALIDATION")
        self.assertIn(
            "future governed source validation",
            " ".join(validation.required_next_steps),
        )
        self.assertIn("object storage is metadata only", " ".join(validation.warnings))

    def test_execution_validation_result_shape(self) -> None:
        module = execution_module()
        request = make_request(adaptive_runtime_requested=True)
        validation = module.evaluate_backend_execution_request(request)
        self.assertIsInstance(validation, module.DashboardBackendExecutionValidation)
        self.assertTrue(validation.valid)
        self.assertTrue(validation.execution_allowed)
        self.assertFalse(validation.execution_performed)
        self.assertTrue(validation.deterministic_default)
        self.assertTrue(validation.adaptive_runtime_requested)
        self.assertEqual(validation.backend_execution_mode, "local_backend_execution")
        self.assertEqual(validation.source_mode, "none")
        self.assertEqual(validation.requested_action, "analyze_selection")
        self.assertTrue(validation.actor_required)
        self.assertTrue(validation.actor_present)
        self.assertTrue(validation.audit_required)
        self.assertEqual(validation.validation_status, "VALID")
        self.assertIn("Phase 7AA gate", " ".join(validation.warnings))

        with self.assertRaises(module.DashboardBackendExecutionModeError):
            module.DashboardBackendExecutionValidation(
                validation_id="VALIDATION",
                request_id="REQUEST",
                valid=True,
                execution_allowed=True,
                execution_performed=True,
                denied_reasons=[],
                warnings=[],
                required_next_steps=[],
                deterministic_default=True,
                adaptive_runtime_requested=False,
                backend_execution_mode="static_read_only",
                source_mode="none",
                requested_action="read_only_view",
                actor_required=False,
                actor_present=False,
                audit_required=False,
                validation_status="VALID",
            )

    def test_serialization_round_trip(self) -> None:
        module = execution_module()
        request = make_request(actor_audit_context=actor_context_payload())
        request_payload = module.backend_execution_request_to_dict(request)
        request_round_trip = module.backend_execution_request_from_dict(request_payload)
        self.assertEqual(request, request_round_trip)
        self.assertEqual(
            request_payload,
            module.backend_execution_request_to_dict(request_round_trip),
        )

        validation = module.evaluate_backend_execution_request(request)
        validation_payload = module.backend_execution_validation_to_dict(validation)
        validation_round_trip = module.backend_execution_validation_from_dict(
            validation_payload
        )
        self.assertEqual(validation, validation_round_trip)
        self.assertEqual(
            validation_payload,
            module.backend_execution_validation_to_dict(validation_round_trip),
        )

    def test_deterministic_ids(self) -> None:
        module = execution_module()
        first = module.create_backend_execution_request_id(
            "local_backend_execution",
            "analyze_selection",
            "local_file",
            target_screen="Screen 3",
        )
        second = module.create_backend_execution_request_id(
            "local_backend_execution",
            "analyze_selection",
            "local_file",
            target_screen="  screen   3 ",
        )
        self.assertEqual(first, second)
        self.assertEqual(
            first,
            "DASHBOARD-BACKEND-REQUEST-LOCAL-BACKEND-EXECUTION-"
            "ANALYZE-SELECTION-LOCAL-FILE-SCREEN-3",
        )

        validation_first = module.create_backend_execution_validation_id(first)
        validation_second = module.create_backend_execution_validation_id(first)
        self.assertEqual(validation_first, validation_second)
        self.assertEqual(
            validation_first,
            "DASHBOARD-BACKEND-VALIDATION-DASHBOARD-BACKEND-REQUEST-"
            "LOCAL-BACKEND-EXECUTION-ANALYZE-SELECTION-LOCAL-FILE-SCREEN-3",
        )

    def test_no_execution_functions_or_libraries(self) -> None:
        source = lower_text(MODULE_PATH)
        names = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_SOURCE_TERMS:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
                self.assertNotIn(forbidden, names)
        self.assertNotIn("run_analysis", names)

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        for module_name in (
            "src.learning.dashboard_backend_execution_mode",
            "learning.dashboard_backend_execution_mode",
            "dashboard_backend_execution_mode",
        ):
            with self.subTest(module_name=module_name):
                self.assertNotIn(module_name, run_analysis_imports)

        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.dashboard_backend_execution_mode", imports)
                self.assertNotIn("learning.dashboard_backend_execution_mode", imports)
                self.assertNotIn("dashboard_backend_execution_mode", imports)

    def test_behavior_files_are_not_modified_by_phase7af(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git not available")
        if not (ROOT / ".git").exists():
            self.skipTest("not a git checkout")

        completed = subprocess.run(
            ("git", "diff", "--name-only", "--", *FORBIDDEN_BEHAVIOR_FILES),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            self.skipTest(completed.stderr.strip() or "git diff unavailable")

        changed = {
            line.strip()
            for line in completed.stdout.splitlines()
            if line.strip()
        }
        changed -= {"src/reporting/html_dashboard.py"}  # Phase 7AN owns disabled Screen 3 action UI.
        self.assertFalse(changed, f"behavior files modified: {sorted(changed)}")

    def test_readme_links_new_docs(self) -> None:
        text = read_text(README)
        for title, filename in (
            (
                "Phase 7AF Dashboard Backend Execution Mode Boundary",
                "phase7af_dashboard_backend_execution_mode.md",
            ),
            (
                "Phase 7AF Backend Execution Request Model",
                "phase7af_backend_execution_request_model.md",
            ),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)


if __name__ == "__main__":
    unittest.main()
