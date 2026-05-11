"""Isolated Oracle Agent Memory prototype adapter for Phase 6N.1.

Oracle Agent Memory is non-authoritative semantic memory. It must never
influence deterministic runtime diagnosis, scoring, recommendations, or
dashboard truth in Phase 6.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is part of project requirements.
    load_dotenv = None  # type: ignore[assignment]

DISABLED_VALUES = {"0", "false", "no", "off", ""}
ENABLED_VALUES = {"1", "true", "yes", "on"}
DEFAULT_DB_NAME = "SPRTRN"
DEFAULT_AGENT_ID = "awr-advisor-phase6n1-prototype"
DEFAULT_USER_ID = "phase6n1-curated-memory"
DEFAULT_TABLE_PREFIX = "AWR_OAM_"
DEFAULT_THREAD_PREFIX = "awr-advisor"
DEFAULT_PHASE6N2_QUERIES = [
    "SPRTRN",
    "io pressure",
    "TUNE FIRST",
    "commit latency",
    "RAC Data Guard operational context",
]


@dataclass(frozen=True)
class OracleAgentMemoryConfig:
    enabled: bool
    compartment_id: str | None = None
    agent_endpoint: str | None = None
    wallet_dir: str | None = None
    wallet_password: str | None = None
    user: str | None = None
    password: str | None = None
    dsn: str | None = None
    table_prefix: str = DEFAULT_TABLE_PREFIX
    schema_policy: str = "create_if_necessary"
    agent_id: str = DEFAULT_AGENT_ID
    user_id: str = DEFAULT_USER_ID
    thread_prefix: str = DEFAULT_THREAD_PREFIX


def load_config_from_env() -> OracleAgentMemoryConfig:
    """Load Oracle Agent Memory prototype settings from environment only."""

    if load_dotenv is not None:
        load_dotenv()

    enabled_value = str(os.getenv("ORACLE_AGENT_MEMORY_ENABLED", "false")).strip().lower()
    enabled = enabled_value in ENABLED_VALUES and enabled_value not in DISABLED_VALUES
    return OracleAgentMemoryConfig(
        enabled=enabled,
        compartment_id=os.getenv("ORACLE_AGENT_MEMORY_COMPARTMENT_ID"),
        agent_endpoint=os.getenv("ORACLE_AGENT_MEMORY_AGENT_ENDPOINT"),
        wallet_dir=os.getenv("ORACLE_AGENT_MEMORY_WALLET_DIR"),
        wallet_password=os.getenv("ORACLE_AGENT_MEMORY_WALLET_PASSWORD"),
        user=os.getenv("ORACLE_AGENT_MEMORY_USER"),
        password=os.getenv("ORACLE_AGENT_MEMORY_PASSWORD"),
        dsn=os.getenv("ORACLE_AGENT_MEMORY_DSN") or os.getenv("ADB_DSN"),
        table_prefix=os.getenv("ORACLE_AGENT_MEMORY_TABLE_PREFIX", DEFAULT_TABLE_PREFIX),
        schema_policy=os.getenv("ORACLE_AGENT_MEMORY_SCHEMA_POLICY", "create_if_necessary"),
        agent_id=os.getenv("ORACLE_AGENT_MEMORY_AGENT_ID", DEFAULT_AGENT_ID),
        user_id=os.getenv("ORACLE_AGENT_MEMORY_USER_ID", DEFAULT_USER_ID),
        thread_prefix=os.getenv("ORACLE_AGENT_MEMORY_THREAD_PREFIX", DEFAULT_THREAD_PREFIX),
    )


def build_curated_memory_payload(
    db_name: str = DEFAULT_DB_NAME,
    *,
    source: str = "phase6n2_live_validation",
) -> dict[str, Any]:
    """Build the Phase 6N.1 curated semantic memory payload.

    The payload is explicitly non-authoritative and cannot be consumed by
    deterministic parser, scoring, recommendation, or dashboard truth paths.
    """

    return {
        "db_name": db_name,
        "primary_issue": "io_pressure",
        "secondary_issue": "commit_pressure",
        "posture": "TUNE FIRST",
        "summary": (
            "Repeated User I/O spikes with intermittent commit latency and "
            "RAC/Data Guard operational context."
        ),
        "source": source,
        "authoritative": False,
        "runtime_influence": False,
    }


class OracleAgentMemoryPrototypeAdapter:
    """Prototype-only adapter for curated semantic recall experiments.

    Oracle Agent Memory is observational, optional, isolated, curated, and
    non-authoritative. This adapter must not be imported by parser, feature
    model, scoring engine, decision engine, recommendation engine, dashboard
    truth rendering, or governed Phase 6 memory table write paths.
    """

    def __init__(
        self,
        config: OracleAgentMemoryConfig | None = None,
        *,
        client_factory: Callable[[OracleAgentMemoryConfig], Any] | None = None,
        connection_factory: Callable[[OracleAgentMemoryConfig], Any] | None = None,
    ) -> None:
        self.config = config or load_config_from_env()
        self._client_factory = client_factory or self._create_client
        self._connection_factory = connection_factory or self._connect_to_adb
        self._client: Any | None = None
        self._connection: Any | None = None

    def initialize(self) -> dict[str, Any]:
        """Initialize the optional Oracle Agent Memory client."""

        if not self.config.enabled:
            return self._disabled_result()
        started_at = time.perf_counter()
        try:
            config_errors = self.validate_config()
            if config_errors:
                return self._configuration_error_result(config_errors, started_at)
            self._client = self._client_factory(self.config)
            return {
                "enabled": True,
                "success": True,
                "message": "oracle_agent_memory_initialized",
                "duration_ms": _duration_ms(started_at),
                "runtime_influence": False,
                "authoritative": False,
                "errors": [],
            }
        except Exception as exc:  # noqa: BLE001
            return self._error_result(exc, started_at=started_at)

    def get_or_create_thread(self, db_name: str = DEFAULT_DB_NAME) -> dict[str, Any]:
        """Create or retrieve a semantic memory thread for a DB name."""

        if not self.config.enabled:
            return self._disabled_result()
        started_at = time.perf_counter()
        try:
            client = self._require_client()
            thread_id = self.thread_key_for_db(db_name)
            metadata = {
                "db_name": db_name,
                "source": "phase6n2_live_validation",
                "authoritative": False,
                "runtime_influence": False,
            }
            try:
                thread = client.get_thread(thread_id)
                created = False
            except Exception:  # noqa: BLE001 - create if missing.
                thread = client.create_thread(
                    thread_id=thread_id,
                    user_id=self.config.user_id,
                    agent_id=self.config.agent_id,
                    metadata=metadata,
                    extract_memories=False,
                    enable_context_summary=False,
                )
                created = True
            return {
                "enabled": True,
                "success": True,
                "thread_id": thread_id,
                "thread_key": thread_id,
                "db_name": db_name,
                "created": created,
                "thread": thread,
                "duration_ms": _duration_ms(started_at),
                "authoritative": False,
                "runtime_influence": False,
                "errors": [],
            }
        except Exception as exc:  # noqa: BLE001
            return self._error_result(exc, started_at=started_at)

    def write_curated_memory(
        self,
        payload: dict[str, Any],
        *,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Write one curated, non-authoritative semantic memory entry."""

        if not self.config.enabled:
            return self._disabled_result()
        started_at = time.perf_counter()
        if payload.get("authoritative") is not False or payload.get("runtime_influence") is not False:
            return {
                "enabled": True,
                "success": False,
                "duration_ms": _duration_ms(started_at),
                "errors": [
                    "curated memory payload must set authoritative=false and runtime_influence=false"
                ],
            }
        try:
            client = self._require_client()
            db_name = str(payload.get("db_name") or DEFAULT_DB_NAME)
            resolved_thread_id = thread_id or self.thread_key_for_db(db_name)
            content = json.dumps(payload, sort_keys=True)
            metadata = {
                "db_name": db_name,
                "source": payload.get("source", "phase6n1_prototype"),
                "authoritative": False,
                "runtime_influence": False,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
            memory_id = client.add_memory(
                content,
                user_id=self.config.user_id,
                agent_id=self.config.agent_id,
                thread_id=resolved_thread_id,
                metadata=metadata,
            )
            return {
                "enabled": True,
                "success": True,
                "memory_id": memory_id,
                "thread_id": resolved_thread_id,
                "thread_key": resolved_thread_id,
                "payload": payload,
                "duration_ms": _duration_ms(started_at),
                "authoritative": False,
                "runtime_influence": False,
                "errors": [],
            }
        except Exception as exc:  # noqa: BLE001
            return self._error_result(exc, started_at=started_at)

    def search_memory(
        self,
        query: str,
        *,
        db_name: str = DEFAULT_DB_NAME,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Search optional semantic memory without changing runtime truth."""

        if not self.config.enabled:
            return self._disabled_result(records=[])
        started_at = time.perf_counter()
        try:
            client = self._require_client()
            thread_id = self.thread_key_for_db(db_name)
            raw_results = client.search(
                query,
                user_id=self.config.user_id,
                agent_id=self.config.agent_id,
                thread_id=thread_id,
                exact_thread_match=True,
                max_results=max(1, min(int(limit), 25)),
            )
            records = [_serialize_search_result(result) for result in raw_results]
            return {
                "enabled": True,
                "success": True,
                "query": query,
                "db_name": db_name,
                "thread_id": thread_id,
                "thread_key": thread_id,
                "records": records,
                "count": len(records),
                "top_result": records[0] if records else None,
                "duration_ms": _duration_ms(started_at),
                "authoritative": False,
                "runtime_influence": False,
                "errors": [],
            }
        except Exception as exc:  # noqa: BLE001
            return self._error_result(exc, records=[], started_at=started_at)

    def validate_config(self) -> list[str]:
        """Return missing configuration messages without exposing secrets."""

        missing = []
        if not self.config.agent_endpoint:
            missing.append("ORACLE_AGENT_MEMORY_AGENT_ENDPOINT is required when enabled")
        if not self.config.user:
            missing.append("ORACLE_AGENT_MEMORY_USER is required when enabled")
        if not self.config.password:
            missing.append("ORACLE_AGENT_MEMORY_PASSWORD is required when enabled")
        if not self.config.dsn:
            missing.append("ORACLE_AGENT_MEMORY_DSN or ADB_DSN is required when enabled")
        return missing

    def thread_key_for_db(self, db_name: str) -> str:
        return _thread_key_for_db(db_name, self.config.thread_prefix)

    def close(self) -> None:
        if self._connection is not None and hasattr(self._connection, "close"):
            self._connection.close()
            self._connection = None

    def _require_client(self) -> Any:
        if self._client is None:
            initialized = self.initialize()
            if not initialized.get("success"):
                raise RuntimeError(initialized.get("errors", ["client initialization failed"])[0])
        return self._client

    def _create_client(self, config: OracleAgentMemoryConfig) -> Any:
        from oracleagentmemory.core.oracleagentmemory import OracleAgentMemory

        connection = self._connection_factory(config)
        self._connection = connection
        return OracleAgentMemory(
            connection=connection,
            embedder=config.agent_endpoint or None,
            extract_memories=False,
            schema_policy=config.schema_policy,
            table_name_prefix=config.table_prefix,
        )

    def _connect_to_adb(self, config: OracleAgentMemoryConfig) -> Any:
        import oracledb

        if not config.user or not config.password or not config.dsn:
            raise ValueError(
                "ORACLE_AGENT_MEMORY_USER, ORACLE_AGENT_MEMORY_PASSWORD, and "
                "ORACLE_AGENT_MEMORY_DSN or ADB_DSN are required when Oracle Agent Memory is enabled"
            )
        wallet_dir = config.wallet_dir or None
        return oracledb.connect(
            user=config.user,
            password=config.password,
            dsn=config.dsn,
            config_dir=wallet_dir,
            wallet_location=wallet_dir,
            wallet_password=config.wallet_password if wallet_dir else None,
        )

    def _disabled_result(self, records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        result = {
            "enabled": False,
            "success": True,
            "skipped": ["oracle_agent_memory_disabled"],
            "authoritative": False,
            "runtime_influence": False,
            "errors": [],
        }
        if records is not None:
            result["records"] = records
            result["count"] = len(records)
        return result

    def _error_result(
        self,
        exc: Exception,
        *,
        records: list[dict[str, Any]] | None = None,
        started_at: float | None = None,
    ) -> dict[str, Any]:
        result = {
            "enabled": True,
            "success": False,
            "error": f"{type(exc).__name__}: {exc}",
            "duration_ms": _duration_ms(started_at) if started_at is not None else None,
            "authoritative": False,
            "runtime_influence": False,
            "errors": [f"{type(exc).__name__}: {exc}"],
        }
        if records is not None:
            result["records"] = records
            result["count"] = len(records)
        return result

    def _configuration_error_result(
        self,
        errors: list[str],
        started_at: float,
    ) -> dict[str, Any]:
        return {
            "enabled": True,
            "success": False,
            "error": "missing Oracle Agent Memory configuration",
            "duration_ms": _duration_ms(started_at),
            "authoritative": False,
            "runtime_influence": False,
            "errors": errors,
        }


def run_phase6n2_live_validation(
    *,
    db_name: str = DEFAULT_DB_NAME,
    queries: list[str] | None = None,
    adapter: OracleAgentMemoryPrototypeAdapter | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Run isolated Phase 6N.2 live semantic validation."""

    prototype_adapter = adapter or OracleAgentMemoryPrototypeAdapter()
    payload = build_curated_memory_payload(db_name, source="phase6n2_live_validation")
    query_values = queries or DEFAULT_PHASE6N2_QUERIES
    isolation = verify_runtime_isolation(repo_root=repo_root)
    try:
        init_result = prototype_adapter.initialize()
        if not init_result.get("enabled", True):
            return {
                "enabled": False,
                "success": True,
                "skipped": init_result.get("skipped", ["oracle_agent_memory_disabled"]),
                "payload": payload,
                "authoritative": False,
                "runtime_influence": False,
                "searches": [],
                "search_results": {},
                "isolation": isolation,
                "isolation_verified": isolation.get("isolation_verified", False),
                "errors": [],
            }
        if not init_result.get("success"):
            return {**init_result, "isolation": isolation, "isolation_verified": False}

        thread_result = prototype_adapter.get_or_create_thread(db_name)
        if not thread_result.get("success"):
            return {**thread_result, "isolation": isolation, "isolation_verified": False}

        write_result = prototype_adapter.write_curated_memory(
            payload,
            thread_id=thread_result.get("thread_id"),
        )
        if not write_result.get("success"):
            return {**write_result, "isolation": isolation, "isolation_verified": False}

        search_results = []
        legacy_search_results = {}
        for query in query_values:
            search_result = prototype_adapter.search_memory(query, db_name=db_name)
            legacy_search_results[query] = search_result
            search_results.append(
                {
                    "query": query,
                    "success": bool(search_result.get("success")),
                    "count": search_result.get("count", 0),
                    "top_result": search_result.get("top_result"),
                    "duration_ms": search_result.get("duration_ms"),
                    "errors": search_result.get("errors", []),
                }
            )
        return {
            "enabled": True,
            "success": all(result.get("success") for result in legacy_search_results.values()),
            "thread_id": thread_result.get("thread_id"),
            "thread_key": thread_result.get("thread_key"),
            "write": {
                "success": bool(write_result.get("success")),
                "memory_id": write_result.get("memory_id"),
                "duration_ms": write_result.get("duration_ms"),
                "errors": write_result.get("errors", []),
            },
            "memory_id": write_result.get("memory_id"),
            "payload": payload,
            "searches": search_results,
            "search_results": legacy_search_results,
            "diagnostics": {
                "init_duration_ms": init_result.get("duration_ms"),
                "thread_duration_ms": thread_result.get("duration_ms"),
            },
            "isolation": isolation,
            "isolation_verified": bool(isolation.get("isolation_verified")),
            "authoritative": False,
            "runtime_influence": False,
            "errors": [],
        }
    finally:
        prototype_adapter.close()


def run_phase6n1_prototype(
    *,
    db_name: str = DEFAULT_DB_NAME,
    queries: list[str] | None = None,
    adapter: OracleAgentMemoryPrototypeAdapter | None = None,
) -> dict[str, Any]:
    """Backward-compatible wrapper for the Phase 6N.2 live validation flow."""

    return run_phase6n2_live_validation(db_name=db_name, queries=queries, adapter=adapter)


def verify_runtime_isolation(repo_root: Path | None = None) -> dict[str, Any]:
    """Statically verify Oracle Agent Memory is not imported by runtime truth paths."""

    root = repo_root or Path(__file__).resolve().parents[2]
    checked_paths = [
        root / "src" / "parser",
        root / "src" / "analysis" / "decision_engine.py",
        root / "src" / "analysis" / "recommendation_engine.py",
        root / "src" / "recommendation",
        root / "scripts" / "run_analysis.py",
        root / "src" / "reporting" / "html_dashboard.py",
    ]
    forbidden_tokens = ("oracle_agent_memory_adapter", "oracleagentmemory")
    violations = []
    for path in checked_paths:
        candidate_files = [path] if path.is_file() else sorted(path.rglob("*.py")) if path.exists() else []
        for candidate in candidate_files:
            text = candidate.read_text(encoding="utf-8", errors="ignore")
            if any(token in text for token in forbidden_tokens):
                violations.append(str(candidate.relative_to(root)))
    return {
        "authoritative": False,
        "runtime_influence": False,
        "deterministic_tables_modified": False,
        "parser_called": False,
        "scoring_called": False,
        "decision_engine_called": False,
        "recommendation_engine_called": False,
        "run_analysis_imports_adapter": False,
        "checked_paths": [str(path.relative_to(root)) for path in checked_paths],
        "violations": violations,
        "isolation_verified": not violations,
    }


def _thread_key_for_db(db_name: str, prefix: str = DEFAULT_THREAD_PREFIX) -> str:
    normalized_prefix = str(prefix or DEFAULT_THREAD_PREFIX).strip() or DEFAULT_THREAD_PREFIX
    normalized_db_name = str(db_name or "UNKNOWN").strip().upper() or "UNKNOWN"
    return f"{normalized_prefix}:db:{normalized_db_name}"


def _serialize_search_result(result: Any) -> dict[str, Any]:
    record = getattr(result, "record", None)
    content = getattr(result, "content", None)
    if content is None and record is not None:
        content = getattr(record, "content", None)
    result_id = getattr(result, "id", None)
    if result_id is None and record is not None:
        result_id = getattr(record, "id", None)
    score = getattr(result, "score", None)
    metadata = getattr(result, "metadata", None)
    if metadata is None and record is not None:
        metadata = getattr(record, "metadata", None)
    return {
        "id": result_id,
        "content": content,
        "score": score,
        "metadata": metadata,
        "authoritative": False,
        "runtime_influence": False,
    }


def _duration_ms(started_at: float) -> float:
    return round((time.perf_counter() - started_at) * 1000.0, 3)
