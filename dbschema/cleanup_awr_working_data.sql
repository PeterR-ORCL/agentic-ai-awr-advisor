--------------------------------------------------------------------------------
-- AWR SIZING ADVISOR
-- CLEANUP WORKING DATA TABLES
--
-- Purpose:
--   Remove previously ingested AWR working data so the dataset can be reloaded
--   cleanly with duplicate guardrails enabled.
--
-- Preserved tables:
--   AWR_SOURCE_SYSTEM
--   AWR_SCORING_MODEL
--   AWR_SCORING_WEIGHT
--   AWR_MODEL_RUN   (preserved by default)
--
-- Removed working data:
--   AWR_ACTION
--   AWR_OUTCOME
--   AWR_RECOMMENDATION
--   AWR_SCORE_RESULT
--   AWR_FEATURE_VECTOR
--   AWR_WAIT_EVENT_FACT
--   AWR_TOP_SQL_FACT
--   AWR_METRIC_FACT
--   AWR_SECTION_DOC
--   AWR_REPORT
--   AWR_INGEST_RUN
--
-- IMPORTANT:
--   Review preserved tables before running.
--   If you also want to clear AWR_MODEL_RUN, uncomment that section.
--------------------------------------------------------------------------------

spool cleanup.log
set echo on
set feedback on
set pagesize 200
set linesize 220
set verify off

prompt ============================================================
prompt PRE-CLEANUP ROW COUNTS
prompt ============================================================

select 'AWR_ACTION'           as table_name, count(*) as row_count from AWR_ACTION
union all
select 'AWR_OUTCOME'          as table_name, count(*) as row_count from AWR_OUTCOME
union all
select 'AWR_RECOMMENDATION'   as table_name, count(*) as row_count from AWR_RECOMMENDATION
union all
select 'AWR_SCORE_RESULT'     as table_name, count(*) as row_count from AWR_SCORE_RESULT
union all
select 'AWR_FEATURE_VECTOR'   as table_name, count(*) as row_count from AWR_FEATURE_VECTOR
union all
select 'AWR_WAIT_EVENT_FACT'  as table_name, count(*) as row_count from AWR_WAIT_EVENT_FACT
union all
select 'AWR_TOP_SQL_FACT'     as table_name, count(*) as row_count from AWR_TOP_SQL_FACT
union all
select 'AWR_METRIC_FACT'      as table_name, count(*) as row_count from AWR_METRIC_FACT
union all
select 'AWR_SECTION_DOC'      as table_name, count(*) as row_count from AWR_SECTION_DOC
union all
select 'AWR_REPORT'           as table_name, count(*) as row_count from AWR_REPORT
union all
select 'AWR_INGEST_RUN'       as table_name, count(*) as row_count from AWR_INGEST_RUN
union all
select 'AWR_SOURCE_SYSTEM'    as table_name, count(*) as row_count from AWR_SOURCE_SYSTEM
union all
select 'AWR_SCORING_MODEL'    as table_name, count(*) as row_count from AWR_SCORING_MODEL
union all
select 'AWR_SCORING_WEIGHT'   as table_name, count(*) as row_count from AWR_SCORING_WEIGHT
union all
select 'AWR_MODEL_RUN'        as table_name, count(*) as row_count from AWR_MODEL_RUN
order by 1;

prompt
prompt ============================================================
prompt DUPLICATE REPORT CHECK BEFORE CLEANUP
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
from AWR_REPORT
group by
    source_system_id,
    dbid,
    instance_number,
    snap_id_begin,
    snap_id_end,
    snap_time_begin,
    snap_time_end
having count(*) > 1
order by snap_time_begin, source_system_id, dbid, instance_number;

prompt
prompt ============================================================
prompt EXACT FILE HASH DUPLICATE CHECK BEFORE CLEANUP
prompt ============================================================

select
    source_system_id,
    file_hash_sha256,
    count(*) as row_count
from AWR_REPORT
group by source_system_id, file_hash_sha256
having count(*) > 1
order by row_count desc, source_system_id, file_hash_sha256;

prompt
prompt ============================================================
prompt STARTING CLEANUP
prompt ============================================================

--------------------------------------------------------------------------------
-- Delete in dependency order (children first)
--------------------------------------------------------------------------------

delete from AWR_ACTION;
prompt Deleted AWR_ACTION

delete from AWR_OUTCOME;
prompt Deleted AWR_OUTCOME

delete from AWR_RECOMMENDATION;
prompt Deleted AWR_RECOMMENDATION

delete from AWR_SCORE_RESULT;
prompt Deleted AWR_SCORE_RESULT

delete from AWR_FEATURE_VECTOR;
prompt Deleted AWR_FEATURE_VECTOR

delete from AWR_WAIT_EVENT_FACT;
prompt Deleted AWR_WAIT_EVENT_FACT

delete from AWR_TOP_SQL_FACT;
prompt Deleted AWR_TOP_SQL_FACT

delete from AWR_METRIC_FACT;
prompt Deleted AWR_METRIC_FACT

delete from AWR_SECTION_DOC;
prompt Deleted AWR_SECTION_DOC

delete from AWR_REPORT;
prompt Deleted AWR_REPORT

delete from AWR_INGEST_RUN;
prompt Deleted AWR_INGEST_RUN

--------------------------------------------------------------------------------
-- OPTIONAL: clear model runs if desired
-- Uncomment only if you want a fully clean analytical history
--------------------------------------------------------------------------------
-- delete from AWR_MODEL_RUN;
-- prompt Deleted AWR_MODEL_RUN

commit;

prompt
prompt ============================================================
prompt POST-CLEANUP ROW COUNTS
prompt ============================================================

select 'AWR_ACTION'           as table_name, count(*) as row_count from AWR_ACTION
union all
select 'AWR_OUTCOME'          as table_name, count(*) as row_count from AWR_OUTCOME
union all
select 'AWR_RECOMMENDATION'   as table_name, count(*) as row_count from AWR_RECOMMENDATION
union all
select 'AWR_SCORE_RESULT'     as table_name, count(*) as row_count from AWR_SCORE_RESULT
union all
select 'AWR_FEATURE_VECTOR'   as table_name, count(*) as row_count from AWR_FEATURE_VECTOR
union all
select 'AWR_WAIT_EVENT_FACT'  as table_name, count(*) as row_count from AWR_WAIT_EVENT_FACT
union all
select 'AWR_TOP_SQL_FACT'     as table_name, count(*) as row_count from AWR_TOP_SQL_FACT
union all
select 'AWR_METRIC_FACT'      as table_name, count(*) as row_count from AWR_METRIC_FACT
union all
select 'AWR_SECTION_DOC'      as table_name, count(*) as row_count from AWR_SECTION_DOC
union all
select 'AWR_REPORT'           as table_name, count(*) as row_count from AWR_REPORT
union all
select 'AWR_INGEST_RUN'       as table_name, count(*) as row_count from AWR_INGEST_RUN
union all
select 'AWR_SOURCE_SYSTEM'    as table_name, count(*) as row_count from AWR_SOURCE_SYSTEM
union all
select 'AWR_SCORING_MODEL'    as table_name, count(*) as row_count from AWR_SCORING_MODEL
union all
select 'AWR_SCORING_WEIGHT'   as table_name, count(*) as row_count from AWR_SCORING_WEIGHT
union all
select 'AWR_MODEL_RUN'        as table_name, count(*) as row_count from AWR_MODEL_RUN
order by 1;

prompt
prompt ============================================================
prompt CLEANUP COMPLETE
prompt Next steps:
prompt 1. Reload AWR reports once
prompt 2. Validate duplicate guardrail
prompt 3. Re-run scoped validation
prompt ============================================================

spool off
