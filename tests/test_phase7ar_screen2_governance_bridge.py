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
BRIDGE_DOC = DOCS / "phase7ar_screen2_governance_bridge.md"
ROUTE_DOC = DOCS / "phase7ar_governance_route_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "screen2_governance_bridge.py"

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
    "execute_governance_action",
    "persist_governance_record",
    "create_learning_candidate",
    "create_candidate",
    "write_database",
    "call_governance_service",
    "run_analysis",
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


class Phase7ARScreen2GovernanceBridgeTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.screen2_governance_bridge")

    @staticmethod
    def review_module():
        return importlib.import_module("src.learning.screen2_diagnostic_review")

    def make_diagnostic_review(self, decision: str = "confirm", **overrides):
        review_module = self.review_module()
        values = {
            "review_id": review_module.create_diagnostic_review_id(
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
            "review_decision": decision,
            "review_status": "proposed",
            "reviewer_actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-JANE-REVIEWER"},
            "review_notes": "unit test",
        }
        values.update(overrides)
        return review_module.DiagnosticReviewRecord(**values)

    def make_evidence_review(self, **overrides):
        review_module = self.review_module()
        parent_review_id = overrides.pop(
            "parent_review_id",
            self.make_diagnostic_review().review_id,
        )
        values = {
            "evidence_review_id": review_module.create_evidence_review_id(
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
        return review_module.EvidenceReviewRecord(**values)

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "Screen2GovernanceRoute"))
        self.assertTrue(hasattr(module, "Screen2CandidateRequestIntent"))
        self.assertTrue(hasattr(module, "Screen2GovernanceBridgeResult"))

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
        self.assertTrue(BRIDGE_DOC.is_file(), BRIDGE_DOC)
        self.assertTrue(ROUTE_DOC.is_file(), ROUTE_DOC)
        text = lower_text(BRIDGE_DOC) + "\n" + lower_text(ROUTE_DOC)
        for phrase in (
            "bridge does not execute governance actions",
            "bridge does not persist governance records",
            "bridge does not create candidates automatically",
            "candidate intents are not candidates",
            "no diagnostic truth is changed",
            "no phase 4i mutation occurs",
            "no parser/scoring/recommendation behavior changes occur",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_supported_route_types_targets_and_workflows(self) -> None:
        module = self.module()
        for route_type in (
            "no_action",
            "close_review",
            "human_review",
            "parser_review",
            "scoring_review",
            "recommendation_review",
            "evidence_validation",
            "source_review",
            "learning_candidate_request",
        ):
            with self.subTest(route_type=route_type):
                self.assertIn(route_type, module.SCREEN2_GOVERNANCE_ROUTE_TYPES)

        for route_target in (
            "parser_governance",
            "scoring_governance",
            "recommendation_governance",
            "evidence_quality",
            "source_quality",
            "learning_candidate_queue",
            "human_review_queue",
            "review_closure",
        ):
            with self.subTest(route_target=route_target):
                self.assertIn(route_target, module.SCREEN2_GOVERNANCE_ROUTE_TARGETS)

        for workflow in (
            "parser_mapping_review",
            "scoring_review",
            "recommendation_rule_review",
            "evidence_availability_review",
            "source_validation_review",
            "learning_candidate_review",
            "human_review",
            "closure",
        ):
            with self.subTest(workflow=workflow):
                self.assertIn(workflow, module.SCREEN2_GOVERNANCE_WORKFLOWS)

        route = module.route_diagnostic_review(self.make_diagnostic_review())[0]
        with self.assertRaises(module.Screen2GovernanceBridgeError):
            module.Screen2GovernanceRoute(
                **{
                    **module.screen2_governance_route_to_dict(route),
                    "route_type": "runtime_apply",
                }
            )
        with self.assertRaises(module.Screen2GovernanceBridgeError):
            module.Screen2GovernanceRoute(
                **{
                    **module.screen2_governance_route_to_dict(route),
                    "route_target": "runtime_truth",
                }
            )
        with self.assertRaises(module.Screen2GovernanceBridgeError):
            module.Screen2GovernanceRoute(
                **{
                    **module.screen2_governance_route_to_dict(route),
                    "governance_workflow": "execute_runtime",
                }
            )

    def test_diagnostic_review_routing(self) -> None:
        module = self.module()
        cases = {
            "confirm": "close_review",
            "dispute": "human_review",
            "insufficient_evidence": "evidence_validation",
            "needs_parser_review": "parser_review",
            "needs_scoring_review": "scoring_review",
            "needs_recommendation_review": "recommendation_review",
            "needs_learning_candidate": "learning_candidate_request",
        }
        for decision, route_type in cases.items():
            with self.subTest(decision=decision):
                routes = module.route_diagnostic_review(
                    self.make_diagnostic_review(decision)
                )
                self.assertEqual([route_type], [route.route_type for route in routes])
                self.assertFalse(routes[0].governance_action_performed)
                self.assertFalse(routes[0].candidate_created)

    def test_evidence_review_routing_order(self) -> None:
        module = self.module()
        routes = module.route_evidence_review(
            self.make_evidence_review(
                evidence_status="missing",
                reliability_status="insufficient_context",
                missing_reason="source_misconfigured",
                review_decision="insufficient_evidence",
                parser_review_recommended=True,
                scoring_review_recommended=True,
                recommendation_review_recommended=True,
                source_review_recommended=True,
            )
        )
        self.assertEqual(
            [
                "parser_review",
                "scoring_review",
                "recommendation_review",
                "source_review",
                "evidence_validation",
            ],
            [route.route_type for route in routes],
        )

    def test_candidate_intent_mapping(self) -> None:
        module = self.module()
        route_types = (
            "needs_parser_review",
            "needs_scoring_review",
            "needs_recommendation_review",
            "insufficient_evidence",
        )
        routes = []
        for decision in route_types:
            routes.extend(module.route_diagnostic_review(self.make_diagnostic_review(decision)))

        intents = module.create_candidate_intents_from_routes(routes)
        self.assertEqual(
            [
                "parser_mapping_candidate",
                "scoring_weight_review_candidate",
                "recommendation_rule_candidate",
                "validation_candidate",
            ],
            [intent.candidate_type for intent in intents],
        )
        for intent in intents:
            with self.subTest(intent=intent.intent_id):
                self.assertTrue(intent.requires_human_review)
                self.assertFalse(intent.candidate_created)
                self.assertFalse(intent.runtime_influence)

    def test_bridge_result_collects_routes_and_intents(self) -> None:
        module = self.module()
        result = module.bridge_screen2_reviews(
            diagnostic_reviews=[
                self.make_diagnostic_review("needs_parser_review"),
                self.make_diagnostic_review(
                    "needs_learning_candidate",
                    review_target_type="recommendation_context",
                    review_target_id="REC-1",
                ),
            ],
            evidence_reviews=[
                self.make_evidence_review(
                    evidence_type="domain_score",
                    evidence_id="CPU-SCORE",
                    evidence_name="CPU score",
                    evidence_status="missing",
                    reliability_status="insufficient_context",
                    missing_reason="absent_from_report",
                    scoring_review_recommended=True,
                    review_decision="insufficient_evidence",
                )
            ],
            actor_id="ACTOR-LOCAL-JANE-REVIEWER",
            notes="unit bridge",
        )
        self.assertGreaterEqual(result.route_count, 3)
        self.assertEqual(result.route_count, len(result.routes))
        self.assertEqual(result.candidate_intent_count, len(result.candidate_intents))
        self.assertFalse(result.governance_actions_performed)
        self.assertFalse(result.candidates_created)
        self.assertFalse(result.runtime_influence)
        self.assertFalse(result.phase4i_mutation_requested)

    def test_validation_rejects_unsafe_fields(self) -> None:
        module = self.module()
        route = module.route_diagnostic_review(
            self.make_diagnostic_review("needs_parser_review")
        )[0]
        route_data = module.screen2_governance_route_to_dict(route)
        with self.assertRaises(module.Screen2GovernanceBridgeError):
            module.Screen2GovernanceRoute(
                **{**route_data, "governance_action_performed": True}
            )
        with self.assertRaises(module.Screen2GovernanceBridgeError):
            module.Screen2GovernanceRoute(**{**route_data, "candidate_created": True})
        with self.assertRaises(module.Screen2GovernanceBridgeError):
            module.Screen2GovernanceRoute(**{**route_data, "runtime_influence": True})
        with self.assertRaises(module.Screen2GovernanceBridgeError):
            module.Screen2GovernanceRoute(
                **{**route_data, "phase4i_mutation_requested": True}
            )

        intent = module.create_candidate_intents_from_routes([route])[0]
        intent_data = module.screen2_candidate_request_intent_to_dict(intent)
        with self.assertRaises(module.Screen2GovernanceBridgeError):
            module.Screen2CandidateRequestIntent(
                **{**intent_data, "candidate_created": True}
            )

        result = module.bridge_screen2_reviews(
            diagnostic_reviews=[self.make_diagnostic_review("needs_parser_review")]
        )
        result_data = module.screen2_governance_bridge_result_to_dict(result)
        with self.assertRaises(module.Screen2GovernanceBridgeError):
            module.Screen2GovernanceBridgeResult(
                **{**result_data, "governance_actions_performed": True}
            )
        with self.assertRaises(module.Screen2GovernanceBridgeError):
            module.Screen2GovernanceBridgeResult(
                **{**result_data, "candidates_created": True}
            )
        with self.assertRaises(module.Screen2GovernanceBridgeError):
            module.Screen2GovernanceBridgeResult(
                **{**result_data, "runtime_influence": True}
            )
        with self.assertRaises(module.Screen2GovernanceBridgeError):
            module.Screen2GovernanceBridgeResult(
                **{**result_data, "phase4i_mutation_requested": True}
            )

    def test_serialization_round_trips_are_deterministic(self) -> None:
        module = self.module()
        route = module.route_diagnostic_review(
            self.make_diagnostic_review("needs_parser_review")
        )[0]
        intent = module.create_candidate_intents_from_routes([route])[0]
        result = module.bridge_screen2_reviews(
            diagnostic_reviews=[self.make_diagnostic_review("needs_parser_review")]
        )

        self.assertEqual(
            module.screen2_governance_route_to_dict(
                module.screen2_governance_route_from_dict(
                    module.screen2_governance_route_to_dict(route)
                )
            ),
            module.screen2_governance_route_to_dict(route),
        )
        self.assertEqual(
            module.screen2_candidate_request_intent_to_dict(
                module.screen2_candidate_request_intent_from_dict(
                    module.screen2_candidate_request_intent_to_dict(intent)
                )
            ),
            module.screen2_candidate_request_intent_to_dict(intent),
        )
        self.assertEqual(
            module.screen2_governance_bridge_result_to_dict(
                module.screen2_governance_bridge_result_from_dict(
                    module.screen2_governance_bridge_result_to_dict(result)
                )
            ),
            module.screen2_governance_bridge_result_to_dict(result),
        )

    def test_deterministic_ids(self) -> None:
        module = self.module()
        route_id = module.create_screen2_governance_route_id(
            "REVIEW-1",
            "parser_review",
            "parser_governance",
        )
        intent_id = module.create_screen2_candidate_intent_id(
            route_id,
            "parser_mapping_candidate",
        )
        result_id = module.create_screen2_governance_bridge_result_id("REVIEW-1")
        self.assertEqual(
            route_id,
            module.create_screen2_governance_route_id(
                "REVIEW-1",
                "parser_review",
                "parser_governance",
            ),
        )
        self.assertEqual(
            intent_id,
            module.create_screen2_candidate_intent_id(
                route_id,
                "parser_mapping_candidate",
            ),
        )
        self.assertEqual(
            result_id,
            module.create_screen2_governance_bridge_result_id("REVIEW-1"),
        )
        for value in (route_id, intent_id, result_id):
            with self.subTest(value=value):
                self.assertFalse(
                    re.search(
                        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                        value.lower(),
                    )
                )

    def test_no_execution_or_persistence_functions(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, names)

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        for module_name in (
            "src.learning.screen2_governance_bridge",
            "learning.screen2_governance_bridge",
            "screen2_governance_bridge",
        ):
            with self.subTest(module_name=module_name):
                self.assertNotIn(module_name, run_analysis_imports)

        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            source = read_text(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.screen2_governance_bridge", imports)
                self.assertNotIn("learning.screen2_governance_bridge", imports)
                self.assertNotIn("screen2_governance_bridge", imports)
                self.assertNotIn("screen2_governance_bridge", source)

    def test_behavior_files_are_not_modified_by_phase7ar(self) -> None:
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
