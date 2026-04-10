--------------------------------------------------------------------------------
-- AWR SIZING ADVISOR
-- SCOPED HISTORY VALIDATION QUERIES (SQLcl SAFE)
--------------------------------------------------------------------------------

spool scope_validation_after_ddlv7.log

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
define DBID='1234567890'
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
define FEATURE_JSON_SAMPLE_LIMIT='20'

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
    value_collapse_rule,
    data_quality_flag
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
    value_collapse_rule,
    data_quality_flag
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
    value_collapse_rule,
    data_quality_flag
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
    value_collapse_rule,
    data_quality_flag
from vw_awr_feature_metric_db_scope
where db_name = '&DB_NAME'
  and metric_name in (
      'EXA_CELL_IO_PCT_DB_TIME',
      'EXA_OFFLOAD_EFFICIENCY',
      'STORAGE_INDEX_SAVINGS_PCT',
      'CELL_SINGLE_BLOCK_LATENCY_MS',
      'CELL_MULTIBLOCK_LATENCY_MS'
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
    value_collapse_rule,
    data_quality_flag
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

prompt
prompt ============================================================
prompt 28. Newly promoted engineered metrics present in report-context scope
prompt ============================================================

with target_metrics as (
    select 'DB_CPU_PCT_DB_TIME' as metric_name, 'FACT_REQUIRED' as metric_class from dual union all
    select 'REDO_GENERATION_PER_SEC', 'FACT_REQUIRED' from dual union all
    select 'CELL_SINGLE_BLOCK_LATENCY_MS', 'FACT_REQUIRED' from dual union all
    select 'HARD_PARSE_PCT', 'CONDITIONAL' from dual union all
    select 'NETWORK_WAIT_PCT_DB_TIME', 'CONDITIONAL' from dual union all
    select 'LOG_WRITE_LATENCY_MS', 'CONDITIONAL' from dual union all
    select 'CURSOR_MUTEX_WAIT_PCT_DB_TIME', 'CONDITIONAL' from dual union all
    select 'CELL_MULTIBLOCK_LATENCY_MS', 'CONDITIONAL' from dual union all
    select 'PGA_CACHE_HIT_PCT', 'JSON_ONLY' from dual union all
    select 'TEMP_SPILL_PCT', 'JSON_ONLY' from dual union all
    select 'SORTS_DISK_PCT', 'JSON_ONLY' from dual union all
    select 'WORKAREA_ONEPASS_PCT', 'JSON_ONLY' from dual union all
    select 'WORKAREA_MULTIPASS_PCT', 'JSON_ONLY' from dual union all
    select 'STORAGE_INDEX_SAVINGS_PCT', 'JSON_ONLY' from dual union all
    select 'TEMP_WRITE_LATENCY_MS', 'JSON_ONLY' from dual union all
    select 'WRITE_LATENCY_MS', 'JSON_ONLY' from dual
)
select
    tm.metric_name,
    tm.metric_class,
    fms.metric_category,
    count(*) as row_count,
    min(fms.snap_begin_time) as first_snap_begin_time,
    max(fms.snap_begin_time) as last_snap_begin_time
from target_metrics tm
left join vw_awr_feature_metric_scope fms
  on fms.metric_name = tm.metric_name
 and fms.db_name = '&DB_NAME'
 and fms.snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
 and fms.snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
group by tm.metric_name, tm.metric_class, fms.metric_category
having count(fms.metric_name) > 0
order by tm.metric_class, tm.metric_name;

prompt
prompt ============================================================
prompt 29. Newly promoted engineered metrics present in DB-scope
prompt ============================================================

with target_metrics as (
    select 'DB_CPU_PCT_DB_TIME' as metric_name, 'FACT_REQUIRED' as metric_class from dual union all
    select 'REDO_GENERATION_PER_SEC', 'FACT_REQUIRED' from dual union all
    select 'CELL_SINGLE_BLOCK_LATENCY_MS', 'FACT_REQUIRED' from dual union all
    select 'HARD_PARSE_PCT', 'CONDITIONAL' from dual union all
    select 'NETWORK_WAIT_PCT_DB_TIME', 'CONDITIONAL' from dual union all
    select 'LOG_WRITE_LATENCY_MS', 'CONDITIONAL' from dual union all
    select 'CURSOR_MUTEX_WAIT_PCT_DB_TIME', 'CONDITIONAL' from dual union all
    select 'CELL_MULTIBLOCK_LATENCY_MS', 'CONDITIONAL' from dual union all
    select 'PGA_CACHE_HIT_PCT', 'JSON_ONLY' from dual union all
    select 'TEMP_SPILL_PCT', 'JSON_ONLY' from dual union all
    select 'SORTS_DISK_PCT', 'JSON_ONLY' from dual union all
    select 'WORKAREA_ONEPASS_PCT', 'JSON_ONLY' from dual union all
    select 'WORKAREA_MULTIPASS_PCT', 'JSON_ONLY' from dual union all
    select 'STORAGE_INDEX_SAVINGS_PCT', 'JSON_ONLY' from dual union all
    select 'TEMP_WRITE_LATENCY_MS', 'JSON_ONLY' from dual union all
    select 'WRITE_LATENCY_MS', 'JSON_ONLY' from dual
)
select
    tm.metric_name,
    tm.metric_class,
    fms.metric_category,
    count(*) as row_count,
    min(fms.snap_begin_time) as first_snap_begin_time,
    max(fms.snap_begin_time) as last_snap_begin_time
from target_metrics tm
left join vw_awr_feature_metric_db_scope fms
  on fms.metric_name = tm.metric_name
 and fms.db_name = '&DB_NAME'
 and fms.snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
 and fms.snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
group by tm.metric_name, tm.metric_class, fms.metric_category
having count(fms.metric_name) > 0
order by tm.metric_class, tm.metric_name;

prompt
prompt ============================================================
prompt 30. FEATURE_JSON non-null promoted metric value presence
prompt Note: this checks non-null numeric values, not merely key existence
prompt ============================================================

with target_metrics as (
    select 'DB_CPU_PCT_DB_TIME' as metric_name, 'FACT_REQUIRED' as metric_class from dual union all
    select 'REDO_GENERATION_PER_SEC', 'FACT_REQUIRED' from dual union all
    select 'CELL_SINGLE_BLOCK_LATENCY_MS', 'FACT_REQUIRED' from dual union all
    select 'HARD_PARSE_PCT', 'CONDITIONAL' from dual union all
    select 'NETWORK_WAIT_PCT_DB_TIME', 'CONDITIONAL' from dual union all
    select 'LOG_WRITE_LATENCY_MS', 'CONDITIONAL' from dual union all
    select 'CURSOR_MUTEX_WAIT_PCT_DB_TIME', 'CONDITIONAL' from dual union all
    select 'CELL_MULTIBLOCK_LATENCY_MS', 'CONDITIONAL' from dual union all
    select 'PGA_CACHE_HIT_PCT', 'JSON_ONLY' from dual union all
    select 'TEMP_SPILL_PCT', 'JSON_ONLY' from dual union all
    select 'SORTS_DISK_PCT', 'JSON_ONLY' from dual union all
    select 'WORKAREA_ONEPASS_PCT', 'JSON_ONLY' from dual union all
    select 'WORKAREA_MULTIPASS_PCT', 'JSON_ONLY' from dual union all
    select 'STORAGE_INDEX_SAVINGS_PCT', 'JSON_ONLY' from dual union all
    select 'TEMP_WRITE_LATENCY_MS', 'JSON_ONLY' from dual union all
    select 'WRITE_LATENCY_MS', 'JSON_ONLY' from dual
),
metric_values as (
    select awr_id, 'WRITE_LATENCY_MS' as metric_name,
           json_value(feature_json, '$.WRITE_LATENCY_MS' returning number null on error) as metric_value_num
    from awr_feature_vector
    union all
    select awr_id, 'TEMP_WRITE_LATENCY_MS',
           json_value(feature_json, '$.TEMP_WRITE_LATENCY_MS' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'LOG_WRITE_LATENCY_MS',
           json_value(feature_json, '$.LOG_WRITE_LATENCY_MS' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'NETWORK_WAIT_PCT_DB_TIME',
           json_value(feature_json, '$.NETWORK_WAIT_PCT_DB_TIME' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'HARD_PARSE_PCT',
           json_value(feature_json, '$.HARD_PARSE_PCT' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'PGA_CACHE_HIT_PCT',
           json_value(feature_json, '$.PGA_CACHE_HIT_PCT' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'TEMP_SPILL_PCT',
           json_value(feature_json, '$.TEMP_SPILL_PCT' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'SORTS_DISK_PCT',
           json_value(feature_json, '$.SORTS_DISK_PCT' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'WORKAREA_ONEPASS_PCT',
           json_value(feature_json, '$.WORKAREA_ONEPASS_PCT' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'WORKAREA_MULTIPASS_PCT',
           json_value(feature_json, '$.WORKAREA_MULTIPASS_PCT' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'CURSOR_MUTEX_WAIT_PCT_DB_TIME',
           json_value(feature_json, '$.CURSOR_MUTEX_WAIT_PCT_DB_TIME' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'CELL_SINGLE_BLOCK_LATENCY_MS',
           json_value(feature_json, '$.CELL_SINGLE_BLOCK_LATENCY_MS' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'CELL_MULTIBLOCK_LATENCY_MS',
           json_value(feature_json, '$.CELL_MULTIBLOCK_LATENCY_MS' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'STORAGE_INDEX_SAVINGS_PCT',
           json_value(feature_json, '$.STORAGE_INDEX_SAVINGS_PCT' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'DB_CPU_PCT_DB_TIME',
           json_value(feature_json, '$.DB_CPU_PCT_DB_TIME' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'REDO_GENERATION_PER_SEC',
           json_value(feature_json, '$.REDO_GENERATION_PER_SEC' returning number null on error)
    from awr_feature_vector
)
select
    tm.metric_name,
    tm.metric_class,
    count(*) as feature_vector_rows_with_nonnull_value
from target_metrics tm
join metric_values mv
  on mv.metric_name = tm.metric_name
join awr_report r
  on r.awr_id = mv.awr_id
where r.db_name = '&DB_NAME'
  and r.snap_time_begin >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and r.snap_time_end   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
  and mv.metric_value_num is not null
group by tm.metric_name, tm.metric_class
order by tm.metric_class, tm.metric_name;

prompt
prompt ============================================================
prompt 31. Sample FEATURE_JSON rows for manual inspection
prompt ============================================================

select *
from (
    select
        fv.feature_vector_id,
        fv.awr_id,
        r.db_name,
        r.dbid,
        r.instance_name,
        r.instance_number,
        r.snap_time_begin,
        r.snap_time_end,
        json_serialize(fv.feature_json returning clob pretty) as feature_json_pretty
    from awr_feature_vector fv
    join awr_report r
      on r.awr_id = fv.awr_id
    where r.db_name = '&DB_NAME'
    order by r.snap_time_begin desc
)
where rownum <= 10;

prompt
prompt ============================================================
prompt 32. Newly promoted engineered metric history at DB-scope
prompt ============================================================

with target_metrics as (
    select 'DB_CPU_PCT_DB_TIME' as metric_name, 'FACT_REQUIRED' as metric_class from dual union all
    select 'REDO_GENERATION_PER_SEC', 'FACT_REQUIRED' from dual union all
    select 'CELL_SINGLE_BLOCK_LATENCY_MS', 'FACT_REQUIRED' from dual union all
    select 'HARD_PARSE_PCT', 'CONDITIONAL' from dual union all
    select 'NETWORK_WAIT_PCT_DB_TIME', 'CONDITIONAL' from dual union all
    select 'LOG_WRITE_LATENCY_MS', 'CONDITIONAL' from dual union all
    select 'CURSOR_MUTEX_WAIT_PCT_DB_TIME', 'CONDITIONAL' from dual union all
    select 'CELL_MULTIBLOCK_LATENCY_MS', 'CONDITIONAL' from dual union all
    select 'PGA_CACHE_HIT_PCT', 'JSON_ONLY' from dual union all
    select 'TEMP_SPILL_PCT', 'JSON_ONLY' from dual union all
    select 'SORTS_DISK_PCT', 'JSON_ONLY' from dual union all
    select 'WORKAREA_ONEPASS_PCT', 'JSON_ONLY' from dual union all
    select 'WORKAREA_MULTIPASS_PCT', 'JSON_ONLY' from dual union all
    select 'STORAGE_INDEX_SAVINGS_PCT', 'JSON_ONLY' from dual union all
    select 'TEMP_WRITE_LATENCY_MS', 'JSON_ONLY' from dual union all
    select 'WRITE_LATENCY_MS', 'JSON_ONLY' from dual
)
select
    fms.db_name,
    fms.snap_begin_time,
    fms.snap_end_time,
    tm.metric_name,
    tm.metric_class,
    fms.metric_category,
    fms.metric_value_num,
    fms.contributing_report_count,
    fms.awr_count,
    fms.distinct_value_count,
    fms.value_collapse_rule,
    fms.data_quality_flag
from target_metrics tm
join vw_awr_feature_metric_db_scope fms
  on fms.metric_name = tm.metric_name
where fms.db_name = '&DB_NAME'
  and fms.snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and fms.snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by tm.metric_class, tm.metric_name, fms.snap_begin_time;

prompt
prompt ============================================================
prompt 33. DB-scope duplicate check for newly promoted metrics only
prompt Expect zero rows
prompt ============================================================

with target_metrics as (
    select 'DB_CPU_PCT_DB_TIME' as metric_name from dual union all
    select 'REDO_GENERATION_PER_SEC' from dual union all
    select 'CELL_SINGLE_BLOCK_LATENCY_MS' from dual union all
    select 'HARD_PARSE_PCT' from dual union all
    select 'NETWORK_WAIT_PCT_DB_TIME' from dual union all
    select 'LOG_WRITE_LATENCY_MS' from dual union all
    select 'CURSOR_MUTEX_WAIT_PCT_DB_TIME' from dual union all
    select 'CELL_MULTIBLOCK_LATENCY_MS' from dual union all
    select 'PGA_CACHE_HIT_PCT' from dual union all
    select 'TEMP_SPILL_PCT' from dual union all
    select 'SORTS_DISK_PCT' from dual union all
    select 'WORKAREA_ONEPASS_PCT' from dual union all
    select 'WORKAREA_MULTIPASS_PCT' from dual union all
    select 'STORAGE_INDEX_SAVINGS_PCT' from dual union all
    select 'TEMP_WRITE_LATENCY_MS' from dual union all
    select 'WRITE_LATENCY_MS' from dual
)
select
    db_name,
    snap_begin_time,
    metric_name,
    count(*) as row_count
from vw_awr_feature_metric_db_scope
where db_name = '&DB_NAME'
  and metric_name in (select metric_name from target_metrics)
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
group by db_name, snap_begin_time, metric_name
having count(*) > 1
order by snap_begin_time, metric_name;

prompt
prompt ============================================================
prompt 34. Data quality flag distribution for newly promoted metrics
prompt ============================================================

with target_metrics as (
    select 'DB_CPU_PCT_DB_TIME' as metric_name, 'FACT_REQUIRED' as metric_class from dual union all
    select 'REDO_GENERATION_PER_SEC', 'FACT_REQUIRED' from dual union all
    select 'CELL_SINGLE_BLOCK_LATENCY_MS', 'FACT_REQUIRED' from dual union all
    select 'HARD_PARSE_PCT', 'CONDITIONAL' from dual union all
    select 'NETWORK_WAIT_PCT_DB_TIME', 'CONDITIONAL' from dual union all
    select 'LOG_WRITE_LATENCY_MS', 'CONDITIONAL' from dual union all
    select 'CURSOR_MUTEX_WAIT_PCT_DB_TIME', 'CONDITIONAL' from dual union all
    select 'CELL_MULTIBLOCK_LATENCY_MS', 'CONDITIONAL' from dual union all
    select 'PGA_CACHE_HIT_PCT', 'JSON_ONLY' from dual union all
    select 'TEMP_SPILL_PCT', 'JSON_ONLY' from dual union all
    select 'SORTS_DISK_PCT', 'JSON_ONLY' from dual union all
    select 'WORKAREA_ONEPASS_PCT', 'JSON_ONLY' from dual union all
    select 'WORKAREA_MULTIPASS_PCT', 'JSON_ONLY' from dual union all
    select 'STORAGE_INDEX_SAVINGS_PCT', 'JSON_ONLY' from dual union all
    select 'TEMP_WRITE_LATENCY_MS', 'JSON_ONLY' from dual union all
    select 'WRITE_LATENCY_MS', 'JSON_ONLY' from dual
)
select
    tm.metric_name,
    tm.metric_class,
    fms.data_quality_flag,
    count(*) as row_count
from target_metrics tm
join vw_awr_feature_metric_db_scope fms
  on fms.metric_name = tm.metric_name
where fms.db_name = '&DB_NAME'
  and fms.snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and fms.snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
group by tm.metric_name, tm.metric_class, fms.data_quality_flag
order by tm.metric_class, tm.metric_name, fms.data_quality_flag;

prompt
prompt ============================================================
prompt 35. Collapse rule distribution for newly promoted metrics
prompt ============================================================

with target_metrics as (
    select 'DB_CPU_PCT_DB_TIME' as metric_name, 'FACT_REQUIRED' as metric_class from dual union all
    select 'REDO_GENERATION_PER_SEC', 'FACT_REQUIRED' from dual union all
    select 'CELL_SINGLE_BLOCK_LATENCY_MS', 'FACT_REQUIRED' from dual union all
    select 'HARD_PARSE_PCT', 'CONDITIONAL' from dual union all
    select 'NETWORK_WAIT_PCT_DB_TIME', 'CONDITIONAL' from dual union all
    select 'LOG_WRITE_LATENCY_MS', 'CONDITIONAL' from dual union all
    select 'CURSOR_MUTEX_WAIT_PCT_DB_TIME', 'CONDITIONAL' from dual union all
    select 'CELL_MULTIBLOCK_LATENCY_MS', 'CONDITIONAL' from dual union all
    select 'PGA_CACHE_HIT_PCT', 'JSON_ONLY' from dual union all
    select 'TEMP_SPILL_PCT', 'JSON_ONLY' from dual union all
    select 'SORTS_DISK_PCT', 'JSON_ONLY' from dual union all
    select 'WORKAREA_ONEPASS_PCT', 'JSON_ONLY' from dual union all
    select 'WORKAREA_MULTIPASS_PCT', 'JSON_ONLY' from dual union all
    select 'STORAGE_INDEX_SAVINGS_PCT', 'JSON_ONLY' from dual union all
    select 'TEMP_WRITE_LATENCY_MS', 'JSON_ONLY' from dual union all
    select 'WRITE_LATENCY_MS', 'JSON_ONLY' from dual
)
select
    tm.metric_name,
    tm.metric_class,
    fms.value_collapse_rule,
    count(*) as row_count
from target_metrics tm
join vw_awr_feature_metric_db_scope fms
  on fms.metric_name = tm.metric_name
where fms.db_name = '&DB_NAME'
  and fms.snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and fms.snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
group by tm.metric_name, tm.metric_class, fms.value_collapse_rule
order by tm.metric_class, tm.metric_name, fms.value_collapse_rule;

prompt
prompt ============================================================
prompt 36. Row-count comparison for newly promoted metrics
prompt ============================================================

with target_metrics as (
    select 'DB_CPU_PCT_DB_TIME' as metric_name, 'FACT_REQUIRED' as metric_class from dual union all
    select 'REDO_GENERATION_PER_SEC', 'FACT_REQUIRED' from dual union all
    select 'CELL_SINGLE_BLOCK_LATENCY_MS', 'FACT_REQUIRED' from dual union all
    select 'HARD_PARSE_PCT', 'CONDITIONAL' from dual union all
    select 'NETWORK_WAIT_PCT_DB_TIME', 'CONDITIONAL' from dual union all
    select 'LOG_WRITE_LATENCY_MS', 'CONDITIONAL' from dual union all
    select 'CURSOR_MUTEX_WAIT_PCT_DB_TIME', 'CONDITIONAL' from dual union all
    select 'CELL_MULTIBLOCK_LATENCY_MS', 'CONDITIONAL' from dual union all
    select 'PGA_CACHE_HIT_PCT', 'JSON_ONLY' from dual union all
    select 'TEMP_SPILL_PCT', 'JSON_ONLY' from dual union all
    select 'SORTS_DISK_PCT', 'JSON_ONLY' from dual union all
    select 'WORKAREA_ONEPASS_PCT', 'JSON_ONLY' from dual union all
    select 'WORKAREA_MULTIPASS_PCT', 'JSON_ONLY' from dual union all
    select 'STORAGE_INDEX_SAVINGS_PCT', 'JSON_ONLY' from dual union all
    select 'TEMP_WRITE_LATENCY_MS', 'JSON_ONLY' from dual union all
    select 'WRITE_LATENCY_MS', 'JSON_ONLY' from dual
)
select
    scope_layer,
    metric_class,
    metric_name,
    row_count
from (
    select
        'VW_AWR_FEATURE_METRIC_SCOPE' as scope_layer,
        tm.metric_class,
        fms.metric_name,
        count(*) as row_count
    from target_metrics tm
    join vw_awr_feature_metric_scope fms
      on fms.metric_name = tm.metric_name
    where fms.db_name = '&DB_NAME'
      and fms.snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
      and fms.snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
    group by tm.metric_class, fms.metric_name

    union all

    select
        'VW_AWR_FEATURE_METRIC_DB_SCOPE' as scope_layer,
        tm.metric_class,
        fms.metric_name,
        count(*) as row_count
    from target_metrics tm
    join vw_awr_feature_metric_db_scope fms
      on fms.metric_name = tm.metric_name
    where fms.db_name = '&DB_NAME'
      and fms.snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
      and fms.snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
    group by tm.metric_class, fms.metric_name
)
order by metric_class, metric_name, scope_layer;

prompt
prompt ============================================================
prompt 37. Promoted engineered metric validation summary
prompt Note:
prompt - FACT_REQUIRED metrics should validate now
prompt - CONDITIONAL metrics depend on persisted source evidence
prompt - JSON_ONLY metrics are informational for this dataset
prompt ============================================================

with target_metrics as (
    select 'DB_CPU_PCT_DB_TIME' as metric_name, 'FACT_REQUIRED' as metric_class from dual union all
    select 'REDO_GENERATION_PER_SEC', 'FACT_REQUIRED' from dual union all
    select 'CELL_SINGLE_BLOCK_LATENCY_MS', 'FACT_REQUIRED' from dual union all
    select 'HARD_PARSE_PCT', 'CONDITIONAL' from dual union all
    select 'NETWORK_WAIT_PCT_DB_TIME', 'CONDITIONAL' from dual union all
    select 'LOG_WRITE_LATENCY_MS', 'CONDITIONAL' from dual union all
    select 'CURSOR_MUTEX_WAIT_PCT_DB_TIME', 'CONDITIONAL' from dual union all
    select 'CELL_MULTIBLOCK_LATENCY_MS', 'CONDITIONAL' from dual union all
    select 'PGA_CACHE_HIT_PCT', 'JSON_ONLY' from dual union all
    select 'TEMP_SPILL_PCT', 'JSON_ONLY' from dual union all
    select 'SORTS_DISK_PCT', 'JSON_ONLY' from dual union all
    select 'WORKAREA_ONEPASS_PCT', 'JSON_ONLY' from dual union all
    select 'WORKAREA_MULTIPASS_PCT', 'JSON_ONLY' from dual union all
    select 'STORAGE_INDEX_SAVINGS_PCT', 'JSON_ONLY' from dual union all
    select 'TEMP_WRITE_LATENCY_MS', 'JSON_ONLY' from dual union all
    select 'WRITE_LATENCY_MS', 'JSON_ONLY' from dual
),
metric_values as (
    select awr_id, 'WRITE_LATENCY_MS' as metric_name,
           json_value(feature_json, '$.WRITE_LATENCY_MS' returning number null on error) as metric_value_num
    from awr_feature_vector
    union all
    select awr_id, 'TEMP_WRITE_LATENCY_MS',
           json_value(feature_json, '$.TEMP_WRITE_LATENCY_MS' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'LOG_WRITE_LATENCY_MS',
           json_value(feature_json, '$.LOG_WRITE_LATENCY_MS' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'NETWORK_WAIT_PCT_DB_TIME',
           json_value(feature_json, '$.NETWORK_WAIT_PCT_DB_TIME' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'HARD_PARSE_PCT',
           json_value(feature_json, '$.HARD_PARSE_PCT' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'PGA_CACHE_HIT_PCT',
           json_value(feature_json, '$.PGA_CACHE_HIT_PCT' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'TEMP_SPILL_PCT',
           json_value(feature_json, '$.TEMP_SPILL_PCT' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'SORTS_DISK_PCT',
           json_value(feature_json, '$.SORTS_DISK_PCT' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'WORKAREA_ONEPASS_PCT',
           json_value(feature_json, '$.WORKAREA_ONEPASS_PCT' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'WORKAREA_MULTIPASS_PCT',
           json_value(feature_json, '$.WORKAREA_MULTIPASS_PCT' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'CURSOR_MUTEX_WAIT_PCT_DB_TIME',
           json_value(feature_json, '$.CURSOR_MUTEX_WAIT_PCT_DB_TIME' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'CELL_SINGLE_BLOCK_LATENCY_MS',
           json_value(feature_json, '$.CELL_SINGLE_BLOCK_LATENCY_MS' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'CELL_MULTIBLOCK_LATENCY_MS',
           json_value(feature_json, '$.CELL_MULTIBLOCK_LATENCY_MS' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'STORAGE_INDEX_SAVINGS_PCT',
           json_value(feature_json, '$.STORAGE_INDEX_SAVINGS_PCT' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'DB_CPU_PCT_DB_TIME',
           json_value(feature_json, '$.DB_CPU_PCT_DB_TIME' returning number null on error)
    from awr_feature_vector
    union all
    select awr_id, 'REDO_GENERATION_PER_SEC',
           json_value(feature_json, '$.REDO_GENERATION_PER_SEC' returning number null on error)
    from awr_feature_vector
),
json_presence as (
    select
        tm.metric_name,
        count(*) as json_key_rows
    from target_metrics tm
    join metric_values mv
      on mv.metric_name = tm.metric_name
    join awr_report r
      on r.awr_id = mv.awr_id
    where r.db_name = '&DB_NAME'
      and r.snap_time_begin >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
      and r.snap_time_end   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
      and mv.metric_value_num is not null
    group by tm.metric_name
),
report_presence as (
    select
        metric_name,
        count(*) as report_scope_rows
    from vw_awr_feature_metric_scope
    where db_name = '&DB_NAME'
      and metric_name in (select metric_name from target_metrics)
      and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
      and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
    group by metric_name
),
db_presence as (
    select
        metric_name,
        count(*) as db_scope_rows
    from vw_awr_feature_metric_db_scope
    where db_name = '&DB_NAME'
      and metric_name in (select metric_name from target_metrics)
      and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
      and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
    group by metric_name
)
select
    tm.metric_name,
    tm.metric_class,
    nvl(jp.json_key_rows, 0) as json_key_rows,
    nvl(rp.report_scope_rows, 0) as report_scope_rows,
    nvl(dp.db_scope_rows, 0) as db_scope_rows,
    case
        when tm.metric_class = 'FACT_REQUIRED' and nvl(dp.db_scope_rows,0) > 0
            then 'VALID'
        when tm.metric_class = 'FACT_REQUIRED' and nvl(dp.db_scope_rows,0) = 0
            then 'FAIL_MISSING_FACT'
        when tm.metric_class = 'CONDITIONAL' and nvl(dp.db_scope_rows,0) > 0
            then 'VALID_IF_PRESENT'
        when tm.metric_class = 'CONDITIONAL' and nvl(dp.db_scope_rows,0) = 0
            then 'OPTIONAL_NO_SOURCE_EVIDENCE'
        when tm.metric_class = 'JSON_ONLY' and nvl(jp.json_key_rows,0) > 0
            then 'INFORMATIONAL_PRESENT'
        else 'INFORMATIONAL_NOT_PRESENT'
    end as validation_status
from target_metrics tm
left join json_presence jp
  on jp.metric_name = tm.metric_name
left join report_presence rp
  on rp.metric_name = tm.metric_name
left join db_presence dp
  on dp.metric_name = tm.metric_name
order by
    case tm.metric_class
        when 'FACT_REQUIRED' then 1
        when 'CONDITIONAL' then 2
        else 3
    end,
    tm.metric_name;

spool off
