from __future__ import annotations

import ast
import importlib
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
MODEL_DOC = DOCS / "phase7aq_diagnostic_review_model.md"
EVIDENCE_DOC = DOCS / "phase7aq_evidence_availability_review.md"
MODULE_PATH = ROOT / "src" / "learning" / "screen2_diagnostic_review.py"

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
    "src/parser",
    "src/parsing",
    "src/scoring",
    "src/decision",
    "src/recommendation",
    "src/recommendations",
    "src/analysis/decision_engine.py",
    "src/analysis/recommendation_engine.py",
    "src/analysis/scoring_adapter.py",
    "dbschema",
    "awr_dashboard",
)

PHASE7AS_ALLOWED_BEHAVIOR_FILE = "src/reporting/html_dashboard.py"
PHASE7AS_ARTIFACT_FILES = {
    "docs/architecture/phase7as_screen2_review_panel.md",
    "docs/architecture/phase7as_screen2_review_request_preview.md",
    "tests/test_dashboard_screen2_review_panel.py",
}

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

FORBIDDEN_FUNCTION_NAMES = (
    "mutate_diagnosis",
    "update_severity",
    "update_score",
    "update_confidence",
    "update_parser_output",
    "update_recommendation",
    "create_candidate",
    "write_review_record",
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
        PHASE7AS_ALLOWED_BEHAVIOR_FILE in disallowed
        and PHASE7AS_ARTIFACT_FILES.intersection(all_changed)
    ):
        disallowed.remove(PHASE7AS_ALLOWED_BEHAVIOR_FILE)
    return disallowed


def python_files(paths: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for relative_path in paths:
        path = ROOT / relative_path
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(child for child in path.rglob("*.py") if child.is_file()))
    return files


class Phase7AQDiagnosticReviewModelTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.screen2_diagnostic_review")

    def make_review(self, **overrides):
        module = self.module()
        values = {
            "review_id": module.create_diagnostic_review_id(
                "RUN-1",
                "AWR-1",
                "primary_issue",
                "CPU",
            ),
            "screen_id": "screen_2",
            "run_id": "RUN-1",
            "awr_id": "AWR-1",
            "review_target_type": "primary_issue",
            "review_target_id": "CPU",
            "domain": "CPU",
            "current_value": "CPU saturation",
            "review_decision": "confirm",
            "review_status": "proposed",
            "reviewer_actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-JANE-REVIEWER"},
            "review_notes": "unit test",
        }
        values.update(overrides)
        return module.DiagnosticReviewRecord(**values)

    def make_evidence(self, **overrides):
        module = self.module()
        parent_review_id = overrides.pop(
            "parent_review_id",
            self.make_review().review_id,
        )
        values = {
            "evidence_review_id": module.create_evidence_review_id(
                parent_review_id,
                "metric",
                "DB-CPU",
            ),
            "parent_review_id": parent_review_id,
            "evidence_type": "metric",
            "evidence_id": "DB-CPU",
            "evidence_name": "DB CPU",
            "domain": "CPU",
            "current_value": 92,
            "evidence_status": "available",
            "reliability_status": "reliable",
            "missing_reason": "not_applicable",
            "confidence_impact": "none",
            "review_decision": "confirm",
            "reviewer_actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
        }
        values.update(overrides)
        return module.EvidenceReviewRecord(**values)

    def make_decision(self, **overrides):
        module = self.module()
        review_id = overrides.pop("review_id", self.make_review().review_id)
        values = {
            "decision_id": module.create_diagnostic_decision_id(review_id, "confirm"),
            "review_id": review_id,
            "decision_type": "confirm",
            "decision_status": "confirmed",
            "actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-JANE-REVIEWER"},
            "decision_summary": "confirmed by unit test",
        }
        values.update(overrides)
        return module.DiagnosticApprovalDecision(**values)

    def make_request(self, **overrides):
        module = self.module()
        values = {
            "request_id": module.create_diagnostic_review_request_id(
                "primary_issue",
                "CPU",
                "confirm",
            ),
            "review_target_type": "primary_issue",
            "review_target_id": "CPU",
            "requested_decision": "confirm",
            "actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-JANE-REVIEWER"},
            "payload": {"current_value": "CPU saturation"},
            "validation_status": "VALID_METADATA_ONLY",
            "can_route_to_governance": True,
            "write_performed": False,
        }
        values.update(overrides)
        return module.DiagnosticReviewRequest(**values)

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "DiagnosticReviewRecord"))
        self.assertTrue(hasattr(module, "EvidenceReviewRecord"))
        self.assertTrue(hasattr(module, "DiagnosticApprovalDecision"))
        self.assertTrue(hasattr(module, "DiagnosticReviewRequest"))

        imports = imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )

    def test_docs_exist_and_contain_required_boundary_phrases(self) -> None:
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)
        self.assertTrue(EVIDENCE_DOC.is_file(), EVIDENCE_DOC)
        text = lower_text(MODEL_DOC) + "\n" + lower_text(EVIDENCE_DOC)
        for phrase in (
            "review records do not mutate diagnostic truth",
            "review records do not change severity/confidence/score",
            "review records do not change parser output",
            "review records do not change recommendations",
            "write_performed=false in 7aq",
            "runtime_influence=false",
            "phase 4i mutation is forbidden",
            "no candidate is created automatically",
            "em extract implementation belongs to phase 8",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_supported_target_types_decisions_and_statuses(self) -> None:
        module = self.module()
        for target_type in (
            "primary_issue",
            "secondary_issue",
            "severity",
            "confidence",
            "domain_score",
            "evidence_group",
            "metric_group",
            "wait_event_group",
            "sql_signal_group",
            "diagnostic_section",
            "parser_derived_evidence",
            "trend_reference",
            "anomaly_reference",
            "missing_metric",
            "unavailable_evidence",
            "recommendation_context",
        ):
            with self.subTest(target_type=target_type):
                self.assertIn(target_type, module.SCREEN2_REVIEW_TARGET_TYPES)

        for decision in (
            "confirm",
            "dispute",
            "insufficient_evidence",
            "needs_parser_review",
            "needs_scoring_review",
            "needs_recommendation_review",
            "needs_learning_candidate",
            "add_reviewer_note",
        ):
            with self.subTest(decision=decision):
                self.assertIn(decision, module.SCREEN2_REVIEW_DECISIONS)

        for status in (
            "proposed",
            "under_review",
            "confirmed",
            "disputed",
            "insufficient_evidence",
            "needs_revision",
            "routed_to_governance",
            "closed",
        ):
            with self.subTest(status=status):
                self.assertIn(status, module.SCREEN2_REVIEW_STATUSES)

        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_review(review_target_type="unsupported_target")
        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_review(review_decision="approve_runtime")
        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_review(review_status="runtime_applied")

    def test_diagnostic_review_record_validation(self) -> None:
        module = self.module()
        record = self.make_review()
        self.assertIs(module.validate_diagnostic_review_record(record), record)
        self.assertFalse(record.runtime_influence)
        self.assertFalse(record.phase4i_mutation_requested)

        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_review(screen_id="screen_3")
        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_review(runtime_influence=True)
        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_review(phase4i_mutation_requested=True)
        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_review(review_decision="unsupported")
        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_review(review_status="unsupported")

    def test_evidence_review_record_validation(self) -> None:
        module = self.module()
        record = self.make_evidence()
        self.assertIs(module.validate_evidence_review_record(record), record)

        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_evidence(evidence_status="runtime_updated")
        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_evidence(reliability_status="trusted_by_default")
        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_evidence(runtime_influence=True)
        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_evidence(phase4i_mutation_requested=True)
        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_evidence(candidate_created=True)

    def test_diagnostic_approval_decision_validation(self) -> None:
        module = self.module()
        decision = self.make_decision()
        self.assertIs(module.validate_diagnostic_approval_decision(decision), decision)

        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_decision(actor_id="")
        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_decision(runtime_influence=True)
        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_decision(phase4i_mutation_requested=True)

    def test_diagnostic_review_request_validation(self) -> None:
        module = self.module()
        request = self.make_request()
        self.assertIs(module.validate_diagnostic_review_request(request), request)
        self.assertTrue(request.can_route_to_governance)
        self.assertFalse(request.write_performed)

        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_request(write_performed=True)
        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_request(runtime_influence=True)
        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_request(phase4i_mutation_requested=True)
        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_request(review_target_type="unsupported")
        with self.assertRaises(module.Screen2DiagnosticReviewError):
            self.make_request(requested_decision="unsupported")

    def test_evidence_availability_classification_recommendation_flags(self) -> None:
        module = self.module()
        parent_review_id = self.make_review().review_id

        parser_gap = module.classify_evidence_review_from_availability(
            {
                "parent_review_id": parent_review_id,
                "name": "Wait class",
                "evidence_type": "wait_event",
                "extracted": False,
            }
        )
        source_gap = module.classify_evidence_review_from_availability(
            {
                "parent_review_id": parent_review_id,
                "name": "ASH sample",
                "evidence_type": "metric",
                "available": False,
                "missing_reason": "source_not_collected",
            }
        )
        scoring_gap = module.classify_evidence_review_from_availability(
            {
                "parent_review_id": parent_review_id,
                "name": "CPU domain score",
                "evidence_type": "domain_score",
                "available": False,
            }
        )
        recommendation_gap = module.classify_evidence_review_from_availability(
            {
                "parent_review_id": parent_review_id,
                "name": "recommendation context",
                "evidence_type": "recommendation_context",
                "available": False,
            }
        )

        self.assertTrue(parser_gap.parser_review_recommended)
        self.assertEqual("parser_gap", parser_gap.missing_reason)
        self.assertTrue(source_gap.source_review_recommended)
        self.assertTrue(scoring_gap.scoring_review_recommended)
        self.assertEqual("high", scoring_gap.confidence_impact)
        self.assertTrue(recommendation_gap.recommendation_review_recommended)
        for record in (parser_gap, source_gap, scoring_gap, recommendation_gap):
            with self.subTest(record=record.evidence_name):
                self.assertFalse(record.candidate_created)
                self.assertFalse(record.runtime_influence)
                self.assertFalse(record.phase4i_mutation_requested)

    def test_serialization_round_trips_are_deterministic(self) -> None:
        module = self.module()
        objects = (
            (
                module.diagnostic_review_record_to_dict,
                module.diagnostic_review_record_from_dict,
                self.make_review(),
            ),
            (
                module.evidence_review_record_to_dict,
                module.evidence_review_record_from_dict,
                self.make_evidence(),
            ),
            (
                module.diagnostic_approval_decision_to_dict,
                module.diagnostic_approval_decision_from_dict,
                self.make_decision(),
            ),
            (
                module.diagnostic_review_request_to_dict,
                module.diagnostic_review_request_from_dict,
                self.make_request(),
            ),
        )
        for to_dict, from_dict, value in objects:
            with self.subTest(value=type(value).__name__):
                serialized = to_dict(value)
                self.assertEqual(to_dict(from_dict(serialized)), serialized)
                self.assertEqual(to_dict(from_dict(serialized)), to_dict(from_dict(serialized)))

    def test_deterministic_ids(self) -> None:
        module = self.module()
        ids = (
            module.create_diagnostic_review_id("RUN-1", "AWR-1", "primary_issue", "CPU"),
            module.create_evidence_review_id("REVIEW-1", "metric", "DB-CPU"),
            module.create_diagnostic_decision_id("REVIEW-1", "confirm"),
            module.create_diagnostic_review_request_id("primary_issue", "CPU", "confirm"),
        )
        self.assertEqual(
            ids[0],
            module.create_diagnostic_review_id("RUN-1", "AWR-1", "primary_issue", "CPU"),
        )
        self.assertEqual(
            ids[1],
            module.create_evidence_review_id("REVIEW-1", "metric", "DB-CPU"),
        )
        self.assertEqual(
            ids[2],
            module.create_diagnostic_decision_id("REVIEW-1", "confirm"),
        )
        self.assertEqual(
            ids[3],
            module.create_diagnostic_review_request_id("primary_issue", "CPU", "confirm"),
        )
        for value in ids:
            with self.subTest(value=value):
                self.assertFalse(
                    re.search(
                        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                        value.lower(),
                    )
                )

    def test_no_mutation_functions(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, names)

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        for module_name in (
            "src.learning.screen2_diagnostic_review",
            "learning.screen2_diagnostic_review",
            "screen2_diagnostic_review",
        ):
            with self.subTest(module_name=module_name):
                self.assertNotIn(module_name, run_analysis_imports)

        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            source = read_text(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.screen2_diagnostic_review", imports)
                self.assertNotIn("learning.screen2_diagnostic_review", imports)
                self.assertNotIn("screen2_diagnostic_review", imports)
                self.assertNotIn("screen2_diagnostic_review", source)

    def test_behavior_files_are_not_modified_by_phase7aq(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
