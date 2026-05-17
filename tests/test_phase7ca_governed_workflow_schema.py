"""Phase 7CA schema tests for governed workflow persistence."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "dbschema" / "phase7ca_governed_workflow_persistence.sql"

REQUIRED_TABLES = (
    "AWR_WORKFLOW_TRANSACTION",
    "AWR_WORKFLOW_REQUEST",
    "AWR_WORKFLOW_VALIDATION",
    "AWR_WORKFLOW_AUDIT",
    "AWR_WORKFLOW_OUTPUT_ARTIFACT",
)

REQUIRED_COLUMNS = {
    "AWR_WORKFLOW_TRANSACTION": (
        "TRANSACTION_GROUP_ID",
        "IDEMPOTENCY_KEY",
        "TRANSACTION_SCOPE",
        "STATUS",
        "ROLLBACK_REFERENCE",
        "CREATED_AT",
        "UPDATED_AT",
        "NOTES",
    ),
    "AWR_WORKFLOW_REQUEST": (
        "WORKFLOW_REQUEST_ID",
        "TRANSACTION_GROUP_ID",
        "IDEMPOTENCY_KEY",
        "SOURCE_SCREEN",
        "WORKFLOW_TYPE",
        "REQUESTED_ACTION",
        "TARGET_TYPE",
        "TARGET_ID",
        "ACTOR_ID",
        "PAYLOAD_CLOB",
        "STATUS",
        "CREATED_AT",
        "UPDATED_AT",
        "ERROR_CLOB",
        "WARNING_CLOB",
        "NOTES",
    ),
    "AWR_WORKFLOW_VALIDATION": (
        "WORKFLOW_VALIDATION_ID",
        "WORKFLOW_REQUEST_ID",
        "VALIDATION_STATUS",
        "VALID_FLAG",
        "DENIED_REASONS_CLOB",
        "WARNINGS_CLOB",
        "REQUIRED_NEXT_STEPS_CLOB",
        "CREATED_AT",
        "NOTES",
    ),
    "AWR_WORKFLOW_AUDIT": (
        "WORKFLOW_AUDIT_ID",
        "WORKFLOW_REQUEST_ID",
        "TRANSACTION_GROUP_ID",
        "ACTOR_ID",
        "ACTION",
        "AUDIT_SUMMARY",
        "PAYLOAD_HASH",
        "CREATED_AT",
        "NOTES",
    ),
    "AWR_WORKFLOW_OUTPUT_ARTIFACT": (
        "WORKFLOW_OUTPUT_ID",
        "WORKFLOW_REQUEST_ID",
        "ARTIFACT_TYPE",
        "ARTIFACT_REFERENCE",
        "ARTIFACT_SUMMARY",
        "ARTIFACT_METADATA_CLOB",
        "STATUS",
        "CREATED_AT",
        "NOTES",
    ),
}

OUTPUT_ARTIFACT_TYPES = (
    "validation_response",
    "analysis_run_record",
    "phase4i_payload_reference",
    "dashboard_artifact_reference",
    "comparison_artifact",
    "error_artifact",
    "source_validation_artifact",
    "object_storage_load_artifact",
    "workflow_audit_artifact",
)


def schema_text() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8")


def upper_schema() -> str:
    return schema_text().upper()


class Phase7CAGovernedWorkflowSchemaTests(unittest.TestCase):
    def test_schema_file_exists(self) -> None:
        self.assertTrue(SCHEMA_PATH.is_file(), SCHEMA_PATH)

    def test_required_table_names_present(self) -> None:
        text = upper_schema()
        for table in REQUIRED_TABLES:
            with self.subTest(table=table):
                self.assertIn(f"CREATE TABLE {table}", text)

    def test_required_columns_present(self) -> None:
        text = upper_schema()
        for table, columns in REQUIRED_COLUMNS.items():
            table_block = self._table_block(text, table)
            for column in columns:
                with self.subTest(table=table, column=column):
                    self.assertIn(column, table_block)

    def test_idempotency_key_present_and_constrained(self) -> None:
        text = upper_schema()
        self.assertIn("IDEMPOTENCY_KEY", text)
        self.assertIn("UK_AWR_WF_TX_IDEMP", text)
        self.assertIn("UK_AWR_WF_REQ_IDEMP", text)
        self.assertRegex(text, r"UNIQUE\s*\(\s*IDEMPOTENCY_KEY\s*\)")

    def test_transaction_group_present_and_indexed(self) -> None:
        text = upper_schema()
        self.assertIn("TRANSACTION_GROUP_ID", text)
        self.assertIn("PRIMARY KEY", self._table_block(text, "AWR_WORKFLOW_TRANSACTION"))
        self.assertIn("IX_AWR_WF_REQ_TX", text)
        self.assertIn("IX_AWR_WF_AUD_TX", text)

    def test_audit_table_and_output_artifact_table_present(self) -> None:
        text = upper_schema()
        audit_block = self._table_block(text, "AWR_WORKFLOW_AUDIT")
        output_block = self._table_block(text, "AWR_WORKFLOW_OUTPUT_ARTIFACT")
        self.assertIn("PAYLOAD_HASH", audit_block)
        self.assertIn("AUDIT_SUMMARY", audit_block)
        self.assertIn("ARTIFACT_REFERENCE", output_block)
        self.assertIn("ARTIFACT_METADATA_CLOB", output_block)

    def test_supported_output_artifact_types_present(self) -> None:
        text = schema_text()
        for artifact_type in OUTPUT_ARTIFACT_TYPES:
            with self.subTest(artifact_type=artifact_type):
                self.assertIn(artifact_type, text)

    def test_no_credential_or_secret_columns(self) -> None:
        text = upper_schema()
        forbidden_tokens = (
            "PASSWORD",
            "PASSWD",
            "TOKEN",
            "PRIVATE_KEY",
            "WALLET",
            "ACCESS_KEY",
            "API_KEY",
            "AUTH_KEY",
        )
        for token in forbidden_tokens:
            with self.subTest(token=token):
                self.assertNotRegex(text, rf"\b{re.escape(token)}\b")

    def test_no_destructive_drop_statements(self) -> None:
        text = upper_schema()
        self.assertNotIn("DROP TABLE", text)
        self.assertNotIn("TRUNCATE TABLE", text)
        self.assertNotIn("CASCADE CONSTRAINTS", text)
        self.assertNotIn("PURGE", text)

    def test_indexes_and_constraints_present(self) -> None:
        text = upper_schema()
        self.assertIn("CREATE INDEX", text)
        self.assertIn("FOREIGN KEY", text)
        self.assertIn("CHECK", text)
        self.assertIn("IS JSON", text)
        for index_name in (
            "IX_AWR_WF_REQ_TX",
            "IX_AWR_WF_REQ_STATUS",
            "IX_AWR_WF_VAL_REQ",
            "IX_AWR_WF_AUD_REQ",
            "IX_AWR_WF_AUD_TX",
            "IX_AWR_WF_OUT_REQ",
            "IX_AWR_WF_OUT_TYPE",
        ):
            with self.subTest(index_name=index_name):
                self.assertIn(index_name, text)

    @staticmethod
    def _table_block(text: str, table_name: str) -> str:
        match = re.search(
            rf"CREATE TABLE {re.escape(table_name)}\s*\((.*?)\n\s*\)\s*\]\s*'",
            text,
            flags=re.DOTALL,
        )
        if not match:
            raise AssertionError(f"Could not locate table block for {table_name}")
        return match.group(1)


if __name__ == "__main__":
    unittest.main()
