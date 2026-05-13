from __future__ import annotations

import ast
import importlib
import json
import os
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
SCORING_DOC = DOCS / "phase7_trend_aware_scoring.md"
MODEL_DOC = DOCS / "phase7_trend_aware_scoring_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "trend_aware_scoring.py"

RUNTIME_PATHS = (
    "scripts/run_analysis.py",
    "src/parser",
    "src/scoring",
    "src/decision",
    "src/recommendation",
    "src/recommendations",
)

FORBIDDEN_IMPORT_PREFIXES = (
    "oracledb",
    "oci",
    "requests",
    "socket",
    "urllib",
    "http.client",
    "httpx",
    "sklearn",
    "tensorflow",
    "torch",
    "src.parser",
    "src.scoring",
    "src.decision",
    "src.recommendation",
    "src.recommendations",
    "src.reporting",
    "src.memory",
)

FORBIDDEN_FUNCTION_NAMES = (
    "apply_trend_score",
    "activate_trend_score",
    "update_runtime_scoring",
    "replace_scoring_engine",
    "learned_model",
    "score_ml",
    "train_model",
    "auto_apply",
    "autonomous_apply",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


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


class Phase7TrendAwareScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = importlib.import_module("src.learning.trend_aware_scoring")

    def trend_context(
        self,
        *,
        domain: str = "CPU",
        trend_direction: str = "degrading",
        trend_strength: float = 0.75,
        trend_confidence: float = 0.9,
        trend_signal_count: int = 4,
    ):
        module = self.module
        return module.TrendContext(
            trend_id=module.create_trend_id(domain, trend_direction, "7d"),
            domain=domain,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            trend_window="7d",
            trend_confidence=trend_confidence,
            trend_signal_count=trend_signal_count,
            evidence_reference="trend://RUN-001/cpu",
            notes=None,
        )

    def anomaly_context(
        self,
        *,
        domain: str = "CPU",
        anomaly_pattern: str = "recurring",
        anomaly_count: int = 3,
        anomaly_severity: float = 0.8,
        anomaly_confidence: float = 0.85,
        recurrence_count: int = 2,
    ):
        module = self.module
        return module.AnomalyContext(
            anomaly_id=module.create_anomaly_id(domain, anomaly_pattern, recurrence_count),
            domain=domain,
            anomaly_count=anomaly_count,
            anomaly_severity=anomaly_severity,
            anomaly_confidence=anomaly_confidence,
            anomaly_pattern=anomaly_pattern,
            recurrence_count=recurrence_count,
            evidence_reference="anomaly://RUN-001/cpu",
            notes=None,
        )

    def scoring_input(
        self,
        *,
        domain: str = "CPU",
        baseline_score: float = 50.0,
        trend_context=None,
        anomaly_context=None,
        run_id: str | None = "RUN-001",
        awr_id: str | None = None,
        runtime_influence: bool = False,
        runtime_active: bool = False,
    ):
        module = self.module
        if trend_context is None:
            trend_context = self.trend_context(domain=domain)
        if anomaly_context is None:
            anomaly_context = self.anomaly_context(domain=domain)
        return module.TrendAwareScoringInput(
            input_id=module.create_trend_aware_input_id(run_id, awr_id, domain, "7U.1"),
            run_id=run_id,
            awr_id=awr_id,
            domain=domain,
            baseline_score=baseline_score,
            trend_context=trend_context,
            anomaly_context=anomaly_context,
            feature_reference="feature://RUN-001/cpu",
            score_version="7U.1",
            runtime_influence=runtime_influence,
            runtime_active=runtime_active,
        )

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.trend_aware_scoring")
        self.assertEqual(before_environment, dict(os.environ))

        imports = imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )
        self.assertNotIn("uuid", imports)
        self.assertNotIn("datetime", imports)
        self.assertFalse(hasattr(module, "learned_model"))
        self.assertFalse(hasattr(module, "score_ml"))
        self.assertFalse(hasattr(module, "train_model"))

    def test_docs_exist(self) -> None:
        self.assertTrue(SCORING_DOC.is_file(), SCORING_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        combined = f"{read_text(SCORING_DOC)}\n{read_text(MODEL_DOC)}"
        lower = combined.lower()
        for phrase in (
            "score(x, t)",
            "advisory/shadow only",
            "deterministic scoring remains authoritative",
            "no runtime scoring changes are applied",
            "learned_model(x) is not implemented",
            "score_ml(x) is not implemented",
            "no model training is implemented",
            "no phase 8 sizing/tco is implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, lower)

    def test_docs_contain_required_sections(self) -> None:
        scoring_text = read_text(SCORING_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Scope",
            "## 3. Non-Goals",
            "## 4. Score(x, t) Concept",
            "## 5. Baseline Deterministic Score",
            "## 6. Trend Context",
            "## 7. Anomaly Context",
            "## 8. Trend-Aware Score Result",
            "## 9. Advisory / Shadow Boundary",
            "## 10. Runtime Influence Boundary",
            "## 11. Deterministic Runtime Boundary",
            "## 12. Decision / Recommendation Boundary",
            "## 13. Parser Boundary",
            "## 14. Materialization Boundary",
            "## 15. ML Boundary",
            "## 16. Relationship to Phase 7S",
            "## 17. Relationship to Phase 7T",
            "## 18. Relationship to Future Phase 7V",
            "## 19. Relationship to Future Phase 7W",
            "## 20. Relationship to Future Phase 8",
            "## 21. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, scoring_text)

        model_text = read_text(MODEL_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. TrendContext Object Shape",
            "## 3. AnomalyContext Object Shape",
            "## 4. TrendAwareScoringInput Object Shape",
            "## 5. TrendAwareScoreResult Object Shape",
            "## 6. Supported Domains",
            "## 7. Supported Trend Directions",
            "## 8. Supported Anomaly Patterns",
            "## 9. Advisory Statuses",
            "## 10. Scoring Rules",
            "## 11. Confidence Rules",
            "## 12. Validation Rules",
            "## 13. Serialization Rules",
            "## 14. Runtime Boundary",
            "## 15. Non-Goals",
            "## 16. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, model_text)

    def test_supported_domains(self) -> None:
        module = self.module
        self.assertEqual(module.DOMAIN_NAMES, ("CPU", "IO", "MEMORY", "COMMIT", "RAC", "ADG"))
        for domain in ("CPU", "IO", "MEMORY", "COMMIT", "RAC", "ADG"):
            with self.subTest(domain=domain):
                context = self.trend_context(domain=domain)
                self.assertEqual(module.validate_trend_context(context).domain, domain)

        io_context = self.trend_context(domain="I/O")
        self.assertEqual(io_context.domain, "IO")
        with self.assertRaises(module.TrendAwareScoringError):
            self.trend_context(domain="NETWORK")

    def test_trend_context_validation(self) -> None:
        module = self.module
        context = self.trend_context()
        self.assertEqual(module.validate_trend_context(context).trend_direction, "degrading")

        with self.assertRaises(module.TrendAwareScoringError):
            self.trend_context(trend_direction="unsupported")
        with self.assertRaises(module.TrendAwareScoringError):
            self.trend_context(trend_strength=1.1)
        with self.assertRaises(module.TrendAwareScoringError):
            self.trend_context(trend_strength=-0.1)
        with self.assertRaises(module.TrendAwareScoringError):
            self.trend_context(trend_confidence=1.1)
        with self.assertRaises(module.TrendAwareScoringError):
            self.trend_context(trend_confidence=-0.1)
        with self.assertRaises(module.TrendAwareScoringError):
            self.trend_context(trend_signal_count=-1)

    def test_anomaly_context_validation(self) -> None:
        module = self.module
        context = self.anomaly_context()
        self.assertEqual(module.validate_anomaly_context(context).anomaly_pattern, "recurring")

        with self.assertRaises(module.TrendAwareScoringError):
            self.anomaly_context(anomaly_pattern="unsupported")
        with self.assertRaises(module.TrendAwareScoringError):
            self.anomaly_context(anomaly_severity=1.1)
        with self.assertRaises(module.TrendAwareScoringError):
            self.anomaly_context(anomaly_severity=-0.1)
        with self.assertRaises(module.TrendAwareScoringError):
            self.anomaly_context(anomaly_confidence=1.1)
        with self.assertRaises(module.TrendAwareScoringError):
            self.anomaly_context(anomaly_confidence=-0.1)
        with self.assertRaises(module.TrendAwareScoringError):
            self.anomaly_context(anomaly_count=-1)
        with self.assertRaises(module.TrendAwareScoringError):
            self.anomaly_context(recurrence_count=-1)

    def test_input_validation(self) -> None:
        module = self.module
        record = self.scoring_input()
        self.assertEqual(
            module.validate_trend_aware_scoring_input(record).baseline_score,
            50.0,
        )

        with self.assertRaises(module.TrendAwareScoringError):
            self.scoring_input(baseline_score=100.1)
        with self.assertRaises(module.TrendAwareScoringError):
            self.scoring_input(baseline_score=-0.1)
        with self.assertRaises(module.TrendAwareScoringError):
            self.scoring_input(run_id=None, awr_id=None)
        with self.assertRaises(module.TrendAwareScoringError):
            self.scoring_input(runtime_influence=True)
        with self.assertRaises(module.TrendAwareScoringError):
            self.scoring_input(runtime_active=True)
        with self.assertRaises(module.TrendAwareScoringError):
            self.scoring_input(
                domain="CPU",
                trend_context=self.trend_context(domain="IO"),
            )

    def test_scoring_behavior(self) -> None:
        module = self.module
        improving = module.compute_trend_aware_score(
            self.scoring_input(
                baseline_score=50.0,
                trend_context=self.trend_context(trend_direction="improving"),
                anomaly_context=self.anomaly_context(
                    anomaly_pattern="none",
                    anomaly_count=0,
                    anomaly_severity=0.0,
                    anomaly_confidence=0.9,
                    recurrence_count=0,
                ),
            )
        )
        self.assertLessEqual(improving.trend_aware_score, improving.baseline_score)

        degrading = module.compute_trend_aware_score(
            self.scoring_input(
                baseline_score=50.0,
                trend_context=self.trend_context(trend_direction="degrading"),
                anomaly_context=self.anomaly_context(
                    anomaly_pattern="none",
                    anomaly_count=0,
                    anomaly_severity=0.0,
                    anomaly_confidence=0.9,
                    recurrence_count=0,
                ),
            )
        )
        self.assertGreater(degrading.trend_aware_score, degrading.baseline_score)

        recurring = module.compute_trend_aware_score(
            self.scoring_input(
                baseline_score=50.0,
                trend_context=self.trend_context(trend_direction="stable", trend_strength=0.0),
                anomaly_context=self.anomaly_context(anomaly_pattern="recurring"),
            )
        )
        self.assertGreater(recurring.trend_aware_score, recurring.baseline_score)

        severe = module.compute_trend_aware_score(
            self.scoring_input(
                baseline_score=50.0,
                trend_context=self.trend_context(trend_direction="stable", trend_strength=0.0),
                anomaly_context=self.anomaly_context(anomaly_pattern="severe"),
            )
        )
        self.assertGreater(severe.trend_aware_score, severe.baseline_score)

        insufficient = module.compute_trend_aware_score(
            self.scoring_input(
                baseline_score=50.0,
                trend_context=self.trend_context(
                    trend_direction="insufficient_data",
                    trend_strength=0.0,
                    trend_confidence=0.2,
                    trend_signal_count=0,
                ),
                anomaly_context=self.anomaly_context(
                    anomaly_pattern="insufficient_data",
                    anomaly_count=0,
                    anomaly_severity=0.0,
                    anomaly_confidence=0.2,
                    recurrence_count=0,
                ),
            )
        )
        self.assertEqual(insufficient.advisory_status, "INSUFFICIENT_CONTEXT")
        self.assertLess(insufficient.confidence, recurring.confidence)

        clamped_high = module.compute_trend_aware_score(
            self.scoring_input(baseline_score=99.0)
        )
        self.assertLessEqual(clamped_high.trend_aware_score, 100.0)

        clamped_low = module.compute_trend_aware_score(
            self.scoring_input(
                baseline_score=1.0,
                trend_context=self.trend_context(
                    trend_direction="improving",
                    trend_strength=1.0,
                    trend_confidence=1.0,
                ),
                anomaly_context=self.anomaly_context(
                    anomaly_pattern="none",
                    anomaly_count=0,
                    anomaly_severity=0.0,
                    anomaly_confidence=1.0,
                    recurrence_count=0,
                ),
            )
        )
        self.assertGreaterEqual(clamped_low.trend_aware_score, 0.0)
        self.assertLessEqual(clamped_high.confidence, 0.95)
        self.assertIn("deterministic runtime remains authoritative", degrading.explanation)

    def test_result_safety(self) -> None:
        module = self.module
        result = module.compute_trend_aware_score(self.scoring_input())
        self.assertFalse(result.runtime_influence)
        self.assertFalse(result.runtime_active)
        self.assertTrue(result.deterministic_runtime_remains_authoritative)
        self.assertNotEqual(result.advisory_status, "RUNTIME_ACTIVE")

        data = module.trend_aware_score_result_to_dict(result)
        data["runtime_influence"] = True
        with self.assertRaises(module.TrendAwareScoringError):
            module.trend_aware_score_result_from_dict(data)

    def test_serialization_round_trips(self) -> None:
        module = self.module
        trend = self.trend_context()
        trend_round_trip = module.trend_context_from_dict(module.trend_context_to_dict(trend))
        self.assertEqual(trend, trend_round_trip)

        anomaly = self.anomaly_context()
        anomaly_round_trip = module.anomaly_context_from_dict(
            module.anomaly_context_to_dict(anomaly)
        )
        self.assertEqual(anomaly, anomaly_round_trip)

        input_record = self.scoring_input()
        input_round_trip = module.trend_aware_input_from_dict(
            module.trend_aware_input_to_dict(input_record)
        )
        self.assertEqual(input_record, input_round_trip)

        result = module.compute_trend_aware_score(input_record)
        result_data = module.trend_aware_score_result_to_dict(result)
        result_round_trip = module.trend_aware_score_result_from_dict(result_data)
        self.assertEqual(result, result_round_trip)

        serialized_a = json.dumps(result_data, sort_keys=True, separators=(",", ":"))
        serialized_b = json.dumps(
            module.trend_aware_score_result_to_dict(result_round_trip),
            sort_keys=True,
            separators=(",", ":"),
        )
        self.assertEqual(serialized_a, serialized_b)

    def test_deterministic_ids(self) -> None:
        module = self.module
        ids_a = (
            module.create_trend_id("CPU", "degrading", "7d"),
            module.create_anomaly_id("CPU", "recurring", 2),
            module.create_trend_aware_input_id("RUN-001", None, "CPU", "7U.1"),
            module.create_trend_aware_result_id("INPUT-001", "7U.1"),
        )
        ids_b = (
            module.create_trend_id("CPU", "degrading", "7d"),
            module.create_anomaly_id("CPU", "recurring", 2),
            module.create_trend_aware_input_id("RUN-001", None, "CPU", "7U.1"),
            module.create_trend_aware_result_id("INPUT-001", "7U.1"),
        )
        self.assertEqual(ids_a, ids_b)

        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        for identifier in ids_a:
            with self.subTest(identifier=identifier):
                self.assertIsNone(uuid_pattern.match(identifier))
                self.assertNotIn("2026", identifier)

    def test_no_runtime_mutation_functions(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden_name in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(function_name=forbidden_name):
                self.assertNotIn(forbidden_name, names)

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        self.assertNotIn("src.learning.trend_aware_scoring", run_analysis_imports)
        self.assertNotIn("learning.trend_aware_scoring", run_analysis_imports)
        self.assertNotIn("trend_aware_scoring", run_analysis_imports)

        for path in python_files(RUNTIME_PATHS):
            imports = imported_modules(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.trend_aware_scoring", imports)
                self.assertNotIn("learning.trend_aware_scoring", imports)
                self.assertNotIn("trend_aware_scoring", imports)

    def test_existing_phase7_validation_entrypoints_still_exist(self) -> None:
        for relative_path in (
            "tests/test_phase7_ml_adaptive_scoring_boundary.py",
            "tests/test_phase7_feature_label_dataset.py",
            "scripts/run_phase7_materialization_validation.py",
            "scripts/run_phase7_materialization_readiness_check.py",
            "scripts/run_phase7_validation.py",
            "scripts/run_phase7_readiness_check.py",
            "scripts/run_phase7h_dashboard_validation.py",
            "scripts/awr_memory_cli.py",
            "scripts/run_phase6_validation.py",
        ):
            with self.subTest(relative_path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file(), relative_path)


if __name__ == "__main__":
    unittest.main()
