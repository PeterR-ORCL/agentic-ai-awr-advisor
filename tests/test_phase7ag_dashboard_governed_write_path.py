"""Phase 7AG tests for dashboard governed write-path metadata."""

from __future__ import annotations

import ast
import importlib
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "learning" / "dashboard_governed_write_path.py"
RUN_ANALYSIS_PATH = ROOT / "scripts" / "run_analysis.py"
DOCS = ROOT / "docs" / "architecture"
ARCHITECTURE_DOC = DOCS / "phase7ag_dashboard_governed_write_path.md"
MODEL_DOC = DOCS / "phase7ag_write_path_model.md"

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

FORBIDDEN_SOURCE_TERMS = (
    "perform_write",
    "execute_write",
    "write_database",
    "call_backend",
    "run_analysis",
    "apply_mutation",
    "mutate_runtime",
    "auto_apply",
    "autonomous_apply",
)

RUNTIME_ISOLATION_PATHS = (
    ROOT / "src" / "parser",
    ROOT / "src" / "scoring",
    ROOT / "src" / "decision",
    ROOT / "src" / "recommendation",
)


class Phase7AGDashboardGovernedWritePathTests(unittest.TestCase):
    """Validate the 7AG write-path framework remains dry-run metadata only."""

    @staticmethod
    def _module():
        return importlib.import_module("src.learning.dashboard_governed_write_path")

    @staticmethod
    def _backend_module():
        return importlib.import_module("src.learning.dashboard_backend_execution_mode")

    @staticmethod
    def _actor_module():
        return importlib.import_module("src.learning.dashboard_actor_identity")

    @staticmethod
    def _read(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _lower(path: Path) -> str:
        return Phase7AGDashboardGovernedWritePathTests._read(path).lower()

    @staticmethod
    def _imported_modules(path: Path) -> set[str]:
        tree = ast.parse(Phase7AGDashboardGovernedWritePathTests._read(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        return imports

    @staticmethod
    def _function_names(path: Path) -> set[str]:
        tree = ast.parse(Phase7AGDashboardGovernedWritePathTests._read(path))
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

    def _actor_audit_context_payload(self) -> dict[str, object]:
        actor = self._actor_module()
        actor_identity = actor.DashboardActorIdentity(
            actor_id=actor.create_actor_id("Jane Reviewer", "local"),
            display_name="Jane Reviewer",
            role="reviewer",
            actor_source="local",
            permission_scope="review",
            authenticated=False,
        )
        context = actor.create_actor_audit_context(
            actor_identity,
            action_scope="diagnostic_review",
            notes="unit-test actor metadata",
        )
        return actor.actor_audit_context_to_dict(context)

    def _backend_execution_request_payload(self) -> dict[str, object]:
        backend = self._backend_module()
        request = backend.DashboardBackendExecutionRequest(
            request_id=backend.create_backend_execution_request_id(
                "local_backend_execution",
                "analyze_selection",
                "none",
                "Screen 3",
            ),
            execution_mode="local_backend_execution",
            requested_action="analyze_selection",
            source_mode="none",
            actor_id="ACTOR-LOCAL-JANE-REVIEWER",
            actor_audit_context=None,
            target_screen="Screen 3",
            selected_state={"sql_id": "abc123"},
            execution_payload={"scope": "unit-test"},
            adaptive_runtime_requested=False,
            deterministic_default=True,
            requires_validation=True,
            requires_actor=True,
            requires_audit=True,
        )
        return backend.backend_execution_request_to_dict(request)

    def _make_request(self, **overrides: object):
        module = self._module()
        values: dict[str, object] = {
            "request_id": module.create_governed_write_request_id(
                "diagnostic_evidence",
                "EVID-1",
                "review",
            ),
            "target_type": "diagnostic_evidence",
            "target_id": "EVID-1",
            "write_intent": "review",
            "actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
            "actor_audit_context": None,
            "backend_execution_request": None,
            "payload": {"review_state": "confirmed"},
            "dry_run": True,
            "requires_actor": True,
            "requires_audit": True,
            "requires_backend_validation": True,
            "runtime_mutation_requested": False,
            "phase4i_mutation_requested": False,
            "created_at": None,
            "notes": "unit-test request",
        }
        values.update(overrides)
        return module.GovernedWriteRequest(**values)

    def test_module_import_safety(self):
        module = self._module()
        self.assertTrue(hasattr(module, "GovernedWriteRequest"))

        imports = self._imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            self.assertFalse(
                any(
                    imported == forbidden or imported.startswith(f"{forbidden}.")
                    for imported in imports
                ),
                f"Forbidden import found in 7AG module: {forbidden}",
            )

    def test_docs_exist(self):
        self.assertTrue(ARCHITECTURE_DOC.exists())
        self.assertTrue(MODEL_DOC.exists())

    def test_docs_contain_required_boundary_phrases(self):
        combined = f"{self._lower(ARCHITECTURE_DOC)}\n{self._lower(MODEL_DOC)}"
        required_phrases = (
            "no write is performed in 7ag",
            "dry_run=true",
            "write_performed=false",
            "non-read-only actions require actor metadata",
            "execute intent requires backend execution validation metadata",
            "runtime mutation is forbidden",
            "phase 4i mutation is forbidden",
            "no dashboard ui is changed",
            "no cli behavior is changed",
            "deterministic runtime remains authoritative",
        )
        for phrase in required_phrases:
            self.assertIn(phrase, combined)

    def test_supported_target_types(self):
        module = self._module()
        expected_targets = {
            "diagnostic_evidence",
            "recommendation",
            "action",
            "outcome",
            "parser_unknown",
            "learning_candidate",
            "materialization_artifact",
            "model_registry_entry",
            "runtime_gate",
            "backend_execution_request",
            "source_selection",
            "historical_baseline",
            "trend_anomaly_review",
            "governance_item",
        }
        self.assertEqual(expected_targets, set(module.GOVERNED_WRITE_TARGET_TYPES))
        for target_type in expected_targets:
            request = self._make_request(
                request_id=module.create_governed_write_request_id(
                    target_type,
                    "TARGET-1",
                    "review",
                ),
                target_type=target_type,
                target_id="TARGET-1",
            )
            self.assertEqual(target_type, request.target_type)
        with self.assertRaises(module.DashboardGovernedWritePathError):
            self._make_request(target_type="dashboard_html")

    def test_supported_write_intents(self):
        module = self._module()
        expected_intents = {
            "read_only",
            "review",
            "approve",
            "reject",
            "request_revision",
            "defer",
            "assign",
            "execute",
            "capture_outcome",
            "create_candidate",
            "link_artifact",
            "validate",
            "close",
        }
        self.assertEqual(expected_intents, set(module.GOVERNED_WRITE_INTENTS))
        for intent in expected_intents:
            request_id = module.create_governed_write_request_id(
                "diagnostic_evidence",
                "TARGET-1",
                intent,
            )
            overrides: dict[str, object] = {
                "request_id": request_id,
                "write_intent": intent,
            }
            if intent == "read_only":
                overrides.update({"actor_id": None, "requires_actor": False})
            if intent == "execute":
                overrides["backend_execution_request"] = (
                    self._backend_execution_request_payload()
                )
            request = self._make_request(**overrides)
            self.assertEqual(intent, request.write_intent)
        with self.assertRaises(module.DashboardGovernedWritePathError):
            self._make_request(write_intent="mutate_runtime")

    def test_default_read_only_request(self):
        module = self._module()
        request = module.default_read_only_write_request(
            "diagnostic_evidence",
            "EVID-READ",
            notes="read-only unit test",
        )
        self.assertEqual("read_only", request.write_intent)
        self.assertTrue(request.dry_run)
        self.assertFalse(request.requires_actor)
        self.assertTrue(request.requires_audit)
        self.assertFalse(request.runtime_mutation_requested)
        self.assertFalse(request.phase4i_mutation_requested)

        validated = module.validate_governed_write_request(request)
        validation = module.evaluate_governed_write_request(validated)
        self.assertTrue(validation.valid)
        self.assertEqual("VALID", validation.validation_status)
        self.assertFalse(validation.write_performed)
        self.assertFalse(validation.actor_required)
        self.assertTrue(validation.audit_required)

    def test_non_read_only_actor_requirement(self):
        module = self._module()
        review_without_actor = self._make_request(
            actor_id=None,
            actor_audit_context=None,
        )
        with self.assertRaises(module.DashboardGovernedWritePathError):
            module.validate_governed_write_request(review_without_actor)
        review_validation = module.evaluate_governed_write_request(review_without_actor)
        self.assertFalse(review_validation.valid)
        self.assertEqual("NEEDS_ACTOR", review_validation.validation_status)
        self.assertFalse(review_validation.write_performed)

        approve_without_actor = self._make_request(
            request_id=module.create_governed_write_request_id(
                "diagnostic_evidence",
                "EVID-APPROVE",
                "approve",
            ),
            target_id="EVID-APPROVE",
            write_intent="approve",
            actor_id=None,
            actor_audit_context=None,
        )
        with self.assertRaises(module.DashboardGovernedWritePathError):
            module.validate_governed_write_request(approve_without_actor)

        review_with_actor_context = self._make_request(
            actor_id=None,
            actor_audit_context=self._actor_audit_context_payload(),
        )
        validated = module.validate_governed_write_request(review_with_actor_context)
        validation = module.evaluate_governed_write_request(validated)
        self.assertTrue(validation.valid)
        self.assertTrue(validation.write_allowed_for_future_handling)
        self.assertTrue(validation.actor_present)
        self.assertFalse(validation.write_performed)

    def test_execute_intent_requires_backend_execution_request(self):
        module = self._module()
        execute_without_backend = self._make_request(
            request_id=module.create_governed_write_request_id(
                "backend_execution_request",
                "EXEC-1",
                "execute",
            ),
            target_type="backend_execution_request",
            target_id="EXEC-1",
            write_intent="execute",
            backend_execution_request=None,
        )
        with self.assertRaises(module.DashboardGovernedWritePathError):
            module.validate_governed_write_request(execute_without_backend)
        missing_backend_validation = module.evaluate_governed_write_request(
            execute_without_backend
        )
        self.assertFalse(missing_backend_validation.valid)
        self.assertEqual(
            "NEEDS_BACKEND_EXECUTION_MODE",
            missing_backend_validation.validation_status,
        )
        self.assertFalse(missing_backend_validation.write_performed)

        execute_with_backend = self._make_request(
            request_id=module.create_governed_write_request_id(
                "backend_execution_request",
                "EXEC-2",
                "execute",
            ),
            target_type="backend_execution_request",
            target_id="EXEC-2",
            write_intent="execute",
            backend_execution_request=self._backend_execution_request_payload(),
        )
        validated = module.validate_governed_write_request(execute_with_backend)
        validation = module.evaluate_governed_write_request(validated)
        self.assertTrue(validation.valid)
        self.assertTrue(validation.backend_validation_present)
        self.assertFalse(validation.write_performed)

    def test_runtime_mutation_protection(self):
        module = self._module()
        with self.assertRaises(module.DashboardGovernedWritePathError):
            self._make_request(runtime_mutation_requested=True)
        with self.assertRaises(module.DashboardGovernedWritePathError):
            self._make_request(phase4i_mutation_requested=True)
        with self.assertRaises(module.DashboardGovernedWritePathError):
            self._make_request(dry_run=False)

        with self.assertRaises(module.DashboardGovernedWritePathError):
            module.GovernedWriteValidation(
                validation_id="VALIDATION-1",
                request_id="REQUEST-1",
                valid=True,
                validation_status="VALID",
                write_allowed_for_future_handling=True,
                write_performed=True,
                dry_run=True,
                actor_required=True,
                actor_present=True,
                audit_required=True,
                backend_validation_required=True,
                backend_validation_present=False,
                runtime_mutation_requested=False,
                phase4i_mutation_requested=False,
                denied_reasons=[],
                warnings=[],
                required_next_steps=[],
            )

        with self.assertRaises(module.DashboardGovernedWritePathError):
            module.GovernedWriteAuditRecord(
                audit_id="AUDIT-1",
                request_id="REQUEST-1",
                validation_id="VALIDATION-1",
                actor_id="ACTOR-1",
                target_type="diagnostic_evidence",
                target_id="EVID-1",
                write_intent="review",
                dry_run=True,
                write_performed=True,
                validation_status="VALID",
                audit_summary="invalid audit",
                runtime_mutation_performed=False,
                phase4i_mutation_performed=False,
            )

        with self.assertRaises(module.DashboardGovernedWritePathError):
            module.GovernedWriteAuditRecord(
                audit_id="AUDIT-2",
                request_id="REQUEST-1",
                validation_id="VALIDATION-1",
                actor_id="ACTOR-1",
                target_type="diagnostic_evidence",
                target_id="EVID-1",
                write_intent="review",
                dry_run=True,
                write_performed=False,
                validation_status="VALID",
                audit_summary="invalid audit",
                runtime_mutation_performed=True,
                phase4i_mutation_performed=False,
            )

    def test_audit_record_creation(self):
        module = self._module()
        request = self._make_request(actor_audit_context=self._actor_audit_context_payload())
        validation = module.evaluate_governed_write_request(request)
        record = module.create_governed_write_audit_record(
            request,
            validation,
            notes="audit unit test",
        )
        second_record = module.create_governed_write_audit_record(
            request,
            validation,
            notes="audit unit test",
        )
        self.assertEqual(record.audit_id, second_record.audit_id)
        self.assertFalse(record.write_performed)
        self.assertFalse(record.runtime_mutation_performed)
        self.assertFalse(record.phase4i_mutation_performed)
        self.assertEqual("VALID", record.validation_status)
        self.assertIs(module.validate_governed_write_audit_record(record), record)

    def test_serialization_round_trips(self):
        module = self._module()
        request = self._make_request(
            actor_audit_context=self._actor_audit_context_payload()
        )
        request_round_trip = module.governed_write_request_from_dict(
            module.governed_write_request_to_dict(request)
        )
        self.assertEqual(request, request_round_trip)

        validation = module.evaluate_governed_write_request(request_round_trip)
        validation_round_trip = module.governed_write_validation_from_dict(
            module.governed_write_validation_to_dict(validation)
        )
        self.assertEqual(validation, validation_round_trip)

        audit = module.create_governed_write_audit_record(
            request_round_trip,
            validation_round_trip,
        )
        audit_round_trip = module.governed_write_audit_record_from_dict(
            module.governed_write_audit_record_to_dict(audit)
        )
        self.assertEqual(audit, audit_round_trip)

    def test_deterministic_ids(self):
        module = self._module()
        first_request_id = module.create_governed_write_request_id(
            "diagnostic_evidence",
            " Evidence 1 ",
            "review",
        )
        second_request_id = module.create_governed_write_request_id(
            "diagnostic_evidence",
            "Evidence 1",
            "review",
        )
        self.assertEqual(first_request_id, second_request_id)
        self.assertEqual(
            "GOVERNED-WRITE-REQUEST-DIAGNOSTIC-EVIDENCE-EVIDENCE-1-REVIEW",
            first_request_id,
        )

        validation_id = module.create_governed_write_validation_id(first_request_id)
        self.assertEqual(
            f"GOVERNED-WRITE-VALIDATION-{first_request_id}",
            validation_id,
        )
        audit_id = module.create_governed_write_audit_id(
            first_request_id,
            validation_id,
        )
        self.assertEqual(
            f"GOVERNED-WRITE-AUDIT-{first_request_id}-{validation_id}",
            audit_id,
        )

    def test_no_execution_functions_or_terms(self):
        source = self._lower(MODULE_PATH)
        functions = self._function_names(MODULE_PATH)
        for term in FORBIDDEN_SOURCE_TERMS:
            self.assertNotIn(term, source)
            self.assertNotIn(term, functions)

    def test_runtime_import_isolation(self):
        self.assertNotIn("dashboard_governed_write_path", self._read(RUN_ANALYSIS_PATH))
        for path in RUNTIME_ISOLATION_PATHS:
            for python_file in self._python_files(path):
                self.assertNotIn(
                    "dashboard_governed_write_path",
                    self._read(python_file),
                    f"{python_file} must not import 7AG dashboard write-path code.",
                )

    def test_behavior_files_not_modified_by_7ag_diff(self):
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
        forbidden_changed -= {"src/reporting/html_dashboard.py"}  # Phase 7AN owns disabled Screen 3 action UI.
        self.assertFalse(changed & forbidden_changed)


if __name__ == "__main__":
    unittest.main()
