--------------------------------------------------------------------------------
-- AWR SIZING ADVISOR
-- SCOPED HISTORY VALIDATION QUERIES (SQLcl SAFE)
--------------------------------------------------------------------------------

spool scope_validation_after_ddlv6.log

set pagesize 200
set linesize 220
set verify off
set feedback on
set serveroutput on
set define on

prompt ============================================================
prompt AWR Sizing Advisor - Scoped Validation
prompt Override any DEFINE values before running if needed
prompt Example:
prompt   DEFINE DB_NAME='FINDB'
prompt   DEFINE HOST_NAME='exa-rac-node01'
prompt   @scope_validation_queries.sql
prompt ============================================================

define DB_NAME='FINDB'
define DBID='0'
define SOURCE_SYSTEM_ID='0'
define HOST_NAME='exa-rac-node01'
define INSTANCE_NAME='FINDB1'
define INSTANCE_NUMBER='1'
define START_TIME='2026-03-29 00:00:00'
define END_TIME='2026-03-29 23:59:59'
define METRIC_NAME='DB CPU(s)'
define FEATURE_METRIC_NAME='CPU_UTIL_P95'
define FILE_HASH_SHA256='REPLACE_WITH_REAL_FILE_HASH'
define SNAP_ID_BEGIN='0'
define SNAP_ID_END='0'
define SNAP_TIME_BEGIN='2026-03-29 00:00:00'
define SNAP_TIME_END='2026-03-29 01:00:00'

prompt
prompt ============================================================
prompt 1. Confirm scoped views exist
prompt ============================================================

select view_name
from user_views
where view_name in (
  'VW_AWR_SCOPE_CONTEXT',
  'VW_AWR_METRIC_SCOPE',
  'VW_AWR_SQL_SCOPE',
  'VW_AWR_WAIT_SCOPE',
  'VW_AWR_FEATURE_SCOPE',
  'VW_AWR_SCORE_SCOPE',
  'VW_AWR_FEATURE_METRIC_SCOPE',
  'VW_AWR_FEATURE_METRIC_DB_SCOPE'
)
order by view_name;

prompt
prompt ============================================================
prompt 2. Discover available raw metric names for DB/timeframe
prompt ============================================================

select distinct metric_name
from vw_awr_metric_scope
where db_name = '&DB_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by metric_name;

prompt
prompt ============================================================
prompt 3. Database-wide raw metric history
prompt ============================================================

select
    db_name,
    dbid,
    host_name,
    instance_name,
    instance_number,
    snap_begin_time,
    snap_end_time,
    metric_domain,
    metric_name,
    metric_value_num,
    unit_of_measure
from vw_awr_metric_scope
where db_name = '&DB_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
  and metric_name = '&METRIC_NAME'
order by snap_begin_time, host_name, instance_number;

prompt
prompt ============================================================
prompt 4. Host-specific raw metric history
prompt ============================================================

select
    db_name,
    host_name,
    instance_name,
    instance_number,
    snap_begin_time,
    metric_name,
    metric_value_num,
    unit_of_measure
from vw_awr_metric_scope
where db_name = '&DB_NAME'
  and host_name = '&HOST_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
  and metric_name = '&METRIC_NAME'
order by snap_begin_time, instance_number;

prompt
prompt ============================================================
prompt 5. Instance-specific raw metric history
prompt ============================================================

select
    db_name,
    instance_name,
    instance_number,
    snap_begin_time,
    metric_name,
    metric_value_num,
    unit_of_measure
from vw_awr_metric_scope
where db_name = '&DB_NAME'
  and instance_name = '&INSTANCE_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
  and metric_name = '&METRIC_NAME'
order by snap_begin_time;

prompt
prompt ============================================================
prompt 6. Host-specific wait history
prompt ============================================================

select
    db_name,
    host_name,
    instance_name,
    snap_begin_time,
    wait_class,
    event_name,
    pct_db_time
from vw_awr_wait_scope
where db_name = '&DB_NAME'
  and host_name = '&HOST_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by snap_begin_time, pct_db_time desc;

prompt
prompt ============================================================
prompt 7. Instance-specific SQL history
prompt ============================================================

select
    db_name,
    instance_name,
    instance_number,
    snap_begin_time,
    sql_id,
    elapsed_time_sec,
    cpu_time_sec,
    executions
from vw_awr_sql_scope
where db_name = '&DB_NAME'
  and instance_name = '&INSTANCE_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by snap_begin_time, elapsed_time_sec desc;

prompt
prompt ============================================================
prompt 8. Canonical feature history by report scope
prompt ============================================================

select
    db_name,
    host_name,
    instance_name,
    instance_number,
    snap_begin_time,
    feature_vector_id,
    observed_at,
    workload_class,
    feature_topology_class,
    feature_platform_class,
    feature_event_class
from vw_awr_feature_scope
where db_name = '&DB_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by snap_begin_time, host_name, instance_number;

prompt
prompt ============================================================
prompt 9. Canonical score history by report scope
prompt ============================================================

select
    db_name,
    host_name,
    instance_name,
    instance_number,
    snap_begin_time,
    score_result_id,
    scored_at,
    workload_class,
    primary_signal_domain,
    total_score,
    confidence_score
from vw_awr_score_scope
where db_name = '&DB_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by snap_begin_time, host_name, instance_number;

prompt
prompt ============================================================
prompt 10. Engineered metric history by report scope
prompt Note: current engineered metrics are DB-scoped semantically,
prompt but may repeat per canonical report/instance context
prompt ============================================================

select
    db_name,
    host_name,
    instance_name,
    instance_number,
    snap_begin_time,
    metric_scope,
    metric_name,
    metric_category,
    metric_value_num
from vw_awr_feature_metric_scope
where db_name = '&DB_NAME'
  and metric_name = '&FEATURE_METRIC_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by snap_begin_time, host_name, instance_number;

prompt
prompt ============================================================
prompt 11. Engineered metric history collapsed to DB + snapshot
prompt This is the practical DB-level validation for DB-scoped features
prompt ============================================================

select
    db_name,
    snap_begin_time,
    metric_name,
    min(metric_value_num) as metric_value_num,
    count(*) as contributing_rows
from vw_awr_feature_metric_scope
where db_name = '&DB_NAME'
  and metric_name = '&FEATURE_METRIC_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
group by db_name, snap_begin_time, metric_name
order by snap_begin_time;

prompt
prompt ============================================================
prompt 12. Feature-scope duplicate check by report scope
prompt Expect zero rows if canonical logical report selection is working
prompt ============================================================

select
    db_name,
    host_name,
    instance_number,
    snap_begin_time,
    count(*) as row_count
from vw_awr_feature_scope
where db_name = '&DB_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
group by db_name, host_name, instance_number, snap_begin_time
having count(*) > 1
order by snap_begin_time, host_name, instance_number;

prompt
prompt ============================================================
prompt 13. Feature metric duplicate check by report scope
prompt Expect zero rows if canonical report selection is working
prompt ============================================================

select
    db_name,
    host_name,
    instance_number,
    snap_begin_time,
    metric_name,
    count(*) as row_count
from vw_awr_feature_metric_scope
where db_name = '&DB_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
group by db_name, host_name, instance_number, snap_begin_time, metric_name
having count(*) > 1
order by snap_begin_time, host_name, instance_number, metric_name;

prompt
prompt ============================================================
prompt 14. DB-level repeated engineered metric rows
prompt This shows DB-scoped feature repetition across report contexts
prompt ============================================================

select
    db_name,
    snap_begin_time,
    metric_name,
    count(*) as row_count
from vw_awr_feature_metric_scope
where db_name = '&DB_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
group by db_name, snap_begin_time, metric_name
having count(*) > 1
order by snap_begin_time, metric_name;

prompt
prompt ============================================================
prompt 15. Score-scope duplicate check by report scope
prompt Expect zero rows if canonical score selection is working
prompt ============================================================

select
    db_name,
    host_name,
    instance_number,
    snap_begin_time,
    count(*) as row_count
from vw_awr_score_scope
where db_name = '&DB_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
group by db_name, host_name, instance_number, snap_begin_time
having count(*) > 1
order by snap_begin_time, host_name, instance_number;

prompt
prompt ============================================================
prompt 16. Raw logical duplicate reports in AWR_REPORT
prompt Historical duplicates may still exist in base data
prompt ============================================================

with report_scope_candidates as (
    select
        r.awr_id,
        r.source_system_id,
        coalesce(
            r.dbid,
            json_value(r.raw_metadata_json,'$.dbid' returning number null on error)
        ) as resolved_dbid,
        coalesce(
            r.instance_number,
            json_value(r.raw_metadata_json,'$.instance_number' returning number null on error)
        ) as resolved_instance_number,
        r.snap_id_begin,
        r.snap_id_end,
        r.snap_time_begin,
        r.snap_time_end,
        r.file_hash_sha256,
        case
            when coalesce(
                r.dbid,
                json_value(r.raw_metadata_json,'$.dbid' returning number null on error)
            ) is not null
             and coalesce(
                r.instance_number,
                json_value(r.raw_metadata_json,'$.instance_number' returning number null on error)
            ) is not null
             and r.snap_id_begin is not null
             and r.snap_id_end is not null
             and r.snap_time_begin is not null
             and r.snap_time_end is not null
            then 'LOGICAL_SNAPSHOT'
            else 'FILE_HASH'
        end as canonical_key_type
    from awr_report r
)
select
    source_system_id,
    canonical_key_type,
    resolved_dbid as dbid,
    resolved_instance_number as instance_number,
    snap_id_begin,
    snap_id_end,
    snap_time_begin,
    snap_time_end,
    file_hash_sha256,
    count(*) as row_count
from report_scope_candidates
group by
    source_system_id,
    canonical_key_type,
    resolved_dbid,
    resolved_instance_number,
    snap_id_begin,
    snap_id_end,
    snap_time_begin,
    snap_time_end,
    file_hash_sha256
having count(*) > 1
order by snap_time_begin, source_system_id, dbid, instance_number;

prompt
prompt ============================================================
prompt 17. Exact duplicate file hash check
prompt ============================================================

select
    source_system_id,
    file_hash_sha256,
    count(*) as row_count
from awr_report
group by source_system_id, file_hash_sha256
having count(*) > 1
order by row_count desc, source_system_id, file_hash_sha256;

prompt
prompt ============================================================
prompt 18. Duplicate-ingest guardrail verification (exact hash)
prompt ============================================================

select
    awr_id,
    source_system_id,
    source_file_name,
    file_hash_sha256,
    ingest_mode,
    created_at
from awr_report
where source_system_id = &SOURCE_SYSTEM_ID
  and file_hash_sha256 = '&FILE_HASH_SHA256'
order by awr_id desc;

prompt
prompt ============================================================
prompt 19. Duplicate-ingest guardrail verification (logical snapshot identity)
prompt ============================================================

select
    awr_id,
    source_system_id,
    dbid,
    instance_number,
    snap_id_begin,
    snap_id_end,
    snap_time_begin,
    snap_time_end,
    ingest_mode,
    created_at
from awr_report
where source_system_id = &SOURCE_SYSTEM_ID
  and dbid = &DBID
  and instance_number = &INSTANCE_NUMBER
  and snap_id_begin = &SNAP_ID_BEGIN
  and snap_id_end = &SNAP_ID_END
  and snap_time_begin = to_timestamp('&SNAP_TIME_BEGIN','YYYY-MM-DD HH24:MI:SS')
  and snap_time_end   = to_timestamp('&SNAP_TIME_END','YYYY-MM-DD HH24:MI:SS')
order by awr_id desc;

prompt
prompt ============================================================
prompt 20. Chosen engineered metric history
prompt ============================================================

select
    db_name,
    host_name,
    instance_name,
    instance_number,
    snap_begin_time,
    metric_name,
    metric_scope,
    metric_category,
    metric_value_num
from vw_awr_feature_metric_scope
where db_name = '&DB_NAME'
  and metric_name = '&FEATURE_METRIC_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by snap_begin_time, host_name, instance_number;

prompt
prompt ============================================================
prompt 21. DB-level engineered metric history
prompt ============================================================

select
    db_name,
    dbid,
    snap_begin_time,
    snap_end_time,
    metric_name,
    metric_scope,
    metric_category,
    metric_value_num,
    contributing_report_count,
    awr_count,
    distinct_value_count,
    value_collapse_rule
from vw_awr_feature_metric_db_scope
where db_name = '&DB_NAME'
  and metric_name = '&FEATURE_METRIC_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by snap_begin_time;

prompt
prompt ============================================================
prompt 22. DB-level engineered metric duplicate row check
prompt Expect zero rows
prompt ============================================================

select
    db_name,
    snap_begin_time,
    metric_name,
    count(*) as row_count
from vw_awr_feature_metric_db_scope
where db_name = '&DB_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
group by db_name, snap_begin_time, metric_name
having count(*) > 1
order by snap_begin_time, metric_name;

prompt
prompt ============================================================
prompt 23. DB-level CPU_UTIL_P95 history
prompt ============================================================

select
    db_name,
    snap_begin_time,
    metric_value_num as cpu_util_p95,
    contributing_report_count,
    awr_count,
    value_collapse_rule
from vw_awr_feature_metric_db_scope
where db_name = '&DB_NAME'
  and metric_name = 'CPU_UTIL_P95'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by snap_begin_time;

prompt
prompt ============================================================
prompt 24. DB-level RAC and GC engineered metric history
prompt ============================================================

select
    db_name,
    snap_begin_time,
    metric_name,
    metric_value_num,
    contributing_report_count,
    awr_count,
    value_collapse_rule
from vw_awr_feature_metric_db_scope
where db_name = '&DB_NAME'
  and metric_name in (
      'CLUSTER_WAIT_PCT_DB_TIME',
      'GC_CR_WAIT_PCT_DB_TIME',
      'GC_CURRENT_WAIT_PCT_DB_TIME',
      'GC_BUFFER_BUSY_PCT_DB_TIME'
  )
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by snap_begin_time, metric_name;

prompt
prompt ============================================================
prompt 25. DB-level Exadata engineered metric history
prompt ============================================================

select
    db_name,
    snap_begin_time,
    metric_name,
    metric_value_num,
    contributing_report_count,
    awr_count,
    value_collapse_rule
from vw_awr_feature_metric_db_scope
where db_name = '&DB_NAME'
  and metric_name in (
      'EXA_CELL_IO_PCT_DB_TIME',
      'EXA_OFFLOAD_EFFICIENCY',
      'EXA_STORAGE_INDEX_SAVINGS'
  )
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by snap_begin_time, metric_name;

prompt
prompt ============================================================
prompt 26. DB-level Data Guard engineered metric history
prompt ============================================================

select
    db_name,
    snap_begin_time,
    metric_name,
    metric_value_num,
    contributing_report_count,
    awr_count,
    value_collapse_rule
from vw_awr_feature_metric_db_scope
where db_name = '&DB_NAME'
  and metric_name in (
      'TRANSPORT_LAG_SEC',
      'APPLY_LAG_SEC',
      'REDO_TRANSPORT_ISSUE_FLAG'
  )
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by snap_begin_time, metric_name;

prompt
prompt ============================================================
prompt 27. Row-count comparison between report-context and DB-level metric scope
prompt ============================================================

select
    scope_layer,
    row_count
from (
    select
        'VW_AWR_FEATURE_METRIC_SCOPE' as scope_layer,
        count(*) as row_count
    from vw_awr_feature_metric_scope
    where db_name = '&DB_NAME'
      and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
      and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
    union all
    select
        'VW_AWR_FEATURE_METRIC_DB_SCOPE' as scope_layer,
        count(*) as row_count
    from vw_awr_feature_metric_db_scope
    where db_name = '&DB_NAME'
      and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
      and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
);

spool off
