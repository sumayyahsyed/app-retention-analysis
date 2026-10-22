-- 08_feature_adoption.sql
-- QUESTION: Which features do new (activated) users actually use in their
-- first 7 days?  Low adoption of a valuable feature = product opportunity.

WITH first_week AS (
    SELECT e.user_id, e.event_name
    FROM events_clean e
    JOIN users_clean u     ON u.user_id = e.user_id
    JOIN activated_users a ON a.user_id = e.user_id
    WHERE e.event_date BETWEEN u.signup_date AND DATE(u.signup_date, '+7 days')
      AND e.event_name IN ('view_portfolio', 'view_statement', 'transfer_funds',
                           'view_research', 'message_advisor')
),
denom AS (SELECT COUNT(*) AS n FROM activated_users)
SELECT
    f.event_name                                            AS feature,
    COUNT(DISTINCT f.user_id)                               AS users_who_used_it,
    ROUND(100.0 * COUNT(DISTINCT f.user_id) / denom.n, 1)   AS adoption_pct_first_7_days,
    ROUND(1.0 * COUNT(*) / COUNT(DISTINCT f.user_id), 1)    AS avg_uses_per_adopter
FROM first_week f, denom
GROUP BY f.event_name, denom.n
ORDER BY adoption_pct_first_7_days DESC;
