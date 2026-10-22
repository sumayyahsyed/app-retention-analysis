# A/B Test Proposal: Simplified Identity Verification

**Author:** Sumayyah Syed  **Status:** Completed (simulated results)  **Related:** `docs/rice_prioritization.md` (improvement #1), `ab_test/ab_test_analysis.py`

---

## 1. Summary

Since the March 15, 2026 onboarding redesign, identity verification has become the biggest leak in WealthView's onboarding funnel, especially on Android (pass rate fell from 79% to 54%). We propose testing a **simplified verification flow** against the current one.

**Result (simulated):** the simplified flow raised onboarding completion by **+4.0 percentage points** overall (p = 0.026) and **+8.1 points on Android** (p = 0.002), with no significant increase in fraud flags. **Recommendation: ship, starting with a staged rollout while monitoring fraud.**

---

## 2. Background

| Evidence | Source |
|---|---|
| ~35% of users who create an account now quit at identity verification | `sql/03`, `sql/04` |
| Android verification pass rate: 78.6% → 54.2% after the redesign (iOS: 81.9% → 74.1%) | `sql/04` |
| Overall activation fell from ~54% to ~43% the week the redesign launched | `sql/05` |
| Users who **do** finish onboarding retain as well as before (D30 ≈ 8% pre and post) | `sql/05` |

The problem is getting users **into** the app, not keeping them, so the fix should target the verification step.

---

## 3. Hypothesis

> **If** we reduce identity verification from 4 screens to 2, with automatic ID photo capture and clearer error messages,
> **then** onboarding completion will increase,
> **because** users currently abandon at this step, and the drop began when the more complex redesigned flow launched.

We expect the largest effect on **Android**, where the redesign caused the biggest drop.

---

## 4. Variants

| | Control (A) | Treatment (B) |
|---|---|---|
| Screens | 4 | 2 |
| ID photo | Manual capture and upload | Automatic capture when the ID is in frame |
| Errors | Generic "Verification failed" | Specific guidance (e.g., "Glare detected, tilt your ID") |
| **Verification checks** | Same | **Same.** Only the experience changes, not the KYC requirements |

---

## 5. Metrics

| Type | Metric | Definition | Goal |
|---|---|---|---|
| **Primary** | Onboarding completion rate | % of new users who reach `onboarding_complete` | Increase |
| Secondary | Day 7 retention | % of new users active on day 7 after signup | Increase or no change |
| **Guardrail** | Fraud flag rate | % of completed onboardings later flagged for fraud | **Must not increase** |
| Guardrail | Support ticket rate | % of new users who contact support during onboarding | Must not increase |

**Why guardrails matter here:** making verification easier could also make it easier for bad actors to get through. For a financial institution, a conversion gain is not worth a compliance or fraud risk.

---

## 6. Design

- **Unit of randomization:** user (so each person sees one flow consistently)
- **Population:** all new users who start onboarding, iOS and Android
- **Split:** 50 / 50, random assignment at first app open
- **Pre-specified segment:** platform (iOS vs Android), since the hypothesis predicts a larger Android effect
- **Exclusions:** internal test accounts

---

## 7. Sample size and duration

| Input | Value | Why |
|---|---|---|
| Baseline completion | 42% | Current post-redesign rate |
| Minimum detectable effect (MDE) | +5 percentage points (42% → 47%) | Smallest lift worth the engineering cost |
| Significance level (α) | 5%, two-sided | Standard |
| Power | 80% | Standard |
| **Users needed** | **1,546 per variant (3,092 total)** | Two-proportion sample size formula |
| New users per day | ~113 | Recent signup volume (`sql/07`) |
| **Duration** | **28 days → 4 full weeks** | Full weeks so weekday and weekend behavior are equally represented |

**Rule:** don't stop early when results look good. Checking repeatedly and stopping at the first significant result inflates false positives.

---

## 8. Decision rules (set before the test starts)

| Outcome | Decision |
|---|---|
| Primary metric significantly better **and** no guardrail significantly worse | **Ship** |
| Primary metric significantly better **but** a guardrail significantly worse | Don't ship; investigate the guardrail first |
| No significant difference | Don't ship; the change isn't worth maintaining |
| Primary metric significantly worse | Don't ship |

---

## 9. Results (simulated)

> These results come from simulated experiment data (`ab_test/experiment_data.csv`), generated to illustrate the analysis.

**Sample check:** control = 1,565, treatment = 1,599. The sample ratio mismatch check passed (p = 0.55), so randomization worked as expected.

| Role | Metric | Control | Treatment | Lift | 95% CI | p-value | Significant? |
|---|---|---|---|---|---|---|---|
| **Primary** | Onboarding completion | 43.5% | 47.5% | **+4.0 pts** (+9.1% relative) | +0.5 to +7.4 pts | **0.026** | ✅ Yes |
| Secondary | Day 7 retention | 8.7% | 9.6% | +0.9 pts | −1.1 to +2.9 pts | 0.39 | No |
| Guardrail | Fraud flag rate (of completers) | 0.15% | 0.79% | +0.6 pts | −0.1 to +1.3 pts | 0.08 | No (borderline) |
| Guardrail | Support ticket rate | 6.0% | 4.1% | **−1.9 pts** | −3.5 to −0.4 pts | **0.013** | ✅ Yes (improved) |

**By platform (pre-specified segment):**

| Platform | Control | Treatment | Lift | p-value |
|---|---|---|---|---|
| iOS | 48.5% | 49.3% | +0.8 pts | 0.74 |
| **Android** | 37.0% | 45.1% | **+8.1 pts** | **0.002** |

### Interpretation

1. **The primary metric improved significantly.** The observed lift (+4.0 pts) is smaller than the MDE (+5 pts) but still significant. The MDE is the effect the test had 80% power to detect, not a minimum for significance.
2. **Android drives the result.** The lift is concentrated on Android, matching the hypothesis that the redesign hurt Android most. iOS is essentially unchanged.
3. **Day 7 retention didn't move significantly.** This is expected: the test wasn't sized for this metric, and more completed onboardings should show up in retention over a longer period.
4. **The fraud guardrail needs attention.** It wasn't significant (p = 0.08), but the rate rose from 0.15% to 0.79%. These are **very small counts** (about 1 vs 6 flagged users), so the test had little power to detect a fraud change. "Not significant" here does not prove "safe."
5. **Support tickets dropped 32%**, a bonus: clearer error messages likely reduced confusion.

---

## 10. Recommendation

**Ship the simplified verification flow, with a staged rollout:**

1. **Week 1–2:** roll out to **100% of Android users** (largest gain) and 50% of iOS users.
2. **Monitor fraud flags weekly** with the risk/compliance team. Set an alert if the rate exceeds **0.5%** of completed onboardings.
3. **Week 3+:** if fraud stays within the threshold, roll out to 100% of all users.
4. **Re-check Day 30 retention** for treatment-period users once they have 30 days of data.

**Expected impact:** at ~10,500 new installs per quarter, a +4 pt lift means about **420 more activated users per quarter**, and more if Android's +8 pt lift holds at full rollout.

**Next experiment:** the week-1 advisor messaging nudge (RICE #3), to test whether the advisor-messaging link with retention is causal.
