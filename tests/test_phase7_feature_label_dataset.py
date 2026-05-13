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
DATASET_DOC = DOCS / "phase7_feature_label_dataset.md"
SCHEMA_DOC = DOCS / "phase7_feature_label_schema.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "feature_label_dataset.py"

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
    "train_model",
    "learned_model",
    "score_ml",
    "score_x_t",
    "apply_ml_score",
    "activate_model",
    "update_runtime_scoring",
    "replace_scoring_engine",
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


class Phase7FeatureLabelDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = importlib.import_module("src.learning.feature_label_dataset")

    def feature_record(
        self,
        *,
        run_id: str | None = "RUN-001",
        awr_id: str | None = None,
        feature_name: str = "db_time_per_sec",
        feature_value: object = 42.5,
        feature_type: str = "numeric",
        feature_schema_version: str = "7T.1",
    ):
        module = self.module
        return module.FeatureRecord(
            feature_id=module.create_feature_id(
                run_id,
                awr_id,
                feature_name,
                feature_schema_version,
            ),
            run_id=run_id,
            awr_id=awr_id,
            feature_name=feature_name,
            feature_domain="workload",
            feature_value=feature_value,
            feature_type=feature_type,
            source_component="deterministic_feature_snapshot",
            source_metric=feature_name,
            feature_schema_version=feature_schema_version,
            evidence_reference="awr://RUN-001/features/db_time_per_sec",
            created_at=None,
            notes=None,
        )

    def label_record(
        self,
        *,
        run_id: str | None = "RUN-001",
        awr_id: str | None = None,
        label_name: str = "tuning_success",
        label_value: object = True,
        label_type: str = "binary",
        label_schema_version: str = "7T.1",
        confidence: float = 0.9,
        outcome_source: str | None = "governed_feedback",
        source_record_id: str | None = "FB-001",
        evidence_reference: str | None = "feedback://FB-001",
    ):
        module = self.module
        return module.LabelRecord(
            label_id=module.create_label_id(
                run_id,
                awr_id,
                label_name,
                label_schema_version,
            ),
            run_id=run_id,
            awr_id=awr_id,
            label_name=label_name,
            label_value=label_value,
            label_type=label_type,
            outcome_source=outcome_source,
            source_record_id=source_record_id,
            label_schema_version=label_schema_version,
            confidence=confidence,
            evidence_reference=evidence_reference,
            reviewed_by="reviewer@example.com",
            created_at=None,
            notes=None,
        )

    def dataset(self, *, features=None, labels=None, runtime_influence=False, runtime_active=False):
        module = self.module
        features = [self.feature_record()] if features is None else features
        labels = [self.label_record()] if labels is None else labels
        return module.FeatureLabelDataset(
            dataset_id=module.create_dataset_id("phase7t_sample", "7T.1", "7T.1"),
            dataset_name="phase7t_sample",
            feature_schema_version="7T.1",
            label_schema_version="7T.1",
            features=features,
            labels=labels,
            source_records=[{"record_id": "RUN-001", "record_type": "awr_snapshot"}],
            dataset_purpose="governed Phase 7T local dataset test fixture",
            created_by="unit-test",
            created_at=None,
            validation_status=module.PROPOSED,
            validation_notes=[],
            train_split_reference=None,
            test_split_reference=None,
            runtime_influence=runtime_influence,
            runtime_active=runtime_active,
        )

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = importlib.import_module("src.learning.feature_label_dataset")
        self.assertEqual(before_environment, dict(os.environ))
        self.assertFalse(hasattr(module, "train_model"))

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

    def test_docs_exist(self) -> None:
        self.assertTrue(DATASET_DOC.is_file(), DATASET_DOC)
        self.assertTrue(SCHEMA_DOC.is_file(), SCHEMA_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        combined = f"{read_text(DATASET_DOC)}\n{read_text(SCHEMA_DOC)}"
        lower = combined.lower()
        for phrase in (
            "x = feature vectors",
            "y = observed outcomes",
            "dataset is not a model",
            "dataset validation is not training",
            "learned_model(x) is not implemented",
            "score_ml(x) is not implemented",
            "score(x, t) is not implemented",
            "runtime_influence=false",
            "runtime_active=false",
            "deterministic runtime remains authoritative",
            "phase 8 sizing/tco is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, lower)

    def test_docs_contain_required_sections(self) -> None:
        dataset_text = read_text(DATASET_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Scope",
            "## 3. Non-Goals",
            "## 4. X = Feature Vectors",
            "## 5. y = Observed Outcomes",
            "## 6. Feature Record Model",
            "## 7. Label Record Model",
            "## 8. Feature / Label Dataset Model",
            "## 9. Dataset Lineage",
            "## 10. Dataset Validation",
            "## 11. Runtime Influence Boundary",
            "## 12. Deterministic Runtime Boundary",
            "## 13. Materialization Boundary",
            "## 14. ML Boundary",
            "## 15. Semantic Context Boundary",
            "## 16. Parser / Scoring / Recommendation Boundary",
            "## 17. Relationship to Phase 7S",
            "## 18. Relationship to Future Phase 7U",
            "## 19. Relationship to Future Phase 7V",
            "## 20. Relationship to Future Phase 7W",
            "## 21. Relationship to Future Phase 8",
            "## 22. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, dataset_text)

        schema_text = read_text(SCHEMA_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Feature Schema",
            "## 3. Label Schema",
            "## 4. Supported Feature Types",
            "## 5. Supported Label Types",
            "## 6. Supported Label Names",
            "## 7. Supervised vs Excluded Labels",
            "## 8. Deterministic ID Rules",
            "## 9. Validation Rules",
            "## 10. Lineage Requirements",
            "## 11. Evidence Requirements",
            "## 12. Runtime Boundary",
            "## 13. Non-Goals",
            "## 14. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, schema_text)

    def test_readme_links_phase7t_docs(self) -> None:
        text = read_text(README)
        for title, filename in (
            (
                "Phase 7T Feature / Label Dataset Model",
                "phase7_feature_label_dataset.md",
            ),
            ("Phase 7T Feature / Label Schema", "phase7_feature_label_schema.md"),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)

    def test_supported_feature_types(self) -> None:
        module = self.module
        for feature_type in (
            "numeric",
            "categorical",
            "boolean",
            "text",
            "derived_numeric",
            "derived_categorical",
            "missing",
        ):
            with self.subTest(feature_type=feature_type):
                self.assertIn(feature_type, module.SUPPORTED_FEATURE_TYPES)

        with self.assertRaises(module.FeatureLabelDatasetError):
            self.feature_record(feature_type="unsupported")
        feature_data = module.feature_record_to_dict(self.feature_record())
        feature_data["runtime_influence"] = True
        with self.assertRaises(module.FeatureLabelDatasetError):
            module.feature_record_from_dict(feature_data)

    def test_supported_label_types_and_names(self) -> None:
        module = self.module
        for label_type in (
            "binary",
            "categorical",
            "ordinal",
            "numeric",
            "outcome_status",
            "review_status",
            "unknown",
        ):
            with self.subTest(label_type=label_type):
                self.assertIn(label_type, module.SUPPORTED_LABEL_TYPES)

        for label_name in (
            "tuning_success",
            "performance_improved",
            "performance_worsened",
            "recommendation_accepted",
            "recommendation_rejected",
            "issue_recurred",
            "risk_confirmed",
            "false_positive",
            "false_negative",
            "action_effective",
            "action_ineffective",
            "no_change",
            "unknown_outcome",
        ):
            with self.subTest(label_name=label_name):
                self.assertIn(label_name, module.SUPPORTED_LABEL_NAMES)

        self.assertNotIn("unknown_outcome", module.SUPERVISED_LABEL_NAMES)
        self.assertIn("unknown_outcome", module.EXCLUDED_LABEL_NAMES)

    def test_deterministic_ids(self) -> None:
        module = self.module
        feature_id_a = module.create_feature_id("RUN-001", None, "db_time", "7T.1")
        feature_id_b = module.create_feature_id("RUN-001", None, "db_time", "7T.1")
        label_id_a = module.create_label_id("RUN-001", None, "tuning_success", "7T.1")
        label_id_b = module.create_label_id("RUN-001", None, "tuning_success", "7T.1")
        dataset_id_a = module.create_dataset_id("sample", "7T.1", "7T.1")
        dataset_id_b = module.create_dataset_id("sample", "7T.1", "7T.1")

        self.assertEqual(feature_id_a, feature_id_b)
        self.assertEqual(label_id_a, label_id_b)
        self.assertEqual(dataset_id_a, dataset_id_b)
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        self.assertIsNone(uuid_pattern.match(feature_id_a))
        self.assertNotIn("2026", feature_id_a)
        self.assertNotIn("2026", label_id_a)
        self.assertNotIn("2026", dataset_id_a)

    def test_feature_validation(self) -> None:
        module = self.module
        self.assertEqual(
            module.validate_feature_record(self.feature_record()).feature_type,
            "numeric",
        )
        categorical = self.feature_record(
            feature_name="platform",
            feature_value="exadata",
            feature_type="categorical",
        )
        self.assertEqual(
            module.validate_feature_record(categorical).feature_value,
            "exadata",
        )

        with self.assertRaises(module.FeatureLabelDatasetError):
            self.feature_record(feature_name="")
        with self.assertRaises(module.FeatureLabelDatasetError):
            self.feature_record(feature_schema_version="")
        with self.assertRaises(module.FeatureLabelDatasetError):
            self.feature_record(run_id=None, awr_id=None)
        with self.assertRaises(module.FeatureLabelDatasetError):
            self.feature_record(feature_type="unsupported")

    def test_feature_value_type_validation(self) -> None:
        module = self.module
        valid_cases = (
            ("numeric", 1.25),
            ("categorical", "OLTP"),
            ("boolean", True),
            ("text", "steady workload"),
            ("derived_numeric", 3.5),
            ("derived_categorical", "high"),
            ("missing", None),
        )
        for feature_type, value in valid_cases:
            with self.subTest(feature_type=feature_type):
                module.validate_feature_record(
                    self.feature_record(
                        feature_name=f"{feature_type}_feature",
                        feature_type=feature_type,
                        feature_value=value,
                    )
                )

        with self.assertRaises(module.FeatureLabelDatasetError):
            self.feature_record(feature_type="numeric", feature_value={"bad": "value"})

    def test_label_validation(self) -> None:
        module = self.module
        self.assertEqual(
            module.validate_label_record(self.label_record()).label_name,
            "tuning_success",
        )

        with self.assertRaises(module.FeatureLabelDatasetError):
            self.label_record(confidence=1.5)
        with self.assertRaises(module.FeatureLabelDatasetError):
            self.label_record(label_name="unsupported")
        with self.assertRaises(module.FeatureLabelDatasetError):
            self.label_record(label_schema_version="")
        with self.assertRaises(module.FeatureLabelDatasetError):
            self.label_record(run_id=None, awr_id=None)
        with self.assertRaises(module.FeatureLabelDatasetError):
            self.label_record(
                outcome_source=None,
                source_record_id=None,
                evidence_reference=None,
            )
        label_data = module.label_record_to_dict(self.label_record())
        label_data["runtime_active"] = True
        with self.assertRaises(module.FeatureLabelDatasetError):
            module.label_record_from_dict(label_data)

        unknown = self.label_record(
            label_name="unknown_outcome",
            label_value="unknown",
            label_type="unknown",
            confidence=0.0,
            outcome_source=None,
            source_record_id=None,
            evidence_reference=None,
        )
        self.assertEqual(module.validate_label_record(unknown).label_name, "unknown_outcome")
        self.assertNotIn(unknown.label_name, module.SUPERVISED_LABEL_NAMES)

    def test_schema_validation(self) -> None:
        module = self.module
        feature_names = ["db_time_per_sec", "platform"]
        feature_schema = module.FeatureSchema(
            schema_id=module.create_feature_schema_id("7T.1", feature_names),
            schema_version="7T.1",
            feature_names=feature_names,
            feature_domains=["workload", "topology"],
            required_features=["db_time_per_sec"],
            optional_features=["platform"],
            created_by="unit-test",
            notes=None,
        )
        self.assertEqual(
            module.validate_feature_schema(feature_schema).schema_id,
            feature_schema.schema_id,
        )

        label_names = list(module.SUPPORTED_LABEL_NAMES)
        label_schema = module.LabelSchema(
            schema_id=module.create_label_schema_id("7T.1", label_names),
            schema_version="7T.1",
            label_names=label_names,
            label_values=["true", "false", "unknown"],
            supervised_labels=list(module.SUPERVISED_LABEL_NAMES),
            excluded_labels=list(module.EXCLUDED_LABEL_NAMES),
            created_by="unit-test",
            notes=None,
        )
        self.assertEqual(
            module.validate_label_schema(label_schema).schema_id,
            label_schema.schema_id,
        )

        with self.assertRaises(module.FeatureLabelDatasetError):
            module.LabelSchema(
                schema_id=module.create_label_schema_id("7T.1", label_names),
                schema_version="7T.1",
                label_names=label_names,
                label_values=[],
                supervised_labels=list(module.SUPERVISED_LABEL_NAMES) + ["unknown_outcome"],
                excluded_labels=[],
                created_by="unit-test",
                notes=None,
            )

    def test_dataset_validation(self) -> None:
        module = self.module
        validated = module.validate_feature_label_dataset(self.dataset())
        self.assertEqual(validated.validation_status, module.VALIDATED)
        self.assertFalse(validated.runtime_influence)
        self.assertFalse(validated.runtime_active)

        with self.assertRaises(module.FeatureLabelDatasetError):
            self.dataset(runtime_influence=True)
        with self.assertRaises(module.FeatureLabelDatasetError):
            self.dataset(runtime_active=True)

        unmatched_feature = self.feature_record(run_id="RUN-002")
        unmatched_dataset = module.validate_feature_label_dataset(
            self.dataset(features=[unmatched_feature], labels=[self.label_record(run_id="RUN-001")])
        )
        self.assertEqual(unmatched_dataset.validation_status, module.INVALID)
        self.assertTrue(
            any("Unmatched feature records" in note for note in unmatched_dataset.validation_notes)
        )
        self.assertTrue(
            any("Unmatched label records" in note for note in unmatched_dataset.validation_notes)
        )

    def test_serialization_round_trips(self) -> None:
        module = self.module
        feature = self.feature_record()
        feature_round_trip = module.feature_record_from_dict(module.feature_record_to_dict(feature))
        self.assertEqual(feature, feature_round_trip)

        label = self.label_record()
        label_round_trip = module.label_record_from_dict(module.label_record_to_dict(label))
        self.assertEqual(label, label_round_trip)

        dataset = module.validate_feature_label_dataset(self.dataset())
        data = module.feature_label_dataset_to_dict(dataset)
        round_trip = module.feature_label_dataset_from_dict(data)
        self.assertEqual(dataset, round_trip)

        serialized_a = json.dumps(data, sort_keys=True, separators=(",", ":"))
        serialized_b = json.dumps(
            module.feature_label_dataset_to_dict(round_trip),
            sort_keys=True,
            separators=(",", ":"),
        )
        self.assertEqual(serialized_a, serialized_b)

    def test_join_features_labels(self) -> None:
        module = self.module
        feature = self.feature_record()
        awr_feature = self.feature_record(
            run_id=None,
            awr_id="AWR-002",
            feature_name="platform",
            feature_value="exadata",
            feature_type="categorical",
        )
        label = self.label_record()
        awr_label = self.label_record(run_id=None, awr_id="AWR-002")
        unmatched_label = self.label_record(run_id="RUN-003")

        before_features = [module.feature_record_to_dict(feature), module.feature_record_to_dict(awr_feature)]
        before_labels = [
            module.label_record_to_dict(label),
            module.label_record_to_dict(awr_label),
            module.label_record_to_dict(unmatched_label),
        ]

        joined = module.join_features_labels(
            [feature, awr_feature],
            [label, awr_label, unmatched_label],
        )
        self.assertEqual(len(joined), 3)
        self.assertEqual(sum(1 for group in joined if group["matched"]), 2)
        self.assertEqual(sum(1 for group in joined if not group["matched"]), 1)
        self.assertEqual(
            before_features,
            [module.feature_record_to_dict(feature), module.feature_record_to_dict(awr_feature)],
        )
        self.assertEqual(
            before_labels,
            [
                module.label_record_to_dict(label),
                module.label_record_to_dict(awr_label),
                module.label_record_to_dict(unmatched_label),
            ],
        )

    def test_dataset_summary(self) -> None:
        module = self.module
        unknown = self.label_record(
            label_name="unknown_outcome",
            label_value="unknown",
            label_type="unknown",
            confidence=0.0,
            outcome_source=None,
            source_record_id=None,
            evidence_reference=None,
        )
        dataset = self.dataset(labels=[self.label_record(), unknown])
        summary = module.dataset_summary(dataset)
        self.assertEqual(summary["feature_count"], 1)
        self.assertEqual(summary["label_count"], 2)
        self.assertEqual(summary["supervised_label_count"], 1)
        self.assertEqual(summary["unknown_outcome_count"], 1)
        self.assertFalse(summary["runtime_influence"])
        self.assertFalse(summary["runtime_active"])
        self.assertFalse(summary["dataset_is_model"])
        self.assertFalse(summary["training_implemented"])

    def test_no_ml_implementation_functions(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden_name in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(function_name=forbidden_name):
                self.assertNotIn(forbidden_name, names)

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        self.assertNotIn("src.learning.feature_label_dataset", run_analysis_imports)
        self.assertNotIn("learning.feature_label_dataset", run_analysis_imports)
        self.assertNotIn("feature_label_dataset", run_analysis_imports)

        for path in python_files(RUNTIME_PATHS):
            imports = imported_modules(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.feature_label_dataset", imports)
                self.assertNotIn("learning.feature_label_dataset", imports)
                self.assertNotIn("feature_label_dataset", imports)

    def test_existing_phase7_validation_entrypoints_still_exist(self) -> None:
        for relative_path in (
            "tests/test_phase7_ml_adaptive_scoring_boundary.py",
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
