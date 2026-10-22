-- 06_retention_by_segment.sql
-- QUESTION: Which kinds of users stick around? (activated users only, so
-- measure engagement separately from the onboarding problem)

WITH base AS (
    SELECT
        u.user_id, u.signup_date, u.platform, u.acquisition_channel,
        u.account_tier, u.age_band, u.redesign_period
    FROM users_clean u
    JOIN activated_users a ON a.user_id = u.user_id
    CROSS JOIN data_window w
    WHERE u.signup_date <= DATE(w.max_date, '-30 days')   -- only users with a full 30 days of data
),
flags AS (
    SELECT
        b.*,
        MAX(CASE WHEN d.active_date = DATE(b.signup_date, '+1 day')  THEN 1 ELSE 0 END) AS d1,
        MAX(CASE WHEN d.active_date = DATE(b.signup_date, '+7 days') THEN 1 ELSE 0 END) AS d7,
        MAX(CASE WHEN d.active_date = DATE(b.signup_date, '+30 days') THEN 1 ELSE 0 END) AS d30
    FROM base b
    LEFT JOIN daily_activity d
           ON d.user_id = b.user_id
          AND d.active_date IN (DATE(b.signup_date, '+1 day'),
                                DATE(b.signup_date, '+7 days'),
                                DATE(b.signup_date, '+30 days'))
    GROUP BY b.user_id
),
long AS (
    SELECT 'platform' AS segment_type, platform AS segment_value, d1, d7, d30 FROM flags
    UNION ALL SELECT 'acquisition_channel', acquisition_channel, d1, d7, d30 FROM flags
    UNION ALL SELECT 'account_tier',        account_tier,        d1, d7, d30 FROM flags
    UNION ALL SELECT 'age_band',            age_band,            d1, d7, d30 FROM flags
)
SELECT
    segment_type,
    segment_value,
    COUNT(*)                              AS activated_users,
    ROUND(100.0 * AVG(d1), 1)             AS d1_pct,
    ROUND(100.0 * AVG(d7), 1)             AS d7_pct,
    ROUND(100.0 * AVG(d30), 1)            AS d30_pct
FROM long
WHERE segment_value <> 'Unknown'
GROUP BY segment_type, segment_value
ORDER BY segment_type, d30_pct DESC;
