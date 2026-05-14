# echotime summary card

**audience:** general  
**domain:** wearable  
**observation mode:** dense  
**overall reliability:** 0.755 (high)

## Executive summary

This looks like a wearable or digital biomarker cohort with about 6 participant(s) and roughly 3 signal channel(s) per participant. In plain language, the strongest signals in its structure are that complexity is very high, coupling and network structure is high, and trend strength is high. Overall evidence quality for this profile is high.

## Dataset facts

| field | value |
|---|---:|
| n_subjects | 6 |
| n_channels_median | 3 |
| length_median | 60 |
| dominant_axes | complexity, coupling_networkedness, trendness |
| reliability | 0.755 (high) |

## Top structure axes

| axis | plain-language label | score | level | what it usually means |
|---|---|---:|---|---|
| complexity | complexity | 0.829 | very high | the signal contains rich local variation rather than one simple repeating template |
| coupling_networkedness | coupling and network structure | 0.709 | high | channels or regions move together in a structured multivariate way |
| trendness | trend strength | 0.646 | high | there is meaningful slow movement or baseline shift rather than pure fluctuation |
| rhythmicity | rhythmicity | 0.477 | moderate | the data contain repeating or oscillatory patterns that may support seasonal or frequency-aware analysis |

## Main takeaways

- complexity: the signal contains rich local variation rather than one simple repeating template.
- coupling and network structure: channels or regions move together in a structured multivariate way.
- trend strength: there is meaningful slow movement or baseline shift rather than pure fluctuation.

## Main watchouts

- Watch drift and nonstationarity: the data-generating behavior changes over time rather than staying stable.
- Watch regime switching: the system appears to move between distinct states or operating modes.
- Watch observation irregularity: measurements do not arrive on a clean, even grid, so timing and missingness matter.

## Analysis opportunities

- Opportunity in coupling and network structure: channels or regions move together in a structured multivariate way.
- Opportunity in trend strength: there is meaningful slow movement or baseline shift rather than pure fluctuation.
- Opportunity in rhythmicity: the data contain repeating or oscillatory patterns that may support seasonal or frequency-aware analysis.

## Recommended next actions

1. Expect single-number summaries to miss part of the structure; representation learning may help.
2. Use multivariate or network-aware models instead of treating each channel as independent.
3. Include detrending or low-frequency structure checks in the workflow and compare trend-aware baselines.
4. Try frequency-aware, seasonal, or cycle-aware summaries before assuming the data are memoryless.
5. Benchmark multivariate and graph-aware models; independent per-channel models will likely discard signal.

## Structural archetypes

trend_dominated, strongly_coupled_multivariate, wearable_monitoring

## Interpretation notes

- Reliability scores combine proxy coverage and data-support heuristics.