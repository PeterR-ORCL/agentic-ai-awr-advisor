from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
import types

from src.models.decision import AwrDecision
from src.models.parse_result import ParseResult
from src.models.run_metadata import RunMetadata
from src.validation.phase45_validation_harness import (
    _derive_pressure_context,
    _parse_seeded_scoring_weights,
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
    "expected_behavior,db_name,dbid,instance_name,snapshot_start,snapshot_end,"
    "expected_evidence_layers,expected_topology_context,expected_pressure_context\n"
)


class Phase45ValidationHarnessTests(unittest.TestCase):
    def test_seeded_scoring_weights_include_new_global_feature_rows(self) -> None:
        feature_codes = {
            row["feature_code"] for row in _parse_seeded_scoring_weights()
        }

        self.assertTrue(
            {
                "TEMP_IO_PRESSURE",
                "HARD_PARSE_PCT",
                "FREE_BUFFER_WAIT_PRESSURE",
                "BUFFER_BUSY_PRESSURE",
                "READ_BY_OTHER_SESSION_PRESSURE",
                "ENQUEUE_COMMIT_PRESSURE",
                "REDO_CONTENTION_PRESSURE",
                "GC_BUFFER_BUSY_PCT_DB_TIME",
                "RAC_BUFFER_BUSY_PRESSURE",
            }.issubset(feature_codes)
        )

    def test_feature_payload_defaults_required_global_signals_to_zero(self) -> None:
        build_feature_payload = _load_build_feature_payload()
        parse_result = ParseResult(
            run_metadata=RunMetadata(
                source_file_name="case.out",
                source_file_path="",
                parse_timestamp="2026-04-27T00:00:00",
            )
        )

        feature_payload = build_feature_payload(parse_result)
        feature_json = feature_payload["feature_json"]

        for feature_code in (
            "TEMP_IO_PRESSURE",
            "WORKAREA_ONEPASS_PCT",
            "WORKAREA_MULTIPASS_PCT",
            "HARD_PARSES_PER_SEC",
            "HARD_PARSE_PCT",
            "BUFFER_CACHE_HIT_RATIO_PCT",
            "LIBRARY_CACHE_HIT_RATIO_PCT",
            "FREE_BUFFER_WAIT_PRESSURE",
            "BUFFER_BUSY_PRESSURE",
            "READ_BY_OTHER_SESSION_PRESSURE",
            "ENQUEUE_COMMIT_PRESSURE",
            "REDO_CONTENTION_PRESSURE",
            "GC_BUFFER_BUSY_PCT_DB_TIME",
            "RAC_BUFFER_BUSY_PRESSURE",
        ):
            self.assertIn(feature_code, feature_json)
            self.assertEqual(feature_json[feature_code], 0.0)

    def test_feature_payload_aggregates_contention_pressure_signals(self) -> None:
        build_feature_payload = _load_build_feature_payload()
        parse_result = ParseResult(
            run_metadata=RunMetadata(
                source_file_name="case.out",
                source_file_path="",
                parse_timestamp="2026-04-27T00:00:00",
            ),
            wait_events=[
                {
                    "event_name": "free buffer waits",
                    "pct_db_time": 2.5,
                    "avg_wait_ms": 1.0,
                    "wait_class": "Concurrency",
                },
                {
                    "event_name": "buffer busy waits",
                    "pct_db_time": 3.0,
                    "avg_wait_ms": 1.5,
                    "wait_class": "Concurrency",
                },
                {
                    "event_name": "read by other session",
                    "pct_db_time": 4.0,
                    "avg_wait_ms": 2.0,
                    "wait_class": "User I/O",
                },
                {
                    "event_name": "enq: TX - row lock contention",
                    "pct_db_time": 1.5,
                    "avg_wait_ms": 3.0,
                    "wait_class": "Application",
                },
                {
                    "event_name": "redo allocation",
                    "pct_db_time": 1.0,
                    "avg_wait_ms": 1.0,
                    "wait_class": "Commit",
                },
                {
                    "event_name": "gc buffer busy acquire",
                    "pct_db_time": 2.0,
                    "avg_wait_ms": 1.0,
                    "wait_class": "Cluster",
                },
                {
                    "event_name": "gc current block busy",
                    "pct_db_time": 1.0,
                    "avg_wait_ms": 1.0,
                    "wait_class": "Cluster",
                },
            ],
            topology_signals={
                "is_rac": True,
                "gc_buffer_busy_pct_db_time": 2.0,
            },
        )

        feature_payload = build_feature_payload(parse_result)
        feature_json = feature_payload["feature_json"]

        self.assertEqual(feature_json["FREE_BUFFER_WAIT_PRESSURE"], 2.5)
        self.assertEqual(feature_json["BUFFER_BUSY_PRESSURE"], 3.0)
        self.assertEqual(feature_json["READ_BY_OTHER_SESSION_PRESSURE"], 4.0)
        self.assertEqual(feature_json["ENQUEUE_COMMIT_PRESSURE"], 1.5)
        self.assertEqual(feature_json["REDO_CONTENTION_PRESSURE"], 1.0)
        self.assertEqual(feature_json["GC_BUFFER_BUSY_PCT_DB_TIME"], 2.0)
        self.assertEqual(feature_json["RAC_BUFFER_BUSY_PRESSURE"], 3.0)

    def test_absent_zero_defaulted_signals_do_not_count_as_scoring_evidence(self) -> None:
        build_feature_payload = _load_build_feature_payload()
        score_weighted_components = _load_score_weighted_components()
        parse_result = ParseResult(
            run_metadata=RunMetadata(
                source_file_name="case.out",
                source_file_path="",
                parse_timestamp="2026-04-27T00:00:00",
            ),
            cpu_metrics=[
                {"metric_name": "DB Time(s)", "per_second": 10.0, "per_transaction": 1.0},
                {"metric_name": "DB CPU(s)", "per_second": 5.0, "per_transaction": 0.5},
                {"metric_name": "Redo size", "per_second": 1000.0},
            ],
            top_sql=[{"pct_total": 20.0}],
        )

        feature_payload = build_feature_payload(parse_result)
        feature_json = feature_payload["feature_json"]
        components = score_weighted_components(feature_json, _parse_seeded_scoring_weights())
        component_by_code = {component["feature_code"]: component for component in components}

        for feature_code in (
            "TEMP_IO_PRESSURE",
            "FREE_BUFFER_WAIT_PRESSURE",
            "BUFFER_BUSY_PRESSURE",
            "READ_BY_OTHER_SESSION_PRESSURE",
            "ENQUEUE_COMMIT_PRESSURE",
            "REDO_CONTENTION_PRESSURE",
            "GC_BUFFER_BUSY_PCT_DB_TIME",
            "RAC_BUFFER_BUSY_PRESSURE",
        ):
            self.assertEqual(feature_json[feature_code], 0.0)
            self.assertIsNone(component_by_code[feature_code]["raw_value"])

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
                + (
                    "case_b.out,MULTI_DOMAIN,IO,CPU,desc,moderate-high severity,"
                    "VALDB,1,val1,01-Apr-26 00:00:00,01-Apr-26 01:00:00,"
                    "CONCURRENCY,RAC,\"CPU,IO\"\n"
                ),
                encoding="utf-8",
            )

            entries, _ = load_manifest_entries(root)

        self.assertEqual(entries[0].file, "case_b.out")
        self.assertEqual(entries[0].scenario_name, "case_b")
        self.assertEqual(entries[0].expected_primary_issue, "IO")
        self.assertEqual(entries[0].expected_secondary_issues, ["CPU"])
        self.assertEqual(entries[0].expected_evidence_layers, ["CONCURRENCY"])
        self.assertEqual(entries[0].expected_topology_context, ["RAC"])
        self.assertEqual(entries[0].expected_pressure_context, ["CPU", "IO"])
        self.assertEqual(entries[0].expected_status, "WARNING")

    def test_old_manifest_schema_defaults_optional_contract_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "manifest.csv").write_text(
                CSV_HEADER_OLD
                + "2026-04-01 00:00:00,VALDB,1,CPU,IO,WARNING,case_a.out,note,CASE_A\n",
                encoding="utf-8",
            )

            entries, _ = load_manifest_entries(root)

        self.assertEqual(entries[0].expected_evidence_layers, [])
        self.assertEqual(entries[0].expected_topology_context, [])
        self.assertEqual(entries[0].expected_pressure_context, [])

    def test_pressure_context_preserves_canonical_order(self) -> None:
        context = _derive_pressure_context(
            {
                "APPLY_LAG_SEC": 100.0,
                "GC_BUFFER_BUSY_PCT_DB_TIME": 3.0,
                "ENQUEUE_COMMIT_PRESSURE": 2.0,
                "BUFFER_BUSY_PRESSURE": 4.0,
                "USER_IO_PRESSURE": 8.0,
                "CPU_UTIL_P95": 75.0,
            }
        )

        self.assertEqual(context, ["CPU", "IO", "MEMORY", "COMMIT", "RAC", "ADG"])

    def test_pressure_context_contains_no_duplicates(self) -> None:
        context = _derive_pressure_context(
            {
                "CPU_UTIL_P95": 70.0,
                "DB_CPU_PCT_DB_TIME": 50.0,
                "USER_IO_PRESSURE": 10.0,
                "READ_LATENCY_MS": 12.0,
                "BUFFER_BUSY_PRESSURE": 5.0,
                "FREE_BUFFER_WAIT_PRESSURE": 4.0,
                "ENQUEUE_COMMIT_PRESSURE": 3.0,
                "LOG_FILE_SYNC_MS": 9.0,
                "GC_BUFFER_BUSY_PCT_DB_TIME": 2.0,
                "RAC_CONTENTION_FLAG": 1.0,
                "APPLY_LAG_SEC": 30.0,
                "REDO_TRANSPORT_ISSUE_FLAG": 1.0,
            }
        )

        self.assertEqual(len(context), len(set(context)))

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

    def test_feature_vector_logical_key_order_is_stable_and_within_capacity(self) -> None:
        (
            feature_key_order,
            logical_dimension_count,
            numeric_capacity,
        ) = _load_feature_vector_contract_constants()

        self.assertEqual(logical_dimension_count, len(feature_key_order))
        self.assertLessEqual(logical_dimension_count, numeric_capacity)
        self.assertEqual(feature_key_order[0], "cpu_pct")
        self.assertEqual(feature_key_order[-1], "feature_presence")
        self.assertIn("FREE_BUFFER_WAIT_PRESSURE", feature_key_order)
        self.assertIn("RAC_BUFFER_BUSY_PRESSURE", feature_key_order)

    def test_feature_vector_logical_dimension_count_matches_current_contract(self) -> None:
        (
            feature_key_order,
            logical_dimension_count,
            _numeric_capacity,
        ) = _load_feature_vector_contract_constants()

        self.assertEqual(logical_dimension_count, 139)
        self.assertEqual(len(set(feature_key_order)), logical_dimension_count)

    def test_concurrency_evidence_layer_is_compared_separately_from_secondary_domains(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "manifest.csv").write_text(
                CSV_HEADER_NEW
                + (
                    "case_a.out,MULTI_DOMAIN,CPU,COMMIT,desc,moderate-high severity,"
                    "VALDB,1,val1,01-Apr-26 00:00:00,01-Apr-26 01:00:00,"
                    "CONCURRENCY,,\n"
                ),
                encoding="utf-8",
            )
            (root / "case_a.out").write_text("stub", encoding="utf-8")

            parse_result = ParseResult(
                run_metadata=RunMetadata(
                    source_file_name="case_a.out",
                    source_file_path="",
                    parse_timestamp="2026-04-27T00:00:00",
                    begin_snapshot_time="2026-04-27 00:00:00",
                    end_snapshot_time="2026-04-27 01:00:00",
                ),
                wait_events=[
                    {
                        "event_name": "latch: cache buffers chains",
                        "wait_class": "Concurrency",
                    }
                ],
            )

            def parser(file_path: str | Path) -> ParseResult:
                del file_path
                return parse_result

            def feature_vector_builder(
                parse_result: ParseResult,
                awr_id: int,
                source_system_id: int,
            ) -> dict[str, object]:
                del parse_result, awr_id, source_system_id
                return {
                    "feature_json": json.dumps(
                        {
                            "CPU_UTIL_P95": 90.0,
                            "LOG_FILE_SYNC_MS": 12.0,
                            "topology_class": "RAC",
                        }
                    )
                }

            def decision_builder(**kwargs: object) -> AwrDecision:
                del kwargs
                return AwrDecision(
                    awr_id=1,
                    overall_status="WARNING",
                    primary_issue="CPU",
                    secondary_issues=["COMMIT"],
                    severity_score=40.0,
                    confidence=0.8,
                    evidence={"domain_scores": {"CPU": 11.0, "COMMIT": 8.0}},
                )

            result = run_validation_harness(
                input_dir=root,
                parser=parser,
                feature_vector_builder=feature_vector_builder,
                decision_builder=decision_builder,
            )

        self.assertEqual(result.passed_count, 1)
        self.assertEqual(result.cases[0].actual_secondary_issues, ["COMMIT"])
        self.assertEqual(result.cases[0].actual_evidence_layers, ["CONCURRENCY"])

    def test_topology_context_does_not_satisfy_canonical_secondary_expectation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "manifest.csv").write_text(
                CSV_HEADER_NEW
                + (
                    "case_a.out,SPARSE_PARTIAL,NONE,RAC,desc,stable or monitor,"
                    "VALDB,1,val1,01-Apr-26 00:00:00,01-Apr-26 01:00:00,"
                    ",RAC,\n"
                ),
                encoding="utf-8",
            )
            (root / "case_a.out").write_text("stub", encoding="utf-8")

            parse_result = ParseResult(
                run_metadata=RunMetadata(
                    source_file_name="case_a.out",
                    source_file_path="",
                    parse_timestamp="2026-04-27T00:00:00",
                    begin_snapshot_time="2026-04-27 00:00:00",
                    end_snapshot_time="2026-04-27 01:00:00",
                )
            )

            def parser(file_path: str | Path) -> ParseResult:
                del file_path
                return parse_result

            def feature_vector_builder(
                parse_result: ParseResult,
                awr_id: int,
                source_system_id: int,
            ) -> dict[str, object]:
                del parse_result, awr_id, source_system_id
                return {
                    "feature_json": json.dumps(
                        {
                            "is_rac": 1.0,
                            "topology_class": "RAC",
                        }
                    )
                }

            def decision_builder(**kwargs: object) -> AwrDecision:
                del kwargs
                return AwrDecision(
                    awr_id=1,
                    overall_status="OK",
                    primary_issue=None,
                    secondary_issues=[],
                    severity_score=10.0,
                    confidence=0.6,
                    evidence={"domain_scores": {"RAC": 0.0}},
                )

            result = run_validation_harness(
                input_dir=root,
                parser=parser,
                feature_vector_builder=feature_vector_builder,
                decision_builder=decision_builder,
            )

        self.assertEqual(result.cases[0].actual_topology_context, ["RAC"])
        self.assertEqual(result.cases[0].actual_secondary_issues, [])
        self.assertEqual(result.failed_count, 1)
        self.assertIn("secondary=NONE", result.cases[0].validation_diagnostics["mismatch_reason"])


if __name__ == "__main__":
    unittest.main()


def _load_build_feature_payload():
    try:
        from src.ingest.awr_adb_loader import _build_feature_payload
    except ModuleNotFoundError as exc:
        if exc.name != "dotenv":
            raise
        sys.modules.setdefault(
            "dotenv",
            types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None),
        )
        from src.ingest.awr_adb_loader import _build_feature_payload
    return _build_feature_payload


def _load_score_weighted_components():
    try:
        from src.ingest.awr_adb_loader import _score_weighted_components
    except ModuleNotFoundError as exc:
        if exc.name != "dotenv":
            raise
        sys.modules.setdefault(
            "dotenv",
            types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None),
        )
        from src.ingest.awr_adb_loader import _score_weighted_components
    return _score_weighted_components


def _load_feature_vector_contract_constants():
    try:
        from src.ingest.awr_adb_loader import (
            FEATURE_VECTOR_LOGICAL_DIMENSION_COUNT,
            FEATURE_VECTOR_LOGICAL_KEY_ORDER,
            FEATURE_VECTOR_NUMERIC_CAPACITY,
        )
    except ModuleNotFoundError as exc:
        if exc.name != "dotenv":
            raise
        sys.modules.setdefault(
            "dotenv",
            types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None),
        )
        from src.ingest.awr_adb_loader import (
            FEATURE_VECTOR_LOGICAL_DIMENSION_COUNT,
            FEATURE_VECTOR_LOGICAL_KEY_ORDER,
            FEATURE_VECTOR_NUMERIC_CAPACITY,
        )
    return (
        FEATURE_VECTOR_LOGICAL_KEY_ORDER,
        FEATURE_VECTOR_LOGICAL_DIMENSION_COUNT,
        FEATURE_VECTOR_NUMERIC_CAPACITY,
    )
