--------------------------------------------------------------------------------
-- AWR SIZING ADVISOR
-- POST-RELOAD VALIDATION SCRIPT (SQLcl SAFE)
--
-- Purpose:
--   Validate that:
--     - No duplicate AWR reports were ingested
--     - Canonical scope views (ddlv6) behave correctly
--     - Feature + score layers are consistent
--     - Engineered metrics (_P95) are stable
--
-- Run AFTER:
--   - cleanup script
--   - fresh AWR reload
--------------------------------------------------------------------------------

spool post_validation_reload.log

set pagesize 200
set linesize 220
set verify off
set feedback on
set define on

define DB_NAME='FINDB'
define START_TIME='2026-03-28 00:00:00'
define END_TIME='2026-03-30 00:00:00'
define METRIC_NAME='CPU_UTIL_P95'

prompt
prompt ============================================================
prompt 1. Row counts (sanity check)
prompt ============================================================

select 'AWR_REPORT' as table_name, count(*) from AWR_REPORT
union all
select 'AWR_FEATURE_VECTOR', count(*) from AWR_FEATURE_VECTOR
union all
select 'AWR_SCORE_RESULT', count(*) from AWR_SCORE_RESULT
union all
select 'AWR_METRIC_FACT', count(*) from AWR_METRIC_FACT
order by 1;

prompt
prompt ============================================================
prompt 2. Duplicate logical AWR reports (MUST BE ZERO)
prompt ============================================================

select
    source_system_id,
    dbid,
    instance_number,
    snap_id_begin,
    snap_id_end,
    snap_time_begin,
    snap_time_end,
    count(*) as row_count
from awr_report
group by
    source_system_id,
    dbid,
    instance_number,
    snap_id_begin,
    snap_id_end,
    snap_time_begin,
    snap_time_end
having count(*) > 1
order by snap_time_begin;

prompt
prompt ============================================================
prompt 3. Duplicate file hash (MUST BE ZERO)
prompt ============================================================

select
    source_system_id,
    file_hash_sha256,
    count(*) as row_count
from awr_report
group by source_system_id, file_hash_sha256
having count(*) > 1;

prompt
prompt ============================================================
prompt 4. Snapshot coverage (should be clean hourly sequence)
prompt ============================================================

select
    db_name,
    snap_begin_time,
    snap_end_time
from vw_awr_scope_context
where db_name = '&DB_NAME'
order by snap_begin_time;

prompt
prompt ============================================================
prompt 5. Feature scope cardinality (EXPECTED: 1 per instance)
prompt ============================================================

select
    db_name,
    snap_begin_time,
    count(*) as row_count
from vw_awr_feature_scope
where db_name = '&DB_NAME'
group by db_name, snap_begin_time
order by snap_begin_time;

prompt
prompt ============================================================
prompt 6. Feature scope duplicates per instance (MUST BE ZERO)
prompt ============================================================

select
    db_name,
    host_name,
    instance_number,
    snap_begin_time,
    count(*) as row_count
from vw_awr_feature_scope
where db_name = '&DB_NAME'
group by db_name, host_name, instance_number, snap_begin_time
having count(*) > 1;

prompt
prompt ============================================================
prompt 7. Score scope duplicates (MUST BE ZERO)
prompt ============================================================

select
    db_name,
    host_name,
    instance_number,
    snap_begin_time,
    count(*) as row_count
from vw_awr_score_scope
where db_name = '&DB_NAME'
group by db_name, host_name, instance_number, snap_begin_time
having count(*) > 1;

prompt
prompt ============================================================
prompt 8. Engineered metric history (raw scope)
prompt ============================================================

select
    db_name,
    host_name,
    instance_number,
    snap_begin_time,
    metric_name,
    metric_value_num
from vw_awr_feature_metric_scope
where db_name = '&DB_NAME'
  and metric_name = '&METRIC_NAME'
order by snap_begin_time, instance_number;

prompt
prompt ============================================================
prompt 9. Engineered metric DB-level collapse (KEY CHECK)
prompt EXPECT: 1 row per snapshot
prompt ============================================================

select
    db_name,
    snap_begin_time,
    metric_name,
    min(metric_value_num) as metric_value,
    count(*) as contributing_rows
from vw_awr_feature_metric_scope
where db_name = '&DB_NAME'
  and metric_name = '&METRIC_NAME'
group by db_name, snap_begin_time, metric_name
order by snap_begin_time;

prompt
prompt ============================================================
prompt 10. Engineered metric duplicates (EXPECTED > 1 for RAC)
prompt ============================================================

select
    db_name,
    snap_begin_time,
    metric_name,
    count(*) as row_count
from vw_awr_feature_metric_scope
where db_name = '&DB_NAME'
group by db_name, snap_begin_time, metric_name
having count(*) > 1
order by snap_begin_time;

prompt
prompt ============================================================
prompt 11. RAC sanity check (instance distribution)
prompt ============================================================

select
    db_name,
    snap_begin_time,
    instance_number,
    count(*) as row_count
from vw_awr_feature_scope
where db_name = '&DB_NAME'
group by db_name, snap_begin_time, instance_number
order by snap_begin_time, instance_number;

prompt
prompt ============================================================
prompt 12. CPU_UTIL_P95 trend (final sanity check)
prompt ============================================================

select
    snap_begin_time,
    min(metric_value_num) as cpu_p95,
    count(*) as rows_per_snapshot
from vw_awr_feature_metric_scope
where db_name = '&DB_NAME'
  and metric_name = 'CPU_UTIL_P95'
group by snap_begin_time
order by snap_begin_time;

prompt
prompt ============================================================
prompt VALIDATION COMPLETE
prompt ============================================================

spool off
