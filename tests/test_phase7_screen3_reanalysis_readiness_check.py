from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_phase7_screen3_reanalysis_readiness_check.py"
README = ROOT / "docs" / "architecture" / "README.md"


class Phase7Screen3ReanalysisReadinessCheckTests(unittest.TestCase):
    def test_script_exists_and_compiles(self) -> None:
        self.assertTrue(SCRIPT.is_file())
        compile(SCRIPT.read_text(encoding="utf-8"), str(SCRIPT), "exec")

    def test_text_output_passes(self) -> None:
        completed = self.run_script()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Phase 7 Screen 3 re-analysis readiness passed.", completed.stdout)
        self.assertIn("screen3_reanalysis_ready=true", completed.stdout)
        self.assertIn("backend_execution_performed=false", completed.stdout)

    def test_json_output_valid(self) -> None:
        completed = self.run_script("--json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)

        self.assertTrue(payload["success"])
        self.assertTrue(payload["screen3_reanalysis_ready"])
        self.assertTrue(payload["missing_metric_handling_ready"])
        self.assertFalse(payload["backend_execution_performed"])
        self.assertFalse(payload["run_analysis_called"])
        self.assertFalse(payload["object_storage_called"])
        self.assertFalse(payload["local_file_read_performed"])
        self.assertFalse(payload["db_lookup_performed"])
        self.assertFalse(payload["phase4i_mutated"])

    def test_readme_links_docs(self) -> None:
        text = README.read_text(encoding="utf-8", errors="ignore")
        self.assertIn("phase7ao_reanalysis_validation_readiness.md", text)
        self.assertIn("phase7ao_missing_metric_evidence_availability.md", text)

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            (sys.executable, str(SCRIPT), *args),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
