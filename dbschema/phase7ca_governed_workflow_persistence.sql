--------------------------------------------------------------------------------
-- Phase 7CA Governed Workflow Persistence
-- Target: Oracle Autonomous Database / Oracle AI Database
--
-- Safe to run more than once. This schema records governed workflow metadata,
-- validation, audit, transaction, and output artifact references only. It does
-- not execute analysis, activate runtime behavior, regenerate dashboards, or
-- mutate Phase 4I deterministic output.
--------------------------------------------------------------------------------

SET SQLBLANKLINES ON
SET DEFINE OFF

DECLARE
    v_exists NUMBER := 0;
BEGIN
    SELECT COUNT(*) INTO v_exists FROM USER_TABLES WHERE TABLE_NAME = 'AWR_WORKFLOW_TRANSACTION';
    IF v_exists = 0 THEN
        EXECUTE IMMEDIATE q'[
            CREATE TABLE AWR_WORKFLOW_TRANSACTION (
                TRANSACTION_GROUP_ID VARCHAR2(160) PRIMARY KEY,
                IDEMPOTENCY_KEY      VARCHAR2(256) NOT NULL,
                TRANSACTION_SCOPE    VARCHAR2(128) NOT NULL,
                STATUS               VARCHAR2(64) DEFAULT 'PENDING' NOT NULL,
                ROLLBACK_REFERENCE   VARCHAR2(512),
                CREATED_AT           TIMESTAMP(6) DEFAULT SYSTIMESTAMP NOT NULL,
                UPDATED_AT           TIMESTAMP(6) DEFAULT SYSTIMESTAMP NOT NULL,
                NOTES                CLOB,
                CONSTRAINT UK_AWR_WF_TX_IDEMP
                    UNIQUE (IDEMPOTENCY_KEY),
                CONSTRAINT CK_AWR_WF_TX_STATUS
                    CHECK (STATUS IN (
                        'PENDING',
                        'IN_PROGRESS',
                        'COMMITTED',
                        'FAILED',
                        'DUPLICATE_REPLAY',
                        'ROLLED_BACK'
                    ))
            )
        ]';
    END IF;
END;
/

DECLARE
    v_exists NUMBER := 0;
BEGIN
    SELECT COUNT(*) INTO v_exists FROM USER_TABLES WHERE TABLE_NAME = 'AWR_WORKFLOW_REQUEST';
    IF v_exists = 0 THEN
        EXECUTE IMMEDIATE q'[
            CREATE TABLE AWR_WORKFLOW_REQUEST (
                WORKFLOW_REQUEST_ID VARCHAR2(160) PRIMARY KEY,
                TRANSACTION_GROUP_ID VARCHAR2(160) NOT NULL,
                IDEMPOTENCY_KEY      VARCHAR2(256) NOT NULL,
                SOURCE_SCREEN        VARCHAR2(64) NOT NULL,
                WORKFLOW_TYPE        VARCHAR2(128) NOT NULL,
                REQUESTED_ACTION     VARCHAR2(128) NOT NULL,
                TARGET_TYPE          VARCHAR2(128),
                TARGET_ID            VARCHAR2(256),
                ACTOR_ID             VARCHAR2(256) NOT NULL,
                PAYLOAD_CLOB         CLOB NOT NULL,
                STATUS               VARCHAR2(64) DEFAULT 'PENDING' NOT NULL,
                CREATED_AT           TIMESTAMP(6) DEFAULT SYSTIMESTAMP NOT NULL,
                UPDATED_AT           TIMESTAMP(6) DEFAULT SYSTIMESTAMP NOT NULL,
                ERROR_CLOB           CLOB,
                WARNING_CLOB         CLOB,
                NOTES                CLOB,
                CONSTRAINT UK_AWR_WF_REQ_IDEMP
                    UNIQUE (IDEMPOTENCY_KEY),
                CONSTRAINT FK_AWR_WF_REQ_TX
                    FOREIGN KEY (TRANSACTION_GROUP_ID)
                    REFERENCES AWR_WORKFLOW_TRANSACTION (TRANSACTION_GROUP_ID),
                CONSTRAINT CK_AWR_WF_REQ_PAYLOAD_JSON
                    CHECK (PAYLOAD_CLOB IS JSON),
                CONSTRAINT CK_AWR_WF_REQ_STATUS
                    CHECK (STATUS IN (
                        'PENDING',
                        'VALIDATED',
                        'FAILED',
                        'COMPLETED',
                        'DUPLICATE_REPLAY',
                        'CANCELLED'
                    ))
            )
        ]';
    END IF;
END;
/

DECLARE
    v_exists NUMBER := 0;
BEGIN
    SELECT COUNT(*) INTO v_exists FROM USER_TABLES WHERE TABLE_NAME = 'AWR_WORKFLOW_VALIDATION';
    IF v_exists = 0 THEN
        EXECUTE IMMEDIATE q'[
            CREATE TABLE AWR_WORKFLOW_VALIDATION (
                WORKFLOW_VALIDATION_ID  VARCHAR2(160) PRIMARY KEY,
                WORKFLOW_REQUEST_ID     VARCHAR2(160) NOT NULL,
                VALIDATION_STATUS       VARCHAR2(128) NOT NULL,
                VALID_FLAG              CHAR(1) DEFAULT 'N' NOT NULL,
                DENIED_REASONS_CLOB     CLOB,
                WARNINGS_CLOB           CLOB,
                REQUIRED_NEXT_STEPS_CLOB CLOB,
                CREATED_AT              TIMESTAMP(6) DEFAULT SYSTIMESTAMP NOT NULL,
                NOTES                   CLOB,
                CONSTRAINT FK_AWR_WF_VAL_REQ
                    FOREIGN KEY (WORKFLOW_REQUEST_ID)
                    REFERENCES AWR_WORKFLOW_REQUEST (WORKFLOW_REQUEST_ID),
                CONSTRAINT CK_AWR_WF_VAL_FLAG
                    CHECK (VALID_FLAG IN ('Y','N')),
                CONSTRAINT CK_AWR_WF_VAL_DENIED_JSON
                    CHECK (DENIED_REASONS_CLOB IS JSON),
                CONSTRAINT CK_AWR_WF_VAL_WARN_JSON
                    CHECK (WARNINGS_CLOB IS JSON),
                CONSTRAINT CK_AWR_WF_VAL_STEPS_JSON
                    CHECK (REQUIRED_NEXT_STEPS_CLOB IS JSON)
            )
        ]';
    END IF;
END;
/

DECLARE
    v_exists NUMBER := 0;
BEGIN
    SELECT COUNT(*) INTO v_exists FROM USER_TABLES WHERE TABLE_NAME = 'AWR_WORKFLOW_AUDIT';
    IF v_exists = 0 THEN
        EXECUTE IMMEDIATE q'[
            CREATE TABLE AWR_WORKFLOW_AUDIT (
                WORKFLOW_AUDIT_ID    VARCHAR2(160) PRIMARY KEY,
                WORKFLOW_REQUEST_ID  VARCHAR2(160) NOT NULL,
                TRANSACTION_GROUP_ID VARCHAR2(160) NOT NULL,
                ACTOR_ID             VARCHAR2(256) NOT NULL,
                ACTION               VARCHAR2(128) NOT NULL,
                AUDIT_SUMMARY        CLOB NOT NULL,
                PAYLOAD_HASH         VARCHAR2(128) NOT NULL,
                CREATED_AT           TIMESTAMP(6) DEFAULT SYSTIMESTAMP NOT NULL,
                NOTES                CLOB,
                CONSTRAINT FK_AWR_WF_AUD_REQ
                    FOREIGN KEY (WORKFLOW_REQUEST_ID)
                    REFERENCES AWR_WORKFLOW_REQUEST (WORKFLOW_REQUEST_ID),
                CONSTRAINT FK_AWR_WF_AUD_TX
                    FOREIGN KEY (TRANSACTION_GROUP_ID)
                    REFERENCES AWR_WORKFLOW_TRANSACTION (TRANSACTION_GROUP_ID)
            )
        ]';
    END IF;
END;
/

DECLARE
    v_exists NUMBER := 0;
BEGIN
    SELECT COUNT(*) INTO v_exists FROM USER_TABLES WHERE TABLE_NAME = 'AWR_WORKFLOW_OUTPUT_ARTIFACT';
    IF v_exists = 0 THEN
        EXECUTE IMMEDIATE q'[
            CREATE TABLE AWR_WORKFLOW_OUTPUT_ARTIFACT (
                WORKFLOW_OUTPUT_ID   VARCHAR2(160) PRIMARY KEY,
                WORKFLOW_REQUEST_ID  VARCHAR2(160) NOT NULL,
                ARTIFACT_TYPE        VARCHAR2(128) NOT NULL,
                ARTIFACT_REFERENCE   VARCHAR2(1024) NOT NULL,
                ARTIFACT_SUMMARY     CLOB,
                ARTIFACT_METADATA_CLOB CLOB,
                STATUS               VARCHAR2(64) DEFAULT 'RECORDED' NOT NULL,
                CREATED_AT           TIMESTAMP(6) DEFAULT SYSTIMESTAMP NOT NULL,
                NOTES                CLOB,
                CONSTRAINT FK_AWR_WF_OUT_REQ
                    FOREIGN KEY (WORKFLOW_REQUEST_ID)
                    REFERENCES AWR_WORKFLOW_REQUEST (WORKFLOW_REQUEST_ID),
                CONSTRAINT CK_AWR_WF_OUT_METADATA_JSON
                    CHECK (ARTIFACT_METADATA_CLOB IS JSON),
                CONSTRAINT CK_AWR_WF_OUT_TYPE
                    CHECK (ARTIFACT_TYPE IN (
                        'validation_response',
                        'analysis_run_record',
                        'phase4i_payload_reference',
                        'dashboard_artifact_reference',
                        'comparison_artifact',
                        'error_artifact',
                        'source_validation_artifact',
                        'object_storage_load_artifact',
                        'workflow_audit_artifact'
                    )),
                CONSTRAINT CK_AWR_WF_OUT_STATUS
                    CHECK (STATUS IN (
                        'RECORDED',
                        'PENDING',
                        'FAILED',
                        'SUPERSEDED'
                    ))
            )
        ]';
    END IF;
END;
/

DECLARE
    v_exists NUMBER := 0;
BEGIN
    SELECT COUNT(*) INTO v_exists FROM USER_INDEXES WHERE INDEX_NAME = 'IX_AWR_WF_REQ_TX';
    IF v_exists = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX IX_AWR_WF_REQ_TX ON AWR_WORKFLOW_REQUEST (TRANSACTION_GROUP_ID)';
    END IF;
END;
/

DECLARE
    v_exists NUMBER := 0;
BEGIN
    SELECT COUNT(*) INTO v_exists FROM USER_INDEXES WHERE INDEX_NAME = 'IX_AWR_WF_REQ_STATUS';
    IF v_exists = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX IX_AWR_WF_REQ_STATUS ON AWR_WORKFLOW_REQUEST (WORKFLOW_TYPE, STATUS, CREATED_AT)';
    END IF;
END;
/

DECLARE
    v_exists NUMBER := 0;
BEGIN
    SELECT COUNT(*) INTO v_exists FROM USER_INDEXES WHERE INDEX_NAME = 'IX_AWR_WF_VAL_REQ';
    IF v_exists = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX IX_AWR_WF_VAL_REQ ON AWR_WORKFLOW_VALIDATION (WORKFLOW_REQUEST_ID)';
    END IF;
END;
/

DECLARE
    v_exists NUMBER := 0;
BEGIN
    SELECT COUNT(*) INTO v_exists FROM USER_INDEXES WHERE INDEX_NAME = 'IX_AWR_WF_AUD_REQ';
    IF v_exists = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX IX_AWR_WF_AUD_REQ ON AWR_WORKFLOW_AUDIT (WORKFLOW_REQUEST_ID)';
    END IF;
END;
/

DECLARE
    v_exists NUMBER := 0;
BEGIN
    SELECT COUNT(*) INTO v_exists FROM USER_INDEXES WHERE INDEX_NAME = 'IX_AWR_WF_AUD_TX';
    IF v_exists = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX IX_AWR_WF_AUD_TX ON AWR_WORKFLOW_AUDIT (TRANSACTION_GROUP_ID)';
    END IF;
END;
/

DECLARE
    v_exists NUMBER := 0;
BEGIN
    SELECT COUNT(*) INTO v_exists FROM USER_INDEXES WHERE INDEX_NAME = 'IX_AWR_WF_OUT_REQ';
    IF v_exists = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX IX_AWR_WF_OUT_REQ ON AWR_WORKFLOW_OUTPUT_ARTIFACT (WORKFLOW_REQUEST_ID)';
    END IF;
END;
/

DECLARE
    v_exists NUMBER := 0;
BEGIN
    SELECT COUNT(*) INTO v_exists FROM USER_INDEXES WHERE INDEX_NAME = 'IX_AWR_WF_OUT_TYPE';
    IF v_exists = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX IX_AWR_WF_OUT_TYPE ON AWR_WORKFLOW_OUTPUT_ARTIFACT (ARTIFACT_TYPE, STATUS, CREATED_AT)';
    END IF;
END;
/
