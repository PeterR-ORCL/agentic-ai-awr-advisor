from __future__ import annotations

import ast
import contextlib
import importlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

import scripts.awr_memory_cli as cli
from src.learning import learning_candidate_model


ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = ROOT / "scripts" / "awr_memory_cli.py"
DOC_PATH = ROOT / "docs" / "architecture" / "phase7_learning_cli_operations.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def run_cli(argv: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = cli.main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


def write_json(directory: Path, name: str, data: object) -> Path:
    path = directory / name
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def memory_records() -> dict[str, list[dict[str, object]]]:
    return {
        "runs": [],
        "recommendations": [],
        "actions": [],
        "outcomes": [],
        "feedback": [],
        "unknown_signals": [
            {
                "unknown_signal_id": 1,
                "section_name": "SQL ordered by Elapsed Time",
                "raw_header_text": "PX wait class detail",
                "frequency_count": 1,
            },
            {
                "unknown_signal_id": 2,
                "section_name": "SQL ordered by Elapsed Time",
                "raw_header_text": "PX wait class detail",
                "frequency_count": 1,
            },
        ],
        "knowledge_requests": [],
        "knowledge_artifacts": [],
    }


def pattern_record() -> dict[str, object]:
    return {
        "pattern_id": "PATTERN-REPEATED-UNKNOWN-SIGNAL-SQL-PX",
        "pattern_type": "repeated_unknown_signal",
        "title": "Repeated unknown signal: SQL / PX wait class detail",
        "description": "The same parser unknown signal appears repeatedly.",
        "source_records": [
            {
                "source_type": "unknown_signal",
                "source_id": 1,
                "normalized_key": "sql_px_wait_class_detail",
            },
            {
                "source_type": "unknown_signal",
                "source_id": 2,
                "normalized_key": "sql_px_wait_class_detail",
            },
        ],
        "affected_domain": None,
        "affected_component": "parser",
        "recurrence_count": 2,
        "observed_effect": "repeated_unknown_signal",
        "confidence": 0.55,
        "rationale": "Two local records share the same parser unknown signal.",
        "requires_human_review": True,
        "runtime_influence": False,
        "suggested_candidate_type": "parser_mapping_candidate",
    }


def candidate_record(
    *,
    status: str = "PROPOSED",
    materialization_reference: str | None = None,
) -> dict[str, object]:
    candidate = learning_candidate_model.LearningCandidate(
        candidate_id="CANDIDATE-PARSER-MAPPING-CANDIDATE-CLI",
        candidate_type="parser_mapping_candidate",
        title="Review repeated SQL PX unknown signal",
        description="Review repeated parser unknown signal in SQL sections.",
        source_evidence=[
            {
                "source_type": "unknown_signal",
                "source_id": 1,
                "normalized_key": "sql_px_wait_class_detail",
            }
        ],
        structured_sources=[
            {
                "source_type": "outcome_pattern",
                "pattern_id": "PATTERN-REPEATED-UNKNOWN-SIGNAL-SQL-PX",
            }
        ],
        semantic_context=None,
        affected_component="parser",
        affected_domain="SQL",
        confidence=0.55,
        rationale="Human review is required before implementation.",
        requires_human_review=True,
        runtime_influence=False,
        status=status,
        created_at=None,
        created_by="test",
        reviewed_by="reviewer@example.com" if status != "PROPOSED" else None,
        review_notes=None,
        materialization_reference=materialization_reference,
    )
    return candidate.to_dict()


def semantic_records(candidate_id: str) -> dict[str, list[dict[str, object]]]:
    return {
        "semantic_records": [
            {
                "record_id": "case-cli",
                "candidate_id": candidate_id,
                "category": "case",
                "summary": "Prior parser governance review for SQL PX wait class detail.",
                "component": "parser",
                "domain": "SQL",
                "score": 0.91,
            }
        ]
    }


class LearningCliCommandTests(unittest.TestCase):
    def test_01_import_safety(self) -> None:
        before_environment = dict(os.environ)

        module = importlib.import_module("scripts.awr_memory_cli")
        for learning_module in (
            "src.learning.outcome_pattern_miner",
            "src.learning.learning_candidate_model",
            "src.learning.learning_candidate_engine",
            "src.learning.semantic_candidate_context",
            "src.learning.learning_governance_bridge",
        ):
            importlib.import_module(learning_module)

        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "build_parser"))
        self.assertTrue(hasattr(module, "main"))

    def test_learning_command_group_exists(self) -> None:
        help_text = cli.build_parser().format_help()
        self.assertIn("learning", help_text)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with self.assertRaises(SystemExit) as raised:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                cli.main(["learning", "--help"])
        self.assertEqual(raised.exception.code, 0)
        learning_help = stdout.getvalue()
        for command in (
            "status",
            "patterns",
            "candidates",
            "candidate-detail",
            "semantic-context",
            "review",
            "export",
            "validate",
        ):
            self.assertIn(command, learning_help)

    def test_learning_status(self) -> None:
        code, stdout, _ = run_cli(["learning", "status"])

        self.assertEqual(code, 0)
        self.assertIn("learning modules available", stdout)
        self.assertIn("runtime_influence=false", stdout)
        self.assertIn("deterministic runtime remains authoritative", stdout)
        self.assertIn("no runtime activation", stdout)

    def test_learning_patterns_empty_input(self) -> None:
        code, stdout, _ = run_cli(["learning", "patterns", "--json"])

        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["patterns"], [])
        self.assertEqual(data["count"], 0)
        self.assertFalse(data["runtime_influence"])
        self.assertTrue(data["no_candidates_generated"])

    def test_learning_patterns_local_input(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            input_path = write_json(Path(tempdir), "memory.json", memory_records())

            code, stdout, _ = run_cli(["learning", "patterns", "--input", str(input_path), "--json"])

        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertGreaterEqual(data["count"], 1)
        self.assertIn("patterns", data)
        self.assertNotIn("candidates", data)
        self.assertFalse(data["runtime_influence"])
        self.assertTrue(all(not pattern["runtime_influence"] for pattern in data["patterns"]))

    def test_learning_candidates_from_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            pattern_path = write_json(Path(tempdir), "patterns.json", {"patterns": [pattern_record()]})

            code, stdout, _ = run_cli(
                ["learning", "candidates", "--input", str(pattern_path), "--json"]
            )

        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["source_mode"], "patterns")
        self.assertEqual(data["count"], 1)
        candidate = data["candidates"][0]
        self.assertEqual(candidate["status"], "PROPOSED")
        self.assertFalse(candidate["runtime_influence"])
        self.assertTrue(candidate["requires_human_review"])
        self.assertTrue(data["proposal_only"])
        self.assertTrue(data["no_approval"])

    def test_learning_candidates_from_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            original = memory_records()
            input_path = write_json(Path(tempdir), "memory.json", original)

            code, stdout, _ = run_cli(
                [
                    "learning",
                    "candidates",
                    "--from-memory",
                    "--input",
                    str(input_path),
                    "--json",
                ]
            )
            after = json.loads(input_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["source_mode"], "memory")
        self.assertGreaterEqual(data["count"], 1)
        self.assertEqual(after, original)
        self.assertFalse(data["runtime_influence"])

    def test_learning_candidate_detail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            candidate = candidate_record()
            input_path = write_json(Path(tempdir), "candidates.json", {"candidates": [candidate]})

            code, stdout, _ = run_cli(
                [
                    "learning",
                    "candidate-detail",
                    "--input",
                    str(input_path),
                    "--candidate-id",
                    candidate["candidate_id"],
                    "--json",
                ]
            )
            after = json.loads(input_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["candidate"]["candidate_id"], candidate["candidate_id"])
        self.assertEqual(after, {"candidates": [candidate]})
        self.assertTrue(data["read_only"])

    def test_learning_semantic_context(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            candidate = candidate_record(status="UNDER_REVIEW")
            candidate_path = write_json(Path(tempdir), "candidate.json", candidate)
            semantic_path = write_json(
                Path(tempdir),
                "semantic.json",
                semantic_records(candidate["candidate_id"]),
            )

            code, stdout, _ = run_cli(
                [
                    "learning",
                    "semantic-context",
                    "--candidate-input",
                    str(candidate_path),
                    "--semantic-input",
                    str(semantic_path),
                    "--json",
                ]
            )

        self.assertEqual(code, 0)
        data = json.loads(stdout)
        attached = data["candidate"]
        self.assertTrue(data["semantic_context_attached"])
        self.assertTrue(data["semantic_context_is_reviewer_assist_only"])
        self.assertTrue(data["semantic_context_is_not_source_evidence"])
        self.assertEqual(attached["confidence"], candidate["confidence"])
        self.assertEqual(attached["status"], candidate["status"])
        self.assertEqual(attached["source_evidence"], candidate["source_evidence"])
        self.assertFalse(attached["runtime_influence"])
        self.assertTrue(attached["semantic_context"]["reviewer_assist"])

    def test_learning_review_actor_requirement(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            candidate_path = write_json(Path(tempdir), "candidate.json", candidate_record())
            for action in cli.LEARNING_REVIEW_ACTIONS:
                with self.subTest(action=action):
                    stdout = io.StringIO()
                    stderr = io.StringIO()
                    with self.assertRaises(SystemExit) as raised:
                        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                            cli.main(
                                [
                                    "learning",
                                    "review",
                                    "--input",
                                    str(candidate_path),
                                    "--action",
                                    action,
                                ]
                            )
                    self.assertEqual(raised.exception.code, 2)
                    self.assertIn("--actor", stderr.getvalue())

    def test_learning_review_approval_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            candidate = candidate_record(status="UNDER_REVIEW")
            candidate_path = write_json(Path(tempdir), "candidate.json", candidate)

            code, stdout, _ = run_cli(
                [
                    "learning",
                    "review",
                    "--input",
                    str(candidate_path),
                    "--action",
                    "approve-for-implementation",
                    "--actor",
                    "reviewer@example.com",
                    "--json",
                ]
            )

        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["candidate"]["status"], "APPROVED_FOR_IMPLEMENTATION")
        self.assertIn("approved for implementation only, not runtime activation", stdout)
        self.assertFalse(data["candidate"]["runtime_influence"])
        self.assertTrue(data["candidate"]["requires_human_review"])

    def test_learning_review_materialization_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            candidate = candidate_record(status="APPROVED_FOR_IMPLEMENTATION")
            candidate_path = write_json(Path(tempdir), "candidate.json", candidate)

            missing_code, missing_stdout, _ = run_cli(
                [
                    "learning",
                    "review",
                    "--input",
                    str(candidate_path),
                    "--action",
                    "attach-materialization",
                    "--actor",
                    "reviewer@example.com",
                ]
            )
            code, stdout, _ = run_cli(
                [
                    "learning",
                    "review",
                    "--input",
                    str(candidate_path),
                    "--action",
                    "attach-materialization",
                    "--actor",
                    "reviewer@example.com",
                    "--materialization-reference",
                    "commit:abc123",
                    "--json",
                ]
            )

        self.assertEqual(missing_code, 1)
        self.assertIn("materialization_reference", missing_stdout)
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["candidate"]["status"], "APPROVED_FOR_IMPLEMENTATION")
        self.assertEqual(data["candidate"]["materialization_reference"], "commit:abc123")
        self.assertFalse(data["candidate"]["runtime_influence"])
        self.assertFalse(data["governance_decision"]["runtime_influence"])

    def test_learning_export(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            directory = Path(tempdir)
            candidate = candidate_record()
            input_path = write_json(directory, "candidate.json", candidate)
            output_path = directory / "export.json"

            code, stdout, _ = run_cli(
                ["learning", "export", "--input", str(input_path), "--kind", "candidates"]
            )
            output_path.write_text("existing\n", encoding="utf-8")
            blocked_code, blocked_stdout, _ = run_cli(
                [
                    "learning",
                    "export",
                    "--input",
                    str(input_path),
                    "--kind",
                    "candidates",
                    "--output",
                    str(output_path),
                ]
            )
            forced_code, forced_stdout, _ = run_cli(
                [
                    "learning",
                    "export",
                    "--input",
                    str(input_path),
                    "--kind",
                    "candidates",
                    "--output",
                    str(output_path),
                    "--force",
                ]
            )
            file_data = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["kind"], "candidates")
        self.assertEqual(data["candidates"][0]["candidate_id"], candidate["candidate_id"])
        self.assertEqual(blocked_code, 1)
        self.assertIn("already exists", blocked_stdout)
        self.assertEqual(forced_code, 0)
        self.assertEqual(json.loads(forced_stdout)["output_path"], str(output_path))
        self.assertEqual(file_data["kind"], "candidates")

    def test_learning_validate(self) -> None:
        code, stdout, _ = run_cli(["learning", "validate", "--json"])

        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertTrue(data["success"])
        self.assertGreater(data["tests_run"], 0)
        self.assertFalse(data["runtime_influence"])
        self.assertTrue(data["local_validation_only"])

    def test_no_unsafe_runtime_operations(self) -> None:
        text = read_text(CLI_PATH)
        lowered = text.lower()

        self.assertNotIn("oracledb", lowered)
        self.assertNotIn("requests.", lowered)
        self.assertNotIn("requests(", lowered)
        self.assertNotIn("subprocess", lowered)
        self.assertNotIn("git ", lowered)
        self.assertNotIn("runtime_influence=True", text)
        for unsafe_name in (
            "activate_candidate",
            "apply_candidate_to_runtime",
            "modify_parser_logic",
            "modify_scoring_logic",
            "modify_recommendation_logic",
        ):
            self.assertNotIn(unsafe_name, lowered)

    def test_runtime_import_isolation(self) -> None:
        self.assert_no_cli_learning_imports(ROOT / "scripts" / "run_analysis.py")
        runtime_paths = [
            ROOT / "src" / "parser",
            ROOT / "src" / "parsing",
            ROOT / "src" / "analysis",
            ROOT / "src" / "recommendation",
            ROOT / "src" / "recommendations",
            ROOT / "src" / "scoring",
            ROOT / "src" / "decision",
        ]

        checked_files: list[Path] = []
        for path in runtime_paths:
            if path.is_dir():
                checked_files.extend(sorted(path.rglob("*.py")))
            elif path.is_file():
                checked_files.append(path)

        self.assertTrue(checked_files, "expected runtime files to inspect")
        for path in checked_files:
            self.assert_no_cli_learning_imports(path)

    def test_documentation_exists_and_contains_required_boundary_phrases(self) -> None:
        self.assertTrue(DOC_PATH.is_file())
        text = read_text(DOC_PATH).lower()

        for phrase in (
            "local and deterministic",
            "no runtime activation",
            "approved for implementation only",
            "runtime_influence=false",
            "requires_human_review=true",
            "actor required",
            "no db writes",
            "no oracle agent memory dependency",
            "no network dependency",
            "dashboard interactivity remains separate and read-only",
        ):
            self.assertIn(phrase, text)

    def assert_no_cli_learning_imports(self, path: Path) -> None:
        if not path.exists():
            return
        tree = ast.parse(read_text(path), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported_modules = [node.module or ""]
            else:
                continue
            for module_name in imported_modules:
                self.assertNotEqual(module_name, "scripts.awr_memory_cli")
                self.assertFalse(module_name.startswith("src.learning"))


if __name__ == "__main__":
    unittest.main()
