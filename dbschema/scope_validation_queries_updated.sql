set pagesize 200
set linesize 220
set verify off
set feedback on
set serveroutput on
set define on

define DB_NAME='FINDB'
define HOST_NAME='exa-rac-node01'
define INSTANCE_NAME='FINDB1'
define START_TIME='2026-03-29 00:00:00'
define END_TIME='2026-03-29 23:59:59'

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
  'VW_AWR_SCORE_SCOPE'
)
order by view_name;

prompt ============================================================
prompt 2. Discover available metric names for the selected DB/timeframe
prompt ============================================================

select distinct metric_name
from vw_awr_metric_scope
where db_name = '&DB_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by metric_name;

prompt ============================================================
prompt 3. Database-wide metric history
prompt Replace metric_name below with one returned by step 2 if needed
prompt ============================================================

select
    db_name,
    host_name,
    instance_name,
    snap_begin_time,
    snap_end_time,
    metric_name,
    metric_value_num
from vw_awr_metric_scope
where db_name = '&DB_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
  and metric_name = 'DB_CPU_PCT'
order by snap_begin_time;

prompt ============================================================
prompt 4. Host-specific metric history
prompt ============================================================

select
    db_name,
    host_name,
    instance_name,
    snap_begin_time,
    metric_name,
    metric_value_num
from vw_awr_metric_scope
where db_name = '&DB_NAME'
  and host_name = '&HOST_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
  and metric_name = 'DB_CPU_PCT'
order by snap_begin_time;

prompt ============================================================
prompt 5. Instance-specific metric history
prompt ============================================================

select
    db_name,
    instance_name,
    instance_number,
    snap_begin_time,
    metric_name,
    metric_value_num
from vw_awr_metric_scope
where db_name = '&DB_NAME'
  and instance_name = '&INSTANCE_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
  and metric_name = 'DB_CPU_PCT'
order by snap_begin_time;

prompt ============================================================
prompt 6. Host-specific wait history
prompt ============================================================

select
    host_name,
    snap_begin_time,
    event_name,
    wait_class,
    pct_db_time
from vw_awr_wait_scope
where db_name = '&DB_NAME'
  and host_name = '&HOST_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by snap_begin_time, pct_db_time desc;

prompt ============================================================
prompt 7. Instance-specific SQL history
prompt ============================================================

select
    db_name,
    instance_name,
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

prompt ============================================================
prompt 8. Feature history by scope
prompt ============================================================

select
    db_name,
    host_name,
    instance_name,
    snap_begin_time,
    workload_class,
    feature_topology_class,
    feature_platform_class,
    feature_event_class
from vw_awr_feature_scope
where db_name = '&DB_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by snap_begin_time;

prompt ============================================================
prompt 9. Score history by scope
prompt ============================================================

select
    db_name,
    host_name,
    instance_name,
    snap_begin_time,
    workload_class,
    primary_signal_domain,
    total_score,
    confidence_score
from vw_awr_score_scope
where db_name = '&DB_NAME'
  and snap_begin_time >= to_timestamp('&START_TIME','YYYY-MM-DD HH24:MI:SS')
  and snap_end_time   <= to_timestamp('&END_TIME','YYYY-MM-DD HH24:MI:SS')
order by snap_begin_time;
