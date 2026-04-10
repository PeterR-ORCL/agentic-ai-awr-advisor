--------------------------------------------------------------------------------
-- AWR SIZING ADVISOR
-- DDlv8: DB-SCOPE METRIC TREND STORAGE
--
-- Purpose:
--   Persist deterministic trend and anomaly signals derived from
--   VW_AWR_FEATURE_METRIC_DB_SCOPE.
--
-- Notes:
--   - Additive only; no existing tables or views are modified here.
--   - DBID is included as a stable identifier alongside DB_NAME.
--   - One row per DB + metric + snapshot begin time.
--------------------------------------------------------------------------------
spool ddlv8_db_metric_trend.log

CREATE TABLE AWR_DB_METRIC_TREND (
    DB_METRIC_TREND_ID       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    DB_NAME                  VARCHAR2(128)        NOT NULL,
    DBID                     NUMBER,
    METRIC_NAME              VARCHAR2(128)        NOT NULL,
    SNAP_BEGIN_TIME          TIMESTAMP(6)         NOT NULL,
    METRIC_VALUE_NUM         NUMBER(18,8),
    ROLLING_MEAN             NUMBER(18,8),
    ROLLING_STD              NUMBER(18,8),
    SLOPE                    NUMBER(18,8),
    PERCENT_CHANGE           NUMBER(18,8),
    ANOMALY_FLAG             CHAR(1) DEFAULT 'N' NOT NULL,
    ANOMALY_TYPE             VARCHAR2(64),
    ANOMALY_SCORE            VARCHAR2(20),
    BASELINE_MEAN            NUMBER(18,8),
    BASELINE_STD             NUMBER(18,8),
    CREATED_AT               TIMESTAMP(6) DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT CK_AWR_DB_METRIC_TREND_FLAG
        CHECK (ANOMALY_FLAG IN ('Y','N')),
    CONSTRAINT CK_AWR_DB_METRIC_TREND_SCORE
        CHECK (ANOMALY_SCORE IN ('LOW','MEDIUM','HIGH') OR ANOMALY_SCORE IS NULL)
)
PARTITION BY RANGE (SNAP_BEGIN_TIME)
INTERVAL (NUMTOYMINTERVAL(1, 'MONTH'))
(
    PARTITION P_AWR_DB_METRIC_TREND_BOOTSTRAP
    VALUES LESS THAN (TIMESTAMP '2025-01-01 00:00:00')
);

CREATE UNIQUE INDEX IX_AWR_DB_METRIC_TREND_U01
    ON AWR_DB_METRIC_TREND (DB_NAME, NVL(DBID, -1), METRIC_NAME, SNAP_BEGIN_TIME);

CREATE INDEX IX_AWR_DB_METRIC_TREND_01
    ON AWR_DB_METRIC_TREND (DB_NAME, METRIC_NAME, SNAP_BEGIN_TIME) LOCAL;

CREATE INDEX IX_AWR_DB_METRIC_TREND_02
    ON AWR_DB_METRIC_TREND (ANOMALY_FLAG, ANOMALY_TYPE, SNAP_BEGIN_TIME) LOCAL;

spool off
