--------------------------------------------------------------------------------
-- AWR SIZING ADVISOR
-- SCOPED HISTORY VALIDATION QUERIES (SQLcl SAFE VERSION)
--------------------------------------------------------------------------------

set verify off
set feedback on
set pages 200
set lines 200

--------------------------------------------------------------------------------
-- INPUT PARAMETERS (SAFE FOR SQLcl)
--------------------------------------------------------------------------------
accept DBID prompt 'Enter DBID: '
accept HOST_NAME prompt 'Enter HOST_NAME: '
accept INSTANCE_NUMBER prompt 'Enter INSTANCE_NUMBER: '
accept METRIC_NAME prompt 'Enter METRIC_NAME (e.g. CPU_UTIL_P95): '
accept START_TIME prompt 'Enter START_TIME (YYYY-MM-DD HH24:MI:SS): '
accept END_TIME prompt 'Enter END_TIME (YYYY-MM-DD HH24:MI:SS): '

--------------------------------------------------------------------------------
-- 1. DATABASE-WIDE METRIC HISTORY
--------------------------------------------------------------------------------
prompt === DATABASE METRIC HISTORY ===
SELECT
    DB_NAME,
    DBID,
    SNAP_END_TIME,
    METRIC_DOMAIN,
    METRIC_NAME,
    METRIC_VALUE_NUM,
    UNIT_OF_MEASURE
FROM VW_AWR_METRIC_SCOPE
WHERE DBID = &DBID
  AND SNAP_END_TIME BETWEEN
      TO_TIMESTAMP('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  AND TO_TIMESTAMP('&END_TIME','YYYY-MM-DD HH24:MI:SS')
  AND METRIC_NAME = '&METRIC_NAME'
ORDER BY SNAP_END_TIME;

--------------------------------------------------------------------------------
-- 2. HOST-SPECIFIC METRIC HISTORY
--------------------------------------------------------------------------------
prompt === HOST METRIC HISTORY ===
SELECT
    HOST_NAME,
    SNAP_END_TIME,
    METRIC_DOMAIN,
    METRIC_NAME,
    METRIC_VALUE_NUM,
    UNIT_OF_MEASURE
FROM VW_AWR_METRIC_SCOPE
WHERE HOST_NAME = '&HOST_NAME'
  AND SNAP_END_TIME BETWEEN
      TO_TIMESTAMP('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  AND TO_TIMESTAMP('&END_TIME','YYYY-MM-DD HH24:MI:SS')
  AND METRIC_NAME = '&METRIC_NAME'
ORDER BY SNAP_END_TIME;

--------------------------------------------------------------------------------
-- 3. INSTANCE-SPECIFIC METRIC HISTORY
--------------------------------------------------------------------------------
prompt === INSTANCE METRIC HISTORY ===
SELECT
    INSTANCE_NAME,
    INSTANCE_NUMBER,
    SNAP_END_TIME,
    METRIC_NAME,
    METRIC_VALUE_NUM,
    UNIT_OF_MEASURE
FROM VW_AWR_METRIC_SCOPE
WHERE DBID = &DBID
  AND INSTANCE_NUMBER = &INSTANCE_NUMBER
  AND SNAP_END_TIME BETWEEN
      TO_TIMESTAMP('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  AND TO_TIMESTAMP('&END_TIME','YYYY-MM-DD HH24:MI:SS')
  AND METRIC_NAME = '&METRIC_NAME'
ORDER BY SNAP_END_TIME;

--------------------------------------------------------------------------------
-- 4. DUPLICATE CHECK (CRITICAL)
--------------------------------------------------------------------------------
prompt === DUPLICATE CHECK (FEATURE SCOPE) ===
SELECT
    DB_NAME,
    SNAP_BEGIN_TIME,
    COUNT(*) AS ROW_COUNT
FROM VW_AWR_FEATURE_SCOPE
GROUP BY DB_NAME, SNAP_BEGIN_TIME
HAVING COUNT(*) > 1
ORDER BY SNAP_BEGIN_TIME;

--------------------------------------------------------------------------------
-- 5. DUPLICATE CHECK (_P95 METRICS)
--------------------------------------------------------------------------------
prompt === DUPLICATE CHECK (FEATURE METRICS) ===
SELECT
    DB_NAME,
    SNAP_BEGIN_TIME,
    METRIC_NAME,
    COUNT(*) AS ROW_COUNT
FROM VW_AWR_FEATURE_METRIC_SCOPE
GROUP BY DB_NAME, SNAP_BEGIN_TIME, METRIC_NAME
HAVING COUNT(*) > 1
ORDER BY SNAP_BEGIN_TIME, METRIC_NAME;

--------------------------------------------------------------------------------
-- 6. SAMPLE CPU P95 TREND
--------------------------------------------------------------------------------
prompt === CPU_UTIL_P95 TREND ===
SELECT
    DB_NAME,
    SNAP_BEGIN_TIME,
    METRIC_VALUE_NUM AS CPU_UTIL_P95
FROM VW_AWR_FEATURE_METRIC_SCOPE
WHERE METRIC_NAME = 'CPU_UTIL_P95'
ORDER BY SNAP_BEGIN_TIME;

--------------------------------------------------------------------------------
-- END
--------------------------------------------------------------------------------
