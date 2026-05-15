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
MODEL_DOC = DOCS / "phase7ak_source_selection_model.md"
BOUNDARY_DOC = DOCS / "phase7ak_local_object_storage_boundary.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "screen3_source_selection.py"

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
    "pathlib",
    "os",
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

FORBIDDEN_SOURCE_TERMS = (
    "read_file",
    "open_file",
    "call_object_storage",
    "list_bucket",
    "download_object",
    "query_database",
    "execute_analysis",
    "run_analysis",
    "subprocess",
    "requests",
    "auto_execute",
    "autonomous_execute",
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
            files.extend(sorted(child for child in path.rglob("*.py") if child.is_file()))
    return files


class Phase7AKSourceSelectionModelTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.screen3_source_selection")

    def make_local_ref(self):
        module = self.module()
        return module.LocalSourceReference(
            local_source_id=module.create_local_source_id(file_name="awr-1.html"),
            file_name="awr-1.html",
            expected_file_type="html",
            exists_hint=False,
            notes="metadata only",
        )

    def make_object_ref(self, configured_hint: bool | None = True):
        module = self.module()
        return module.ObjectStorageSourceReference(
            object_source_id=module.create_object_source_id(
                namespace="namespace",
                bucket="bucket",
                object_name="path/awr.html",
                region="us-ashburn-1",
            ),
            namespace="namespace",
            bucket="bucket",
            object_name="path/awr.html",
            region="us-ashburn-1",
            credential_mode="config_file",
            configured_hint=configured_hint,
            notes="metadata only",
        )

    def make_existing_run_ref(self):
        module = self.module()
        return module.ExistingRunSourceReference(
            run_source_id=module.create_existing_run_source_id(run_id="RUN-1"),
            run_id="RUN-1",
            awr_id="AWR-1",
            dbid="123",
            database_name="PROD",
            snapshot_label="snap-1",
        )

    def make_em_ref(self):
        module = self.module()
        return module.FutureEMExtractSourceReference(
            em_source_id=module.create_future_em_extract_source_id(
                extract_id="EM-EXTRACT-1",
            ),
            extract_id="EM-EXTRACT-1",
            extract_format="future-json",
            em_version="future",
            target_name="prod-db",
            target_type="oracle_database",
        )

    def make_selection(self, source_mode: str, **overrides):
        module = self.module()
        values = {
            "source_selection_id": module.create_source_selection_id(
                source_mode,
                source_label="unit-test",
            ),
            "source_mode": source_mode,
            "source_label": "unit-test",
            "validation_status": "VALID_METADATA_ONLY",
            "notes": "unit test",
        }
        values.update(overrides)
        return module.SourceSelection(**values)

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "SourceSelection"))
        self.assertTrue(hasattr(module, "SourceValidationResult"))

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
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)
        self.assertTrue(BOUNDARY_DOC.is_file(), BOUNDARY_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        text = lower_text(MODEL_DOC) + "\n" + lower_text(BOUNDARY_DOC)
        for phrase in (
            "source selection is not execution",
            "no files are read",
            "no object storage calls are made",
            "no db lookup is made",
            "can_execute=false in phase 7ak",
            "execution_blocked=true in phase 7ak",
            "future_em_extract is placeholder only",
            "em extract implementation belongs to phase 8",
            "phase 8 sizing/tco is not implemented",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_supported_source_modes(self) -> None:
        module = self.module()
        self.assertEqual(
            module.SCREEN3_SOURCE_MODES,
            (
                "none",
                "local_staged",
                "local_file",
                "existing_run",
                "object_storage",
                "future_upload",
                "future_em_extract",
            ),
        )
        for source_mode in module.SCREEN3_SOURCE_MODES:
            with self.subTest(source_mode=source_mode):
                source_id = module.create_source_selection_id(source_mode, "label")
                self.assertTrue(source_id.startswith("SCREEN3-SOURCE-SELECTION-"))

        with self.assertRaises(module.Screen3SourceSelectionError):
            module.create_source_selection_id("unsupported")

    def test_local_source_reference_metadata_only(self) -> None:
        module = self.module()
        ref = self.make_local_ref()
        self.assertIs(module.validate_local_source_reference(ref), ref)
        self.assertEqual("LOCAL-SOURCE-AWR-1-HTML", ref.local_source_id)
        self.assertFalse(ref.exists_hint)

        impossible_path_ref = module.LocalSourceReference(
            local_source_id=module.create_local_source_id(
                local_path="/definitely/not/checked/awr.html",
            ),
            local_path="/definitely/not/checked/awr.html",
            expected_file_type="html",
            exists_hint=True,
        )
        self.assertIs(
            module.validate_local_source_reference(impossible_path_ref),
            impossible_path_ref,
        )

        with self.assertRaises(module.Screen3SourceSelectionError):
            module.LocalSourceReference(local_source_id="LOCAL-SOURCE-EMPTY")
        with self.assertRaises(module.Screen3SourceSelectionError):
            module.LocalSourceReference(
                local_source_id="LOCAL-SOURCE-BAD-TYPE",
                file_name="awr.bin",
                expected_file_type="binary",
            )

    def test_object_storage_source_reference_metadata_only(self) -> None:
        module = self.module()
        ref = self.make_object_ref()
        self.assertIs(module.validate_object_storage_source_reference(ref), ref)
        first_id = module.create_object_source_id(
            namespace="namespace",
            bucket="bucket",
            object_name="path/awr.html",
            region="us-ashburn-1",
        )
        second_id = module.create_object_source_id(
            namespace="namespace",
            bucket="bucket",
            object_name="path/awr.html",
            region="us-ashburn-1",
        )
        self.assertEqual(first_id, second_id)
        self.assertTrue(first_id.startswith("OBJECT-SOURCE-NAMESPACE-BUCKET-"))

        for missing_field in ("namespace", "bucket", "object_name", "region"):
            values = {
                "object_source_id": "OBJECT-SOURCE-TEST",
                "namespace": "namespace",
                "bucket": "bucket",
                "object_name": "path/awr.html",
                "region": "us-ashburn-1",
            }
            values[missing_field] = ""
            with self.subTest(missing_field=missing_field):
                with self.assertRaises(module.Screen3SourceSelectionError):
                    module.ObjectStorageSourceReference(**values)

        with self.assertRaises(module.Screen3SourceSelectionError):
            module.ObjectStorageSourceReference(
                object_source_id="OBJECT-SOURCE-BAD-CREDENTIAL",
                namespace="namespace",
                bucket="bucket",
                object_name="path/awr.html",
                region="us-ashburn-1",
                credential_mode="password",
            )

    def test_existing_run_source_reference_metadata_only(self) -> None:
        module = self.module()
        ref = self.make_existing_run_ref()
        self.assertIs(module.validate_existing_run_source_reference(ref), ref)
        self.assertEqual("EXISTING-RUN-SOURCE-RUN-1", ref.run_source_id)
        self.assertEqual(
            module.create_existing_run_source_id(run_id="RUN-1"),
            module.create_existing_run_source_id(run_id="RUN-1"),
        )

        with self.assertRaises(module.Screen3SourceSelectionError):
            module.ExistingRunSourceReference(run_source_id="EXISTING-RUN-SOURCE-EMPTY")

    def test_future_em_extract_placeholder(self) -> None:
        module = self.module()
        ref = self.make_em_ref()
        self.assertIs(module.validate_future_em_extract_source_reference(ref), ref)
        selection = self.make_selection(
            "future_em_extract",
            future_em_extract_source=ref,
        )
        result = module.evaluate_source_selection(selection)
        self.assertEqual("FUTURE_SOURCE_NOT_IMPLEMENTED", result.validation_status)
        self.assertFalse(result.can_execute)
        self.assertTrue(result.execution_blocked)
        self.assertNotIn("adapter", lower_text(MODULE_PATH))

    def test_source_selection_validation_rules(self) -> None:
        module = self.module()
        no_source = module.default_no_source_selection(notes="placeholder")
        self.assertEqual("none", no_source.source_mode)
        self.assertEqual("NO_SOURCE_SELECTED", no_source.validation_status)

        local_selection = self.make_selection(
            "local_file",
            local_source=self.make_local_ref(),
        )
        self.assertIs(module.validate_source_selection(local_selection), local_selection)

        object_selection = self.make_selection(
            "object_storage",
            object_storage_source=self.make_object_ref(),
        )
        self.assertIs(
            module.validate_source_selection(object_selection),
            object_selection,
        )

        existing_selection = self.make_selection(
            "existing_run",
            existing_run_source=self.make_existing_run_ref(),
        )
        self.assertIs(
            module.validate_source_selection(existing_selection),
            existing_selection,
        )

        em_selection = self.make_selection(
            "future_em_extract",
            future_em_extract_source=self.make_em_ref(),
        )
        self.assertIs(module.validate_source_selection(em_selection), em_selection)

        for source_mode in (
            "local_file",
            "local_staged",
            "object_storage",
            "existing_run",
            "future_em_extract",
        ):
            with self.subTest(source_mode=source_mode):
                with self.assertRaises(module.Screen3SourceSelectionError):
                    module.validate_source_selection(self.make_selection(source_mode))

        self.assertEqual(
            module.create_source_selection_id("local_file", "label"),
            module.create_source_selection_id("local_file", "label"),
        )

    def test_evaluate_source_selection_metadata_only(self) -> None:
        module = self.module()
        no_source_result = module.evaluate_source_selection(
            module.default_no_source_selection(),
        )
        self.assertEqual("NO_SOURCE_SELECTED", no_source_result.validation_status)
        self.assertFalse(no_source_result.valid)

        local_result = module.evaluate_source_selection(
            self.make_selection("local_file", local_source=self.make_local_ref())
        )
        self.assertEqual("VALID_METADATA_ONLY", local_result.validation_status)
        self.assertTrue(local_result.valid)

        object_result = module.evaluate_source_selection(
            self.make_selection(
                "object_storage",
                object_storage_source=self.make_object_ref(configured_hint=True),
            )
        )
        self.assertEqual("VALID_METADATA_ONLY", object_result.validation_status)
        self.assertTrue(object_result.valid)

        object_needs_config = module.evaluate_source_selection(
            self.make_selection(
                "object_storage",
                object_storage_source=self.make_object_ref(configured_hint=False),
            )
        )
        self.assertEqual(
            "NEEDS_OBJECT_STORAGE_CONFIG",
            object_needs_config.validation_status,
        )

        future_upload = module.evaluate_source_selection(
            self.make_selection("future_upload")
        )
        self.assertEqual("FUTURE_SOURCE_NOT_IMPLEMENTED", future_upload.validation_status)

        for result in (
            no_source_result,
            local_result,
            object_result,
            object_needs_config,
            future_upload,
        ):
            with self.subTest(status=result.validation_status):
                self.assertFalse(result.can_execute)
                self.assertTrue(result.execution_blocked)
                self.assertFalse(result.object_storage_call_performed)
                self.assertFalse(result.local_file_read_performed)
                self.assertFalse(result.db_lookup_performed)

    def test_source_validation_result_safety_flags(self) -> None:
        module = self.module()
        base = {
            "validation_id": "SOURCE-VALIDATION-1",
            "source_selection_id": "SOURCE-SELECTION-1",
            "valid": True,
            "validation_status": "VALID_METADATA_ONLY",
            "source_mode": "local_file",
            "denied_reasons": ["execution is not allowed in Phase 7AK"],
            "warnings": [],
            "required_next_steps": [],
        }
        for field_name, bad_value in (
            ("can_execute", True),
            ("execution_blocked", False),
            ("object_storage_call_performed", True),
            ("local_file_read_performed", True),
            ("db_lookup_performed", True),
        ):
            values = dict(base)
            values[field_name] = bad_value
            with self.subTest(field_name=field_name):
                with self.assertRaises(module.Screen3SourceSelectionError):
                    module.SourceValidationResult(**values)

    def test_serialization_round_trips(self) -> None:
        module = self.module()
        local_ref = self.make_local_ref()
        object_ref = self.make_object_ref()
        existing_ref = self.make_existing_run_ref()
        em_ref = self.make_em_ref()

        self.assertEqual(
            local_ref,
            module.local_source_reference_from_dict(
                module.local_source_reference_to_dict(local_ref)
            ),
        )
        self.assertEqual(
            object_ref,
            module.object_storage_source_reference_from_dict(
                module.object_storage_source_reference_to_dict(object_ref)
            ),
        )
        self.assertEqual(
            existing_ref,
            module.existing_run_source_reference_from_dict(
                module.existing_run_source_reference_to_dict(existing_ref)
            ),
        )
        self.assertEqual(
            em_ref,
            module.future_em_extract_source_reference_from_dict(
                module.future_em_extract_source_reference_to_dict(em_ref)
            ),
        )

        selection = self.make_selection("local_file", local_source=local_ref)
        self.assertEqual(
            selection,
            module.source_selection_from_dict(module.source_selection_to_dict(selection)),
        )

        result = module.evaluate_source_selection(selection)
        self.assertEqual(
            result,
            module.source_validation_result_from_dict(
                module.source_validation_result_to_dict(result)
            ),
        )

    def test_no_execution_functions_or_terms(self) -> None:
        source = lower_text(MODULE_PATH)
        functions = function_names(MODULE_PATH)
        for term in FORBIDDEN_SOURCE_TERMS:
            with self.subTest(term=term):
                self.assertNotIn(term, functions)
                self.assertNotIn(term, source)

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        for module_name in (
            "src.learning.screen3_source_selection",
            "learning.screen3_source_selection",
            "screen3_source_selection",
        ):
            with self.subTest(module_name=module_name):
                self.assertNotIn(module_name, run_analysis_imports)

        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            source = read_text(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.screen3_source_selection", imports)
                self.assertNotIn("learning.screen3_source_selection", imports)
                self.assertNotIn("screen3_source_selection", imports)
                self.assertNotIn("screen3_source_selection", source)

    def test_behavior_files_are_not_modified_by_phase7ak(self) -> None:
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
                "Phase 7AK Source Selection Model",
                "phase7ak_source_selection_model.md",
            ),
            (
                "Phase 7AK Local / Object Storage Boundary",
                "phase7ak_local_object_storage_boundary.md",
            ),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)


if __name__ == "__main__":
    unittest.main()
