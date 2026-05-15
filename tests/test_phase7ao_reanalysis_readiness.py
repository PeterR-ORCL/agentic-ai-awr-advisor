from __future__ import annotations

import ast
import importlib
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
MODULE_PATH = ROOT / "src" / "learning" / "reanalysis_readiness.py"

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

FORBIDDEN_FUNCTION_NAMES = (
    "execute_analysis",
    "execute_reanalysis",
    "call_object_storage",
    "read_local_file",
    "query_database",
    "regenerate_dashboard",
    "mutate_phase4i",
    "auto_execute",
    "autonomous_execute",
)

FORBIDDEN_SOURCE_SNIPPETS = (
    "execute_analysis(",
    "execute_reanalysis(",
    "call_object_storage(",
    "read_local_file(",
    "query_database(",
    "regenerate_dashboard(",
    "mutate_phase4i(",
    "auto_execute(",
    "autonomous_execute(",
    "run_analysis(",
    "run_analysis.py",
    "requests.",
    "subprocess.",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


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


class Phase7AOReAnalysisReadinessTests(unittest.TestCase):
    @staticmethod
    def module():
        return importlib.import_module("src.learning.reanalysis_readiness")

    def test_01_module_import_safety(self) -> None:
        module = self.module()
        self.assertTrue(hasattr(module, "EvidenceAvailabilityRecord"))
        self.assertTrue(hasattr(module, "EvidenceAvailabilitySummary"))
        self.assertTrue(hasattr(module, "ReAnalysisReadinessResult"))

        imports = imported_modules(MODULE_PATH)
        for imported in imports:
            for forbidden in FORBIDDEN_IMPORT_PREFIXES:
                with self.subTest(imported=imported, forbidden=forbidden):
                    self.assertFalse(
                        imported == forbidden or imported.startswith(f"{forbidden}."),
                        f"forbidden import {imported}",
                    )

    def test_docs_exist_and_contain_boundaries(self) -> None:
        docs = [
            DOCS / "phase7ao_reanalysis_validation_readiness.md",
            DOCS / "phase7ao_missing_metric_evidence_availability.md",
        ]
        for path in docs:
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file())

        combined = "\n".join(read_text(path).lower() for path in docs)
        required = (
            "validation/readiness is not execution",
            "no backend execution",
            "no run_analysis.py call",
            "no object storage call",
            "no file read",
            "no db lookup",
            "no phase 4i mutation",
            "missing metric handling is validation only",
            "screen 2 evidence review model remains future 7aq.1",
            "phase 8 sizing/tco is not implemented",
            "evidence availability handling does not alter diagnosis",
            "evidence availability handling does not alter scoring",
            "evidence availability handling does not alter recommendations",
            "missing metric review candidates are recommendations for future workflow only",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_evidence_record_validation(self) -> None:
        module = self.module()
        record = module.EvidenceAvailabilityRecord(
            evidence_id=module.create_evidence_id("DB CPU", "metric", "AWR-1", "RUN-1"),
            evidence_name="DB CPU",
            evidence_type="metric",
            source_report_id="AWR-1",
            source_run_id="RUN-1",
            availability_status="available",
            reliability_status="reliable",
            missing_reason="not_applicable",
            confidence_impact="none",
        )
        self.assertIs(module.validate_evidence_availability_record(record), record)

        with self.assertRaises(module.ReAnalysisReadinessError):
            module.EvidenceAvailabilityRecord(
                evidence_id="BAD",
                evidence_name="DB CPU",
                evidence_type="bad_type",
            )

    def test_classifies_missing_unavailable_unsupported_not_extracted_and_unreliable(self) -> None:
        module = self.module()
        cases = [
            ({"name": "DB CPU", "evidence_type": "metric", "available": True, "value": 10}, "available"),
            ({"name": "ASH", "evidence_type": "metric", "available": False}, "missing"),
            ({"name": "IO metric", "evidence_type": "metric", "value": None}, "unavailable"),
            (
                {
                    "name": "RAC metric",
                    "evidence_type": "topology",
                    "supported": False,
                    "missing_reason": "unsupported_by_topology",
                },
                "unsupported",
            ),
            ({"name": "Wait class", "evidence_type": "wait_event", "extracted": False}, "not_extracted"),
            (
                {
                    "name": "Overall score",
                    "evidence_type": "score",
                    "value": 70,
                    "reliability": "unreliable",
                },
                "not_reliable",
            ),
        ]
        for source, expected_status in cases:
            with self.subTest(expected_status=expected_status):
                record = module.classify_evidence_availability(source)
                self.assertEqual(record.availability_status, expected_status)

    def test_review_recommendation_flags(self) -> None:
        module = self.module()
        parser_gap = module.classify_evidence_availability(
            {"name": "Wait class", "evidence_type": "wait_event", "extracted": False}
        )
        source_gap = module.classify_evidence_availability(
            {
                "name": "ASH sample",
                "evidence_type": "metric",
                "available": False,
                "missing_reason": "source_misconfigured",
            }
        )
        scoring_gap = module.classify_evidence_availability(
            {"name": "Overall score", "evidence_type": "score", "value": None}
        )

        self.assertTrue(parser_gap.parser_review_recommended)
        self.assertTrue(source_gap.source_review_recommended)
        self.assertTrue(scoring_gap.scoring_review_recommended)

    def test_evidence_summary_validation(self) -> None:
        module = self.module()
        summary = module.build_evidence_availability_summary(
            [
                {"name": "DB CPU", "evidence_type": "metric", "available": True, "value": 10},
                {"name": "Wait class", "evidence_type": "wait_event", "extracted": False},
                {"name": "Overall score", "evidence_type": "score", "value": None},
            ]
        )
        self.assertEqual(summary.total_evidence_count, 3)
        self.assertEqual(summary.available_count, 1)
        self.assertEqual(summary.missing_count, 2)
        self.assertEqual(summary.parser_gap_count, 1)
        self.assertTrue(summary.parser_review_recommended)
        self.assertTrue(summary.scoring_review_recommended)
        self.assertIs(module.validate_evidence_availability_summary(summary), summary)

    def test_reanalysis_readiness_result_validation_and_runtime_flags(self) -> None:
        module = self.module()
        result = module.evaluate_reanalysis_readiness(context_label="unit")

        self.assertTrue(result.screen3_reanalysis_ready)
        self.assertEqual(result.readiness_status, "READY_METADATA_ONLY")
        self.assertFalse(result.backend_execution_performed)
        self.assertFalse(result.run_analysis_called)
        self.assertFalse(result.object_storage_called)
        self.assertFalse(result.local_file_read_performed)
        self.assertFalse(result.db_lookup_performed)
        self.assertFalse(result.phase4i_mutated)
        self.assertFalse(result.dashboard_regenerated)
        self.assertIs(module.validate_reanalysis_readiness_result(result), result)

        with self.assertRaises(module.ReAnalysisReadinessError):
            module.ReAnalysisReadinessResult(
                readiness_id="BAD",
                screen3_reanalysis_ready=True,
                source_selection_ready=True,
                request_model_ready=True,
                controller_ready=True,
                comparison_ready=True,
                missing_metric_handling_ready=True,
                action_ui_preview_only=True,
                backend_execution_performed=True,
                run_analysis_called=False,
                object_storage_called=False,
                local_file_read_performed=False,
                db_lookup_performed=False,
                phase4i_mutated=False,
                dashboard_regenerated=False,
                readiness_status="READY_METADATA_ONLY",
                denied_reasons=[],
                warnings=[],
                required_next_steps=[],
            )

    def test_readiness_needs_evidence_review_when_handling_not_ready(self) -> None:
        module = self.module()
        result = module.evaluate_reanalysis_readiness(
            missing_metric_handling_ready=False,
            context_label="needs-evidence",
        )
        self.assertFalse(result.screen3_reanalysis_ready)
        self.assertEqual(result.readiness_status, "NEEDS_EVIDENCE_REVIEW")

    def test_serialization_round_trips(self) -> None:
        module = self.module()
        record = module.classify_evidence_availability(
            {
                "name": "DB CPU",
                "evidence_type": "metric",
                "available": True,
                "value": 10,
                "source_report_id": "AWR-1",
            }
        )
        summary = module.build_evidence_availability_summary([record])
        readiness = module.evaluate_reanalysis_readiness(context_label="round-trip")

        self.assertEqual(
            module.evidence_availability_record_to_dict(
                module.evidence_availability_record_from_dict(
                    module.evidence_availability_record_to_dict(record)
                )
            ),
            module.evidence_availability_record_to_dict(record),
        )
        self.assertEqual(
            module.evidence_availability_summary_to_dict(
                module.evidence_availability_summary_from_dict(
                    module.evidence_availability_summary_to_dict(summary)
                )
            ),
            module.evidence_availability_summary_to_dict(summary),
        )
        self.assertEqual(
            module.reanalysis_readiness_result_to_dict(
                module.reanalysis_readiness_result_from_dict(
                    module.reanalysis_readiness_result_to_dict(readiness)
                )
            ),
            module.reanalysis_readiness_result_to_dict(readiness),
        )

    def test_no_execution_functions_or_source_snippets(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, names)

        source = read_text(MODULE_PATH)
        for snippet in FORBIDDEN_SOURCE_SNIPPETS:
            with self.subTest(snippet=snippet):
                self.assertNotIn(snippet, source)


if __name__ == "__main__":
    unittest.main()
