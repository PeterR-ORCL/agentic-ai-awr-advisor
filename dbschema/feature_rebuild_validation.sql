--------------------------------------------------------------------------------
-- AWR SIZING ADVISOR
-- FEATURE REBUILD VALIDATION
--
-- SQLcl-safe smoke test for REBUILD_FEATURE_VECTORS maintenance runs.
-- Purpose:
--   - confirm no duplicate AWR_REPORT rows were introduced
--   - confirm rebuilt FEATURE_JSON contains non-null promoted metric values
--   - confirm promoted metrics are exposed through report scope and DB scope
--   - confirm latest score rows exist after rebuild
--
-- Notes:
--   - this is a focused rebuild validation script, not the full scoped-history
--     validation harness
--   - "presence" below means non-null numeric metric values, not merely key names
--------------------------------------------------------------------------------

set pagesize 200
set linesize 220
set verify off
set feedback on

define DB_NAME='FINDB'
define DBID='1234567890'
define SAMPLE_LIMIT='20'
define START_TIME='2026-03-29 00:00:00'
define END_TIME='2026-03-29 23:59:59'

spool feature_rebuild_validation.log

prompt 1. Duplicate AWR_REPORT logical identity check (must remain zero new duplicates)

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
order by snap_time_begin, dbid, instance_number;

prompt
prompt 2. FEATURE_JSON non-null promoted metric value presence after rebuild

with promoted_metrics as (
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
    select fv.awr_id, 'WRITE_LATENCY_MS' as metric_name,
           json_value(fv.feature_json, '$.WRITE_LATENCY_MS' returning number null on error) as metric_value_num
    from awr_feature_vector fv
    union all
    select fv.awr_id, 'TEMP_WRITE_LATENCY_MS',
           json_value(fv.feature_json, '$.TEMP_WRITE_LATENCY_MS' returning number null on error)
    from awr_feature_vector fv
    union all
    select fv.awr_id, 'LOG_WRITE_LATENCY_MS',
           json_value(fv.feature_json, '$.LOG_WRITE_LATENCY_MS' returning number null on error)
    from awr_feature_vector fv
    union all
    select fv.awr_id, 'NETWORK_WAIT_PCT_DB_TIME',
           json_value(fv.feature_json, '$.NETWORK_WAIT_PCT_DB_TIME' returning number null on error)
    from awr_feature_vector fv
    union all
    select fv.awr_id, 'HARD_PARSE_PCT',
           json_value(fv.feature_json, '$.HARD_PARSE_PCT' returning number null on error)
    from awr_feature_vector fv
    union all
    select fv.awr_id, 'PGA_CACHE_HIT_PCT',
           json_value(fv.feature_json, '$.PGA_CACHE_HIT_PCT' returning number null on error)
    from awr_feature_vector fv
    union all
    select fv.awr_id, 'TEMP_SPILL_PCT',
           json_value(fv.feature_json, '$.TEMP_SPILL_PCT' returning number null on error)
    from awr_feature_vector fv
    union all
    select fv.awr_id, 'SORTS_DISK_PCT',
           json_value(fv.feature_json, '$.SORTS_DISK_PCT' returning number null on error)
    from awr_feature_vector fv
    union all
    select fv.awr_id, 'WORKAREA_ONEPASS_PCT',
           json_value(fv.feature_json, '$.WORKAREA_ONEPASS_PCT' returning number null on error)
    from awr_feature_vector fv
    union all
    select fv.awr_id, 'WORKAREA_MULTIPASS_PCT',
           json_value(fv.feature_json, '$.WORKAREA_MULTIPASS_PCT' returning number null on error)
    from awr_feature_vector fv
    union all
    select fv.awr_id, 'CURSOR_MUTEX_WAIT_PCT_DB_TIME',
           json_value(fv.feature_json, '$.CURSOR_MUTEX_WAIT_PCT_DB_TIME' returning number null on error)
    from awr_feature_vector fv
    union all
    select fv.awr_id, 'CELL_SINGLE_BLOCK_LATENCY_MS',
           json_value(fv.feature_json, '$.CELL_SINGLE_BLOCK_LATENCY_MS' returning number null on error)
    from awr_feature_vector fv
    union all
    select fv.awr_id, 'CELL_MULTIBLOCK_LATENCY_MS',
           json_value(fv.feature_json, '$.CELL_MULTIBLOCK_LATENCY_MS' returning number null on error)
    from awr_feature_vector fv
    union all
    select fv.awr_id, 'STORAGE_INDEX_SAVINGS_PCT',
           json_value(fv.feature_json, '$.STORAGE_INDEX_SAVINGS_PCT' returning number null on error)
    from awr_feature_vector fv
    union all
    select fv.awr_id, 'DB_CPU_PCT_DB_TIME',
           json_value(fv.feature_json, '$.DB_CPU_PCT_DB_TIME' returning number null on error)
    from awr_feature_vector fv
    union all
    select fv.awr_id, 'REDO_GENERATION_PER_SEC',
           json_value(fv.feature_json, '$.REDO_GENERATION_PER_SEC' returning number null on error)
    from awr_feature_vector fv
)
select
    pm.metric_name,
    pm.metric_class,
    count(*) as feature_vector_rows_with_nonnull_value
from promoted_metrics pm
join metric_values mv
  on mv.metric_name = pm.metric_name
join awr_report r
  on r.awr_id = mv.awr_id
where r.db_name = '&DB_NAME'
  and r.dbid = &DBID
  and r.snap_time_begin >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and r.snap_time_end   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
  and mv.metric_value_num is not null
group by pm.metric_name, pm.metric_class
order by
    case pm.metric_class
        when 'FACT_REQUIRED' then 1
        when 'CONDITIONAL' then 2
        else 3
    end,
    pm.metric_name;

prompt
prompt 3. Sample rebuilt feature vectors

select *
from (
    select
        fv.feature_vector_id,
        fv.awr_id,
        r.db_name,
        r.dbid,
        r.instance_name,
        r.snap_time_begin,
        r.snap_time_end,
        json_serialize(fv.feature_json returning clob pretty) as feature_json_pretty
    from awr_feature_vector fv
    join awr_report r
      on r.awr_id = fv.awr_id
     and r.source_system_id = fv.source_system_id
    where r.db_name = '&DB_NAME'
      and r.dbid = &DBID
    order by r.snap_time_begin, fv.feature_vector_id
)
where rownum <= &SAMPLE_LIMIT;

prompt
prompt 4. Report-scope engineered metric exposure for promoted metrics

with promoted_metrics as (
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
    pm.metric_name,
    pm.metric_class,
    count(*) as row_count
from promoted_metrics pm
join vw_awr_feature_metric_scope v
  on v.metric_name = pm.metric_name
where v.db_name = '&DB_NAME'
  and v.dbid = &DBID
  and v.snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and v.snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
group by pm.metric_name, pm.metric_class
order by
    case pm.metric_class
        when 'FACT_REQUIRED' then 1
        when 'CONDITIONAL' then 2
        else 3
    end,
    pm.metric_name;

prompt
prompt 5. DB-scope engineered metric exposure for promoted metrics

with promoted_metrics as (
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
    pm.metric_name,
    pm.metric_class,
    count(*) as row_count,
    min(v.data_quality_flag) as min_quality_flag,
    min(v.value_collapse_rule) as min_collapse_rule
from promoted_metrics pm
join vw_awr_feature_metric_db_scope v
  on v.metric_name = pm.metric_name
where v.db_name = '&DB_NAME'
  and v.dbid = &DBID
  and v.snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and v.snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
group by pm.metric_name, pm.metric_class
order by
    case pm.metric_class
        when 'FACT_REQUIRED' then 1
        when 'CONDITIONAL' then 2
        else 3
    end,
    pm.metric_name;

prompt
prompt 6. Latest score results after feature rebuild

select
    awr_id,
    score_result_id,
    feature_vector_id,
    scored_at,
    total_score,
    confidence_score,
    risk_level
from vw_awr_score_scope
where db_name = '&DB_NAME'
  and dbid = &DBID
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by snap_begin_time, awr_id;

spool off
