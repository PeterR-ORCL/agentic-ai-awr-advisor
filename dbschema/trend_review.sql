select metric_name, anomaly_type, count(*) as row_count
from awr_db_metric_trend
where metric_name in (
  'FAILOVER_EVENT_FLAG',
  'ROLE_TRANSITION_FLAG',
  'INTERCONNECT_STRESS_FLAG',
  'POST_FAILOVER_RECOVERY_FLAG',
  'REDO_TRANSPORT_ISSUE_FLAG',
  'RAC_CONTENTION_FLAG',
  'SMART_SCAN_FLAG',
  'EXADATA_IO_BENEFIT_FLAG',
  'FLASH_CACHE_HIT_FLAG'
)
group by metric_name, anomaly_type
order by metric_name, anomaly_type;

select metric_name, snap_begin_time, metric_value_num, anomaly_type, anomaly_score
from awr_db_metric_trend
where metric_name = 'CELL_SINGLE_BLOCK_LATENCY_MS'
order by snap_begin_time;

select metric_name, anomaly_type, count(*) as row_count
from awr_db_metric_trend
where metric_name in (
  'DB_CPU_PCT_DB_TIME',
  'REDO_GENERATION_PER_SEC',
  'CELL_SINGLE_BLOCK_LATENCY_MS'
)
group by metric_name, anomaly_type
order by metric_name, anomaly_type;

select
    metric_name,
    snap_begin_time,
    metric_value_num,
    anomaly_type,
    anomaly_score
from awr_db_metric_trend
where metric_name in (
    'FAILOVER_EVENT_FLAG',
    'ROLE_TRANSITION_FLAG',
    'INTERCONNECT_STRESS_FLAG',
    'POST_FAILOVER_RECOVERY_FLAG',
    'REDO_TRANSPORT_ISSUE_FLAG'
)
order by metric_name, snap_begin_time;

select
    metric_name,
    snap_begin_time,
    metric_value_num,
    anomaly_type,
    anomaly_score
from awr_db_metric_trend
where metric_name = 'CELL_SINGLE_BLOCK_LATENCY_MS'
order by snap_begin_time;
