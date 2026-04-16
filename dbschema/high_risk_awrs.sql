SELECT
    s.awr_id,
    r.snap_id_begin,
    r.snap_id_end,
    r.snap_time_begin,
    r.snap_time_end,
    s.decision_domain,
    s.total_score,
    s.risk_level,
    s.confidence_score,
    s.severity_score,
    s.urgency_score,
    s.business_impact_score,
    s.workload_class,
    s.topology_class,
    s.platform_class,
    s.event_class,
    s.primary_signal_domain
FROM
    awr_score_result s
    JOIN awr_source_system ss
        ON s.source_system_id = ss.source_system_id
    LEFT JOIN awr_report r
        ON s.awr_id = r.awr_id
WHERE
    ss.dbid = 1234567890
    AND s.risk_level IN ('MEDIUM')
ORDER BY
    s.total_score DESC,
    r.snap_time_begin;
