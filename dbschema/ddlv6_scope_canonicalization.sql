--------------------------------------------------------------------------------
-- AWR SIZING ADVISOR
-- DDlv6: CANONICAL REPORT-LEVEL SCOPE DEDUPLICATION
--
-- ddlv5 deduped FEATURE_VECTOR rows per AWR_ID, but duplicate logical
-- AWR_REPORT rows still survived upstream. Those duplicate AWR_IDs then
-- propagated into scope, feature, score, and engineered metric views.
--
-- ddlv6 fixes that by:
--   1. Choosing one canonical AWR_REPORT row per logical snapshot scope.
--   2. Choosing the latest feature / score row only for that winning report.
--   3. Preserving honest DB-scoped semantics for engineered feature metrics.
--
-- Canonical logical snapshot identity:
--   Preferred:
--     SOURCE_SYSTEM_ID + DBID + INSTANCE_NUMBER
--     + SNAP_ID_BEGIN + SNAP_ID_END
--     + SNAP_TIME_BEGIN + SNAP_TIME_END
--
--   Fallback when the logical snapshot identity is incomplete:
--     SOURCE_SYSTEM_ID + FILE_HASH_SHA256
--
-- Deterministic winner:
--   latest CREATED_AT, then highest AWR_ID
--------------------------------------------------------------------------------
spool ddlv6_scope_canonicalization.log

CREATE OR REPLACE VIEW VW_AWR_SCOPE_CONTEXT AS
WITH report_scope_candidates AS (
    SELECT
        r.*,
        COALESCE(
            r.DBID,
            JSON_VALUE(
                r.RAW_METADATA_JSON,
                '$.dbid' RETURNING NUMBER NULL ON ERROR
            )
        ) AS RESOLVED_DBID,
        COALESCE(
            r.INSTANCE_NUMBER,
            JSON_VALUE(
                r.RAW_METADATA_JSON,
                '$.instance_number' RETURNING NUMBER NULL ON ERROR
            )
        ) AS RESOLVED_INSTANCE_NUMBER,
        CASE
            WHEN COALESCE(
                r.DBID,
                JSON_VALUE(
                    r.RAW_METADATA_JSON,
                    '$.dbid' RETURNING NUMBER NULL ON ERROR
                )
            ) IS NOT NULL
             AND COALESCE(
                r.INSTANCE_NUMBER,
                JSON_VALUE(
                    r.RAW_METADATA_JSON,
                    '$.instance_number' RETURNING NUMBER NULL ON ERROR
                )
            ) IS NOT NULL
             AND r.SNAP_ID_BEGIN IS NOT NULL
             AND r.SNAP_ID_END IS NOT NULL
             AND r.SNAP_TIME_BEGIN IS NOT NULL
             AND r.SNAP_TIME_END IS NOT NULL
            THEN 1
            ELSE 0
        END AS HAS_LOGICAL_SNAPSHOT_ID
    FROM AWR_REPORT r
),
canonical_report_per_scope AS (
    SELECT
        c.*,
        ROW_NUMBER() OVER (
            PARTITION BY
                c.SOURCE_SYSTEM_ID,
                CASE
                    WHEN c.HAS_LOGICAL_SNAPSHOT_ID = 1
                    THEN 'LOGICAL_SNAPSHOT'
                    ELSE 'FILE_HASH'
                END,
                CASE
                    WHEN c.HAS_LOGICAL_SNAPSHOT_ID = 1
                    THEN c.RESOLVED_DBID
                END,
                CASE
                    WHEN c.HAS_LOGICAL_SNAPSHOT_ID = 1
                    THEN c.RESOLVED_INSTANCE_NUMBER
                END,
                CASE
                    WHEN c.HAS_LOGICAL_SNAPSHOT_ID = 1
                    THEN c.SNAP_ID_BEGIN
                END,
                CASE
                    WHEN c.HAS_LOGICAL_SNAPSHOT_ID = 1
                    THEN c.SNAP_ID_END
                END,
                CASE
                    WHEN c.HAS_LOGICAL_SNAPSHOT_ID = 1
                    THEN c.SNAP_TIME_BEGIN
                END,
                CASE
                    WHEN c.HAS_LOGICAL_SNAPSHOT_ID = 1
                    THEN c.SNAP_TIME_END
                END,
                CASE
                    WHEN c.HAS_LOGICAL_SNAPSHOT_ID = 0
                    THEN c.FILE_HASH_SHA256
                END
            ORDER BY c.CREATED_AT DESC, c.AWR_ID DESC
        ) AS RN
    FROM report_scope_candidates c
),
canonical_report_set AS (
    SELECT *
    FROM canonical_report_per_scope
    WHERE RN = 1
),
latest_feature_per_awr AS (
    SELECT
        fv.AWR_ID,
        fv.SOURCE_SYSTEM_ID,
        fv.FEATURE_VECTOR_ID,
        fv.OBSERVED_AT,
        fv.TOPOLOGY_CLASS,
        fv.PLATFORM_CLASS,
        fv.EVENT_CLASS,
        ROW_NUMBER() OVER (
            PARTITION BY fv.AWR_ID, fv.SOURCE_SYSTEM_ID
            ORDER BY fv.OBSERVED_AT DESC, fv.FEATURE_VECTOR_ID DESC
        ) AS RN
    FROM AWR_FEATURE_VECTOR fv
    JOIN canonical_report_set cr
      ON cr.AWR_ID = fv.AWR_ID
     AND cr.SOURCE_SYSTEM_ID = fv.SOURCE_SYSTEM_ID
),
latest_score_per_awr AS (
    SELECT
        sr.AWR_ID,
        sr.SOURCE_SYSTEM_ID,
        sr.SCORE_RESULT_ID,
        sr.SCORED_AT,
        sr.TOPOLOGY_CLASS,
        sr.PLATFORM_CLASS,
        sr.EVENT_CLASS,
        ROW_NUMBER() OVER (
            PARTITION BY sr.AWR_ID, sr.SOURCE_SYSTEM_ID
            ORDER BY sr.SCORED_AT DESC, sr.SCORE_RESULT_ID DESC
        ) AS RN
    FROM AWR_SCORE_RESULT sr
    JOIN canonical_report_set cr
      ON cr.AWR_ID = sr.AWR_ID
     AND cr.SOURCE_SYSTEM_ID = sr.SOURCE_SYSTEM_ID
)
SELECT
    r.AWR_ID,
    r.SOURCE_SYSTEM_ID,
    s.SOURCE_SYSTEM_CODE,
    COALESCE(r.DB_NAME, s.DB_NAME, s.DB_UNIQUE_NAME) AS DB_NAME,
    COALESCE(r.RESOLVED_DBID, s.DBID) AS DBID,
    COALESCE(
        r.HOST_NAME,
        s.PRIMARY_HOST_NAME,
        JSON_VALUE(
            r.RAW_METADATA_JSON,
            '$.host_name' RETURNING VARCHAR2(256) NULL ON ERROR
        )
    ) AS HOST_NAME,
    COALESCE(
        r.INSTANCE_NAME,
        JSON_VALUE(
            r.RAW_METADATA_JSON,
            '$.instance_name' RETURNING VARCHAR2(128) NULL ON ERROR
        )
    ) AS INSTANCE_NAME,
    r.RESOLVED_INSTANCE_NUMBER AS INSTANCE_NUMBER,
    r.SNAP_TIME_BEGIN AS SNAP_BEGIN_TIME,
    r.SNAP_TIME_END AS SNAP_END_TIME,
    COALESCE(
        r.DB_VERSION,
        s.DB_VERSION,
        JSON_VALUE(
            r.RAW_METADATA_JSON,
            '$.db_version' RETURNING VARCHAR2(64) NULL ON ERROR
        )
    ) AS DB_VERSION,
    COALESCE(
        s.DATABASE_ROLE,
        JSON_VALUE(
            r.PARSER_OUTPUT_JSON,
            '$.topology_signals.database_role' RETURNING VARCHAR2(64)
            NULL ON ERROR
        ),
        JSON_VALUE(
            s.TAGS_JSON,
            '$.database_role' RETURNING VARCHAR2(64) NULL ON ERROR
        )
    ) AS DATABASE_ROLE,
    COALESCE(
        s.INSTANCE_COUNT,
        JSON_VALUE(
            r.PARSER_OUTPUT_JSON,
            '$.topology_signals.instance_count' RETURNING NUMBER NULL ON ERROR
        ),
        JSON_VALUE(
            s.TAGS_JSON,
            '$.instance_count' RETURNING NUMBER NULL ON ERROR
        )
    ) AS INSTANCE_COUNT,
    COALESCE(
        r.PLATFORM_NAME,
        s.PLATFORM_NAME,
        JSON_VALUE(
            r.RAW_METADATA_JSON,
            '$.platform' RETURNING VARCHAR2(256) NULL ON ERROR
        )
    ) AS PLATFORM,
    COALESCE(
        fv.TOPOLOGY_CLASS,
        ls.TOPOLOGY_CLASS,
        JSON_VALUE(
            r.PARSER_OUTPUT_JSON,
            '$.topology_signals.topology_class' RETURNING VARCHAR2(64)
            NULL ON ERROR
        ),
        JSON_VALUE(
            s.TAGS_JSON,
            '$.topology_class' RETURNING VARCHAR2(64) NULL ON ERROR
        )
    ) AS TOPOLOGY_CLASS,
    COALESCE(
        fv.PLATFORM_CLASS,
        ls.PLATFORM_CLASS,
        JSON_VALUE(
            r.PARSER_OUTPUT_JSON,
            '$.topology_signals.platform_class' RETURNING VARCHAR2(64)
            NULL ON ERROR
        ),
        JSON_VALUE(
            s.TAGS_JSON,
            '$.platform_class' RETURNING VARCHAR2(64) NULL ON ERROR
        )
    ) AS PLATFORM_CLASS
FROM canonical_report_set r
JOIN AWR_SOURCE_SYSTEM s
  ON s.SOURCE_SYSTEM_ID = r.SOURCE_SYSTEM_ID
LEFT JOIN latest_feature_per_awr fv
  ON fv.AWR_ID = r.AWR_ID
 AND fv.SOURCE_SYSTEM_ID = r.SOURCE_SYSTEM_ID
 AND fv.RN = 1
LEFT JOIN latest_score_per_awr ls
  ON ls.AWR_ID = r.AWR_ID
 AND ls.SOURCE_SYSTEM_ID = r.SOURCE_SYSTEM_ID
 AND ls.RN = 1;


CREATE OR REPLACE VIEW VW_AWR_FEATURE_SCOPE AS
WITH canonical_awr AS (
    SELECT AWR_ID, SOURCE_SYSTEM_ID
    FROM VW_AWR_SCOPE_CONTEXT
),
latest_feature_per_awr AS (
    SELECT
        fv.*,
        ROW_NUMBER() OVER (
            PARTITION BY fv.AWR_ID, fv.SOURCE_SYSTEM_ID
            ORDER BY fv.OBSERVED_AT DESC, fv.FEATURE_VECTOR_ID DESC
        ) AS RN
    FROM AWR_FEATURE_VECTOR fv
    JOIN canonical_awr ca
      ON ca.AWR_ID = fv.AWR_ID
     AND ca.SOURCE_SYSTEM_ID = fv.SOURCE_SYSTEM_ID
)
SELECT
    sc.AWR_ID,
    sc.SOURCE_SYSTEM_ID,
    sc.SOURCE_SYSTEM_CODE,
    sc.DB_NAME,
    sc.DBID,
    sc.HOST_NAME,
    sc.INSTANCE_NAME,
    sc.INSTANCE_NUMBER,
    sc.SNAP_BEGIN_TIME,
    sc.SNAP_END_TIME,
    sc.DB_VERSION,
    sc.DATABASE_ROLE,
    sc.INSTANCE_COUNT,
    sc.PLATFORM,
    sc.TOPOLOGY_CLASS,
    sc.PLATFORM_CLASS,
    fv.FEATURE_VECTOR_ID,
    fv.OBSERVED_AT,
    fv.VECTOR_VERSION,
    fv.FEATURE_SET_NAME,
    fv.FEATURE_SET_VERSION,
    fv.WORKLOAD_CLASS,
    fv.TOPOLOGY_CLASS AS FEATURE_TOPOLOGY_CLASS,
    fv.PLATFORM_CLASS AS FEATURE_PLATFORM_CLASS,
    fv.EVENT_CLASS AS FEATURE_EVENT_CLASS,
    fv.VECTOR_STATUS,
    fv.FEATURE_VECTOR,
    fv.NARRATIVE_EMBEDDING,
    fv.FEATURE_JSON,
    fv.NORMALIZATION_JSON,
    fv.EXPLANATION_JSON,
    fv.SOURCE_LINEAGE_JSON,
    fv.CREATED_AT
FROM latest_feature_per_awr fv
JOIN VW_AWR_SCOPE_CONTEXT sc
  ON sc.AWR_ID = fv.AWR_ID
 AND sc.SOURCE_SYSTEM_ID = fv.SOURCE_SYSTEM_ID
WHERE fv.RN = 1;


CREATE OR REPLACE VIEW VW_AWR_SCORE_SCOPE AS
WITH canonical_awr AS (
    SELECT AWR_ID, SOURCE_SYSTEM_ID
    FROM VW_AWR_SCOPE_CONTEXT
),
latest_score_per_awr AS (
    SELECT
        sr.*,
        ROW_NUMBER() OVER (
            PARTITION BY sr.AWR_ID, sr.SOURCE_SYSTEM_ID
            ORDER BY sr.SCORED_AT DESC, sr.SCORE_RESULT_ID DESC
        ) AS RN
    FROM AWR_SCORE_RESULT sr
    JOIN canonical_awr ca
      ON ca.AWR_ID = sr.AWR_ID
     AND ca.SOURCE_SYSTEM_ID = sr.SOURCE_SYSTEM_ID
)
SELECT
    sc.AWR_ID,
    sc.SOURCE_SYSTEM_ID,
    sc.SOURCE_SYSTEM_CODE,
    sc.DB_NAME,
    sc.DBID,
    sc.HOST_NAME,
    sc.INSTANCE_NAME,
    sc.INSTANCE_NUMBER,
    sc.SNAP_BEGIN_TIME,
    sc.SNAP_END_TIME,
    sc.DB_VERSION,
    sc.DATABASE_ROLE,
    sc.INSTANCE_COUNT,
    sc.PLATFORM,
    sc.TOPOLOGY_CLASS,
    sc.PLATFORM_CLASS,
    sr.SCORE_RESULT_ID,
    sr.FEATURE_VECTOR_ID,
    sr.SCORING_MODEL_ID,
    sm.MODEL_CODE,
    sm.MODEL_NAME,
    sm.MODEL_VERSION,
    sr.SCORED_AT,
    sr.DECISION_DOMAIN,
    sr.RISK_LEVEL,
    sr.TOTAL_SCORE,
    sr.CONFIDENCE_SCORE,
    sr.SEVERITY_SCORE,
    sr.URGENCY_SCORE,
    sr.BUSINESS_IMPACT_SCORE,
    sr.WORKLOAD_CLASS,
    sr.TOPOLOGY_CLASS AS SCORE_TOPOLOGY_CLASS,
    sr.PLATFORM_CLASS AS SCORE_PLATFORM_CLASS,
    sr.EVENT_CLASS,
    sr.PRIMARY_SIGNAL_DOMAIN,
    sr.EXPLANATION_JSON,
    sr.CONTRIBUTION_JSON,
    sr.SCORECARD_JSON,
    sr.CREATED_AT
FROM latest_score_per_awr sr
JOIN VW_AWR_SCOPE_CONTEXT sc
  ON sc.AWR_ID = sr.AWR_ID
 AND sc.SOURCE_SYSTEM_ID = sr.SOURCE_SYSTEM_ID
LEFT JOIN AWR_SCORING_MODEL sm
  ON sm.SCORING_MODEL_ID = sr.SCORING_MODEL_ID
WHERE sr.RN = 1;


CREATE OR REPLACE VIEW VW_AWR_FEATURE_METRIC_SCOPE AS
WITH feature_metric_base AS (
    SELECT
        fs.AWR_ID,
        fs.SOURCE_SYSTEM_ID,
        fs.DB_NAME,
        fs.DBID,
        fs.HOST_NAME,
        fs.INSTANCE_NAME,
        fs.INSTANCE_NUMBER,
        fs.SNAP_BEGIN_TIME,
        fs.SNAP_END_TIME,
        fs.DB_VERSION,
        fs.DATABASE_ROLE,
        fs.INSTANCE_COUNT,
        fs.PLATFORM,
        fs.TOPOLOGY_CLASS,
        fs.PLATFORM_CLASS,
        fs.FEATURE_VECTOR_ID,
        fs.OBSERVED_AT,
        jt.*
    FROM VW_AWR_FEATURE_SCOPE fs
    CROSS APPLY JSON_TABLE(
        fs.FEATURE_JSON,
        '$'
        COLUMNS (
            CPU_UTIL_P95 NUMBER PATH '$.CPU_UTIL_P95' NULL ON ERROR,
            DB_CPU_PCT_DB_TIME NUMBER PATH '$.DB_CPU_PCT_DB_TIME' NULL ON ERROR,
            DB_TIME_PER_TXN NUMBER PATH '$.DB_TIME_PER_TXN' NULL ON ERROR,
            DB_TIME_PER_SEC NUMBER PATH '$.db_time_per_sec' NULL ON ERROR,
            DB_CPU_PER_SEC NUMBER PATH '$.db_cpu_per_sec' NULL ON ERROR,
            READ_LATENCY_MS NUMBER PATH '$.READ_LATENCY_MS' NULL ON ERROR,
            WRITE_LATENCY_MS NUMBER PATH '$.WRITE_LATENCY_MS' NULL ON ERROR,
            TEMP_WRITE_LATENCY_MS NUMBER PATH '$.TEMP_WRITE_LATENCY_MS' NULL ON ERROR,
            LOG_FILE_SYNC_MS NUMBER PATH '$.LOG_FILE_SYNC_MS' NULL ON ERROR,
            LOG_WRITE_LATENCY_MS NUMBER PATH '$.LOG_WRITE_LATENCY_MS' NULL ON ERROR,
            REDO_GENERATION_PER_SEC NUMBER PATH '$.REDO_GENERATION_PER_SEC' NULL ON ERROR,
            TOP_SQL_LOAD_CONCENTRATION NUMBER PATH '$.TOP_SQL_LOAD_CONCENTRATION' NULL ON ERROR,
            HARD_PARSES_PER_SEC NUMBER PATH '$.HARD_PARSES_PER_SEC' NULL ON ERROR,
            HARD_PARSE_PCT NUMBER PATH '$.HARD_PARSE_PCT' NULL ON ERROR,
            SOFT_PARSE_PCT NUMBER PATH '$.SOFT_PARSE_PCT' NULL ON ERROR,
            BUFFER_CACHE_HIT_RATIO_PCT NUMBER PATH '$.BUFFER_CACHE_HIT_RATIO_PCT' NULL ON ERROR,
            LIBRARY_CACHE_HIT_RATIO_PCT NUMBER PATH '$.LIBRARY_CACHE_HIT_RATIO_PCT' NULL ON ERROR,
            PARSE_CPU_TO_PARSE_ELAPSED_PCT NUMBER PATH '$.PARSE_CPU_TO_PARSE_ELAPSED_PCT' NULL ON ERROR,
            PGA_CACHE_HIT_PCT NUMBER PATH '$.PGA_CACHE_HIT_PCT' NULL ON ERROR,
            THROUGHPUT_USER_CALLS_PER_SEC NUMBER PATH '$.THROUGHPUT_USER_CALLS_PER_SEC' NULL ON ERROR,
            TRANSACTIONS_PER_SEC NUMBER PATH '$.transactions_per_sec' NULL ON ERROR,
            TEMP_IO_PRESSURE NUMBER PATH '$.TEMP_IO_PRESSURE' NULL ON ERROR,
            PGA_SPILL_PRESSURE NUMBER PATH '$.PGA_SPILL_PRESSURE' NULL ON ERROR,
            TEMP_SPILL_PCT NUMBER PATH '$.TEMP_SPILL_PCT' NULL ON ERROR,
            SORTS_DISK_PCT NUMBER PATH '$.SORTS_DISK_PCT' NULL ON ERROR,
            WORKAREA_ONEPASS_PCT NUMBER PATH '$.WORKAREA_ONEPASS_PCT' NULL ON ERROR,
            WORKAREA_MULTIPASS_PCT NUMBER PATH '$.WORKAREA_MULTIPASS_PCT' NULL ON ERROR,
            USER_IO_PRESSURE NUMBER PATH '$.USER_IO_PRESSURE' NULL ON ERROR,
            COMMIT_PRESSURE NUMBER PATH '$.COMMIT_PRESSURE' NULL ON ERROR,
            CONCURRENCY_PRESSURE NUMBER PATH '$.CONCURRENCY_PRESSURE' NULL ON ERROR,
            NETWORK_WAIT_PCT_DB_TIME NUMBER PATH '$.NETWORK_WAIT_PCT_DB_TIME' NULL ON ERROR,
            CURSOR_MUTEX_WAIT_PCT_DB_TIME NUMBER PATH '$.CURSOR_MUTEX_WAIT_PCT_DB_TIME' NULL ON ERROR,
            READ_MB_PER_SEC NUMBER PATH '$.READ_MB_PER_SEC' NULL ON ERROR,
            WRITE_MB_PER_SEC NUMBER PATH '$.WRITE_MB_PER_SEC' NULL ON ERROR,
            CLUSTER_WAIT_PCT_DB_TIME NUMBER PATH '$.CLUSTER_WAIT_PCT_DB_TIME' NULL ON ERROR,
            GC_CR_WAIT_PCT_DB_TIME NUMBER PATH '$.GC_CR_WAIT_PCT_DB_TIME' NULL ON ERROR,
            GC_CURRENT_WAIT_PCT_DB_TIME NUMBER PATH '$.GC_CURRENT_WAIT_PCT_DB_TIME' NULL ON ERROR,
            GC_BUFFER_BUSY_PCT_DB_TIME NUMBER PATH '$.GC_BUFFER_BUSY_PCT_DB_TIME' NULL ON ERROR,
            INTERCONNECT_STRESS_FLAG NUMBER PATH '$.INTERCONNECT_STRESS_FLAG' NULL ON ERROR,
            RAC_CONTENTION_FLAG NUMBER PATH '$.RAC_CONTENTION_FLAG' NULL ON ERROR,
            EXA_CELL_IO_PCT_DB_TIME NUMBER PATH '$.EXA_CELL_IO_PCT_DB_TIME' NULL ON ERROR,
            EXA_OFFLOAD_EFFICIENCY NUMBER PATH '$.EXA_OFFLOAD_EFFICIENCY' NULL ON ERROR,
            STORAGE_INDEX_SAVINGS_PCT NUMBER PATH '$.STORAGE_INDEX_SAVINGS_PCT' NULL ON ERROR,
            CELL_SINGLE_BLOCK_LATENCY_MS NUMBER PATH '$.CELL_SINGLE_BLOCK_LATENCY_MS' NULL ON ERROR,
            CELL_MULTIBLOCK_LATENCY_MS NUMBER PATH '$.CELL_MULTIBLOCK_LATENCY_MS' NULL ON ERROR,
            EXA_STORAGE_INDEX_SAVINGS NUMBER PATH '$.EXA_STORAGE_INDEX_SAVINGS' NULL ON ERROR,
            SMART_SCAN_FLAG NUMBER PATH '$.SMART_SCAN_FLAG' NULL ON ERROR,
            FLASH_CACHE_HIT_FLAG NUMBER PATH '$.flash_cache_hit_flag' NULL ON ERROR,
            EXADATA_IO_BENEFIT_FLAG NUMBER PATH '$.exadata_io_benefit_flag' NULL ON ERROR,
            TRANSPORT_LAG_SEC NUMBER PATH '$.TRANSPORT_LAG_SEC' NULL ON ERROR,
            APPLY_LAG_SEC NUMBER PATH '$.APPLY_LAG_SEC' NULL ON ERROR,
            REDO_TRANSPORT_ISSUE_FLAG NUMBER PATH '$.REDO_TRANSPORT_ISSUE_FLAG' NULL ON ERROR,
            FAILOVER_EVENT_FLAG NUMBER PATH '$.FAILOVER_EVENT_FLAG' NULL ON ERROR,
            ROLE_TRANSITION_FLAG NUMBER PATH '$.ROLE_TRANSITION_FLAG' NULL ON ERROR,
            POST_FAILOVER_RECOVERY_FLAG NUMBER PATH '$.POST_FAILOVER_RECOVERY_FLAG' NULL ON ERROR
        )
    ) jt
),
feature_metric_unpivot AS (
    SELECT
        AWR_ID,
        SOURCE_SYSTEM_ID,
        DB_NAME,
        DBID,
        HOST_NAME,
        INSTANCE_NAME,
        INSTANCE_NUMBER,
        SNAP_BEGIN_TIME,
        SNAP_END_TIME,
        DB_VERSION,
        DATABASE_ROLE,
        INSTANCE_COUNT,
        PLATFORM,
        TOPOLOGY_CLASS,
        PLATFORM_CLASS,
        FEATURE_VECTOR_ID,
        OBSERVED_AT,
        METRIC_NAME,
        METRIC_VALUE_NUM
    FROM feature_metric_base
    UNPIVOT (
        METRIC_VALUE_NUM FOR METRIC_NAME IN (
            CPU_UTIL_P95,
            DB_CPU_PCT_DB_TIME,
            DB_TIME_PER_TXN,
            DB_TIME_PER_SEC,
            DB_CPU_PER_SEC,
            READ_LATENCY_MS,
            WRITE_LATENCY_MS,
            TEMP_WRITE_LATENCY_MS,
            LOG_FILE_SYNC_MS,
            LOG_WRITE_LATENCY_MS,
            REDO_GENERATION_PER_SEC,
            TOP_SQL_LOAD_CONCENTRATION,
            HARD_PARSES_PER_SEC,
            HARD_PARSE_PCT,
            SOFT_PARSE_PCT,
            BUFFER_CACHE_HIT_RATIO_PCT,
            LIBRARY_CACHE_HIT_RATIO_PCT,
            PARSE_CPU_TO_PARSE_ELAPSED_PCT,
            PGA_CACHE_HIT_PCT,
            THROUGHPUT_USER_CALLS_PER_SEC,
            TRANSACTIONS_PER_SEC,
            TEMP_IO_PRESSURE,
            PGA_SPILL_PRESSURE,
            TEMP_SPILL_PCT,
            SORTS_DISK_PCT,
            WORKAREA_ONEPASS_PCT,
            WORKAREA_MULTIPASS_PCT,
            USER_IO_PRESSURE,
            COMMIT_PRESSURE,
            CONCURRENCY_PRESSURE,
            NETWORK_WAIT_PCT_DB_TIME,
            CURSOR_MUTEX_WAIT_PCT_DB_TIME,
            READ_MB_PER_SEC,
            WRITE_MB_PER_SEC,
            CLUSTER_WAIT_PCT_DB_TIME,
            GC_CR_WAIT_PCT_DB_TIME,
            GC_CURRENT_WAIT_PCT_DB_TIME,
            GC_BUFFER_BUSY_PCT_DB_TIME,
            INTERCONNECT_STRESS_FLAG,
            RAC_CONTENTION_FLAG,
            EXA_CELL_IO_PCT_DB_TIME,
            EXA_OFFLOAD_EFFICIENCY,
            STORAGE_INDEX_SAVINGS_PCT,
            CELL_SINGLE_BLOCK_LATENCY_MS,
            CELL_MULTIBLOCK_LATENCY_MS,
            EXA_STORAGE_INDEX_SAVINGS,
            SMART_SCAN_FLAG,
            FLASH_CACHE_HIT_FLAG,
            EXADATA_IO_BENEFIT_FLAG,
            TRANSPORT_LAG_SEC,
            APPLY_LAG_SEC,
            REDO_TRANSPORT_ISSUE_FLAG,
            FAILOVER_EVENT_FLAG,
            ROLE_TRANSITION_FLAG,
            POST_FAILOVER_RECOVERY_FLAG
        )
    )
)
SELECT
    AWR_ID,
    SOURCE_SYSTEM_ID,
    DB_NAME,
    DBID,
    HOST_NAME,
    INSTANCE_NAME,
    INSTANCE_NUMBER,
    SNAP_BEGIN_TIME,
    SNAP_END_TIME,
    DB_VERSION,
    DATABASE_ROLE,
    INSTANCE_COUNT,
    PLATFORM,
    TOPOLOGY_CLASS,
    PLATFORM_CLASS,
    METRIC_NAME,
    'DB' AS METRIC_SCOPE,
    CASE
        WHEN METRIC_NAME IN (
            'CPU_UTIL_P95',
            'DB_CPU_PCT_DB_TIME',
            'DB_TIME_PER_TXN',
            'DB_TIME_PER_SEC',
            'DB_CPU_PER_SEC',
            'READ_LATENCY_MS',
            'WRITE_LATENCY_MS',
            'TEMP_WRITE_LATENCY_MS',
            'LOG_FILE_SYNC_MS',
            'LOG_WRITE_LATENCY_MS',
            'REDO_GENERATION_PER_SEC',
            'TOP_SQL_LOAD_CONCENTRATION',
            'HARD_PARSES_PER_SEC',
            'HARD_PARSE_PCT',
            'SOFT_PARSE_PCT',
            'BUFFER_CACHE_HIT_RATIO_PCT',
            'LIBRARY_CACHE_HIT_RATIO_PCT',
            'PARSE_CPU_TO_PARSE_ELAPSED_PCT',
            'PGA_CACHE_HIT_PCT',
            'THROUGHPUT_USER_CALLS_PER_SEC',
            'TRANSACTIONS_PER_SEC',
            'TEMP_IO_PRESSURE',
            'PGA_SPILL_PRESSURE',
            'TEMP_SPILL_PCT',
            'SORTS_DISK_PCT',
            'WORKAREA_ONEPASS_PCT',
            'WORKAREA_MULTIPASS_PCT',
            'USER_IO_PRESSURE',
            'COMMIT_PRESSURE',
            'CONCURRENCY_PRESSURE',
            'NETWORK_WAIT_PCT_DB_TIME',
            'CURSOR_MUTEX_WAIT_PCT_DB_TIME',
            'READ_MB_PER_SEC',
            'WRITE_MB_PER_SEC'
        ) THEN 'GENERAL'
        WHEN METRIC_NAME IN (
            'CLUSTER_WAIT_PCT_DB_TIME',
            'GC_CR_WAIT_PCT_DB_TIME',
            'GC_CURRENT_WAIT_PCT_DB_TIME',
            'GC_BUFFER_BUSY_PCT_DB_TIME',
            'INTERCONNECT_STRESS_FLAG',
            'RAC_CONTENTION_FLAG'
        ) THEN 'RAC_CLUSTER'
        WHEN METRIC_NAME IN (
            'EXA_CELL_IO_PCT_DB_TIME',
            'EXA_OFFLOAD_EFFICIENCY',
            'STORAGE_INDEX_SAVINGS_PCT',
            'CELL_SINGLE_BLOCK_LATENCY_MS',
            'CELL_MULTIBLOCK_LATENCY_MS',
            'EXA_STORAGE_INDEX_SAVINGS',
            'SMART_SCAN_FLAG',
            'FLASH_CACHE_HIT_FLAG',
            'EXADATA_IO_BENEFIT_FLAG'
        ) THEN 'EXADATA'
        WHEN METRIC_NAME IN (
            'TRANSPORT_LAG_SEC',
            'APPLY_LAG_SEC',
            'REDO_TRANSPORT_ISSUE_FLAG'
        ) THEN 'DATA_GUARD'
        ELSE 'TOPOLOGY_EVENT'
    END AS METRIC_CATEGORY,
    METRIC_VALUE_NUM,
    FEATURE_VECTOR_ID,
    OBSERVED_AT
FROM feature_metric_unpivot
WHERE METRIC_VALUE_NUM IS NOT NULL;

spool off
