from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import datetime
import json
from inspect import signature
from pathlib import Path
import re
from typing import Any, Callable
import sys
import types

from src.analysis.decision_engine import (
    DOMAIN_ORDER,
    PRIMARY_QUALIFICATION_THRESHOLD,
    build_decision,
)
from src.analysis.scoring_adapter import build_decision_input_from_score_result
from src.analysis.trend_engine import compute_trend_features, detect_anomalies
from src.parser.awr_parser import parse_awr_file

MANIFEST_CSV_NAME = "manifest.csv"
MANIFEST_JSON_NAME = "manifest.json"
OUTPUT_VERSION = "phase4g"
OUTPUT_SOURCE = "phase4g-validation"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_PRESSURE_CONTEXT_ORDER = ("CPU", "IO", "MEMORY", "COMMIT", "RAC", "ADG")
PRESSURE_CONTEXT_RULES: tuple[
    tuple[str, tuple[str, ...], tuple[str, ...]],
    ...,
] = (
    ("CPU", ("CPU_UTIL_P95", "DB_CPU_PCT_DB_TIME", "AAS_PER_CPU"), ()),
    (
        "IO",
        (
            "READ_LATENCY_MS",
            "WRITE_LATENCY_MS",
            "USER_IO_PRESSURE",
            "READ_BY_OTHER_SESSION_PRESSURE",
            "TEMP_IO_PRESSURE",
        ),
        (),
    ),
    (
        "MEMORY",
        (
            "PGA_SPILL_PRESSURE",
            "TEMP_SPILL_PCT",
            "SORTS_DISK_PCT",
            "FREE_BUFFER_WAIT_PRESSURE",
            "BUFFER_BUSY_PRESSURE",
            "WORKAREA_ONEPASS_PCT",
            "WORKAREA_MULTIPASS_PCT",
        ),
        (),
    ),
    (
        "COMMIT",
        (
            "LOG_FILE_SYNC_MS",
            "LOG_WRITE_LATENCY_MS",
            "ENQUEUE_COMMIT_PRESSURE",
            "REDO_CONTENTION_PRESSURE",
            "COMMIT_PRESSURE",
        ),
        (),
    ),
    (
        "RAC",
        (
            "CLUSTER_WAIT_PCT_DB_TIME",
            "GC_CURRENT_WAIT_PCT_DB_TIME",
            "GC_CR_WAIT_PCT_DB_TIME",
            "GC_BUFFER_BUSY_PCT_DB_TIME",
            "RAC_BUFFER_BUSY_PRESSURE",
        ),
        ("INTERCONNECT_STRESS_FLAG", "RAC_CONTENTION_FLAG"),
    ),
    (
        "ADG",
        ("APPLY_LAG_SEC", "TRANSPORT_LAG_SEC"),
        (
            "REDO_TRANSPORT_ISSUE_FLAG",
            "FAILOVER_EVENT_FLAG",
            "ROLE_TRANSITION_FLAG",
            "POST_FAILOVER_RECOVERY_FLAG",
        ),
    ),
)
SCORING_MODEL_SEED_FILES = (
    PROJECT_ROOT / "dbschema" / "ddlv2_final.sql",
    PROJECT_ROOT / "dbschema" / "ddlv3-1_topology_platform.sql",
)
SCORING_MODEL_PATTERN = re.compile(
    r"INSERT INTO AWR_SCORING_MODEL\s*\([\s\S]*?\)\s*VALUES\s*\(\s*"
    r"'(?P<model_code>[^']+)'\s*,\s*"
    r"'(?P<model_name>[^']+)'\s*,\s*"
    r"'(?P<model_version>[^']+)'\s*,\s*"
    r"'(?P<model_type>[^']+)'\s*,\s*"
    r"'(?P<target_decision_domain>[^']+)'\s*,\s*"
    r"'(?P<status>[^']+)'\s*,\s*"
    r"JSON\('(?P<threshold_json>[^']+)'\)\s*,\s*"
    r"JSON\('(?P<model_config_json>[^']+)'\)\s*"
    r"\)",
    re.IGNORECASE | re.DOTALL,
)
SCORING_WEIGHT_PATTERN = re.compile(
    r"INSERT INTO AWR_SCORING_WEIGHT\s*\([\s\S]*?\)\s*SELECT\s*"
    r"m\.SCORING_MODEL_ID,\s*"
    r"'(?P<feature_code>[^']+)'\s*,\s*"
    r"'(?P<feature_name>[^']+)'\s*,\s*"
    r"'(?P<feature_domain>[^']+)'\s*,\s*"
    r"'(?P<feature_path>[^']+)'\s*,\s*"
    r"(?P<weight_value>[-0-9.]+)\s*,\s*"
    r"'(?P<normalization_method>[^']+)'\s*,\s*"
    r"'(?P<transform_method>[^']+)'\s*,\s*"
    r"'(?P<polarity>[^']+)'\s*"
    r"(?:,\s*'(?P<notes>[^']*)'\s*)?"
    r"FROM",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(slots=True)
class ValidationManifestEntry:
    begin_time: datetime | None
    db_name: str
    dbid: int | None
    expected_primary_issue: str
    expected_secondary_issues: list[str]
    expected_evidence_layers: list[str]
    expected_topology_context: list[str]
    expected_pressure_context: list[str]
    expected_status: str
    expected_status_source: str
    file: str
    notes: str
    scenario_name: str
    manifest_order: int = 0


@dataclass(slots=True)
class ValidationCaseResult:
    scenario_name: str
    file: str
    expected_primary_issue: str
    actual_primary_issue: str
    expected_secondary_issues: list[str]
    actual_secondary_issues: list[str]
    expected_evidence_layers: list[str]
    actual_evidence_layers: list[str]
    expected_topology_context: list[str]
    actual_topology_context: list[str]
    expected_pressure_context: list[str]
    actual_pressure_context: list[str]
    expected_status: str
    actual_status: str
    passed: bool
    validation_diagnostics: dict[str, Any] | None
    output: dict[str, Any]


@dataclass(slots=True)
class ValidationHarnessResult:
    manifest_source: str
    case_count: int
    passed_count: int
    failed_count: int
    cases: list[ValidationCaseResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_source": self.manifest_source,
            "case_count": self.case_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "cases": [asdict(case) for case in self.cases],
        }


@dataclass(slots=True)
class _ScenarioArtifact:
    awr_id: int
    entry: ValidationManifestEntry
    parse_result: Any
    feature_json: dict[str, Any]
    score_result: dict[str, Any] | None
    trend_rows: list[dict[str, Any]]


def load_manifest_entries(
    input_dir: str | Path,
    manifest_path: str | Path | None = None,
) -> tuple[list[ValidationManifestEntry], str]:
    base_dir = Path(input_dir)
    if manifest_path is not None:
        resolved_manifest = Path(manifest_path)
        suffix = resolved_manifest.suffix.lower()
        if suffix == ".csv":
            return _load_manifest_csv(resolved_manifest), str(resolved_manifest)
        if suffix == ".json":
            return _load_manifest_json(resolved_manifest), str(resolved_manifest)
        raise ValueError("Manifest path must point to a .csv or .json file.")

    csv_path = base_dir / MANIFEST_CSV_NAME
    json_path = base_dir / MANIFEST_JSON_NAME
    if csv_path.exists():
        return _load_manifest_csv(csv_path), str(csv_path)
    if json_path.exists():
        return _load_manifest_json(json_path), str(json_path)
    raise FileNotFoundError(
        f"No manifest found in {base_dir}; expected {MANIFEST_CSV_NAME} or {MANIFEST_JSON_NAME}."
    )


def run_validation_harness(
    input_dir: str | Path,
    manifest_path: str | Path | None = None,
    parser: Callable[[str | Path], Any] = parse_awr_file,
    feature_vector_builder: Callable[[Any, int, int], dict[str, Any]] | None = None,
    decision_builder: Callable[..., Any] = build_decision,
    include_decision_diagnostics: bool = True,
) -> ValidationHarnessResult:
    entries, manifest_source = load_manifest_entries(
        input_dir,
        manifest_path=manifest_path,
    )
    builder = feature_vector_builder or _load_feature_vector_builder()
    artifacts = _build_scenario_artifacts(entries, Path(input_dir), parser, builder)
    _populate_local_trend_rows(artifacts)

    case_results: list[ValidationCaseResult] = []
    for artifact in artifacts:
        decision = _invoke_decision_builder(
            decision_builder=decision_builder,
            awr_id=artifact.awr_id,
            feature_json=artifact.feature_json,
            score_result=artifact.score_result,
            trend_rows=artifact.trend_rows,
            include_decision_diagnostics=include_decision_diagnostics,
        )
        actual_primary_issue, actual_secondary_issues = normalize_decision_for_validation(
            decision
        )
        actual_evidence_layers = _derive_evidence_layers(
            artifact.parse_result,
            artifact.feature_json,
        )
        actual_topology_context = _derive_topology_context(artifact.feature_json)
        actual_pressure_context = _derive_pressure_context(artifact.feature_json)
        status_compared = artifact.entry.expected_status != "UNSPECIFIED"
        passed = (
            actual_primary_issue == artifact.entry.expected_primary_issue
            and actual_secondary_issues == artifact.entry.expected_secondary_issues
            and (
                not artifact.entry.expected_evidence_layers
                or actual_evidence_layers == artifact.entry.expected_evidence_layers
            )
            and (
                not artifact.entry.expected_topology_context
                or actual_topology_context == artifact.entry.expected_topology_context
            )
            and (
                not artifact.entry.expected_pressure_context
                or actual_pressure_context == artifact.entry.expected_pressure_context
            )
            and (
                not status_compared
                or decision.overall_status == artifact.entry.expected_status
            )
        )
        validation_diagnostics = _build_validation_diagnostics(
            decision=decision,
            actual_primary_issue=actual_primary_issue,
            actual_secondary_issues=actual_secondary_issues,
            actual_evidence_layers=actual_evidence_layers,
            actual_topology_context=actual_topology_context,
            actual_pressure_context=actual_pressure_context,
            expected_evidence_layers=artifact.entry.expected_evidence_layers,
            expected_topology_context=artifact.entry.expected_topology_context,
            expected_pressure_context=artifact.entry.expected_pressure_context,
            expected_status=artifact.entry.expected_status,
            status_compared=status_compared,
            passed=passed,
        )
        output = {
            "awr_id": getattr(decision, "awr_id", artifact.awr_id),
            "decision": decision.to_dict(),
            "output_version": OUTPUT_VERSION,
            "source": OUTPUT_SOURCE,
            "validation_diagnostics": validation_diagnostics,
        }
        case_results.append(
            ValidationCaseResult(
                scenario_name=artifact.entry.scenario_name,
                file=artifact.entry.file,
                expected_primary_issue=artifact.entry.expected_primary_issue,
                actual_primary_issue=actual_primary_issue,
                expected_secondary_issues=artifact.entry.expected_secondary_issues,
                actual_secondary_issues=actual_secondary_issues,
                expected_evidence_layers=artifact.entry.expected_evidence_layers,
                actual_evidence_layers=actual_evidence_layers,
                expected_topology_context=artifact.entry.expected_topology_context,
                actual_topology_context=actual_topology_context,
                expected_pressure_context=artifact.entry.expected_pressure_context,
                actual_pressure_context=actual_pressure_context,
                expected_status=artifact.entry.expected_status,
                actual_status=decision.overall_status,
                passed=passed,
                validation_diagnostics=validation_diagnostics,
                output=output,
            )
        )

    passed_count = sum(1 for case in case_results if case.passed)
    failed_count = len(case_results) - passed_count
    return ValidationHarnessResult(
        manifest_source=manifest_source,
        case_count=len(case_results),
        passed_count=passed_count,
        failed_count=failed_count,
        cases=case_results,
    )


def normalize_decision_for_validation(decision: Any) -> tuple[str, list[str]]:
    evidence = getattr(decision, "evidence", {}) or {}
    domain_scores = evidence.get("domain_scores") or {}
    qualifying_domains = [
        domain
        for domain in DOMAIN_ORDER
        if _safe_float(domain_scores.get(domain)) is not None
        and float(domain_scores[domain]) >= PRIMARY_QUALIFICATION_THRESHOLD
    ]
    primary_issue = getattr(decision, "primary_issue", None)
    if primary_issue in (None, "", "NONE"):
        return "NONE", [
            domain for domain in list(getattr(decision, "secondary_issues", [])) if domain
        ]
    if getattr(decision, "overall_status", "") == "OK" and not qualifying_domains:
        return "NONE", []
    return str(primary_issue), list(getattr(decision, "secondary_issues", []))


def _invoke_decision_builder(
    decision_builder: Callable[..., Any],
    awr_id: int,
    feature_json: dict[str, Any],
    score_result: dict[str, Any] | None,
    trend_rows: list[dict[str, Any]],
    include_decision_diagnostics: bool,
) -> Any:
    decision_input = build_decision_input_from_score_result(
        awr_id=awr_id,
        score_result=score_result,
        trend_rows=trend_rows,
        feature_evidence=feature_json,
    )
    kwargs = {
        "decision_input": decision_input,
    }
    parameters = signature(decision_builder).parameters
    accepts_var_kwargs = any(
        parameter.kind == parameter.VAR_KEYWORD for parameter in parameters.values()
    )
    if include_decision_diagnostics and (
        "include_diagnostics" in parameters or accepts_var_kwargs
    ):
        kwargs["include_diagnostics"] = True
    return decision_builder(**kwargs)


def _build_validation_diagnostics(
    decision: Any,
    actual_primary_issue: str,
    actual_secondary_issues: list[str],
    actual_evidence_layers: list[str],
    actual_topology_context: list[str],
    actual_pressure_context: list[str],
    expected_evidence_layers: list[str],
    expected_topology_context: list[str],
    expected_pressure_context: list[str],
    expected_status: str,
    status_compared: bool,
    passed: bool,
) -> dict[str, Any]:
    evidence = getattr(decision, "evidence", {}) or {}
    decision_diagnostics = evidence.get("decision_diagnostics")
    normalized_to_none = actual_primary_issue == "NONE"
    domain_scores = (evidence.get("domain_scores") or {}).copy()
    mismatch_reason = None
    if not passed:
        mismatch_reason = _build_mismatch_reason(
            actual_primary_issue=actual_primary_issue,
            actual_secondary_issues=actual_secondary_issues,
            actual_evidence_layers=actual_evidence_layers,
            actual_topology_context=actual_topology_context,
            actual_pressure_context=actual_pressure_context,
            expected_evidence_layers=expected_evidence_layers,
            expected_topology_context=expected_topology_context,
            expected_pressure_context=expected_pressure_context,
            actual_status=getattr(decision, "overall_status", ""),
            expected_status=expected_status,
            status_compared=status_compared,
        )
    return {
        "decision_diagnostics": decision_diagnostics,
        "domain_scores": domain_scores,
        "normalized_to_none": normalized_to_none,
        "normalized_primary_issue": actual_primary_issue,
        "normalized_secondary_issues": list(actual_secondary_issues),
        "actual_evidence_layers": list(actual_evidence_layers),
        "actual_topology_context": list(actual_topology_context),
        "actual_pressure_context": list(actual_pressure_context),
        "status_compared": status_compared,
        "mismatch_reason": mismatch_reason,
    }


def _build_mismatch_reason(
    actual_primary_issue: str,
    actual_secondary_issues: list[str],
    actual_evidence_layers: list[str],
    actual_topology_context: list[str],
    actual_pressure_context: list[str],
    expected_evidence_layers: list[str],
    expected_topology_context: list[str],
    expected_pressure_context: list[str],
    actual_status: str,
    expected_status: str,
    status_compared: bool,
) -> str:
    fragments = [
        f"primary={actual_primary_issue}",
        f"secondary={','.join(actual_secondary_issues) or 'NONE'}",
    ]
    if expected_evidence_layers:
        fragments.append(
            "evidence_layers="
            + (",".join(actual_evidence_layers) or "NONE")
            + " expected="
            + ",".join(expected_evidence_layers)
        )
    if expected_topology_context:
        fragments.append(
            "topology_context="
            + (",".join(actual_topology_context) or "NONE")
            + " expected="
            + ",".join(expected_topology_context)
        )
    if expected_pressure_context:
        fragments.append(
            "pressure_context="
            + (",".join(actual_pressure_context) or "NONE")
            + " expected="
            + ",".join(expected_pressure_context)
        )
    if status_compared:
        fragments.append(f"status={actual_status} expected={expected_status}")
    else:
        fragments.append(f"status={actual_status} expected=UNSPECIFIED")
    return "; ".join(fragments)


def render_validation_cli_summary(result: ValidationHarnessResult) -> str:
    lines = [
        "=" * 56,
        "PHASE 4G VALIDATION SUMMARY",
        "=" * 56,
        f"Manifest Source: {result.manifest_source}",
        f"Cases: {result.case_count}",
        f"Passed: {result.passed_count}",
        f"Failed: {result.failed_count}",
    ]
    if result.failed_count:
        lines.append("")
        lines.append("MISMATCHED CASES:")
        for case in result.cases:
            if case.passed:
                continue
            lines.append(
                f"- {case.scenario_name}: expected "
                f"{case.expected_primary_issue}/{case.expected_status}, got "
                f"{case.actual_primary_issue}/{case.actual_status}"
            )
    lines.append("=" * 56)
    return "\n".join(lines)


def write_validation_json_summary(
    result: ValidationHarnessResult,
    output_path: str | Path,
) -> None:
    path = Path(output_path)
    path.write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=False, default=str) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the Phase 4G validation harness against a local dataset."
    )
    parser.add_argument(
        "dataset_dir",
        nargs="?",
        default="data/input",
        help="Dataset directory containing AWR files and manifest files.",
    )
    parser.add_argument(
        "--manifest",
        dest="manifest_path",
        help="Optional explicit manifest path (.csv or .json).",
    )
    parser.add_argument(
        "--json-output",
        dest="json_output",
        default="validation_summary_24.json",
        help="Optional path to write the machine-readable validation summary.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_validation_harness(
            input_dir=args.dataset_dir,
            manifest_path=args.manifest_path,
        )
    except Exception as exc:
        print(f"Validation harness failed: {exc}", file=sys.stderr)
        return 1

    print(render_validation_cli_summary(result))
    if args.json_output:
        write_validation_json_summary(result, args.json_output)
        print(f"JSON summary written to: {args.json_output}")
    return 0


def _build_scenario_artifacts(
    entries: list[ValidationManifestEntry],
    input_dir: Path,
    parser: Callable[[str | Path], Any],
    feature_vector_builder: Callable[[Any, int, int], dict[str, Any]],
) -> list[_ScenarioArtifact]:
    artifacts: list[_ScenarioArtifact] = []
    for awr_id, entry in enumerate(entries, start=1):
        file_path = input_dir / entry.file
        if not file_path.exists():
            raise FileNotFoundError(f"Manifest file does not exist: {file_path}")
        parse_result = parser(file_path)
        feature_vector = feature_vector_builder(parse_result, awr_id, awr_id)
        feature_json = _coerce_feature_json(feature_vector)
        score_result = _build_seeded_score_result(
            parse_result=parse_result,
            awr_id=awr_id,
            feature_json=feature_json,
        )
        artifacts.append(
            _ScenarioArtifact(
                awr_id=awr_id,
                entry=entry,
                parse_result=parse_result,
                feature_json=feature_json,
                score_result=score_result,
                trend_rows=[],
            )
        )
    return artifacts


def _populate_local_trend_rows(artifacts: list[_ScenarioArtifact]) -> None:
    history: dict[tuple[str, int | None, str], list[tuple[datetime | None, float]]] = {}
    for artifact in artifacts:
        current_trend_rows: list[dict[str, Any]] = []
        numeric_metrics = _numeric_feature_metrics(artifact.feature_json)
        for metric_name, metric_value in numeric_metrics.items():
            history_key = (artifact.entry.db_name, artifact.entry.dbid, metric_name)
            metric_history = list(history.get(history_key, []))
            metric_history.append((artifact.entry.begin_time, metric_value))
            trend_features = compute_trend_features(metric_history)
            anomaly_rows = detect_anomalies(metric_history, trend_features, metric_name)
            current_anomaly = anomaly_rows[-1]
            if current_anomaly.get("anomaly_flag") != "Y":
                history[history_key] = metric_history
                continue
            current_trend_rows.append(
                {
                    "metric_name": metric_name,
                    "metric_value_num": metric_value,
                    "anomaly_flag": current_anomaly.get("anomaly_flag"),
                    "anomaly_type": current_anomaly.get("anomaly_type"),
                    "anomaly_score": current_anomaly.get("anomaly_score"),
                }
            )
            history[history_key] = metric_history
        artifact.trend_rows = current_trend_rows


def _numeric_feature_metrics(feature_json: dict[str, Any]) -> dict[str, float]:
    numeric_metrics: dict[str, float] = {}
    for key, value in feature_json.items():
        numeric_value = _safe_float(value)
        if numeric_value is None:
            continue
        numeric_metrics[str(key)] = numeric_value
    return numeric_metrics


def _coerce_feature_json(feature_vector: dict[str, Any]) -> dict[str, Any]:
    feature_json = feature_vector.get("feature_json")
    if isinstance(feature_json, dict):
        return feature_json
    if isinstance(feature_json, str) and feature_json.strip():
        return json.loads(feature_json)
    raise ValueError("Feature vector builder did not return a usable feature_json payload.")


def _load_manifest_csv(path: Path) -> list[ValidationManifestEntry]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return _build_manifest_entries(rows)


def _load_manifest_json(path: Path) -> list[ValidationManifestEntry]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("reports")
    if not isinstance(payload, list):
        raise ValueError("Manifest JSON must contain a list of scenario objects.")
    return _build_manifest_entries(payload)


def _build_manifest_entries(rows: list[dict[str, Any]]) -> list[ValidationManifestEntry]:
    entries = []
    for index, row in enumerate(rows):
        expected_status, expected_status_source = _resolve_expected_status(row)
        file_name = str(
            row.get("file")
            or row.get("filename")
            or row.get("file_name")
            or ""
        ).strip()
        scenario_name = str(row.get("scenario_name") or "").strip()
        if not scenario_name:
            scenario_name = Path(file_name).stem or f"case_{index + 1}"
        entries.append(
            ValidationManifestEntry(
                begin_time=_parse_manifest_begin_time(
                    row.get("begin_time") or row.get("snapshot_start")
                ),
                db_name=str(row.get("db_name") or "").strip(),
                dbid=_safe_int(row.get("dbid")),
                expected_primary_issue=_normalize_manifest_issue(
                    row.get("expected_primary_issue") or row.get("dominant_domain")
                ),
                expected_secondary_issues=_split_expected_secondary_issues(
                    row.get("expected_secondary_issues") or row.get("secondary_domains")
                ),
                expected_evidence_layers=_split_expected_secondary_issues(
                    row.get("expected_evidence_layers")
                ),
                expected_topology_context=_split_expected_secondary_issues(
                    row.get("expected_topology_context")
                ),
                expected_pressure_context=_split_expected_secondary_issues(
                    row.get("expected_pressure_context")
                ),
                expected_status=expected_status,
                expected_status_source=expected_status_source,
                file=file_name,
                notes=str(
                    row.get("notes") or row.get("description") or row.get("expected_behavior") or ""
                ).strip(),
                scenario_name=scenario_name,
                manifest_order=index,
            )
        )
    return sorted(
        entries,
        key=lambda entry: (
            entry.begin_time is None,
            entry.begin_time or datetime.max,
            entry.manifest_order,
            entry.scenario_name,
        ),
    )


def _resolve_expected_status(row: dict[str, Any]) -> tuple[str, str]:
    explicit_status = str(row.get("expected_status") or "").strip().upper()
    if explicit_status:
        return explicit_status, "manifest"

    expected_behavior = str(row.get("expected_behavior") or "").lower()
    if not expected_behavior:
        return "UNSPECIFIED", "unspecified"

    if any(
        phrase in expected_behavior
        for phrase in (
            "do not classify as severe",
            "low urgency",
            "keep severity low",
        )
    ):
        return "OK", "derived_from_expected_behavior"
    if any(
        phrase in expected_behavior
        for phrase in (
            "moderate-high",
            "moderate at most",
            "moderate confidence",
            "reduced confidence",
            "moderate severity",
        )
    ):
        return "WARNING", "derived_from_expected_behavior"
    if any(
        phrase in expected_behavior
        for phrase in (
            "high severity",
            "critical",
            "severe",
        )
    ):
        return "CRITICAL", "derived_from_expected_behavior"
    if any(
        phrase in expected_behavior
        for phrase in (
            "low severity",
            "keep severity low",
            "do nothing",
            "stable or monitor",
            "observe",
            "low-confidence observe",
            "downgrade posture",
        )
    ):
        return "OK", "derived_from_expected_behavior"
    return "UNSPECIFIED", "unspecified"


def _parse_manifest_begin_time(value: Any) -> datetime | None:
    raw_value = str(value or "").strip()
    if not raw_value:
        return None
    for pattern in ("%Y-%m-%d %H:%M:%S", "%d-%b-%y %H:%M:%S"):
        try:
            return datetime.strptime(raw_value, pattern)
        except ValueError:
            continue
    raise ValueError(f"Unsupported manifest timestamp format: {raw_value}")


def _split_expected_secondary_issues(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip().upper() for item in value if str(item).strip()]
    raw_value = str(value or "").strip()
    if not raw_value:
        return []
    return [item.strip().upper() for item in raw_value.split(",") if item.strip()]


def _derive_evidence_layers(parse_result: Any, feature_json: dict[str, Any]) -> list[str]:
    wait_events = getattr(parse_result, "wait_events", None) or []
    wait_class_names = {
        str(row.get("wait_class") or "").strip().upper()
        for row in wait_events
        if isinstance(row, dict)
    }
    event_names = [
        str(row.get("event_name") or "").strip().lower()
        for row in wait_events
        if isinstance(row, dict)
    ]
    layers: list[str] = []
    concurrency_present = (
        "CONCURRENCY" in wait_class_names
        or any(
            token in event_name
            for event_name in event_names
            for token in (
                "latch",
                "mutex",
                "cursor pin",
                "cache buffers chains",
            )
        )
        or (_safe_float(feature_json.get("CONCURRENCY_PRESSURE")) or 0.0) > 0.0
    )
    if concurrency_present:
        layers.append("CONCURRENCY")
    return layers


def _derive_topology_context(feature_json: dict[str, Any]) -> list[str]:
    context: list[str] = []
    topology_class = str(feature_json.get("topology_class") or "").upper()
    if "RAC" in topology_class or (_safe_float(feature_json.get("is_rac")) or 0.0) >= 0.5:
        context.append("RAC")
    if (
        "ADG" in topology_class
        or (_safe_float(feature_json.get("is_dataguard")) or 0.0) >= 0.5
        or (_safe_float(feature_json.get("is_standby")) or 0.0) >= 0.5
    ):
        context.append("ADG")
    return context


def _derive_pressure_context(feature_json: dict[str, Any]) -> list[str]:
    context: list[str] = []
    seen: set[str] = set()
    for domain, feature_keys, flag_keys in PRESSURE_CONTEXT_RULES:
        has_pressure_evidence = _has_any_feature(feature_json, *feature_keys) or _has_any_flag(
            feature_json,
            *flag_keys,
        )
        if has_pressure_evidence and domain not in seen:
            context.append(domain)
            seen.add(domain)
    return context


def _has_any_feature(feature_json: dict[str, Any], *keys: str) -> bool:
    return any((_safe_float(feature_json.get(key)) or 0.0) > 0.0 for key in keys)


def _has_any_flag(feature_json: dict[str, Any], *keys: str) -> bool:
    return any((_safe_float(feature_json.get(key)) or 0.0) >= 0.5 for key in keys)


def _normalize_manifest_issue(value: Any) -> str:
    normalized = str(value or "").strip().upper()
    return normalized or "NONE"


def _load_feature_vector_builder() -> Callable[[Any, int, int], dict[str, Any]]:
    try:
        from src.ingest.awr_adb_loader import build_feature_vector_record
    except ModuleNotFoundError as exc:
        if exc.name != "dotenv":
            raise
        sys.modules.setdefault(
            "dotenv",
            types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None),
        )
        from src.ingest.awr_adb_loader import build_feature_vector_record
    return build_feature_vector_record


def _build_seeded_score_result(
    parse_result: Any,
    awr_id: int,
    feature_json: dict[str, Any],
) -> dict[str, Any] | None:
    build_score_result_record, scoring_model, scoring_weights = _load_seeded_scoring_components()
    return build_score_result_record(
        parse_result=parse_result,
        awr_id=awr_id,
        source_system_id=awr_id,
        feature_vector_id=awr_id,
        feature_json=feature_json,
        scoring_model=scoring_model,
        scoring_weights=scoring_weights,
    )


def _load_seeded_scoring_components(
) -> tuple[Callable[..., dict[str, Any] | None], dict[str, Any], list[dict[str, Any]]]:
    try:
        from src.ingest.awr_adb_loader import _build_score_result_record
    except ModuleNotFoundError as exc:
        if exc.name != "dotenv":
            raise
        sys.modules.setdefault(
            "dotenv",
            types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None),
        )
        from src.ingest.awr_adb_loader import _build_score_result_record
    scoring_model = _parse_seeded_scoring_model()
    scoring_weights = _parse_seeded_scoring_weights()
    return _build_score_result_record, scoring_model, scoring_weights


def _parse_seeded_scoring_model() -> dict[str, Any]:
    for seed_file in SCORING_MODEL_SEED_FILES:
        if not seed_file.exists():
            continue
        match = SCORING_MODEL_PATTERN.search(seed_file.read_text(encoding="utf-8"))
        if match is None:
            continue
        return {
            "scoring_model_id": 1,
            "model_code": match.group("model_code"),
            "model_name": match.group("model_name"),
            "model_version": match.group("model_version"),
            "model_type": match.group("model_type"),
            "target_decision_domain": match.group("target_decision_domain"),
            "status": match.group("status"),
            "score_min": 0.0,
            "score_max": 100.0,
            "threshold_json": json.loads(match.group("threshold_json")),
            "model_config_json": json.loads(match.group("model_config_json")),
        }
    raise FileNotFoundError("Unable to locate seeded scoring model definition for Phase 4G validation.")


def _parse_seeded_scoring_weights() -> list[dict[str, Any]]:
    weights: list[dict[str, Any]] = []
    seen_codes: set[str] = set()
    for seed_file in SCORING_MODEL_SEED_FILES:
        if not seed_file.exists():
            continue
        sql_text = seed_file.read_text(encoding="utf-8")
        for match in SCORING_WEIGHT_PATTERN.finditer(sql_text):
            feature_code = match.group("feature_code")
            if feature_code in seen_codes:
                continue
            seen_codes.add(feature_code)
            weights.append(
                {
                    "feature_code": feature_code,
                    "feature_name": match.group("feature_name"),
                    "feature_domain": match.group("feature_domain"),
                    "feature_path": match.group("feature_path"),
                    "weight_value": _safe_float(match.group("weight_value")) or 0.0,
                    "normalization_method": match.group("normalization_method"),
                    "transform_method": match.group("transform_method"),
                    "polarity": match.group("polarity"),
                    "notes": match.group("notes") or None,
                }
            )
    if not weights:
        raise FileNotFoundError("Unable to locate seeded scoring weight definitions for Phase 4G validation.")
    return weights


def _safe_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").strip())
        except ValueError:
            return None
    return None


def _safe_int(value: Any) -> int | None:
    numeric_value = _safe_float(value)
    if numeric_value is None:
        return None
    return int(numeric_value)


if __name__ == "__main__":
    raise SystemExit(main())
