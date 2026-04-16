SELECT
    s.awr_id,
    r.snap_time_begin,
    r.snap_time_end,
    s.total_score,
    LAG(s.total_score) OVER (ORDER BY r.snap_time_begin) AS prev_score,
    s.total_score
      - LAG(s.total_score) OVER (ORDER BY r.snap_time_begin) AS score_delta,
    s.risk_level,
    s.workload_class,
    s.event_class
FROM
    awr_score_result s
    JOIN awr_source_system ss
        ON s.source_system_id = ss.source_system_id
    LEFT JOIN awr_report r
        ON s.awr_id = r.awr_id
WHERE
    ss.dbid = 1234567890
ORDER BY
    r.snap_time_begin;
