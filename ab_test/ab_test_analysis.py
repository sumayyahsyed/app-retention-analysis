"""
ab_test_analysis.py
-------------------
Three parts, matching what an analyst actually does for an experiment:

  PART 1 - PLAN:      How many users do we need, and how long will it take?
  PART 2 - SIMULATE:  Create fake experiment results (stand-in for real data)
  PART 3 - ANALYZE:   Was the change a real improvement? Check guardrails.

The test:
  Control   (A) = current post-redesign verification flow (4 screens, manual photo upload)
  Treatment (B) = simplified flow (2 screens, auto-capture of ID, clearer error messages)
"""

import math
import os

import numpy as np
import pandas as pd

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(7)


def norm_cdf(z: float) -> float:
    """Standard normal CDF (what scipy.stats.norm.cdf does)."""
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


# Z values for the usual settings
Z_ALPHA_2 = 1.96   # two-sided test at alpha = 0.05
Z_POWER = 0.84     # 80% power


# =============================================================================
# PART 1 - PLAN: sample size and duration
# =============================================================================
BASELINE = 0.42          # current onboarding completion (post-redesign, from sql/05)
MDE = 0.05               # smallest lift worth detecting: +5 percentage points
DAILY_NEW_USERS = 113    # ~3,400 signups/month in recent months (from sql/07)

p1, p2 = BASELINE, BASELINE + MDE
n_per_arm = math.ceil(((Z_ALPHA_2 + Z_POWER) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))) / MDE ** 2)
days_needed = math.ceil(2 * n_per_arm / DAILY_NEW_USERS)
weeks = math.ceil(days_needed / 7)

print("=" * 70)
print("PART 1 - EXPERIMENT PLAN")
print("=" * 70)
print(f"Baseline onboarding completion : {BASELINE:.0%}")
print(f"Minimum detectable effect (MDE): +{MDE * 100:.0f} percentage points ({p1:.0%} -> {p2:.0%})")
print("Significance level / power      : 5% (two-sided) / 80%")
print(f"Users needed per variant        : {n_per_arm:,}")
print(f"Total users needed              : {2 * n_per_arm:,}")
print(f"New users per day               : ~{DAILY_NEW_USERS}")
print(f"Days needed                     : {days_needed} -> run for {weeks} full weeks")
print("(Full weeks so weekday/weekend behavior is represented equally.)")


# =============================================================================
# PART 2 - SIMULATE experiment data
# =============================================================================
n_total = weeks * 7 * DAILY_NEW_USERS
df = pd.DataFrame({
    "user_id": [f"x{i:06d}" for i in range(1, n_total + 1)],
    "variant": rng.choice(["control", "treatment"], size=n_total),
    "platform": rng.choice(["iOS", "Android"], size=n_total, p=[0.55, 0.45]),
})

# True underlying rates
complete_rate = {("control", "iOS"): 0.49, ("control", "Android"): 0.36,
                 ("treatment", "iOS"): 0.52, ("treatment", "Android"): 0.48}
fraud_rate = {"control": 0.008, "treatment": 0.009}        # guardrail: barely changes
ticket_rate = {"control": 0.060, "treatment": 0.045}       # guardrail: improves

df["completed_onboarding"] = [int(rng.random() < complete_rate[(v, p)]) for v, p in zip(df.variant, df.platform)]
df["retained_d7"] = [int(c == 1 and rng.random() < 0.20) for c in df.completed_onboarding]
df["fraud_flag"] = [int(c == 1 and rng.random() < fraud_rate[v]) for v, c in zip(df.variant, df.completed_onboarding)]
df["support_ticket"] = [int(rng.random() < ticket_rate[v]) for v in df.variant]
df.to_csv(os.path.join(OUT_DIR, "experiment_data.csv"), index=False)


# =============================================================================
# PART 3 - ANALYZE
# =============================================================================
def two_prop_test(df_, metric, denom_mask=None):
    """Two-proportion z-test of treatment vs control for a 0/1 metric."""
    d = df_ if denom_mask is None else df_[denom_mask]
    a = d[d.variant == "control"][metric]
    b = d[d.variant == "treatment"][metric]
    pa, pb, na, nb = a.mean(), b.mean(), len(a), len(b)
    pooled = (a.sum() + b.sum()) / (na + nb)
    se_pooled = math.sqrt(pooled * (1 - pooled) * (1 / na + 1 / nb))
    z = (pb - pa) / se_pooled
    p_value = 2 * (1 - norm_cdf(abs(z)))
    se_diff = math.sqrt(pa * (1 - pa) / na + pb * (1 - pb) / nb)
    lo, hi = (pb - pa) - Z_ALPHA_2 * se_diff, (pb - pa) + Z_ALPHA_2 * se_diff
    return {"metric": metric, "control_n": na, "treatment_n": nb,
            "control_rate_pct": round(100 * pa, 2), "treatment_rate_pct": round(100 * pb, 2),
            "abs_lift_pts": round(100 * (pb - pa), 2), "rel_lift_pct": round(100 * (pb - pa) / pa, 1),
            "ci95_low_pts": round(100 * lo, 2), "ci95_high_pts": round(100 * hi, 2),
            "z": round(z, 2), "p_value": round(p_value, 4), "significant": p_value < 0.05}


print("\n" + "=" * 70)
print("PART 3 - RESULTS")
print("=" * 70)

# Sanity check: sample ratio mismatch (is the split really ~50/50?)
counts = df.variant.value_counts()
expected = len(df) / 2
chi2 = sum((counts[v] - expected) ** 2 / expected for v in ["control", "treatment"])
srm_p = 2 * (1 - norm_cdf(math.sqrt(chi2)))   # chi-square with 1 df == z^2
print(f"Split: control={counts['control']:,}  treatment={counts['treatment']:,}  "
      f"(SRM check p={srm_p:.3f} -> {'OK' if srm_p > 0.01 else 'PROBLEM: investigate assignment'})\n")

results = [
    {"role": "PRIMARY",   **two_prop_test(df, "completed_onboarding")},
    {"role": "SECONDARY", **two_prop_test(df, "retained_d7")},
    {"role": "GUARDRAIL", **two_prop_test(df, "fraud_flag", df.completed_onboarding == 1)},
    {"role": "GUARDRAIL", **two_prop_test(df, "support_ticket")},
]
res = pd.DataFrame(results)
pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 20)
print(res.to_string(index=False))

print("\nPrimary metric by platform (did it fix the Android problem?):")
seg = pd.DataFrame([{"platform": p, **two_prop_test(df[df.platform == p], "completed_onboarding")}
                    for p in ["iOS", "Android"]])
print(seg[["platform", "control_rate_pct", "treatment_rate_pct", "abs_lift_pts", "p_value"]].to_string(index=False))

res.to_csv(os.path.join(OUT_DIR, "experiment_results.csv"), index=False)
seg.to_csv(os.path.join(OUT_DIR, "experiment_results_by_platform.csv"), index=False)

# ---- Decision rule (decided BEFORE the test started) ----
primary = results[0]
fraud = results[2]
fraud_ok = not (fraud["significant"] and fraud["abs_lift_pts"] > 0)
print("\nDECISION")
if primary["significant"] and primary["abs_lift_pts"] > 0 and fraud_ok:
    print(f"SHIP: onboarding completion +{primary['abs_lift_pts']} pts "
          f"(95% CI {primary['ci95_low_pts']} to {primary['ci95_high_pts']}), "
          f"no significant increase in fraud flags.")
else:
    print("DO NOT SHIP: primary metric not significantly better, or a guardrail got worse.")
