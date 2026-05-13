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
HARNESS_DOC = DOCS / "phase7_ml_training_backtesting.md"
MODEL_DOC = DOCS / "phase7_ml_backtesting_model.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "ml_training_backtesting.py"

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
    "numpy",
    "src.parser",
    "src.scoring",
    "src.decision",
    "src.recommendation",
    "src.recommendations",
    "src.reporting",
    "src.memory",
)

FORBIDDEN_FUNCTION_NAMES = (
    "activate_model",
    "deploy_model",
    "save_model",
    "load_model",
    "update_runtime_scoring",
    "replace_scoring_engine",
    "apply_ml_score",
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


class Phase7MLTrainingBacktestingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = importlib.import_module("src.learning.ml_training_backtesting")
        cls.dataset_module = importlib.import_module("src.learning.feature_label_dataset")

    def feature_record(
        self,
        *,
        run_id: str = "RUN-001",
        feature_name: str = "db_time_per_sec",
        feature_value: object = 42.5,
        feature_type: str = "numeric",
        feature_schema_version: str = "7T.1",
    ):
        module = self.dataset_module
        return module.FeatureRecord(
            feature_id=module.create_feature_id(
                run_id,
                None,
                feature_name,
                feature_schema_version,
            ),
            run_id=run_id,
            awr_id=None,
            feature_name=feature_name,
            feature_domain="workload",
            feature_value=feature_value,
            feature_type=feature_type,
            source_component="deterministic_feature_snapshot",
            source_metric=feature_name,
            feature_schema_version=feature_schema_version,
            evidence_reference=f"awr://{run_id}/features/{feature_name}",
            created_at=None,
            notes=None,
        )

    def label_record(
        self,
        *,
        run_id: str = "RUN-001",
        label_name: str = "tuning_success",
        label_value: object = True,
        label_type: str = "binary",
        label_schema_version: str = "7T.1",
    ):
        module = self.dataset_module
        return module.LabelRecord(
            label_id=module.create_label_id(
                run_id,
                None,
                label_name,
                label_schema_version,
            ),
            run_id=run_id,
            awr_id=None,
            label_name=label_name,
            label_value=label_value,
            label_type=label_type,
            outcome_source="governed_feedback",
            source_record_id=f"FB-{run_id}",
            label_schema_version=label_schema_version,
            confidence=0.9,
            evidence_reference=f"feedback://{run_id}",
            reviewed_by="reviewer@example.com",
            created_at=None,
            notes=None,
        )

    def dataset(
        self,
        *,
        label_values: list[object] | None = None,
        label_name: str = "tuning_success",
        label_type: str = "binary",
    ):
        dataset_module = self.dataset_module
        label_values = [True, True, False, True, False] if label_values is None else label_values
        features = []
        labels = []
        source_records = []
        for index, label_value in enumerate(label_values, start=1):
            run_id = f"RUN-{index:03d}"
            features.append(
                self.feature_record(
                    run_id=run_id,
                    feature_name="db_time_per_sec",
                    feature_value=40.0 + index,
                )
            )
            features.append(
                self.feature_record(
                    run_id=run_id,
                    feature_name="deterministic_score",
                    feature_value=60.0 + index,
                )
            )
            labels.append(
                self.label_record(
                    run_id=run_id,
                    label_name=label_name,
                    label_value=label_value,
                    label_type=label_type,
                )
            )
            source_records.append(
                {
                    "record_id": run_id,
                    "record_type": "awr_snapshot",
                    "created_at": f"2025-01-{index:02d}T00:00:00Z",
                    "deterministic_score": 60.0 + index,
                    "trend_aware_score": 61.0 + index,
                    "shadow_ml_score": 62.0 + index,
                }
            )
        dataset = dataset_module.FeatureLabelDataset(
            dataset_id=dataset_module.create_dataset_id(
                "phase7w_sample",
                "7T.1",
                "7T.1",
            ),
            dataset_name="phase7w_sample",
            feature_schema_version="7T.1",
            label_schema_version="7T.1",
            features=features,
            labels=labels,
            source_records=source_records,
            dataset_purpose="governed Phase 7W local dataset test fixture",
            created_by="unit-test",
            created_at=None,
            validation_status=dataset_module.PROPOSED,
            validation_notes=[],
            train_split_reference=None,
            test_split_reference=None,
            runtime_influence=False,
            runtime_active=False,
        )
        return dataset_module.validate_feature_label_dataset(dataset)

    def training_setup(self):
        module = self.module
        dataset = self.dataset()
        split = module.create_dataset_split(dataset)
        plan = module.create_training_plan(
            dataset,
            "baseline_majority",
            "tuning_success",
            created_by="unit-test",
        )
        result = module.run_baseline_training(plan, dataset, split)
        return dataset, split, plan, result

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.ml_training_backtesting")
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
        self.assertTrue(HARNESS_DOC.is_file(), HARNESS_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        combined = f"{read_text(HARNESS_DOC)}\n{read_text(MODEL_DOC)}"
        lower = combined.lower()
        for phrase in (
            "training/backtesting artifacts are evaluation records only",
            "no real ml framework is required",
            "no model is runtime active",
            "backtesting success is not runtime activation",
            "deterministic scoring remains authoritative",
            "no runtime scoring changes are applied",
            "phase 8 sizing/tco is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, lower)

    def test_docs_contain_required_sections(self) -> None:
        harness_text = read_text(HARNESS_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Scope",
            "## 3. Non-Goals",
            "## 4. Training / Backtesting Is Not Runtime Activation",
            "## 5. Dataset Inputs",
            "## 6. Dataset Split Model",
            "## 7. Training Plan Model",
            "## 8. Training Result Model",
            "## 9. Backtest Result Model",
            "## 10. Supported Model Families",
            "## 11. Supported Split Strategies",
            "## 12. Metrics",
            "## 13. Runtime Influence Boundary",
            "## 14. Deterministic Runtime Boundary",
            "## 15. Relationship to Phase 7S",
            "## 16. Relationship to Phase 7T",
            "## 17. Relationship to Phase 7U",
            "## 18. Relationship to Phase 7V",
            "## 19. Relationship to Future Phase 7X",
            "## 20. Relationship to Future Phase 7Y",
            "## 21. Relationship to Future Phase 7Z",
            "## 22. Relationship to Phase 8",
            "## 23. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, harness_text)

        model_text = read_text(MODEL_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. DatasetSplit Object Shape",
            "## 3. MLTrainingPlan Object Shape",
            "## 4. MLTrainingResult Object Shape",
            "## 5. MLBacktestResult Object Shape",
            "## 6. Supported Model Families",
            "## 7. Split Strategies",
            "## 8. Metric Rules",
            "## 9. Statuses",
            "## 10. Serialization Rules",
            "## 11. Deterministic ID Rules",
            "## 12. Runtime Boundary",
            "## 13. Non-Goals",
            "## 14. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, model_text)

    def test_readme_links_phase7w_docs(self) -> None:
        text = read_text(README)
        for title, filename in (
            (
                "Phase 7W ML Training / Backtesting Harness",
                "phase7_ml_training_backtesting.md",
            ),
            ("Phase 7W ML Backtesting Model", "phase7_ml_backtesting_model.md"),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)

    def test_split_creation(self) -> None:
        module = self.module
        dataset = self.dataset()
        split_a = module.create_dataset_split(dataset)
        split_b = module.create_dataset_split(dataset)

        self.assertEqual(split_a, split_b)
        self.assertEqual(
            split_a.split_id,
            module.create_split_id(
                dataset.dataset_id,
                "deterministic_holdout",
                None,
            ),
        )
        self.assertFalse(set(split_a.train_record_ids) & set(split_a.test_record_ids))
        self.assertIn("RUN-005", split_a.test_record_ids)

        seeded_a = module.create_dataset_split(dataset, split_seed=17)
        seeded_b = module.create_dataset_split(dataset, split_seed=17)
        self.assertEqual(seeded_a, seeded_b)
        self.assertEqual(seeded_a.split_seed, 17)

        with self.assertRaises(module.MLTrainingBacktestingError):
            module.create_dataset_split(dataset, split_strategy="random")

    def test_training_plan_validation(self) -> None:
        module = self.module
        dataset = self.dataset()
        plan = module.create_training_plan(
            dataset,
            "baseline_majority",
            "tuning_success",
            created_by="unit-test",
        )
        self.assertEqual(module.validate_training_plan(plan), plan)
        self.assertFalse(plan.runtime_influence)
        self.assertFalse(plan.runtime_active)

        with self.assertRaises(module.MLTrainingBacktestingError):
            module.create_training_plan(dataset, "svm", "tuning_success")

        plan_data = module.training_plan_to_dict(plan)
        plan_data["runtime_influence"] = True
        with self.assertRaises(module.MLTrainingBacktestingError):
            module.training_plan_from_dict(plan_data)

        plan_data = module.training_plan_to_dict(plan)
        plan_data["runtime_active"] = True
        with self.assertRaises(module.MLTrainingBacktestingError):
            module.training_plan_from_dict(plan_data)

    def test_baseline_majority_training(self) -> None:
        module = self.module
        dataset, split, plan, result = self.training_setup()

        self.assertEqual(result.training_status, "TRAINED")
        self.assertEqual(result.training_id, module.create_training_id(plan.training_plan_id, split.split_id))
        self.assertEqual(result.metrics["accuracy"], 0.75)
        self.assertEqual(result.metrics["baseline_accuracy"], 0.75)
        self.assertEqual(result.metrics["precision"], 0.75)
        self.assertEqual(result.metrics["recall"], 1.0)
        self.assertFalse(result.runtime_active)
        self.assertFalse(result.runtime_influence_granted)
        self.assertTrue(result.deterministic_runtime_remains_authoritative)

        self.assertEqual(dataset.dataset_id, result.dataset_id)

    def test_baseline_numeric_mean_training(self) -> None:
        module = self.module
        dataset = self.dataset(
            label_values=[10.0, 12.0, 14.0, 16.0, 18.0],
            label_name="performance_improved",
            label_type="numeric",
        )
        split = module.create_dataset_split(dataset)
        plan = module.create_training_plan(
            dataset,
            "baseline_numeric_mean",
            "performance_improved",
        )
        result = module.run_baseline_training(plan, dataset, split)

        self.assertEqual(result.training_status, "TRAINED")
        self.assertEqual(result.metrics["mean_absolute_error"], 2.0)
        self.assertFalse(result.runtime_active)
        self.assertFalse(result.runtime_influence_granted)

    def test_insufficient_data_training(self) -> None:
        module = self.module
        dataset = self.dataset()
        split = module.create_dataset_split(dataset)
        plan = module.create_training_plan(
            dataset,
            "baseline_majority",
            "risk_confirmed",
        )
        result = module.run_baseline_training(plan, dataset, split)

        self.assertEqual(result.training_status, "INSUFFICIENT_DATA")
        self.assertEqual(result.insufficient_label_count, len(split.train_record_ids))
        self.assertFalse(result.runtime_active)
        self.assertFalse(result.runtime_influence_granted)

    def test_backtesting(self) -> None:
        module = self.module
        dataset, split, _plan, result = self.training_setup()
        backtest = module.run_backtest(result, dataset, split)

        self.assertEqual(backtest.backtest_id, module.create_backtest_id(result.training_id, split.split_id))
        self.assertEqual(backtest.backtest_status, "BACKTESTED")
        self.assertEqual(backtest.test_record_count, 1)
        self.assertEqual(backtest.disagreement_count, 1)
        self.assertEqual(backtest.metrics["accuracy"], 0.0)
        self.assertEqual(backtest.metrics["disagreement_rate"], 1.0)
        self.assertEqual(
            backtest.baseline_comparison["score_reference_summary"][
                "deterministic_score_available_count"
            ],
            2,
        )
        self.assertFalse(backtest.runtime_active)
        self.assertFalse(backtest.runtime_influence_granted)
        self.assertTrue(backtest.deterministic_runtime_remains_authoritative)

    def test_validation_rejects_invalid_metrics_statuses_and_runtime_flags(self) -> None:
        module = self.module
        dataset, split, _plan, result = self.training_setup()

        result_data = module.training_result_to_dict(result)
        result_data["metrics"] = {"accuracy": -0.1}
        with self.assertRaises(module.MLTrainingBacktestingError):
            module.training_result_from_dict(result_data)

        result_data = module.training_result_to_dict(result)
        result_data["training_status"] = "ACTIVE"
        with self.assertRaises(module.MLTrainingBacktestingError):
            module.training_result_from_dict(result_data)

        result_data = module.training_result_to_dict(result)
        result_data["runtime_active"] = True
        with self.assertRaises(module.MLTrainingBacktestingError):
            module.training_result_from_dict(result_data)

        result_data = module.training_result_to_dict(result)
        result_data["runtime_influence_granted"] = True
        with self.assertRaises(module.MLTrainingBacktestingError):
            module.training_result_from_dict(result_data)

        backtest = module.run_backtest(result, dataset, split)
        backtest_data = module.backtest_result_to_dict(backtest)
        backtest_data["backtest_status"] = "ACTIVE"
        with self.assertRaises(module.MLTrainingBacktestingError):
            module.backtest_result_from_dict(backtest_data)

        backtest_data = module.backtest_result_to_dict(backtest)
        backtest_data["deterministic_runtime_remains_authoritative"] = False
        with self.assertRaises(module.MLTrainingBacktestingError):
            module.backtest_result_from_dict(backtest_data)

    def test_serialization_round_trips(self) -> None:
        module = self.module
        dataset, split, plan, result = self.training_setup()
        backtest = module.run_backtest(result, dataset, split)

        split_round_trip = module.dataset_split_from_dict(module.dataset_split_to_dict(split))
        plan_round_trip = module.training_plan_from_dict(module.training_plan_to_dict(plan))
        result_round_trip = module.training_result_from_dict(module.training_result_to_dict(result))
        backtest_round_trip = module.backtest_result_from_dict(
            module.backtest_result_to_dict(backtest)
        )

        self.assertEqual(split, split_round_trip)
        self.assertEqual(plan, plan_round_trip)
        self.assertEqual(result, result_round_trip)
        self.assertEqual(backtest, backtest_round_trip)

        serialized_a = json.dumps(
            module.backtest_result_to_dict(backtest),
            sort_keys=True,
            separators=(",", ":"),
        )
        serialized_b = json.dumps(
            module.backtest_result_to_dict(backtest_round_trip),
            sort_keys=True,
            separators=(",", ":"),
        )
        self.assertEqual(serialized_a, serialized_b)

    def test_deterministic_ids(self) -> None:
        module = self.module
        dataset = self.dataset()
        split_id_a = module.create_split_id(dataset.dataset_id, "deterministic_holdout")
        split_id_b = module.create_split_id(dataset.dataset_id, "deterministic_holdout")
        plan_id_a = module.create_training_plan_id(
            dataset.dataset_id,
            "baseline_majority",
            "tuning_success",
        )
        plan_id_b = module.create_training_plan_id(
            dataset.dataset_id,
            "baseline_majority",
            "tuning_success",
        )
        training_id_a = module.create_training_id(plan_id_a, split_id_a)
        training_id_b = module.create_training_id(plan_id_b, split_id_b)
        backtest_id_a = module.create_backtest_id(training_id_a, split_id_a)
        backtest_id_b = module.create_backtest_id(training_id_b, split_id_b)

        self.assertEqual(split_id_a, split_id_b)
        self.assertEqual(plan_id_a, plan_id_b)
        self.assertEqual(training_id_a, training_id_b)
        self.assertEqual(backtest_id_a, backtest_id_b)

        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        for identifier in (split_id_a, plan_id_a, training_id_a, backtest_id_a):
            with self.subTest(identifier=identifier):
                self.assertIsNone(uuid_pattern.match(identifier))
                self.assertNotIn("2026", identifier)

    def test_no_active_ml_runtime_functions(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden_name in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(function_name=forbidden_name):
                self.assertNotIn(forbidden_name, names)

    def test_runtime_import_isolation(self) -> None:
        for path in python_files(RUNTIME_PATHS):
            text = read_text(path)
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotIn("ml_training_backtesting", text)

    def test_existing_phase_ml_modules_still_import(self) -> None:
        for module_name in (
            "src.learning.ml_boundary",
            "src.learning.feature_label_dataset",
            "src.learning.trend_aware_scoring",
            "src.learning.shadow_ml_model_interface",
        ):
            with self.subTest(module=module_name):
                importlib.import_module(module_name)


if __name__ == "__main__":
    unittest.main()
