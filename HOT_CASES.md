# EchoTime hot case gallery

**window:** next_90_days  
**audience:** general

These are high-attention cases chosen for shareability, public interest, and clear time-series storytelling.

## OpenClaw GitHub stars and star-velocity bursts

**case key:** `openclaw_star_velocity`  
**Likely attention window:** March–May 2026

**Why this can travel:** This is a classic hype-cycle time series: a fast open-source project with social amplification, release-driven bursts, and potential security/event shocks.

**Data to track:**

- daily star count
- daily new stars
- fork count
- release dates
- security/advisory dates
- docs traffic or install traffic if you have it

**Similarity questions worth asking:**

- Does the current 14-day growth curve look more like an organic climb or a short viral spike?
- Do post-release star surges resemble earlier release windows?
- How similar is OpenClaw's growth to another breakout GitHub project?

**Recommended API:**

- `compare_series(current_window, historical_window)`
- `rolling_similarity(repo_a_daily_stars, repo_b_daily_stars, window=14)`
- `compare_profiles(dataset_a, dataset_b)`

**What non-method users should see:**

- a similarity summary saying whether this looks like another sustainable growth window or just a spike
- a narrative report explaining whether rhythm, trend, or burstiness is driving the resemblance

**Notes:**

- Use cumulative stars and daily star increments side by side; they answer different questions.
- Keep event annotations such as releases, tweets, and advisories instead of only storing the numeric series.

## Breakout GitHub projects: compare star curves across launches

**case key:** `github_breakout_repo_benchmarks`  
**Likely attention window:** March–May 2026

**Why this can travel:** Developers, investors, and open-source founders all understand star-growth charts quickly, so they travel well across disciplines and social channels.

**Data to track:**

- daily stars for several repositories
- daily issues and pull requests
- release cadence
- referral traffic or docs sessions if available

**Similarity questions worth asking:**

- Which new repo most resembles a previous breakout launch in its first 30 days?
- Do two repos share the same long-tail decay pattern after the initial spike?
- Is a repo's community growth more similar to a consumer-product launch than to a typical open-source release?

**Recommended API:**

- `compare_series(repo_a_daily_stars, repo_b_daily_stars)`
- `compare_profiles(repo_a_panel, repo_b_panel)`
- `rolling_similarity(repo_a_daily_stars, repo_b_daily_stars, window=30)`

**What non-method users should see:**

- a leaderboard of nearest historical analogs
- a simple summary of whether two launches match in trend, timing, and volatility

**Notes:**

- Normalize by launch day or first 1,000 stars when comparing early-stage growth curves.

## BTC vs gold vs oil under shock and macro headlines

**case key:** `btc_vs_gold_vs_oil`  
**Likely attention window:** March–May 2026

**Why this can travel:** This is a high-traffic financial story because the three series often react differently to risk, inflation, liquidity, and geopolitical shocks.

**Data to track:**

- daily close or hourly close for BTC
- spot gold or gold ETF close
- Brent or WTI close
- major policy or geopolitical timestamps

**Similarity questions worth asking:**

- When does BTC move more like a risk asset and when does it resemble a stress-sensitive macro series?
- Do gold and oil share the same shock windows or only the same broad trend?
- Which pair becomes more similar during geopolitical escalation?

**Recommended API:**

- `compare_series(btc_returns, gold_returns)`
- `rolling_similarity(gold_returns, oil_returns, window=20)`
- `compare_profiles(window_a, window_b)`

**What non-method users should see:**

- a rolling similarity chart for pairs of assets
- a narrative report translating similarity changes into regime language

**Notes:**

- Use returns or z-scored prices when scales differ wildly.
- Rolling windows are usually more informative than one all-period average for the whole year.

## Launch-week traffic, signup bursts, and docs demand

**case key:** `launch_traffic_vs_signup_conversion`  
**Likely attention window:** Any 90-day launch or campaign window

**Why this can travel:** This is one of the fastest routes to a shareable time-series story because product teams, founders, and growth marketers immediately understand the plots.

**Data to track:**

- daily sessions
- daily signups
- docs traffic
- GitHub stars or waitlist growth
- campaign timestamps

**Similarity questions worth asking:**

- Did this launch behave more like a community release or a paid campaign burst?
- Are docs-traffic spikes synchronized with signup spikes?
- Which earlier launch is the nearest analog to the current one?

**Recommended API:**

- `compare_series(signups, docs_sessions)`
- `rolling_similarity(launch_a_sessions, launch_b_sessions, window=7)`
- `compare_profiles(product_a_dataset, product_b_dataset)`

**What non-method users should see:**

- a one-page launch summary with shared peaks, lagged peaks, and watchouts
- plain-language notes on whether the launch looks healthy or purely burst-driven

**Notes:**

- Keep campaign/event markers and channel labels if you want to explain the patterns later.
