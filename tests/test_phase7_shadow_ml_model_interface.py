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
INTERFACE_DOC = DOCS / "phase7_shadow_ml_model_interface.md"
OUTPUT_DOC = DOCS / "phase7_shadow_ml_output_model.md"
MODULE_PATH = ROOT / "src" / "learning" / "shadow_ml_model_interface.py"

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
    "xgboost",
    "lightgbm",
    "catboost",
    "src.parser",
    "src.scoring",
    "src.decision",
    "src.recommendation",
    "src.recommendations",
    "src.reporting",
    "src.memory",
)

FORBIDDEN_FUNCTION_NAMES = (
    "train_model",
    "fit_model",
    "learned_model",
    "activate_model",
    "load_model",
    "save_model",
    "update_runtime_scoring",
    "replace_scoring_engine",
    "auto_apply",
    "autonomous_apply",
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


class Phase7ShadowMLModelInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = importlib.import_module("src.learning.shadow_ml_model_interface")

    def metadata(
        self,
        *,
        model_family: str = "baseline_mock",
        model_version: str = "7V.1",
        feature_schema_version: str | None = "7T.1",
        label_schema_version: str | None = "7T.1",
        runtime_active: bool = False,
        runtime_influence_granted: bool = False,
    ):
        module = self.module
        model_id = module.create_shadow_model_id(
            model_family,
            model_version,
            feature_schema_version,
            label_schema_version,
        )
        return module.ShadowModelMetadata(
            model_id=model_id,
            model_family=model_family,
            model_version=model_version,
            feature_schema_version=feature_schema_version,
            label_schema_version=label_schema_version,
            training_reference="training://not-implemented",
            validation_reference="validation://shadow-fixture",
            runtime_active=runtime_active,
            runtime_influence_granted=runtime_influence_granted,
            notes="unit test metadata",
        )

    def shadow_input(
        self,
        *,
        metadata=None,
        run_id: str | None = "RUN-001",
        awr_id: str | None = None,
        deterministic_score: float = 62.0,
        trend_aware_score: float | None = 68.0,
        feature_values: dict[str, object] | None = None,
        runtime_influence: bool = False,
        runtime_active: bool = False,
    ):
        module = self.module
        metadata = self.metadata() if metadata is None else metadata
        feature_values = (
            {
                "cpu_risk": 0.82,
                "io_wait_pressure": 71.0,
                "db_time_per_sec": 42.5,
            }
            if feature_values is None
            else feature_values
        )
        return module.ShadowMLInput(
            input_id=module.create_shadow_ml_input_id(
                run_id,
                awr_id,
                metadata.model_id,
                "7V.1",
            ),
            run_id=run_id,
            awr_id=awr_id,
            feature_reference="feature://RUN-001/shadow",
            dataset_reference="dataset://phase7t/sample",
            deterministic_score=deterministic_score,
            trend_aware_score=trend_aware_score,
            feature_values=feature_values,
            model_id=metadata.model_id,
            score_version="7V.1",
            runtime_influence=runtime_influence,
            runtime_active=runtime_active,
        )

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.shadow_ml_model_interface")
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
        for forbidden_name in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(function_name=forbidden_name):
                self.assertFalse(hasattr(module, forbidden_name))

    def test_docs_exist(self) -> None:
        self.assertTrue(INTERFACE_DOC.is_file(), INTERFACE_DOC)
        self.assertTrue(OUTPUT_DOC.is_file(), OUTPUT_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        combined = f"{read_text(INTERFACE_DOC)}\n{read_text(OUTPUT_DOC)}"
        lower = combined.lower()
        for phrase in (
            "score_ml(x) exists only as a shadow interface/result contract",
            "no real ml model is implemented",
            "no training is implemented",
            "no learned_model(x) is implemented",
            "no model registry is implemented",
            "shadow ml is non-authoritative",
            "deterministic scoring remains authoritative",
            "shadow output does not change runtime scoring",
            "runtime_influence=false",
            "runtime_active=false",
            "runtime_influence_granted=false",
            "phase 8 sizing/tco is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, lower)

    def test_docs_contain_required_sections(self) -> None:
        interface_text = read_text(INTERFACE_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Scope",
            "## 3. Non-Goals",
            "## 4. Score_ml(x) Shadow Interface Concept",
            "## 5. Shadow Model Metadata",
            "## 6. Shadow ML Input",
            "## 7. Shadow ML Output",
            "## 8. Placeholder Shadow Score",
            "## 9. Deterministic Runtime Boundary",
            "## 10. Runtime Influence Boundary",
            "## 11. Relationship to Deterministic Score",
            "## 12. Relationship to Trend-Aware Score",
            "## 13. Relationship to Feature / Label Dataset",
            "## 14. Relationship to Phase 7S Boundary",
            "## 15. Relationship to Future Phase 7W Training / Backtesting",
            "## 16. Relationship to Future Phase 7X Explainability",
            "## 17. Relationship to Future Phase 7Y Model Registry",
            "## 18. Relationship to Future Phase 8",
            "## 19. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, interface_text)

        output_text = read_text(OUTPUT_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. ShadowModelMetadata Object Shape",
            "## 3. ShadowMLInput Object Shape",
            "## 4. ShadowMLOutput Object Shape",
            "## 5. Supported Model Families",
            "## 6. Advisory Statuses",
            "## 7. Placeholder Scoring Rules",
            "## 8. Validation Rules",
            "## 9. Serialization Rules",
            "## 10. Deterministic ID Rules",
            "## 11. Runtime Boundary",
            "## 12. Non-Goals",
            "## 13. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, output_text)

    def test_supported_model_families(self) -> None:
        module = self.module
        self.assertEqual(
            module.SHADOW_MODEL_FAMILIES,
            (
                "tree",
                "neural_net",
                "hybrid_rule_ml",
                "linear",
                "baseline_mock",
                "external_placeholder",
            ),
        )
        for family in module.SHADOW_MODEL_FAMILIES:
            with self.subTest(family=family):
                metadata = self.metadata(model_family=family)
                self.assertEqual(
                    module.validate_shadow_model_metadata(metadata).model_family,
                    family,
                )

        with self.assertRaises(module.ShadowMLInterfaceError):
            module.create_shadow_model_id("unsupported", "7V.1")
        with self.assertRaises(module.ShadowMLInterfaceError):
            module.ShadowModelMetadata(
                model_id="SHADOW-MODEL-UNSUPPORTED",
                model_family="unsupported",
                model_version="7V.1",
                feature_schema_version=None,
                label_schema_version=None,
                training_reference=None,
                validation_reference=None,
                runtime_active=False,
                runtime_influence_granted=False,
                notes=None,
            )

    def test_metadata_validation(self) -> None:
        module = self.module
        metadata = self.metadata()
        self.assertEqual(module.validate_shadow_model_metadata(metadata), metadata)
        self.assertFalse(metadata.runtime_active)
        self.assertFalse(metadata.runtime_influence_granted)

        with self.assertRaises(module.ShadowMLInterfaceError):
            self.metadata(runtime_active=True)
        with self.assertRaises(module.ShadowMLInterfaceError):
            self.metadata(runtime_influence_granted=True)
        metadata_data = module.shadow_model_metadata_to_dict(metadata)
        metadata_data["runtime_influence"] = True
        with self.assertRaises(module.ShadowMLInterfaceError):
            module.shadow_model_metadata_from_dict(metadata_data)
        with self.assertRaises(module.ShadowMLInterfaceError):
            module.ShadowModelMetadata(
                model_id="SHADOW-MODEL-UNSUPPORTED",
                model_family="unsupported",
                model_version="7V.1",
                feature_schema_version=None,
                label_schema_version=None,
                training_reference=None,
                validation_reference=None,
                runtime_active=False,
                runtime_influence_granted=False,
                notes=None,
            )
        with self.assertRaises(module.ShadowMLInterfaceError):
            module.ShadowModelMetadata(
                model_id="SHADOW-MODEL-BASELINE-MOCK",
                model_family="baseline_mock",
                model_version="",
                feature_schema_version=None,
                label_schema_version=None,
                training_reference=None,
                validation_reference=None,
                runtime_active=False,
                runtime_influence_granted=False,
                notes=None,
            )

    def test_input_validation(self) -> None:
        module = self.module
        record = self.shadow_input()
        self.assertEqual(module.validate_shadow_ml_input(record), record)
        self.assertFalse(record.runtime_influence)
        self.assertFalse(record.runtime_active)

        with self.assertRaises(module.ShadowMLInterfaceError):
            self.shadow_input(run_id=None, awr_id=None)
        with self.assertRaises(module.ShadowMLInterfaceError):
            self.shadow_input(deterministic_score=100.1)
        with self.assertRaises(module.ShadowMLInterfaceError):
            self.shadow_input(deterministic_score=-0.1)
        with self.assertRaises(module.ShadowMLInterfaceError):
            self.shadow_input(trend_aware_score=100.1)
        with self.assertRaises(module.ShadowMLInterfaceError):
            self.shadow_input(trend_aware_score=-0.1)
        with self.assertRaises(module.ShadowMLInterfaceError):
            self.shadow_input(runtime_influence=True)
        with self.assertRaises(module.ShadowMLInterfaceError):
            self.shadow_input(runtime_active=True)
        with self.assertRaises(module.ShadowMLInterfaceError):
            self.shadow_input(feature_values=[])
        input_data = module.shadow_ml_input_to_dict(record)
        input_data["runtime_influence_granted"] = True
        with self.assertRaises(module.ShadowMLInterfaceError):
            module.shadow_ml_input_from_dict(input_data)

    def test_placeholder_shadow_scoring(self) -> None:
        module = self.module
        metadata = self.metadata()
        input_record = self.shadow_input(metadata=metadata)
        output_a = module.compute_placeholder_shadow_score(input_record, metadata)
        output_b = module.compute_placeholder_shadow_score(input_record, metadata)
        self.assertEqual(output_a, output_b)
        self.assertGreaterEqual(output_a.shadow_ml_score, 0.0)
        self.assertLessEqual(output_a.shadow_ml_score, 100.0)
        self.assertLessEqual(output_a.confidence, 0.95)
        self.assertIn(
            output_a.advisory_status,
            ("SHADOW_ONLY", "INSUFFICIENT_MODEL_CONTEXT"),
        )
        self.assertTrue(output_a.deterministic_runtime_remains_authoritative)
        self.assertFalse(output_a.runtime_influence)
        self.assertFalse(output_a.runtime_active)
        self.assertFalse(output_a.runtime_influence_granted)

        clamped_high = module.compute_placeholder_shadow_score(
            self.shadow_input(
                metadata=metadata,
                deterministic_score=99.0,
                trend_aware_score=100.0,
                feature_values={"cpu_risk": 100.0, "latency_pressure": 100.0},
            ),
            metadata,
        )
        self.assertLessEqual(clamped_high.shadow_ml_score, 100.0)

        insufficient = module.compute_placeholder_shadow_score(
            module.ShadowMLInput(
                input_id=module.create_shadow_ml_input_id(
                    "RUN-002",
                    None,
                    metadata.model_id,
                    "7V.1",
                ),
                run_id="RUN-002",
                awr_id=None,
                feature_reference=None,
                dataset_reference=None,
                deterministic_score=40.0,
                trend_aware_score=None,
                feature_values={},
                model_id=metadata.model_id,
                score_version="7V.1",
                runtime_influence=False,
                runtime_active=False,
            ),
            metadata,
        )
        self.assertEqual(insufficient.advisory_status, "INSUFFICIENT_MODEL_CONTEXT")
        self.assertLess(insufficient.confidence, output_a.confidence)

    def test_comparison(self) -> None:
        module = self.module
        comparison = module.compare_shadow_scores(
            deterministic_score=60.0,
            trend_aware_score=70.0,
            shadow_ml_score=65.0,
        )
        self.assertEqual(comparison["ml_delta_from_deterministic"], 5.0)
        self.assertEqual(comparison["ml_delta_from_trend_aware"], -5.0)

        missing_trend = module.compare_shadow_scores(
            deterministic_score=60.0,
            trend_aware_score=None,
            shadow_ml_score=65.0,
        )
        self.assertEqual(missing_trend["ml_delta_from_deterministic"], 5.0)
        self.assertIsNone(missing_trend["ml_delta_from_trend_aware"])
        self.assertIsNone(missing_trend["trend_aware_score"])

    def test_output_validation(self) -> None:
        module = self.module
        metadata = self.metadata()
        output = module.compute_placeholder_shadow_score(
            self.shadow_input(metadata=metadata),
            metadata,
        )
        self.assertEqual(module.validate_shadow_ml_output(output), output)
        self.assertFalse(output.runtime_influence)
        self.assertFalse(output.runtime_active)
        self.assertFalse(output.runtime_influence_granted)
        self.assertTrue(output.deterministic_runtime_remains_authoritative)

        for field_name in (
            "runtime_influence",
            "runtime_active",
            "runtime_influence_granted",
        ):
            data = module.shadow_ml_output_to_dict(output)
            data[field_name] = True
            with self.subTest(field_name=field_name):
                with self.assertRaises(module.ShadowMLInterfaceError):
                    module.shadow_ml_output_from_dict(data)

        data = module.shadow_ml_output_to_dict(output)
        data["deterministic_runtime_remains_authoritative"] = False
        with self.assertRaises(module.ShadowMLInterfaceError):
            module.shadow_ml_output_from_dict(data)

    def test_serialization_round_trips(self) -> None:
        module = self.module
        metadata = self.metadata()
        metadata_round_trip = module.shadow_model_metadata_from_dict(
            module.shadow_model_metadata_to_dict(metadata)
        )
        self.assertEqual(metadata, metadata_round_trip)

        input_record = self.shadow_input(metadata=metadata)
        input_round_trip = module.shadow_ml_input_from_dict(
            module.shadow_ml_input_to_dict(input_record)
        )
        self.assertEqual(input_record, input_round_trip)

        output = module.compute_placeholder_shadow_score(input_record, metadata)
        output_data = module.shadow_ml_output_to_dict(output)
        output_round_trip = module.shadow_ml_output_from_dict(output_data)
        self.assertEqual(output, output_round_trip)

        serialized_a = json.dumps(output_data, sort_keys=True, separators=(",", ":"))
        serialized_b = json.dumps(
            module.shadow_ml_output_to_dict(output_round_trip),
            sort_keys=True,
            separators=(",", ":"),
        )
        self.assertEqual(serialized_a, serialized_b)

    def test_deterministic_ids(self) -> None:
        module = self.module
        ids_a = (
            module.create_shadow_model_id("baseline_mock", "7V.1", "7T.1", "7T.1"),
            module.create_shadow_ml_input_id(
                "RUN-001",
                None,
                "SHADOW-MODEL-BASELINE-MOCK-7V-1-7T-1-7T-1",
                "7V.1",
            ),
            module.create_shadow_ml_output_id(
                "SHADOW-INPUT-RUN-001-MODEL-7V-1",
                "SHADOW-MODEL-BASELINE-MOCK-7V-1-7T-1-7T-1",
            ),
        )
        ids_b = (
            module.create_shadow_model_id("baseline_mock", "7V.1", "7T.1", "7T.1"),
            module.create_shadow_ml_input_id(
                "RUN-001",
                None,
                "SHADOW-MODEL-BASELINE-MOCK-7V-1-7T-1-7T-1",
                "7V.1",
            ),
            module.create_shadow_ml_output_id(
                "SHADOW-INPUT-RUN-001-MODEL-7V-1",
                "SHADOW-MODEL-BASELINE-MOCK-7V-1-7T-1-7T-1",
            ),
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

    def test_no_active_ml_training_functions(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden_name in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(function_name=forbidden_name):
                self.assertNotIn(forbidden_name, names)

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        self.assertNotIn(
            "src.learning.shadow_ml_model_interface",
            run_analysis_imports,
        )
        self.assertNotIn("learning.shadow_ml_model_interface", run_analysis_imports)
        self.assertNotIn("shadow_ml_model_interface", run_analysis_imports)

        for path in python_files(RUNTIME_PATHS):
            imports = imported_modules(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.shadow_ml_model_interface", imports)
                self.assertNotIn("learning.shadow_ml_model_interface", imports)
                self.assertNotIn("shadow_ml_model_interface", imports)

    def test_existing_phase7_validation_entrypoints_still_exist(self) -> None:
        for relative_path in (
            "tests/test_phase7_ml_adaptive_scoring_boundary.py",
            "tests/test_phase7_feature_label_dataset.py",
            "tests/test_phase7_trend_aware_scoring.py",
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
