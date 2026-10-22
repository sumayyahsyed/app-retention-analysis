-- 03_onboarding_funnel.sql
-- QUESTION: Of everyone who opened the app, how many made it through each
-- onboarding step, and where is the biggest drop?
-- step_conversion_pct = % of users from the PREVIOUS step who reached this one
-- overall_pct         = % of all users who reached this step

WITH user_steps AS (
    SELECT
        user_id,
        MAX(CASE WHEN event_name = 'app_open'            THEN 1 ELSE 0 END) AS s1,
        MAX(CASE WHEN event_name = 'create_account'      THEN 1 ELSE 0 END) AS s2,
        MAX(CASE WHEN event_name = 'verify_identity'     THEN 1 ELSE 0 END) AS s3,
        MAX(CASE WHEN event_name = 'link_account'        THEN 1 ELSE 0 END) AS s4,
        MAX(CASE WHEN event_name = 'onboarding_complete' THEN 1 ELSE 0 END) AS s5
    FROM events_clean
    GROUP BY user_id
),
totals AS (
    SELECT 1 AS step_order, '1. App opened'        AS step, SUM(s1) AS users FROM user_steps
    UNION ALL SELECT 2, '2. Account created',   SUM(s2) FROM user_steps
    UNION ALL SELECT 3, '3. Identity verified', SUM(s3) FROM user_steps
    UNION ALL SELECT 4, '4. Bank account linked', SUM(s4) FROM user_steps
    UNION ALL SELECT 5, '5. Onboarding complete', SUM(s5) FROM user_steps
)
SELECT
    step_order,
    step,
    users,
    ROUND(100.0 * users / LAG(users) OVER (ORDER BY step_order), 1) AS step_conversion_pct,
    ROUND(100.0 * users / FIRST_VALUE(users) OVER (ORDER BY step_order), 1) AS overall_pct,
    LAG(users) OVER (ORDER BY step_order) - users AS users_lost_at_step
FROM totals
ORDER BY step_order;
