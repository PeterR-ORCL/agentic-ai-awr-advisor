from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from src.models.decision import AwrDecision
from src.validation.phase45_validation_harness import (
    load_manifest_entries,
    normalize_decision_for_validation,
    run_validation_harness,
)

CSV_HEADER_OLD = (
    "begin_time,db_name,dbid,expected_primary_issue,expected_secondary_issues,"
    "expected_status,file,notes,scenario_name\n"
)

CSV_HEADER_NEW = (
    "file_name,scenario_type,dominant_domain,secondary_domains,description,"
    "expected_behavior,db_name,dbid,instance_name,snapshot_start,snapshot_end\n"
)


class Phase45ValidationHarnessTests(unittest.TestCase):
    def test_manifest_csv_preferred_over_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "manifest.csv").write_text(
                CSV_HEADER_OLD
                + "2026-04-01 00:00:00,VALDB,1,CPU,,WARNING,case_a.out,note,CSV_CASE\n",
                encoding="utf-8",
            )
            (root / "manifest.json").write_text(
                json.dumps(
                    {
                        "dataset": "test",
                        "reports": [
                            {
                                "file_name": "case_b.out",
                                "scenario_type": "MULTI_DOMAIN",
                                "dominant_domain": "IO",
                                "secondary_domains": ["CPU"],
                                "expected_behavior": "moderate-high severity",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            entries, manifest_source = load_manifest_entries(root)

        self.assertEqual(entries[0].scenario_name, "CSV_CASE")
        self.assertTrue(manifest_source.endswith("manifest.csv"))

    def test_explicit_manifest_path_overrides_directory_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            explicit_manifest = root / "override.json"
            explicit_manifest.write_text(
                json.dumps(
                    {
                        "dataset": "test",
                        "reports": [
                            {
                                "file_name": "case_b.out",
                                "scenario_type": "MULTI_DOMAIN",
                                "dominant_domain": "IO",
                                "secondary_domains": ["CPU"],
                                "expected_behavior": "moderate-high severity",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            entries, manifest_source = load_manifest_entries(
                root,
                manifest_path=explicit_manifest,
            )

        self.assertEqual(entries[0].file, "case_b.out")
        self.assertEqual(entries[0].expected_primary_issue, "IO")
        self.assertEqual(entries[0].expected_secondary_issues, ["CPU"])
        self.assertEqual(entries[0].expected_status, "WARNING")
        self.assertTrue(manifest_source.endswith("override.json"))

    def test_new_manifest_schema_is_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "manifest.csv").write_text(
                CSV_HEADER_NEW
                + "case_b.out,MULTI_DOMAIN,IO,CPU,desc,moderate-high severity,VALDB,1,val1,01-Apr-26 00:00:00,01-Apr-26 01:00:00\n",
                encoding="utf-8",
            )

            entries, _ = load_manifest_entries(root)

        self.assertEqual(entries[0].file, "case_b.out")
        self.assertEqual(entries[0].scenario_name, "case_b")
        self.assertEqual(entries[0].expected_primary_issue, "IO")
        self.assertEqual(entries[0].expected_secondary_issues, ["CPU"])
        self.assertEqual(entries[0].expected_status, "WARNING")

    def test_json_manifest_reports_payload_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "dataset": "test",
                        "report_count": 1,
                        "reports": [
                            {
                                "file_name": "case_b.out",
                                "scenario_type": "RECOVERY",
                                "dominant_domain": "NONE",
                                "secondary_domains": ["CPU"],
                                "expected_behavior": "stable or monitor",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            entries, _ = load_manifest_entries(root, manifest_path=manifest)

        self.assertEqual(entries[0].expected_primary_issue, "NONE")
        self.assertEqual(entries[0].expected_secondary_issues, ["CPU"])
        self.assertEqual(entries[0].expected_status, "OK")

    def test_expected_primary_issue_none_is_supported(self) -> None:
        decision = AwrDecision(
            awr_id=1,
            overall_status="OK",
            primary_issue=None,
            secondary_issues=[],
            severity_score=10.0,
            confidence=0.5,
            evidence={
                "domain_scores": {
                    domain: 0.0
                    for domain in ["CPU", "IO", "MEMORY", "COMMIT", "RAC", "ADG"]
                }
            },
        )

        actual_primary_issue, actual_secondary_issues = normalize_decision_for_validation(
            decision
        )

        self.assertEqual(actual_primary_issue, "NONE")
        self.assertEqual(actual_secondary_issues, [])

    def test_local_harness_runs_decision_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "manifest.csv").write_text(
                CSV_HEADER_OLD
                + "2026-04-01 00:00:00,VALDB,1,CPU,,WARNING,case_a.out,note,CASE_A\n",
                encoding="utf-8",
            )
            (root / "case_a.out").write_text("stub", encoding="utf-8")

            def parser(file_path: str | Path) -> dict[str, str]:
                return {"file_path": str(file_path)}

            def feature_vector_builder(
                parse_result: dict[str, str],
                awr_id: int,
                source_system_id: int,
            ) -> dict[str, str]:
                del parse_result, awr_id, source_system_id
                return {"feature_json": json.dumps({"DB_CPU_PCT_DB_TIME": 45.0})}

            def decision_builder(**kwargs: object) -> AwrDecision:
                del kwargs
                return AwrDecision(
                    awr_id=1,
                    overall_status="WARNING",
                    primary_issue="CPU",
                    secondary_issues=[],
                    severity_score=35.0,
                    confidence=0.71,
                    evidence={"domain_scores": {"CPU": 0.4}},
                )

            result = run_validation_harness(
                input_dir=root,
                parser=parser,
                feature_vector_builder=feature_vector_builder,
                decision_builder=decision_builder,
            )

        self.assertEqual(result.case_count, 1)
        self.assertEqual(result.passed_count, 1)
        self.assertEqual(result.cases[0].actual_primary_issue, "CPU")
        self.assertIn("decision", result.cases[0].output)
        diagnostics = result.cases[0].validation_diagnostics
        self.assertFalse(diagnostics["normalized_to_none"])
        self.assertEqual(diagnostics["normalized_primary_issue"], "CPU")


if __name__ == "__main__":
    unittest.main()
