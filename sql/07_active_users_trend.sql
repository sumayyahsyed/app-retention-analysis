-- 07_active_users_trend.sql
-- QUESTION: How is overall usage trending month to month?
--   MAU          = distinct users active at least once in the month
--   avg_DAU      = average distinct users active per day in the month
--   stickiness   = avg_DAU / MAU  (how many days a month a typical user shows up)
--   new_signups  = users who installed that month

WITH dau AS (
    SELECT active_date, COUNT(DISTINCT user_id) AS dau
    FROM daily_activity
    GROUP BY active_date
),
monthly_dau AS (
    SELECT STRFTIME('%Y-%m', active_date) AS month, ROUND(AVG(dau), 0) AS avg_dau
    FROM dau
    GROUP BY month
),
mau AS (
    SELECT STRFTIME('%Y-%m', active_date) AS month, COUNT(DISTINCT user_id) AS mau
    FROM daily_activity
    GROUP BY month
),
signups AS (
    SELECT STRFTIME('%Y-%m', signup_date) AS month, COUNT(*) AS new_signups
    FROM users_clean
    GROUP BY month
)
SELECT
    m.month,
    m.mau,
    d.avg_dau,
    ROUND(100.0 * d.avg_dau / m.mau, 1)                                   AS stickiness_pct,
    COALESCE(s.new_signups, 0)                                            AS new_signups,
    ROUND(100.0 * (m.mau - LAG(m.mau) OVER (ORDER BY m.month))
          / LAG(m.mau) OVER (ORDER BY m.month), 1)                        AS mau_mom_change_pct
FROM mau m
JOIN monthly_dau d ON d.month = m.month
LEFT JOIN signups s ON s.month = m.month
ORDER BY m.month;
