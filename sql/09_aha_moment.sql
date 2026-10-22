-- 09_aha_moment.sql
-- Only compare users who were active on at least one day in days 1-7.
-- Now every comparison is "engaged users who did X" vs "engaged users who
-- didn't", and only features with a genuine extra effect stand out.
-- Even then, this is correlation, not causation.

WITH base AS (
    SELECT u.user_id, u.signup_date
    FROM users_clean u
    JOIN activated_users a ON a.user_id = u.user_id
    CROSS JOIN data_window w
    WHERE u.signup_date <= DATE(w.max_date, '-30 days')          -- full 30 days of data
      AND EXISTS (SELECT 1 FROM daily_activity d                 -- came back in week 1
                  WHERE d.user_id = u.user_id
                    AND d.active_date BETWEEN DATE(u.signup_date, '+1 day')
                                          AND DATE(u.signup_date, '+7 days'))
),
week1 AS (
    SELECT
        b.user_id,
        MAX(CASE WHEN e.event_name = 'message_advisor' THEN 1 ELSE 0 END) AS used_message_advisor,
        MAX(CASE WHEN e.event_name = 'transfer_funds'  THEN 1 ELSE 0 END) AS used_transfer_funds,
        MAX(CASE WHEN e.event_name = 'view_statement'  THEN 1 ELSE 0 END) AS used_view_statement,
        MAX(CASE WHEN e.event_name = 'view_research'   THEN 1 ELSE 0 END) AS used_view_research
    FROM base b
    LEFT JOIN events_clean e
           ON e.user_id = b.user_id
          AND e.event_date BETWEEN b.signup_date AND DATE(b.signup_date, '+7 days')
    GROUP BY b.user_id
),
d30 AS (
    SELECT b.user_id,
           MAX(CASE WHEN d.active_date = DATE(b.signup_date, '+30 days') THEN 1 ELSE 0 END) AS retained_d30
    FROM base b
    LEFT JOIN daily_activity d
           ON d.user_id = b.user_id AND d.active_date = DATE(b.signup_date, '+30 days')
    GROUP BY b.user_id
),
joined AS (SELECT w.*, d.retained_d30 FROM week1 w JOIN d30 d ON d.user_id = w.user_id),
long AS (
    SELECT 'message_advisor' AS feature, used_message_advisor AS used, retained_d30 FROM joined
    UNION ALL SELECT 'transfer_funds', used_transfer_funds, retained_d30 FROM joined
    UNION ALL SELECT 'view_statement', used_view_statement, retained_d30 FROM joined
    UNION ALL SELECT 'view_research',  used_view_research,  retained_d30 FROM joined
)
SELECT
    feature,
    SUM(used)                                                                    AS users_who_used,
    SUM(1 - used)                                                                AS users_who_did_not,
    ROUND(100.0 * SUM(used * retained_d30) / NULLIF(SUM(used), 0), 1)            AS d30_pct_used,
    ROUND(100.0 * SUM((1 - used) * retained_d30) / NULLIF(SUM(1 - used), 0), 1) AS d30_pct_did_not,
    ROUND( (1.0 * SUM(used * retained_d30) / NULLIF(SUM(used), 0))
         / NULLIF(1.0 * SUM((1 - used) * retained_d30) / NULLIF(SUM(1 - used), 0), 0), 2) AS retention_lift_x
FROM long
GROUP BY feature
ORDER BY retention_lift_x DESC;
