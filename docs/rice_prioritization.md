# WealthView: Prioritized Product Improvements (RICE)

**Goal:** Recover activation and engagement lost since the March 15, 2026 onboarding redesign.
**Method:** Each idea comes from a specific finding in the SQL analysis and is scored with **RICE**:

> **RICE score = (Reach × Impact × Confidence) ÷ Effort**

---

## Scoring scales

| Factor | What it means | Scale used |
|---|---|---|
| **Reach** | Users affected **per quarter** | Number of users (from the data) |
| **Impact** | How much it moves the target metric for each user reached | 3 = massive, 2 = high, 1 = medium, 0.5 = low, 0.25 = minimal |
| **Confidence** | How sure we are about reach and impact | 100% = proven, 80% = strong evidence, 50% = correlational / some evidence, 30% = a hunch |
| **Effort** | Total team time (design + engineering + review) | Person-weeks |

### Reach assumptions (from `sql/07` and `sql/04`)
- **New installs per quarter:** ~10,500 (recent average of ~3,500 signups/month)
- **Create an account:** 86% → **~9,000** users/quarter
- **Pass verification (post-redesign):** ~65% of account creators → **~5,900**
- **Abandon at verification (post-redesign):** ~35% of account creators → **~3,100**
- **Finish onboarding (post-redesign):** 43% → **~4,500**
- **Paid social share of installs:** 25% → **~2,600**

---

## Prioritized list

| Rank | Improvement | Finding it addresses | Reach | Impact | Confidence | Effort | **RICE** |
|---|---|---|---|---|---|---|---|
| **1** | **Simplify identity verification (Android first):** cut 4 screens to 2, auto-capture ID photo, clearer error messages | Android verify pass rate fell 79% → 54% after the redesign (iOS 82% → 74%) | 9,000 | 3 | 80% | 6 | **3,600** |
| 2 | **"Finish verifying" reminder:** save progress and send a push/email to users who abandon at verification | ~35% of account creators now drop at verification | 3,100 | 1 | 60% | 1 | **1,860** |
| 3 | **Week-1 advisor nudge:** prompt new users to message their advisor (e.g., an intro message from the advisor after onboarding) | Messaging an advisor in week 1 = 17.6% vs 7.0% D30 retention, but only 22% do it | 4,500 | 2 | 50% | 3 | **1,500** |
| 4 | **Shift acquisition spend** from paid social toward an advisor referral program | Paid social D30 = 6.0% vs 10.1% for advisor referrals | 2,600 | 1 | 70% | 2 | **910** |
| 5 | **"Link a bank account later" option** in onboarding | 19% of verified users drop at bank linking | 5,900 | 1 | 50% | 4 | **738** |
| 6 | **Personalized research / insights feed** to drive week-1 feature use | Feature users retain better, but the effect is mostly general engagement | 4,500 | 0.5 | 30% | 5 | **135** |

---

## Why this order

**1. Simplify identity verification (top priority).** It has the biggest reach (everyone who creates an account goes through it), and the evidence is the strongest in the analysis: the drop started the exact week the redesign launched and is concentrated on Android. Restoring each platform to its pre-redesign verification rate would lift overall activation from about **43% to 54%**, or roughly **1,000+ additional activated users per quarter**. Confidence is 80% rather than 100% because the redesign timing is strong evidence but not a controlled test; this is the improvement proposed for the A/B test.

**2. Verification reminder (quick win).** It's a small build (1 person-week) aimed at people who already showed intent by creating an account. It ranks high because of the low effort, not a large impact. **Dependency:** if #1 succeeds, fewer people abandon verification, so this idea's reach shrinks. Ship #1 first, then size #2 again.

**3. Week-1 advisor nudge.** Potentially high impact, since advisor messaging shows the biggest retention gap of any feature, even among equally active users. Confidence is only 50% because the link is **correlational**: users who message advisors may simply be more committed clients. This should be the **next A/B test** after verification.

**4. Shift acquisition spend.** Low engineering effort, but it's a marketing decision with budget trade-offs. Medium confidence: referral users may retain better because of who they are (existing advisor relationships), so the gap might not fully transfer to new users brought in through a referral program.

**5. "Link later" option.** Real drop-off (19%), but skipping might hurt long-term engagement, since a linked account is what makes the app useful. Low confidence and moderate effort.

**6. Insights feed.** Deprioritized. Once you compare engaged users with each other, viewing research doesn't stand out the way advisor messaging does.

---

## Compliance note

Identity verification is a **Know Your Customer (KYC)** requirement for a financial services app. Any simplification must keep the same regulatory checks and only change the **experience** (fewer screens, automatic capture, clearer errors), not what gets verified. This is why the A/B test includes **fraud flags** as a guardrail metric.

## What would change this ranking

- If engineering estimates the verification fix at 12+ person-weeks, #1's score halves (1,800), roughly tying with #2. It would still rank first, since #2 depends on it.
- If an A/B test shows the advisor nudge **causes** better retention, its confidence rises to 80% and its score to 2,400.
- If new-user volume keeps falling, reach shrinks for every item, but the ranking stays the same.
