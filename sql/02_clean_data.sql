-- 02_clean_data.sql
-- PURPOSE: Builds clean tables that every later query uses.
--   * remove internal test accounts
--   * remove duplicate events
--   * label missing platform as 'Unknown'
--   * add an event_date column and a pre/post-redesign flag

DROP TABLE IF EXISTS users_clean;
CREATE TABLE users_clean AS
SELECT
    user_id,
    signup_date,
    COALESCE(NULLIF(platform, ''), 'Unknown') AS platform,
    acquisition_channel,
    age_band,
    account_tier,
    CASE WHEN signup_date >= '2026-03-15' THEN 'post_redesign' ELSE 'pre_redesign' END AS redesign_period
FROM users
WHERE acquisition_channel <> 'internal_test';

DROP TABLE IF EXISTS events_clean;
CREATE TABLE events_clean AS
SELECT DISTINCT
    e.event_id,
    e.user_id,
    e.event_name,
    e.event_ts,
    DATE(e.event_ts) AS event_date
FROM events e
JOIN users_clean u ON u.user_id = e.user_id;

CREATE INDEX IF NOT EXISTS idx_ev_user ON events_clean(user_id);
CREATE INDEX IF NOT EXISTS idx_ev_date ON events_clean(event_date);
CREATE INDEX IF NOT EXISTS idx_ev_name ON events_clean(event_name);

-- Helper table: one row per user per day they were active
DROP TABLE IF EXISTS daily_activity;
CREATE TABLE daily_activity AS
SELECT DISTINCT user_id, event_date AS active_date
FROM events_clean;
CREATE INDEX IF NOT EXISTS idx_da_user ON daily_activity(user_id, active_date);

-- Helper table: last date in the data. A user who signed up fewer than 30
-- days before this can't have a Day-30 result yet, so we must exclude them
-- (otherwise recent cohorts look artificially bad).
DROP TABLE IF EXISTS data_window;
CREATE TABLE data_window AS
SELECT MAX(event_date) AS max_date FROM events_clean;

-- Helper table: who finished onboarding ("activated")
DROP TABLE IF EXISTS activated_users;
CREATE TABLE activated_users AS
SELECT DISTINCT user_id FROM events_clean WHERE event_name = 'onboarding_complete';
