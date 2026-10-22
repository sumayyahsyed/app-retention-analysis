-- 04_funnel_by_redesign_and_platform.sql
-- QUESTION: Did the March 15 onboarding redesign change conversion,
-- and is any platform hit harder?
-- This is the "diagnosis" query: it turns "activation is down" into
-- "verification on Android got much worse after the redesign."

WITH user_steps AS (
    SELECT
        u.user_id,
        u.redesign_period,
        u.platform,
        MAX(CASE WHEN e.event_name = 'create_account'      THEN 1 ELSE 0 END) AS created,
        MAX(CASE WHEN e.event_name = 'verify_identity'     THEN 1 ELSE 0 END) AS verified,
        MAX(CASE WHEN e.event_name = 'link_account'        THEN 1 ELSE 0 END) AS linked,
        MAX(CASE WHEN e.event_name = 'onboarding_complete' THEN 1 ELSE 0 END) AS completed
    FROM users_clean u
    JOIN events_clean e ON e.user_id = u.user_id
    WHERE u.platform <> 'Unknown'
    GROUP BY u.user_id, u.redesign_period, u.platform
)
SELECT
    redesign_period,
    platform,
    COUNT(*)                                                   AS users,
    ROUND(100.0 * SUM(created)   / COUNT(*), 1)                AS pct_created_account,
    ROUND(100.0 * SUM(verified)  / NULLIF(SUM(created), 0), 1) AS verify_rate_of_created,
    ROUND(100.0 * SUM(linked)    / NULLIF(SUM(verified), 0), 1) AS link_rate_of_verified,
    ROUND(100.0 * SUM(completed) / COUNT(*), 1)                AS overall_activation_pct
FROM user_steps
GROUP BY redesign_period, platform
ORDER BY redesign_period DESC, platform;
