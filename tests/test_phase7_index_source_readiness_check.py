from __future__ import annotations

import json
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_phase7_index_source_readiness_check.py"
README = ROOT / "docs" / "architecture" / "README.md"

REQUIRED_CATEGORIES = (
    "source_mode_entry",
    "source_status",
    "object_storage_config",
    "handoff_metadata",
    "dashboard_panels",
    "validation_script",
    "documentation_complete",
    "runtime_safety",
)

README_LINKS = (
    "phase7bt_index_screen3_handoff.md",
    "phase7bt_index_screen3_handoff_model.md",
    "phase7_index_source_validation_matrix.md",
    "phase7_index_source_readiness.md",
    "phase7_index_source_release_certification.md",
    "phase7_index_source_operational_checklist.md",
)


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (sys.executable, str(SCRIPT), *args),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


class Phase7IndexSourceReadinessCheckTests(unittest.TestCase):
    _json_payload: dict[str, object] | None = None
    _text_result: subprocess.CompletedProcess[str] | None = None

    def test_readiness_script_exists_and_compiles(self) -> None:
        self.assertTrue(SCRIPT.is_file(), SCRIPT)
        with tempfile.TemporaryDirectory() as tempdir:
            py_compile.compile(
                str(SCRIPT),
                cfile=str(Path(tempdir) / "run_phase7_index_source_readiness_check.pyc"),
                doraise=True,
            )

    def test_text_output_passes(self) -> None:
        completed = self.text_result()
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn("Phase 7 index source readiness passed.", completed.stdout)
        self.assertIn("index_source_ready=true", completed.stdout)

    def test_json_output_valid(self) -> None:
        payload = self.json_payload()
        self.assertEqual(payload["phase"], "Phase 7BQ-7BT")
        self.assertEqual(payload["command"], "run_phase7_index_source_readiness_check")
        self.assertIs(payload["success"], True)
        self.assertIs(payload["index_source_ready"], True)

    def test_readiness_categories_present(self) -> None:
        payload = self.json_payload()
        categories = payload["readiness_categories"]  # type: ignore[index]
        for category in REQUIRED_CATEGORIES:
            with self.subTest(category=category):
                self.assertIn(category, categories)
                self.assertIs(categories[category], True)

    def test_no_handoff_or_source_execution_flags(self) -> None:
        payload = self.json_payload()
        for field_name in (
            "handoff_performed",
            "screen3_state_updated",
            "backend_request_created",
            "source_access_performed",
            "object_storage_called",
            "local_file_read_performed",
            "db_lookup_performed",
            "run_analysis_called",
            "phase8_implemented",
        ):
            with self.subTest(field_name=field_name):
                self.assertIs(payload[field_name], False)
        self.assertIs(payload["future_em_extract_placeholder"], True)

    def test_readme_links_docs(self) -> None:
        text = README.read_text(encoding="utf-8", errors="ignore")
        for link in README_LINKS:
            with self.subTest(link=link):
                self.assertIn(link, text)

    @classmethod
    def json_payload(cls) -> dict[str, object]:
        if cls._json_payload is None:
            completed = run_script("--json")
            if completed.returncode != 0:
                raise AssertionError(completed.stderr or completed.stdout)
            cls._json_payload = json.loads(completed.stdout)
        return cls._json_payload

    @classmethod
    def text_result(cls) -> subprocess.CompletedProcess[str]:
        if cls._text_result is None:
            cls._text_result = run_script()
        return cls._text_result


if __name__ == "__main__":
    unittest.main()
