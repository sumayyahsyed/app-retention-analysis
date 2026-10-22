-- 01_data_quality_checks.sql
-- PURPOSE: Before analyzing anything, check the raw data for problems.

SELECT 'total users' AS check_name, COUNT(*) AS value FROM users
UNION ALL
SELECT 'total event rows', COUNT(*) FROM events
UNION ALL
SELECT 'duplicate event rows (same event_id appears 2+ times)',
       COUNT(*) - COUNT(DISTINCT event_id) FROM events
UNION ALL
SELECT 'internal test accounts', COUNT(*) FROM users WHERE acquisition_channel = 'internal_test'
UNION ALL
SELECT 'users with missing platform', COUNT(*) FROM users WHERE platform IS NULL OR platform = ''
UNION ALL
SELECT 'events from users not in users table', COUNT(*)
FROM events e LEFT JOIN users u ON u.user_id = e.user_id WHERE u.user_id IS NULL
UNION ALL
SELECT 'events dated before user signup', COUNT(*)
FROM events e JOIN users u ON u.user_id = e.user_id WHERE DATE(e.event_ts) < u.signup_date;
