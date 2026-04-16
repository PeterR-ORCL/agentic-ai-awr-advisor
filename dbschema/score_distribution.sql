SELECT
    risk_level,
    COUNT(*) AS cnt,
    MIN(total_score) AS min_score,
    MAX(total_score) AS max_score,
    ROUND(AVG(total_score), 2) AS avg_score
FROM
    awr_score_result s
    JOIN awr_source_system ss
        ON s.source_system_id = ss.source_system_id
WHERE
    ss.dbid = 1234567890
GROUP BY
    risk_level
ORDER BY
    min_score;
