--------------------------------------------------------------------------------
-- AWR SIZING ADVISOR
-- DDlv7: DB-LEVEL ENGINEERED FEATURE METRIC SCOPE
--
-- Purpose:
--   Surface engineered feature metrics at honest DB scope with one canonical
--   row per DB + snapshot + metric.
--
-- Source:
--   VW_AWR_FEATURE_METRIC_SCOPE
--
-- Canonical DB-level collapse rule:
--   1. Group by DB_NAME + DBID + SNAP_BEGIN_TIME + SNAP_END_TIME + METRIC_NAME.
--   2. If all contributing report-context rows carry the same metric value,
--      keep that exact value.
--   3. If values differ, keep the metric value from the canonical winning
--      report context for that DB snapshot + metric.
--
-- Winner alignment:
--   The winning report context uses the same deterministic ordering already
--   established in the canonical scoped-report layer:
--     latest AWR_REPORT.CREATED_AT, then highest AWR_ID.
--
-- Notes:
--   - Engineered metrics remain honestly DB-scoped today.
--   - Host / instance derivation is not fabricated here.
--------------------------------------------------------------------------------
spool ddlv7_feature_metric_db_scope.log

CREATE OR REPLACE VIEW VW_AWR_FEATURE_METRIC_DB_SCOPE AS
WITH db_metric_rollup AS (
    SELECT
        COALESCE(fms.DB_NAME, 'UNKNOWN') AS NORMALIZED_DB_NAME,
        NVL(fms.DBID, -1) AS NORMALIZED_DBID,
        fms.DB_NAME,
        fms.DBID,
        fms.SNAP_BEGIN_TIME,
        fms.SNAP_END_TIME,
        fms.METRIC_NAME,
        COUNT(*) AS CONTRIBUTING_REPORT_COUNT,
        COUNT(DISTINCT fms.AWR_ID) AS AWR_COUNT,
        COUNT(DISTINCT fms.METRIC_VALUE_NUM) AS DISTINCT_VALUE_COUNT,
        MIN(fms.METRIC_VALUE_NUM) AS IDENTICAL_METRIC_VALUE_NUM
    FROM VW_AWR_FEATURE_METRIC_SCOPE fms
    GROUP BY
        COALESCE(fms.DB_NAME, 'UNKNOWN'),
        NVL(fms.DBID, -1),
        fms.DB_NAME,
        fms.DBID,
        fms.SNAP_BEGIN_TIME,
        fms.SNAP_END_TIME,
        fms.METRIC_NAME
),
db_metric_context_winner AS (
    SELECT
        fms.DB_NAME,
        fms.DBID,
        fms.SNAP_BEGIN_TIME,
        fms.SNAP_END_TIME,
        fms.DB_VERSION,
        fms.DATABASE_ROLE,
        fms.INSTANCE_COUNT,
        fms.PLATFORM,
        fms.TOPOLOGY_CLASS,
        fms.PLATFORM_CLASS,
        fms.METRIC_NAME,
        fms.METRIC_CATEGORY,
        fms.METRIC_VALUE_NUM,
        fms.AWR_ID,
        COALESCE(fms.DB_NAME, 'UNKNOWN') AS NORMALIZED_DB_NAME,
        NVL(fms.DBID, -1) AS NORMALIZED_DBID,
        ROW_NUMBER() OVER (
            PARTITION BY
                COALESCE(fms.DB_NAME, 'UNKNOWN'),
                NVL(fms.DBID, -1),
                fms.SNAP_BEGIN_TIME,
                fms.SNAP_END_TIME,
                fms.METRIC_NAME
            ORDER BY r.CREATED_AT DESC, fms.AWR_ID DESC
        ) AS RN
    FROM VW_AWR_FEATURE_METRIC_SCOPE fms
    JOIN AWR_REPORT r
      ON r.AWR_ID = fms.AWR_ID
     AND r.SOURCE_SYSTEM_ID = fms.SOURCE_SYSTEM_ID
)
SELECT
    winner.DB_NAME,
    winner.DBID,
    winner.SNAP_BEGIN_TIME,
    winner.SNAP_END_TIME,
    winner.DB_VERSION,
    winner.DATABASE_ROLE,
    winner.INSTANCE_COUNT,
    winner.PLATFORM,
    winner.TOPOLOGY_CLASS,
    winner.PLATFORM_CLASS,
    rollup.METRIC_NAME,
    'DB' AS METRIC_SCOPE,
    winner.METRIC_CATEGORY,
    CASE
        WHEN rollup.DISTINCT_VALUE_COUNT <= 1
        THEN rollup.IDENTICAL_METRIC_VALUE_NUM
        ELSE winner.METRIC_VALUE_NUM
    END AS METRIC_VALUE_NUM,
    rollup.CONTRIBUTING_REPORT_COUNT,
    rollup.AWR_COUNT,
    TO_CHAR(winner.SNAP_BEGIN_TIME, 'YYYY-MM-DD HH24:MI')
    || ' - '
    || TO_CHAR(winner.SNAP_END_TIME, 'YYYY-MM-DD HH24:MI') AS SNAPSHOT_LABEL,
    rollup.DISTINCT_VALUE_COUNT,
    CASE
        WHEN rollup.DISTINCT_VALUE_COUNT <= 1
        THEN 'IDENTICAL_VALUE'
        ELSE 'CANONICAL_REPORT_WINNER'
    END AS VALUE_COLLAPSE_RULE,
    CASE
        WHEN rollup.DISTINCT_VALUE_COUNT <= 1
        THEN 'CONSISTENT'
        ELSE 'CONFLICTING_REPORT_CONTEXT_VALUES'
    END AS DATA_QUALITY_FLAG
FROM db_metric_rollup rollup
JOIN db_metric_context_winner winner
  ON winner.NORMALIZED_DB_NAME = rollup.NORMALIZED_DB_NAME
 AND winner.NORMALIZED_DBID = rollup.NORMALIZED_DBID
 AND winner.SNAP_BEGIN_TIME = rollup.SNAP_BEGIN_TIME
 AND winner.SNAP_END_TIME = rollup.SNAP_END_TIME
 AND winner.METRIC_NAME = rollup.METRIC_NAME
 AND winner.RN = 1;

spool off
