-- 05_retention_cohorts.sql
-- QUESTION: Of users who signed up in a given week, what % came back
-- exactly 1, 7 and 30 days later?
-- Definition used: "Day N retention" = active on calendar day signup_date + N.
-- (Classic/exact-day retention. A looser "rolling" definition would count
--  anyone active on day N OR later.)
--
-- Two versions are shown per cohort:
--   *_all       = denominator is everyone who installed
--   *_activated = denominator is only users who finished onboarding
--
-- Users whose Day-N date is after the end of the data get NULL for that
-- metric, and AVG() ignores NULLs, so recent cohorts are not unfairly
-- counted as "not retained". Cohorts with no mature users show blank.

WITH cohort AS (
    SELECT
        u.user_id,
        u.signup_date,
        DATE(u.signup_date, 'weekday 0', '-6 days') AS cohort_week,   -- Monday of signup week
        CASE WHEN a.user_id IS NOT NULL THEN 1 ELSE 0 END AS is_activated
    FROM users_clean u
    LEFT JOIN activated_users a ON a.user_id = u.user_id
),
flags AS (
    SELECT
        c.user_id,
        c.cohort_week,
        c.is_activated,
        CASE WHEN DATE(c.signup_date, '+1 day')  <= w.max_date
             THEN MAX(CASE WHEN d.active_date = DATE(c.signup_date, '+1 day')  THEN 1 ELSE 0 END) END AS d1,
        CASE WHEN DATE(c.signup_date, '+7 days') <= w.max_date
             THEN MAX(CASE WHEN d.active_date = DATE(c.signup_date, '+7 days') THEN 1 ELSE 0 END) END AS d7,
        CASE WHEN DATE(c.signup_date, '+30 days') <= w.max_date
             THEN MAX(CASE WHEN d.active_date = DATE(c.signup_date, '+30 days') THEN 1 ELSE 0 END) END AS d30
    FROM cohort c
    CROSS JOIN data_window w
    LEFT JOIN daily_activity d
           ON d.user_id = c.user_id
          AND d.active_date IN (DATE(c.signup_date, '+1 day'),
                                DATE(c.signup_date, '+7 days'),
                                DATE(c.signup_date, '+30 days'))
    GROUP BY c.user_id, c.cohort_week, c.is_activated, c.signup_date, w.max_date
)
SELECT
    cohort_week,
    COUNT(*)                                                       AS cohort_size,
    SUM(is_activated)                                              AS activated_users,
    ROUND(100.0 * SUM(is_activated) / COUNT(*), 1)                 AS activation_pct,
    ROUND(100.0 * AVG(d1), 1)                                      AS d1_pct_all,
    ROUND(100.0 * AVG(d7), 1)                                      AS d7_pct_all,
    ROUND(100.0 * AVG(d30), 1)                                     AS d30_pct_all,
    ROUND(100.0 * AVG(CASE WHEN is_activated = 1 THEN d1  END), 1) AS d1_pct_activated,
    ROUND(100.0 * AVG(CASE WHEN is_activated = 1 THEN d7  END), 1) AS d7_pct_activated,
    ROUND(100.0 * AVG(CASE WHEN is_activated = 1 THEN d30 END), 1) AS d30_pct_activated
FROM flags
GROUP BY cohort_week
ORDER BY cohort_week;
