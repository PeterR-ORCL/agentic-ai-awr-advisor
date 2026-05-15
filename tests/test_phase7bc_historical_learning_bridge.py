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
BRIDGE_DOC = DOCS / "phase7bc_historical_learning_bridge.md"
MODEL_DOC = DOCS / "phase7bc_historical_learning_intent_model.md"
PANEL_DOC = DOCS / "phase7bc_screen4_historical_review_panel.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "screen4_historical_learning_bridge.py"

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
    "src.trend",
    "src.anomaly",
    "src.decision",
    "src.recommendation",
    "src.recommendations",
    "src.analysis",
    "src.memory",
    "scripts.awr_memory_cli",
    "scripts.run_analysis",
    "oracle_agent_memory",
)

FORBIDDEN_SOURCE_TERMS = (
    "persist_candidate_intent",
    "persist_review_record",
    "create_learning_candidate",
    "create_dataset_label",
    "update_trend",
    "update_anomaly",
    "update_score",
    "mutate_phase4i",
    "write_database",
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


class Phase7BCHistoricalLearningBridgeTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.screen4_historical_learning_bridge")

    @staticmethod
    def review_module():
        return importlib.import_module("src.learning.screen4_trend_anomaly_review")

    def make_candidate_intent(self, **overrides):
        module = self.module()
        values = {
            "intent_id": module.create_historical_candidate_intent_id(
                "SCREEN4-TREND-REVIEW-RUN-1-TREND-CPU",
                "validation_candidate",
            ),
            "source_review_id": "SCREEN4-TREND-REVIEW-RUN-1-TREND-CPU",
            "source_trend_review_id": "SCREEN4-TREND-REVIEW-RUN-1-TREND-CPU",
            "source_anomaly_review_id": None,
            "source_baseline_candidate_id": "HIST-BASELINE-CANDIDATE-RUN-BASE",
            "candidate_type": "validation_candidate",
            "affected_domain": "CPU",
            "affected_component": "CPU trend",
            "rationale": "Historical review decision requires future review.",
            "source_evidence": ["SCREEN4-TREND-REVIEW-RUN-1-TREND-CPU"],
            "confidence": 0.7,
            "requires_human_review": True,
            "candidate_created": False,
            "runtime_influence": False,
            "phase4i_mutation_requested": False,
            "notes": "intent only",
        }
        values.update(overrides)
        return module.HistoricalLearningCandidateIntent(**values)

    def make_signal_intent(self, **overrides):
        module = self.module()
        values = {
            "signal_intent_id": module.create_historical_signal_intent_id(
                "SCREEN4-TREND-REVIEW-RUN-1-TREND-CPU",
                "trend_review_signal",
                "risk_confirmed",
            ),
            "signal_type": "trend_review_signal",
            "label_name": "risk_confirmed",
            "label_value": "confirmed",
            "source_review_id": "SCREEN4-TREND-REVIEW-RUN-1-TREND-CPU",
            "source_trend_review_id": "SCREEN4-TREND-REVIEW-RUN-1-TREND-CPU",
            "source_anomaly_review_id": None,
            "affected_domain": "CPU",
            "confidence": 0.7,
            "dataset_label_created": False,
            "requires_human_review": True,
            "runtime_influence": False,
            "notes": "signal only",
        }
        values.update(overrides)
        return module.HistoricalLearningSignalIntent(**values)

    def make_governance_route(self, **overrides):
        module = self.module()
        values = {
            "route_id": module.create_historical_governance_route_id(
                "SCREEN4-TREND-REVIEW-RUN-1-TREND-CPU",
                "human_review",
                "human_review_queue",
            ),
            "route_type": "human_review",
            "route_target": "human_review_queue",
            "source_review_id": "SCREEN4-TREND-REVIEW-RUN-1-TREND-CPU",
            "affected_domain": "CPU",
            "recommended_action": "Review through future governed workflow",
            "governance_workflow": "human_review_workflow_preview",
            "route_status": "proposed",
            "governance_action_performed": False,
            "candidate_created": False,
            "runtime_influence": False,
            "phase4i_mutation_requested": False,
            "notes": "route only",
        }
        values.update(overrides)
        return module.HistoricalGovernanceRoute(**values)

    def make_bridge_result(self, **overrides):
        module = self.module()
        candidate = self.make_candidate_intent()
        signal = self.make_signal_intent()
        route = self.make_governance_route()
        values = {
            "bridge_result_id": module.create_historical_bridge_result_id(1),
            "source_review_count": 1,
            "candidate_intent_count": 1,
            "learning_signal_intent_count": 1,
            "governance_route_count": 1,
            "candidate_intents": [candidate],
            "learning_signal_intents": [signal],
            "governance_routes": [route],
            "bridge_status": "valid_intents_only",
            "candidates_created": False,
            "dataset_labels_created": False,
            "governance_actions_performed": False,
            "runtime_influence": False,
            "phase4i_mutation_requested": False,
            "denied_reasons": [],
            "warnings": ["intents only"],
            "required_next_steps": ["future governed workflow"],
            "notes": "summary only",
        }
        values.update(overrides)
        return module.HistoricalReviewLearningBridgeResult(**values)

    def make_trend_review(self, **overrides):
        module = self.review_module()
        values = {
            "trend_review_id": module.create_trend_review_id(
                "RUN-1",
                "AWR-1",
                "TREND-CPU",
            ),
            "run_id": "RUN-1",
            "awr_id": "AWR-1",
            "baseline_candidate_id": "HIST-BASELINE-CANDIDATE-RUN-BASE",
            "comparison_context_id": "HIST-COMPARISON-CONTEXT-BASE-TARGET",
            "trend_id": "TREND-CPU",
            "trend_name": "CPU trend",
            "domain": "CPU",
            "trend_direction": "increasing",
            "trend_strength": 0.82,
            "review_decision": "request_trend_aware_scoring_review",
            "review_status": "under_review",
            "reviewer_actor_id": "ACTOR-LOCAL-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-REVIEWER"},
            "review_notes": "recurrence visible",
            "write_performed": False,
            "trend_truth_changed": False,
            "scoring_mutation_requested": False,
            "runtime_influence": False,
            "phase4i_mutation_requested": False,
        }
        values.update(overrides)
        return module.HistoricalTrendReviewRecord(**values)

    def make_anomaly_review(self, **overrides):
        module = self.review_module()
        values = {
            "anomaly_review_id": module.create_anomaly_review_id(
                "RUN-1",
                "AWR-1",
                "ANOM-CPU",
            ),
            "run_id": "RUN-1",
            "awr_id": "AWR-1",
            "baseline_candidate_id": "HIST-BASELINE-CANDIDATE-RUN-BASE",
            "comparison_context_id": "HIST-COMPARISON-CONTEXT-BASE-TARGET",
            "anomaly_id": "ANOM-CPU",
            "anomaly_name": "CPU anomaly",
            "domain": "CPU",
            "anomaly_pattern": "spike",
            "anomaly_severity": 0.66,
            "review_decision": "mark_anomaly_false_positive",
            "review_status": "false_positive",
            "reviewer_actor_id": "ACTOR-LOCAL-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-REVIEWER"},
            "review_notes": "false positive claim",
            "write_performed": False,
            "anomaly_truth_changed": False,
            "scoring_mutation_requested": False,
            "runtime_influence": False,
            "phase4i_mutation_requested": False,
        }
        values.update(overrides)
        return module.HistoricalAnomalyReviewRecord(**values)

    def test_import_safety(self) -> None:
        before = set(os.environ)
        module = self.module()
        after = set(os.environ)

        self.assertEqual(before, after)
        imports = imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden
                        or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    ),
                    f"forbidden import {forbidden} found in {imports}",
                )
        self.assertTrue(hasattr(module, "bridge_historical_reviews"))

    def test_docs_exist_and_contain_required_boundaries(self) -> None:
        for path in (BRIDGE_DOC, MODEL_DOC, PANEL_DOC):
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), path)

        combined = "\n".join(lower_text(path) for path in (BRIDGE_DOC, MODEL_DOC))
        required_phrases = (
            "candidate intents are not candidates",
            "learning signal intents are not dataset labels",
            "no candidates are created automatically",
            "no dataset labels are created",
            "no trend/anomaly truth is changed",
            "no scoring behavior is changed",
            "no phase 4i mutation occurs",
            "deterministic runtime remains authoritative",
            "phase 8 sizing/tco is not implemented",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_supported_constants(self) -> None:
        module = self.module()
        for value in (
            "scoring_weight_review_candidate",
            "recommendation_rule_candidate",
            "validation_candidate",
            "documentation_candidate",
            "parser_mapping_candidate",
        ):
            self.assertIn(value, module.HISTORICAL_CANDIDATE_TYPES)
        for value in (
            "trend_review_signal",
            "anomaly_review_signal",
            "recurrence_signal",
            "false_positive_signal",
            "evidence_quality_signal",
            "baseline_quality_signal",
            "scoring_review_signal",
        ):
            self.assertIn(value, module.HISTORICAL_LEARNING_SIGNAL_TYPES)
        for value in (
            "issue_recurred",
            "false_positive",
            "false_negative",
            "no_change",
            "risk_confirmed",
            "unknown_outcome",
        ):
            self.assertIn(value, module.HISTORICAL_LEARNING_LABEL_NAMES)

    def test_candidate_intent_validation(self) -> None:
        module = self.module()
        intent = self.make_candidate_intent()
        self.assertIs(module.validate_historical_learning_candidate_intent(intent), intent)
        for field, value in (
            ("candidate_created", True),
            ("requires_human_review", False),
            ("runtime_influence", True),
            ("phase4i_mutation_requested", True),
            ("confidence", 0.99),
            ("candidate_type", "unsupported"),
        ):
            with self.subTest(field=field):
                with self.assertRaises(module.Screen4HistoricalLearningBridgeError):
                    self.make_candidate_intent(**{field: value})

    def test_signal_intent_validation(self) -> None:
        module = self.module()
        intent = self.make_signal_intent()
        self.assertIs(module.validate_historical_learning_signal_intent(intent), intent)
        for field, value in (
            ("dataset_label_created", True),
            ("requires_human_review", False),
            ("runtime_influence", True),
            ("confidence", 0.99),
            ("signal_type", "unsupported"),
            ("label_name", "unsupported"),
        ):
            with self.subTest(field=field):
                with self.assertRaises(module.Screen4HistoricalLearningBridgeError):
                    self.make_signal_intent(**{field: value})

    def test_governance_route_validation(self) -> None:
        module = self.module()
        route = self.make_governance_route()
        self.assertIs(module.validate_historical_governance_route(route), route)
        for field, value in (
            ("governance_action_performed", True),
            ("candidate_created", True),
            ("runtime_influence", True),
            ("phase4i_mutation_requested", True),
            ("route_type", "unsupported"),
            ("route_target", "unsupported"),
        ):
            with self.subTest(field=field):
                with self.assertRaises(module.Screen4HistoricalLearningBridgeError):
                    self.make_governance_route(**{field: value})

    def test_bridge_result_validation(self) -> None:
        module = self.module()
        result = self.make_bridge_result()
        self.assertIs(module.validate_historical_review_learning_bridge_result(result), result)
        for field, value in (
            ("candidates_created", True),
            ("dataset_labels_created", True),
            ("governance_actions_performed", True),
            ("runtime_influence", True),
            ("phase4i_mutation_requested", True),
            ("bridge_status", "unsupported"),
        ):
            with self.subTest(field=field):
                with self.assertRaises(module.Screen4HistoricalLearningBridgeError):
                    self.make_bridge_result(**{field: value})

    def test_decision_mappings(self) -> None:
        module = self.module()
        expected_candidates = {
            "request_trend_aware_scoring_review": "scoring_weight_review_candidate",
            "request_anomaly_sensitivity_review": "scoring_weight_review_candidate",
            "request_scoring_threshold_review": "scoring_weight_review_candidate",
            "request_learning_candidate": "validation_candidate",
            "mark_anomaly_false_positive": "validation_candidate",
            "dispute_trend": "validation_candidate",
            "mark_trend_insufficient": "validation_candidate",
        }
        for decision, expected in expected_candidates.items():
            with self.subTest(decision=decision):
                self.assertEqual(
                    module.candidate_type_for_historical_decision(decision),
                    expected,
                )
        self.assertEqual(
            module.candidate_type_for_historical_decision(
                "request_learning_candidate",
                {"recurrence_pattern": True},
            ),
            "scoring_weight_review_candidate",
        )
        self.assertEqual(
            module.candidate_type_for_historical_decision(
                "request_learning_candidate",
                {"recurrence_pattern": True, "recommendation_context": True},
            ),
            "recommendation_rule_candidate",
        )

        expected_signals = {
            "mark_anomaly_false_positive": "false_positive_signal",
            "request_learning_candidate": "recurrence_signal",
            "mark_trend_insufficient": "evidence_quality_signal",
            "request_scoring_threshold_review": "scoring_review_signal",
        }
        for decision, expected in expected_signals.items():
            with self.subTest(signal_decision=decision):
                self.assertEqual(
                    module.signal_type_for_historical_decision(decision),
                    expected,
                )

        expected_labels = {
            "mark_anomaly_false_positive": "false_positive",
            "request_learning_candidate": "issue_recurred",
            "approve_trend": "risk_confirmed",
            "dispute_trend": "unknown_outcome",
        }
        for decision, expected in expected_labels.items():
            with self.subTest(label_decision=decision):
                self.assertEqual(
                    module.label_name_for_historical_decision(decision),
                    expected,
                )

    def test_bridge_from_reviews_creates_intents_only(self) -> None:
        module = self.module()
        result = module.bridge_historical_reviews(
            trend_reviews=[self.make_trend_review()],
            anomaly_reviews=[self.make_anomaly_review()],
            notes="preview bridge",
        )

        self.assertEqual(result.source_review_count, 2)
        self.assertEqual(result.candidate_intent_count, 2)
        self.assertEqual(result.learning_signal_intent_count, 2)
        self.assertEqual(result.governance_route_count, 2)
        self.assertFalse(result.candidates_created)
        self.assertFalse(result.dataset_labels_created)
        self.assertFalse(result.governance_actions_performed)
        self.assertFalse(result.runtime_influence)
        self.assertFalse(result.phase4i_mutation_requested)
        self.assertTrue(all(not intent.candidate_created for intent in result.candidate_intents))
        self.assertTrue(
            all(
                not intent.dataset_label_created
                for intent in result.learning_signal_intents
            )
        )
        self.assertTrue(all(not route.candidate_created for route in result.governance_routes))

    def test_serialization_round_trips(self) -> None:
        module = self.module()
        objects = (
            (
                self.make_candidate_intent(),
                module.historical_learning_candidate_intent_to_dict,
                module.historical_learning_candidate_intent_from_dict,
            ),
            (
                self.make_signal_intent(),
                module.historical_learning_signal_intent_to_dict,
                module.historical_learning_signal_intent_from_dict,
            ),
            (
                self.make_governance_route(),
                module.historical_governance_route_to_dict,
                module.historical_governance_route_from_dict,
            ),
            (
                self.make_bridge_result(),
                module.historical_review_learning_bridge_result_to_dict,
                module.historical_review_learning_bridge_result_from_dict,
            ),
        )
        for obj, to_dict, from_dict in objects:
            with self.subTest(obj=type(obj).__name__):
                data = to_dict(obj)
                round_trip = from_dict(data)
                self.assertEqual(to_dict(round_trip), data)

    def test_deterministic_ids(self) -> None:
        module = self.module()
        calls = (
            lambda: module.create_historical_candidate_intent_id(
                "review-1",
                "validation_candidate",
            ),
            lambda: module.create_historical_signal_intent_id(
                "review-1",
                "trend_review_signal",
                "risk_confirmed",
            ),
            lambda: module.create_historical_governance_route_id(
                "review-1",
                "human_review",
                "human_review_queue",
            ),
            lambda: module.create_historical_bridge_result_id(3),
        )
        for call in calls:
            first = call()
            second = call()
            with self.subTest(identifier=first):
                self.assertEqual(first, second)
                self.assertNotRegex(first.lower(), r"[0-9a-f]{8}-[0-9a-f]{4}-")
                self.assertNotRegex(first, r"20\d{2}[-:]?\d{2}[-:]?\d{2}")

    def test_no_mutation_or_persistence_functions(self) -> None:
        names = function_names(MODULE_PATH)
        source = lower_text(MODULE_PATH)
        for term in FORBIDDEN_SOURCE_TERMS:
            with self.subTest(term=term):
                self.assertNotIn(term, names)
                self.assertNotIn(term, source)

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        for module_name in (
            "src.learning.screen4_historical_learning_bridge",
            "learning.screen4_historical_learning_bridge",
            "screen4_historical_learning_bridge",
        ):
            with self.subTest(module_name=module_name):
                self.assertNotIn(module_name, run_analysis_imports)

        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            source = read_text(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.screen4_historical_learning_bridge", imports)
                self.assertNotIn("learning.screen4_historical_learning_bridge", imports)
                self.assertNotIn("screen4_historical_learning_bridge", imports)
                self.assertNotIn("screen4_historical_learning_bridge", source)

    def test_readme_links_new_docs(self) -> None:
        text = read_text(README)
        for title, filename in (
            (
                "Phase 7BC Historical Review to Learning Candidate Bridge",
                "phase7bc_historical_learning_bridge.md",
            ),
            (
                "Phase 7BC Historical Learning Intent Model",
                "phase7bc_historical_learning_intent_model.md",
            ),
            (
                "Phase 7BC Screen 4 Historical Review Panel",
                "phase7bc_screen4_historical_review_panel.md",
            ),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)


if __name__ == "__main__":
    unittest.main()
