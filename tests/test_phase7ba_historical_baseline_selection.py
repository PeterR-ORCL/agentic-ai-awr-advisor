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
MODEL_DOC = DOCS / "phase7ba_historical_baseline_selection.md"
OBJECT_DOC = DOCS / "phase7ba_baseline_selection_model.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "screen4_baseline_selection.py"

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

PHASE7BC_ALLOWED_DASHBOARD_PREVIEW_FILE = "src/reporting/html_dashboard.py"
PHASE7BC_REQUIRED_PREVIEW_ARTIFACTS = {
    "src/learning/screen4_historical_learning_bridge.py",
    "tests/test_phase7bc_historical_learning_bridge.py",
    "tests/test_dashboard_screen4_historical_review_panel.py",
    "docs/architecture/phase7bc_historical_learning_bridge.md",
    "docs/architecture/phase7bc_historical_learning_intent_model.md",
    "docs/architecture/phase7bc_screen4_historical_review_panel.md",
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

FORBIDDEN_SOURCE_TERMS = (
    "persist_baseline",
    "make_baseline_official",
    "update_historical_truth",
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


def disallowed_behavior_changes_for_phase7bc(
    changed: set[str],
    all_changed: set[str],
) -> set[str]:
    if (
        PHASE7BC_ALLOWED_DASHBOARD_PREVIEW_FILE in changed
        and PHASE7BC_REQUIRED_PREVIEW_ARTIFACTS.issubset(all_changed)
    ):
        return changed - {PHASE7BC_ALLOWED_DASHBOARD_PREVIEW_FILE}
    return changed


class Phase7BAHistoricalBaselineSelectionTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.screen4_baseline_selection")

    def make_candidate(self, **overrides):
        module = self.module()
        run_id = overrides.get("run_id", "RUN-BASELINE-1")
        awr_id = overrides.get("awr_id", "AWR-BASELINE-1")
        snapshot_label = overrides.get("snapshot_label", "snap-10")
        values = {
            "baseline_candidate_id": module.create_baseline_candidate_id(
                run_id=run_id,
                awr_id=awr_id,
                snapshot_label=snapshot_label,
            ),
            "baseline_name": "Stable CPU baseline",
            "run_id": run_id,
            "awr_id": awr_id,
            "dbid": "123456789",
            "database_name": "ORCL",
            "snapshot_label": snapshot_label,
            "start_time": "2026-05-01T10:00:00",
            "end_time": "2026-05-01T11:00:00",
            "workload_class": "OLTP",
            "stability_score": 88.0,
            "evidence_quality": "high",
            "missing_metric_count": 0,
            "anomaly_count": 0,
            "trend_volatility": 2.5,
            "candidate_status": "proposed",
            "source_context": {"screen": "screen_4"},
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.HistoricalBaselineCandidate(**values)

    def make_request(self, **overrides):
        module = self.module()
        candidate_id = overrides.get(
            "candidate_id",
            module.create_baseline_candidate_id(
                run_id="RUN-BASELINE-1",
                awr_id="AWR-BASELINE-1",
                snapshot_label="snap-10",
            ),
        )
        comparison_purpose = overrides.get(
            "comparison_purpose",
            "current_vs_baseline",
        )
        values = {
            "selection_request_id": module.create_baseline_selection_request_id(
                candidate_id,
                comparison_purpose,
            ),
            "candidate_id": candidate_id,
            "requested_by_actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
            "actor_audit_context": {"actor_id": "ACTOR-LOCAL-JANE-REVIEWER"},
            "selection_reason": "Stable historical period",
            "comparison_purpose": comparison_purpose,
            "target_run_id": "RUN-TARGET-1",
            "target_awr_id": "AWR-TARGET-1",
            "target_snapshot_label": "snap-20",
            "target_domain": "CPU",
            "requested_status": "proposed",
            "write_performed": False,
            "baseline_official": False,
            "runtime_influence": False,
            "phase4i_mutation_requested": False,
            "created_at": "2026-05-15T12:00:00",
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.HistoricalBaselineSelectionRequest(**values)

    def make_validation(self, **overrides):
        module = self.module()
        request = overrides.pop("request", self.make_request())
        values = {
            "validation_id": module.create_baseline_validation_id(
                request.selection_request_id,
            ),
            "selection_request_id": request.selection_request_id,
            "candidate_id": request.candidate_id,
            "valid": True,
            "validation_status": "valid_metadata_only",
            "evidence_quality": "high",
            "stability_acceptable": True,
            "missing_metric_risk": "none",
            "anomaly_risk": "none",
            "workload_similarity": "not_evaluated",
            "comparison_valid": True,
            "baseline_official": False,
            "write_performed": False,
            "denied_reasons": [],
            "warnings": ["metadata only"],
            "required_next_steps": ["future governed write path"],
            "runtime_influence": False,
            "phase4i_mutation_requested": False,
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.HistoricalBaselineValidation(**values)

    def make_context(self, **overrides):
        module = self.module()
        candidate_id = overrides.get(
            "baseline_candidate_id",
            module.create_baseline_candidate_id(
                run_id="RUN-BASELINE-1",
                awr_id="AWR-BASELINE-1",
                snapshot_label="snap-10",
            ),
        )
        target_run_id = overrides.get("target_run_id", "RUN-TARGET-1")
        comparison_type = overrides.get(
            "comparison_type",
            "single_baseline_to_target",
        )
        values = {
            "comparison_context_id": module.create_historical_comparison_context_id(
                candidate_id,
                target_run_id=target_run_id,
                comparison_type=comparison_type,
            ),
            "baseline_candidate_id": candidate_id,
            "target_run_id": target_run_id,
            "target_awr_id": "AWR-TARGET-1",
            "comparison_type": comparison_type,
            "comparison_purpose": "current_vs_baseline",
            "compared_domains": ["CPU", "IO"],
            "baseline_snapshot_label": "snap-10",
            "target_snapshot_label": "snap-20",
            "limitations": ["metadata only"],
            "runtime_influence": False,
            "phase4i_mutation_requested": False,
            "notes": "metadata only",
        }
        values.update(overrides)
        return module.HistoricalComparisonContext(**values)

    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = self.module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "HistoricalBaselineCandidate"))
        self.assertTrue(hasattr(module, "HistoricalBaselineSelectionRequest"))
        self.assertTrue(hasattr(module, "HistoricalBaselineValidation"))
        self.assertTrue(hasattr(module, "HistoricalComparisonContext"))

        imports = imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )

    def test_docs_exist_and_contain_boundary_phrases(self) -> None:
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)
        self.assertTrue(OBJECT_DOC.is_file(), OBJECT_DOC)
        text = lower_text(MODEL_DOC) + "\n" + lower_text(OBJECT_DOC)
        for phrase in (
            "baseline selection records are local metadata only",
            "no baseline is made official",
            "no historical truth is changed",
            "no trend/anomaly/scoring behavior is changed",
            "no phase 4i mutation occurs",
            "phase 8 sizing/tco is not implemented",
            "baseline_official=false",
            "write_performed=false",
            "runtime_influence=false",
            "phase4i_mutation_requested=false",
            "no baseline is persisted or made official in 7ba",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_supported_values_and_unsupported_values(self) -> None:
        module = self.module()
        self.assertEqual(
            module.HISTORICAL_BASELINE_STATUSES,
            (
                "proposed",
                "under_review",
                "validated",
                "rejected",
                "insufficient_evidence",
                "superseded",
                "closed",
            ),
        )
        self.assertEqual(
            module.HISTORICAL_EVIDENCE_QUALITY_VALUES,
            ("high", "medium", "low", "insufficient", "unknown"),
        )
        self.assertEqual(
            module.HISTORICAL_COMPARISON_PURPOSES,
            (
                "before_after_tuning",
                "stable_vs_degraded",
                "current_vs_baseline",
                "workload_regression",
                "anomaly_review",
                "trend_review",
                "general_historical_review",
            ),
        )
        self.assertEqual(
            module.HISTORICAL_COMPARISON_TYPES,
            (
                "single_baseline_to_target",
                "before_after",
                "multi_snapshot_baseline",
                "workload_class_baseline",
                "historical_window_baseline",
            ),
        )
        self.assertIn(
            "not_official_in_this_phase",
            module.HISTORICAL_BASELINE_VALIDATION_STATUSES,
        )
        with self.assertRaises(module.Screen4BaselineSelectionError):
            self.make_candidate(candidate_status="official")
        with self.assertRaises(module.Screen4BaselineSelectionError):
            self.make_candidate(evidence_quality="perfect")
        with self.assertRaises(module.Screen4BaselineSelectionError):
            self.make_request(comparison_purpose="runtime_activation")
        with self.assertRaises(module.Screen4BaselineSelectionError):
            self.make_context(comparison_type="runtime_baseline")

    def test_baseline_candidate_validation(self) -> None:
        module = self.module()
        candidate = self.make_candidate()
        self.assertIs(module.validate_historical_baseline_candidate(candidate), candidate)

        for overrides in (
            {"run_id": None, "awr_id": None},
            {"stability_score": -0.1},
            {"stability_score": 100.1},
            {"missing_metric_count": -1},
            {"anomaly_count": -1},
            {"trend_volatility": -1.0},
            {"evidence_quality": "unsupported"},
            {"candidate_status": "official"},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen4BaselineSelectionError):
                    self.make_candidate(**overrides)

    def test_selection_request_validation(self) -> None:
        module = self.module()
        request = self.make_request()
        self.assertIs(
            module.validate_historical_baseline_selection_request(request),
            request,
        )
        self.assertFalse(request.write_performed)
        self.assertFalse(request.baseline_official)
        self.assertFalse(request.runtime_influence)
        self.assertFalse(request.phase4i_mutation_requested)

        missing_actor = self.make_request(requested_by_actor_id=None)
        with self.assertRaises(module.Screen4BaselineSelectionError):
            module.validate_historical_baseline_selection_request(missing_actor)

        for overrides in (
            {"baseline_official": True},
            {"write_performed": True},
            {"runtime_influence": True},
            {"phase4i_mutation_requested": True},
            {"requested_status": "official"},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen4BaselineSelectionError):
                    self.make_request(**overrides)

    def test_validation_result_validation(self) -> None:
        module = self.module()
        validation = self.make_validation()
        self.assertIs(
            module.validate_historical_baseline_validation(validation),
            validation,
        )

        for overrides in (
            {"baseline_official": True},
            {"write_performed": True},
            {"runtime_influence": True},
            {"phase4i_mutation_requested": True},
            {"validation_status": "official"},
            {"evidence_quality": "perfect"},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen4BaselineSelectionError):
                    self.make_validation(**overrides)

    def test_comparison_context_validation(self) -> None:
        module = self.module()
        context = self.make_context()
        self.assertIs(module.validate_historical_comparison_context(context), context)
        self.assertFalse(context.runtime_influence)
        self.assertFalse(context.phase4i_mutation_requested)

        for overrides in (
            {"comparison_type": "official_runtime"},
            {"comparison_purpose": "official_runtime"},
            {"compared_domains": "CPU"},
            {"runtime_influence": True},
            {"phase4i_mutation_requested": True},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(module.Screen4BaselineSelectionError):
                    self.make_context(**overrides)

    def test_evaluate_baseline_selection(self) -> None:
        module = self.module()
        candidate = self.make_candidate()
        request = self.make_request(candidate_id=candidate.baseline_candidate_id)

        missing_actor = module.evaluate_baseline_selection(
            candidate,
            self.make_request(
                candidate_id=candidate.baseline_candidate_id,
                requested_by_actor_id=None,
            ),
        )
        self.assertFalse(missing_actor.valid)
        self.assertEqual("needs_actor", missing_actor.validation_status)

        missing_candidate = module.evaluate_baseline_selection(None, request)
        self.assertFalse(missing_candidate.valid)
        self.assertEqual("needs_candidate", missing_candidate.validation_status)

        low_quality = module.evaluate_baseline_selection(
            self.make_candidate(evidence_quality="low"),
            request,
        )
        self.assertFalse(low_quality.valid)
        self.assertEqual("insufficient_evidence", low_quality.validation_status)

        missing_metric = module.evaluate_baseline_selection(
            self.make_candidate(missing_metric_count=2),
            request,
        )
        self.assertFalse(missing_metric.valid)
        self.assertEqual("high_missing_metric_risk", missing_metric.validation_status)
        self.assertIn("baseline candidate has missing metrics", missing_metric.warnings)

        anomaly = module.evaluate_baseline_selection(
            self.make_candidate(anomaly_count=1),
            request,
        )
        self.assertFalse(anomaly.valid)
        self.assertEqual("high_anomaly_risk", anomaly.validation_status)
        self.assertIn("baseline candidate includes anomalies", anomaly.warnings)

        valid = module.evaluate_baseline_selection(candidate, request)
        self.assertTrue(valid.valid)
        self.assertEqual("valid_metadata_only", valid.validation_status)
        self.assertFalse(valid.baseline_official)
        self.assertFalse(valid.write_performed)
        self.assertFalse(valid.runtime_influence)
        self.assertFalse(valid.phase4i_mutation_requested)

    def test_serialization_round_trips_are_deterministic(self) -> None:
        module = self.module()
        objects = (
            (
                module.historical_baseline_candidate_to_dict,
                module.historical_baseline_candidate_from_dict,
                self.make_candidate(),
            ),
            (
                module.historical_baseline_selection_request_to_dict,
                module.historical_baseline_selection_request_from_dict,
                self.make_request(),
            ),
            (
                module.historical_baseline_validation_to_dict,
                module.historical_baseline_validation_from_dict,
                self.make_validation(),
            ),
            (
                module.historical_comparison_context_to_dict,
                module.historical_comparison_context_from_dict,
                self.make_context(),
            ),
        )
        for to_dict, from_dict, value in objects:
            with self.subTest(value=type(value).__name__):
                serialized = to_dict(value)
                self.assertEqual(to_dict(from_dict(serialized)), serialized)
                self.assertEqual(
                    to_dict(from_dict(serialized)),
                    to_dict(from_dict(serialized)),
                )

    def test_deterministic_ids(self) -> None:
        module = self.module()
        ids = (
            module.create_baseline_candidate_id(
                run_id="RUN-1",
                awr_id="AWR-1",
                snapshot_label="snap-1",
            ),
            module.create_baseline_selection_request_id(
                "HIST-BASELINE-CANDIDATE-RUN-1-SNAP-1",
                "current_vs_baseline",
            ),
            module.create_baseline_validation_id(
                "HIST-BASELINE-REQUEST-HIST-BASELINE-CANDIDATE-RUN-1-SNAP-1-CURRENT-VS-BASELINE"
            ),
            module.create_historical_comparison_context_id(
                "HIST-BASELINE-CANDIDATE-RUN-1-SNAP-1",
                target_run_id="RUN-2",
                comparison_type="single_baseline_to_target",
            ),
        )
        self.assertEqual(
            ids[0],
            module.create_baseline_candidate_id(
                run_id="RUN-1",
                awr_id="AWR-1",
                snapshot_label="snap-1",
            ),
        )
        self.assertEqual(
            ids[1],
            module.create_baseline_selection_request_id(
                "HIST-BASELINE-CANDIDATE-RUN-1-SNAP-1",
                "current_vs_baseline",
            ),
        )
        self.assertEqual(
            ids[2],
            module.create_baseline_validation_id(
                "HIST-BASELINE-REQUEST-HIST-BASELINE-CANDIDATE-RUN-1-SNAP-1-CURRENT-VS-BASELINE"
            ),
        )
        self.assertEqual(
            ids[3],
            module.create_historical_comparison_context_id(
                "HIST-BASELINE-CANDIDATE-RUN-1-SNAP-1",
                target_run_id="RUN-2",
                comparison_type="single_baseline_to_target",
            ),
        )
        for value in ids:
            with self.subTest(value=value):
                self.assertFalse(
                    re.search(
                        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                        value.lower(),
                    )
                )

    def test_no_mutation_or_persistence_functions(self) -> None:
        names = function_names(MODULE_PATH)
        source = read_text(MODULE_PATH)
        for forbidden in FORBIDDEN_SOURCE_TERMS:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, names)
                self.assertNotIn(forbidden, source)

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        for module_name in (
            "src.learning.screen4_baseline_selection",
            "learning.screen4_baseline_selection",
            "screen4_baseline_selection",
        ):
            with self.subTest(module_name=module_name):
                self.assertNotIn(module_name, run_analysis_imports)

        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            source = read_text(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.screen4_baseline_selection", imports)
                self.assertNotIn("learning.screen4_baseline_selection", imports)
                self.assertNotIn("screen4_baseline_selection", imports)
                self.assertNotIn("screen4_baseline_selection", source)

    def test_behavior_files_are_not_modified_by_phase7ba(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git not available")
        if not (ROOT / ".git").exists():
            self.skipTest("not a git checkout")

        try:
            changed = git_changed_paths(FORBIDDEN_BEHAVIOR_FILES)
            all_changed = git_changed_paths()
        except RuntimeError as exc:
            self.skipTest(str(exc))

        changed = disallowed_behavior_changes_for_phase7bc(changed, all_changed)
        self.assertFalse(changed, f"behavior files modified: {sorted(changed)}")

    def test_readme_links_new_docs(self) -> None:
        text = read_text(README)
        for title, filename in (
            (
                "Phase 7BA Historical Baseline Selection",
                "phase7ba_historical_baseline_selection.md",
            ),
            (
                "Phase 7BA Baseline Selection Model",
                "phase7ba_baseline_selection_model.md",
            ),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)


if __name__ == "__main__":
    unittest.main()
