# echotime similarity summary

**Compared:** OpenClaw-style candidate vs durable breakout analog

## Headline

These two inputs show **very high** similarity overall (score 0.992).

OpenClaw-style candidate and durable breakout analog are strongly similar overall. The best agreement appears in trend similarity and shape similarity.

## Most important similarity dimensions

| plain-language label | score |
|---|---:|
| trend similarity | 1.000 |
| shape similarity | 1.000 |
| dtw similarity | 0.997 |
| spectral similarity | 0.991 |

## Recommended next actions

- Plot both series after z-score normalization to show the shared shape without scale differences.
- Run rolling or windowed similarity if you expect the relationship to change over time.
- Use structural-profile similarity when scales, frequencies, or observation modes differ too much for raw-shape comparison.
- Inspect spectral or seasonality-aware models because the two series share rhythm strongly.