query = """
SELECT

    CASE
        WHEN public_pct >= 50 AND public_pct < 60 THEN '50-59%'
        WHEN public_pct >= 60 AND public_pct < 70 THEN '60-69%'
        WHEN public_pct >= 70 AND public_pct < 80 THEN '70-79%'
        WHEN public_pct >= 80 AND public_pct < 90 THEN '80-89%'
        WHEN public_pct >= 90 THEN '90%+'
    END AS public_range,

    COUNT(*) AS games,

    SUM(
        CASE
            WHEN public_result = 'WIN'
            THEN 1
            ELSE 0
        END
    ) AS wins,

    SUM(
        CASE
            WHEN public_result = 'LOSS'
            THEN 1
            ELSE 0
        END
    ) AS losses,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN public_result = 'WIN'
                THEN 1
                ELSE 0
            END
        )
        / COUNT(*),
        1
    ) AS ats_pct

FROM games

WHERE public_result IN ('WIN', 'LOSS')

GROUP BY public_range

ORDER BY public_range
"""