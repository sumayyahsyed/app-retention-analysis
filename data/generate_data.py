"""
generate_data.py
----------------
Creates a realistic, synthetic event dataset for "WealthView", a fictional
wealth-management mobile app.

Output:
    users.csv   - one row per user who installed the app
    events.csv  - one row per in-app event (onboarding steps + engagement)

PATTERNS IN DATA:
    1. On 2026-03-15 a redesigned onboarding flow launched. Identity
       verification completion dropped after it, especially on Android.
    2. Android users retain somewhat worse than iOS users overall.
    3. Users who message their advisor in their first week retain ~2x better
       (the "aha moment"), even compared with other equally active users.
    4. Advisor-referral users retain best; paid-social users retain worst.
    5. New signups slowly decline after the redesign, so monthly active
       users (MAU) fall from their peak.

DATA QUALITY ISSUES:
    - ~0.4% of event rows are exact duplicates (same event_id)
    - a few dozen internal test accounts (acquisition_channel = 'internal_test')
    - a small share of users with a missing platform value
"""

import os
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

SEED = 42
SIGNUP_START = date(2025, 9, 1)    # app launch
SIGNUP_END = date(2026, 7, 31)
EVENT_END = date(2026, 7, 31)      # data "pulled" on this day
REDESIGN_DATE = date(2026, 3, 15)  # onboarding redesign launch

rng = np.random.default_rng(SEED)
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# 1. Users
# ---------------------------------------------------------------------------
def daily_signups(d: date) -> int:
    """Expected installs per day: flat before the redesign, slow decline after
    (worse reviews), with lower volume on weekends."""
    base = 150.0
    if d >= REDESIGN_DATE:
        days_after = (d - REDESIGN_DATE).days
        base *= max(0.78, 1 - 0.0021 * days_after)
    if d.weekday() >= 5:
        base *= 0.8
    return int(rng.poisson(base))


user_rows = []
uid = 0
d = SIGNUP_START
while d <= SIGNUP_END:
    for _ in range(daily_signups(d)):
        uid += 1
        user_rows.append({
            "user_id": f"u{uid:06d}",
            "signup_date": d.isoformat(),
            "platform": rng.choice(["iOS", "Android"], p=[0.55, 0.45]),
            "acquisition_channel": rng.choice(
                ["organic", "paid_social", "search", "advisor_referral"],
                p=[0.35, 0.25, 0.22, 0.18]),
            "age_band": rng.choice(
                ["18-34", "35-49", "50-64", "65+"], p=[0.22, 0.33, 0.30, 0.15]),
            "account_tier": rng.choice(
                ["standard", "premier", "private_client"], p=[0.60, 0.30, 0.10]),
        })
    d += timedelta(days=1)

# Internal test accounts
for i in range(40):
    uid += 1
    user_rows.append({
        "user_id": f"u{uid:06d}",
        "signup_date": (SIGNUP_START + timedelta(days=int(rng.integers(0, 250)))).isoformat(),
        "platform": rng.choice(["iOS", "Android"]),
        "acquisition_channel": "internal_test",
        "age_band": "35-49",
        "account_tier": "standard",
    })

users = pd.DataFrame(user_rows)


# ---------------------------------------------------------------------------
# 2. Events
# ---------------------------------------------------------------------------
events = []  # tuples: (user_id, event_name, event_ts)


def ts(day: date) -> str:
    """Random timestamp between 7:00 and 23:00 on the given day."""
    secs = int(rng.integers(7 * 3600, 23 * 3600))
    return (datetime.combine(day, datetime.min.time()) + timedelta(seconds=secs)).strftime("%Y-%m-%d %H:%M:%S")


def verify_prob(platform: str, signup: date) -> float:
    """Chance a user who created an account gets through identity verification."""
    if signup < REDESIGN_DATE:
        return 0.82 if platform == "iOS" else 0.79
    return 0.74 if platform == "iOS" else 0.53   # redesign hurt Android badly


CHANNEL_MULT = {"organic": 1.10, "paid_social": 0.72, "search": 1.00,
                "advisor_referral": 1.35, "internal_test": 3.0}
TIER_MULT = {"standard": 0.95, "premier": 1.05, "private_client": 1.20}
PLATFORM_MULT = {"iOS": 1.0, "Android": 0.88}
FEATURES = ["view_portfolio", "view_statement", "transfer_funds", "view_research", "message_advisor"]

for u in users.itertuples(index=False):
    signup = date.fromisoformat(u.signup_date)
    is_test = u.acquisition_channel == "internal_test"

    # ---- Onboarding funnel (all on signup day) ----
    t0 = datetime.combine(signup, datetime.min.time()) + timedelta(seconds=int(rng.integers(7 * 3600, 22 * 3600)))
    step_times = [t0 + timedelta(minutes=int(m)) for m in np.cumsum(rng.integers(1, 6, size=5))]
    events.append((u.user_id, "app_open", t0.strftime("%Y-%m-%d %H:%M:%S")))

    p_link = 0.88 if u.account_tier == "private_client" else 0.80
    funnel = [("create_account", 1.0 if is_test else 0.86),
              ("verify_identity", 1.0 if is_test else verify_prob(u.platform, signup)),
              ("link_account", 1.0 if is_test else p_link),
              ("onboarding_complete", 1.0 if is_test else 0.95)]
    completed = True
    for (step, p), t in zip(funnel, step_times):
        if rng.random() < p:
            events.append((u.user_id, step, t.strftime("%Y-%m-%d %H:%M:%S")))
        else:
            completed = False
            break

    horizon = (EVENT_END - signup).days

    if not completed:
        # A few non-activated users come back once or twice, then give up
        for day_n in range(1, min(8, horizon + 1)):
            if rng.random() < 0.06 * np.exp(-day_n / 2):
                events.append((u.user_id, "app_open", ts(signup + timedelta(days=day_n))))
        continue

    # ---- Engagement for activated users ----
    early_messager = rng.random() < (0.35 if u.account_tier == "private_client" else 0.20)
    mult = (rng.gamma(2.0, 0.5)                    # personal engagement level (mean 1)
            * CHANNEL_MULT[u.acquisition_channel]
            * TIER_MULT[u.account_tier]
            * PLATFORM_MULT[u.platform]
            * (2.4 if early_messager else 1.0))
    # Every user eventually churns; early messagers stay longer
    churn_day = rng.exponential(120 if early_messager else 70)

    # Day-0 activity right after onboarding
    events.append((u.user_id, "view_portfolio", (step_times[-1] + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S")))
    if early_messager:
        events.append((u.user_id, "message_advisor", (step_times[-1] + timedelta(minutes=6)).strftime("%Y-%m-%d %H:%M:%S")))

    day_ns = np.arange(1, horizon + 1)
    p_active = np.minimum(0.95, mult * (0.30 * np.exp(-day_ns / 4) + 0.12 * np.exp(-day_ns / 40) + 0.03))
    p_active[day_ns > churn_day] = 0.0
    active_days = day_ns[rng.random(len(day_ns)) < p_active]

    for day_n in active_days:
        day = signup + timedelta(days=int(day_n))
        events.append((u.user_id, "app_open", ts(day)))
        # In week 1, only "early messagers" message their advisor
        w = np.array([0.55, 0.15, 0.12, 0.12, 0.06 if (day_n > 7 or early_messager) else 0.0])
        w = w / w.sum()
        for _ in range(1 + rng.poisson(1.2)):
            events.append((u.user_id, rng.choice(FEATURES, p=w), ts(day)))

ev = pd.DataFrame(events, columns=["user_id", "event_name", "event_ts"])
ev = ev.sort_values(["event_ts", "user_id"]).reset_index(drop=True)
ev.insert(0, "event_id", [f"e{i:08d}" for i in range(1, len(ev) + 1)])

# ---------------------------------------------------------------------------
# 3. Inject data-quality issues
# ---------------------------------------------------------------------------
dupes = ev.sample(frac=0.004, random_state=SEED)                 # duplicate rows
ev = pd.concat([ev, dupes]).sort_values(["event_ts", "event_id"]).reset_index(drop=True)

missing = users.sample(frac=0.003, random_state=SEED).index      # missing platform
users.loc[missing, "platform"] = None

users.to_csv(os.path.join(OUT_DIR, "users.csv"), index=False)
ev.to_csv(os.path.join(OUT_DIR, "events.csv"), index=False)

print(f"users.csv : {len(users):,} rows")
print(f"events.csv: {len(ev):,} rows")
print(f"Saved to  : {OUT_DIR}")
